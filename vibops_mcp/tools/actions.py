"""
Action tools (write operations) — 8 tools.

These tools trigger infrastructure changes via VibOps jobs.
All operations are recorded in the audit log.
"""
from vibops_mcp import client


import asyncio


async def _run_job(action: str, payload: dict) -> dict:
    """Submit a job and return its initial state (async — poll with get_job)."""
    return await client.post("/api/v1/jobs", body={"action": action, "payload": payload})


async def _run_job_sync(action: str, payload: dict, timeout: int = 30) -> dict:
    """Submit a job and poll until completion (up to timeout seconds).

    Returns the job dict. If the job does not reach a terminal state within
    `timeout` seconds, returns the last observed state with `timed_out: true`.
    """
    job = await _run_job(action, payload)
    job_id = job.get("id")
    if not job_id:
        return job
    for _ in range(timeout // 2):
        await asyncio.sleep(2)
        result = await client.get(f"/api/v1/jobs/{job_id}")
        if result.get("status") in ("success", "failed"):
            return result
    result["timed_out"] = True
    result["message"] = (
        f"Job {job_id} did not complete within {timeout}s. "
        "Use get_job to check its current status."
    )
    return result


async def scale_deployment(
    cluster_name: str,
    deployment_name: str,
    replicas: int,
    namespace: str = "default",
) -> dict:
    """
    Scale the replica count of a Kubernetes deployment.

    Changes the number of running pods — does not add or remove cluster nodes.
    Set replicas to 0 to suspend a workload, 1 or more to run it.

    Write operation — recorded in the audit log.

    Args:
        cluster_name: Name of the target cluster (as returned by list_clusters).
        deployment_name: Name of the deployment to scale (e.g. llama3, ollama).
        replicas: Desired number of running pods (0 to suspend).
        namespace: Kubernetes namespace (default: 'default').
    """
    payload: dict = {
        "cluster": cluster_name,
        "name": deployment_name,
        "replicas": replicas,
        "namespace": namespace,
    }
    return await _run_job("scale_cluster", payload)


async def deploy_model(
    cluster_name: str,
    model_name: str,
    namespace: str = "default",
    replicas: int = 1,
    gpu_count: int | None = None,
    image: str | None = None,
    env: dict | None = None,
) -> dict:
    """
    Deploy an AI model onto a GPU cluster.

    Use this for standard model deployments. For custom Helm chart deployments,
    use helm_upgrade instead.

    Write operation — recorded in the audit log.

    Args:
        cluster_name: Target cluster name.
        model_name: Model identifier (e.g. llama3:8b, mistral:7b).
        namespace: Kubernetes namespace (default: 'default').
        replicas: Number of replicas (default 1).
        gpu_count: Number of GPUs to allocate per replica (optional).
        image: Override the default container image (optional).
        env: Environment variables to inject into the container (optional).
    """
    payload: dict = {
        "cluster": cluster_name,
        "model": model_name,
        "replicas": replicas,
        "namespace": namespace,
    }
    if gpu_count is not None:
        payload["gpu_count"] = gpu_count
    if image:
        payload["image"] = image
    if env:
        payload["env"] = env
    return await _run_job("deploy_model", payload)


async def helm_upgrade(
    cluster_name: str,
    release_name: str,
    chart: str,
    namespace: str = "default",
    values: dict | None = None,
) -> dict:
    """
    Run helm upgrade --install for a chart on a cluster.

    Use this for Helm chart deployments. For deploying standard AI models,
    use deploy_model instead.

    Write operation — recorded in the audit log.

    Args:
        cluster_name: Target cluster.
        release_name: Helm release name (created if it does not exist).
        chart: Helm chart reference (e.g. bitnami/nginx or ./charts/myapp).
        namespace: Kubernetes namespace (default: 'default').
        values: Helm values to override (dict, optional).
    """
    payload: dict = {
        "cluster": cluster_name,
        "name": release_name,
        "chart": chart,
        "namespace": namespace,
        "wait": False,
    }
    if values:
        payload["values"] = values
    return await _run_job("helm_upgrade", payload)


async def helm_uninstall(cluster_name: str, release_name: str, namespace: str = "default") -> dict:
    """
    Uninstall a Helm release from a cluster.

    Removes all Kubernetes resources created by the release.

    Write operation — recorded in the audit log.

    Args:
        cluster_name: Target cluster.
        release_name: Name of the Helm release to remove.
        namespace: Kubernetes namespace (default: 'default').
    """
    return await _run_job_sync("helm_uninstall", {
        "cluster": cluster_name,
        "name": release_name,
        "namespace": namespace,
    }, timeout=30)


async def run_kubectl(cluster_name: str, command: list[str]) -> dict:
    """
    Execute a kubectl command on a cluster.

    Use this only for operations not covered by dedicated tools. Prefer
    scale_deployment to scale pods, deploy_model for model deployments, and
    helm_upgrade or helm_uninstall for Helm operations.

    Suitable for: get, describe, logs, top, rollout, label, annotate.
    Avoid destructive commands (delete namespace, delete deployment) — use
    dedicated VibOps tools or submit a job via the API instead.

    Write operations executed via this tool are recorded in the audit log.

    Args:
        cluster_name: Target cluster.
        command: kubectl arguments as a list, without the 'kubectl' prefix.
                 Example: ["get", "pods", "-n", "default"]
    """
    return await _run_job_sync("kubectl_exec", {
        "cluster": cluster_name,
        "command": command,
    })


async def git_clone(repo_url: str, branch: str = "main", cluster_name: str | None = None) -> dict:
    """
    Clone a git repository onto the VibOps gateway.

    If cluster_name is provided, Kubernetes manifests found in the repository
    will be automatically applied to that cluster (kubectl apply).
    If cluster_name is omitted, the repository is cloned but nothing is applied.

    Write operation — recorded in the audit log.

    Args:
        repo_url: Git repository URL (HTTPS or SSH).
        branch: Branch to clone (default: main).
        cluster_name: If provided, apply manifests to this cluster after cloning.
    """
    payload: dict = {"repo_url": repo_url, "branch": branch}
    if cluster_name:
        payload["cluster"] = cluster_name
    return await _run_job("git_clone", payload)


async def create_secret(name: str, value: str, description: str | None = None) -> dict:
    """
    Store an encrypted secret in the VibOps vault.

    The value is encrypted at rest and never returned by the API after storage.
    If a secret with the same name already exists, it is overwritten.

    Write operation — recorded in the audit log.

    Args:
        name: Secret name (used to reference this secret in job payloads).
        value: Secret value (encrypted, never logged or returned).
        description: Optional description of what this secret is for.
    """
    body: dict = {"name": name, "value": value}
    if description:
        body["description"] = description
    return await client.post("/api/v1/secrets", body=body)


async def trigger_pipeline(pipeline_id: str, payload: dict | None = None) -> dict:
    """
    Manually trigger an automation pipeline.

    Pipelines are sequences of jobs that execute in order. Retrieve available
    pipeline IDs with list_pipelines.

    Write operation — recorded in the audit log.

    Args:
        pipeline_id: UUID of the pipeline to trigger.
        payload: Optional input parameters passed to the pipeline steps.
    """
    return await client.post(f"/api/v1/pipelines/{pipeline_id}/trigger", body=payload or {})

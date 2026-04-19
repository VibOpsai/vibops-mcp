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
    """Submit a job and poll until completion (up to timeout seconds)."""
    job = await _run_job(action, payload)
    job_id = job.get("id")
    if not job_id:
        return job
    for _ in range(timeout // 2):
        await asyncio.sleep(2)
        result = await client.get(f"/api/v1/jobs/{job_id}")
        if result.get("status") in ("success", "failed"):
            return result
    return job


async def scale_cluster(
    cluster_name: str,
    replicas: int,
    deployment_name: str | None = None,
    namespace: str | None = None,
) -> dict:
    """
    Scale a Kubernetes deployment.

    Args:
        cluster_name: Target cluster name.
        replicas: Desired replica count.
        deployment_name: Name of the deployment to scale (e.g. llama3, ollama).
        namespace: Kubernetes namespace (optional, defaults to 'default').
    """
    payload: dict = {"cluster": cluster_name, "replicas": replicas}
    if deployment_name:
        payload["name"] = deployment_name
    if namespace:
        payload["namespace"] = namespace
    return await _run_job("scale_cluster", payload)


async def deploy_model(
    cluster_name: str,
    model_name: str,
    namespace: str | None = None,
    replicas: int = 1,
    extra: dict | None = None,
) -> dict:
    """
    Deploy an AI model onto a GPU cluster.

    Args:
        cluster_name: Target cluster name.
        model_name: Model identifier (e.g. llama3:8b, mistral:7b).
        namespace: Kubernetes namespace (optional).
        replicas: Number of replicas (default 1).
        extra: Additional deployment parameters (image, resources, env vars…).
    """
    payload: dict = {
        "cluster": cluster_name,
        "model": model_name,
        "replicas": replicas,
    }
    if namespace:
        payload["namespace"] = namespace
    if extra:
        payload.update(extra)
    return await _run_job("deploy_model", payload)


async def helm_upgrade(
    cluster_name: str,
    release_name: str,
    chart: str,
    namespace: str = "default",
    values: dict | None = None,
) -> dict:
    """
    Run helm upgrade --install on a cluster.

    Args:
        cluster_name: Target cluster.
        release_name: Helm release name.
        chart: Helm chart reference (e.g. bitnami/nginx or ./charts/myapp).
        namespace: Kubernetes namespace (default: 'default').
        values: Helm values to override (dict, optional).
    """
    payload: dict = {
        "cluster": cluster_name,
        "name": release_name,
        "chart": chart,
        "namespace": namespace,
    }
    if values:
        payload["values"] = values
    return await _run_job("helm_upgrade", payload)


async def helm_uninstall(cluster_name: str, release_name: str, namespace: str = "default") -> dict:
    """
    Uninstall a Helm release from a cluster.

    Args:
        cluster_name: Target cluster.
        release_name: Helm release to remove.
        namespace: Kubernetes namespace (default: 'default').
    """
    return await _run_job("helm_uninstall", {
        "cluster": cluster_name,
        "name": release_name,
        "namespace": namespace,
    })


async def run_kubectl(cluster_name: str, command: list[str]) -> dict:
    """
    Run an arbitrary kubectl command on a cluster.
    The command is a list of arguments (without 'kubectl' prefix).
    Example: ["get", "pods", "-n", "default"]

    Args:
        cluster_name: Target cluster.
        command: kubectl arguments as a list.
    """
    return await _run_job_sync("kubectl_exec", {
        "cluster": cluster_name,
        "command": command,
    })


async def git_clone(repo_url: str, branch: str = "main", cluster_name: str | None = None) -> dict:
    """
    Clone a git repository (used to pull manifests or model configs).

    Args:
        repo_url: Git repository URL.
        branch: Branch to clone (default: main).
        cluster_name: Target cluster if repo contains K8s manifests to apply.
    """
    payload: dict = {"repo_url": repo_url, "branch": branch}
    if cluster_name:
        payload["cluster"] = cluster_name
    return await _run_job("git_clone", payload)


async def create_secret(name: str, value: str, description: str | None = None) -> dict:
    """
    Store an encrypted secret in the VibOps vault.

    Args:
        name: Secret name (used to reference it in jobs).
        value: Secret value (stored encrypted, never logged).
        description: Optional human-readable description.
    """
    body: dict = {"name": name, "value": value}
    if description:
        body["description"] = description
    return await client.post("/api/v1/secrets", body=body)


async def trigger_pipeline(pipeline_id: str, payload: dict | None = None) -> dict:
    """
    Manually trigger an automation pipeline.

    Args:
        pipeline_id: UUID of the pipeline to trigger.
        payload: Optional input payload for the pipeline.
    """
    return await client.post(f"/api/v1/pipelines/{pipeline_id}/trigger", body=payload or {})

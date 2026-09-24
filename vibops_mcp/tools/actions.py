"""
Action tools (write operations) — 37 tools.

These tools trigger infrastructure changes via VibOps jobs.
All operations are recorded in the audit log.
"""
from vibops_mcp import client


import asyncio


async def _run_job(action: str, payload: dict, gateway_id: str | None = None) -> dict:
    """Submit a job and return its initial state (async — poll with get_job)."""
    body: dict = {"action": action, "payload": payload}
    if gateway_id:
        body["gateway_id"] = gateway_id
    return await client.post("/api/v1/jobs", body=body)


async def _run_job_sync(action: str, payload: dict, timeout: int = 30, gateway_id: str | None = None) -> dict:
    """Submit a job and poll until completion (up to timeout seconds).

    Returns the job dict. If the job does not reach a terminal state within
    `timeout` seconds, returns the last observed state with `timed_out: true`.
    """
    job = await _run_job(action, payload, gateway_id=gateway_id)
    job_id = job.get("id")
    if not job_id:
        return job
    result = job  # fallback if loop runs zero iterations
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
    gateway_id: str | None = None,
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
        gateway_id: Gateway UUID from list_clusters. Omit for single-gateway deployments;
                    provide to disambiguate when multiple gateways share a cluster name.
    """
    payload: dict = {
        "cluster": cluster_name,
        "name": deployment_name,
        "replicas": replicas,
        "namespace": namespace,
    }
    return await _run_job("scale_cluster", payload, gateway_id=gateway_id)


async def deploy_model(
    cluster_name: str,
    model_name: str,
    namespace: str = "default",
    replicas: int = 1,
    gpu_count: int | None = None,
    image: str | None = None,
    env: dict | None = None,
    gateway_id: str | None = None,
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
        gateway_id: Gateway UUID from list_clusters. Omit for single-gateway deployments;
                    provide to disambiguate when multiple gateways share a cluster name.
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
    return await _run_job("deploy_model", payload, gateway_id=gateway_id)


async def helm_upgrade(
    cluster_name: str,
    release_name: str,
    chart: str,
    namespace: str = "default",
    values: dict | None = None,
    confirmed: bool = False,
    gateway_id: str | None = None,
) -> dict:
    """
    Run helm upgrade --install for a chart on a cluster. Destructive — requires
    confirmed=True.

    On an existing release this replaces the running workloads, so it is gated
    like any other destructive action: call once to get the dry-run preview, then
    again with confirmed=True.

    Use this for Helm chart deployments. For deploying standard AI models,
    use deploy_model instead.

    Write operation — recorded in the audit log.

    Args:
        cluster_name: Target cluster.
        release_name: Helm release name (created if it does not exist).
        chart: Helm chart reference (e.g. bitnami/nginx or ./charts/myapp).
        namespace: Kubernetes namespace (default: 'default').
        values: Helm values to override (dict, optional).
        confirmed: Must be True to proceed. Pass False (default) for a dry-run preview.
        gateway_id: Gateway UUID from list_clusters. Omit for single-gateway deployments;
                    provide to disambiguate when multiple gateways share a cluster name.
    """
    payload: dict = {
        "cluster": cluster_name,
        "name": release_name,
        "chart": chart,
        "namespace": namespace,
        "wait": False,
        "confirmed": confirmed,
    }
    if values:
        payload["values"] = values
    return await _run_job("helm_upgrade", payload, gateway_id=gateway_id)


async def helm_uninstall(
    cluster_name: str,
    release_name: str,
    namespace: str = "default",
    confirmed: bool = False,
    gateway_id: str | None = None,
) -> dict:
    """
    Uninstall a Helm release from a cluster. Destructive — requires confirmed=True.

    Removes all Kubernetes resources created by the release.

    Write operation — recorded in the audit log.

    Args:
        cluster_name: Target cluster.
        release_name: Name of the Helm release to remove.
        namespace: Kubernetes namespace (default: 'default').
        confirmed: Must be True to proceed. Pass False (default) for a dry-run preview.
        gateway_id: Gateway UUID from list_clusters. Omit for single-gateway deployments;
                    provide to disambiguate when multiple gateways share a cluster name.
    """
    # `confirmed` etait absent : l'action est destructive depuis toujours, donc le
    # moteur de politiques repondait 409 et cet outil ne pouvait pas aboutir.
    # Trouve le 24/09 en corrigeant le drapeau de helm_install.
    return await _run_job_sync("helm_uninstall", {
        "cluster": cluster_name,
        "name": release_name,
        "namespace": namespace,
        "confirmed": confirmed,
    }, timeout=30, gateway_id=gateway_id)


_KUBECTL_ALLOWED_VERBS = frozenset({
    "get", "describe", "logs", "top", "rollout", "label", "annotate",
    "api-resources", "api-versions", "explain", "cluster-info",
    "config", "version", "wait", "auth",
})

_KUBECTL_BLOCKED_VERBS = frozenset({
    "exec", "delete", "apply", "patch", "create", "edit", "replace",
    "cp", "run", "attach", "port-forward", "proxy", "taint", "drain",
    "cordon", "uncordon",
})


async def run_kubectl(
    cluster_name: str,
    command: list[str],
    gateway_id: str | None = None,
) -> dict:
    """
    Execute a kubectl command on a cluster.

    Use this only for operations not covered by dedicated tools. Prefer
    scale_deployment to scale pods, deploy_model for model deployments, and
    helm_upgrade or helm_uninstall for Helm operations.

    Allowed verbs: get, describe, logs, top, rollout, label, annotate,
    api-resources, api-versions, explain, cluster-info, config, version, wait, auth.

    Blocked verbs: exec, delete, apply, patch, create, edit, replace,
    cp, run, attach, port-forward, proxy, taint, drain, cordon, uncordon.

    Write operations executed via this tool are recorded in the audit log.

    Args:
        cluster_name: Target cluster.
        command: kubectl arguments as a list, without the 'kubectl' prefix.
                 Example: ["get", "pods", "-n", "default"]
        gateway_id: Gateway UUID from list_clusters. Omit for single-gateway deployments;
                    provide to disambiguate when multiple gateways share a cluster name.
    """
    if not command:
        return {"error": "No kubectl command provided."}
    verb = command[0]
    if verb in _KUBECTL_BLOCKED_VERBS or verb not in _KUBECTL_ALLOWED_VERBS:
        return {"error": f"kubectl verb '{verb}' is not allowed via MCP. Use dedicated VibOps tools for destructive operations."}
    return await _run_job_sync("kubectl_exec", {
        "cluster": cluster_name,
        "command": command,
    }, gateway_id=gateway_id)


async def git_clone(
    repo_url: str,
    branch: str = "main",
    cluster_name: str | None = None,
    gateway_id: str | None = None,
) -> dict:
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
        gateway_id: Gateway UUID from list_clusters. Omit for single-gateway deployments;
                    provide to disambiguate when multiple gateways share a cluster name.
    """
    payload: dict = {"repo_url": repo_url, "branch": branch}
    if cluster_name:
        payload["cluster"] = cluster_name
    return await _run_job("git_clone", payload, gateway_id=gateway_id)


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


# ── Slurm HPC (6 tools) ───────────────────────────────────────────────────────

async def slurm_get_cluster_info(
    host: str | None = None,
    partition: str | None = None,
    gateway_id: str | None = None,
) -> dict:
    """
    Get Slurm cluster information: partitions, node states, and GPU availability.

    Returns a summary of all nodes, their GPU resources (GRES), memory, and
    current state (idle / allocated / down).

    Args:
        host: Slurm head node hostname. Overrides the SLURM_HOST env var on the gateway.
        partition: Filter output to a specific partition (optional).
        gateway_id: Gateway UUID for the site where the Slurm cluster is deployed.
    """
    payload: dict = {}
    if host:
        payload["host"] = host
    if partition:
        payload["partition"] = partition
    return await _run_job_sync("slurm_get_cluster_info", payload, timeout=20, gateway_id=gateway_id)


async def slurm_list_jobs(
    host: str | None = None,
    user: str | None = None,
    partition: str | None = None,
    state: str | None = None,
    gateway_id: str | None = None,
) -> dict:
    """
    List running and pending Slurm jobs.

    Returns job ID, name, user, state, partition, node count, GPU allocation,
    submit time, and time limit for each job.

    Args:
        host: Slurm head node hostname (overrides SLURM_HOST).
        user: Filter by username (optional).
        partition: Filter by partition name (optional).
        state: Filter by job state — RUNNING, PENDING, FAILED, COMPLETED (optional).
        gateway_id: Gateway UUID for the target site.
    """
    payload: dict = {}
    if host:
        payload["host"] = host
    if user:
        payload["user"] = user
    if partition:
        payload["partition"] = partition
    if state:
        payload["state"] = state
    return await _run_job_sync("slurm_list_jobs", payload, timeout=20, gateway_id=gateway_id)


async def slurm_get_job_status(
    job_id: int,
    host: str | None = None,
    gateway_id: str | None = None,
) -> dict:
    """
    Get the current status and resource usage of a specific Slurm job.

    Queries squeue for running/pending jobs and falls back to sacct for
    completed or failed jobs.

    Args:
        job_id: Slurm job ID.
        host: Slurm head node hostname (overrides SLURM_HOST).
        gateway_id: Gateway UUID for the target site.
    """
    payload: dict = {"job_id": job_id}
    if host:
        payload["host"] = host
    return await _run_job_sync("slurm_get_job_status", payload, timeout=20, gateway_id=gateway_id)


async def slurm_get_job_output(
    job_id: int,
    host: str | None = None,
    log_path: str | None = None,
    lines: int = 50,
    gateway_id: str | None = None,
) -> dict:
    """
    Tail the stdout log file of a Slurm job to monitor training progress.

    Reads the last N lines of the job's output file. If log_path is omitted,
    defaults to slurm-{job_id}.out in the user's home directory.

    Args:
        job_id: Slurm job ID.
        host: Slurm head node hostname (overrides SLURM_HOST).
        log_path: Explicit path to the log file (optional).
        lines: Number of lines to return (default: 50).
        gateway_id: Gateway UUID for the target site.
    """
    payload: dict = {"job_id": job_id, "lines": lines}
    if host:
        payload["host"] = host
    if log_path:
        payload["log_path"] = log_path
    return await _run_job_sync("slurm_get_job_output", payload, timeout=20, gateway_id=gateway_id)


async def slurm_submit_job(
    job_name: str,
    nodes: int,
    gpus_per_node: int,
    script: str,
    host: str | None = None,
    partition: str | None = None,
    ntasks_per_node: int | None = None,
    time: str | None = None,
    output: str | None = None,
    error: str | None = None,
    account: str | None = None,
    dry_run: bool = False,
    gateway_id: str | None = None,
) -> dict:
    """
    Submit a multi-node GPU training job to Slurm via sbatch.

    Generates a complete sbatch script from the provided spec and submits it.
    Set dry_run=true to preview the script without submitting.

    Write operation — recorded in the audit log.

    Args:
        job_name: Job name (--job-name).
        nodes: Number of nodes to allocate (--nodes).
        gpus_per_node: GPUs per node (--gpus-per-node).
        script: Shell script body — the command to run (e.g. torchrun --nproc_per_node=8 train.py).
        host: Slurm head node hostname (overrides SLURM_HOST).
        partition: Target Slurm partition (--partition).
        ntasks_per_node: MPI tasks per node (default: gpus_per_node).
        time: Wall-clock time limit in HH:MM:SS or D-HH:MM:SS format (--time).
        output: Path to stdout log file (default: slurm-%j.out).
        error: Path to stderr log file (default: slurm-%j.err).
        account: Slurm account / allocation for billing (--account).
        dry_run: If true, return the sbatch script without submitting.
        gateway_id: Gateway UUID for the site where the Slurm cluster is deployed.
    """
    import re as _re
    _dangerous_patterns = _re.compile(
        r"(curl\s.*\|\s*(ba)?sh|wget\s.*\|\s*(ba)?sh|"
        r"rm\s+-rf\s+/|mkfs\.|dd\s+if=|>\s*/dev/sd|"
        r"/etc/passwd|/etc/shadow|chmod\s+[0-7]*777)",
        _re.IGNORECASE,
    )
    if _dangerous_patterns.search(script):
        return {"error": "Script contains potentially dangerous patterns. Review and submit via the Slurm CLI directly."}
    payload: dict = {
        "job_name":      job_name,
        "nodes":         nodes,
        "gpus_per_node": gpus_per_node,
        "script":        script,
        "dry_run":       dry_run,
    }
    if host:
        payload["host"] = host
    if partition:
        payload["partition"] = partition
    if ntasks_per_node is not None:
        payload["ntasks_per_node"] = ntasks_per_node
    if time:
        payload["time"] = time
    if output:
        payload["output"] = output
    if error:
        payload["error"] = error
    if account:
        payload["account"] = account
    return await _run_job_sync("slurm_submit_job", payload, timeout=30, gateway_id=gateway_id)


async def slurm_cancel_job(
    job_id: int,
    host: str | None = None,
    signal: str = "SIGTERM",
    gateway_id: str | None = None,
) -> dict:
    """
    Cancel a running or pending Slurm job by job ID (scancel).

    Write operation — recorded in the audit log.

    Args:
        job_id: Slurm job ID to cancel.
        host: Slurm head node hostname (overrides SLURM_HOST).
        signal: Signal to send to the job (default: SIGTERM). Use SIGKILL for immediate termination.
        gateway_id: Gateway UUID for the target site.
    """
    payload: dict = {"job_id": job_id, "signal": signal}
    if host:
        payload["host"] = host
    return await _run_job_sync("slurm_cancel_job", payload, timeout=20, gateway_id=gateway_id)


# ── Container Registry ────────────────────────────────────────────────────────

async def registry_list_repos(
    registry_type: str,
    registry_url: str | None = None,
    project: str | None = None,
    username: str | None = None,
    password: str | None = None,
    region: str | None = None,
    limit: int = 50,
    gateway_id: str | None = None,
) -> dict:
    """
    List repositories in a container registry (Harbor, ECR, or Google Artifact Registry).

    Args:
        registry_type: Registry backend — "harbor", "ecr", or "gar".
        registry_url: Harbor base URL (e.g. https://registry.acme.com) or ECR registry URI.
        project: Harbor project name or GAR repository path prefix.
        username: Harbor username (or "AWS" for ECR token auth).
        password: Harbor password or registry token.
        region: AWS region (ECR only, e.g. us-east-1).
        limit: Maximum number of repositories to return (default 50).
        gateway_id: Gateway UUID for the target site.
    """
    payload: dict = {"registry_type": registry_type, "limit": limit}
    if registry_url:
        payload["registry_url"] = registry_url
    if project:
        payload["project"] = project
    if username:
        payload["username"] = username
    if password:
        payload["password"] = password
    if region:
        payload["region"] = region
    return await _run_job_sync("registry_list_repos", payload, timeout=30, gateway_id=gateway_id)


async def registry_list_tags(
    registry_type: str,
    image: str,
    registry_url: str | None = None,
    username: str | None = None,
    password: str | None = None,
    region: str | None = None,
    gateway_id: str | None = None,
) -> dict:
    """
    List all tags for a specific image in a container registry.

    Args:
        registry_type: Registry backend — "harbor", "ecr", or "gar".
        image: Image name without tag (e.g. "myproject/myapp" for Harbor, repo name for ECR).
        registry_url: Harbor base URL or ECR registry URI.
        username: Harbor username or registry token username.
        password: Harbor password or registry token.
        region: AWS region (ECR only).
        gateway_id: Gateway UUID for the target site.
    """
    payload: dict = {"registry_type": registry_type, "image": image}
    if registry_url:
        payload["registry_url"] = registry_url
    if username:
        payload["username"] = username
    if password:
        payload["password"] = password
    if region:
        payload["region"] = region
    return await _run_job_sync("registry_list_tags", payload, timeout=30, gateway_id=gateway_id)


async def registry_check_image(
    registry_type: str,
    image: str,
    registry_url: str | None = None,
    username: str | None = None,
    password: str | None = None,
    region: str | None = None,
    gateway_id: str | None = None,
) -> dict:
    """
    Check whether a specific image:tag exists in a container registry.

    Returns exists=True/False without raising an error when the image is absent.
    Useful for pre-deployment checks and stale image detection.

    Args:
        registry_type: Registry backend — "harbor", "ecr", or "gar".
        image: Image name with tag (e.g. "myproject/myapp:v1.2.3").
        registry_url: Harbor base URL or ECR registry URI.
        username: Harbor username or registry token username.
        password: Harbor password or registry token.
        region: AWS region (ECR only).
        gateway_id: Gateway UUID for the target site.
    """
    payload: dict = {"registry_type": registry_type, "image": image}
    if registry_url:
        payload["registry_url"] = registry_url
    if username:
        payload["username"] = username
    if password:
        payload["password"] = password
    if region:
        payload["region"] = region
    return await _run_job_sync("registry_check_image", payload, timeout=20, gateway_id=gateway_id)


async def registry_delete_tag(
    registry_type: str,
    image: str,
    registry_url: str | None = None,
    username: str | None = None,
    password: str | None = None,
    region: str | None = None,
    confirmed: bool = False,
    gateway_id: str | None = None,
) -> dict:
    """
    Delete an image tag from a container registry. Destructive — requires confirmed=True.

    Permanently removes the specified tag. The underlying image layers are deleted
    only if no other tag references them. Requires operator role in VibOps.

    Write operation — recorded in the audit log.

    Args:
        registry_type: Registry backend — "harbor", "ecr", or "gar".
        image: Image name with tag to delete (e.g. "myproject/myapp:old-tag").
        registry_url: Harbor base URL or ECR registry URI.
        username: Harbor username or registry token username.
        password: Harbor password or registry token.
        region: AWS region (ECR only).
        confirmed: Must be True to proceed. Pass False (default) for a dry-run preview.
        gateway_id: Gateway UUID for the target site.
    """
    payload: dict = {
        "registry_type": registry_type,
        "image": image,
        "confirmed": confirmed,
    }
    if registry_url:
        payload["registry_url"] = registry_url
    if username:
        payload["username"] = username
    if password:
        payload["password"] = password
    if region:
        payload["region"] = region
    return await _run_job_sync("registry_delete_tag", payload, timeout=30, gateway_id=gateway_id)


# ── VM / Hypervisor actions ──────────────────────────────────────────────────

async def proxmox_list_vms(
    node: str | None = None,
    status: str = "all",
    gateway_id: str | None = None,
) -> dict:
    """List all VMs on a Proxmox cluster. Filter by node or status (running/stopped/all)."""
    payload: dict = {}
    if node:
        payload["node"] = node
    if status != "all":
        payload["status"] = status
    return await _run_job_sync("proxmox_list_vms", payload, gateway_id=gateway_id)


async def proxmox_start_vm(vmid: int, node: str, gateway_id: str | None = None) -> dict:
    """Start a stopped Proxmox VM."""
    return await _run_job_sync("proxmox_start_vm", {"vmid": vmid, "node": node}, gateway_id=gateway_id)


async def proxmox_stop_vm(vmid: int, node: str, gateway_id: str | None = None) -> dict:
    """Gracefully shutdown a running Proxmox VM."""
    return await _run_job_sync("proxmox_stop_vm", {"vmid": vmid, "node": node}, gateway_id=gateway_id)


async def proxmox_migrate_vm(
    vmid: int, node: str, target: str,
    online: bool = True, gateway_id: str | None = None,
) -> dict:
    """Live-migrate a Proxmox VM to another node."""
    return await _run_job_sync("proxmox_migrate_vm", {
        "vmid": vmid, "node": node, "target": target, "online": online,
    }, gateway_id=gateway_id)


async def proxmox_create_snapshot(vmid: int, node: str, name: str, gateway_id: str | None = None) -> dict:
    """Create a snapshot of a Proxmox VM."""
    return await _run_job_sync("proxmox_create_snapshot", {
        "vmid": vmid, "node": node, "name": name,
    }, gateway_id=gateway_id)


async def xo_list_vms(power_state: str = "all", gateway_id: str | None = None) -> dict:
    """List all VMs on XCP-ng pools managed by Xen Orchestra."""
    payload: dict = {}
    if power_state != "all":
        payload["power_state"] = power_state
    return await _run_job_sync("xo_list_vms", payload, gateway_id=gateway_id)


async def xo_start_vm(vm_id: str, gateway_id: str | None = None) -> dict:
    """Start a halted XCP-ng VM."""
    return await _run_job_sync("xo_start_vm", {"vm_id": vm_id}, gateway_id=gateway_id)


async def xo_stop_vm(vm_id: str, gateway_id: str | None = None) -> dict:
    """Cleanly shutdown a running XCP-ng VM."""
    return await _run_job_sync("xo_stop_vm", {"vm_id": vm_id}, gateway_id=gateway_id)


async def xo_migrate_vm(vm_id: str, target_host_id: str, gateway_id: str | None = None) -> dict:
    """Live-migrate an XCP-ng VM to another host."""
    return await _run_job_sync("xo_migrate_vm", {
        "vm_id": vm_id, "target_host_id": target_host_id,
    }, gateway_id=gateway_id)


async def xo_snapshot_vm(vm_id: str, name: str, gateway_id: str | None = None) -> dict:
    """Create a snapshot of an XCP-ng VM."""
    return await _run_job_sync("xo_snapshot_vm", {"vm_id": vm_id, "name": name}, gateway_id=gateway_id)


# ── XO V2V Migration + Backup + Storage ─────────────────────────────────────

async def xo_v2v_list_esxi(gateway_id: str | None = None) -> dict:
    """
    List ESXi hosts configured in Xen Orchestra for V2V migration.

    Returns the ESXi servers that XO can connect to for importing VMware VMs
    into XCP-ng. Add ESXi servers in XO → Settings → Servers.

    Args:
        gateway_id: Target gateway (optional).
    """
    return await _run_job_sync("xo_v2v_list_esxi", {}, gateway_id=gateway_id)


async def xo_v2v_list_vmware_vms(esxi_id: str, gateway_id: str | None = None) -> dict:
    """
    List VMs on a VMware ESXi host available for V2V migration to XCP-ng.

    Args:
        esxi_id: ESXi server ID (from xo_v2v_list_esxi).
        gateway_id: Target gateway (optional).
    """
    return await _run_job_sync("xo_v2v_list_vmware_vms", {"esxi_id": esxi_id}, gateway_id=gateway_id)


async def xo_v2v_migrate(
    esxi_id: str,
    vm_name: str,
    target_sr: str | None = None,
    target_network: str | None = None,
    gateway_id: str | None = None,
) -> dict:
    """
    Migrate a VM from VMware ESXi to XCP-ng using V2V warm migration.

    Warm migration streams disk data while the source VM is still running,
    then performs a brief cutover (seconds of downtime). Works with all
    ESXi versions including VMFS6 and VSAN.

    Write operation — recorded in the audit log.

    Args:
        esxi_id: Source ESXi server ID.
        vm_name: Name of the VM to migrate on ESXi.
        target_sr: Target storage repository UUID on XCP-ng (optional).
        target_network: Target network UUID on XCP-ng (optional).
        gateway_id: Target gateway (optional).
    """
    payload: dict = {"esxi_id": esxi_id, "vm_name": vm_name, "confirmed": True}
    if target_sr:
        payload["target_sr"] = target_sr
    if target_network:
        payload["target_network"] = target_network
    return await _run_job_sync("xo_v2v_migrate", payload, gateway_id=gateway_id)


async def xo_v2v_status(task_id: str, gateway_id: str | None = None) -> dict:
    """
    Check the status of a running V2V migration (progress %, phase, ETA).

    Args:
        task_id: Migration task ID (returned by xo_v2v_migrate).
        gateway_id: Target gateway (optional).
    """
    return await _run_job_sync("xo_v2v_status", {"task_id": task_id}, gateway_id=gateway_id)


async def xo_list_backups(gateway_id: str | None = None) -> dict:
    """
    List backup jobs configured in Xen Orchestra.

    Shows job name, mode (full, delta, disaster recovery), and enabled status.

    Args:
        gateway_id: Target gateway (optional).
    """
    return await _run_job_sync("xo_list_backups", {}, gateway_id=gateway_id)


async def xo_run_backup(job_id: str, gateway_id: str | None = None) -> dict:
    """
    Trigger a backup job immediately.

    Write operation — recorded in the audit log.

    Args:
        job_id: Backup job ID (from xo_list_backups).
        gateway_id: Target gateway (optional).
    """
    return await _run_job_sync("xo_run_backup", {"job_id": job_id, "confirmed": True}, gateway_id=gateway_id)


async def xo_restore_backup(
    backup_id: str,
    target_sr: str | None = None,
    gateway_id: str | None = None,
) -> dict:
    """
    Restore a VM from an XO backup.

    Write operation — recorded in the audit log.

    Args:
        backup_id: Backup ID to restore.
        target_sr: Target storage repository UUID (optional).
        gateway_id: Target gateway (optional).
    """
    payload: dict = {"backup_id": backup_id, "confirmed": True}
    if target_sr:
        payload["target_sr"] = target_sr
    return await _run_job_sync("xo_restore_backup", payload, gateway_id=gateway_id)


async def xo_list_srs(gateway_id: str | None = None) -> dict:
    """
    List storage repositories (SRs) across all XCP-ng pools.

    Returns capacity, usage, free space and usage percentage for each SR.

    Args:
        gateway_id: Target gateway (optional).
    """
    return await _run_job_sync("xo_list_srs", {}, gateway_id=gateway_id)


async def xo_list_tasks(gateway_id: str | None = None) -> dict:
    """
    List running and recent tasks in Xen Orchestra.

    Shows migrations, backups, snapshots, and other operations in progress
    with their status and progress percentage.

    Args:
        gateway_id: Target gateway (optional).
    """
    return await _run_job_sync("xo_list_tasks", {}, gateway_id=gateway_id)


async def xo_rolling_pool_update(pool_id: str, gateway_id: str | None = None) -> dict:
    """
    Start a rolling pool update — patches all XCP-ng hosts one by one.

    VMs are automatically live-migrated to other hosts before each host
    is patched and rebooted. Zero downtime for running workloads.

    Write operation — recorded in the audit log.

    Args:
        pool_id: XCP-ng pool UUID (from xo_list_pools).
        gateway_id: Target gateway (optional).
    """
    return await _run_job_sync("xo_rolling_pool_update", {"pool_id": pool_id, "confirmed": True}, gateway_id=gateway_id)


# ── VMware vSphere actions ───────────────────────────────────────────────────

async def vsphere_list_vms(
    power_state: str = "all",
    datacenter: str | None = None,
    cluster: str | None = None,
    gateway_id: str | None = None,
) -> dict:
    """List all VMs in the vCenter inventory. Filter by power_state (all/poweredOn/poweredOff/suspended), datacenter, or cluster."""
    payload: dict = {}
    if power_state != "all":
        payload["power_state"] = power_state
    if datacenter:
        payload["datacenter"] = datacenter
    if cluster:
        payload["cluster"] = cluster
    return await _run_job_sync("vsphere_list_vms", payload, gateway_id=gateway_id)


async def vsphere_get_vm(name: str, gateway_id: str | None = None) -> dict:
    """Get detailed information about a specific vSphere VM by name."""
    return await _run_job_sync("vsphere_get_vm", {"name": name}, gateway_id=gateway_id)


async def vsphere_start_vm(name: str, gateway_id: str | None = None) -> dict:
    """Power on a vSphere VM."""
    return await _run_job_sync("vsphere_start_vm", {"name": name}, gateway_id=gateway_id)


async def vsphere_stop_vm(
    name: str,
    force: bool = False,
    gateway_id: str | None = None,
) -> dict:
    """Shut down a vSphere VM. Attempts guest shutdown via VMware Tools by default; set force=True for immediate hard power-off."""
    return await _run_job_sync("vsphere_stop_vm", {"name": name, "force": force}, gateway_id=gateway_id)


async def vsphere_restart_vm(
    name: str,
    force: bool = False,
    gateway_id: str | None = None,
) -> dict:
    """Restart a vSphere VM. Attempts guest reboot via VMware Tools by default; set force=True for immediate hard reset."""
    return await _run_job_sync("vsphere_restart_vm", {"name": name, "force": force}, gateway_id=gateway_id)


async def vsphere_migrate_vm(
    name: str,
    target_host: str,
    dry_run: bool = False,
    gateway_id: str | None = None,
) -> dict:
    """Live-migrate (vMotion) a vSphere VM to another ESXi host. Set dry_run=True to validate without moving."""
    return await _run_job_sync("vsphere_migrate_vm", {
        "name": name, "target_host": target_host, "dry_run": dry_run,
    }, gateway_id=gateway_id)


async def vsphere_create_snapshot(
    name: str,
    snapshot_name: str,
    description: str = "",
    memory: bool = False,
    gateway_id: str | None = None,
) -> dict:
    """Create a snapshot of a vSphere VM. Quiescing is attempted automatically when VMware Tools is running."""
    return await _run_job_sync("vsphere_create_snapshot", {
        "name": name, "snapshot_name": snapshot_name,
        "description": description, "memory": memory,
    }, gateway_id=gateway_id)


async def vsphere_list_hosts(
    datacenter: str | None = None,
    cluster: str | None = None,
    gateway_id: str | None = None,
) -> dict:
    """List all ESXi hosts in the vCenter inventory with CPU, memory, and connection state."""
    payload: dict = {}
    if datacenter:
        payload["datacenter"] = datacenter
    if cluster:
        payload["cluster"] = cluster
    return await _run_job_sync("vsphere_list_hosts", payload, gateway_id=gateway_id)


async def vsphere_get_vm_metrics(name: str, gateway_id: str | None = None) -> dict:
    """Get real-time CPU, memory, disk, and network metrics for a vSphere VM."""
    return await _run_job_sync("vsphere_get_vm_metrics", {"name": name}, gateway_id=gateway_id)


# ── HPE VME (Morpheus) ──────────────────────────────────────────────────────

async def vme_list_instances(
    status: str = "all",
    cloud: str | None = None,
    gateway_id: str | None = None,
) -> dict:
    """
    List all VMs managed by HPE VM Essentials (Morpheus).

    Returns name, status, cloud/zone, service plan, CPU and memory for each
    instance. HPE VME manages both KVM-native VMs and imported VMware VMs
    from the same console.

    Args:
        status: Filter by VM status — "running", "stopped", or "all" (default).
        cloud: Filter by cloud/zone name (optional).
        gateway_id: Target gateway (optional if only one VME gateway exists).
    """
    payload: dict = {}
    if status != "all":
        payload["status"] = status
    if cloud:
        payload["cloud"] = cloud
    return await _run_job_sync("vme_list_instances", payload, gateway_id=gateway_id)


async def vme_get_instance(instance_id: int, gateway_id: str | None = None) -> dict:
    """
    Get detailed status and configuration of a specific HPE VME instance.

    Returns CPU, memory, disk, network, cloud assignment, service plan,
    creation date and IP address.

    Args:
        instance_id: Morpheus instance ID (from vme_list_instances).
        gateway_id: Target gateway (optional).
    """
    return await _run_job_sync("vme_get_instance", {"instance_id": instance_id}, gateway_id=gateway_id)


async def vme_list_servers(cloud: str | None = None, gateway_id: str | None = None) -> dict:
    """
    List all physical hosts managed by HPE VME with CPU, memory and status.

    Args:
        cloud: Filter by cloud/zone name (optional).
        gateway_id: Target gateway (optional).
    """
    payload: dict = {}
    if cloud:
        payload["cloud"] = cloud
    return await _run_job_sync("vme_list_servers", payload, gateway_id=gateway_id)


async def vme_list_clouds(gateway_id: str | None = None) -> dict:
    """
    List all clouds/zones configured in HPE VME.

    A cloud in Morpheus represents a hypervisor target: KVM (VME native),
    VMware vSphere, or any other supported provider. This shows what
    infrastructure VME is managing.

    Args:
        gateway_id: Target gateway (optional).
    """
    return await _run_job_sync("vme_list_clouds", {}, gateway_id=gateway_id)


async def vme_start_instance(instance_id: int, gateway_id: str | None = None) -> dict:
    """
    Start a stopped HPE VME instance.

    Write operation — recorded in the audit log.

    Args:
        instance_id: Morpheus instance ID.
        gateway_id: Target gateway (optional).
    """
    return await _run_job_sync("vme_start_instance", {"instance_id": instance_id}, gateway_id=gateway_id)


async def vme_stop_instance(instance_id: int, gateway_id: str | None = None) -> dict:
    """
    Stop a running HPE VME instance (graceful shutdown).

    Write operation — recorded in the audit log.

    Args:
        instance_id: Morpheus instance ID.
        gateway_id: Target gateway (optional).
    """
    return await _run_job_sync("vme_stop_instance", {"instance_id": instance_id}, gateway_id=gateway_id)


async def vme_restart_instance(instance_id: int, gateway_id: str | None = None) -> dict:
    """
    Restart an HPE VME instance.

    Write operation — recorded in the audit log.

    Args:
        instance_id: Morpheus instance ID.
        gateway_id: Target gateway (optional).
    """
    return await _run_job_sync("vme_restart_instance", {"instance_id": instance_id}, gateway_id=gateway_id)


async def vme_create_snapshot(instance_id: int, name: str, gateway_id: str | None = None) -> dict:
    """
    Create a snapshot of an HPE VME instance. Use before migrations or risky changes.

    Write operation — recorded in the audit log.

    Args:
        instance_id: Morpheus instance ID.
        name: Snapshot name (e.g. "pre-migration-2026-09-09").
        gateway_id: Target gateway (optional).
    """
    return await _run_job_sync("vme_create_snapshot", {"instance_id": instance_id, "name": name}, gateway_id=gateway_id)


async def vme_list_snapshots(instance_id: int, gateway_id: str | None = None) -> dict:
    """
    List all snapshots for an HPE VME instance.

    Args:
        instance_id: Morpheus instance ID.
        gateway_id: Target gateway (optional).
    """
    return await _run_job_sync("vme_list_snapshots", {"instance_id": instance_id}, gateway_id=gateway_id)


async def vme_convert_image(image_id: int, format: str, gateway_id: str | None = None) -> dict:
    """
    Convert a virtual image to a different disk format.

    Key tool for VMware-to-VME migrations: converts VMDK images to QCOW2
    (KVM-native format) without manual intervention. The conversion runs
    asynchronously on the Morpheus appliance.

    Write operation — recorded in the audit log.

    Args:
        image_id: Virtual image ID (from vme_list_virtual_images).
        format: Target format — "qcow2", "vmdk", "raw", or "vhd".
        gateway_id: Target gateway (optional).
    """
    return await _run_job_sync("vme_convert_image", {"image_id": image_id, "format": format}, gateway_id=gateway_id)


async def vme_list_virtual_images(image_type: str | None = None, gateway_id: str | None = None) -> dict:
    """
    List available virtual images in HPE VME (templates, ISOs, uploaded images).

    Use before vme_convert_image to find the image ID of a VMware VMDK
    that needs conversion for migration.

    Args:
        image_type: Filter by type (optional).
        gateway_id: Target gateway (optional).
    """
    payload: dict = {}
    if image_type:
        payload["image_type"] = image_type
    return await _run_job_sync("vme_list_virtual_images", payload, gateway_id=gateway_id)


async def vme_detect_vm_waste(stopped_days_threshold: int = 7, gateway_id: str | None = None) -> dict:
    """
    Detect VM waste in HPE VME: stopped instances and over-provisioned VMs.

    Returns actionable recommendations with severity levels. Use for FinOps
    reviews and cost optimisation.

    Args:
        stopped_days_threshold: Flag VMs stopped for more than N days (default: 7).
        gateway_id: Target gateway (optional).
    """
    return await _run_job_sync("vme_detect_vm_waste", {"stopped_days_threshold": stopped_days_threshold}, gateway_id=gateway_id)


async def vme_get_activity(max: int = 50, gateway_id: str | None = None) -> dict:
    """
    Get recent activity/audit log from HPE VME — provisioning, changes, logins.

    Args:
        max: Max results (default: 50).
        gateway_id: Target gateway (optional).
    """
    return await _run_job_sync("vme_get_activity", {"max": max}, gateway_id=gateway_id)


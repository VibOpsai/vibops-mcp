"""
Observation tools (read-only) — 15 tools.

These tools let the LLM inspect the state of the infrastructure
without triggering any side effects.
"""
from vibops_mcp import client


async def list_clusters() -> dict:
    """List all Kubernetes clusters and their GPU utilisation."""
    return await client.get("/api/v1/gateways")


async def get_cluster_deployments(cluster_name: str, namespace: str | None = None) -> dict:
    """
    Return live Kubernetes deployment status for a cluster.
    Polls the cluster via the VibOps gateway (up to 20 s).

    Args:
        cluster_name: Name of the kubectl context / Kind cluster.
        namespace: Filter to a specific namespace (optional).
    """
    params = {}
    if namespace:
        params["namespace"] = namespace
    return await client.get(f"/api/v1/clusters/{cluster_name}/deployments", params=params)


async def list_jobs(
    status: str | None = None,
    action: str | None = None,
    limit: int = 20,
) -> dict:
    """
    List recent jobs (operations executed on the infrastructure).

    Args:
        status: Filter by status — pending | running | success | failed.
        action: Filter by action name, e.g. scale_cluster, deploy_model.
        limit: Maximum number of jobs to return (default 20, max 100).
    """
    params: dict = {"limit": min(limit, 100)}
    if status:
        params["status"] = status
    if action:
        params["action"] = action
    return await client.get("/api/v1/jobs", params=params)


async def get_job(job_id: str) -> dict:
    """
    Get the details and result of a specific job.

    Args:
        job_id: UUID of the job.
    """
    job = await client.get(f"/api/v1/jobs/{job_id}")
    # Truncate logs to avoid token overflow (helm/kubectl output can be hundreds of KB)
    if job.get("logs") and len(job["logs"]) > 1000:
        job["logs"] = job["logs"][:1000] + f" ... [{len(job['logs']) - 1000} chars truncated]"
    return job


async def get_gpu_metrics(hours: int = 24) -> dict:
    """
    Return hourly GPU utilisation time-series for the last N hours.
    Aggregated across all clusters for the organisation.

    Args:
        hours: Look-back window in hours (default 24, max 168).
    """
    return await client.get("/api/v1/metrics/gpu", params={"hours": hours})


async def get_workload_breakdown(hours: int = 24) -> dict:
    """
    Return the breakdown of jobs by workload type for the last N hours.
    Types: inference | training | observation | operations | gitops | maintenance | other.

    Args:
        hours: Look-back window in hours (default 24, max 168).
    """
    return await client.get("/api/v1/metrics/workloads", params={"hours": hours})


async def get_mttr(hours: int = 168) -> dict:
    """
    Return Mean Time To Resolve GPU alerts per cluster and severity.

    Args:
        hours: Look-back window in hours (default 168 = 7 days).
    """
    return await client.get("/api/v1/metrics/mttr", params={"hours": hours})


async def get_cost_estimate(hours: int = 24) -> dict:
    """
    Return estimated GPU spend for the last N hours.
    Requires GPU cost rates to be configured per cluster.

    Args:
        hours: Look-back window in hours (default 24).
    """
    return await client.get("/api/v1/metrics/cost", params={"hours": hours})


async def list_gateways() -> dict:
    """List all registered VibOps gateways (remote agents) and their status."""
    return await client.get("/api/v1/gateways")


async def list_alerts(severity: str | None = None, resolved: bool | None = None) -> dict:
    """
    List GPU alerts.

    Args:
        severity: Filter by severity — warning | critical.
        resolved: True to show only resolved alerts, False for open alerts.
    """
    params: dict = {}
    if severity:
        params["severity"] = severity
    if resolved is not None:
        params["resolved"] = str(resolved).lower()
    return await client.get("/api/v1/alerts", params=params)


async def list_secrets(search: str | None = None) -> dict:
    """
    List available secrets (names and metadata only, never values).

    Args:
        search: Filter secrets by name (optional).
    """
    params = {"search": search} if search else {}
    return await client.get("/api/v1/secrets", params=params)


async def list_providers() -> dict:
    """List configured custom AI/GPU cloud providers."""
    return await client.get("/api/v1/providers")


async def list_pipelines(limit: int = 10) -> dict:
    """
    List automation pipelines (sequences of jobs).

    Args:
        limit: Maximum number of pipelines to return (default: 10, max: 200).
    """
    return await client.get("/api/v1/pipelines", params={"limit": limit})


async def get_cluster_rate(cluster_name: str) -> dict:
    """
    Get the configured GPU cost rate for a cluster.

    Args:
        cluster_name: Name of the cluster.
    """
    return await client.get(f"/api/v1/clusters/{cluster_name}/rate")


async def list_kubectl_contexts() -> dict:
    """List available kubectl contexts from the kubeconfig."""
    return await client.get("/api/v1/clusters/contexts")

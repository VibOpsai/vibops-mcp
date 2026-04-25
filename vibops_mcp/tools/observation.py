"""
Observation tools (read-only) — 15 tools.

These tools let the LLM inspect the state of the infrastructure
without triggering any side effects.
"""
from vibops_mcp import client


async def list_clusters() -> dict:
    """
    List all clusters registered in VibOps, with current GPU utilisation summary.

    Start with this tool when the user asks about available clusters or general
    fleet status. For raw kubeconfig contexts (including clusters not yet registered
    in VibOps), use list_kubectl_contexts instead.
    """
    return await client.get("/api/v1/gateways")


async def get_cluster_deployments(cluster_name: str, namespace: str | None = None) -> dict:
    """
    Return live Kubernetes deployment status for a cluster, including replica counts,
    pod health, and resource usage. Polls the cluster via the VibOps gateway (up to 20s).

    Call this when investigating deployment health, replica counts, or pod failures.

    Args:
        cluster_name: Name of the cluster as returned by list_clusters.
        namespace: Restrict results to a single namespace (optional).
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
    List recent VibOps operations (scale, deploy, helm, kubectl...).

    A VibOps job is not a Kubernetes Job — it represents any infrastructure operation
    submitted through VibOps. Use get_job to retrieve the full result of a specific
    operation.

    Args:
        status: Filter by status — pending | running | success | failed.
        action: Filter by action type — scale_cluster | deploy_model | helm_upgrade |
                helm_uninstall | kubectl_exec | git_clone.
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
    Return the details and result of a specific VibOps operation.

    Call this to check whether a previously submitted action succeeded or failed,
    and to retrieve its output (kubectl stdout, Helm output, error message).

    Args:
        job_id: Full UUID or short ID (first 8 characters) of the job.
    """
    job = await client.get(f"/api/v1/jobs/{job_id}")
    # Truncate logs to avoid token overflow (helm/kubectl output can be hundreds of KB)
    if job.get("logs") and len(job["logs"]) > 1000:
        job["logs"] = job["logs"][:1000] + f" ... [{len(job['logs']) - 1000} chars truncated]"
    return job


async def get_gpu_metrics(hours: int = 24) -> dict:
    """
    Return hourly GPU utilisation time-series for the last N hours.

    Use this to assess whether GPUs are idle, saturated, or trending toward failure.
    For cost implications of that utilisation, use get_cost_estimate.
    For a breakdown of what workloads are consuming the GPUs, use get_workload_breakdown.

    Args:
        hours: Look-back window in hours (default 24, max 168).
    """
    return await client.get("/api/v1/metrics/gpu", params={"hours": hours})


async def get_workload_breakdown(hours: int = 24) -> dict:
    """
    Return the distribution of GPU work by workload type for the last N hours.
    Types: inference | training | observation | operations | gitops | maintenance | other.

    Use this to understand what your GPU fleet is being used for.
    For raw utilisation percentages, use get_gpu_metrics.

    Args:
        hours: Look-back window in hours (default 24).
    """
    return await client.get("/api/v1/metrics/workloads", params={"hours": hours})


async def get_mttr(hours: int = 168) -> dict:
    """
    Return Mean Time To Resolve (MTTR) for GPU alerts, broken down by cluster and severity.

    Use this to assess operational reliability and incident response speed over time.

    Args:
        hours: Look-back window in hours (default 168 = 7 days).
    """
    return await client.get("/api/v1/metrics/mttr", params={"hours": hours})


async def get_cost_estimate(hours: int = 24) -> dict:
    """
    Return estimated GPU spend for the last N hours.

    Requires cost rates to be configured per cluster (use set_cluster_rate).
    Returns null costs if no rates are configured.
    For GPU utilisation data without cost, use get_gpu_metrics.

    Args:
        hours: Look-back window in hours (default 24).
    """
    return await client.get("/api/v1/metrics/cost", params={"hours": hours})


async def list_gateways() -> dict:
    """
    List all registered VibOps gateways and their connection status.

    A gateway is a remote agent installed in the customer infrastructure that bridges
    VibOps Core to local Kubernetes clusters and cloud APIs.
    To list clusters managed by those gateways, use list_clusters.
    """
    return await client.get("/api/v1/gateways")


async def list_alerts(severity: str | None = None, resolved: bool | None = None) -> dict:
    """
    List GPU infrastructure alerts (thermal throttling, OOM kills, low utilisation,
    hardware errors).

    Call this when investigating performance degradation, unexpected restarts, or before
    making scaling decisions. Open alerts (resolved=False) indicate active issues.

    Args:
        severity: Filter by severity — warning | critical.
        resolved: False for active alerts, True for resolved alerts. Omit for all.
    """
    params: dict = {}
    if severity:
        params["severity"] = severity
    if resolved is not None:
        params["resolved"] = str(resolved).lower()
    return await client.get("/api/v1/alerts", params=params)


async def list_secrets(search: str | None = None) -> dict:
    """
    List secret names and metadata stored in the VibOps vault. Values are never returned.

    Use this to check which credentials are available before submitting jobs that
    require them. To store a new secret, use create_secret.

    Args:
        search: Filter by name (optional substring match).
    """
    params = {"search": search} if search else {}
    return await client.get("/api/v1/secrets", params=params)


async def list_providers() -> dict:
    """
    List configured custom AI and GPU cloud providers (e.g. DGX Cloud, Scaleway, Outscale).

    Providers extend VibOps with additional connectors beyond the built-in ones.
    """
    return await client.get("/api/v1/providers")


async def list_pipelines(limit: int = 10) -> dict:
    """
    List automation pipelines — named sequences of jobs that execute in order.

    A pipeline is distinct from a single job: it orchestrates multiple operations
    (e.g. deploy to staging → health check → promote to production).
    To trigger a pipeline, use trigger_pipeline with its UUID.

    Args:
        limit: Maximum number of pipelines to return (default 10, max 200).
    """
    return await client.get("/api/v1/pipelines", params={"limit": limit})


async def get_cluster_rate(cluster_name: str) -> dict:
    """
    Return the configured GPU cost rate for a cluster.

    Used to verify the rate before interpreting get_cost_estimate results.
    To set or update the rate, use set_cluster_rate.

    Args:
        cluster_name: Name of the cluster.
    """
    return await client.get(f"/api/v1/clusters/{cluster_name}/rate")


async def list_kubectl_contexts() -> dict:
    """
    List raw kubectl contexts from the gateway's kubeconfig.

    Use this only to discover clusters not yet registered in VibOps, or to debug
    context name mismatches. For normal cluster discovery, use list_clusters.
    """
    return await client.get("/api/v1/clusters/contexts")

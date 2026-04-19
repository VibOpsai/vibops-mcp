"""
VibOps MCP server — entry point.

Run via:
  vibops-mcp              (after pip install vibops-mcp)
  python -m vibops_mcp    (from source)

Required environment variables:
  VIBOPS_URL    — base URL of your VibOps instance
  VIBOPS_TOKEN  — API token (VibOps → Settings → API Tokens)

Claude Desktop configuration (~/.config/claude/claude_desktop_config.json):
  {
    "mcpServers": {
      "vibops": {
        "command": "vibops-mcp",
        "env": {
          "VIBOPS_URL": "https://vibops.example.com",
          "VIBOPS_TOKEN": "your-token-here"
        }
      }
    }
  }
"""
from mcp.server.fastmcp import FastMCP

from vibops_mcp.tools import observation, actions, config

mcp = FastMCP(
    name="vibops",
    instructions=(
        "You are connected to a VibOps instance that manages GPU infrastructure. "
        "Use the observation tools to inspect cluster state, GPU metrics, jobs, and cost. "
        "Use the action tools to deploy models, scale workloads, and run Helm or kubectl operations. "
        "Use the configuration tools to set cost rates and manage gateways. "
        "All write operations are recorded in the VibOps audit log."
    ),
)


# ── Observation tools (15) ─────────────────────────────────────────────────────

@mcp.tool()
async def list_clusters() -> dict:
    """List all Kubernetes clusters and their GPU utilisation."""
    return await observation.list_clusters()


@mcp.tool()
async def get_cluster_deployments(cluster_name: str, namespace: str | None = None) -> dict:
    """
    Return live Kubernetes deployment status for a cluster.
    Polls the cluster via the VibOps gateway (up to 20 s).

    Args:
        cluster_name: Name of the kubectl context / Kind cluster.
        namespace: Filter to a specific namespace (optional).
    """
    return await observation.get_cluster_deployments(cluster_name, namespace)


@mcp.tool()
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
    return await observation.list_jobs(status, action, limit)


@mcp.tool()
async def get_job(job_id: str) -> dict:
    """
    Get the details and result of a specific job.

    Args:
        job_id: UUID of the job.
    """
    return await observation.get_job(job_id)


@mcp.tool()
async def get_gpu_metrics(hours: int = 24) -> dict:
    """
    Return hourly GPU utilisation time-series for the last N hours.

    Args:
        hours: Look-back window in hours (default 24, max 168).
    """
    return await observation.get_gpu_metrics(hours)


@mcp.tool()
async def get_workload_breakdown(hours: int = 24) -> dict:
    """
    Return the breakdown of jobs by workload type for the last N hours.
    Types: inference | training | observation | operations | gitops | maintenance | other.

    Args:
        hours: Look-back window in hours (default 24).
    """
    return await observation.get_workload_breakdown(hours)


@mcp.tool()
async def get_mttr(hours: int = 168) -> dict:
    """
    Return Mean Time To Resolve GPU alerts per cluster and severity.

    Args:
        hours: Look-back window in hours (default 168 = 7 days).
    """
    return await observation.get_mttr(hours)


@mcp.tool()
async def get_cost_estimate(hours: int = 24) -> dict:
    """
    Return estimated GPU spend for the last N hours.
    Requires GPU cost rates to be configured per cluster (use set_cluster_rate).

    Args:
        hours: Look-back window in hours (default 24).
    """
    return await observation.get_cost_estimate(hours)


@mcp.tool()
async def list_gateways() -> dict:
    """List all registered VibOps gateways (remote agents) and their status."""
    return await observation.list_gateways()


@mcp.tool()
async def list_alerts(severity: str | None = None, resolved: bool | None = None) -> dict:
    """
    List GPU alerts.

    Args:
        severity: Filter by severity — warning | critical.
        resolved: True for resolved alerts, False for open alerts.
    """
    return await observation.list_alerts(severity, resolved)


@mcp.tool()
async def list_secrets(search: str | None = None) -> dict:
    """
    List available secrets (names and metadata only, never values).

    Args:
        search: Filter secrets by name (optional).
    """
    return await observation.list_secrets(search)


@mcp.tool()
async def list_providers() -> dict:
    """List configured custom AI/GPU cloud providers."""
    return await observation.list_providers()


@mcp.tool()
async def list_pipelines(limit: int = 10) -> dict:
    """
    List automation pipelines (sequences of jobs).

    Args:
        limit: Maximum number of pipelines to return (default: 10, max: 200).
    """
    return await observation.list_pipelines(limit=limit)


@mcp.tool()
async def get_cluster_rate(cluster_name: str) -> dict:
    """
    Get the configured GPU cost rate for a cluster.

    Args:
        cluster_name: Name of the cluster.
    """
    return await observation.get_cluster_rate(cluster_name)


@mcp.tool()
async def list_kubectl_contexts() -> dict:
    """List available kubectl contexts from the kubeconfig."""
    return await observation.list_kubectl_contexts()


# ── Action tools (8) ──────────────────────────────────────────────────────────

@mcp.tool()
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
    return await actions.scale_cluster(cluster_name, replicas, deployment_name, namespace)


@mcp.tool()
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
    return await actions.deploy_model(cluster_name, model_name, namespace, replicas, extra)


@mcp.tool()
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
    return await actions.helm_upgrade(cluster_name, release_name, chart, namespace, values)


@mcp.tool()
async def helm_uninstall(cluster_name: str, release_name: str, namespace: str = "default") -> dict:
    """
    Uninstall a Helm release from a cluster.

    Args:
        cluster_name: Target cluster.
        release_name: Helm release to remove.
        namespace: Kubernetes namespace (default: 'default').
    """
    return await actions.helm_uninstall(cluster_name, release_name, namespace)


@mcp.tool()
async def run_kubectl(cluster_name: str, command: list[str]) -> dict:
    """
    Run an arbitrary kubectl command on a cluster.
    Example command: ["get", "pods", "-n", "default"]

    Args:
        cluster_name: Target cluster.
        command: kubectl arguments as a list (without 'kubectl' prefix).
    """
    return await actions.run_kubectl(cluster_name, command)


@mcp.tool()
async def git_clone(repo_url: str, branch: str = "main", cluster_name: str | None = None) -> dict:
    """
    Clone a git repository (pull manifests or model configs).

    Args:
        repo_url: Git repository URL.
        branch: Branch to clone (default: main).
        cluster_name: Target cluster if repo contains K8s manifests to apply.
    """
    return await actions.git_clone(repo_url, branch, cluster_name)


@mcp.tool()
async def create_secret(name: str, value: str, description: str | None = None) -> dict:
    """
    Store an encrypted secret in the VibOps vault.

    Args:
        name: Secret name (used to reference it in jobs).
        value: Secret value (stored encrypted, never logged).
        description: Optional human-readable description.
    """
    return await actions.create_secret(name, value, description)


@mcp.tool()
async def trigger_pipeline(pipeline_id: str, payload: dict | None = None) -> dict:
    """
    Manually trigger an automation pipeline.

    Args:
        pipeline_id: UUID of the pipeline to trigger.
        payload: Optional input payload for the pipeline.
    """
    return await actions.trigger_pipeline(pipeline_id, payload)


# ── Configuration tools (3) ───────────────────────────────────────────────────

@mcp.tool()
async def set_cluster_rate(cluster_name: str, rate_per_gpu_hour: float, currency: str = "USD") -> dict:
    """
    Set the GPU cost rate for a cluster (organisation admin only).

    Args:
        cluster_name: Name of the cluster.
        rate_per_gpu_hour: Cost per GPU per hour (e.g. 2.50).
        currency: Currency code (default: USD).
    """
    return await config.set_cluster_rate(cluster_name, rate_per_gpu_hour, currency)


@mcp.tool()
async def register_gateway(name: str, description: str | None = None, clusters: list[str] | None = None) -> dict:
    """
    Register a new VibOps gateway (remote agent).
    Returns a one-time token to configure the gateway with.

    Args:
        name: Human-readable name for the gateway.
        description: Optional description (location, purpose…).
        clusters: List of cluster names this gateway manages.
    """
    return await config.register_gateway(name, description, clusters)


@mcp.tool()
async def delete_gateway(gateway_id: str) -> dict:
    """
    Revoke a VibOps gateway and its token.

    Args:
        gateway_id: UUID of the gateway to delete.
    """
    return await config.delete_gateway(gateway_id)


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()

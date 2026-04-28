"""
Configuration tools — 3 tools.

These tools let the LLM read and update VibOps configuration.
"""
from vibops_mcp import client


async def set_cluster_rate(cluster_name: str, rate_per_gpu_hour: float, currency: str = "USD") -> dict:
    """
    Set the GPU cost rate for a cluster.

    Required to enable cost estimates (get_cost_estimate). Can be updated at any time.
    Requires organisation admin role.

    Write operation — recorded in the audit log.

    Args:
        cluster_name: Name of the cluster.
        rate_per_gpu_hour: Cost per GPU per hour (e.g. 2.50 for $2.50/GPU/hr).
        currency: ISO 4217 currency code (default: USD).
    """
    return await client.post(f"/api/v1/clusters/{cluster_name}/rate", body={
        "rate_per_gpu_hour": rate_per_gpu_hour,
        "currency": currency.upper(),
    })


async def register_gateway(name: str, description: str | None = None, clusters: list[str] | None = None) -> dict:
    """
    Register a new VibOps gateway (remote agent).

    Returns a one-time bearer token to configure the gateway with — store it
    immediately, it cannot be retrieved again.

    Write operation — recorded in the audit log.

    Args:
        name: Human-readable name for the gateway (e.g. 'prod-vpc', 'eu-west-dc').
        description: Optional description of the gateway's location or purpose.
        clusters: List of cluster names this gateway will manage.
    """
    body: dict = {"name": name, "clusters": clusters or []}
    if description:
        body["description"] = description
    return await client.post("/api/v1/gateways", body=body)


async def delete_gateway(gateway_id: str) -> dict:
    """
    Revoke a VibOps gateway and invalidate its token.

    The gateway will immediately lose the ability to poll for jobs.
    Existing jobs assigned to this gateway will fail.

    Write operation — recorded in the audit log.

    Args:
        gateway_id: UUID of the gateway to revoke.
    """
    return await client.delete(f"/api/v1/gateways/{gateway_id}")

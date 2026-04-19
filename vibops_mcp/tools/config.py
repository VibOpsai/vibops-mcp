"""
Configuration tools — 3 tools.

These tools let the LLM read and update VibOps configuration.
"""
from vibops_mcp import client


async def set_cluster_rate(cluster_name: str, rate_per_gpu_hour: float, currency: str = "USD") -> dict:
    """
    Set the GPU cost rate for a cluster (organisation admin only).
    Used to calculate cost estimates in get_cost_estimate.

    Args:
        cluster_name: Name of the cluster.
        rate_per_gpu_hour: Cost per GPU per hour (e.g. 2.50).
        currency: Currency code (default: USD).
    """
    return await client.post(f"/api/v1/clusters/{cluster_name}/rate", body={
        "rate_per_gpu_hour": rate_per_gpu_hour,
        "currency": currency.upper(),
    })


async def register_gateway(name: str, description: str | None = None, clusters: list[str] | None = None) -> dict:
    """
    Register a new VibOps gateway (remote agent).
    Returns a one-time token to configure the gateway with.

    Args:
        name: Human-readable name for the gateway.
        description: Optional description (location, purpose…).
        clusters: List of cluster names this gateway manages.
    """
    body: dict = {"name": name, "clusters": clusters or []}
    if description:
        body["description"] = description
    return await client.post("/api/v1/gateways", body=body)


async def delete_gateway(gateway_id: str) -> dict:
    """
    Revoke a VibOps gateway and its token.

    Args:
        gateway_id: UUID of the gateway to delete.
    """
    return await client.delete(f"/api/v1/gateways/{gateway_id}")

"""
FinOps tools for VibOps MCP.

Covers GPU cost visibility, budget tracking, chargeback reporting and waste
detection. All tools are read-only (no write operations).
"""
from vibops_mcp import client


async def get_budget() -> dict:
    """
    Return the current GPU budget configuration and consumption for the organisation.

    Shows budget limits (tokens, cost in USD/EUR), current consumption for the
    active period, percentage used, and the behaviour configured at the limit
    (queue / throttle / reject). Use set_cluster_rate to configure per-GPU
    hourly rates before relying on cost figures.
    """
    return await client.get("/api/v1/budget")


async def get_chargeback(year: int, month: int) -> dict:
    """
    Return the chargeback report for a given month, broken down by tenant and agent.

    Chargeback allocates GPU costs to cost centres based on elapsed_hours ×
    gpu_count × ClusterRate per workload. Useful for inter-department billing
    or to validate cloud invoices against actual AI workload consumption.

    Args:
        year: Four-digit year (e.g. 2026).
        month: Month number 1–12 (e.g. 5 for May).
    """
    return await client.get(f"/api/v1/chargeback/{year}/{month}")


async def get_spend_trend(days: int = 30) -> dict:
    """
    Return GPU spend trend over the specified number of days.

    Provides daily cost series per cluster and per tenant, enabling detection
    of cost regressions after new deployments. Anomalous spikes are flagged
    automatically. Requires cluster rates to be configured via set_cluster_rate.

    Args:
        days: Lookback window in days (default 30, max 90).
    """
    return await client.get("/api/v1/spend/trend", params={"days": days})


async def get_agent_usage(
    period: str = "30d",
    agent_id: str | None = None,
    team: str | None = None,
    model: str | None = None,
) -> dict:
    """
    Return LLM inference usage aggregated by agent — token consumption, GPU cost,
    and request counts. Use this to understand which AI agents are consuming the
    most inference resources and how costs distribute across teams.

    This is the only tool that bridges agent-level identity with GPU-level cost.
    Typical questions it answers:
    - "Which agent costs the most in GPU this month?"
    - "How much does the pricing agent spend on Llama-70B vs Mistral-7B?"
    - "Which team is over budget on LLM inference?"

    Args:
        period: Lookback period — "7d", "30d", or "mtd" (month-to-date). Default "30d".
        agent_id: Filter to a specific agent (optional).
        team: Filter to a specific team (optional).
        model: Filter to a specific LLM model (optional).
    """
    params: dict = {"period": period}
    if agent_id:
        params["agent_id"] = agent_id
    if team:
        params["team"] = team
    if model:
        params["model"] = model
    return await client.get("/api/v1/finops/agent-usage", params=params)


async def get_agent_usage_detail(agent_id: str) -> dict:
    """
    Return detailed LLM inference usage for a specific agent — daily breakdown,
    model distribution, cost trend, and optimisation recommendations.

    Use after get_agent_usage identifies an agent of interest. Shows:
    - Daily request count, token usage, and cost over the last 30 days
    - Breakdown by LLM model (which models this agent uses and how much each costs)
    - Cost trend (increasing / stable / decreasing)

    Args:
        agent_id: The agent identifier (as reported via X-VibOps-Agent-Id header).
    """
    return await client.get(f"/api/v1/finops/agent-usage/{agent_id}")


async def get_waste_analysis() -> dict:
    """
    Return GPU waste analysis — idle resources consuming budget without doing work.

    Identifies: GPU nodes with <10 % utilisation over the past 24 h, deployments
    with zero jobs in the past 7 days, over-provisioned replicas relative to
    queue depth. Each finding includes an estimated wasted cost and a
    recommended remediation action (scale down, suspend, or reassign).
    """
    return await client.get("/api/v1/waste")

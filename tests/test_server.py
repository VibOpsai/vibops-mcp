"""
Tests for vibops_mcp/server.py

Verifies that all tools are registered on the MCP server with correct names,
and that the server instructions include the routing guide.

Note: argument routing is tested at the tool level in test_actions.py and
test_observation.py — there are no wrappers to test here since tools are
registered directly from tools/*.py.
"""
from vibops_mcp import server


EXPECTED_TOOLS = {
    # Observation (15)
    "list_clusters",
    "get_cluster_deployments",
    "list_jobs",
    "get_job",
    "get_gpu_metrics",
    "get_workload_breakdown",
    "get_mttr",
    "get_cost_estimate",
    "list_gateways",
    "list_alerts",
    "list_secrets",
    "list_providers",
    "list_pipelines",
    "get_cluster_rate",
    "list_kubectl_contexts",
    # Actions (8)
    "scale_deployment",
    "deploy_model",
    "helm_upgrade",
    "helm_uninstall",
    "run_kubectl",
    "git_clone",
    "create_secret",
    "trigger_pipeline",
    # Config (3)
    "set_cluster_rate",
    "register_gateway",
    "delete_gateway",
}


def _registered_tool_names() -> set[str]:
    """Extract the set of registered tool names from the FastMCP instance."""
    # FastMCP stores tools in _tool_manager or similar; fall back to iterating
    try:
        return {name for name in server.mcp._tool_manager._tools}
    except AttributeError:
        pass
    try:
        return {t.name for t in server.mcp.list_tools()}
    except Exception:
        pass
    # Last resort: inspect the tools dict directly
    return set(getattr(server.mcp, "_tools", {}).keys())


def test_all_tools_registered():
    """All 26 expected tools must be registered on the MCP server."""
    registered = _registered_tool_names()
    missing = EXPECTED_TOOLS - registered
    assert not missing, f"Tools not registered: {missing}"


def test_no_unexpected_tools():
    """No extra tools should be registered beyond the expected 26."""
    registered = _registered_tool_names()
    unexpected = registered - EXPECTED_TOOLS
    assert not unexpected, f"Unexpected tools registered: {unexpected}"


def test_scale_deployment_registered_not_scale_cluster():
    """scale_deployment must be registered (renamed from scale_cluster)."""
    registered = _registered_tool_names()
    assert "scale_deployment" in registered
    assert "scale_cluster" not in registered, (
        "scale_cluster was renamed to scale_deployment — old name must not be registered"
    )


def test_server_instructions_contain_routing_guide():
    """MCP instructions must contain the routing guide for correct tool selection."""
    instructions = server.mcp._instructions if hasattr(server.mcp, "_instructions") else ""
    if not instructions:
        # Try alternate attribute names
        instructions = getattr(server.mcp, "instructions", "") or ""
    assert "list_clusters" in instructions
    assert "scale_deployment" in instructions
    assert "run_kubectl" in instructions

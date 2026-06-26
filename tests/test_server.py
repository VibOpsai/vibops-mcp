"""
Tests for vibops_mcp/server.py

Verifies that all tools are registered on the MCP server with correct names,
and that the server instructions include the routing guide.

Note: argument routing is tested at the tool level in test_actions.py,
test_observation.py, test_governance.py and test_finops.py — there are no
wrappers to test here since tools are registered directly from tools/*.py.
"""
from vibops_mcp import server


EXPECTED_TOOLS = {
    # Observation (16)
    "list_clusters",
    "get_cluster_deployments",
    "list_jobs",
    "get_job",
    "get_gpu_metrics",
    "get_workload_breakdown",
    "get_mttr",
    "get_cost_estimate",
    "get_job_metrics",
    "list_gateways",
    "list_alerts",
    "list_secrets",
    "list_providers",
    "list_pipelines",
    "get_cluster_rate",
    "list_kubectl_contexts",
    # Actions (14)
    "scale_deployment",
    "deploy_model",
    "helm_upgrade",
    "helm_uninstall",
    "run_kubectl",
    "git_clone",
    "create_secret",
    "trigger_pipeline",
    "slurm_get_cluster_info",
    "slurm_list_jobs",
    "slurm_get_job_status",
    "slurm_get_job_output",
    "slurm_submit_job",
    "slurm_cancel_job",
    # Config (3)
    "set_cluster_rate",
    "register_gateway",
    "delete_gateway",
    # Actions — Container Registry (4)
    "registry_list_repos",
    "registry_list_tags",
    "registry_check_image",
    "registry_delete_tag",
    # Governance (22)
    "list_anomalies",
    "get_open_anomalies",
    "resolve_anomaly",
    "list_ai_act_controls",
    "get_ai_act_score",
    "update_ai_act_control",
    "list_compliance_reports",
    "generate_compliance_report",
    "get_compliance_report",
    "list_audit_logs",
    "verify_audit_chain",
    "get_policy",
    "update_policy",
    "list_agent_identities",
    "create_agent_identity",
    "rotate_agent_identity",
    "revoke_agent_identity",
    "get_agent_dependency_graph",
    "get_agent_dependencies",
    "list_eval_rubrics",
    "evaluate_job",
    "get_job_evaluations",
    # Governance — Sprint 6 (5)
    "get_ldap_config",
    "update_ldap_config",
    "get_siem_config",
    "update_siem_config",
    "push_to_siem",
    # FinOps (4)
    "get_budget",
    "get_chargeback",
    "get_spend_trend",
    "get_waste_analysis",
}


def _registered_tool_names() -> set[str]:
    """Extract the set of registered tool names from the FastMCP instance."""
    try:
        return {name for name in server.mcp._tool_manager._tools}
    except AttributeError:
        pass
    try:
        return {t.name for t in server.mcp.list_tools()}
    except Exception:
        pass
    return set(getattr(server.mcp, "_tools", {}).keys())


def test_all_tools_registered():
    """All 68 expected tools must be registered on the MCP server."""
    registered = _registered_tool_names()
    missing = EXPECTED_TOOLS - registered
    assert not missing, f"Tools not registered: {missing}"


def test_no_unexpected_tools():
    """No extra tools should be registered beyond the expected 68."""
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
    """MCP instructions must contain routing hints for all major tool groups."""
    instructions = server.mcp._instructions if hasattr(server.mcp, "_instructions") else ""
    if not instructions:
        instructions = getattr(server.mcp, "instructions", "") or ""
    assert "list_clusters" in instructions
    assert "scale_deployment" in instructions
    assert "run_kubectl" in instructions
    assert "get_open_anomalies" in instructions
    assert "get_ai_act_score" in instructions
    assert "generate_compliance_report" in instructions
    assert "verify_audit_chain" in instructions
    assert "get_waste_analysis" in instructions

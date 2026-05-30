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

from vibops_mcp.tools import observation, actions, config, governance, finops

mcp = FastMCP(
    name="vibops",
    instructions=(
        "You are connected to a VibOps instance that manages GPU Kubernetes infrastructure.\n\n"
        "Routing guide:\n"
        "- Start with list_clusters to discover available clusters before taking any action.\n"
        "- list_clusters returns gateway_id per cluster — pass it to action tools when multiple gateways share a cluster name.\n"
        "- For general fleet health, call list_clusters then list_alerts then get_open_anomalies.\n"
        "- To investigate a specific cluster, call get_cluster_deployments.\n"
        "- GPU utilisation: get_gpu_metrics. Cost: get_cost_estimate. Workload types: get_workload_breakdown.\n"
        "- Job health (success rate, latency): get_job_metrics. For individual jobs: get_job or list_jobs.\n"
        "- To scale pods in a deployment, use scale_deployment. Do not use helm or run_kubectl for scaling.\n"
        "- To deploy a model, use deploy_model. For arbitrary Helm charts, use helm_upgrade.\n"
        "- Use run_kubectl only for operations not covered by dedicated tools (get, describe, logs).\n"
        "- Before triggering a pipeline, use list_pipelines to find its UUID.\n"
        "- GPU anomalies (idle, spike, node loss): get_open_anomalies, then resolve_anomaly once fixed.\n"
        "- AI Act compliance: list_ai_act_controls + get_ai_act_score. Update controls with update_ai_act_control.\n"
        "- Compliance reports (SOC 2, RGPD, HIPAA): generate_compliance_report, then poll get_compliance_report.\n"
        "- Audit integrity: list_audit_logs to query events, verify_audit_chain to confirm no tampering.\n"
        "- Policy changes: get_policy first, modify, then update_policy. Changes are immediate.\n"
        "- Agent machine keys: list_agent_identities, create_agent_identity (key shown once), rotate_agent_identity, revoke_agent_identity.\n"
        "- Agent dependencies: get_agent_dependency_graph for org-wide view, get_agent_dependencies for one agent.\n"
        "- Job quality: list_eval_rubrics, evaluate_job, get_job_evaluations.\n"
        "- GPU cost & waste: get_budget, get_spend_trend, get_chargeback, get_waste_analysis.\n"
        "- All write operations (deploy, scale, helm, kubectl, policy, identities) are recorded in the VibOps audit log.\n"
        "- VibOps jobs are infrastructure operations, not Kubernetes Jobs. Use list_jobs to review recent operations."
    ),
)


# ── Observation tools (16) ────────────────────────────────────────────────────

mcp.tool()(observation.list_clusters)
mcp.tool()(observation.get_cluster_deployments)
mcp.tool()(observation.list_jobs)
mcp.tool()(observation.get_job)
mcp.tool()(observation.get_gpu_metrics)
mcp.tool()(observation.get_workload_breakdown)
mcp.tool()(observation.get_mttr)
mcp.tool()(observation.get_cost_estimate)
mcp.tool()(observation.get_job_metrics)
mcp.tool()(observation.list_gateways)
mcp.tool()(observation.list_alerts)
mcp.tool()(observation.list_secrets)
mcp.tool()(observation.list_providers)
mcp.tool()(observation.list_pipelines)
mcp.tool()(observation.get_cluster_rate)
mcp.tool()(observation.list_kubectl_contexts)


# ── Action tools (14) ─────────────────────────────────────────────────────────

mcp.tool()(actions.scale_deployment)
mcp.tool()(actions.deploy_model)
mcp.tool()(actions.helm_upgrade)
mcp.tool()(actions.helm_uninstall)
mcp.tool()(actions.run_kubectl)
mcp.tool()(actions.git_clone)
mcp.tool()(actions.create_secret)
mcp.tool()(actions.trigger_pipeline)

# Slurm HPC
mcp.tool()(actions.slurm_get_cluster_info)
mcp.tool()(actions.slurm_list_jobs)
mcp.tool()(actions.slurm_get_job_status)
mcp.tool()(actions.slurm_get_job_output)
mcp.tool()(actions.slurm_submit_job)
mcp.tool()(actions.slurm_cancel_job)


# ── Configuration tools (3) ───────────────────────────────────────────────────

mcp.tool()(config.set_cluster_rate)
mcp.tool()(config.register_gateway)
mcp.tool()(config.delete_gateway)


# ── Governance tools (22) ─────────────────────────────────────────────────────

# Anomalies
mcp.tool()(governance.list_anomalies)
mcp.tool()(governance.get_open_anomalies)
mcp.tool()(governance.resolve_anomaly)

# AI Act compliance
mcp.tool()(governance.list_ai_act_controls)
mcp.tool()(governance.get_ai_act_score)
mcp.tool()(governance.update_ai_act_control)

# Compliance reports
mcp.tool()(governance.list_compliance_reports)
mcp.tool()(governance.generate_compliance_report)
mcp.tool()(governance.get_compliance_report)

# Audit log
mcp.tool()(governance.list_audit_logs)
mcp.tool()(governance.verify_audit_chain)

# Policy
mcp.tool()(governance.get_policy)
mcp.tool()(governance.update_policy)

# Agent identity lifecycle
mcp.tool()(governance.list_agent_identities)
mcp.tool()(governance.create_agent_identity)
mcp.tool()(governance.rotate_agent_identity)
mcp.tool()(governance.revoke_agent_identity)

# Agent dependency graph
mcp.tool()(governance.get_agent_dependency_graph)
mcp.tool()(governance.get_agent_dependencies)

# LLM-as-judge evaluation
mcp.tool()(governance.list_eval_rubrics)
mcp.tool()(governance.evaluate_job)
mcp.tool()(governance.get_job_evaluations)


# ── FinOps tools (4) ──────────────────────────────────────────────────────────

mcp.tool()(finops.get_budget)
mcp.tool()(finops.get_chargeback)
mcp.tool()(finops.get_spend_trend)
mcp.tool()(finops.get_waste_analysis)


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()

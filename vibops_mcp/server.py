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
        "You are connected to a VibOps instance that manages GPU Kubernetes infrastructure.\n\n"
        "Routing guide:\n"
        "- Start with list_clusters to discover available clusters before taking any action.\n"
        "- For general fleet health, call list_clusters then list_alerts.\n"
        "- To investigate a specific cluster, call get_cluster_deployments.\n"
        "- GPU utilisation: get_gpu_metrics. Cost: get_cost_estimate. Workload types: get_workload_breakdown.\n"
        "- To scale pods in a deployment, use scale_deployment. Do not use helm or run_kubectl for scaling.\n"
        "- To deploy a model, use deploy_model. For arbitrary Helm charts, use helm_upgrade.\n"
        "- Use run_kubectl only for operations not covered by dedicated tools (get, describe, logs).\n"
        "- Before triggering a pipeline, use list_pipelines to find its UUID.\n"
        "- All write operations (deploy, scale, helm, kubectl) are recorded in the VibOps audit log.\n"
        "- VibOps jobs are infrastructure operations, not Kubernetes Jobs. Use list_jobs to review recent operations."
    ),
)


# ── Observation tools (15) ────────────────────────────────────────────────────
# Docstrings live in tools/observation.py — registered directly to avoid duplication.

mcp.tool()(observation.list_clusters)
mcp.tool()(observation.get_cluster_deployments)
mcp.tool()(observation.list_jobs)
mcp.tool()(observation.get_job)
mcp.tool()(observation.get_gpu_metrics)
mcp.tool()(observation.get_workload_breakdown)
mcp.tool()(observation.get_mttr)
mcp.tool()(observation.get_cost_estimate)
mcp.tool()(observation.list_gateways)
mcp.tool()(observation.list_alerts)
mcp.tool()(observation.list_secrets)
mcp.tool()(observation.list_providers)
mcp.tool()(observation.list_pipelines)
mcp.tool()(observation.get_cluster_rate)
mcp.tool()(observation.list_kubectl_contexts)


# ── Action tools (8) ──────────────────────────────────────────────────────────
# Docstrings live in tools/actions.py — registered directly to avoid duplication.

mcp.tool()(actions.scale_deployment)
mcp.tool()(actions.deploy_model)
mcp.tool()(actions.helm_upgrade)
mcp.tool()(actions.helm_uninstall)
mcp.tool()(actions.run_kubectl)
mcp.tool()(actions.git_clone)
mcp.tool()(actions.create_secret)
mcp.tool()(actions.trigger_pipeline)


# ── Configuration tools (3) ───────────────────────────────────────────────────
# Docstrings live in tools/config.py — registered directly to avoid duplication.

mcp.tool()(config.set_cluster_rate)
mcp.tool()(config.register_gateway)
mcp.tool()(config.delete_gateway)


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()

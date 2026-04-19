# vibops-mcp

The provider-agnostic MCP server for GPU infrastructure — one interface for any cloud, any cluster, any provider.

## The problem

Large enterprises and CSPs managing GPU infrastructure deal with fragmentation — AWS, GCP, Azure, on-prem, neoclouds, each with their own API, dashboard, and cost model. Correlating utilisation, cost, and workload type across providers requires jumping between 5 tools.

## The solution

`vibops-mcp` is a single MCP server that abstracts this complexity. One `pip install`, 26 tools, and your AI assistant can observe, operate, and optimize your entire GPU fleet — regardless of where it runs.

- **Observe** — GPU utilisation, workload breakdown, MTTR, cost estimates, live K8s deployments
- **Act** — deploy models, scale clusters, run Helm/kubectl, trigger pipelines
- **Configure** — set cost rates, manage gateways, store secrets

All operations go through your VibOps instance and are recorded in the audit log.

## Installation

```bash
pip install vibops-mcp
```

## Configuration

You need two environment variables:

| Variable | Description |
|----------|-------------|
| `VIBOPS_URL` | Base URL of your VibOps instance, e.g. `https://vibops.example.com` |
| `VIBOPS_TOKEN` | API token — create one in VibOps → Settings → API Tokens |

## Claude Desktop

Add to `~/.config/claude/claude_desktop_config.json` (macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
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
```

## Cursor

Add to `.cursor/mcp.json` in your project root, or to the global config:

```json
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
```

## Claude Code (CLI)

```bash
claude mcp add vibops vibops-mcp \
  -e VIBOPS_URL=https://vibops.example.com \
  -e VIBOPS_TOKEN=your-token-here
```

## Available tools

### Observation (read-only)

| Tool | Description |
|------|-------------|
| `list_clusters` | List clusters and GPU utilisation |
| `list_kubectl_contexts` | List available kubectl contexts |
| `get_cluster_deployments` | Live K8s deployment status for a cluster |
| `get_cluster_rate` | Get configured GPU cost rate for a cluster |
| `list_jobs` | List recent jobs with optional filters |
| `get_job` | Get job details and result |
| `get_gpu_metrics` | Hourly GPU utilisation time-series |
| `get_workload_breakdown` | Job count by workload type |
| `get_mttr` | Mean Time To Resolve GPU alerts |
| `get_cost_estimate` | Estimated GPU spend |
| `list_gateways` | List registered gateways and status |
| `list_alerts` | List GPU alerts (open or resolved) |
| `list_secrets` | List secrets (names only, never values) |
| `list_providers` | List configured AI/GPU cloud providers |
| `list_pipelines` | List automation pipelines |

### Actions (write)

| Tool | Description |
|------|-------------|
| `scale_cluster` | Scale a K8s deployment or node pool |
| `deploy_model` | Deploy an AI model onto a GPU cluster |
| `helm_upgrade` | Run helm upgrade --install |
| `helm_uninstall` | Uninstall a Helm release |
| `run_kubectl` | Run an arbitrary kubectl command |
| `git_clone` | Clone a git repository |
| `create_secret` | Store an encrypted secret |
| `trigger_pipeline` | Manually trigger an automation pipeline |

### Configuration

| Tool | Description |
|------|-------------|
| `set_cluster_rate` | Set GPU cost rate for a cluster (admin only) |
| `register_gateway` | Register a new gateway (returns one-time token) |
| `delete_gateway` | Revoke a gateway |

## Example prompts

```
"What's our GPU utilisation trend over the last 7 days?"
"Show me the cost breakdown per cluster this week."
"Deploy llama3:8b on vibops-dev with 2 replicas."
"Which clusters have open critical GPU alerts?"
"Scale the inference namespace to 4 replicas on prod-cluster."
"What's our MTTR for critical alerts?"
```

## Roadmap

### Wave 1 — Current (v0.1)
- ✅ Kubernetes (generic — on-prem, Kind, kubeadm)
- ✅ Any VibOps-connected cluster via gateway

### Wave 2 — Q2 2026
- 🔜 NVIDIA DGX Cloud (NGC API)
- 🔜 AWS (EC2 GPU + EKS)
- 🔜 GCP (A3/A2 + GKE)
- 🔜 Azure (ND/NC series + AKS)

### Wave 3 — Q3 2026
- 🔜 CoreWeave, Lambda Labs, RunPod
- 🔜 OVHcloud, Scaleway
- 🔜 Dell APEX, HPE GreenLake

Want a provider prioritised? [Open an issue](https://github.com/VibOpsai/vibops-mcp/issues/new).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). All contributions require a DCO sign-off (`git commit -s`).

## License

MIT — free to use, modify, and distribute. See [LICENSE](LICENSE).

Built on [FastMCP](https://github.com/jlowin/fastmcp) and the [VibOps](https://vibops.io) platform.

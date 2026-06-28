# vibops-mcp

The provider-agnostic MCP server for GPU infrastructure — one interface for any cloud, any cluster, any provider.

## The problem

Large enterprises and CSPs managing GPU infrastructure deal with fragmentation — AWS, GCP, Azure, on-prem, neoclouds, each with their own API, dashboard, and cost model. Correlating utilisation, cost, workload type, and compliance posture across providers requires jumping between 5 tools.

## The solution

`vibops-mcp` is a single MCP server that abstracts this complexity. One `pip install`, 70 tools, and your AI assistant can observe, operate, govern, and optimize your entire GPU fleet — regardless of where it runs.

- **Observe** — GPU utilisation, workload breakdown, MTTR, cost estimates, live K8s deployments
- **Act** — deploy models, scale deployments, run Helm/kubectl, trigger pipelines, submit Slurm jobs
- **Govern** — anomaly detection, AI Act compliance, SOC 2/RGPD reports, immutable audit chain, policy management
- **FinOps** — budget tracking, chargeback, spend trends, waste analysis

All operations go through your VibOps instance and are recorded in the audit log.

## Installation

```bash
pip install git+https://github.com/VibOpsai/vibops-mcp.git
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

### Observation (16 tools — read-only)

| Tool | Description |
|------|-------------|
| `list_clusters` | List clusters and GPU utilisation |
| `list_kubectl_contexts` | List available kubectl contexts |
| `get_cluster_deployments` | Live K8s deployment status for a cluster |
| `get_cluster_rate` | Get configured GPU cost rate for a cluster |
| `list_jobs` | List recent jobs with optional filters |
| `get_job` | Get job details and result |
| `get_job_metrics` | Job success rate, latency P50/P95/P99, error breakdown |
| `get_gpu_metrics` | Hourly GPU utilisation time-series |
| `get_workload_breakdown` | Job count by workload type |
| `get_mttr` | Mean Time To Resolve GPU alerts |
| `get_cost_estimate` | Estimated GPU spend |
| `list_gateways` | List registered gateways and status |
| `list_alerts` | List GPU alerts (open or resolved) |
| `list_secrets` | List secrets (names only, never values) |
| `list_providers` | List configured AI/GPU cloud providers |
| `list_pipelines` | List automation pipelines |

### Actions (18 tools — write)

| Tool | Description |
|------|-------------|
| `scale_deployment` | Scale a K8s deployment replica count |
| `deploy_model` | Deploy an AI model onto a GPU cluster |
| `helm_upgrade` | Run helm upgrade --install |
| `helm_uninstall` | Uninstall a Helm release |
| `run_kubectl` | Run an arbitrary kubectl command |
| `git_clone` | Clone a git repository |
| `create_secret` | Store an encrypted secret |
| `trigger_pipeline` | Manually trigger an automation pipeline |
| `slurm_get_cluster_info` | Get Slurm cluster info and partition details |
| `slurm_list_jobs` | List Slurm jobs with optional filters |
| `slurm_get_job_status` | Get status of a specific Slurm job |
| `slurm_get_job_output` | Retrieve stdout/stderr of a completed Slurm job |
| `slurm_submit_job` | Submit a new Slurm job |
| `slurm_cancel_job` | Cancel a running or pending Slurm job |
| `registry_list_repos` | List container registry repositories |
| `registry_list_tags` | List tags for a container image |
| `registry_check_image` | Check image details (size, layers, created date) |
| `registry_delete_tag` | Delete a stale image tag (requires confirmed=True) |

### Configuration (3 tools)

| Tool | Description |
|------|-------------|
| `set_cluster_rate` | Set GPU cost rate for a cluster (admin only) |
| `register_gateway` | Register a new gateway (returns one-time token) |
| `delete_gateway` | Revoke a gateway |

### Agent Infrastructure Control Plane (12 tools)

The missing layer between your AI agents and your GPU fleet. Works with any framework (n8n, LangChain, CrewAI, Dify) — just point to the VibOps LLM Proxy.

| Tool | Description |
|------|-------------|
| **FinOps per agent** | |
| `get_agent_usage` | GPU cost per agent — tokens, requests, cost, GPU-hours. *"Which agent costs the most?"* |
| `get_agent_usage_detail` | Drill-down on one agent — daily breakdown, model distribution, cost trend |
| `get_agent_budget` | Current budget + MTD spend for an agent |
| `set_agent_budget` | Set monthly spend limit — soft alert at 80%, hard block at 100% (HTTP 429) |
| **Model access control** | |
| `get_agent_model_rules` | List model access rules — which agent can use which LLM |
| `update_agent_model_rule` | Create a rule: glob patterns, deny-first. *"RH agents → Mistral only"* |
| **Identity lifecycle** | |
| `list_agent_identities` | List machine identities for agents |
| `create_agent_identity` | Create a new machine identity (key shown once) |
| `rotate_agent_identity` | Rotate the key for an existing identity |
| `revoke_agent_identity` | Revoke an identity immediately |
| **Dependency graph** | |
| `get_agent_dependency_graph` | Full org-wide graph: agent→model, agent→connector, agent→sub-agent |
| `get_agent_dependencies` | Dependencies for one agent — impact analysis before migration |

### Governance & Compliance (21 tools)

| Tool | Description |
|------|-------------|
| `list_anomalies` | List GPU anomalies with optional cluster/status filter |
| `get_open_anomalies` | Get all currently open anomalies |
| `resolve_anomaly` | Mark an anomaly as resolved |
| `list_ai_act_controls` | List AI Act compliance controls |
| `get_ai_act_score` | Get the overall AI Act compliance score |
| `update_ai_act_control` | Update status, notes, or evidence URL for a control |
| `list_compliance_reports` | List generated compliance reports |
| `generate_compliance_report` | Generate a SOC 2, RGPD, or HIPAA report asynchronously |
| `get_compliance_report` | Poll/retrieve a generated compliance report |
| `list_audit_logs` | Query the immutable audit log with filters |
| `verify_audit_chain` | Verify HMAC-SHA256 integrity of the full audit chain |
| `get_policy` | Get the current organisation policy |
| `update_policy` | Replace the organisation policy (immediate effect) |
| `list_eval_rubrics` | List LLM-as-judge evaluation rubrics |
| `evaluate_job` | Trigger LLM-as-judge evaluation for a job |
| `get_job_evaluations` | Retrieve evaluation results for a job |
| `get_ldap_config` | Get LDAP / Active Directory configuration |
| `update_ldap_config` | Configure or enable/disable LDAP integration |
| `get_siem_config` | Get SIEM push export configuration |
| `update_siem_config` | Set Splunk/Datadog SIEM destination |
| `push_to_siem` | Export audit events to configured SIEM |

### GPU FinOps (4 tools)

| Tool | Description |
|------|-------------|
| `get_budget` | Get current GPU budget and consumed spend |
| `get_chargeback` | Get chargeback breakdown by tenant for a given month |
| `get_spend_trend` | Get daily GPU spend trend (default: last 30 days) |
| `get_waste_analysis` | Identify idle GPU resources and cost optimisation opportunities |

## LLM Inference Proxy

VibOps includes a transparent OpenAI-compatible proxy (port 8004) that sits between your AI agents and LLM inference servers (vLLM, Ollama, TGI). Every inference request is logged with agent attribution for FinOps.

Your agents point to the proxy instead of the LLM directly:

```
# Before
OPENAI_BASE_URL=http://vllm:8000/v1

# After
OPENAI_BASE_URL=http://vibops-proxy:8004/v1
```

Add a `X-VibOps-Agent-Id` header to attribute costs per agent:

```bash
curl -X POST http://vibops-proxy:8004/v1/chat/completions \
  -H "X-VibOps-Agent-Id: pricing-agent-v2" \
  -H "X-VibOps-Team: supply-chain" \
  -d '{"model": "mistral:7b", "messages": [...]}'
```

The proxy captures: agent ID, team, model, tokens, latency, GPU cost — visible in the console FinOps dashboard and queryable via `get_agent_usage`.

## Example prompts

```
"What's our GPU utilisation trend over the last 7 days?"
"Show me the cost breakdown per cluster this week."
"Deploy llama3:8b on vibops-dev with 2 replicas."
"Which clusters have open critical GPU alerts?"
"Scale the inference deployment to 4 replicas on prod-cluster."
"What's our MTTR for critical alerts?"
"Are there any open GPU anomalies right now?"
"What's our AI Act compliance score and which controls are non-compliant?"
"Generate a SOC 2 report for Q1 2026."
"Verify the audit chain hasn't been tampered with."
"Show me the spend trend for the last 7 days and flag any waste."
"Create a machine identity for the pricing-agent with a 1-year expiry."
"Which agents depend on the claude-opus-4-6 model?"
"Which agent costs the most in GPU this month?"
"Show me the inference cost breakdown for the pricing agent."
"What's the GPU spend per team for the last 7 days?"
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). All contributions require a DCO sign-off (`git commit -s`).

## License

MIT — free to use, modify, and distribute. See [LICENSE](LICENSE).

Built on [FastMCP](https://github.com/jlowin/fastmcp) and the [VibOps](https://vibops.ai) platform.

"""
Governance, compliance, security and observability tools for VibOps MCP.

Covers:
  - Anomaly detection & resolution
  - AI Act compliance controls & scoring
  - SOC 2 / RGPD / HIPAA compliance report generation
  - Immutable audit log inspection & chain verification
  - Organisation policy management
  - Agent identity lifecycle (create / rotate / revoke)
  - Agent dependency graph
  - LLM-as-judge evaluation rubrics & job evaluations
"""
from vibops_mcp import client


# ── Anomalies ─────────────────────────────────────────────────────────────────

async def list_anomalies(
    cluster_name: str | None = None,
    status: str | None = None,
) -> dict:
    """
    List GPU anomalies detected by VibOps across all clusters.

    Anomalies are detected automatically every 5 minutes: gpu_idle (<10 %
    utilisation), gpu_spike (>90 %), node_loss (node disappeared from scrape),
    utilization_drop (>30 pt drop in one window). Duplicates are suppressed —
    only one open event per anomaly type per cluster exists at a time.

    Args:
        cluster_name: Filter by cluster name (optional).
        status: Filter by status — "open" or "resolved" (optional, returns all if omitted).
    """
    params: dict = {}
    if cluster_name:
        params["cluster_name"] = cluster_name
    if status:
        params["status"] = status
    return await client.get("/api/v1/anomalies", params=params or None)


async def get_open_anomalies() -> dict:
    """
    Return all currently open (unresolved) GPU anomalies across the fleet.

    Use this for a quick fleet health check alongside list_alerts. An open
    anomaly means the triggering condition is still active. Resolution is
    automatic once the condition disappears, or manual via resolve_anomaly.
    """
    return await client.get("/api/v1/anomalies/open")


async def resolve_anomaly(anomaly_id: str, reason: str | None = None) -> dict:
    """
    Manually mark an anomaly as resolved.

    Use when the underlying issue has been addressed outside VibOps (e.g.
    a workload was restarted manually). Automatic resolution still applies
    when the condition normalises on the next detection cycle.

    Write operation — recorded in the audit log.

    Args:
        anomaly_id: UUID of the anomaly to resolve (from list_anomalies).
        reason: Optional free-text explanation of how the issue was resolved.
    """
    body: dict = {}
    if reason:
        body["reason"] = reason
    return await client.post(f"/api/v1/anomalies/{anomaly_id}/resolve", body=body)


# ── AI Act compliance controls ────────────────────────────────────────────────

async def list_ai_act_controls() -> dict:
    """
    List all AI Act compliance controls and their current status.

    VibOps pre-seeds 6 articles: Art.9 (risk management), Art.12 (logging &
    traceability), Art.13 (transparency), Art.14 (human oversight), Art.15
    (accuracy & robustness), Art.17 (quality management). Each control has a
    status (compliant / partial / non_compliant / not_applicable), optional
    notes, and an evidence URL.

    Use get_ai_act_score to get the aggregated compliance percentage.
    """
    return await client.get("/api/v1/compliance/ai-act")


async def get_ai_act_score() -> dict:
    """
    Return the organisation's overall AI Act compliance score (0–100).

    Score is the weighted average of applicable controls: compliant=1.0,
    partial=0.5, non_compliant=0.0. Controls marked not_applicable are
    excluded from the denominator so they do not penalise the score.

    Use list_ai_act_controls to see per-article breakdown and identify gaps.
    """
    return await client.get("/api/v1/compliance/ai-act/score")


async def update_ai_act_control(
    control_id: str,
    status: str,
    notes: str | None = None,
    evidence_url: str | None = None,
) -> dict:
    """
    Update the status, notes or evidence URL of an AI Act control.

    Write operation — recorded in the audit log.

    Args:
        control_id: UUID of the control to update (from list_ai_act_controls).
        status: New compliance status — one of: compliant, partial,
                non_compliant, not_applicable.
        notes: Free-text justification or implementation notes (optional).
        evidence_url: URL to supporting evidence document or test report (optional).
    """
    body: dict = {"status": status}
    if notes is not None:
        body["notes"] = notes
    if evidence_url is not None:
        body["evidence_url"] = evidence_url
    return await client.patch(f"/api/v1/compliance/ai-act/{control_id}", body=body)


# ── Compliance reports ────────────────────────────────────────────────────────

async def list_compliance_reports(report_type: str | None = None) -> dict:
    """
    List generated compliance reports for the organisation.

    Reports are generated asynchronously; status moves from "pending" to
    "ready" (or "failed") once the audit log analysis completes. Use
    get_compliance_report to retrieve the full findings once ready.

    Args:
        report_type: Filter by framework — "soc2", "gdpr", or "hipaa" (optional).
    """
    params: dict = {}
    if report_type:
        params["report_type"] = report_type
    return await client.get("/api/v1/compliance/reports", params=params or None)


async def generate_compliance_report(report_type: str, period: str) -> dict:
    """
    Trigger generation of a compliance report by analysing the audit log.

    Generation is asynchronous — this call returns immediately with a report
    object in "pending" status. Poll get_compliance_report until status is
    "ready". Generation time depends on audit log volume for the period.

    Write operation — recorded in the audit log.

    Args:
        report_type: Compliance framework — "soc2", "gdpr", or "hipaa".
        period: Time period to analyse. Formats accepted:
                  "2026-Q1"  (quarter),
                  "2026-05"  (month),
                  "2026"     (full year).
    """
    return await client.post("/api/v1/compliance/reports", body={
        "report_type": report_type,
        "period": period,
    })


async def get_compliance_report(report_id: str) -> dict:
    """
    Retrieve a compliance report by ID, including its findings once ready.

    Poll this after generate_compliance_report until status == "ready".
    The "summary" field contains per-control findings, counts of passing /
    failing events, and remediation recommendations.

    Args:
        report_id: UUID of the report (from generate_compliance_report or
                   list_compliance_reports).
    """
    return await client.get(f"/api/v1/compliance/reports/{report_id}")


# ── Audit log ─────────────────────────────────────────────────────────────────

async def list_audit_logs(
    from_dt: str | None = None,
    to_dt: str | None = None,
    action: str | None = None,
    limit: int = 50,
) -> dict:
    """
    Query the immutable VibOps audit log.

    Every operation (deploy, scale, policy change, identity rotation…) is
    recorded with full context: actor, org, cluster, parameters, result,
    duration, cost. Entries are HMAC-chained — use verify_audit_chain to
    confirm integrity.

    Args:
        from_dt: Start of time window, ISO 8601 (e.g. "2026-05-01T00:00:00Z"). Optional.
        to_dt: End of time window, ISO 8601. Optional.
        action: Filter by action type (e.g. "helm_upgrade", "scale_cluster"). Optional.
        limit: Maximum number of entries to return (default 50, max 500).
    """
    params: dict = {"limit": limit}
    if from_dt:
        params["from"] = from_dt
    if to_dt:
        params["to"] = to_dt
    if action:
        params["action"] = action
    return await client.get("/api/v1/audit", params=params)


async def verify_audit_chain() -> dict:
    """
    Verify the cryptographic integrity of the entire audit log chain.

    Each audit entry is signed with HMAC-SHA256 chaining the previous entry's
    hash. This endpoint traverses the full chain and reports the first broken
    link if tampering is detected, or confirms the chain is intact.

    Returns: {"valid": true} if the chain is intact, or {"valid": false,
    "broken_at": <entry_id>, "detail": "..."} if corruption is found.
    """
    return await client.get("/api/v1/audit/verify")


# ── Policy ────────────────────────────────────────────────────────────────────

async def get_policy() -> dict:
    """
    Return the active policy configuration for the current organisation.

    Policy controls: allowed LLM models, budget limits per agent, tool
    permission matrix, rate limits, escalation rules and default-deny
    behaviour. Changes take effect immediately on all active agents.
    """
    return await client.get("/api/v1/policy")


async def update_policy(policy: dict) -> dict:
    """
    Replace the organisation policy configuration.

    The full policy object must be supplied (not a partial patch). Retrieve
    the current policy with get_policy, modify the desired fields, then submit.
    Changes are applied immediately — active agents will reflect the new policy
    within seconds. All changes are recorded in the audit log.

    Write operation — recorded in the audit log.

    Args:
        policy: Complete policy object as returned by get_policy, with
                modifications applied. Unknown keys are rejected.
    """
    return await client.put("/api/v1/policy", body=policy)


# ── Agent identity lifecycle ──────────────────────────────────────────────────

async def list_agent_identities() -> dict:
    """
    List all agent machine identities for the organisation.

    Each identity has a name, key prefix (vib_…), creation date, last-used
    timestamp, rotation history, and revocation status. The raw key is never
    stored — only its SHA-256 hash is retained after creation.

    Use create_agent_identity to issue a new identity for a service or agent.
    """
    return await client.get("/api/v1/agent-identities")


async def create_agent_identity(
    name: str,
    expires_at: str | None = None,
) -> dict:
    """
    Create a new agent machine identity and return its API key.

    The raw key is returned ONCE in this response and never again — store it
    securely immediately. The key is prefixed with "vib_" and stored as a
    SHA-256 hash in VibOps. If the key is lost, rotate the identity instead
    of recreating it.

    Write operation — recorded in the audit log.

    Args:
        name: Human-readable label for this identity (e.g. "pricing-agent-prod").
        expires_at: Optional expiry date in ISO 8601 format (e.g. "2027-01-01T00:00:00Z").
                    If omitted, the identity does not expire.
    """
    body: dict = {"name": name}
    if expires_at:
        body["expires_at"] = expires_at
    return await client.post("/api/v1/agent-identities", body=body)


async def rotate_agent_identity(identity_id: str) -> dict:
    """
    Rotate the API key for an agent identity.

    Generates a new key and immediately invalidates the previous one. The new
    raw key is returned ONCE in this response — store it securely. The identity
    itself (ID, name, history) is preserved; only the key changes.

    Use this for scheduled key rotation or if a key is suspected of being
    compromised. To permanently disable an identity, use revoke_agent_identity.

    Write operation — recorded in the audit log.

    Args:
        identity_id: UUID of the identity to rotate (from list_agent_identities).
    """
    return await client.post(f"/api/v1/agent-identities/{identity_id}/rotate")


async def revoke_agent_identity(identity_id: str) -> dict:
    """
    Permanently revoke an agent identity, blocking all future authentication.

    Revocation is immediate and irreversible. The identity record is retained
    for audit purposes but the key is rejected on all subsequent API calls.
    Use rotate_agent_identity instead if you simply want to cycle the key.

    Write operation — recorded in the audit log.

    Args:
        identity_id: UUID of the identity to revoke (from list_agent_identities).
    """
    return await client.post(f"/api/v1/agent-identities/{identity_id}/revoke")


# ── Agent dependency graph ────────────────────────────────────────────────────

async def get_agent_dependency_graph() -> dict:
    """
    Return the full directed dependency graph for all agents in the organisation.

    Edges represent runtime relationships: agent→model (which LLM an agent
    calls), agent→connector (which data sources it uses), agent→agent (which
    sub-agents it orchestrates). Each edge records call_count, first_seen and
    last_seen timestamps.

    Key use case: impact analysis — "if I replace this LLM model, which agents
    are affected and how frequently do they call it?"
    """
    return await client.get("/api/v1/agents/graph")


async def get_agent_dependencies(agent_id: str) -> dict:
    """
    Return the dependency edges for a single agent.

    Shows what models, connectors and sub-agents this agent depends on, with
    call counts and timestamps. Use get_agent_dependency_graph for the full
    organisation-wide view.

    Args:
        agent_id: ID or name of the agent (as registered in the tool catalogue).
    """
    return await client.get(f"/api/v1/agents/{agent_id}/dependencies")


# ── LLM-as-judge evaluation ───────────────────────────────────────────────────

async def list_eval_rubrics() -> dict:
    """
    List LLM-as-judge evaluation rubrics defined for the organisation.

    A rubric defines evaluation criteria (accuracy, safety, relevance…), a
    scoring grid (0–10 with justification), and the LLM provider used as judge
    (Claude, OpenAI, Ollama, Groq). Rubrics marked is_auto_scanner=true trigger
    automatically after every completed job.
    """
    return await client.get("/api/v1/eval/rubrics")


async def evaluate_job(job_id: str, rubric_id: str) -> dict:
    """
    Trigger an LLM-as-judge evaluation of a completed job against a rubric.

    The evaluation runs asynchronously: the judge LLM scores the job's
    input/output against each criterion in the rubric and produces a numeric
    score with a textual justification. Results are retrievable via
    get_job_evaluations.

    Write operation — recorded in the audit log.

    Args:
        job_id: UUID of the job to evaluate (must be in "success" or "failed" state).
        rubric_id: UUID of the rubric to apply (from list_eval_rubrics).
    """
    return await client.post(f"/api/v1/eval/jobs/{job_id}/evaluate", body={
        "rubric_id": rubric_id,
    })


async def get_job_evaluations(job_id: str) -> dict:
    """
    Return all LLM-as-judge evaluation results for a specific job.

    Each evaluation includes: rubric applied, overall score (0–10), per-criterion
    breakdown, textual justification from the judge LLM, evaluation timestamp
    and the provider used. A job may have multiple evaluations if different
    rubrics were applied or if it was re-evaluated.

    Args:
        job_id: UUID of the job (from list_jobs or get_job).
    """
    return await client.get(f"/api/v1/eval/jobs/{job_id}/evaluations")

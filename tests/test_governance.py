"""
Tests for vibops_mcp/tools/governance.py

Verifies that each tool calls the correct API endpoint with the correct
method and parameters. All HTTP calls are mocked — no live VibOps instance
required.
"""
import pytest
from unittest.mock import AsyncMock, patch

from vibops_mcp.tools import governance


# ── Anomalies ─────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_anomalies_no_filters():
    with patch("vibops_mcp.tools.governance.client.get", new_callable=AsyncMock) as mock:
        mock.return_value = []
        await governance.list_anomalies()
    mock.assert_called_once_with("/api/v1/anomalies", params=None)


@pytest.mark.asyncio
async def test_list_anomalies_with_filters():
    with patch("vibops_mcp.tools.governance.client.get", new_callable=AsyncMock) as mock:
        mock.return_value = []
        await governance.list_anomalies(cluster_name="gpu-prod", status="open")
    mock.assert_called_once_with(
        "/api/v1/anomalies",
        params={"cluster_name": "gpu-prod", "status": "open"},
    )


@pytest.mark.asyncio
async def test_get_open_anomalies():
    with patch("vibops_mcp.tools.governance.client.get", new_callable=AsyncMock) as mock:
        mock.return_value = []
        await governance.get_open_anomalies()
    mock.assert_called_once_with("/api/v1/anomalies/open")


@pytest.mark.asyncio
async def test_resolve_anomaly_without_reason():
    with patch("vibops_mcp.tools.governance.client.post", new_callable=AsyncMock) as mock:
        mock.return_value = {"status": "resolved"}
        await governance.resolve_anomaly("anomaly-uuid-1")
    mock.assert_called_once_with("/api/v1/anomalies/anomaly-uuid-1/resolve", body={})


@pytest.mark.asyncio
async def test_resolve_anomaly_with_reason():
    with patch("vibops_mcp.tools.governance.client.post", new_callable=AsyncMock) as mock:
        mock.return_value = {"status": "resolved"}
        await governance.resolve_anomaly("anomaly-uuid-1", reason="Restarted workload")
    mock.assert_called_once_with(
        "/api/v1/anomalies/anomaly-uuid-1/resolve",
        body={"reason": "Restarted workload"},
    )


# ── AI Act ────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_ai_act_controls():
    with patch("vibops_mcp.tools.governance.client.get", new_callable=AsyncMock) as mock:
        mock.return_value = {"controls": []}
        await governance.list_ai_act_controls()
    mock.assert_called_once_with("/api/v1/compliance/ai-act")


@pytest.mark.asyncio
async def test_get_ai_act_score():
    with patch("vibops_mcp.tools.governance.client.get", new_callable=AsyncMock) as mock:
        mock.return_value = {"score": 83.3}
        await governance.get_ai_act_score()
    mock.assert_called_once_with("/api/v1/compliance/ai-act/score")


@pytest.mark.asyncio
async def test_update_ai_act_control_status_only():
    with patch("vibops_mcp.tools.governance.client.patch", new_callable=AsyncMock) as mock:
        mock.return_value = {"status": "compliant"}
        await governance.update_ai_act_control("ctrl-uuid", "compliant")
    mock.assert_called_once_with(
        "/api/v1/compliance/ai-act/ctrl-uuid",
        body={"status": "compliant"},
    )


@pytest.mark.asyncio
async def test_update_ai_act_control_full():
    with patch("vibops_mcp.tools.governance.client.patch", new_callable=AsyncMock) as mock:
        mock.return_value = {"status": "partial"}
        await governance.update_ai_act_control(
            "ctrl-uuid", "partial",
            notes="In progress", evidence_url="https://example.com/evidence",
        )
    mock.assert_called_once_with(
        "/api/v1/compliance/ai-act/ctrl-uuid",
        body={
            "status": "partial",
            "notes": "In progress",
            "evidence_url": "https://example.com/evidence",
        },
    )


# ── Compliance reports ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_compliance_reports_no_filter():
    with patch("vibops_mcp.tools.governance.client.get", new_callable=AsyncMock) as mock:
        mock.return_value = []
        await governance.list_compliance_reports()
    mock.assert_called_once_with("/api/v1/compliance/reports", params=None)


@pytest.mark.asyncio
async def test_list_compliance_reports_filtered():
    with patch("vibops_mcp.tools.governance.client.get", new_callable=AsyncMock) as mock:
        mock.return_value = []
        await governance.list_compliance_reports(report_type="soc2")
    mock.assert_called_once_with(
        "/api/v1/compliance/reports", params={"report_type": "soc2"}
    )


@pytest.mark.asyncio
async def test_generate_compliance_report():
    with patch("vibops_mcp.tools.governance.client.post", new_callable=AsyncMock) as mock:
        mock.return_value = {"id": "rpt-uuid", "status": "pending"}
        await governance.generate_compliance_report("soc2", "2026-Q1")
    mock.assert_called_once_with(
        "/api/v1/compliance/reports",
        body={"report_type": "soc2", "period": "2026-Q1"},
    )


@pytest.mark.asyncio
async def test_get_compliance_report():
    with patch("vibops_mcp.tools.governance.client.get", new_callable=AsyncMock) as mock:
        mock.return_value = {"id": "rpt-uuid", "status": "ready"}
        await governance.get_compliance_report("rpt-uuid")
    mock.assert_called_once_with("/api/v1/compliance/reports/rpt-uuid")


# ── Audit log ─────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_audit_logs_defaults():
    with patch("vibops_mcp.tools.governance.client.get", new_callable=AsyncMock) as mock:
        mock.return_value = {"entries": []}
        await governance.list_audit_logs()
    mock.assert_called_once_with("/api/v1/audit", params={"limit": 50})


@pytest.mark.asyncio
async def test_list_audit_logs_with_filters():
    with patch("vibops_mcp.tools.governance.client.get", new_callable=AsyncMock) as mock:
        mock.return_value = {"entries": []}
        await governance.list_audit_logs(
            from_dt="2026-05-01T00:00:00Z",
            to_dt="2026-05-31T23:59:59Z",
            action="helm_upgrade",
            limit=100,
        )
    mock.assert_called_once_with(
        "/api/v1/audit",
        params={
            "limit": 100,
            "from": "2026-05-01T00:00:00Z",
            "to": "2026-05-31T23:59:59Z",
            "action": "helm_upgrade",
        },
    )


@pytest.mark.asyncio
async def test_verify_audit_chain():
    with patch("vibops_mcp.tools.governance.client.get", new_callable=AsyncMock) as mock:
        mock.return_value = {"valid": True}
        await governance.verify_audit_chain()
    mock.assert_called_once_with("/api/v1/audit/verify")


# ── Policy ────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_policy():
    with patch("vibops_mcp.tools.governance.client.get", new_callable=AsyncMock) as mock:
        mock.return_value = {"default_deny": True}
        await governance.get_policy()
    mock.assert_called_once_with("/api/v1/policy")


@pytest.mark.asyncio
async def test_update_policy():
    policy = {"default_deny": True, "allowed_models": ["claude-opus-4-6"]}
    with patch("vibops_mcp.tools.governance.client.put", new_callable=AsyncMock) as mock:
        mock.return_value = policy
        await governance.update_policy(policy)
    mock.assert_called_once_with("/api/v1/policy", body=policy)


# ── Agent identities ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_agent_identities():
    with patch("vibops_mcp.tools.governance.client.get", new_callable=AsyncMock) as mock:
        mock.return_value = []
        await governance.list_agent_identities()
    mock.assert_called_once_with("/api/v1/agent-identities")


@pytest.mark.asyncio
async def test_create_agent_identity_no_expiry():
    with patch("vibops_mcp.tools.governance.client.post", new_callable=AsyncMock) as mock:
        mock.return_value = {"id": "id-uuid", "key": "vib_abc123"}
        await governance.create_agent_identity("pricing-agent-prod")
    mock.assert_called_once_with(
        "/api/v1/agent-identities", body={"name": "pricing-agent-prod"}
    )


@pytest.mark.asyncio
async def test_create_agent_identity_with_expiry():
    with patch("vibops_mcp.tools.governance.client.post", new_callable=AsyncMock) as mock:
        mock.return_value = {"id": "id-uuid", "key": "vib_abc123"}
        await governance.create_agent_identity(
            "pricing-agent-prod", expires_at="2027-01-01T00:00:00Z"
        )
    mock.assert_called_once_with(
        "/api/v1/agent-identities",
        body={"name": "pricing-agent-prod", "expires_at": "2027-01-01T00:00:00Z"},
    )


@pytest.mark.asyncio
async def test_rotate_agent_identity():
    with patch("vibops_mcp.tools.governance.client.post", new_callable=AsyncMock) as mock:
        mock.return_value = {"key": "vib_newkey"}
        await governance.rotate_agent_identity("id-uuid")
    mock.assert_called_once_with("/api/v1/agent-identities/id-uuid/rotate")


@pytest.mark.asyncio
async def test_revoke_agent_identity():
    with patch("vibops_mcp.tools.governance.client.post", new_callable=AsyncMock) as mock:
        mock.return_value = {"is_revoked": True}
        await governance.revoke_agent_identity("id-uuid")
    mock.assert_called_once_with("/api/v1/agent-identities/id-uuid/revoke")


# ── Agent dependency graph ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_agent_dependency_graph():
    with patch("vibops_mcp.tools.governance.client.get", new_callable=AsyncMock) as mock:
        mock.return_value = {"nodes": [], "edges": []}
        await governance.get_agent_dependency_graph()
    mock.assert_called_once_with("/api/v1/agents/graph")


@pytest.mark.asyncio
async def test_get_agent_dependencies():
    with patch("vibops_mcp.tools.governance.client.get", new_callable=AsyncMock) as mock:
        mock.return_value = {"edges": []}
        await governance.get_agent_dependencies("pricing-agent")
    mock.assert_called_once_with("/api/v1/agents/pricing-agent/dependencies")


# ── Eval / LLM-as-judge ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_eval_rubrics():
    with patch("vibops_mcp.tools.governance.client.get", new_callable=AsyncMock) as mock:
        mock.return_value = []
        await governance.list_eval_rubrics()
    mock.assert_called_once_with("/api/v1/eval/rubrics")


@pytest.mark.asyncio
async def test_evaluate_job():
    with patch("vibops_mcp.tools.governance.client.post", new_callable=AsyncMock) as mock:
        mock.return_value = {"id": "eval-uuid", "status": "pending"}
        await governance.evaluate_job("job-uuid", "rubric-uuid")
    mock.assert_called_once_with(
        "/api/v1/eval/jobs/job-uuid/evaluate",
        body={"rubric_id": "rubric-uuid"},
    )


@pytest.mark.asyncio
async def test_get_job_evaluations():
    with patch("vibops_mcp.tools.governance.client.get", new_callable=AsyncMock) as mock:
        mock.return_value = []
        await governance.get_job_evaluations("job-uuid")
    mock.assert_called_once_with("/api/v1/eval/jobs/job-uuid/evaluations")

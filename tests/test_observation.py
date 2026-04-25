"""
Tests for vibops_mcp/tools/observation.py

Mocks client.get so no running VibOps instance is needed.
Verifies that each tool calls the correct endpoint with the correct params.
"""
import pytest
from unittest.mock import AsyncMock, patch

from vibops_mcp.tools import observation


# ── list_clusters ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_clusters_calls_correct_endpoint():
    with patch("vibops_mcp.tools.observation.client.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = []
        await observation.list_clusters()
    mock_get.assert_called_once_with("/api/v1/gateways")


# ── get_cluster_deployments ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_cluster_deployments_no_namespace():
    with patch("vibops_mcp.tools.observation.client.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = {}
        await observation.get_cluster_deployments("prod-cluster")
    mock_get.assert_called_once_with("/api/v1/clusters/prod-cluster/deployments", params={})


@pytest.mark.asyncio
async def test_get_cluster_deployments_with_namespace():
    with patch("vibops_mcp.tools.observation.client.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = {}
        await observation.get_cluster_deployments("prod-cluster", namespace="ai")
    mock_get.assert_called_once_with(
        "/api/v1/clusters/prod-cluster/deployments", params={"namespace": "ai"}
    )


# ── list_jobs ─────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_jobs_default_limit():
    with patch("vibops_mcp.tools.observation.client.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = []
        await observation.list_jobs()
    _, kwargs = mock_get.call_args
    assert kwargs["params"]["limit"] == 20


@pytest.mark.asyncio
async def test_list_jobs_limit_capped_at_100():
    with patch("vibops_mcp.tools.observation.client.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = []
        await observation.list_jobs(limit=500)
    _, kwargs = mock_get.call_args
    assert kwargs["params"]["limit"] == 100


@pytest.mark.asyncio
async def test_list_jobs_filters_forwarded():
    with patch("vibops_mcp.tools.observation.client.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = []
        await observation.list_jobs(status="failed", action="scale_cluster")
    _, kwargs = mock_get.call_args
    assert kwargs["params"]["status"] == "failed"
    assert kwargs["params"]["action"] == "scale_cluster"


# ── get_job ───────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_job_calls_correct_endpoint():
    with patch("vibops_mcp.tools.observation.client.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = {"id": "abc", "status": "success"}
        result = await observation.get_job("abc")
    mock_get.assert_called_once_with("/api/v1/jobs/abc")
    assert result["id"] == "abc"


@pytest.mark.asyncio
async def test_get_job_truncates_long_logs():
    long_logs = "x" * 2000
    with patch("vibops_mcp.tools.observation.client.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = {"id": "abc", "status": "success", "logs": long_logs}
        result = await observation.get_job("abc")
    assert len(result["logs"]) < len(long_logs)
    assert "truncated" in result["logs"]


@pytest.mark.asyncio
async def test_get_job_does_not_truncate_short_logs():
    with patch("vibops_mcp.tools.observation.client.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = {"id": "abc", "status": "success", "logs": "short log"}
        result = await observation.get_job("abc")
    assert result["logs"] == "short log"


# ── list_gateways ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_gateways_calls_correct_endpoint():
    with patch("vibops_mcp.tools.observation.client.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = []
        await observation.list_gateways()
    mock_get.assert_called_once_with("/api/v1/gateways")


# ── list_alerts ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_alerts_no_filters():
    with patch("vibops_mcp.tools.observation.client.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = []
        await observation.list_alerts()
    _, kwargs = mock_get.call_args
    assert kwargs["params"] == {}


@pytest.mark.asyncio
async def test_list_alerts_with_severity():
    with patch("vibops_mcp.tools.observation.client.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = []
        await observation.list_alerts(severity="critical")
    _, kwargs = mock_get.call_args
    assert kwargs["params"]["severity"] == "critical"


@pytest.mark.asyncio
async def test_list_alerts_resolved_false():
    with patch("vibops_mcp.tools.observation.client.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = []
        await observation.list_alerts(resolved=False)
    _, kwargs = mock_get.call_args
    assert kwargs["params"]["resolved"] == "false"


# ── metrics ───────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_gpu_metrics_default_hours():
    with patch("vibops_mcp.tools.observation.client.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = {}
        await observation.get_gpu_metrics()
    mock_get.assert_called_once_with("/api/v1/metrics/gpu", params={"hours": 24})


@pytest.mark.asyncio
async def test_get_cost_estimate_custom_hours():
    with patch("vibops_mcp.tools.observation.client.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = {}
        await observation.get_cost_estimate(hours=48)
    mock_get.assert_called_once_with("/api/v1/metrics/cost", params={"hours": 48})


# ── list_pipelines ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_pipelines_default_limit():
    with patch("vibops_mcp.tools.observation.client.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = []
        await observation.list_pipelines()
    mock_get.assert_called_once_with("/api/v1/pipelines", params={"limit": 10})


# ── list_kubectl_contexts ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_kubectl_contexts_endpoint():
    with patch("vibops_mcp.tools.observation.client.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = {}
        await observation.list_kubectl_contexts()
    mock_get.assert_called_once_with("/api/v1/clusters/contexts")

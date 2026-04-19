"""
Tests for vibops_mcp/tools/actions.py

Mocks client.post/client.get so no running VibOps instance is needed.
Verifies that each action builds the correct payload before sending it.
"""
import pytest
from unittest.mock import AsyncMock, patch

from vibops_mcp.tools import actions


JOB_PENDING = {"id": "test-job-id", "status": "pending"}
JOB_SUCCESS = {"id": "test-job-id", "status": "success", "result": {"output": "ok"}}


# ── scale_cluster ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_scale_cluster_sends_deployment_name():
    """deployment_name must reach the payload as 'name'."""
    with patch("vibops_mcp.tools.actions.client.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = JOB_PENDING
        await actions.scale_cluster("kind-vibops-dev", 3, deployment_name="llama3", namespace="default")

    _, kwargs = mock_post.call_args
    payload = kwargs["body"]["payload"] if "body" in kwargs else mock_post.call_args[0][1]["payload"]
    body = mock_post.call_args[1]["body"] if mock_post.call_args[1] else mock_post.call_args[0][1]
    payload = body["payload"]

    assert payload["name"] == "llama3"
    assert payload["namespace"] == "default"
    assert payload["replicas"] == 3
    assert payload["cluster"] == "kind-vibops-dev"


@pytest.mark.asyncio
async def test_scale_cluster_without_deployment_name_omits_name_key():
    """If deployment_name is None, 'name' should not be in the payload."""
    with patch("vibops_mcp.tools.actions.client.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = JOB_PENDING
        await actions.scale_cluster("kind-vibops-dev", 2)

    body = mock_post.call_args[1]["body"] if mock_post.call_args[1] else mock_post.call_args[0][1]
    payload = body["payload"]

    assert "name" not in payload
    assert payload["replicas"] == 2


@pytest.mark.asyncio
async def test_scale_cluster_without_namespace_omits_namespace_key():
    """If namespace is None, 'namespace' should not be in the payload."""
    with patch("vibops_mcp.tools.actions.client.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = JOB_PENDING
        await actions.scale_cluster("kind-vibops-dev", 1, deployment_name="ollama")

    body = mock_post.call_args[1]["body"] if mock_post.call_args[1] else mock_post.call_args[0][1]
    payload = body["payload"]

    assert "namespace" not in payload
    assert payload["name"] == "ollama"


@pytest.mark.asyncio
async def test_scale_cluster_action_name():
    """The job action must be 'scale_cluster'."""
    with patch("vibops_mcp.tools.actions.client.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = JOB_PENDING
        await actions.scale_cluster("kind-vibops-dev", 3, deployment_name="llama3")

    body = mock_post.call_args[1]["body"] if mock_post.call_args[1] else mock_post.call_args[0][1]
    assert body["action"] == "scale_cluster"


# ── run_kubectl ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_run_kubectl_sends_correct_payload():
    """run_kubectl must pass cluster and command to the payload."""
    with patch("vibops_mcp.tools.actions.client.post", new_callable=AsyncMock) as mock_post, \
         patch("vibops_mcp.tools.actions.client.get", new_callable=AsyncMock) as mock_get:
        mock_post.return_value = JOB_PENDING
        mock_get.return_value = JOB_SUCCESS
        result = await actions.run_kubectl("kind-vibops-dev", ["get", "pods", "-n", "ai"])

    body = mock_post.call_args[1]["body"] if mock_post.call_args[1] else mock_post.call_args[0][1]
    payload = body["payload"]

    assert payload["cluster"] == "kind-vibops-dev"
    assert payload["command"] == ["get", "pods", "-n", "ai"]
    assert body["action"] == "kubectl_exec"


@pytest.mark.asyncio
async def test_run_kubectl_polls_until_success():
    """_run_job_sync must poll get() until the job completes."""
    with patch("vibops_mcp.tools.actions.client.post", new_callable=AsyncMock) as mock_post, \
         patch("vibops_mcp.tools.actions.client.get", new_callable=AsyncMock) as mock_get, \
         patch("asyncio.sleep", new_callable=AsyncMock):
        mock_post.return_value = JOB_PENDING
        mock_get.side_effect = [
            {"id": "test-job-id", "status": "pending"},
            JOB_SUCCESS,
        ]
        result = await actions.run_kubectl("kind-vibops-dev", ["get", "nodes"])

    assert result["status"] == "success"
    assert mock_get.call_count == 2


# ── deploy_model ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_deploy_model_payload():
    with patch("vibops_mcp.tools.actions.client.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = JOB_PENDING
        await actions.deploy_model("kind-vibops-dev", "llama3:8b", namespace="default", replicas=2)

    body = mock_post.call_args[1]["body"] if mock_post.call_args[1] else mock_post.call_args[0][1]
    payload = body["payload"]

    assert payload["model"] == "llama3:8b"
    assert payload["replicas"] == 2
    assert payload["namespace"] == "default"
    assert body["action"] == "deploy_model"

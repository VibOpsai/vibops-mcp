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


# ── scale_deployment ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_scale_deployment_sends_correct_payload():
    """All fields must reach the payload with correct keys."""
    with patch("vibops_mcp.tools.actions.client.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = JOB_PENDING
        await actions.scale_deployment("kind-vibops-dev", "llama3", 3, namespace="default")

    body = mock_post.call_args[1]["body"] if mock_post.call_args[1] else mock_post.call_args[0][1]
    payload = body["payload"]

    assert payload["name"] == "llama3"
    assert payload["namespace"] == "default"
    assert payload["replicas"] == 3
    assert payload["cluster"] == "kind-vibops-dev"


@pytest.mark.asyncio
async def test_scale_deployment_default_namespace():
    """Namespace defaults to 'default' when not provided."""
    with patch("vibops_mcp.tools.actions.client.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = JOB_PENDING
        await actions.scale_deployment("kind-vibops-dev", "llama3", 2)

    body = mock_post.call_args[1]["body"] if mock_post.call_args[1] else mock_post.call_args[0][1]
    assert body["payload"]["namespace"] == "default"


@pytest.mark.asyncio
async def test_scale_deployment_action_name():
    """The backend action must remain 'scale_cluster' (Core API contract)."""
    with patch("vibops_mcp.tools.actions.client.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = JOB_PENDING
        await actions.scale_deployment("kind-vibops-dev", "llama3", 3)

    body = mock_post.call_args[1]["body"] if mock_post.call_args[1] else mock_post.call_args[0][1]
    assert body["action"] == "scale_cluster"


# ── deploy_model ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_deploy_model_payload():
    with patch("vibops_mcp.tools.actions.client.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = JOB_PENDING
        await actions.deploy_model("kind-vibops-dev", "llama3:8b", namespace="ai", replicas=2)

    body = mock_post.call_args[1]["body"] if mock_post.call_args[1] else mock_post.call_args[0][1]
    payload = body["payload"]

    assert payload["model"] == "llama3:8b"
    assert payload["replicas"] == 2
    assert payload["namespace"] == "ai"
    assert body["action"] == "deploy_model"


@pytest.mark.asyncio
async def test_deploy_model_optional_fields_omitted_when_none():
    """gpu_count, image, env should not appear in payload when not provided."""
    with patch("vibops_mcp.tools.actions.client.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = JOB_PENDING
        await actions.deploy_model("kind-vibops-dev", "llama3:8b")

    body = mock_post.call_args[1]["body"] if mock_post.call_args[1] else mock_post.call_args[0][1]
    payload = body["payload"]

    assert "gpu_count" not in payload
    assert "image" not in payload
    assert "env" not in payload


@pytest.mark.asyncio
async def test_deploy_model_optional_fields_included_when_provided():
    """gpu_count, image, env must be forwarded when provided."""
    with patch("vibops_mcp.tools.actions.client.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = JOB_PENDING
        await actions.deploy_model(
            "kind-vibops-dev", "llama3:8b",
            gpu_count=2, image="custom/llama:latest", env={"HF_TOKEN": "secret"}
        )

    body = mock_post.call_args[1]["body"] if mock_post.call_args[1] else mock_post.call_args[0][1]
    payload = body["payload"]

    assert payload["gpu_count"] == 2
    assert payload["image"] == "custom/llama:latest"
    assert payload["env"] == {"HF_TOKEN": "secret"}


# ── run_kubectl ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_run_kubectl_sends_correct_payload():
    """run_kubectl must pass cluster and command to the payload."""
    with patch("vibops_mcp.tools.actions.client.post", new_callable=AsyncMock) as mock_post, \
         patch("vibops_mcp.tools.actions.client.get", new_callable=AsyncMock) as mock_get:
        mock_post.return_value = JOB_PENDING
        mock_get.return_value = JOB_SUCCESS
        await actions.run_kubectl("kind-vibops-dev", ["get", "pods", "-n", "ai"])

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


@pytest.mark.asyncio
async def test_run_job_sync_timeout_sets_timed_out_flag():
    """When a job does not complete within timeout, timed_out must be set."""
    with patch("vibops_mcp.tools.actions.client.post", new_callable=AsyncMock) as mock_post, \
         patch("vibops_mcp.tools.actions.client.get", new_callable=AsyncMock) as mock_get, \
         patch("asyncio.sleep", new_callable=AsyncMock):
        mock_post.return_value = JOB_PENDING
        mock_get.return_value = {"id": "test-job-id", "status": "running"}
        result = await actions._run_job_sync("kubectl_exec", {"cluster": "x", "command": []}, timeout=4)

    assert result.get("timed_out") is True
    assert "get_job" in result.get("message", "")

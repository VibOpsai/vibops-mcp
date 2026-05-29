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


# ── helm_upgrade ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_helm_upgrade_payload():
    with patch("vibops_mcp.tools.actions.client.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = JOB_PENDING
        await actions.helm_upgrade(
            "kind-vibops-dev", "llama3", "vibops/llama3", namespace="ai",
            values={"replicas": 2}
        )

    body = mock_post.call_args[1]["body"] if mock_post.call_args[1] else mock_post.call_args[0][1]
    payload = body["payload"]

    assert body["action"] == "helm_upgrade"
    assert payload["cluster"] == "kind-vibops-dev"
    assert payload["name"] == "llama3"
    assert payload["chart"] == "vibops/llama3"
    assert payload["namespace"] == "ai"
    assert payload["values"] == {"replicas": 2}
    assert payload["wait"] is False


@pytest.mark.asyncio
async def test_helm_upgrade_no_values_omits_key():
    with patch("vibops_mcp.tools.actions.client.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = JOB_PENDING
        await actions.helm_upgrade("kind-vibops-dev", "nginx", "bitnami/nginx")

    body = mock_post.call_args[1]["body"] if mock_post.call_args[1] else mock_post.call_args[0][1]
    assert "values" not in body["payload"]


# ── helm_uninstall ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_helm_uninstall_payload():
    with patch("vibops_mcp.tools.actions.client.post", new_callable=AsyncMock) as mock_post, \
         patch("vibops_mcp.tools.actions.client.get", new_callable=AsyncMock) as mock_get, \
         patch("asyncio.sleep", new_callable=AsyncMock):
        mock_post.return_value = JOB_PENDING
        mock_get.return_value = JOB_SUCCESS
        await actions.helm_uninstall("kind-vibops-dev", "llama3", namespace="ai")

    body = mock_post.call_args[1]["body"] if mock_post.call_args[1] else mock_post.call_args[0][1]
    payload = body["payload"]

    assert body["action"] == "helm_uninstall"
    assert payload["cluster"] == "kind-vibops-dev"
    assert payload["name"] == "llama3"
    assert payload["namespace"] == "ai"


@pytest.mark.asyncio
async def test_helm_uninstall_default_namespace():
    with patch("vibops_mcp.tools.actions.client.post", new_callable=AsyncMock) as mock_post, \
         patch("vibops_mcp.tools.actions.client.get", new_callable=AsyncMock) as mock_get, \
         patch("asyncio.sleep", new_callable=AsyncMock):
        mock_post.return_value = JOB_PENDING
        mock_get.return_value = JOB_SUCCESS
        await actions.helm_uninstall("kind-vibops-dev", "nginx")

    body = mock_post.call_args[1]["body"] if mock_post.call_args[1] else mock_post.call_args[0][1]
    assert body["payload"]["namespace"] == "default"


# ── git_clone ─────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_git_clone_without_cluster():
    """Without cluster_name, repo is cloned but nothing is applied."""
    with patch("vibops_mcp.tools.actions.client.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = JOB_PENDING
        await actions.git_clone("https://github.com/acme/ml-models", branch="main")

    body = mock_post.call_args[1]["body"] if mock_post.call_args[1] else mock_post.call_args[0][1]
    payload = body["payload"]

    assert body["action"] == "git_clone"
    assert payload["repo_url"] == "https://github.com/acme/ml-models"
    assert payload["branch"] == "main"
    assert "cluster" not in payload


@pytest.mark.asyncio
async def test_git_clone_with_cluster_includes_cluster():
    """With cluster_name, cluster must be in the payload to trigger apply."""
    with patch("vibops_mcp.tools.actions.client.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = JOB_PENDING
        await actions.git_clone(
            "https://github.com/acme/ml-models", cluster_name="prod-cluster"
        )

    body = mock_post.call_args[1]["body"] if mock_post.call_args[1] else mock_post.call_args[0][1]
    assert body["payload"]["cluster"] == "prod-cluster"


# ── create_secret ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_secret_payload():
    with patch("vibops_mcp.tools.actions.client.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = {"name": "hf_token"}
        await actions.create_secret("hf_token", "hf-abc123", description="HuggingFace token")

    body = mock_post.call_args[1]["body"] if mock_post.call_args[1] else mock_post.call_args[0][1]

    assert body["name"] == "hf_token"
    assert body["value"] == "hf-abc123"
    assert body["description"] == "HuggingFace token"


@pytest.mark.asyncio
async def test_create_secret_no_description_omits_key():
    with patch("vibops_mcp.tools.actions.client.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = {"name": "hf_token"}
        await actions.create_secret("hf_token", "hf-abc123")

    body = mock_post.call_args[1]["body"] if mock_post.call_args[1] else mock_post.call_args[0][1]
    assert "description" not in body


# ── trigger_pipeline ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_trigger_pipeline_calls_correct_endpoint():
    with patch("vibops_mcp.tools.actions.client.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = {"status": "accepted"}
        await actions.trigger_pipeline("uuid-1234")

    path = mock_post.call_args[0][0] if mock_post.call_args[0] else mock_post.call_args[1].get("path", "")
    # Check the path contains the pipeline id
    call_args = mock_post.call_args
    assert "uuid-1234" in str(call_args)


@pytest.mark.asyncio
async def test_trigger_pipeline_with_payload():
    with patch("vibops_mcp.tools.actions.client.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = {"status": "accepted"}
        await actions.trigger_pipeline("uuid-1234", payload={"env": "prod"})

    body = mock_post.call_args[1]["body"] if mock_post.call_args[1] else mock_post.call_args[0][1]
    assert body == {"env": "prod"}


@pytest.mark.asyncio
async def test_trigger_pipeline_no_payload_sends_empty_dict():
    with patch("vibops_mcp.tools.actions.client.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = {"status": "accepted"}
        await actions.trigger_pipeline("uuid-1234")

    body = mock_post.call_args[1]["body"] if mock_post.call_args[1] else mock_post.call_args[0][1]
    assert body == {}


# ── _run_job_sync timeout ─────────────────────────────────────────────────────

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


# ── gateway_id passthrough ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_scale_deployment_forwards_gateway_id():
    """gateway_id must appear in the POST body when provided."""
    with patch("vibops_mcp.tools.actions.client.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = JOB_PENDING
        await actions.scale_deployment(
            "prod-cluster", "llama3", 3, gateway_id="gw-uuid-123"
        )

    body = mock_post.call_args[1]["body"] if mock_post.call_args[1] else mock_post.call_args[0][1]
    assert body["gateway_id"] == "gw-uuid-123"


@pytest.mark.asyncio
async def test_scale_deployment_no_gateway_id_omits_key():
    """When gateway_id is not provided, it must not appear in the POST body."""
    with patch("vibops_mcp.tools.actions.client.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = JOB_PENDING
        await actions.scale_deployment("prod-cluster", "llama3", 3)

    body = mock_post.call_args[1]["body"] if mock_post.call_args[1] else mock_post.call_args[0][1]
    assert "gateway_id" not in body


@pytest.mark.asyncio
async def test_deploy_model_forwards_gateway_id():
    with patch("vibops_mcp.tools.actions.client.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = JOB_PENDING
        await actions.deploy_model("prod-cluster", "llama3:8b", gateway_id="gw-uuid-456")

    body = mock_post.call_args[1]["body"] if mock_post.call_args[1] else mock_post.call_args[0][1]
    assert body["gateway_id"] == "gw-uuid-456"


@pytest.mark.asyncio
async def test_run_kubectl_forwards_gateway_id():
    with patch("vibops_mcp.tools.actions.client.post", new_callable=AsyncMock) as mock_post, \
         patch("vibops_mcp.tools.actions.client.get", new_callable=AsyncMock) as mock_get, \
         patch("asyncio.sleep", new_callable=AsyncMock):
        mock_post.return_value = JOB_PENDING
        mock_get.return_value = JOB_SUCCESS
        await actions.run_kubectl("prod-cluster", ["get", "pods"], gateway_id="gw-uuid-789")

    body = mock_post.call_args[1]["body"] if mock_post.call_args[1] else mock_post.call_args[0][1]
    assert body["gateway_id"] == "gw-uuid-789"


@pytest.mark.asyncio
async def test_helm_upgrade_forwards_gateway_id():
    with patch("vibops_mcp.tools.actions.client.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = JOB_PENDING
        await actions.helm_upgrade(
            "prod-cluster", "nginx", "bitnami/nginx", gateway_id="gw-uuid-abc"
        )

    body = mock_post.call_args[1]["body"] if mock_post.call_args[1] else mock_post.call_args[0][1]
    assert body["gateway_id"] == "gw-uuid-abc"


@pytest.mark.asyncio
async def test_git_clone_forwards_gateway_id():
    with patch("vibops_mcp.tools.actions.client.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = JOB_PENDING
        await actions.git_clone(
            "https://github.com/acme/ml-models", cluster_name="prod-cluster", gateway_id="gw-uuid-def"
        )

    body = mock_post.call_args[1]["body"] if mock_post.call_args[1] else mock_post.call_args[0][1]
    assert body["gateway_id"] == "gw-uuid-def"

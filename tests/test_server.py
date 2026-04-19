"""
Tests for vibops_mcp/server.py

Verifies that MCP tool wrappers pass arguments correctly to the underlying
actions functions — specifically catches positional-argument bugs like the
one where namespace was passed as deployment_name.
"""
import pytest
from unittest.mock import AsyncMock, patch


# ── scale_cluster ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_server_scale_cluster_passes_deployment_name():
    """server.scale_cluster must forward deployment_name to actions.scale_cluster."""
    from vibops_mcp import server

    with patch("vibops_mcp.server.actions.scale_cluster", new_callable=AsyncMock) as mock_action:
        mock_action.return_value = {"status": "pending"}
        await server.scale_cluster(
            cluster_name="kind-vibops-dev",
            replicas=3,
            deployment_name="llama3",
            namespace="default",
        )

    mock_action.assert_called_once_with("kind-vibops-dev", 3, "llama3", "default")


@pytest.mark.asyncio
async def test_server_scale_cluster_namespace_not_passed_as_deployment_name():
    """
    Regression: namespace must NOT end up in the deployment_name position.
    Before the fix: actions.scale_cluster(cluster, replicas, namespace)
    caused namespace="default" to be interpreted as deployment_name.
    """
    from vibops_mcp import server

    with patch("vibops_mcp.server.actions.scale_cluster", new_callable=AsyncMock) as mock_action:
        mock_action.return_value = {"status": "pending"}
        await server.scale_cluster(
            cluster_name="kind-vibops-dev",
            replicas=3,
            namespace="default",
        )

    args = mock_action.call_args[0]
    # args: (cluster_name, replicas, deployment_name, namespace)
    deployment_name_arg = args[2]
    namespace_arg = args[3]

    assert deployment_name_arg is None, (
        f"deployment_name should be None when not provided, got {deployment_name_arg!r}"
    )
    assert namespace_arg == "default", (
        f"namespace should be 'default', got {namespace_arg!r}"
    )


@pytest.mark.asyncio
async def test_server_scale_cluster_all_none_optional_args():
    """Calling with only required args must pass None for optional ones."""
    from vibops_mcp import server

    with patch("vibops_mcp.server.actions.scale_cluster", new_callable=AsyncMock) as mock_action:
        mock_action.return_value = {"status": "pending"}
        await server.scale_cluster(cluster_name="kind-vibops-dev", replicas=1)

    mock_action.assert_called_once_with("kind-vibops-dev", 1, None, None)


# ── run_kubectl ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_server_run_kubectl_passes_args():
    from vibops_mcp import server

    with patch("vibops_mcp.server.actions.run_kubectl", new_callable=AsyncMock) as mock_action:
        mock_action.return_value = {"status": "success"}
        await server.run_kubectl("kind-vibops-dev", ["get", "pods", "-n", "ai"])

    mock_action.assert_called_once_with("kind-vibops-dev", ["get", "pods", "-n", "ai"])


# ── deploy_model ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_server_deploy_model_passes_args():
    from vibops_mcp import server

    with patch("vibops_mcp.server.actions.deploy_model", new_callable=AsyncMock) as mock_action:
        mock_action.return_value = {"status": "pending"}
        await server.deploy_model(
            cluster_name="kind-vibops-dev",
            model_name="llama3:8b",
            namespace="default",
            replicas=2,
        )

    mock_action.assert_called_once_with("kind-vibops-dev", "llama3:8b", "default", 2, None)

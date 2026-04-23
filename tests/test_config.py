"""
Tests for vibops_mcp/tools/config.py

Mocks client.post/client.delete so no running VibOps instance is needed.
"""
import pytest
from unittest.mock import AsyncMock, patch

from vibops_mcp.tools import config


# ── set_cluster_rate ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_set_cluster_rate_payload():
    with patch("vibops_mcp.tools.config.client.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = {"rate_per_gpu_hour": 2.5, "currency": "USD"}
        await config.set_cluster_rate("prod-cluster", 2.5)

    mock_post.assert_called_once_with(
        "/api/v1/clusters/prod-cluster/rate",
        body={"rate_per_gpu_hour": 2.5, "currency": "USD"},
    )


@pytest.mark.asyncio
async def test_set_cluster_rate_currency_uppercased():
    with patch("vibops_mcp.tools.config.client.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = {}
        await config.set_cluster_rate("prod-cluster", 3.0, currency="eur")

    _, kwargs = mock_post.call_args
    assert kwargs["body"]["currency"] == "EUR"


# ── register_gateway ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_register_gateway_minimal():
    with patch("vibops_mcp.tools.config.client.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = {"id": "gw-1", "token": "tok"}
        await config.register_gateway("prod-vpc")

    mock_post.assert_called_once_with(
        "/api/v1/gateways",
        body={"name": "prod-vpc", "clusters": []},
    )


@pytest.mark.asyncio
async def test_register_gateway_with_description_and_clusters():
    with patch("vibops_mcp.tools.config.client.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = {"id": "gw-1", "token": "tok"}
        await config.register_gateway(
            "prod-vpc",
            description="Production VPC",
            clusters=["cluster-a", "cluster-b"],
        )

    _, kwargs = mock_post.call_args
    assert kwargs["body"]["description"] == "Production VPC"
    assert kwargs["body"]["clusters"] == ["cluster-a", "cluster-b"]


@pytest.mark.asyncio
async def test_register_gateway_no_description_key_omitted():
    with patch("vibops_mcp.tools.config.client.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = {}
        await config.register_gateway("gw")

    _, kwargs = mock_post.call_args
    assert "description" not in kwargs["body"]


# ── delete_gateway ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_delete_gateway_calls_correct_endpoint():
    with patch("vibops_mcp.tools.config.client.delete", new_callable=AsyncMock) as mock_delete:
        mock_delete.return_value = {"deleted": True}
        result = await config.delete_gateway("gw-abc123")

    mock_delete.assert_called_once_with("/api/v1/gateways/gw-abc123")
    assert result == {"deleted": True}

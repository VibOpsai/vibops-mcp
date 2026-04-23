"""
Tests for vibops_mcp/client.py

Mocks httpx.AsyncClient to test error handling, retry logic,
and header injection without a real VibOps instance.
"""
import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


def _make_response(status_code: int, json_data=None, content=b"{}"):
    r = MagicMock()
    r.status_code = status_code
    r.content = content if content else b""
    r.json.return_value = json_data or {}
    if status_code >= 400:
        from httpx import HTTPStatusError, Request, Response
        r.raise_for_status.side_effect = HTTPStatusError(
            message=f"HTTP {status_code}", request=MagicMock(), response=MagicMock()
        )
    else:
        r.raise_for_status.return_value = None
    return r


# ── environment validation ────────────────────────────────────────────────────

def test_missing_vibops_url_raises():
    env = {k: v for k, v in os.environ.items() if k != "VIBOPS_URL"}
    with patch.dict(os.environ, env, clear=True):
        from vibops_mcp import client
        with pytest.raises(RuntimeError, match="VIBOPS_URL"):
            client._base_url()


def test_missing_vibops_token_raises():
    env = {k: v for k, v in os.environ.items() if k != "VIBOPS_TOKEN"}
    with patch.dict(os.environ, env, clear=True):
        from vibops_mcp import client
        with pytest.raises(RuntimeError, match="VIBOPS_TOKEN"):
            client._token()


# ── headers ───────────────────────────────────────────────────────────────────

def test_client_includes_mcp_source_header():
    with patch.dict(os.environ, {"VIBOPS_URL": "http://localhost:8000", "VIBOPS_TOKEN": "tok"}):
        from vibops_mcp import client
        c = client._client()
        assert c.headers.get("x-vibops-source") == "mcp"
        assert c.headers.get("authorization") == "Bearer tok"


# ── retry logic ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_retries_on_502_then_succeeds():
    """GET should retry on 502 and succeed on the next attempt."""
    resp_502 = _make_response(502)
    resp_200 = _make_response(200, json_data={"ok": True})

    with patch.dict(os.environ, {"VIBOPS_URL": "http://localhost:8000", "VIBOPS_TOKEN": "tok"}):
        from vibops_mcp import client
        with patch("vibops_mcp.client._client") as mock_client_factory, \
             patch("asyncio.sleep", new_callable=AsyncMock):
            mock_http = AsyncMock()
            mock_http.request = AsyncMock(side_effect=[resp_502, resp_200])
            mock_http.__aenter__ = AsyncMock(return_value=mock_http)
            mock_http.__aexit__ = AsyncMock(return_value=False)
            mock_client_factory.return_value = mock_http

            result = await client.get("/api/v1/health")

    assert result == {"ok": True}
    assert mock_http.request.call_count == 2


@pytest.mark.asyncio
async def test_get_fails_after_max_retries():
    """GET should raise after exhausting retries on persistent 503."""
    resp_503 = _make_response(503)

    with patch.dict(os.environ, {"VIBOPS_URL": "http://localhost:8000", "VIBOPS_TOKEN": "tok"}):
        from vibops_mcp import client
        with patch("vibops_mcp.client._client") as mock_client_factory, \
             patch("asyncio.sleep", new_callable=AsyncMock):
            mock_http = AsyncMock()
            mock_http.request = AsyncMock(return_value=resp_503)
            mock_http.__aenter__ = AsyncMock(return_value=mock_http)
            mock_http.__aexit__ = AsyncMock(return_value=False)
            mock_client_factory.return_value = mock_http

            with pytest.raises(Exception):
                await client.get("/api/v1/health")

    assert mock_http.request.call_count == client._MAX_RETRIES


@pytest.mark.asyncio
async def test_get_does_not_retry_on_404():
    """GET should not retry on client errors (4xx)."""
    resp_404 = _make_response(404)

    with patch.dict(os.environ, {"VIBOPS_URL": "http://localhost:8000", "VIBOPS_TOKEN": "tok"}):
        from vibops_mcp import client
        with patch("vibops_mcp.client._client") as mock_client_factory:
            mock_http = AsyncMock()
            mock_http.request = AsyncMock(return_value=resp_404)
            mock_http.__aenter__ = AsyncMock(return_value=mock_http)
            mock_http.__aexit__ = AsyncMock(return_value=False)
            mock_client_factory.return_value = mock_http

            with pytest.raises(Exception):
                await client.get("/api/v1/missing")

    assert mock_http.request.call_count == 1


@pytest.mark.asyncio
async def test_delete_returns_deleted_true_on_204():
    """DELETE returning 204 No Content should return {deleted: True}."""
    resp_204 = _make_response(204, content=b"")

    with patch.dict(os.environ, {"VIBOPS_URL": "http://localhost:8000", "VIBOPS_TOKEN": "tok"}):
        from vibops_mcp import client
        with patch("vibops_mcp.client._client") as mock_client_factory:
            mock_http = AsyncMock()
            mock_http.request = AsyncMock(return_value=resp_204)
            mock_http.__aenter__ = AsyncMock(return_value=mock_http)
            mock_http.__aexit__ = AsyncMock(return_value=False)
            mock_client_factory.return_value = mock_http

            result = await client.delete("/api/v1/secrets/mykey")

    assert result == {"deleted": True}

"""
Async HTTP client wrapping the VibOps REST API.

Configuration (env vars):
  VIBOPS_URL    — base URL of your VibOps instance, e.g. https://vibops.example.com
  VIBOPS_TOKEN  — API token (create one in VibOps → Settings → API Tokens)
"""
import asyncio
import os
import httpx

_TIMEOUT = 60.0
_RETRY_STATUSES = {502, 503, 504}
_MAX_RETRIES = 3
_RETRY_BACKOFF = 1.0  # seconds, doubled on each attempt


def _base_url() -> str:
    url = os.environ.get("VIBOPS_URL", "").rstrip("/")
    if not url:
        raise RuntimeError(
            "VIBOPS_URL environment variable is not set. "
            "Set it to your VibOps instance URL, e.g. https://vibops.example.com"
        )
    return url


def _token() -> str:
    tok = os.environ.get("VIBOPS_TOKEN", "")
    if not tok:
        raise RuntimeError(
            "VIBOPS_TOKEN environment variable is not set. "
            "Create an API token in VibOps → Settings → API Tokens."
        )
    return tok


def _client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        base_url=_base_url(),
        headers={
            "Authorization": f"Bearer {_token()}",
            "X-VibOps-Source": "mcp",
        },
        timeout=_TIMEOUT,
    )


async def _request(method: str, path: str, **kwargs) -> dict:
    """Execute an HTTP request with exponential backoff retry on transient errors."""
    delay = _RETRY_BACKOFF
    for attempt in range(_MAX_RETRIES):
        async with _client() as c:
            r = await c.request(method, path, **kwargs)
        if r.status_code not in _RETRY_STATUSES or attempt == _MAX_RETRIES - 1:
            r.raise_for_status()
            if r.status_code == 204 or not r.content:
                return {"deleted": True}
            return r.json()
        await asyncio.sleep(delay)
        delay *= 2
    # unreachable — loop always returns or raises
    raise RuntimeError("retry loop exhausted")  # pragma: no cover


async def get(path: str, params: dict | None = None) -> dict:
    return await _request("GET", path, params=params)


async def post(path: str, body: dict | None = None) -> dict:
    return await _request("POST", path, json=body or {})


async def delete(path: str) -> dict:
    return await _request("DELETE", path)

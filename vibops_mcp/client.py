"""
Async HTTP client wrapping the VibOps REST API.

Configuration (env vars):
  VIBOPS_URL    — base URL of your VibOps instance, e.g. https://vibops.example.com
  VIBOPS_TOKEN  — API token (create one in VibOps → Settings → API Tokens)
"""
import os
import httpx

_TIMEOUT = 60.0


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


async def get(path: str, params: dict | None = None) -> dict:
    async with _client() as c:
        r = await c.get(path, params=params)
        r.raise_for_status()
        return r.json()


async def post(path: str, body: dict | None = None) -> dict:
    async with _client() as c:
        r = await c.post(path, json=body or {})
        r.raise_for_status()
        return r.json()


async def delete(path: str) -> dict:
    async with _client() as c:
        r = await c.delete(path)
        r.raise_for_status()
        if r.status_code == 204 or not r.content:
            return {"deleted": True}
        return r.json()

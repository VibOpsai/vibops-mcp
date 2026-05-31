"""
Tests for vibops_mcp/tools/finops.py
"""
import pytest
from unittest.mock import AsyncMock, patch

from vibops_mcp.tools import finops


@pytest.mark.asyncio
async def test_get_budget():
    with patch("vibops_mcp.tools.finops.client.get", new_callable=AsyncMock) as mock:
        mock.return_value = {"limit_usd": 5000, "consumed_usd": 1230.5}
        await finops.get_budget()
    mock.assert_called_once_with("/api/v1/budget")


@pytest.mark.asyncio
async def test_get_chargeback():
    with patch("vibops_mcp.tools.finops.client.get", new_callable=AsyncMock) as mock:
        mock.return_value = {"tenants": []}
        await finops.get_chargeback(2026, 5)
    mock.assert_called_once_with("/api/v1/chargeback/2026/5")


@pytest.mark.asyncio
async def test_get_spend_trend_default():
    with patch("vibops_mcp.tools.finops.client.get", new_callable=AsyncMock) as mock:
        mock.return_value = {"series": []}
        await finops.get_spend_trend()
    mock.assert_called_once_with("/api/v1/spend/trend", params={"days": 30})


@pytest.mark.asyncio
async def test_get_spend_trend_custom_days():
    with patch("vibops_mcp.tools.finops.client.get", new_callable=AsyncMock) as mock:
        mock.return_value = {"series": []}
        await finops.get_spend_trend(days=7)
    mock.assert_called_once_with("/api/v1/spend/trend", params={"days": 7})


@pytest.mark.asyncio
async def test_get_waste_analysis():
    with patch("vibops_mcp.tools.finops.client.get", new_callable=AsyncMock) as mock:
        mock.return_value = {"findings": []}
        await finops.get_waste_analysis()
    mock.assert_called_once_with("/api/v1/waste")

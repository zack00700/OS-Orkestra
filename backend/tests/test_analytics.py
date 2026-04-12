"""
Tests — Analytics (overview, ranking)
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_analytics_overview(client: AsyncClient, auth_headers: dict):
    """Vue d'ensemble analytics."""
    response = await client.get("/api/v1/analytics/overview?days=30", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "total_sent" in data
    assert "open_rate" in data
    assert "click_rate" in data
    assert "period_days" in data
    assert data["period_days"] == 30


@pytest.mark.asyncio
async def test_analytics_ranking(client: AsyncClient, auth_headers: dict):
    """Ranking des campagnes."""
    response = await client.get("/api/v1/analytics/campaigns/ranking?limit=10", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_analytics_unauthenticated(client: AsyncClient):
    """Analytics sans token."""
    response = await client.get("/api/v1/analytics/overview?days=30")
    assert response.status_code in (401, 403)

"""
Tests — Campagnes (création, liste, détails)
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_campaign(client: AsyncClient, auth_headers: dict):
    """Créer une campagne."""
    response = await client.post("/api/v1/campaigns/", headers=auth_headers, json={
        "name": "Test Campaign",
        "subject": "Test Subject",
        "campaign_type": "external",
        "channel": "email",
    })
    assert response.status_code in (200, 201)


@pytest.mark.asyncio
async def test_list_campaigns(client: AsyncClient, auth_headers: dict):
    """Lister les campagnes."""
    # Créer d'abord
    await client.post("/api/v1/campaigns/", headers=auth_headers, json={
        "name": "List Test",
        "subject": "Subject",
        "campaign_type": "external",
        "channel": "email",
    })

    response = await client.get("/api/v1/campaigns/?page=1&page_size=10", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data


@pytest.mark.asyncio
async def test_campaigns_unauthenticated(client: AsyncClient):
    """Accéder aux campagnes sans token."""
    response = await client.get("/api/v1/campaigns/?page=1&page_size=10")
    assert response.status_code in (401, 403)

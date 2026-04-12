"""
Tests — Scoring automatique (ouverture, clic, désinscription)
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_scoring_summary(client: AsyncClient, auth_headers: dict):
    """Endpoint résumé scoring accessible."""
    response = await client.get("/api/v1/tracking/scores/summary")
    assert response.status_code == 200
    data = response.json()
    assert "rules" in data
    # Les clés sont les valeurs lowercase de l'enum EventType
    assert data["rules"]["opened"] == 5
    assert data["rules"]["clicked"] == 10
    assert data["rules"]["unsubscribed"] == -20


@pytest.mark.asyncio
async def test_tracking_open_returns_pixel(client: AsyncClient):
    """Le pixel de tracking retourne une image GIF même si le contact n'existe pas."""
    response = await client.get("/api/v1/tracking/open/fake-campaign-id/fake-contact-id")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/gif"


@pytest.mark.asyncio
async def test_tracking_click_redirects(client: AsyncClient):
    """Le clic redirige vers l'URL cible même si le contact n'existe pas."""
    response = await client.get(
        "/api/v1/tracking/click/fake-campaign-id/fake-contact-id?url=https://opensid.com",
        follow_redirects=False,
    )
    assert response.status_code == 307
    assert "opensid.com" in response.headers.get("location", "")


@pytest.mark.asyncio
async def test_tracking_click_rejects_bad_url(client: AsyncClient):
    """Le clic refuse les URLs non http/https (anti Open Redirect)."""
    response = await client.get(
        "/api/v1/tracking/click/fake-campaign-id/fake-contact-id?url=javascript:alert(1)",
        follow_redirects=False,
    )
    assert response.status_code == 400

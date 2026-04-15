"""
Tests — Endpoints WhatsApp (send-test, send-text)
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_whatsapp_unauthenticated(client: AsyncClient):
    resp = await client.post("/api/v1/whatsapp/send-test", json={"to_phone": "33612345678"})
    assert resp.status_code in (401, 403)


@pytest.mark.asyncio
async def test_whatsapp_not_configured(client: AsyncClient, auth_headers: dict):
    """Sans config WhatsApp → 400."""
    from app.api.v1.endpoints import diffusion, whatsapp_send
    diffusion._config_cache.pop("whatsapp_config", None)
    whatsapp_send._rate_buckets.clear()
    resp = await client.post(
        "/api/v1/whatsapp/send-test",
        json={"to_phone": "33612345678"},
        headers=auth_headers,
    )
    assert resp.status_code == 400
    assert "non configuré" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_whatsapp_invalid_phone(client: AsyncClient, auth_headers: dict):
    """Numéro non-numérique → 400."""
    from app.api.v1.endpoints import diffusion, whatsapp_send
    diffusion._config_cache["whatsapp_config"] = {"api_token": "x", "phone_number_id": "y"}
    whatsapp_send._rate_buckets.clear()
    resp = await client.post(
        "/api/v1/whatsapp/send-test",
        json={"to_phone": "abcdefgh"},
        headers=auth_headers,
    )
    assert resp.status_code == 400
    assert "invalide" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_whatsapp_phone_too_short(client: AsyncClient, auth_headers: dict):
    """Numéro trop court → 422 (Pydantic)."""
    from app.api.v1.endpoints import whatsapp_send
    whatsapp_send._rate_buckets.clear()
    resp = await client.post(
        "/api/v1/whatsapp/send-test",
        json={"to_phone": "123"},
        headers=auth_headers,
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_whatsapp_send_text_requires_message(client: AsyncClient, auth_headers: dict):
    """send-text sans message → 422."""
    from app.api.v1.endpoints import whatsapp_send
    whatsapp_send._rate_buckets.clear()
    resp = await client.post(
        "/api/v1/whatsapp/send-text",
        json={"to_phone": "33612345678"},
        headers=auth_headers,
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_whatsapp_rate_limit(client: AsyncClient, auth_headers: dict):
    """Dépasser RATE_LIMIT_REQUESTS → 429."""
    from app.api.v1.endpoints import diffusion, whatsapp_send
    diffusion._config_cache.pop("whatsapp_config", None)  # Fail en 400 avant httpx
    whatsapp_send._rate_buckets.clear()

    for _ in range(whatsapp_send.RATE_LIMIT_REQUESTS):
        await client.post(
            "/api/v1/whatsapp/send-test",
            json={"to_phone": "33612345678"},
            headers=auth_headers,
        )

    resp = await client.post(
        "/api/v1/whatsapp/send-test",
        json={"to_phone": "33612345678"},
        headers=auth_headers,
    )
    assert resp.status_code == 429


def test_mask_phone():
    from app.api.v1.endpoints.whatsapp_send import _mask_phone
    assert _mask_phone("33612345678") == "3361234****"
    assert _mask_phone("1234") == "***"
    assert _mask_phone("") == "***"

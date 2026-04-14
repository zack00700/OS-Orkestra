"""
Tests — Module IA (proxy Anthropic)
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_ai_chat_unauthenticated(client: AsyncClient):
    """Accès /ai/chat sans auth."""
    resp = await client.post("/api/v1/ai/chat", json={"messages": [{"role": "user", "content": "hi"}]})
    assert resp.status_code in (401, 403)


@pytest.mark.asyncio
async def test_ai_chat_missing_api_key(client: AsyncClient, auth_headers: dict, monkeypatch):
    """Sans ANTHROPIC_API_KEY → 500."""
    from app.api.v1.endpoints import ai_chat
    monkeypatch.setattr(ai_chat, "ANTHROPIC_API_KEY", "")
    resp = await client.post(
        "/api/v1/ai/chat",
        json={"messages": [{"role": "user", "content": "hi"}]},
        headers=auth_headers,
    )
    assert resp.status_code == 500


@pytest.mark.asyncio
async def test_ai_chat_invalid_role_rejected(client: AsyncClient, auth_headers: dict, monkeypatch):
    """Role invalide rejeté par Pydantic (422)."""
    from app.api.v1.endpoints import ai_chat
    monkeypatch.setattr(ai_chat, "ANTHROPIC_API_KEY", "dummy")
    resp = await client.post(
        "/api/v1/ai/chat",
        json={"messages": [{"role": "system", "content": "hi"}]},
        headers=auth_headers,
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_ai_chat_empty_content_rejected(client: AsyncClient, auth_headers: dict, monkeypatch):
    """Content vide rejeté."""
    from app.api.v1.endpoints import ai_chat
    monkeypatch.setattr(ai_chat, "ANTHROPIC_API_KEY", "dummy")
    resp = await client.post(
        "/api/v1/ai/chat",
        json={"messages": [{"role": "user", "content": ""}]},
        headers=auth_headers,
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_ai_chat_oversized_content_rejected(client: AsyncClient, auth_headers: dict, monkeypatch):
    """Content > MAX_MESSAGE_CHARS rejeté."""
    from app.api.v1.endpoints import ai_chat
    monkeypatch.setattr(ai_chat, "ANTHROPIC_API_KEY", "dummy")
    huge = "a" * (ai_chat.MAX_MESSAGE_CHARS + 1)
    resp = await client.post(
        "/api/v1/ai/chat",
        json={"messages": [{"role": "user", "content": huge}]},
        headers=auth_headers,
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_ai_chat_rate_limit(client: AsyncClient, auth_headers: dict, monkeypatch):
    """Au-delà de RATE_LIMIT_REQUESTS, renvoie 429."""
    from app.api.v1.endpoints import ai_chat
    monkeypatch.setattr(ai_chat, "ANTHROPIC_API_KEY", "")  # Fail fast à 500 avant httpx
    ai_chat._rate_buckets.clear()

    # Simule RATE_LIMIT_REQUESTS appels qui passent (ils vont échouer en 500 car pas de clé,
    # mais le rate limit s'incrémente avant)
    for _ in range(ai_chat.RATE_LIMIT_REQUESTS):
        await client.post(
            "/api/v1/ai/chat",
            json={"messages": [{"role": "user", "content": "x"}]},
            headers=auth_headers,
        )

    # Le suivant doit être bloqué en 429
    resp = await client.post(
        "/api/v1/ai/chat",
        json={"messages": [{"role": "user", "content": "x"}]},
        headers=auth_headers,
    )
    assert resp.status_code == 429

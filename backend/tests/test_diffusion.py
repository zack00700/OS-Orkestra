"""
Tests — Diffusion (config SMTP, test)
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_diffusion_config(client: AsyncClient, auth_headers: dict):
    """Récupérer la config de diffusion."""
    response = await client.get("/api/v1/diffusion/config", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "smtp" in data
    assert "whatsapp" in data
    assert "sms" in data


@pytest.mark.asyncio
async def test_configure_smtp(client: AsyncClient, auth_headers: dict):
    """Configurer le SMTP."""
    response = await client.post("/api/v1/diffusion/config/smtp", headers=auth_headers, json={
        "host": "smtp.test.com",
        "port": 587,
        "username": "test@test.com",
        "password": "testpass",
        "use_tls": True,
        "from_email": "test@test.com",
        "from_name": "Test",
    })
    assert response.status_code == 200
    assert response.json()["status"] == "saved"


@pytest.mark.asyncio
async def test_diffusion_unauthenticated(client: AsyncClient):
    """Config diffusion sans token."""
    response = await client.get("/api/v1/diffusion/config")
    assert response.status_code in (401, 403)

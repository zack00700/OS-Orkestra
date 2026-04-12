"""
Tests — Authentification (login, register, me)
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, auth_headers: dict):
    """Login avec des identifiants valides."""
    response = await client.post("/api/v1/auth/login", json={
        "email": "test@orkestra.com",
        "password": "TestPass123",
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, auth_headers: dict):
    """Login avec un mauvais mot de passe."""
    response = await client.post("/api/v1/auth/login", json={
        "email": "test@orkestra.com",
        "password": "WrongPassword",
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_unknown_email(client: AsyncClient):
    """Login avec un email inconnu."""
    response = await client.post("/api/v1/auth/login", json={
        "email": "unknown@orkestra.com",
        "password": "TestPass123",
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_authenticated(client: AsyncClient, auth_headers: dict):
    """Accéder au profil avec un token valide."""
    response = await client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@orkestra.com"
    assert data["role"] == "admin"


@pytest.mark.asyncio
async def test_me_unauthenticated(client: AsyncClient):
    """Accéder au profil sans token."""
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 403 or response.status_code == 401


@pytest.mark.asyncio
async def test_register_new_user(client: AsyncClient, auth_headers: dict):
    """Créer un nouveau compte."""
    response = await client.post("/api/v1/auth/register", json={
        "email": "new@orkestra.com",
        "password": "NewPass123!",
        "full_name": "New User",
        "role": "viewer",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "new@orkestra.com"


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient, auth_headers: dict):
    """Créer un compte avec un email existant."""
    response = await client.post("/api/v1/auth/register", json={
        "email": "test@orkestra.com",
        "password": "AnotherPass123",
        "full_name": "Duplicate",
        "role": "viewer",
    })
    assert response.status_code == 409

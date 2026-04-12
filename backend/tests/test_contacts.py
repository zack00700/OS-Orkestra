"""
Tests — Contacts (CRUD, stats, recherche)
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_contact(client: AsyncClient, auth_headers: dict):
    """Créer un contact."""
    response = await client.post("/api/v1/contacts/", headers=auth_headers, json={
        "email": "contact1@test.com",
        "first_name": "Hassan",
        "last_name": "Alami",
        "company": "SolarTech",
        "country": "Maroc",
        "city": "Casablanca",
        "source": "manual",
    })
    assert response.status_code in (200, 201)


@pytest.mark.asyncio
async def test_list_contacts(client: AsyncClient, auth_headers: dict):
    """Lister les contacts."""
    # Créer un contact d'abord
    await client.post("/api/v1/contacts/", headers=auth_headers, json={
        "email": "list@test.com",
        "first_name": "Test",
        "last_name": "List",
        "source": "manual",
    })

    response = await client.get("/api/v1/contacts/?page=1&page_size=10", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_search_contacts(client: AsyncClient, auth_headers: dict):
    """Rechercher des contacts."""
    await client.post("/api/v1/contacts/", headers=auth_headers, json={
        "email": "findme@test.com",
        "first_name": "Findable",
        "last_name": "Person",
        "source": "manual",
    })

    response = await client.get("/api/v1/contacts/?search=Findable", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_contact_stats(client: AsyncClient, auth_headers: dict):
    """Statistiques des contacts."""
    await client.post("/api/v1/contacts/", headers=auth_headers, json={
        "email": "stats@test.com",
        "first_name": "Stats",
        "source": "manual",
    })

    response = await client.get("/api/v1/contacts/stats", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "active" in data
    assert "by_source" in data


@pytest.mark.asyncio
async def test_contacts_unauthenticated(client: AsyncClient):
    """Accéder aux contacts sans token."""
    response = await client.get("/api/v1/contacts/?page=1&page_size=10")
    assert response.status_code in (401, 403)

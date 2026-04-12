"""
Tests — Segments (création, liste, comptage dynamique, contacts)
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_segment(client: AsyncClient, auth_headers: dict):
    """Créer un segment avec filtre."""
    response = await client.post("/api/v1/segments/", headers=auth_headers, json={
        "name": "Test Maroc",
        "description": "Contacts marocains",
        "filter_criteria": {"country": "Maroc"},
        "is_dynamic": True,
    })
    assert response.status_code in (200, 201)
    data = response.json()
    assert data["name"] == "Test Maroc"
    assert "contact_count" in data


@pytest.mark.asyncio
async def test_list_segments(client: AsyncClient, auth_headers: dict):
    """Lister les segments."""
    # Créer d'abord
    await client.post("/api/v1/segments/", headers=auth_headers, json={
        "name": "List Seg",
        "description": "Test",
        "filter_criteria": {},
    })

    response = await client.get("/api/v1/segments/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_segment_dynamic_count(client: AsyncClient, auth_headers: dict):
    """Le comptage dynamique reflète les contacts réels."""
    # Créer un contact marocain
    await client.post("/api/v1/contacts/", headers=auth_headers, json={
        "email": "maroc@test.com",
        "first_name": "Test",
        "country": "Maroc",
        "source": "manual",
    })

    # Créer un segment Maroc
    seg_response = await client.post("/api/v1/segments/", headers=auth_headers, json={
        "name": "Dynamic Maroc",
        "filter_criteria": {"country": "Maroc"},
    })
    data = seg_response.json()
    assert data["contact_count"] >= 1


@pytest.mark.asyncio
async def test_segment_contacts(client: AsyncClient, auth_headers: dict):
    """Voir les contacts d'un segment."""
    # Créer un contact
    await client.post("/api/v1/contacts/", headers=auth_headers, json={
        "email": "segcontact@test.com",
        "first_name": "Seg",
        "country": "Ghana",
        "source": "manual",
    })

    # Créer un segment
    seg_response = await client.post("/api/v1/segments/", headers=auth_headers, json={
        "name": "Ghana Seg",
        "filter_criteria": {"country": "Ghana"},
    })
    seg_id = seg_response.json()["id"]

    # Lister les contacts du segment
    response = await client.get(f"/api/v1/segments/{seg_id}/contacts", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "contacts" in data
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_delete_segment(client: AsyncClient, auth_headers: dict):
    """Supprimer un segment."""
    seg_response = await client.post("/api/v1/segments/", headers=auth_headers, json={
        "name": "To Delete",
        "filter_criteria": {},
    })
    seg_id = seg_response.json()["id"]

    response = await client.delete(f"/api/v1/segments/{seg_id}", headers=auth_headers)
    assert response.status_code == 200

"""
Tests — Sprint 7 (Template editor), Sprint 8 (Settings), Sprint 9 (CSV import)
"""
import pytest
import io
from httpx import AsyncClient


# ══════════════════════════════════════════════════════════
# SPRINT 7 — Template Editor
# ══════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_create_template(client: AsyncClient, auth_headers: dict):
    """Créer un template."""
    response = await client.post(
        "/api/v1/templates/",
        json={
            "name": "Test Template",
            "subject": "Hello {{first_name}}",
            "html_content": "<html><body><h1>Hello</h1></body></html>",
            "category": "newsletter",
        },
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Template"
    assert "id" in data


@pytest.mark.asyncio
async def test_list_templates(client: AsyncClient, auth_headers: dict):
    """Lister les templates."""
    response = await client.get("/api/v1/templates/", headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_update_template(client: AsyncClient, auth_headers: dict):
    """Créer puis mettre à jour un template."""
    # Create
    create_resp = await client.post(
        "/api/v1/templates/",
        json={
            "name": "To Update",
            "subject": "Old Subject",
            "html_content": "<p>old</p>",
            "category": "test",
        },
        headers=auth_headers,
    )
    template_id = create_resp.json()["id"]

    # Update
    update_resp = await client.put(
        f"/api/v1/templates/{template_id}",
        json={
            "html_content": "<p>new content</p>",
            "subject": "New Subject",
        },
        headers=auth_headers,
    )
    assert update_resp.status_code == 200
    assert "mis à jour" in update_resp.json()["message"]


@pytest.mark.asyncio
async def test_template_unauthenticated(client: AsyncClient):
    """Accès templates sans auth."""
    response = await client.get("/api/v1/templates/")
    assert response.status_code in (401, 403)


# ══════════════════════════════════════════════════════════
# SPRINT 8 — Persistance config diffusion (DB)
# ══════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_diffusion_smtp_persists(client: AsyncClient, auth_headers: dict):
    """Configure SMTP, GET config redonne les valeurs (masquées)."""
    from app.api.v1.endpoints import diffusion
    diffusion._config_cache.clear()

    smtp_payload = {
        "host": "smtp.example.com",
        "port": 587,
        "username": "user@example.com",
        "password": "secret123",
        "from_email": "noreply@example.com",
        "from_name": "Test Orkestra",
        "use_tls": True,
    }
    post_resp = await client.post(
        "/api/v1/diffusion/config/smtp",
        json=smtp_payload,
        headers=auth_headers,
    )
    assert post_resp.status_code == 200

    get_resp = await client.get("/api/v1/diffusion/config", headers=auth_headers)
    assert get_resp.status_code == 200
    smtp_cfg = get_resp.json()["smtp"]
    assert smtp_cfg.get("host") == "smtp.example.com"
    assert smtp_cfg.get("port") == 587
    assert smtp_cfg.get("password") == "****"
    assert smtp_cfg.get("status") == "configured"


# ══════════════════════════════════════════════════════════
# SPRINT 9 — CSV Import
# ══════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_csv_preview(client: AsyncClient, auth_headers: dict):
    """Upload CSV pour preview."""
    csv_content = "email,first_name,last_name,company\ntest@example.com,Jean,Dupont,ACME\ntest2@example.com,Marie,Martin,Corp"
    files = {"file": ("test.csv", io.BytesIO(csv_content.encode()), "text/csv")}
    response = await client.post(
        "/api/v1/import/csv/preview",
        files=files,
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_columns"] == 4
    assert len(data["preview_rows"]) == 2
    suggested = data["mapping_suggestions"].values()
    assert "email" in suggested
    assert "first_name" in suggested
    assert "company" in suggested


@pytest.mark.asyncio
async def test_csv_import_rejects_non_csv(client: AsyncClient, auth_headers: dict):
    """Refuser les fichiers non-CSV."""
    files = {"file": ("test.txt", io.BytesIO(b"hello"), "text/plain")}
    response = await client.post(
        "/api/v1/import/csv/preview",
        files=files,
        headers=auth_headers,
    )
    assert response.status_code == 400

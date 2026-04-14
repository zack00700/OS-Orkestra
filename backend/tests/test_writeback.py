"""
Tests — Sprint 10 : Write-back CRM
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_writeback_config_not_configured(client: AsyncClient, auth_headers: dict):
    """Config write-back non configurée par défaut."""
    response = await client.get("/api/v1/sync/config", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data.get("status") == "not_configured"


@pytest.mark.asyncio
async def test_writeback_preview(client: AsyncClient, auth_headers: dict):
    """Preview des contacts à synchroniser."""
    response = await client.get("/api/v1/sync/preview", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "total_syncable" in data
    assert "preview" in data


@pytest.mark.asyncio
async def test_writeback_logs_empty(client: AsyncClient, auth_headers: dict):
    """Historique sync vide au départ."""
    response = await client.get("/api/v1/sync/logs", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "logs" in data


@pytest.mark.asyncio
async def test_writeback_execute_no_config(client: AsyncClient, auth_headers: dict):
    """Execute write-back sans config → erreur 400."""
    response = await client.post("/api/v1/sync/execute", headers=auth_headers)
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_writeback_unauthenticated(client: AsyncClient):
    """Accès sync sans auth."""
    response = await client.get("/api/v1/sync/config")
    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_writeback_config_roundtrip(client: AsyncClient, auth_headers: dict):
    """Save config → GET config : round-trip + masquage password."""
    from app.api.v1.endpoints import writeback
    writeback._writeback_cache.clear()

    payload = {
        "config": {
            "host": "crm.example.com",
            "port": 1433,
            "username": "crm_user",
            "password": "super_secret",
            "database": "CRM_DB",
            "table": "Clients",
            "key_field": "ClientID",
        },
        "field_mapping": [
            {"orkestra_field": "email", "crm_field": "Email"},
            {"orkestra_field": "lead_score", "crm_field": "Score"},
        ],
    }
    save_resp = await client.post("/api/v1/sync/config", json=payload, headers=auth_headers)
    assert save_resp.status_code == 200

    get_resp = await client.get("/api/v1/sync/config", headers=auth_headers)
    assert get_resp.status_code == 200
    cfg = get_resp.json()
    assert cfg["host"] == "crm.example.com"
    assert cfg["table"] == "Clients"
    assert cfg["key_field"] == "ClientID"
    assert cfg["password"] == "****"
    assert len(cfg["field_mapping"]) == 2


@pytest.mark.asyncio
async def test_writeback_rejects_sql_injection_in_table(client: AsyncClient, auth_headers: dict):
    """Rejette les identifiants SQL malicieux (table, crm_field)."""
    from app.api.v1.endpoints import writeback
    writeback._writeback_cache.clear()

    payload = {
        "config": {
            "host": "crm.example.com", "port": 1433, "username": "u", "password": "p",
            "database": "db", "table": "Clients; DROP TABLE contacts--",
            "key_field": "ClientID",
        },
        "field_mapping": [{"orkestra_field": "email", "crm_field": "Email"}],
    }
    resp = await client.post("/api/v1/sync/config", json=payload, headers=auth_headers)
    assert resp.status_code == 400

    payload["config"]["table"] = "Clients"
    payload["field_mapping"] = [{"orkestra_field": "email", "crm_field": "Email; DROP--"}]
    resp = await client.post("/api/v1/sync/config", json=payload, headers=auth_headers)
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_writeback_rejects_unauthorized_orkestra_field(client: AsyncClient, auth_headers: dict):
    """Rejette un orkestra_field hors whitelist."""
    from app.api.v1.endpoints import writeback
    writeback._writeback_cache.clear()

    payload = {
        "config": {
            "host": "crm.example.com", "port": 1433, "username": "u", "password": "p",
            "database": "db", "table": "Clients", "key_field": "ClientID",
        },
        "field_mapping": [{"orkestra_field": "hashed_password", "crm_field": "Pwd"}],
    }
    resp = await client.post("/api/v1/sync/config", json=payload, headers=auth_headers)
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_writeback_preserves_password_when_empty(client: AsyncClient, auth_headers: dict):
    """Re-save avec password vide doit conserver l'ancien."""
    from app.api.v1.endpoints import writeback
    writeback._writeback_cache.clear()

    initial = {
        "config": {
            "host": "crm.example.com", "port": 1433, "username": "u", "password": "original_pwd",
            "database": "db", "table": "Clients", "key_field": "ClientID",
        },
        "field_mapping": [{"orkestra_field": "email", "crm_field": "Email"}],
    }
    r = await client.post("/api/v1/sync/config", json=initial, headers=auth_headers)
    assert r.status_code == 200

    # Re-save avec password vide → ancien conservé
    update = {
        "config": {
            "host": "crm.newhost.com", "port": 1433, "username": "u", "password": "",
            "database": "db", "table": "Clients", "key_field": "ClientID",
        },
        "field_mapping": [{"orkestra_field": "email", "crm_field": "Email"}],
    }
    r = await client.post("/api/v1/sync/config", json=update, headers=auth_headers)
    assert r.status_code == 200

    assert writeback._writeback_cache["writeback_config"]["password"] == "original_pwd"
    assert writeback._writeback_cache["writeback_config"]["host"] == "crm.newhost.com"


@pytest.mark.asyncio
async def test_writeback_execute_with_injection_in_contact_ids(client: AsyncClient, auth_headers: dict):
    """Contact_ids malicieux sont traités comme params bindés (pas d'injection)."""
    from app.api.v1.endpoints import writeback
    writeback._writeback_cache.clear()

    # Config valide
    save_payload = {
        "config": {
            "host": "nope.invalid", "port": 1433, "username": "u", "password": "p",
            "database": "db", "table": "Clients", "key_field": "ClientID",
        },
        "field_mapping": [{"orkestra_field": "email", "crm_field": "Email"}],
    }
    await client.post("/api/v1/sync/config", json=save_payload, headers=auth_headers)

    # contact_ids avec payload injection — doit juste ne pas trouver de contact, pas crasher
    resp = await client.post(
        "/api/v1/sync/execute",
        json={"contact_ids": ["' OR 1=1--", "nonexistent-id"]},
        headers=auth_headers,
    )
    # Soit no_data (param bindé = aucun match), soit completed/partial si pymssql tente la connexion
    # L'essentiel : pas de 500 SQL error, pas de crash
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("status") in ("no_data", "completed", "partial")

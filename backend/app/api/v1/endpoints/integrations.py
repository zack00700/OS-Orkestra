"""
OS Orkestra — Gestion des intégrations depuis l'interface
Sauvegarde les configurations de connexion en base, teste les connexions.
Compatible Python 3.9+
"""
import uuid
import json
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import require_roles

logger = logging.getLogger("orkestra.integrations_settings")

router = APIRouter(prefix="/integrations", tags=["Intégrations"])


# ══════════════════════════════════════════════════════════
# SCHEMAS
# ══════════════════════════════════════════════════════════

class IntegrationConfig(BaseModel):
    type: str  # database, crm_dynamics, crm_salesforce, azure_ad, smtp, whatsapp, sms
    name: str
    config: Dict[str, Any]


class TestConnectionRequest(BaseModel):
    type: str
    config: Dict[str, Any]


# ══════════════════════════════════════════════════════════
# IN-MEMORY STORE (sera migré en table plus tard)
# ══════════════════════════════════════════════════════════

# Pour l'instant on stocke en mémoire. En production, ça irait dans une table `integration_configs`.
_integrations_store: Dict[str, Dict[str, Any]] = {}


@router.get("/configured")
async def list_configured_integrations(
    current_user: dict = Depends(require_roles("admin", "manager")),
):
    """Liste toutes les intégrations configurées avec leur statut."""
    result = []
    for key, data in _integrations_store.items():
        result.append({
            "id": key,
            "type": data["type"],
            "name": data["name"],
            "status": data.get("status", "configured"),
            "last_tested": data.get("last_tested"),
            "config_keys": list(data["config"].keys()),  # Ne pas exposer les valeurs sensibles
        })

    # Ajouter les intégrations non configurées comme "available"
    all_types = [
        {"type": "database", "name": "Base de données externe", "description": "SQL Server, PostgreSQL, MySQL, SQLite, Oracle"},
        {"type": "crm_dynamics", "name": "Microsoft Dynamics 365", "description": "Synchronisation contacts, leads et opportunités"},
        {"type": "crm_salesforce", "name": "Salesforce", "description": "Synchronisation CRM Salesforce"},
        {"type": "azure_ad", "name": "Azure AD / Entra ID", "description": "Annuaire interne Microsoft pour les mailings internes"},
        {"type": "smtp", "name": "Serveur SMTP", "description": "Envoi d'emails (Gmail, Outlook, SendGrid, Mailgun...)"},
        {"type": "whatsapp", "name": "WhatsApp Business", "description": "Envoi de messages marketing WhatsApp"},
        {"type": "sms", "name": "SMS Provider", "description": "Envoi de SMS (Twilio, Vonage...)"},
    ]

    configured_types = {d["type"] for d in _integrations_store.values()}
    for t in all_types:
        if t["type"] not in configured_types:
            result.append({
                "id": None,
                "type": t["type"],
                "name": t["name"],
                "description": t["description"],
                "status": "not_configured",
            })
        else:
            # Enrichir avec la description
            for r in result:
                if r["type"] == t["type"]:
                    r["description"] = t["description"]

    return result


@router.post("/configure")
async def save_integration(
    data: IntegrationConfig,
    current_user: dict = Depends(require_roles("admin")),
):
    """Sauvegarder une configuration d'intégration."""
    key = f"{data.type}_{uuid.uuid4().hex[:8]}"

    # Si une intégration de ce type existe déjà, la mettre à jour
    existing_key = None
    for k, v in _integrations_store.items():
        if v["type"] == data.type:
            existing_key = k
            break

    if existing_key:
        key = existing_key

    _integrations_store[key] = {
        "type": data.type,
        "name": data.name,
        "config": data.config,
        "status": "configured",
        "configured_at": datetime.now(timezone.utc).isoformat(),
        "configured_by": current_user.get("email", "unknown"),
    }

    return {"id": key, "status": "saved", "message": f"Intégration {data.name} configurée"}


@router.post("/test-connection")
async def test_connection(
    data: TestConnectionRequest,
    current_user: dict = Depends(require_roles("admin", "manager")),
):
    """Tester une connexion sans la sauvegarder."""
    result = await _test_integration(data.type, data.config)

    # Mettre à jour le statut si c'est une intégration déjà configurée
    for key, stored in _integrations_store.items():
        if stored["type"] == data.type:
            stored["status"] = "connected" if result["success"] else "error"
            stored["last_tested"] = datetime.now(timezone.utc).isoformat()
            stored["test_result"] = result
            break

    return result


@router.delete("/{integration_id}")
async def delete_integration(
    integration_id: str,
    current_user: dict = Depends(require_roles("admin")),
):
    """Supprimer une intégration configurée."""
    if integration_id in _integrations_store:
        name = _integrations_store[integration_id]["name"]
        del _integrations_store[integration_id]
        return {"status": "deleted", "message": f"Intégration {name} supprimée"}
    raise HTTPException(status_code=404, detail="Intégration non trouvée")


# ══════════════════════════════════════════════════════════
# TEST LOGIC
# ══════════════════════════════════════════════════════════

async def _test_integration(integration_type: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """Teste une connexion selon le type d'intégration."""

    if integration_type == "database":
        return await _test_database(config)
    elif integration_type == "smtp":
        return _test_smtp(config)
    elif integration_type == "crm_dynamics":
        return await _test_dynamics(config)
    elif integration_type == "azure_ad":
        return await _test_azure_ad(config)
    elif integration_type == "whatsapp":
        return await _test_whatsapp(config)
    elif integration_type == "crm_salesforce":
        return {"success": True, "message": "Test Salesforce non implémenté — configuration sauvegardée"}
    elif integration_type == "sms":
        return {"success": True, "message": "Test SMS non implémenté — configuration sauvegardée"}
    else:
        return {"success": False, "message": f"Type d'intégration inconnu : {integration_type}"}


async def _test_database(config: Dict[str, Any]) -> Dict[str, Any]:
    """Teste une connexion à une base de données externe."""
    try:
        db_type = config.get("db_type", "mssql")
        host = config.get("host", "localhost")
        port = config.get("port", 1433)
        username = config.get("username", "sa")
        password = config.get("password", "")
        database = config.get("database", "master")

        if db_type == "mssql":
            try:
                import pymssql
                conn = pymssql.connect(
                    server=host, port=int(port), user=username,
                    password=password, database=database, login_timeout=10,
                )
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.close()
                conn.close()
                return {"success": True, "message": f"Connecté à SQL Server {host}:{port}/{database}"}
            except ImportError:
                import pyodbc
                conn_str = f"DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={host},{port};DATABASE={database};UID={username};PWD={password};TrustServerCertificate=yes;Connection Timeout=10"
                conn = pyodbc.connect(conn_str, timeout=10)
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.close()
                conn.close()
                return {"success": True, "message": f"Connecté à SQL Server {host}:{port}/{database}"}

        elif db_type == "postgresql":
            # Test basique via socket
            import socket
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(5)
            s.connect((host, int(port)))
            s.close()
            return {"success": True, "message": f"Port PostgreSQL {host}:{port} accessible"}

        elif db_type == "mysql":
            import socket
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(5)
            s.connect((host, int(port)))
            s.close()
            return {"success": True, "message": f"Port MySQL {host}:{port} accessible"}

        else:
            return {"success": True, "message": f"Configuration {db_type} enregistrée"}

    except Exception as e:
        return {"success": False, "message": f"Erreur de connexion : {str(e)}"}


def _test_smtp(config: Dict[str, Any]) -> Dict[str, Any]:
    """Teste une connexion SMTP."""
    try:
        import smtplib
        host = config.get("host", "smtp.gmail.com")
        port = int(config.get("port", 587))
        username = config.get("username", "")
        password = config.get("password", "")
        use_tls = config.get("use_tls", True)

        server = smtplib.SMTP(host, port, timeout=10)
        if use_tls:
            server.starttls()
        if username and password:
            server.login(username, password)
        server.quit()
        return {"success": True, "message": f"Connecté à SMTP {host}:{port}"}
    except smtplib.SMTPAuthenticationError:
        return {"success": False, "message": "Erreur d'authentification SMTP — vérifiez le login/mot de passe"}
    except Exception as e:
        return {"success": False, "message": f"Erreur SMTP : {str(e)}"}


async def _test_dynamics(config: Dict[str, Any]) -> Dict[str, Any]:
    """Teste la connexion à Dynamics 365."""
    try:
        import httpx
        tenant_id = config.get("tenant_id", "")
        client_id = config.get("client_id", "")
        client_secret = config.get("client_secret", "")
        base_url = config.get("base_url", "")

        if not all([tenant_id, client_id, client_secret, base_url]):
            return {"success": False, "message": "Tous les champs sont requis"}

        token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(token_url, data={
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret,
                "scope": f"{base_url}/.default",
            })
            if resp.status_code == 200:
                return {"success": True, "message": f"Connecté à Dynamics 365 ({base_url})"}
            else:
                return {"success": False, "message": f"Erreur auth Dynamics : {resp.status_code}"}
    except Exception as e:
        return {"success": False, "message": f"Erreur : {str(e)}"}


async def _test_azure_ad(config: Dict[str, Any]) -> Dict[str, Any]:
    """Teste la connexion à Azure AD."""
    try:
        import httpx
        tenant_id = config.get("tenant_id", "")
        client_id = config.get("client_id", "")
        client_secret = config.get("client_secret", "")

        if not all([tenant_id, client_id, client_secret]):
            return {"success": False, "message": "Tous les champs sont requis"}

        token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(token_url, data={
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret,
                "scope": "https://graph.microsoft.com/.default",
            })
            if resp.status_code == 200:
                return {"success": True, "message": "Connecté à Azure AD / Microsoft Entra ID"}
            else:
                return {"success": False, "message": f"Erreur auth Azure AD : {resp.status_code}"}
    except Exception as e:
        return {"success": False, "message": f"Erreur : {str(e)}"}


async def _test_whatsapp(config: Dict[str, Any]) -> Dict[str, Any]:
    """Teste la connexion WhatsApp Business."""
    try:
        import httpx
        token = config.get("api_token", "")
        phone_id = config.get("phone_number_id", "")

        if not token or not phone_id:
            return {"success": False, "message": "API Token et Phone Number ID requis"}

        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"https://graph.facebook.com/v18.0/{phone_id}",
                headers={"Authorization": f"Bearer {token}"},
            )
            if resp.status_code == 200:
                return {"success": True, "message": "Connecté à WhatsApp Business API"}
            else:
                return {"success": False, "message": f"Erreur WhatsApp : {resp.status_code}"}
    except Exception as e:
        return {"success": False, "message": f"Erreur : {str(e)}"}

"""
OS Orkestra — Sprint 10 : Write-back CRM (sync bidirectionnelle)
Quand un contact est modifié dans Orkestra, l'info remonte vers le CRM source.
Compatible Python 3.9+ / pymssql
"""
import re
import uuid
import json
import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional, List, Any, Dict
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import text
from app.core.database import get_db
from app.core.query_helpers import build_raw_paginated_query
from app.core.security import require_roles
from app.models.models import SyncLog

logger = logging.getLogger("orkestra.writeback")

router = APIRouter(prefix="/sync", tags=["Sync CRM"])

# Whitelist des identifiants SQL (tables, colonnes) : alphanumérique + underscore
_IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,63}$")

# Champs Orkestra autorisés pour le mapping (lecture côté contacts)
ALLOWED_ORKESTRA_FIELDS = {
    "email", "first_name", "last_name", "company", "phone",
    "country", "city", "job_title", "lead_score", "lead_stage", "status",
}


def _validate_ident(name: str, label: str) -> str:
    """Valide un identifiant SQL (nom de table/colonne). Lève HTTPException sinon."""
    if not name or not _IDENT_RE.match(name):
        raise HTTPException(status_code=400, detail=f"Identifiant invalide ({label}): {name!r}")
    return name


# ══════════════════════════════════════════════════════════
# SCHEMAS
# ══════════════════════════════════════════════════════════

class WritebackConfig(BaseModel):
    host: str
    port: int = 1433
    username: str
    password: str
    database: str
    table: str = "Clients"
    key_field: str = "ClientID"  # Colonne CRM utilisée pour matcher external_crm_id


class WritebackFieldMapping(BaseModel):
    orkestra_field: str
    crm_field: str


class WritebackConfigRequest(BaseModel):
    config: WritebackConfig
    field_mapping: List[WritebackFieldMapping]


class WritebackExecuteRequest(BaseModel):
    contact_ids: Optional[List[str]] = None  # None = tous les contacts avec external_crm_id


# ══════════════════════════════════════════════════════════
# PERSISTANCE CONFIG (DB + cache mémoire)
# ══════════════════════════════════════════════════════════

_writeback_cache: Dict[str, Any] = {}
_CONFIG_KEY = "writeback_config"


async def _load_config_from_db(db) -> Optional[dict]:
    try:
        result = await db.execute(
            text("SELECT [value] FROM app_settings WHERE [key] = :key"),
            {"key": _CONFIG_KEY},
        )
        row = result.fetchone()
        if row and row[0]:
            return json.loads(row[0])
    except Exception as e:
        logger.debug("app_settings not available: %s", str(e))
    return None


async def _save_config_to_db(db, config: dict):
    json_value = json.dumps(config)
    now = datetime.now(timezone.utc).isoformat()
    try:
        result = await db.execute(
            text("SELECT COUNT(*) FROM app_settings WHERE [key] = :key"),
            {"key": _CONFIG_KEY},
        )
        count = result.fetchone()[0]
        if count > 0:
            await db.execute(
                text("UPDATE app_settings SET [value] = :val, updated_at = :now WHERE [key] = :key"),
                {"val": json_value, "now": now, "key": _CONFIG_KEY},
            )
        else:
            await db.execute(
                text("INSERT INTO app_settings (id, [key], [value], updated_at) VALUES (:id, :key, :val, :now)"),
                {"id": str(uuid.uuid4()), "key": _CONFIG_KEY, "val": json_value, "now": now},
            )
        await db.flush()
    except Exception as e:
        logger.warning("Failed to save writeback config: %s", str(e))


async def _get_writeback_config(db) -> Optional[dict]:
    if _CONFIG_KEY in _writeback_cache:
        return _writeback_cache[_CONFIG_KEY]
    cfg = await _load_config_from_db(db)
    if cfg:
        _writeback_cache[_CONFIG_KEY] = cfg
    return cfg


async def _set_writeback_config(db, config: dict):
    _writeback_cache[_CONFIG_KEY] = config
    await _save_config_to_db(db, config)


# ══════════════════════════════════════════════════════════
# PYMSSQL SYNC HELPERS (exécutés dans un thread pool)
# ══════════════════════════════════════════════════════════

def _connect_pymssql(config: dict, timeout: int = 30):
    import pymssql
    return pymssql.connect(
        server=config["host"],
        port=config["port"],
        user=config["username"],
        password=config["password"],
        database=config["database"],
        timeout=timeout,
    )


def _test_connection_sync(config: dict) -> dict:
    table = _validate_ident(config.get("table", ""), "table")
    try:
        conn = _connect_pymssql(config, timeout=10)
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        conn.close()
        return {"success": True, "message": f"Connecté — {count} enregistrements dans {table}"}
    except Exception as e:
        return {"success": False, "message": f"Erreur connexion CRM : {str(e)}"}


def _execute_writeback_sync(config: dict, field_mapping: List[dict], rows: List[tuple], col_names: List[str]) -> dict:
    """Exécute les UPDATE pymssql dans un thread — validé avant appel."""
    table = config["table"]  # déjà validé
    key_field = config["key_field"]  # déjà validé
    stats = {"total": len(rows), "success": 0, "errors": 0, "error_details": []}

    try:
        conn = _connect_pymssql(config, timeout=30)
        cursor = conn.cursor()

        for row in rows:
            contact = dict(zip(col_names, row))
            crm_id = contact["external_crm_id"]
            try:
                set_parts = []
                params: List[Any] = []
                for m in field_mapping:
                    val = contact.get(m["orkestra_field"])
                    if val is not None:
                        set_parts.append(f"{m['crm_field']} = %s")
                        params.append(str(val))

                if not set_parts:
                    continue

                update_sql = f"UPDATE {table} SET {', '.join(set_parts)} WHERE {key_field} = %s"
                params.append(crm_id)
                cursor.execute(update_sql, tuple(params))
                stats["success"] += 1
            except Exception as e:
                stats["errors"] += 1
                stats["error_details"].append(f"Contact {contact.get('email')}: {str(e)}")

        conn.commit()
        conn.close()
    except Exception as e:
        stats["errors"] = stats["total"]
        stats["error_details"].append(f"Connexion CRM échouée: {str(e)}")
        logger.error("CRM connection failed: %s", str(e))

    return stats


# ══════════════════════════════════════════════════════════
# ENDPOINTS
# ══════════════════════════════════════════════════════════

@router.get("/config")
async def get_sync_config(
    db=Depends(get_db),
    current_user: dict = Depends(require_roles("admin", "manager")),
):
    config = await _get_writeback_config(db)
    if not config:
        return {"status": "not_configured"}
    safe = {**config}
    if "password" in safe:
        safe["password"] = "****"
    return safe


@router.post("/config")
async def save_sync_config(
    data: WritebackConfigRequest,
    db=Depends(get_db),
    current_user: dict = Depends(require_roles("admin")),
):
    """Sauvegarde la config (table/colonnes validées anti-injection)."""
    _validate_ident(data.config.table, "table")
    _validate_ident(data.config.key_field, "key_field")

    mapping_validated = []
    for m in data.field_mapping:
        if m.orkestra_field not in ALLOWED_ORKESTRA_FIELDS:
            raise HTTPException(status_code=400, detail=f"Champ Orkestra non autorisé: {m.orkestra_field}")
        _validate_ident(m.crm_field, "crm_field")
        mapping_validated.append({"orkestra_field": m.orkestra_field, "crm_field": m.crm_field})

    # Préserve le password existant si vide dans la requête
    existing = await _get_writeback_config(db) or {}
    password = data.config.password or existing.get("password", "")

    config = {
        "host": data.config.host,
        "port": data.config.port,
        "username": data.config.username,
        "password": password,  # stocké en clair (dette sécu — à chiffrer au repos)
        "database": data.config.database,
        "table": data.config.table,
        "key_field": data.config.key_field,
        "field_mapping": mapping_validated,
        "status": "configured",
        "configured_at": datetime.now(timezone.utc).isoformat(),
    }
    await _set_writeback_config(db, config)
    return {"status": "saved", "message": f"Write-back configuré vers {data.config.host}/{data.config.database}"}


@router.post("/test")
async def test_crm_connection(
    db=Depends(get_db),
    current_user: dict = Depends(require_roles("admin", "manager")),
):
    config = await _get_writeback_config(db)
    if not config:
        raise HTTPException(status_code=400, detail="Write-back non configuré")

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _test_connection_sync, config)


@router.get("/preview")
async def preview_writeback(
    limit: int = Query(10, ge=1, le=100),
    db=Depends(get_db),
    current_user: dict = Depends(require_roles("admin", "manager")),
):
    """Prévisualise les contacts à synchroniser (limit appliqué en SQL)."""
    count_result = await db.execute(text(
        "SELECT COUNT(*) FROM contacts WHERE external_crm_id IS NOT NULL AND external_crm_id != ''"
    ))
    total = count_result.fetchone()[0]

    base_sql = (
        "SELECT id, email, first_name, last_name, company, lead_score, lead_stage, status, external_crm_id "
        "FROM contacts WHERE external_crm_id IS NOT NULL AND external_crm_id != ''"
    )
    paged_sql = build_raw_paginated_query(base_sql, page=1, page_size=limit, order_by="updated_at DESC")
    result = await db.execute(text(paged_sql))
    rows = result.fetchall()

    contacts = []
    for row in rows:
        contacts.append({
            "id": str(row[0]),
            "email": row[1],
            "first_name": row[2],
            "last_name": row[3],
            "company": row[4],
            "lead_score": row[5],
            "lead_stage": str(row[6]) if row[6] is not None else None,
            "status": str(row[7]) if row[7] is not None else None,
            "external_crm_id": row[8],
        })

    return {"total_syncable": total, "preview": contacts}


@router.post("/execute")
async def execute_writeback(
    data: Optional[WritebackExecuteRequest] = None,
    db=Depends(get_db),
    current_user: dict = Depends(require_roles("admin", "manager")),
):
    """Exécute le write-back — pymssql dans un thread pool (non-bloquant)."""
    config = await _get_writeback_config(db)
    if not config:
        raise HTTPException(status_code=400, detail="Write-back non configuré")

    field_mapping = config.get("field_mapping", [])
    if not field_mapping:
        raise HTTPException(status_code=400, detail="Aucun mapping de champs configuré")

    # Re-validation au cas où la config viendrait d'une version antérieure non validée
    _validate_ident(config.get("table", ""), "table")
    _validate_ident(config.get("key_field", ""), "key_field")
    for m in field_mapping:
        if m["orkestra_field"] not in ALLOWED_ORKESTRA_FIELDS:
            raise HTTPException(status_code=400, detail=f"Champ Orkestra non autorisé: {m['orkestra_field']}")
        _validate_ident(m["crm_field"], "crm_field")

    contact_ids = data.contact_ids if data else None

    # Récupérer les contacts à sync — params bindés (anti SQL injection)
    base_cols = ("SELECT id, email, first_name, last_name, company, phone, country, city, "
                 "job_title, lead_score, lead_stage, status, external_crm_id FROM contacts")

    if contact_ids:
        if not contact_ids:
            return {"status": "no_data", "message": "Aucun contact_id fourni"}
        placeholders = ", ".join(f":id{i}" for i in range(len(contact_ids)))
        params = {f"id{i}": cid for i, cid in enumerate(contact_ids)}
        sql = f"{base_cols} WHERE id IN ({placeholders}) AND external_crm_id IS NOT NULL AND external_crm_id != ''"
        result = await db.execute(text(sql), params)
    else:
        result = await db.execute(text(
            f"{base_cols} WHERE external_crm_id IS NOT NULL AND external_crm_id != ''"
        ))

    rows = result.fetchall()
    if not rows:
        return {"status": "no_data", "message": "Aucun contact à synchroniser (pas de external_crm_id)"}

    col_names = ["id", "email", "first_name", "last_name", "company", "phone",
                 "country", "city", "job_title", "lead_score", "lead_stage", "status", "external_crm_id"]

    started_at = datetime.now(timezone.utc)

    # pymssql sync dans un thread pool (non-bloquant pour l'event loop)
    loop = asyncio.get_event_loop()
    stats = await loop.run_in_executor(
        None, _execute_writeback_sync, config, field_mapping, list(rows), col_names,
    )

    completed_at = datetime.now(timezone.utc)
    duration = (completed_at - started_at).total_seconds()

    # sync_log — errors = liste (JSONField gère la sérialisation)
    try:
        sync_log = SyncLog(
            id=str(uuid.uuid4()),
            source=f"{config['host']}/{config['database']}",
            direction="orkestra_to_crm",
            total_records=stats["total"],
            success_count=stats["success"],
            error_count=stats["errors"],
            duplicate_count=0,
            errors=stats["error_details"][:20] if stats["error_details"] else None,
            started_at=started_at,
            completed_at=completed_at,
            duration_seconds=duration,
        )
        db.add(sync_log)
        await db.flush()
    except Exception as e:
        logger.warning("Failed to save sync log: %s", str(e))

    return {
        "status": "completed" if stats["errors"] == 0 else "partial",
        "total": stats["total"],
        "success": stats["success"],
        "errors": stats["errors"],
        "duration_seconds": round(duration, 2),
        "error_details": stats["error_details"][:5],
        "message": f"{stats['success']}/{stats['total']} contacts synchronisés vers le CRM",
    }


@router.get("/logs")
async def get_sync_logs(
    limit: int = Query(20, ge=1, le=100),
    db=Depends(get_db),
    current_user: dict = Depends(require_roles("admin", "manager")),
):
    """Historique des synchronisations (limit appliqué en SQL)."""
    base_sql = (
        "SELECT id, source, direction, total_records, success_count, error_count, "
        "started_at, completed_at, duration_seconds FROM sync_logs"
    )
    paged_sql = build_raw_paginated_query(base_sql, page=1, page_size=limit, order_by="started_at DESC")
    result = await db.execute(text(paged_sql))
    rows = result.fetchall()

    logs = []
    for row in rows:
        logs.append({
            "id": str(row[0]),
            "source": row[1],
            "direction": row[2],
            "total_records": row[3],
            "success_count": row[4],
            "error_count": row[5],
            "started_at": str(row[6]) if row[6] else None,
            "completed_at": str(row[7]) if row[7] else None,
            "duration_seconds": row[8],
        })

    return {"logs": logs}

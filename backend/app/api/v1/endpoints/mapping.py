"""
OS Orkestra — Endpoints Mapping
Permet de lire le schéma d'une base externe, configurer le mapping des colonnes,
prévisualiser les données et lancer l'import.
Compatible Python 3.9+
"""
import uuid
import json
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import require_roles

logger = logging.getLogger("orkestra.mapping")

router = APIRouter(prefix="/mapping", tags=["Mapping"])


# ══════════════════════════════════════════════════════════
# SCHEMAS
# ══════════════════════════════════════════════════════════

class ExternalDBConfig(BaseModel):
    db_type: str  # mssql, postgresql, mysql
    host: str
    port: int = 1433
    username: str
    password: str
    database: str


class TableSchemaRequest(BaseModel):
    connection: ExternalDBConfig
    table_name: str


class MappingConfig(BaseModel):
    name: str  # Nom du mapping (ex: "CRM Client Import")
    connection: ExternalDBConfig
    source_table: str
    field_mappings: List[Dict[str, str]]  # [{"source": "CompanyName", "target": "company"}, ...]
    custom_field_mappings: List[Dict[str, str]] = []  # Champs qui vont dans custom_fields
    value_mappings: Dict[str, Dict[str, str]] = {}  # {"Statut": {"Actif": "active", "Inactif": "inactive"}}
    filters: Optional[str] = None  # WHERE clause optionnelle


class PreviewRequest(BaseModel):
    connection: ExternalDBConfig
    source_table: str
    field_mappings: List[Dict[str, str]]
    custom_field_mappings: List[Dict[str, str]] = []
    value_mappings: Dict[str, Dict[str, str]] = {}
    limit: int = 5


# ══════════════════════════════════════════════════════════
# SAVED MAPPINGS STORE
# ══════════════════════════════════════════════════════════

_saved_mappings: Dict[str, Dict[str, Any]] = {}


# ══════════════════════════════════════════════════════════
# HELPERS — CONNEXION EXTERNE
# ══════════════════════════════════════════════════════════

def _get_external_connection(config: ExternalDBConfig):
    """Crée une connexion à une base externe."""
    if config.db_type == "mssql":
        try:
            import pymssql
            conn = pymssql.connect(
                server=config.host,
                port=config.port,
                user=config.username,
                password=config.password,
                database=config.database,
                login_timeout=10,
            )
            return conn
        except ImportError:
            import pyodbc
            conn_str = (
                f"DRIVER={{ODBC Driver 18 for SQL Server}};"
                f"SERVER={config.host},{config.port};"
                f"DATABASE={config.database};"
                f"UID={config.username};PWD={config.password};"
                f"TrustServerCertificate=yes;Connection Timeout=10"
            )
            return pyodbc.connect(conn_str)

    elif config.db_type == "postgresql":
        import psycopg2
        return psycopg2.connect(
            host=config.host, port=config.port,
            user=config.username, password=config.password,
            database=config.database, connect_timeout=10,
        )

    elif config.db_type == "mysql":
        import pymysql
        return pymysql.connect(
            host=config.host, port=config.port,
            user=config.username, password=config.password,
            database=config.database, connect_timeout=10,
        )

    raise HTTPException(status_code=400, detail=f"Type de base non supporté : {config.db_type}")


# ══════════════════════════════════════════════════════════
# ENDPOINTS
# ══════════════════════════════════════════════════════════

@router.post("/list-tables")
async def list_tables(
    config: ExternalDBConfig,
    current_user: dict = Depends(require_roles("admin", "manager")),
):
    """Liste les tables d'une base externe."""
    try:
        conn = _get_external_connection(config)
        cursor = conn.cursor()

        if config.db_type == "mssql":
            cursor.execute(
                "SELECT TABLE_SCHEMA, TABLE_NAME, TABLE_TYPE "
                "FROM INFORMATION_SCHEMA.TABLES "
                "WHERE TABLE_TYPE IN ('BASE TABLE', 'VIEW') "
                "ORDER BY TABLE_SCHEMA, TABLE_NAME"
            )
        elif config.db_type == "postgresql":
            cursor.execute(
                "SELECT table_schema, table_name, table_type "
                "FROM information_schema.tables "
                "WHERE table_schema NOT IN ('pg_catalog', 'information_schema') "
                "ORDER BY table_schema, table_name"
            )
        elif config.db_type == "mysql":
            cursor.execute(
                "SELECT TABLE_SCHEMA, TABLE_NAME, TABLE_TYPE "
                "FROM INFORMATION_SCHEMA.TABLES "
                "WHERE TABLE_SCHEMA = %s "
                "ORDER BY TABLE_NAME",
                (config.database,)
            )

        tables = []
        for row in cursor.fetchall():
            tables.append({
                "schema": row[0],
                "name": row[1],
                "type": row[2],
                "full_name": f"{row[0]}.{row[1]}",
            })

        cursor.close()
        conn.close()
        return {"tables": tables, "count": len(tables)}

    except Exception as e:
        logger.error(f"list-tables error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/table-schema")
async def get_table_schema(
    data: TableSchemaRequest,
    current_user: dict = Depends(require_roles("admin", "manager")),
):
    """Récupère le schéma (colonnes) d'une table externe."""
    try:
        conn = _get_external_connection(data.connection)
        cursor = conn.cursor()

        # Séparer schema.table si nécessaire
        parts = data.table_name.split(".")
        table = parts[-1]
        schema = parts[0] if len(parts) > 1 else "dbo"

        if data.connection.db_type == "mssql":
            cursor.execute(
                "SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH, IS_NULLABLE, COLUMN_DEFAULT "
                "FROM INFORMATION_SCHEMA.COLUMNS "
                "WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s "
                "ORDER BY ORDINAL_POSITION",
                (schema, table)
            )
        elif data.connection.db_type == "postgresql":
            cursor.execute(
                "SELECT column_name, data_type, character_maximum_length, is_nullable, column_default "
                "FROM information_schema.columns "
                "WHERE table_schema = %s AND table_name = %s "
                "ORDER BY ordinal_position",
                (schema, table)
            )
        elif data.connection.db_type == "mysql":
            cursor.execute(
                "SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH, IS_NULLABLE, COLUMN_DEFAULT "
                "FROM INFORMATION_SCHEMA.COLUMNS "
                "WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s "
                "ORDER BY ORDINAL_POSITION",
                (data.connection.database, table)
            )

        columns = []
        for row in cursor.fetchall():
            columns.append({
                "name": row[0],
                "type": row[1],
                "max_length": row[2],
                "nullable": row[3] == "YES",
                "default": str(row[4]) if row[4] else None,
            })

        # Sample data (5 premières lignes)
        cursor.execute(f"SELECT TOP 5 * FROM [{schema}].[{table}]" if data.connection.db_type == "mssql"
                       else f"SELECT * FROM \"{schema}\".\"{table}\" LIMIT 5")
        sample_rows = []
        col_names = [col["name"] for col in columns]
        for row in cursor.fetchall():
            sample_rows.append(dict(zip(col_names, [str(v) if v is not None else None for v in row])))

        cursor.close()
        conn.close()

        # Auto-suggest mapping
        suggestions = _auto_suggest_mapping(columns)

        return {
            "table": data.table_name,
            "columns": columns,
            "sample_data": sample_rows,
            "row_count": len(sample_rows),
            "suggested_mapping": suggestions,
        }

    except Exception as e:
        logger.error(f"table-schema error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/preview")
async def preview_import(
    data: PreviewRequest,
    current_user: dict = Depends(require_roles("admin", "manager")),
):
    """Prévisualise les données transformées selon le mapping."""
    try:
        conn = _get_external_connection(data.connection)
        cursor = conn.cursor()

        # Colonnes source
        source_cols = [m["source"] for m in data.field_mappings]
        source_cols += [m["source"] for m in data.custom_field_mappings]
        cols_sql = ", ".join([f"[{c}]" for c in source_cols])

        parts = data.source_table.split(".")
        table = parts[-1]
        schema = parts[0] if len(parts) > 1 else "dbo"

        if data.connection.db_type == "mssql":
            cursor.execute(f"SELECT TOP {data.limit} {cols_sql} FROM [{schema}].[{table}]")
        else:
            cursor.execute(f"SELECT {cols_sql} FROM \"{schema}\".\"{table}\" LIMIT {data.limit}")

        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        # Transformer selon le mapping
        transformed = []
        for row in rows:
            record = {}
            custom = {}
            idx = 0

            # Champs standard
            for mapping in data.field_mappings:
                value = str(row[idx]) if row[idx] is not None else None
                # Appliquer value mapping si configuré
                if mapping["source"] in data.value_mappings and value:
                    vm = data.value_mappings[mapping["source"]]
                    value = vm.get(value, value)
                record[mapping["target"]] = value
                idx += 1

            # Champs custom
            for mapping in data.custom_field_mappings:
                value = str(row[idx]) if row[idx] is not None else None
                custom[mapping["target"]] = value
                idx += 1

            if custom:
                record["custom_fields"] = custom

            transformed.append(record)

        return {
            "preview": transformed,
            "count": len(transformed),
            "source_table": data.source_table,
        }

    except Exception as e:
        logger.error(f"preview error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/import")
async def run_import(
    data: MappingConfig,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_roles("admin", "manager")),
):
    """Lance l'import des données avec le mapping configuré."""
    try:
        conn = _get_external_connection(data.connection)
        cursor = conn.cursor()

        # Colonnes source
        source_cols = [m["source"] for m in data.field_mappings]
        source_cols += [m["source"] for m in data.custom_field_mappings]
        cols_sql = ", ".join([f"[{c}]" for c in source_cols])

        parts = data.source_table.split(".")
        table = parts[-1]
        schema = parts[0] if len(parts) > 1 else "dbo"

        query = f"SELECT {cols_sql} FROM [{schema}].[{table}]"
        if data.filters:
            query += f" WHERE {data.filters}"

        cursor.execute(query)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        # Importer dans Orkestra
        from app.models.models import Contact, ContactSource, ContactStatus
        from sqlalchemy import select

        stats = {"imported": 0, "updated": 0, "skipped": 0, "errors": []}

        for row_idx, row in enumerate(rows):
            try:
                record = {}
                custom = {}
                idx = 0

                for mapping in data.field_mappings:
                    value = str(row[idx]) if row[idx] is not None else None
                    if mapping["source"] in data.value_mappings and value:
                        vm = data.value_mappings[mapping["source"]]
                        value = vm.get(value, value)
                    record[mapping["target"]] = value
                    idx += 1

                for mapping in data.custom_field_mappings:
                    value = str(row[idx]) if row[idx] is not None else None
                    custom[mapping["target"]] = value
                    idx += 1

                email = record.get("email", "")
                if not email:
                    stats["skipped"] += 1
                    continue

                # Vérifier doublon
                existing = await db.execute(
                    select(Contact).where(Contact.email == email)
                )
                existing_contact = existing.scalar_one_or_none()

                if existing_contact:
                    # Update
                    for field, value in record.items():
                        if field != "email" and value:
                            setattr(existing_contact, field, value)
                    if custom:
                        existing_contact.custom_fields = json.dumps(custom)
                    existing_contact.updated_at = datetime.now(timezone.utc)
                    stats["updated"] += 1
                else:
                    # Insert
                    contact = Contact(
                        id=uuid.uuid4(),
                        email=email,
                        first_name=record.get("first_name"),
                        last_name=record.get("last_name"),
                        company=record.get("company"),
                        job_title=record.get("job_title"),
                        phone=record.get("phone"),
                        country=record.get("country"),
                        city=record.get("city"),
                        source=ContactSource.CRM_DYNAMICS,
                        status=ContactStatus.ACTIVE,
                        is_internal=False,
                        gdpr_consent=True,
                        custom_fields=json.dumps(custom) if custom else None,
                        tags=json.dumps(["imported", "crm"]),
                    )
                    db.add(contact)
                    stats["imported"] += 1

            except Exception as e:
                stats["errors"].append({"row": row_idx, "error": str(e)})

        await db.flush()
        stats["total_processed"] = len(rows)

        return stats

    except Exception as e:
        logger.error(f"import error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/save")
async def save_mapping(
    data: MappingConfig,
    current_user: dict = Depends(require_roles("admin", "manager")),
):
    """Sauvegarder un mapping pour réutilisation."""
    mapping_id = f"map_{uuid.uuid4().hex[:8]}"
    _saved_mappings[mapping_id] = {
        "id": mapping_id,
        "name": data.name,
        "source_table": data.source_table,
        "connection_host": data.connection.host,
        "connection_db": data.connection.database,
        "field_mappings": data.field_mappings,
        "custom_field_mappings": data.custom_field_mappings,
        "value_mappings": data.value_mappings,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": current_user.get("email"),
    }
    return {"id": mapping_id, "message": f"Mapping '{data.name}' sauvegardé"}


@router.get("/saved")
async def list_saved_mappings(
    current_user: dict = Depends(require_roles("admin", "manager")),
):
    """Liste les mappings sauvegardés."""
    return list(_saved_mappings.values())


@router.delete("/saved/{mapping_id}")
async def delete_mapping(
    mapping_id: str,
    current_user: dict = Depends(require_roles("admin")),
):
    if mapping_id in _saved_mappings:
        del _saved_mappings[mapping_id]
        return {"message": "Mapping supprimé"}
    raise HTTPException(status_code=404, detail="Mapping non trouvé")


# Champs cibles Orkestra disponibles
ORKESTRA_FIELDS = [
    {"name": "email", "label": "Email", "required": True, "type": "standard"},
    {"name": "first_name", "label": "Prénom", "required": False, "type": "standard"},
    {"name": "last_name", "label": "Nom", "required": False, "type": "standard"},
    {"name": "company", "label": "Entreprise", "required": False, "type": "standard"},
    {"name": "job_title", "label": "Poste", "required": False, "type": "standard"},
    {"name": "phone", "label": "Téléphone", "required": False, "type": "standard"},
    {"name": "country", "label": "Pays", "required": False, "type": "standard"},
    {"name": "city", "label": "Ville", "required": False, "type": "standard"},
    {"name": "business_unit", "label": "Business Unit", "required": False, "type": "standard"},
    {"name": "segment", "label": "Segment", "required": False, "type": "standard"},
]


@router.get("/target-fields")
async def get_target_fields(
    current_user: dict = Depends(require_roles("admin", "manager")),
):
    """Liste les champs cibles disponibles dans Orkestra."""
    return ORKESTRA_FIELDS


# ══════════════════════════════════════════════════════════
# AUTO-SUGGEST MAPPING
# ══════════════════════════════════════════════════════════

def _auto_suggest_mapping(columns: List[Dict]) -> List[Dict[str, str]]:
    """Suggère automatiquement un mapping basé sur les noms de colonnes."""
    suggestions = []
    rules = {
        "email": ["email", "contactemail", "mail", "e_mail", "emailaddress", "adresse_email"],
        "first_name": ["prenom", "firstname", "first_name", "givenname", "given_name", "prenomcontact"],
        "last_name": ["nom", "nomdefamille", "lastname", "last_name", "surname", "family_name", "nomcontact"],
        "company": ["companyname", "company", "societe", "entreprise", "organization", "organisation", "raison_sociale"],
        "phone": ["telephone", "phone", "tel", "mobile", "phonenumber", "phone_number", "numero"],
        "job_title": ["poste", "jobtitle", "job_title", "titre", "fonction", "position", "role"],
        "country": ["pays", "country", "nation"],
        "city": ["ville", "city", "localite"],
        "business_unit": ["departement", "department", "business_unit", "bu", "service", "division"],
        "segment": ["segment", "categorie", "category", "type_client", "clienttype"],
    }

    for col in columns:
        col_lower = col["name"].lower().replace(" ", "").replace("_", "")
        matched = False
        for target, keywords in rules.items():
            for kw in keywords:
                if kw.replace("_", "") in col_lower or col_lower in kw.replace("_", ""):
                    suggestions.append({
                        "source": col["name"],
                        "target": target,
                        "confidence": "high" if col_lower == kw.replace("_", "") else "medium",
                    })
                    matched = True
                    break
            if matched:
                break

        if not matched:
            suggestions.append({
                "source": col["name"],
                "target": f"custom_fields.{col['name'].lower()}",
                "confidence": "custom",
            })

    return suggestions

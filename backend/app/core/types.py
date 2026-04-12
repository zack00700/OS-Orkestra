"""
OS HubLine — Types de colonnes portables multi-moteur

Résout les incompatibilités entre moteurs SQL :

┌─────────────┬────────────────┬──────────────┬────────────┬──────────┬──────────┐
│ Type        │ PostgreSQL     │ SQL Server   │ MySQL      │ SQLite   │ Oracle   │
├─────────────┼────────────────┼──────────────┼────────────┼──────────┼──────────┤
│ GUID        │ UUID natif     │ UNIQUEID.    │ CHAR(36)   │ CHAR(36) │ RAW(16)  │
│ ArrayField  │ ARRAY(String)  │ NVARCHAR(MAX)│ JSON       │ TEXT     │ CLOB     │
│ JSONField   │ JSONB          │ NVARCHAR(MAX)│ JSON       │ TEXT     │ CLOB     │
│ BoolField   │ BOOLEAN        │ BIT          │ TINYINT(1) │ INTEGER  │ NUMBER(1)│
│ TextField   │ TEXT           │ NVARCHAR(MAX)│ LONGTEXT   │ TEXT     │ CLOB     │
└─────────────┴────────────────┴──────────────┴────────────┴──────────┴──────────┘

Usage :
    from app.core.types import GUID, ArrayField, JSONField

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    tags: Mapped[list[str] | None] = mapped_column(ArrayField(), nullable=True)
    config: Mapped[dict] = mapped_column(JSONField(), default=dict)
"""
import json
import uuid
from typing import Any, Optional

from sqlalchemy import String, Text, TypeDecorator, types
from sqlalchemy.dialects import postgresql, mssql, mysql, oracle


# ══════════════════════════════════════════════════════════
# GUID — UUID portable
# ══════════════════════════════════════════════════════════

class GUID(TypeDecorator):
    """
    UUID portable : utilise le type natif sur PostgreSQL,
    UNIQUEIDENTIFIER sur SQL Server, CHAR(36) ailleurs.
    """
    impl = String(36)
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(postgresql.UUID(as_uuid=True))
        elif dialect.name == "mssql":
            return dialect.type_descriptor(mssql.UNIQUEIDENTIFIER())
        elif dialect.name == "oracle":
            return dialect.type_descriptor(oracle.RAW(16))
        else:
            # MySQL, MariaDB, SQLite → CHAR(36)
            return dialect.type_descriptor(String(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name == "postgresql":
            return value  # asyncpg gère les UUID nativement
        elif dialect.name == "mssql":
            return str(value) if isinstance(value, uuid.UUID) else value
        elif dialect.name == "oracle":
            if isinstance(value, uuid.UUID):
                return value.bytes
            return value
        else:
            return str(value) if isinstance(value, uuid.UUID) else value

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if dialect.name == "oracle":
            if isinstance(value, bytes):
                return uuid.UUID(bytes=value)
        if isinstance(value, uuid.UUID):
            return value
        return uuid.UUID(str(value))


# ══════════════════════════════════════════════════════════
# ArrayField — Liste sérialisée en JSON
# ══════════════════════════════════════════════════════════

class ArrayField(TypeDecorator):
    """
    Liste de valeurs portable :
    - PostgreSQL → ARRAY natif
    - Autres → JSON sérialisé (TEXT sur SQLite, NVARCHAR(MAX) sur SQL Server)

    Supporte les opérations de filtrage cross-DB via les méthodes helper.
    """
    impl = Text
    cache_ok = True

    def __init__(self, item_type=String, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.item_type = item_type

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(postgresql.ARRAY(self.item_type))
        elif dialect.name == "mssql":
            return dialect.type_descriptor(mssql.NVARCHAR(None))  # NVARCHAR(MAX)
        elif dialect.name in ("mysql", "mariadb"):
            return dialect.type_descriptor(mysql.JSON())
        else:
            return dialect.type_descriptor(Text())

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name == "postgresql":
            return value  # PG ARRAY natif
        return json.dumps(value, ensure_ascii=False)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if dialect.name == "postgresql":
            return value  # déjà une list
        if isinstance(value, str):
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return []
        if isinstance(value, list):
            return value
        return []


# ══════════════════════════════════════════════════════════
# JSONField — JSON portable
# ══════════════════════════════════════════════════════════

class JSONField(TypeDecorator):
    """
    JSON portable :
    - PostgreSQL → JSONB (indexable, opérateurs natifs)
    - MySQL/MariaDB → JSON natif
    - SQL Server → NVARCHAR(MAX) + sérialisation
    - SQLite → TEXT + sérialisation
    - Oracle → CLOB + sérialisation
    """
    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(postgresql.JSONB())
        elif dialect.name in ("mysql", "mariadb"):
            return dialect.type_descriptor(mysql.JSON())
        elif dialect.name == "mssql":
            return dialect.type_descriptor(mssql.NVARCHAR(None))
        elif dialect.name == "oracle":
            return dialect.type_descriptor(oracle.CLOB())
        else:
            return dialect.type_descriptor(Text())

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name in ("postgresql", "mysql", "mariadb"):
            return value  # driver gère la sérialisation
        return json.dumps(value, ensure_ascii=False, default=str)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, (dict, list)):
            return value  # déjà désérialisé
        if isinstance(value, str):
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
        return value


# ══════════════════════════════════════════════════════════
# LargeText — TEXT portable (NVARCHAR(MAX), CLOB, etc.)
# ══════════════════════════════════════════════════════════

class LargeText(TypeDecorator):
    """
    Texte long portable :
    - SQL Server → NVARCHAR(MAX)
    - Oracle → CLOB
    - Autres → TEXT
    """
    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "mssql":
            return dialect.type_descriptor(mssql.NVARCHAR(None))
        elif dialect.name == "oracle":
            return dialect.type_descriptor(oracle.CLOB())
        return dialect.type_descriptor(Text())

"""
OS HubLine — Couche d'abstraction base de données multi-moteur

Supporte : PostgreSQL, SQL Server, MySQL/MariaDB, SQLite, Oracle
Gère automatiquement les différences dialectales :
  - UUID : natif (PG) vs CHAR(36) (autres)
  - ARRAY : natif (PG) vs JSON/TEXT sérialisé (autres)
  - JSON : natif (PG/MySQL) vs NVARCHAR(MAX) (SQL Server) vs TEXT (SQLite)
  - Pagination : LIMIT/OFFSET vs OFFSET FETCH vs ROWNUM
  - String functions : ILIKE (PG) vs LIKE + COLLATE (SQL Server) vs LOWER+LIKE
  - Boolean : natif (PG/MySQL) vs BIT (SQL Server) vs INTEGER (SQLite)
"""
import logging
from enum import Enum
from typing import Optional
from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
    AsyncEngine,
)
from sqlalchemy.orm import DeclarativeBase
from app.core.config import get_settings

logger = logging.getLogger("hubline.database")
settings = get_settings()


# ══════════════════════════════════════════════════════════
# DATABASE DIALECT DETECTION
# ══════════════════════════════════════════════════════════

class DatabaseDialect(str, Enum):
    POSTGRESQL = "postgresql"
    SQLSERVER = "mssql"
    MYSQL = "mysql"
    MARIADB = "mariadb"
    SQLITE = "sqlite"
    ORACLE = "oracle"


_DIALECT_MAP = {
    "postgresql": DatabaseDialect.POSTGRESQL,
    "postgres": DatabaseDialect.POSTGRESQL,
    "mssql": DatabaseDialect.SQLSERVER,
    "mysql": DatabaseDialect.MYSQL,
    "mariadb": DatabaseDialect.MARIADB,
    "sqlite": DatabaseDialect.SQLITE,
    "oracle": DatabaseDialect.ORACLE,
}

_ASYNC_DRIVERS = {
    DatabaseDialect.POSTGRESQL: "asyncpg",
    DatabaseDialect.SQLSERVER: "aioodbc",
    DatabaseDialect.MYSQL: "aiomysql",
    DatabaseDialect.MARIADB: "aiomysql",
    DatabaseDialect.SQLITE: "aiosqlite",
    DatabaseDialect.ORACLE: "oracledb",
}

_SYNC_DRIVERS = {
    DatabaseDialect.POSTGRESQL: "psycopg2",
    DatabaseDialect.SQLSERVER: "pyodbc",
    DatabaseDialect.MYSQL: "pymysql",
    DatabaseDialect.MARIADB: "pymysql",
    DatabaseDialect.SQLITE: "",
    DatabaseDialect.ORACLE: "oracledb",
}


def detect_dialect(url: str) -> DatabaseDialect:
    scheme = url.split("://")[0].split("+")[0].lower()
    dialect = _DIALECT_MAP.get(scheme)
    if not dialect:
        raise ValueError(
            f"Dialecte non supporté : '{scheme}'. "
            f"Supportés : {', '.join(_DIALECT_MAP.keys())}"
        )
    return dialect


def get_async_url(url: str) -> str:
    """Normalise l'URL pour le driver async approprié."""
    dialect = detect_dialect(url)
    driver = _ASYNC_DRIVERS[dialect]
    if f"+{driver}" in url:
        return url
    parts = url.split("://", 1)
    base_scheme = parts[0].split("+")[0]
    new_scheme = f"{base_scheme}+{driver}" if driver else base_scheme
    return f"{new_scheme}://{parts[1]}"


def get_sync_url(url: str) -> str:
    """Normalise l'URL pour le driver sync (Alembic)."""
    dialect = detect_dialect(url)
    driver = _SYNC_DRIVERS[dialect]
    parts = url.split("://", 1)
    base_scheme = parts[0].split("+")[0]
    new_scheme = f"{base_scheme}+{driver}" if driver else base_scheme
    return f"{new_scheme}://{parts[1]}"


# ══════════════════════════════════════════════════════════
# DIALECT CAPABILITIES
# ══════════════════════════════════════════════════════════

class DialectCapabilities:
    """Décrit les capacités et limites de chaque moteur SQL."""

    def __init__(self, dialect: DatabaseDialect):
        self.dialect = dialect

    @property
    def supports_native_uuid(self) -> bool:
        return self.dialect == DatabaseDialect.POSTGRESQL

    @property
    def supports_native_array(self) -> bool:
        return self.dialect == DatabaseDialect.POSTGRESQL

    @property
    def supports_native_json(self) -> bool:
        return self.dialect in (
            DatabaseDialect.POSTGRESQL, DatabaseDialect.MYSQL, DatabaseDialect.MARIADB,
        )

    @property
    def supports_ilike(self) -> bool:
        return self.dialect == DatabaseDialect.POSTGRESQL

    @property
    def supports_returning(self) -> bool:
        return self.dialect in (
            DatabaseDialect.POSTGRESQL, DatabaseDialect.SQLSERVER,
            DatabaseDialect.ORACLE, DatabaseDialect.SQLITE,
        )

    @property
    def supports_boolean_native(self) -> bool:
        return self.dialect in (
            DatabaseDialect.POSTGRESQL, DatabaseDialect.MYSQL, DatabaseDialect.MARIADB,
        )

    @property
    def pagination_style(self) -> str:
        """
        'limit_offset'  : LIMIT n OFFSET m (PG, MySQL, SQLite)
        'offset_fetch'  : OFFSET m ROWS FETCH NEXT n ROWS ONLY (SQL Server 2012+)
        'rownum'        : WHERE ROWNUM <= n (Oracle legacy)
        Note : SQLAlchemy .limit().offset() gère la traduction auto,
               mais cette info sert pour le raw SQL.
        """
        if self.dialect == DatabaseDialect.SQLSERVER:
            return "offset_fetch"
        elif self.dialect == DatabaseDialect.ORACLE:
            return "rownum"
        return "limit_offset"

    @property
    def max_parameters_per_query(self) -> int:
        limits = {
            DatabaseDialect.SQLITE: 999,
            DatabaseDialect.SQLSERVER: 2100,
            DatabaseDialect.MYSQL: 65535,
            DatabaseDialect.POSTGRESQL: 32767,
            DatabaseDialect.ORACLE: 65535,
        }
        return limits.get(self.dialect, 10000)

    @property
    def default_schema(self) -> Optional[str]:
        schemas = {
            DatabaseDialect.POSTGRESQL: "public",
            DatabaseDialect.SQLSERVER: "dbo",
        }
        return schemas.get(self.dialect)

    @property
    def json_extract_function(self) -> str:
        """
        PG       : json_column->>'key'
        SQL Server: JSON_VALUE(column, '$.key')
        MySQL    : JSON_EXTRACT(column, '$.key')
        SQLite   : json_extract(column, '$.key')
        """
        return {
            DatabaseDialect.POSTGRESQL: "arrow",
            DatabaseDialect.SQLSERVER: "json_value",
            DatabaseDialect.MYSQL: "json_extract",
            DatabaseDialect.MARIADB: "json_extract",
            DatabaseDialect.SQLITE: "json_extract",
            DatabaseDialect.ORACLE: "json_value",
        }[self.dialect]

    def get_engine_options(self) -> dict:
        base = {
            "pool_pre_ping": True,
            "pool_size": settings.DATABASE_POOL_SIZE,
            "max_overflow": settings.DATABASE_MAX_OVERFLOW,
            "echo": settings.DATABASE_ECHO,
        }
        if self.dialect == DatabaseDialect.SQLITE:
            base.pop("pool_size", None)
            base.pop("max_overflow", None)
        if self.dialect == DatabaseDialect.SQLSERVER:
            base["connect_args"] = {"TrustServerCertificate": "yes", "timeout": 30}
        if self.dialect in (DatabaseDialect.MYSQL, DatabaseDialect.MARIADB):
            base["connect_args"] = {"charset": "utf8mb4"}
        return base


# ══════════════════════════════════════════════════════════
# ENGINE FACTORY
# ══════════════════════════════════════════════════════════

_current_dialect: Optional[DatabaseDialect] = None
_capabilities: Optional[DialectCapabilities] = None


def get_dialect() -> DatabaseDialect:
    global _current_dialect
    if _current_dialect is None:
        _current_dialect = detect_dialect(settings.DATABASE_URL)
    return _current_dialect


def get_capabilities() -> DialectCapabilities:
    global _capabilities
    if _capabilities is None:
        _capabilities = DialectCapabilities(get_dialect())
    return _capabilities


def create_engine_for_dialect() -> AsyncEngine:
    dialect = get_dialect()
    caps = get_capabilities()
    async_url = get_async_url(settings.DATABASE_URL)
    engine_opts = caps.get_engine_options()

    logger.info(
        f"Initialisation DB : dialect={dialect.value}, "
        f"driver={_ASYNC_DRIVERS[dialect]}, pagination={caps.pagination_style}"
    )

    eng = create_async_engine(async_url, **engine_opts)

    if dialect == DatabaseDialect.SQLITE:
        @event.listens_for(eng.sync_engine, "connect")
        def _sqlite_pragmas(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.close()

    if dialect == DatabaseDialect.SQLSERVER:
        @event.listens_for(eng.sync_engine, "connect")
        def _mssql_options(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("SET ANSI_NULLS ON")
            cursor.execute("SET QUOTED_IDENTIFIER ON")
            cursor.close()

    return eng


# ══════════════════════════════════════════════════════════
# SESSION
# ══════════════════════════════════════════════════════════

engine = create_engine_for_dialect()

async_session_factory = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def check_db_connection() -> dict:
    dialect = get_dialect()
    try:
        async with engine.begin() as conn:
            q = "SELECT 1 FROM DUAL" if dialect == DatabaseDialect.ORACLE else "SELECT 1"
            result = await conn.execute(text(q))
            return {"status": "connected", "dialect": dialect.value, "driver": _ASYNC_DRIVERS[dialect]}
    except Exception as e:
        return {"status": "error", "dialect": dialect.value, "error": str(e)}

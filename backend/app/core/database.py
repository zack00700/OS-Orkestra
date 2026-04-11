"""
OS HubLine — Couche d'abstraction base de données multi-moteur
Compatible Python 3.9+

Supporte : PostgreSQL, SQL Server (pyodbc + pymssql), MySQL, SQLite, Oracle
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


def detect_dialect(url: str) -> DatabaseDialect:
    scheme = url.split("://")[0].split("+")[0].lower()
    dialect = _DIALECT_MAP.get(scheme)
    if not dialect:
        raise ValueError(f"Dialecte non supporté : '{scheme}'")
    return dialect


def get_async_url(url: str) -> str:
    """
    Normalise l'URL pour le driver async.
    Gère pyodbc, pymssql, et les autres drivers.
    """
    dialect = detect_dialect(url)

    # Si déjà un driver async spécifié, garder tel quel
    if "+aioodbc" in url or "+aiosqlite" in url or "+asyncpg" in url or "+aiomysql" in url:
        return url

    # SQL Server : détecter pyodbc vs pymssql
    if dialect == DatabaseDialect.SQLSERVER:
        if "+pyodbc" in url:
            return url.replace("+pyodbc", "+aioodbc")
        elif "+pymssql" in url:
            # pymssql n'a pas de driver async natif, on utilise le mode sync dans un thread
            # SQLAlchemy gère ça automatiquement avec create_async_engine
            return url
        else:
            # Pas de driver spécifié, essayer pymssql d'abord (plus portable, pas besoin d'ODBC)
            try:
                import pymssql
                parts = url.split("://", 1)
                return f"mssql+pymssql://{parts[1]}"
            except ImportError:
                pass
            try:
                import aioodbc
                parts = url.split("://", 1)
                return f"mssql+aioodbc://{parts[1]}"
            except ImportError:
                pass
            return url

    # PostgreSQL
    if dialect == DatabaseDialect.POSTGRESQL:
        if "+asyncpg" not in url:
            parts = url.split("://", 1)
            base = parts[0].split("+")[0]
            return f"{base}+asyncpg://{parts[1]}"
        return url

    # MySQL
    if dialect in (DatabaseDialect.MYSQL, DatabaseDialect.MARIADB):
        if "+aiomysql" not in url:
            parts = url.split("://", 1)
            base = parts[0].split("+")[0]
            return f"{base}+aiomysql://{parts[1]}"
        return url

    # SQLite
    if dialect == DatabaseDialect.SQLITE:
        if "+aiosqlite" not in url:
            parts = url.split("://", 1)
            return f"sqlite+aiosqlite://{parts[1]}"
        return url

    return url


class DialectCapabilities:
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
        return self.dialect in (DatabaseDialect.POSTGRESQL, DatabaseDialect.MYSQL, DatabaseDialect.MARIADB)

    @property
    def supports_ilike(self) -> bool:
        return self.dialect == DatabaseDialect.POSTGRESQL

    @property
    def supports_returning(self) -> bool:
        return self.dialect in (DatabaseDialect.POSTGRESQL, DatabaseDialect.SQLSERVER, DatabaseDialect.ORACLE, DatabaseDialect.SQLITE)

    @property
    def supports_boolean_native(self) -> bool:
        return self.dialect in (DatabaseDialect.POSTGRESQL, DatabaseDialect.MYSQL, DatabaseDialect.MARIADB)

    @property
    def pagination_style(self) -> str:
        if self.dialect == DatabaseDialect.SQLSERVER:
            return "offset_fetch"
        elif self.dialect == DatabaseDialect.ORACLE:
            return "rownum"
        return "limit_offset"

    @property
    def max_parameters_per_query(self) -> int:
        limits = {DatabaseDialect.SQLITE: 999, DatabaseDialect.SQLSERVER: 2100, DatabaseDialect.MYSQL: 65535, DatabaseDialect.POSTGRESQL: 32767, DatabaseDialect.ORACLE: 65535}
        return limits.get(self.dialect, 10000)

    @property
    def default_schema(self) -> Optional[str]:
        return {"postgresql": "public", "mssql": "dbo"}.get(self.dialect.value)

    @property
    def json_extract_function(self) -> str:
        return {"postgresql": "arrow", "mssql": "json_value", "mysql": "json_extract", "mariadb": "json_extract", "sqlite": "json_extract", "oracle": "json_value"}[self.dialect.value]

    def get_engine_options(self) -> dict:
        base = {"pool_pre_ping": True, "pool_size": settings.DATABASE_POOL_SIZE, "max_overflow": settings.DATABASE_MAX_OVERFLOW, "echo": settings.DATABASE_ECHO}
        if self.dialect == DatabaseDialect.SQLITE:
            base.pop("pool_size", None)
            base.pop("max_overflow", None)
        return base


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

    logger.info(f"DB init: dialect={dialect.value}, url_scheme={async_url.split('://')[0]}")

    # pymssql ne supporte pas l'async nativement, mais SQLAlchemy le gère
    # en wrappant les appels sync dans un thread pool
    if "+pymssql" in async_url:
        from sqlalchemy import create_engine
        sync_engine = create_engine(async_url.replace("+pymssql", "+pymssql"), **engine_opts)
        from sqlalchemy.ext.asyncio import AsyncEngine as AE
        eng = AsyncEngine(sync_engine)
        return eng

    eng = create_async_engine(async_url, **engine_opts)

    if dialect == DatabaseDialect.SQLITE:
        @event.listens_for(eng.sync_engine, "connect")
        def _sqlite_pragmas(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.close()

    return eng


engine = create_engine_for_dialect()
async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


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
            return {"status": "connected", "dialect": dialect.value}
    except Exception as e:
        return {"status": "error", "dialect": dialect.value, "error": str(e)}

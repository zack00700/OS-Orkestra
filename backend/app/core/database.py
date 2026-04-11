"""
OS Orkestra — Base de données multi-moteur
Compatible pymssql (sync) sur Render + pyodbc (local) + asyncpg (PostgreSQL)
Python 3.9+
"""
import logging
from enum import Enum
from typing import Optional
from sqlalchemy import event, text, create_engine
from sqlalchemy.orm import Session, sessionmaker, DeclarativeBase
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
    AsyncEngine,
)
from app.core.config import get_settings

logger = logging.getLogger("orkestra.database")
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


def _is_pymssql_url(url: str) -> bool:
    return "+pymssql" in url


def _is_async_capable(url: str) -> bool:
    """Vérifie si l'URL utilise un driver async natif."""
    async_drivers = ["+asyncpg", "+aiomysql", "+aiosqlite", "+aioodbc"]
    return any(d in url for d in async_drivers)


def _build_sync_url(url: str) -> str:
    """Construit l'URL sync pour pymssql ou pyodbc."""
    # Si déjà pymssql ou pyodbc, garder tel quel
    if "+pymssql" in url or "+pyodbc" in url:
        return url
    # Sinon ajouter pymssql par défaut pour mssql
    dialect = detect_dialect(url)
    if dialect == DatabaseDialect.SQLSERVER:
        parts = url.split("://", 1)
        base = parts[0].split("+")[0]
        return f"{base}+pymssql://{parts[1]}"
    return url


def _build_async_url(url: str) -> str:
    """Construit l'URL async si possible."""
    dialect = detect_dialect(url)

    if dialect == DatabaseDialect.POSTGRESQL:
        if "+asyncpg" not in url:
            parts = url.split("://", 1)
            base = parts[0].split("+")[0]
            return f"{base}+asyncpg://{parts[1]}"
        return url

    if dialect in (DatabaseDialect.MYSQL, DatabaseDialect.MARIADB):
        if "+aiomysql" not in url:
            parts = url.split("://", 1)
            base = parts[0].split("+")[0]
            return f"{base}+aiomysql://{parts[1]}"
        return url

    if dialect == DatabaseDialect.SQLITE:
        if "+aiosqlite" not in url:
            parts = url.split("://", 1)
            return f"sqlite+aiosqlite://{parts[1]}"
        return url

    if dialect == DatabaseDialect.SQLSERVER:
        if "+aioodbc" in url:
            return url
        if "+pyodbc" in url:
            return url.replace("+pyodbc", "+aioodbc")

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
    def pagination_style(self) -> str:
        if self.dialect == DatabaseDialect.SQLSERVER:
            return "offset_fetch"
        elif self.dialect == DatabaseDialect.ORACLE:
            return "rownum"
        return "limit_offset"

    @property
    def max_parameters_per_query(self) -> int:
        limits = {DatabaseDialect.SQLITE: 999, DatabaseDialect.SQLSERVER: 2100, DatabaseDialect.MYSQL: 65535, DatabaseDialect.POSTGRESQL: 32767}
        return limits.get(self.dialect, 10000)

    @property
    def default_schema(self) -> Optional[str]:
        return {"postgresql": "public", "mssql": "dbo"}.get(self.dialect.value)

    @property
    def json_extract_function(self) -> str:
        return {"postgresql": "arrow", "mssql": "json_value", "mysql": "json_extract", "mariadb": "json_extract", "sqlite": "json_extract", "oracle": "json_value"}.get(self.dialect.value, "json_extract")


_current_dialect = None
_capabilities = None
_use_sync_mode = False


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


class Base(DeclarativeBase):
    pass


# ══════════════════════════════════════════════════════════
# ENGINE + SESSION FACTORY
# Détecte automatiquement si on peut faire de l'async
# ou si on doit fallback en sync (pymssql)
# ══════════════════════════════════════════════════════════

def _create_engine():
    """Crée le bon type d'engine selon le driver disponible."""
    global _use_sync_mode

    url = settings.DATABASE_URL
    dialect = get_dialect()

    engine_opts = {
        "pool_pre_ping": True,
        "echo": settings.DATABASE_ECHO,
    }

    if dialect != DatabaseDialect.SQLITE:
        engine_opts["pool_size"] = settings.DATABASE_POOL_SIZE
        engine_opts["max_overflow"] = settings.DATABASE_MAX_OVERFLOW

    # CAS 1 : pymssql → mode SYNC (pas de driver async)
    if _is_pymssql_url(url) or (dialect == DatabaseDialect.SQLSERVER and not _is_async_capable(url)):
        _use_sync_mode = True
        sync_url = _build_sync_url(url)
        logger.info(f"DB init (SYNC mode): dialect={dialect.value}, url={sync_url.split('@')[0]}@...")
        return create_engine(sync_url, **engine_opts)

    # CAS 2 : driver async disponible
    _use_sync_mode = False
    async_url = _build_async_url(url)
    logger.info(f"DB init (ASYNC mode): dialect={dialect.value}")

    eng = create_async_engine(async_url, **engine_opts)

    if dialect == DatabaseDialect.SQLITE:
        @event.listens_for(eng.sync_engine, "connect")
        def _sqlite_pragmas(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.close()

    return eng


engine = _create_engine()

# Session factory — sync ou async selon le mode
if _use_sync_mode:
    _sync_session_factory = sessionmaker(engine, expire_on_commit=False)
    # Wrapper pour garder une API async uniforme
    # On utilise un wrapper qui simule AsyncSession avec un Session sync
    async_session_factory = None
else:
    async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    _sync_session_factory = None


# ══════════════════════════════════════════════════════════
# SYNC WRAPPER — simule une AsyncSession avec du sync
# Permet de garder le même code dans les services
# ══════════════════════════════════════════════════════════

class SyncSessionWrapper:
    """Wrappe une Session sync pour exposer la même API qu'AsyncSession."""

    def __init__(self, session: Session):
        self._session = session

    async def execute(self, *args, **kwargs):
        return self._session.execute(*args, **kwargs)

    async def flush(self):
        self._session.flush()

    async def commit(self):
        self._session.commit()

    async def rollback(self):
        self._session.rollback()

    async def close(self):
        self._session.close()

    async def refresh(self, instance):
        self._session.refresh(instance)

    def add(self, instance):
        self._session.add(instance)

    async def delete(self, instance):
        self._session.delete(instance)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._session.close()


async def get_db():
    """Dependency injection — fournit une session DB (sync ou async)."""
    if _use_sync_mode:
        session = _sync_session_factory()
        wrapper = SyncSessionWrapper(session)
        try:
            yield wrapper
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    else:
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
    """Crée les tables au démarrage (dev mode)."""
    if _use_sync_mode:
        Base.metadata.create_all(engine)
    else:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)


async def check_db_connection() -> dict:
    """Test de connexion."""
    dialect = get_dialect()
    try:
        if _use_sync_mode:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return {"status": "connected", "dialect": dialect.value, "mode": "sync"}
        else:
            async with engine.begin() as conn:
                q = "SELECT 1 FROM DUAL" if dialect == DatabaseDialect.ORACLE else "SELECT 1"
                await conn.execute(text(q))
            return {"status": "connected", "dialect": dialect.value, "mode": "async"}
    except Exception as e:
        return {"status": "error", "dialect": dialect.value, "error": str(e)}

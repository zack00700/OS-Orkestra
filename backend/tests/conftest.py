"""
OS Orkestra — Configuration des tests
Utilise SQLite in-memory pour les tests (pas besoin de SQL Server)
"""
import os
import pytest
import asyncio
from typing import AsyncGenerator

# Forcer SQLite in-memory pour les tests AVANT d'importer quoi que ce soit
os.environ["DATABASE_URL"] = "sqlite+aiosqlite://"
os.environ["ENVIRONMENT"] = "test"
os.environ["JWT_SECRET_KEY"] = "test-secret-key"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["ALLOWED_ORIGINS"] = '["*"]'

from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool
from sqlalchemy import event

from app.main import app
from app.core.database import Base, get_db
from app.core.security import hash_password


# ── Test Database (in-memory, shared via StaticPool) ──
test_engine = create_async_engine(
    "sqlite+aiosqlite://",
    echo=False,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
test_session_factory = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@event.listens_for(test_engine.sync_engine, "connect")
def _sqlite_pragmas(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


async def override_get_db():
    async with test_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


app.dependency_overrides[get_db] = override_get_db


# ── Fixtures ─────────────────────────────────────────

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
async def setup_database():
    """Crée les tables avant chaque test et les supprime après."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client() -> AsyncGenerator:
    """Client HTTP pour tester les endpoints."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def db_session() -> AsyncGenerator:
    """Session DB pour insérer des données de test."""
    async with test_session_factory() as session:
        yield session


@pytest.fixture
async def auth_headers(client: AsyncClient, db_session: AsyncSession) -> dict:
    """Crée un utilisateur admin et retourne les headers d'authentification."""
    from app.models.models import User, UserRole
    import uuid

    user = User(
        id=str(uuid.uuid4()),
        email="test@orkestra.com",
        hashed_password=hash_password("TestPass123"),
        full_name="Test Admin",
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()

    # Login
    response = await client.post("/api/v1/auth/login", json={
        "email": "test@orkestra.com",
        "password": "TestPass123",
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

"""
╔═══════════════════════════════════════════════════════════╗
║              OS HubLine — by OpenSID                      ║
║    Marketing Automation & Campaign Management Platform     ║
╚═══════════════════════════════════════════════════════════╝
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import time

from app.core.config import get_settings
from app.core.database import init_db
from app.api.v1.router import api_router

settings = get_settings()

# ── Logging ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("hubline")


# ── Lifespan ────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 OS HubLine starting up...")
    if settings.ENVIRONMENT == "development":
        await init_db()
        logger.info("📦 Database tables created (dev mode)")
    yield
    logger.info("🛑 OS HubLine shutting down...")


# ── App ─────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS ────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request timing middleware ───────────────────────────
@app.middleware("http")
async def add_timing_header(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - start
    response.headers["X-Process-Time"] = f"{duration:.4f}"
    return response


# ── Global exception handler ───────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Erreur interne du serveur"},
    )


# ── Routes ──────────────────────────────────────────────
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/", tags=["Root"])
async def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "status": "running",
    }


@app.get("/health", tags=["Health"])
async def health():
    from app.core.database import check_db_connection, get_dialect, get_capabilities
    db_status = await check_db_connection()
    caps = get_capabilities()
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "database": {
            **db_status,
            "pagination": caps.pagination_style,
            "native_uuid": caps.supports_native_uuid,
            "native_array": caps.supports_native_array,
            "native_json": caps.supports_native_json,
        },
    }

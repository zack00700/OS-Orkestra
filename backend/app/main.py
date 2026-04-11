"""
╔═══════════════════════════════════════════════════════════╗
║              OS Orkestra — by OpenSID                      ║
║    Marketing Automation & Campaign Management Platform     ║
╚═══════════════════════════════════════════════════════════╝
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
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
logger = logging.getLogger("orkestra")


# ── Lifespan ────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("OS Orkestra starting up...")
    if settings.ENVIRONMENT == "development":
        await init_db()
        logger.info("Database tables created (dev mode)")
    yield
    logger.info("OS Orkestra shutting down...")


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


# ── API Routes ──────────────────────────────────────────
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


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


# ── Frontend React (servir les fichiers buildés) ────────
# Le build command sur Render copie frontend/dist → backend/frontend_dist
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend_dist")

if os.path.exists(FRONTEND_DIR):
    logger.info(f"Frontend found at {FRONTEND_DIR} — serving static files")

    # Servir les assets (JS, CSS, images)
    assets_dir = os.path.join(FRONTEND_DIR, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="static_assets")

    # Catch-all : toute route non-API renvoie index.html (SPA routing)
    @app.get("/{full_path:path}", tags=["Frontend"])
    async def serve_frontend(full_path: str):
        # Ne pas intercepter les routes API et docs
        if full_path.startswith("api/") or full_path in ("docs", "redoc", "openapi.json", "health"):
            return JSONResponse(status_code=404, content={"detail": "Not found"})

        # Chercher le fichier exact (favicon, robots.txt, etc.)
        file_path = os.path.join(FRONTEND_DIR, full_path)
        if full_path and os.path.isfile(file_path):
            return FileResponse(file_path)

        # Sinon renvoyer index.html (React Router gère le routing côté client)
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))
else:
    logger.info("No frontend build found — API only mode")

    @app.get("/", tags=["Root"])
    async def root():
        return {
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "docs": "/docs",
            "status": "running",
        }

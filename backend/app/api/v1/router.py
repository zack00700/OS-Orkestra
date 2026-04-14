"""
OS Orkestra — Routeur API v1
"""
from fastapi import APIRouter
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.contacts import router as contacts_router
from app.api.v1.endpoints.campaigns import router as campaigns_router
from app.api.v1.endpoints.integrations import router as integrations_router
from app.api.v1.endpoints.tracking import router as tracking_router
from app.api.v1.endpoints.analytics import router as analytics_router
from app.api.v1.endpoints.templates_segments import templates_router, segments_router
from app.api.v1.endpoints.mapping import router as mapping_router
from app.api.v1.endpoints.diffusion import router as diffusion_router
from app.api.v1.endpoints.csv_import import router as csv_import_router
from app.api.v1.endpoints.writeback import router as writeback_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(contacts_router)
api_router.include_router(campaigns_router)
api_router.include_router(integrations_router)
api_router.include_router(tracking_router)
api_router.include_router(analytics_router)
api_router.include_router(templates_router)
api_router.include_router(segments_router)
api_router.include_router(mapping_router)
api_router.include_router(diffusion_router)
api_router.include_router(csv_import_router)
api_router.include_router(writeback_router)

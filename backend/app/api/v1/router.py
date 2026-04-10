"""
OS HubLine — Routeur API v1
"""
from fastapi import APIRouter
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.contacts import router as contacts_router
from app.api.v1.endpoints.campaigns import router as campaigns_router
from app.api.v1.endpoints.integrations import router as integrations_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(contacts_router)
api_router.include_router(campaigns_router)
api_router.include_router(integrations_router)

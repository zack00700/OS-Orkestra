"""
OS Orkestra — Endpoints de tracking (ouvertures et clics)
Compatible Python 3.9+
"""
from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, Query
from fastapi.responses import RedirectResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services import CampaignService
from app.models.models import EventType

router = APIRouter(prefix="/tracking", tags=["Tracking"])

# Pixel GIF transparent 1x1
TRACKING_PIXEL = bytes([
    0x47, 0x49, 0x46, 0x38, 0x39, 0x61, 0x01, 0x00, 0x01, 0x00,
    0x80, 0x00, 0x00, 0xFF, 0xFF, 0xFF, 0x00, 0x00, 0x00, 0x21,
    0xF9, 0x04, 0x00, 0x00, 0x00, 0x00, 0x00, 0x2C, 0x00, 0x00,
    0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0x00, 0x02, 0x02, 0x4C,
    0x01, 0x00, 0x3B
])


@router.get("/open/{campaign_id}/{contact_id}")
async def track_open(
    campaign_id: UUID,
    contact_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Pixel de tracking — enregistre une ouverture."""
    try:
        service = CampaignService(db)
        await service.record_event(
            campaign_id=campaign_id,
            contact_id=contact_id,
            event_type=EventType.OPENED,
        )
    except Exception:
        pass  # Ne jamais bloquer le rendu de l'email
    return Response(content=TRACKING_PIXEL, media_type="image/gif")


@router.get("/click/{campaign_id}/{contact_id}")
async def track_click(
    campaign_id: UUID,
    contact_id: UUID,
    url: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Redirection de clic — enregistre le clic puis redirige."""
    try:
        service = CampaignService(db)
        await service.record_event(
            campaign_id=campaign_id,
            contact_id=contact_id,
            event_type=EventType.CLICKED,
            url_clicked=url,
        )
    except Exception:
        pass
    return RedirectResponse(url=url)

"""
OS HubLine — API Endpoints : Campagnes
"""
from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import get_current_user, require_roles
from app.services import CampaignService
from app.schemas import (
    CampaignCreate, CampaignResponse, CampaignUpdate,
    CampaignListResponse, CampaignAnalytics, MessageResponse,
)
from app.models import CampaignStatus, CampaignType, ChannelType

router = APIRouter(prefix="/campaigns", tags=["Campagnes"])


@router.get("/", response_model=CampaignListResponse)
async def list_campaigns(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[CampaignStatus] = None,
    campaign_type: Optional[CampaignType] = None,
    channel: Optional[ChannelType] = None,
    search: Optional[str] = None,
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Liste des campagnes avec filtres."""
    service = CampaignService(db)
    return await service.list(
        page=page, page_size=page_size, status=status,
        campaign_type=campaign_type, channel=channel,
        search=search, sort_by=sort_by, sort_order=sort_order,
    )


@router.get("/dashboard")
async def get_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Données du dashboard principal."""
    service = CampaignService(db)
    return await service.get_dashboard_stats()


@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    service = CampaignService(db)
    campaign = await service.get_by_id(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campagne non trouvée")
    return campaign


@router.get("/{campaign_id}/analytics", response_model=CampaignAnalytics)
async def get_campaign_analytics(
    campaign_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Analytics détaillés d'une campagne."""
    service = CampaignService(db)
    analytics = await service.get_analytics(campaign_id)
    if not analytics:
        raise HTTPException(status_code=404, detail="Campagne non trouvée")
    return analytics


@router.post("/", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    data: CampaignCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_roles("admin", "manager", "editor")),
):
    """Créer une nouvelle campagne."""
    service = CampaignService(db)
    user_id = UUID(current_user["sub"])
    return await service.create(data, user_id)


@router.patch("/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(
    campaign_id: UUID,
    data: CampaignUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_roles("admin", "manager", "editor")),
):
    service = CampaignService(db)
    campaign = await service.update(campaign_id, data)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campagne non trouvée")
    return campaign


@router.post("/{campaign_id}/launch", response_model=CampaignResponse)
async def launch_campaign(
    campaign_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_roles("admin", "manager")),
):
    """Lancer une campagne."""
    service = CampaignService(db)
    campaign = await service.launch(campaign_id)
    if not campaign:
        raise HTTPException(
            status_code=400,
            detail="Impossible de lancer cette campagne (vérifiez le statut)"
        )
    # Déclencher l'envoi async
    from app.tasks.celery_tasks import send_campaign_emails
    send_campaign_emails.delay(str(campaign_id))
    return campaign


@router.post("/{campaign_id}/pause", response_model=CampaignResponse)
async def pause_campaign(
    campaign_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_roles("admin", "manager")),
):
    service = CampaignService(db)
    campaign = await service.pause(campaign_id)
    if not campaign:
        raise HTTPException(status_code=400, detail="Impossible de mettre en pause")
    return campaign


@router.post("/{campaign_id}/complete", response_model=CampaignResponse)
async def complete_campaign(
    campaign_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_roles("admin", "manager")),
):
    service = CampaignService(db)
    campaign = await service.complete(campaign_id)
    if not campaign:
        raise HTTPException(status_code=400, detail="Impossible de terminer")
    return campaign

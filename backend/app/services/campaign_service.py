"""
OS HubLine — Service Campagnes
"""
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import (
    Campaign, CampaignEvent, CampaignStatus, CampaignType,
    ChannelType, EventType, Contact,
)
from app.schemas import (
    CampaignCreate, CampaignUpdate, CampaignResponse,
    CampaignListResponse, CampaignAnalytics,
)


class CampaignService:
    """Service de gestion des campagnes."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: CampaignCreate, user_id: uuid.UUID) -> Campaign:
        campaign = Campaign(
            **data.model_dump(exclude_none=True),
            created_by=user_id,
        )
        self.db.add(campaign)
        await self.db.flush()
        await self.db.refresh(campaign)
        return campaign

    async def get_by_id(self, campaign_id: uuid.UUID) -> Optional[Campaign]:
        result = await self.db.execute(
            select(Campaign).where(Campaign.id == campaign_id)
        )
        return result.scalar_one_or_none()

    async def list(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[CampaignStatus] = None,
        campaign_type: Optional[CampaignType] = None,
        channel: Optional[ChannelType] = None,
        search: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> CampaignListResponse:
        query = select(Campaign)
        count_query = select(func.count(Campaign.id))

        filters = []
        if status:
            filters.append(Campaign.status == status)
        if campaign_type:
            filters.append(Campaign.campaign_type == campaign_type)
        if channel:
            filters.append(Campaign.channel == channel)
        if search:
            filters.append(Campaign.name.ilike(f"%{search}%"))

        if filters:
            combined = and_(*filters)
            query = query.where(combined)
            count_query = count_query.where(combined)

        sort_col = getattr(Campaign, sort_by, Campaign.created_at)
        query = query.order_by(sort_col.desc() if sort_order == "desc" else sort_col.asc())

        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        campaigns = result.scalars().all()

        return CampaignListResponse(
            items=[CampaignResponse.model_validate(c) for c in campaigns],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def update(self, campaign_id: uuid.UUID, data: CampaignUpdate) -> Optional[Campaign]:
        campaign = await self.get_by_id(campaign_id)
        if not campaign:
            return None

        update_data = data.model_dump(exclude_none=True)
        for field, value in update_data.items():
            setattr(campaign, field, value)

        campaign.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self.db.refresh(campaign)
        return campaign

    async def launch(self, campaign_id: uuid.UUID) -> Optional[Campaign]:
        """Lancer une campagne (passer en RUNNING)."""
        campaign = await self.get_by_id(campaign_id)
        if not campaign or campaign.status not in (CampaignStatus.DRAFT, CampaignStatus.SCHEDULED):
            return None

        campaign.status = CampaignStatus.RUNNING
        campaign.sent_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self.db.refresh(campaign)
        return campaign

    async def pause(self, campaign_id: uuid.UUID) -> Optional[Campaign]:
        campaign = await self.get_by_id(campaign_id)
        if not campaign or campaign.status != CampaignStatus.RUNNING:
            return None
        campaign.status = CampaignStatus.PAUSED
        await self.db.flush()
        return campaign

    async def complete(self, campaign_id: uuid.UUID) -> Optional[Campaign]:
        campaign = await self.get_by_id(campaign_id)
        if not campaign:
            return None
        campaign.status = CampaignStatus.COMPLETED
        campaign.completed_at = datetime.now(timezone.utc)
        await self.db.flush()
        return campaign

    async def record_event(
        self,
        campaign_id: uuid.UUID,
        contact_id: uuid.UUID,
        event_type: EventType,
        metadata: Optional[dict] = None,
        url_clicked: Optional[str] = None,
    ) -> CampaignEvent:
        """Enregistrer un événement de tracking."""
        event = CampaignEvent(
            campaign_id=campaign_id,
            contact_id=contact_id,
            event_type=event_type,
            metadata_json=metadata,
            url_clicked=url_clicked,
        )
        self.db.add(event)

        # Mise à jour des compteurs agrégés
        campaign = await self.get_by_id(campaign_id)
        if campaign:
            counter_map = {
                EventType.SENT: "total_sent",
                EventType.DELIVERED: "total_delivered",
                EventType.OPENED: "total_opened",
                EventType.CLICKED: "total_clicked",
                EventType.BOUNCED_SOFT: "total_bounced",
                EventType.BOUNCED_HARD: "total_bounced",
                EventType.UNSUBSCRIBED: "total_unsubscribed",
            }
            attr = counter_map.get(event_type)
            if attr:
                setattr(campaign, attr, getattr(campaign, attr) + 1)

        await self.db.flush()
        await self.db.refresh(event)
        return event

    async def get_analytics(self, campaign_id: uuid.UUID) -> Optional[CampaignAnalytics]:
        """Calculer les analytics d'une campagne."""
        campaign = await self.get_by_id(campaign_id)
        if not campaign:
            return None

        # Comptage des opens et clicks uniques
        unique_opens = await self.db.execute(
            select(func.count(func.distinct(CampaignEvent.contact_id)))
            .where(and_(
                CampaignEvent.campaign_id == campaign_id,
                CampaignEvent.event_type == EventType.OPENED,
            ))
        )
        unique_clicks = await self.db.execute(
            select(func.count(func.distinct(CampaignEvent.contact_id)))
            .where(and_(
                CampaignEvent.campaign_id == campaign_id,
                CampaignEvent.event_type == EventType.CLICKED,
            ))
        )

        sent = max(campaign.total_sent, 1)  # Éviter division par zéro
        delivered = max(campaign.total_delivered, 1)
        u_opens = unique_opens.scalar() or 0
        u_clicks = unique_clicks.scalar() or 0

        return CampaignAnalytics(
            campaign_id=campaign.id,
            campaign_name=campaign.name,
            total_sent=campaign.total_sent,
            total_delivered=campaign.total_delivered,
            total_opened=campaign.total_opened,
            unique_opens=u_opens,
            total_clicked=campaign.total_clicked,
            unique_clicks=u_clicks,
            total_bounced=campaign.total_bounced,
            total_unsubscribed=campaign.total_unsubscribed,
            open_rate=round(u_opens / delivered * 100, 2),
            click_rate=round(u_clicks / delivered * 100, 2),
            reactivity_rate=round(u_clicks / max(u_opens, 1) * 100, 2),
            deliverability_rate=round(campaign.total_delivered / sent * 100, 2),
            bounce_rate=round(campaign.total_bounced / sent * 100, 2),
            unsubscribe_rate=round(campaign.total_unsubscribed / sent * 100, 2),
        )

    async def get_dashboard_stats(self) -> dict:
        """Stats globales pour le dashboard."""
        now = datetime.now(timezone.utc)
        thirty_days_ago = now - timedelta(days=30)

        total_campaigns = await self.db.execute(select(func.count(Campaign.id)))
        active_campaigns = await self.db.execute(
            select(func.count(Campaign.id))
            .where(Campaign.status == CampaignStatus.RUNNING)
        )
        total_sent_30d = await self.db.execute(
            select(func.count(CampaignEvent.id))
            .where(and_(
                CampaignEvent.event_type == EventType.SENT,
                CampaignEvent.timestamp >= thirty_days_ago,
            ))
        )

        return {
            "total_campaigns": total_campaigns.scalar() or 0,
            "active_campaigns": active_campaigns.scalar() or 0,
            "total_sent_30d": total_sent_30d.scalar() or 0,
        }

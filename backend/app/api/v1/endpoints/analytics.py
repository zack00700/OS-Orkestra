"""
OS Orkestra — Endpoints Analytics avancés
Compatible Python 3.9+
"""
from uuid import UUID
from typing import Optional
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, and_, cast, Date
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.models import (
    Campaign, CampaignEvent, Contact, EventType,
    CampaignStatus, CampaignType,
)

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/overview")
async def get_overview(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Vue d'ensemble analytics sur N jours."""
    since = datetime.now(timezone.utc) - timedelta(days=days)

    # Total envoyés
    total_sent = await db.execute(
        select(func.count(CampaignEvent.id)).where(
            and_(CampaignEvent.event_type == EventType.SENT, CampaignEvent.timestamp >= since)
        )
    )
    # Total délivrés
    total_delivered = await db.execute(
        select(func.count(CampaignEvent.id)).where(
            and_(CampaignEvent.event_type == EventType.DELIVERED, CampaignEvent.timestamp >= since)
        )
    )
    # Total ouverts
    total_opened = await db.execute(
        select(func.count(CampaignEvent.id)).where(
            and_(CampaignEvent.event_type == EventType.OPENED, CampaignEvent.timestamp >= since)
        )
    )
    # Total cliqués
    total_clicked = await db.execute(
        select(func.count(CampaignEvent.id)).where(
            and_(CampaignEvent.event_type == EventType.CLICKED, CampaignEvent.timestamp >= since)
        )
    )
    # Unique opens
    unique_opens = await db.execute(
        select(func.count(func.distinct(CampaignEvent.contact_id))).where(
            and_(CampaignEvent.event_type == EventType.OPENED, CampaignEvent.timestamp >= since)
        )
    )
    # Unique clicks
    unique_clicks = await db.execute(
        select(func.count(func.distinct(CampaignEvent.contact_id))).where(
            and_(CampaignEvent.event_type == EventType.CLICKED, CampaignEvent.timestamp >= since)
        )
    )
    # Bounces
    total_bounced = await db.execute(
        select(func.count(CampaignEvent.id)).where(
            and_(
                CampaignEvent.event_type.in_([EventType.BOUNCED_SOFT, EventType.BOUNCED_HARD]),
                CampaignEvent.timestamp >= since,
            )
        )
    )
    # Unsubscribes
    total_unsub = await db.execute(
        select(func.count(CampaignEvent.id)).where(
            and_(CampaignEvent.event_type == EventType.UNSUBSCRIBED, CampaignEvent.timestamp >= since)
        )
    )
    # Campaigns count
    total_campaigns = await db.execute(select(func.count(Campaign.id)))
    active_campaigns = await db.execute(
        select(func.count(Campaign.id)).where(Campaign.status == CampaignStatus.RUNNING)
    )

    s = total_sent.scalar() or 0
    d = total_delivered.scalar() or 0
    o = total_opened.scalar() or 0
    c = total_clicked.scalar() or 0
    uo = unique_opens.scalar() or 0
    uc = unique_clicks.scalar() or 0
    b = total_bounced.scalar() or 0

    return {
        "period_days": days,
        "total_sent": s,
        "total_delivered": d,
        "total_opened": o,
        "total_clicked": c,
        "unique_opens": uo,
        "unique_clicks": uc,
        "total_bounced": b,
        "total_unsubscribed": total_unsub.scalar() or 0,
        "total_campaigns": total_campaigns.scalar() or 0,
        "active_campaigns": active_campaigns.scalar() or 0,
        "open_rate": round(uo / max(d, 1) * 100, 2),
        "click_rate": round(uc / max(d, 1) * 100, 2),
        "bounce_rate": round(b / max(s, 1) * 100, 2),
        "deliverability_rate": round(d / max(s, 1) * 100, 2),
    }


@router.get("/campaigns/ranking")
async def get_campaigns_ranking(
    limit: int = Query(10, ge=1, le=50),
    sort_by: str = Query("total_opened", regex="^(total_sent|total_opened|total_clicked|total_delivered)$"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Classement des campagnes par performance."""
    sort_col = getattr(Campaign, sort_by, Campaign.total_opened)
    result = await db.execute(
        select(Campaign)
        .where(Campaign.total_sent > 0)
        .order_by(sort_col.desc())
        .limit(limit)
    )
    campaigns = result.scalars().all()

    ranking = []
    for camp in campaigns:
        d = max(camp.total_delivered, 1)
        ranking.append({
            "id": str(camp.id),
            "name": camp.name,
            "type": camp.campaign_type.value if hasattr(camp.campaign_type, 'value') else camp.campaign_type,
            "channel": camp.channel.value if hasattr(camp.channel, 'value') else camp.channel,
            "status": camp.status.value if hasattr(camp.status, 'value') else camp.status,
            "total_sent": camp.total_sent,
            "total_delivered": camp.total_delivered,
            "total_opened": camp.total_opened,
            "total_clicked": camp.total_clicked,
            "total_bounced": camp.total_bounced,
            "total_unsubscribed": camp.total_unsubscribed,
            "open_rate": round(camp.total_opened / d * 100, 2),
            "click_rate": round(camp.total_clicked / d * 100, 2),
            "bounce_rate": round(camp.total_bounced / max(camp.total_sent, 1) * 100, 2),
        })
    return ranking


@router.get("/campaigns/{campaign_id}/detail")
async def get_campaign_detail(
    campaign_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Analytics détaillés d'une campagne spécifique."""
    # Campaign info
    camp_result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
    camp = camp_result.scalar_one_or_none()
    if not camp:
        return {"error": "Campagne non trouvée"}

    d = max(camp.total_delivered, 1)
    s = max(camp.total_sent, 1)

    # Top URLs cliquées
    url_clicks = await db.execute(
        select(CampaignEvent.url_clicked, func.count(CampaignEvent.id).label("clicks"))
        .where(and_(
            CampaignEvent.campaign_id == campaign_id,
            CampaignEvent.event_type == EventType.CLICKED,
            CampaignEvent.url_clicked.isnot(None),
        ))
        .group_by(CampaignEvent.url_clicked)
        .order_by(func.count(CampaignEvent.id).desc())
        .limit(10)
    )

    # Events par type
    events_by_type = await db.execute(
        select(CampaignEvent.event_type, func.count(CampaignEvent.id))
        .where(CampaignEvent.campaign_id == campaign_id)
        .group_by(CampaignEvent.event_type)
    )

    return {
        "campaign": {
            "id": str(camp.id),
            "name": camp.name,
            "type": camp.campaign_type.value if hasattr(camp.campaign_type, 'value') else camp.campaign_type,
            "channel": camp.channel.value if hasattr(camp.channel, 'value') else camp.channel,
            "status": camp.status.value if hasattr(camp.status, 'value') else camp.status,
            "subject": camp.subject,
            "sent_at": camp.sent_at.isoformat() if camp.sent_at else None,
            "completed_at": camp.completed_at.isoformat() if camp.completed_at else None,
        },
        "metrics": {
            "total_sent": camp.total_sent,
            "total_delivered": camp.total_delivered,
            "total_opened": camp.total_opened,
            "total_clicked": camp.total_clicked,
            "total_bounced": camp.total_bounced,
            "total_unsubscribed": camp.total_unsubscribed,
            "open_rate": round(camp.total_opened / d * 100, 2),
            "click_rate": round(camp.total_clicked / d * 100, 2),
            "reactivity_rate": round(camp.total_clicked / max(camp.total_opened, 1) * 100, 2),
            "deliverability_rate": round(camp.total_delivered / s * 100, 2),
            "bounce_rate": round(camp.total_bounced / s * 100, 2),
            "unsubscribe_rate": round(camp.total_unsubscribed / s * 100, 2),
        },
        "top_links": [
            {"url": row[0], "clicks": row[1]}
            for row in url_clicks.all()
        ],
        "events_breakdown": {
            str(row[0]): row[1]
            for row in events_by_type.all()
        },
    }


@router.get("/segments/performance")
async def get_segments_performance(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Performance par segment de contacts."""
    from app.models.models import Segment

    result = await db.execute(select(Segment))
    segments = result.scalars().all()

    data = []
    for seg in segments:
        data.append({
            "id": str(seg.id),
            "name": seg.name,
            "contact_count": seg.contact_count,
            "is_dynamic": seg.is_dynamic,
        })
    return data

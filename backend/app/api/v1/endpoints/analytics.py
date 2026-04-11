"""
OS Orkestra — Endpoints Analytics avancés
Compatible Python 3.9+ / pymssql sync
"""
from uuid import UUID
from typing import Optional
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, and_, text
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.models import (
    Campaign, CampaignEvent, Contact, EventType,
    CampaignStatus, CampaignType,
)

router = APIRouter(prefix="/analytics", tags=["Analytics"])


def _safe_scalar(result):
    """Extrait un scalar de manière sûre pour sync et async."""
    try:
        row = result.fetchone()
        return row[0] if row else 0
    except Exception:
        try:
            return result.scalar() or 0
        except Exception:
            return 0


@router.get("/overview")
async def get_overview(
    days: int = Query(30, ge=1, le=365),
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Vue d'ensemble analytics sur N jours."""
    since_str = (datetime.now(timezone.utc) - timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')

    s = _safe_scalar(await db.execute(text(f"SELECT COUNT(*) FROM campaign_events WHERE event_type = 'SENT' AND timestamp >= '{since_str}'")))
    d = _safe_scalar(await db.execute(text(f"SELECT COUNT(*) FROM campaign_events WHERE event_type = 'DELIVERED' AND timestamp >= '{since_str}'")))
    o = _safe_scalar(await db.execute(text(f"SELECT COUNT(*) FROM campaign_events WHERE event_type = 'OPENED' AND timestamp >= '{since_str}'")))
    c = _safe_scalar(await db.execute(text(f"SELECT COUNT(*) FROM campaign_events WHERE event_type = 'CLICKED' AND timestamp >= '{since_str}'")))
    uo = _safe_scalar(await db.execute(text(f"SELECT COUNT(DISTINCT contact_id) FROM campaign_events WHERE event_type = 'OPENED' AND timestamp >= '{since_str}'")))
    uc = _safe_scalar(await db.execute(text(f"SELECT COUNT(DISTINCT contact_id) FROM campaign_events WHERE event_type = 'CLICKED' AND timestamp >= '{since_str}'")))
    b = _safe_scalar(await db.execute(text(f"SELECT COUNT(*) FROM campaign_events WHERE event_type IN ('BOUNCED_SOFT','BOUNCED_HARD') AND timestamp >= '{since_str}'")))
    u = _safe_scalar(await db.execute(text(f"SELECT COUNT(*) FROM campaign_events WHERE event_type = 'UNSUBSCRIBED' AND timestamp >= '{since_str}'")))
    tc = _safe_scalar(await db.execute(text("SELECT COUNT(*) FROM campaigns")))
    ac = _safe_scalar(await db.execute(text("SELECT COUNT(*) FROM campaigns WHERE status = 'RUNNING'")))

    return {
        "period_days": days,
        "total_sent": s,
        "total_delivered": d,
        "total_opened": o,
        "total_clicked": c,
        "unique_opens": uo,
        "unique_clicks": uc,
        "total_bounced": b,
        "total_unsubscribed": u,
        "total_campaigns": tc,
        "active_campaigns": ac,
        "open_rate": round(uo / max(d, 1) * 100, 2),
        "click_rate": round(uc / max(d, 1) * 100, 2),
        "bounce_rate": round(b / max(s, 1) * 100, 2),
        "deliverability_rate": round(d / max(s, 1) * 100, 2),
    }


@router.get("/campaigns/ranking")
async def get_campaigns_ranking(
    limit: int = Query(10, ge=1, le=50),
    sort_by: str = Query("total_opened"),
    db=Depends(get_db),
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
            "type": camp.campaign_type.value if hasattr(camp.campaign_type, 'value') else str(camp.campaign_type),
            "channel": camp.channel.value if hasattr(camp.channel, 'value') else str(camp.channel),
            "status": camp.status.value if hasattr(camp.status, 'value') else str(camp.status),
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
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Analytics détaillés d'une campagne spécifique."""
    camp_result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
    camp = camp_result.scalar_one_or_none()
    if not camp:
        return {"error": "Campagne non trouvée"}

    d = max(camp.total_delivered, 1)
    s = max(camp.total_sent, 1)

    # Top URLs cliquées
    cid = str(campaign_id)
    url_result = await db.execute(text(
        f"SELECT url_clicked, COUNT(*) as clicks FROM campaign_events "
        f"WHERE campaign_id = '{cid}' AND event_type = 'CLICKED' AND url_clicked IS NOT NULL "
        f"GROUP BY url_clicked ORDER BY COUNT(*) DESC"
    ))

    # Events par type
    evt_result = await db.execute(text(
        f"SELECT event_type, COUNT(*) as cnt FROM campaign_events "
        f"WHERE campaign_id = '{cid}' GROUP BY event_type"
    ))

    return {
        "campaign": {
            "id": str(camp.id),
            "name": camp.name,
            "type": camp.campaign_type.value if hasattr(camp.campaign_type, 'value') else str(camp.campaign_type),
            "channel": camp.channel.value if hasattr(camp.channel, 'value') else str(camp.channel),
            "status": camp.status.value if hasattr(camp.status, 'value') else str(camp.status),
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
            for row in url_result.fetchall()
        ],
        "events_breakdown": {
            str(row[0]): row[1]
            for row in evt_result.fetchall()
        },
    }


@router.get("/segments/performance")
async def get_segments_performance(
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Performance par segment de contacts."""
    from app.models.models import Segment
    result = await db.execute(select(Segment))
    segments = result.scalars().all()
    return [
        {"id": str(seg.id), "name": seg.name, "contact_count": seg.contact_count, "is_dynamic": seg.is_dynamic}
        for seg in segments
    ]

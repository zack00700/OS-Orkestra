"""
OS Orkestra — Endpoints de tracking (ouvertures et clics)
+ Scoring automatique des contacts
Compatible Python 3.9+
"""
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import urlparse
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse, Response
from sqlalchemy import select, text
from app.core.database import get_db
from app.models.models import CampaignEvent, EventType, Contact, Campaign

logger = logging.getLogger("orkestra.tracking")

router = APIRouter(prefix="/tracking", tags=["Tracking"])

# Pixel GIF transparent 1x1
TRACKING_PIXEL = bytes([
    0x47, 0x49, 0x46, 0x38, 0x39, 0x61, 0x01, 0x00, 0x01, 0x00,
    0x80, 0x00, 0x00, 0xFF, 0xFF, 0xFF, 0x00, 0x00, 0x00, 0x21,
    0xF9, 0x04, 0x00, 0x00, 0x00, 0x00, 0x00, 0x2C, 0x00, 0x00,
    0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0x00, 0x02, 0x02, 0x4C,
    0x01, 0x00, 0x3B
])

# ══════════════════════════════════════════════════════════
# SCORING CONFIG
# ══════════════════════════════════════════════════════════

SCORE_RULES = {
    EventType.OPENED: 5,
    EventType.CLICKED: 10,
    EventType.UNSUBSCRIBED: -20,
    EventType.BOUNCED_SOFT: -5,
    EventType.BOUNCED_HARD: -10,
}


def _calculate_lead_stage(score: int) -> str:
    """Détermine le lead_stage basé sur le score."""
    if score >= 80:
        return "purchase"
    elif score >= 50:
        return "consideration"
    elif score >= 20:
        return "interest"
    return "awareness"


async def _update_contact_score(db, contact_id: str, event_type: EventType):
    """Met à jour le lead_score et lead_stage d'un contact après un événement."""
    delta = SCORE_RULES.get(event_type, 0)
    if delta == 0:
        return

    try:
        result = await db.execute(
            select(Contact).where(Contact.id == contact_id)
        )
        contact = result.scalar_one_or_none()
        if not contact:
            return

        old_score = contact.lead_score or 0
        new_score = max(0, old_score + delta)
        new_stage = _calculate_lead_stage(new_score)

        contact.lead_score = new_score
        contact.lead_stage = new_stage
        await db.flush()
        logger.info("Contact %s score updated: %d -> %d (%s), stage: %s",
                     contact_id, old_score, new_score, event_type.value, new_stage)
    except Exception as e:
        logger.warning("Failed to update score for contact %s: %s", contact_id, str(e))


async def _record_event(db, campaign_id: str, contact_id: str, event_type: EventType, url_clicked: Optional[str] = None):
    """Enregistre un événement de campagne et met à jour le score."""
    try:
        # Enregistrer l'événement
        event = CampaignEvent(
            id=str(uuid.uuid4()),
            campaign_id=str(campaign_id),
            contact_id=str(contact_id),
            event_type=event_type,
            timestamp=datetime.now(timezone.utc),
            url_clicked=url_clicked,
        )
        db.add(event)

        # Mettre à jour les compteurs de la campagne
        counter_map = {
            EventType.OPENED: "total_opened",
            EventType.CLICKED: "total_clicked",
            EventType.UNSUBSCRIBED: "total_unsubscribed",
            EventType.BOUNCED_SOFT: "total_bounced",
            EventType.BOUNCED_HARD: "total_bounced",
        }
        counter_col = counter_map.get(event_type)
        if counter_col:
            await db.execute(
                text(f"UPDATE campaigns SET {counter_col} = {counter_col} + 1 WHERE id = :cid"),
                {"cid": str(campaign_id)}
            )

        # Mettre à jour le score du contact
        await _update_contact_score(db, str(contact_id), event_type)

        await db.flush()
    except Exception as e:
        logger.warning("Failed to record event: %s", str(e))


# ══════════════════════════════════════════════════════════
# ENDPOINTS
# ══════════════════════════════════════════════════════════

@router.get("/open/{campaign_id}/{contact_id}")
async def track_open(
    campaign_id: str,
    contact_id: str,
    db=Depends(get_db),
):
    """Pixel de tracking — enregistre une ouverture + met à jour le score (+5)."""
    try:
        await _record_event(db, campaign_id, contact_id, EventType.OPENED)
    except Exception:
        pass  # Ne jamais bloquer le rendu de l'email
    return Response(content=TRACKING_PIXEL, media_type="image/gif")


@router.get("/click/{campaign_id}/{contact_id}")
async def track_click(
    campaign_id: str,
    contact_id: str,
    url: str = Query(...),
    db=Depends(get_db),
):
    """Redirection de clic — enregistre le clic + met à jour le score (+10)."""
    # Validation anti Open Redirect
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise HTTPException(status_code=400, detail="URL invalide")

    try:
        await _record_event(db, campaign_id, contact_id, EventType.CLICKED, url_clicked=url)
    except Exception:
        pass
    return RedirectResponse(url=url)


@router.post("/unsubscribe/{campaign_id}/{contact_id}")
async def track_unsubscribe(
    campaign_id: str,
    contact_id: str,
    db=Depends(get_db),
):
    """Désinscription — enregistre + met à jour le score (-20)."""
    try:
        await _record_event(db, campaign_id, contact_id, EventType.UNSUBSCRIBED)

        # Mettre le contact en statut unsubscribed
        result = await db.execute(
            select(Contact).where(Contact.id == str(contact_id))
        )
        contact = result.scalar_one_or_none()
        if contact:
            contact.status = "unsubscribed"
            await db.flush()
    except Exception as e:
        logger.warning("Failed to process unsubscribe: %s", str(e))

    return {"status": "unsubscribed", "message": "Vous avez été désinscrit."}


@router.get("/scores/summary")
async def get_scoring_summary(
    db=Depends(get_db),
):
    """Résumé du scoring — distribution des contacts par lead_stage."""
    try:
        result = await db.execute(text(
            "SELECT lead_stage, COUNT(*) as cnt, AVG(lead_score) as avg_score "
            "FROM contacts GROUP BY lead_stage"
        ))
        rows = result.fetchall()
        return {
            "stages": [
                {"stage": row[0], "count": row[1], "avg_score": round(row[2] or 0, 1)}
                for row in rows
            ],
            "rules": {k.value: v for k, v in SCORE_RULES.items()},
        }
    except Exception as e:
        return {"error": str(e)}

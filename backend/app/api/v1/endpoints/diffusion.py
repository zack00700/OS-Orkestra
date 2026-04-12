"""
OS Orkestra — Endpoints Diffusion
Configure les canaux d'envoi (SMTP, WhatsApp, SMS) et gère l'envoi réel.
Compatible Python 3.9+ / pymssql sync
"""
import uuid
import json
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, text
from app.core.database import get_db
from app.core.security import require_roles, get_current_user
from app.models.models import Campaign, Contact, Template, Segment, CampaignEvent, EventType, CampaignStatus

logger = logging.getLogger("orkestra.diffusion")

router = APIRouter(prefix="/diffusion", tags=["Diffusion"])

# Whitelist des colonnes autorisées pour les filtres (anti SQL injection)
ALLOWED_FILTER_COLUMNS = {"country", "city", "company", "segment", "source", "status", "lead_stage", "business_unit"}


# ══════════════════════════════════════════════════════════
# SCHEMAS
# ══════════════════════════════════════════════════════════

class SMTPConfig(BaseModel):
    host: str
    port: int = 587
    username: str
    password: str
    use_tls: bool = True
    from_email: str
    from_name: str = "OS Orkestra"


class WhatsAppConfig(BaseModel):
    api_token: str
    phone_number_id: str


class SMSConfig(BaseModel):
    provider: str = "twilio"
    api_key: str
    api_secret: str = ""
    from_number: str = ""


class SendTestEmail(BaseModel):
    to_email: str
    subject: str = "Test OS Orkestra"
    body: str = "Ceci est un email de test envoyé depuis OS Orkestra."


class LaunchCampaignRequest(BaseModel):
    campaign_id: str


# ══════════════════════════════════════════════════════════
# STOCKAGE CONFIG (en mémoire — sera persisté plus tard)
# ══════════════════════════════════════════════════════════

_diffusion_config: Dict[str, Any] = {}


# ══════════════════════════════════════════════════════════
# ENDPOINTS CONFIG
# ══════════════════════════════════════════════════════════

@router.get("/config")
async def get_diffusion_config(
    current_user: dict = Depends(require_roles("admin", "manager")),
):
    """Récupère la config de diffusion actuelle."""
    safe = {}
    for key, val in _diffusion_config.items():
        if isinstance(val, dict):
            safe[key] = {k: ("****" if k in ("password", "api_token", "api_key", "api_secret") else v) for k, v in val.items()}
        else:
            safe[key] = val
    return {
        "smtp": safe.get("smtp", {"status": "not_configured"}),
        "whatsapp": safe.get("whatsapp", {"status": "not_configured"}),
        "sms": safe.get("sms", {"status": "not_configured"}),
    }


@router.post("/config/smtp")
async def configure_smtp(
    data: SMTPConfig,
    current_user: dict = Depends(require_roles("admin")),
):
    """Configure le serveur SMTP pour l'envoi d'emails."""
    _diffusion_config["smtp"] = data.model_dump()
    _diffusion_config["smtp"]["status"] = "configured"
    _diffusion_config["smtp"]["configured_at"] = datetime.now(timezone.utc).isoformat()
    return {"status": "saved", "message": f"SMTP configuré : {data.host}:{data.port}"}


@router.post("/config/whatsapp")
async def configure_whatsapp(
    data: WhatsAppConfig,
    current_user: dict = Depends(require_roles("admin")),
):
    """Configure l'API WhatsApp Business."""
    _diffusion_config["whatsapp"] = data.model_dump()
    _diffusion_config["whatsapp"]["status"] = "configured"
    return {"status": "saved", "message": "WhatsApp Business configuré"}


@router.post("/config/sms")
async def configure_sms(
    data: SMSConfig,
    current_user: dict = Depends(require_roles("admin")),
):
    """Configure le provider SMS."""
    _diffusion_config["sms"] = data.model_dump()
    _diffusion_config["sms"]["status"] = "configured"
    return {"status": "saved", "message": f"SMS configuré ({data.provider})"}


# ══════════════════════════════════════════════════════════
# TEST SMTP
# ══════════════════════════════════════════════════════════

@router.post("/test-smtp")
async def test_smtp_connection(
    current_user: dict = Depends(require_roles("admin", "manager")),
):
    """Teste la connexion SMTP."""
    smtp = _diffusion_config.get("smtp")
    if not smtp:
        raise HTTPException(status_code=400, detail="SMTP non configuré")

    try:
        server = smtplib.SMTP(smtp["host"], smtp["port"], timeout=10)
        if smtp.get("use_tls", True):
            server.starttls()
        server.login(smtp["username"], smtp["password"])
        server.quit()
        _diffusion_config["smtp"]["status"] = "connected"
        _diffusion_config["smtp"]["last_tested"] = datetime.now(timezone.utc).isoformat()
        return {"success": True, "message": f"Connecté à {smtp['host']}:{smtp['port']}"}
    except smtplib.SMTPAuthenticationError:
        _diffusion_config["smtp"]["status"] = "error"
        return {"success": False, "message": "Erreur d'authentification — vérifiez le login/mot de passe"}
    except Exception as e:
        _diffusion_config["smtp"]["status"] = "error"
        return {"success": False, "message": f"Erreur : {str(e)}"}


@router.post("/send-test-email")
async def send_test_email(
    data: SendTestEmail,
    current_user: dict = Depends(require_roles("admin", "manager")),
):
    """Envoie un email de test."""
    smtp = _diffusion_config.get("smtp")
    if not smtp:
        raise HTTPException(status_code=400, detail="SMTP non configuré — allez dans Diffusion > Email")

    try:
        result = _send_email(
            to_email=data.to_email,
            subject=data.subject,
            html_content=f"<html><body><h2>{data.subject}</h2><p>{data.body}</p><hr><small>Envoyé depuis OS Orkestra</small></body></html>",
            text_content=data.body,
            smtp_config=smtp,
        )
        return result
    except Exception as e:
        return {"success": False, "message": str(e)}


# ══════════════════════════════════════════════════════════
# LANCER UNE CAMPAGNE (envoi réel)
# ══════════════════════════════════════════════════════════

@router.post("/launch-campaign")
async def launch_campaign(
    data: LaunchCampaignRequest,
    db=Depends(get_db),
    current_user: dict = Depends(require_roles("admin", "manager")),
):
    """Lance une campagne — envoie les emails aux contacts du segment."""
    smtp = _diffusion_config.get("smtp")
    if not smtp:
        raise HTTPException(status_code=400, detail="SMTP non configuré — allez dans Diffusion > Email")

    # Récupérer la campagne
    result = await db.execute(select(Campaign).where(Campaign.id == data.campaign_id))
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campagne non trouvée")

    # Vérifier le statut (comparaison insensible à la casse pour gérer UPPER en DB)
    status_str = campaign.status.value if hasattr(campaign.status, 'value') else str(campaign.status)
    if status_str.upper() not in ("DRAFT", "SCHEDULED"):
        raise HTTPException(status_code=400, detail=f"Campagne en statut {status_str} — ne peut pas être lancée")

    # Récupérer le template
    template_html = "<html><body><h2>{{subject}}</h2><p>Bonjour {{first_name}},</p><p>Ce message vous est envoyé par {{from_name}}.</p></body></html>"
    template_text = "Bonjour {{first_name}}, ce message vous est envoyé par {{from_name}}."
    if campaign.template_id:
        tpl_result = await db.execute(select(Template).where(Template.id == campaign.template_id))
        tpl = tpl_result.scalar_one_or_none()
        if tpl:
            template_html = tpl.html_content
            template_text = tpl.text_content or ""

    # Récupérer les contacts du segment (avec requêtes paramétrées)
    contacts = await _get_segment_contacts(db, campaign.segment_id)

    if not contacts:
        raise HTTPException(status_code=400, detail="Aucun contact dans le segment ciblé")

    # Mettre à jour le statut
    campaign.status = CampaignStatus.RUNNING
    campaign.sent_at = datetime.now(timezone.utc)
    await db.flush()

    # Envoyer les emails
    stats = {"sent": 0, "errors": 0, "total": len(contacts)}
    subject = campaign.subject or campaign.name
    from_name = campaign.from_name or smtp.get("from_name", "OS Orkestra")
    from_email = campaign.from_email or smtp.get("from_email", smtp["username"])

    for contact in contacts:
        contact_id = str(contact[0])
        email = contact[1]
        first_name = contact[2] or ""
        last_name = contact[3] or ""
        company = contact[4] or ""

        # Personnaliser le template
        html = template_html.replace("{{first_name}}", first_name)
        html = html.replace("{{last_name}}", last_name)
        html = html.replace("{{company}}", company)
        html = html.replace("{{email}}", email)
        html = html.replace("{{subject}}", subject)
        html = html.replace("{{from_name}}", from_name)

        txt = template_text.replace("{{first_name}}", first_name)
        txt = txt.replace("{{last_name}}", last_name)
        txt = txt.replace("{{company}}", company)

        # Envoyer
        send_result = _send_email(
            to_email=email,
            subject=subject,
            html_content=html,
            text_content=txt,
            smtp_config=smtp,
            from_email=from_email,
            from_name=from_name,
        )

        if send_result.get("success"):
            stats["sent"] += 1
            # Enregistrer les événements
            db.add(CampaignEvent(
                id=str(uuid.uuid4()),
                campaign_id=str(campaign.id),
                contact_id=contact_id,
                event_type=EventType.SENT,
                timestamp=datetime.now(timezone.utc),
            ))
            db.add(CampaignEvent(
                id=str(uuid.uuid4()),
                campaign_id=str(campaign.id),
                contact_id=contact_id,
                event_type=EventType.DELIVERED,
                timestamp=datetime.now(timezone.utc),
            ))
        else:
            stats["errors"] += 1
            logger.warning(f"Email failed for {email}: {send_result.get('message')}")

    # Mettre à jour les compteurs
    campaign.total_sent = stats["sent"]
    campaign.total_delivered = stats["sent"]
    campaign.total_bounced = stats["errors"]
    if stats["errors"] == 0:
        campaign.status = CampaignStatus.COMPLETED
        campaign.completed_at = datetime.now(timezone.utc)
    await db.flush()

    return {
        "status": "completed" if stats["errors"] == 0 else "partial",
        "campaign": campaign.name,
        "total_contacts": stats["total"],
        "sent": stats["sent"],
        "errors": stats["errors"],
        "message": f"{stats['sent']} emails envoyés sur {stats['total']} contacts",
    }


# ══════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════

async def _get_segment_contacts(db, segment_id) -> list:
    """Récupère les contacts d'un segment avec des requêtes sécurisées."""
    if not segment_id:
        # Pas de segment → tous les contacts
        result = await db.execute(text(
            "SELECT id, email, first_name, last_name, company FROM contacts"
        ))
        return result.fetchall()

    # Récupérer le segment et ses filtres
    seg_result = await db.execute(select(Segment).where(Segment.id == segment_id))
    seg = seg_result.scalar_one_or_none()
    if not seg:
        return []

    criteria = seg.filter_criteria
    if isinstance(criteria, str):
        try:
            criteria = json.loads(criteria)
        except Exception:
            criteria = {}

    if not criteria:
        result = await db.execute(text(
            "SELECT id, email, first_name, last_name, company FROM contacts"
        ))
        return result.fetchall()

    # Construire la requête avec des paramètres bindés (anti SQL injection)
    where_parts = []
    params = {}
    param_idx = 0
    for k, v in criteria.items():
        if k in ALLOWED_FILTER_COLUMNS:
            param_name = f"p{param_idx}"
            where_parts.append(f"{k} = :{param_name}")
            params[param_name] = str(v)
            param_idx += 1

    if not where_parts:
        result = await db.execute(text(
            "SELECT id, email, first_name, last_name, company FROM contacts"
        ))
        return result.fetchall()

    where_sql = " WHERE " + " AND ".join(where_parts)
    result = await db.execute(
        text(f"SELECT id, email, first_name, last_name, company FROM contacts{where_sql}"),
        params,
    )
    return result.fetchall()


def _send_email(
    to_email: str,
    subject: str,
    html_content: str,
    text_content: str = "",
    smtp_config: dict = None,
    from_email: str = None,
    from_name: str = None,
) -> dict:
    """Envoie un email via SMTP."""
    if not smtp_config:
        return {"success": False, "message": "SMTP non configuré"}

    sender_email = from_email or smtp_config.get("from_email", smtp_config["username"])
    sender_name = from_name or smtp_config.get("from_name", "OS Orkestra")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{sender_name} <{sender_email}>"
    msg["To"] = to_email

    if text_content:
        msg.attach(MIMEText(text_content, "plain", "utf-8"))
    msg.attach(MIMEText(html_content, "html", "utf-8"))

    try:
        server = smtplib.SMTP(smtp_config["host"], smtp_config["port"], timeout=15)
        if smtp_config.get("use_tls", True):
            server.starttls()
        server.login(smtp_config["username"], smtp_config["password"])
        server.sendmail(sender_email, [to_email], msg.as_string())
        server.quit()
        logger.info(f"Email sent to {to_email}")
        return {"success": True, "message": f"Email envoyé à {to_email}"}
    except smtplib.SMTPRecipientsRefused:
        return {"success": False, "message": f"Destinataire refusé : {to_email}"}
    except smtplib.SMTPAuthenticationError:
        return {"success": False, "message": "Erreur d'authentification SMTP"}
    except Exception as e:
        return {"success": False, "message": f"Erreur SMTP : {str(e)}"}

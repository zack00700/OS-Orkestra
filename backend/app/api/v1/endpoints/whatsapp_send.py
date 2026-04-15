"""
OS Orkestra — Envoi WhatsApp via Meta Cloud API.
Compatible Python 3.9+
"""
import re
import time
import logging
from collections import deque
from typing import Dict, Deque
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
import httpx
from app.core.database import get_db
from app.core.security import require_roles
from app.api.v1.endpoints.diffusion import _get_config as _get_diffusion_config

logger = logging.getLogger("orkestra.whatsapp")

router = APIRouter(prefix="/whatsapp", tags=["WhatsApp"])

META_API_URL = "https://graph.facebook.com/v21.0"

RATE_LIMIT_REQUESTS = 20
RATE_LIMIT_WINDOW_SEC = 60

_rate_buckets: Dict[str, Deque[float]] = {}


# ══════════════════════════════════════════════════════════
# SCHEMAS
# ══════════════════════════════════════════════════════════

class WhatsAppTestRequest(BaseModel):
    to_phone: str = Field(min_length=8, max_length=20)


class WhatsAppTextRequest(BaseModel):
    to_phone: str = Field(min_length=8, max_length=20)
    message: str = Field(min_length=1, max_length=4000)


# ══════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════

_PHONE_RE = re.compile(r"^\d{8,15}$")


def _clean_phone(phone: str) -> str:
    """Normalise en digits-only sans +. Lève HTTPException si invalide."""
    cleaned = re.sub(r"[\s\-().+]", "", phone or "")
    if not _PHONE_RE.match(cleaned):
        raise HTTPException(status_code=400, detail=f"Numéro invalide (attendu 8-15 chiffres): {phone!r}")
    return cleaned


def _mask_phone(phone: str) -> str:
    """Masque les 4 derniers chiffres pour les logs."""
    if not phone or len(phone) < 5:
        return "***"
    return phone[:-4] + "****"


def _check_rate_limit(user_key: str):
    now = time.time()
    bucket = _rate_buckets.setdefault(user_key, deque())
    while bucket and now - bucket[0] > RATE_LIMIT_WINDOW_SEC:
        bucket.popleft()
    if len(bucket) >= RATE_LIMIT_REQUESTS:
        raise HTTPException(
            status_code=429,
            detail=f"Trop de requêtes WhatsApp. Max {RATE_LIMIT_REQUESTS} / {RATE_LIMIT_WINDOW_SEC}s.",
        )
    bucket.append(now)


async def _load_config(db) -> dict:
    config = await _get_diffusion_config(db, "whatsapp_config")
    if not config or not config.get("api_token") or not config.get("phone_number_id"):
        raise HTTPException(status_code=400, detail="WhatsApp non configuré — allez dans Diffusion > WhatsApp")
    return config


def _parse_meta_error(response: httpx.Response) -> dict:
    """Parse la réponse d'erreur Meta en se protégeant du non-JSON."""
    try:
        body = response.json()
        err = body.get("error", {}) if isinstance(body, dict) else {}
        msg = err.get("message") or "Erreur inconnue"
        code = err.get("code", "")
        # Codes Meta fréquents
        if code == 131047:
            msg += " (fenêtre 24h expirée — utilisez un template via /send-test)"
        elif code == 131030:
            msg += " (numéro non autorisé en mode sandbox — ajoutez-le dans Meta Business)"
        return {"message": msg, "code": code}
    except Exception:
        return {"message": (response.text[:200] or f"HTTP {response.status_code}"), "code": ""}


async def _post_meta(config: dict, payload: dict) -> dict:
    """POST vers Meta Cloud API — retourne {success, message, message_id?} ou lève 502."""
    phone_number_id = config["phone_number_id"]
    access_token = config["api_token"]

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                f"{META_API_URL}/{phone_number_id}/messages",
                headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
                json=payload,
            )
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Timeout — Meta API ne répond pas")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Erreur réseau Meta : {str(e)}")

    if response.status_code in (200, 201):
        try:
            result = response.json()
            msg_id = (result.get("messages") or [{}])[0].get("id", "")
        except Exception:
            msg_id = ""
        return {"success": True, "message_id": msg_id}

    err = _parse_meta_error(response)
    logger.warning("WhatsApp API error: %s (code %s)", err["message"], err["code"])
    raise HTTPException(status_code=502, detail=f"Erreur WhatsApp : {err['message']}")


# ══════════════════════════════════════════════════════════
# ENDPOINTS
# ══════════════════════════════════════════════════════════

@router.post("/send-test")
async def send_test_whatsapp(
    data: WhatsAppTestRequest,
    db=Depends(get_db),
    current_user: dict = Depends(require_roles("admin", "manager")),
):
    """Envoie le template 'hello_world' (obligatoire pour initier une conversation)."""
    user_id = str(current_user.get("id") or current_user.get("email") or "anon")
    _check_rate_limit(user_id)

    config = await _load_config(db)
    to_phone = _clean_phone(data.to_phone)

    payload = {
        "messaging_product": "whatsapp",
        "to": to_phone,
        "type": "template",
        "template": {"name": "hello_world", "language": {"code": "en_US"}},
    }

    result = await _post_meta(config, payload)
    logger.info("WhatsApp template sent to %s, id=%s", _mask_phone(to_phone), result.get("message_id", ""))
    return {
        "success": True,
        "message": f"Message WhatsApp (template hello_world) envoyé à +{to_phone}",
        "message_id": result.get("message_id", ""),
    }


@router.post("/send-text")
async def send_text_whatsapp(
    data: WhatsAppTextRequest,
    db=Depends(get_db),
    current_user: dict = Depends(require_roles("admin", "manager")),
):
    """Envoie un message texte libre (uniquement dans la fenêtre 24h après réponse du contact)."""
    user_id = str(current_user.get("id") or current_user.get("email") or "anon")
    _check_rate_limit(user_id)

    config = await _load_config(db)
    to_phone = _clean_phone(data.to_phone)

    payload = {
        "messaging_product": "whatsapp",
        "to": to_phone,
        "type": "text",
        "text": {"body": data.message},
    }

    result = await _post_meta(config, payload)
    logger.info("WhatsApp text sent to %s, id=%s", _mask_phone(to_phone), result.get("message_id", ""))
    return {
        "success": True,
        "message": f"Message envoyé à +{to_phone}",
        "message_id": result.get("message_id", ""),
    }

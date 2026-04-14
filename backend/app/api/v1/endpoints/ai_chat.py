"""
OS Orkestra — Assistant IA
Proxy backend pour l'API Anthropic (évite CORS + protège la clé API).
Avec prompt caching, rate limit par user et validation des inputs.
Compatible Python 3.9+
"""
import os
import time
import logging
from collections import deque
from typing import List, Deque, Dict, Literal
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
import httpx
from app.core.security import get_current_user

logger = logging.getLogger("orkestra.ai")

router = APIRouter(prefix="/ai", tags=["AI Assistant"])

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
# Modèle par défaut : Haiku 4.5 (rapide + bon marché pour un chatbot support)
AI_MODEL = os.environ.get("AI_MODEL", "claude-haiku-4-5-20251001")

MAX_MESSAGES_HISTORY = 20
MAX_MESSAGE_CHARS = 8000
RATE_LIMIT_REQUESTS = 30
RATE_LIMIT_WINDOW_SEC = 60

SYSTEM_PROMPT = """Tu es l'assistant IA intégré à OS Orkestra, un outil de marketing automation développé par OpenSID.
Tu aides l'utilisateur à effectuer des actions dans l'outil et à comprendre ses données.

Fonctionnalités de l'outil :
- Contacts : import depuis CRM ou CSV, scoring automatique, lead stages (awareness → interest → consideration → purchase)
- Campagnes : création, envoi email via SMTP, tracking (ouvertures, clics)
- Segments : dynamiques basés sur des filtres (pays, ville, score, source, statut)
- Templates : éditeur HTML avec variables personnalisées ({{first_name}}, {{company}}, etc.)
- Diffusion : config SMTP, WhatsApp, SMS
- Analytics : taux d'ouverture, taux de clic, ranking campagnes
- Import CSV : upload + mapping + import
- Write-back CRM : sync bidirectionnelle vers le CRM source

Quand l'utilisateur demande une action :
1. Si c'est une question sur les données → explique comment trouver l'info dans l'interface
2. Si c'est une action complexe → donne les étapes précises à suivre
3. Si c'est une demande de création → guide l'utilisateur vers la bonne page

Réponds toujours en français, de manière concise et professionnelle.
Utilise des listes courtes quand c'est utile.
Ne mentionne jamais que tu es Claude ou Anthropic — tu es l'assistant IA d'Orkestra par OpenSID."""


# ══════════════════════════════════════════════════════════
# RATE LIMIT (en mémoire — par user)
# ══════════════════════════════════════════════════════════

_rate_buckets: Dict[str, Deque[float]] = {}


def _check_rate_limit(user_key: str):
    now = time.time()
    bucket = _rate_buckets.setdefault(user_key, deque())
    # Nettoie les timestamps hors fenêtre
    while bucket and now - bucket[0] > RATE_LIMIT_WINDOW_SEC:
        bucket.popleft()
    if len(bucket) >= RATE_LIMIT_REQUESTS:
        raise HTTPException(
            status_code=429,
            detail=f"Trop de requêtes. Max {RATE_LIMIT_REQUESTS} / {RATE_LIMIT_WINDOW_SEC}s.",
        )
    bucket.append(now)


# ══════════════════════════════════════════════════════════
# SCHEMAS
# ══════════════════════════════════════════════════════════

class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=MAX_MESSAGE_CHARS)


class ChatRequest(BaseModel):
    messages: List[ChatMessage] = Field(min_length=1)


# ══════════════════════════════════════════════════════════
# ENDPOINT
# ══════════════════════════════════════════════════════════

@router.post("/chat")
async def ai_chat(
    data: ChatRequest,
    current_user: dict = Depends(get_current_user),
):
    """Envoie un message à l'assistant IA et retourne la réponse."""
    user_id = str(current_user.get("id") or current_user.get("email") or "anon")
    _check_rate_limit(user_id)

    if not ANTHROPIC_API_KEY:
        raise HTTPException(status_code=500, detail="Clé API Anthropic non configurée (ANTHROPIC_API_KEY)")

    # Limite l'historique — garde les N derniers messages
    truncated = data.messages[-MAX_MESSAGES_HISTORY:]
    api_messages = [{"role": m.role, "content": m.content} for m in truncated]

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "anthropic-beta": "prompt-caching-2024-07-31",
                },
                json={
                    "model": AI_MODEL,
                    "max_tokens": 1024,
                    # System prompt avec cache_control → réduit drastiquement les tokens facturés
                    "system": [
                        {"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}},
                    ],
                    "messages": api_messages,
                },
            )

        if response.status_code != 200:
            try:
                error_body = response.json()
                err_msg = error_body.get("error", {}).get("message", "Erreur inconnue")
            except Exception:
                err_msg = response.text[:200] or f"HTTP {response.status_code}"
            logger.warning("Anthropic API error: %s", err_msg)
            raise HTTPException(status_code=502, detail=f"Erreur API IA : {err_msg}")

        result = response.json()
        reply = ""
        for block in result.get("content", []):
            if block.get("type") == "text":
                reply += block.get("text", "")

        return {"reply": reply, "model": AI_MODEL}

    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="L'IA met trop de temps à répondre. Réessayez.")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("AI chat error: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Erreur : {str(e)}")

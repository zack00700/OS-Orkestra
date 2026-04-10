"""
OS HubLine — Connecteur WhatsApp Business API
Envoi de messages marketing via WhatsApp Cloud API.
"""
import httpx
import logging
from typing import Optional
from app.core.config import get_settings

logger = logging.getLogger("hubline.integrations.whatsapp")
settings = get_settings()


class WhatsAppConnector:
    """Connecteur WhatsApp Cloud API (Meta Business)."""

    def __init__(self):
        self.api_url = settings.WHATSAPP_API_URL or "https://graph.facebook.com/v18.0"
        self.token = settings.WHATSAPP_API_TOKEN
        self.phone_number_id = settings.WHATSAPP_PHONE_NUMBER_ID

    async def _request(self, method: str, endpoint: str, **kwargs) -> dict:
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
        url = f"{self.api_url}/{endpoint}"

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.request(method, url, headers=headers, **kwargs)
            response.raise_for_status()
            return response.json()

    async def send_template_message(
        self,
        to_phone: str,
        template_name: str,
        language_code: str = "fr",
        components: Optional[list[dict]] = None,
    ) -> dict:
        """Envoyer un message template WhatsApp."""
        payload = {
            "messaging_product": "whatsapp",
            "to": to_phone,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language_code},
            },
        }
        if components:
            payload["template"]["components"] = components

        return await self._request(
            "POST",
            f"{self.phone_number_id}/messages",
            json=payload,
        )

    async def send_text_message(self, to_phone: str, text: str) -> dict:
        """Envoyer un message texte simple."""
        payload = {
            "messaging_product": "whatsapp",
            "to": to_phone,
            "type": "text",
            "text": {"body": text},
        }
        return await self._request(
            "POST",
            f"{self.phone_number_id}/messages",
            json=payload,
        )

    async def get_templates(self) -> list[dict]:
        """Lister les templates WhatsApp disponibles."""
        # Le business_id doit être configuré
        data = await self._request("GET", f"{self.phone_number_id}/message_templates")
        return data.get("data", [])

    async def test_connection(self) -> dict:
        try:
            data = await self._request("GET", f"{self.phone_number_id}")
            return {"status": "connected", "phone": data.get("display_phone_number")}
        except Exception as e:
            logger.error(f"WhatsApp connection test failed: {e}")
            return {"status": "error", "message": str(e)}

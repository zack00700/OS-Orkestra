"""
OS Orkestra — Service d'envoi d'emails (SMTP)
Gère l'envoi réel, la personnalisation et le tracking.
Compatible Python 3.9+
"""
import smtplib
import logging
import uuid
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from app.core.config import get_settings

logger = logging.getLogger("orkestra.email")
settings = get_settings()

TRACKING_BASE_URL = "http://localhost:8000/api/v1"


class EmailService:
    """Service d'envoi d'emails via SMTP."""

    def __init__(self):
        self.host = settings.SMTP_HOST
        self.port = settings.SMTP_PORT
        self.user = settings.SMTP_USER
        self.password = settings.SMTP_PASSWORD
        self.use_tls = settings.SMTP_USE_TLS
        self.from_email = settings.SMTP_FROM_EMAIL
        self.from_name = settings.SMTP_FROM_NAME

    def _render_template(self, html: str, variables: Dict[str, Any]) -> str:
        """Remplace les {{variable}} dans le template."""
        rendered = html
        for key, value in variables.items():
            rendered = rendered.replace("{{" + key + "}}", str(value or ""))
        return rendered

    def _add_tracking_pixel(self, html: str, campaign_id: str, contact_id: str) -> str:
        """Ajoute un pixel de tracking invisible pour détecter les ouvertures."""
        pixel_url = f"{TRACKING_BASE_URL}/tracking/open/{campaign_id}/{contact_id}"
        pixel = f'<img src="{pixel_url}" width="1" height="1" style="display:none" alt="" />'
        if "</body>" in html:
            return html.replace("</body>", f"{pixel}</body>")
        return html + pixel

    def _wrap_links(self, html: str, campaign_id: str, contact_id: str) -> str:
        """Remplace les liens pour tracker les clics."""
        import re
        def replace_link(match):
            original_url = match.group(1)
            if "tracking" in original_url:
                return match.group(0)
            track_url = f"{TRACKING_BASE_URL}/tracking/click/{campaign_id}/{contact_id}?url={original_url}"
            return f'href="{track_url}"'
        return re.sub(r'href="(https?://[^"]+)"', replace_link, html)

    def send_single(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        campaign_id: Optional[str] = None,
        contact_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Envoie un seul email."""
        sender_email = from_email or self.from_email
        sender_name = from_name or self.from_name

        # Ajouter tracking si campaign
        if campaign_id and contact_id:
            html_content = self._add_tracking_pixel(html_content, campaign_id, contact_id)
            html_content = self._wrap_links(html_content, campaign_id, contact_id)

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{sender_name} <{sender_email}>"
        msg["To"] = to_email
        msg["X-Campaign-ID"] = campaign_id or ""
        msg["X-Contact-ID"] = contact_id or ""

        if text_content:
            msg.attach(MIMEText(text_content, "plain", "utf-8"))
        msg.attach(MIMEText(html_content, "html", "utf-8"))

        try:
            if self.use_tls:
                server = smtplib.SMTP(self.host, self.port, timeout=30)
                server.starttls()
            else:
                server = smtplib.SMTP(self.host, self.port, timeout=30)

            if self.user and self.password:
                server.login(self.user, self.password)

            server.sendmail(sender_email, [to_email], msg.as_string())
            server.quit()

            logger.info(f"Email sent to {to_email} (campaign={campaign_id})")
            return {"status": "sent", "to": to_email}

        except smtplib.SMTPRecipientsRefused:
            logger.warning(f"Recipient refused: {to_email}")
            return {"status": "bounced", "to": to_email, "error": "recipient_refused"}
        except smtplib.SMTPAuthenticationError:
            logger.error("SMTP authentication failed")
            return {"status": "error", "to": to_email, "error": "auth_failed"}
        except Exception as e:
            logger.error(f"SMTP error for {to_email}: {e}")
            return {"status": "error", "to": to_email, "error": str(e)}

    def send_batch(
        self,
        recipients: List[Dict[str, Any]],
        subject: str,
        html_template: str,
        text_template: Optional[str] = None,
        campaign_id: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Envoie un batch d'emails avec personnalisation."""
        results = {"sent": 0, "bounced": 0, "errors": 0, "details": []}

        for recipient in recipients:
            variables = {
                "first_name": recipient.get("first_name", ""),
                "last_name": recipient.get("last_name", ""),
                "email": recipient.get("email", ""),
                "company": recipient.get("company", ""),
                "job_title": recipient.get("job_title", ""),
            }

            rendered_html = self._render_template(html_template, variables)
            rendered_subject = self._render_template(subject, variables)
            rendered_text = self._render_template(text_template, variables) if text_template else None

            result = self.send_single(
                to_email=recipient["email"],
                subject=rendered_subject,
                html_content=rendered_html,
                text_content=rendered_text,
                from_email=from_email,
                from_name=from_name,
                campaign_id=campaign_id,
                contact_id=str(recipient.get("id", "")),
            )

            if result["status"] == "sent":
                results["sent"] += 1
            elif result["status"] == "bounced":
                results["bounced"] += 1
            else:
                results["errors"] += 1
            results["details"].append(result)

        return results

    def test_connection(self) -> Dict[str, Any]:
        """Teste la connexion SMTP."""
        try:
            server = smtplib.SMTP(self.host, self.port, timeout=10)
            if self.use_tls:
                server.starttls()
            if self.user and self.password:
                server.login(self.user, self.password)
            server.quit()
            return {"status": "connected", "host": self.host, "port": self.port}
        except Exception as e:
            return {"status": "error", "host": self.host, "error": str(e)}

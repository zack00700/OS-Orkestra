"""
OS HubLine — Tâches Celery (traitements asynchrones)
"""
import logging
from celery import Celery
from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger("hubline.tasks")

celery_app = Celery(
    "hubline",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,  # 10 min max par tâche
    task_soft_time_limit=540,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=100,
)


# ── Sync CRM ────────────────────────────────────────────

@celery_app.task(name="hubline.sync_dynamics_contacts", bind=True, max_retries=3)
def sync_dynamics_contacts(self, modified_since: str = None):
    """Synchroniser les contacts depuis Dynamics 365."""
    import asyncio
    from app.integrations.crm.dynamics import DynamicsConnector

    async def _sync():
        connector = DynamicsConnector()
        contacts = await connector.fetch_contacts(modified_since=modified_since)
        logger.info(f"Fetched {len(contacts)} contacts from Dynamics")
        # TODO: upsert dans la DB via ContactService
        return {"fetched": len(contacts)}

    try:
        return asyncio.run(_sync())
    except Exception as exc:
        logger.error(f"Dynamics sync failed: {exc}")
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))


@celery_app.task(name="hubline.sync_azure_ad_users", bind=True, max_retries=3)
def sync_azure_ad_users(self, department: str = None, country: str = None):
    """Synchroniser les utilisateurs depuis Azure AD."""
    import asyncio
    from app.integrations.azure_ad.connector import AzureADConnector

    async def _sync():
        connector = AzureADConnector()
        users = await connector.fetch_users(department=department, country=country)
        logger.info(f"Fetched {len(users)} users from Azure AD")
        return {"fetched": len(users)}

    try:
        return asyncio.run(_sync())
    except Exception as exc:
        logger.error(f"Azure AD sync failed: {exc}")
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))


# ── Campaign Sending ────────────────────────────────────

@celery_app.task(name="hubline.send_campaign_emails", bind=True, max_retries=2)
def send_campaign_emails(self, campaign_id: str, batch_size: int = 100):
    """Envoyer les emails d'une campagne par lots."""
    logger.info(f"Sending campaign {campaign_id} in batches of {batch_size}")
    # TODO: Implémenter l'envoi SMTP par lot
    # 1. Charger la campagne et son segment
    # 2. Récupérer les contacts du segment
    # 3. Rendre le template avec personnalisation
    # 4. Envoyer par batch via SMTP
    # 5. Enregistrer les événements SENT/BOUNCED
    return {"campaign_id": campaign_id, "status": "completed"}


@celery_app.task(name="hubline.send_whatsapp_campaign", bind=True, max_retries=2)
def send_whatsapp_campaign(self, campaign_id: str):
    """Envoyer une campagne WhatsApp."""
    import asyncio
    from app.integrations.whatsapp.connector import WhatsAppConnector

    async def _send():
        connector = WhatsAppConnector()
        # TODO: charger contacts et envoyer
        return {"campaign_id": campaign_id, "status": "completed"}

    try:
        return asyncio.run(_send())
    except Exception as exc:
        logger.error(f"WhatsApp campaign failed: {exc}")
        raise self.retry(exc=exc, countdown=120)


# ── Data Quality ────────────────────────────────────────

@celery_app.task(name="hubline.run_data_quality_check")
def run_data_quality_check():
    """Exécuter un audit de qualité des données contacts."""
    logger.info("Running data quality check...")
    # TODO: Implémenter
    # 1. Vérifier les emails invalides (regex + MX check)
    # 2. Détecter les doublons (fuzzy matching)
    # 3. Calculer le taux de complétion des champs clés
    # 4. Identifier les contacts obsolètes (>12 mois sans interaction)
    # 5. Générer un DataQualityReport
    return {"status": "completed"}


# ── Scheduled Tasks (beat) ──────────────────────────────

celery_app.conf.beat_schedule = {
    "sync-dynamics-every-hour": {
        "task": "hubline.sync_dynamics_contacts",
        "schedule": 3600.0,
    },
    "sync-azure-ad-every-6h": {
        "task": "hubline.sync_azure_ad_users",
        "schedule": 21600.0,
    },
    "data-quality-daily": {
        "task": "hubline.run_data_quality_check",
        "schedule": 86400.0,
    },
}

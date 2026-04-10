"""
OS HubLine — API Endpoints : Intégrations & Synchronisation
"""
from fastapi import APIRouter, Depends
from app.core.security import require_roles
from app.integrations import DynamicsConnector, AzureADConnector, WhatsAppConnector

router = APIRouter(prefix="/integrations", tags=["Intégrations"])


@router.get("/test/dynamics")
async def test_dynamics(current_user: dict = Depends(require_roles("admin"))):
    """Tester la connexion à Dynamics 365."""
    connector = DynamicsConnector()
    return await connector.test_connection()


@router.get("/test/azure-ad")
async def test_azure_ad(current_user: dict = Depends(require_roles("admin"))):
    """Tester la connexion à Azure AD."""
    connector = AzureADConnector()
    return await connector.test_connection()


@router.get("/test/whatsapp")
async def test_whatsapp(current_user: dict = Depends(require_roles("admin"))):
    """Tester la connexion WhatsApp Business."""
    connector = WhatsAppConnector()
    return await connector.test_connection()


@router.post("/sync/dynamics")
async def trigger_dynamics_sync(current_user: dict = Depends(require_roles("admin", "manager"))):
    """Déclencher une synchronisation Dynamics manuelle."""
    from app.tasks.celery_tasks import sync_dynamics_contacts
    task = sync_dynamics_contacts.delay()
    return {"task_id": task.id, "status": "queued"}


@router.post("/sync/azure-ad")
async def trigger_azure_ad_sync(current_user: dict = Depends(require_roles("admin", "manager"))):
    """Déclencher une synchronisation Azure AD manuelle."""
    from app.tasks.celery_tasks import sync_azure_ad_users
    task = sync_azure_ad_users.delay()
    return {"task_id": task.id, "status": "queued"}


@router.get("/azure-ad/departments")
async def get_departments(current_user: dict = Depends(require_roles("admin", "manager"))):
    """Lister les départements Azure AD."""
    connector = AzureADConnector()
    return await connector.fetch_departments()


@router.get("/azure-ad/groups")
async def get_groups(current_user: dict = Depends(require_roles("admin", "manager"))):
    """Lister les groupes Azure AD."""
    connector = AzureADConnector()
    return await connector.fetch_groups()

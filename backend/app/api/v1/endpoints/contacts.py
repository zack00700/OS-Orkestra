"""
OS HubLine — API Endpoints : Contacts
"""
from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import get_current_user, require_roles
from app.services import ContactService
from app.schemas import (
    ContactCreate, ContactResponse, ContactUpdate,
    ContactListResponse, MessageResponse,
)
from app.models import ContactStatus, ContactSource, LeadStage

router = APIRouter(prefix="/contacts", tags=["Contacts"])


@router.get("/", response_model=ContactListResponse)
async def list_contacts(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    search: Optional[str] = None,
    status: Optional[ContactStatus] = None,
    source: Optional[ContactSource] = None,
    is_internal: Optional[bool] = None,
    lead_stage: Optional[LeadStage] = None,
    segment: Optional[str] = None,
    country: Optional[str] = None,
    business_unit: Optional[str] = None,
    sort_by: str = Query("created_at", regex="^(created_at|email|last_name|lead_score|company)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Liste paginée des contacts avec filtres avancés."""
    service = ContactService(db)
    return await service.list_contacts(
        page=page, page_size=page_size, search=search,
        status=status, source=source, is_internal=is_internal,
        lead_stage=lead_stage, segment=segment, country=country,
        business_unit=business_unit, sort_by=sort_by, sort_order=sort_order,
    )


@router.get("/stats")
async def get_contact_stats(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Statistiques globales sur les contacts."""
    service = ContactService(db)
    return await service.get_stats()


@router.get("/{contact_id}", response_model=ContactResponse)
async def get_contact(
    contact_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Détail d'un contact."""
    service = ContactService(db)
    contact = await service.get_by_id(contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact non trouvé")
    return contact


@router.post("/", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
async def create_contact(
    data: ContactCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_roles("admin", "manager", "editor")),
):
    """Créer un nouveau contact."""
    service = ContactService(db)
    existing = await service.get_by_email(data.email, data.source)
    if existing:
        raise HTTPException(status_code=409, detail="Un contact avec cet email existe déjà pour cette source")
    return await service.create(data)


@router.patch("/{contact_id}", response_model=ContactResponse)
async def update_contact(
    contact_id: UUID,
    data: ContactUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_roles("admin", "manager", "editor")),
):
    """Mettre à jour un contact."""
    service = ContactService(db)
    contact = await service.update(contact_id, data)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact non trouvé")
    return contact


@router.delete("/{contact_id}", response_model=MessageResponse)
async def delete_contact(
    contact_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_roles("admin")),
):
    """Supprimer un contact (RGPD - droit à l'oubli)."""
    service = ContactService(db)
    success = await service.delete(contact_id)
    if not success:
        raise HTTPException(status_code=404, detail="Contact non trouvé")
    return MessageResponse(message="Contact supprimé avec succès")


@router.post("/bulk-import", response_model=dict)
async def bulk_import_contacts(
    contacts: list[ContactCreate],
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_roles("admin", "manager")),
):
    """Import en masse de contacts."""
    service = ContactService(db)
    return await service.bulk_import(contacts)


@router.post("/{contact_id}/score", response_model=ContactResponse)
async def update_lead_score(
    contact_id: UUID,
    score_delta: int = Query(..., ge=-100, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_roles("admin", "manager")),
):
    """Modifier le score de lead d'un contact."""
    service = ContactService(db)
    contact = await service.update_lead_score(contact_id, score_delta)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact non trouvé")
    return contact

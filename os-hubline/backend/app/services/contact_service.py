"""
OS HubLine — Service Contacts (CRUD + logique métier)

Utilise les query helpers portables pour être compatible avec
tous les moteurs SQL (PostgreSQL, SQL Server, MySQL, SQLite, Oracle).
"""
import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Contact, ContactStatus, ContactSource, LeadStage
from app.schemas import ContactCreate, ContactUpdate, ContactListResponse, ContactResponse
from app.core.query_helpers import case_insensitive_like, array_overlap


class ContactService:
    """Service de gestion des contacts."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: ContactCreate) -> Contact:
        """Créer un nouveau contact."""
        contact = Contact(
            **data.model_dump(exclude_none=True),
        )
        self.db.add(contact)
        await self.db.flush()
        await self.db.refresh(contact)
        return contact

    async def get_by_id(self, contact_id: uuid.UUID) -> Optional[Contact]:
        """Récupérer un contact par son ID."""
        result = await self.db.execute(
            select(Contact).where(Contact.id == contact_id)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str, source: Optional[ContactSource] = None) -> Optional[Contact]:
        """Récupérer un contact par email (et source optionnelle)."""
        query = select(Contact).where(Contact.email == email)
        if source:
            query = query.where(Contact.source == source)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list(
        self,
        page: int = 1,
        page_size: int = 50,
        search: Optional[str] = None,
        status: Optional[ContactStatus] = None,
        source: Optional[ContactSource] = None,
        is_internal: Optional[bool] = None,
        lead_stage: Optional[LeadStage] = None,
        segment: Optional[str] = None,
        country: Optional[str] = None,
        business_unit: Optional[str] = None,
        tags: Optional[list[str]] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> ContactListResponse:
        """Liste paginée et filtrable des contacts."""
        query = select(Contact)
        count_query = select(func.count(Contact.id))

        # Filtres
        filters = []
        if search:
            # Portable : ILIKE (PG) / LOWER+LIKE (SQLite) / LIKE (SQL Server, MySQL)
            filters.append(
                or_(
                    case_insensitive_like(Contact.email, search),
                    case_insensitive_like(Contact.first_name, search),
                    case_insensitive_like(Contact.last_name, search),
                    case_insensitive_like(Contact.company, search),
                )
            )
        if status:
            filters.append(Contact.status == status)
        if source:
            filters.append(Contact.source == source)
        if is_internal is not None:
            filters.append(Contact.is_internal == is_internal)
        if lead_stage:
            filters.append(Contact.lead_stage == lead_stage)
        if segment:
            filters.append(Contact.segment == segment)
        if country:
            filters.append(Contact.country == country)
        if business_unit:
            filters.append(Contact.business_unit == business_unit)
        if tags:
            # Portable : @> ARRAY (PG) / JSON_CONTAINS (MySQL) / LIKE JSON (SQL Server, SQLite)
            filters.append(array_overlap(Contact.tags, tags))

        if filters:
            combined = and_(*filters)
            query = query.where(combined)
            count_query = count_query.where(combined)

        # Tri
        sort_col = getattr(Contact, sort_by, Contact.created_at)
        if sort_order == "desc":
            query = query.order_by(sort_col.desc())
        else:
            query = query.order_by(sort_col.asc())

        # Pagination — SQLAlchemy traduit .limit().offset() selon le dialecte :
        # PG/MySQL/SQLite → LIMIT n OFFSET m
        # SQL Server      → OFFSET m ROWS FETCH NEXT n ROWS ONLY
        # Oracle           → OFFSET m ROWS FETCH NEXT n ROWS ONLY (12c+)
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0
        total_pages = max(1, (total + page_size - 1) // page_size)

        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        contacts = result.scalars().all()

        return ContactListResponse(
            items=[ContactResponse.model_validate(c) for c in contacts],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def update(self, contact_id: uuid.UUID, data: ContactUpdate) -> Optional[Contact]:
        """Mettre à jour un contact."""
        contact = await self.get_by_id(contact_id)
        if not contact:
            return None

        update_data = data.model_dump(exclude_none=True)
        for field, value in update_data.items():
            setattr(contact, field, value)

        contact.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self.db.refresh(contact)
        return contact

    async def delete(self, contact_id: uuid.UUID) -> bool:
        """Supprimer un contact."""
        contact = await self.get_by_id(contact_id)
        if not contact:
            return False
        await self.db.delete(contact)
        await self.db.flush()
        return True

    async def bulk_import(self, contacts_data: list[ContactCreate]) -> dict:
        """Import en masse de contacts avec déduplication."""
        stats = {"created": 0, "updated": 0, "skipped": 0, "errors": []}

        for idx, data in enumerate(contacts_data):
            try:
                existing = await self.get_by_email(data.email, data.source)
                if existing:
                    # Mise à jour si existant
                    update = ContactUpdate(**data.model_dump(exclude={"email", "source"}, exclude_none=True))
                    await self.update(existing.id, update)
                    stats["updated"] += 1
                else:
                    await self.create(data)
                    stats["created"] += 1
            except Exception as e:
                stats["errors"].append({"row": idx, "email": data.email, "error": str(e)})
                stats["skipped"] += 1

        return stats

    async def update_lead_score(self, contact_id: uuid.UUID, score_delta: int) -> Optional[Contact]:
        """Mettre à jour le score de lead."""
        contact = await self.get_by_id(contact_id)
        if not contact:
            return None

        contact.lead_score = max(0, contact.lead_score + score_delta)

        # Mise à jour automatique du stage selon le score
        if contact.lead_score >= 80:
            contact.lead_stage = LeadStage.PURCHASE
        elif contact.lead_score >= 50:
            contact.lead_stage = LeadStage.CONSIDERATION
        elif contact.lead_score >= 20:
            contact.lead_stage = LeadStage.INTEREST
        else:
            contact.lead_stage = LeadStage.AWARENESS

        await self.db.flush()
        await self.db.refresh(contact)
        return contact

    async def get_stats(self) -> dict:
        """Statistiques globales sur les contacts."""
        total = await self.db.execute(select(func.count(Contact.id)))
        active = await self.db.execute(
            select(func.count(Contact.id)).where(Contact.status == ContactStatus.ACTIVE)
        )
        internal = await self.db.execute(
            select(func.count(Contact.id)).where(Contact.is_internal == True)
        )
        by_source = await self.db.execute(
            select(Contact.source, func.count(Contact.id))
            .group_by(Contact.source)
        )
        by_stage = await self.db.execute(
            select(Contact.lead_stage, func.count(Contact.id))
            .group_by(Contact.lead_stage)
        )

        return {
            "total": total.scalar() or 0,
            "active": active.scalar() or 0,
            "internal": internal.scalar() or 0,
            "by_source": {str(row[0]): row[1] for row in by_source.all()},
            "by_stage": {str(row[0]): row[1] for row in by_stage.all()},
        }

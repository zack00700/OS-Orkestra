"""
OS Orkestra — Service Contacts (CRUD + logique métier)
Compatible Python 3.9+ / pymssql sync + async
"""
import uuid
import json
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import select, func, or_, and_, text, literal_column
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Contact, ContactStatus, ContactSource, LeadStage
from app.schemas import ContactCreate, ContactUpdate, ContactListResponse, ContactResponse
from app.core.query_helpers import case_insensitive_like, array_overlap


def _fix_contact(contact):
    """Parse les champs JSON stockés comme strings (tags, custom_fields) pour Pydantic."""
    if hasattr(contact, 'tags') and isinstance(contact.tags, str):
        try:
            contact.tags = json.loads(contact.tags)
        except (json.JSONDecodeError, TypeError):
            contact.tags = []
    if hasattr(contact, 'custom_fields') and isinstance(contact.custom_fields, str):
        try:
            contact.custom_fields = json.loads(contact.custom_fields)
        except (json.JSONDecodeError, TypeError):
            contact.custom_fields = {}
    return contact


class ContactService:
    """Service de gestion des contacts."""

    def __init__(self, db):
        self.db = db

    async def create(self, data: ContactCreate) -> Contact:
        contact = Contact(
            **data.model_dump(exclude_none=True),
        )
        self.db.add(contact)
        await self.db.flush()
        await self.db.refresh(contact)
        return contact

    async def get_by_id(self, contact_id: uuid.UUID) -> Optional[Contact]:
        result = await self.db.execute(
            select(Contact).where(Contact.id == contact_id)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str, source: Optional[ContactSource] = None) -> Optional[Contact]:
        query = select(Contact).where(Contact.email == email)
        if source:
            query = query.where(Contact.source == source)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_contacts(
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
        tags: Optional[List[str]] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> ContactListResponse:
        """Liste paginée et filtrable des contacts."""
        query = select(Contact)

        filters = []
        if search:
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

        if filters:
            combined = and_(*filters)
            query = query.where(combined)

        sort_col = getattr(Contact, sort_by, Contact.created_at)
        if sort_order == "desc":
            query = query.order_by(sort_col.desc())
        else:
            query = query.order_by(sort_col.asc())

        # Count total using raw SQL to avoid pymssql/GUID issues
        count_result = await self.db.execute(text("SELECT COUNT(*) FROM contacts"))
        row = count_result.fetchone()
        total = row[0] if row else 0

        total_pages = max(1, (total + page_size - 1) // page_size)

        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        contacts = result.scalars().all()

        return ContactListResponse(
            items=[ContactResponse.model_validate(_fix_contact(c)) for c in contacts],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def update(self, contact_id: uuid.UUID, data: ContactUpdate) -> Optional[Contact]:
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
        contact = await self.get_by_id(contact_id)
        if not contact:
            return False
        await self.db.delete(contact)
        await self.db.flush()
        return True

    async def bulk_import(self, contacts_data: List[ContactCreate]) -> dict:
        stats = {"created": 0, "updated": 0, "skipped": 0, "errors": []}

        for idx, data in enumerate(contacts_data):
            try:
                existing = await self.get_by_email(data.email, data.source)
                if existing:
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
        contact = await self.get_by_id(contact_id)
        if not contact:
            return None

        contact.lead_score = max(0, contact.lead_score + score_delta)

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
        # Use raw SQL to avoid pymssql type conversion issues with COUNT + GUID
        total_r = await self.db.execute(text("SELECT COUNT(*) FROM contacts"))
        total = total_r.fetchone()[0]

        active_r = await self.db.execute(text("SELECT COUNT(*) FROM contacts WHERE status = 'ACTIVE'"))
        active = active_r.fetchone()[0]

        internal_r = await self.db.execute(text("SELECT COUNT(*) FROM contacts WHERE is_internal = 1"))
        internal = internal_r.fetchone()[0]

        by_source_r = await self.db.execute(text("SELECT source, COUNT(*) as cnt FROM contacts GROUP BY source"))
        by_source = {str(row[0]): row[1] for row in by_source_r.fetchall()}

        by_stage_r = await self.db.execute(text("SELECT lead_stage, COUNT(*) as cnt FROM contacts GROUP BY lead_stage"))
        by_stage = {str(row[0]): row[1] for row in by_stage_r.fetchall()}

        return {
            "total": total,
            "active": active,
            "internal": internal,
            "by_source": by_source,
            "by_stage": by_stage,
        }

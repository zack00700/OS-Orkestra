"""
OS Orkestra — Endpoints Templates & Segments
Compatible Python 3.9+
"""
from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import get_current_user, require_roles
from app.models.models import Template, Segment
from app.schemas.schemas import (
    TemplateCreate, TemplateResponse, SegmentCreate, SegmentResponse,
)

# ── TEMPLATES ──────────────────────────────────────────

templates_router = APIRouter(prefix="/templates", tags=["Templates"])


@templates_router.get("/")
async def list_templates(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(
        select(Template).where(Template.is_active == True).order_by(Template.name)
    )
    templates = result.scalars().all()
    return [
        {
            "id": str(t.id),
            "name": t.name,
            "subject": t.subject,
            "category": t.category,
            "variables": t.variables,
            "is_active": t.is_active,
        }
        for t in templates
    ]


@templates_router.get("/{template_id}")
async def get_template(
    template_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(select(Template).where(Template.id == template_id))
    t = result.scalar_one_or_none()
    if not t:
        raise HTTPException(status_code=404, detail="Template non trouvé")
    return {
        "id": str(t.id),
        "name": t.name,
        "subject": t.subject,
        "html_content": t.html_content,
        "text_content": t.text_content,
        "category": t.category,
        "variables": t.variables,
    }


@templates_router.post("/")
async def create_template(
    data: TemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_roles("admin", "manager", "editor")),
):
    import uuid as _uuid
    tpl = Template(
        id=_uuid.uuid4(),
        name=data.name,
        subject=data.subject,
        html_content=data.html_content,
        text_content=data.text_content,
        category=data.category,
        variables=data.variables,
    )
    db.add(tpl)
    await db.flush()
    await db.refresh(tpl)
    return {"id": str(tpl.id), "name": tpl.name, "message": "Template créé"}


# ── SEGMENTS ───────────────────────────────────────────

segments_router = APIRouter(prefix="/segments", tags=["Segments"])


@segments_router.get("/")
async def list_segments(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(select(Segment).order_by(Segment.name))
    segments = result.scalars().all()
    return [
        {
            "id": str(s.id),
            "name": s.name,
            "description": s.description,
            "contact_count": s.contact_count,
            "is_dynamic": s.is_dynamic,
        }
        for s in segments
    ]


@segments_router.get("/{segment_id}")
async def get_segment(
    segment_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(select(Segment).where(Segment.id == segment_id))
    s = result.scalar_one_or_none()
    if not s:
        raise HTTPException(status_code=404, detail="Segment non trouvé")
    return {
        "id": str(s.id),
        "name": s.name,
        "description": s.description,
        "contact_count": s.contact_count,
        "filter_criteria": s.filter_criteria,
    }

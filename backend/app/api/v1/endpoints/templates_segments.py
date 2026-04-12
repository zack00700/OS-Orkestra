"""
OS Orkestra — Endpoints Templates & Segments (dynamiques)
Compatible Python 3.9+ / pymssql sync
"""
import uuid as _uuid
import json
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, text
from app.core.database import get_db
from app.core.query_helpers import build_raw_paginated_query
from app.core.security import get_current_user, require_roles
from app.models.models import Template, Segment, Contact
from app.schemas.schemas import TemplateCreate, SegmentCreate

# ── TEMPLATES ──────────────────────────────────────────

templates_router = APIRouter(prefix="/templates", tags=["Templates"])


@templates_router.get("/")
async def list_templates(
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(
        select(Template).where(Template.is_active.is_(True)).order_by(Template.name)
    )
    templates = result.scalars().all()
    return [
        {
            "id": str(t.id),
            "name": t.name,
            "subject": t.subject,
            "category": t.category,
            "variables": _parse_json(t.variables),
            "is_active": t.is_active,
        }
        for t in templates
    ]


@templates_router.get("/{template_id}")
async def get_template(
    template_id: str,
    db=Depends(get_db),
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
        "variables": _parse_json(t.variables),
    }


@templates_router.post("/")
async def create_template(
    data: TemplateCreate,
    db=Depends(get_db),
    current_user: dict = Depends(require_roles("admin", "manager", "editor")),
):
    tpl = Template(
        id=str(_uuid.uuid4()),
        name=data.name,
        subject=data.subject,
        html_content=data.html_content,
        text_content=data.text_content,
        category=data.category,
        variables=json.dumps(data.variables) if data.variables else None,
    )
    db.add(tpl)
    await db.flush()
    return {"id": str(tpl.id), "name": tpl.name, "message": "Template créé"}


# ── SEGMENTS (DYNAMIQUES) ─────────────────────────────

segments_router = APIRouter(prefix="/segments", tags=["Segments"])


@segments_router.get("/")
async def list_segments(
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(select(Segment).order_by(Segment.name))
    segments = result.scalars().all()

    output = []
    for s in segments:
        # Recalculer le count dynamiquement
        criteria = _parse_json(s.filter_criteria)
        count = await _count_contacts_for_segment(db, criteria)

        output.append({
            "id": str(s.id),
            "name": s.name,
            "description": s.description,
            "contact_count": count,
            "is_dynamic": s.is_dynamic,
            "filter_criteria": criteria,
        })
    return output


@segments_router.get("/{segment_id}")
async def get_segment(
    segment_id: str,
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(select(Segment).where(Segment.id == segment_id))
    s = result.scalar_one_or_none()
    if not s:
        raise HTTPException(status_code=404, detail="Segment non trouvé")

    criteria = _parse_json(s.filter_criteria)
    count = await _count_contacts_for_segment(db, criteria)

    return {
        "id": str(s.id),
        "name": s.name,
        "description": s.description,
        "contact_count": count,
        "filter_criteria": criteria,
    }


@segments_router.get("/{segment_id}/contacts")
async def get_segment_contacts(
    segment_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db=Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Liste les contacts d'un segment basé sur ses filtres."""
    result = await db.execute(select(Segment).where(Segment.id == segment_id))
    s = result.scalar_one_or_none()
    if not s:
        raise HTTPException(status_code=404, detail="Segment non trouvé")

    criteria = _parse_json(s.filter_criteria)
    where_clause, params = _build_where_clause(criteria)

    # Count
    count_sql = f"SELECT COUNT(*) FROM contacts{where_clause}"
    count_result = await db.execute(text(count_sql))
    total = count_result.fetchone()[0]

    # Paginated results (portable : LIMIT/OFFSET pour SQLite/PG, OFFSET FETCH pour SQL Server)
    base_sql = f"SELECT id, email, first_name, last_name, company, country, city, phone, job_title, source, status, lead_stage, lead_score FROM contacts{where_clause}"
    data_sql = build_raw_paginated_query(base_sql, page=page, page_size=page_size, order_by="email")
    data_result = await db.execute(text(data_sql))
    rows = data_result.fetchall()

    contacts = []
    for row in rows:
        contacts.append({
            "id": str(row[0]),
            "email": row[1],
            "first_name": row[2],
            "last_name": row[3],
            "company": row[4],
            "country": row[5],
            "city": row[6],
            "phone": row[7],
            "job_title": row[8],
            "source": str(row[9]),
            "status": str(row[10]),
            "lead_stage": str(row[11]),
            "lead_score": row[12],
        })

    return {
        "segment": s.name,
        "total": total,
        "page": page,
        "page_size": page_size,
        "contacts": contacts,
    }


@segments_router.post("/")
async def create_segment(
    data: SegmentCreate,
    db=Depends(get_db),
    current_user: dict = Depends(require_roles("admin", "manager")),
):
    """Créer un segment avec des filtres dynamiques."""
    seg = Segment(
        id=str(_uuid.uuid4()),
        name=data.name,
        description=data.description,
        filter_criteria=json.dumps(data.filter_criteria) if isinstance(data.filter_criteria, dict) else str(data.filter_criteria),
        is_dynamic=data.is_dynamic,
        contact_count=0,
    )
    db.add(seg)
    await db.flush()

    # Calculer le count initial
    criteria = data.filter_criteria if isinstance(data.filter_criteria, dict) else {}
    count = await _count_contacts_for_segment(db, criteria)

    return {
        "id": str(seg.id),
        "name": seg.name,
        "contact_count": count,
        "message": f"Segment '{seg.name}' créé avec {count} contacts",
    }


@segments_router.delete("/{segment_id}")
async def delete_segment(
    segment_id: str,
    db=Depends(get_db),
    current_user: dict = Depends(require_roles("admin")),
):
    result = await db.execute(select(Segment).where(Segment.id == segment_id))
    s = result.scalar_one_or_none()
    if not s:
        raise HTTPException(status_code=404, detail="Segment non trouvé")
    await db.delete(s)
    await db.flush()
    return {"message": f"Segment '{s.name}' supprimé"}


# ── HELPERS ───────────────────────────────────────────

def _parse_json(value):
    """Parse une valeur JSON stockée comme string."""
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return {}
    return {}


def _build_where_clause(criteria: dict) -> tuple:
    """Construit une clause WHERE SQL à partir des critères du segment."""
    if not criteria:
        return "", {}

    conditions = []
    for key, value in criteria.items():
        if key in ("country", "city", "company", "segment", "source", "status", "lead_stage", "business_unit"):
            if isinstance(value, list):
                values_str = ", ".join([f"'{v}'" for v in value])
                conditions.append(f"{key} IN ({values_str})")
            else:
                conditions.append(f"{key} = '{value}'")
        elif key == "is_internal":
            conditions.append(f"is_internal = {1 if value else 0}")
        elif key == "min_score":
            conditions.append(f"lead_score >= {int(value)}")
        elif key == "max_score":
            conditions.append(f"lead_score <= {int(value)}")
        elif key == "has_email":
            conditions.append("email IS NOT NULL AND email != ''")

    if not conditions:
        return "", {}

    return " WHERE " + " AND ".join(conditions), {}


async def _count_contacts_for_segment(db, criteria: dict) -> int:
    """Compte les contacts qui matchent les critères d'un segment."""
    where_clause, _ = _build_where_clause(criteria)
    sql = f"SELECT COUNT(*) FROM contacts{where_clause}"
    result = await db.execute(text(sql))
    row = result.fetchone()
    return row[0] if row else 0

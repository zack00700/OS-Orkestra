"""
OS Orkestra — Import CSV
Upload CSV + mapping auto-suggest + import contacts
Compatible Python 3.9+
"""
import uuid
import csv
import io
import re
import json
import logging
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy import text
from app.core.database import get_db
from app.core.security import require_roles
from app.models.models import Contact

logger = logging.getLogger("orkestra.csv_import")

router = APIRouter(prefix="/import", tags=["Import"])

_EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")


@router.post("/csv/preview")
async def preview_csv(
    file: UploadFile = File(...),
    current_user: dict = Depends(require_roles("admin", "manager")),
):
    """Upload un CSV et retourne les premières lignes + colonnes pour le mapping."""
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Le fichier doit être un .csv")

    content = await file.read()
    try:
        text_content = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        text_content = content.decode("latin-1")

    reader = csv.DictReader(io.StringIO(text_content))
    columns = reader.fieldnames or []
    rows = []
    for i, row in enumerate(reader):
        if i >= 5:
            break
        rows.append(dict(row))

    # Auto-suggest mapping
    mapping_suggestions = {}
    orkestra_fields = [
        "email", "first_name", "last_name", "company", "phone",
        "country", "city", "job_title", "source",
    ]
    for field in orkestra_fields:
        for col in columns:
            col_clean = col.lower().replace("_", "").replace(" ", "").replace("-", "")
            field_clean = field.lower().replace("_", "")
            if field_clean in col_clean:
                mapping_suggestions[col] = field
                break

    return {
        "filename": file.filename,
        "total_columns": len(columns),
        "columns": columns,
        "preview_rows": rows,
        "mapping_suggestions": mapping_suggestions,
        "orkestra_fields": orkestra_fields,
    }


@router.post("/csv/execute")
async def execute_csv_import(
    file: UploadFile = File(...),
    mapping_json: str = Form(...),
    db=Depends(get_db),
    current_user: dict = Depends(require_roles("admin", "manager")),
):
    """Importe les contacts depuis un CSV avec le mapping fourni."""
    mapping = json.loads(mapping_json)

    content = await file.read()
    try:
        text_content = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        text_content = content.decode("latin-1")

    reader = csv.DictReader(io.StringIO(text_content))
    imported = 0
    skipped = 0
    errors = []

    # Précharge tous les emails existants en une seule requête (évite N+1)
    try:
        existing_result = await db.execute(text("SELECT email FROM contacts"))
        existing_emails = {r[0].lower() for r in existing_result.fetchall() if r[0]}
    except Exception:
        await db.rollback()
        existing_emails = set()

    for i, row in enumerate(reader):
        try:
            contact_data = {}
            for csv_col, orkestra_field in mapping.items():
                if csv_col in row and orkestra_field:
                    contact_data[orkestra_field] = row[csv_col].strip() if row[csv_col] else None

            email = contact_data.get("email")
            if not email or not _EMAIL_RE.match(email):
                skipped += 1
                continue

            if email.lower() in existing_emails:
                skipped += 1
                continue

            contact = Contact(
                id=str(uuid.uuid4()),
                email=email,
                first_name=contact_data.get("first_name"),
                last_name=contact_data.get("last_name"),
                company=contact_data.get("company"),
                phone=contact_data.get("phone"),
                country=contact_data.get("country"),
                city=contact_data.get("city"),
                job_title=contact_data.get("job_title"),
                source=contact_data.get("source", "csv_import"),
                status="active",
                lead_stage="awareness",
                lead_score=0,
                tags=json.dumps(["imported", "csv"]),
            )
            db.add(contact)
            existing_emails.add(email.lower())
            imported += 1

        except Exception as e:
            await db.rollback()
            errors.append(f"Ligne {i + 1}: {str(e)}")

    if imported > 0:
        try:
            await db.flush()
        except Exception as e:
            await db.rollback()
            errors.append(f"Flush: {str(e)}")
            imported = 0

    return {
        "status": "completed",
        "imported": imported,
        "skipped": skipped,
        "errors": errors[:10],
        "message": f"{imported} contacts importés, {skipped} ignorés",
    }

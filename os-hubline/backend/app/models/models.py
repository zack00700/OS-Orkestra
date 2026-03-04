"""
OS HubLine — Modèles ORM portables (SQLAlchemy 2.0)

Compatible : PostgreSQL, SQL Server, MySQL/MariaDB, SQLite, Oracle
Utilise les types portables GUID, ArrayField, JSONField au lieu des
types spécifiques PostgreSQL (UUID, ARRAY, JSONB).
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    String, Text, Integer, Float, Boolean, DateTime, ForeignKey,
    Enum as SAEnum, Index, UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.core.types import GUID, ArrayField, JSONField, LargeText
import enum


# ══════════════════════════════════════════════════════════
# ENUMS
# ══════════════════════════════════════════════════════════

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    EDITOR = "editor"
    VIEWER = "viewer"


class ContactSource(str, enum.Enum):
    CRM_DYNAMICS = "crm_dynamics"
    CRM_SALESFORCE = "crm_salesforce"
    AZURE_AD = "azure_ad"
    IMPORT_CSV = "import_csv"
    WEBFORM = "webform"
    MANUAL = "manual"


class ContactStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    UNSUBSCRIBED = "unsubscribed"
    BOUNCED = "bounced"
    BLACKLISTED = "blacklisted"


class CampaignStatus(str, enum.Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class CampaignType(str, enum.Enum):
    EXTERNAL = "external"
    INTERNAL = "internal"


class ChannelType(str, enum.Enum):
    EMAIL = "email"
    SMS = "sms"
    WHATSAPP = "whatsapp"


class LeadStage(str, enum.Enum):
    AWARENESS = "awareness"
    INTEREST = "interest"
    CONSIDERATION = "consideration"
    PURCHASE = "purchase"
    RETENTION = "retention"


class EventType(str, enum.Enum):
    SENT = "sent"
    DELIVERED = "delivered"
    OPENED = "opened"
    CLICKED = "clicked"
    BOUNCED_SOFT = "bounced_soft"
    BOUNCED_HARD = "bounced_hard"
    UNSUBSCRIBED = "unsubscribed"
    SPAM_REPORTED = "spam_reported"
    CONVERTED = "converted"


# ══════════════════════════════════════════════════════════
# MIXINS
# ══════════════════════════════════════════════════════════

class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


# ══════════════════════════════════════════════════════════
# MODELS — Tous les types sont portables cross-DB
# ══════════════════════════════════════════════════════════

class User(TimestampMixin, Base):
    """Utilisateur de la plateforme OS HubLine."""
    __tablename__ = "users"

    # GUID() → UUID natif sur PG, UNIQUEIDENTIFIER sur SQL Server, CHAR(36) ailleurs
    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(SAEnum(UserRole, native_enum=False, length=20), default=UserRole.VIEWER)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    azure_ad_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    campaigns: Mapped[list["Campaign"]] = relationship(back_populates="created_by_user")


class Contact(TimestampMixin, Base):
    """Contact (prospect, client ou collaborateur interne)."""
    __tablename__ = "contacts"
    __table_args__ = (
        Index("ix_contacts_email_source", "email", "source"),
        UniqueConstraint("email", "source", name="uq_contact_email_source"),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), index=True)
    first_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    company: Mapped[str | None] = mapped_column(String(255), nullable=True)
    job_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    business_unit: Mapped[str | None] = mapped_column(String(100), nullable=True)
    segment: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # native_enum=False → stocke en VARCHAR, pas en type ENUM natif
    # (SQL Server et SQLite ne supportent pas les ENUMs natifs)
    source: Mapped[ContactSource] = mapped_column(
        SAEnum(ContactSource, native_enum=False, length=30), default=ContactSource.MANUAL
    )
    status: Mapped[ContactStatus] = mapped_column(
        SAEnum(ContactStatus, native_enum=False, length=20), default=ContactStatus.ACTIVE
    )
    lead_stage: Mapped[LeadStage] = mapped_column(
        SAEnum(LeadStage, native_enum=False, length=20), default=LeadStage.AWARENESS
    )
    lead_score: Mapped[int] = mapped_column(Integer, default=0)
    is_internal: Mapped[bool] = mapped_column(Boolean, default=False)
    gdpr_consent: Mapped[bool] = mapped_column(Boolean, default=False)
    gdpr_consent_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    external_crm_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    azure_ad_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # JSONField() → JSONB sur PG, JSON sur MySQL, NVARCHAR(MAX) sur SQL Server, TEXT sur SQLite
    custom_fields: Mapped[dict | None] = mapped_column(JSONField(), nullable=True)
    # ArrayField() → ARRAY(String) sur PG, JSON sur MySQL, NVARCHAR(MAX)/TEXT sérialisé ailleurs
    tags: Mapped[list[str] | None] = mapped_column(ArrayField(), nullable=True)

    events: Mapped[list["CampaignEvent"]] = relationship(back_populates="contact")
    segment_memberships: Mapped[list["SegmentMembership"]] = relationship(back_populates="contact")


class Segment(TimestampMixin, Base):
    """Segment de contacts pour ciblage."""
    __tablename__ = "segments"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    filter_criteria: Mapped[dict] = mapped_column(JSONField(), default=dict)
    is_dynamic: Mapped[bool] = mapped_column(Boolean, default=True)
    contact_count: Mapped[int] = mapped_column(Integer, default=0)

    memberships: Mapped[list["SegmentMembership"]] = relationship(back_populates="segment")


class SegmentMembership(Base):
    """Table d'association Contact <-> Segment."""
    __tablename__ = "segment_memberships"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    contact_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("contacts.id", ondelete="CASCADE"))
    segment_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("segments.id", ondelete="CASCADE"))
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    contact: Mapped["Contact"] = relationship(back_populates="segment_memberships")
    segment: Mapped["Segment"] = relationship(back_populates="memberships")


class Template(TimestampMixin, Base):
    """Template email réutilisable."""
    __tablename__ = "templates"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255))
    subject: Mapped[str] = mapped_column(String(500))
    # LargeText() → TEXT sur PG, NVARCHAR(MAX) sur SQL Server, CLOB sur Oracle
    html_content: Mapped[str] = mapped_column(LargeText())
    text_content: Mapped[str | None] = mapped_column(LargeText(), nullable=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    thumbnail_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    variables: Mapped[list[str] | None] = mapped_column(ArrayField(), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Campaign(TimestampMixin, Base):
    """Campagne emailing (interne ou externe)."""
    __tablename__ = "campaigns"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    campaign_type: Mapped[CampaignType] = mapped_column(SAEnum(CampaignType, native_enum=False, length=20))
    channel: Mapped[ChannelType] = mapped_column(SAEnum(ChannelType, native_enum=False, length=20), default=ChannelType.EMAIL)
    status: Mapped[CampaignStatus] = mapped_column(SAEnum(CampaignStatus, native_enum=False, length=20), default=CampaignStatus.DRAFT)
    template_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("templates.id"), nullable=True)
    segment_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("segments.id"), nullable=True)
    subject: Mapped[str | None] = mapped_column(String(500), nullable=True)
    from_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    from_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id"))
    tags: Mapped[list[str] | None] = mapped_column(ArrayField(), nullable=True)

    # Métriques agrégées
    total_sent: Mapped[int] = mapped_column(Integer, default=0)
    total_delivered: Mapped[int] = mapped_column(Integer, default=0)
    total_opened: Mapped[int] = mapped_column(Integer, default=0)
    total_clicked: Mapped[int] = mapped_column(Integer, default=0)
    total_bounced: Mapped[int] = mapped_column(Integer, default=0)
    total_unsubscribed: Mapped[int] = mapped_column(Integer, default=0)

    created_by_user: Mapped["User"] = relationship(back_populates="campaigns")
    template: Mapped["Template"] = relationship()
    segment: Mapped["Segment"] = relationship()
    events: Mapped[list["CampaignEvent"]] = relationship(back_populates="campaign")


class CampaignEvent(Base):
    """Événement de tracking (envoi, ouverture, clic, etc.)."""
    __tablename__ = "campaign_events"
    __table_args__ = (
        Index("ix_events_campaign_type", "campaign_id", "event_type"),
        Index("ix_events_contact_campaign", "contact_id", "campaign_id"),
        Index("ix_events_timestamp", "timestamp"),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    campaign_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("campaigns.id", ondelete="CASCADE"))
    contact_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("contacts.id", ondelete="CASCADE"))
    event_type: Mapped[EventType] = mapped_column(SAEnum(EventType, native_enum=False, length=20))
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    metadata_json: Mapped[dict | None] = mapped_column(JSONField(), nullable=True)
    url_clicked: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)

    campaign: Mapped["Campaign"] = relationship(back_populates="events")
    contact: Mapped["Contact"] = relationship(back_populates="events")


class AutomationScenario(TimestampMixin, Base):
    """Scénario d'automatisation (workflow)."""
    __tablename__ = "automation_scenarios"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    trigger_type: Mapped[str] = mapped_column(String(100))
    trigger_config: Mapped[dict] = mapped_column(JSONField(), default=dict)
    steps: Mapped[list[dict]] = mapped_column(JSONField(), default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    total_enrolled: Mapped[int] = mapped_column(Integer, default=0)
    total_completed: Mapped[int] = mapped_column(Integer, default=0)


class SyncLog(TimestampMixin, Base):
    """Journal de synchronisation CRM / Azure AD."""
    __tablename__ = "sync_logs"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    source: Mapped[str] = mapped_column(String(50))
    direction: Mapped[str] = mapped_column(String(20))
    total_records: Mapped[int] = mapped_column(Integer, default=0)
    success_count: Mapped[int] = mapped_column(Integer, default=0)
    error_count: Mapped[int] = mapped_column(Integer, default=0)
    duplicate_count: Mapped[int] = mapped_column(Integer, default=0)
    errors: Mapped[list[dict] | None] = mapped_column(JSONField(), nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)


class DataQualityReport(TimestampMixin, Base):
    """Rapport de qualité des données."""
    __tablename__ = "data_quality_reports"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    report_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    total_contacts: Mapped[int] = mapped_column(Integer, default=0)
    email_valid_pct: Mapped[float] = mapped_column(Float, default=0.0)
    field_completion_pct: Mapped[float] = mapped_column(Float, default=0.0)
    duplicate_count: Mapped[int] = mapped_column(Integer, default=0)
    stale_count: Mapped[int] = mapped_column(Integer, default=0)
    details: Mapped[dict | None] = mapped_column(JSONField(), nullable=True)

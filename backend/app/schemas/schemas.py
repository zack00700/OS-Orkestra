"""
OS HubLine — Schémas Pydantic (validation API)
Compatible Python 3.9+
"""
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from app.models.models import (
    UserRole, ContactSource, ContactStatus, CampaignStatus,
    CampaignType, ChannelType, LeadStage, EventType,
)


# ══════════════════════════════════════════════════════════
# AUTH
# ══════════════════════════════════════════════════════════

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    refresh_token: str


# ══════════════════════════════════════════════════════════
# USER
# ══════════════════════════════════════════════════════════

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=2, max_length=255)
    role: UserRole = UserRole.VIEWER


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


# ══════════════════════════════════════════════════════════
# CONTACT
# ══════════════════════════════════════════════════════════

class ContactCreate(BaseModel):
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company: Optional[str] = None
    job_title: Optional[str] = None
    phone: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    business_unit: Optional[str] = None
    segment: Optional[str] = None
    source: ContactSource = ContactSource.MANUAL
    is_internal: bool = False
    gdpr_consent: bool = False
    tags: Optional[List[str]] = None
    custom_fields: Optional[Dict[str, Any]] = None


class ContactResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    company: Optional[str]
    job_title: Optional[str]
    phone: Optional[str]
    country: Optional[str]
    city: Optional[str]
    business_unit: Optional[str]
    segment: Optional[str]
    source: ContactSource
    status: ContactStatus
    lead_stage: LeadStage
    lead_score: int
    is_internal: bool
    gdpr_consent: bool
    tags: Optional[List[str]]
    created_at: datetime
    updated_at: datetime


class ContactUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company: Optional[str] = None
    job_title: Optional[str] = None
    phone: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    business_unit: Optional[str] = None
    segment: Optional[str] = None
    status: Optional[ContactStatus] = None
    lead_stage: Optional[LeadStage] = None
    lead_score: Optional[int] = None
    tags: Optional[List[str]] = None
    custom_fields: Optional[Dict[str, Any]] = None


class ContactListResponse(BaseModel):
    items: List[ContactResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ══════════════════════════════════════════════════════════
# SEGMENT
# ══════════════════════════════════════════════════════════

class SegmentCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    description: Optional[str] = None
    filter_criteria: Dict[str, Any] = Field(default_factory=dict)
    is_dynamic: bool = True


class SegmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    description: Optional[str]
    filter_criteria: Dict[str, Any]
    is_dynamic: bool
    contact_count: int
    created_at: datetime


# ══════════════════════════════════════════════════════════
# TEMPLATE
# ══════════════════════════════════════════════════════════

class TemplateCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    subject: str = Field(min_length=2, max_length=500)
    html_content: str
    text_content: Optional[str] = None
    category: Optional[str] = None
    variables: Optional[List[str]] = None


class TemplateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    subject: str
    html_content: str
    text_content: Optional[str]
    category: Optional[str]
    variables: Optional[List[str]]
    is_active: bool
    created_at: datetime


# ══════════════════════════════════════════════════════════
# CAMPAIGN
# ══════════════════════════════════════════════════════════

class CampaignCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    description: Optional[str] = None
    campaign_type: CampaignType
    channel: ChannelType = ChannelType.EMAIL
    template_id: Optional[UUID] = None
    segment_id: Optional[UUID] = None
    subject: Optional[str] = None
    from_name: Optional[str] = None
    from_email: Optional[EmailStr] = None
    scheduled_at: Optional[datetime] = None
    tags: Optional[List[str]] = None


class CampaignResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    description: Optional[str]
    campaign_type: CampaignType
    channel: ChannelType
    status: CampaignStatus
    template_id: Optional[UUID]
    segment_id: Optional[UUID]
    subject: Optional[str]
    from_name: Optional[str]
    from_email: Optional[str]
    scheduled_at: Optional[datetime]
    sent_at: Optional[datetime]
    completed_at: Optional[datetime]
    total_sent: int
    total_delivered: int
    total_opened: int
    total_clicked: int
    total_bounced: int
    total_unsubscribed: int
    tags: Optional[List[str]]
    created_at: datetime
    updated_at: datetime


class CampaignUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[CampaignStatus] = None
    template_id: Optional[UUID] = None
    segment_id: Optional[UUID] = None
    subject: Optional[str] = None
    from_name: Optional[str] = None
    from_email: Optional[EmailStr] = None
    scheduled_at: Optional[datetime] = None
    tags: Optional[List[str]] = None


class CampaignListResponse(BaseModel):
    items: List[CampaignResponse]
    total: int
    page: int
    page_size: int


# ══════════════════════════════════════════════════════════
# CAMPAIGN ANALYTICS
# ══════════════════════════════════════════════════════════

class CampaignAnalytics(BaseModel):
    campaign_id: UUID
    campaign_name: str
    total_sent: int
    total_delivered: int
    total_opened: int
    unique_opens: int
    total_clicked: int
    unique_clicks: int
    total_bounced: int
    total_unsubscribed: int
    open_rate: float
    click_rate: float
    reactivity_rate: float
    deliverability_rate: float
    bounce_rate: float
    unsubscribe_rate: float


class DashboardStats(BaseModel):
    total_contacts: int
    active_contacts: int
    internal_contacts: int
    total_campaigns: int
    active_campaigns: int
    total_sent_30d: int
    avg_open_rate_30d: float
    avg_click_rate_30d: float
    avg_deliverability_30d: float
    top_campaigns: List[CampaignAnalytics]
    recent_syncs: List[Dict[str, Any]]
    data_quality_score: float


# ══════════════════════════════════════════════════════════
# AUTOMATION
# ══════════════════════════════════════════════════════════

class AutomationCreate(BaseModel):
    name: str
    description: Optional[str] = None
    trigger_type: str
    trigger_config: Dict[str, Any] = Field(default_factory=dict)
    steps: List[Dict[str, Any]] = Field(default_factory=list)


class AutomationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    description: Optional[str]
    trigger_type: str
    trigger_config: Dict[str, Any]
    steps: List[Dict[str, Any]]
    is_active: bool
    total_enrolled: int
    total_completed: int
    created_at: datetime


# ══════════════════════════════════════════════════════════
# SYNC & DATA QUALITY
# ══════════════════════════════════════════════════════════

class SyncLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    source: str
    direction: str
    total_records: int
    success_count: int
    error_count: int
    duplicate_count: int
    started_at: datetime
    completed_at: Optional[datetime]
    duration_seconds: Optional[float]


class DataQualityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    report_date: datetime
    total_contacts: int
    email_valid_pct: float
    field_completion_pct: float
    duplicate_count: int
    stale_count: int
    details: Optional[Dict[str, Any]]


# ══════════════════════════════════════════════════════════
# COMMON
# ══════════════════════════════════════════════════════════

class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str
    database: str
    redis: str


class MessageResponse(BaseModel):
    message: str
    detail: Optional[str] = None

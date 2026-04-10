"""
OS HubLine — Configuration centrale
Compatible Python 3.9+
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional, List
from functools import lru_cache


class Settings(BaseSettings):
    """Configuration de l'application OS HubLine."""

    # ── App ──────────────────────────────────────────────
    APP_NAME: str = "OS HubLine"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "Marketing Automation & Campaign Management — OpenSID"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    API_V1_PREFIX: str = "/api/v1"
    SECRET_KEY: str = "CHANGE-ME-IN-PRODUCTION"
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    # ── Database ─────────────────────────────────────────
    DATABASE_URL: str = "mssql+pyodbc://sa:password@localhost:1433/hubline?driver=ODBC+Driver+18+for+SQL+Server"
    DATABASE_ECHO: bool = False
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10

    # ── Redis ────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_TTL: int = 300

    # ── Celery ───────────────────────────────────────────
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # ── JWT Auth ─────────────────────────────────────────
    JWT_SECRET_KEY: str = "CHANGE-ME"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── Azure AD / Microsoft Entra ID ────────────────────
    AZURE_TENANT_ID: Optional[str] = None
    AZURE_CLIENT_ID: Optional[str] = None
    AZURE_CLIENT_SECRET: Optional[str] = None
    AZURE_AUTHORITY: str = "https://login.microsoftonline.com"
    AZURE_SCOPES: List[str] = ["https://graph.microsoft.com/.default"]

    # ── CRM Dynamics ─────────────────────────────────────
    DYNAMICS_BASE_URL: Optional[str] = None
    DYNAMICS_CLIENT_ID: Optional[str] = None
    DYNAMICS_CLIENT_SECRET: Optional[str] = None
    DYNAMICS_TENANT_ID: Optional[str] = None

    # ── CRM Salesforce ───────────────────────────────────
    SALESFORCE_BASE_URL: Optional[str] = None
    SALESFORCE_CLIENT_ID: Optional[str] = None
    SALESFORCE_CLIENT_SECRET: Optional[str] = None
    SALESFORCE_USERNAME: Optional[str] = None
    SALESFORCE_PASSWORD: Optional[str] = None

    # ── WhatsApp Business API ────────────────────────────
    WHATSAPP_API_URL: Optional[str] = None
    WHATSAPP_API_TOKEN: Optional[str] = None
    WHATSAPP_PHONE_NUMBER_ID: Optional[str] = None

    # ── Email / SMTP ─────────────────────────────────────
    SMTP_HOST: str = "smtp.example.com"
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_EMAIL: str = "noreply@opensid.com"
    SMTP_FROM_NAME: str = "OS HubLine"
    SMTP_USE_TLS: bool = True

    # ── Storage ──────────────────────────────────────────
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE_MB: int = 25

    # ── Rate Limiting ────────────────────────────────────
    RATE_LIMIT_PER_MINUTE: int = 60

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()

"""Application configuration loaded from environment variables."""
from __future__ import annotations

from typing import List, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    APP_ENV: str = "development"
    APP_NAME: str = "PATCHORA"
    APP_VERSION: str = "0.1.0"
    SECRET_KEY: str = "change-me-in-production-to-a-very-long-and-secure-random-key"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # Security & Authentication
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_MAX_LENGTH: int = 128

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://bughunter:password@localhost:5432/bughunter_db"
    USE_SQLITE: bool = False
    SQLITE_PATH: str = "./bughunter.db"

    # Payment Gateway & Billing
    PAYMENT_PROVIDER: str = "sandbox"  # "stripe" | "sandbox"
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_PUBLISHABLE_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None
    BILLING_CURRENCY: str = "USD"

    # AI Bug-Fixing & Remediation Engine
    AI_PROVIDER: str = "deterministic_rules"  # "deterministic_rules" | "gemini" | "openai" | "anthropic"
    GEMINI_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    AI_MODEL_NAME: str = "gemini-1.5-pro"
    AI_MAX_TOKENS: int = 4096
    AI_TEMPERATURE: float = 0.2
    REMEDIATION_ISOLATION_WORKSPACE: str = "./remediation_sandboxes"

    # Git Integration, CI/CD & Secure Deployment (Phase 9)
    GITHUB_CLIENT_ID: Optional[str] = None
    GITHUB_CLIENT_SECRET: Optional[str] = None
    GITHUB_DEFAULT_BRANCH: str = "main"
    ENABLE_PRODUCTION_DEPLOYMENT: bool = False  # Disabled by default for security
    ENABLE_STAGING_DEPLOYMENT: bool = True

    # Client Finder Automation & Compliant Outreach (Phase 10)
    OUTREACH_PROVIDER: str = "sandbox_logger"  # "sandbox_logger" | "smtp"
    OUTREACH_FROM_EMAIL: str = "security@patchora.io"
    OUTREACH_FROM_NAME: str = "PATCHORA Security Team"
    OUTREACH_DAILY_RATE_LIMIT: int = 50
    OUTREACH_COMPLIANCE_ADDRESS: str = "PATCHORA Inc., 100 Cyber Defense Way, Suite 400, San Francisco, CA 94105"
    OUTREACH_OPT_OUT_BASE_URL: str = "http://localhost:5173/opt-out"

    # CORS — stored as a raw comma-separated string so it loads from env cleanly
    CORS_ORIGINS: str = "https://patchura-frontend.onrender.com"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def effective_database_url(self) -> str:
        """Return the database URL, substituting SQLite if USE_SQLITE is set."""
        if self.USE_SQLITE:
            return f"sqlite+aiosqlite:///{self.SQLITE_PATH}"
        return self.DATABASE_URL


settings = Settings()

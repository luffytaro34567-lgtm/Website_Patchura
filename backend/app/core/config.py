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

    # CORS Configuration
    CORS_ORIGINS: Optional[str] = "https://patchura-frontend.onrender.com,http://localhost:5173,http://localhost:3000"
    BACKEND_CORS_ORIGINS: Optional[str] = None
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
    CORS_ALLOW_HEADERS: List[str] = [
        "Authorization",
        "Content-Type",
        "Accept",
        "Origin",
        "X-Request-ID",
        "Access-Control-Request-Method",
        "Access-Control-Request-Headers",
    ]
    CORS_EXPOSE_HEADERS: List[str] = ["X-Request-ID", "X-Process-Time-Ms"]
    CORS_MAX_AGE: int = 600

    @property
    def cors_origin_regex(self) -> Optional[str]:
        """Allow any Render HTTPS domain dynamically for preview and staging branches."""
        return r"^https://.*\.onrender\.com$"

    @property
    def cors_origins_list(self) -> List[str]:
        # Merge both CORS_ORIGINS and BACKEND_CORS_ORIGINS if set
        raw_values: List[str] = []
        if self.CORS_ORIGINS:
            raw_values.append(self.CORS_ORIGINS)
        if self.BACKEND_CORS_ORIGINS:
            raw_values.append(self.BACKEND_CORS_ORIGINS)

        parsed_items: List[str] = []
        for raw in raw_values:
            text = (raw or "").strip()
            if not text:
                continue

            # Support JSON array format e.g. ["https://..."]
            if text.startswith("[") and text.endswith("]"):
                try:
                    import json
                    items = json.loads(text)
                    if isinstance(items, list):
                        parsed_items.extend(str(x) for x in items)
                        continue
                except Exception:
                    pass

            # Comma-separated list
            parsed_items.extend(text.split(","))

        cleaned_origins: List[str] = []
        for item in parsed_items:
            # Strip whitespace, brackets, single/double quotes, and trailing slashes
            cleaned = item.strip().strip("[]'\"`").rstrip("/")
            if cleaned and cleaned not in cleaned_origins:
                cleaned_origins.append(cleaned)

        # Baseline origin for production
        prod_origins = ["https://patchura-frontend.onrender.com"]
        for po in prod_origins:
            norm_po = po.rstrip("/")
            if norm_po not in cleaned_origins and "*" not in cleaned_origins:
                cleaned_origins.append(norm_po)

        # Local development origins are only added if not running in production
        if self.APP_ENV != "production":
            dev_origins = [
                "http://localhost:5173",
                "http://localhost:3000",
                "http://127.0.0.1:5173",
                "http://127.0.0.1:3000",
            ]
            for d in dev_origins:
                norm_d = d.rstrip("/")
                if norm_d not in cleaned_origins and "*" not in cleaned_origins:
                    cleaned_origins.append(norm_d)

        return cleaned_origins

    def validate_cors_settings(self) -> None:
        """Validate CORS configuration at startup and raise clear, descriptive errors."""
        origins = self.cors_origins_list
        if not origins:
            raise ValueError("CORS configuration error: No allowed origins defined.")

        if self.APP_ENV == "production" and "*" in origins and self.CORS_ALLOW_CREDENTIALS:
            raise ValueError(
                "CORS security violation: Wildcard origin '*' cannot be paired with "
                "allow_credentials=True in production. Whitelist explicit trusted origins."
            )

        for origin in origins:
            if origin != "*" and not (origin.startswith("http://") or origin.startswith("https://")):
                raise ValueError(
                    f"CORS configuration error: Origin '{origin}' is invalid. "
                    "Allowed origins must start with 'http://' or 'https://'."
                )

    @property
    def effective_database_url(self) -> str:
        """Return the database URL, substituting SQLite if USE_SQLITE is set."""
        if self.USE_SQLITE:
            return f"sqlite+aiosqlite:///{self.SQLITE_PATH}"
        url = self.DATABASE_URL
        # Normalize Render/Heroku postgres URLs for asyncpg driver
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://") and not url.startswith("postgresql+asyncpg://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url


settings = Settings()

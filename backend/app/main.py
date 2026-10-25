"""
PATCHORA — FastAPI Application Entry Point
"""
from __future__ import annotations

import time
import uuid
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging import configure_logging
from app.db.session import init_db
from app.api.routes import admin, auth, client, health, root, scanner, websites, scans, reports, billing, remediations, deployment, leads
from app.errors.handlers import register_exception_handlers

configure_logging()
logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    settings.validate_cors_settings()
    logger.info(
        "Starting PATCHORA",
        version=settings.APP_VERSION,
        env=settings.APP_ENV,
        cors_origins=settings.cors_origins_list,
    )
    await init_db()
    yield
    logger.info("Shutting down PATCHORA")


def create_application() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="PATCHORA — AI-Assisted Vulnerability Assessment, Security Remediation, and Secure Patch Delivery Platform",
        docs_url="/api/docs" if settings.APP_ENV != "production" else None,
        redoc_url="/api/redoc" if settings.APP_ENV != "production" else None,
        openapi_url="/api/openapi.json" if settings.APP_ENV != "production" else None,
        lifespan=lifespan,
    )

    # ── CORS ─────────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_origin_regex=settings.cors_origin_regex,
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=settings.CORS_ALLOW_METHODS,
        allow_headers=settings.CORS_ALLOW_HEADERS,
        expose_headers=settings.CORS_EXPOSE_HEADERS,
        max_age=settings.CORS_MAX_AGE,
    )

    # ── Security Headers & Request Correlation Middleware ─────────────────────
    @app.middleware("http")
    async def security_headers_and_correlation_middleware(request: Request, call_next):
        # 1. Body size guard (Max 10 MB)
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > 10 * 1024 * 1024:
            return JSONResponse(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                content={
                    "success": False,
                    "error": {
                        "code": 413,
                        "message": "Request payload exceeds maximum permitted size (10 MB).",
                    },
                },
            )

        # 2. Correlation ID
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex

        # 3. Request timing
        start = time.perf_counter()
        response = await call_next(request)
        elapsed = round((time.perf_counter() - start) * 1000, 2)

        # 4. Attach Security Headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time-Ms"] = str(elapsed)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-XSS-Protection"] = "0"
        response.headers["Permissions-Policy"] = "accelerometer=(), camera=(), geolocation=(), gyroscope=(), magnetometer=(), microphone=(), payment=(), usb=()"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "img-src 'self' data: https:; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "font-src 'self'; "
            "frame-ancestors 'none';"
        )

        if settings.APP_ENV == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        return response

    # ── Routes ───────────────────────────────────────────────────────────────
    app.include_router(root.router)
    app.include_router(health.router, prefix="/api")
    app.include_router(scanner.router, prefix="/api")
    app.include_router(auth.router, prefix="/api")
    app.include_router(admin.router, prefix="/api")
    app.include_router(client.router, prefix="/api")
    app.include_router(websites.router, prefix="/api")
    app.include_router(scans.router, prefix="/api")
    app.include_router(reports.router, prefix="/api")
    app.include_router(billing.router, prefix="/api")
    app.include_router(remediations.router, prefix="/api")
    app.include_router(deployment.router, prefix="/api")
    app.include_router(leads.router, prefix="/api")

    # ── Exception handlers ───────────────────────────────────────────────────
    register_exception_handlers(app)

    return app


app = create_application()

"""Health check route."""
from __future__ import annotations

import time

import structlog
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db

router = APIRouter(tags=["Health"])
logger = structlog.get_logger(__name__)

_start_time = time.time()


class DatabaseStatus(BaseModel):
    connected: bool
    error: str | None = None


class HealthResponse(BaseModel):
    status: str          # "healthy" | "degraded"
    version: str
    environment: str
    uptime_seconds: float
    database: DatabaseStatus


@router.get("/health", response_model=HealthResponse, summary="Service health check")
async def health_check(db: AsyncSession = Depends(get_db)) -> HealthResponse:
    """
    Returns the health status of the API and its dependencies.
    - **healthy**: all systems operational
    - **degraded**: API is running but one or more dependencies are unavailable
    """
    db_status = DatabaseStatus(connected=False)
    try:
        await db.execute(text("SELECT 1"))
        db_status = DatabaseStatus(connected=True)
    except Exception as exc:
        logger.warning("Health check: DB unreachable", error=str(exc))
        db_status = DatabaseStatus(connected=False, error="Database unreachable")

    overall = "healthy" if db_status.connected else "degraded"

    return HealthResponse(
        status=overall,
        version=settings.APP_VERSION,
        environment=settings.APP_ENV,
        uptime_seconds=round(time.time() - _start_time, 2),
        database=db_status,
    )

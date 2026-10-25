"""Root route — returns basic application information."""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.config import settings

router = APIRouter(tags=["Root"])


class AppInfoResponse(BaseModel):
    name: str
    version: str
    environment: str
    docs_url: str | None


@router.get("/", response_model=AppInfoResponse, summary="Application info")
async def root() -> AppInfoResponse:
    """Return basic application metadata."""
    return AppInfoResponse(
        name=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.APP_ENV,
        docs_url="/api/docs" if settings.APP_ENV != "production" else None,
    )

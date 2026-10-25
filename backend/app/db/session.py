"""Async SQLAlchemy database session and engine setup."""
from __future__ import annotations

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

logger = structlog.get_logger(__name__)


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""
    pass


# Engine is created lazily so configuration is resolved at startup
_engine = None
_async_session_factory = None


def get_engine():
    global _engine
    if _engine is None:
        db_url = settings.effective_database_url
        connect_args = {}
        if "sqlite" in db_url:
            connect_args = {"check_same_thread": False}
        _engine = create_async_engine(
            db_url,
            echo=settings.DEBUG,
            connect_args=connect_args,
        )
        logger.info("Database engine created", url=db_url.split("@")[-1])
    return _engine


def get_session_factory():
    global _async_session_factory
    if _async_session_factory is None:
        _async_session_factory = async_sessionmaker(
            bind=get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _async_session_factory


# Helper function for session context management
def async_session_factory():
    """Return an async session from the session maker."""
    return get_session_factory()()


def reset_engine():
    """Reset cached engine and session factory (useful for testing)."""
    global _engine, _async_session_factory
    _engine = None
    _async_session_factory = None


async def init_db() -> None:
    """Verify the database connection and initialize tables when using SQLite fallback."""
    try:
        engine = get_engine()
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("Database connection verified")

        # Auto-create tables in SQLite fallback mode or test mode
        if "sqlite" in settings.effective_database_url:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("SQLite schema initialized")
    except Exception as exc:
        logger.warning("Database connection failed at startup", error=str(exc))


async def get_db() -> AsyncSession:
    """FastAPI dependency — yields an async database session."""
    async with get_session_factory()() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

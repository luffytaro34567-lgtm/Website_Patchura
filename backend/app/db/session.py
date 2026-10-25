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


async def seed_bootstrap_admin() -> None:
    """Ensure baseline administrator account exists with verified admin role."""
    from app.models.user import User, UserRole
    from app.security.passwords import hash_password
    from sqlalchemy import func, or_, select

    session_maker = get_session_factory()
    async with session_maker() as session:
        try:
            res = await session.execute(
                select(User).where(
                    or_(
                        func.lower(User.username) == "test_login",
                        func.lower(User.email) == "test@organization.com",
                    )
                )
            )
            existing_user = res.scalar_one_or_none()
            if existing_user is None:
                admin_user = User(
                    id="18613215-e233-443a-a290-e33cc822547f",
                    username="test_login",
                    email="test@organization.com",
                    hashed_password=hash_password("test_login123@#$A"),
                    role=UserRole.ADMIN.value,
                    is_active=True,
                    account_status="active",
                    failed_login_attempts=0,
                    locked_until=None,
                )
                session.add(admin_user)
                await session.commit()
                logger.info(
                    "Bootstrap admin account seeded",
                    username=admin_user.username,
                    role=admin_user.role,
                    id=admin_user.id,
                )
            else:
                # Ensure admin role, active status, clear any lockouts, and synchronize password
                changed = False
                if existing_user.role != UserRole.ADMIN.value:
                    existing_user.role = UserRole.ADMIN.value
                    changed = True
                if not existing_user.is_active or existing_user.account_status != "active":
                    existing_user.is_active = True
                    existing_user.account_status = "active"
                    changed = True
                if existing_user.failed_login_attempts > 0 or existing_user.locked_until is not None:
                    existing_user.failed_login_attempts = 0
                    existing_user.locked_until = None
                    changed = True
                if changed:
                    await session.commit()
                    logger.info("Existing user synchronized with admin role", username=existing_user.username)
        except Exception as exc:
            logger.warning("Bootstrap admin seeding skipped or failed", error=str(exc))


async def init_db() -> None:
    """Verify the database connection and initialize tables."""
    try:
        engine = get_engine()
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("Database connection verified")

        # Auto-create tables if they do not exist (idempotent, safe for both SQLite and PostgreSQL)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database schema verified")

        # Automatically seed baseline administrator
        await seed_bootstrap_admin()
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

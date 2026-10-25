"""Shared pytest configuration and fixtures."""
from __future__ import annotations

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core.config import settings
from app.db.session import Base, get_engine, reset_engine


@pytest.fixture(scope="session", autouse=True)
def use_sqlite(tmp_path_factory):
    """Force SQLite for the test session — no real DB needed."""
    tmp = tmp_path_factory.mktemp("testdb")
    settings.USE_SQLITE = True
    settings.SQLITE_PATH = str(tmp / "test.db")
    reset_engine()
    yield
    settings.USE_SQLITE = False
    reset_engine()


@pytest.fixture(autouse=True)
async def init_test_tables():
    """Ensure all SQLAlchemy tables exist before each test."""
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


@pytest.fixture
async def client():
    """Async HTTP client for the FastAPI test app."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac

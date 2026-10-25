"""Tests for the /api/health endpoint."""
from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_health_returns_200(client):
    response = await client.get("/api/health")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_health_shape(client):
    response = await client.get("/api/health")
    data = response.json()
    assert "status" in data
    assert "version" in data
    assert "environment" in data
    assert "uptime_seconds" in data
    assert "database" in data


@pytest.mark.asyncio
async def test_health_status_value(client):
    """Status must be either 'healthy' or 'degraded' — never a fabricated value."""
    response = await client.get("/api/health")
    data = response.json()
    assert data["status"] in ("healthy", "degraded")


@pytest.mark.asyncio
async def test_health_version_present(client):
    response = await client.get("/api/health")
    data = response.json()
    assert data["version"] != ""

"""Tests for the root / endpoint."""
from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_root_returns_200(client):
    response = await client.get("/")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_root_shape(client):
    response = await client.get("/")
    data = response.json()
    assert "name" in data
    assert "version" in data
    assert "environment" in data

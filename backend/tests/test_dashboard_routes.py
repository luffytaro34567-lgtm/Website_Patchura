"""
Tests for Admin Panel and Client Panel Dashboard Backend Endpoints.
Verifies role-based access control, real data aggregations, and status management.
"""
from __future__ import annotations

import pytest
from app.db.session import get_session_factory
from app.models.user import User, UserRole
from app.security.passwords import hash_password


@pytest.fixture
async def setup_users(client):
    """Provisions one Admin and two Clients for testing dashboard endpoints."""
    session_factory = get_session_factory()
    async with session_factory() as session:
        admin = User(
            username="admin_boss",
            email="admin_boss@bughunter.internal",
            hashed_password=hash_password("AdminPass123!"),
            role=UserRole.ADMIN.value,
            is_active=True,
        )
        client1 = User(
            username="client_one",
            email="client1@example.com",
            hashed_password=hash_password("ClientPass123!"),
            role=UserRole.CLIENT.value,
            is_active=True,
        )
        client2 = User(
            username="client_two",
            email="client2@example.com",
            hashed_password=hash_password("ClientPass123!"),
            role=UserRole.CLIENT.value,
            is_active=False,
        )
        session.add_all([admin, client1, client2])
        await session.commit()
        await session.refresh(admin)
        await session.refresh(client1)
        await session.refresh(client2)

    # Login admin
    a_res = await client.post(
        "/api/auth/login",
        json={"login": "admin_boss", "password": "AdminPass123!"},
    )
    admin_token = a_res.json()["access_token"]

    # Login client1
    c_res = await client.post(
        "/api/auth/login",
        json={"login": "client_one", "password": "ClientPass123!"},
    )
    client_token = c_res.json()["access_token"]

    return {
        "admin": admin,
        "client1": client1,
        "client2": client2,
        "admin_token": admin_token,
        "client_token": client_token,
    }


@pytest.mark.asyncio
async def test_admin_overview_requires_admin_role(client, setup_users):
    client_token = setup_users["client_token"]
    # Client attempt must fail with 403 Forbidden
    res = await client.get(
        "/api/admin/overview",
        headers={"Authorization": f"Bearer {client_token}"},
    )
    assert res.status_code == 403

    # Unauthenticated attempt must fail with 401
    res_unauth = await client.get("/api/admin/overview")
    assert res_unauth.status_code == 401


@pytest.mark.asyncio
async def test_admin_overview_returns_real_aggregates(client, setup_users):
    admin_token = setup_users["admin_token"]
    res = await client.get(
        "/api/admin/overview",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["total_users"] >= 3
    assert data["total_admins"] >= 1
    assert data["total_clients"] >= 2
    assert data["system_status"] in ("healthy", "degraded")
    assert len(data["services"]) >= 3
    assert "php2shell" in data["security_shields"]


@pytest.mark.asyncio
async def test_admin_user_filtering_and_search(client, setup_users):
    admin_token = setup_users["admin_token"]

    # Filter by role
    res = await client.get(
        "/api/admin/users?role=client",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res.status_code == 200
    users = res.json()
    for u in users:
        assert u["role"] == "client"

    # Search by username query
    res_search = await client.get(
        "/api/admin/users?q=client_one",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_search.status_code == 200
    search_results = res_search.json()
    assert len(search_results) == 1
    assert search_results[0]["username"] == "client_one"


@pytest.mark.asyncio
async def test_admin_toggle_user_status(client, setup_users):
    admin_token = setup_users["admin_token"]
    target_id = setup_users["client1"].id

    # Deactivate client1
    res = await client.patch(
        f"/api/admin/users/{target_id}/status",
        json={"is_active": False},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res.status_code == 200
    assert res.json()["is_active"] is False

    # Reactivate client1
    res_reactivate = await client.patch(
        f"/api/admin/users/{target_id}/status",
        json={"is_active": True},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_reactivate.status_code == 200
    assert res_reactivate.json()["is_active"] is True


@pytest.mark.asyncio
async def test_admin_cannot_deactivate_self(client, setup_users):
    admin_token = setup_users["admin_token"]
    admin_id = setup_users["admin"].id

    res = await client.patch(
        f"/api/admin/users/{admin_id}/status",
        json={"is_active": False},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res.status_code == 400
    assert "cannot suspend their own account" in res.json()["error"]["message"]


@pytest.mark.asyncio
async def test_client_overview_endpoint(client, setup_users):
    client_token = setup_users["client_token"]
    res = await client.get(
        "/api/client/overview",
        headers={"Authorization": f"Bearer {client_token}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["username"] == "client_one"
    assert data["active_targets_count"] == 0  # honest non-fabricated value
    assert data["scans_completed_count"] == 0
    assert data["php2shell_protected"] is True

"""
Comprehensive tests for Authentication, Client Registration, Role-Based Access Control,
Token Rotation, and Account Security.
"""
from __future__ import annotations

import pytest
from sqlalchemy import select, update
from app.db.session import get_session_factory
from app.models.user import User, UserRole
from app.security.passwords import hash_password


@pytest.mark.asyncio
async def test_client_registration_success(client):
    payload = {
        "username": "alice_sec",
        "email": "alice@example.com",
        "password": "Password123!",
        "password_confirmation": "Password123!",
    }
    response = await client.post("/api/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "alice_sec"
    assert data["email"] == "alice@example.com"
    assert data["role"] == "client"  # public registration is strictly client
    assert data["is_active"] is True
    assert "password" not in data
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_client_registration_password_mismatch(client):
    payload = {
        "username": "bob_sec",
        "email": "bob@example.com",
        "password": "Password123!",
        "password_confirmation": "DifferentPass123!",
    }
    response = await client.post("/api/auth/register", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_client_registration_weak_password(client):
    # Missing uppercase and special char
    payload = {
        "username": "charlie_sec",
        "email": "charlie@example.com",
        "password": "password123",
        "password_confirmation": "password123",
    }
    response = await client.post("/api/auth/register", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_client_registration_duplicate_username_and_email(client):
    payload = {
        "username": "david_sec",
        "email": "david@example.com",
        "password": "Password123!",
        "password_confirmation": "Password123!",
    }
    res1 = await client.post("/api/auth/register", json=payload)
    assert res1.status_code == 201

    # Duplicate username
    payload2 = {
        "username": "david_sec",
        "email": "david2@example.com",
        "password": "Password123!",
        "password_confirmation": "Password123!",
    }
    res2 = await client.post("/api/auth/register", json=payload2)
    assert res2.status_code == 409

    # Duplicate email
    payload3 = {
        "username": "david3_sec",
        "email": "david@example.com",
        "password": "Password123!",
        "password_confirmation": "Password123!",
    }
    res3 = await client.post("/api/auth/register", json=payload3)
    assert res3.status_code == 409


@pytest.mark.asyncio
async def test_authentication_login_success(client):
    reg = {
        "username": "eva_sec",
        "email": "eva@example.com",
        "password": "Password123!",
        "password_confirmation": "Password123!",
    }
    await client.post("/api/auth/register", json=reg)

    # Login with username
    login_res = await client.post(
        "/api/auth/login",
        json={"login": "eva_sec", "password": "Password123!"},
    )
    assert login_res.status_code == 200
    data = login_res.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["username"] == "eva_sec"

    # Login with email
    login_email_res = await client.post(
        "/api/auth/login",
        json={"login": "eva@example.com", "password": "Password123!"},
    )
    assert login_email_res.status_code == 200


@pytest.mark.asyncio
async def test_authentication_invalid_credentials(client):
    # Nonexistent user
    res1 = await client.post(
        "/api/auth/login",
        json={"login": "nonexistent_user", "password": "WrongPassword123!"},
    )
    assert res1.status_code == 401

    # Existing user, wrong password
    reg = {
        "username": "frank_sec",
        "email": "frank@example.com",
        "password": "Password123!",
        "password_confirmation": "Password123!",
    }
    await client.post("/api/auth/register", json=reg)

    res2 = await client.post(
        "/api/auth/login",
        json={"login": "frank_sec", "password": "WrongPassword123!"},
    )
    assert res2.status_code == 401


@pytest.mark.asyncio
async def test_disabled_account_cannot_login_or_access(client):
    reg = {
        "username": "grace_disabled",
        "email": "grace@example.com",
        "password": "Password123!",
        "password_confirmation": "Password123!",
    }
    await client.post("/api/auth/register", json=reg)

    login_res = await client.post(
        "/api/auth/login",
        json={"login": "grace_disabled", "password": "Password123!"},
    )
    access_token = login_res.json()["access_token"]

    # Now disable account in DB
    session_factory = get_session_factory()
    async with session_factory() as session:
        await session.execute(
            update(User).where(User.username == "grace_disabled").values(is_active=False)
        )
        await session.commit()

    # Try to login again
    login_disabled = await client.post(
        "/api/auth/login",
        json={"login": "grace_disabled", "password": "Password123!"},
    )
    assert login_disabled.status_code == 401

    # Try to access /api/auth/me with existing access token
    me_res = await client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert me_res.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token_rotation_and_reuse_detection(client):
    reg = {
        "username": "heidi_sec",
        "email": "heidi@example.com",
        "password": "Password123!",
        "password_confirmation": "Password123!",
    }
    await client.post("/api/auth/register", json=reg)

    login_res = await client.post(
        "/api/auth/login",
        json={"login": "heidi_sec", "password": "Password123!"},
    )
    data1 = login_res.json()
    refresh_token_1 = data1["refresh_token"]

    # Rotate refresh token
    rotate_res = await client.post(
        "/api/auth/refresh",
        json={"refresh_token": refresh_token_1},
    )
    assert rotate_res.status_code == 200
    data2 = rotate_res.json()
    refresh_token_2 = data2["refresh_token"]
    assert refresh_token_2 != refresh_token_1

    # REUSE DETECTION: Attempt to use the old refresh_token_1 again!
    reuse_res = await client.post(
        "/api/auth/refresh",
        json={"refresh_token": refresh_token_1},
    )
    assert reuse_res.status_code == 401
    assert "compromise detected" in reuse_res.json()["error"]["message"].lower()

    # Verify that refresh_token_2 was also invalidated because of family revocation
    next_res = await client.post(
        "/api/auth/refresh",
        json={"refresh_token": refresh_token_2},
    )
    assert next_res.status_code == 401


@pytest.mark.asyncio
async def test_logout_revokes_token(client):
    reg = {
        "username": "ivan_sec",
        "email": "ivan@example.com",
        "password": "Password123!",
        "password_confirmation": "Password123!",
    }
    await client.post("/api/auth/register", json=reg)

    login_res = await client.post(
        "/api/auth/login",
        json={"login": "ivan_sec", "password": "Password123!"},
    )
    data = login_res.json()
    refresh_token = data["refresh_token"]

    # Logout
    logout_res = await client.post(
        "/api/auth/logout",
        json={"refresh_token": refresh_token},
    )
    assert logout_res.status_code == 200

    # Refresh should now fail
    ref_res = await client.post(
        "/api/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert ref_res.status_code == 401


@pytest.mark.asyncio
async def test_rbac_admin_endpoint_protection(client):
    # 1. Register a client
    client_reg = {
        "username": "judy_client",
        "email": "judy@example.com",
        "password": "Password123!",
        "password_confirmation": "Password123!",
    }
    await client.post("/api/auth/register", json=client_reg)
    c_login = await client.post(
        "/api/auth/login",
        json={"login": "judy_client", "password": "Password123!"},
    )
    client_token = c_login.json()["access_token"]

    # Client attempts to access admin endpoint
    admin_access_by_client = await client.get(
        "/api/auth/admin/users",
        headers={"Authorization": f"Bearer {client_token}"},
    )
    assert admin_access_by_client.status_code == 403

    # 2. Provision an Admin directly in DB
    session_factory = get_session_factory()
    async with session_factory() as session:
        admin_user = User(
            username="super_admin",
            email="admin@example.com",
            hashed_password=hash_password("AdminSecurePass123!"),
            role=UserRole.ADMIN.value,
            is_active=True,
        )
        session.add(admin_user)
        await session.commit()

    # Admin logs in
    a_login = await client.post(
        "/api/auth/login",
        json={"login": "super_admin", "password": "AdminSecurePass123!"},
    )
    assert a_login.status_code == 200
    admin_token = a_login.json()["access_token"]

    # Admin accesses /api/auth/admin/users
    admin_access = await client.get(
        "/api/auth/admin/users",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert admin_access.status_code == 200
    users_list = admin_access.json()
    assert len(users_list) >= 2

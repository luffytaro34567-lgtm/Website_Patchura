"""
Regression and Contract Tests for End-to-End Login Flow.
Validates:
- Case-insensitive login via username or email
- Correct response envelope and JWT token generation
- Password verification and timing mitigation
- Account lockout after repeated failed attempts
- Safe error messages (no user enumeration)
- Malformed payload handling (Pydantic 422)
- Rate limiting protection (15 requests/min)
"""
from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_login_success_case_insensitive_and_contract(client: AsyncClient):
    # Register client
    reg = {
        "username": "TestSecurityUser",
        "email": "TestSecurity@domain.com",
        "password": "SecurePassword123!",
        "password_confirmation": "SecurePassword123!",
    }
    reg_res = await client.post("/api/auth/register", json=reg)
    assert reg_res.status_code == 201

    # 1. Login with uppercase username
    res1 = await client.post(
        "/api/auth/login",
        json={"login": "TESTSECURITYUSER", "password": "SecurePassword123!"},
    )
    assert res1.status_code == 200
    data1 = res1.json()
    assert "access_token" in data1
    assert "refresh_token" in data1
    assert data1["token_type"] == "bearer"
    assert data1["expires_in"] == 900
    assert data1["user"]["username"] == "TestSecurityUser"
    assert data1["user"]["email"] == "testsecurity@domain.com"
    assert data1["user"]["role"] == "client"

    # 2. Login with uppercase email
    res2 = await client.post(
        "/api/auth/login",
        json={"login": "TESTSECURITY@DOMAIN.COM", "password": "SecurePassword123!"},
    )
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["user"]["id"] == data1["user"]["id"]


@pytest.mark.asyncio
async def test_login_invalid_credentials_uniform_error(client: AsyncClient):
    # 1. Nonexistent user
    res1 = await client.post(
        "/api/auth/login",
        json={"login": "nonexistent_person", "password": "RandomPassword123!"},
    )
    assert res1.status_code == 401
    assert res1.json()["detail"] == "Invalid username/email or password."

    # 2. Existing user, incorrect password
    reg = {
        "username": "wrong_pass_user",
        "email": "wrongpass@example.com",
        "password": "ValidPassword123!",
        "password_confirmation": "ValidPassword123!",
    }
    await client.post("/api/auth/register", json=reg)

    res2 = await client.post(
        "/api/auth/login",
        json={"login": "wrong_pass_user", "password": "IncorrectPassword123!"},
    )
    assert res2.status_code == 401
    assert res2.json()["detail"] == "Invalid username/email or password."


@pytest.mark.asyncio
async def test_login_malformed_requests(client: AsyncClient):
    # Empty JSON body
    res1 = await client.post("/api/auth/login", json={})
    assert res1.status_code == 422
    assert res1.json()["success"] is False
    assert "detail" in res1.json()

    # Missing password
    res2 = await client.post("/api/auth/login", json={"login": "someuser"})
    assert res2.status_code == 422

    # Missing login
    res3 = await client.post("/api/auth/login", json={"password": "somepassword"})
    assert res3.status_code == 422


@pytest.mark.asyncio
async def test_login_account_lockout_after_five_failures(client: AsyncClient):
    reg = {
        "username": "lockout_victim",
        "email": "lockout@example.com",
        "password": "TargetPassword123!",
        "password_confirmation": "TargetPassword123!",
    }
    await client.post("/api/auth/register", json=reg)

    # 5 consecutive failures
    for attempt in range(5):
        res = await client.post(
            "/api/auth/login",
            json={"login": "lockout_victim", "password": f"BadPassword{attempt}!"},
        )
        assert res.status_code == 401

    # 6th attempt should now be locked
    res_locked = await client.post(
        "/api/auth/login",
        json={"login": "lockout_victim", "password": "TargetPassword123!"},
    )
    assert res_locked.status_code == 401
    assert "locked" in res_locked.json()["detail"].lower()


@pytest.mark.asyncio
async def test_login_rate_limiting(client: AsyncClient):
    # Attempt 15 logins (within limit)
    for i in range(15):
        res = await client.post(
            "/api/auth/login",
            json={"login": f"user_{i}", "password": "DummyPassword123!"},
        )
        assert res.status_code in (401, 422)

    # 16th attempt triggers 429 Too Many Requests
    res_blocked = await client.post(
        "/api/auth/login",
        json={"login": "user_overflow", "password": "DummyPassword123!"},
    )
    assert res_blocked.status_code == 429
    assert "rate limit" in res_blocked.json()["detail"].lower()
    assert "retry-after" in res_blocked.headers

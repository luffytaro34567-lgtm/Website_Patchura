"""
Comprehensive Tests for Website Target Registration, Ownership Verification,
Explicit Scan Authorization, and SSRF Prevention.
"""
from __future__ import annotations

import pytest
from sqlalchemy import update
from app.db.session import get_session_factory
from app.models.user import User, UserRole
from app.models.website import VerificationMethod, VerificationStatus, Website
from app.security.passwords import hash_password


@pytest.fixture
async def setup_test_client_and_admin(client):
    session_factory = get_session_factory()
    async with session_factory() as session:
        client_user = User(
            username="site_owner",
            email="owner@domain.com",
            hashed_password=hash_password("OwnerSecure123!"),
            role=UserRole.CLIENT.value,
            is_active=True,
        )
        other_client = User(
            username="other_owner",
            email="other@domain.com",
            hashed_password=hash_password("OtherSecure123!"),
            role=UserRole.CLIENT.value,
            is_active=True,
        )
        admin_user = User(
            username="admin_verifier",
            email="admin_verifier@bughunter.internal",
            hashed_password=hash_password("AdminSecure123!"),
            role=UserRole.ADMIN.value,
            is_active=True,
        )
        session.add_all([client_user, other_client, admin_user])
        await session.commit()
        await session.refresh(client_user)
        await session.refresh(other_client)
        await session.refresh(admin_user)

    # Login tokens
    c_res = await client.post(
        "/api/auth/login",
        json={"login": "site_owner", "password": "OwnerSecure123!"},
    )
    client_token = c_res.json()["access_token"]

    o_res = await client.post(
        "/api/auth/login",
        json={"login": "other_owner", "password": "OtherSecure123!"},
    )
    other_token = o_res.json()["access_token"]

    a_res = await client.post(
        "/api/auth/login",
        json={"login": "admin_verifier", "password": "AdminSecure123!"},
    )
    admin_token = a_res.json()["access_token"]

    return {
        "client_user": client_user,
        "other_client": other_client,
        "admin_user": admin_user,
        "client_token": client_token,
        "other_token": other_token,
        "admin_token": admin_token,
    }


@pytest.mark.asyncio
async def test_register_website_success(client, setup_test_client_and_admin):
    token = setup_test_client_and_admin["client_token"]
    payload = {
        "name": "Production Store",
        "target_url": "https://shop.example.com",
        "verification_method": "file",
    }
    res = await client.post(
        "/api/websites",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "Production Store"
    assert data["domain"] == "shop.example.com"
    assert data["verification_status"] == "pending"
    assert data["verification_token"].startswith("bh_verify_")
    assert data["instructions"] is not None
    assert data["instructions"]["file_path"] == "/.well-known/bughunter-verification.txt"


@pytest.mark.asyncio
async def test_ssrf_prohibited_targets_rejected(client, setup_test_client_and_admin):
    token = setup_test_client_and_admin["client_token"]

    prohibited_urls = [
        "http://localhost",
        "http://127.0.0.1",
        "http://10.0.0.1",
        "http://192.168.1.1",
        "http://169.254.169.254",  # AWS / Cloud IMDS metadata
        "http://metadata.google.internal",
        "ftp://example.com",
        "file:///etc/passwd",
    ]

    for bad_url in prohibited_urls:
        res = await client.post(
            "/api/websites",
            json={"name": "Bad Target", "target_url": bad_url},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 422, f"Expected 422 for prohibited URL: {bad_url}"


@pytest.mark.asyncio
async def test_duplicate_domain_registration_rejected(client, setup_test_client_and_admin):
    token = setup_test_client_and_admin["client_token"]
    payload = {
        "name": "My Blog",
        "target_url": "https://my-blog.example.com",
        "verification_method": "file",
    }
    res1 = await client.post("/api/websites", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert res1.status_code == 201

    # Attempt duplicate
    res2 = await client.post("/api/websites", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert res2.status_code == 409


@pytest.mark.asyncio
async def test_unverified_website_cannot_be_authorized(client, setup_test_client_and_admin):
    token = setup_test_client_and_admin["client_token"]
    # Register site (starts as pending)
    res = await client.post(
        "/api/websites",
        json={"name": "Pending App", "target_url": "https://pending-app.example.com"},
        headers={"Authorization": f"Bearer {token}"},
    )
    website_id = res.json()["id"]

    # Attempt to authorize before verification
    auth_payload = {
        "authorized_by_name": "Jane Owner",
        "authorized_by_email": "jane@example.com",
        "legal_confirmation": True,
        "allowed_scan_types": "passive,owasp_standard",
    }
    auth_res = await client.post(
        f"/api/websites/{website_id}/authorize",
        json=auth_payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert auth_res.status_code == 400
    assert "ownership must be verified" in auth_res.json()["error"]["message"].lower()


@pytest.mark.asyncio
async def test_verified_website_scan_authorization_and_revocation(client, setup_test_client_and_admin):
    token = setup_test_client_and_admin["client_token"]

    # Register
    res = await client.post(
        "/api/websites",
        json={"name": "Corporate Portal", "target_url": "https://corporate.example.com"},
        headers={"Authorization": f"Bearer {token}"},
    )
    website_id = res.json()["id"]

    # Manually mark verified in DB to simulate successful challenge
    session_factory = get_session_factory()
    async with session_factory() as session:
        await session.execute(
            update(Website)
            .where(Website.id == website_id)
            .values(verification_status=VerificationStatus.VERIFIED.value)
        )
        await session.commit()

    # Now grant explicit scan authorization
    auth_payload = {
        "authorized_by_name": "Alice Security VP",
        "authorized_by_email": "alice@corporate.example.com",
        "legal_confirmation": True,
        "allowed_scan_types": "passive,owasp_standard",
    }
    auth_res = await client.post(
        f"/api/websites/{website_id}/authorize",
        json=auth_payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert auth_res.status_code == 200
    auth_data = auth_res.json()
    assert auth_data["authorization"]["is_authorized"] is True
    assert auth_data["authorization"]["authorized_by_name"] == "Alice Security VP"

    # Revoke authorization
    revoke_res = await client.post(
        f"/api/websites/{website_id}/revoke-authorization",
        json={"revocation_reason": "Maintenance window active."},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert revoke_res.status_code == 200
    revoked_data = revoke_res.json()
    assert revoked_data["authorization"]["is_authorized"] is False
    assert revoked_data["authorization"]["is_revoked"] is True


@pytest.mark.asyncio
async def test_cross_client_isolation(client, setup_test_client_and_admin):
    client_token = setup_test_client_and_admin["client_token"]
    other_token = setup_test_client_and_admin["other_token"]

    # Client A creates a site
    res = await client.post(
        "/api/websites",
        json={"name": "Secret App", "target_url": "https://secret.example.com"},
        headers={"Authorization": f"Bearer {client_token}"},
    )
    site_id = res.json()["id"]

    # Client B attempts to view or delete Client A's site
    view_res = await client.get(
        f"/api/websites/{site_id}",
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert view_res.status_code == 403

    del_res = await client.delete(
        f"/api/websites/{site_id}",
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert del_res.status_code == 403


@pytest.mark.asyncio
async def test_admin_inspects_and_suspends_website(client, setup_test_client_and_admin):
    client_token = setup_test_client_and_admin["client_token"]
    admin_token = setup_test_client_and_admin["admin_token"]

    # Client registers site
    res = await client.post(
        "/api/websites",
        json={"name": "Suspicious Target", "target_url": "https://suspicious.example.com"},
        headers={"Authorization": f"Bearer {client_token}"},
    )
    site_id = res.json()["id"]

    # Admin lists all websites
    admin_list = await client.get(
        "/api/admin/websites",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert admin_list.status_code == 200
    assert any(w["id"] == site_id for w in admin_list.json())

    # Admin suspends website
    suspend_res = await client.patch(
        f"/api/admin/websites/{site_id}/suspend",
        json={"is_suspended": True, "suspension_reason": "Suspected phishing target."},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert suspend_res.status_code == 200
    assert suspend_res.json()["is_suspended_by_admin"] is True

    # Client attempts to verify a suspended target
    client_verify = await client.post(
        f"/api/websites/{site_id}/verify",
        headers={"Authorization": f"Bearer {client_token}"},
    )
    assert client_verify.status_code == 403
    assert "suspended" in client_verify.json()["error"]["message"].lower()

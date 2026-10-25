"""
Comprehensive tests for Vulnerability Scanning Execution, Findings Engine,
Authorization Gating, Client Isolation, Scan History, and Admin Oversight.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import update

from app.db.session import get_session_factory
from app.models.scan import FindingSeverity, Scan, ScanFinding, ScanProfile, ScanStatus
from app.models.user import User, UserRole
from app.models.website import ScanAuthorization, VerificationMethod, VerificationStatus, Website
from app.security.passwords import hash_password
from app.services.scanner.web_scanner import WebScannerEngine


@pytest.fixture
async def setup_scan_test_users(client):
    session_factory = get_session_factory()
    async with session_factory() as session:
        client_a = User(
            username="scanner_client_a",
            email="client_a@scan-test.com",
            hashed_password=hash_password("ClientSecure123!"),
            role=UserRole.CLIENT.value,
            is_active=True,
        )
        client_b = User(
            username="scanner_client_b",
            email="client_b@scan-test.com",
            hashed_password=hash_password("ClientSecure123!"),
            role=UserRole.CLIENT.value,
            is_active=True,
        )
        admin_user = User(
            username="scanner_admin",
            email="admin@scan-test.internal",
            hashed_password=hash_password("AdminSecure123!"),
            role=UserRole.ADMIN.value,
            is_active=True,
        )
        session.add_all([client_a, client_b, admin_user])
        await session.commit()
        await session.refresh(client_a)
        await session.refresh(client_b)
        await session.refresh(admin_user)

    # Login tokens
    a_res = await client.post(
        "/api/auth/login",
        json={"login": "scanner_client_a", "password": "ClientSecure123!"},
    )
    token_a = a_res.json()["access_token"]

    b_res = await client.post(
        "/api/auth/login",
        json={"login": "scanner_client_b", "password": "ClientSecure123!"},
    )
    token_b = b_res.json()["access_token"]

    adm_res = await client.post(
        "/api/auth/login",
        json={"login": "scanner_admin", "password": "AdminSecure123!"},
    )
    token_admin = adm_res.json()["access_token"]

    return {
        "client_a": client_a,
        "client_b": client_b,
        "admin": admin_user,
        "token_a": token_a,
        "token_b": token_b,
        "token_admin": token_admin,
    }


@pytest.mark.asyncio
async def test_scan_blocked_if_website_not_verified(client, setup_scan_test_users):
    token_a = setup_scan_test_users["token_a"]

    # Register unverified website
    reg_res = await client.post(
        "/api/websites",
        json={"name": "Pending Site", "target_url": "https://unverified.target.com", "verification_method": "file"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert reg_res.status_code == 201
    website_id = reg_res.json()["id"]

    # Attempt to start scan
    scan_res = await client.post(
        "/api/scans",
        json={"website_id": website_id, "profile": "standard"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert scan_res.status_code == 400
    assert "ownership is not verified" in scan_res.json()["error"]["message"].lower()


@pytest.mark.asyncio
async def test_scan_blocked_if_not_authorized(client, setup_scan_test_users):
    token_a = setup_scan_test_users["token_a"]
    user_a = setup_scan_test_users["client_a"]

    # Register website and manually verify it in DB
    session_factory = get_session_factory()
    async with session_factory() as session:
        ws = Website(
            user_id=user_a.id,
            name="Verified But Unauthorized",
            target_url="https://verified-site.com",
            domain="verified-site.com",
            verification_status=VerificationStatus.VERIFIED.value,
        )
        session.add(ws)
        await session.commit()
        await session.refresh(ws)
        website_id = ws.id

    # Attempt to start scan without authorization
    scan_res = await client.post(
        "/api/scans",
        json={"website_id": website_id, "profile": "standard"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert scan_res.status_code == 403
    assert "active scan authorization warrant" in scan_res.json()["error"]["message"].lower()


@pytest.mark.asyncio
async def test_scan_blocked_if_authorization_revoked(client, setup_scan_test_users):
    token_a = setup_scan_test_users["token_a"]
    user_a = setup_scan_test_users["client_a"]

    session_factory = get_session_factory()
    async with session_factory() as session:
        ws = Website(
            user_id=user_a.id,
            name="Revoked Auth Site",
            target_url="https://revoked.target.com",
            domain="revoked.target.com",
            verification_status=VerificationStatus.VERIFIED.value,
        )
        session.add(ws)
        await session.commit()
        await session.refresh(ws)

        auth = ScanAuthorization(
            website_id=ws.id,
            user_id=user_a.id,
            is_authorized=False,
            is_revoked=True,
            authorized_by_name="Alice Owner",
            authorized_by_email="alice@target.com",
            legal_confirmation=True,
        )
        session.add(auth)
        await session.commit()
        website_id = ws.id

    scan_res = await client.post(
        "/api/scans",
        json={"website_id": website_id, "profile": "standard"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert scan_res.status_code == 403


@pytest.mark.asyncio
async def test_scan_blocked_if_suspended_by_admin(client, setup_scan_test_users):
    token_a = setup_scan_test_users["token_a"]
    user_a = setup_scan_test_users["client_a"]

    session_factory = get_session_factory()
    async with session_factory() as session:
        ws = Website(
            user_id=user_a.id,
            name="Suspended Target",
            target_url="https://suspended.target.com",
            domain="suspended.target.com",
            verification_status=VerificationStatus.VERIFIED.value,
            is_suspended_by_admin=True,
            suspension_reason="Terms of Service abuse investigation",
        )
        session.add(ws)
        await session.commit()
        await session.refresh(ws)

        auth = ScanAuthorization(
            website_id=ws.id,
            user_id=user_a.id,
            is_authorized=True,
            authorized_by_name="Alice Owner",
            authorized_by_email="alice@target.com",
            legal_confirmation=True,
        )
        session.add(auth)
        await session.commit()
        website_id = ws.id

    scan_res = await client.post(
        "/api/scans",
        json={"website_id": website_id, "profile": "standard"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert scan_res.status_code == 403
    assert "suspended by administrator" in scan_res.json()["error"]["message"].lower()


@pytest.mark.asyncio
async def test_create_and_execute_authorized_scan(client, setup_scan_test_users):
    token_a = setup_scan_test_users["token_a"]
    user_a = setup_scan_test_users["client_a"]

    session_factory = get_session_factory()
    async with session_factory() as session:
        ws = Website(
            user_id=user_a.id,
            name="Production Application",
            target_url="https://app.secure-customer.com",
            domain="app.secure-customer.com",
            verification_status=VerificationStatus.VERIFIED.value,
        )
        session.add(ws)
        await session.commit()
        await session.refresh(ws)

        auth = ScanAuthorization(
            website_id=ws.id,
            user_id=user_a.id,
            is_authorized=True,
            authorized_by_name="Alice CTO",
            authorized_by_email="alice@secure-customer.com",
            legal_confirmation=True,
            expires_at=datetime.now(timezone.utc) + timedelta(days=90),
        )
        session.add(auth)
        await session.commit()
        website_id = ws.id

    # Create scan
    res = await client.post(
        "/api/scans",
        json={"website_id": website_id, "profile": "php_deep"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert res.status_code == 201
    scan_data = res.json()
    assert scan_data["status"] == "queued"
    assert scan_data["profile"] == "php_deep"
    assert scan_data["target_url"] == "https://app.secure-customer.com"
    scan_id = scan_data["id"]

    # Verify listing
    list_res = await client.get("/api/scans", headers={"Authorization": f"Bearer {token_a}"})
    assert list_res.status_code == 200
    assert any(s["id"] == scan_id for s in list_res.json())

    # Verify single scan details
    detail_res = await client.get(f"/api/scans/{scan_id}", headers={"Authorization": f"Bearer {token_a}"})
    assert detail_res.status_code == 200
    assert detail_res.json()["id"] == scan_id


@pytest.mark.asyncio
async def test_scan_client_isolation(client, setup_scan_test_users):
    token_a = setup_scan_test_users["token_a"]
    token_b = setup_scan_test_users["token_b"]
    user_a = setup_scan_test_users["client_a"]

    # Create scan for client A
    session_factory = get_session_factory()
    async with session_factory() as session:
        ws = Website(
            user_id=user_a.id,
            name="Isolated Site",
            target_url="https://isolated.target.com",
            domain="isolated.target.com",
            verification_status=VerificationStatus.VERIFIED.value,
        )
        session.add(ws)
        await session.commit()
        await session.refresh(ws)

        scan = Scan(
            website_id=ws.id,
            user_id=user_a.id,
            profile="standard",
            status=ScanStatus.QUEUED.value,
            target_url=ws.target_url,
            target_domain=ws.domain,
        )
        session.add(scan)
        await session.commit()
        await session.refresh(scan)
        scan_id = scan.id

    # Client B attempts to view Client A's scan
    view_res = await client.get(f"/api/scans/{scan_id}", headers={"Authorization": f"Bearer {token_b}"})
    assert view_res.status_code == 403

    # Client B attempts to cancel Client A's scan
    cancel_res = await client.post(f"/api/scans/{scan_id}/cancel", headers={"Authorization": f"Bearer {token_b}"})
    assert cancel_res.status_code == 403


@pytest.mark.asyncio
async def test_scan_cancellation_by_client_and_admin(client, setup_scan_test_users):
    token_a = setup_scan_test_users["token_a"]
    token_admin = setup_scan_test_users["token_admin"]
    user_a = setup_scan_test_users["client_a"]

    session_factory = get_session_factory()
    async with session_factory() as session:
        ws = Website(
            user_id=user_a.id,
            name="Cancel Target",
            target_url="https://cancel-test.com",
            domain="cancel-test.com",
            verification_status=VerificationStatus.VERIFIED.value,
        )
        session.add(ws)
        await session.commit()
        await session.refresh(ws)

        scan1 = Scan(
            website_id=ws.id,
            user_id=user_a.id,
            profile="standard",
            status=ScanStatus.RUNNING.value,
            target_url=ws.target_url,
            target_domain=ws.domain,
        )
        scan2 = Scan(
            website_id=ws.id,
            user_id=user_a.id,
            profile="passive",
            status=ScanStatus.RUNNING.value,
            target_url=ws.target_url,
            target_domain=ws.domain,
        )
        session.add_all([scan1, scan2])
        await session.commit()
        await session.refresh(scan1)
        await session.refresh(scan2)
        scan1_id = scan1.id
        scan2_id = scan2.id

    # Client cancels scan 1
    c_res = await client.post(f"/api/scans/{scan1_id}/cancel", headers={"Authorization": f"Bearer {token_a}"})
    assert c_res.status_code == 200
    assert c_res.json()["status"] == "cancelled"
    assert c_res.json()["cancelled_by"] == "client"

    # Admin cancels scan 2 via admin endpoint
    adm_res = await client.post(f"/api/admin/scans/{scan2_id}/cancel", headers={"Authorization": f"Bearer {token_admin}"})
    assert adm_res.status_code == 200
    assert adm_res.json()["status"] == "cancelled"
    assert adm_res.json()["cancelled_by"] == "admin"


@pytest.mark.asyncio
async def test_scan_export_json_summary(client, setup_scan_test_users):
    token_a = setup_scan_test_users["token_a"]
    user_a = setup_scan_test_users["client_a"]

    session_factory = get_session_factory()
    async with session_factory() as session:
        ws = Website(
            user_id=user_a.id,
            name="Exportable Site",
            target_url="https://export-test.com",
            domain="export-test.com",
            verification_status=VerificationStatus.VERIFIED.value,
        )
        session.add(ws)
        await session.commit()
        await session.refresh(ws)

        scan = Scan(
            website_id=ws.id,
            user_id=user_a.id,
            profile="php_deep",
            status=ScanStatus.COMPLETED.value,
            target_url=ws.target_url,
            target_domain=ws.domain,
            total_findings=2,
            high_count=1,
            critical_count=1,
            duration_seconds=3.45,
        )
        session.add(scan)
        await session.commit()
        await session.refresh(scan)

        finding = ScanFinding(
            scan_id=scan.id,
            website_id=ws.id,
            title="PHP2Shell Memory Corruption Exposure Risk",
            severity=FindingSeverity.CRITICAL.value,
            category="PHP2Shell Protection",
            description="Exposed internal PHP error handlers vulnerable to CVE-2026-109618.",
            evidence="X-Powered-By: PHP/8.1.2\nFatal error: memory fault",
            remediation="Set display_errors = Off and apply PHP2Shell security patches.",
            cwe_id="CWE-209",
            cvss_score=9.2,
            target_url=ws.target_url,
        )
        session.add(finding)
        await session.commit()
        scan_id = scan.id

    res = await client.get(f"/api/scans/{scan_id}/export", headers={"Authorization": f"Bearer {token_a}"})
    assert res.status_code == 200
    data = res.json()
    assert data["scan_id"] == scan_id
    assert data["total_findings"] == 2
    assert data["severity_breakdown"]["critical"] == 1
    assert data["severity_breakdown"]["high"] == 1
    assert len(data["findings"]) == 1
    assert data["findings"][0]["title"] == "PHP2Shell Memory Corruption Exposure Risk"
    assert data["php2shell_shield_evaluated"] is True

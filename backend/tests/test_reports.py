"""
Comprehensive tests for Paid Detailed Vulnerability Reports, Entitlement Gates,
Order Checkout Workflows, Report Document Generation, and Access Logs.
"""
from __future__ import annotations

import pytest
from app.db.session import get_session_factory
from app.models.scan import FindingSeverity, Scan, ScanFinding, ScanStatus
from app.models.user import User, UserRole
from app.models.website import VerificationStatus, Website
from app.security.passwords import hash_password


@pytest.fixture
async def setup_report_test_env(client):
    session_factory = get_session_factory()
    async with session_factory() as session:
        client_a = User(
            username="rep_client_a",
            email="rep_a@domain.com",
            hashed_password=hash_password("ClientSecure123!"),
            role=UserRole.CLIENT.value,
            is_active=True,
        )
        client_b = User(
            username="rep_client_b",
            email="rep_b@domain.com",
            hashed_password=hash_password("ClientSecure123!"),
            role=UserRole.CLIENT.value,
            is_active=True,
        )
        admin = User(
            username="rep_admin",
            email="rep_admin@bughunter.internal",
            hashed_password=hash_password("AdminSecure123!"),
            role=UserRole.ADMIN.value,
            is_active=True,
        )
        session.add_all([client_a, client_b, admin])
        await session.commit()
        await session.refresh(client_a)
        await session.refresh(client_b)
        await session.refresh(admin)

        # Website and completed scan for client_a
        ws = Website(
            user_id=client_a.id,
            name="Production Portal",
            target_url="https://portal.mycompany.com",
            domain="portal.mycompany.com",
            verification_status=VerificationStatus.VERIFIED.value,
        )
        session.add(ws)
        await session.commit()
        await session.refresh(ws)

        scan = Scan(
            website_id=ws.id,
            user_id=client_a.id,
            profile="php_deep",
            status=ScanStatus.COMPLETED.value,
            target_url=ws.target_url,
            target_domain=ws.domain,
            total_findings=2,
            critical_count=1,
            high_count=1,
            duration_seconds=4.2,
        )
        session.add(scan)
        await session.commit()
        await session.refresh(scan)

        f1 = ScanFinding(
            scan_id=scan.id,
            website_id=ws.id,
            title="PHP2Shell Unhandled Memory Fault Leak (CVE-2026-109618)",
            severity=FindingSeverity.CRITICAL.value,
            category="PHP2Shell Protection",
            description="Exposed internal PHP error handlers vulnerable to RCE.",
            evidence="X-Powered-By: PHP/8.1.0\nFatal error: memory fault in zend_error_cb",
            remediation="Disable display_errors and apply security patches.",
            cwe_id="CWE-209",
            cvss_score=9.2,
            target_url=ws.target_url,
        )
        f2 = ScanFinding(
            scan_id=scan.id,
            website_id=ws.id,
            title="Missing Content-Security-Policy (CSP)",
            severity=FindingSeverity.HIGH.value,
            category="Security Headers",
            description="No CSP header configured.",
            evidence="Content-Security-Policy: [NOT PRESENT]",
            remediation="Add strict CSP header.",
            cwe_id="CWE-693",
            cvss_score=7.5,
            target_url=ws.target_url,
        )
        session.add_all([f1, f2])
        await session.commit()

    # Logins
    a_res = await client.post("/api/auth/login", json={"login": "rep_client_a", "password": "ClientSecure123!"})
    token_a = a_res.json()["access_token"]

    b_res = await client.post("/api/auth/login", json={"login": "rep_client_b", "password": "ClientSecure123!"})
    token_b = b_res.json()["access_token"]

    adm_res = await client.post("/api/auth/login", json={"login": "rep_admin", "password": "AdminSecure123!"})
    token_admin = adm_res.json()["access_token"]

    return {
        "client_a": client_a,
        "client_b": client_b,
        "admin": admin,
        "scan": scan,
        "token_a": token_a,
        "token_b": token_b,
        "token_admin": token_admin,
    }


@pytest.mark.asyncio
async def test_free_summary_allowed_but_detailed_report_denied_without_entitlement(client, setup_report_test_env):
    token_a = setup_report_test_env["token_a"]
    scan = setup_report_test_env["scan"]

    # 1. Free scan status check allows viewing basic summary
    status_res = await client.get(f"/api/reports/scan/{scan.id}/status", headers={"Authorization": f"Bearer {token_a}"})
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert status_data["has_entitlement"] is False
    assert status_data["can_purchase"] is True
    assert status_data["pricing"]["price"] == 49.0

    # 2. Free scan details endpoint allows viewing basic count metrics
    free_res = await client.get(f"/api/scans/{scan.id}", headers={"Authorization": f"Bearer {token_a}"})
    assert free_res.status_code == 200
    assert free_res.json()["total_findings"] == 2

    # 3. Accessing Detailed Report endpoint is strictly DENIED (403 Forbidden)
    denied_res = await client.get(f"/api/reports/scan/{scan.id}/details", headers={"Authorization": f"Bearer {token_a}"})
    assert denied_res.status_code == 403
    assert "entitlement" in denied_res.json()["error"]["message"].lower()


@pytest.mark.asyncio
async def test_order_creation_and_successful_checkout_grants_entitlement(client, setup_report_test_env):
    token_a = setup_report_test_env["token_a"]
    scan = setup_report_test_env["scan"]

    # 1. Initiate purchase order
    order_res = await client.post(
        f"/api/reports/scan/{scan.id}/order",
        json={"scan_id": scan.id, "payment_method": "dev_checkout"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert order_res.status_code == 201
    order_data = order_res.json()
    assert order_data["status"] == "pending"
    assert order_data["amount"] == 49.0
    order_id = order_data["id"]

    # 2. Complete order with simulated success
    complete_res = await client.post(
        f"/api/reports/orders/{order_id}/complete",
        json={"simulate_status": "completed"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert complete_res.status_code == 200
    assert complete_res.json()["status"] == "completed"

    # 3. Verify status endpoint now confirms active entitlement
    status_res = await client.get(f"/api/reports/scan/{scan.id}/status", headers={"Authorization": f"Bearer {token_a}"})
    assert status_res.status_code == 200
    assert status_res.json()["has_entitlement"] is True

    # 4. Accessing Detailed Report endpoint is now GRANTED
    doc_res = await client.get(f"/api/reports/scan/{scan.id}/details", headers={"Authorization": f"Bearer {token_a}"})
    assert doc_res.status_code == 200
    doc_data = doc_res.json()
    assert doc_data["scan_id"] == scan.id
    assert doc_data["overall_risk_score"] > 0.0
    assert doc_data["has_php2shell_finding"] is True
    assert "PHP2Shell" in doc_data["php2shell_posture"]
    assert len(doc_data["findings"]) == 2
    assert "html_content" in doc_data


@pytest.mark.asyncio
async def test_order_failure_simulation_does_not_grant_entitlement(client, setup_report_test_env):
    token_a = setup_report_test_env["token_a"]
    scan = setup_report_test_env["scan"]

    # 1. Create order
    order_res = await client.post(
        f"/api/reports/scan/{scan.id}/order",
        json={"scan_id": scan.id, "payment_method": "dev_checkout"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    order_id = order_res.json()["id"]

    # 2. Simulate failed payment
    fail_res = await client.post(
        f"/api/reports/orders/{order_id}/complete",
        json={"simulate_status": "failed"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert fail_res.status_code == 200
    assert fail_res.json()["status"] == "failed"

    # 3. Access to detailed report must still be 403 Forbidden
    doc_res = await client.get(f"/api/reports/scan/{scan.id}/details", headers={"Authorization": f"Bearer {token_a}"})
    assert doc_res.status_code == 403


@pytest.mark.asyncio
async def test_report_client_isolation(client, setup_report_test_env):
    token_b = setup_report_test_env["token_b"]
    scan = setup_report_test_env["scan"]

    # Client B attempts to order Client A's report
    order_res = await client.post(
        f"/api/reports/scan/{scan.id}/order",
        json={"scan_id": scan.id},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert order_res.status_code == 403

    # Client B attempts to check report status
    status_res = await client.get(f"/api/reports/scan/{scan.id}/status", headers={"Authorization": f"Bearer {token_b}"})
    assert status_res.status_code == 403


@pytest.mark.asyncio
async def test_admin_manual_grant_and_order_inspection(client, setup_report_test_env):
    token_admin = setup_report_test_env["token_admin"]
    token_a = setup_report_test_env["token_a"]
    scan = setup_report_test_env["scan"]

    # Admin manually grants entitlement
    grant_res = await client.post(
        "/api/reports/admin/grant-entitlement",
        json={"scan_id": scan.id, "reason": "Authorized VIP support grant"},
        headers={"Authorization": f"Bearer {token_admin}"},
    )
    assert grant_res.status_code == 200
    assert grant_res.json()["is_active"] is True

    # Client A can now immediately access detailed report
    doc_res = await client.get(f"/api/reports/scan/{scan.id}/details", headers={"Authorization": f"Bearer {token_a}"})
    assert doc_res.status_code == 200

    # Admin can list all orders
    orders_res = await client.get("/api/reports/admin/orders", headers={"Authorization": f"Bearer {token_admin}"})
    assert orders_res.status_code == 200

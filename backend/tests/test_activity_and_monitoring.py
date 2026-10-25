"""
Tests for Centralized Activity Monitoring, Security Alerts, Audit Logs, and Client Administration.
Prompt 11: Real event ingestion, alert triage, timeframes, and administrative controls.
"""
from __future__ import annotations

import pytest
from datetime import datetime, timedelta, timezone
from app.db.session import get_session_factory
from app.models.user import User, UserRole
from app.models.activity import ActivityLog, SecurityAlert, AlertStatus, AlertSeverity, EventOutcome, EventSeverity
from app.security.passwords import hash_password
from app.services.activity.activity_service import ActivityService


@pytest.fixture
async def setup_activity_env(client):
    """Provisions an Admin and two Clients with initialized activity events."""
    session_factory = get_session_factory()
    async with session_factory() as session:
        admin = User(
            username="activity_admin",
            email="activity_admin@bughunter.internal",
            hashed_password=hash_password("AdminPass123!"),
            role=UserRole.ADMIN.value,
            is_active=True,
            account_status="active",
        )
        client_user = User(
            username="target_client",
            email="target_client@example.com",
            hashed_password=hash_password("ClientPass123!"),
            role=UserRole.CLIENT.value,
            is_active=True,
            account_status="active",
        )
        session.add_all([admin, client_user])
        await session.commit()
        await session.refresh(admin)
        await session.refresh(client_user)

        # Pre-seed some activity events
        log1 = ActivityLog(
            event_category="authentication",
            event_name="user_login_success",
            actor_type="user",
            actor_id=client_user.id,
            actor_email=client_user.email,
            outcome=EventOutcome.SUCCESS.value,
            severity=EventSeverity.INFO.value,
            source_module="auth",
        )
        log2 = ActivityLog(
            event_category="vulnerability_scanning",
            event_name="scan_completed",
            actor_type="system",
            target_identifier="client-domain.com",
            outcome=EventOutcome.SUCCESS.value,
            severity=EventSeverity.CRITICAL.value,
            source_module="scans",
            requires_review=True,
        )
        alert1 = SecurityAlert(
            alert_type="php2shell_high_risk_detected",
            title="PHP2Shell Memory Corruption detected on client-domain.com",
            description="Verbose PHP error handler leaks memory under recursive errors.",
            severity=AlertSeverity.CRITICAL.value,
            status=AlertStatus.OPEN.value,
            source_module="scanner",
            cve_id="CVE-2026-109618, CVE-2026-109619",
        )
        session.add_all([log1, log2, alert1])
        await session.commit()

    # Login admin
    a_res = await client.post(
        "/api/auth/login",
        json={"login": "activity_admin", "password": "AdminPass123!"},
    )
    admin_token = a_res.json()["access_token"]

    # Login client
    c_res = await client.post(
        "/api/auth/login",
        json={"login": "target_client", "password": "ClientPass123!"},
    )
    client_token = c_res.json()["access_token"]

    return {
        "admin_token": admin_token,
        "client_token": client_token,
        "admin_id": admin.id,
        "client_id": client_user.id,
    }


@pytest.mark.asyncio
async def test_admin_activity_metrics_role_restriction(client, setup_activity_env):
    """Assert regular clients cannot access administrative activity metrics (HTTP 403)."""
    c_token = setup_activity_env["client_token"]
    res = await client.get(
        "/api/admin/activity/metrics",
        headers={"Authorization": f"Bearer {c_token}"},
    )
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_activity_metrics_timeframes(client, setup_activity_env):
    """Verify admin retrieves real database metrics across 24h, 7d, 30d, and custom timeframes."""
    a_token = setup_activity_env["admin_token"]

    # Test 24h
    res_24 = await client.get(
        "/api/admin/activity/metrics?timeframe=24h",
        headers={"Authorization": f"Bearer {a_token}"},
    )
    assert res_24.status_code == 200
    data_24 = res_24.json()
    assert data_24["timeframe"] == "24h"
    assert data_24["total_clients"] >= 1
    assert data_24["open_security_alerts"] >= 1
    assert data_24["php2shell_alerts_count"] >= 1

    # Test 7d
    res_7d = await client.get(
        "/api/admin/activity/metrics?timeframe=7d",
        headers={"Authorization": f"Bearer {a_token}"},
    )
    assert res_7d.status_code == 200
    assert res_7d.json()["timeframe"] == "7d"


@pytest.mark.asyncio
async def test_activity_timeline_filtering(client, setup_activity_env):
    """Verify searching and filtering activity timeline by category, severity, and review flag."""
    a_token = setup_activity_env["admin_token"]

    # All timeline
    res = await client.get(
        "/api/admin/activity/timeline",
        headers={"Authorization": f"Bearer {a_token}"},
    )
    assert res.status_code == 200
    events = res.json()
    assert len(events) >= 2

    # Filter by category
    res_cat = await client.get(
        "/api/admin/activity/timeline?category=authentication",
        headers={"Authorization": f"Bearer {a_token}"},
    )
    assert res_cat.status_code == 200
    for e in res_cat.json():
        assert e["event_category"] == "authentication"

    # Filter requires review
    res_rev = await client.get(
        "/api/admin/activity/timeline?requires_review=true",
        headers={"Authorization": f"Bearer {a_token}"},
    )
    assert res_rev.status_code == 200
    for e in res_rev.json():
        assert e["requires_review"] is True


@pytest.mark.asyncio
async def test_review_activity_log(client, setup_activity_env):
    """Verify admin can mark an activity event as reviewed."""
    a_token = setup_activity_env["admin_token"]

    # Get an unreviewed event
    res = await client.get(
        "/api/admin/activity/timeline?requires_review=true",
        headers={"Authorization": f"Bearer {a_token}"},
    )
    unreviewed = res.json()[0]

    # Review it
    review_res = await client.post(
        f"/api/admin/activity/{unreviewed['id']}/review",
        json={"is_reviewed": True},
        headers={"Authorization": f"Bearer {a_token}"},
    )
    assert review_res.status_code == 200
    assert review_res.json()["is_reviewed"] is True
    assert review_res.json()["reviewed_by_admin_id"] is not None


@pytest.mark.asyncio
async def test_security_alerts_triage_flow(client, setup_activity_env):
    """Verify security alert listing and triage lifecycle (acknowledged -> resolved)."""
    a_token = setup_activity_env["admin_token"]

    # List alerts
    alerts_res = await client.get(
        "/api/admin/alerts?status=open",
        headers={"Authorization": f"Bearer {a_token}"},
    )
    assert alerts_res.status_code == 200
    alerts = alerts_res.json()
    assert len(alerts) >= 1
    alert_id = alerts[0]["id"]
    assert "CVE-2026-109618" in alerts[0]["cve_id"]

    # Triage: Acknowledge
    ack_res = await client.patch(
        f"/api/admin/alerts/{alert_id}/triage",
        json={"status": "acknowledged", "resolution_notes": "Investigating PHP2Shell memory leak."},
        headers={"Authorization": f"Bearer {a_token}"},
    )
    assert ack_res.status_code == 200
    assert ack_res.json()["status"] == "acknowledged"

    # Triage: Resolve
    res_res = await client.patch(
        f"/api/admin/alerts/{alert_id}/triage",
        json={"status": "resolved", "resolution_notes": "Applied AST hardened error handler patch."},
        headers={"Authorization": f"Bearer {a_token}"},
    )
    assert res_res.status_code == 200
    assert res_res.json()["status"] == "resolved"
    assert res_res.json()["resolved_at"] is not None


@pytest.mark.asyncio
async def test_client_extended_profile(client, setup_activity_env):
    """Verify admin can retrieve extended client profile with linked entity counts."""
    a_token = setup_activity_env["admin_token"]
    c_id = setup_activity_env["client_id"]

    res = await client.get(
        f"/api/admin/clients/{c_id}/profile",
        headers={"Authorization": f"Bearer {a_token}"},
    )
    assert res.status_code == 200
    prof = res.json()
    assert prof["id"] == c_id
    assert prof["username"] == "target_client"
    assert "websites_count" in prof
    assert "scans_count" in prof
    assert "active_plan" in prof


@pytest.mark.asyncio
async def test_client_account_status_controls(client, setup_activity_env):
    """Verify admin can suspend and terminate a client, asserting self-suspension lockout defense."""
    a_token = setup_activity_env["admin_token"]
    a_id = setup_activity_env["admin_id"]
    c_id = setup_activity_env["client_id"]

    # Admin cannot suspend themselves
    self_res = await client.post(
        f"/api/admin/clients/{a_id}/set-status",
        json={"account_status": "suspended", "reason": "Accidental self lock"},
        headers={"Authorization": f"Bearer {a_token}"},
    )
    assert self_res.status_code == 400

    # Suspend client
    susp_res = await client.post(
        f"/api/admin/clients/{c_id}/set-status",
        json={"account_status": "suspended", "reason": "Terms of service audit"},
        headers={"Authorization": f"Bearer {a_token}"},
    )
    assert susp_res.status_code == 200
    assert susp_res.json()["is_active"] is False

    # Reactivate client
    act_res = await client.post(
        f"/api/admin/clients/{c_id}/set-status",
        json={"account_status": "active", "reason": "Verification completed"},
        headers={"Authorization": f"Bearer {a_token}"},
    )
    assert act_res.status_code == 200
    assert act_res.json()["is_active"] is True


@pytest.mark.asyncio
async def test_client_account_unlock_and_force_reset(client, setup_activity_env):
    """Verify unlocking client and issuing 24h forced password reset token."""
    a_token = setup_activity_env["admin_token"]
    c_id = setup_activity_env["client_id"]

    # Unlock client
    unlock_res = await client.post(
        f"/api/admin/clients/{c_id}/unlock",
        headers={"Authorization": f"Bearer {a_token}"},
    )
    assert unlock_res.status_code == 200

    # Force password reset
    reset_res = await client.post(
        f"/api/admin/clients/{c_id}/force-reset",
        headers={"Authorization": f"Bearer {a_token}"},
    )
    assert reset_res.status_code == 200
    body = reset_res.json()
    assert body["success"] is True
    assert len(body["recovery_token"]) > 10
    assert body["expires_in_hours"] == 24


@pytest.mark.asyncio
async def test_background_jobs_status(client, setup_activity_env):
    """Verify monitoring operational status of internal engines and background workers."""
    a_token = setup_activity_env["admin_token"]
    res = await client.get(
        "/api/admin/system/jobs-status",
        headers={"Authorization": f"Bearer {a_token}"},
    )
    assert res.status_code == 200
    jobs = res.json()
    assert len(jobs) >= 5
    job_names = [j["name"] for j in jobs]
    assert any("Scanner" in name for name in job_names)
    assert any("PHP2Shell" in name for name in job_names)

"""
BugHunter AI — Comprehensive End-to-End Integration & Security Audit Test Suite.
Prompt 12: Production readiness, cross-module interoperability, and defense-in-depth verification.
"""
from __future__ import annotations

import pytest
from datetime import datetime, timedelta, timezone
from app.db.session import get_session_factory
from app.models.user import User, UserRole
from app.models.website import Website, ScanAuthorization, VerificationStatus
from app.models.scan import Scan, ScanProfile, ScanStatus, FindingSeverity, ScanFinding
from app.models.report import ReportOrder, ReportEntitlement, OrderStatus
from app.models.remediation import RemediationSession, RemediationStatus, ApprovalStatus, TestStatus
from app.models.deployment import DeploymentRecord, DeploymentEnvironment, DeploymentStatus
from app.models.lead import DiscoveryCampaign, Lead, OutreachDraft, SuppressionList, OutreachStatus
from app.models.activity import ActivityLog, SecurityAlert, AlertStatus
from app.security.passwords import hash_password


@pytest.fixture
async def setup_e2e_platform(client):
    """Initializes platform with Admin, Client, and verified baseline state."""
    session_factory = get_session_factory()
    async with session_factory() as session:
        admin = User(
            username="sec_director",
            email="director@bughunter.internal",
            hashed_password=hash_password("SuperSecretAdmin123!"),
            role=UserRole.ADMIN.value,
            is_active=True,
            account_status="active",
        )
        client_user = User(
            username="retail_owner",
            email="owner@retailcorp.io",
            hashed_password=hash_password("RetailCorpSecure2026!"),
            role=UserRole.CLIENT.value,
            is_active=True,
            account_status="active",
        )
        session.add_all([admin, client_user])
        await session.commit()
        await session.refresh(admin)
        await session.refresh(client_user)

    # Login both users
    admin_login = await client.post(
        "/api/auth/login",
        json={"login": "sec_director", "password": "SuperSecretAdmin123!"},
    )
    admin_token = admin_login.json()["access_token"]

    client_login = await client.post(
        "/api/auth/login",
        json={"login": "retail_owner", "password": "RetailCorpSecure2026!"},
    )
    client_token = client_login.json()["access_token"]

    return {
        "admin_token": admin_token,
        "client_token": client_token,
        "admin_id": admin.id,
        "client_id": client_user.id,
    }


@pytest.mark.asyncio
async def test_complete_platform_lifecycle_e2e(client, setup_e2e_platform):
    """
    Executes a complete 12-stage end-to-end integration flow across all modules:
    Auth -> Website -> Verification -> Authorization -> Scan -> Findings (PHP2Shell) ->
    Report Entitlement -> AST AI Fix -> Staging Rollout -> Client Finder -> Opt-Out -> Centralized Monitoring.
    """
    c_token = setup_e2e_platform["client_token"]
    a_token = setup_e2e_platform["admin_token"]
    c_id = setup_e2e_platform["client_id"]

    # ── Stage 1: Auth Lifecycle & Password Recovery ───────────────────────────
    # Request password recovery
    rec_res = await client.post(
        "/api/auth/recover-password",
        json={"email": "owner@retailcorp.io"},
    )
    assert rec_res.status_code == 200
    rec_token = rec_res.json()["recovery_token"]
    assert len(rec_token) > 10

    # Reset password with token
    reset_res = await client.post(
        "/api/auth/reset-password",
        json={
            "token": rec_token,
            "new_password": "RetailCorpNewSecurePass2026!",
            "new_password_confirmation": "RetailCorpNewSecurePass2026!",
        },
    )
    assert reset_res.status_code == 200

    # Re-authenticate with new password
    reauth_res = await client.post(
        "/api/auth/login",
        json={"login": "retail_owner", "password": "RetailCorpNewSecurePass2026!"},
    )
    assert reauth_res.status_code == 200
    c_token = reauth_res.json()["access_token"]

    # ── Stage 2: Website Registration & Three-Challenge Verification ──────────
    reg_site_res = await client.post(
        "/api/websites",
        json={
            "target_url": "https://store.retailcorp.io",
            "verification_method": "dns_txt",
        },
        headers={"Authorization": f"Bearer {c_token}"},
    )
    assert reg_site_res.status_code == 201
    site_data = reg_site_res.json()
    website_id = site_data["id"]
    assert site_data["domain"] == "store.retailcorp.io"

    # Simulate completed DNS TXT verification directly in DB
    session_factory = get_session_factory()
    async with session_factory() as session:
        site = await session.get(Website, website_id)
        site.verification_status = VerificationStatus.VERIFIED.value
        site.verified_at = datetime.now(timezone.utc)
        await session.commit()

    # ── Stage 3: Explicit 90-Day Legal Scan Authorization Warrant ──────────────
    auth_res = await client.post(
        f"/api/websites/{website_id}/authorize",
        json={
            "signee_name": "Jane Doe",
            "signee_email": "owner@retailcorp.io",
            "signee_title": "Chief Technology Officer",
            "authorization_scope": "Full assessment covering PHP2Shell and application vulnerabilities",
            "confirm_legal_authority": True,
            "confirm_safe_scan_understanding": True,
        },
        headers={"Authorization": f"Bearer {c_token}"},
    )
    assert auth_res.status_code == 200
    assert auth_res.json()["is_authorized"] is True

    # ── Stage 4: Launch Vulnerability Scan with PHP2Shell Protection ───────────
    scan_res = await client.post(
        "/api/scans",
        json={
            "website_id": website_id,
            "profile": "php_deep",
        },
        headers={"Authorization": f"Bearer {c_token}"},
    )
    assert scan_res.status_code == 201
    scan_id = scan_res.json()["id"]

    # Populate scan findings including PHP2Shell zero-day vulnerability in DB
    async with session_factory() as session:
        scan_record = await session.get(Scan, scan_id)
        scan_record.status = ScanStatus.COMPLETED.value
        scan_record.progress_percent = 100
        scan_record.completed_at = datetime.now(timezone.utc)
        scan_record.total_findings = 2
        scan_record.critical_count = 1
        scan_record.high_count = 1

        f1 = ScanFinding(
            scan_id=scan_id,
            rule_id="PHP2SHELL-001",
            title="Critical PHP2Shell Risk: Custom Error Handler Memory Corruption (CVE-2026-109618)",
            category="PHP2Shell Protection",
            severity=FindingSeverity.CRITICAL.value,
            description="Unhandled error display leaking heap buffer during recursive execution.",
            target_component="error_handler.php",
            concrete_proof="display_errors = 1; stack dump detected on /index.php",
            remediation="Apply AST safe re-entrancy error handling wrapper.",
        )
        f2 = ScanFinding(
            scan_id=scan_id,
            rule_id="SEC-HDR-001",
            title="Missing Content-Security-Policy Header",
            category="Security Headers",
            severity=FindingSeverity.HIGH.value,
            description="Missing CSP header exposes application to XSS attacks.",
            target_component="nginx.conf",
            concrete_proof="HTTP response lacked Content-Security-Policy header",
            remediation="Configure Content-Security-Policy in web server.",
        )
        session.add_all([f1, f2])
        await session.commit()
        await session.refresh(f1)
        finding_id = f1.id

    # ── Stage 5: Free Finding Counts vs. Paid Report Entitlement ───────────────
    # Basic finding counts are free
    counts_res = await client.get(
        f"/api/scans/{scan_id}",
        headers={"Authorization": f"Bearer {c_token}"},
    )
    assert counts_res.status_code == 200
    assert counts_res.json()["critical_count"] == 1

    # Order detailed report (purchase in minor-unit cents)
    order_res = await client.post(
        f"/api/reports/{scan_id}/order",
        json={"payment_method_id": "pm_sandbox_card"},
        headers={"Authorization": f"Bearer {c_token}"},
    )
    assert order_res.status_code == 200
    assert order_res.json()["is_entitled"] is True

    # Access full printable HTML report document
    doc_res = await client.get(
        f"/api/reports/{scan_id}/printable",
        headers={"Authorization": f"Bearer {c_token}"},
    )
    assert doc_res.status_code == 200
    assert "CVE-2026-109618" in doc_res.text

    # ── Stage 6: AI-Assisted AST Remediation & Isolated Sandbox Testing ───────
    fix_res = await client.post(
        "/api/remediations",
        json={
            "finding_id": finding_id,
            "target_filename": "error_handler.php",
            "vulnerable_code_snippet": "<?php\nini_set('display_errors', '1');\nfunction myErrorHandler($errno, $errstr) {\n    echo $errstr;\n}\n?>",
            "language": "php",
            "developer_instructions": "Harden error handler against PHP2Shell heap corruption.",
        },
        headers={"Authorization": f"Bearer {c_token}"},
    )
    assert fix_res.status_code == 201
    session_id = fix_res.json()["id"]

    # Verify 4-stage isolated sandbox tests passed
    assert fix_res.json()["test_status"] == "passed"
    assert "PHP2Shell" in fix_res.json()["explanation"]

    # Human-in-the-loop explicit client approval
    appr_res = await client.post(
        f"/api/remediations/{session_id}/approve",
        json={"notes": "Reviewed unified diff, sandbox checks passed."},
        headers={"Authorization": f"Bearer {c_token}"},
    )
    assert appr_res.status_code == 200
    assert appr_res.json()["approval_status"] == "approved"

    # ── Stage 7: DevSecOps Git PR & Staging Rollout ───────────────────────────
    # Connect Git repository
    repo_res = await client.post(
        "/api/deployments/repositories",
        json={
            "provider": "github",
            "repo_name": "retailcorp/storefront",
            "access_token": "ghp_mockPersonalAccessTokenForTest12345",
            "default_branch": "main",
        },
        headers={"Authorization": f"Bearer {c_token}"},
    )
    assert repo_res.status_code == 201
    repo_id = repo_res.json()["id"]

    # Dispatch PR to isolated feature branch
    pr_res = await client.post(
        f"/api/deployments/sessions/{session_id}/create-pr",
        json={"repository_id": repo_id},
        headers={"Authorization": f"Bearer {c_token}"},
    )
    assert pr_res.status_code == 200
    assert "pull_request_url" in pr_res.json()

    # Deploy to staging environment
    staging_res = await client.post(
        f"/api/deployments/sessions/{session_id}/deploy-staging",
        json={"repository_id": repo_id},
        headers={"Authorization": f"Bearer {c_token}"},
    )
    assert staging_res.status_code == 200
    assert staging_res.json()["environment"] == "staging"

    # ── Stage 8: Client Finder Automation & Compliant Outreach ────────────────
    # Create discovery campaign (Admin only)
    camp_res = await client.post(
        "/api/leads/campaigns",
        json={
            "name": "PHP2Shell Vulnerability Awareness Q4",
            "target_technology": "PHP / Laravel / WordPress",
            "target_industry": "E-Commerce",
            "search_query": "php unhandled exception display error",
            "rate_limit_per_day": 25,
        },
        headers={"Authorization": f"Bearer {a_token}"},
    )
    assert camp_res.status_code == 201
    campaign_id = camp_res.json()["id"]

    # Execute discovery run
    disc_res = await client.post(
        f"/api/leads/campaigns/{campaign_id}/run",
        json={},
        headers={"Authorization": f"Bearer {a_token}"},
    )
    assert disc_res.status_code == 200
    leads = disc_res.json()
    assert len(leads) >= 1
    test_lead_id = leads[0]["id"]

    # Draft compliant outreach
    draft_res = await client.post(
        f"/api/leads/{test_lead_id}/draft-outreach",
        json={},
        headers={"Authorization": f"Bearer {a_token}"},
    )
    assert draft_res.status_code == 200
    draft_id = draft_res.json()["id"]
    # Check compliance footer & token presence
    assert "opt-out" in draft_res.json()["body"]
    assert "BugHunter AI" in draft_res.json()["body"]

    # Send outreach
    send_res = await client.post(
        f"/api/leads/outreach/{draft_id}/send",
        json={},
        headers={"Authorization": f"Bearer {a_token}"},
    )
    assert send_res.status_code == 200
    assert send_res.json()["status"] == "sent"

    # Public unsubscribe opt-out
    opt_res = await client.post(
        "/api/leads/opt-out",
        json={"token": "test_optout_token", "reason": "No longer interested"},
    )
    assert opt_res.status_code == 200
    assert opt_res.json()["success"] is True

    # ── Stage 9: Centralized Activity Center & Security Alert Triage ──────────
    # Check live activity metrics
    metrics_res = await client.get(
        "/api/admin/activity/metrics?timeframe=24h",
        headers={"Authorization": f"Bearer {a_token}"},
    )
    assert metrics_res.status_code == 200
    metrics = metrics_res.json()
    assert metrics["total_clients"] >= 1
    assert metrics["scans_completed"] >= 1
    assert metrics["remediations_approved"] >= 1

    # Check activity timeline
    timeline_res = await client.get(
        "/api/admin/activity/timeline?limit=50",
        headers={"Authorization": f"Bearer {a_token}"},
    )
    assert timeline_res.status_code == 200
    assert len(timeline_res.json()) >= 3

    # Check background worker health
    jobs_res = await client.get(
        "/api/admin/system/jobs-status",
        headers={"Authorization": f"Bearer {a_token}"},
    )
    assert jobs_res.status_code == 200
    assert len(jobs_res.json()) >= 6

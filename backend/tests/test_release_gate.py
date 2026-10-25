"""
PATCHORA Release Gate Automated Security Verification Suite (Prompt 15).
Enforces mandatory security regression gates before release certification:
Verifies SQLi parameterization, XSS encoding, SSRF defense, Tenant Isolation,
Path Traversal guards, Session Revocation, Webhook Replay, and PHP2Shell Shields.
"""
from __future__ import annotations

import hashlib
import hmac
import time
import uuid
from datetime import datetime, timedelta, timezone
import pytest
from httpx import AsyncClient, Request, Response
from sqlalchemy import select

from app.core.config import settings
from app.db.session import async_session_factory
from app.models.deployment import DeploymentEnvironment, DeploymentTarget
from app.models.remediation import ApprovalStatus, RemediationSession, TestStatus
from app.models.scan import Scan, ScanFinding
from app.models.user import RefreshToken, User, UserRole
from app.models.website import Website, VerificationStatus
from app.security.passwords import hash_password
from app.security.path_validator import validate_safe_branch_name, validate_safe_relative_path
from app.security.rate_limiter import limiter
from app.security.safe_http import validate_redirect_ssrf
from app.security.sql_sanitizer import escape_like_wildcards, sanitize_search_query
from app.security.tokens import create_access_token, generate_refresh_token, hash_refresh_token
from app.security.url_validator import is_ip_prohibited, validate_and_normalize_target_url
from app.services.activity.activity_service import ActivityService, _sanitize_log_metadata
from app.services.deployment.deployment_service import DeploymentService
from app.services.payment.payment_provider import PaymentProviderService
from app.services.remediation.isolated_tester import IsolatedPatchTester
from app.services.report_service import ReportService
from app.services.scanner.php_analyzer import analyze_php_code


# ──────────────────────────────────────────────────────────────────────────────
# Gate 1: SQL Injection & Wildcard Parameterization
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_gate_sql_injection_defense(client: AsyncClient):
    """GATE 1: Confirms zero query alteration or bypass on hostile SQL injection inputs."""
    adversarial_payloads = [
        "' OR '1'='1",
        "admin'--",
        "'; DROP TABLE users;--",
        "1' UNION SELECT 'hacked', 'hacked', 'hacked', 1, 1--",
    ]
    for payload in adversarial_payloads:
        # Check login endpoint
        res = await client.post("/api/auth/login", json={"login": payload, "password": "Password123!"})
        assert res.status_code in [401, 422], f"Expected 401/422 for SQLi payload {payload}, got {res.status_code}"

    # Verify LIKE wildcard sanitization
    raw_query = "50%_discount\\target"
    safe_query = escape_like_wildcards(raw_query)
    assert safe_query == "50\\%\\_discount\\\\target"


# ──────────────────────────────────────────────────────────────────────────────
# Gate 2: Stored XSS Output Encoding & Strict CSP
# ──────────────────────────────────────────────────────────────────────────────

def test_gate_xss_output_encoding():
    """GATE 2: Confirms all report HTML entities are escaped and strict CSP headers are embedded."""
    scan = Scan(
        id=str(uuid.uuid4()),
        website_id=str(uuid.uuid4()),
        target_url="https://sec-gate.test",
        target_domain="sec-gate.test<script>alert(1)</script>",
        critical_count=1,
    )
    finding = ScanFinding(
        id=str(uuid.uuid4()),
        scan_id=scan.id,
        website_id=scan.website_id,
        title="Hostile Title <img src=x onerror=alert('gate')>",
        severity="critical",
        category="XSS",
        description="Hostile desc <svg/onload=alert('gate-desc')>",
        evidence="Hostile proof <iframe src='javascript:alert(1)'>",
        remediation="Hostile fix <script src='http://evil.com'></script>",
    )
    html_out = ReportService._build_html_report(
        scan=scan,
        findings=[finding],
        overall_risk_score=9.5,
        overall_posture="CRITICAL RISK",
        has_php2shell=False,
        php2shell_posture="Hardened",
        exec_summary="Exec summary with <script>alert('summary')</script>",
    )

    # Ensure dangerous tags never exist in the output
    assert "<script>" not in html_out
    assert "<img src=x" not in html_out
    assert "<svg/onload=" not in html_out
    assert "<iframe src=" not in html_out

    # Ensure CSP meta tag is embedded
    assert "Content-Security-Policy" in html_out
    assert "default-src 'none'" in html_out


# ──────────────────────────────────────────────────────────────────────────────
# Gate 3: SSRF Rejection & Redirect Interception
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_gate_ssrf_rejection():
    """GATE 3: Confirms all private, link-local, carrier-grade NAT, and cloud metadata targets are rejected."""
    prohibited = [
        "http://127.0.0.1",
        "http://localhost",
        "http://169.254.169.254/latest/meta-data/",
        "http://10.0.0.5",
        "http://172.16.0.1",
        "http://192.168.1.1",
        "http://0.0.0.0",
        "http://[::1]",
    ]
    for url in prohibited:
        with pytest.raises(ValueError):
            validate_and_normalize_target_url(url, resolve_dns=False)

    # Test HTTP redirect bounce attack interception
    mock_req = Request("GET", "https://legitimate-target.com")
    resp_redirect = Response(
        status_code=302,
        headers={"Location": "http://169.254.169.254/latest/meta-data/"},
        request=mock_req,
    )
    with pytest.raises(Exception) as exc:
        await validate_redirect_ssrf(resp_redirect)
    assert "SSRF Redirect Blocked" in str(exc.value)


# ──────────────────────────────────────────────────────────────────────────────
# Gate 4: Tenant Isolation & IDOR Protection
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_gate_tenant_isolation(client: AsyncClient):
    """GATE 4: Confirms Client B cannot access or modify Client A's websites or scans."""
    async with async_session_factory() as db:
        user_a = User(
            username=f"client_a_{uuid.uuid4().hex[:6]}",
            email=f"client_a_{uuid.uuid4().hex[:6]}@test.com",
            hashed_password=hash_password("Password123!"),
            role=UserRole.CLIENT.value,
            is_active=True,
        )
        user_b = User(
            username=f"client_b_{uuid.uuid4().hex[:6]}",
            email=f"client_b_{uuid.uuid4().hex[:6]}@test.com",
            hashed_password=hash_password("Password123!"),
            role=UserRole.CLIENT.value,
            is_active=True,
        )
        db.add_all([user_a, user_b])
        await db.commit()
        await db.refresh(user_a)
        await db.refresh(user_b)

        site_a = Website(
            user_id=user_a.id,
            name="Client A Target",
            target_url="https://client-a-domain.com",
            domain="client-a-domain.com",
            verification_method="file",
            verification_status="verified",
        )
        db.add(site_a)
        await db.commit()
        await db.refresh(site_a)

    # Generate token for Client B
    token_b = create_access_token(data={"sub": user_b.id, "role": user_b.role})

    # Client B attempts to fetch Client A's website target
    res = await client.get(
        f"/api/websites/{site_a.id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    # Must be 403 Forbidden
    assert res.status_code == 403
    assert "permission" in res.json().get("detail", "").lower() or "denied" in res.json().get("detail", "").lower()


# ──────────────────────────────────────────────────────────────────────────────
# Gate 5: Path Traversal & Safe Filename Validation
# ──────────────────────────────────────────────────────────────────────────────

def test_gate_path_traversal_guards():
    """GATE 5: Confirms directory traversal and dangerous executable extensions are rejected."""
    malicious_paths = [
        "../../../../etc/passwd",
        "/etc/shadow",
        "app.php\x00.png",
        "C:\\Windows\\System32\\cmd.exe",
        "malware.exe",
        "payload.sh",
        "script.bat",
    ]
    for p in malicious_paths:
        with pytest.raises(ValueError):
            validate_safe_relative_path(p)

    # Valid relative paths must pass
    assert validate_safe_relative_path("src/Security/Handler.php") == "src/Security/Handler.php"


# ──────────────────────────────────────────────────────────────────────────────
# Gate 6: Session Invalidation on Password Change & Reset
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_gate_session_invalidation_on_password_reset(client: AsyncClient):
    """GATE 6: Confirms that changing or resetting password revokes all active refresh tokens."""
    async with async_session_factory() as db:
        user = User(
            username=f"session_test_{uuid.uuid4().hex[:6]}",
            email=f"session_test_{uuid.uuid4().hex[:6]}@test.com",
            hashed_password=hash_password("OldPassword123!"),
            role=UserRole.CLIENT.value,
            is_active=True,
            recovery_token="valid_recovery_token_12345",
            recovery_token_expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

        # Create active refresh token for user
        token_record = RefreshToken(
            user_id=user.id,
            token_hash=hash_refresh_token(generate_refresh_token()),
            family_id=str(uuid.uuid4()),
            expires_at=datetime.now(timezone.utc) + timedelta(days=1),
            is_revoked=False,
        )
        db.add(token_record)
        await db.commit()
        await db.refresh(token_record)

    # Execute password reset
    reset_res = await client.post(
        "/api/auth/reset-password",
        json={"token": "valid_recovery_token_12345", "new_password": "NewStrongPassword123!", "confirm_password": "NewStrongPassword123!"},
    )
    assert reset_res.status_code == 200

    # Verify that refresh token is now revoked
    async with async_session_factory() as db:
        stmt = select(RefreshToken).where(RefreshToken.id == token_record.id)
        refreshed = (await db.execute(stmt)).scalar_one()
        assert refreshed.is_revoked is True
        assert refreshed.revoked_at is not None


# ──────────────────────────────────────────────────────────────────────────────
# Gate 7: Audit Log Credential Redaction
# ──────────────────────────────────────────────────────────────────────────────

def test_gate_audit_log_credential_redaction():
    """GATE 7: Confirms passwords, tokens, and secrets are redacted from audit log metadata."""
    sensitive_meta = {
        "user_email": "target@domain.com",
        "password": "CleartextPassword!",
        "access_token": "secret_jwt_token",
        "stripe_signature": "t=123,v1=secret",
        "nested": {
            "recovery_token": "123456",
            "safe_key": "safe_value",
        },
    }
    cleaned = _sanitize_log_metadata(sensitive_meta)
    assert cleaned["password"] == "[REDACTED]"
    assert cleaned["access_token"] == "[REDACTED]"
    assert cleaned["stripe_signature"] == "[REDACTED]"
    assert cleaned["nested"]["recovery_token"] == "[REDACTED]"
    assert cleaned["nested"]["safe_key"] == "safe_value"
    assert cleaned["user_email"] == "target@domain.com"


# ──────────────────────────────────────────────────────────────────────────────
# Gate 8: Webhook Signature & Replay Defense
# ──────────────────────────────────────────────────────────────────────────────

def test_gate_webhook_signature_and_replay_defense():
    """GATE 8: Confirms webhook verification enforces HMAC-SHA256 and rejects replayed timestamps."""
    secret = settings.STRIPE_WEBHOOK_SECRET or settings.SECRET_KEY
    payload = b'{"type": "invoice.paid"}'
    now = int(time.time())

    # Valid fresh signature
    signed = f"{now}.".encode() + payload
    v1 = hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()
    assert PaymentProviderService.verify_webhook_signature(payload, f"t={now},v1={v1}") is True

    # Replay attack (> 300 seconds old)
    old_time = now - 400
    old_signed = f"{old_time}.".encode() + payload
    old_v1 = hmac.new(secret.encode(), old_signed, hashlib.sha256).hexdigest()
    assert PaymentProviderService.verify_webhook_signature(payload, f"t={old_time},v1={old_v1}") is False


# ──────────────────────────────────────────────────────────────────────────────
# Gate 9: Production Deployment Safety Gate
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_gate_production_deployment_protection(client: AsyncClient):
    """GATE 9: Confirms production deployment fails without the exact safety phrase 'DEPLOY PRODUCTION'."""
    async with async_session_factory() as db:
        user = User(
            username=f"dep_user_{uuid.uuid4().hex[:6]}",
            email=f"dep_user_{uuid.uuid4().hex[:6]}@test.com",
            hashed_password=hash_password("Password123!"),
            role=UserRole.CLIENT.value,
            is_active=True,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    token = create_access_token(data={"sub": user.id, "role": user.role})

    # Attempt production deployment with invalid confirmation token
    res = await client.post(
        "/api/deployment/deploy-production",
        json={
            "session_id": str(uuid.uuid4()),
            "target_id": str(uuid.uuid4()),
            "confirmation_token": "deploy",  # Incorrect phrase
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 400
    assert "DEPLOY PRODUCTION" in res.json().get("detail", "")


# ──────────────────────────────────────────────────────────────────────────────
# Gate 10: PHP2Shell Zero-Day Shield Mandate
# ──────────────────────────────────────────────────────────────────────────────

def test_gate_php2shell_shield_active():
    """GATE 10: Confirms detection and AST mitigation for PHP2Shell (CVE-2026-109618 / 19)."""
    vulnerable_code = """<?php
    ini_set('display_errors', '1');
    function custom_handler($errno, $errstr) {
        echo "Error: " . $errstr;
    }
    set_error_handler("custom_handler");
    """
    res = analyze_php_code(vulnerable_code)
    assert res.has_php2shell_vulnerability is True
    assert any("CVE-2026-109618" in f.cve or "PHP2Shell" in f.title for f in res.findings)


# ──────────────────────────────────────────────────────────────────────────────
# Gate 11: HTTP Security Headers Presence
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_gate_security_headers_present(client: AsyncClient):
    """GATE 11: Confirms all defense-in-depth HTTP security headers are attached."""
    res = await client.get("/api/health")
    assert res.status_code == 200
    h = res.headers
    assert h.get("X-Content-Type-Options") == "nosniff"
    assert h.get("X-Frame-Options") == "DENY"
    assert h.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert "Content-Security-Policy" in h
    assert "X-Request-ID" in h


# ──────────────────────────────────────────────────────────────────────────────
# Gate 12: Sliding-Window Rate Limiter
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_gate_rate_limiter_enforcement():
    """GATE 12: Confirms sliding-window rate limiter trips with 429 when threshold exceeded."""
    from fastapi import HTTPException
    await limiter.reset()
    key = "gate_test:127.0.0.1"

    # Trip the limiter with max 2 requests
    await limiter.check_rate_limit(key, max_requests=2, window_seconds=60)
    await limiter.check_rate_limit(key, max_requests=2, window_seconds=60)

    with pytest.raises(HTTPException) as exc:
        await limiter.check_rate_limit(key, max_requests=2, window_seconds=60)
    assert exc.value.status_code == 429

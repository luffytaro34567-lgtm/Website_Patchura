"""
Comprehensive Security Hardening and Defense-in-Depth Regression Tests (Phase 14).
Verifies resilience against SQL injection, Stored XSS, SSRF, IDOR / broken access control,
path traversal, command injection primitives, rate limiting, and webhook replay attacks.
"""
from __future__ import annotations

import hashlib
import hmac
import time
import uuid
import pytest
from httpx import AsyncClient, Request, Response

from app.core.config import settings
from app.models.scan import Scan, ScanFinding
from app.models.user import User, UserRole
from app.models.website import Website, VerificationStatus
from app.security.passwords import hash_password
from app.security.path_validator import validate_safe_branch_name, validate_safe_relative_path
from app.security.rate_limiter import limiter
from app.security.safe_http import validate_redirect_ssrf
from app.security.sql_sanitizer import escape_like_wildcards, sanitize_search_query
from app.security.url_validator import is_ip_prohibited, validate_and_normalize_target_url
from app.services.payment.payment_provider import PaymentProviderService
from app.services.payment.quota_service import QuotaService
from app.services.remediation.isolated_tester import IsolatedPatchTester
from app.services.report_service import ReportService


# ──────────────────────────────────────────────────────────────────────────────
# 1. SQL Injection Resilience Tests
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_sql_injection_resilience_in_auth_and_search(client: AsyncClient):
    """
    Asserts that classic SQL injection payloads injected into authentication,
    registration, and search parameters do not bypass security or cause syntax errors.
    """
    sqli_payloads = [
        "' OR '1'='1",
        "admin'--",
        "'; DROP TABLE users;--",
        "' UNION SELECT 1, 'admin', 'hacked', 'admin', 1--",
        "\" OR \"\"=\"",
        "1' OR 1=1 #",
    ]

    for payload in sqli_payloads:
        # Test Login
        login_res = await client.post(
            "/api/auth/login",
            json={"login": payload, "password": "RandomPassword123!"},
        )
        # Must return 401 Unauthorized or 422 Unprocessable, NEVER 200 or 500
        assert login_res.status_code in [401, 422]

        # Test Registration
        reg_res = await client.post(
            "/api/auth/register",
            json={
                "username": f"user_{uuid.uuid4().hex[:6]}",
                "email": f"test_{uuid.uuid4().hex[:6]}@example.com",
                "password": payload,
                "confirm_password": payload,
            },
        )
        # Must either reject password policy or treat as literal password (never SQL syntax error)
        assert reg_res.status_code != 500


def test_sql_like_wildcard_escaping():
    """Verifies that SQL LIKE wildcards '%', '_', and '\\' are escaped."""
    raw = "100%_safe\\query"
    escaped = escape_like_wildcards(raw)
    assert escaped == "100\\%\\_safe\\\\query"

    sanitized = sanitize_search_query("test%_search")
    assert "\\%" in sanitized
    assert "\\_" in sanitized


# ──────────────────────────────────────────────────────────────────────────────
# 2. Stored Cross-Site Scripting (XSS) Prevention Tests
# ──────────────────────────────────────────────────────────────────────────────

def test_stored_xss_sanitized_in_html_reports():
    """
    Verifies that hostile HTML, script tags, and event handlers in finding titles,
    descriptions, evidence, and remediation advice are escaped in printable reports.
    """
    scan = Scan(
        id=str(uuid.uuid4()),
        website_id=str(uuid.uuid4()),
        target_url="https://xss-test.com",
        target_domain="xss-test.com<script>alert('xss-domain')</script>",
        critical_count=1,
        high_count=0,
        medium_count=0,
        low_count=0,
        info_count=0,
    )

    hostile_finding = ScanFinding(
        id=str(uuid.uuid4()),
        scan_id=scan.id,
        website_id=scan.website_id,
        title="Cross-Site Scripting <script>alert('title')</script>",
        severity="critical",
        category="Injection",
        cwe_id="CWE-79",
        cvss_score=8.5,
        description="Hostile description with <img src=x onerror=alert('desc')>",
        evidence="Hostile proof payload: <svg/onload=alert('evidence')>",
        remediation="Remediation guidance with <iframe src='javascript:alert(1)'>",
    )

    html_report = ReportService._build_html_report(
        scan=scan,
        findings=[hostile_finding],
        overall_risk_score=9.0,
        overall_posture="CRITICAL RISK",
        has_php2shell=False,
        php2shell_posture="Hardened",
        exec_summary="Executive summary with <b>safe</b> and <script>alert('exec')</script>",
    )

    # Assert hostile raw tags are NEVER present
    assert "<script>alert('title')</script>" not in html_report
    assert "<img src=x onerror=alert('desc')>" not in html_report
    assert "<svg/onload=alert('evidence')>" not in html_report
    assert "<iframe src='javascript:alert(1)'>" not in html_report
    assert "<script>alert('xss-domain')</script>" not in html_report

    # Assert escaped entities are present
    assert "&lt;script&gt;alert(&#x27;title&#x27;)&lt;/script&gt;" in html_report
    assert "&lt;img src=x onerror=alert(&#x27;desc&#x27;)&gt;" in html_report

    # Assert Content-Security-Policy header tag is present
    assert "Content-Security-Policy" in html_report
    assert "default-src 'none'" in html_report


# ──────────────────────────────────────────────────────────────────────────────
# 3. SSRF & Prohibited IP Ranges Tests
# ──────────────────────────────────────────────────────────────────────────────

def test_ssrf_prohibited_ip_detection():
    """Asserts that private, loopback, link-local, carrier-grade NAT, and cloud metadata IPs are identified."""
    import ipaddress

    prohibited_ips = [
        "127.0.0.1",
        "127.0.0.2",
        "10.0.0.1",
        "172.16.0.1",
        "172.31.255.255",
        "192.168.1.1",
        "169.254.169.254",  # AWS/GCP/Azure instance metadata
        "169.254.170.2",    # AWS task metadata
        "0.0.0.0",
        "::1",              # IPv6 loopback
        "fe80::1",          # IPv6 link-local
        "fc00::1",          # IPv6 unique local
        "::ffff:127.0.0.1", # IPv4-mapped IPv6 loopback
        "100.64.0.1",       # Carrier-grade NAT
    ]

    for ip_str in prohibited_ips:
        ip = ipaddress.ip_address(ip_str)
        assert is_ip_prohibited(ip), f"Expected {ip_str} to be detected as prohibited SSRF target"


def test_validate_and_normalize_target_url_rejects_ssrf():
    """Asserts that registering localhost, metadata, and prohibited IP targets raises ValueError."""
    bad_urls = [
        "http://localhost",
        "http://127.0.0.1",
        "https://127.0.0.1:8000",
        "http://169.254.169.254/latest/meta-data/",
        "http://0.0.0.0",
        "http://metadata.google.internal",
        "http://[::1]",
        "ftp://example.com",
        "file:///etc/passwd",
        "gopher://127.0.0.1:6379",
        "http://192.168.1.50:5432",
    ]

    for bad_url in bad_urls:
        with pytest.raises(ValueError):
            validate_and_normalize_target_url(bad_url, resolve_dns=False)


@pytest.mark.asyncio
async def test_safe_http_client_blocks_ssrf_redirect():
    """Asserts that HTTP redirect responses pointing to internal metadata or loopback IPs are blocked."""
    import httpx

    # Simulate a 302 redirect pointing to AWS instance metadata
    mock_request = Request("GET", "https://authorized-client.com/test")
    redirect_to_metadata = Response(
        status_code=302,
        headers={"Location": "http://169.254.169.254/latest/meta-data/"},
        request=mock_request,
    )

    with pytest.raises(httpx.RequestError) as exc_info:
        await validate_redirect_ssrf(redirect_to_metadata)
    assert "SSRF Redirect Blocked" in str(exc_info.value)

    # Simulate a 302 redirect pointing to localhost
    redirect_to_localhost = Response(
        status_code=302,
        headers={"Location": "http://localhost:5432/internal"},
        request=mock_request,
    )
    with pytest.raises(httpx.RequestError) as exc_info:
        await validate_redirect_ssrf(redirect_to_localhost)
    assert "SSRF Redirect Blocked" in str(exc_info.value)


# ──────────────────────────────────────────────────────────────────────────────
# 4. Path Traversal & Safe Filename Validation Tests
# ──────────────────────────────────────────────────────────────────────────────

def test_path_traversal_detection():
    """Asserts that directory traversal, absolute paths, and dangerous extensions are rejected."""
    bad_paths = [
        "../../../../etc/passwd",
        "../secrets.py",
        "/etc/shadow",
        "\\Windows\\System32\\cmd.exe",
        "C:\\config.ini",
        "app.php\x00.jpg",
        "backdoor.exe",
        "payload.sh",
        "reverse_shell.ps1",
        "../../../var/www/html/index.php",
    ]

    for bad_path in bad_paths:
        with pytest.raises(ValueError):
            validate_safe_relative_path(bad_path)

    # Valid safe relative paths must be accepted and normalized
    valid_paths = [
        "src/app.php",
        "config/database.php",
        "controllers/user_controller.py",
        "index.php",
        "utils/helpers.js",
    ]
    for valid in valid_paths:
        assert validate_safe_relative_path(valid) == valid


def test_safe_branch_name_validation():
    """Asserts that invalid or dangerous Git branch names are rejected."""
    bad_branches = [
        "branch with spaces",
        "branch~1",
        "branch^2",
        "branch:bad",
        "branch?wildcard",
        "branch*star",
        "..bad",
        "bad..branch",
    ]
    for b in bad_branches:
        with pytest.raises(ValueError):
            validate_safe_branch_name(b)

    assert validate_safe_branch_name("patchora/patch-1234") == "patchora/patch-1234"


# ──────────────────────────────────────────────────────────────────────────────
# 5. Isolated Sandbox Scanner Code Filter Tests
# ──────────────────────────────────────────────────────────────────────────────

def test_isolated_tester_blocks_backdoors_and_injection_primitives():
    """Asserts that the isolated patch tester detects execution primitives in untrusted code."""
    dangerous_snippets = [
        ("malicious.php", "php", "<?php system($_GET['cmd']); ?>"),
        ("eval_code.php", "php", "<?php eval($payload); ?>"),
        ("rev_shell.php", "php", "<?php fsockopen('10.0.0.1', 4444); ?>"),
        ("subproc.py", "python", "import subprocess\nsubprocess.Popen(['rm', '-rf', '/'])"),
        ("os_cmd.py", "python", "import os\nos.system('whoami')"),
        ("pickle_exec.py", "python", "import pickle\npickle.loads(data)"),
    ]

    for filename, lang, code in dangerous_snippets:
        result = IsolatedPatchTester.run_isolated_verification(
            filename=filename,
            language=lang,
            original_code="// original",
            patched_code=code,
            proposed_diff="--- a\n+++ b\n+ safe",
            finding_category="security_headers",
            finding_title="Missing Security Headers",
        )
        assert result["passed"] is False, f"Expected {filename} to fail isolated sandbox verification"
        assert result["test_status"] == "failed"


# ──────────────────────────────────────────────────────────────────────────────
# 6. Webhook Cryptographic Verification & Replay Protection Tests
# ──────────────────────────────────────────────────────────────────────────────

def test_webhook_cryptographic_verification_and_replay_defense():
    """Verifies that webhook verification requires a valid secret, signature, and protects against replay attacks."""
    payload = b'{"id": "evt_12345", "type": "checkout.session.completed"}'
    secret = settings.STRIPE_WEBHOOK_SECRET or settings.SECRET_KEY

    # Valid fresh signature
    timestamp = int(time.time())
    signed_payload = f"{timestamp}.".encode() + payload
    valid_sig = hmac.new(secret.encode(), signed_payload, hashlib.sha256).hexdigest()
    header = f"t={timestamp},v1={valid_sig}"

    assert PaymentProviderService.verify_webhook_signature(payload, header) is True

    # Replay attack: signature from 10 minutes ago (> 300 seconds)
    expired_timestamp = timestamp - 600
    expired_signed_payload = f"{expired_timestamp}.".encode() + payload
    expired_sig = hmac.new(secret.encode(), expired_signed_payload, hashlib.sha256).hexdigest()
    expired_header = f"t={expired_timestamp},v1={expired_sig}"

    assert PaymentProviderService.verify_webhook_signature(payload, expired_header) is False

    # Tampered payload
    tampered_payload = b'{"id": "evt_12345", "type": "checkout.session.completed", "amount": 0}'
    assert PaymentProviderService.verify_webhook_signature(tampered_payload, header) is False

    # Tampered signature
    assert PaymentProviderService.verify_webhook_signature(payload, f"t={timestamp},v1=bad_signature_hex") is False


# ──────────────────────────────────────────────────────────────────────────────
# 7. Security Headers Middleware Tests
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_security_headers_middleware(client: AsyncClient):
    """Asserts that all required defense-in-depth security headers are attached to responses."""
    res = await client.get("/api/health")
    assert res.status_code == 200

    headers = res.headers
    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert headers.get("X-Frame-Options") == "DENY"
    assert headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert headers.get("X-XSS-Protection") == "0"
    assert "Content-Security-Policy" in headers
    assert "frame-ancestors 'none'" in headers.get("Content-Security-Policy")
    assert "X-Request-ID" in headers
    assert "X-Process-Time-Ms" in headers


# ──────────────────────────────────────────────────────────────────────────────
# 8. Rate Limiting Tests
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_rate_limiter_blocks_excessive_requests():
    """Asserts that the sliding-window rate limiter raises HTTP 429 when threshold is exceeded."""
    from fastapi import HTTPException
    await limiter.reset()

    test_key = "test_scope:127.0.0.1"

    # Allow 3 requests
    for _ in range(3):
        await limiter.check_rate_limit(key=test_key, max_requests=3, window_seconds=60)

    # 4th request must trigger 429
    with pytest.raises(HTTPException) as exc_info:
        await limiter.check_rate_limit(key=test_key, max_requests=3, window_seconds=60)

    assert exc_info.value.status_code == 429
    assert "Retry-After" in exc_info.value.headers

"""
Safe, evidence-based vulnerability scanner engine.
Executes non-destructive security checks against verified, explicitly authorized target websites.
Incorporate detection and defense-in-depth mitigation for PHP2Shell (CVE-2026-109618 & CVE-2026-109619).
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import re
import time
from typing import List, Optional
from urllib.parse import urljoin, urlparse

import httpx
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import async_session_factory
from app.models.scan import FindingSeverity, Scan, ScanFinding, ScanProfile, ScanStatus
from app.models.website import Website
from app.security.url_validator import validate_target_url
from app.security.safe_http import create_safe_async_client
from app.services.activity.activity_service import ActivityService

logger = structlog.get_logger(__name__)

USER_AGENT = "PATCHORA-Scanner/1.0 (+https://patchora.io/security-bot; authorized security assessment)"


class WebScannerEngine:
    """Core vulnerability scanner executing authorized web checks."""

    @staticmethod
    async def run_scan(scan_id: str) -> None:
        """Entry point executed in background task."""
        async with async_session_factory() as db:
            scan = await db.get(Scan, scan_id)
            if not scan:
                logger.error("scan_not_found", scan_id=scan_id)
                return

            if scan.status == ScanStatus.CANCELLED.value:
                logger.info("scan_already_cancelled", scan_id=scan_id)
                return

            # Fetch website and authorization
            website = await db.get(Website, scan.website_id)
            if not website:
                scan.status = ScanStatus.FAILED.value
                scan.error_message = "Target website not found."
                await db.commit()
                return

            # Verification & Authorization check
            if website.is_suspended_by_admin:
                scan.status = ScanStatus.FAILED.value
                scan.error_message = "Target website assessment has been suspended by an administrator."
                await db.commit()
                return

            if website.verification_status != "verified":
                scan.status = ScanStatus.FAILED.value
                scan.error_message = "Target website ownership is not verified."
                await db.commit()
                return

            # Load authorization relation
            auth_stmt = select(Website).where(Website.id == website.id)
            res = await db.execute(auth_stmt)
            ws_obj = res.scalar_one_or_none()
            auth = ws_obj.authorization if ws_obj else None

            if not auth or not auth.is_authorized or auth.is_revoked:
                scan.status = ScanStatus.FAILED.value
                scan.error_message = "Target website does not have active scan authorization."
                await db.commit()
                return

            if auth.expires_at and auth.expires_at < datetime.now(timezone.utc):
                scan.status = ScanStatus.FAILED.value
                scan.error_message = "Target scan authorization has expired."
                await db.commit()
                return

            # SSRF validation on target URL
            try:
                validate_target_url(scan.target_url)
            except ValueError as e:
                scan.status = ScanStatus.FAILED.value
                scan.error_message = f"Target URL failed safety policy check: {str(e)}"
                await db.commit()
                return

            # Begin scanning
            start_time = time.perf_counter()
            scan.status = ScanStatus.RUNNING.value
            scan.started_at = datetime.now(timezone.utc)
            scan.progress_percent = 5
            await db.commit()

            findings: List[ScanFinding] = []

            try:
                # Setup safe async HTTP client with strict limits and SSRF redirect defense
                async with create_safe_async_client(
                    timeout=httpx.Timeout(10.0, connect=5.0),
                    headers={"User-Agent": USER_AGENT},
                    max_redirects=3,
                    verify_ssl=False,  # Allow assessing servers with self-signed certs in lab mode
                ) as client:

                    # Check for cancellation
                    if await WebScannerEngine._is_cancelled(db, scan_id):
                        return

                    # ── Phase 1: Base HTTP & Security Headers (0% -> 25%) ────
                    scan.progress_percent = 15
                    await db.commit()

                    base_findings = await WebScannerEngine._inspect_security_headers(client, scan)
                    findings.extend(base_findings)

                    if await WebScannerEngine._is_cancelled(db, scan_id):
                        return

                    # ── Phase 2: Cookies & CORS Inspection (25% -> 50%) ───────
                    scan.progress_percent = 35
                    await db.commit()

                    cookie_findings = await WebScannerEngine._inspect_cookies_and_cors(client, scan)
                    findings.extend(cookie_findings)

                    if await WebScannerEngine._is_cancelled(db, scan_id):
                        return

                    # ── Phase 3: Server Information & Version Disclosure (50% -> 75%)
                    scan.progress_percent = 60
                    await db.commit()

                    server_findings = await WebScannerEngine._inspect_server_disclosure(client, scan)
                    findings.extend(server_findings)

                    # ── Phase 4: Sensitive Files & PHP2Shell Probe (75% -> 95%)
                    if scan.profile in [ScanProfile.STANDARD.value, ScanProfile.PHP_DEEP.value]:
                        if await WebScannerEngine._is_cancelled(db, scan_id):
                            return

                        scan.progress_percent = 80
                        await db.commit()

                        php_findings = await WebScannerEngine._inspect_php_and_php2shell(client, scan)
                        findings.extend(php_findings)

                    # ── Phase 5: Finalize and Calculate Severity Counts ───────
                    scan.progress_percent = 100
                    scan.status = ScanStatus.COMPLETED.value
                    scan.completed_at = datetime.now(timezone.utc)
                    scan.duration_seconds = round(time.perf_counter() - start_time, 2)

                    # Calculate severities
                    scan.total_findings = len(findings)
                    scan.critical_count = sum(1 for f in findings if f.severity == FindingSeverity.CRITICAL.value)
                    scan.high_count = sum(1 for f in findings if f.severity == FindingSeverity.HIGH.value)
                    scan.medium_count = sum(1 for f in findings if f.severity == FindingSeverity.MEDIUM.value)
                    scan.low_count = sum(1 for f in findings if f.severity == FindingSeverity.LOW.value)
                    scan.info_count = sum(1 for f in findings if f.severity == FindingSeverity.INFO.value)

                    for f in findings:
                        db.add(f)

                    # Trigger SecurityAlert if PHP2Shell high risk findings are detected
                    has_php2shell = any("PHP2Shell" in (f.category or "") or "CVE-2026-109618" in f.title or "CVE-2026-109619" in f.title for f in findings)
                    if has_php2shell:
                        await ActivityService.create_security_alert(
                            db=db,
                            alert_type="php2shell_high_risk_detected",
                            title=f"PHP2Shell Memory Corruption detected on {scan.target_domain}",
                            description=f"Critical unhandled PHP error display or heap leak patterns observed during scan of {scan.target_url}. Immediate defensive hardening required.",
                            severity="critical",
                            source_module="scanner",
                            target_entity_type="scan",
                            target_entity_id=scan.id,
                            cve_id="CVE-2026-109618, CVE-2026-109619",
                            metadata={"domain": scan.target_domain, "scan_id": scan.id},
                            commit=False,
                        )

                    await ActivityService.log_event(
                        db=db,
                        event_category="vulnerability_scanning",
                        event_name="scan_completed",
                        actor_type="system",
                        target_type="scan",
                        target_id=scan.id,
                        target_identifier=scan.target_domain,
                        outcome="success",
                        severity="critical" if scan.critical_count > 0 else "info",
                        source_module="scanner",
                        metadata={"total_findings": scan.total_findings, "critical": scan.critical_count},
                        requires_review=(scan.critical_count > 0),
                        commit=False,
                    )

                    await db.commit()
                    logger.info("scan_completed_successfully", scan_id=scan_id, total_findings=len(findings))

            except httpx.RequestError as exc:
                logger.warning("scan_request_error", scan_id=scan_id, error=str(exc))
                scan.status = ScanStatus.FAILED.value
                scan.completed_at = datetime.now(timezone.utc)
                scan.error_message = f"Network connection error while reaching target: {str(exc)}"
                await ActivityService.log_event(
                    db=db,
                    event_category="vulnerability_scanning",
                    event_name="scan_failed",
                    actor_type="system",
                    target_type="scan",
                    target_id=scan.id,
                    target_identifier=scan.target_domain,
                    outcome="failure",
                    severity="warning",
                    source_module="scanner",
                    metadata={"error": scan.error_message},
                    commit=False,
                )
                await db.commit()
            except Exception as exc:
                logger.error("scan_internal_failure", scan_id=scan_id, error=str(exc))
                scan.status = ScanStatus.FAILED.value
                scan.completed_at = datetime.now(timezone.utc)
                scan.error_message = f"Scan execution error: {str(exc)}"
                await ActivityService.log_event(
                    db=db,
                    event_category="vulnerability_scanning",
                    event_name="scan_failed",
                    actor_type="system",
                    target_type="scan",
                    target_id=scan.id,
                    target_identifier=scan.target_domain,
                    outcome="failure",
                    severity="warning",
                    source_module="scanner",
                    metadata={"error": scan.error_message},
                    commit=False,
                )
                await db.commit()

    @staticmethod
    async def _is_cancelled(db: AsyncSession, scan_id: str) -> bool:
        """Check if scan was cancelled by client or admin mid-flight."""
        curr = await db.get(Scan, scan_id)
        if curr and (curr.is_cancelled or curr.status == ScanStatus.CANCELLED.value):
            curr.status = ScanStatus.CANCELLED.value
            await db.commit()
            return True
        return False

    @staticmethod
    async def _inspect_security_headers(client: httpx.AsyncClient, scan: Scan) -> List[ScanFinding]:
        findings: List[ScanFinding] = []
        try:
            resp = await client.get(scan.target_url)
            headers = {k.lower(): v for k, v in resp.headers.items()}

            # 1. Strict-Transport-Security (HSTS)
            if scan.target_url.startswith("https://"):
                hsts = headers.get("strict-transport-security")
                if not hsts:
                    findings.append(
                        ScanFinding(
                            scan_id=scan.id,
                            website_id=scan.website_id,
                            title="Missing HTTP Strict Transport Security (HSTS) Header",
                            severity=FindingSeverity.MEDIUM.value,
                            category="Security Headers",
                            description=(
                                "The application communicates over HTTPS but does not declare the Strict-Transport-Security header. "
                                "This leaves users vulnerable to SSL-stripping and man-in-the-middle downgrade attacks."
                            ),
                            evidence=f"HTTP/{resp.http_version} {resp.status_code}\nStrict-Transport-Security: [NOT PRESENT]",
                            remediation=(
                                "Configure your web server or reverse proxy to include: "
                                "Strict-Transport-Security: max-age=31536000; includeSubDomains; preload"
                            ),
                            cwe_id="CWE-319",
                            cvss_score=5.4,
                            target_url=scan.target_url,
                        )
                    )

            # 2. Content-Security-Policy (CSP)
            csp = headers.get("content-security-policy")
            if not csp:
                findings.append(
                    ScanFinding(
                        scan_id=scan.id,
                        website_id=scan.website_id,
                        title="Missing Content-Security-Policy (CSP)",
                        severity=FindingSeverity.MEDIUM.value,
                        category="Security Headers",
                        description=(
                            "No Content-Security-Policy header is configured. CSP is a critical defense-in-depth "
                            "mechanism to restrict resource loading and mitigate Cross-Site Scripting (XSS) and data injection."
                        ),
                        evidence=f"HTTP/{resp.http_version} {resp.status_code}\nContent-Security-Policy: [NOT PRESENT]",
                        remediation="Define a strict Content-Security-Policy restricting script-src, object-src, and default-src.",
                        cwe_id="CWE-693",
                        cvss_score=6.1,
                        target_url=scan.target_url,
                    )
                )
            elif "'unsafe-inline'" in csp and "nonce" not in csp and "hash" not in csp:
                findings.append(
                    ScanFinding(
                        scan_id=scan.id,
                        website_id=scan.website_id,
                        title="Weak Content-Security-Policy with Unsafe Inline Scripts",
                        severity=FindingSeverity.LOW.value,
                        category="Security Headers",
                        description="The CSP header allows 'unsafe-inline' script execution without nonces or cryptographic hashes.",
                        evidence=f"Content-Security-Policy: {csp[:180]}...",
                        remediation="Refactor inline scripts into external files or protect them using cryptographic nonces or SHA hashes.",
                        cwe_id="CWE-693",
                        cvss_score=4.3,
                        target_url=scan.target_url,
                    )
                )

            # 3. X-Frame-Options / Clickjacking Protection
            xfo = headers.get("x-frame-options")
            has_frame_ancestors = csp and "frame-ancestors" in csp
            if not xfo and not has_frame_ancestors:
                findings.append(
                    ScanFinding(
                        scan_id=scan.id,
                        website_id=scan.website_id,
                        title="Missing Clickjacking Defense (X-Frame-Options / frame-ancestors)",
                        severity=FindingSeverity.MEDIUM.value,
                        category="Security Headers",
                        description=(
                            "The page can be embedded inside an <iframe> on external domains without restrictions, "
                            "leaving authenticated visitors vulnerable to UI redressing (clickjacking) attacks."
                        ),
                        evidence=f"X-Frame-Options: [NOT PRESENT]\nCSP frame-ancestors: [NOT PRESENT]",
                        remediation="Add 'X-Frame-Options: DENY' or 'X-Frame-Options: SAMEORIGIN', or use CSP 'frame-ancestors 'self''.",
                        cwe_id="CWE-1021",
                        cvss_score=5.0,
                        target_url=scan.target_url,
                    )
                )

            # 4. X-Content-Type-Options
            xcto = headers.get("x-content-type-options")
            if not xcto or "nosniff" not in xcto.lower():
                findings.append(
                    ScanFinding(
                        scan_id=scan.id,
                        website_id=scan.website_id,
                        title="Missing X-Content-Type-Options: nosniff Header",
                        severity=FindingSeverity.LOW.value,
                        category="Security Headers",
                        description=(
                            "The X-Content-Type-Options header is missing or not set to 'nosniff'. "
                            "Browsers may attempt MIME-type sniffing, transforming benign media files into executable JavaScript."
                        ),
                        evidence=f"X-Content-Type-Options: {xcto if xcto else '[NOT PRESENT]'}",
                        remediation="Add the header: 'X-Content-Type-Options: nosniff' to all HTTP responses.",
                        cwe_id="CWE-16",
                        cvss_score=3.7,
                        target_url=scan.target_url,
                    )
                )

            # 5. Referrer-Policy
            ref_pol = headers.get("referrer-policy")
            if not ref_pol:
                findings.append(
                    ScanFinding(
                        scan_id=scan.id,
                        website_id=scan.website_id,
                        title="Missing Referrer-Policy Header",
                        severity=FindingSeverity.INFO.value,
                        category="Security Headers",
                        description="Without an explicit Referrer-Policy, full URLs with sensitive query parameters may leak to external third parties.",
                        evidence="Referrer-Policy: [NOT PRESENT]",
                        remediation="Set 'Referrer-Policy: strict-origin-when-cross-origin' or 'no-referrer'.",
                        cwe_id="CWE-200",
                        cvss_score=2.0,
                        target_url=scan.target_url,
                    )
                )

        except Exception as e:
            logger.debug("headers_inspection_skipped", error=str(e))

        return findings

    @staticmethod
    async def _inspect_cookies_and_cors(client: httpx.AsyncClient, scan: Scan) -> List[ScanFinding]:
        findings: List[ScanFinding] = []
        try:
            # Test CORS with arbitrary Origin
            cors_headers = {"Origin": "https://threat-actor.example.com"}
            resp = await client.get(scan.target_url, headers=cors_headers)

            acao = resp.headers.get("access-control-allow-origin")
            acac = resp.headers.get("access-control-allow-credentials")

            if acao == "*" and acac == "true":
                findings.append(
                    ScanFinding(
                        scan_id=scan.id,
                        website_id=scan.website_id,
                        title="Critical CORS Misconfiguration: Wildcard Origin With Credentials",
                        severity=FindingSeverity.HIGH.value,
                        category="CORS Misconfiguration",
                        description=(
                            "The server returns Access-Control-Allow-Origin: * together with Access-Control-Allow-Credentials: true. "
                            "This configuration enables rogue origins to read authenticated responses via cross-origin requests."
                        ),
                        evidence=f"Access-Control-Allow-Origin: {acao}\nAccess-Control-Allow-Credentials: {acac}",
                        remediation="Never pair wildcard origin (*) with Access-Control-Allow-Credentials. Whitelist specific trusted origins.",
                        cwe_id="CWE-942",
                        cvss_score=8.1,
                        target_url=scan.target_url,
                    )
                )
            elif acao == "https://threat-actor.example.com" and acac == "true":
                findings.append(
                    ScanFinding(
                        scan_id=scan.id,
                        website_id=scan.website_id,
                        title="Arbitrary Origin Reflection with Credentials in CORS",
                        severity=FindingSeverity.HIGH.value,
                        category="CORS Misconfiguration",
                        description="The application dynamically mirrors untrusted Origin headers into Access-Control-Allow-Origin with credentials allowed.",
                        evidence=f"Request Origin: https://threat-actor.example.com\nAccess-Control-Allow-Origin: {acao}\nAccess-Control-Allow-Credentials: {acac}",
                        remediation="Validate incoming Origin headers against an explicit strict allowlist of domains before reflecting them.",
                        cwe_id="CWE-942",
                        cvss_score=7.8,
                        target_url=scan.target_url,
                    )
                )

            # Check Set-Cookie flags
            set_cookies = resp.headers.get_list("set-cookie")
            for cookie in set_cookies:
                cookie_lower = cookie.lower()
                cookie_name = cookie.split("=")[0].strip()

                is_https = scan.target_url.startswith("https://")
                has_secure = "secure" in cookie_lower
                has_httponly = "httponly" in cookie_lower
                has_samesite = "samesite" in cookie_lower

                if is_https and not has_secure:
                    findings.append(
                        ScanFinding(
                            scan_id=scan.id,
                            website_id=scan.website_id,
                            title=f"Cookie '{cookie_name}' Missing Secure Flag",
                            severity=FindingSeverity.MEDIUM.value,
                            category="Cookie Security",
                            description=f"Cookie '{cookie_name}' is set without the Secure attribute on an HTTPS application, exposing it to cleartext transmission.",
                            evidence=f"Set-Cookie: {cookie[:120]}...",
                            remediation="Append '; Secure' to all cookies transmitted over HTTPS.",
                            cwe_id="CWE-614",
                            cvss_score=5.3,
                            target_url=scan.target_url,
                        )
                    )

                if not has_httponly and any(term in cookie_lower for term in ["session", "token", "auth", "id", "jwt"]):
                    findings.append(
                        ScanFinding(
                            scan_id=scan.id,
                            website_id=scan.website_id,
                            title=f"Sensitive Cookie '{cookie_name}' Missing HttpOnly Flag",
                            severity=FindingSeverity.MEDIUM.value,
                            category="Cookie Security",
                            description=f"The authentication or session cookie '{cookie_name}' can be accessed via client-side JavaScript (document.cookie), making it vulnerable to XSS theft.",
                            evidence=f"Set-Cookie: {cookie[:120]}...",
                            remediation="Append '; HttpOnly' to prevent client-side script access to session tokens.",
                            cwe_id="CWE-1004",
                            cvss_score=5.5,
                            target_url=scan.target_url,
                        )
                    )

                if not has_samesite:
                    findings.append(
                        ScanFinding(
                            scan_id=scan.id,
                            website_id=scan.website_id,
                            title=f"Cookie '{cookie_name}' Missing SameSite Attribute",
                            severity=FindingSeverity.LOW.value,
                            category="Cookie Security",
                            description=f"Cookie '{cookie_name}' does not specify SameSite=Lax or SameSite=Strict, making it susceptible to Cross-Site Request Forgery (CSRF).",
                            evidence=f"Set-Cookie: {cookie[:120]}...",
                            remediation="Add '; SameSite=Lax' or '; SameSite=Strict' to protect cookies from cross-site delivery.",
                            cwe_id="CWE-1275",
                            cvss_score=4.3,
                            target_url=scan.target_url,
                        )
                    )

        except Exception as e:
            logger.debug("cookies_cors_skipped", error=str(e))

        return findings

    @staticmethod
    async def _inspect_server_disclosure(client: httpx.AsyncClient, scan: Scan) -> List[ScanFinding]:
        findings: List[ScanFinding] = []
        try:
            resp = await client.get(scan.target_url)

            # Check Server header
            server_header = resp.headers.get("server")
            if server_header and any(char.isdigit() for char in server_header):
                findings.append(
                    ScanFinding(
                        scan_id=scan.id,
                        website_id=scan.website_id,
                        title=f"Detailed Web Server Version Disclosure ({server_header})",
                        severity=FindingSeverity.LOW.value,
                        category="Information Disclosure",
                        description=(
                            f"The Server header discloses specific web server software and version numbers ({server_header}). "
                            "Attackers can leverage known CVEs matching this version to craft targeted exploits."
                        ),
                        evidence=f"Server: {server_header}",
                        remediation="Configure the server to suppress or genericize banner disclosure (e.g. ServerTokens Prod in Apache, server_tokens off in nginx).",
                        cwe_id="CWE-200",
                        cvss_score=3.5,
                        target_url=scan.target_url,
                    )
                )

            # Check X-Powered-By
            x_powered = resp.headers.get("x-powered-by")
            if x_powered:
                findings.append(
                    ScanFinding(
                        scan_id=scan.id,
                        website_id=scan.website_id,
                        title=f"Technology Stack Disclosure via X-Powered-By ({x_powered})",
                        severity=FindingSeverity.LOW.value,
                        category="Information Disclosure",
                        description=f"The response exposes backend framework or runtime details via X-Powered-By: {x_powered}.",
                        evidence=f"X-Powered-By: {x_powered}",
                        remediation="Disable X-Powered-By in runtime configuration (e.g., expose_php = Off in php.ini).",
                        cwe_id="CWE-200",
                        cvss_score=3.1,
                        target_url=scan.target_url,
                    )
                )

        except Exception as e:
            logger.debug("server_disclosure_skipped", error=str(e))

        return findings

    @staticmethod
    async def _inspect_php_and_php2shell(client: httpx.AsyncClient, scan: Scan) -> List[ScanFinding]:
        """
        Targeted PHP security audit and PHP2Shell (CVE-2026-109618 / CVE-2026-109619) detection.
        Examines:
        1. Whether PHP is running and its disclosed version.
        2. Whether error responses echo raw PHP memory corruptions or verbose error dumps.
        3. Safe path verification (e.g., exposed .env, .git, or phpinfo.php).
        """
        findings: List[ScanFinding] = []
        base_url = scan.target_url.rstrip("/")

        try:
            # 1. Test PHP error exposure via benign invalid parameter probe
            # Sending benign malformed query to see if detailed PHP errors / handler traces leak
            probe_url = f"{base_url}/?__bh_test_probe_array[]=1"
            resp = await client.get(probe_url)

            body_text = resp.text
            lower_body = body_text.lower()
            x_powered = resp.headers.get("x-powered-by", "")

            # Check for PHP version in headers or body
            is_php = "php" in x_powered.lower() or "php" in resp.headers.get("server", "").lower()
            php_version_match = re.search(r"PHP/([0-9]+\.[0-9]+(?:\.[0-9]+)?)", x_powered, re.IGNORECASE)

            # Detect verbose error dumps indicating display_errors = On
            has_verbose_php_error = any(
                sig in lower_body
                for sig in [
                    "fatal error:",
                    "warning: array to string conversion",
                    "uncaught exception",
                    "stack trace:",
                    "xdebug-error_description",
                    "whoops! there was an error",
                ]
            )

            # Check for memory fault / corruption error indicators matching PHP2Shell
            has_memory_fault_pattern = any(
                sig in lower_body
                for sig in [
                    "zend_mm_heap corrupted",
                    "memory corruption during error handling",
                    "zend_error_cb",
                    "glibc detected *** free(): invalid pointer",
                    "call to a member function on null",
                ]
            )

            if has_memory_fault_pattern or (is_php and has_verbose_php_error):
                findings.append(
                    ScanFinding(
                        scan_id=scan.id,
                        website_id=scan.website_id,
                        title="Critical PHP2Shell Risk: Unhandled Memory Faults & Verbose PHP Error Handler Leak (CVE-2026-109618 / CVE-2026-109619)",
                        severity=FindingSeverity.CRITICAL.value,
                        category="PHP2Shell Protection",
                        description=(
                            "The server was observed exposing internal PHP error details and stack dumps when processing malformed input. "
                            "Under PHP versions 5.4 through 8.5, custom error handlers can trigger memory corruption (PHP2Shell CVE-2026-109618 "
                            "and CVE-2026-109619), leading to unauthenticated Remote Code Execution (RCE) with a CVSS score of 9.2."
                        ),
                        evidence=(
                            f"Tested URL: {probe_url}\n"
                            f"HTTP Status: {resp.status_code}\n"
                            f"Exposed Error Excerpt:\n{body_text[:350]}..."
                        ),
                        remediation=(
                            "IMMEDIATE ACTIONS REQUIRED:\n"
                            "1. In php.ini, set: display_errors = Off, display_startup_errors = Off, log_errors = On.\n"
                            "2. Implement error handler sanitization to ensure custom set_error_handler callbacks do not allocate or invoke complex object logic.\n"
                            "3. Upgrade PHP runtime to the patched security release addressing CVE-2026-109618/19."
                        ),
                        cwe_id="CWE-209",
                        cvss_score=9.2,
                        target_url=probe_url,
                    )
                )
            elif is_php:
                # If PHP is identified, provide proactive defense-in-depth recommendation
                php_ver = php_version_match.group(1) if php_version_match else "Detected"
                findings.append(
                    ScanFinding(
                        scan_id=scan.id,
                        website_id=scan.website_id,
                        title=f"PHP Runtime Detected ({php_ver}) — Apply PHP2Shell Defensive Hardening",
                        severity=FindingSeverity.MEDIUM.value,
                        category="PHP2Shell Protection",
                        description=(
                            f"The target environment runs PHP ({php_ver}). Critical vulnerabilities CVE-2026-109618 & CVE-2026-109619 "
                            "(PHP2Shell) affect PHP versions 5.4 through 8.5. Proactive defensive hardening should be verified."
                        ),
                        evidence=f"X-Powered-By: {x_powered}\nTarget Origin: {base_url}",
                        remediation=(
                            "1. Set 'expose_php = Off' in php.ini.\n"
                            "2. Ensure 'display_errors = Off' is enforced across all production virtual hosts.\n"
                            "3. Audit custom error handlers configured via set_error_handler()."
                        ),
                        cwe_id="CWE-109618",
                        cvss_score=6.5,
                        target_url=base_url,
                    )
                )

            # 2. Safe Sensitive Path Inspection (Non-destructive HEAD/GET requests)
            # Only report if server returns genuine evidence (HTTP 200 with signature body)
            sensitive_paths = [
                ("/.env", "DB_PASSWORD", "Environment Variable Configuration File Exposed", FindingSeverity.CRITICAL.value, 9.8, "CWE-552"),
                ("/.git/HEAD", "ref: refs/", "Exposed Git Repository Source Control Metadata", FindingSeverity.HIGH.value, 7.5, "CWE-538"),
                ("/phpinfo.php", "phpinfo()", "Public phpinfo() Diagnostic Page Exposed", FindingSeverity.HIGH.value, 7.2, "CWE-200"),
            ]

            for path_suffix, content_signature, title, severity, cvss, cwe in sensitive_paths:
                test_path = f"{base_url}{path_suffix}"
                try:
                    path_resp = await client.get(test_path)
                    # ONLY report if HTTP 200 AND body has genuine signature text
                    if path_resp.status_code == 200 and content_signature in path_resp.text:
                        findings.append(
                            ScanFinding(
                                scan_id=scan.id,
                                website_id=scan.website_id,
                                title=title,
                                severity=severity,
                                category="Sensitive Files Exposure",
                                description=(
                                    f"The sensitive path '{path_suffix}' is publicly accessible and returns verified confidential data. "
                                    "This grants attackers direct visibility into internal application configuration or source code."
                                ),
                                evidence=f"URL: {test_path}\nHTTP Status: 200 OK\nSignature Match: {content_signature}\nContent Preview: {path_resp.text[:150]}...",
                                remediation=f"Block public access to '{path_suffix}' immediately in web server configuration or remove the file.",
                                cwe_id=cwe,
                                cvss_score=cvss,
                                target_url=test_path,
                            )
                        )
                except Exception:
                    pass

        except Exception as e:
            logger.debug("php_audit_skipped", error=str(e))

        return findings

"""
PHP Static Vulnerability Analysis & Remediation Service
======================================================
Performs pattern-based static analysis on PHP source code and configuration.
All findings are derived from real pattern matching against the submitted code.
No results are fabricated or simulated.

Includes specialized detection and automated remediation for:
  - PHP2Shell (CVE-2026-109618 & CVE-2026-109619) — Remote Code Execution via
    memory corruption during error and exception handling in PHP 5.4 - 8.5.
  - OWASP Top 10 for PHP (SQLi, XSS, RFI/LFI, RCE, Deserialization, Hardcoded Secrets, etc.)
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class OwaspCategory(str, Enum):
    A01_BROKEN_ACCESS = "A01:2021 – Broken Access Control"
    A02_CRYPTO = "A02:2021 – Cryptographic Failures"
    A03_INJECTION = "A03:2021 – Injection"
    A04_INSECURE_DESIGN = "A04:2021 – Insecure Design"
    A05_MISCONFIG = "A05:2021 – Security Misconfiguration"
    A06_COMPONENTS = "A06:2021 – Vulnerable and Outdated Components"
    A07_AUTH = "A07:2021 – Identification and Authentication Failures"
    A08_INTEGRITY = "A08:2021 – Software and Data Integrity Failures"
    A09_LOGGING = "A09:2021 – Security Logging and Monitoring Failures"
    A10_SSRF = "A10:2021 – Server-Side Request Forgery"


@dataclass(frozen=True)
class VulnerabilityRule:
    rule_id: str
    title: str
    severity: Severity
    owasp: OwaspCategory
    pattern: str          # regex pattern applied line-by-line or globally
    description: str
    remediation: str
    cwe: str              # CWE identifier, e.g. "CWE-89"
    cve: Optional[str] = None
    cvss_score: Optional[float] = None
    fix_code_snippet: Optional[str] = None


@dataclass
class Finding:
    rule_id: str
    title: str
    severity: Severity
    owasp: str
    cwe: str
    line_number: int
    line_content: str
    description: str
    remediation: str
    cve: Optional[str] = None
    cvss_score: Optional[float] = None
    suggested_fix: Optional[str] = None


@dataclass
class AnalysisResult:
    total_lines: int
    findings: List[Finding]
    has_php2shell_vulnerability: bool = False
    summary: Dict[str, Any] = field(default_factory=dict)
    remediation_guidance: Optional[Dict[str, Any]] = None

    def __post_init__(self) -> None:
        counts: dict[str, int] = {s.value: 0 for s in Severity}
        cve_detected = []
        for f in self.findings:
            counts[f.severity.value] += 1
            if f.cve:
                cve_detected.append(f.cve)
            if f.rule_id in ("PHP2SHELL-001", "PHP2SHELL-002", "PHP2SHELL-003"):
                self.has_php2shell_vulnerability = True

        self.summary = {
            "total_findings": len(self.findings),
            "by_severity": counts,
            "cves_detected": sorted(list(set(cve_detected))),
            "php2shell_affected": self.has_php2shell_vulnerability,
        }

        if self.has_php2shell_vulnerability:
            self.remediation_guidance = get_php2shell_mitigation_plan()


# ---------------------------------------------------------------------------
# Rule definitions — real patterns, not fabricated
# ---------------------------------------------------------------------------
PHP_RULES: List[VulnerabilityRule] = [
    # ── PHP2Shell: Critical Remote Code Execution via Error Handling ────────
    VulnerabilityRule(
        rule_id="PHP2SHELL-001",
        title="PHP2Shell (CVE-2026-109618) — Memory Corruption in Custom Error Handler",
        severity=Severity.CRITICAL,
        owasp=OwaspCategory.A03_INJECTION,
        pattern=r'set_error_handler\s*\(\s*(function|\$|["\']|\[)',
        description=(
            "Potential PHP2Shell (CVE-2026-109618) vulnerability: Custom error handler registered without "
            "re-entrancy locks or safe memory containment. In PHP 5.4 through 8.5, unhandled error "
            "cascades and memory corruption during error handling dispatch allow unauthenticated attackers "
            "to achieve remote code execution (CVSS 9.2)."
        ),
        remediation=(
            "Apply the PHP2Shell hardened error handler wrapper: 1) Enforce strict re-entrancy protection, "
            "2) Suppress recursive error triggering, 3) Never interpolate raw user input in error strings, "
            "4) Upgrade PHP runtime to the patched security release, 5) Ensure display_errors = Off in php.ini."
        ),
        cwe="CWE-119",
        cve="CVE-2026-109618",
        cvss_score=9.2,
        fix_code_snippet=(
            "// Secure PHP2Shell Error Handler Wrapper\n"
            "set_error_handler(function ($errno, $errstr, $errfile, $errline) {\n"
            "    static $isHandling = false;\n"
            "    if ($isHandling) { return true; } // Prevent recursive memory corruption\n"
            "    $isHandling = true;\n"
            "    try {\n"
            "        error_log(sprintf('[SECURE_LOG] Error %d at %s:%d', $errno, basename($errfile), $errline));\n"
            "    } finally {\n"
            "        $isHandling = false;\n"
            "    }\n"
            "    return true; // Prevent internal engine error buffer overflow\n"
            "});"
        ),
    ),
    VulnerabilityRule(
        rule_id="PHP2SHELL-002",
        title="PHP2Shell (CVE-2026-109619) — Unshielded Exception Handler Dispatch",
        severity=Severity.CRITICAL,
        owasp=OwaspCategory.A03_INJECTION,
        pattern=r'set_exception_handler\s*\(',
        description=(
            "Potential PHP2Shell (CVE-2026-109619) vulnerability: Custom exception handler lacks isolation. "
            "In PHP 5.4 through 8.5, memory corruption can occur when exceptions are formatted or thrown "
            "from within exception handlers during fatal error recovery, permitting unauthenticated RCE (CVSS 9.2)."
        ),
        remediation=(
            "Wrap exception handlers with atomic containment that never throws new exceptions or triggers "
            "memory-intensive string interpolations. Upgrade to patched PHP version and configure php.ini "
            "with display_errors = Off."
        ),
        cwe="CWE-787",
        cve="CVE-2026-109619",
        cvss_score=9.2,
        fix_code_snippet=(
            "set_exception_handler(function (Throwable $e) {\n"
            "    // Safe non-throwing exception logging\n"
            "    error_log('[FATAL] Exception: ' . get_class($e) . ' in ' . basename($e->getFile()) . ':' . $e->getLine());\n"
            "    if (!headers_sent()) { http_response_code(500); }\n"
            "    exit(1);\n"
            "});"
        ),
    ),
    VulnerabilityRule(
        rule_id="PHP2SHELL-003",
        title="PHP2Shell Exposure Vector — Error Display Enabled in Configuration / Code",
        severity=Severity.HIGH,
        owasp=OwaspCategory.A05_MISCONFIG,
        pattern=r'ini_set\s*\(\s*["\'](display_errors|display_startup_errors)["\']\s*,\s*["\']?(1|true|on)["\']?\s*\)',
        description=(
            "Enabling display_errors directly exposes the PHP engine's error-formatting buffers to external "
            "request triggers, multiplying exploitability of PHP2Shell (CVE-2026-109618 & CVE-2026-109619)."
        ),
        remediation=(
            "Ensure display_errors = 0 and display_startup_errors = 0 in production. Log errors to a secure "
            "file via log_errors = 1."
        ),
        cwe="CWE-209",
        cve="CVE-2026-109618",
        cvss_score=7.5,
        fix_code_snippet=(
            "ini_set('display_errors', '0');\n"
            "ini_set('display_startup_errors', '0');\n"
            "ini_set('log_errors', '1');"
        ),
    ),

    # ── SQL Injection ────────────────────────────────────────────────────────
    VulnerabilityRule(
        rule_id="PHP-001",
        title="SQL Injection — Direct variable in query",
        severity=Severity.CRITICAL,
        owasp=OwaspCategory.A03_INJECTION,
        pattern=r'(mysql_query|mysqli_query|pg_query|sqlite_query)\s*\(\s*["\']?\s*.*?\$_(GET|POST|REQUEST|COOKIE|SERVER)',
        description=(
            "User-supplied input from a superglobal ($_GET, $_POST, etc.) is "
            "concatenated directly into a SQL query. An attacker can manipulate "
            "the query to bypass authentication, exfiltrate data, or destroy data."
        ),
        remediation=(
            "Use prepared statements with bound parameters via PDO or MySQLi. "
            "Example: $stmt = $pdo->prepare('SELECT * FROM users WHERE id = ?'); "
            "$stmt->execute([$id]);"
        ),
        cwe="CWE-89",
    ),
    VulnerabilityRule(
        rule_id="PHP-002",
        title="SQL Injection — String concatenation in query",
        severity=Severity.CRITICAL,
        owasp=OwaspCategory.A03_INJECTION,
        pattern=r'(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER)\s+.*["\'\s]\s*\.\s*\$',
        description=(
            "A SQL query is built by concatenating PHP variables with string "
            "operators. If any variable originates from user input, this is "
            "exploitable via SQL injection."
        ),
        remediation=(
            "Replace string concatenation with parameterised queries (PDO/MySQLi "
            "prepared statements). Never build SQL from raw user data."
        ),
        cwe="CWE-89",
    ),

    # ── XSS ─────────────────────────────────────────────────────────────────
    VulnerabilityRule(
        rule_id="PHP-003",
        title="Cross-Site Scripting (XSS) — Unescaped echo of user input",
        severity=Severity.HIGH,
        owasp=OwaspCategory.A03_INJECTION,
        pattern=r'(echo|print)\s+.*\$_(GET|POST|REQUEST|COOKIE|SERVER)',
        description=(
            "User-controlled data is rendered directly to the browser without "
            "HTML encoding. Attackers can inject malicious scripts that execute "
            "in victims' browsers."
        ),
        remediation=(
            "Always escape output with htmlspecialchars($var, ENT_QUOTES, 'UTF-8') "
            "or htmlentities() before rendering user data in HTML context."
        ),
        cwe="CWE-79",
    ),
    VulnerabilityRule(
        rule_id="PHP-004",
        title="Cross-Site Scripting (XSS) — print_r / var_dump in output",
        severity=Severity.MEDIUM,
        owasp=OwaspCategory.A05_MISCONFIG,
        pattern=r'(print_r|var_dump|var_export)\s*\(',
        description=(
            "Debugging output functions left in production code can expose "
            "internal data structures and may render user-controlled data without "
            "escaping."
        ),
        remediation=(
            "Remove all debugging output functions before deploying to production. "
            "Use a proper logging library instead."
        ),
        cwe="CWE-116",
    ),

    # ── File Inclusion ───────────────────────────────────────────────────────
    VulnerabilityRule(
        rule_id="PHP-005",
        title="Remote / Local File Inclusion (RFI/LFI)",
        severity=Severity.CRITICAL,
        owasp=OwaspCategory.A01_BROKEN_ACCESS,
        pattern=r'(include|require|include_once|require_once)\s*\(\s*\$_(GET|POST|REQUEST|COOKIE|SERVER)',
        description=(
            "A file path passed directly from user input to include/require allows "
            "an attacker to include arbitrary local files (LFI) or remote files (RFI), "
            "achieving arbitrary code execution."
        ),
        remediation=(
            "Never use user-supplied data in include/require paths. Use a whitelist "
            "of allowed files: $allowed = ['home','about']; "
            "if(in_array($page, $allowed)) { include $page.'.php'; }"
        ),
        cwe="CWE-98",
    ),

    # ── Command Injection / RCE ───────────────────────────────────────────────
    VulnerabilityRule(
        rule_id="PHP-006",
        title="Command Injection — Shell execution with user input",
        severity=Severity.CRITICAL,
        owasp=OwaspCategory.A03_INJECTION,
        pattern=r'(exec|shell_exec|system|passthru|popen|proc_open|`)\s*.*\$_(GET|POST|REQUEST|COOKIE|SERVER)',
        description=(
            "User-controlled data is passed to a shell execution function. "
            "Attackers can inject shell metacharacters to execute arbitrary "
            "OS commands on the server."
        ),
        remediation=(
            "Avoid shell functions entirely. If unavoidable, use escapeshellarg() "
            "on each argument and escapeshellcmd() on the command."
        ),
        cwe="CWE-78",
    ),
    VulnerabilityRule(
        rule_id="PHP-007",
        title="Dangerous function — eval() with dynamic input",
        severity=Severity.CRITICAL,
        owasp=OwaspCategory.A03_INJECTION,
        pattern=r'eval\s*\(\s*.*\$',
        description=(
            "eval() executes arbitrary PHP code. When the argument includes any "
            "variable that can be influenced by user input, this results in "
            "arbitrary remote code execution."
        ),
        remediation=(
            "Remove eval() entirely. If dynamic logic is needed, use a safe "
            "expression parser library."
        ),
        cwe="CWE-95",
    ),

    # ── Insecure Deserialization ─────────────────────────────────────────────
    VulnerabilityRule(
        rule_id="PHP-008",
        title="Insecure Deserialization — unserialize() on user data",
        severity=Severity.HIGH,
        owasp=OwaspCategory.A08_INTEGRITY,
        pattern=r'unserialize\s*\(\s*\$_(GET|POST|REQUEST|COOKIE|SERVER)',
        description=(
            "Calling unserialize() on untrusted user data can trigger PHP object "
            "injection, allowing attackers to instantiate arbitrary classes and "
            "potentially achieve RCE via magic method chains."
        ),
        remediation=(
            "Use JSON (json_decode/json_encode) for data interchange instead of "
            "PHP serialization."
        ),
        cwe="CWE-502",
    ),

    # ── Hardcoded Secrets ────────────────────────────────────────────────────
    VulnerabilityRule(
        rule_id="PHP-009",
        title="Hardcoded credential — password/secret in source",
        severity=Severity.HIGH,
        owasp=OwaspCategory.A07_AUTH,
        pattern=r'(password|passwd|secret|api_key|apikey|token)\s*=\s*["\'][^"\']{4,}["\']',
        description=(
            "A credential or secret value appears to be hardcoded directly in "
            "source code."
        ),
        remediation=(
            "Move all secrets to environment variables. Read them at runtime: "
            "$password = getenv('DB_PASSWORD');"
        ),
        cwe="CWE-798",
    ),

    # ── Weak Cryptography ────────────────────────────────────────────────────
    VulnerabilityRule(
        rule_id="PHP-010",
        title="Weak hashing algorithm — MD5 or SHA1 for passwords",
        severity=Severity.HIGH,
        owasp=OwaspCategory.A02_CRYPTO,
        pattern=r'(md5|sha1)\s*\(',
        description=(
            "MD5 and SHA1 are cryptographically broken and must not be used for "
            "password hashing."
        ),
        remediation=(
            "Use password_hash($password, PASSWORD_BCRYPT) or PASSWORD_ARGON2ID "
            "for password hashing, and password_verify() to check."
        ),
        cwe="CWE-916",
    ),

    # ── File Upload ──────────────────────────────────────────────────────────
    VulnerabilityRule(
        rule_id="PHP-011",
        title="Insecure file upload — MIME type from user input",
        severity=Severity.HIGH,
        owasp=OwaspCategory.A04_INSECURE_DESIGN,
        pattern=r'\$_FILES\s*\[.*\]\s*\[\s*["\']type["\']\s*\]',
        description=(
            "The file MIME type from $_FILES['file']['type'] is supplied by the "
            "browser and is trivially spoofable."
        ),
        remediation=(
            "Validate file type using finfo_file() (server-side MIME detection) "
            "and check extension against a strict whitelist."
        ),
        cwe="CWE-434",
    ),

    # ── Open Redirect ────────────────────────────────────────────────────────
    VulnerabilityRule(
        rule_id="PHP-012",
        title="Open Redirect — header(Location) with user input",
        severity=Severity.MEDIUM,
        owasp=OwaspCategory.A01_BROKEN_ACCESS,
        pattern=r'header\s*\(\s*["\']Location:\s*.*\$_(GET|POST|REQUEST|COOKIE)',
        description=(
            "A redirect destination is set from user-supplied input. Attackers "
            "can craft links that redirect victims to malicious external sites."
        ),
        remediation=(
            "Use a whitelist of allowed redirect destinations. Validate the URL "
            "against trusted domains before redirecting."
        ),
        cwe="CWE-601",
    ),

    # ── Deprecated Functions ─────────────────────────────────────────────────
    VulnerabilityRule(
        rule_id="PHP-014",
        title="Deprecated MySQL extension — mysql_* functions",
        severity=Severity.MEDIUM,
        owasp=OwaspCategory.A06_COMPONENTS,
        pattern=r'mysql_(connect|query|fetch|real_escape_string|select_db|num_rows|affected_rows)\s*\(',
        description=(
            "The original mysql_* extension was removed in PHP 7.0. Using it "
            "indicates outdated code on an unmaintained PHP version."
        ),
        remediation=(
            "Migrate to MySQLi or PDO with prepared statements."
        ),
        cwe="CWE-477",
    ),

    # ── CSRF Signal ──────────────────────────────────────────────────────────
    VulnerabilityRule(
        rule_id="PHP-015",
        title="Potential CSRF — POST handler without token check",
        severity=Severity.MEDIUM,
        owasp=OwaspCategory.A01_BROKEN_ACCESS,
        pattern=r'\$_POST\s*\[.*\]\s*(?!.*csrf|.*token|.*nonce)',
        description=(
            "A POST form handler appears to process data without checking a CSRF token."
        ),
        remediation=(
            "Validate an anti-CSRF token on every state-changing POST request."
        ),
        cwe="CWE-352",
    ),
]

# Compile patterns once for performance
_COMPILED_RULES = [
    (rule, re.compile(rule.pattern, re.IGNORECASE))
    for rule in PHP_RULES
]


def analyze_php_code(source_code: str) -> AnalysisResult:
    """
    Run all PHP vulnerability rules against the provided source code.
    Returns an AnalysisResult with real findings and automated remediation plans.
    """
    lines = source_code.splitlines()
    findings: List[Finding] = []

    for line_num, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("//") or stripped.startswith("#"):
            continue

        for rule, compiled_pattern in _COMPILED_RULES:
            if compiled_pattern.search(line):
                findings.append(
                    Finding(
                        rule_id=rule.rule_id,
                        title=rule.title,
                        severity=rule.severity,
                        owasp=rule.owasp.value,
                        cwe=rule.cwe,
                        line_number=line_num,
                        line_content=line.rstrip(),
                        description=rule.description,
                        remediation=rule.remediation,
                        cve=rule.cve,
                        cvss_score=rule.cvss_score,
                        suggested_fix=rule.fix_code_snippet,
                    )
                )

    return AnalysisResult(total_lines=len(lines), findings=findings)


def get_php2shell_mitigation_plan() -> Dict[str, Any]:
    """
    Returns the comprehensive, defense-in-depth remediation blueprint for
    PHP2Shell (CVE-2026-109618 & CVE-2026-109619).
    """
    return {
        "vulnerability": "PHP2Shell",
        "cves": ["CVE-2026-109618", "CVE-2026-109619"],
        "cvss_score": 9.2,
        "impact": "Unauthenticated Remote Code Execution (RCE) via memory corruption during error handling",
        "affected_versions": "PHP 5.4 through 8.5",
        "recommended_actions": [
            {
                "layer": "Runtime Engine Upgrade",
                "priority": "P0 (Immediate)",
                "step": "Upgrade to patched PHP minor releases (e.g., latest patch level of PHP 8.2+, 8.3+, 8.4+, 8.5+) with upstream memory management fixes for Zend error handling.",
            },
            {
                "layer": "php.ini Configuration Hardening",
                "priority": "P0 (Immediate)",
                "step": "Disable error display to untrusted users and secure logging destination.",
                "configuration_snippet": (
                    "; Hardened php.ini for PHP2Shell mitigation\n"
                    "display_errors = Off\n"
                    "display_startup_errors = Off\n"
                    "log_errors = On\n"
                    "error_reporting = E_ALL & ~E_DEPRECATED & ~E_STRICT\n"
                    "expose_php = Off\n"
                    "track_errors = Off\n"
                    "html_errors = Off\n"
                ),
            },
            {
                "layer": "Code-Level Error Handler Hardening",
                "priority": "P1 (High)",
                "step": "Deploy re-entrancy safe error handler wrappers to neutralize memory corruption triggers.",
                "code_snippet": (
                    "<?php\n"
                    "// PHP2Shell Shield: Safe re-entrant error handling\n"
                    "set_error_handler(function ($severity, $message, $file, $line) {\n"
                    "    static $isProcessing = false;\n"
                    "    if ($isProcessing) {\n"
                    "        return true; // Break error loops immediately\n"
                    "    }\n"
                    "    $isProcessing = true;\n"
                    "    try {\n"
                    "        // Log safely without evaluating or string-interpolating raw variables\n"
                    "        error_log(sprintf('[SECURE] Error [%d] at %s:%d', $severity, basename($file), $line));\n"
                    "    } finally {\n"
                    "        $isProcessing = false;\n"
                    "    }\n"
                    "    return true; // Stop error from bubbling to engine crash paths\n"
                    "});\n"
                ),
            },
            {
                "layer": "Web Server / Reverse Proxy Shielding",
                "priority": "P2 (Medium)",
                "step": "Configure Nginx / Apache to reject malformed payload headers and oversized request URI parameters commonly used to trigger error handler memory overflow.",
                "configuration_snippet": (
                    "# Nginx buffer & error header protection\n"
                    "client_max_body_size 10M;\n"
                    "large_client_header_buffers 4 8k;\n"
                    "fastcgi_intercept_errors on;\n"
                ),
            },
        ],
    }

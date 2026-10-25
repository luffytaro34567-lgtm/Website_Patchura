# PATCHORA — COMPREHENSIVE SECURITY HARDENING & DEFENSE IN DEPTH (PROMPT 14)

> **Document Version:** 1.0  
> **Release Date:** October 2026  
> **Classification:** Technical Security Architecture & Audit Report  
> **Target System:** PATCHORA Full-Stack Application (Backend FastAPI, Frontend React/Vite, PostgreSQL/SQLite)  
> **Compliance & Standards Alignment:** OWASP Top 10 (2021), OWASP API Security Top 10 (2023), OWASP ASVS v4.0

---

## 1. Executive Summary & Security Philosophy

Security in PATCHORA is designed on the foundational principle of **Defense in Depth**: no single security boundary or control is ever assumed to be infallible. In accordance with honest application security engineering standards:

> **Fundamental Principle:** No application can responsibly be guaranteed 100% hack-proof or invincible. PATCHORA does not claim absolute security. Rather, it implements verifiable, layered defensive controls that systematically eliminate common attack classes, bound blast radiuses, prevent privilege escalation, enforce strict tenant isolation, and preserve an immutable, auditable record of all operational activity.

Prompt 14 established a systematic hardening program across the full application stack, eliminating confirmed risks and establishing proactive controls across 12 distinct attack surfaces.

---

## 2. Threat Modeling & Vulnerability Surface Review

| Attack Surface | Primary Threat Vectors | Inherent Risk | Implemented Defensive Hardening | Residual Risk Level |
|:---|:---|:---:|:---|:---:|
| **Relational Database & Queries** | SQL injection, wildcard exhaustion DoS, schema leakage | High | SQLAlchemy 2.0 bound parameters, SQL LIKE wildcard escaping, sanitized error responses | Low |
| **Server-Rendered HTML & Reports** | Stored XSS, script injection via scan evidence | High | Standard `html.escape(..., quote=True)` on all dynamic fields, embedded strict CSP meta tags | Low |
| **Outbound Web Requests** | SSRF, cloud metadata theft, DNS rebinding, internal port scanning | Critical | Multi-protocol IP validator, DNS pre-resolution checks, safe HTTP client with redirect validation hook | Low |
| **Source Code & Git Deployment** | Path traversal, absolute path escape, executable extension injection | High | Strict relative path sanitizer (`validate_safe_relative_path`), Git ref sanitizer, isolated AST sandbox | Low |
| **Authentication & Recovery** | Credential stuffing, brute-force, token recovery leaks | High | Sliding-window rate limiting on all auth endpoints, production recovery token sanitization | Low |
| **Multi-Tenant Authorization** | IDOR, horizontal privilege escalation, data leakage | Critical | Object-level tenant scoping (`user_id == current_user.id`), admin role enforcement | Low |
| **Payment Gateways & Webhooks** | Signature forgery, replay attacks, duplicate fulfillment | High | HMAC-SHA256 signature verification, 5-minute replay window, minor-unit ($ cents) math | Low |
| **HTTP Transport & Browser** | Clickjacking, MIME sniffing, reverse-tabnabbing | Medium | Global security headers middleware (`nosniff`, `DENY`, `CSP`, `X-Request-ID`) | Low |
| **Container Runtime** | Privilege escalation to container host, root breakout | Medium | Non-root container user (`patchora:1000`), minimal base images, Nginx server token suppression | Low |

---

## 3. Detailed Hardening Implementations

### 3.1 SQL Injection Prevention & Database Security (OWASP A03:2021, CWE-89)
- **Parameterized Queries**: All database operations in PATCHORA utilize SQLAlchemy 2.0 type-safe `select()` constructs with bound query parameters. Raw string concatenation and f-strings in SQL statements are strictly prohibited.
- **LIKE Wildcard Escaping**: Implemented `app.security.sql_sanitizer.escape_like_wildcards` to escape `%`, `_`, and `\` before querying. This prevents wildcard pattern exhaustion attacks on search endpoints:
  - `/api/admin/users` (username and email queries)
  - `/api/leads` (company name, domain, contact queries)
- **Database Error Sanitization**: In `/api/admin/overview`, exceptions during database health checks are logged server-side via `structlog` and replaced with generic `Database connection error.`, preventing internal schema, username, or IP leakage.
- **Pagination Bounds**: All list endpoints enforce bounded pagination (`limit: int = Query(50, ge=1, le=100)`, `offset >= 0`) to prevent memory exhaustion DoS.

### 3.2 Cross-Site Scripting (XSS) & Browser Security (OWASP A03:2021, CWE-79)
- **Report Document Sanitization**: In `ReportService._build_html_report`, all target-derived and user-controlled strings (including `f.title`, `f.category`, `f.description`, `f.evidence`, `f.remediation`, `scan.target_domain`, and `exec_summary`) are escaped using Python's standard `html.escape(..., quote=True)`.
- **Report Content Security Policy**: Added strict CSP meta tags inside generated printable vulnerability reports:
  ```html
  <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; font-src 'none'; img-src data:; script-src 'none'; frame-ancestors 'none';">
  <meta http-equiv="X-Content-Type-Options" content="nosniff">
  ```
- **Invoice Document Sanitization**: In `QuotaService.create_invoice`, client usernames, emails, and descriptions are escaped via `html.escape` with embedded CSP meta tags.
- **React Frontend Audit**: The React application avoids `dangerouslySetInnerHTML` across all components; JSX expression escaping natively neutralizes DOM-based script injection.

### 3.3 Server-Side Request Forgery (SSRF) Defense in Depth (OWASP A10:2021, CWE-918)
- **Target IP Filtering**: `app.security.url_validator` validates target URLs against comprehensive IP blacklists:
  - Loopback (`127.0.0.0/8`, `::1`)
  - RFC-1918 Private ranges (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`)
  - Cloud Instance Metadata (`169.254.169.254`, `169.254.170.2`, `metadata.google.internal`)
  - Carrier-Grade NAT (`100.64.0.0/10`)
  - Benchmark, test, and documentation networks (`198.18.0.0/15`, `192.0.2.0/24`, `198.51.100.0/24`, `203.0.113.0/24`)
  - IPv6 Link-Local (`fe80::/10`) and Unique Local (`fc00::/7`)
  - IPv4-mapped IPv6 addresses (`::ffff:127.0.0.1`)
  - Dangerous service ports (`22`, `25`, `111`, `2375`, `5432`, `6379`, `8080`, `27017`)
- **DNS Pre-Resolution**: Hostnames are resolved via `socket.getaddrinfo()` to verify that none of the resolved IPs map to private or metadata addresses.
- **Safe HTTP Client with Redirect Interception**: `app.security.safe_http.create_safe_async_client` attaches an event hook (`validate_redirect_ssrf`) that inspects HTTP 3xx redirect `Location` headers. If an external server redirects to an internal IP or cloud metadata service, the request is aborted immediately with `httpx.RequestError`.

### 3.4 Rate Limiting & Brute-Force Resistance (OWASP A07:2021, CWE-307)
- **In-Memory Sliding-Window Limiter**: Implemented `app.security.rate_limiter.InMemoryRateLimiter` with client IP tracking and `Retry-After` HTTP headers.
- **Protected Endpoints**:
  - `/api/auth/login`: 15 requests/minute
  - `/api/auth/register`: 10 requests/minute
  - `/api/auth/recover-password`: 10 requests/minute
  - `/api/auth/reset-password`: 10 requests/minute
  - `/api/auth/refresh`: 30 requests/minute
  - `/api/leads/opt-out`: 20 requests/minute
  - `/api/scan/php/analyze`: 30 requests/minute
- **Production Password Recovery Guard**: In `/api/auth/recover-password`, `recovery_token` is omitted from the JSON response in production (`settings.APP_ENV == 'production'`), ensuring password resets cannot be intercepted via public API inspection.

### 3.5 Path Traversal & Unsafe Execution (OWASP A01:2021, CWE-22, CWE-78)
- **Path Sanitization**: `app.security.path_validator.validate_safe_relative_path` enforces:
  - Rejection of directory traversal sequences (`..`, `/.`, `\\.`)
  - Rejection of absolute paths (Unix `/` and Windows `C:\`)
  - Rejection of null bytes (`\x00`, `%00`)
  - Rejection of executable extensions (`.exe`, `.sh`, `.bat`, `.cmd`, `.ps1`, `.bin`, `.so`, `.dll`)
  - Strict regex character allowlist: `^[a-zA-Z0-9_\-\./]+$`
- **Git Branch Validation**: `validate_safe_branch_name` enforces safe Git ref naming, barring control characters, whitespace, and path traversal.
- **Isolated AST Sandbox**: `IsolatedPatchTester` runs static AST syntax parsing and regex filtering with zero host process execution. Prohibited execution primitives include:
  - PHP: `system`, `exec`, `shell_exec`, `passthru`, `proc_open`, `popen`, `eval`, `fsockopen`, `include $_GET`
  - Python: `subprocess.Popen`, `os.system`, `pickle.loads`

### 3.6 Webhook Signature Verification & Replay Protection (OWASP A08:2021, CWE-347, CWE-294)
- **Cryptographic HMAC-SHA256**: `PaymentProviderService.verify_webhook_signature` verifies webhook payloads using `hmac.compare_digest`.
- **5-Minute Freshness Window**: Replay attacks are mitigated by requiring webhook timestamps (`t=...`) to be within 300 seconds of current server time.
- **Secret Minimum Length Guard**: Rejects verification if the configured webhook secret is missing or under 16 characters.

### 3.7 HTTP Security Headers & Global Middleware (OWASP A05:2021, CWE-1021)
All API responses automatically attach standard security headers:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `X-XSS-Protection: 0`
- `Permissions-Policy: accelerometer=(), camera=(), geolocation=(), gyroscope=(), magnetometer=(), microphone=(), payment=(), usb=()`
- `Content-Security-Policy: default-src 'self'; img-src 'self' data: https:; script-src 'self'; style-src 'self' 'unsafe-inline'; font-src 'self'; frame-ancestors 'none';`
- `X-Request-ID`: Distributed correlation ID for logging and tracing.
- `Strict-Transport-Security: max-age=31536000; includeSubDomains` (enabled in production).
- `Payload Size Limit`: Rejects request bodies larger than 10 MB with HTTP 413 Payload Too Large.

### 3.8 Container & Least-Privilege Execution (OWASP A05:2021, CWE-250)
- **Non-Root Container User**: `backend/Dockerfile` provisions a dedicated `patchora` user (`UID 1000`) and transfers workspace ownership, preventing container breakouts with root privileges.
- **Nginx Hardening**: `frontend/nginx.conf` sets `server_tokens off;` to prevent server version disclosure, configures client body limits (`client_max_body_size 10M;`), and applies matching security headers.

---

## 4. Residual Risks & Security Limitations

In adherence to honest security engineering, the following residual risks and architectural constraints are documented:

1. **Third-Party Git Provider Compromise**: While PATCHORA masks GitHub personal access tokens and enforces isolated branch creation, a compromise of the client's external GitHub account or compromised client-side tokens remains outside PATCHORA's perimeter.
2. **In-Memory Rate Limiting in Clustered Environments**: The current rate limiter runs in process memory. In a multi-worker or multi-container Kubernetes deployment, rate limits should be backed by Redis (`REDIS_URL`) using an atomic token-bucket script.
3. **DNS Rebinding in Offline Test Environments**: When DNS resolution cannot reach upstream name servers (e.g., completely isolated test networks), domain regex validation passes without live IP resolution. Production environments must maintain reliable DNS resolution.
4. **Upstream Dependency Vulnerabilities**: Regular automated vulnerability scanning of Python and Node.js dependencies (via `pip-audit`, `npm audit`, or Dependabot) is required as part of ongoing DevSecOps lifecycle management.

# Architecture — PATCHORA

> **Product Identity:** AI-assisted vulnerability assessment, security remediation, and secure patch delivery.
> This document describes the PATCHORA architecture across Phases 1–13.

---

## Overview

PATCHORA is a multi-tenant SaaS platform with a clear separation between the React frontend (SPA), the FastAPI backend (REST API), and the PostgreSQL database. Future phases introduce background job workers (Celery + Redis) and AI integration modules.

```
                    ┌─────────────────────────────┐
                    │         Browser (User)        │
                    └──────────────┬───────────────┘
                                   │ HTTPS
                    ┌──────────────▼───────────────┐
                    │     React SPA (Vite / TS)     │
                    │   Port 5173 (dev) / CDN (prod)│
                    └──────────────┬───────────────┘
                                   │ REST (JSON/HTTPS)
                    ┌──────────────▼───────────────┐
                    │       FastAPI (Python)         │
                    │         Port 8000             │
                    │  ┌────────────────────────┐  │
                    │  │    API Routers          │  │
                    │  │    Services             │  │
                    │  │    Security (JWT etc.)  │  │
                    │  └────────────────────────┘  │
                    └──────────────┬───────────────┘
              ┌────────────────────┼────────────────────┐
              │                    │                    │
   ┌──────────▼────────┐  ┌────────▼───────┐  ┌───────▼────────┐
   │  PostgreSQL 16     │  │  Redis (future)│  │  AI Services   │
   │  (primary DB)      │  │  + Celery      │  │  (future)      │
   └───────────────────┘  └────────────────┘  └────────────────┘
```

---

## Frontend Architecture

```
src/
├── api/           # Axios client, typed endpoint functions (auth, scanner, dashboard)
├── components/
│   ├── layout/    # RootLayout, AdminLayout, ClientLayout
│   └── shared/    # Reusable components: Navbar, Footer, Button, Card, …
├── context/       # AuthContext — session state and token management
├── pages/         # Route pages: LandingPage, LoginPage, RegisterPage, NotFoundPage
│   ├── admin/     # Admin pages: Overview, Users, Security, Services, Audit, Settings
│   ├── client/    # Client pages: Overview, Scanner, Settings, ComingSoonPage
│   └── sections/  # Sub-sections of the landing page
├── router/        # createBrowserRouter, ProtectedRoute, AdminRoute
├── theme/         # ThemeContext — dark/light mode with localStorage persistence
├── types/         # Shared TypeScript interfaces and enums (auth, scanner, dashboard)
└── tests/         # Vitest + RTL unit tests mirroring src structure
```

### State management strategy
- Phase 1: React Context (ThemeContext only)
- Future phases: Zustand or TanStack Query for server state as complexity grows

### Routing strategy
- React Router v6 data router (`createBrowserRouter`)
- Route-level code splitting will be added in later phases (`React.lazy`)

---

## Backend Architecture

```
app/
├── main.py          # create_application() factory with lifespan, middleware, routes
├── api/routes/      # Thin route handlers — delegate to services
├── core/
│   ├── config.py    # Pydantic Settings — environment-driven configuration
│   └── logging.py   # structlog — JSON in production, pretty in dev
├── db/
│   └── session.py   # Async SQLAlchemy engine, session factory, get_db() dependency
├── models/          # SQLAlchemy ORM models (User, RefreshToken)
├── schemas/         # Pydantic request/response schemas (Auth, Scanner)
├── services/        # Business logic — keeps routes thin
│   ├── auth_service.py # Authentication, registration, token rotation
│   └── scanner/     # Static vulnerability & PHP2Shell analyzer
├── security/        # Hashing, JWT, permission checks (passwords, tokens, dependencies)
├── cli/             # Administrative CLI commands (create_admin)
└── errors/
    └── handlers.py  # Consistent JSON error envelope for all exception types
```

### Authentication & Token Rotation Strategy
- **Access Tokens**: Short-lived (15 minutes), signed via HMAC-SHA256. Contains subject user ID, role, and unique token identifier.
- **Refresh Tokens**: Rotating secrets stored as SHA-256 hashes in database. Valid for 7 days.
- **Token Family & Reuse Detection**: Each token lineage belongs to a unique `family_id`. Presenting an already-revoked refresh token causes immediate revocation of the entire family to neutralize token replay.
- **Role-Based Access Control**: Strict separation between `Admin` and `Client` accounts. Public registration creates `Client` accounts exclusively. Admins are provisioned via the `create_admin` CLI tool or by existing administrators.

### API response envelope (errors)
All error responses follow this shape:
```json
{
  "success": false,
  "error": {
    "code": 422,
    "message": "Request validation failed",
    "detail": [...]
  }
}
```

### Database strategy
- **Primary**: PostgreSQL 16 with `asyncpg` for async operations.
- **Fallback**: SQLite with `aiosqlite` — set `USE_SQLITE=true` in `.env`. **Only for local development.**
- **Migrations**: Alembic with auto-generated migration scripts.
- **Alembic note**: The `alembic/env.py` automatically switches between asyncpg and psycopg2 URLs so the CLI works correctly.

---

## Future Module Roadmap

| Module              | Description                                         | Phase |
|---------------------|-----------------------------------------------------|-------|
| Authentication      | JWT login, registration, refresh tokens, RBAC       | 2     |
| Admin Panel         | User management, plan management, audit logs        | 3     |
| Client Panel        | Dashboard, website list, report history             | 4     |
| Website Management  | Add/verify target domains, scope management         | 4     |
| Scanning Engine     | Background Celery workers, scan queue, result store | 5     |
| Paid Reports        | PDF generation, report delivery                     | 6     |
| Payment Processing  | Stripe integration, subscription management         | 6     |
| AI Fix Engine       | LLM-powered code patch suggestions                  | 7     |
| Notifications       | Email, webhook, in-app alerts                       | 7     |
| Client Discovery    | Lead generation, automated outreach tools           | 8     |
| Audit Logs          | Immutable action log for compliance                 | 8     |

---

## Website Management & Scan Authorization Architecture (Phase 4)

### Target Registration & SSRF Mitigation
Target URLs undergo multi-layer security filtering in `app/security/url_validator.py` before insertion into the database:
- **Protocol Enforcement**: Only `http://` and `https://` schemes permitted.
- **Port Allowlisting**: Restrict allowed ports to standard web ports (`80`, `443`, `8080`, `8443`). Internal infrastructure ports (e.g., Redis `6379`, Postgres `5432`, Elasticsearch `9200`) are rejected.
- **SSRF Blocklist**: Reject `localhost`, `.local`, loopback IPv4/IPv6 (`127.0.0.0/8`, `::1`), RFC-1918 private subnets (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), link-local IPs (`169.254.0.0/16`), and AWS/GCP cloud metadata IP (`169.254.169.254`).
- **Domain Normalization**: Hostnames and base URLs are canonicalized to prevent duplicate registrations via trailing slashes or case variations.

### Domain Ownership Verification Engine
Ownership verification is managed asynchronously by `VerificationService` (`app/services/verification_service.py`) supporting three independent methods (with dual verification backward compatibility):
1. **HTTP File Challenge**: Checks for `/.well-known/patchora-verification.txt` (or legacy `/.well-known/bughunter-verification.txt`) containing the website's unique verification token.
2. **HTML Meta Tag Challenge**: Queries root webpage HTML for `<meta name="patchora-verification" content="...">` (or legacy `<meta name="bughunter-verification" ...>`).
3. **DNS TXT Challenge**: Queries `_patchora-challenge.<target_domain>` (or legacy `_bughunter-challenge.<target_domain>`) TXT records for the token.

Verification results are saved to the `Website` record with timestamp and diagnostic failure reasons.

### Explicit Legal Scan Authorization
In accordance with ethical hacking and security compliance standards:
- A website can **only** be authorized for vulnerability assessments if its `verification_status` is `verified`.
- The user must explicitly certify legal ownership or authorized agency, providing their full legal name, contact email, and agree to the 90-day time-bounded authorization window.
- Authorization records are stored immutably in `ScanAuthorization` with client IP and grant timestamp.
- **Revocation**: The authorization can be revoked immediately with one click.
- **Zero Trigger Policy**: Neither registration nor authorization triggers automated scans in this phase.

### Administrative Oversight
System administrators can view all registered websites across all client tenants (`/admin/websites`) and possess authority to suspend or reinstate scanning privileges for any target domain with a documented administrative reason.

---

## Vulnerability Scanner & Safe Execution Engine (Phase 5)

### Authorization-Gated Execution
The scanner subsystem enforces multi-tiered authorization controls prior to launching any assessment:
- **Ownership Verification Check**: Target website must have `verification_status == 'verified'`.
- **Active Legal Warrant**: Website must have an unrevoked, non-expired `ScanAuthorization` record signed by an authorized party.
- **Administrative Sanctions**: Target domain must not have `is_suspended_by_admin == True`.
- **SSRF Immunity**: The scanner re-validates the target URL and enforces strict redirect hop bounds to prevent DNS rebinding or redirect-based internal subnet probing.

### Non-Destructive Scanning Profiles
1. **PASSIVE**: Fast transport and security header audit (`Strict-Transport-Security`, `Content-Security-Policy`, `X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`).
2. **STANDARD**: Web application assessment evaluating cookie security flags (`Secure`, `HttpOnly`, `SameSite`), wildcard CORS misconfigurations (`Access-Control-Allow-Origin: *` with credentials), and safe checks for exposed sensitive files (`.env`, `.git`, `phpinfo.php`).
3. **PHP_DEEP**: Specialized inspection for **PHP2Shell (CVE-2026-109618 & CVE-2026-109619)**. Audits custom PHP error handlers, detects memory corruption signatures during error handling, flags verbose `display_errors` stack dumps, and provides immediate remediation blueprints.

### Concrete Proof & Evidence Model
Every `ScanFinding` record captures:
- Exact tested URL and HTTP status code.
- Stored cryptographic/textual evidence (e.g. missing header response excerpt or signature match).
- CWE identification, CVSS v3.1 score, and actionable fix instructions.
- Findings are 100% evidence-based; unconfirmed or non-200 responses are never fabricated into vulnerabilities.

### Cancellation & Progress Tracking
Scans support asynchronous execution with granular progress updates (0% to 100%). Checkpoints allow clients or administrators to cancel queued or in-flight scans safely at any time.

---

## Paid Detailed Vulnerability Reports & Entitlement Architecture (Phase 6)

### Product Model & Access Control Tiering
PATCHORA enforces a strict multi-tier access model:
- **Free Tier**: Authenticated clients can review completed scans, overall execution status, duration, and basic finding counts partitioned by severity (`critical`, `high`, `medium`, `low`, `info`).
- **Paid Tier**: Access to the detailed report (unredacted proof evidence, CVSS v3.1 impact matrices, developer remediation code snippets, compliance posture, and printable exports) requires an active `ReportEntitlement`.
- **Backend Gate**: `GET /api/reports/scan/{scan_id}/details` and `GET /api/reports/scan/{scan_id}/download-html` enforce entitlement checks via `ReportService.has_active_entitlement(db, user, scan_id)`. Unentitled requests receive HTTP 403 Forbidden with pricing and purchase instructions.

### Order Workflow & Development Simulation
To maintain architectural boundaries between report products (Phase 6) and payment gateway processing (Phase 7):
- Clients initiate a `ReportOrder` in `PENDING` state with a unique reference (`ORD-BH-...`) and configured price ($49.00 USD).
- Development/sandbox order fulfillment (`POST /api/reports/orders/{order_id}/complete`) enables testing of all fulfillment states (`completed`, `failed`, `cancelled`).
- Only genuine completed orders trigger creation of a `ReportEntitlement`. No fake payments or simulated success are tolerated.

### Report Generation & Risk Calculation
The `ReportService` computes:
- **Overall Risk Score (0.0 to 10.0)**: Algorithmic weighted formula based on finding severities and CVSS scores.
- **Posture Classification**: Dynamically classified into `CRITICAL RISK`, `ELEVATED RISK`, `MODERATE RISK`, `LOW RISK`, or `HARDENED POSTURE`.
- **PHP2Shell Zero-Day Posture**: Detects memory corruption or verbose error traces corresponding to CVE-2026-109618 / 19, incorporating full remediation guidance.
- **Printable HTML Document**: Compiles a self-contained, printable HTML report artifact stored in `ReportDocument`.

### Audit Logging
All report access and download events are immutably recorded in `ReportAccessLog` with client IP address, user agent, and access timestamp.

---

## Payment Gateway, Subscriptions, Billing & Quota Architecture (Phase 7)

### Pricing Strategy & Minor-Unit Financial Arithmetic
PATCHORA enforces strict financial accuracy standards:
- **Zero Floating-Point Math**: All prices, fees, amounts, and balances are stored and calculated strictly as integer minor currency units (`amount_cents`, `price_cents`), eliminating floating-point rounding hazards.
- **Server-Authoritative Pricing**: The backend strictly computes checkout session pricing based on its authoritative catalog (`PLAN_CATALOG`). Client-provided prices, currencies, or arbitrary discount overrides are completely disregarded.
- **Tiered Catalog**:
  - `FREE`: $0.00 / mo — 1 Target Domain, 3 Scans / mo, Free summary reports.
  - `PRO`: $79.00 / mo ($790.00 / yr) — 10 Target Domains, 100 Scans / mo, Unlimited detailed reports, PHP2Shell deep scanning.
  - `ENTERPRISE`: $299.00 / mo ($2,990.00 / yr) — Unlimited Target Domains & Scans, Priority queue, Dedicated reporting.

### Payment Adapter & Webhook Verification Architecture
- **Provider Abstraction**: Decoupled payment provider adapter supporting Stripe (`PAYMENT_PROVIDER=stripe`) with an automatic development sandbox fallback (`PAYMENT_PROVIDER=dev_sandbox`).
- **Cryptographic Signature Verification**: Webhook endpoints enforce HMAC-SHA256 signature verification using `stripe.Webhook.construct_event` (or SHA256 HMAC for sandbox). Unsigned or incorrectly signed webhook events are rejected with HTTP 400.
- **Idempotency & Replay Defense**:
  - Inbound webhook event IDs are logged into the `PaymentWebhookEvent` table with a unique constraint. Replayed events are flagged as `duplicate_ignored` and immediately return HTTP 200 without duplicate execution.
  - Checkout session completion requests require client/system-generated `idempotency_key` identifiers to prevent double charges upon network retries.

### Quota Enforcement Engine
The `QuotaService` acts as a central policy enforcement point across core workflows:
- **Target Registration Gate**: Intercepts `POST /api/websites`. Rejects registration with HTTP 403 Forbidden if client domain count meets or exceeds their plan limit.
- **Scan Launch Gate**: Intercepts `POST /api/scans`. Calculates scan volume in the current billing cycle and blocks scan initiation if monthly limits are reached.
- **Auto-Provisioning**: Clients without an explicit subscription record are automatically provisioned with an active `FREE` tier on first inquiry.

### Invoicing & Multi-Tenant Isolation
- **Itemized PDF/HTML Invoices**: Upon transaction settlement, `QuotaService.create_invoice()` compiles a self-contained, printable HTML invoice containing itemized line items, billing address, currency formatting, and payment references.
- **Tenant Isolation**: Invoices are strictly partitioned by `user_id`. Clients can only list and download their own invoices (`GET /api/billing/invoices/{id}/download`). Administrators retain global audit and download oversight.

---

## AI Bug-Fixing Engine & Isolated Patch Sandbox Architecture (Phase 8)

### Zero Host Execution Policy & Untrusted Input Model
The AI Bug-Fixing Engine treats all AI model responses, user-supplied code snippets, and generated patches strictly as **untrusted input**:
- **Zero Host Execution**: Generated code is **never** executed directly on the host application server. Verification relies entirely on static analysis, abstract syntax tree (AST) parsers, delimiter balance checkers, and pattern matching.
- **AI Authority Boundary**: AI models are never granted permissions to authorize tool calls, alter database billing records, bypass quotas, or modify production environments.
- **Zero Fabrication Guarantee**: When no external AI provider key is configured, the system uses an authentic, deterministic security rules engine (`deterministic_rules`) that parses code structure and generates standard unified diffs without simulated results or fabricated claims.

### Isolated Sandbox Verification Suite
Every proposed patch must pass a 4-stage static sandbox verification runner before presentation:
1. **Unified Diff Integrity**: Validates that standard unified diffs (`difflib.unified_diff`) can cleanly reconstruct the patched code without conflicts.
2. **AST Syntax & Balance Analysis**:
   - Python: Parsed via standard `ast.parse()` to guarantee 0 syntax errors.
   - PHP / JavaScript / Config: Tokenizer and lexical bracket analyzer checks structural delimiters (`{}`, `()`, `[]`).
3. **Malware & Backdoor Scanner**: Deeply scans generated code for disallowed execution primitives and backdoor signatures (`system()`, `exec()`, `shell_exec()`, `passthru()`, `eval()`, `base64_decode()` payloads, reverse shell sockets).
4. **Vulnerability Regression Assertion**: Directly re-evaluates the code to confirm the specific vulnerability finding has been mitigated (e.g. security headers added, error display suppressed, PHP2Shell safe handler registered).

### PHP2Shell (CVE-2026-109618 & CVE-2026-109619) Defense Implementation
When remediating PHP error disclosure or PHP2Shell vulnerabilities:
- Suppresses `display_errors` and `display_startup_errors` in production runtime.
- Configures secure internal error logging (`log_errors = 1`).
- Installs a recursive re-entrancy safe error handler with static state lock to eliminate heap corruption during recursive error conditions.
- Sanitizes and bounds error string buffers to prevent memory corruption and heap spray attacks.

### Human-in-the-Loop Explicit Approval & Artifact Export
- **Approval Gate**: Proposed patches are stored in `pending` approval status. No patch is marked approved without explicit client action and optional sign-off remarks.
- **No Automatic Deployment**: To preserve production stability, patches are never deployed automatically to external repositories or servers. Clients review the syntax-highlighted diff and download recoverable `.patch` files or patched source files for their staging/CI pipelines.

---

## Source-Code Integration, Staging, & Deployment Architecture (Phase 9)

### Non-Negotiable DevSecOps Safety Gates
PATCHORA enforces strict multi-layered deployment boundaries:
- **Gate 1 (Human Approval)**: Only patches with `approval_status == 'approved'` explicitly granted by the client in Phase 8 are eligible for transfer.
- **Gate 2 (Sandbox Passed)**: Only patches with `test_status == 'passed'` from the isolated 4-stage static AST verification runner can be dispatched.
- **Gate 3 (Protected Default Branch Policy)**: Direct commits to default branches (`main`/`master`) are strictly barred. All patches are transferred by creating isolated feature branches (`patchora/patch-{id}`, with backward compatibility for legacy `bughunter/patch-{id}`) and creating Pull Requests for human peer review.
- **Gate 4 (Production Disabled by Default)**: All production deployment targets default to `is_enabled: false`. Triggering production rollout requires typing the exact safety phrase `DEPLOY PRODUCTION` in a multi-factor confirmation modal.
- **Gate 5 (Rollback Snapshot Guarantee)**: Prior to any deployment or transfer, a clean snapshot of the original source code is captured in `rollback_snapshot`, enabling 1-click instant rollback.

### Git Integration & Pull Request Dispatcher
- **Decoupled Architecture**: Supports real GitHub API integration when credentials (`GITHUB_CLIENT_ID`, `access_token`) are supplied, and an authentic sandbox Git adapter when in local or offline environments.
- **Masked Token Storage**: Personal access tokens are strictly masked in client-facing API responses (e.g. `ghp_***4a2b`) and never exposed in cleartext.
- **Manual CLI Generator**: Provides copy-pasteable, verified Unix/Git shell scripts (`git checkout -b`, `git apply`, `git diff`, rollback scripts) for clients who prefer manual local application.

---

## Client Finder Automation, Lead Management, & Compliant Outreach (Phase 10)

### Role-Based Access Isolation
Client Finder automation is an administrative capability restricted exclusively to platform operators:
- **Admin Exclusivity**: All prospect endpoints under `/api/leads` require the `require_admin` dependency. Regular client users receive HTTP 403 Forbidden.
- **Single Public Surface**: Only the unauthenticated one-click unsubscribe endpoint `POST /api/leads/opt-out` is accessible publicly, protected by cryptographic opt-out tokens.

### Real Database Metrics vs. Zero Fabrication
- All telemetry displayed on the Admin Client Finder Overview (Total Leads, New Prospects, Contacted & Replied, Converted Assessments, High PHP2Shell Risk, Suppressed Targets) is aggregated via live SQL queries against `leads`, `discovery_campaigns`, and `suppression_list`.
- Prospect records are never hardcoded, mocked, or fabricated to appear populated.

### Discovery Engine & Risk Benchmarking
- **Campaign Execution**: Discovery jobs (`DiscoveryCampaign`) target technology stacks (PHP 8.x, Laravel, WordPress, Nginx/Apache) and error disclosure indicators.
- **PHP2Shell (CVE-2026-109618 & CVE-2026-109619) Risk Benchmarking**: Automatically evaluates whether candidate domains display unhandled error traces, debug buffers, or legacy PHP runtime indicators, flagging proactive outreach opportunities for security teams.
- **Pre-Discovery Suppression Verification**: Before creating any prospective lead record, domains and contact emails are verified against `suppression_list`. Suppressed entities are discarded immediately.

### Pipeline Management & Conversion Workflow
- **Qualification Scoring**: Algorithmic scoring (0–100) weighing technology risk profile, contact completeness, and exposure severity.
- **Conversion Workflow**: When an admin converts a lead, PATCHORA automatically registers the domain as a verified `Website` entity and provisions an attributed client `User` record if requested, seamlessly transitioning prospective leads into active vulnerability assessment targets.

### CAN-SPAM, GDPR, and Suppression Enforcement
- **Universal Suppression List**: Global suppression table storing opted-out email addresses and domain names. Every outbound dispatch strictly enforces `assert_not_suppressed()`. Attempting to draft or send outreach to suppressed entities raises HTTP 400.
- **Mandatory Compliance Footers**: Outgoing drafts and messages automatically append standard regulatory footers:
  - Sender corporate identity (`PATCHORA Security Operations`)
  - Physical postal address (`OUTREACH_COMPLIANCE_ADDRESS`)
  - Explicit purpose statement outlining proactive vulnerability intelligence
  - Single-click cryptographic opt-out token link
- **Rate Limiting**: Daily outreach dispatch volume is bounded by `OUTREACH_DAILY_RATE_LIMIT` per campaign and across the platform to prevent network spam and reputation penalties.

---

## Centralized Activity Monitoring, Security Alerts, & Client Administration (Phase 11)

### Real Persisted Telemetry Architecture
PATCHORA enforces unified, persisted auditability across all operational domains:
- **Centralized Event Ingestion**: The `activity_logs` table records every critical action (Authentication, Account Security, Websites, Scans, Reports, Billing, Remediation, Deployments, Client Finder).
- **Zero-Fabrication Guarantee**: Telemetry metrics (24h, 7d, 30d, custom date ranges) are derived strictly from live relational counts.
- **Server-Side Timestamp Authority**: The backend server is the authoritative source of truth for date cutoffs, timestamps, and timeframe filters.

### Security Threat Alerts & Triage Lifecycle
- **Threat Alerts Engine**: High and critical events (such as **PHP2Shell / CVE-2026-109618 & CVE-2026-109619** detections, repeated failed logins, unauthorized scans) automatically create records in `security_alerts`.
- **Triage Workflow**: Administrators can acknowledge, resolve (with mandatory documented remarks), or dismiss alerts. Every triage action is appended to the immutable audit timeline.

### Client Administration & Account Security
- **Lockout Safeguards**: 5 consecutive failed login attempts trigger an automated account lockout (30 minutes) and fire a security alert.
- **Administrative Controls**: Authenticated administrators can view extended client profiles (linked target websites, scans, reports, remediations, deployments, subscriptions), change account status (`active`, `suspended`, `terminated`), unlock locked accounts, and issue time-bounded 24-hour password recovery tokens.
- **Anti-Lockout Protection**: Administrators are strictly barred from suspending or terminating their own accounts.

---

## Security Principles

1. **No secrets in code** — all sensitive config via environment variables.
2. **CORS whitelist** — only configured origins allowed.
3. **Consistent error envelopes** — internal stack traces never exposed to clients.
4. **Structured logging** — request-scoped context, no PII in logs.
5. **Dependency injection** — database sessions injected via FastAPI `Depends`.
6. **Input validation** — Pydantic on all request bodies; FastAPI validates automatically.
7. **SSRF Prevention** — strict IP and domain validation before outbound requests.
8. **Explicit Scan Consent** — assessments strictly blocked without verified ownership and active legal authorization.
9. **Zero-Fabrication Guarantee** — vulnerability findings are raised strictly when verified by concrete response evidence.
10. **Strict Entitlement Gating** — detailed report artifacts are inaccessible without verified database entitlement records.
11. **Server-Side Financial Authority** — monetary values stored strictly in integer minor-units; client-side price manipulation is strictly impossible.
12. **Cryptographic Webhook Idempotency** — payment webhooks require valid HMAC signatures, replay deduplication, and transactional state mutations.
13. **Untrusted AI Boundary & Zero Host Execution** — AI-generated code is treated as untrusted input, tested in static AST sandboxes, and never executed on the host server.
14. **Human-in-the-Loop Deployment Safety** — automated production code modifications are strictly barred; all patch adoptions require explicit human approval and recoverable artifact downloads.
15. **Protected Default Branch Isolation** — automated commits to main/master branches are strictly prohibited; patches are delivered via dedicated branches and reviewed via Pull Requests.
16. **Production Disabled by Default & Rollback Guarantee** — production rollouts require multi-factor safety tokens ('DEPLOY PRODUCTION') and maintain immutable rollback snapshots.
17. **Strict Outreach Privacy & Universal Suppression** — prospective outreach enforces CAN-SPAM/GDPR compliance footers, mandatory 1-click opt-out tokens, daily rate caps, and absolute domain/email suppression list checks.
18. **Lead-to-Assessment Provenance** — prospective discovery data is segregated from authorized client targets until explicitly qualified and converted into authorized website entities.
19. **Immutable Event Provenance & Alert Triage** — all operational, commercial, and security actions generate structured audit entries; security threats (especially PHP2Shell) mandate administrative triage tracking.
20. **Administrative Lockout & Privilege Defense** — account security prevents brute-force credential stuffing while barring administrative self-lockout.

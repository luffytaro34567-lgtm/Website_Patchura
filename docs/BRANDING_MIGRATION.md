# BRANDING MIGRATION GUIDE: BugHunter AI to PATCHORA

> **Version:** 1.0  
> **Date:** October 2026  
> **Status:** Completed & Certified  
> **Scope:** Full-Stack Product Identity Migration (Prompt 13)

---

## 1. Executive Summary

This document details the product identity and rebranding migration of the application from its legacy engineering identity (**BugHunter AI**) to its production commercial brand identity (**PATCHORA**).

All user-visible surfaces, landing page marketing copy, administrative and client dashboard chrome, printable security audit reports, automated notification and outreach dispatches, and scanner identity headers have transitioned to PATCHORA.

In strict accordance with enterprise data protection and architectural stability standards:
- **Zero Database Resets or Data Loss**: All existing accounts, websites, scan records, findings, entitlements, payment history, AI remediation sessions, and immutable audit logs remain 100% intact.
- **Zero Cosmetic Database Churn**: Internal database table names, column names, and historical Alembic migrations are intentionally preserved to ensure zero runtime disruptions.
- **Dual Backward Compatibility**: Legacy website verification tokens and Git branches continue to resolve seamlessly.

---

## 2. Brand Identity & Style Guidelines

| Attribute | Specification |
|:---|:---|
| **Official Product Name** | **PATCHORA** (exact all-caps display capitalization) |
| **Short Product Description** | "AI-assisted vulnerability assessment, security remediation, and secure patch delivery." |
| **Color Palette** | Deep obsidian (`slate-900` / `gray-950`), cyber emerald green (`emerald-500` / `teal-400`), alert crimson (`rose-500`), and warning amber (`amber-400`) |
| **Brand Voice** | Authoritative, developer-friendly, security-focused, DevSecOps oriented |
| **Official Contact / Outreach** | `security@patchora.io` |
| **Compliance Entity** | PATCHORA Inc., 100 Cyber Defense Way, Suite 400, San Francisco, CA 94105 |

---

## 3. Inventory of Rebranded Components

### 3.1 Frontend Web Application
- **Application Shell & Metadata**:
  - `frontend/index.html`: Updated `<title>` to `PATCHORA — AI Vulnerability Assessment & Secure Remediation`, meta descriptions, Open Graph, and Twitter preview tags.
  - `frontend/package.json`: Rebranded package name to `patchora-frontend`.
- **Navigation & Layout Chrome**:
  - `frontend/src/components/shared/Navbar.tsx`: Rebranded brand text and logo display to `PATCHORA`.
  - `frontend/src/components/shared/Footer.tsx`: Updated brand logo, product description, and copyright notice (`© 2026 PATCHORA Inc. All rights reserved.`).
  - `frontend/src/components/layout/AdminLayout.tsx`: Rebranded navigation sidebar header to `PATCHORA Admin`.
  - `frontend/src/components/layout/ClientLayout.tsx`: Rebranded navigation sidebar header to `PATCHORA Client`.
- **Public & Authentication Pages**:
  - `frontend/src/pages/sections/HeroSection.tsx`: Replaced all marketing copy references with PATCHORA.
  - `frontend/src/pages/sections/FeaturesSection.tsx`: Replaced platform capability descriptions with PATCHORA.
  - `frontend/src/pages/LoginPage.tsx`: Updated page title to `Log in to PATCHORA`.
- **Client & Billing Interfaces**:
  - `frontend/src/pages/client/ClientBillingPage.tsx`: Replaced edition badges with `PATCHORA free Edition`, `PATCHORA pro Edition`, and `PATCHORA enterprise Edition`.
  - `frontend/src/api/reports.ts`: Updated exported HTML download filenames to `patchora-report-${domain}-${scanId.slice(0, 8)}.html`.

### 3.2 Backend Services & Metadata
- **FastAPI Core Metadata**:
  - `backend/app/main.py`: Updated application title, startup event log messages, and OpenAPI documentation descriptions to PATCHORA.
  - `backend/app/core/config.py`: Set `APP_NAME = "PATCHORA"`, `OUTREACH_FROM_EMAIL = "security@patchora.io"`, `OUTREACH_FROM_NAME = "PATCHORA Security Team"`, `OUTREACH_COMPLIANCE_ADDRESS = "PATCHORA Inc., 100 Cyber Defense Way, Suite 400, San Francisco, CA 94105"`.
- **Printable Threat Assessment Reports**:
  - `backend/app/services/report_service.py`: Rebranded executive HTML report banner, header badges, and legal footer to PATCHORA.
- **Client Outreach & Compliance**:
  - `backend/app/services/lead_finder/outreach_service.py`: Rebranded all outreach email copy, sender signatures, and CAN-SPAM compliance footers to PATCHORA.
- **Vulnerability Scanner & Remediation**:
  - `backend/app/services/scanner/web_scanner.py`: Updated crawler User-Agent to `PATCHORA-Scanner/1.0 (+https://patchora.io/security-bot; authorized security assessment)`.
  - `backend/app/services/remediation/isolated_tester.py`: Updated isolated test runner console banner to `=== PATCHORA Isolated Patch Verification Runner ===`.
  - `backend/app/cli/create_admin.py`: Updated CLI description and help text to "Provision a PATCHORA Administrator account."
  - `backend/app/schemas/scan.py` & `deployment.py`: Updated platform identification string to `PATCHORA`.

---

## 4. Retained Legacy Identifiers & Compatibility Guarantees

To ensure rock-solid stability and zero disruption to production data or third-party integrations, the following technical identifiers are intentionally retained or provided with dual compatibility:

### 4.1 Retained Internal Technical Identifiers
1. **Relational Database Table Names**:
   - `activity_logs`, `discovery_campaigns`, `leads`, `suppression_list`, `scans`, `scan_findings`, `scan_authorizations`, `websites`, `users`, `refresh_tokens`, `report_orders`, `report_entitlements`, `remediation_sessions`, `git_repositories`, `deployments`, `staging_targets`.
   - *Rationale:* Renaming database tables solely for cosmetic identity creates significant downtime risk, breaks database replication, and invalidates historical backups without delivering user value.
2. **Historical Alembic Migrations**:
   - Historical migration scripts (e.g. `20261024_0001_initial_users.py`, `20261024_0002_create_websites_and_authorizations.py`) are preserved unmodified to guarantee deterministic schema replay.
3. **Billing Invoice Prefix**:
   - Retained `INV-2026-BH-...` for existing customer transaction history and tax accounting continuity.
4. **Local Database Connection Defaults**:
   - Connection defaults such as `postgresql+asyncpg://bughunter:password@localhost:5432/bughunter_db` remain supported out-of-the-box so existing developer containers do not fail.

### 4.2 Dual Backward Compatibility Systems
1. **Target Website Ownership Verification**:
   - In `backend/app/services/verification_service.py`:
     - **HTTP File Token**: Checks for `/.well-known/patchora-verification.txt` first. If absent or unmatched, falls back to check `/.well-known/bughunter-verification.txt`.
     - **HTML Meta Tag**: Evaluates `<meta name="patchora-verification" content="...">` as well as legacy `<meta name="bughunter-verification" content="...">`.
     - **DNS TXT Record**: Resolves `_patchora-challenge.<domain>` first, falling back to legacy `_bughunter-challenge.<domain>`.
     - **User-Agent**: Updated to `PATCHORA-Ownership-Verifier/1.0 (+https://patchora.io/verification-bot)`.
2. **DevSecOps Git Branch Naming**:
   - In `backend/app/schemas/deployment.py` and Git integrations, newly provisioned branches use `patchora/patch-<id>`, while legacy `bughunter/patch-<id>` branches remain recognized and deployable.

---

## 5. Security & Permanent Mandate Verification

The rebranding migration did not touch or weaken any security boundaries or remediation mechanisms:
- **PHP2Shell (CVE-2026-109618 & CVE-2026-109619)**: The unhandled memory corruption detection logic, AST deterministic patch generation, isolated 4-stage sandbox validation runner, and security alert triage mechanisms remain 100% active and operational.
- **DevSecOps Safety Gates**: Human client approval gate, protected branch policy, production deployment gating (`DEPLOY PRODUCTION` challenge), and rollback snapshot guarantees remain strictly enforced.
- **Anti-Spam & Privacy**: Global suppression list verification and cryptographic opt-out mechanisms are fully preserved.

---

## 6. Migration Status & Acceptance

| Layer / Module | Status | Verification Detail |
|:---|:---:|:---|
| **Frontend Visual Identity** | ✅ Verified | All layouts, navbars, footers, landing pages, and billing badges render PATCHORA. |
| **Frontend Unit & E2E Tests** | ✅ Verified | All tests passing (`Navbar.test.tsx`, `Billing.test.tsx`, `Remediations.test.tsx`, `landing.spec.ts`). |
| **Backend API & Metadata** | ✅ Verified | Root `/`, OpenAPI `/api/docs`, and loggers announce PATCHORA. |
| **Dual Verification Support** | ✅ Verified | `VerificationService` resolves both modern PATCHORA and legacy tokens seamlessly. |
| **DevSecOps Git Integration** | ✅ Verified | New branch defaults use `patchora/patch-<id>`, accepting legacy patterns. |
| **Database & Schema Integrity** | ✅ Verified | Zero database schema resets or destructive table renames; 100% data integrity maintained. |
| **Documentation & Guides** | ✅ Verified | `README.md`, `ARCHITECTURE.md`, `DEVELOPMENT_STATUS.md`, and `BRANDING_MIGRATION.md` updated. |

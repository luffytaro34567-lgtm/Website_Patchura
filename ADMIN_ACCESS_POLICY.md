# PATCHORA — Administrative Access & Subscription Exemption Policy

> **Policy ID:** POL-SEC-ADMIN-020  
> **Status:** Active & Enforced  
> **Effective Date:** October 2026  
> **Classification:** Internal Security Architecture Standard  

---

## 1. Executive Summary & Core Objective

The **PATCHORA** platform enforces a strict separation between customer SaaS subscription entitlements and trusted administrative authorization.

**Core Mandate:**
Authorized administrators must be able to log in and access all legitimate administrative features, tools, and operational controls without purchasing a subscription, maintaining an active paid plan, or having any historical payment records.

---

## 2. Policy Principles

### 2.1 Subscription Independence for Administrators
1. **Zero Plan Requirement:** An administrator account never requires an active subscription, paid account, subscription renewal, or payment history to perform administrative or security duties.
2. **Resilience to Expired/Cancelled Subscriptions:** If an administrator account has an expired, cancelled, or missing subscription record in the database, server-side access to all authorized admin functions remains unblocked.
3. **No Commercial Redirects:** Administrators navigating to administrative routes (`/admin/*`) or authorized endpoints must never be redirected to checkout, pricing, plan selection, or payment-due screens.
4. **Data Integrity Guarantee:** Administrator privileges do not alter, overwrite, or fabricate customer billing records, transaction history, or subscription state.

### 2.2 Server-Side RBAC Enforcement
1. **Authoritative Server Role Checks:** Administrative status is evaluated strictly on the server by verifying the authenticated user's database record (`User.role == UserRole.ADMIN.value`).
2. **Zero Trust on Client Signals:** Administrator access is **never** granted based on:
   - Frontend state, UI flags, or client-side storage (`localStorage`, `sessionStorage`).
   - Request query parameters, cookies, or self-asserted JSON body claims.
   - User email domain name or unverified profile fields.
   - User-supplied token claims without database re-verification.
3. **Immutability of Role on Public Endpoints:** Public user registration (`/api/auth/register`) strictly provisions accounts with `role: "client"`. The administrator role can only be assigned through trusted out-of-band administrative provisioning (`python -m app.cli.create_admin`), administrative promotion of existing accounts (`python -m app.cli.promote_admin`), or by an existing authenticated administrator (`POST /api/auth/users`).

### 2.3 Regular User Subscription Preservation
1. **Paid Entitlements Preserved:** Ordinary users (`role: "client"`) remain strictly subject to their subscription quotas, feature tiers, and payment rules.
2. **Backend Enforcement:** Target website limits, monthly scan allowances, and paid vulnerability report downloads are enforced server-side via `QuotaService` and `ReportService`.
3. **Audit Trail:** All subscription upgrades, checkout sessions, and cancellation events are logged to the immutable activity ledger.

---

## 3. Architecture & Implementation Matrix

| Layer | Component | Implementation Details |
| :--- | :--- | :--- |
| **Backend Authorization** | `app.security.entitlements.EntitlementService` | Centralized helper providing `can_access_admin_portal()`, `can_execute_admin_operation()`, and `can_access_paid_feature()`. Unconditionally authorizes verified admins without subscription lookups. |
| **Route Protection Dependency** | `app.security.dependencies.require_admin` | Re-verifies user from database on every request. Rejects non-admin attempts with HTTP 403 Forbidden. |
| **Subscription Quotas** | `app.services.payment.quota_service.QuotaService` | Grants admin exemptions for target registrations and scan execution (`can_add_target_website`, `can_execute_scan`). |
| **Report Access Control** | `app.services.report_service.ReportService` | `has_active_entitlement()` unconditionally grants verified administrators access to detailed audit reports and PDF/HTML downloads. |
| **Billing Presentation** | `app.api.routes.billing.get_my_subscription` | Returns unconstrained admin quota response in-memory for admin accounts without modifying underlying database records. |
| **Frontend Route Guards** | `frontend/src/router/ProtectedRoute.tsx` (`AdminRoute`) | Verifies `isAdmin` claim; grants immediate access to `<AdminLayout />` without prompting for subscription upgrades. |
| **Frontend Login Navigation** | `frontend/src/pages/LoginPage.tsx` | Automatically routes authenticated administrators to `/admin/dashboard`. |
| **Billing UI Indicators** | `frontend/src/pages/client/ClientBillingPage.tsx` | Displays "Administrator Exemption" notice and marks plan tiers as "Admin Access Granted". |

---

## 4. Permitted Administrative Operations Without Subscription

Authorized administrators have unconstrained access to:
1. **Platform Overview & Telemetry:** `GET /api/admin/overview`, `GET /api/admin/system/jobs-status`
2. **User & Client Management:** `GET /api/admin/users`, `PATCH /api/admin/users/{id}/status`, `POST /api/admin/clients/{id}/unlock`, `POST /api/admin/clients/{id}/force-reset`
3. **Target Website Oversight:** `GET /api/admin/websites`, `PATCH /api/admin/websites/{id}/suspend`
4. **Scan Operations & Cancellation:** `GET /api/admin/scans`, `POST /api/admin/scans/{id}/cancel`
5. **Activity & Security Center:** `GET /api/admin/activity/metrics`, `GET /api/admin/activity/timeline`, `POST /api/admin/activity/{id}/review`
6. **Security Alert Triage:** `GET /api/admin/alerts`, `PATCH /api/admin/alerts/{id}/triage`
7. **Billing & Revenue Analytics:** `GET /api/billing/admin/stats`, `GET /api/billing/admin/transactions`
8. **DevSecOps Deployments:** `GET /api/deployment/admin/overview`
9. **Remediation Metrics:** `GET /api/remediations/admin/stats`
10. **Client Finder Automation:** `GET /api/leads/*`, `POST /api/leads/*`

---

## 5. Verification & Test Compliance

The policy is validated through automated regression test suites:
- **Backend Test Suite:** `backend/tests/test_admin_access_without_subscription.py` (7/7 Scenarios Passing)
  - Scenario 1: Admin with NO subscription row accesses dashboard & admin APIs (HTTP 200).
  - Scenario 2: Admin with EXPIRED / CANCELLED subscription retains full admin capabilities (HTTP 200).
  - Scenario 3: Admin executes operational actions (website suspension, alert triage, account status) without a paid plan.
  - Scenario 4: Regular client exceeding plan quotas is rejected with HTTP 403 Forbidden.
  - Scenario 5: Regular client attempting admin endpoints is rejected with HTTP 403 Forbidden.
  - Scenario 6: Privilege escalation attacks (JWT parameter tampering, buying Enterprise tier) fail to grant admin access.
  - Scenario 7: Standard client billing lifecycle (checkout, upgrades, cancellation) remains unaltered.
- **Frontend Test Suite:** `frontend/src/tests/AdminAccessWithoutSubscription.test.tsx` (3/3 Tests Passing)
  - `AdminRoute` permits administrators without subscription verification.
  - `AdminRoute` blocks regular clients with `Access Restricted`.
  - `ClientBillingPage` renders exemption indicators and disables upgrade checkout for administrators.

# PATCHORA — Frontend API Configuration & Connection Architecture

This document describes the frontend-to-backend API connectivity, environment configuration, URL normalization rules, authentication handling, and endpoint routing for PATCHORA.

---

## 1. Deployed Environments & Base URLs

| Environment | Frontend URL | Backend API Base URL | Configuration Source |
| :--- | :--- | :--- | :--- |
| **Production** | `https://patchura-frontend.onrender.com` | `https://patchura-backend.onrender.com` | `frontend/.env.production` / `render.yaml` |
| **Local Development** | `http://localhost:5173` | `http://localhost:8000` (or Vite proxy) | `frontend/.env` / `vite.config.ts` |

---

## 2. Centralized API Client Architecture

All API calls throughout the React/TypeScript frontend are routed strictly through the centralized Axios client defined in [`frontend/src/api/client.ts`](file:///c:/website%20projects/Website_Patchura/frontend/src/api/client.ts).

### Base URL Resolution Strategy
The base URL is determined using `resolveApiBaseUrl()`:
1. **Explicit Environment Variable:** Reads `import.meta.env.VITE_API_BASE_URL`.
2. **Trailing Slash & Prefix Sanitization:** Cleans leading/trailing whitespace, strips trailing slashes (`/`), and removes duplicate trailing `/api` suffixes via `normalizeApiBaseUrl()`.
3. **Production Mode Guard:** When built with `vite build` (`import.meta.env.PROD === true`), defaults to `https://patchura-backend.onrender.com` even if environment variables are not supplied.
4. **Development Mode Guard:** In development (`import.meta.env.DEV === true`), falls back to empty string `''` to leverage the local Vite `/api` proxy targeting `http://localhost:8000`.

### Request Interceptor & URL Normalization
- **Path Sanitization:** Automatically cleans duplicate slashes (`//api//auth//login` &rarr; `/api/auth/login`) and guards against accidental double `/api/api/` prefixes.
- **Bearer Token Injection:** Automatically attaches `Authorization: Bearer <token>` when an active access token is held in memory (`currentAccessToken`).
- **Token Management:** Exposes `setApiAccessToken(token: string | null)` and `getApiAccessToken()` for the `AuthContext` session manager.

### Response Interceptor & Error Normalization
Errors returned by Axios are normalized into an `error.userMessage` string:
1. `error.response.data.error.message` (standard PATCHORA error response schema)
2. `error.response.data.detail` (FastAPI standard string or array of validation errors)
3. Fallback to `error.message` (e.g. `'Network Error'` or timeout)

---

## 3. Environment Variable Security

In accordance with strict security standards:
- **No Secrets in `VITE_`:** No database passwords, Stripe secret keys, JWT secret keys, or private API keys are prefixed with `VITE_`.
- Only public, client-safe variables are exposed:
  - `VITE_API_BASE_URL` (the backend domain)
  - `VITE_APP_NAME` (application branding)
- Private secrets remain exclusively on the backend server or inside Render's secure server environment.

---

## 4. Frontend-to-Backend Route Mapping Contract

Every frontend module in `frontend/src/api/` maps directly to the corresponding FastAPI backend route and payload:

| Module | Frontend Function | HTTP Method | Endpoint Path | Payload Schema |
| :--- | :--- | :--- | :--- | :--- |
| **Auth** | `loginUser(data)` | `POST` | `/api/auth/login` | JSON `{ login, password }` |
| **Auth** | `registerClient(data)` | `POST` | `/api/auth/register` | JSON `{ username, email, password, password_confirmation }` |
| **Auth** | `rotateRefreshToken(token)` | `POST` | `/api/auth/refresh` | JSON `{ refresh_token }` |
| **Auth** | `logoutUser(token)` | `POST` | `/api/auth/logout` | JSON `{ refresh_token }` |
| **Auth** | `fetchCurrentUser()` | `GET` | `/api/auth/me` | None (Bearer Token) |
| **Auth** | `recoverPassword(email)` | `POST` | `/api/auth/recover-password` | JSON `{ email }` |
| **Auth** | `resetPasswordWithToken(...)` | `POST` | `/api/auth/reset-password` | JSON `{ token, new_password, new_password_confirmation }` |
| **Health** | `fetchHealth()` | `GET` | `/api/health` | None |
| **Scanner** | `analyzePhpCode(code, file)` | `POST` | `/api/scan/php/analyze` | JSON `{ source_code, file_name }` |
| **Scanner** | `getPhp2ShellMitigation()` | `GET` | `/api/scan/php/php2shell-mitigation` | None |
| **Websites**| `listWebsites()` | `GET` | `/api/websites` | None |
| **Websites**| `createWebsite(data)` | `POST` | `/api/websites` | JSON `{ name, target_url, verification_method }` |
| **Websites**| `verifyWebsite(id)` | `POST` | `/api/websites/:id/verify` | None |
| **Websites**| `authorizeWebsiteScan(...)` | `POST` | `/api/websites/:id/authorize` | JSON `{ legal_authorization_confirmed, ... }` |
| **Scans** | `listScans(websiteId)` | `GET` | `/api/scans` | Query `{ website_id }` |
| **Scans** | `createScan(data)` | `POST` | `/api/scans` | JSON `{ website_id, scan_type, scan_scope }` |
| **Scans** | `getScanDetails(scanId)` | `GET` | `/api/scans/:id` | None |
| **Reports** | `getDetailedReport(scanId)` | `GET` | `/api/reports/scan/:id/details` | None |
| **Reports** | `downloadReportHtml(scanId)` | `GET` | `/api/reports/scan/:id/download-html` | None (`blob` response) |
| **Billing** | `listPlans()` | `GET` | `/api/billing/plans` | None |
| **Billing** | `getMySubscription()` | `GET` | `/api/billing/subscription` | None |
| **Billing** | `createCheckoutSession(...)`| `POST` | `/api/billing/checkout-session` | JSON `{ plan_tier, billing_interval }` |
| **Remediations**| `createRemediation(...)`| `POST` | `/api/remediations/request` | JSON `{ scan_id, finding_id, engine }` |
| **Remediations**| `testPatch(sessionId)` | `POST` | `/api/remediations/:id/test` | JSON `{}` |
| **Remediations**| `approvePatch(sessionId)`| `POST` | `/api/remediations/:id/approve` | JSON `{ approval_notes }` |
| **Deployment** | `getDeploymentHistory()` | `GET` | `/api/deployment/history` | None |
| **Deployment** | `deployToStaging(data)` | `POST` | `/api/deployment/deploy-staging` | JSON `{ session_id, target_id }` |
| **Deployment** | `deployToProduction(data)`| `POST` | `/api/deployment/deploy-production` | JSON `{ session_id, target_id, confirmation_code }` |
| **Leads** | `listLeads(params)` | `GET` | `/api/leads` | Query params |
| **Leads** | `createLead(data)` | `POST` | `/api/leads` | JSON `{ company_name, domain, ... }` |

---

## 5. Verification & Test Suite

Automated verification was performed with Vitest:

1. **`src/tests/ApiClient.test.ts` (8 passing tests):**
   - URL trailing slash stripping (`https://patchura-backend.onrender.com/` &rarr; `https://patchura-backend.onrender.com`)
   - URL redundant prefix stripping (`https://patchura-backend.onrender.com/api` &rarr; `https://patchura-backend.onrender.com`)
   - Empty, null, and whitespace input resilience
   - Production fallback verification
   - Interceptor Bearer token injection
   - Interceptor path double-slash deduplication (`//api//auth//login` &rarr; `/api/auth/login`)
   - Interceptor `/api/api/` prefix deduplication
   - `loginUser` JSON schema and POST request contract verification

2. **`src/tests/Auth.test.tsx` (5 passing tests):**
   - Login page form rendering
   - Registration link navigation
   - Empty submission client-side validation
   - Registration page policy checklist verification

3. **TypeScript Build Verification:**
   - `tsc --noEmit` passed with 0 errors.
   - `npm run build` compiled `dist/` production assets in 4.35s with `https://patchura-backend.onrender.com` bundled.

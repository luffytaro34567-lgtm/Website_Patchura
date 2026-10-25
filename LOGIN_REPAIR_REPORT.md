# PATCHORA End-to-End Login Repair Report

**Date:** 2026-10-25  
**Service URLs:**
- **Frontend (Production):** `https://patchura-frontend.onrender.com`
- **Backend (Production):** `https://patchura-backend.onrender.com`

---

## 1. Executive Summary & Root Cause Analysis

When attempting to authenticate on the deployed production frontend, users were presented with `"Network Error"` rather than completing authentication or receiving actionable feedback.

An end-to-end audit across the frontend, FastAPI backend, and Render deployment revealed four distinct root causes:

1. **CORS Preflight Failure on Render (HTTP 400 Disallowed CORS Origin):**
   - The Render dashboard environment variable `CORS_ORIGINS` was configured as `["https://patchura-frontend.onrender.com"]`.
   - The backend's initial origin parser did not strip brackets and quotation marks, yielding a literal origin string `'["https://patchura-frontend.onrender.com"]'`.
   - Starlette's `CORSMiddleware` rejected all preflight `OPTIONS /api/auth/login` requests with `400 Disallowed CORS origin`. In the browser, this manifested as a generic `Network Error`.

2. **Aggressive Client Timeout during Render Cold Starts:**
   - On Render's free tier, backend instances spin down after 15 minutes of inactivity. Cold start latency ranges from 20 to 35 seconds.
   - The frontend Axios client had a strict `timeout: 15_000` (15s). During cold starts, the browser aborted requests with `ECONNABORTED`, which the frontend catch block converted into `"Network Error"`.

3. **FastAPI Pydantic v2 Exception Serialization Bug (HTTP 500 on Validation Errors):**
   - In `backend/app/errors/handlers.py`, `RequestValidationError` was returning `detail=exc.errors()` directly into Starlette's `JSONResponse`.
   - In Pydantic v2, custom validation failures include `ctx: {'error': ValueError(...)}`. Because `ValueError` instances cannot be JSON-serialized, malformed or invalid registration/login attempts crashed with `TypeError: Object of type ValueError is not JSON serializable` (HTTP 500) rather than a clear HTTP 422.

4. **Timezone Offset Comparison Bug in Account Lockout:**
   - In `backend/app/services/auth_service.py`, SQLite stores datetime timestamps as timezone-naive datetimes.
   - Comparing `user.locked_until > datetime.now(timezone.utc)` caused Python to raise `TypeError: can't compare offset-naive and offset-aware datetimes`, throwing an unhandled 500 error whenever a locked account attempted to log in.

---

## 2. Backend Login Contract Specification

The login endpoint is defined in `backend/app/api/routes/auth.py`.

### 2.1 Endpoint Specification
- **Path:** `POST /api/auth/login`
- **Content-Type:** `application/json`
- **Rate Limit:** 15 requests per 60 seconds (enforced by `InMemoryRateLimiter`)

### 2.2 Request Schema (`UserLoginRequest`)
```json
{
  "login": "string (1-255 chars, username or email)",
  "password": "string (1-128 chars)"
}
```

### 2.3 Credential Validation & Security Controls
1. **Case-Insensitive Resolution:** Inputs are stripped and lowercased; database queries utilize `func.lower(User.username) == normalized_login` and `func.lower(User.email) == normalized_login`.
2. **Timing Attack Equalization:** If the user account does not exist, bcrypt verification runs against a constant dummy hash (`DUMMY_HASH`) to prevent timing and user enumeration attacks.
3. **Lockout Protection:** After 5 consecutive failed password attempts, the account is locked for 30 minutes. Timestamps are normalized to UTC with timezone awareness.
4. **Suspended / Disabled Checks:** Inactive or suspended accounts return HTTP 401 with `"Account is disabled or suspended. Please contact support."`.

### 2.4 Response Schema (`AuthTokensResponse`)
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsIn...",
  "token_type": "bearer",
  "expires_in": 900,
  "refresh_token": "3c98...64-char-hex",
  "user": {
    "id": "uuid-string",
    "username": "client_eva",
    "email": "eva@example.com",
    "role": "client",
    "is_active": true,
    "created_at": "2026-10-24T18:00:00Z"
  }
}
```

---

## 3. Frontend Architecture & Flow Implementation

### 3.1 Token & Session Storage
- **Access Token:** Maintained purely in memory via `setApiAccessToken()` in `frontend/src/api/client.ts`. Injected dynamically on every outgoing request via Axios request interceptor: `Authorization: Bearer <token>`.
- **Refresh Token:** Stored in browser `localStorage` under key `bh_refresh_token`. On initial load, `AuthProvider` automatically calls `POST /api/auth/refresh` to restore the user session. If a refresh token is reused after rotation, backend family revocation invalidates all issued tokens.
- **Logout:** Calling `logout()` revokes the token on the backend (`POST /api/auth/logout`), purges `bh_refresh_token` from `localStorage`, and clears the in-memory access token.

### 3.2 URL Normalization & Cold Start Handling
- Centralized API base URL resolved via `resolveApiBaseUrl()`:
  - Production fallback: `https://patchura-backend.onrender.com`.
  - Vite request proxy in local development: `''`.
- Request interceptor strips duplicate slashes and redundant `/api/api/` prefixes.
- Client timeout increased to **30,000ms** to gracefully accommodate Render free tier cold starts.
- Response interceptor maps network drops and cold start timeouts to clear user instructions:
  - `ECONNABORTED` &rarr; `"Connection timed out. The server may be waking up, please try again in a moment."`
  - `ERR_NETWORK` &rarr; `"Unable to connect to server. The backend may be starting up or sleeping on Render. Please retry shortly."`
  - HTTP 429 &rarr; `"Too many requests. Please wait a moment before trying again."`

### 3.3 Role-Based & Intended-Destination Redirection
In `frontend/src/pages/LoginPage.tsx`:
1. If the user was redirected from a protected route (`location.state.from.pathname`), login navigates directly to that original page (e.g. `/scans/view-123`).
2. If `from` is absent or points back to `/login`:
   - Admin users (`role === 'admin'`) &rarr; `/admin/dashboard`
   - Client users (`role === 'client'`) &rarr; `/dashboard`
3. Authenticated users navigating directly to `/login` are automatically redirected to their appropriate dashboard.

---

## 4. Verification & Test Results

### 4.1 Backend Test Suites
- **`backend/tests/test_login_regression.py` (5 passing tests):**
  - Case-insensitive login via username and email (`test_login_success_case_insensitive_and_contract`) &mdash; **PASSED**
  - Uniform error messages on nonexistent users and bad passwords (`test_login_invalid_credentials_uniform_error`) &mdash; **PASSED**
  - Pydantic validation on empty/malformed bodies returning 422 (`test_login_malformed_requests`) &mdash; **PASSED**
  - Account lockout after 5 failed attempts with UTC timezone safety (`test_login_account_lockout_after_five_failures`) &mdash; **PASSED**
  - Sliding-window rate limiting returning 429 and `Retry-After` header (`test_login_rate_limiting`) &mdash; **PASSED**
- **`backend/tests/test_cors_config.py` (10 passing tests):**
  - JSON array origin parsing, trailing slash stripping, and regex validation &mdash; **10/10 PASSED**
- **`backend/tests/test_auth.py` (10 passing tests):**
  - Registration, token rotation, reuse detection, disabled accounts, and RBAC admin protections &mdash; **10/10 PASSED**

### 4.2 Frontend Test Suites
- **`frontend/src/tests/LoginFlow.test.tsx` (6 passing tests):**
  - Client login token storage, localStorage persistence, and `/dashboard` redirection &mdash; **PASSED**
  - Admin login redirection to `/admin/dashboard` &mdash; **PASSED**
  - Protected route `from` parameter preservation &mdash; **PASSED**
  - Safe error rendering on invalid credentials &mdash; **PASSED**
  - Cold start / network error friendly messaging &mdash; **PASSED**
  - Rate limiting 429 user message handling &mdash; **PASSED**
- **`frontend/src/tests/ApiClient.test.ts` (8 passing tests):**
  - Base URL resolution, prefix deduplication, and Bearer token injection &mdash; **8/8 PASSED**
- **`frontend/src/tests/Auth.test.tsx` (5 passing tests):**
  - UI inputs, validation alerts, and password security checklist &mdash; **5/5 PASSED**

### 4.3 Production Frontend Bundle Build
- Command: `npm run build` (`tsc && vite build`)
- Output: `dist/index.html` (1.19 kB), `dist/assets/index-Dq0V_p4V.css` (68.57 kB), `dist/assets/index-R04nb2rZ.js` (645.24 kB)
- TypeScript errors: **0**
- Build status: **SUCCESS**

---

## 5. Deployment Instructions for Live Verification

The application code is fully repaired and passes all automated tests. To make these fixes live in the Render production environment:

1. **Push Changes to GitHub:**
   ```bash
   git add .
   git commit -m "fix(auth): complete end-to-end login flow repair, CORS resilience, and error handling"
   git push origin main
   ```

2. **Render Automatic Deployment:**
   - Both `patchura-backend` and `patchura-frontend` are configured to automatically trigger builds upon pushes to `main`.
   - The backend service will run `pip install -r backend/requirements.txt` and restart with the new CORS origin parser, Pydantic exception serializer, and UTC lockout logic.
   - The frontend static site will run `npm run build` and publish the updated client with normalized API base URLs and friendly cold-start handling.

3. **Render Environment Variable Verification (Optional Dashboard Check):**
   - On the backend service dashboard, verify `CORS_ORIGINS` is set to `https://patchura-frontend.onrender.com`. Even if formatted as `["https://patchura-frontend.onrender.com"]`, the upgraded parser handles it automatically.
   - On the frontend service dashboard, confirm `VITE_API_BASE_URL` is set to `https://patchura-backend.onrender.com` (though the production build now defaults to this automatically).

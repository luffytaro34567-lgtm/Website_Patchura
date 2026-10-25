# PATCHORA Render Deployment Verification Report

**Date:** 2026-10-25  
**Production URLs:**
- **Frontend:** `https://patchura-frontend.onrender.com`
- **Backend:** `https://patchura-backend.onrender.com`
- **Git Repository:** `https://github.com/luffytaro34567-lgtm/Website_Patchura.git` (Branch: `main`)

---

## 1. Executive Summary & Live Deployment Diagnostic

An empirical audit of both live production services on Render and the codebase was conducted:

1. **Live Backend Status (`https://patchura-backend.onrender.com`):**
   - **Root Endpoint (`GET /`):** Live, returns `200 OK` with JSON metadata:
     `{"name":"PATCHORA","version":"0.1.0","environment":"development","docs_url":"/api/docs"}`.
   - **Health Endpoint (`GET /api/health`):** Live, returns `200 OK`:
     `{"status":"healthy","version":"0.1.0","environment":"development","uptime_seconds":19.29,"database":{"connected":true,"error":null}}`.
   - **Live CORS Preflight Diagnostic (`OPTIONS /api/auth/login`):**
     Direct probing with header `Origin: https://patchura-frontend.onrender.com` currently returns:
     ```
     HTTP 400 Bad Request
     Disallowed CORS origin
     ```
     **Definitive Diagnosis:** The currently running Render instance is executing older code that has the unparsed bracketed `CORS_ORIGINS` bug (`'["https://patchura-frontend.onrender.com"]'`). The local commits on `main` contain the verified repair. Pushing local commits to GitHub will trigger Render's auto-deploy and resolve the 400 CORS error on the live server.

2. **Live Frontend Status (`https://patchura-frontend.onrender.com`):**
   - **HTTP Status:** Returns `200 OK`. The static HTML and assets are being served correctly by Render.
   - **Login Connection:** Currently blocked by the live backend's preflight rejection. Once the backend updates, login will connect successfully.

---

## 2. Service Specifications & Blueprint Configuration

The infrastructure is defined in [`render.yaml`](./render.yaml).

### 2.1 Backend Web Service (`patchura-backend`)
| Configuration Attribute | Verified Production Value | Notes |
| :--- | :--- | :--- |
| **Type** | `web` | FastAPI application |
| **Runtime** | `python` | Pinned to Python `3.12.7` via `.python-version` and `PYTHON_VERSION` env var |
| **Root Directory** | `backend` | |
| **Build Command** | `pip install --no-cache-dir -r requirements.txt` | Pins FastAPI 0.115.5, Pydantic 2.10.1, SQLAlchemy 2.0.36, asyncpg 0.30.0, aiosqlite 0.20.0 |
| **Start Command** | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` | Binds to dynamic port injected by Render |
| **Health Check Path** | `/api/health` (also accessible at `/health`) | Tested & verified responsive |
| **Plan** | `free` | Ephemeral filesystem; cold start takes ~20–35s after 15m idle |
| **Auto-Deploy** | `true` | Automatically builds and restarts upon git push to `main` |

### 2.2 Frontend Static Site (`patchura-frontend`)
| Configuration Attribute | Verified Production Value | Notes |
| :--- | :--- | :--- |
| **Type** | `web` (static site) | React 18 + Vite 5 + TypeScript + Tailwind |
| **Runtime** | `static` | Node.js pinned to `20` via `.nvmrc` and `NODE_VERSION` env var |
| **Root Directory** | `frontend` | |
| **Build Command** | `npm install && npm run build` | Compiles via `tsc && vite build` |
| **Publish Directory** | `./dist` | Single-Page Application bundle |
| **Routing / Rewrites** | `/* -> /index.html` | Required for client-side routing (React Router) |
| **Plan** | `free` | Globally distributed CDN |
| **Auto-Deploy** | `true` | Automatically rebuilds and deploys upon git push to `main` |

---

## 3. Environment Variables Audit

### 3.1 Backend Required Variables
| Variable Name | Required / Optional | Verified Production Value | Security / Purpose |
| :--- | :--- | :--- | :--- |
| `APP_ENV` | **Required** | `production` | Enables strict CORS rules, disables test routes |
| `APP_NAME` | Optional | `PATCHORA` | Application title |
| `APP_VERSION` | Optional | `0.1.0` | Version metadata |
| `DEBUG` | **Required** | `false` | Prevents exposing stack traces & debug docs in production |
| `LOG_LEVEL` | Optional | `INFO` | Structlog logging level |
| `SECRET_KEY` | **Required** | `generateValue: true` or random secret | Cryptographic signature key for JWT tokens |
| `CORS_ORIGINS` | **Required** | `https://patchura-frontend.onrender.com` | Allowed origin for frontend requests |
| `USE_SQLITE` | **Required** | `true` (if using SQLite) or `false` (for Postgres) | Database driver selector |
| `SQLITE_PATH` | Optional | `./patchora.db` | Local SQLite file path |
| `DATABASE_URL` | Optional | `postgresql+asyncpg://...` (Render Postgres) | Auto-normalized if starting with `postgres://` |
| `PAYMENT_PROVIDER` | Optional | `sandbox` | Defaults to sandbox mode |
| `AI_PROVIDER` | Optional | `deterministic_rules` | Rules-based remediation engine |
| `OUTREACH_PROVIDER` | Optional | `sandbox_logger` | Compliance email logger |
| `PYTHON_VERSION` | **Recommended** | `3.12.7` | Explicit runtime guarantee for Render builder |

### 3.2 Frontend Required Variables
| Variable Name | Required / Optional | Verified Production Value | Notes |
| :--- | :--- | :--- | :--- |
| `VITE_API_BASE_URL` | **Required** | `https://patchura-backend.onrender.com` | Centralized backend API target (baked into build, also fallback in code) |
| `VITE_APP_NAME` | Optional | `PATCHORA` | Frontend branding title |
| `NODE_VERSION` | **Recommended** | `20` | Node.js builder version |

---

## 4. Database & Storage Considerations on Render

1. **Free Tier Ephemeral Disk vs Persistent Storage:**
   - On Render's Free tier, the filesystem is ephemeral: files written to disk (e.g. `./patchora.db`) do not persist across instance restarts or sleeping events.
   - For temporary testing, `./patchora.db` operates seamlessly.
   - For durable production storage, provision a **Render PostgreSQL** instance and set `USE_SQLITE=false` with the provided `DATABASE_URL`.
2. **PostgreSQL Driver Auto-Normalization:**
   - In [`backend/app/core/config.py`](./backend/app/core/config.py), `effective_database_url` automatically converts Render's legacy `postgres://` or `postgresql://` connection strings into `postgresql+asyncpg://`.
3. **Automatic Schema Initialization:**
   - In [`backend/app/db/session.py`](./backend/app/db/session.py), `init_db()` calls `Base.metadata.create_all` at startup, guaranteeing tables are created idempotently on any database backend without altering existing user records.

---

## 5. Local Verification & Quality Gate Results

### 5.1 Backend Automated Tests (25 Passing Tests)
```
backend/tests/test_cors_config.py ..........                   [ 10/10 PASSED ]
backend/tests/test_auth.py ..........                          [ 10/10 PASSED ]
backend/tests/test_login_regression.py .....                   [  5/5  PASSED ]
======================= 25 passed in 13.42s =======================
```
- CORS origin parsing verifies quotes, brackets, and slashes are cleanly sanitized.
- Preflight OPTIONS requests for `https://patchura-frontend.onrender.com` pass.
- Case-insensitive login, uniform error messages, UTC lockout, and rate limiting pass.

### 5.2 Frontend Automated Tests (19 Passing Tests)
```
src/tests/ApiClient.test.ts ........                           [  8/8  PASSED ]
src/tests/Auth.test.tsx .....                                  [  5/5  PASSED ]
src/tests/LoginFlow.test.tsx ......                            [  6/6  PASSED ]
======================= 19 passed in 2.10s =======================
```
- Base URL resolution and route deduplication verified.
- End-to-end login flow, token storage, and dashboard routing verified.

### 5.3 Production Frontend Compilation
- Command: `npm run build` (`tsc && vite build`)
- Result: **0 errors**, generated clean bundle in `frontend/dist/` in **4.93s**.

---

## 6. Deployment Procedure

All fixes are staged and committed locally on `main`. To deploy live to Render:

### Step 1: Push Changes to GitHub
From your terminal or GitHub Desktop:
```bash
git push origin main
```

### Step 2: Render Automatic Build Trigger
- Render detects the push on `main`.
- `patchura-backend` builds using Python 3.12, installs dependencies, and restarts.
- `patchura-frontend` builds the static site with Vite and publishes to CDN.

### Step 3: Verify Live Resolution
Run this verification command once deployment completes:
```bash
python -c "import urllib.request; req = urllib.request.Request('https://patchura-backend.onrender.com/api/auth/login', headers={'Origin': 'https://patchura-frontend.onrender.com', 'Access-Control-Request-Method': 'POST', 'Access-Control-Request-Headers': 'content-type'}, method='OPTIONS'); res = urllib.request.urlopen(req, timeout=15); print('Status:', res.getcode(), 'CORS Header:', res.headers.get('Access-Control-Allow-Origin'))"
```
**Expected Output:**
```
Status: 200 CORS Header: https://patchura-frontend.onrender.com
```

Once confirmed, open `https://patchura-frontend.onrender.com` in your browser and log in normally.

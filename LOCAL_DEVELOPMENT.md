# PATCHORA — Localhost Configuration, Startup & Development Guide

**Document Version:** 1.0.0  
**Phase:** Prompt 19 — Localhost Configuration, Startup & Verification  
**Date:** October 24, 2026  
**Application Name:** PATCHORA  
**Default Local URLs:**  
- **Frontend Web Application:** [`http://localhost:5173`](http://localhost:5173)  
- **Backend REST API:** [`http://localhost:8000`](http://localhost:8000)  
- **Interactive Swagger Docs:** [`http://localhost:8000/api/docs`](http://localhost:8000/api/docs)  
- **System Health Endpoint:** [`http://localhost:8000/api/health`](http://localhost:8000/api/health)  

---

## 1. System Requirements & Prerequisites

PATCHORA supports two local development workflows:
1. **Native Local Development (Recommended for fast iteration)**
2. **Containerized Development via Docker Compose**

### Required Runtimes (Native Workflow)
- **Python:** Version 3.11 or 3.12 (`python --version`)
- **Node.js:** Version 18.x or 20.x (`node --version`)
- **Package Manager:** `npm` (v9+) or `pnpm` (v8+)
- **Git:** For revision tracking and Git deployment adapter testing

### Alternative Containerized Workflow
- **Docker Engine & Docker Compose:** Docker Desktop (v24+) or Docker Engine on Linux/macOS.

---

## 2. Quick-Start (1-Click Launchers)

For Windows environments, automated launchers are provided in the repository root:

- **Launch Both Servers (Backend + Frontend):**
  Double-click `start-dev.bat` or run in PowerShell:
  ```powershell
  .\start-dev.ps1
  ```
- **Launch Backend Only:** Double-click `run-backend.bat`
- **Launch Frontend Only:** Double-click `run-frontend.bat`

---

## 3. Step-by-Step Manual Setup

### Step 3.1: Environment Configuration
The repository provides a pre-configured `.env` file with secure local development defaults. If you need to regenerate it from `.env.example`:

```powershell
# Copy template to .env in root
Copy-Item .env.example .env

# Copy to subdirectories for direct terminal sessions
Copy-Item .env backend\.env
Copy-Item .env frontend\.env
```

#### Key Local Environment Variables

| Variable | Local Default | Description |
| :--- | :--- | :--- |
| `APP_ENV` | `development` | Enables detailed logging and interactive Swagger docs |
| `USE_SQLITE` | `true` | **Zero-config SQLite database** (`./patchora.db`) |
| `SQLITE_PATH` | `./patchora.db` | Local SQLite database file path |
| `DATABASE_URL` | `postgresql+asyncpg://bughunter:password@localhost:5432/bughunter_db` | Used if `USE_SQLITE=false` |
| `SECRET_KEY` | `patchora-local-dev-secret-key-at-least-32-chars-long` | JWT token signing key |
| `CORS_ORIGINS` | `http://localhost:5173,http://localhost:3000` | Allowed frontend origins |
| `PAYMENT_PROVIDER` | `sandbox` | Enables simulated checkout without real credit cards |
| `AI_PROVIDER` | `deterministic_rules` | Zero-API-key AST remediation and patch generation |
| `OUTREACH_PROVIDER` | `sandbox_logger` | Logs outbound lead outreach safely to console |
| `VITE_API_BASE_URL` | `http://localhost:8000` | Frontend API target address |

---

### Step 3.2: Backend Installation & Startup

1. Open a terminal and navigate to `backend/`:
   ```bash
   cd backend
   ```
2. Create and activate a Python virtual environment:
   - **Windows (PowerShell):**
     ```powershell
     python -m venv .venv
     .\.venv\Scripts\Activate.ps1
     ```
   - **Windows (CMD):**
     ```cmd
     python -m venv .venv
     call .venv\Scripts\activate.bat
     ```
   - **Linux / macOS:**
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```
3. Install backend dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Initialize the Database:
   - **When using SQLite (`USE_SQLITE=true`):** Tables are automatically initialized on startup via `Base.metadata.create_all`.
   - **When using PostgreSQL (`USE_SQLITE=false`):** Apply Alembic forward migrations:
     ```bash
     alembic upgrade head
     ```
5. Provision an Initial Administrator Account:
   ```bash
   python -m app.cli.create_admin --username admin --email admin@patchora.io --password AdminSecure2026!
   ```
6. Start the FastAPI backend server:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```
   *The backend will be live at `http://localhost:8000`.*

---

### Step 3.3: Frontend Installation & Startup

1. Open a second terminal and navigate to `frontend/`:
   ```bash
   cd frontend
   ```
2. Install npm dependencies:
   ```bash
   npm install
   ```
3. Start the Vite development server:
   ```bash
   npm run dev
   ```
   *The frontend will be live at `http://localhost:5173`.*

---

## 4. Alternative: Running via Docker Compose

To run the complete stack (PostgreSQL + FastAPI + Vite React) in isolated Docker containers:

```bash
# Build and start all services
docker-compose up --build

# Run in background (detached mode)
docker-compose up -d

# View service logs
docker-compose logs -f

# Provision admin inside running container
docker-compose exec backend python -m app.cli.create_admin --username admin --email admin@patchora.io --password AdminSecure2026!

# Stop all services
docker-compose down
```

---

## 5. Localhost Verification Checklist

After launching the application, open your browser to [`http://localhost:5173`](http://localhost:5173) and verify the following:

- [ ] **Landing Page & Branding:** Confirm the official PATCHORA shield and circuit logo renders in header and footer.
- [ ] **System Health:** Navigate to [`http://localhost:8000/api/health`](http://localhost:8000/api/health) and confirm `{"status": "healthy", "database": {"connected": true}}`.
- [ ] **Client Registration:** Click "Get Started" and register a new client account at `http://localhost:5173/register`.
- [ ] **Client Login:** Log in using the registered client credentials.
- [ ] **Admin Login:** Log in with the provisioned administrator credentials (`admin` / `AdminSecure2026!`) at `http://localhost:5173/login`.
- [ ] **Target Registration:** Register a test domain (e.g. `https://test-example.com`) and inspect challenge tokens.
- [ ] **PHP Scanner & AST Rules:** Run a passive security check via the client scanner interface.
- [ ] **Interactive API Docs:** Explore available endpoints at [`http://localhost:8000/api/docs`](http://localhost:8000/api/docs).

---

## 6. Running Automated Tests Locally

### Backend Unit & Security Tests
```bash
cd backend
pytest -v
```
To run the automated 12-Gate Security Release Regression Suite:
```bash
pytest backend/tests/test_release_gate.py -v
```

### Frontend Tests & Type Checking
```bash
cd frontend
# Run Vitest component test suite
npm test

# Run TypeScript type check
npm run type-check

# Run production build validation
npm run build
```

---

## 7. Troubleshooting Common Errors

### 1. Port 8000 or 5173 Already in Use
- **Cause:** Another process or previous instance is running.
- **Resolution (Windows):**
  ```powershell
  # Check which process is using port 8000
  netstat -ano | findstr :8000
  # Terminate the process by PID
  taskkill /PID <PID> /F
  ```
- **Alternative:** Change `port: 5174` in `frontend/vite.config.ts` or run Uvicorn on another port:
  ```bash
  uvicorn app.main:app --port 8080 --reload
  ```

### 2. CORS Error (`Origin Not Allowed`)
- **Cause:** Frontend origin does not match `CORS_ORIGINS`.
- **Resolution:** Add your browser URL to `.env`:
  ```ini
  CORS_ORIGINS=http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173
  ```

### 3. Database Connection Failure (`PostgreSQL`)
- **Cause:** Local PostgreSQL server is not running or credentials differ.
- **Resolution:** Switch to zero-config SQLite mode in `.env`:
  ```ini
  USE_SQLITE=true
  SQLITE_PATH=./patchora.db
  ```
  Restart the backend, and SQLite will auto-initialize instantly.

### 4. PowerShell Script Execution Disabled (`PSSecurityException`)
- **Cause:** Windows default ExecutionPolicy blocks running `.ps1` scripts.
- **Resolution:**
  ```powershell
  Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
  .\start-dev.ps1
  ```
  Or run `start-dev.bat` instead.

---

## 8. Stopping Local Development Services

- **Native Terminal Windows:** Press `Ctrl + C` in both the backend and frontend terminal windows.
- **Docker Compose:** Run `docker-compose down` in the repository root.
- **Background Processes:** Run `taskkill /IM uvicorn.exe /F` and `taskkill /IM node.exe /F`.

# PATCHORA

> **Status:** Production & Localhost Ready (Phases 1–19 Completed & Verified)
> **Product Identity:** AI-assisted vulnerability assessment, security remediation, and secure patch delivery.
> **Architecture:** Full-stack Website Vulnerability Assessment, Paid Threat Reporting, AI-Assisted AST Remediation, DevSecOps Pull-Request Deployment, Client Finder Automation, Centralized Activity Center, and Official Visual Brand Identity.
> **Zero-Day Defense Mandate:** Full active mitigation and detection for **PHP2Shell (CVE-2026-109618 & CVE-2026-109619)** unhandled memory corruption.

PATCHORA is a full-stack SaaS platform for website vulnerability assessment and AI-assisted bug fixing.

---

## Table of Contents

1. [Tech Stack](#tech-stack)
2. [Project Structure](#project-structure)
3. [Quick Start (Localhost)](#quick-start-localhost)
4. [Running with Docker Compose](#running-with-docker-compose)
5. [Environment Variables](#environment-variables)
6. [Testing](#testing)
7. [Documentation Links](#documentation-links)
8. [Development Status](#development-status)

---

## Tech Stack

| Layer      | Technology                              |
|------------|-----------------------------------------|
| Frontend   | React 18, TypeScript 5, Vite 5, Tailwind CSS 3, React Router 6 |
| Backend    | Python 3.12, FastAPI 0.115, Pydantic v2, SQLAlchemy 2 (async) |
| Database   | PostgreSQL 16 (primary) / SQLite (local fallback) |
| Migrations | Alembic 1.14                            |
| Testing    | Pytest + pytest-asyncio (BE) · Vitest + RTL (FE) · Playwright (E2E) |
| Container  | Docker + Docker Compose                 |
| Future     | Redis + Celery (background jobs)        |

---

## Project Structure

```
patchora/
├── backend/
│   ├── app/
│   │   ├── api/routes/        # FastAPI route handlers
│   │   ├── core/              # Config, logging
│   │   ├── db/                # SQLAlchemy engine & session
│   │   ├── models/            # ORM models
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── services/          # Business logic
│   │   ├── security/          # Auth helpers
│   │   ├── errors/            # Exception handlers
│   │   └── main.py            # Application factory
│   ├── alembic/               # Database migrations
│   ├── tests/                 # Pytest tests
│   ├── requirements.txt
│   ├── pytest.ini
│   ├── alembic.ini
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── api/               # Axios client + endpoint functions
│   │   ├── components/
│   │   │   ├── layout/        # RootLayout, AdminLayout, ClientLayout
│   │   │   └── shared/        # Navbar, Footer, reusable UI
│   │   ├── hooks/             # Custom React hooks
│   │   ├── pages/             # Route-level page components
│   │   │   └── sections/      # Landing page section components
│   │   ├── router/            # React Router config
│   │   ├── theme/             # Dark/light mode context
│   │   ├── types/             # TypeScript type definitions
│   │   └── tests/             # Vitest + RTL unit tests
│   ├── e2e/                   # Playwright E2E tests
│   ├── public/                # Static assets
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   └── Dockerfile
├── docs/
│   ├── ARCHITECTURE.md
│   ├── BRANDING_MIGRATION.md
│   └── DEVELOPMENT_STATUS.md
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

---

## Quick Start (Localhost)

For comprehensive local configuration details, troubleshooting, and testing instructions, see **[`LOCAL_DEVELOPMENT.md`](LOCAL_DEVELOPMENT.md)**.

### 1-Click Launchers (Windows)
- Run `start-dev.bat` or `.\start-dev.ps1` in the repository root.
- Starts the FastAPI backend at `http://localhost:8000` and Vite frontend at `http://localhost:5173`.

### Manual Startup

#### 1. Configure Environment
```bash
cp .env.example .env
# Defaults enable zero-config SQLite mode (patchora.db)
```

#### 2. Backend (FastAPI)
```bash
cd backend
python -m venv .venv
source .venv/bin/activate    # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
# Create initial admin:
python -m app.cli.create_admin --username admin --email admin@patchora.io --password AdminSecure2026!
# Launch server:
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
# API available at http://localhost:8000 (Swagger docs at http://localhost:8000/api/docs)
```

#### 3. Frontend (React + Vite)
```bash
cd frontend
npm install
npm run dev
# Application available at http://localhost:5173
```

---

## Running with Docker Compose

```bash
cp .env.example .env
docker compose up --build
```

Services:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/api/docs
- Database: localhost:5432

---

## Environment Variables

See [`.env.example`](.env.example) for all available options.

Key variables:

| Variable         | Description                              | Default                       |
|-----------------|------------------------------------------|-------------------------------|
| `DATABASE_URL`  | PostgreSQL async connection URL           | `postgresql+asyncpg://...`    |
| `USE_SQLITE`    | Use SQLite instead of PostgreSQL          | `false`                       |
| `CORS_ORIGINS`  | Comma-separated list of allowed origins   | `http://localhost:5173,...`   |
| `SECRET_KEY`    | Secret key for signing tokens (future)    | Must be changed in production |
| `APP_ENV`       | `development`, `staging`, or `production` | `development`                 |
| `VITE_API_BASE_URL` | Backend URL used by the frontend      | `http://localhost:8000`       |

---

## Testing

### Backend (pytest)

```bash
cd backend
pytest
```

### Frontend unit tests (Vitest)

```bash
cd frontend
npm test
```

### Frontend E2E tests (Playwright)

```bash
cd frontend
npm run test:e2e
```

---

## Documentation Links

- [`LOCAL_DEVELOPMENT.md`](LOCAL_DEVELOPMENT.md) — Localhost configuration, ports, troubleshooting, and verification
- [`docs/BRAND_GUIDELINES.md`](docs/BRAND_GUIDELINES.md) — Official brand identity, color palettes, and logo assets
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — System architecture, domain models, and API blueprints
- [`docs/SECURITY_HARDENING.md`](docs/SECURITY_HARDENING.md) — Defense-in-depth security controls
- [`docs/DEVELOPMENT_STATUS.md`](docs/DEVELOPMENT_STATUS.md) — Complete phase checklist & milestone logs

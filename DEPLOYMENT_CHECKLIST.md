# PATCHORA — PRODUCTION DEPLOYMENT CHECKLIST & RUNBOOK

This document provides step-by-step instructions for deploying PATCHORA to production environments. Follow all steps in sequence to ensure a secure, repeatable, and verifiable deployment.

---

## 1. Pre-Deployment Prerequisites

Ensure the deployment target host meets the following minimum requirements:

- **Hardware:** 2+ vCPUs, 4 GB+ RAM, 20 GB+ SSD storage.
- **Operating System:** Linux (Ubuntu 22.04 LTS / Debian 12 / RHEL 9 recommended).
- **Runtime Dependencies:**
  - Docker Engine 24.0+ and Docker Compose v2.20+
  - PostgreSQL 16+ (or managed PostgreSQL via AWS RDS, GCP Cloud SQL, or Supabase)
  - Reverse Proxy / Load Balancer with TLS termination (NGINX, Traefik, Caddy, or Cloudflare)
  - Valid SSL/TLS Certificate (Let's Encrypt or corporate CA)

---

## 2. Environment Variables Specification

Create a `.env` file in the project root directory. **Never commit the `.env` file to version control.**

All variables are explicitly detailed below:

| Variable Name | Required | Default / Example | Purpose & Notes |
| :--- | :--- | :--- | :--- |
| `APP_ENV` | **Yes** | `production` | Sets environment mode (`production` disables debug docs and enables HSTS). |
| `APP_NAME` | No | `PATCHORA` | Application brand name used across UI and reports. |
| `APP_VERSION` | No | `0.1.0` | Application release version string. |
| `SECRET_KEY` | **Yes** | *(Generate 64-char random hex)* | Cryptographic key for JWT signatures and session tokens. Must be at least 32 characters. |
| `DEBUG` | **Yes** | `false` | Must be `false` in production. Disables verbose stack traces. |
| `LOG_LEVEL` | No | `INFO` | Application log level (`DEBUG`, `INFO`, `WARNING`, `ERROR`). |
| `JWT_ALGORITHM` | No | `HS256` | JWT signing algorithm. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `15` | Access token lifespan in minutes. |
| `REFRESH_TOKEN_EXPIRE_DAYS` | No | `7` | Refresh token lifespan in days. |
| `PASSWORD_MIN_LENGTH` | No | `8` | Minimum client password length. |
| `PASSWORD_MAX_LENGTH` | No | `128` | Maximum client password length. |
| `DATABASE_URL` | **Yes** | `postgresql+asyncpg://user:pass@host:5432/patchora_db` | Async PostgreSQL connection string with `asyncpg` driver. |
| `USE_SQLITE` | No | `false` | Fallback SQLite flag. Must be `false` in production. |
| `CORS_ORIGINS` | **Yes** | `https://app.patchora.io` | Comma-separated list of permitted frontend origins. |
| `PAYMENT_PROVIDER` | **Yes** | `stripe` | `stripe` for production; `sandbox` for mock billing. |
| `STRIPE_SECRET_KEY` | Conditional | `sk_live_...` | Required if `PAYMENT_PROVIDER=stripe`. |
| `STRIPE_PUBLISHABLE_KEY` | Conditional | `pk_live_...` | Required if `PAYMENT_PROVIDER=stripe`. |
| `STRIPE_WEBHOOK_SECRET` | Conditional | `whsec_...` | Required for HMAC webhook verification. |
| `BILLING_CURRENCY` | No | `USD` | Standard ISO currency code. |
| `AI_PROVIDER` | No | `deterministic_rules` | `deterministic_rules`, `gemini`, `openai`, or `anthropic`. |
| `GEMINI_API_KEY` | Conditional | `AIza...` | Required if `AI_PROVIDER=gemini`. |
| `OPENAI_API_KEY` | Conditional | `sk-...` | Required if `AI_PROVIDER=openai`. |
| `ANTHROPIC_API_KEY` | Conditional | `sk-ant-...` | Required if `AI_PROVIDER=anthropic`. |
| `REMEDIATION_ISOLATION_WORKSPACE`| No | `./remediation_sandboxes` | Directory for isolated patch syntax checking. |
| `GITHUB_CLIENT_ID` | Conditional | `Ov23...` | OAuth Client ID for GitHub PR integration. |
| `GITHUB_CLIENT_SECRET` | Conditional | `...` | OAuth Client Secret for GitHub PR integration. |
| `ENABLE_PRODUCTION_DEPLOYMENT` | **Yes** | `false` | Must remain `false` unless explicit approval for prod deployments is granted. |
| `ENABLE_STAGING_DEPLOYMENT` | No | `true` | Enables staging deployment targets. |
| `OUTREACH_PROVIDER` | No | `sandbox_logger` | `smtp` for production emails; `sandbox_logger` for dry-run. |
| `OUTREACH_FROM_EMAIL` | Conditional | `security@patchora.io` | Sender email address for ethical outreach. |
| `OUTREACH_FROM_NAME` | No | `PATCHORA Security Team` | Display name for outreach emails. |
| `OUTREACH_DAILY_RATE_LIMIT` | No | `50` | Maximum daily outreach emails to prevent spamming. |
| `OUTREACH_COMPLIANCE_ADDRESS` | **Yes** | `100 Cyber Defense Way, SF, CA` | Physical mailing address for CAN-SPAM compliance. |
| `OUTREACH_OPT_OUT_BASE_URL` | **Yes** | `https://app.patchora.io/opt-out` | URL endpoint for cryptographic one-click unsubscribe. |
| `VITE_API_BASE_URL` | **Yes** | `https://api.patchora.io` (or `/api`) | Base API endpoint consumed by the frontend client. |

---

## 3. Database Migration Procedure

Before starting the web services, execute the forward Alembic migrations to apply all 9 schema revisions:

```bash
# 1. Verify database connectivity
docker compose exec backend python -c "from app.db.session import engine; import asyncio; asyncio.run(engine.connect())"

# 2. Run Alembic upgrade to head
docker compose exec backend alembic upgrade head

# 3. Verify current revision
docker compose exec backend alembic current
# Expected output: 20261024_0009 (head)
```

> [!IMPORTANT]
> Never run `alembic downgrade` on a production database with live data unless performing a tested recovery procedure. Always take a full database snapshot (`pg_dump`) prior to schema changes.

---

## 4. Production Build & Container Startup

Deploy the production stack using Docker Compose:

```bash
# 1. Build production images (multi-stage build with non-root security)
docker compose -f docker-compose.prod.yml build --no-cache

# 2. Start services in detached mode
docker compose -f docker-compose.prod.yml up -d

# 3. Inspect container statuses
docker compose -f docker-compose.prod.yml ps
```

Verify that both `backend` and `frontend` services report `Up (healthy)`.

---

## 5. Initial Admin Account Provisioning

Administrative accounts cannot be registered via the public registration form. Provision the initial super-admin account using the secure CLI tool:

```bash
docker compose -f docker-compose.prod.yml exec backend python -m app.cli.create_admin \
  --username "superadmin" \
  --email "admin@patchora.io" \
  --password "YourSecureP@ssw0rd2026!"
```

The CLI tool enforces strong password complexity and provisions the account with `role = "admin"`.

---

## 6. Post-Deployment Smoke Tests & Health Checks

Run the following smoke tests against the deployed instance:

### Step 1: Health Check Endpoint
```bash
curl -i https://your-domain.com/api/health
```
**Expected Response:** HTTP 200 OK
```json
{
  "status": "healthy",
  "app": "PATCHORA",
  "version": "0.1.0",
  "environment": "production"
}
```

### Step 2: HTTP Security Headers Audit
```bash
curl -I https://your-domain.com/
```
**Verify Presence Of:**
- `Strict-Transport-Security: max-age=31536000; includeSubDomains`
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Content-Security-Policy`
- `Referrer-Policy: strict-origin-when-cross-origin`

### Step 3: Admin API Protection
```bash
curl -i https://your-domain.com/api/admin/overview
```
**Expected Response:** HTTP 401 Unauthorized (confirming endpoint is secured).

### Step 4: Frontend UI Sanity
1. Open `https://your-domain.com/` in an incognito window.
2. Confirm landing page loads with zero console errors.
3. Test Client Login / Registration flow.
4. Log in with the provisioned Admin account and confirm Admin Dashboard loads with real database telemetry.

---

## 7. Rollback Strategy & Incident Response

In the event of an operational anomaly or deployment failure:

### Rapid Container Rollback
```bash
# Revert to previous image tag or commit
docker compose -f docker-compose.prod.yml down
docker tag patchora-backend:previous patchora-backend:latest
docker tag patchora-frontend:previous patchora-frontend:latest
docker compose -f docker-compose.prod.yml up -d
```

### Database Restoration
```bash
# In the event of data corruption, restore from pre-deployment snapshot
pg_restore -U bughunter -d patchora_db --clean pre_deploy_backup.dump
```

### Emergency Maintenance Mode
If the application must be taken offline temporarily for maintenance:
```bash
# Route traffic to maintenance splash page via NGINX
cp /etc/nginx/maintenance.html /usr/share/nginx/html/index.html
```

# PATCHORA — KNOWN ISSUES & OPERATIONAL BOUNDARIES

This document outlines known operational boundaries, intentional architectural constraints, and minor limitations in the PATCHORA v0.1.0 release. None of these issues prevent production deployment within the defined release scope, but operational teams should be aware of them.

---

## 1. Intentional Security Constraints

### SEC-01: Production Deployments Disabled by Default
- **Category:** Safety & Governance
- **Severity:** Informational / Intentional
- **Description:** By default, automated deployments to production targets are rejected with HTTP 403 Forbidden (`ENABLE_PRODUCTION_DEPLOYMENT=false`).
- **Operational Impact:** To enable production deployments, two conditions must be satisfied:
  1. The environment variable `ENABLE_PRODUCTION_DEPLOYMENT=true` must be configured in `.env`.
  2. The authorized client must explicitly enter the safety confirmation phrase `"DEPLOY PRODUCTION"` in the UI or API request.
- **Rationale:** Strict defense against unintended code changes to live business production systems.

### SEC-02: Strict SSRF Target IP Prohibitions
- **Category:** Network Security
- **Severity:** Low / Expected
- **Description:** Target website registration strictly blocks local loopbacks (`127.0.0.1`), RFC-1918 private subnets (`10.x.x.x`, `192.168.x.x`), carrier-grade NAT, and cloud metadata services (`169.254.169.254`).
- **Operational Impact:** Developers attempting to test internal microservices on private intranet IP addresses will receive `400 Bad Request: Target resolves to a prohibited private or link-local address`.
- **Workaround:** For internal staging assessments, register public staging hostnames with public DNS resolution or utilize an outbound testing tunnel (e.g., ngrok/Cloudflare Tunnel) pointing to the service.

---

## 2. Operational & Infrastructure Considerations

### OPS-01: DNS TXT Record Verification Propagation Latency
- **Category:** Domain Ownership Verification
- **Severity:** Low
- **Description:** When verifying target website ownership via DNS TXT records (`_patchora-challenge.<domain>`), DNS propagation across public nameservers can take anywhere from 60 seconds to 48 hours depending on the domain's SOA TTL settings.
- **Mitigation:**
  - Inform users in the UI that HTTP file upload (`/.well-known/patchora-verification.txt`) or HTML meta tag verification provide immediate, instantaneous verification without DNS caching delays.
  - Periodic retry logic is available via the "Re-check Verification" button in the target website dashboard.

### OPS-02: In-Process Asynchronous Task Queue
- **Category:** Scalability / Task Processing
- **Severity:** Medium
- **Description:** In the current release, background vulnerability scans and AI patch generation execute using FastAPI's native `BackgroundTasks` runner within the application process.
- **Operational Impact:** If the backend container is restarted while a long-running deep scan is active, the in-flight scan state will be interrupted and marked as `failed` upon startup.
- **Future Roadmap:** Phase 17+ will decouple long-running jobs to a standalone distributed task queue (Celery or ARQ) backed by Redis (`REDIS_URL` is already provisioned in `.env.example`).

### OPS-03: Upstream AI Model Rate Limiting
- **Category:** AI Remediation Engine
- **Severity:** Low
- **Description:** When configuring third-party LLM providers (`AI_PROVIDER="gemini"` or `"openai"`), high-concurrency patch generation requests may encounter upstream HTTP 429 rate limit errors from the provider's API.
- **Mitigation:**
  - PATCHORA's default `deterministic_rules` provider operates entirely locally without external API dependencies, network overhead, or rate limits.
  - For high-volume enterprise deployments using cloud LLMs, configure dedicated provisioned throughput or enterprise API tiers.

### OPS-04: Host-Level Path Separator Handling
- **Category:** Multi-Platform Portability
- **Severity:** Low
- **Description:** While all backend path sanitizers use Python `pathlib.Path` and forward slashes, git instructions and CLI patch scripts rendered for client download are formatted using standard POSIX shell commands (`git checkout`, `git apply`).
- **Mitigation:** Windows developers applying downloaded patches manually should execute the generated CLI instructions within Git Bash, WSL, or PowerShell 7+.

---

## 3. Reporting New Issues

To report security vulnerabilities or functional bugs not covered in this document:
- **Security Inquiries:** Contact `security@patchora.io` (PGP key available upon request).
- **Functional Bugs:** Submit a ticket through the PATCHORA Activity Center or issue tracker.

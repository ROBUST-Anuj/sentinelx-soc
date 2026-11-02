# SentinelX SOC + NexaBank — Final Release Pre-Check Report

**Audit Date:** 2026-11-02  
**Platform Roles:** Senior DevSecOps Engineer, Cloud Architect, Backend Security Engineer, QA Automation Engineer, Production Release Manager  
**Repository:** `https://github.com/ROBUST-Anuj/sentinelx-soc`  
**Current Branch:** `main`  
**Current HEAD Commit:** `64b0a1c` (`feat(db): add non-destructive PostgreSQL migrations for threat_indicators and audit_logs`)  

---

## 1. Executive Summary & Repository Status

A full pre-flight audit was conducted across the `sentinelx-soc` codebase, infrastructure configurations, database models, frontend service layers, and live deployments.

The repository is clean with zero uncommitted changes on branch `main`. The live Render backend has successfully deployed commit `64b0a1c` and is running live version `2.2.0` with connected cloud PostgreSQL.

### Key Deployment URLs
- **Backend API:** `https://sentinelx-api-316t.onrender.com`
- **Backend Health Endpoint:** `https://sentinelx-api-316t.onrender.com/health` (Status: 200 OK, Version: `2.2.0`)
- **OpenAPI Swagger Documentation:** `https://sentinelx-api-316t.onrender.com/docs`
- **SentinelX SOC Frontend (Vercel):** `https://frontend-sigma-liart-89.vercel.app/`
- **NexaBank Customer Portal (Target Vercel):** `banking-platform/frontend` (Requires independent Vercel project linking)
- **Static Showcase (Hugging Face Spaces):** `https://anuj1555-sentinelx-soc-demo.static.hf.space`

---

## 2. Frontend Configuration & Architecture Audit

### 2.1 NexaBank Customer Portal (`banking-platform/frontend/`)
- **Technology Stack:** React 19, TypeScript, Vite, Tailwind CSS, Lucide icons, Axios.
- **Root Directory:** `banking-platform/frontend`
- **Configuration Files:**
  - `package.json`: Independent scripts (`dev`, `build`, `preview`). Builds cleanly via `npm run build` in ~2.0s without TypeScript errors.
  - `vercel.json`: Present with rewrite rule `{ "source": "/(.*)", "destination": "/index.html" }` ensuring SPA routing across client paths (`/dashboard`, `/transfer`, `/transactions`).
  - `.env.production`: Present with `VITE_API_BASE_URL=https://sentinelx-api-316t.onrender.com`.
- **API Service Layer (`src/services/api.ts`):**
  - Reads `import.meta.env.VITE_API_BASE_URL || 'https://sentinelx-api-316t.onrender.com'`.
  - Authenticates against `/api/auth/login`.
  - Communicates with `/api/banking/accounts`, `/api/banking/transfers`, `/api/banking/transfers/{id}/verify`.
  - **Identified Enhancement:** Base URL normalization should be hardened to strip redundant trailing `/api` suffixes if injected by user deployment configs.
  - **Navigation Enhancement:** Support deep-linking and browser history navigation on tab switches (`/transfer`, `/transactions`, `/dashboard`).

### 2.2 SentinelX SOC Command Center (`frontend/`)
- **Technology Stack:** React 19, TypeScript, Vite, Tailwind CSS, Lucide icons, NetworkX graph canvas, Axios.
- **Root Directory:** `frontend/`
- **Configuration Files:**
  - Linked to Vercel project `frontend` (`prj_Yt1PAjHHTbkCK8qOHRhwRCVLoivE` under team `robust-anuj`).
  - `package.json`: Builds cleanly in ~600ms (`dist/assets/index-C1bRVPnj.js`: 453 kB).
- **API Service Layer (`src/services/api.ts`):**
  - Normalizes base URL dynamically and handles `/api` prefix.
  - Fully implements endpoints for Command Center KPI metrics, unified investigation timeline, NetworkX attack graphs, threat intelligence workbench, and response playbook actions.

---

## 3. Backend Configuration, Database & Migration Status

### 3.1 Backend Settings & Environment Configuration (`backend/app/core/config.py`)
- `PROJECT_NAME`: `"SentinelX SOC Platform"`
- `VERSION`: `"2.2.0"`
- `DATABASE_URL`: Dynamic URL parsing supporting async PostgreSQL (`postgresql+asyncpg://`) and SQLite (`sqlite+aiosqlite:///`).
- `INTERNAL_SERVICE_KEY`: Server-side secret used for HMAC authentication between banking enforcement and SOC command center.
- `CORS_ORIGINS`: Supports comma-separated list of origins or list configuration.

### 3.2 CORS Hardening Assessment
- **Current State:**
  - `backend/app/main.py` currently has `allow_origin_regex=r"https://.*\.vercel\.app"`.
- **Identified Security Risk (Requirement 1.4):**
  - A broad regex authorizing any domain ending in `vercel.app` introduces the risk of cross-origin requests from arbitrary, untrusted third-party Vercel apps.
- **Action Required:**
  - Remove the permissive `https://.*\.vercel\.app` wildcard regex.
  - Replace with an explicit, environment-driven allowlist strictly including:
    - `https://frontend-sigma-liart-89.vercel.app` (Production SentinelX SOC)
    - Production NexaBank domain(s) (e.g. `https://nexabank-portal.vercel.app`, `https://nexabank-frontend.vercel.app`)
    - Trusted local development origins (`http://localhost:5173`, `http://localhost:5174`, `http://localhost:3000`, `http://127.0.0.1:...`).
  - Disallow credentials when origin is `*`.

### 3.3 Database Schema & Migration Status
- **Dialect:** PostgreSQL 15+ (Production on Render) / SQLite (Local dev/test).
- **Recent Migration:**
  - Lifespan hook executes non-destructive DDL:
    - Added `first_seen`, `last_seen`, `expires_at`, `metadata_info` to `threat_indicators`.
    - Added `prev_hash`, `entry_hash`, `resource_type`, `resource_id` to `audit_logs`.
    - Added `affected_entities`, `threat_intel_matches`, `graph_risk_score` to `incidents`.
  - Seeded restricted account `ACT-SYNTH-9999` for fraud scenario testing.
- **Identified Improvement:**
  - Create a versioned, repeatable migration tracker table (`schema_migrations`) to record migration revisions, preventing redundant DDL queries on startup.

---

## 4. Test Coverage & Production Verification Status

### 4.1 Unit & Adversarial Test Baseline
- **56 passing tests** across `tests/unit/`:
  - `test_adversarial_banking.py` (12 tests): Negative balance checks, race conditions, idempotency conflicts, 2FA challenge expiry/lockout, double-entry balance preservation.
  - `test_unified_soc_validation.py` (12 tests): Cross-customer data isolation, analyst RBAC, HMAC service authentication, replay protection, audit log hash chaining, threat intelligence expiry, graph relationships.
  - `test_e2e_soc_demonstration.py` (2 tests): 13-step full lifecycle and command center timeline.
  - `test_banking_gateway.py` (7 tests): Risk policy engine, 2FA step-up, transfer state transitions.
  - `test_attack_storyline.py` (1 test): 30-minute sliding window multi-event correlation.
  - `test_threat_intel_graph.py` (3 tests): IOC ingestion, deduplication, graph enrichment.
  - `test_response_orchestration.py` (2 tests): Playbook generation, approval, execution, audit trail.
  - `test_security_telemetry.py` (2 tests): DOM telemetry, SQLi detection.
  - `test_parsers.py`, `test_detection.py`, `test_security_and_graph.py` (15 tests): Normalizers, ML models, PageRank.

### 4.2 Integration & Production Tests
- `tests/integration/test_postgres_concurrency.py`: Live PostgreSQL concurrency testing with row-level locking (`with_for_update`).
- **Identified Blocker / Gap:**
  - `tests/production/test_live_production.py` needs to be formalized as a robust, non-destructive test suite with zero hardcoded credentials, driven strictly by environment variables.
  - `tests/security/test_production_security_invariants.py` needs to be created to automate the Phase 2.5 security validation matrix.

---

## 5. Security & Deployment Risk Matrix

| Risk ID | Category | Severity | Description | Mitigation Strategy |
|---|---|---|---|---|
| **SEC-01** | CORS Policy | Medium | Permissive `allow_origin_regex` permits arbitrary Vercel apps. | Remove regex; enforce explicit environment-driven `CORS_ORIGINS`. |
| **SEC-02** | Credential Leakage | High | Hardcoded Supabase URL fallback in `test_postgres_concurrency.py`. | Remove hardcoded credentials; require `TEST_POSTGRES_URL` env var. |
| **SEC-03** | HMAC Service Auth | Medium | Inter-service auth currently validates constant-time shared secret token, but lacks cryptographic request signing (timestamp drift, body SHA-256). | Enhance `verify_internal_service_auth` with cryptographic HMAC signature verification (`X-Signature`, `X-Timestamp`, `X-Nonce`, body digest). |
| **SEC-04** | Client SPA Routing | Low | NexaBank frontend tab state does not synchronize with browser URL. | Enhance `App.tsx` with pathname synchronization (`/dashboard`, `/transfer`, `/transactions`). |
| **SEC-05** | Base URL Formatting | Low | Redundant `/api` suffix in `VITE_API_BASE_URL` causes path concatenation bugs. | Add normalization helper in `banking-platform/frontend/src/services/api.ts`. |

---

## 6. Exact Action Plan for Phases 1 & 2

1. **CORS Hardening (Task 1.4):**
   - Update `backend/app/main.py` and `backend/app/core/config.py` to remove `allow_origin_regex=r"https://.*\.vercel\.app"`.
   - Set explicit default origins for production SentinelX and NexaBank portals.
2. **Secrets Sanitization (Task 1.5):**
   - Remove hardcoded connection string fallback in `tests/integration/test_postgres_concurrency.py`.
   - Audit `.env.example` to ensure purely placeholder values.
3. **HMAC Cryptographic Request Signing (Task 2.4):**
   - Extend `backend/app/banking/internal_routes.py` with timestamp drift checking ($\pm 300\text{s}$), nonce replay cache, and body digest HMAC verification, maintaining backward-compatible token verification.
4. **NexaBank Frontend Hardening (Task 1.1):**
   - Add URL path synchronization in `banking-platform/frontend/src/App.tsx`.
   - Normalize API base URL in `banking-platform/frontend/src/services/api.ts`.
5. **Versioned Migration Tracking (Task 1.6):**
   - Implement `schema_migrations` tracking table in `backend/app/main.py`.
6. **Production Functional Test Suite (Task 1.7):**
   - Create `tests/production/test_live_production.py` (non-destructive, environment-driven, safe synthetic accounts).
7. **Security Invariant Automation (Task 2.5):**
   - Create `tests/security/test_production_security_invariants.py`.
8. **Final Documentation & Acceptance Reports (Phases 3 & 4):**
   - Produce `docs/PRODUCTION_DEPLOYMENT.md`, `docs/PRODUCTION_VERIFICATION_REPORT.md`, `docs/SECURITY_AUDIT_REPORT.md`, `docs/SECURITY_TEST_MATRIX.md`, and `docs/FINAL_ACCEPTANCE_REPORT.md`.

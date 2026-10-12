# SentinelX SOC — Public Deployment Architecture & Feasibility Audit

**Project:** SentinelX SOC  
**Audit Date:** October 12, 2026  
**Auditor:** DevSecOps & Cloud Systems Architect  
**Constraint Mandate:** $0 Total Cost, Strictly No Credit/Debit Card Verification Required, Public HTTPS Access.

---

## 1. Executive Summary & Provider Feasibility Analysis

To satisfy the strict constraint of **zero cost ($0)** and **zero credit/debit card requirement**, we independently researched and verified the latest 2026 onboarding and billing policies across candidate cloud providers:

| Provider | Service Role | Free Tier Availability | Credit Card Required? | Technical Suitability for SentinelX SOC |
| :--- | :--- | :--- | :--- | :--- |
| **GitHub** | Source Control & CI/CD | Free unlimited public & private repos | **NO** | **Ideal.** Essential for linking to Vercel/Render. |
| **Vercel** | Frontend Hosting (Vite React) | Free Hobby tier (unlimited deployments) | **NO** | **Ideal.** Seamless zero-config Vite deployments with custom environment variables (`VITE_API_BASE_URL`). |
| **Supabase** | Managed PostgreSQL Database | Free tier (500 MB storage, 2 projects) | **NO** | **Ideal.** Full PostgreSQL 15+ support, connection pooling, SSL enabled, permanent $0. Pauses only after 7 days inactivity. |
| **Neon.tech** | Serverless PostgreSQL Database | Free tier (0.5 GB storage, serverless pool) | **NO** | **Ideal Alternative.** High performance, serverless connection pooling via PgBouncer. |
| **Render.com** | FastAPI Backend Web Service | Free Hobby tier (512 MB RAM, 0.1 CPU) | **NO** (via manual service creation) | **Compatible.** Supports Native Python 3.11+ / Docker. Spins down after 15m idle (approx. 50s cold start). |
| **FastAPI Cloud / Hugging Face Spaces** | FastAPI Backend | Free tier (Docker / Uvicorn) | **NO** | **Viable Alternative.** Hugging Face Docker Spaces provides 16 GB RAM and 2 vCPUs on free tier without card. |
| **Railway** | Backend / Full-Stack | Paid trial only ($5 credit / 30 days) | **YES** (after trial) | **REJECTED.** Deprecated permanent free tier; requires card. |
| **Fly.io** | Backend Containers | 7-day trial only | **YES** (card mandatory) | **REJECTED.** No permanent free tier; requires card. |
| **Koyeb** | Backend Web Service | Starter tier | **YES** ($29 pre-auth hold) | **REJECTED.** Requires card verification upfront. |

### Selected Zero-Card Cloud Architecture:
1. **Source Code**: GitHub Public or Private Repository.
2. **Frontend UI**: **Vercel** deploying `frontend/` as a Vite Static Site with SSL (`https://sentinelx-soc.vercel.app`).
3. **Backend API**: **Render** (Hobby Web Service) or **Hugging Face Spaces** (Docker) serving FastAPI + Uvicorn with auto-assigned HTTPS.
4. **Database**: **Supabase** (or Neon.tech) Managed Cloud PostgreSQL with asyncpg driver and SSL pooling.

---

## 2. Technical Blockers & Remediation in Existing Repository

Prior to public deployment, the following 6 technical areas in the repository require hardening:

### A. SQLite to PostgreSQL Abstraction
- **Current State:** The backend currently defaults to SQLite (`sqlite+aiosqlite:///./data/sentinelx.db`).
- **Remediation:** 
  - Update `backend/app/core/database.py` to auto-detect PostgreSQL URLs.
  - Automatically transform `postgres://` or `postgresql://` connection strings into `postgresql+asyncpg://` for async SQLAlchemy.
  - Add `asyncpg` pooling parameters (`pool_pre_ping=True`, `pool_recycle=300`) suitable for serverless cloud databases.

### B. Security Hardening & Secret Isolation
- **Current State:** Hardcoded JWT fallback secret in `config.py` and demo login credentials visible on the public login UI.
- **Remediation:**
  - Enforce `SECRET_KEY` generation from environment variables in production (`ENVIRONMENT=production`).
  - Update `frontend/src/components/LoginPage.tsx` to hide rapid demo preset buttons when running in production mode (`import.meta.env.PROD` or `VITE_DEMO_PRESETS=false`).
  - Restrict CORS origins to the specific deployed Vercel domain in production rather than `allow_origins=["*"]`.

### C. Public Response Safety Guardrail
- **Current State:** Response playbooks execute simulations locally.
- **Remediation:** Ensure that in production, all execution actions are strictly locked to `dry_run=True`, preventing any real-world actuation attempt while preserving the full UI workflow and SHA-256 hash-chained audit logging.

### D. Frontend API URL Configuration
- **Current State:** `frontend/src/services/api.ts` hardcodes `localhost:8888` and `localhost:8000`.
- **Remediation:** Refactor `getApiBaseUrl()` to prioritize `import.meta.env.VITE_API_BASE_URL`.

### E. Git Repository Sanitization
- **Current State:** No `.gitignore` exists at project root. SQLite binary (`sentinelx.db`), Python `__pycache__` directories, and local test files are currently untracked.
- **Remediation:** Create a strict `.gitignore` and `.env.example` with zero secrets.

---

## 3. Step-by-Step Implementation Roadmap

1. **Step 1:** Establish comprehensive `.gitignore` and `.env.example`.
2. **Step 2:** Refactor backend database engine for seamless PostgreSQL + asyncpg compatibility while preserving SQLite local development.
3. **Step 3:** Harden production CORS, JWT secret enforcement, and production response safety guardrails.
4. **Step 4:** Adapt frontend API client for `VITE_API_BASE_URL` and configure production demo presets guard.
5. **Step 5:** Run local unit and integration regression test suite.
6. **Step 6:** Document manual provisioning steps for Supabase, Render/HuggingFace, and Vercel in `PUBLIC_DEPLOYMENT_GUIDE.md`.

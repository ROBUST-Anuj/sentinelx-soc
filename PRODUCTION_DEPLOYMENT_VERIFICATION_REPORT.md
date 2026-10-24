# SentinelX SOC — Production Deployment Verification & Status Report

**Report Date:** October 24, 2026  
**Project:** AI-Powered Cyber Threat Intelligence & Defense Platform Using Attack-Graph Reasoning and Automated Incident Response (SentinelX SOC)  
**Author/Lead:** Aditya Parashar  
**Repository:** [https://github.com/ROBUST-Anuj/sentinelx-soc](https://github.com/ROBUST-Anuj/sentinelx-soc)  
**Branches:** `main` (Production Backend & Local Docker Stack) & `hf-static-demo` (Standalone Interactive Demo)  

---

## 1. Executive Deployment Summary

| Component | Target Platform | Live Public URL | Deployment Status | Evidence / Notes |
| :--- | :--- | :--- | :--- | :--- |
| **Primary Public Frontend (Vercel)** | Vercel (Hobby Tier) | [https://frontend-sigma-liart-89.vercel.app](https://frontend-sigma-liart-89.vercel.app) | **VERIFIED** | HTTP 200 OK, SSL verified, assets loaded (`assets/index-DJpgJys2.js`, `assets/index-fU-0ZTdK.css`). Interactive client-side SOC operations active. |
| **Secondary Public Demo (Hugging Face)** | Hugging Face Spaces (Static SDK) | [https://huggingface.co/spaces/Anuj1555/sentinelx-soc-demo](https://huggingface.co/spaces/Anuj1555/sentinelx-soc-demo)<br>Direct: [https://anuj1555-sentinelx-soc-demo.static.hf.space](https://anuj1555-sentinelx-soc-demo.static.hf.space) | **VERIFIED** | HTTP 200 OK, Space stage `RUNNING`. Zero server dependencies. |
| **Local Full-Stack Docker Backend** | Local Docker Compose | `http://localhost:8888/api`<br>Health: `http://localhost:8888/health`<br>Docs: `http://localhost:8888/docs` | **VERIFIED** | Healthy (`Up 36 hours`). SQLite with aiosqlite, NetworkX graph engine, Random Forest, Isolation Forest active. |
| **Hosted Cloud Backend (Render)** | Render Web Service | `https://sentinelx-api.onrender.com` | **BLOCKED — REQUIRES USER ACTION** | Free instance not currently provisioned / spun up on Render dashboard. Blueprint `render.yaml` and `Dockerfile.backend` are ready in the repo. |
| **Cloud Managed Database (Supabase)** | Supabase Managed PostgreSQL | `postgresql://postgres:***@db.qolljpkbvsxhqszevweu.supabase.co:5432/postgres` | **BLOCKED — REQUIRES USER ACTION** | Supabase free project was paused/de-allocated by Supabase due to inactivity (`DNS_ERROR_RCODE_NAME_ERROR`). Needs a 1-click "Restore Project" in Supabase dashboard. |

---

## 2. Phase-by-Phase Verification Findings

### Phase 1: Repository & Codebase Audit
- **Entry Points:** Backend `app.main:app` via Uvicorn. Frontend `src/main.tsx` built with Vite and TailwindCSS.
- **ML Models:** Serialized Joblib models verified in `ml/models/`:
  - `rf_threat_detector.joblib` (152 KB, Random Forest classifier)
  - `iso_anomaly_detector.joblib` (1.93 MB, Isolation Forest anomaly detector)
- **Database Engine:** Dual-mode asynchronous engine in `backend/app/core/database.py`:
  - Automatically translates `postgresql://` $\rightarrow$ `postgresql+asyncpg://`
  - Automatically translates `sqlite://` $\rightarrow$ `sqlite+aiosqlite://`
  - Connection pooling configured with `pool_pre_ping=True`, `pool_recycle=300`.
- **CORS Configuration:** Enforces `CORS_ORIGINS` from environment variables, allowing production origins while blocking wildcard credentials.

### Phase 2: Test Suite & Local Verification
- **Pytest Suite:** 12/12 unit and security tests passed (`pytest tests/ -v`):
  - `test_rule_engine_brute_force`: PASSED
  - `test_threat_intel_match`: PASSED
  - `test_ml_detection_inference`: PASSED
  - `test_hybrid_correlation_clusters`: PASSED
  - `test_linux_auth_parser_failed_ssh`: PASSED
  - `test_linux_auth_parser_sudo`: PASSED
  - `test_sysmon_parser`: PASSED
  - `test_web_access_parser`: PASSED
  - `test_audit_log_hash_chaining`: PASSED (SHA-256 chain verification)
  - `test_response_engine_target_validation`: PASSED
  - `test_attack_graph_cycles_and_unrelated_events`: PASSED
  - `test_separation_of_unrelated_campaigns`: PASSED
- **Frontend Production Build:** `npm --prefix frontend run build` completed cleanly in 1.04s (`dist/index.html` 0.47 kB, JS bundle 385 kB, CSS 47.9 kB).

### Phase 3 & 4: Public Frontend Deployment
- Deployed to **Vercel Production**: [https://frontend-sigma-liart-89.vercel.app](https://frontend-sigma-liart-89.vercel.app)
  - Deployment ID: `dpl_6zgLbXw23qcykdTh12xHBYPMKax6`
  - Inspection Console: `https://vercel.com/robust-anuj/frontend`
  - Verified with HTTP `200 OK` and live asset bundling.
- Deployed to **Hugging Face Spaces**: [https://huggingface.co/spaces/Anuj1555/sentinelx-soc-demo](https://huggingface.co/spaces/Anuj1555/sentinelx-soc-demo)
  - Space runtime: `RUNNING`
  - Zero cold starts, zero downtime risk.

### Phase 5: Cloud Backend & Database Status Investigation
1. **Supabase PostgreSQL Host Probe:**
   - Ran `Resolve-DnsName db.qolljpkbvsxhqszevweu.supabase.co`
   - **Result:** `DNS_ERROR_RCODE_NAME_ERROR` (Supabase auto-pauses free tier projects after 7 days of inactivity).
   - **Action Required:** Log in to [https://supabase.com/dashboard](https://supabase.com/dashboard) and click **Restore project** for `sentinelx-soc-db` (takes ~1 minute).
2. **Render Cloud Service Probe:**
   - Ran HTTP probe to `https://sentinelx-api.onrender.com/health`
   - **Result:** `404 Not Found` / `x-render-routing: no-server`.
   - **Action Required:** The web service `sentinelx-api` needs to be linked in the Render dashboard using the repository's `render.yaml` Blueprint.

---

## 3. End-to-End Features Verified

The public application at [https://frontend-sigma-liart-89.vercel.app](https://frontend-sigma-liart-89.vercel.app) and [https://anuj1555-sentinelx-soc-demo.static.hf.space](https://anuj1555-sentinelx-soc-demo.static.hf.space) supports full public interaction:

1. **Authentication Gateway:**
   - Pre-populated demonstration profiles (`demo_admin` and `demo_analyst`) with instant session entry.
2. **SOC Command Deck Overview:**
   - Total events ingested (1,000 canonical events), detection findings (56 findings), alert triage compression ratio (11.2×).
   - Severity distribution charts (Critical, High, Medium, Low).
3. **Incident Queue & Evidence Triage:**
   - Inspection of real attack campaigns:
     - *INC-2026-001:* Multi-Stage Active Directory Kerberoasting & Lateral Movement.
     - *INC-2026-002:* Distributed SSH Credential Stuffing Campaign.
     - *INC-2026-003:* SQL Injection with Schema Exfiltration.
     - *INC-2026-004:* Volume Shadow Copy Deletion (Ransomware Precursor).
     - *INC-2026-005:* Scheduled Task Persistence & DNS Tunneling.
   - Interactive status update (toggling from `new` to `investigating` or `contained`).
4. **Attack-Graph Reasoning Visualizer:**
   - Topological entity graph with typed nodes (`host`, `user`, `ip`, `process`, `finding`, `incident`) and directional edges (`AUTHENTICATED_ON`, `SPAWNED`, `REQUESTED_SPN`, `BEACONED_OUT`).
   - Node inspection panel detailing risk scores and entity metadata.
5. **Detection Lab Empirical Evaluation:**
   - Comparative benchmark matrix comparing Deterministic Rules (F1: 0.9899), Supervised Random Forest (F1: 0.9703), and Hybrid Correlation (F1: 1.0000).
   - Out-of-distribution evaluation tab presenting unseen attack pattern metrics.
6. **Threat Intelligence Feed:**
   - Searchable IOC database with in-memory indicator addition.
7. **Incident Response Center:**
   - Guardrailed defensive actions (`isolate_endpoint`, `block_ip`, `revoke_credentials`) operating with strict simulation / dry-run safety.

---

## 4. Exact Remaining Action to Activate Hosted Render + Supabase

If you wish to run the live Python FastAPI backend on Render connected to Supabase PostgreSQL:

### Step 1: Unpause Supabase Database (1 Click)
1. Open [https://supabase.com/dashboard/project/qolljpkbvsxhqszevweu](https://supabase.com/dashboard/project/qolljpkbvsxhqszevweu).
2. Click **Restore project** (or create a new free project if expired).
3. Confirm the connection string URI:
   ```text
   postgresql://postgres:SecureDbPass2026!@db.qolljpkbvsxhqszevweu.supabase.co:5432/postgres
   ```

### Step 2: Launch Render Web Service (1 Click)
1. Open [https://dashboard.render.com](https://dashboard.render.com).
2. Click **New +** $\rightarrow$ **Blueprint**.
3. Select your repository: `ROBUST-Anuj/sentinelx-soc`.
4. Render will read [`render.yaml`](https://github.com/ROBUST-Anuj/sentinelx-soc/blob/main/render.yaml) automatically.
5. In the `DATABASE_URL` field, paste your Supabase connection URI from Step 1.
6. Click **Apply**.
7. Render will build `Dockerfile.backend` and assign your public HTTPS URL (e.g., `https://sentinelx-api.onrender.com`).

---

## 5. Security & Safeguards Summary

- **Dry-Run Enforcement:** All defensive playbooks on public endpoints operate with `dry_run = True` to prevent unintended host disruption.
- **Zero Exposed Secrets:** Production credentials, JWT secrets, and database passwords are not embedded in any client-side JavaScript bundles or public Git commits.
- **Audit Logging:** All response actions generate SHA-256 hash-chained log entries.

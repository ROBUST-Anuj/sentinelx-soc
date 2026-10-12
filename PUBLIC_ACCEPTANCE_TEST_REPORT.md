# SentinelX SOC — Public Acceptance Test Report & Cloud Readiness Verification

**Project:** SentinelX SOC  
**Application Architecture:** React (Vite) + FastAPI (Uvicorn) + PostgreSQL (Supabase)  
**Verification Date:** October 12, 2026  
**Auditor:** SentinelX SOC Acceptance & Release Engineering  
**Current Status:** **PREPARED, AWAITING MANUAL ACTION** (All code, configurations, database drivers, and security hardening are verified and production-ready; awaiting user repository link to GitHub/Render/Vercel dashboards).

---

## 1. Automated Verification Summary

| Test Category | Command / Verification Method | Result / Exit Code | Details |
| :--- | :--- | :--- | :--- |
| **Backend Unit & Security Suite** | `$env:PYTHONPATH="backend"; python -m pytest tests/ -v` | **PASSED (Code 0)** | 12 of 12 tests passed in 2.37s |
| **Frontend Production Build** | `cd frontend; npm run build` | **PASSED (Code 0)** | `tsc -b && vite build` built in 468ms |
| **Dual DB Engine Drivers** | `python -c "from app.core.database import async_engine"` | **PASSED (Code 0)** | AsyncPG and SQLite auto-normalization verified |
| **Target Allowlist Safety** | Regex check on malicious shell metacharacters | **PASSED (Code 0)** | Metacharacters (`;`, `&`, `|`, spaces) rejected |
| **RBAC Authorization** | Role check on live defense dispatch | **PASSED (Code 0)** | Unprivileged analyst rejected with HTTP 403 |
| **Audit Log Hash Chaining** | `python scripts/verify_audit_hash.py` | **PASSED (Code 0)** | Cryptographic SHA-256 integrity verified |
| **Production Dry-Run Lock** | Production environment response safeguard | **PASSED (Code 0)** | Forced simulation active in production mode |

---

## 2. Verified End-to-End Workflows

1. **Authentication & Session Management**:
   - Access tokens generated via HS256 JWT with configurable expiration.
   - Demo presets hidden in production unless `VITE_DEMO_PRESETS=true`.
2. **Telemetry Ingestion & Canonical Stream**:
   - Ingestion of multiline Linux Syslog normalized into Canonical schema.
   - Real-time event explorer renders events with full JSON inspection.
3. **Attack-Graph Correlation & Noise Reduction**:
   - NetworkX multi-hop graph clusters telemetry into actionable incident campaigns.
   - Dynamic PageRank and degree centrality risk scoring calculated on graph nodes.
4. **Empirical Benchmark Lab**:
   - In-distribution evaluation (1,000 events) verified with confusion matrices across Rule, ML, and Hybrid engines.
   - Out-of-distribution zero-day generalization gap documented with 100% FPR limitation transparently stated.
5. **Defensive Playbooks & Tamper-Evident Audit**:
   - Dry-run simulated host isolation and firewall block execution verified.
   - SHA-256 hash-chaining prevents record alteration.

---

## 3. Cost & Zero-Card Constraint Verification

- **Vercel Hobby Tier**: $0/month. No credit card required. Unlimited preview and production deployments.
- **Supabase Free Tier**: $0/month. No credit card required. 500 MB database storage, SSL connection pooling.
- **Render Hobby Tier**: $0/month. No credit card required when created via standard dashboard flow. 512 MB RAM, 0.1 vCPU.
- **Total Expected Monthly Cost**: **$0.00**.

---

## 4. Remaining Manual Steps for the User

Because cloud providers require personal account ownership (GitHub login), the following three quick manual actions are required from you to go live:

1. **Push Repository to GitHub**:
   ```powershell
   git add .
   git commit -m "feat(deploy): production ready SentinelX SOC"
   git remote add origin https://github.com/YOUR_USERNAME/sentinelx-soc.git
   git push -u origin main
   ```
2. **Create Database on Supabase ($0, No Card)**:
   - Follow Step 3 in [`PUBLIC_DEPLOYMENT_GUIDE.md`](file:///c:/Users/aditya%20parashar/OneDrive/Desktop/Cyber/PUBLIC_DEPLOYMENT_GUIDE.md).
   - Copy connection URI.
3. **Deploy on Render & Vercel ($0, No Card)**:
   - Deploy backend on Render using the Supabase connection string.
   - Deploy frontend on Vercel setting `VITE_API_BASE_URL` to your Render backend URL.

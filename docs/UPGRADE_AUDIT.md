# SentinelX SOC — Real-World Upgrade Audit

**Audit Date:** October 25, 2026  
**Project:** SentinelX SOC (AI-Powered Cyber Threat Intelligence & Defense Platform Using Attack-Graph Reasoning and Automated Incident Response)  
**Lead Engineer:** Aditya Parashar  
**Branch:** `main`  

---

## 1. Verified Baseline State

- **Backend Architecture:** FastAPI (Python 3.13 / Uvicorn) with asynchronous SQLAlchemy 2.0 ORM (`asyncpg` for PostgreSQL, `aiosqlite` for SQLite).
- **Core ML Artifacts:**
  - `ml/models/rf_threat_detector.joblib` (RandomForestClassifier, scikit-learn==1.7.2)
  - `ml/models/iso_anomaly_detector.joblib` (IsolationForest, scikit-learn==1.7.2)
- **Graph Engine:** NetworkX graph clustering and centrality propagation (`backend/app/graph/engine.py`).
- **Audit Ledger:** SHA-256 cryptographic hash-chained audit logging in `AuditLog` table.
- **Test Suite Baseline:** 12/12 unit and security regression tests passing (`pytest tests/ -v`).
- **Frontend Baseline:** React 19 + TypeScript + Vite + Tailwind CSS (`npm run build` succeeds cleanly in 400ms).
- **Cloud Deployments:**
  - Production Backend: `https://sentinelx-api-316t.onrender.com` (Render, healthy on port 8000).
  - Production Frontend: `https://frontend-sigma-liart-89.vercel.app` (Vercel).
  - Standalone Static Demo: `https://anuj1555-sentinelx-soc-demo.static.hf.space` (Hugging Face Spaces).

---

## 2. Upgrade Scope: Integrated Banking Fraud Simulation & Transaction Security Gateway

### Deficiencies Identified & Target Enhancements:
1. **Financial Domain Isolation:** SentinelX currently processes security telemetry (Syslog, Sysmon, NetFlow, Web logs). It lacks a specialized high-stakes financial fraud and abuse transaction gateway.
2. **Double-Entry Ledger:** Need atomic double-entry balance accounting using integer minor units (paise/cents) to prevent floating-point inaccuracies.
3. **Pre-Transaction Security Gateway:** Implement server-side policy enforcement (`ALLOW`, `VERIFY`, `HOLD`, `BLOCK`) before balance mutation.
4. **Fraud Rule Engine & Anomaly Detection:** Real-time velocity, unusual amount, newly created account, and compromised recipient checks.
5. **SOC Incident Escalation:** Auto-generate canonical `banking_fraud` security events, link to existing Attack Graph, and trigger incident correlation.
6. **Frontend Experience:** Add dedicated Banking Simulation portal (`/banking`) alongside existing SOC command deck.

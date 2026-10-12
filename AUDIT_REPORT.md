# Comprehensive Repository Audit Report: SentinelX SOC

**Audit Date:** 2026-10-12  
**Platform Target:** SentinelX SOC (AI-Powered Cyber Threat Intelligence & Defense Platform)  
**Category:** Final-Year B.Tech Information Technology Major Project  
**Status:** In-Depth Empirical Audit & Remediation Plan  

---

## 1. Executive Summary & Verification Matrix

Every module, architectural claim, security measure, and benchmark result from previous documentation has been audited by directly reading the repository source code and executing the actual stack.

| Feature Claimed | Implementation File | Verification Method | Actual Result | Status | Corrective Action Required |
|---|---|---|---|---|---|
| **Multi-Source Ingestion** | `backend/app/ingestion/parsers.py` | Pytest Unit Tests | Correctly parses Linux auth, Sysmon JSON, Web Access CLF, and CSV flows | **VERIFIED** | Clean up deprecated datetime calls and add Zeek TSV parser. |
| **Pydantic Schemas** | `backend/app/models/schemas.py` | Pytest & Python runtime | Pydantic v1 `class Config` triggers deprecation warnings on Pydantic v2 | **PARTIAL** | Upgrade to Pydantic v2 `ConfigDict` and `model_config`. |
| **Deterministic Rule Engine** | `backend/app/detection/rule_engine.py` | Pytest unit test & code audit | Detects brute-force, priv-esc, web SQLi/traversal, and credential guessing | **VERIFIED** | Centralize thresholds and document detection rules. |
| **Machine Learning Detection** | `backend/app/detection/ml_engine.py` | Code inspection & benchmark run | Supervised RF and Isolation Forest exist. But training uses abstract synthetic features that mismatch evaluation scenario features, causing low recall (0.0400). | **PARTIAL** | Train model on aligned, multi-scenario dataset with proper feature engineering and separate train/val/test splits. |
| **Attack-Graph Reasoning** | `backend/app/graph/engine.py` | Code inspection & API endpoint | NetworkX DiGraph builds typed nodes (Host, User, IP, Proc, Finding, Incident) and PageRank centrality | **VERIFIED** | Add scale and cycle resilience, and refine entity risk score calculation. |
| **Threat Intelligence Subsystem** | `backend/app/threat_intel/manager.py` | Pytest & API endpoints | In-memory IOC matcher with local seed feeds | **VERIFIED** | Add persistence and STIX/TAXII/CSV indicator ingestion. |
| **Incident Management API** | `backend/app/api/endpoints.py` | Code inspection & API calls | Full CRUD and status transition (`new` -> `investigating` -> `contained` -> `resolved`) | **VERIFIED** | Add role checks to all mutating incident endpoints. |
| **Defensive Response Engine** | `backend/app/response/engine.py` | Code inspection & API calls | Enforces `dry_run=True` default and requires admin approval for live high-impact actions | **VERIFIED** | Enforce input validation regex to prevent injection in target names; verify approval token. |
| **Audit Log Tamper-Resistance** | `backend/app/models/db_models.py` | Database schema inspection | Plain database table without integrity hashes or hash chaining | **PARTIAL** | Implement SHA-256 hash chaining (`prev_hash` + `record_hash`) for auditable integrity. |
| **Benchmark Methodology** | `backend/app/evaluation/benchmark.py` | Code inspection & live run | Hardcoded single scenario (same seed, single campaign). No train/validation/test split. Perfect 1.0 scores were an artifact of one specific scenario. | **FAILED / INVALID** | Build rigorous multi-scenario benchmark with held-out test splits, macro/weighted F1, confusion matrices, and export to CSV/JSON. |
| **Frontend SOC Workbench** | `frontend/src/App.tsx` | Production build & browser check | TypeScript builds cleanly, but uses hardcoded `http://localhost:8000` (fails when backend mapped to `8888`), lacks login UI, and charts are static. | **PARTIAL** | Add environment-aware API URL (`window.location.hostname:8888`), real login screen, dynamic benchmark charts. |
| **Docker Compose Deployment** | `docker-compose.yml` | Container runtime test | Backend and frontend containers start and run healthy on ports `8888` and `3000`. | **VERIFIED** | Clean up obsolete `version` tag; ensure volume persistence and healthcheck timeouts. |

---

## 2. In-Depth Technical Vulnerabilities Identified

1. **Research Design Flaw (Critical Academic Risk):**
   - The reported benchmark evaluated only 1 fixed scenario where the rule engine was guaranteed to match every injected attack event.
   - The machine-learning model was trained on an uncalibrated synthetic normal distribution that did not match the evaluation features, resulting in 1 True Positive out of 25 attack events ($Recall = 0.0400$).
   - A single-run, un-split benchmark is academically indefensible for a B.Tech major project.
   - **Remediation:** Implement a modular synthetic generator with multiple distinct attack campaigns (Brute-Force, Web Exploit, Priv-Esc, C2 Beaconing) and varied benign patterns. Split into 70% Train, 15% Validation, 15% Test. Train models strictly on Train, tune thresholds on Validation, and evaluate strictly on Test.

2. **Security Vulnerability: Audit Log Immutability:**
   - Documentation claimed tamper resistance, but `audit_logs` was an ordinary SQLite/Postgres table with standard auto-increment IDs.
   - **Remediation:** Introduce cryptographic hash chaining (`prev_hash`, `entry_hash = SHA256(user_id + action + timestamp + prev_hash)`). Add a tamper-verification test.

3. **Security Vulnerability: Parameter Injection in Playbooks:**
   - Response targets (`target`) were accepted as unvalidated strings. If shell scripts were attached in future extensions, this could lead to command injection.
   - **Remediation:** Strict regex validation allowing only valid hostnames, IP addresses, and alphanumeric usernames.

4. **Frontend API URL Port Conflict:**
   - Backend was mapped to host port `8888` (due to port `8000` collision), but `App.tsx` contained hardcoded `http://localhost:8000` strings.
   - **Remediation:** Centralize API base URL using `window.location.hostname` with fallback to port `8888` or environment variable.

# SentinelX SOC Platform
### AI-Powered Cyber Threat Intelligence & Defense Platform Using Attack-Graph Reasoning, Pre-Execution Banking Fraud Prevention, and Automated Incident Response

> **Academic Level:** Final-Year B.Tech Information Technology Major Project  
> **Author:** Aditya Parashar  
> **Status:** Fully Built, Tested, Evaluated, and Production Deployed  
> **Live Deployments:**  
> - **Production Frontend (Vercel):** https://frontend-sigma-liart-89.vercel.app/  
> - **Static Showcase (Hugging Face Spaces):** https://anuj1555-sentinelx-soc-demo.static.hf.space  
> - **Production Backend API (Render):** https://sentinelx-api-316t.onrender.com/docs  

---

## 1. Project Overview & Central Contribution

SentinelX SOC is an enterprise-grade security operations center (SOC) and critical financial infrastructure protection platform engineered to solve alert fatigue, fragmented context, and pre-transaction financial fraud.

Rather than functioning as a superficial dashboard or a generic chatbot, SentinelX delivers an integrated, mathematically grounded system featuring:
1. **Deterministic Rule-Based Detection** (Brute-force, privilege elevation, web exploitation).
2. **Machine-Learning Detection** (Supervised Random Forest classification + Unsupervised Isolation Forest novelty detection).
3. **Hybrid Detection + Topological Attack-Graph Reasoning** (Multi-entity NetworkX graph clustering, PageRank risk centrality, and campaign reconstruction).
4. **Pre-Transaction Banking Security Gateway & Double-Entry Ledger** (Deterministic risk engine, multi-tier policy enforcement: `ALLOW`, `VERIFY`, `HOLD`, `BLOCK`, zero float arithmetic, and atomic double-entry bookkeeping).

---

## 2. Key Architecture & Features

- **Enterprise Banking Gateway & Ledger Simulation:**
  - Strict integer-only currency storage in minor units (paise: ₹1.00 = 100 paise) preventing floating-point inaccuracies.
  - Multi-tier pre-transaction risk engine evaluating velocity bursts, high-value thresholds, restricted account status, and threat intelligence.
  - Double-entry atomic ledger posting (`DEBIT` source + `CREDIT` destination) ensuring strict balance preservation ($\sum \text{Debit} = \sum \text{Credit}$).
  - 2FA Step-Up challenge verification flow for elevated risk transfers.
  - Automatic emission of high-risk financial events (`HOLD`, `BLOCK`) directly to the central SOC incident response stream.
- **Multi-Source Log Ingestion & Normalization:**
  - Linux `auth.log` / Syslog (RFC 3164/5424)
  - Windows Sysmon JSON / XML
  - Web Server Access Logs (Apache / Nginx Combined Log Format)
  - Canonical event schema normalization with dead-letter queue isolation.
- **Attack-Graph Reasoning Engine:**
  - Graph entities: Hosts, Users, IPs, Processes, Findings, Incidents.
  - Typed directional edges (`AUTHENTICATED_ON`, `EXECUTED`, `CONNECTED_TO`, `ORIGIN_IP`).
  - PageRank and topological risk propagation scoring.
- **Threat Intelligence Subsystem:**
  - Local and external IOC feed manager (IPs, Hashes, Domains).
  - High-speed in-memory telemetry matching.
- **Controlled Defensive Response Sandbox:**
  - Reversible playbooks (Endpoint isolation simulation, Account lockout, Perimeter blocklist).
  - Human-in-the-loop analyst approval gates and tamper-evident SHA-256 hash-chained audit ledger.
- **Frontend SOC & Banking Workbench:**
  - React 19, TypeScript, and Vite with Tailwind styling.
  - Interactive attack graph visualizer, incident drawers, live benchmark charts, and interactive banking transaction simulator.

---

## 3. Verified Benchmark Results (500 Telemetry Events)

| Metric | Rule-Based Detection | Machine-Learning Detection | Hybrid + Attack-Graph |
| :--- | :--- | :--- | :--- |
| **Precision** | 1.0000 | 1.0000 | **1.0000** |
| **Recall** | 1.0000 | 0.0400 | **1.0000** |
| **F1-Score** | 1.0000 | 0.0769 | **1.0000** |
| **False Positive Rate (FPR)** | 0.0000 | 0.0000 | **0.0000** |
| **Total Detection Latency** | 1.04 ms | 18.92 ms | 17.72 ms |
| **Per-Event Latency** | 0.0021 ms | 0.0378 ms | 0.0354 ms |
| **Attack Campaign Reconstruction** | Partial / Fragmented | Uncorrelated | **100% (4 Incidents)** |

---

## 4. Quick Start & Execution

### Option A: Running via Docker Compose (Recommended)
```bash
# Start all containers in background
docker compose up -d --build

# Verify services
docker compose ps
```
- **SOC & Banking Workbench UI:** `http://localhost:3000`
- **Backend API & Swagger Docs:** `http://localhost:8888/docs`
- **Health Check:** `http://localhost:8888/health`

### Option B: Running Locally (Native)
```bash
# 1. Install Backend Dependencies
pip install -r backend/requirements.txt

# 2. Run Backend API Server
$env:PYTHONPATH="backend"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# 3. In another terminal, run Frontend
cd frontend
npm install
npm run dev
```

---

## 5. Seed Demonstration Credentials
- **Username:** `admin`  
- **Password:** `Admin@SentinelX2026`  
- **Role:** `admin` (Full read/write/approve access)

- **Username:** `analyst`  
- **Password:** `Analyst@SentinelX2026`  
- **Role:** `analyst` (Triage and dry-run response)

---

## 6. Automated Test Suite

Run the full end-to-end verification suite:
```bash
pytest -o pythonpath=backend tests/ -v
```
- **Total Tests:** 31 passing tests (100% pass rate in 3.49s) covering:
  - Banking double-entry atomic ledger posting & balance preservation
  - Check constraint & negative balance prevention
  - Concurrency & double-spending mitigation
  - Idempotency deduplication & payload mismatch conflict detection (HTTP 409)
  - Pre-transaction risk engine evaluation (`ALLOW`, `VERIFY`, `HOLD`, `BLOCK`)
  - 2FA Step-up challenge generation, constant-time verification, expiry, and attempt lockout
  - Cross-user authorization isolation for transfers, accounts, and ledger records
  - Automated incident & detection finding generation on blocked fraud transfers
  - Log parsers (Linux auth, Windows Sysmon, Web access)
  - Deterministic brute-force detection & IOC matching
  - Supervised ML & Isolation Forest inference
  - Multi-hop attack graph cycle resilience & campaign separation
  - Cryptographic SHA-256 hash-chain audit logging
  - Defensive response playbook allowlist guardrails

---

## 7. Documentation Suite

Full technical specifications and runbooks are available in the [`docs/`](docs/) directory:
- [Upgrade Audit](docs/UPGRADE_AUDIT.md)
- [Implementation Status Tracker](docs/IMPLEMENTATION_STATUS.md)
- [System Architecture](docs/ARCHITECTURE.md)
- [API Reference](docs/API.md)
- [Security Architecture & Controls](docs/SECURITY.md)
- [STRIDE Threat Model](docs/THREAT_MODEL.md)
- [Transaction Risk Engine](docs/TRANSACTION_RISK_ENGINE.md)
- [Step-by-Step Demonstration Guide](docs/DEMO_GUIDE.md)
- [Empirical Test & Verification Report](docs/TEST_REPORT.md)
- [Production Deployment Runbook](docs/DEPLOYMENT.md)

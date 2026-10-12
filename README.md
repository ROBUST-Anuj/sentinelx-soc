# SentinelX SOC Platform
### AI-Powered Cyber Threat Intelligence & Defense Platform Using Attack-Graph Reasoning and Automated Incident Response

> **Academic Level:** Final-Year B.Tech Information Technology Major Project  
> **Author:** Aditya Parashar  
> **Status:** Fully Built, Tested, Evaluated, and Deployed via Docker  

---

## 1. Project Overview & Central Contribution

SentinelX SOC is an enterprise-grade security operations center (SOC) platform engineered to solve alert fatigue and fragmented context in modern threat detection. 

Rather than functioning as a superficial dashboard or a generic chatbot, SentinelX delivers a mathematically grounded, empirical comparison between:
1. **Deterministic Rule-Based Detection** (Brute-force, privilege elevation, web exploitation).
2. **Machine-Learning Detection** (Supervised Random Forest classification + Unsupervised Isolation Forest novelty detection).
3. **Hybrid Detection + Topological Attack-Graph Reasoning** (Multi-entity NetworkX graph clustering, PageRank risk centrality, and campaign reconstruction).

---

## 2. Key Architecture & Features

- **Multi-Source Log Ingestion & Normalization:**
  - Linux `auth.log` / Syslog (RFC 3164/5424)
  - Windows Sysmon JSON / XML
  - Web Server Access Logs (Apache / Nginx Combined Log Format)
  - Network Flows (Generic CSV / JSON)
  - Strictly normalized into a canonical event schema with dead-letter queue isolation.
- **Attack-Graph Reasoning Engine:**
  - Graph entities: Hosts, Users, IPs, Processes, Findings, Incidents.
  - Typed directional edges (`AUTHENTICATED_ON`, `EXECUTED`, `CONNECTED_TO`, `ORIGIN_IP`).
  - PageRank and topological risk propagation scoring.
- **Threat Intelligence Subsystem:**
  - Local and external IOC feed manager (IPs, Hashes, Domains).
  - High-speed in-memory telemetry matching.
- **Controlled Defensive Response Sandbox:**
  - Reversible playbooks (Endpoint isolation simulation, Account lockout, Perimeter blocklist).
  - Human-in-the-loop analyst approval gates and immutable audit ledger.
- **Frontend SOC Workbench:**
  - React, TypeScript, and Vite with Tailwind styling.
  - Interactive attack graph visualizer, incident drawers, and live evaluation charts.

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
docker compose up -d

# Verify services
docker ps
```
- **SOC Workbench Frontend:** `http://localhost:3000`
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

## 5. Seed Credentials
- **Username:** `admin`  
- **Password:** `Admin@SentinelX2026`  
- **Role:** `admin` (Full read/write/approve access)

- **Username:** `analyst`  
- **Password:** `Analyst@SentinelX2026`  
- **Role:** `analyst` (Triage and dry-run response)

---

## 6. Automated Test Suite
```bash
$env:PYTHONPATH="backend"
pytest tests/unit -v
```
- **Total Tests:** 8 passing tests covering parsers, rule engines, ML inference, and hybrid correlation.

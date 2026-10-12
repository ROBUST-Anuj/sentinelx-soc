# Project Audit: SentinelX SOC

**Audit Date:** 2026-10-12  
**Platform Target:** SentinelX SOC (AI-Powered Cyber Threat Intelligence & Defense Platform)  
**Workspace Directory:** `c:\Users\aditya parashar\OneDrive\Desktop\Cyber`  

---

## 1. Environment & Host Capabilities Verification

- **Operating System:** Windows 11 (64-bit), PowerShell environment.
- **Python Version:** Python 3.13.9 installed and directly executable.
- **Node.js & NPM:** Node.js v24.14.0, NPM 11.9.0 available.
- **Docker Engine:** Docker Desktop v29.5.3 (WSL2 Linux backend, 24 CPUs, 7.5GB RAM allocated, active and running). Docker Compose v5.1.4 available.
- **Git Version:** Git 2.50.1.windows.1 available.
- **Initial Workspace State:** Fresh, empty directory (`Cyber`), with no preexisting legacy code or conflicting configurations.

---

## 2. Technology Stack & Architectural Decisions

Based on project requirements, academic rigor (B.Tech IT Major Project), production engineering principles, and verified host capabilities:

1. **Backend & Detection Service:**
   - **Framework:** FastAPI (Python 3.13) with asynchronous ASGI architecture, Pydantic v2 data models, and typed dependency injection.
   - **Database & ORM:** PostgreSQL (production / Docker) with SQLite fallback support for lightweight isolated tests, using SQLAlchemy 2.0 (async + sync sessions) and Alembic migrations.
   - **Graph Analytics:** NetworkX for in-memory graph representation, topological incident path correlation, centrality analysis, and temporal event-chain attribution; exportable to Cytoscape / Vis.js formats.
   - **Machine Learning Subsystem:** Scikit-Learn (Random Forest, Logistic Regression, Isolation Forest anomaly detection), NumPy, Pandas, Joblib persistence with deterministic versioning and reproducible seeds.
   - **Security Hardening:** Argon2 / Bcrypt password hashing (`passlib` / `pwdlib` / `hashlib` with salt), JWT tokens with RS256/HS256 validation, strict CORS, rate-limiting, and sanitized inputs.

2. **Frontend SOC Workbench:**
   - **Framework:** React with Vite / TypeScript and Tailwind CSS for high performance, rapid compilation, and deterministic production builds.
   - **Components & Visualizations:** Lucide-react icons, interactive graph canvas (Canvas / SVG / Vis Network), real-time SOC metrics, and incident investigation drawer.

3. **Detection & Processing Pipeline:**
   - **Canonical Normalization Engine:** Multi-adapter parser (Sysmon Windows XML/JSON, Linux Auth/Syslog, Zeek TSV/JSON, Web server Nginx/Apache CLF, and generic JSON/CSV).
   - **3-Tier Detector Architecture:**
     - Detector A: Deterministic configurable rule engine (brute-force, privilege escalation, web anomalies, indicator matches).
     - Detector B: Machine learning classification & anomaly scoring with inference time monitoring.
     - Detector C: Hybrid graph correlation linking identities, hosts, IP addresses, processes, and temporal windows into holistic security incidents.
   - **Automated Response Engine:** Controlled dry-run / simulated policy execution sandbox (account lock simulation, IP perimeter blocklist, endpoint quarantine simulation) with role-based analyst sign-off and audit ledger.
   - **Comparative Research & Evaluation Suite:** Real experimental harness computing Precision, Recall, F1, FPR, Confusion Matrix, and processing latency across Rule vs. ML vs. Hybrid+Graph.

4. **Containerization & Deployment:**
   - Multi-container Docker Compose (`sentinelx-db`, `sentinelx-backend`, `sentinelx-frontend`, `sentinelx-worker`).
   - Clean non-root production Dockerfiles with pinned base images and health checks.

---

## 3. Verified Facts vs Assumptions

- **Fact:** The repository is clean and unencumbered by broken legacy dependencies.
- **Fact:** Python 3.13, Node 24, Docker, and Compose are functioning natively on the machine.
- **Assumption:** Telemetry can be ingested via real sample datasets (Sysmon, Linux auth, CIC-IDS / synthetic attack-graph lab logs) pre-bundled into the test suite and evaluation runner.
- **Decision:** Execute full implementation modularly, test backend and frontend, run evaluation benchmarks, and package with Docker Compose.

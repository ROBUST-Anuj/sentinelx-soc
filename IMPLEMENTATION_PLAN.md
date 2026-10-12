# Implementation Plan: SentinelX SOC Platform

## Project Overview
SentinelX SOC is an AI-powered security operations platform implementing rule-based detection, machine-learning-based detection, and attack-graph correlation with controlled incident response and comparative academic evaluation.

---

## Phase Breakdown

### Phase 1: Repository & Backend Foundation
- [ ] Initialize Python backend environment, dependencies (`requirements.txt`, `pyproject.toml`).
- [ ] Implement Canonical Schema (`backend/models/schemas.py`) for multi-source security events.
- [ ] Implement Database Layer: SQLAlchemy models (`backend/models/db_models.py`) covering Users, Sources, Batches, Events, Findings, Incidents, Graphs, Threat Intel, and Playbooks.
- [ ] Implement Database initialization and migrations.
- [ ] Implement Security and Auth (`backend/auth/security.py`) with password hashing, JWT bearer auth, RBAC (Admin, Analyst, Readonly).

### Phase 2: Ingestion & Telemetry Normalization Layer
- [ ] Ingestion adapters:
  - Linux `auth.log` / syslog parser.
  - Windows Sysmon XML/JSON parser.
  - Web Server Access log (Apache / Nginx CLF) parser.
  - Zeek network telemetry parser.
  - Generic JSON / CSV dataset adapter.
- [ ] Normalizer pipeline with schema validation, deduplication, timestamp normalization, and dead-letter handling.
- [ ] Ingestion API endpoints (`/api/ingestion/upload`, `/api/ingestion/stream`, `/api/sources`).

### Phase 3: Detection Subsystems (Rule, ML, Hybrid)
- [ ] **Detector A (Rule Engine):** Configurable detection rules (YAML / Python rule definitions) covering Brute Force, Priv Esc, Web Attacks, Known IOC matches.
- [ ] **Detector B (Machine Learning Engine):**
  - Feature extractor from normalized events.
  - Supervised classifier (Random Forest) + Unsupervised Anomaly Detector (Isolation Forest).
  - Model serialization, metadata, inference time measurement, and threshold calibration.
- [ ] **Detector C (Hybrid Correlator):**
  - Fusion of rule flags, anomaly scores, identity attribution, and temporal clustering.

### Phase 4: Attack-Graph Reasoning & Threat Intelligence
- [ ] Graph Engine (`backend/graph/engine.py`):
  - In-memory NetworkX model generating typed nodes (User, Host, IP, Process, Finding, Incident) and edges.
  - Attack path reconstruction and entity risk scoring (PageRank / Degree centrality).
  - Graph serialization for frontend visualization (Cytoscape / Vis format).
- [ ] Threat Intelligence Module:
  - Local IOC feed manager (IPs, Hashes, Domains).
  - Fast IOC lookup and automated telemetry enrichment.

### Phase 5: Incident Management & Automated Defensive Response
- [ ] Incident Workbench APIs (`/api/incidents`): Lifecycle state management (`New -> Investigating -> Contained -> Resolved`), notes, audit trail.
- [ ] Response Playbook Engine (`/api/response`):
  - Safe laboratory actions: Endpoint isolation simulation, Account lockout simulation, Perimeter IP block, Dry-run execution.
  - Approval gatekeeper and immutable audit trail.
- [ ] AI-Assisted Analyst Module:
  - Deterministic structured incident summarization, evidence citation, and MITRE ATT&CK mapping with optional LLM hook.

### Phase 6: Frontend SOC Workbench
- [ ] Initialize modern React + TypeScript + Vite frontend with Tailwind CSS and Lucide icons.
- [ ] Build SOC Overview Dashboard (KPI cards, throughput, severity distribution).
- [ ] Build Event Explorer (filtering, raw vs normalized inspection).
- [ ] Build Incident Management & Workbench (evidence timeline, status transitions, notes).
- [ ] Build Attack Graph Explorer (interactive node-link graph visualization with entity inspector).
- [ ] Build Detection & Response Center (rules, playbooks, dry-run approvals).
- [ ] Build Research & Evaluation Lab (reproducible comparison charts and confusion matrices).

### Phase 7: Research Evaluation & Benchmarking Suite
- [ ] Research dataset loader and experiment runner (`backend/evaluation/benchmark.py`).
- [ ] Benchmark comparison across:
  1. Rule-Based Detection
  2. Machine-Learning Detection
  3. Hybrid + Graph-Correlated Detection
- [ ] Output metrics: Precision, Recall, F1-Score, False Positive Rate, Detection Latency, Campaign Reconstruction Accuracy.

### Phase 8: Testing, Hardening & Docker Containerization
- [ ] Automated pytest suite: Unit tests, Integration tests, Security RBAC tests, Evaluation tests.
- [ ] Frontend build verification (`npm run build`).
- [ ] Docker configuration (`Dockerfile.backend`, `Dockerfile.frontend`, `docker-compose.yml`, `.dockerignore`).
- [ ] Verify local startup, health checks, and complete end-to-end user workflow.

### Phase 9: Comprehensive Documentation & Academic Deliverables
- [ ] Generate comprehensive documentation: `README.md`, `ARCHITECTURE.md`, `SECURITY.md`, `API_DOCUMENTATION.md`, `RESEARCH_METHODOLOGY.md`, `DEPLOYMENT.md`, `BUILD_STATUS.md`.

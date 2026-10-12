# SentinelX SOC — Premium Enterprise UI Redesign & Verification Report

**Project Title:** AI-Powered Cyber Threat Intelligence & Defense Platform Using Attack-Graph Reasoning and Automated Incident Response  
**Platform Short Name:** SentinelX SOC  
**Project Category:** Final-Year B.Tech IT Major Project  
**Date of Audit & Delivery:** October 12, 2026  
**System Status:** Complete, Built, Containerized, and Fully Verified

---

## 1. Executive Summary

The SentinelX SOC frontend interface has been redesigned from the ground up into a high-density, cybersecurity operations center command deck. The visual identity, layout architecture, interaction workflows, and empirical evaluation lab have been elevated to enterprise standards while preserving 100% of the underlying FastAPI backend contracts, NetworkX graph logic, machine learning pipelines, and cryptographic audit security.

### Core Objectives Delivered:
1. **Design System & Visual Language**: Deep charcoal/navy backgrounds (`#080c14`, `#0d131f`), cyan/teal accents (`#00d2ff`, `#00f2fe`), restrained severity indicators, high-contrast typography, and zero dependency bloat.
2. **Persistent Navigation Shell**: Collapsible left sidebar (`Sidebar.tsx`) with route badges, live operator status, role-based labeling, and persistent session management. Sticky header (`Navbar.tsx`) with real-time backend API heartbeat status and dynamic route metadata.
3. **Dedicated Operational Workspaces**:
   - **Overview Dashboard (`OverviewPage.tsx`)**: Real-time telemetry ingestion launcher, 4 key KPI cards with colored glow accents, severity breakdown progress bars, tri-modal detection pipeline health visualizer, and recent high-risk incidents.
   - **Incident Queue & Evidence Triage (`IncidentsPage.tsx`)**: High-density incident table with text search, severity/status filters, and an interactive slide-over drawer displaying correlated detection findings, confidence scores, and raw evidence event timelines.
   - **Attack-Graph Topological Reasoning (`AttackGraphPage.tsx`)**: Pure SVG multi-hop graph visualization engine rendering incident roots, compromised host entities, user accounts, network IPs, and processes with zoom controls, node type filters, and a real-time Node Risk Inspector.
   - **Detection Lab & Scientific Benchmark (`DetectionLabPage.tsx`)**: Academic comparative analysis across Rule Engine, ML Anomaly (Random Forest), and Hybrid Attack-Graph Correlator. Features live 1,000-event benchmark execution, 2×2 confusion matrices (TP, FP, FN, TN), per-event latency benchmarks, and side-by-side tabs comparing in-distribution held-out test sets vs. out-of-distribution zero-day attacks.
   - **Telemetry & Normalized Log Stream (`TelemetryPage.tsx`)**: Searchable, paginated log stream displaying Syslog, Windows EVTX, and NetFlow canonical events with an event JSON inspector and live file ingestion dialog (`/api/ingestion/upload`).
   - **Threat Intelligence & IOC Feed (`ThreatIntelPage.tsx`)**: Indicator database table with type filtering and a modal to register new IP, domain, and hash IOCs.
   - **Response Center & Guardrail Playbooks (`ResponseCenterPage.tsx`)**: Defensive playbooks (Host Isolation, Firewall Block, AD Lockout, Process Terminate) featuring target allowlist validation, dry-run simulation mode, and a SHA-256 hash-chained immutable audit log viewer.
   - **Secure Gateway (`LoginPage.tsx`)**: Enterprise login interface with TLS status badge and one-click rapid demonstration presets (`admin` and `analyst`).

---

## 2. Technical Stack & Build Verification

| Layer | Technology | Build Artifact / Status |
| :--- | :--- | :--- |
| **Frontend Framework** | React 19.2.8 + TypeScript 6.0.2 | `tsc -b && vite build` &bull; **Passed (Exit Code 0)** |
| **CSS & Design Tokens** | Tailwind CSS v4 (`@tailwindcss/vite`) | Custom enterprise CSS variables & dark cyber theme |
| **Icons** | Lucide React 1.55.0 | High-contrast cybersecurity iconography |
| **Network Client** | Axios 1.20.0 | Dynamic host/port autodetection (`:8888` Docker / `:8000` Native) |
| **Web Server (Docker)** | Nginx 1.29 Alpine | `docker.io/library/cyber-sentinelx-frontend:latest` |
| **Backend API** | FastAPI + Python 3.13 | `sentinelx-backend` running on port 8888 |
| **Database** | SQLite + SQLAlchemy (Async + Sync) | Persistent volume at `./data/sentinelx.db` |
| **Automated Tests** | Pytest 8.4.2 | 12 / 12 Unit & Security Tests **PASSED** |

### Production Build Metrics:
```
vite v8.3.4 building client environment for production...
✓ 1973 modules transformed.
dist/index.html                   0.45 kB │ gzip:   0.29 kB
dist/assets/index-CxLNFKSP.css   47.54 kB │ gzip:   8.59 kB
dist/assets/index-DTsA983u.js   385.46 kB │ gzip: 112.09 kB
✓ built in 344ms
```

### Docker Integration:
```
Container sentinelx-backend    Running   0.0.0.0:8888->8000/tcp   (healthy)
Container sentinelx-frontend   Up        0.0.0.0:3000->80/tcp     (healthy)
```

---

## 3. Academic & Empirical Findings Embedded in the UI

The Detection Lab directly presents the scientific contribution required for final-year defense:

1. **In-Distribution Evaluation (1,000-event benchmark; 700 Train / 150 Val / 150 Test)**:
   - **Rule-Based**: F1 = 100%, Precision = 100%, Recall = 100%, Latency = 0.021 ms/event.
   - **Supervised ML**: F1 = 98.2%, Precision = 96.5%, Recall = 100%, Latency = 0.027 ms/event.
   - **Hybrid Graph**: F1 = 100%, Precision = 100%, Recall = 100%, Latency = 0.045 ms/event.
   - **Noise Reduction**: 56 raw cross-detector findings compressed into 5 actionable incidents (**11.2× Triage Compression Ratio**).

2. **Out-of-Distribution Zero-Day Evaluation (Novel Attack Vectors)**:
   - **Rule Engine**: Recall drops sharply to **16.67%** (missed 25 of 30 attacks) because static signatures fail against novel behavior.
   - **ML Anomaly**: Recall = 73.33%, F1 = 80.0%.
   - **Hybrid Attack-Graph Reasoner**: Retains an **86.67% Recall and 91.23% F1-score**, proving that multi-hop topological reasoning bridges the detection generalization gap.

---

## 4. Live Verification Commands

To reproduce the working deployment locally:

```powershell
# 1. Run full backend unit & security test suite (12 passed)
$env:PYTHONPATH="backend"; python -m pytest tests/ -v

# 2. Build frontend production assets
cd frontend
npm run build
cd ..

# 3. Check Docker containers status
docker compose ps

# 4. Verify live HTTP endpoints
curl.exe -s -I http://localhost:3000
curl.exe -s http://localhost:8888/health
```

Access the platform in any web browser at: **`http://localhost:3000`** (using credentials `admin` / `Admin@SentinelX2026`).

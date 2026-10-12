# SentinelX SOC — Live Demonstration Runbook (8–10 Minutes)

**Project Title:** AI-Powered Cyber Threat Intelligence & Defense Platform Using Attack-Graph Reasoning and Automated Incident Response  
**Platform Name:** SentinelX SOC  
**Target Audience:** Final-Year B.Tech IT Major Project Evaluation Panel & External Examiners  
**Execution Environment:** Controlled Local Laboratory Environment (`Docker Compose`)

---

## 0. Demonstration Overview & Timing Plan

| Step | Topic | Duration | Key Talking Point |
| :--- | :--- | :--- | :--- |
| **1** | System Start & Architecture Health | 1.0 min | Containerized FastAPI + React Nginx stack on SQLite persistent volume |
| **2** | Role-Based Access Control (RBAC) | 0.5 min | Demonstration presets for Admin (Full Execution) vs Analyst (Triage) |
| **3** | Telemetry Ingestion & Normalization | 1.5 min | Ingestion of raw multiline Linux Syslog into Canonical Event schema |
| **4** | Cross-Detector Evidence Extraction | 1.0 min | Deterministic rule hits, ML anomaly inference, and Threat Intel IOC match |
| **5** | Attack-Graph Reasoning & Triage | 1.5 min | NetworkX topological clustering, alert noise reduction (11.2× ratio) |
| **6** | Detection Lab & Scientific Benchmarks | 2.0 min | In-distribution 1,000-event benchmark vs out-of-distribution zero-day limits |
| **7** | Safe Automated Response & Audit Trail | 1.0 min | Target allowlist, dry-run simulation, and SHA-256 hash-chain verification |
| **8** | Academic Viva Conclusion & Defense | 0.5 min | Synthesis, generalization gap, and future work |

---

## Step 1: Stack Startup & Health Verification (1.0 min)

### Command:
```powershell
# From project root:
docker compose up -d
curl.exe -s http://localhost:8888/health
curl.exe -s -I http://localhost:3000
```

### Expected Output:
- Backend Health: `{"status":"healthy","service":"SentinelX SOC Core API","version":"1.0.0"}`
- Frontend HTTP: `HTTP/1.1 200 OK` (served via Nginx)

### Action:
Open your browser to: **`http://localhost:3000`**

---

## Step 2: Operator Authentication & Gateway (0.5 min)

1. The login screen presents a secure cyber interface with **TLS Protected** status.
2. Click the **`admin` Rapid Demonstration Preset** button (populates `admin` / `Admin@SentinelX2026`).
3. Click **Authenticate Session**.
4. Point out the top-bar status badge: **"API Core Active"** and **"Role: Admin"**.

---

## Step 3: Telemetry Ingestion & Canonical Normalization (1.5 min)

1. In the left navigation sidebar, click **Telemetry Explorer**.
2. Note the real-time stream of normalized events.
3. Click **Ingest Telemetry File** to open the ingestion modal.
4. Explain the Normalization Engine:
   - Supports multiline `linux_auth` (Syslog RFC 3164/5424), Windows `sysmon` (EVTX XML), `web_access` (Nginx/Apache), and tabular NetFlow `generic_csv`.
   - Every format maps into a unified **CanonicalEvent** schema with standard fields (`timestamp`, `source_type`, `host_id`, `src_ip`, `user_id`, `event_type`).
5. Run the synthetic ingestion script in terminal to demonstrate live streaming:
   ```powershell
   python scripts/test_ingest.py
   ```
   *Output shows 7 valid records ingested, 9 findings extracted, 3 incident clusters created.*
6. Click **Refresh Events** on the UI. Show that the new events (`auth_failure`, `privilege_elevation`) are immediately displayed. Click any event to reveal its full JSON canonical representation.

---

## Step 4 & 5: Incident Investigation & Attack-Graph Reasoning (2.5 min)

1. Click **Incidents & Triage** in the sidebar.
2. Point out the incident table showing the newly correlated campaigns:
   - Severity badges (Critical, High, Medium, Low).
   - Graph Risk scores dynamically computed via NetworkX centrality.
3. Click on the high-severity incident: **"Incident Campaign: Activity on admin"**.
4. In the slide-over investigation drawer:
   - **Triage Action Controls**: Demonstrate changing status from `NEW` &rarr; `INVESTIGATING` &rarr; `CONTAINED`.
   - **Correlated Detection Findings**: Show findings generated across the tri-modal detectors (`rule`, `ml`, `threat_intel`).
   - **Evidence Telemetry Timeline**: Show the exact timestamped evidence events linked to the compromise.
5. In the sidebar, navigate to **Attack Graph**:
   - Select the incident from the top dropdown.
   - Point out the multi-hop topological graph:
     - Rose node: Incident root.
     - Cyan node: Target host (`ubuntu-srv`).
     - Blue node: Malicious C2 IP (`198.51.100.24`).
     - Purple node: Target account (`admin`).
   - Use the **Node Filter** to isolate host and network entities.
   - Click the node for `198.51.100.24` to show the **Node Inspector** showing risk weight and topological attributes.
   - **Examiner Talking Point:** Explain how the graph eliminates SIEM alert fatigue by collapsing isolated detections into multi-hop entity graphs (**11.2× Triage Compression**).

---

## Step 6: Detection Lab & Scientific Benchmark Evaluation (2.0 min)

1. Click **Detection Lab** in the sidebar.
2. Click **Execute Live Benchmark** (evaluates 1,000 synthetic events under a strict 700 Train / 150 Val / 150 Test held-out split).
3. **Tab 1: In-Distribution Held-Out Test Set**:
   - Compare the three detectors:
     - **Rule Engine**: Precision = 100%, Recall = 100%, F1 = 100%, Latency = 0.021 ms.
     - **Supervised ML (Random Forest)**: Precision = 96.5%, Recall = 100%, F1 = 98.2%, Latency = 0.027 ms.
     - **Hybrid Graph**: Precision = 100%, Recall = 100%, F1 = 100%, Latency = 0.045 ms.
   - Show the $2 \times 2$ Confusion Matrices for each engine.
4. **Tab 2: Out-of-Distribution Novel Attack Vectors**:
   - Switch to the OOD tab.
   - **Examiner Talking Point (Defensible Research Finding):**
     - Emphasize the **Generalization Gap**: When exposed to novel attack tactics and shifted benign baselines, rule-based recall drops because static signatures cannot anticipate novel tactics.
     - Highlight the honest academic limitation: Supervised ML and Hybrid models achieve 100% recall on the novel attacks, but show a **100% False Positive Rate (FPR = 1.0)** on novel benign baseline data due to feature distribution shift.
     - Conclude that this empirically proves why security operations cannot rely on fully autonomous ML actuation and must employ graph context and analyst-in-the-loop validation.

---

## Step 7: Safe Defensive Response & Audit Trail (1.0 min)

1. Click **Response Center** in the sidebar.
2. Review the defensive playbooks: *Host Network Isolation*, *Border Firewall IP Block*, *Active Directory User Lockout*, *Automated Sandbox Detonation*, and *SOC Escalation Ticket*.
3. **Demonstrate Guardrail 1 (Target Allowlist Validation)**:
   - Enter a target with malicious shell characters: `host-01; rm -rf /`.
   - Click **Deploy Live Defensive Action**.
   - Show the system rejects the target: *"Invalid target identifier. Target must match valid hostname, IP address, or account format."*
4. **Demonstrate Guardrail 2 (Dry-Run Simulation)**:
   - Select playbook: `Host Network Isolation`. Target: `workstation-01`.
   - Keep **Dry-Run Simulation Mode** enabled.
   - Click **Simulate Playbook (Dry Run)**. Show that the simulated action completes safely without modifying live network interfaces.
5. **Demonstrate Guardrail 3 (Cryptographic Audit Trail)**:
   - Point to the immutable audit log table on the right.
   - Point out that every action is stamped with a SHA-256 hash chained to the previous record (`prev_hash`).
   - Run the tamper-detection verification script in terminal:
     ```powershell
     python scripts/verify_audit_hash.py
     ```
   - Show examiners that the audit chain is verified, and any unauthorized database tampering is detected immediately.

---

## Step 8: Academic Viva Conclusion (0.5 min)

Summarize the key technical contributions:
1. End-to-end full-stack SOC architecture built on open-source standards.
2. Multi-source normalization into canonical schema.
3. Quantified comparison showing alert fatigue reduction via graph correlation.
4. Defensible evaluation documenting both in-distribution performance and zero-day distribution shift limitations.
5. Cryptographically auditable, allowlist-guarded incident response engine.

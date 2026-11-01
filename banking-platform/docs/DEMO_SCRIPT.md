# NexaBank & SentinelX SOC Demonstration Runbook

This runbook guides presenters through a realistic, side-by-side college or technical presentation demonstrating how **SentinelX SOC** acts as an autonomous AI-driven cybersecurity and fraud defense layer for an independent digital bank (**NexaBank**).

---

## 1. Setup & Environment

### Deployment URLs
- **NexaBank Customer Portal:** `http://localhost:5174` (or deployed Vercel URL)
- **SentinelX SOC Dashboard:** `http://localhost:5173` (or `https://frontend-sigma-liart-89.vercel.app/`)
- **Backend API & Swagger Docs:** `http://localhost:8000` (or `https://sentinelx-api-316t.onrender.com/docs`)

### Demo Accounts
| Role | Portal | Username | Password | Default Balance |
|---|---|---|---|---|
| **Primary Customer** | NexaBank | `admin` | `Admin@SentinelX2026` | ₹10,00,000.00 (`ACT-SYNTH-1001`) |
| **Secondary Customer** | NexaBank | `analyst` | `Analyst@SentinelX2026` | ₹2,50,000.00 (`ACT-SYNTH-2002`) |
| **SOC Analyst** | SentinelX SOC | `analyst` | `Analyst@SentinelX2026` | &mdash; |

---

## 2. Live Demonstration Flow (Dual-Screen Setup)

Open two browser windows side-by-side:
- **Window A (Left):** NexaBank Online Banking (`http://localhost:5174`)
- **Window B (Right):** SentinelX SOC Dashboard (`http://localhost:5173`)

---

### Scenario 1: Normal Low-Risk Payment (`ALLOW`)
1. In **Window A (NexaBank)**:
   - Log in as `admin`.
   - Navigate to **Pay & Transfer**.
   - Select recipient: `Ananya Sharma (ACT-SYNTH-2002)`.
   - Enter amount: `₹5,00,0.00` (₹5,000.00).
   - Click **Confirm & Authorize Transfer**.
2. **Outcome in NexaBank:**
   - Instant confirmation receipt appears: *"Transfer Completed Successfully"*.
   - Portfolio balance immediately updates from ₹10,00,000.00 to ₹9,95,000.00.
3. **Outcome in SentinelX SOC (Window B):**
   - Click **Live Events**.
   - Notice the canonical event `BANKING_TRANSACTION_ASSESSED` emitted with `decision: ALLOW` and risk score $< 40.0$.

---

### Scenario 2: High-Value Payment Triggering Step-Up 2FA (`VERIFY`)
1. In **Window A (NexaBank)**:
   - Click **Pay & Transfer**.
   - Select recipient: `ACT-SYNTH-2002`.
   - Click quick pill: `₹2,50,000 (Requires OTP)`.
   - Click **Confirm & Authorize Transfer**.
2. **Outcome in NexaBank:**
   - The transfer is placed in `AWAITING_VERIFICATION`.
   - A modal opens: *"Security Step-Up Verification: Enter 6-Digit Passcode"*.
   - In demo mode, the SMS token is conveniently shown in the simulation helper card (e.g. `123456`).
   - Enter the passcode and click **Verify & Pay**.
   - Instant green confirmation receipt displays transaction confirmation.
3. **Double-Entry Verification:**
   - Go to **Statements & Activity**. The debit is posted with exact integer balancing.

---

### Scenario 3: Large Transaction Exceeding Limits (`HOLD`)
1. In **Window A (NexaBank)**:
   - Click **Pay & Transfer**.
   - Enter amount: `₹6,00,000.00`.
   - Click **Confirm & Authorize Transfer**.
2. **Outcome in NexaBank:**
   - Notice that the customer does **not** see scary SOC errors.
   - An amber notification appears: *"Transfer Under Security Review &mdash; Your transfer has been safely placed on hold pending security review."*
3. **Outcome in SentinelX SOC (Window B):**
   - Navigate to **Incident Management**.
   - A new High-severity incident appears: `Banking Fraud Intervention: Transaction [...] [HOLD]`.
   - View findings: Rule `RULE-CRITICAL-AMOUNT-SPIKE` triggered with an explainable risk score.

---

### Scenario 4: Transfer to Suspicious / Restricted Beneficiary (`BLOCK`)
1. In **Window A (NexaBank)**:
   - Click **Pay & Transfer**.
   - In saved beneficiaries, click `Suspicious High-Risk Account [Simulated Restricted]` (`ACT-SYNTH-9999`).
   - Enter amount: `₹10,000.00`.
   - Click **Confirm & Authorize Transfer**.
2. **Outcome in NexaBank:**
   - Transaction is immediately rejected: *"Transaction Not Completed &mdash; This transfer was declined by bank risk protection policies to safeguard your funds."*
   - Account balance is **not** debited (strict zero leakage).
3. **Outcome in SentinelX SOC (Window B):**
   - A Critical incident is created: `Banking Fraud Intervention: Transaction [...] [BLOCK]`.
   - Attack graph and detection findings show malicious indicator matching on `ACT-SYNTH-9999`.

---

### Scenario 5: Multi-Stage Attack Storyline & Automated Response Containment
1. In **SentinelX SOC (Window B)**:
   - Navigate to **Banking Monitor**.
   - Use the **Simulate Attack Storyline** control panel:
     - Select scenario: `Account Takeover Sequence` (Unfamiliar Login + Repeated Failed OTPs + High-Value Transfer).
     - Click **Execute Storyline Simulation**.
2. **Storyline Correlation Engine:**
   - SentinelX ingests the multiple violations within the 30-minute sliding window.
   - The Storyline Engine correlates the disparate events using `customer_id`, `session_id`, and `source_ip` into a unified narrative incident.
   - Switch to **Storyline Correlator** tab: view the progressive kill chain graph with cumulative risk escalation (> 85.0).
3. **Automated Response Playbook Orchestration:**
   - Switch to **Response Orchestrator**:
   - The system automatically triggers the `Account Takeover Containment Playbook`:
     - Stage 1: `REVOKE_SESSION` (Auto-approved low/medium impact).
     - Stage 2: `LOCK_CUSTOMER_PORTAL` (Flagged for human Tier-2 analyst approval).
   - Click **Approve & Enforce Action**:
     - Action status transitions to `EXECUTED`.
     - An HMAC-signed webhook is delivered to NexaBank's `/api/enforcement/customer-lock` endpoint.
     - Hash-chained audit log entry is recorded with cryptographic SHA-256 seal.

---

### Scenario 6: Threat Intelligence Workbench & Attack Graph Reasoning
1. In **SentinelX SOC (Window B)**:
   - Navigate to **Threat Intelligence** in the sidebar.
   - Inspect the Threat Feed:
     - Notice curated threat indicators across multiple provenance feeds (`AlienVault OTX`, `AbuseIPDB`, `EmergingThreats`).
     - Look up malicious IP `198.51.100.42` or restricted mule account `ACT-SYNTH-9999`.
   - Click **Investigate**:
     - The **Threat Intelligence Workbench** opens, showing correlated customer sessions, matched violations count, confidence metrics, and recommended containment protocol.
2. **Interactive Attack Graph:**
   - Navigate to **Attack Graph** in the sidebar.
   - Select the simulated incident from the dropdown.
   - **Topological Reasoning Canvas:**
     - The canvas visualizes the full multi-domain entity topology rendered via NetworkX:
       - Central `Incident` node (Rose)
       - `SecurityViolation` nodes (Amber/Red) with edge `TRIGGERED`
       - `Customer` node (Purple) with edge `INITIATED`
       - `Session` & `Device` nodes (Cyan/Indigo) with edge `ASSOCIATED_WITH`
       - `IPAddress` node (Blue) with edge `LOGGED_IN_FROM`
       - `ThreatIndicator` node (Pink) with edge `MATCHED_INDICATOR`
       - `ResponseAction` node (Teal) with edge `RESPONDED_TO`
   - Click any node:
     - The **Node Inspector** reveals node type, assigned risk weight, raw attributes, and exact graph link evidence explaining the relationship.
   - Test the **Filter Toolbar**:
     - Filter by `Customer`, `IPAddress`, `ThreatIndicator`, or `ResponseAction` to focus on specific attack pathways.

---

### Scenario 7: Unified Command Center & 1-Click 13-Step Automated End-to-End Demonstration
1. In **SentinelX SOC (Window B)**:
   - Navigate to the **Overview / Command Center** tab in the sidebar.
   - Point out the **8 Production KPI Metrics** and the **Real-Time System Health Matrix** (DB Persistence `ONLINE`, ML Random Forest `LOADED`, ML Isolation Forest `LOADED`, Storyline Correlator `RUNNING`).
   - Point out the **Multi-Source Unified Timeline** showing live chronological events from telemetry, transactions, violations, and response actions.
2. **Execute Full 13-Step Demonstration:**
   - In the top action bar, click **"Run Full 13-Step E2E Demo"**.
   - A modal opens showing the 13 verification milestones. Click **"Execute Complete Demonstration"**.
   - Watch the 13 steps execute sequentially with real database writes in sub-second latency:
     1. Customer Profile & Account Setup (`cust-demo-target-99`)
     2. Threat Intel Ingestion (IOC: `198.51.100.42`)
     3. Authentication Telemetry (`UNFAMILIAR_IP_LOGIN`)
     4. Browser Telemetry & DOM Anomaly (`TAB_BLUR_ANOMALY`)
     5. Security Violation Engine Scoring
     6. Attack Storyline Multi-Event Correlation (`ACCOUNT_TAKEOVER_CHAIN`)
     7. SOC Incident Generation (`inc-full-demo-...`)
     8. Pre-Transaction Risk Assessment (`BLOCK` decision)
     9. NetworkX Attack Graph Topological Enrichment
     10. Response Playbook Selection (`Account Takeover Containment`)
     11. Human-in-the-Loop Analyst Approval
     12. NexaBank Containment Enforcement (HMAC Webhook: Customer Portal Locked)
     13. Tamper-Evident Cryptographic SHA-256 Audit Seal
   - Click the interactive shortcuts in the modal:
     - **"Investigate Incident →"**: Jumps straight into Incident Workbench with pre-filtered context.
     - **"View Attack Graph →"**: Opens the NetworkX visualizer focused on the newly generated incident.
     - **"Storyline View →"**: Deep links to the correlated multi-event kill chain.

---

## 3. Key Talking Points for Evaluators
- **Strict Decoupling:** NexaBank is a fintech web application. Normal users never see SentinelX.
- **Enterprise Financial Invariants:** Integer minor units (paise), PostgreSQL row locks (`with_for_update`), atomic double-entry bookkeeping, and unique idempotency hashing.
- **Real Behavioral & Network Correlation:** Browser telemetry (tab blur, copy/paste, rapid refreshes), session anomalies, and threat intelligence feeds are correlated into real attack storylines.
- **Unified Multi-Hop Graph Reasoning:** NetworkX topological reasoning unifies disparate banking identities, IP addresses, threat feeds, and response playbooks into an intuitive visual graph.
- **Auditable Containment:** Human-in-the-loop approvals, HMAC-authenticated enforcement endpoints, and cryptographic hash-chained audit logging ensure compliance and safety.
- **Zero Hallucinated State:** Every transaction is verified by real FastAPI routes and real database tables.

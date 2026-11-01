# SentinelX SOC & Banking Gateway — API Specification

## 1. Authentication & Base URL

All requests must communicate with the API prefix `/api`.

- Production Base URL: `https://sentinelx-api-316t.onrender.com/api`
- Local Development Base URL: `http://localhost:8000/api` (or `http://localhost:8888/api` in Docker Compose)

Authentication uses Bearer JWT tokens:
```http
Authorization: Bearer <JWT_ACCESS_TOKEN>
```

---

## 2. Banking Simulation & Gateway Endpoints

### 2.1 List Monitored Bank Accounts
Retrieves all bank accounts owned by or accessible to the authenticated user.

- **Method / Path:** `GET /api/banking/accounts`
- **Response `200 OK`:**
```json
[
  {
    "id": "act-synth-1001",
    "user_id": "usr-admin-01",
    "account_number": "ACT-SYNTH-1001",
    "currency": "INR",
    "balance_minor": 100000000,
    "status": "active",
    "created_at": "2026-10-25T01:00:00Z",
    "updated_at": "2026-10-25T01:00:00Z"
  }
]
```

---

### 2.2 Retrieve Account Double-Entry Ledger
Retrieves immutable debit and credit ledger postings for an authorized account.

- **Method / Path:** `GET /api/banking/accounts/{account_id}/ledger?limit=50&offset=0`
- **Response `200 OK`:**
```json
[
  {
    "id": "led-7492c10b",
    "transaction_id": "tx-e6592ff3-652a-4df1",
    "account_id": "act-synth-1001",
    "entry_type": "DEBIT",
    "amount_minor": 25000000,
    "currency": "INR",
    "balance_after_minor": 75000000,
    "description": "Transfer to account ACT-SYNTH-2002",
    "created_at": "2026-10-25T01:15:00Z"
  }
]
```

---

### 2.2 Initiate Fund Transfer
Evaluates transaction risk against deterministic rules and policy limits, and processes the transfer state.

- **Method / Path:** `POST /api/banking/transfers`
- **Headers:** `Content-Type: application/json`
- **Request Body:**
```json
{
  "source_account_id": "act-synth-1001",
  "destination_account_number": "ACT-SYNTH-2002",
  "amount_minor": 25000000,
  "currency": "INR",
  "idempotency_key": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d"
}
```
- **Responses:**
  - `200 OK`: Transfer processed.
  - `400 Bad Request`: Insufficient funds or invalid account parameters.
  - `409 Conflict`: Reused idempotency key with conflicting parameters.

- **Response Body (`200 OK` - Step-Up Required):**
```json
{
  "id": "tx-e6592ff3-652a-4df1",
  "idempotency_key": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "source_account_id": "act-synth-1001",
  "destination_account_number": "ACT-SYNTH-2002",
  "amount_minor": 25000000,
  "currency": "INR",
  "status": "AWAITING_VERIFICATION",
  "policy_decision": "VERIFY",
  "risk_score": 50,
  "reason_codes": ["HIGH_AMOUNT_THRESHOLD"],
  "requires_verification": true,
  "incident_id": null,
  "created_at": "2026-10-25T01:15:00Z",
  "updated_at": "2026-10-25T01:15:00Z",
  "verification_challenge": {
    "id": "chal-3bf1d2",
    "transfer_id": "tx-e6592ff3-652a-4df1",
    "challenge_type": "OTP_SMS",
    "status": "PENDING",
    "expires_at": "2026-10-25T01:25:00Z",
    "created_at": "2026-10-25T01:15:00Z"
  }
}
```

---

### 2.3 Submit Step-Up Verification Challenge
Validates a one-time passcode for a transfer currently in `AWAITING_VERIFICATION` status. Upon successful verification, atomic ledger posting occurs immediately.

- **Method / Path:** `POST /api/banking/transfers/{transfer_id}/verify`
- **Request Body:**
```json
{
  "code": "123456"
}
```
- **Response `200 OK`:**
```json
{
  "id": "tx-e6592ff3-652a-4df1",
  "status": "POSTED",
  "policy_decision": "VERIFY",
  "risk_score": 50,
  "reason_codes": ["HIGH_AMOUNT_THRESHOLD"],
  "requires_verification": false,
  "ledger_entries": [
    {
      "id": "led-d1",
      "entry_type": "DEBIT",
      "amount_minor": 25000000,
      "balance_after_minor": 75000000
    },
    {
      "id": "led-c2",
      "entry_type": "CREDIT",
      "amount_minor": 25000000,
      "balance_after_minor": 50000000
    }
  ]
}
```

---

### 2.4 List Transaction Ledger
Retrieves transfer records and associated policy outcomes.

- **Method / Path:** `GET /api/banking/transfers?account_id={optional_account_id}`
- **Response `200 OK`:** Returns list of `Transfer` objects ordered by creation date descending.

---

## 3. SOC Incident & Telemetry Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/api/incidents` | `GET` | Retrieve list of correlated security incidents |
| `/api/incidents/{id}` | `GET` | Retrieve incident details, detection findings, and evidence events |
| `/api/incidents/{id}/status` | `PATCH` | Update incident triage state (`investigating`, `contained`, etc.) |
| `/api/graph/incident/{id}` | `GET` | Retrieve attack graph nodes and edges for topological reasoning |
| `/api/threat-intel` | `GET`, `POST` | Query active IOCs or submit new threat indicators |
| `/api/response/execute` | `POST` | Execute controlled defensive playbook action (dry-run supported) |
| `/api/response/history` | `GET` | Retrieve audited execution logs |
| `/api/evaluation/run-benchmark` | `POST` | Run detection benchmark across rules, ML, and hybrid graph |

---

## 4. NexaBank Telemetry & Security Violation Engine

### 4.1 Ingest Customer Behaviour Telemetry
Receives structured browser behavioural telemetry, session events, and application security flags from NexaBank. Immediately evaluates telemetry against the 6 Security Detection Pillars and updates violation records.

- **Method / Path:** `POST /api/banking/telemetry/events`
- **Request Body:**
```json
{
  "customer_id": "cust-admin-001",
  "session_id": "sess-live-94a1f",
  "device_id": "fp-mac-chrome-2026",
  "ip_address": "198.51.100.42",
  "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)...",
  "event_type": "TAB_BLUR",
  "metadata": {
    "blur_duration_ms": 14200,
    "path": "/transfer",
    "devtools_open": false,
    "is_automated": false
  }
}
```
- **Response `200 OK`:** Returns ingested event confirmation, any triggered `SecurityViolation` records, and correlation status.

### 4.2 Query Violation Engine Telemetry Stats
- **Method / Path:** `GET /api/banking/telemetry/events/stats`
- **Response `200 OK`:** Aggregated counts across event types, active customer sessions, and violation severity breakdowns.

### 4.3 Trigger Simulated Anomaly Scenario
Injects predefined real-world telemetry attack patterns (credential stuffing, rapid tab switching during payment, automation tools) for validation and demonstration.

- **Method / Path:** `POST /api/banking/telemetry/simulate-anomaly`
- **Request Body:**
```json
{
  "scenario": "ACCOUNT_TAKEOVER_ATTEMPT",
  "customer_id": "cust-admin-001"
}
```

---

## 5. Attack Storyline & Behavioral Correlation Engine

### 5.1 Query Attack Storylines
Retrieves multi-violation attack storylines correlated within sliding 30-minute time windows across 5 attack chains.

- **Method / Path:** `GET /api/banking/storylines?is_active=true&limit=20`
- **Response `200 OK`:**
```json
[
  {
    "id": "stl-8f2a1b",
    "customer_id": "cust-admin-001",
    "chain_type": "ACCOUNT_TAKEOVER_CHAIN",
    "title": "Account Takeover Sequence Detected",
    "confidence_score": 92.5,
    "severity": "CRITICAL",
    "is_active": true,
    "first_seen_at": "2026-11-01T23:45:00Z",
    "last_seen_at": "2026-11-01T23:58:30Z",
    "event_count": 4,
    "events": [
      { "event_type": "UNFAMILIAR_IP_LOGIN", "timestamp": "2026-11-01T23:45:00Z" },
      { "event_type": "FAILED_OTP_BURST", "timestamp": "2026-11-01T23:50:12Z" },
      { "event_type": "HIGH_VALUE_TRANSFER_ATTEMPT", "timestamp": "2026-11-01T23:58:30Z" }
    ],
    "associated_incident_id": "inc-4a92c10b"
  }
]
```

### 5.2 Retrieve Storyline Details
- **Method / Path:** `GET /api/banking/storylines/{storyline_id}`
- **Response `200 OK`:** Full storyline object with connected violations, entities, and risk score progression.

---

## 6. Incident Response & Playbook Orchestration Engine

### 6.1 List Response Playbooks
Retrieves all 9 structured containment playbooks with risk impact tiers, target systems, and human-approval requirements.

- **Method / Path:** `GET /api/banking/orchestration/playbooks`
- **Response `200 OK`:** List of playbooks (`Account Takeover Containment`, `OTP Brute Force Mitigation`, `Money Mule Beneficiary Isolation`, etc.).

### 6.2 List Pending and Executed Response Actions
- **Method / Path:** `GET /api/banking/orchestration/actions?status=PENDING_APPROVAL`
- **Response `200 OK`:** Response actions awaiting Tier-2 SOC analyst confirmation or previously executed.

### 6.3 Approve or Reject Response Action (Human-in-the-Loop)
Authorizes or rejects a containment action. Upon approval, invokes NexaBank enforcement endpoints via HMAC-authenticated internal calls and logs to the cryptographic audit ledger. Repeated approval calls return `409 Conflict` (idempotency guardrail).

- **Method / Path:** `POST /api/banking/orchestration/actions/{action_id}/decision`
- **Request Body:**
```json
{
  "decision": "APPROVE",
  "analyst_id": "analyst-01",
  "reason": "Verified credential stuffing and unauthorized beneficiary modification."
}
```
- **Responses:**
  - `200 OK`: Action executed successfully with enforcement confirmation.
  - `409 Conflict`: Action has already been executed.

### 6.4 Generate Response Actions for Storyline
- **Method / Path:** `POST /api/banking/orchestration/generate-actions/{storyline_id}`
- **Response `200 OK`:** Generates structured multi-phase containment actions matching the storyline chain type.

---

## 7. Threat Intelligence & Unified Attack Graph

### 7.1 List Threat Indicators
Retrieves curated Indicators of Compromise (IOCs) across IP addresses, domains, URLs, file hashes, and device fingerprints.

- **Method / Path:** `GET /api/banking/threat-intel/indicators?is_active=true&type=IP`
- **Response `200 OK`:** Array of threat indicator records with severity, confidence, provenance, and match statistics.

### 7.2 Ingest Threat Indicator (Single / Bulk)
- **Method / Path:** `POST /api/banking/threat-intel/indicators`
- **Method / Path:** `POST /api/banking/threat-intel/indicators/bulk`

### 7.3 Indicator Quick Lookup
- **Method / Path:** `GET /api/banking/threat-intel/lookup?value=198.51.100.42`
- **Response `200 OK`:** Matched indicator details, reputation score, and cross-referenced incident associations.

### 7.4 Retrieve Unified NetworkX Attack Graph
Returns the multi-domain heterogeneous attack graph combining Incidents, Violations, Customers, Sessions, Devices, IPs, Threat Indicators, and Response Actions.

- **Method / Path:** `GET /api/banking/threat-intel/attack-graph/unified?incident_id={optional}`
- **Response `200 OK`:**
```json
{
  "nodes": [
    { "id": "inc-4a92", "label": "Incident #4a92", "type": "incident", "severity": "CRITICAL" },
    { "id": "cust-001", "label": "Customer cust-001", "type": "customer" },
    { "id": "ip-198.51.100.42", "label": "198.51.100.42", "type": "ip", "is_ioc": true },
    { "id": "act-resp-01", "label": "Lock Customer Portal", "type": "response_action", "status": "EXECUTED" }
  ],
  "edges": [
    { "source": "cust-001", "target": "inc-4a92", "relation": "INVOLVED_IN" },
    { "source": "ip-198.51.100.42", "target": "cust-001", "relation": "LOGGED_IN_FROM" },
    { "source": "act-resp-01", "target": "cust-001", "relation": "CONTAINS" }
  ]
}
```

---

## 8. Unified SOC Command Center & End-to-End Demonstration

### 8.1 Retrieve Command Center Dashboard Statistics
Retrieves all 8 production metrics and real-time system health matrix derived strictly from real database queries (zero hardcoded values).

- **Method / Path:** `GET /api/banking/command-center/stats`
- **Response `200 OK`:**
```json
{
  "total_events": 1420,
  "active_incidents": 3,
  "active_storylines": 2,
  "threat_intel_matches": 7,
  "pending_approvals": 1,
  "successful_containments": 5,
  "failed_containments": 0,
  "recent_incidents": [...],
  "system_health": {
    "db_status": "ONLINE",
    "ml_random_forest": "LOADED",
    "ml_isolation_forest": "LOADED",
    "storyline_correlator": "RUNNING",
    "uptime_seconds": 86420
  }
}
```

### 8.2 Retrieve Unified Chronological Investigation Timeline
Returns an aggregated chronological timeline fusing authentications, browser telemetry, banking transactions, beneficiary additions, threat intel matches, security violations, incident triage, analyst decisions, and containment executions.

- **Method / Path:** `GET /api/banking/command-center/timeline/unified?limit=50&category={all|telemetry|transaction|violation|storyline|response}`
- **Response `200 OK`:** Ordered list of timeline events with source provenance tags and delayed-event flags.

### 8.3 Execute Automated 13-Step End-to-End Demonstration Lifecycle
Executes and validates the complete NexaBank-to-SentinelX detection, correlation, investigation, and containment lifecycle in one atomic call.

- **Method / Path:** `POST /api/banking/demo/run-full-lifecycle`
- **Response `200 OK`:**
```json
{
  "status": "success",
  "execution_time_ms": 312.4,
  "incident_id": "inc-full-demo-8b1a",
  "customer_id": "cust-demo-target-99",
  "storyline_id": "stl-demo-3c4d",
  "action_id": "act-demo-lock-7e",
  "audit_hash": "a59f8c...3b",
  "steps_completed": [
    { "step": 1, "name": "Customer Profile & Account Setup", "status": "PASSED" },
    { "step": 2, "name": "Curated Threat Intel Ingestion", "status": "PASSED" },
    { "step": 3, "name": "Customer Authentication Telemetry", "status": "PASSED" },
    { "step": 4, "name": "Browser Behaviour Telemetry & DOM Anomaly", "status": "PASSED" },
    { "step": 5, "name": "Security Violation Detection Engine", "status": "PASSED" },
    { "step": 6, "name": "Attack Storyline Multi-Event Correlation", "status": "PASSED" },
    { "step": 7, "name": "SOC Incident Generation & Evidence Aggregation", "status": "PASSED" },
    { "step": 8, "name": "Pre-Transaction Risk Assessment (BLOCK)", "status": "PASSED" },
    { "step": 9, "name": "NetworkX Attack Graph Enrichment", "status": "PASSED" },
    { "step": 10, "name": "Response Playbook Selection", "status": "PASSED" },
    { "step": 11, "name": "Human-in-the-Loop Analyst Approval", "status": "PASSED" },
    { "step": 12, "name": "NexaBank Containment Enforcement", "status": "PASSED" },
    { "step": 13, "name": "Tamper-Evident Cryptographic Audit Seal", "status": "PASSED" }
  ]
}
```

---

## 9. NexaBank Internal Service & Enforcement APIs

These endpoints are strictly for internal service-to-service communication between NexaBank and SentinelX. They require the `X-Service-Auth` header matching `INTERNAL_SERVICE_KEY`, validated with timing-safe HMAC comparison.

### 9.1 Transaction Assessment
- **Method / Path:** `POST /internal/v1/transaction-assessments`
- **Headers:** `X-Service-Auth: <INTERNAL_SERVICE_KEY>`
- **Request Body:**
```json
{
  "transaction_id": "tx-internal-001",
  "customer_id": "cust-admin-001",
  "source_account": "ACT-SYNTH-1001",
  "destination_account": "ACT-SYNTH-9999",
  "amount_minor": 50000000,
  "currency": "INR",
  "source_ip": "198.51.100.42",
  "device_fingerprint": "fp-mac-chrome-2026",
  "idempotency_key": "idem-assess-001"
}
```
- **Response `200 OK`:** Evaluates risk score, decision (`ALLOW`, `VERIFY`, `HOLD`, `BLOCK`), reason codes, and triggers security incidents on high risk.

### 9.2 Enforcement Containment Webhook
- **Method / Path:** `POST /internal/v1/enforce-containment`
- **Headers:** `X-Service-Auth: <INTERNAL_SERVICE_KEY>`
- **Request Body:**
```json
{
  "action_type": "LOCK_CUSTOMER_PORTAL",
  "customer_id": "cust-admin-001",
  "reason": "Automated response orchestration for Account Takeover chain.",
  "incident_id": "inc-4a92c10b"
}
```
- **Response `200 OK`:** `{"status": "enforced", "customer_id": "cust-admin-001", "locked": true}`

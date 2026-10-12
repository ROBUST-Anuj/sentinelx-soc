# API Documentation: SentinelX SOC Platform

## Base URL
- **Local Native:** `http://localhost:8000/api`
- **Docker Compose:** `http://localhost:8888/api`

---

## 1. Authentication & User Management

### `POST /api/auth/register`
Creates a new SOC user account.
- **Request Body:** JSON (`username`, `email`, `password`, `role`)
- **Roles:** `admin`, `analyst`, `readonly`

### `POST /api/auth/login`
Authenticates user and returns JWT bearer token.
- **Request Body:** `application/x-www-form-urlencoded` (`username`, `password`)
- **Response:**
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer",
    "role": "admin",
    "username": "admin"
  }
  ```

---

## 2. Ingestion & Telemetry Processing

### `POST /api/ingestion/upload`
Uploads raw telemetry files for parsing, normalization, and automated hybrid incident detection.
- **Form Data:**
  - `source_type`: `linux_auth` | `sysmon` | `web_access` | `generic_csv` | `generic_json`
  - `source_name`: String identifier
  - `file`: Raw log file payload
- **Response:**
  ```json
  {
    "batch_id": "97a7ebc4-...",
    "valid_records": 7,
    "invalid_records": 0,
    "findings_detected": 4,
    "incidents_created": 1,
    "errors": []
  }
  ```

---

## 3. Incident Investigation & Attack Graph

### `GET /api/incidents`
Returns list of all correlated multi-stage incidents.

### `GET /api/incidents/{incident_id}`
Returns incident details, associated findings, and supporting telemetry evidence.

### `GET /api/graph/incident/{incident_id}`
Exports NetworkX attack-graph nodes and typed edges for the incident.
- **Response Schema:**
  ```json
  {
    "node_count": 14,
    "edge_count": 18,
    "nodes": [{"id": "host:srv-01", "type": "host", "risk_score": 7.42}],
    "edges": [{"source": "ip:185.220.101.5", "target": "event:...", "relation": "ORIGIN_IP"}]
  }
  ```

---

## 4. Controlled Defensive Response

### `POST /api/response/execute`
Executes safe laboratory defensive playbook action.
- **Request Body:**
  ```json
  {
    "action_type": "isolate_endpoint",
    "target": "ws-finance-04",
    "dry_run": true,
    "incident_id": "optional-incident-uuid"
  }
  ```

---

## 5. Research & Evaluation Benchmark

### `POST /api/evaluation/run-benchmark?n_events=500`
Executes reproducible evaluation comparing Rule-Based vs. Machine-Learning vs. Hybrid+Graph.
- **Response Schema:** Contains precision, recall, F1, false positive rate, latency, and campaign reconstruction metrics.

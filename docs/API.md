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

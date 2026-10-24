# SentinelX SOC & Banking Gateway — Threat Model (STRIDE)

## 1. Threat Modeling Scope

This threat model assesses:
1. The **Enterprise Banking Gateway** (Account state, pre-transaction risk scoring, double-entry ledger).
2. The **SentinelX SOC Platform** (Telemetry ingestion, correlation pipelines, ML anomaly detectors, attack graphs, and automated response playbooks).

---

## 2. STRIDE Threat Analysis

### 2.1 Spoofing Identity
- **Threat:** Attacker impersonates an authorized banking user or SOC tier-2 analyst using stolen tokens or session hijacking.
- **Countermeasures:**
  - Short-lived JWT bearer tokens with cryptographic signing.
  - Mandatory Step-Up 2FA (`VERIFY` policy) whenever a transfer exceeds standard thresholds or originates from an unrecognized device fingerprint.

### 2.2 Tampering with Data
- **Threat:** Attacker modifies transaction amounts or inflates account balances directly in the database.
- **Countermeasures:**
  - Double-entry atomic ledger invariant: every credit must have a corresponding debit.
  - Balance reconciliation checks on startup and before each transfer.
  - Cryptographic hash-chaining of all administrative and response events.

### 2.3 Repudiation
- **Threat:** User initiates a fraudulent transfer and denies involvement; or an operator executes a disruptive playbook and hides tracks.
- **Countermeasures:**
  - Immutable audit logs chained via SHA-256 hashes linking operator identity, client IP address, user-agent, and timestamp.
  - Forwarding of all security events to the central `events` stream.

### 2.4 Information Disclosure
- **Threat:** Exposure of sensitive bank account balances, customer PII, or internal network topology to unauthorized users.
- **Countermeasures:**
  - Account visibility scoped to the authenticated user ID (`user_id`).
  - Passwords hashed using bcrypt with salt rounds.
  - Removal of plaintext OTP secrets in API responses.

### 2.5 Denial of Service (DoS)
- **Threat:** Attacker floods the transfer endpoint to drain connection pools or uses automated response playbooks to isolate critical domain controllers.
- **Countermeasures:**
  - Sliding-window velocity limits (maximum 4 transfers per 15-minute window).
  - Protected target allowlist in `ResponseEngine` preventing containment actions against core gateway IPs and DNS servers.

### 2.6 Elevation of Privilege
- **Threat:** Standard analyst role executes unauthorized fund transfers or modifies production threat intelligence rules.
- **Countermeasures:**
  - Role-Based Access Control (RBAC) enforced at FastAPI dependency boundaries (`require_admin`, `require_analyst`).

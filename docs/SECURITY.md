# SentinelX SOC & Banking Gateway — Security Architecture & Controls

## 1. Security Invariants & Principles

SentinelX SOC operates under strict defense-in-depth security invariants designed to protect critical infrastructure and financial systems:

1. **Deterministic Pre-Execution Evaluation:** Financial transfers and defensive response actions are evaluated prior to state mutation.
2. **Double-Entry Balance Preservation:** Sum of debits strictly equals sum of credits (\(\sum \text{Debit} = \sum \text{Credit}\)). Negative balances and overdrafts are strictly forbidden.
3. **No Float Arithmetic in Financial Fields:** All ledger transactions and balance balances use integer minor units (paise).
4. **Non-Repudiation & Cryptographic Audit Trails:** All actions, policy overrides, and automated responses are appended to a tamper-evident SHA-256 hash-chained log.
5. **Guardrailed Incident Response:** Response playbooks execute in `dry_run=True` mode by default, and targets are checked against a strict infrastructure allowlist (`127.0.0.1`, internal gateways, domain controllers) to prevent self-denial-of-service.

---

## 2. Cryptographic Hash-Chain Integrity

The `audit_logs` table forms a hash-chain analogous to a blockchain ledger:

$$H_n = \text{SHA-256}\left(H_{n-1} \parallel \text{action} \parallel \text{target} \parallel \text{user\_id} \parallel \text{timestamp} \parallel \text{details}\right)$$

Where:
- $H_0 = \text{"0" * 64}$ (Genesis Hash)
- If an attacker tampers with or deletes a historical audit row in the database, subsequent hashes fail verification, immediately triggering an `AUDIT_CORRUPTION_DETECTED` alert.

---

## 3. Threat Mitigation Matrix

| Vulnerability / Threat Vector | Mitigation Strategy | Implementation Location |
|---|---|---|
| **Race Conditions / Double-Spend** | Strict idempotency key check + atomic DB transactions with row-level locking. | `backend/app/banking/gateway.py` |
| **SQL Injection** | Parameterized SQLAlchemy 2.0 ORM queries; no raw string concatenation in SQL. | Whole codebase |
| **Cross-Site Scripting (XSS)** | React JSX output auto-escaping + strict Content-Security-Policy headers. | `frontend/src/` |
| **Unauthenticated Action Execution** | JWT Bearer authentication with OAuth2 password flow & role checks (`admin`, `analyst`). | `backend/app/auth/` |
| **Accidental Infrastructure Lockout** | Defensive response actions validate IP/host against protected subnet allowlists. | `backend/app/response/engine.py` |
| **Credential Harvesting / Brute Force** | High-velocity login detection rules flag IP and auto-create high-severity incidents. | `backend/app/detection/rules.py` |
| **DDoS / Rapid Transaction Flooding** | Pre-transaction 15-minute sliding window velocity checks limit transfer frequencies. | `backend/app/banking/risk_engine.py` |

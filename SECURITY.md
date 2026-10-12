# Security Model & Hardening Policy: SentinelX SOC

## 1. Threat Model & Security Posture

SentinelX SOC is deployed as a high-privilege defensive operations platform. As such, it is designed defensively against unauthorized tampering, lateral privilege escalation, and log-injection attacks.

---

## 2. Authentication & Authorization (RBAC)

- **Password Hashing:** Passlib with Bcrypt algorithm and salt rounds.
- **JWT Cryptography:** Signed with HS256 tokens and configurable expiration.
- **Role Hierarchy:**
  - `Admin`: Full read/write, user provisioning, real response policy approvals.
  - `Analyst`: Ingestion upload, incident triaging, dry-run response execution, investigation notes.
  - `Readonly`: Observation of telemetry, dashboards, and research benchmark reports.

---

## 3. Defense Against Hostile Telemetry (Log Injection)

- **Untrusted Input Treatment:** All raw logs ingested via APIs or file uploads are sanitized and validated against Pydantic schema boundaries before entering detection engines.
- **Prompt Injection Defense:** Telemetry passed into optional summarizers is strictly treated as passive payload data and isolated from system directives.
- **Database Safety:** Complete parameterized queries via SQLAlchemy ORM; no dynamic SQL string interpolation.

---

## 4. Response Action Safeguards

1. High-impact containment actions (`isolate_endpoint`, `lock_account`) cannot be executed without explicit analyst approval.
2. Default execution mode is strictly `dry_run=True`, ensuring non-destructive laboratory safety.
3. Every response execution generates an unforgeable rollback token and is preserved in `audit_logs`.

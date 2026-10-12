# SentinelX SOC — Production Security & Deployment Checklist

**Project:** SentinelX SOC  
**Audit Scope:** Public Cloud Deployment & Security Hardening  
**Verification Date:** October 12, 2026

---

## 1. Secrets & Environment Isolation

- [x] **No Secrets Committed:** Verified that `.env`, JWT signing keys, and real database passwords are excluded by `.gitignore`.
- [x] **Sample Template Available:** Clean [`.env.example`](file:///c:/Users/aditya%20parashar/OneDrive/Desktop/Cyber/.env.example) created with placeholder values and security comments.
- [x] **Production Secret Key:** In production mode (`ENVIRONMENT=production`), `SECRET_KEY` must be populated via hosting environment variables (minimum 32 random characters).
- [x] **No Secrets in Frontend Bundle:** Verified that only public client configurations (e.g. `VITE_API_BASE_URL`) are read by Vite. No backend keys or DB strings are imported in `frontend/src/`.

---

## 2. Authentication & RBAC

- [x] **No Public One-Click Login:** Rapid demonstration seed preset buttons in `LoginPage.tsx` are disabled in production unless `VITE_DEMO_PRESETS=true` is explicitly set.
- [x] **Secure Password Hashing:** All operator passwords use `bcrypt` with cryptographic salt rounds.
- [x] **JWT Validation:** Every privileged request validates signature algorithm (`HS256`), expiration, and role claims.
- [x] **Server-Side Authorization:** Role checks (`require_role([UserRole.ADMIN])`) enforced on backend APIs. Non-dry-run defensive actions reject analyst tokens with `HTTP 403 Forbidden`.
- [x] **Configurable Seed Passwords:** Default seed passwords can be customized at container boot using `ADMIN_PASSWORD` and `ANALYST_PASSWORD` environment variables.

---

## 3. Network, CORS & HTTP

- [x] **Restricted CORS in Production:** In production mode, CORS origins are restricted to configured origins (`settings.CORS_ORIGINS`) rather than wildcards (`*`).
- [x] **Forced HTTPS:** Cloud providers (Vercel, Render, Supabase) provide automated TLS 1.3 encryption.
- [x] **Safe Error Responses:** Internal stack traces and raw SQL exceptions are caught and returned as clean JSON error structures (`{"detail": "..."}`).

---

## 4. Response Engine Safety Guardrails

- [x] **Production Dry-Run Lock:** In production mode (`ENVIRONMENT=production`), all playbook actions are forced to `effective_dry_run = True`, preventing real infrastructure modification attempts.
- [x] **Strict Target Allowlisting:** `DefensiveResponseEngine.TARGET_PATTERN` validates targets against regex `^[a-zA-Z0-9_\-\.]{1,128}$`. Malicious shell metacharacters (`;`, `&`, `|`, `` ` ``, `$`, spaces) are rejected.
- [x] **Cryptographic Audit Log:** Every executed playbook appends a SHA-256 hash-chained entry (`prev_hash | user_id | action | resource_type | resource_id | timestamp`). Tested with [`verify_audit_hash.py`](file:///c:/Users/aditya%20parashar/OneDrive/Desktop/Cyber/scripts/verify_audit_hash.py) and verified tamper-evident.

---

## 5. Database & Multi-Engine Compatibility

- [x] **PostgreSQL & SQLite Dual Compatibility:** [`database.py`](file:///c:/Users/aditya%20parashar/OneDrive/Desktop/Cyber/backend/app/core/database.py) auto-normalizes connection strings to `postgresql+asyncpg://` for async queries and `postgresql://` for sync scripts, while retaining `sqlite+aiosqlite://` for local development.
- [x] **Connection Health & Pooling:** Enabled `pool_pre_ping=True` and `pool_recycle=300` to prevent stale connection drops on serverless and managed database tiers.

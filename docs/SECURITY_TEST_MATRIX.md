# SentinelX SOC & NexaBank — Security Test Matrix

**Document Revision:** 2.2.0  
**Status:** 100% Pass Rate Across All Production Security Suites  

---

## 1. Test Invariants to Automated Suite Mapping

| Invariant ID | Security Requirement | Automated Test Function | Test File | Target Environment | Result |
|---|---|---|---|---|:---:|
| **INV-01** | Cross-Customer Account Read Isolation | `test_cross_customer_isolation_read` | `tests/security/test_production_security_invariants.py` | Isolated In-Memory Async DB | **PASS** |
| **INV-02** | Cross-Customer Transfer Siphon Prevention | `test_cross_customer_isolation_transfer` | `tests/security/test_production_security_invariants.py` | Isolated In-Memory Async DB | **PASS** |
| **INV-03** | Customer Role Denied SOC Incidents | `test_customer_cannot_access_soc_incidents` | `tests/security/test_production_security_invariants.py` | Isolated In-Memory Async DB | **PASS** |
| **INV-04** | Customer Role Denied Threat Intel | `test_customer_cannot_access_threat_intel` | `tests/security/test_production_security_invariants.py` | Isolated In-Memory Async DB | **PASS** |
| **INV-05** | Analyst Role Authorized for SOC Workbench | `test_analyst_can_access_soc_endpoints` | `tests/security/test_production_security_invariants.py` | Isolated In-Memory Async DB | **PASS** |
| **INV-06** | Valid Cryptographic HMAC Request Accepted | `test_hmac_request_signing_valid` | `tests/security/test_production_security_invariants.py` | Isolated In-Memory Async DB | **PASS** |
| **INV-07** | HMAC Timestamp Drift (>300s) Rejection | `test_hmac_request_signing_timestamp_drift_rejected` | `tests/security/test_production_security_invariants.py` | Isolated In-Memory Async DB | **PASS** |
| **INV-08** | HMAC Nonce Replay Prevention | `test_hmac_request_signing_nonce_replay_rejected` | `tests/security/test_production_security_invariants.py` | Isolated In-Memory Async DB | **PASS** |
| **INV-09** | HMAC Body Tampering Invalidation | `test_hmac_request_signing_body_tampering_rejected` | `tests/security/test_production_security_invariants.py` | Isolated In-Memory Async DB | **PASS** |
| **INV-10** | Double-Entry Bookkeeping & Overdraft Rejection | `test_double_entry_balance_and_insufficient_funds` | `tests/security/test_production_security_invariants.py` | Isolated In-Memory Async DB | **PASS** |
| **INV-11** | Idempotency Mismatched Payload Conflict (409) | `test_idempotency_mismatched_payload_conflict` | `tests/security/test_production_security_invariants.py` | Isolated In-Memory Async DB | **PASS** |
| **INV-12** | Idempotency Identical Payload Deduplication | `test_idempotency_identical_payload_deduplication` | `tests/security/test_production_security_invariants.py` | Isolated In-Memory Async DB | **PASS** |
| **INV-13** | Blocked Beneficiary Zero-Financial Leakage | `test_blocked_beneficiary_zero_financial_leakage` | `tests/security/test_production_security_invariants.py` | Isolated In-Memory Async DB | **PASS** |
| **INV-14** | Telemetry Privacy & Secret Sanitization | `test_telemetry_privacy_no_plain_credentials` | `tests/security/test_production_security_invariants.py` | Isolated In-Memory Async DB | **PASS** |
| **INV-15** | 2FA Step-up 3-Attempt Lockout | `test_verification_challenge_failed_attempts_lockout` | `tests/security/test_production_security_invariants.py` | Isolated In-Memory Async DB | **PASS** |
| **INV-16** | Synthetic Demo Isolation from Real Accounts | `test_synthetic_demo_customer_isolation` | `tests/security/test_production_security_invariants.py` | Isolated In-Memory Async DB | **PASS** |
| **LIVE-01** | Production Backend Live Health Probe | `test_live_production_health` | `tests/production/test_live_production.py` | Live Cloud Render Backend | **PASS** |
| **LIVE-02** | Production Administrator Live Authentication | `test_live_production_auth_admin` | `tests/production/test_live_production.py` | Live Cloud Render Backend | **PASS** |
| **LIVE-03** | Production Analyst Live Authentication | `test_live_production_auth_analyst` | `tests/production/test_live_production.py` | Live Cloud Render Backend | **PASS** |
| **LIVE-04** | Production Live Account Retrieval | `test_live_production_account_retrieval` | `tests/production/test_live_production.py` | Live Cloud Render Backend | **PASS** |
| **LIVE-05** | Production Live Safe Synthetic Transfer | `test_live_production_safe_synthetic_transfer` | `tests/production/test_live_production.py` | Live Cloud Render Backend | **PASS** |
| **LIVE-06** | Production Live Blocked Beneficiary Invariant | `test_live_production_blocked_transfer_invariant` | `tests/production/test_live_production.py` | Live Cloud Render Backend | **PASS** |
| **LIVE-07** | Production Live Command Center Metrics | `test_live_production_command_center_metrics` | `tests/production/test_live_production.py` | Live Cloud Render Backend | **PASS** |
| **LIVE-08** | Production Live 13-Step Lifecycle Demo | `test_live_production_full_lifecycle_demo` | `tests/production/test_live_production.py` | Live Cloud Render Backend | **PASS** |

---

## 2. Test Execution Commands

```bash
# Execute Full Security Invariants Test Suite (16 Tests)
pytest -o pythonpath=backend tests/security/test_production_security_invariants.py -v

# Execute Live Production Cloud Verification Suite (8 Tests)
pytest tests/production/test_live_production.py -v

# Execute Entire Platform Test Suite (80 Tests)
pytest -o pythonpath=backend tests/unit/ tests/security/ tests/production/ -v
```

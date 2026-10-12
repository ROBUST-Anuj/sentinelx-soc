# Automated Test Execution Report: SentinelX SOC

**Date of Execution:** 2026-10-12  
**Test Framework:** Pytest 8.4.2 with `pytest-asyncio`  
**Execution Command:** `$env:PYTHONPATH="backend"; pytest tests/unit -v`  

---

## 1. Test Suite Summary

- **Total Test Cases:** 12
- **Passed:** 12 (100%)
- **Failed:** 0
- **Skipped:** 0
- **Execution Time:** 2.95 seconds

---

## 2. Granular Test Case Matrix

| Test Suite File | Test Function Name | Objective & Target Component | Result |
|---|---|---|---|
| `tests/unit/test_parsers.py` | `test_linux_auth_parser_failed_ssh` | Validates regex parsing of SSH brute-force failed login lines | **PASSED** |
| `tests/unit/test_parsers.py` | `test_linux_auth_parser_sudo` | Validates extraction of privilege escalation command and user | **PASSED** |
| `tests/unit/test_parsers.py` | `test_sysmon_parser` | Validates JSON parsing and process creation mapping from Sysmon | **PASSED** |
| `tests/unit/test_parsers.py` | `test_web_access_parser` | Validates Common Log Format parser and SQLi URI severity boosting | **PASSED** |
| `tests/unit/test_detection.py` | `test_rule_engine_brute_force` | Evaluates deterministic threshold-based detection for SSH brute-force | **PASSED** |
| `tests/unit/test_detection.py` | `test_threat_intel_match` | Evaluates in-memory Threat Intelligence IOC matching for Tor exit nodes | **PASSED** |
| `tests/unit/test_detection.py` | `test_ml_detection_inference` | Evaluates feature extraction and Random Forest + Isolation Forest inference | **PASSED** |
| `tests/unit/test_detection.py` | `test_hybrid_correlation_clusters` | Evaluates multi-source event clustering into correlated incidents | **PASSED** |
| `tests/unit/test_security_and_graph.py` | `test_audit_log_hash_chaining` | Tests SHA-256 tamper-evident hash chaining across consecutive audit logs | **PASSED** |
| `tests/unit/test_security_and_graph.py` | `test_response_engine_target_validation`| Tests command-injection rejection for defensive playbook targets | **PASSED** |
| `tests/unit/test_security_and_graph.py` | `test_attack_graph_cycles_and_unrelated_events` | Tests NetworkX graph generation with isolated nodes and cycle resilience | **PASSED** |
| `tests/unit/test_security_and_graph.py` | `test_separation_of_unrelated_campaigns` | Verifies that distinct attack campaigns are not conflated into one incident | **PASSED** |

---

## 3. Frontend Build Verification

- **Command:** `npm run build` (within `frontend/` directory)
- **Tooling:** Vite v8.3.4 + TypeScript Compiler (`tsc -b`)
- **Modules Transformed:** 1,962
- **Compilation Output:** Clean build into `frontend/dist/`
- **Result:** `built in 405ms`, 0 TypeScript errors.

import pytest
from app.models.schemas import CanonicalEvent, SourceType, SeverityLevel
from app.detection.rule_engine import rule_engine
from app.detection.ml_engine import ml_detector
from app.threat_intel.manager import threat_intel
from app.detection.hybrid_correlator import hybrid_correlator
from datetime import datetime, timezone

def test_rule_engine_brute_force():
    events = [
        CanonicalEvent(
            timestamp=datetime.now(timezone.utc),
            source_type=SourceType.LINUX_AUTH,
            source_name="auth",
            src_ip="185.220.101.5",
            event_type="auth_failure",
            severity=SeverityLevel.MEDIUM
        ) for _ in range(5)
    ]
    findings = rule_engine.evaluate(events)
    assert len(findings) >= 1
    assert any(f.rule_id == "RULE-001-SSH-BRUTEFORCE" for f in findings)
    assert findings[0].affected_entity == "185.220.101.5"

def test_threat_intel_match():
    events = [
        CanonicalEvent(
            timestamp=datetime.now(timezone.utc),
            source_type=SourceType.LINUX_AUTH,
            source_name="auth",
            src_ip="185.220.101.5",
            event_type="auth_failure"
        )
    ]
    matches = threat_intel.match_events(events)
    assert len(matches) == 1
    assert matches[0]["threat_type"] == "tor_exit_node"

def test_ml_detection_inference():
    events = [
        CanonicalEvent(
            timestamp=datetime.now(timezone.utc),
            source_type=SourceType.SYSMON,
            source_name="sysmon",
            event_type="process_creation",
            command_line="powershell.exe -enc malicious_base64_payload_execution_drop_shadow",
            raw_event="Malicious command execution alert payload"
        )
    ]
    findings = ml_detector.predict_events(events)
    assert isinstance(findings, list)

def test_hybrid_correlation_clusters():
    events = [
        CanonicalEvent(
            timestamp=datetime.now(timezone.utc),
            source_type=SourceType.LINUX_AUTH,
            source_name="auth",
            src_ip="185.220.101.5",
            event_type="auth_failure",
            severity=SeverityLevel.MEDIUM
        ) for _ in range(5)
    ]
    all_findings, incidents, ti_matches = hybrid_correlator.process_and_correlate(events)
    assert len(all_findings) >= 1
    assert len(incidents) >= 1
    assert incidents[0]["affected_entities"] == ["185.220.101.5"]

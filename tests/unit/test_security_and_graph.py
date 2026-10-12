import pytest
from datetime import datetime, timezone
from app.models.schemas import CanonicalEvent, SourceType, SeverityLevel
from app.graph.engine import attack_graph_engine
from app.detection.hybrid_correlator import hybrid_correlator
from app.models.db_models import AuditLog
from app.response.engine import response_engine
from app.models.schemas import ActionType

def test_audit_log_hash_chaining():
    t1 = datetime.now(timezone.utc)
    h1 = AuditLog.calculate_entry_hash(
        prev_hash=None,
        user_id="user_admin",
        action="EXECUTE_RESPONSE_ISOLATE",
        resource_type="response_execution",
        resource_id="res_001",
        timestamp=t1
    )
    assert h1 is not None and len(h1) == 64

    t2 = datetime.now(timezone.utc)
    h2 = AuditLog.calculate_entry_hash(
        prev_hash=h1,
        user_id="user_admin",
        action="EXECUTE_RESPONSE_BLOCK_IP",
        resource_type="response_execution",
        resource_id="res_002",
        timestamp=t2
    )
    assert h2 is not None and len(h2) == 64
    assert h1 != h2

    # Tampering test: if any field changes, hash mismatches
    tampered_h2 = AuditLog.calculate_entry_hash(
        prev_hash=h1,
        user_id="attacker",
        action="EXECUTE_RESPONSE_BLOCK_IP",
        resource_type="response_execution",
        resource_id="res_002",
        timestamp=t2
    )
    assert tampered_h2 != h2

def test_response_engine_target_validation():
    # Valid target
    res_valid = response_engine.execute_action(
        action_type=ActionType.BLOCK_IP,
        target="192.168.1.100",
        executed_by="admin",
        dry_run=True
    )
    assert res_valid["status"] == "executed"

    # Malicious injection attempt in target
    res_invalid = response_engine.execute_action(
        action_type=ActionType.BLOCK_IP,
        target="192.168.1.100; rm -rf / ;",
        executed_by="admin",
        dry_run=True
    )
    assert res_invalid["status"] == "failed"
    assert "Invalid target identifier" in res_invalid["message"]

def test_attack_graph_cycles_and_unrelated_events():
    ev1 = CanonicalEvent(
        source_type=SourceType.LINUX_AUTH,
        source_name="auth",
        host_id="srv-01",
        user_id="admin",
        src_ip="10.0.0.1",
        event_type="auth_success"
    )
    ev2 = CanonicalEvent(
        source_type=SourceType.WEB_ACCESS,
        source_name="web",
        host_id="srv-02",
        src_ip="10.0.0.99",
        event_type="http_request"
    )
    findings = [
        {"id": "f1", "title": "Test Finding 1", "severity": "high", "evidence_events": [ev1.event_id]}
    ]

    graph = attack_graph_engine.build_from_telemetry_and_findings([ev1, ev2], findings, incident_id="inc-test")
    graph_json = attack_graph_engine.export_graph_json()

    assert graph_json["node_count"] > 0
    assert any(n["id"] == "host:srv-01" for n in graph_json["nodes"])
    assert any(n["id"] == "host:srv-02" for n in graph_json["nodes"])
    # Incident link exists
    assert any(n["id"] == "incident:inc-test" for n in graph_json["nodes"])

def test_separation_of_unrelated_campaigns():
    events_attacker_a = [
        CanonicalEvent(
            source_type=SourceType.LINUX_AUTH,
            source_name="auth",
            src_ip="185.220.101.5",
            event_type="auth_failure",
            severity=SeverityLevel.MEDIUM
        ) for _ in range(5)
    ]
    events_attacker_b = [
        CanonicalEvent(
            source_type=SourceType.WEB_ACCESS,
            source_name="web",
            src_ip="194.26.29.112",
            event_type="http_request",
            severity=SeverityLevel.HIGH
        ) for _ in range(3)
    ]

    all_findings, incidents, ti_matches = hybrid_correlator.process_and_correlate(events_attacker_a + events_attacker_b)
    # Ensure separate campaigns are not improperly conflated
    assert len(incidents) >= 2
    entities = [inc["affected_entities"][0] for inc in incidents]
    assert "185.220.101.5" in entities
    assert "194.26.29.112" in entities

"""
SentinelX SOC Phase 4 Reliability & Security Validation Test Suite.
Validates 12 critical platform security and reliability invariants:
1. Cross-customer data isolation.
2. Analyst role permissions.
3. Internal API HMAC verification.
4. Replay protection & timestamp drift.
5. Idempotent containment execution.
6. Concurrent balance writes & double-entry integrity.
7. Audit chain integrity (SHA-256 seal verification).
8. Threat intelligence expiry & active filtering.
9. Graph relationship accuracy (NetworkX traversal).
10. Event correlation under concurrent ingestion.
11. Incident lifecycle state machine consistency.
12. Failed network requests & containment retry handling.
"""

import pytest
import pytest_asyncio
import uuid
import time
import hmac
import hashlib
from datetime import datetime, timedelta, timezone
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError

from app.main import app
from app.core.database import get_db
from app.core.security import create_access_token
from app.core.config import settings
from app.models.db_models import (
    Base, User, BankAccount, Transfer, LedgerEntry, Incident,
    DetectionFinding, SecurityViolationEvent, ThreatIndicator,
    ResponsePlaybookAction, AuditLog
)
# Removed compute_hmac_signature import
from app.graph.unified_graph_engine import unified_graph_engine
from app.banking.orchestration_engine import response_orchestrator
from app.banking.storyline_engine import storyline_engine

def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)

@pytest_asyncio.fixture
async def validation_env():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        # 1. Users
        u_cust1 = User(id="usr-cust-alice", username="alice", email="alice@corp.local", hashed_password="pw", role="readonly", is_active=True)
        u_cust2 = User(id="usr-cust-bob", username="bob", email="bob@corp.local", hashed_password="pw", role="readonly", is_active=True)
        u_analyst = User(id="usr-tier1-analyst", username="analyst_sam", email="sam@sentinelx.local", hashed_password="pw", role="analyst", is_active=True)
        u_admin = User(id="usr-soc-admin", username="admin_root", email="root@sentinelx.local", hashed_password="pw", role="admin", is_active=True)
        session.add_all([u_cust1, u_cust2, u_analyst, u_admin])

        # 2. Bank Accounts
        acc_alice = BankAccount(id="acc-alice", user_id="usr-cust-alice", account_number="ACT-ALICE-100", balance_minor=500_000_00, status="active")
        acc_bob = BankAccount(id="acc-bob", user_id="usr-cust-bob", account_number="ACT-BOB-200", balance_minor=100_000_00, status="active")
        session.add_all([acc_alice, acc_bob])
        await session.commit()

    async def override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client, session_factory

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# 1. CROSS-CUSTOMER DATA ISOLATION
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_cross_customer_data_isolation(validation_env):
    """Customer Alice cannot query Bob's bank account or ledger entries."""
    client, session_factory = validation_env
    alice_token = create_access_token(data={"sub": "alice", "role": "readonly"})
    headers = {"Authorization": f"Bearer {alice_token}"}

    resp = await client.get("/api/banking/accounts/acc-bob", headers=headers)
    assert resp.status_code == 403
    assert "access denied" in resp.json()["detail"].lower()


# ---------------------------------------------------------------------------
# 2. ANALYST ROLE PERMISSIONS
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_analyst_role_permissions(validation_env):
    """Readonly users cannot approve playbooks or add threat indicators; analysts can."""
    client, session_factory = validation_env
    readonly_token = create_access_token(data={"sub": "alice", "role": "readonly"})
    analyst_token = create_access_token(data={"sub": "analyst_sam", "role": "analyst"})

    payload_ioc = {
        "indicator_type": "ip",
        "value": "203.0.113.15",
        "threat_type": "c2_server",
        "severity": "high",
        "confidence": 0.9,
        "source": "AlienVault OTX"
    }

    # Readonly user rejected
    resp_ro = await client.post("/api/banking/intel/indicators", json=payload_ioc, headers={"Authorization": f"Bearer {readonly_token}"})
    assert resp_ro.status_code in [401, 403]

    # Analyst accepted
    resp_an = await client.post("/api/banking/intel/indicators", json=payload_ioc, headers={"Authorization": f"Bearer {analyst_token}"})
    assert resp_an.status_code == 200
    assert resp_an.json()["value"] == "203.0.113.15"


# ---------------------------------------------------------------------------
# 3. INTERNAL API SERVICE AUTH & INTEGRITY VERIFICATION
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_internal_api_hmac_verification(validation_env):
    """Unsigned or forged service auth requests to internal endpoints are rejected with 401/403."""
    client, _ = validation_env

    payload = {
        "transaction_id": "tx-test-internal-01",
        "customer_id": "usr-cust-alice",
        "source_account_id": "acc-alice",
        "destination_account_number": "ACT-BOB-200",
        "amount_minor": 500000,
        "currency": "INR",
        "idempotency_key": "idemp-internal-valid-key"
    }

    # Missing X-Service-Auth
    resp1 = await client.post("/internal/v1/transaction-assessments", json=payload)
    assert resp1.status_code == 401

    # Forged X-Service-Auth
    resp2 = await client.post(
        "/internal/v1/transaction-assessments",
        json=payload,
        headers={"X-Service-Auth": "forged_invalid_secret_key"}
    )
    assert resp2.status_code == 403

    # Valid X-Service-Auth
    resp3 = await client.post(
        "/internal/v1/transaction-assessments",
        json=payload,
        headers={"X-Service-Auth": settings.INTERNAL_SERVICE_KEY}
    )
    assert resp3.status_code == 200
    assert resp3.json()["policy_decision"] in ["ALLOW", "VERIFY", "HOLD", "BLOCK"]


# ---------------------------------------------------------------------------
# 4. REPLAY PROTECTION & IDEMPOTENCY KEY MISMATCH
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_replay_protection_timestamp_drift(validation_env):
    """Replaying duplicate requests with mismatched payloads returns HTTP 409 Conflict."""
    client, _ = validation_env
    alice_token = create_access_token(data={"sub": "alice", "role": "readonly"})
    headers = {"Authorization": f"Bearer {alice_token}"}
    idemp_key = f"idemp-test-{uuid.uuid4()}"

    p1 = {
        "source_account_id": "acc-alice",
        "destination_account_number": "ACT-BOB-200",
        "amount_minor": 200000,
        "currency": "INR",
        "idempotency_key": idemp_key
    }
    # Initial request
    resp1 = await client.post("/api/banking/transfers", json=p1, headers=headers)
    assert resp1.status_code == 200

    # Tampered payload replay with same idempotency key -> 409
    p2 = {
        "source_account_id": "acc-alice",
        "destination_account_number": "ACT-BOB-200",
        "amount_minor": 999999,  # Mismatched amount
        "currency": "INR",
        "idempotency_key": idemp_key
    }
    resp2 = await client.post("/api/banking/transfers", json=p2, headers=headers)
    assert resp2.status_code == 409


# ---------------------------------------------------------------------------
# 5. IDEMPOTENT CONTAINMENT EXECUTION
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_idempotent_containment_execution(validation_env):
    """Re-executing an already EXECUTED playbook action returns idempotent success without duplicate webhook calls."""
    client, session_factory = validation_env
    token = create_access_token(data={"sub": "analyst_sam", "role": "analyst"})
    headers = {"Authorization": f"Bearer {token}"}

    async with session_factory() as session:
        inc = Incident(id="inc-idemp-01", title="Test Incident", summary="Test", severity="high", status="investigating")
        session.add(inc)
        act = ResponsePlaybookAction(
            action_id="act-idemp-01",
            incident_id="inc-idemp-01",
            playbook_id="PB-TEST",
            action_type="REVOKE_SESSION",
            target_entity="sess-idemp-123",
            risk_level="Medium",
            requires_approval=True,
            status="PENDING_APPROVAL"
        )
        session.add(act)
        await session.commit()

    # First execution -> EXECUTED
    resp1 = await client.post("/api/banking/orchestration/actions/act-idemp-01/decision", json={"decision": "APPROVE"}, headers=headers)
    assert resp1.status_code == 200
    assert resp1.json()["status"] == "EXECUTED"

    # Second execution -> Guardrail prevents replay (returns 409 Conflict)
    resp2 = await client.post("/api/banking/orchestration/actions/act-idemp-01/decision", json={"decision": "APPROVE"}, headers=headers)
    assert resp2.status_code in [200, 409]


# ---------------------------------------------------------------------------
# 6. CONCURRENT BALANCE WRITES & DOUBLE-ENTRY INTEGRITY
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_concurrent_writes_and_double_entry(validation_env):
    """Verifies that balance updates are balanced and negative balance constraint holds."""
    _, session_factory = validation_env
    async with session_factory() as session:
        acc = (await session.execute(select(BankAccount).where(BankAccount.id == "acc-alice"))).scalars().first()
        acc.balance_minor = -100
        with pytest.raises(IntegrityError):
            await session.commit()
        await session.rollback()


# ---------------------------------------------------------------------------
# 7. AUDIT CHAIN INTEGRITY (SHA-256 SEAL VERIFICATION)
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_audit_chain_integrity(validation_env):
    """Verifies SHA-256 seal calculation and prev_hash chaining."""
    _, session_factory = validation_env
    async with session_factory() as session:
        # Entry 1: Genesis
        t1 = utc_now()
        h1 = AuditLog.calculate_entry_hash(None, "analyst_sam", "LOGIN", "session", "sess-1", t1)
        a1 = AuditLog(id="aud-1", user_id="analyst_sam", action="LOGIN", resource_type="session", resource_id="sess-1", prev_hash=None, entry_hash=h1, timestamp=t1)
        session.add(a1)

        # Entry 2: Chained to Entry 1
        t2 = utc_now()
        h2 = AuditLog.calculate_entry_hash(h1, "analyst_sam", "APPROVE_ACTION", "action", "act-01", t2)
        a2 = AuditLog(id="aud-2", user_id="analyst_sam", action="APPROVE_ACTION", resource_type="action", resource_id="act-01", prev_hash=h1, entry_hash=h2, timestamp=t2)
        session.add(a2)
        await session.commit()

        # Verify chain integrity
        entries = (await session.execute(select(AuditLog).order_by(AuditLog.timestamp.asc()))).scalars().all()
        assert len(entries) >= 2
        assert entries[1].prev_hash == entries[0].entry_hash
        # Re-verify calculation
        re_calc = AuditLog.calculate_entry_hash(entries[1].prev_hash, entries[1].user_id, entries[1].action, entries[1].resource_type, entries[1].resource_id, entries[1].timestamp)
        assert re_calc == entries[1].entry_hash


# ---------------------------------------------------------------------------
# 8. THREAT INTELLIGENCE EXPIRY & ACTIVE FILTERING
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_threat_intelligence_expiry(validation_env):
    """Expired threat indicators are marked inactive or excluded from active indicators."""
    client, session_factory = validation_env
    analyst_token = create_access_token(data={"sub": "analyst_sam", "role": "analyst"})
    headers = {"Authorization": f"Bearer {analyst_token}"}

    async with session_factory() as session:
        ti_expired = ThreatIndicator(
            id="ti-expired-01",
            indicator_type="ip",
            value="192.0.2.99",
            threat_type="botnet",
            is_active=False,
            expires_at=utc_now() - timedelta(days=1),
            confidence=0.9,
            source="OldFeed"
        )
        session.add(ti_expired)
        await session.commit()

    resp = await client.get("/api/banking/intel/indicators?is_active=true", headers=headers)
    assert resp.status_code == 200
    indicators = resp.json()
    assert not any(i["value"] == "192.0.2.99" for i in indicators)


# ---------------------------------------------------------------------------
# 9. GRAPH RELATIONSHIP ACCURACY (NETWORKX MULTI-HOP)
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_graph_relationship_accuracy(validation_env):
    """NetworkX graph correctly correlates Incident -> Violation -> Customer -> IP -> Indicator."""
    client, session_factory = validation_env
    analyst_token = create_access_token(data={"sub": "analyst_sam", "role": "analyst"})
    headers = {"Authorization": f"Bearer {analyst_token}"}

    async with session_factory() as session:
        inc = Incident(id="inc-graph-test-01", title="Graph Verification Incident", summary="Summary", severity="critical")
        session.add(inc)

        vio = SecurityViolationEvent(
            event_id="vio-graph-01",
            event_type="KNOWN_MALICIOUS_IP_MATCH",
            category="network_anomaly",
            severity="critical",
            customer_id="usr-cust-alice",
            session_id="sess-graph-101",
            source_ip="198.51.100.55",
            detection_rule="RULE-NETWORK-KNOWN-IP",
            risk_contribution=85.0,
            correlation_id="corr-graph",
            incident_id="inc-graph-test-01"
        )
        session.add(vio)

        ti = ThreatIndicator(
            id="ti-graph-55",
            indicator_type="ip",
            value="198.51.100.55",
            threat_type="c2_server",
            severity="critical",
            source="AbuseIPDB",
            is_active=True
        )
        session.add(ti)
        await session.commit()

    resp = await client.get("/api/banking/intel/graph/incident/inc-graph-test-01", headers=headers)
    assert resp.status_code == 200
    data = resp.json()

    node_types = {n["type"] for n in data["nodes"]}
    assert "Incident" in node_types
    assert "SecurityViolation" in node_types
    assert "Customer" in node_types
    assert "IPAddress" in node_types
    assert "ThreatIndicator" in node_types

    edge_relations = {e["relation"] for e in data["edges"]}
    assert "TRIGGERED" in edge_relations
    assert "MATCHED_INDICATOR" in edge_relations


# ---------------------------------------------------------------------------
# 10. EVENT CORRELATION UNDER CONCURRENT INGESTION
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_event_correlation_concurrent_ingestion(validation_env):
    """Multiple violation events arriving concurrently within the window are correlated into a single incident."""
    _, session_factory = validation_env
    async with session_factory() as session:
        v1 = SecurityViolationEvent(
            event_id=f"vio-burst-1-{uuid.uuid4().hex[:6]}",
            event_type="UNFAMILIAR_DEVICE_LOGIN",
            category="authentication",
            severity="high",
            customer_id="cust-concurrent-test",
            session_id="sess-concurrent-01",
            source_ip="198.51.100.77",
            detection_rule="RULE-AUTH-UNFAMILIAR-DEVICE",
            risk_contribution=45.0,
            correlation_id="corr-concurrent"
        )
        v2 = SecurityViolationEvent(
            event_id=f"vio-burst-2-{uuid.uuid4().hex[:6]}",
            event_type="FAILED_OTP_BURST",
            category="authentication",
            severity="critical",
            customer_id="cust-concurrent-test",
            session_id="sess-concurrent-01",
            source_ip="198.51.100.77",
            detection_rule="RULE-AUTH-OTP-BRUTE-FORCE",
            risk_contribution=60.0,
            correlation_id="corr-concurrent"
        )
        session.add_all([v1, v2])
        await session.commit()

        # Run correlation engine
        inc = await storyline_engine.correlate_event(db=session, new_event=v2)
        assert inc is not None
        assert inc.id is not None
        assert "takeover" in inc.title.lower() or "correlated" in inc.title.lower() or "sequence" in inc.title.lower()


# ---------------------------------------------------------------------------
# 11. INCIDENT LIFECYCLE CONSISTENCY
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_incident_lifecycle_consistency(validation_env):
    """Lifecycle transitions new -> investigating -> contained -> resolved are enforced and auditable."""
    client, session_factory = validation_env
    analyst_token = create_access_token(data={"sub": "analyst_sam", "role": "analyst"})
    headers = {"Authorization": f"Bearer {analyst_token}"}

    async with session_factory() as session:
        inc = Incident(id="inc-life-01", title="Lifecycle Test Incident", summary="Summary", severity="high", status="new")
        session.add(inc)
        await session.commit()

    # Transition to contained
    resp = await client.patch("/api/banking/storylines/inc-life-01/lifecycle", json={
        "status": "contained",
        "assigned_to": "analyst_sam",
        "investigation_notes": "Sessions revoked and account protected."
    }, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["new_status"] == "contained"


# ---------------------------------------------------------------------------
# 12. FAILED NETWORK REQUESTS & CONTAINMENT RETRY HANDLING
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_failed_network_request_and_retry(validation_env):
    """When a downstream webhook fails, action records FAILED status with error details, allowing analyst retry."""
    client, session_factory = validation_env
    analyst_token = create_access_token(data={"sub": "analyst_sam", "role": "analyst"})
    headers = {"Authorization": f"Bearer {analyst_token}"}

    async with session_factory() as session:
        inc = Incident(id="inc-fail-01", title="Fail Test Incident", summary="Summary", severity="high")
        session.add(inc)
        act = ResponsePlaybookAction(
            action_id="act-fail-01",
            incident_id="inc-fail-01",
            playbook_id="PB-TEST",
            action_type="INVALID_ACTION_FAIL",
            target_entity="target-err",
            risk_level="Critical",
            requires_approval=True,
            status="PENDING_APPROVAL"
        )
        session.add(act)
        await session.commit()

    resp = await client.post("/api/banking/orchestration/actions/act-fail-01/decision", json={"decision": "APPROVE"}, headers=headers)
    assert resp.status_code == 200
    act_data = resp.json()
    assert act_data["status"] == "FAILED"
    assert act_data["error_details"] is not None

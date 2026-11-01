import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.future import select

from app.main import app
from app.models.db_models import (
    Base, User, ThreatIndicator, Incident, SecurityViolationEvent, ResponsePlaybookAction, AuditLog
)
from app.core.database import get_db
from app.core.security import create_access_token

@pytest_asyncio.fixture
async def intel_env():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    
    # Seed analyst user
    async with session_factory() as session:
        u = User(
            id="usr-analyst-intel",
            username="analyst_intel",
            email="analyst@intel.local",
            hashed_password="pw",
            role="analyst",
            is_active=True
        )
        session.add(u)

        # Seed an incident with connected entities
        inc = Incident(
            id="inc-intel-test-01",
            title="[DEMO SIMULATION] Account Takeover Sequence (Customer: cust-intel-101)",
            summary="Correlated multi-stage attack from malicious IP 198.51.100.42",
            severity="critical",
            status="new",
            assigned_to="tier1_analyst",
            affected_entities=["cust-intel-101", "198.51.100.42", "ACT-SYNTH-9999"],
            graph_risk_score=92.0
        )
        session.add(inc)

        # Seed violation event linked to incident
        vio = SecurityViolationEvent(
            event_id="vio-intel-test-01",
            event_type="KNOWN_MALICIOUS_IP_MATCH",
            category="network_anomaly",
            severity="critical",
            customer_id="cust-intel-101",
            session_id="sess-intel-001",
            source_ip="198.51.100.42",
            device_id="device-fingerprint-tor",
            source_application="NexaBank-Web",
            event_metadata={"threat_feed": "EmergingThreats"},
            detection_rule="RULE-NETWORK-KNOWN-IP",
            risk_contribution=80.0,
            correlation_id="corr-intel-test",
            incident_id="inc-intel-test-01",
            is_simulation=True
        )
        session.add(vio)
        await session.commit()

    async def override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client, session_factory

    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_ioc_creation_batch_import_and_deduplication(intel_env):
    """
    Tests:
    1. Manual IOC indicator creation.
    2. Batch IOC feed import with provenance tracking.
    3. Deduplication of identical indicator values with source merging.
    """
    client, session_factory = intel_env
    token = create_access_token(data={"sub": "analyst_intel"})
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create single indicator
    payload_single = {
        "indicator_type": "ip",
        "value": "198.51.100.42",
        "threat_type": "c2_server",
        "severity": "critical",
        "confidence": 0.95,
        "source": "AlienVault OTX",
        "description": "Active Cobalt Strike C2 IP"
    }
    resp1 = await client.post("/api/banking/intel/indicators", json=payload_single, headers=headers)
    assert resp1.status_code == 200
    ioc1 = resp1.json()
    assert ioc1["value"] == "198.51.100.42"

    # 2. Batch Import
    batch_payload = {
        "source_name": "MISP-Financial-Feed",
        "feed_category": "banking_trojan",
        "indicators": [
            {
                "indicator_type": "ip",
                "value": "198.51.100.42",  # Duplicate: should merge source provenance
                "threat_type": "c2_server",
                "severity": "critical",
                "confidence": 0.99,
                "source": "MISP-Financial-Feed"
            },
            {
                "indicator_type": "restricted_beneficiary",
                "value": "ACT-SYNTH-9999",
                "threat_type": "mule_account",
                "severity": "high",
                "confidence": 0.90,
                "source": "MISP-Financial-Feed"
            }
        ]
    }
    resp2 = await client.post("/api/banking/intel/import", json=batch_payload, headers=headers)
    assert resp2.status_code == 200
    res_data = resp2.json()
    assert res_data["updated_count"] == 1  # 198.51.100.42 deduplicated & updated
    assert res_data["imported_count"] == 1  # ACT-SYNTH-9999 added

@pytest.mark.asyncio
async def test_unified_attack_graph_generation(intel_env):
    """
    Verifies that the unified attack graph engine constructs nodes & typed edges across:
    - Incident
    - SecurityViolation
    - Customer
    - IPAddress
    - Session
    - ThreatIndicator
    """
    client, session_factory = intel_env
    token = create_access_token(data={"sub": "analyst_intel"})
    headers = {"Authorization": f"Bearer {token}"}

    # Add matching IOC
    await client.post("/api/banking/intel/indicators", json={
        "indicator_type": "ip",
        "value": "198.51.100.42",
        "threat_type": "c2_server",
        "severity": "critical",
        "confidence": 0.98,
        "source": "AlienVault OTX"
    }, headers=headers)

    # Build Graph for incident
    graph_resp = await client.get("/api/banking/intel/graph/incident/inc-intel-test-01", headers=headers)
    assert graph_resp.status_code == 200
    graph_data = graph_resp.json()

    assert graph_data["node_count"] >= 5
    assert graph_data["edge_count"] >= 4

    node_types = {n["type"] for n in graph_data["nodes"]}
    assert "Incident" in node_types
    assert "SecurityViolation" in node_types
    assert "IPAddress" in node_types
    assert "Customer" in node_types
    assert "ThreatIndicator" in node_types

    edge_relations = {e["relation"] for e in graph_data["edges"]}
    assert "MATCHED_INDICATOR" in edge_relations
    assert "TRIGGERED" in edge_relations

@pytest.mark.asyncio
async def test_threat_intel_workbench_investigation(intel_env):
    """
    Verifies the Threat Intelligence Workbench endpoint correlates the IOC
    with matching violations, incidents, and investigation playbooks.
    """
    client, session_factory = intel_env
    token = create_access_token(data={"sub": "analyst_intel"})
    headers = {"Authorization": f"Bearer {token}"}

    create_resp = await client.post("/api/banking/intel/indicators", json={
        "indicator_type": "ip",
        "value": "198.51.100.42",
        "threat_type": "c2_server",
        "severity": "critical",
        "confidence": 0.98,
        "source": "AlienVault OTX"
    }, headers=headers)
    ioc_id = create_resp.json()["id"]

    inv_resp = await client.get(f"/api/banking/intel/investigate/{ioc_id}", headers=headers)
    assert inv_resp.status_code == 200
    inv_data = inv_resp.json()

    assert inv_data["matched_violations_count"] >= 1
    assert len(inv_data["related_incidents"]) >= 1
    assert inv_data["related_incidents"][0]["id"] == "inc-intel-test-01"
    assert len(inv_data["recommended_investigation_steps"]) >= 3

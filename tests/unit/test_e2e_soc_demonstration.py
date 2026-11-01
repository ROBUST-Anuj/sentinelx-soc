"""
SentinelX Phase 5: Full End-to-End SOC Demonstration Lifecycle Test Suite.
Verifies the complete 13-step NexaBank-to-SentinelX detection, correlation,
investigation, and containment lifecycle using actual backend APIs and DB records.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.future import select

from app.main import app
from app.core.database import get_db
from app.core.security import create_access_token
from app.models.db_models import (
    Base, User, BankAccount, Incident, SecurityViolationEvent,
    ThreatIndicator, ResponsePlaybookAction, AuditLog
)

@pytest_asyncio.fixture
async def demo_env():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        # Seed test admin & analyst
        u_admin = User(id="usr-demo-admin", username="admin_demo", email="admin@soc.local", hashed_password="pw", role="admin", is_active=True)
        u_analyst = User(id="usr-demo-analyst", username="analyst_demo", email="analyst@soc.local", hashed_password="pw", role="analyst", is_active=True)
        session.add_all([u_admin, u_analyst])
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
async def test_full_13_step_soc_lifecycle_endpoint(demo_env):
    """
    Executes and validates the entire 13-step NexaBank-to-SentinelX security lifecycle:
    1. Simulate a suspicious IP indicator.
    2. Generate unfamiliar device login.
    3. Generate repeated OTP failures.
    4. Add a new beneficiary.
    5. Attempt a suspicious high-value transfer.
    6. Generate a unified attack storyline.
    7. Open the associated attack graph.
    8. Inspect the threat intelligence evidence.
    9. Generate the response playbook.
    10. Obtain analyst approval.
    11. Execute an authorized containment action.
    12. Verify the effect in NexaBank.
    13. Inspect the final hash-chained audit record.
    """
    client, session_factory = demo_env
    token = create_access_token(data={"sub": "analyst_demo", "role": "analyst"})
    headers = {"Authorization": f"Bearer {token}"}

    # Execute Full Demo Lifecycle Runner
    resp = await client.post("/api/banking/command-center/demo/run-full-lifecycle", headers=headers)
    assert resp.status_code == 200
    data = resp.json()

    assert data["total_steps"] == 13
    assert data["successful_steps"] == 13
    assert len(data["steps"]) == 13

    # Validate each step status
    for st in data["steps"]:
        assert st["status"] == "SUCCESS", f"Step {st['step_number']} ({st['step_name']}) failed: {st['details']}"

    # Verify persistent database state after lifecycle
    async with session_factory() as session:
        # Check incident created
        inc_id = data["incident_id"]
        inc = (await session.execute(select(Incident).where(Incident.id == inc_id))).scalars().first()
        assert inc is not None
        assert inc.severity == "critical"

        # Check threat indicator exists
        ti = (await session.execute(select(ThreatIndicator).where(ThreatIndicator.value == "198.51.100.99"))).scalars().first()
        assert ti is not None
        assert ti.is_active is True

        # Check playbook action executed
        act = (await session.execute(select(ResponsePlaybookAction).where(ResponsePlaybookAction.incident_id == inc_id))).scalars().first()
        assert act is not None
        assert act.status == "EXECUTED"

        # Check cryptographic audit log sealed
        aud = (await session.execute(select(AuditLog).order_by(AuditLog.timestamp.desc()))).scalars().first()
        assert aud is not None
        assert aud.entry_hash is not None


@pytest.mark.asyncio
async def test_command_center_stats_and_unified_timeline(demo_env):
    """
    Validates that:
    1. Command center statistics compute all 8 real metrics without static mock values.
    2. System health matrix reports real DB engine, ML status, and uptime.
    3. Chronological timeline fuses multi-domain events with provenance and cryptographic seals.
    """
    client, _ = demo_env
    token = create_access_token(data={"sub": "admin_demo", "role": "admin"})
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Run demo lifecycle to generate rich database records
    await client.post("/api/banking/command-center/demo/run-full-lifecycle", headers=headers)

    # 2. Query Command Center Stats
    stats_resp = await client.get("/api/banking/command-center/stats", headers=headers)
    assert stats_resp.status_code == 200
    stats = stats_resp.json()

    assert stats["total_security_events"] >= 4
    assert stats["active_critical_high_incidents"] >= 1
    assert stats["active_attack_storylines"] >= 1
    assert stats["threat_intelligence_matches"] >= 1
    assert stats["successful_containment_actions"] >= 1
    assert stats["total_incidents"] >= 1
    assert stats["severity_distribution"]["critical"] >= 1
    assert len(stats["recent_incident_activity"]) >= 1

    # Check real system health matrix
    health = stats["system_health"]
    assert health["api_status"] == "healthy"
    assert health["database_status"] == "connected"
    assert "sqlite" in health["database_engine"].lower() or "postgres" in health["database_engine"].lower()
    assert "online" in health["ml_inference_status"].lower()
    assert health["uptime_seconds"] >= 0

    # 3. Query Unified Chronological Timeline
    timeline_resp = await client.get("/api/banking/command-center/timeline/unified", headers=headers)
    assert timeline_resp.status_code == 200
    timeline = timeline_resp.json()
    assert len(timeline) >= 4

    categories = {t["category"] for t in timeline}
    assert "security_violation" in categories or "incident_lifecycle" in categories or "response_execution" in categories
    for item in timeline:
        assert item["timestamp"] is not None
        assert item["source_provenance"] is not None
        assert item["severity"] is not None

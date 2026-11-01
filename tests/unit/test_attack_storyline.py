import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.future import select

from app.main import app
from app.models.db_models import Base, User, SecurityViolationEvent, Incident, DetectionFinding
from app.core.database import get_db
from app.core.security import create_access_token

@pytest_asyncio.fixture
async def test_env():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    
    # Pre-seed analyst user
    async with session_factory() as session:
        u = User(
            id="usr-analyst-1",
            username="analyst_test",
            email="analyst@test.local",
            hashed_password="pw",
            role="analyst",
            is_active=True
        )
        session.add(u)
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
async def test_ato_kill_chain_produces_unified_attack_storyline(test_env):
    """
    Submits a 3-step Account Takeover Sequence:
    Step 1: UNFAMILIAR_DEVICE_LOGIN
    Step 2: FAILED_OTP_BURST
    Step 3: AMOUNT_MANIPULATION_ATTEMPT
    
    Verifies that:
    1. Only ONE unified Incident is generated.
    2. The title identifies the Account Takeover sequence.
    3. All events are attached to the same incident ID.
    4. Timeline and investigation playbook are present.
    """
    client, session_factory = test_env
    token = create_access_token(data={"sub": "analyst_test"})
    headers = {"Authorization": f"Bearer {token}"}

    customer_id = "cust-target-101"
    session_id = "sess-compromised-999"

    # Step 1: Unfamiliar Device Login
    resp1 = await client.post("/api/banking/security/events", json={
        "event_type": "UNFAMILIAR_DEVICE_LOGIN",
        "category": "authentication",
        "customer_id": customer_id,
        "session_id": session_id,
        "source_application": "NexaBank-Web",
        "event_metadata": {"asn": "AS-12345", "device": "Linux-Tor-Exit"},
        "is_simulation": True
    }, headers=headers)
    assert resp1.status_code == 200
    data1 = resp1.json()
    inc1_id = data1["incident_id"]
    assert inc1_id is not None

    # Step 2: Failed OTP Burst in same session
    resp2 = await client.post("/api/banking/security/events", json={
        "event_type": "FAILED_OTP_BURST",
        "category": "authentication",
        "customer_id": customer_id,
        "session_id": session_id,
        "source_application": "NexaBank-Web",
        "event_metadata": {"consecutive_failures": 5},
        "is_simulation": True
    }, headers=headers)
    assert resp2.status_code == 200
    data2 = resp2.json()

    # Step 3: Transaction Amount Manipulation
    resp3 = await client.post("/api/banking/security/events", json={
        "event_type": "AMOUNT_MANIPULATION_ATTEMPT",
        "category": "transaction_fraud",
        "customer_id": customer_id,
        "session_id": session_id,
        "source_application": "NexaBank-Web",
        "event_metadata": {"attempted_amount": 99999900},
        "is_simulation": True
    }, headers=headers)
    assert resp3.status_code == 200
    data3 = resp3.json()

    # CRITICAL INVARIANT: All 3 events share the same unified Incident ID (no duplicates)
    assert data2["incident_id"] == inc1_id
    assert data3["incident_id"] == inc1_id

    # Verify Storyline endpoint returns complete timeline
    story_resp = await client.get(f"/api/banking/storylines/{inc1_id}", headers=headers)
    assert story_resp.status_code == 200
    story_data = story_resp.json()

    assert story_data["incident_id"] == inc1_id
    assert story_data["event_count"] >= 3
    assert len(story_data["timeline"]) >= 3
    assert "Takeover" in story_data["title"] or "ATO" in story_data["title"]
    assert len(story_data["recommended_playbook"]) > 0

    # Lifecycle update: Transition from NEW -> INVESTIGATING -> CONTAINED -> RESOLVED
    life_resp = await client.patch(f"/api/banking/storylines/{inc1_id}/lifecycle", json={
        "status": "contained",
        "assigned_to": "senior_analyst",
        "investigation_notes": "Revoked customer JWT and frozen source account."
    }, headers=headers)
    assert life_resp.status_code == 200
    assert life_resp.json()["new_status"] == "contained"

    # Verify in DB
    async with session_factory() as session:
        inc = (await session.execute(select(Incident).where(Incident.id == inc1_id))).scalars().first()
        assert inc.status == "contained"
        assert inc.assigned_to == "senior_analyst"

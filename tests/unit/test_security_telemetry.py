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
async def test_client_and_db():
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
async def test_browser_telemetry_ingestion_and_privacy(test_client_and_db):
    client, session_factory = test_client_and_db
    token = create_access_token(data={"sub": "analyst_test"})
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "event_type": "TAB_SWITCH_BURST",
        "category": "browser_behaviour",
        "customer_id": "usr-analyst-1",
        "session_id": "sess-xyz-123",
        "transaction_id": "tx-pending-456",
        "device_id": "device-browser-chrome-win",
        "source_application": "NexaBank-Web",
        "event_metadata": {
            "tab_switch_count": 5,
            "time_window_sec": 10,
            "password": "DO_NOT_STORE_PLAINTEXT_SECRET",
            "otp": "999999"
        },
        "is_simulation": False
    }

    resp = await client.post("/api/banking/security/events", json=payload, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["event_type"] == "TAB_SWITCH_BURST"
    assert data["category"] == "browser_behaviour"
    assert data["severity"] == "medium"
    # Ensure privacy sanitization stripped raw password and otp
    assert "password" not in data["event_metadata"]
    assert "otp" not in data["event_metadata"]
    assert data["event_metadata"]["tab_switch_count"] == 5

@pytest.mark.asyncio
async def test_application_security_sqli_detection_and_incident(test_client_and_db):
    client, session_factory = test_client_and_db
    token = create_access_token(data={"sub": "analyst_test"})
    headers = {"Authorization": f"Bearer {token}"}

    # Controlled test SQLi probe in search/input memo
    payload = {
        "event_type": "INPUT_FIELD_PROBE",
        "category": "browser_behaviour",
        "customer_id": "usr-analyst-1",
        "session_id": "sess-sqli-test",
        "device_id": "device-dev",
        "event_metadata": {
            "memo_input": "admin' OR '1'='1' --",
            "field": "description"
        },
        "is_simulation": True
    }

    resp = await client.post("/api/banking/security/events", json=payload, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    # Authoritative backend classified it as critical application security
    assert data["category"] == "application_security"
    assert data["severity"] == "critical"
    assert data["incident_id"] is not None

    # Check that SOC incident was created
    async with session_factory() as session:
        inc = (await session.execute(
            select(Incident).where(Incident.id == data["incident_id"])
        )).scalars().first()
        assert inc is not None
        assert inc.severity == "critical"
        assert "[DEMO SIMULATION]" in inc.title

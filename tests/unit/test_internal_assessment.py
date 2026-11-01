import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.future import select

from app.main import app
from app.models.db_models import Base, BankAccount, Event, Incident, DetectionFinding
from app.core.database import get_db
from app.core.config import settings

@pytest_asyncio.fixture
async def test_app_client():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    
    # Pre-seed accounts
    async with session_factory() as session:
        acc1 = BankAccount(
            id="acc-source-1",
            user_id="cust-101",
            account_number="ACT-NEXA-101",
            currency="INR",
            balance_minor=1_000_000_00,
            status="active"
        )
        acc2 = BankAccount(
            id="acc-dest-2",
            user_id="cust-202",
            account_number="ACT-NEXA-202",
            currency="INR",
            balance_minor=100_000_00,
            status="active"
        )
        acc_suspicious = BankAccount(
            id="acc-dest-bad",
            user_id="cust-bad",
            account_number="ACT-NEXA-999",
            currency="INR",
            balance_minor=5_000_00,
            status="suspended"
        )
        session.add_all([acc1, acc2, acc_suspicious])
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
async def test_internal_assessment_requires_auth(test_app_client):
    client, _ = test_app_client
    payload = {
        "transaction_id": "tx-test-001",
        "customer_id": "cust-101",
        "source_account_id": "acc-source-1",
        "destination_account_number": "ACT-NEXA-202",
        "amount_minor": 5_000_00,
        "currency": "INR",
        "idempotency_key": "idemp-key-test-001"
    }
    # No auth header -> 401
    resp = await client.post("/internal/v1/transaction-assessments", json=payload)
    assert resp.status_code == 401

    # Wrong auth header -> 403
    resp = await client.post(
        "/internal/v1/transaction-assessments",
        json=payload,
        headers={"X-Service-Auth": "wrong-secret-token"}
    )
    assert resp.status_code == 403

@pytest.mark.asyncio
async def test_internal_assessment_allow_decision(test_app_client):
    client, session_factory = test_app_client
    headers = {"X-Service-Auth": settings.INTERNAL_SERVICE_KEY}
    payload = {
        "transaction_id": "tx-normal-002",
        "customer_id": "cust-101",
        "source_account_id": "acc-source-1",
        "destination_account_number": "ACT-NEXA-202",
        "amount_minor": 5_000_00,  # ₹5,000 (Low risk)
        "currency": "INR",
        "source_ip": "10.0.0.1",
        "idempotency_key": "idemp-key-test-002"
    }

    resp = await client.post("/internal/v1/transaction-assessments", json=payload, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["policy_decision"] == "ALLOW"
    assert data["risk_score"] < 40.0
    assert data["requires_verification"] is False

    # Check SOC Canonical Event was stored
    async with session_factory() as session:
        event = (await session.execute(
            select(Event).where(Event.event_type == "BANKING_TRANSACTION_ASSESSED")
        )).scalars().first()
        assert event is not None
        assert event.source_name == "NexaBank-Transaction-Gateway"
        assert event.normalized_fields["transaction_id"] == "tx-normal-002"

@pytest.mark.asyncio
async def test_internal_assessment_blocks_restricted_and_creates_soc_incident(test_app_client):
    client, session_factory = test_app_client
    headers = {"X-Service-Auth": settings.INTERNAL_SERVICE_KEY}
    payload = {
        "transaction_id": "tx-blocked-003",
        "customer_id": "cust-101",
        "source_account_id": "acc-source-1",
        "destination_account_number": "ACT-NEXA-999",  # suspended account
        "amount_minor": 10_000_00,
        "currency": "INR",
        "source_ip": "192.168.1.100",
        "idempotency_key": "idemp-key-test-003"
    }

    resp = await client.post("/internal/v1/transaction-assessments", json=payload, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["policy_decision"] == "BLOCK"
    assert "DESTINATION_ACCOUNT_RESTRICTED" in data["reason_codes"]
    assert data["incident_id"] is not None

    # Verify SOC incident and detection finding created in database
    async with session_factory() as session:
        inc = (await session.execute(
            select(Incident).where(Incident.id == data["incident_id"])
        )).scalars().first()
        assert inc is not None
        assert inc.severity == "critical"
        assert "cust-101" in inc.affected_entities

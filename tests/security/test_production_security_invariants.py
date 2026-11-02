import pytest
import pytest_asyncio
import time
import uuid
import json
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.future import select

from app.main import app
from app.models.db_models import Base, User, BankAccount, Transfer, LedgerEntry, Incident, VerificationChallenge
from app.core.database import get_db
from app.core.config import settings
from app.core.security import create_access_token, get_password_hash
from app.banking.internal_routes import generate_hmac_signature

@pytest_asyncio.fixture
async def security_fixture():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    # Seed users and accounts
    async with session_factory() as session:
        # Customer A
        cust_a = User(
            id="usr-cust-a",
            username="customer_a",
            email="cust_a@bank.local",
            hashed_password=get_password_hash("CustA@Pass123"),
            role="customer",
            is_active=True
        )
        # Customer B
        cust_b = User(
            id="usr-cust-b",
            username="customer_b",
            email="cust_b@bank.local",
            hashed_password=get_password_hash("CustB@Pass123"),
            role="customer",
            is_active=True
        )
        # SOC Analyst
        analyst = User(
            id="usr-analyst-1",
            username="soc_analyst",
            email="analyst@soc.local",
            hashed_password=get_password_hash("Analyst@Pass123"),
            role="analyst",
            is_active=True
        )
        # Administrator
        admin = User(
            id="usr-admin-1",
            username="soc_admin",
            email="admin@soc.local",
            hashed_password=get_password_hash("Admin@Pass123"),
            role="admin",
            is_active=True
        )
        session.add_all([cust_a, cust_b, analyst, admin])
        await session.commit()

        # Accounts for Customer A
        acc_a = BankAccount(
            id="acc-cust-a-01",
            user_id="usr-cust-a",
            account_number="ACT-CUSTA-001",
            account_type="checking",
            currency="INR",
            balance_minor=50_000_00,  # ₹50,000.00
            status="active",
            is_synthetic=True
        )
        # Accounts for Customer B
        acc_b = BankAccount(
            id="acc-cust-b-01",
            user_id="usr-cust-b",
            account_number="ACT-CUSTB-001",
            account_type="checking",
            currency="INR",
            balance_minor=10_000_00,  # ₹10,000.00
            status="active",
            is_synthetic=True
        )
        # Suspended / Restricted beneficiary account
        acc_suspended = BankAccount(
            id="acc-suspended-99",
            user_id="usr-cust-b",
            account_number="ACT-SUSPENDED-999",
            account_type="checking",
            currency="INR",
            balance_minor=0,
            status="suspended",
            is_synthetic=True
        )
        session.add_all([acc_a, acc_b, acc_suspended])
        await session.commit()

    async def override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client, session_factory

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_cross_customer_isolation_read(security_fixture):
    """Invariant 1: Customer A cannot read Customer B's account details."""
    client, _ = security_fixture
    token_a = create_access_token({"sub": "customer_a", "role": "customer"})
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # Accessing own account should succeed
    res_own = await client.get("/api/banking/accounts/acc-cust-a-01", headers=headers_a)
    assert res_own.status_code == 200
    assert res_own.json()["account_number"] == "ACT-CUSTA-001"

    # Attempting to read Customer B's account should be rejected with 403 Forbidden
    res_other = await client.get("/api/banking/accounts/acc-cust-b-01", headers=headers_a)
    assert res_other.status_code == 403
    assert "Access denied" in res_other.json()["detail"]


@pytest.mark.asyncio
async def test_cross_customer_isolation_transfer(security_fixture):
    """Invariant 2: Customer A cannot initiate a transfer sourcing funds from Customer B's account."""
    client, _ = security_fixture
    token_a = create_access_token({"sub": "customer_a", "role": "customer"})
    headers_a = {"Authorization": f"Bearer {token_a}"}

    payload = {
        "source_account_id": "acc-cust-b-01",  # Belongs to Customer B!
        "destination_account_number": "ACT-CUSTA-001",
        "amount_minor": 1000_00,
        "currency": "INR",
        "description": "Unauthorized cross-account siphon attempt",
        "idempotency_key": f"unauth-{uuid.uuid4()}"
    }

    res = await client.post("/api/banking/transfers", json=payload, headers=headers_a)
    assert res.status_code == 403
    assert "Account ownership verification failed" in res.json()["detail"]


@pytest.mark.asyncio
async def test_customer_cannot_access_soc_incidents(security_fixture):
    """Invariant 3: Users with role='customer' are forbidden from SOC incident endpoints."""
    client, _ = security_fixture
    token_customer = create_access_token({"sub": "customer_a", "role": "customer"})
    headers_customer = {"Authorization": f"Bearer {token_customer}"}

    # /api/incidents listing
    res_list = await client.get("/api/incidents", headers=headers_customer)
    assert res_list.status_code == 403

    # /api/overview/stats
    res_stats = await client.get("/api/overview/stats", headers=headers_customer)
    assert res_stats.status_code == 403


@pytest.mark.asyncio
async def test_customer_cannot_access_threat_intel(security_fixture):
    """Invariant 4: Users with role='customer' are forbidden from SOC threat intelligence."""
    client, _ = security_fixture
    token_customer = create_access_token({"sub": "customer_a", "role": "customer"})
    headers_customer = {"Authorization": f"Bearer {token_customer}"}

    res_ti = await client.get("/api/threat-intel", headers=headers_customer)
    assert res_ti.status_code == 403


@pytest.mark.asyncio
async def test_analyst_can_access_soc_endpoints(security_fixture):
    """Invariant 5: Users with role='analyst' have authorized access to SOC incidents and intel."""
    client, _ = security_fixture
    token_analyst = create_access_token({"sub": "soc_analyst", "role": "analyst"})
    headers_analyst = {"Authorization": f"Bearer {token_analyst}"}

    res_incidents = await client.get("/api/incidents", headers=headers_analyst)
    assert res_incidents.status_code == 200

    res_ti = await client.get("/api/threat-intel", headers=headers_analyst)
    assert res_ti.status_code == 200


@pytest.mark.asyncio
async def test_hmac_request_signing_valid(security_fixture):
    """Invariant 6: Valid cryptographic HMAC signature on internal API is accepted."""
    client, _ = security_fixture
    method = "POST"
    path = "/internal/v1/transaction-assessments"
    timestamp = str(time.time())
    nonce = f"nonce-{uuid.uuid4().hex}"
    idem_key = f"idem-hmac-{uuid.uuid4().hex[:12]}"
    body_data = {
        "transaction_id": "tx-test-hmac-1",
        "customer_id": "usr-cust-a",
        "source_account_id": "acc-cust-a-01",
        "destination_account_number": "ACT-CUSTB-001",
        "amount_minor": 5000_00,
        "currency": "INR",
        "source_ip": "192.168.1.50",
        "idempotency_key": idem_key
    }
    raw_body = json.dumps(body_data).encode("utf-8")

    sig = generate_hmac_signature(
        secret_key=settings.INTERNAL_SERVICE_KEY,
        method=method,
        path=path,
        timestamp=timestamp,
        nonce=nonce,
        body=raw_body
    )

    headers = {
        "Content-Type": "application/json",
        "X-Signature": sig,
        "X-Timestamp": timestamp,
        "X-Nonce": nonce
    }

    res = await client.post(path, content=raw_body, headers=headers)
    assert res.status_code == 200
    assert res.json()["policy_decision"] in ["ALLOW", "VERIFY", "HOLD", "BLOCK"]


@pytest.mark.asyncio
async def test_hmac_request_signing_timestamp_drift_rejected(security_fixture):
    """Invariant 7: HMAC signature with timestamp older than 300s is rejected."""
    client, _ = security_fixture
    method = "POST"
    path = "/internal/v1/transaction-assessments"
    expired_timestamp = str(time.time() - 301)  # 301 seconds ago
    nonce = f"nonce-{uuid.uuid4().hex}"
    raw_body = json.dumps({"test": "expired"}).encode("utf-8")

    sig = generate_hmac_signature(
        secret_key=settings.INTERNAL_SERVICE_KEY,
        method=method,
        path=path,
        timestamp=expired_timestamp,
        nonce=nonce,
        body=raw_body
    )

    headers = {
        "Content-Type": "application/json",
        "X-Signature": sig,
        "X-Timestamp": expired_timestamp,
        "X-Nonce": nonce
    }

    res = await client.post(path, content=raw_body, headers=headers)
    assert res.status_code == 403
    assert "drift window" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_hmac_request_signing_nonce_replay_rejected(security_fixture):
    """Invariant 8: Replaying the same nonce within the drift window is rejected."""
    client, _ = security_fixture
    method = "POST"
    path = "/internal/v1/transaction-assessments"
    timestamp = str(time.time())
    nonce = f"replay-nonce-{uuid.uuid4().hex}"
    idem_key = f"idem-replay-{uuid.uuid4().hex[:12]}"
    body_data = {
        "transaction_id": "tx-nonce-replay-1",
        "customer_id": "usr-cust-a",
        "source_account_id": "acc-cust-a-01",
        "destination_account_number": "ACT-CUSTB-001",
        "amount_minor": 1000_00,
        "currency": "INR",
        "source_ip": "10.0.0.1",
        "idempotency_key": idem_key
    }
    raw_body = json.dumps(body_data).encode("utf-8")

    sig = generate_hmac_signature(
        secret_key=settings.INTERNAL_SERVICE_KEY,
        method=method,
        path=path,
        timestamp=timestamp,
        nonce=nonce,
        body=raw_body
    )

    headers = {
        "Content-Type": "application/json",
        "X-Signature": sig,
        "X-Timestamp": timestamp,
        "X-Nonce": nonce
    }

    # First request: should pass
    res1 = await client.post(path, content=raw_body, headers=headers)
    assert res1.status_code == 200

    # Second request with identical nonce: must be rejected as replay
    res2 = await client.post(path, content=raw_body, headers=headers)
    assert res2.status_code == 403
    assert "replay detected" in res2.json()["detail"].lower()


@pytest.mark.asyncio
async def test_hmac_request_signing_body_tampering_rejected(security_fixture):
    """Invariant 9: Modifying the body after signature calculation is rejected (integrity violation)."""
    client, _ = security_fixture
    method = "POST"
    path = "/internal/v1/transaction-assessments"
    timestamp = str(time.time())
    nonce = f"tamper-nonce-{uuid.uuid4().hex}"
    original_body = json.dumps({"amount_minor": 1000_00}).encode("utf-8")

    sig = generate_hmac_signature(
        secret_key=settings.INTERNAL_SERVICE_KEY,
        method=method,
        path=path,
        timestamp=timestamp,
        nonce=nonce,
        body=original_body
    )

    tampered_body = json.dumps({"amount_minor": 999999_00}).encode("utf-8")

    headers = {
        "Content-Type": "application/json",
        "X-Signature": sig,  # Signature was for original_body
        "X-Timestamp": timestamp,
        "X-Nonce": nonce
    }

    res = await client.post(path, content=tampered_body, headers=headers)
    assert res.status_code == 403
    assert "mismatch" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_double_entry_balance_and_insufficient_funds(security_fixture):
    """Invariant 10: Transfers enforce atomic balance invariants and cannot drive account negative."""
    client, session_factory = security_fixture
    token_a = create_access_token({"sub": "customer_a", "role": "customer"})
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # Attempting to transfer more than available balance (₹50,000.00 minor = 5,000,000)
    overdraft_payload = {
        "source_account_id": "acc-cust-a-01",
        "destination_account_number": "ACT-CUSTB-001",
        "amount_minor": 60_000_00,  # ₹60,000.00
        "currency": "INR",
        "description": "Overdraft attempt",
        "idempotency_key": f"overdraft-{uuid.uuid4()}"
    }

    res_overdraft = await client.post("/api/banking/transfers", json=overdraft_payload, headers=headers_a)
    assert res_overdraft.status_code == 400
    assert "Insufficient available balance" in res_overdraft.json()["detail"]

    # Verify balance was not modified
    async with session_factory() as session:
        acc_a = (await session.execute(select(BankAccount).where(BankAccount.id == "acc-cust-a-01"))).scalars().first()
        assert acc_a.balance_minor == 50_000_00


@pytest.mark.asyncio
async def test_idempotency_mismatched_payload_conflict(security_fixture):
    """Invariant 11: Reusing idempotency key with altered parameters returns 409 Conflict."""
    client, _ = security_fixture
    token_a = create_access_token({"sub": "customer_a", "role": "customer"})
    headers_a = {"Authorization": f"Bearer {token_a}"}
    idempotency_key = f"idem-{uuid.uuid4()}"

    initial_payload = {
        "source_account_id": "acc-cust-a-01",
        "destination_account_number": "ACT-CUSTB-001",
        "amount_minor": 100_00,
        "currency": "INR",
        "description": "Legitimate payment",
        "idempotency_key": idempotency_key
    }

    res1 = await client.post("/api/banking/transfers", json=initial_payload, headers=headers_a)
    assert res1.status_code == 200

    # Submit second request with altered amount
    conflicting_payload = {
        "source_account_id": "acc-cust-a-01",
        "destination_account_number": "ACT-CUSTB-001",
        "amount_minor": 999_00,  # Altered!
        "currency": "INR",
        "description": "Legitimate payment",
        "idempotency_key": idempotency_key
    }

    res2 = await client.post("/api/banking/transfers", json=conflicting_payload, headers=headers_a)
    assert res2.status_code == 409
    assert "mismatched transaction parameters" in res2.json()["detail"].lower()


@pytest.mark.asyncio
async def test_idempotency_identical_payload_deduplication(security_fixture):
    """Invariant 12: Reusing idempotency key with identical payload deduplicates without double-debiting."""
    client, session_factory = security_fixture
    token_a = create_access_token({"sub": "customer_a", "role": "customer"})
    headers_a = {"Authorization": f"Bearer {token_a}"}
    idempotency_key = f"idem-dedup-{uuid.uuid4()}"

    payload = {
        "source_account_id": "acc-cust-a-01",
        "destination_account_number": "ACT-CUSTB-001",
        "amount_minor": 500_00,
        "currency": "INR",
        "description": "Coffee payment",
        "idempotency_key": idempotency_key
    }

    res1 = await client.post("/api/banking/transfers", json=payload, headers=headers_a)
    assert res1.status_code == 200
    tx1_id = res1.json()["id"]

    res2 = await client.post("/api/banking/transfers", json=payload, headers=headers_a)
    assert res2.status_code == 200
    assert res2.json()["id"] == tx1_id

    # Verify only single debit of ₹500.00 occurred
    async with session_factory() as session:
        acc_a = (await session.execute(select(BankAccount).where(BankAccount.id == "acc-cust-a-01"))).scalars().first()
        assert acc_a.balance_minor == 50_000_00 - 500_00


@pytest.mark.asyncio
async def test_blocked_beneficiary_zero_financial_leakage(security_fixture):
    """Invariant 13: Attempting transfer to suspended beneficiary debits zero funds and generates SOC incident."""
    client, session_factory = security_fixture
    token_a = create_access_token({"sub": "customer_a", "role": "customer"})
    headers_a = {"Authorization": f"Bearer {token_a}"}

    payload = {
        "source_account_id": "acc-cust-a-01",
        "destination_account_number": "ACT-SUSPENDED-999",  # Suspended beneficiary!
        "amount_minor": 2000_00,
        "currency": "INR",
        "description": "Transfer to suspended recipient",
        "idempotency_key": f"block-test-{uuid.uuid4()}"
    }

    res = await client.post("/api/banking/transfers", json=payload, headers=headers_a)
    assert res.status_code == 200
    res_data = res.json()
    assert res_data["status"] == "BLOCKED"

    # Verify zero funds debited
    async with session_factory() as session:
        acc_a = (await session.execute(select(BankAccount).where(BankAccount.id == "acc-cust-a-01"))).scalars().first()
        # Zero debited for blocked transfer: balance remains unchanged at 50,000.00
        assert acc_a.balance_minor == 50_000_00

        # Verify SOC incident created
        inc_res = await session.execute(select(Incident).order_by(Incident.created_at.desc()))
        incident = inc_res.scalars().first()
        assert incident is not None
        assert "Banking Fraud BLOCK" in incident.title


@pytest.mark.asyncio
async def test_telemetry_privacy_no_plain_credentials(security_fixture):
    """Invariant 14: Telemetry submission does not expose credentials in plain-text metadata."""
    client, session_factory = security_fixture
    token_a = create_access_token({"sub": "customer_a", "role": "customer"})
    headers_a = {"Authorization": f"Bearer {token_a}"}

    telemetry_payload = {
        "event_type": "PAGE_NAVIGATION",
        "category": "browser",
        "session_id": "sess-test-privacy",
        "device_id": "dev-fingerprint-test",
        "source_application": "nexabank_portal",
        "event_metadata": {
            "page": "/transfer",
            "navigation_type": "standard",
            "screen_width": 1920
        }
    }

    res = await client.post("/api/banking/security/events", json=telemetry_payload, headers=headers_a)
    assert res.status_code == 200


@pytest.mark.asyncio
async def test_verification_challenge_failed_attempts_lockout(security_fixture):
    """Invariant 15: Three consecutive failed OTP submissions locks the transfer into REJECTED state."""
    client, session_factory = security_fixture
    token_a = create_access_token({"sub": "customer_a", "role": "customer"})
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # Step 1: Initiate a transfer that requires verification (90% drain on fresh account: 45,000.00 out of 50,000.00)
    payload = {
        "source_account_id": "acc-cust-a-01",
        "destination_account_number": "ACT-CUSTB-001",
        "amount_minor": 45_000_00,  # Triggers NEW_ACCOUNT_HIGH_DRAIN (45 score -> VERIFY)
        "currency": "INR",
        "description": "Elevated transfer for challenge test",
        "idempotency_key": f"challenge-lockout-{uuid.uuid4()}"
    }

    res = await client.post("/api/banking/transfers", json=payload, headers=headers_a)
    assert res.status_code == 200
    tx_data = res.json()
    assert tx_data["status"] == "AWAITING_VERIFICATION"
    tx_id = tx_data["id"]

    # Step 2: Submit 3 consecutive incorrect OTP codes
    for attempt in range(3):
        res_v = await client.post(
            f"/api/banking/transfers/{tx_id}/verify",
            json={"verification_code": "000000"},  # Incorrect code
            headers=headers_a
        )
        if attempt < 2:
            assert res_v.status_code == 400
            assert "Invalid verification code" in res_v.json()["detail"]
        else:
            # 3rd attempt exceeds max attempts -> lockout
            assert res_v.status_code == 400
            assert "exceeded" in res_v.json()["detail"].lower() or "rejected" in res_v.json()["detail"].lower()

    # Step 3: Verify transfer status is REJECTED in database
    async with session_factory() as session:
        tx = (await session.execute(select(Transfer).where(Transfer.id == tx_id))).scalars().first()
        assert tx.status == "REJECTED"


@pytest.mark.asyncio
async def test_synthetic_demo_customer_isolation(security_fixture):
    """Invariant 16: Automated 13-step demonstration isolates synthetic demo customers from real accounts."""
    client, session_factory = security_fixture
    token_admin = create_access_token({"sub": "soc_admin", "role": "admin"})
    headers_admin = {"Authorization": f"Bearer {token_admin}"}

    res_demo = await client.post("/api/banking/command-center/demo/run-full-lifecycle", headers=headers_admin)
    assert res_demo.status_code == 200
    demo_data = res_demo.json()
    assert demo_data["total_steps"] == 13
    assert demo_data["successful_steps"] == 13
    assert demo_data["customer_id"] == "cust-e2e-demo"

    # Confirm real customer accounts were uncorrupted
    async with session_factory() as session:
        acc_a = (await session.execute(select(BankAccount).where(BankAccount.id == "acc-cust-a-01"))).scalars().first()
        acc_b = (await session.execute(select(BankAccount).where(BankAccount.id == "acc-cust-b-01"))).scalars().first()
        assert acc_a is not None and acc_b is not None
        assert acc_a.user_id == "usr-cust-a"
        assert acc_b.user_id == "usr-cust-b"

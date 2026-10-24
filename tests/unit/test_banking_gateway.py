import pytest
import pytest_asyncio
import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from fastapi import HTTPException

from app.models.db_models import Base, User, BankAccount, Transfer, LedgerEntry, VerificationChallenge
from app.models.schemas import TransferCreateRequest, PolicyDecision, TransferStatus
from app.banking.gateway import transaction_gateway
from app.banking.risk_engine import fraud_engine

@pytest_asyncio.fixture
async def async_db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        # Seed test users
        u1 = User(id="user-alice", username="alice", email="alice@test.local", hashed_password="pw", role="analyst")
        u2 = User(id="user-bob", username="bob", email="bob@test.local", hashed_password="pw", role="analyst")
        session.add_all([u1, u2])
        await session.commit()
        
        # Seed accounts
        acc1 = BankAccount(
            id="acc-alice",
            user_id="user-alice",
            account_number="ACT-ALICE-01",
            currency="INR",
            balance_minor=100_000_00,  # ₹1,00,000.00
            status="active"
        )
        acc2 = BankAccount(
            id="acc-bob",
            user_id="user-bob",
            account_number="ACT-BOB-02",
            currency="INR",
            balance_minor=10_000_00,   # ₹10,000.00
            status="active"
        )
        acc_frozen = BankAccount(
            id="acc-frozen",
            user_id="user-bob",
            account_number="ACT-FROZEN-03",
            currency="INR",
            balance_minor=50_000_00,
            status="frozen"
        )
        session.add_all([acc1, acc2, acc_frozen])
        await session.commit()
        
        yield session

    await engine.dispose()

@pytest.mark.asyncio
async def test_normal_transfer_allow_and_double_entry(async_db: AsyncSession):
    """Scenario 1: Normal transfer posts atomically with balanced ledger entries."""
    req = TransferCreateRequest(
        source_account_id="acc-alice",
        destination_account_number="ACT-BOB-02",
        amount_minor=5_000_00,  # ₹5,000.00
        currency="INR",
        description="Normal gift transfer",
        idempotency_key=str(uuid.uuid4())
    )

    transfer = await transaction_gateway.initiate_transfer(
        db=async_db,
        req=req,
        current_user_id="user-alice"
    )

    assert transfer.status == TransferStatus.POSTED.value
    assert transfer.policy_decision == PolicyDecision.ALLOW.value
    assert transfer.risk_score < 25.0

    # Verify double-entry balances
    from sqlalchemy.future import select
    acc_alice = (await async_db.execute(select(BankAccount).where(BankAccount.id == "acc-alice"))).scalars().first()
    acc_bob = (await async_db.execute(select(BankAccount).where(BankAccount.id == "acc-bob"))).scalars().first()

    assert acc_alice.balance_minor == 95_000_00
    assert acc_bob.balance_minor == 15_000_00

    # Verify balanced ledger entries (1 DEBIT + 1 CREDIT summing to 0 net)
    entries = (await async_db.execute(select(LedgerEntry).where(LedgerEntry.transaction_id == transfer.id))).scalars().all()
    assert len(entries) == 2
    types = {e.entry_type for e in entries}
    assert types == {"DEBIT", "CREDIT"}
    debit = next(e for e in entries if e.entry_type == "DEBIT")
    credit = next(e for e in entries if e.entry_type == "CREDIT")
    assert debit.amount_minor == 5_000_00
    assert credit.amount_minor == 5_000_00

@pytest.mark.asyncio
async def test_idempotency_deduplication(async_db: AsyncSession):
    """Scenario 2: Duplicate submission with same key returns existing record without double-posting."""
    idem_key = "IDEM-TEST-KEY-001"
    req = TransferCreateRequest(
        source_account_id="acc-alice",
        destination_account_number="ACT-BOB-02",
        amount_minor=2_000_00,
        currency="INR",
        idempotency_key=idem_key
    )

    tx1 = await transaction_gateway.initiate_transfer(async_db, req, "user-alice")
    tx2 = await transaction_gateway.initiate_transfer(async_db, req, "user-alice")

    assert tx1.id == tx2.id

    from sqlalchemy.future import select
    acc_alice = (await async_db.execute(select(BankAccount).where(BankAccount.id == "acc-alice"))).scalars().first()
    # Balance should only have been debited ONCE
    assert acc_alice.balance_minor == 98_000_00

@pytest.mark.asyncio
async def test_insufficient_balance_rejection(async_db: AsyncSession):
    """Scenario 3: Overspending attempts are rejected before risk assessment or ledger mutation."""
    req = TransferCreateRequest(
        source_account_id="acc-alice",
        destination_account_number="ACT-BOB-02",
        amount_minor=999_999_00,  # exceeds balance
        currency="INR",
        idempotency_key=str(uuid.uuid4())
    )

    with pytest.raises(HTTPException) as exc:
        await transaction_gateway.initiate_transfer(async_db, req, "user-alice")
    assert exc.value.status_code == 400
    assert "Insufficient" in exc.value.detail

@pytest.mark.asyncio
async def test_high_amount_triggers_verification_challenge(async_db: AsyncSession):
    """Scenario 4: Elevated transfer amount requires mock step-up verification."""
    # Give Alice more funds to trigger 2,50,000 INR transfer
    from sqlalchemy.future import select
    acc_alice = (await async_db.execute(select(BankAccount).where(BankAccount.id == "acc-alice"))).scalars().first()
    acc_alice.balance_minor = 500_000_00
    await async_db.commit()

    req = TransferCreateRequest(
        source_account_id="acc-alice",
        destination_account_number="ACT-BOB-02",
        amount_minor=250_000_00,  # ₹2,50,000.00 (triggers ELEVATED_TRANSFER_AMOUNT)
        currency="INR",
        idempotency_key=str(uuid.uuid4())
    )

    tx = await transaction_gateway.initiate_transfer(async_db, req, "user-alice")
    assert tx.status == TransferStatus.AWAITING_VERIFICATION.value
    assert tx.policy_decision == PolicyDecision.VERIFY.value

    # Balance must NOT be deducted yet
    acc_alice_check = (await async_db.execute(select(BankAccount).where(BankAccount.id == "acc-alice"))).scalars().first()
    assert acc_alice_check.balance_minor == 500_000_00

    # Retrieve challenge and verify
    chal = (await async_db.execute(select(VerificationChallenge).where(VerificationChallenge.transfer_id == tx.id))).scalars().first()
    assert chal is not None

    # Complete verification
    verified_tx = await transaction_gateway.verify_challenge(
        db=async_db,
        transfer_id=tx.id,
        code=chal.expected_code,
        current_user_id="user-alice"
    )
    assert verified_tx.status == TransferStatus.POSTED.value

    # Balance should now be deducted
    acc_alice_posted = (await async_db.execute(select(BankAccount).where(BankAccount.id == "acc-alice"))).scalars().first()
    assert acc_alice_posted.balance_minor == 250_000_00

@pytest.mark.asyncio
async def test_blocked_transfer_to_restricted_account(async_db: AsyncSession):
    """Scenario 5: Transfer to frozen destination is BLOCKED and generates SOC alert."""
    req = TransferCreateRequest(
        source_account_id="acc-alice",
        destination_account_number="ACT-FROZEN-03",
        amount_minor=1_000_00,
        currency="INR",
        idempotency_key=str(uuid.uuid4())
    )

    tx = await transaction_gateway.initiate_transfer(async_db, req, "user-alice")
    assert tx.status == TransferStatus.BLOCKED.value
    assert tx.policy_decision == PolicyDecision.BLOCK.value
    assert "DESTINATION_ACCOUNT_RESTRICTED" in tx.reason_codes

    # Balances unaltered
    from sqlalchemy.future import select
    acc_alice = (await async_db.execute(select(BankAccount).where(BankAccount.id == "acc-alice"))).scalars().first()
    assert acc_alice.balance_minor == 100_000_00

@pytest.mark.asyncio
async def test_critical_amount_triggers_hold(async_db: AsyncSession):
    """Scenario 6: Critical transfer amount exceeding threshold triggers HELD status."""
    from sqlalchemy.future import select
    acc_alice = (await async_db.execute(select(BankAccount).where(BankAccount.id == "acc-alice"))).scalars().first()
    acc_alice.balance_minor = 10_000_000_00 # 10,00,000 INR
    await async_db.commit()

    req = TransferCreateRequest(
        source_account_id="acc-alice",
        destination_account_number="ACT-BOB-02",
        amount_minor=600_000_00,  # ₹6,00,000.00 (critical threshold > 5,00,000)
        currency="INR",
        idempotency_key=str(uuid.uuid4())
    )

    tx = await transaction_gateway.initiate_transfer(async_db, req, "user-alice")
    assert tx.status == TransferStatus.HELD.value
    assert tx.policy_decision == PolicyDecision.HOLD.value
    assert "CRITICAL_AMOUNT_THRESHOLD" in tx.reason_codes

    # Ensure funds were not deducted
    acc_alice_check = (await async_db.execute(select(BankAccount).where(BankAccount.id == "acc-alice"))).scalars().first()
    assert acc_alice_check.balance_minor == 10_000_000_00

@pytest.mark.asyncio
async def test_invalid_verification_code_rejected(async_db: AsyncSession):
    """Scenario 7: Incorrect OTP code is rejected and transfer stays in AWAITING_VERIFICATION."""
    from sqlalchemy.future import select
    acc_alice = (await async_db.execute(select(BankAccount).where(BankAccount.id == "acc-alice"))).scalars().first()
    acc_alice.balance_minor = 500_000_00
    await async_db.commit()

    req = TransferCreateRequest(
        source_account_id="acc-alice",
        destination_account_number="ACT-BOB-02",
        amount_minor=250_000_00,
        currency="INR",
        idempotency_key=str(uuid.uuid4())
    )

    tx = await transaction_gateway.initiate_transfer(async_db, req, "user-alice")
    assert tx.status == TransferStatus.AWAITING_VERIFICATION.value

    with pytest.raises(HTTPException) as exc:
        await transaction_gateway.verify_challenge(
            db=async_db,
            transfer_id=tx.id,
            code="000000",
            current_user_id="user-alice"
        )
    assert exc.value.status_code == 400
    assert "Invalid verification code" in exc.value.detail

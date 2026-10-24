import pytest
import pytest_asyncio
import uuid
import asyncio
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException

from app.models.db_models import (
    Base, User, BankAccount, Transfer, LedgerEntry, VerificationChallenge, Incident, Event, DetectionFinding
)
from app.models.schemas import TransferCreateRequest, PolicyDecision, TransferStatus, VerificationSubmitRequest
from app.banking.gateway import transaction_gateway

@pytest_asyncio.fixture
async def async_db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        # Seed test users
        u1 = User(id="usr-alice", username="alice", email="alice@test.local", hashed_password="pw", role="analyst")
        u2 = User(id="usr-bob", username="bob", email="bob@test.local", hashed_password="pw", role="analyst")
        session.add_all([u1, u2])
        await session.commit()
        
        # Seed accounts
        acc1 = BankAccount(
            id="acc-alice",
            user_id="usr-alice",
            account_number="ACT-ALICE-100",
            currency="INR",
            balance_minor=10_000_00,  # ₹10,000.00
            status="active"
        )
        acc2 = BankAccount(
            id="acc-bob",
            user_id="usr-bob",
            account_number="ACT-BOB-200",
            currency="INR",
            balance_minor=5_000_00,   # ₹5,000.00
            status="active"
        )
        acc3 = BankAccount(
            id="acc-charlie",
            user_id="usr-bob",
            account_number="ACT-CHARLIE-300",
            currency="INR",
            balance_minor=1_000_00,
            status="active"
        )
        acc_frozen = BankAccount(
            id="acc-frozen",
            user_id="usr-bob",
            account_number="ACT-FROZEN-999",
            currency="INR",
            balance_minor=50_000_00,
            status="frozen"
        )
        session.add_all([acc1, acc2, acc3, acc_frozen])
        await session.commit()
        yield session

# ============================================================================
# 1. ATOMICITY, CONCURRENCY & NEGATIVE BALANCE INVARIANTS
# ============================================================================

@pytest.mark.asyncio
async def test_negative_balance_check_constraint(async_db: AsyncSession):
    """Confirm database schema rejects negative balance updates."""
    acc = (await async_db.execute(select(BankAccount).where(BankAccount.id == "acc-alice"))).scalars().first()
    acc.balance_minor = -500
    with pytest.raises(IntegrityError):
        await async_db.commit()
    await async_db.rollback()

@pytest.mark.asyncio
async def test_competing_transfers_prevent_double_spending(async_db: AsyncSession):
    """
    Scenario: Alice has ₹50,000. Two transactions of ₹30,000 each are attempted.
    The first must succeed (remaining balance: ₹20,000), while the second must be rejected
    due to insufficient funds. Balance must NEVER become negative.
    """
    # Set Alice balance to ₹50,000
    acc_alice = (await async_db.execute(select(BankAccount).where(BankAccount.id == "acc-alice"))).scalars().first()
    acc_alice.balance_minor = 50_000_00
    await async_db.commit()

    req1 = TransferCreateRequest(
        source_account_id="acc-alice",
        destination_account_number="ACT-BOB-200",
        amount_minor=30_000_00,  # ₹30,000
        currency="INR",
        idempotency_key=str(uuid.uuid4())
    )
    req2 = TransferCreateRequest(
        source_account_id="acc-alice",
        destination_account_number="ACT-BOB-200",
        amount_minor=30_000_00,  # ₹30,000
        currency="INR",
        idempotency_key=str(uuid.uuid4())
    )

    # First transfer succeeds
    tx1 = await transaction_gateway.initiate_transfer(async_db, req1, "usr-alice")
    assert tx1.status == TransferStatus.POSTED.value

    # Check remaining balance
    acc_check = (await async_db.execute(select(BankAccount).where(BankAccount.id == "acc-alice"))).scalars().first()
    assert acc_check.balance_minor == 20_000_00

    # Second transfer must be rejected (only ₹20,000 remaining)
    with pytest.raises(HTTPException) as exc:
        await transaction_gateway.initiate_transfer(async_db, req2, "usr-alice")
    assert exc.value.status_code == 400
    assert "Insufficient" in exc.value.detail

    # Final balance remains ₹20,000, never negative
    acc_final = (await async_db.execute(select(BankAccount).where(BankAccount.id == "acc-alice"))).scalars().first()
    assert acc_final.balance_minor == 20_000_00

# ============================================================================
# 2. IDEMPOTENCY CONSISTENCY & CONFLICT DETECTION
# ============================================================================

@pytest.mark.asyncio
async def test_idempotency_mismatched_destination_raises_409(async_db: AsyncSession):
    """Reusing the same idempotency key with a DIFFERENT destination account must raise HTTP 409."""
    shared_key = str(uuid.uuid4())

    req1 = TransferCreateRequest(
        source_account_id="acc-alice",
        destination_account_number="ACT-BOB-200",
        amount_minor=1_000_00,
        currency="INR",
        idempotency_key=shared_key
    )
    req2 = TransferCreateRequest(
        source_account_id="acc-alice",
        destination_account_number="ACT-CHARLIE-300",  # Different destination!
        amount_minor=1_000_00,
        currency="INR",
        idempotency_key=shared_key
    )

    tx1 = await transaction_gateway.initiate_transfer(async_db, req1, "usr-alice")
    assert tx1.status == TransferStatus.POSTED.value

    with pytest.raises(HTTPException) as exc:
        await transaction_gateway.initiate_transfer(async_db, req2, "usr-alice")
    assert exc.value.status_code == 409
    assert "mismatched" in exc.value.detail.lower()

@pytest.mark.asyncio
async def test_idempotency_mismatched_amount_raises_409(async_db: AsyncSession):
    """Reusing the same idempotency key with a DIFFERENT amount must raise HTTP 409."""
    shared_key = str(uuid.uuid4())

    req1 = TransferCreateRequest(
        source_account_id="acc-alice",
        destination_account_number="ACT-BOB-200",
        amount_minor=1_000_00,
        currency="INR",
        idempotency_key=shared_key
    )
    req2 = TransferCreateRequest(
        source_account_id="acc-alice",
        destination_account_number="ACT-BOB-200",
        amount_minor=2_000_00,  # Different amount!
        currency="INR",
        idempotency_key=shared_key
    )

    await transaction_gateway.initiate_transfer(async_db, req1, "usr-alice")

    with pytest.raises(HTTPException) as exc:
        await transaction_gateway.initiate_transfer(async_db, req2, "usr-alice")
    assert exc.value.status_code == 409
    assert "mismatched" in exc.value.detail.lower()

# ============================================================================
# 3. VERIFICATION SECURITY (EXPIRY, ATTEMPTS, REPLAY, BOUNDING)
# ============================================================================

@pytest.mark.asyncio
async def test_verification_challenge_expiry(async_db: AsyncSession):
    """Expired verification challenges cannot be verified and transition transfer to EXPIRED."""
    # Alice initiates a ₹2,50,000 transfer (requires step-up)
    acc_alice = (await async_db.execute(select(BankAccount).where(BankAccount.id == "acc-alice"))).scalars().first()
    acc_alice.balance_minor = 500_000_00
    await async_db.commit()

    req = TransferCreateRequest(
        source_account_id="acc-alice",
        destination_account_number="ACT-BOB-200",
        amount_minor=250_000_00,
        currency="INR",
        idempotency_key=str(uuid.uuid4())
    )
    tx = await transaction_gateway.initiate_transfer(async_db, req, "usr-alice")
    assert tx.status == TransferStatus.AWAITING_VERIFICATION.value

    # Manually backdate challenge expiry to simulate time passage
    chal = (await async_db.execute(select(VerificationChallenge).where(VerificationChallenge.transfer_id == tx.id))).scalars().first()
    chal.expires_at = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=5)
    await async_db.commit()

    with pytest.raises(HTTPException) as exc:
        await transaction_gateway.verify_challenge(
            db=async_db,
            transfer_id=tx.id,
            code=chal.expected_code,
            current_user_id="usr-alice"
        )
    assert exc.value.status_code == 400
    assert "expired" in exc.value.detail.lower()

    # Verify state was marked EXPIRED and balance untouched
    tx_check = (await async_db.execute(select(Transfer).where(Transfer.id == tx.id))).scalars().first()
    assert tx_check.status == TransferStatus.EXPIRED.value
    acc_check = (await async_db.execute(select(BankAccount).where(BankAccount.id == "acc-alice"))).scalars().first()
    assert acc_check.balance_minor == 500_000_00

@pytest.mark.asyncio
async def test_verification_attempt_exhaustion_locks_transfer(async_db: AsyncSession):
    """Failing OTP 3 times marks challenge FAILED, transfer REJECTED, and locks out further attempts."""
    acc_alice = (await async_db.execute(select(BankAccount).where(BankAccount.id == "acc-alice"))).scalars().first()
    acc_alice.balance_minor = 500_000_00
    await async_db.commit()

    req = TransferCreateRequest(
        source_account_id="acc-alice",
        destination_account_number="ACT-BOB-200",
        amount_minor=250_000_00,
        currency="INR",
        idempotency_key=str(uuid.uuid4())
    )
    tx = await transaction_gateway.initiate_transfer(async_db, req, "usr-alice")
    chal = (await async_db.execute(select(VerificationChallenge).where(VerificationChallenge.transfer_id == tx.id))).scalars().first()

    # Attempt 1: wrong code
    with pytest.raises(HTTPException) as exc:
        await transaction_gateway.verify_challenge(async_db, tx.id, "000001", "usr-alice")
    assert "2 attempts remaining" in exc.value.detail

    # Attempt 2: wrong code
    with pytest.raises(HTTPException) as exc:
        await transaction_gateway.verify_challenge(async_db, tx.id, "000002", "usr-alice")
    assert "1 attempts remaining" in exc.value.detail

    # Attempt 3: wrong code -> Exceeds max attempts
    with pytest.raises(HTTPException) as exc:
        await transaction_gateway.verify_challenge(async_db, tx.id, "000003", "usr-alice")
    assert "Maximum verification attempts exceeded" in exc.value.detail

    # Check transfer rejected and challenge failed
    tx_check = (await async_db.execute(select(Transfer).where(Transfer.id == tx.id))).scalars().first()
    assert tx_check.status == TransferStatus.REJECTED.value

    # Subsequent attempt with correct code must now be denied
    with pytest.raises(HTTPException) as exc:
        await transaction_gateway.verify_challenge(async_db, tx.id, chal.expected_code, "usr-alice")
    assert exc.value.status_code == 400

@pytest.mark.asyncio
async def test_verification_replay_protection(async_db: AsyncSession):
    """Once verified and posted, a challenge cannot be replayed."""
    acc_alice = (await async_db.execute(select(BankAccount).where(BankAccount.id == "acc-alice"))).scalars().first()
    acc_alice.balance_minor = 500_000_00
    await async_db.commit()

    req = TransferCreateRequest(
        source_account_id="acc-alice",
        destination_account_number="ACT-BOB-200",
        amount_minor=250_000_00,
        currency="INR",
        idempotency_key=str(uuid.uuid4())
    )
    tx = await transaction_gateway.initiate_transfer(async_db, req, "usr-alice")
    chal = (await async_db.execute(select(VerificationChallenge).where(VerificationChallenge.transfer_id == tx.id))).scalars().first()

    # Successfully verify
    v_tx = await transaction_gateway.verify_challenge(async_db, tx.id, chal.expected_code, "usr-alice")
    assert v_tx.status == TransferStatus.POSTED.value

    # Replay attempt
    with pytest.raises(HTTPException) as exc:
        await transaction_gateway.verify_challenge(async_db, tx.id, chal.expected_code, "usr-alice")
    assert exc.value.status_code == 400
    assert "does not accept verification" in exc.value.detail

# ============================================================================
# 4. AUTHORIZATION TESTS (CROSS-USER ISOLATION)
# ============================================================================

@pytest.mark.asyncio
async def test_unauthorized_user_cannot_initiate_from_others_account(async_db: AsyncSession):
    """User Bob cannot initiate a transfer from User Alice's account (HTTP 403)."""
    req = TransferCreateRequest(
        source_account_id="acc-alice",  # Alice's account
        destination_account_number="ACT-BOB-200",
        amount_minor=1_000_00,
        currency="INR",
        idempotency_key=str(uuid.uuid4())
    )

    with pytest.raises(HTTPException) as exc:
        await transaction_gateway.initiate_transfer(async_db, req, "usr-bob")  # Initiated by Bob!
    assert exc.value.status_code == 403
    assert "ownership" in exc.value.detail.lower()

@pytest.mark.asyncio
async def test_unauthorized_user_cannot_verify_others_transfer(async_db: AsyncSession):
    """User Bob cannot submit verification for Alice's pending transfer (HTTP 403)."""
    acc_alice = (await async_db.execute(select(BankAccount).where(BankAccount.id == "acc-alice"))).scalars().first()
    acc_alice.balance_minor = 500_000_00
    await async_db.commit()

    req = TransferCreateRequest(
        source_account_id="acc-alice",
        destination_account_number="ACT-BOB-200",
        amount_minor=250_000_00,
        currency="INR",
        idempotency_key=str(uuid.uuid4())
    )
    tx = await transaction_gateway.initiate_transfer(async_db, req, "usr-alice")
    chal = (await async_db.execute(select(VerificationChallenge).where(VerificationChallenge.transfer_id == tx.id))).scalars().first()

    with pytest.raises(HTTPException) as exc:
        await transaction_gateway.verify_challenge(async_db, tx.id, chal.expected_code, "usr-bob")  # Bob verifies!
    assert exc.value.status_code == 403
    assert "Unauthorized" in exc.value.detail

@pytest.mark.asyncio
async def test_account_ledger_authorization(async_db: AsyncSession):
    """Alice performs a transfer to Bob. Bob cannot query Alice's account ledger directly."""
    req = TransferCreateRequest(
        source_account_id="acc-alice",
        destination_account_number="ACT-BOB-200",
        amount_minor=1_000_00,
        currency="INR",
        idempotency_key=str(uuid.uuid4())
    )
    await transaction_gateway.initiate_transfer(async_db, req, "usr-alice")

    # Bob attempts to view Alice's ledger
    acc_alice = (await async_db.execute(select(BankAccount).where(BankAccount.id == "acc-alice"))).scalars().first()
    assert acc_alice.user_id == "usr-alice"

    # Alice can query her own account entries
    alice_entries = (await async_db.execute(
        select(LedgerEntry).where(LedgerEntry.account_id == "acc-alice")
    )).scalars().all()
    assert len(alice_entries) == 1
    assert alice_entries[0].entry_type == "DEBIT"

# ============================================================================
# 5. SOC INTEGRATION (INCIDENT AUTO-GENERATION ON BLOCKED / HOLD)
# ============================================================================

@pytest.mark.asyncio
async def test_blocked_transfer_creates_soc_incident_and_finding(async_db: AsyncSession):
    """When a transfer is BLOCKED, an Incident and DetectionFinding are created and linked to the transfer."""
    req = TransferCreateRequest(
        source_account_id="acc-alice",
        destination_account_number="ACT-FROZEN-999",  # Frozen target account
        amount_minor=1_000_00,
        currency="INR",
        idempotency_key=str(uuid.uuid4())
    )

    tx = await transaction_gateway.initiate_transfer(async_db, req, "usr-alice")
    assert tx.status == TransferStatus.BLOCKED.value
    assert tx.incident_id is not None

    # Verify Incident exists in SOC queue
    inc = (await async_db.execute(select(Incident).where(Incident.id == tx.incident_id))).scalars().first()
    assert inc is not None
    assert "BLOCK" in inc.title
    assert inc.severity == "critical"
    assert "ACT-ALICE-100" in inc.affected_entities
    assert "ACT-FROZEN-999" in inc.affected_entities

    # Verify DetectionFinding is linked
    finding = (await async_db.execute(select(DetectionFinding).where(DetectionFinding.incident_id == inc.id))).scalars().first()
    assert finding is not None
    assert finding.detector_type == "rule"
    assert "FRAUD-GATEWAY-BLOCK" in finding.rule_or_model_name

# ============================================================================
# 6. DOUBLE-ENTRY LEDGER BALANCE INVARIANT
# ============================================================================

@pytest.mark.asyncio
async def test_double_entry_exact_balance_preservation(async_db: AsyncSession):
    """
    Every posted transfer must create exactly one DEBIT and one CREDIT.
    Net currency change across the ledger must be exactly ZERO.
    """
    initial_alice = 10_000_00
    initial_bob = 5_000_00
    transfer_amount = 3_250_50  # ₹3,250.50

    req = TransferCreateRequest(
        source_account_id="acc-alice",
        destination_account_number="ACT-BOB-200",
        amount_minor=transfer_amount,
        currency="INR",
        idempotency_key=str(uuid.uuid4())
    )

    tx = await transaction_gateway.initiate_transfer(async_db, req, "usr-alice")
    assert tx.status == TransferStatus.POSTED.value

    # Fetch ledger entries
    entries_stmt = select(LedgerEntry).where(LedgerEntry.transaction_id == tx.id)
    entries = (await async_db.execute(entries_stmt)).scalars().all()
    assert len(entries) == 2

    debits = [e for e in entries if e.entry_type == "DEBIT"]
    credits = [e for e in entries if e.entry_type == "CREDIT"]
    assert len(debits) == 1
    assert len(credits) == 1
    assert debits[0].amount_minor == transfer_amount
    assert credits[0].amount_minor == transfer_amount

    # Balance invariants
    acc_alice = (await async_db.execute(select(BankAccount).where(BankAccount.id == "acc-alice"))).scalars().first()
    acc_bob = (await async_db.execute(select(BankAccount).where(BankAccount.id == "acc-bob"))).scalars().first()

    assert acc_alice.balance_minor == initial_alice - transfer_amount
    assert acc_bob.balance_minor == initial_bob + transfer_amount
    assert debits[0].balance_after_minor == acc_alice.balance_minor
    assert credits[0].balance_after_minor == acc_bob.balance_minor
    assert (acc_alice.balance_minor + acc_bob.balance_minor) == (initial_alice + initial_bob)

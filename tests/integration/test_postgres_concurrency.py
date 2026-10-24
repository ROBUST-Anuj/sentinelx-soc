import pytest
import pytest_asyncio
import os
import uuid
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException

from app.models.db_models import Base, User, BankAccount, Transfer, LedgerEntry
from app.models.schemas import TransferCreateRequest, TransferStatus
from app.banking.gateway import transaction_gateway

PG_TEST_URL = os.getenv(
    "TEST_POSTGRES_URL",
    "postgresql+asyncpg://postgres:SecureDbPass2026!@db.qolljpkbvsxhqszevweu.supabase.co:5432/postgres"
)

@pytest_asyncio.fixture
async def pg_db_session():
    """Connect to live PostgreSQL, create tables if missing, seed test accounts, and clean up."""
    try:
        engine = create_async_engine(PG_TEST_URL, echo=False)
    except Exception as e:
        pytest.skip(f"PostgreSQL connection unavailable: {e}")

    SessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    
    unique_suffix = str(uuid.uuid4())[:8]
    user_id = f"usr-pg-{unique_suffix}"
    src_id = f"acc-pg-src-{unique_suffix}"
    dst_id = f"acc-pg-dst-{unique_suffix}"
    src_acc_num = f"PG-SRC-{unique_suffix}"
    dst_acc_num = f"PG-DST-{unique_suffix}"

    async with SessionLocal() as session:
        # Create user
        u = User(id=user_id, username=f"pg_user_{unique_suffix}", email=f"pg_{unique_suffix}@test.local", hashed_password="pw", role="analyst")
        session.add(u)
        
        # Create accounts: Source has ₹50,000.00
        src = BankAccount(
            id=src_id,
            user_id=user_id,
            account_number=src_acc_num,
            currency="INR",
            balance_minor=50_000_00,  # ₹50,000.00
            status="active"
        )
        dst = BankAccount(
            id=dst_id,
            user_id=user_id,
            account_number=dst_acc_num,
            currency="INR",
            balance_minor=0,
            status="active"
        )
        session.add_all([src, dst])
        await session.commit()

    yield {
        "engine": engine,
        "session_maker": SessionLocal,
        "user_id": user_id,
        "src_id": src_id,
        "dst_id": dst_id,
        "src_acc_num": src_acc_num,
        "dst_acc_num": dst_acc_num
    }

    # Clean up test data
    try:
        async with SessionLocal() as session:
            # Delete transfers and ledgers for these accounts
            txs = (await session.execute(select(Transfer).where(Transfer.source_account_id == src_id))).scalars().all()
            for t in txs:
                await session.delete(t)
            accs = (await session.execute(select(BankAccount).where(BankAccount.id.in_([src_id, dst_id])))).scalars().all()
            for a in accs:
                await session.delete(a)
            usr = (await session.execute(select(User).where(User.id == user_id))).scalars().first()
            if usr:
                await session.delete(usr)
            await session.commit()
        await engine.dispose()
    except Exception:
        pass

@pytest.mark.asyncio
async def test_postgresql_concurrent_competing_transfers(pg_db_session):
    """
    Simulate two concurrent competing transfer requests against PostgreSQL:
    Initial Balance: ₹50,000.00
    Request 1: ₹30,000.00
    Request 2: ₹30,000.00
    Total requested: ₹60,000.00 > ₹50,000.00.
    With PostgreSQL row-level locking (with_for_update), exactly one must succeed,
    the other must be rejected for insufficient funds, and balance must NEVER go negative.
    """
    sm = pg_db_session["session_maker"]
    user_id = pg_db_session["user_id"]
    src_id = pg_db_session["src_id"]
    dst_acc_num = pg_db_session["dst_acc_num"]

    req1 = TransferCreateRequest(
        source_account_id=src_id,
        destination_account_number=dst_acc_num,
        amount_minor=30_000_00,
        currency="INR",
        idempotency_key=str(uuid.uuid4())
    )
    req2 = TransferCreateRequest(
        source_account_id=src_id,
        destination_account_number=dst_acc_num,
        amount_minor=30_000_00,
        currency="INR",
        idempotency_key=str(uuid.uuid4())
    )

    results = []

    async def execute_transfer(req):
        async with sm() as s:
            try:
                tx = await transaction_gateway.initiate_transfer(s, req, user_id)
                results.append(("SUCCESS", tx.status))
            except HTTPException as e:
                results.append(("ERROR", e.status_code, e.detail))
            except Exception as e:
                results.append(("FATAL", type(e).__name__, str(e)))

    # Execute both concurrently via asyncio.gather on real PostgreSQL connections
    await asyncio.gather(
        execute_transfer(req1),
        execute_transfer(req2),
        return_exceptions=False
    )

    successes = [r for r in results if r[0] == "SUCCESS"]
    errors = [r for r in results if r[0] == "ERROR"]

    # Exactly one succeeded and one rejected
    assert len(successes) == 1, f"Expected 1 success, got {len(successes)}: {results}"
    assert len(errors) == 1, f"Expected 1 error, got {len(errors)}: {results}"
    assert errors[0][1] == 400
    assert "Insufficient" in errors[0][2]

    # Verify final balance in PostgreSQL
    async with sm() as s:
        src = (await s.execute(select(BankAccount).where(BankAccount.id == src_id))).scalars().first()
        assert src.balance_minor == 20_000_00  # ₹50,000 - ₹30,000 = ₹20,000. Never negative.

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.future import select

from app.main import app
from app.models.db_models import (
    Base, User, BankAccount, Transfer, Incident, ResponsePlaybookAction, AuditLog
)
from app.core.database import get_db
from app.core.security import create_access_token

@pytest_asyncio.fixture
async def orchestration_env():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    
    # Pre-seed analyst user and target bank account
    async with session_factory() as session:
        u_analyst = User(
            id="usr-analyst-1",
            username="analyst_soc",
            email="analyst@soc.local",
            hashed_password="pw",
            role="analyst",
            is_active=True
        )
        u_readonly = User(
            id="usr-readonly-1",
            username="readonly_user",
            email="readonly@soc.local",
            hashed_password="pw",
            role="readonly",
            is_active=True
        )
        session.add_all([u_analyst, u_readonly])

        # Target account for containment testing
        target_acc = BankAccount(
            id="acc-target-beneficiary",
            user_id="usr-analyst-1",
            account_number="ACT-SYNTH-9999",
            currency="INR",
            balance_minor=500_000_00,
            status="active"
        )
        session.add(target_acc)

        # Pre-seed an incident
        inc = Incident(
            id="inc-test-ato-100",
            title="[DEMO SIMULATION] Account Takeover Sequence (Customer: cust-101)",
            summary="Multi-stage ATO sequence detected.",
            severity="critical",
            status="new",
            assigned_to="tier1_analyst",
            affected_entities=["cust-101", "sess-compromised-123", "ACT-SYNTH-9999"],
            graph_risk_score=85.0
        )
        session.add(inc)
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
async def test_playbook_generation_approval_and_enforcement(orchestration_env):
    """
    Verifies the end-to-end Response Orchestration pipeline:
    1. Automated Playbook Action Generation for ATO Incident.
    2. Approval Authorization Controls (Readonly user rejected, Analyst authorized).
    3. Live Containment Enforcement against NexaBank (Session Revocation & Beneficiary Suspension).
    4. Duplicate execution prevention (409 Conflict).
    5. Containment status progression on parent Incident (Transitions to 'contained').
    6. Rollback / Compensation verification.
    """
    client, session_factory = orchestration_env
    token_analyst = create_access_token(data={"sub": "analyst_soc"})
    token_readonly = create_access_token(data={"sub": "readonly_user"})

    headers_analyst = {"Authorization": f"Bearer {token_analyst}"}
    headers_readonly = {"Authorization": f"Bearer {token_readonly}"}

    # 1. Generate Playbook Actions
    gen_resp = await client.post("/api/banking/orchestration/actions/generate/inc-test-ato-100", headers=headers_analyst)
    assert gen_resp.status_code == 200
    actions = gen_resp.json()
    assert len(actions) >= 1
    action_ato = actions[0]
    action_id = action_ato["action_id"]

    # 2. Authorization Check: Readonly user cannot approve action
    rej_resp = await client.post(
        f"/api/banking/orchestration/actions/{action_id}/decision",
        json={"decision": "APPROVE"},
        headers=headers_readonly
    )
    assert rej_resp.status_code == 403

    # 3. Analyst Approves Action
    appr_resp = await client.post(
        f"/api/banking/orchestration/actions/{action_id}/decision",
        json={"decision": "APPROVE", "analyst_notes": "Revoking session to contain credential leakage."},
        headers=headers_analyst
    )
    assert appr_resp.status_code == 200
    appr_data = appr_resp.json()
    assert appr_data["status"] == "EXECUTED"
    assert appr_data["approved_by"] == "analyst_soc"
    assert appr_data["rollback_token"] is not None

    # 4. Duplicate Approval Prevention: Attempting to approve again returns 409 Conflict
    dup_resp = await client.post(
        f"/api/banking/orchestration/actions/{action_id}/decision",
        json={"decision": "APPROVE"},
        headers=headers_analyst
    )
    assert dup_resp.status_code == 409

    # 5. Parent Incident Status Transitioned to 'contained'
    async with session_factory() as session:
        inc = (await session.execute(select(Incident).where(Incident.id == "inc-test-ato-100"))).scalars().first()
        assert inc.status == "contained"

    # 6. Test Rollback Procedure
    roll_resp = await client.post(
        f"/api/banking/orchestration/actions/{action_id}/decision",
        json={"decision": "ROLLBACK", "analyst_notes": "Containment verified and compensation complete."},
        headers=headers_analyst
    )
    assert roll_resp.status_code == 200
    assert roll_resp.json()["status"] == "ROLLED_BACK"

@pytest.mark.asyncio
async def test_direct_containment_enforcement_beneficiary_restriction(orchestration_env):
    """
    Directly tests NexaBank Core enforcement endpoint:
    Suspends a target beneficiary account and checks database persistence and audit log.
    """
    client, session_factory = orchestration_env
    from app.core.config import settings

    payload = {
        "incident_id": "inc-test-ato-100",
        "action_id": "act-enforce-test-01",
        "action_type": "RESTRICT_BENEFICIARY",
        "target_entity": "ACT-SYNTH-9999",
        "approved_by": "analyst_soc",
        "idempotency_key": "idemp-contain-001"
    }

    # Call enforcement endpoint with service auth
    resp = await client.post(
        "/internal/v1/enforce-containment",
        json=payload,
        headers={"X-Service-Auth": settings.INTERNAL_SERVICE_KEY}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["status"] == "EXECUTED"

    # Verify target bank account in DB has been suspended
    async with session_factory() as session:
        acc = (await session.execute(
            select(BankAccount).where(BankAccount.account_number == "ACT-SYNTH-9999")
        )).scalars().first()
        assert acc.status == "suspended"

        # Verify audit log
        audit = (await session.execute(
            select(AuditLog).where(AuditLog.resource_id == "act-enforce-test-01")
        )).scalars().first()
        assert audit is not None
        assert "RESTRICT_BENEFICIARY" in audit.action

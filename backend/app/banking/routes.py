"""
Banking Simulation API Routes.
Exposes account overview, synthetic transfer initiation, step-up verification challenge,
and ledger/audit transaction history.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional

from app.core.config import settings
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.db_models import User, BankAccount, Transfer, LedgerEntry, VerificationChallenge
from app.models.schemas import (
    BankAccountResponse, TransferCreateRequest, TransferResponse,
    VerificationSubmitRequest, RiskAssessmentResponse, LedgerEntryResponse
)
from app.banking.gateway import transaction_gateway

banking_router = APIRouter(prefix="/banking", tags=["Banking Simulation & Fraud Gateway"])

def format_currency(minor_units: int, currency: str = "INR") -> str:
    amount = minor_units / 100.0
    if currency == "INR":
        return f"₹{amount:,.2f}"
    elif currency == "USD":
        return f"${amount:,.2f}"
    return f"{amount:,.2f} {currency}"

@banking_router.get("/accounts", response_model=List[BankAccountResponse])
async def list_user_accounts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all synthetic accounts owned by the authenticated user."""
    stmt = select(BankAccount).where(BankAccount.user_id == current_user.id)
    res = await db.execute(stmt)
    accounts = res.scalars().all()

    response = []
    for acc in accounts:
        response.append(BankAccountResponse(
            id=acc.id,
            user_id=acc.user_id,
            account_number=acc.account_number,
            account_type=acc.account_type,
            currency=acc.currency,
            balance_minor=acc.balance_minor,
            balance_formatted=format_currency(acc.balance_minor, acc.currency),
            status=acc.status,
            is_synthetic=acc.is_synthetic,
            created_at=acc.created_at
        ))
    return response

@banking_router.get("/accounts/{account_id}", response_model=BankAccountResponse)
async def get_account_detail(
    account_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve details and available balance for a specific synthetic account."""
    stmt = select(BankAccount).where(BankAccount.id == account_id)
    res = await db.execute(stmt)
    acc = res.scalars().first()

    if not acc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found.")

    if acc.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    return BankAccountResponse(
        id=acc.id,
        user_id=acc.user_id,
        account_number=acc.account_number,
        account_type=acc.account_type,
        currency=acc.currency,
        balance_minor=acc.balance_minor,
        balance_formatted=format_currency(acc.balance_minor, acc.currency),
        status=acc.status,
        is_synthetic=acc.is_synthetic,
        created_at=acc.created_at
    )

@banking_router.get("/accounts/{account_id}/ledger", response_model=List[LedgerEntryResponse])
async def get_account_ledger(
    account_id: str,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve double-entry ledger history for an authorized account."""
    acc_stmt = select(BankAccount).where(BankAccount.id == account_id)
    acc = (await db.execute(acc_stmt)).scalars().first()
    if not acc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found.")

    if acc.user_id != current_user.id and current_user.role not in ["admin", "analyst"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    ledger_stmt = (
        select(LedgerEntry)
        .where(LedgerEntry.account_id == account_id)
        .order_by(LedgerEntry.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    entries = (await db.execute(ledger_stmt)).scalars().all()
    return [
        LedgerEntryResponse(
            id=e.id,
            transaction_id=e.transaction_id,
            account_id=e.account_id,
            entry_type=e.entry_type,
            amount_minor=e.amount_minor,
            currency=e.currency,
            balance_after_minor=e.balance_after_minor,
            description=e.description,
            created_at=e.created_at
        )
        for e in entries
    ]

@banking_router.post("/transfers", response_model=TransferResponse)
async def initiate_transfer(
    req: TransferCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Submit a simulated bank transfer through the pre-transaction security gateway.
    Evaluates fraud risk, enforces policy (ALLOW, VERIFY, HOLD, BLOCK), and executes atomic ledger posting.
    """
    client_ip = request.client.host if request.client else "127.0.0.1"
    transfer = await transaction_gateway.initiate_transfer(
        db=db,
        req=req,
        current_user_id=current_user.id,
        client_ip=client_ip
    )

    # Expose challenge code ONLY if running in non-production simulation/demo mode
    chal_stmt = select(VerificationChallenge).where(VerificationChallenge.transfer_id == transfer.id)
    chal_res = await db.execute(chal_stmt)
    chal = chal_res.scalars().first()

    allow_demo_code = (settings.ENVIRONMENT != "production")
    mock_code = chal.expected_code if (chal and chal.status == "PENDING" and allow_demo_code) else None

    return TransferResponse(
        id=transfer.id,
        idempotency_key=transfer.idempotency_key,
        source_account_id=transfer.source_account_id,
        destination_account_id=transfer.destination_account_id,
        amount_minor=transfer.amount_minor,
        amount_formatted=format_currency(transfer.amount_minor, transfer.currency),
        currency=transfer.currency,
        status=transfer.status,
        policy_decision=transfer.policy_decision,
        risk_score=transfer.risk_score,
        risk_level=transfer.risk_level,
        reason_codes=transfer.reason_codes or [],
        decision_explanation=transfer.decision_explanation,
        correlation_id=transfer.correlation_id,
        incident_id=transfer.incident_id,
        created_at=transfer.created_at,
        verification_challenge_id=chal.id if chal else None,
        mock_challenge_code=mock_code
    )

@banking_router.post("/transfers/{transfer_id}/verify", response_model=TransferResponse)
async def submit_transfer_verification(
    transfer_id: str,
    req: VerificationSubmitRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Submit step-up verification code to release an AWAITING_VERIFICATION transfer."""
    transfer = await transaction_gateway.verify_challenge(
        db=db,
        transfer_id=transfer_id,
        code=req.verification_code,
        current_user_id=current_user.id
    )

    return TransferResponse(
        id=transfer.id,
        idempotency_key=transfer.idempotency_key,
        source_account_id=transfer.source_account_id,
        destination_account_id=transfer.destination_account_id,
        amount_minor=transfer.amount_minor,
        amount_formatted=format_currency(transfer.amount_minor, transfer.currency),
        currency=transfer.currency,
        status=transfer.status,
        policy_decision=transfer.policy_decision,
        risk_score=transfer.risk_score,
        risk_level=transfer.risk_level,
        reason_codes=transfer.reason_codes or [],
        decision_explanation=transfer.decision_explanation,
        correlation_id=transfer.correlation_id,
        incident_id=transfer.incident_id,
        created_at=transfer.created_at
    )

@banking_router.get("/transfers", response_model=List[TransferResponse])
async def list_transfers(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve transfer history for the authenticated user (both sent & received) or all transfers for analysts."""
    stmt = select(Transfer).order_by(Transfer.created_at.desc())
    if current_user.role not in ["admin", "analyst"]:
        user_acc_stmt = select(BankAccount.id).where(BankAccount.user_id == current_user.id)
        user_acc_ids = (await db.execute(user_acc_stmt)).scalars().all()
        stmt = stmt.where(
            (Transfer.initiated_by_user_id == current_user.id) |
            (Transfer.source_account_id.in_(user_acc_ids)) |
            (Transfer.destination_account_id.in_(user_acc_ids))
        )
    stmt = stmt.limit(limit).offset(offset)

    res = await db.execute(stmt)
    transfers = res.scalars().all()

    return [
        TransferResponse(
            id=t.id,
            idempotency_key=t.idempotency_key,
            source_account_id=t.source_account_id,
            destination_account_id=t.destination_account_id,
            amount_minor=t.amount_minor,
            amount_formatted=format_currency(t.amount_minor, t.currency),
            currency=t.currency,
            status=t.status,
            policy_decision=t.policy_decision,
            risk_score=t.risk_score,
            risk_level=t.risk_level,
            reason_codes=t.reason_codes or [],
            decision_explanation=t.decision_explanation,
            correlation_id=t.correlation_id,
            incident_id=t.incident_id,
            created_at=t.created_at
        )
        for t in transfers
    ]

@banking_router.get("/transfers/{transfer_id}/risk", response_model=RiskAssessmentResponse)
async def get_transfer_risk_assessment(
    transfer_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve explainable risk assessment and triggered rules for a transfer."""
    stmt = select(Transfer).where(Transfer.id == transfer_id)
    res = await db.execute(stmt)
    transfer = res.scalars().first()

    if not transfer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transfer not found.")

    if transfer.initiated_by_user_id != current_user.id and current_user.role not in ["admin", "analyst"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    risk_stmt = select(RiskAssessment).where(RiskAssessment.transfer_id == transfer_id)
    risk_res = await db.execute(risk_stmt)
    assessment = risk_res.scalars().first()

    if not assessment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Risk assessment not found.")

    return RiskAssessmentResponse(
        transfer_id=assessment.transfer_id,
        total_score=assessment.total_score,
        risk_level=assessment.risk_level,
        policy_decision=assessment.policy_decision,
        reason_codes=assessment.reason_codes or [],
        explanation=assessment.explanation,
        rule_findings=assessment.rule_findings or [],
        assessment_version=assessment.assessment_version,
        created_at=assessment.created_at
    )

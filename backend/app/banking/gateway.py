"""
Transaction Security Gateway & Double-Entry Atomic Ledger Engine.
Handles:
1. Account ownership verification & business rule validation.
2. Idempotency control & deduplication with full payload consistency verification.
3. Pre-transaction security risk evaluation.
4. Formal state transitions: CREATED -> ASSESSING -> AWAITING_VERIFICATION / HELD / BLOCKED / POSTED.
5. Atomic double-entry bookkeeping (DEBIT source + CREDIT dest) with balance validation and locking.
6. Forwarding of suspicious events to the SentinelX SOC event stream and incident queue.
"""

import uuid
import secrets
from typing import Dict, Any, Tuple
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from app.models.db_models import (
    BankAccount, Transfer, LedgerEntry, RiskAssessment,
    VerificationChallenge, Event, AuditLog, Incident, DetectionFinding
)
from app.models.schemas import (
    TransferCreateRequest, TransferStatus, PolicyDecision,
    SourceType, SeverityLevel
)
from app.banking.risk_engine import fraud_engine

def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)

class TransactionGateway:
    """
    Core authoritative transaction and ledger state processor.
    Balances are never modified without a valid state transition and atomic ledger balancing.
    """

    async def initiate_transfer(
        self,
        db: AsyncSession,
        req: TransferCreateRequest,
        current_user_id: str,
        client_ip: str | None = None
    ) -> Transfer:
        # 1. Resolve Destination Account first to validate payload completeness
        dest_stmt = select(BankAccount).where(BankAccount.account_number == req.destination_account_number)
        dest_res = await db.execute(dest_stmt)
        dest_account = dest_res.scalars().first()

        if not dest_account:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Destination beneficiary account does not exist.")

        # 2. Strict Idempotency Check with full parameter comparison
        existing_tx_stmt = select(Transfer).where(Transfer.idempotency_key == req.idempotency_key)
        existing_res = await db.execute(existing_tx_stmt)
        existing_tx = existing_res.scalars().first()

        if existing_tx:
            # Verify payload consistency across source, destination, amount, and currency
            if (existing_tx.source_account_id != req.source_account_id or
                existing_tx.destination_account_id != dest_account.id or
                existing_tx.amount_minor != req.amount_minor or
                existing_tx.currency != req.currency):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Idempotency key reused with mismatched transaction parameters."
                )
            return existing_tx

        # 3. Source Account Ownership & Status with Row-Level Lock
        src_stmt = select(BankAccount).where(BankAccount.id == req.source_account_id).with_for_update()
        src_res = await db.execute(src_stmt)
        source_account = src_res.scalars().first()

        if not source_account:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source account not found.")

        if source_account.user_id != current_user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized: Account ownership verification failed.")

        if source_account.status != "active":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Source account is currently {source_account.status}.")

        if dest_account.id == source_account.id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Self-transfers to the same account are not permitted.")

        if dest_account.currency != req.currency or source_account.currency != req.currency:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Multi-currency conversion is not supported.")

        # 4. Balance Invariant Check
        if source_account.balance_minor < req.amount_minor:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient available balance for transfer.")

        # 5. Create Transfer Record in CREATED / ASSESSING state
        correlation_id = str(uuid.uuid4())
        transfer = Transfer(
            idempotency_key=req.idempotency_key,
            source_account_id=source_account.id,
            destination_account_id=dest_account.id,
            amount_minor=req.amount_minor,
            currency=req.currency,
            description=req.description,
            status=TransferStatus.ASSESSING.value,
            correlation_id=correlation_id,
            initiated_by_user_id=current_user_id
        )
        db.add(transfer)
        await db.flush()  # assign transfer.id

        # 6. Pre-Transaction Security Risk Evaluation
        eval_result = await fraud_engine.evaluate_transaction(
            db=db,
            source_account=source_account,
            dest_account=dest_account,
            amount_minor=req.amount_minor,
            client_ip=client_ip
        )

        decision: PolicyDecision = eval_result["policy_decision"]
        transfer.policy_decision = decision.value
        transfer.risk_score = eval_result["total_score"]
        transfer.risk_level = eval_result["risk_level"]
        transfer.reason_codes = eval_result["reason_codes"]
        transfer.decision_explanation = eval_result["explanation"]

        # Persist detailed RiskAssessment
        assessment = RiskAssessment(
            transfer_id=transfer.id,
            total_score=eval_result["total_score"],
            risk_level=eval_result["risk_level"],
            policy_decision=decision.value,
            rule_findings=eval_result["rule_findings"],
            reason_codes=eval_result["reason_codes"],
            explanation=eval_result["explanation"],
            assessment_version=eval_result["assessment_version"]
        )
        db.add(assessment)

        # 7. Apply Policy Decision & State Machine Transitions
        if decision == PolicyDecision.ALLOW:
            # Post immediately via atomic double-entry
            await self._execute_atomic_ledger_post(db, transfer, source_account, dest_account)
            transfer.status = TransferStatus.POSTED.value

        elif decision == PolicyDecision.VERIFY:
            # Generate cryptographically secure mock challenge step-up
            mock_code = f"{secrets.randbelow(900000) + 100000}"
            challenge = VerificationChallenge(
                transfer_id=transfer.id,
                challenge_type="MOCK_OTP",
                expected_code=mock_code,
                status="PENDING",
                expires_at=utc_now() + timedelta(minutes=10)
            )
            db.add(challenge)
            transfer.status = TransferStatus.AWAITING_VERIFICATION.value

        elif decision == PolicyDecision.HOLD:
            transfer.status = TransferStatus.HELD.value
            await self._emit_soc_security_event(
                db, transfer, source_account, dest_account,
                event_type="BANKING_FRAUD_HOLD",
                severity=SeverityLevel.HIGH,
                reason="Transfer placed on manual security review hold due to elevated fraud indicators."
            )

        elif decision == PolicyDecision.BLOCK:
            transfer.status = TransferStatus.BLOCKED.value
            await self._emit_soc_security_event(
                db, transfer, source_account, dest_account,
                event_type="BANKING_FRAUD_BLOCK",
                severity=SeverityLevel.CRITICAL,
                reason="Transfer blocked by automated policy engine: High-risk anomaly pattern detected."
            )

        # 8. Hash-Chained Audit Record
        await self._create_audit_entry(
            db=db,
            user_id=current_user_id,
            action=f"BANKING_TRANSFER_{transfer.status}",
            resource_id=transfer.id,
            details={
                "amount": req.amount_minor,
                "src": source_account.account_number,
                "dst": dest_account.account_number,
                "score": transfer.risk_score,
                "decision": transfer.policy_decision
            },
            ip_address=client_ip
        )

        try:
            await db.commit()
        except IntegrityError:
            await db.rollback()
            # Concurrency race on idempotency_key
            retry_stmt = select(Transfer).where(Transfer.idempotency_key == req.idempotency_key)
            retry_res = await db.execute(retry_stmt)
            concurrent_tx = retry_res.scalars().first()
            if concurrent_tx:
                if (concurrent_tx.source_account_id != req.source_account_id or
                    concurrent_tx.destination_account_id != dest_account.id or
                    concurrent_tx.amount_minor != req.amount_minor or
                    concurrent_tx.currency != req.currency):
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Idempotency key reused with mismatched transaction parameters."
                    )
                return concurrent_tx
            raise

        await db.refresh(transfer)
        return transfer

    async def verify_challenge(
        self,
        db: AsyncSession,
        transfer_id: str,
        code: str,
        current_user_id: str
    ) -> Transfer:
        transfer_stmt = select(Transfer).where(Transfer.id == transfer_id)
        transfer_res = await db.execute(transfer_stmt)
        transfer = transfer_res.scalars().first()

        if not transfer:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transfer not found.")

        if transfer.initiated_by_user_id != current_user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized to verify this transfer.")

        if transfer.status != TransferStatus.AWAITING_VERIFICATION.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Transfer is in '{transfer.status}' state and does not accept verification."
            )

        chal_stmt = select(VerificationChallenge).where(VerificationChallenge.transfer_id == transfer.id).with_for_update()
        chal_res = await db.execute(chal_stmt)
        challenge = chal_res.scalars().first()

        if not challenge or challenge.status != "PENDING":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No active verification challenge found.")

        now = utc_now()
        if now > challenge.expires_at:
            challenge.status = "EXPIRED"
            transfer.status = TransferStatus.EXPIRED.value
            await db.commit()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification challenge has expired.")

        challenge.attempt_count += 1

        # Constant-time comparison to prevent timing attacks
        if not secrets.compare_digest(challenge.expected_code, code.strip()):
            if challenge.attempt_count >= challenge.max_attempts:
                challenge.status = "FAILED"
                transfer.status = TransferStatus.REJECTED.value
                await db.commit()
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Maximum verification attempts exceeded. Transfer rejected.")
            await db.commit()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid verification code. {challenge.max_attempts - challenge.attempt_count} attempts remaining.")

        # Challenge Succeeded -> Complete Posting with Row-Level Locks
        challenge.status = "VERIFIED"
        challenge.verified_at = now

        src_stmt = select(BankAccount).where(BankAccount.id == transfer.source_account_id).with_for_update()
        dest_stmt = select(BankAccount).where(BankAccount.id == transfer.destination_account_id).with_for_update()
        src_account = (await db.execute(src_stmt)).scalars().first()
        dest_account = (await db.execute(dest_stmt)).scalars().first()

        if src_account.balance_minor < transfer.amount_minor:
            transfer.status = TransferStatus.FAILED.value
            transfer.decision_explanation = "Transfer failed at posting time: Balance depleted."
            await db.commit()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient balance during execution.")

        await self._execute_atomic_ledger_post(db, transfer, src_account, dest_account)
        transfer.status = TransferStatus.POSTED.value

        await self._create_audit_entry(
            db=db,
            user_id=current_user_id,
            action="BANKING_TRANSFER_VERIFIED_POSTED",
            resource_id=transfer.id,
            details={"transfer_id": transfer.id, "amount": transfer.amount_minor}
        )

        await db.commit()
        await db.refresh(transfer)
        return transfer

    async def _execute_atomic_ledger_post(
        self,
        db: AsyncSession,
        transfer: Transfer,
        source: BankAccount,
        dest: BankAccount
    ):
        """
        Executes strict double-entry balance mutation:
        - Exactly one DEBIT from source
        - Exactly one CREDIT to dest
        - Net change = 0 (balanced)
        """
        if source.balance_minor < transfer.amount_minor:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient available balance for transfer.")

        # Deduct source
        source.balance_minor -= transfer.amount_minor
        source.updated_at = utc_now()
        debit_entry = LedgerEntry(
            transaction_id=transfer.id,
            account_id=source.id,
            entry_type="DEBIT",
            amount_minor=transfer.amount_minor,
            currency=transfer.currency,
            balance_after_minor=source.balance_minor,
            description=f"Transfer to account {dest.account_number}"
        )
        db.add(debit_entry)

        # Credit destination
        dest.balance_minor += transfer.amount_minor
        dest.updated_at = utc_now()
        credit_entry = LedgerEntry(
            transaction_id=transfer.id,
            account_id=dest.id,
            entry_type="CREDIT",
            amount_minor=transfer.amount_minor,
            currency=transfer.currency,
            balance_after_minor=dest.balance_minor,
            description=f"Received transfer from account {source.account_number}"
        )
        db.add(credit_entry)

    async def _emit_soc_security_event(
        self,
        db: AsyncSession,
        transfer: Transfer,
        source: BankAccount,
        dest: BankAccount,
        event_type: str,
        severity: SeverityLevel,
        reason: str
    ):
        """
        Injects suspicious transaction events directly into the canonical SOC telemetry pipeline
        and auto-creates a correlated Incident and DetectionFinding for analyst triage.
        """
        event_id = f"EVT-BANK-{str(uuid.uuid4())[:8]}"
        soc_event = Event(
            event_id=event_id,
            timestamp=utc_now(),
            source_type="generic_json",
            source_name="banking-transaction-gateway",
            host_id=f"acc-{source.account_number}",
            user_id=f"user-{transfer.initiated_by_user_id}",
            event_type=event_type,
            severity=severity.value,
            raw_event=(
                f"Banking Gateway Security Event: {reason} | Amount: {transfer.amount_minor / 100:.2f} {transfer.currency} | "
                f"Source: {source.account_number} -> Dest: {dest.account_number} | RiskScore: {transfer.risk_score} | "
                f"Decision: {transfer.policy_decision} | Reasons: {','.join(transfer.reason_codes or [])}"
            )
        )
        db.add(soc_event)

        # Auto-create correlated Incident for SOC Command Deck
        inc_id = f"INC-BANK-{str(uuid.uuid4())[:8]}"
        incident = Incident(
            id=inc_id,
            title=f"Banking Fraud {transfer.policy_decision}: {source.account_number} -> {dest.account_number}",
            summary=(
                f"{reason} Attempted transfer of {transfer.amount_minor / 100:.2f} {transfer.currency} "
                f"from account {source.account_number} to {dest.account_number}. "
                f"Risk score: {transfer.risk_score}/100. Triggered reason codes: {', '.join(transfer.reason_codes or [])}."
            ),
            status="new",
            severity=severity.value,
            first_seen=utc_now(),
            last_seen=utc_now(),
            affected_entities=[source.account_number, dest.account_number, f"user-{transfer.initiated_by_user_id}"],
            threat_intel_matches=transfer.reason_codes or [],
            graph_risk_score=float(transfer.risk_score)
        )
        db.add(incident)
        transfer.incident_id = incident.id

        finding = DetectionFinding(
            detector_type="rule",
            rule_or_model_name=f"FRAUD-GATEWAY-{transfer.policy_decision}",
            severity=severity.value,
            title=f"Fraud Gateway Policy {transfer.policy_decision}",
            description=reason,
            evidence_events=[event_id],
            affected_entity=source.account_number,
            confidence=0.95,
            incident_id=inc_id,
            metadata_info={
                "transfer_id": transfer.id,
                "amount_minor": transfer.amount_minor,
                "currency": transfer.currency,
                "decision": transfer.policy_decision,
                "risk_score": transfer.risk_score,
                "reason_codes": transfer.reason_codes
            }
        )
        db.add(finding)

    async def _create_audit_entry(
        self,
        db: AsyncSession,
        user_id: str,
        action: str,
        resource_id: str,
        details: Dict[str, Any],
        ip_address: str | None = None
    ):
        last_audit_res = await db.execute(
            select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(1).with_for_update()
        )
        last_audit = last_audit_res.scalars().first()
        prev_hash = last_audit.entry_hash if last_audit else None
        
        audit_time = utc_now()
        entry_hash = AuditLog.calculate_entry_hash(
            prev_hash=prev_hash,
            user_id=user_id,
            action=action,
            resource_type="banking_transfer",
            resource_id=resource_id,
            timestamp=audit_time
        )

        entry = AuditLog(
            user_id=user_id,
            action=action,
            resource_type="banking_transfer",
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
            prev_hash=prev_hash,
            entry_hash=entry_hash,
            timestamp=audit_time
        )
        db.add(entry)

transaction_gateway = TransactionGateway()

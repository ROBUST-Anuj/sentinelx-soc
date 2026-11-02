"""
Internal Server-to-Server Fraud Assessment API Routes.
Exposes /internal/v1/transaction-assessments for external platforms (e.g., NexaBank).
Protected via X-Service-Auth header or Internal API token.
Emits canonical security events and creates SOC incidents when high-risk or blocked transfers occur.
"""

import uuid
import hmac
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
from app.core.database import get_db
from app.models.db_models import BankAccount, Event, DetectionFinding, Incident, AuditLog
from app.models.schemas import (
    TransactionAssessmentRequest,
    TransactionAssessmentResponse,
    PolicyDecision,
    SourceType,
    SeverityLevel,
)
from app.banking.risk_engine import fraud_engine

internal_router = APIRouter(prefix="/internal/v1", tags=["Internal Security Service APIs"])

def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)

import hashlib
import time
from typing import Tuple, Dict, Optional
from fastapi import Request

# Replay cache for nonces within the valid timestamp drift window: (nonce -> expiry_timestamp)
_NONCE_CACHE: Dict[str, float] = {}

def generate_hmac_signature(
    secret_key: str,
    method: str,
    path: str,
    timestamp: str,
    nonce: str,
    body: bytes
) -> str:
    """
    Calculates SHA-256 HMAC signature covering:
    HTTP Method, Request Path, Timestamp, Nonce, and Body SHA-256 Digest.
    """
    body_hash = hashlib.sha256(body).hexdigest()
    canonical_payload = f"{method.upper()}\n{path}\n{timestamp}\n{nonce}\n{body_hash}".encode("utf-8")
    return hmac.new(secret_key.encode("utf-8"), canonical_payload, hashlib.sha256).hexdigest()

def verify_hmac_signature(
    secret_key: str,
    method: str,
    path: str,
    timestamp: str,
    nonce: str,
    body: bytes,
    signature: str,
    max_drift_seconds: int = 300
) -> Tuple[bool, str]:
    """
    Cryptographic HMAC signature verification:
    1. Validates timestamp drift within max_drift_seconds (default: 300s / 5 mins).
    2. Enforces nonce replay prevention with automatic expiration pruning.
    3. Performs constant-time comparison against expected HMAC-SHA256 signature.
    """
    # 1. Timestamp drift check
    try:
        req_time = float(timestamp)
    except (ValueError, TypeError):
        return False, "Invalid timestamp format."

    current_time = time.time()
    if abs(current_time - req_time) > max_drift_seconds:
        return False, "Request timestamp exceeds allowable drift window."

    # 2. Nonce replay prevention
    now = time.time()
    # Prune expired nonces
    expired = [k for k, exp in _NONCE_CACHE.items() if exp < now]
    for k in expired:
        _NONCE_CACHE.pop(k, None)

    if nonce in _NONCE_CACHE:
        return False, "Nonce replay detected."

    _NONCE_CACHE[nonce] = req_time + max_drift_seconds

    # 3. Constant-time signature comparison
    expected_sig = generate_hmac_signature(
        secret_key=secret_key,
        method=method,
        path=path,
        timestamp=timestamp,
        nonce=nonce,
        body=body
    )
    if not hmac.compare_digest(expected_sig, signature):
        return False, "HMAC signature mismatch (tampering or invalid secret)."

    return True, "Valid signature."

async def verify_internal_service_auth(
    request: Request,
    x_service_auth: Optional[str] = Header(None, alias="X-Service-Auth"),
    x_signature: Optional[str] = Header(None, alias="X-Signature"),
    x_timestamp: Optional[str] = Header(None, alias="X-Timestamp"),
    x_nonce: Optional[str] = Header(None, alias="X-Nonce")
):
    """
    Authenticates inter-service server-to-server calls.
    Supports:
    1. Full Cryptographic HMAC Signature: X-Signature, X-Timestamp, X-Nonce covering method, path, and body.
    2. Token-Based Service Key: X-Service-Auth (constant-time compared against INTERNAL_SERVICE_KEY).
    """
    # Mode 1: Cryptographic Request Signing
    if x_signature:
        if not x_timestamp or not x_nonce:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing required X-Timestamp or X-Nonce for HMAC request signature."
            )
        body = await request.body()
        is_valid, reason = verify_hmac_signature(
            secret_key=settings.INTERNAL_SERVICE_KEY,
            method=request.method,
            path=request.url.path,
            timestamp=x_timestamp,
            nonce=x_nonce,
            body=body,
            signature=x_signature
        )
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=reason
            )
        return True

    # Mode 2: Static Token Header (Backward-compatible inter-service token)
    if x_service_auth:
        expected_token = settings.INTERNAL_SERVICE_KEY
        if not hmac.compare_digest(x_service_auth, expected_token):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid internal service credentials."
            )
        return True

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Missing required internal service authentication (X-Signature or X-Service-Auth)."
    )

@internal_router.post(
    "/transaction-assessments",
    response_model=TransactionAssessmentResponse,
    summary="Real-time Server-to-Server Fraud Risk Assessment"
)
async def assess_transaction(
    req: TransactionAssessmentRequest,
    db: AsyncSession = Depends(get_db),
    _authorized: bool = Depends(verify_internal_service_auth)
):
    """
    Evaluates incoming banking transaction for fraud, velocity spikes, and known threat signals.
    Emits canonical telemetry to the SentinelX SOC event stream.
    Returns authoritative decision: ALLOW, VERIFY, HOLD, or BLOCK.
    """
    # 1. Resolve source and destination accounts if known locally
    src_res = await db.execute(select(BankAccount).where(BankAccount.id == req.source_account_id))
    source_acc = src_res.scalars().first()

    dest_res = await db.execute(select(BankAccount).where(BankAccount.account_number == req.destination_account_number))
    dest_acc = dest_res.scalars().first()

    # Synthetic or fallback mock account representation for risk evaluation
    if not source_acc:
        source_acc = BankAccount(
            id=req.source_account_id,
            user_id=req.customer_id,
            account_number="EXT-" + req.source_account_id[-8:],
            currency=req.currency,
            balance_minor=100_000_00,
            status="active"
        )
    if not dest_acc:
        dest_acc = BankAccount(
            id=str(uuid.uuid4()),
            user_id="beneficiary-external",
            account_number=req.destination_account_number,
            currency=req.currency,
            balance_minor=0,
            status="active"
        )

    # 2. Run fraud evaluation through the FraudDetectionEngine
    risk_res = await fraud_engine.evaluate_transaction(
        db=db,
        source_account=source_acc,
        dest_account=dest_acc,
        amount_minor=req.amount_minor,
        client_ip=req.source_ip
    )

    policy_decision = risk_res["policy_decision"]
    total_score = risk_res["total_score"]
    risk_level = risk_res["risk_level"]
    reason_codes = risk_res["reason_codes"]
    explanation = risk_res["explanation"]

    correlation_id = f"corr-tx-{req.transaction_id[:8]}"
    incident_id = None
    now = utc_now()

    # 3. Emit Canonical Security Event into SentinelX SOC Event Stream
    sec_event = Event(
        event_id=f"evt-{uuid.uuid4()}",
        timestamp=now,
        source_type=SourceType.GENERIC_JSON.value,
        source_name="NexaBank-Transaction-Gateway",
        host_id="nexabank-core-cluster",
        user_id=req.customer_id,
        src_ip=req.source_ip,
        event_type="BANKING_TRANSACTION_ASSESSED",
        raw_event=f"Internal assessment for tx {req.transaction_id}: amount={req.amount_minor} decision={policy_decision.value} score={total_score}",
        normalized_fields={
            "transaction_id": req.transaction_id,
            "customer_id": req.customer_id,
            "source_account_id": req.source_account_id,
            "destination_account_number": req.destination_account_number,
            "amount_minor": req.amount_minor,
            "currency": req.currency,
            "policy_decision": policy_decision.value,
            "risk_score": total_score,
            "risk_level": risk_level,
            "reason_codes": reason_codes,
            "channel": req.channel
        }
    )
    db.add(sec_event)

    # 4. If HIGH risk or BLOCKED/HELD, generate SOC Finding & Incident
    if policy_decision in [PolicyDecision.BLOCK, PolicyDecision.HOLD] or total_score >= 60.0:
        sev = SeverityLevel.CRITICAL.value if policy_decision == PolicyDecision.BLOCK else SeverityLevel.HIGH.value
        
        inc = Incident(
            title=f"Banking Fraud Intervention: Transaction {req.transaction_id[:8]} [{policy_decision.value}]",
            summary=f"Automated fraud engine triggered {policy_decision.value} for tx {req.transaction_id}. Score: {total_score}. Explanation: {explanation}",
            severity=sev,
            status="new",
            assigned_to="tier1_analyst",
            affected_entities=[req.customer_id, req.source_account_id, req.destination_account_number],
            graph_risk_score=float(total_score)
        )
        db.add(inc)
        await db.flush()
        incident_id = inc.id

        finding = DetectionFinding(
            detector_type="rule",
            rule_or_model_name="RULE-INTERNAL-FRAUD-ASSESSMENT",
            severity=sev,
            title=f"Automated Banking Fraud Alert: {', '.join(reason_codes) or 'High Risk Policy Trigger'}",
            description=explanation,
            evidence_events=[sec_event.event_id],
            affected_entity=req.customer_id,
            confidence=0.92,
            incident_id=incident_id,
            metadata_info={
                "transaction_id": req.transaction_id,
                "amount_minor": req.amount_minor,
                "decision": policy_decision.value,
                "risk_score": total_score,
                "reason_codes": reason_codes
            }
        )
        db.add(finding)

    # 5. Append immutable audit log
    entry_hash = AuditLog.calculate_entry_hash(
        prev_hash="INTERNAL_CHAIN",
        user_id=f"nexabank:{req.customer_id}",
        action=f"INTERNAL_TRANSACTION_ASSESSMENT:{policy_decision.value}",
        resource_type="TransactionAssessment",
        resource_id=req.transaction_id,
        timestamp=now
    )
    audit_entry = AuditLog(
        user_id=f"nexabank:{req.customer_id}",
        action=f"INTERNAL_TRANSACTION_ASSESSMENT:{policy_decision.value}",
        resource_type="TransactionAssessment",
        resource_id=req.transaction_id,
        details={
            "transaction_id": req.transaction_id,
            "amount_minor": req.amount_minor,
            "policy_decision": policy_decision.value,
            "risk_score": total_score,
            "incident_id": incident_id
        },
        ip_address=req.source_ip,
        prev_hash="INTERNAL_CHAIN",
        entry_hash=entry_hash,
        timestamp=now
    )
    db.add(audit_entry)
    await db.commit()

    return TransactionAssessmentResponse(
        assessment_id=f"asm-{uuid.uuid4().hex[:12]}",
        transaction_id=req.transaction_id,
        policy_decision=policy_decision,
        risk_score=total_score,
        risk_level=risk_level,
        requires_verification=(policy_decision == PolicyDecision.VERIFY),
        reason_codes=reason_codes,
        explanation=explanation,
        correlation_id=correlation_id,
        incident_id=incident_id,
        assessed_at=now
    )

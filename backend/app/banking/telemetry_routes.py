"""
Banking Security Telemetry & Violation Monitoring Endpoints.
Exposes:
- POST /api/banking/telemetry/events : Ingestion of browser behavior, authentication, and application security events.
- GET  /api/banking/violations       : Query violation logs with filters for SOC investigation.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Request, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.db_models import User, SecurityViolationEvent
from app.models.schemas import SecurityViolationEventCreate, SecurityViolationEventResponse
from app.banking.violation_engine import violation_engine

telemetry_router = APIRouter(prefix="/banking/security", tags=["Banking Security Monitoring"])

@telemetry_router.post("/events", response_model=SecurityViolationEventResponse)
async def submit_security_telemetry_event(
    req: SecurityViolationEventCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """
    Ingest a telemetry or violation event from NexaBank client or proxy.
    Automatically captures client IP, applies privacy sanitization, calculates authoritative risk,
    and forwards to the SentinelX SOC event stream.
    """
    client_ip = request.client.host if request.client else "127.0.0.1"
    customer_id = current_user.id if current_user else req.customer_id

    event = await violation_engine.ingest_violation_event(
        db=db,
        event_type=req.event_type,
        category=req.category,
        customer_id=customer_id,
        session_id=req.session_id,
        transaction_id=req.transaction_id,
        source_ip=client_ip,
        device_id=req.device_id,
        source_application=req.source_application,
        metadata=req.event_metadata,
        is_simulation=req.is_simulation
    )
    return event

@telemetry_router.get("/violations", response_model=List[SecurityViolationEventResponse])
async def list_security_violations(
    category: Optional[str] = Query(None, description="Filter by category"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    customer_id: Optional[str] = Query(None, description="Filter by customer ID"),
    is_simulation: Optional[bool] = Query(None, description="Filter demo simulation events"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Query security violation events for SOC monitoring and incident triage.
    Restricted to authenticated analysts and administrators.
    """
    if current_user.role not in ["admin", "analyst"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    stmt = select(SecurityViolationEvent).order_by(SecurityViolationEvent.created_at.desc())
    if category:
        stmt = stmt.where(SecurityViolationEvent.category == category)
    if severity:
        stmt = stmt.where(SecurityViolationEvent.severity == severity)
    if customer_id:
        stmt = stmt.where(SecurityViolationEvent.customer_id == customer_id)
    if is_simulation is not None:
        stmt = stmt.where(SecurityViolationEvent.is_simulation == is_simulation)

    stmt = stmt.limit(limit).offset(offset)
    res = await db.execute(stmt)
    violations = res.scalars().all()
    return violations

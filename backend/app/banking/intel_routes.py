"""
Threat Intelligence & Unified Attack Graph Investigation Router.
Exposes:
- GET  /api/banking/intel/indicators       : List all threat indicators with type, severity, and active filters.
- POST /api/banking/intel/indicators       : Add manual or synthetic IOC indicator.
- POST /api/banking/intel/import           : Controlled batch import of structured IOC feeds with provenance tracking.
- GET  /api/banking/graph/incident/{id}    : Unified multi-domain attack graph for an incident.
- GET  /api/banking/intel/investigate/{id} : Comprehensive workbench investigation correlating IOC with incidents.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.models.db_models import User, ThreatIndicator, Incident, SecurityViolationEvent, ResponsePlaybookAction, AuditLog
from app.models.schemas import UserRole, ThreatIndicatorCreate, ThreatIndicatorResponse
from app.graph.unified_graph_engine import unified_graph_engine

intel_router = APIRouter(prefix="/banking/intel", tags=["Threat Intelligence & Graph Investigation"])

def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)

class IOCBatchImportRequest(BaseModel):
    source_name: str = Field(..., description="Feed source name (e.g. MISP, AlienVault, Internal Bank Feed)")
    feed_category: str = Field(default="commercial_ti")
    indicators: List[ThreatIndicatorCreate]

@intel_router.get("/indicators", response_model=List[ThreatIndicatorResponse])
async def list_threat_indicators(
    indicator_type: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List threat intelligence indicators with optional filters."""
    if current_user.role not in ["admin", "analyst"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    stmt = select(ThreatIndicator).order_by(ThreatIndicator.created_at.desc())
    if indicator_type:
        stmt = stmt.where(ThreatIndicator.indicator_type == indicator_type)
    if severity:
        stmt = stmt.where(ThreatIndicator.severity == severity)
    if is_active is not None:
        stmt = stmt.where(ThreatIndicator.is_active == is_active)

    stmt = stmt.limit(limit)
    res = await db.execute(stmt)
    return res.scalars().all()

@intel_router.post("/indicators", response_model=ThreatIndicatorResponse)
async def create_threat_indicator(
    ioc: ThreatIndicatorCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.ANALYST]))
):
    """Add a new verified or synthetic IOC indicator to the database."""
    # Deduplicate: check if value already exists
    existing = await db.execute(select(ThreatIndicator).where(ThreatIndicator.value == ioc.value))
    found = existing.scalars().first()
    if found:
        found.last_seen = utc_now()
        found.confidence = max(found.confidence, ioc.confidence)
        await db.commit()
        await db.refresh(found)
        return found

    now = utc_now()
    indicator = ThreatIndicator(
        indicator_type=ioc.indicator_type,
        value=ioc.value.strip(),
        threat_type=ioc.threat_type,
        severity=ioc.severity if isinstance(ioc.severity, str) else ioc.severity.value,
        confidence=ioc.confidence,
        source=ioc.source,
        description=ioc.description,
        is_active=True,
        first_seen=now,
        last_seen=now,
        expires_at=ioc.expires_at,
        metadata_info=ioc.metadata_info or {},
        created_at=now
    )
    db.add(indicator)
    await db.commit()
    await db.refresh(indicator)
    return indicator

@intel_router.post("/import")
async def import_ioc_feed_batch(
    req: IOCBatchImportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.ANALYST]))
):
    """Controlled batch import of structured IOCs with provenance tracking and deduplication."""
    now = utc_now()
    imported = 0
    updated = 0

    for ioc in req.indicators:
        val = ioc.value.strip()
        existing = (await db.execute(select(ThreatIndicator).where(ThreatIndicator.value == val))).scalars().first()
        if existing:
            existing.last_seen = now
            existing.source = f"{existing.source}, {req.source_name}"
            updated += 1
        else:
            db_ioc = ThreatIndicator(
                indicator_type=ioc.indicator_type,
                value=val,
                threat_type=ioc.threat_type,
                severity=ioc.severity if isinstance(ioc.severity, str) else ioc.severity.value,
                confidence=ioc.confidence,
                source=req.source_name,
                description=ioc.description or f"Imported from {req.source_name}",
                is_active=True,
                first_seen=now,
                last_seen=now,
                expires_at=ioc.expires_at,
                metadata_info={"import_batch_category": req.feed_category},
                created_at=now
            )
            db.add(db_ioc)
            imported += 1

    audit = AuditLog(
        user_id=current_user.id,
        action=f"IOC_FEED_IMPORT:{req.source_name}",
        resource_type="ThreatIntelligence",
        resource_id=req.source_name,
        details={"imported": imported, "updated": updated, "total_records": len(req.indicators)},
        ip_address="127.0.0.1",
        prev_hash="TI_IMPORT_CHAIN",
        entry_hash=AuditLog.calculate_entry_hash(
            "TI_IMPORT_CHAIN", current_user.id, "IMPORT", "TI", req.source_name, now
        ),
        timestamp=now
    )
    db.add(audit)
    await db.commit()

    return {
        "status": "success",
        "source_name": req.source_name,
        "imported_count": imported,
        "updated_count": updated,
        "total_processed": len(req.indicators)
    }

@intel_router.get("/graph/incident/{incident_id}")
async def get_incident_attack_graph(
    incident_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Constructs the unified interactive multi-domain attack graph for an incident."""
    if current_user.role not in ["admin", "analyst"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    graph_data = await unified_graph_engine.build_incident_graph(db, incident_id)
    return graph_data

@intel_router.get("/investigate/{indicator_id}")
async def investigate_threat_indicator(
    indicator_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Threat Intelligence Workbench:
    Correlates an IOC with observed security violation events, banking transactions,
    attack storylines, and containment actions.
    """
    if current_user.role not in ["admin", "analyst"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    ioc_res = await db.execute(select(ThreatIndicator).where(ThreatIndicator.id == indicator_id))
    ioc = ioc_res.scalars().first()
    if not ioc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Threat indicator not found.")

    # Find matching violations (by source_ip or metadata value)
    vio_res = await db.execute(
        select(SecurityViolationEvent).where(
            (SecurityViolationEvent.source_ip == ioc.value) |
            (SecurityViolationEvent.customer_id == ioc.value)
        )
    )
    violations = vio_res.scalars().all()

    # Find linked incidents
    incident_ids = list({v.incident_id for v in violations if v.incident_id})
    incidents = []
    if incident_ids:
        inc_res = await db.execute(select(Incident).where(Incident.id.in_(incident_ids)))
        incidents = [
            {"id": i.id, "title": i.title, "severity": i.severity, "status": i.status, "risk_score": i.graph_risk_score}
            for i in inc_res.scalars().all()
        ]

    # Find linked response actions
    actions = []
    if incident_ids:
        act_res = await db.execute(select(ResponsePlaybookAction).where(ResponsePlaybookAction.incident_id.in_(incident_ids)))
        actions = [
            {"action_id": a.action_id, "action_type": a.action_type, "status": a.status, "target": a.target_entity}
            for a in act_res.scalars().all()
        ]

    return {
        "indicator": {
            "id": ioc.id,
            "type": ioc.indicator_type,
            "value": ioc.value,
            "threat_type": ioc.threat_type,
            "severity": ioc.severity,
            "confidence": ioc.confidence,
            "source": ioc.source,
            "first_seen": ioc.first_seen.isoformat() if ioc.first_seen else None,
            "last_seen": ioc.last_seen.isoformat() if ioc.last_seen else None,
            "is_active": ioc.is_active
        },
        "matched_violations_count": len(violations),
        "related_incidents": incidents,
        "related_response_actions": actions,
        "recommended_investigation_steps": [
            f"Review ingress NetFlow/HTTP traffic originating from IOC {ioc.value}.",
            "Verify whether customer credentials used alongside this indicator have been compromised in third-party breaches.",
            "Cross-correlate with active NexaBank transfer sessions and beneficiary listings.",
            "If severity is High/Critical, trigger PLAYBOOK_MALICIOUS_IP to apply edge perimeter drop."
        ]
    }

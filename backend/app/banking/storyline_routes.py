"""
Attack Storyline SOC Investigation Endpoints.
Exposes:
- GET /api/banking/storylines/{incident_id} : Returns the unified attack sequence, timeline, playbook, and correlated violation events.
- PATCH /api/banking/storylines/{incident_id}/lifecycle : Assign, Contain, or Resolve an ongoing storyline.
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.models.db_models import User, Incident, DetectionFinding, SecurityViolationEvent, AuditLog
from app.models.schemas import UserRole, IncidentStatus

storyline_router = APIRouter(prefix="/banking/storylines", tags=["Attack Storyline & Investigation"])

class StorylineLifecycleUpdate(BaseModel):
    status: IncidentStatus
    assigned_to: Optional[str] = None
    investigation_notes: Optional[str] = None

@storyline_router.get("/{incident_id}")
async def get_attack_storyline_detail(
    incident_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves the complete correlated Attack Storyline:
    Incident overview, linked violation events ordered by time, triggered detection findings,
    affected entities, risk assessment, and recommended response steps.
    """
    if current_user.role not in ["admin", "analyst"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    # 1. Fetch Incident
    inc_res = await db.execute(select(Incident).where(Incident.id == incident_id))
    inc = inc_res.scalars().first()
    if not inc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attack Storyline Incident not found.")

    # 2. Fetch all linked Security Violation Events
    vio_res = await db.execute(
        select(SecurityViolationEvent)
        .where(SecurityViolationEvent.incident_id == incident_id)
        .order_by(SecurityViolationEvent.created_at.asc())
    )
    violations = vio_res.scalars().all()

    # 3. Fetch Findings
    f_res = await db.execute(
        select(DetectionFinding)
        .where(DetectionFinding.incident_id == incident_id)
        .order_by(DetectionFinding.created_at.asc())
    )
    findings = f_res.scalars().all()

    # Extract recommended playbook if stored in finding metadata
    playbook = []
    for f in findings:
        if f.metadata_info and "playbook" in f.metadata_info:
            playbook = f.metadata_info["playbook"]
            break

    timeline = [
        {
            "event_id": v.event_id,
            "timestamp": v.created_at.isoformat() if v.created_at else None,
            "event_type": v.event_type,
            "category": v.category,
            "severity": v.severity,
            "source_ip": v.source_ip,
            "device_id": v.device_id,
            "risk_contribution": v.risk_contribution,
            "detection_rule": v.detection_rule,
            "metadata": v.event_metadata,
            "is_simulation": v.is_simulation
        }
        for v in violations
    ]

    return {
        "incident_id": inc.id,
        "title": inc.title,
        "summary": inc.summary,
        "severity": inc.severity,
        "status": inc.status,
        "assigned_to": inc.assigned_to,
        "first_seen": inc.first_seen.isoformat() if inc.first_seen else None,
        "last_seen": inc.last_seen.isoformat() if inc.last_seen else None,
        "affected_entities": inc.affected_entities or [],
        "graph_risk_score": inc.graph_risk_score,
        "recommended_playbook": playbook,
        "event_count": len(timeline),
        "timeline": timeline,
        "findings": [
            {
                "id": f.id,
                "detector_type": f.detector_type,
                "rule_name": f.rule_or_model_name,
                "title": f.title,
                "severity": f.severity,
                "confidence": f.confidence,
                "description": f.description
            }
            for f in findings
        ]
    }

@storyline_router.patch("/{incident_id}/lifecycle")
async def update_storyline_lifecycle(
    incident_id: str,
    update: StorylineLifecycleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.ANALYST]))
):
    """
    Updates the lifecycle of an active Attack Storyline:
    Transitions between NEW -> INVESTIGATING -> CONTAINED -> RESOLVED, and assigns analysts.
    """
    inc_res = await db.execute(select(Incident).where(Incident.id == incident_id))
    inc = inc_res.scalars().first()
    if not inc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found.")

    prev_status = inc.status
    inc.status = update.status.value
    if update.assigned_to:
        inc.assigned_to = update.assigned_to

    # Log to audit trail
    audit = AuditLog(
        user_id=current_user.id,
        action=f"STORYLINE_LIFECYCLE_UPDATE:{prev_status}->{inc.status}",
        resource_type="Incident",
        resource_id=incident_id,
        details={
            "previous_status": prev_status,
            "new_status": inc.status,
            "assigned_to": inc.assigned_to,
            "notes": update.investigation_notes
        },
        ip_address="127.0.0.1",
        prev_hash="INCIDENT_CHAIN",
        entry_hash=AuditLog.calculate_entry_hash(
            "INCIDENT_CHAIN", current_user.id, "STATUS_CHANGE", "Incident", incident_id, inc.updated_at or inc.created_at
        )
    )
    db.add(audit)
    await db.commit()
    await db.refresh(inc)

    return {
        "status": "success",
        "incident_id": inc.id,
        "previous_status": prev_status,
        "new_status": inc.status,
        "assigned_to": inc.assigned_to
    }

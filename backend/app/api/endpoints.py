from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import uuid

from app.core.database import get_db
from app.core.security import (
    verify_password, get_password_hash, create_access_token,
    get_current_user, require_role
)
from app.models.db_models import (
    User, DataSource, IngestionBatch, Event, DetectionFinding,
    Incident, IncidentNote, ThreatIndicator, ResponseExecution, AuditLog
)
from app.models.schemas import (
    Token, UserCreate, UserResponse, UserRole, CanonicalEvent,
    SourceType, SeverityLevel, IncidentStatus, ActionType,
    ResponseActionRequest, ThreatIndicatorCreate
)
from app.ingestion.normalizer import normalizer
from app.detection.hybrid_correlator import hybrid_correlator
from app.graph.engine import attack_graph_engine
from app.threat_intel.manager import threat_intel
from app.response.engine import response_engine
from app.evaluation.benchmark import evaluation_harness

api_router = APIRouter()

# ----------------- AUTHENTICATION -----------------
@api_router.post("/auth/register", response_model=UserResponse)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == user_in.username))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Username already registered")
        
    user = User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        role=user_in.role.value,
        is_active=True
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

@api_router.post("/auth/login", response_model=Token)
async def login(username: str = Form(...), password: str = Form(...), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalars().first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user account")
        
    access_token = create_access_token(data={"sub": user.username, "role": user.role})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role,
        "username": user.username
    }

@api_router.get("/auth/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user

# ----------------- SOC OVERVIEW / HEALTH -----------------
@api_router.get("/overview/stats")
async def get_soc_stats(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Counts
    events_res = await db.execute(select(Event))
    events = events_res.scalars().all()
    
    from sqlalchemy.orm import selectinload
    incidents_res = await db.execute(select(Incident).options(selectinload(Incident.findings)))
    incidents = incidents_res.scalars().all()
    
    findings_res = await db.execute(select(DetectionFinding))
    findings = findings_res.scalars().all()
    
    # Severity distribution
    sev_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "informational": 0}
    for inc in incidents:
        sev = inc.severity.lower() if inc.severity else "medium"
        sev_counts[sev] = sev_counts.get(sev, 0) + 1

    return {
        "total_events": len(events),
        "total_findings": len(findings),
        "total_incidents": len(incidents),
        "active_sources": 4,
        "severity_distribution": sev_counts,
        "recent_incidents": [
            {
                "id": inc.id,
                "title": inc.title,
                "severity": inc.severity,
                "status": inc.status,
                "created_at": inc.created_at.isoformat(),
                "findings_count": len(inc.findings) if inc.findings else 0
            } for inc in incidents[:5]
        ]
    }

# ----------------- TELEMETRY INGESTION -----------------
@api_router.post("/ingestion/upload")
async def ingest_log_file(
    source_type: SourceType = Form(...),
    source_name: str = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    batch_id = str(uuid.uuid4())
    content = (await file.read()).decode("utf-8", errors="replace")
    
    # Run Normalization
    events, valid_count, invalid_count, errors = normalizer.process_content(
        content=content,
        source_type=source_type,
        source_name=source_name,
        batch_id=batch_id
    )

    # Persist Batch
    batch = IngestionBatch(
        id=batch_id,
        source_name=source_name,
        source_type=source_type.value,
        filename=file.filename,
        total_records=valid_count + invalid_count,
        valid_records=valid_count,
        invalid_records=invalid_count,
        status="completed",
        error_message="\n".join(errors[:5]) if errors else None
    )
    db.add(batch)

    # Persist Events
    db_events = []
    for ev in events:
        db_ev = Event(
            event_id=ev.event_id,
            timestamp=ev.timestamp,
            source_type=ev.source_type.value,
            source_name=ev.source_name,
            host_id=ev.host_id,
            user_id=ev.user_id,
            src_ip=ev.src_ip,
            src_port=ev.src_port,
            dst_ip=ev.dst_ip,
            dst_port=ev.dst_port,
            protocol=ev.protocol,
            event_type=ev.event_type,
            severity=ev.severity.value,
            process_name=ev.process_name,
            process_path=ev.process_path,
            command_line=ev.command_line,
            parent_process=ev.parent_process,
            file_hash=ev.file_hash,
            raw_event=ev.raw_event,
            normalized_fields=ev.normalized_fields,
            ingestion_batch_id=batch_id
        )
        db.add(db_ev)
        db_events.append(db_ev)

    # Run Hybrid Correlator
    findings, incidents, ti_matches = hybrid_correlator.process_and_correlate(events)

    # Save Incidents & Findings
    for inc_data in incidents:
        db_inc = Incident(
            id=inc_data["id"],
            title=inc_data["title"],
            summary=inc_data["summary"],
            status=inc_data["status"],
            severity=inc_data["severity"],
            first_seen=datetime.fromisoformat(inc_data["first_seen"]),
            last_seen=datetime.fromisoformat(inc_data["last_seen"]),
            affected_entities=inc_data["affected_entities"],
            threat_intel_matches=inc_data["threat_intel_matches"],
            graph_risk_score=inc_data["graph_risk_score"]
        )
        db.add(db_inc)

    for f_data in findings:
        db_f = DetectionFinding(
            id=f_data["id"],
            detector_type=f_data["detector_type"],
            rule_or_model_name=f_data["rule_or_model_name"],
            severity=f_data["severity"],
            title=f_data["title"],
            description=f_data["description"],
            evidence_events=f_data["evidence_events"],
            affected_entity=f_data.get("affected_entity"),
            confidence=f_data.get("confidence", 0.9),
            incident_id=f_data.get("incident_id"),
            metadata_info=f_data.get("metadata", {})
        )
        db.add(db_f)

    await db.commit()

    return {
        "batch_id": batch_id,
        "valid_records": valid_count,
        "invalid_records": invalid_count,
        "findings_detected": len(findings),
        "incidents_created": len(incidents),
        "errors": errors[:5]
    }

# ----------------- EVENTS API -----------------
@api_router.get("/events")
async def get_events(
    limit: int = 50,
    offset: int = 0,
    source_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = select(Event).order_by(Event.timestamp.desc()).offset(offset).limit(limit)
    if source_type:
        query = query.where(Event.source_type == source_type)
    res = await db.execute(query)
    events = res.scalars().all()
    return events

@api_router.get("/incidents")
async def get_incidents(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from sqlalchemy.orm import selectinload
    res = await db.execute(select(Incident).options(selectinload(Incident.findings)).order_by(Incident.created_at.desc()))
    incidents = res.scalars().all()
    return [
        {
            "id": inc.id,
            "title": inc.title,
            "summary": inc.summary,
            "status": inc.status,
            "severity": inc.severity,
            "assigned_to": inc.assigned_to,
            "first_seen": inc.first_seen.isoformat() if inc.first_seen else None,
            "last_seen": inc.last_seen.isoformat() if inc.last_seen else None,
            "affected_entities": inc.affected_entities or [],
            "threat_intel_matches": inc.threat_intel_matches or [],
            "graph_risk_score": inc.graph_risk_score,
            "findings_count": len(inc.findings) if inc.findings else 0,
            "created_at": inc.created_at.isoformat() if inc.created_at else None
        }
        for inc in incidents
    ]

@api_router.get("/incidents/{incident_id}")
async def get_incident_detail(
    incident_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    res = await db.execute(select(Incident).where(Incident.id == incident_id))
    inc = res.scalars().first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")
        
    f_res = await db.execute(select(DetectionFinding).where(DetectionFinding.incident_id == incident_id))
    findings = f_res.scalars().all()

    # Evidence events
    ev_ids = []
    for f in findings:
        if f.evidence_events:
            ev_ids.extend(f.evidence_events)
    ev_ids = list(set(ev_ids))
    
    events_detail = []
    if ev_ids:
        ev_res = await db.execute(select(Event).where(Event.event_id.in_(ev_ids)))
        events_detail = ev_res.scalars().all()

    return {
        "incident": inc,
        "findings": findings,
        "evidence_events": events_detail
    }

@api_router.patch("/incidents/{incident_id}/status")
async def update_incident_status(
    incident_id: str,
    status: IncidentStatus,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.ANALYST]))
):
    res = await db.execute(select(Incident).where(Incident.id == incident_id))
    inc = res.scalars().first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")
    inc.status = status.value
    await db.commit()
    return {"status": "success", "new_status": status.value}

# ----------------- ATTACK GRAPH EXPLORER -----------------
@api_router.get("/graph/incident/{incident_id}")
async def get_incident_attack_graph(
    incident_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    f_res = await db.execute(select(DetectionFinding).where(DetectionFinding.incident_id == incident_id))
    findings = f_res.scalars().all()
    
    ev_ids = []
    for f in findings:
        if f.evidence_events:
            ev_ids.extend(f.evidence_events)
            
    events = []
    if ev_ids:
        ev_res = await db.execute(select(Event).where(Event.event_id.in_(ev_ids)))
        db_events = ev_res.scalars().all()
        # Convert DB events to CanonicalEvent format for graph engine
        for de in db_events:
            events.append(CanonicalEvent(
                event_id=de.event_id,
                timestamp=de.timestamp,
                source_type=SourceType(de.source_type),
                source_name=de.source_name,
                host_id=de.host_id,
                user_id=de.user_id,
                src_ip=de.src_ip,
                dst_ip=de.dst_ip,
                event_type=de.event_type,
                process_name=de.process_name,
                command_line=de.command_line
            ))
            
    findings_dicts = [
        {
            "id": f.id,
            "title": f.title,
            "severity": f.severity,
            "evidence_events": f.evidence_events,
            "confidence": f.confidence
        } for f in findings
    ]
    
    attack_graph_engine.build_from_telemetry_and_findings(events, findings_dicts, incident_id)
    return attack_graph_engine.export_graph_json()

# ----------------- DEFENSIVE RESPONSE -----------------
@api_router.post("/response/execute")
async def execute_response(
    req: ResponseActionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.ANALYST]))
):
    # In public/production deployment, strictly force simulation to prevent destructive live actions
    effective_dry_run = True if settings.ENVIRONMENT == "production" else req.dry_run

    if not effective_dry_run and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Live defense execution requires Administrator authorization."
        )

    execution = response_engine.execute_action(
        action_type=req.action_type,
        target=req.target,
        executed_by=current_user.username,
        dry_run=effective_dry_run,
        incident_id=req.incident_id,
        approved_by=current_user.username if current_user.role == "admin" else None
    )
    
    db_exec = ResponseExecution(
        incident_id=req.incident_id,
        action_type=req.action_type.value,
        target=req.target,
        status=execution["status"],
        dry_run=req.dry_run,
        parameters=req.parameters,
        result_details=execution.get("result_details", {}),
        executed_by=current_user.username,
        approved_by=current_user.username if current_user.role == "admin" else None,
        executed_at=datetime.utcnow()
    )
    db.add(db_exec)
    # Fetch last audit log entry for hash chaining
    last_audit_res = await db.execute(select(AuditLog).order_by(AuditLog.timestamp.desc()))
    last_audit = last_audit_res.scalars().first()
    prev_hash = last_audit.entry_hash if last_audit else None
    
    audit_time = datetime.utcnow()
    entry_hash = AuditLog.calculate_entry_hash(
        prev_hash=prev_hash,
        user_id=current_user.id,
        action=f"EXECUTE_RESPONSE_{req.action_type.value.upper()}",
        resource_type="response_execution",
        resource_id=db_exec.id,
        timestamp=audit_time
    )

    audit_entry = AuditLog(
        user_id=current_user.id,
        action=f"EXECUTE_RESPONSE_{req.action_type.value.upper()}",
        resource_type="response_execution",
        resource_id=db_exec.id,
        details={"target": req.target, "status": execution["status"], "dry_run": req.dry_run},
        prev_hash=prev_hash,
        entry_hash=entry_hash,
        timestamp=audit_time
    )
    db.add(audit_entry)

    await db.commit()
    return execution

@api_router.get("/response/history")
async def get_response_history(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    res = await db.execute(select(ResponseExecution).order_by(ResponseExecution.created_at.desc()))
    return res.scalars().all()

# ----------------- THREAT INTEL -----------------
@api_router.get("/threat-intel")
async def get_threat_indicators(
    current_user: User = Depends(get_current_user)
):
    return list(threat_intel.ioc_database.values())

@api_router.post("/threat-intel")
async def add_threat_indicator(
    ioc: ThreatIndicatorCreate,
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.ANALYST]))
):
    threat_intel.add_indicator(ioc.dict())
    return {"status": "success", "indicator": ioc.dict()}

# ----------------- RESEARCH BENCHMARK -----------------
@api_router.post("/evaluation/run-benchmark")
async def run_evaluation(
    n_events: int = 1000,
    current_user: User = Depends(get_current_user)
):
    """Executes live reproducible benchmark across Rule, ML, and Hybrid+Graph models"""
    results = evaluation_harness.run_eval_pipeline(n_events=n_events)
    return results

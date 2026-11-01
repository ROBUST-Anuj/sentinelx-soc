"""
Real-Time Security Violation & Behavioural Correlator Engine.
Classifies and evaluates 6 security pillars:
1. Browser Behaviour & DOM anomalies (Page Visibility, blur, rapid interactions, repeated copy/paste metadata).
2. Authentication & Account Takeover (Failed OTP bursts, session reuse, credential stuffing).
3. Transaction Fraud (Velocity bursts, new beneficiary draining).
4. Beneficiary & Account Manipulation.
5. Network & Device Anomalies (Unusual User-Agent shifts, Rapid API bursts).
6. Application Security Violations (Safe SQLi test strings, XSS test probes, tampering, parameter manipulation).

Enforces backend deduplication windows and score decay to avoid naive additive score inflation.
"""

import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from app.models.db_models import SecurityViolationEvent, Event, Incident, DetectionFinding, AuditLog
from app.models.schemas import SourceType, SeverityLevel
from app.banking.storyline_engine import storyline_engine

def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)

# Regular expressions for safe application security probing detection
SQLI_PATTERN = re.compile(r"(\b(UNION(\s+ALL)?|SELECT|INSERT|DELETE|UPDATE|DROP|ALTER)\b|--|\'|\"|/\*|\*/|\bOR\s+[\'\"]?\d+[\'\"]?\s*=\s*[\'\"]?\d+|sleep\(|benchmark\()", re.IGNORECASE)
XSS_PATTERN = re.compile(r"(<script\b[^>]*>|javascript:|onerror\s*=|onload\s*=|alert\(|<img\s+src=)", re.IGNORECASE)

class SecurityViolationEngine:
    """
    Evaluates telemetry payloads, executes authoritative risk classification,
    applies time-window deduplication, and escalates to SOC incidents.
    """

    # Deduplication and Rate Windows (seconds)
    DEDUP_WINDOW_SECONDS: int = 15
    MAX_BROWSER_BURST: int = 4

    def analyze_payload_security(self, metadata: Dict[str, Any]) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Inspects freeform metadata for SQLi or XSS patterns.
        Returns: (violation_detected, attack_type, matched_rule)
        """
        for k, v in metadata.items():
            if isinstance(v, str):
                if SQLI_PATTERN.search(v):
                    return True, "SQL_INJECTION_PATTERN_DETECTED", "RULE-APP-SEC-SQLI"
                if XSS_PATTERN.search(v):
                    return True, "XSS_PROBE_PATTERN_DETECTED", "RULE-APP-SEC-XSS"
        return False, None, None

    async def ingest_violation_event(
        self,
        db: AsyncSession,
        event_type: str,
        category: str,
        customer_id: Optional[str],
        session_id: Optional[str],
        transaction_id: Optional[str],
        source_ip: str,
        device_id: Optional[str],
        source_application: str,
        metadata: Dict[str, Any],
        is_simulation: bool = False
    ) -> SecurityViolationEvent:
        now = utc_now()

        # Sanitize metadata: remove any accidentally transmitted raw OTP/password fields
        sanitized_meta = {
            k: v for k, v in metadata.items()
            if k.lower() not in ["password", "otp", "code", "secret", "token", "raw_content"]
        }

        # 1. Authoritative Backend Classification (Do not trust client-supplied severity or score)
        rule_name = f"RULE-{category.upper()}-{event_type}"
        severity = "low"
        risk_score = 5.0

        # Check for Application Security patterns in metadata
        has_app_sec_violation, app_sec_type, app_sec_rule = self.analyze_payload_security(sanitized_meta)
        if has_app_sec_violation:
            event_type = app_sec_type or event_type
            category = "application_security"
            rule_name = app_sec_rule or rule_name
            severity = "critical"
            risk_score = 85.0
        elif category == "browser_behaviour":
            # Normal tab switching is low risk; repeated switching is medium
            if event_type in ["TAB_SWITCH_BURST", "EXCESSIVE_REFRESH", "FULLSCREEN_EXIT_DURING_OTP"]:
                severity = "medium"
                risk_score = 25.0
            elif event_type == "REPEATED_PASTE_ATTEMPT":
                severity = "low"
                risk_score = 10.0
            else:
                severity = "informational"
                risk_score = 5.0
        elif category == "authentication":
            if event_type in ["FAILED_OTP_BURST", "OTP_BRUTE_FORCE", "MULTIPLE_FAILED_LOGINS"]:
                severity = "high"
                risk_score = 70.0
            elif event_type in ["SESSION_TOKEN_REUSE", "UNAUTHORIZED_ACCESS_ATTEMPT", "UNFAMILIAR_DEVICE_LOGIN"]:
                severity = "high"
                risk_score = 65.0
            else:
                severity = "medium"
                risk_score = 30.0
        elif category == "transaction_fraud":
            if event_type in ["AMOUNT_MANIPULATION_ATTEMPT", "RAPID_DRAIN_PATTERN", "CONCURRENT_TRANSACTION_BURST"]:
                severity = "critical"
                risk_score = 85.0
            elif event_type in ["RESTRICTED_BENEFICIARY_ATTEMPT"]:
                severity = "critical"
                risk_score = 90.0
            else:
                severity = "high"
                risk_score = 55.0
        elif category == "beneficiary_manipulation":
            if event_type in ["BENEFICIARY_MUTATION_PRE_TRANSFER", "RESTRICTED_BENEFICIARY_CREATED"]:
                severity = "high"
                risk_score = 75.0
            else:
                severity = "medium"
                risk_score = 35.0
        elif category == "network_anomaly":
            if event_type in ["KNOWN_MALICIOUS_IP_MATCH", "API_ENUMERATION_BURST"]:
                severity = "critical"
                risk_score = 80.0
            elif event_type in ["UNUSUAL_USER_AGENT_SHIFT", "RAPID_IP_CHANGE"]:
                severity = "medium"
                risk_score = 40.0
            else:
                severity = "low"
                risk_score = 20.0
        elif category == "application_security":
            severity = "critical"
            risk_score = 90.0

        # 2. Backend Deduplication Check within DEDUP_WINDOW_SECONDS
        window_start = now - timedelta(seconds=self.DEDUP_WINDOW_SECONDS)
        dedup_stmt = select(func.count(SecurityViolationEvent.id)).where(
            SecurityViolationEvent.event_type == event_type,
            SecurityViolationEvent.category == category,
            SecurityViolationEvent.source_ip == source_ip,
            SecurityViolationEvent.created_at >= window_start
        )
        if customer_id:
            dedup_stmt = dedup_stmt.where(SecurityViolationEvent.customer_id == customer_id)
        
        recent_count = (await db.execute(dedup_stmt)).scalar() or 0
        if recent_count > 0:
            # Dampen score contribution to avoid linear inflation
            risk_score = round(risk_score * 0.2, 1)

        correlation_id = f"corr-sec-{customer_id or source_ip.replace('.', '-')}-{now.strftime('%Y%m%d%H')}"
        incident_id = None

        # 1.5 Create persistent SecurityViolationEvent record first so correlation can reference it
        violation_event = SecurityViolationEvent(
            event_id=f"vio-{uuid.uuid4().hex[:12]}",
            event_type=event_type,
            category=category,
            severity=severity,
            timestamp=now,
            customer_id=customer_id,
            session_id=session_id,
            transaction_id=transaction_id,
            source_ip=source_ip,
            device_id=device_id,
            source_application=source_application,
            event_metadata=sanitized_meta,
            detection_rule=rule_name,
            risk_contribution=risk_score,
            correlation_id=correlation_id,
            incident_id=incident_id,
            is_simulation=is_simulation,
            created_at=now
        )
        db.add(violation_event)
        await db.flush()

        # 3. Escalate or Correlate to Unified Attack Storyline
        # First, run correlation engine to see if this event links to an existing or new multi-stage attack storyline
        storyline_inc = await storyline_engine.correlate_event(db, violation_event)
        if storyline_inc:
            incident_id = storyline_inc.id
            violation_event.incident_id = incident_id
        elif severity in ["high", "critical"] or risk_score >= 60.0:
            sev_level = SeverityLevel.CRITICAL.value if severity == "critical" else SeverityLevel.HIGH.value
            sim_prefix = "[DEMO SIMULATION] " if is_simulation else ""
            
            inc = Incident(
                title=f"{sim_prefix}Security Violation: {event_type} [{category.replace('_', ' ').title()}]",
                summary=f"Automated security detection rule {rule_name} fired. Affected customer: {customer_id or 'Anonymous'}. Severity: {severity}. Risk: {risk_score}.",
                severity=sev_level,
                status="new",
                assigned_to="tier1_analyst",
                affected_entities=[e for e in [customer_id, source_ip, transaction_id] if e],
                graph_risk_score=float(risk_score)
            )
            db.add(inc)
            await db.flush()
            incident_id = inc.id
            violation_event.incident_id = incident_id

            finding = DetectionFinding(
                detector_type="rule",
                rule_or_model_name=rule_name,
                severity=sev_level,
                title=f"{sim_prefix}{event_type} on {source_application}",
                description=f"Security telemetry trigger: {category} event observed with risk contribution {risk_score}. Metadata: {sanitized_meta}",
                evidence_events=[correlation_id],
                affected_entity=customer_id or source_ip,
                confidence=0.95,
                incident_id=incident_id,
                metadata_info={
                    "event_type": event_type,
                    "category": category,
                    "source_ip": source_ip,
                    "device_id": device_id,
                    "is_simulation": is_simulation,
                    **sanitized_meta
                }
            )
            db.add(finding)

        # 4. Canonical SOC Event Stream Recording
        soc_event = Event(
            event_id=f"evt-sec-{uuid.uuid4()}",
            timestamp=now,
            source_type=SourceType.GENERIC_JSON.value,
            source_name=source_application,
            host_id="nexabank-client-fleet",
            user_id=customer_id,
            src_ip=source_ip,
            event_type=f"BANKING_VIOLATION_{event_type}",
            severity=severity,
            raw_event=f"Violation {event_type} in {category}: score={risk_score} severity={severity} sim={is_simulation}",
            normalized_fields={
                "category": category,
                "event_type": event_type,
                "customer_id": customer_id,
                "session_id": session_id,
                "transaction_id": transaction_id,
                "source_ip": source_ip,
                "device_id": device_id,
                "risk_contribution": risk_score,
                "is_simulation": is_simulation,
                **sanitized_meta
            }
        )
        db.add(soc_event)

        # 5. Commit audit and changes
        audit = AuditLog(
            user_id=customer_id or f"ip:{source_ip}",
            action=f"SECURITY_VIOLATION:{event_type}",
            resource_type="SecurityViolationEvent",
            resource_id=violation_event.event_id,
            details={"category": category, "severity": severity, "score": risk_score},
            ip_address=source_ip,
            prev_hash="VIOLATION_STREAM",
            entry_hash=AuditLog.calculate_entry_hash(
                "VIOLATION_STREAM", customer_id or source_ip, f"VIOLATION:{event_type}", "Violation", violation_event.event_id, now
            ),
            timestamp=now
        )
        db.add(audit)
        await db.commit()
        await db.refresh(violation_event)

        return violation_event

violation_engine = SecurityViolationEngine()

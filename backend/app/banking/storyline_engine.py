"""
SentinelX Unified Attack Storyline & Behavioural Correlation Engine.
Correlates multi-stage security violations into coherent, multi-hop Attack Storylines.

Multi-Stage Correlation Patterns Detected:
1. ACCOUNT TAKEOVER (ATO) KILL-CHAIN:
   Unfamiliar device/login + Repeated Failed OTP / Bursts + High-Value Transfer.
2. COMPROMISED BENEFICIARY / MONEY MULE:
   New Beneficiary Created + Rapid Burst Transfer + Suspicious/Restricted Destination.
3. SOCIAL ENGINEERING / DOM INTERFERENCE:
   Tab/Focus Anomalies + OTP Failure/Challenge + Sensitive Banking Operation.
4. TARGETED RECON & NETWORK EGRESS:
   Malicious IP/Tor Node + Rapid Device/Session Drift + Account Access / Enumeration.
5. APPLICATION TAMPERING & EXPLOIT ATTEMPT:
   Multiple Unauthorized/SQLi/XSS Probes + Transaction Amount / Status Tampering.

Features:
- Configurable correlation windows (default: 30 minutes).
- Deduplicates ongoing incidents: reuses and attaches new events to existing active incidents rather than creating redundant tickets.
- Assembles rich Attack Storyline with unified timeline, severity scoring, and SOC playbook investigation steps.
- Supports lifecycle transitions: NEW -> INVESTIGATING -> CONTAINED -> RESOLVED.
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.models.db_models import (
    Incident, DetectionFinding, SecurityViolationEvent, Event, AuditLog
)
from app.models.schemas import SeverityLevel

def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)

class AttackStorylineEngine:
    """
    Stateful Behavioral Correlator for multi-event attack sequences.
    """

    # Correlation sliding window in minutes
    CORRELATION_WINDOW_MINUTES: int = 30

    # Pattern definitions: list of required / reinforcing event markers
    PATTERNS = [
        {
            "category": "ACCOUNT_TAKEOVER_CHAIN",
            "title": "Correlated Account Takeover (ATO) Sequence",
            "required_signals": [
                {"UNFAMILIAR_DEVICE_LOGIN", "SESSION_TOKEN_REUSE"},
                {"FAILED_OTP_BURST", "OTP_BRUTE_FORCE", "WINDOW_BLUR_DURING_TRANSACTION"},
            ],
            "reinforcing_signals": ["HIGH_TRANSACTION_VELOCITY", "AMOUNT_MANIPULATION_ATTEMPT", "NEW_ACCOUNT_HIGH_DRAIN"],
            "severity": SeverityLevel.CRITICAL.value,
            "recommended_playbook": [
                "Immediately revoke active JWT session tokens for customer account.",
                "Enforce administrative hold on source bank account.",
                "Contact customer via out-of-band verified phone to verify transfer legitimacy.",
                "Review device fingerprint and IP autonomous system reputation."
            ]
        },
        {
            "category": "BENEFICIARY_MULE_SCHEME",
            "title": "Mule Beneficiary Mutation & Drain Pattern",
            "required_signals": [
                {"BENEFICIARY_MUTATION_PRE_TRANSFER", "RESTRICTED_BENEFICIARY_CREATED"},
                {"RESTRICTED_BENEFICIARY_ATTEMPT", "RAPID_DRAIN_PATTERN", "DESTINATION_ACCOUNT_RESTRICTED"}
            ],
            "reinforcing_signals": ["RAPID_SUCCESSION_BURST", "HIGH_TRANSACTION_VELOCITY"],
            "severity": SeverityLevel.CRITICAL.value,
            "recommended_playbook": [
                "Place freeze on recipient beneficiary account and linked settlement rails.",
                "Review ledger entries for matching mule syndicate accounts.",
                "Verify beneficiary creation timestamps and IP geolocation shift."
            ]
        },
        {
            "category": "BROWSER_DOM_INTERFERENCE",
            "title": "Suspicious Tab Switching & Verification Interference",
            "required_signals": [
                {"TAB_SWITCH_BURST", "WINDOW_BLUR_DURING_TRANSACTION", "FULLSCREEN_EXIT_DURING_OTP"},
                {"FAILED_OTP_BURST", "REPEATED_PASTE_ATTEMPT"}
            ],
            "reinforcing_signals": ["HIGH_TRANSACTION_VELOCITY"],
            "severity": SeverityLevel.HIGH.value,
            "recommended_playbook": [
                "Inspect user session for signs of remote assistance software or screen sharing.",
                "Prompt customer with step-up hardware or biometric challenge.",
                "Confirm customer was not guided by an external unauthorized third party."
            ]
        },
        {
            "category": "TARGETED_NETWORK_INTRUSION",
            "title": "Malicious Threat Intel Node & Access Recon",
            "required_signals": [
                {"KNOWN_MALICIOUS_IP_MATCH", "THREAT_INTEL_MALICIOUS_IP"},
                {"UNFAMILIAR_DEVICE_LOGIN", "API_ENUMERATION_BURST", "UNAUTHORIZED_ACCESS_ATTEMPT"}
            ],
            "reinforcing_signals": ["SESSION_TOKEN_REUSE"],
            "severity": SeverityLevel.CRITICAL.value,
            "recommended_playbook": [
                "Block offending IP CIDR block at the ingress API gateway.",
                "Audit all API queries associated with origin session and device ID.",
                "Verify whether credential stuffing list was weaponized against banking API."
            ]
        },
        {
            "category": "APPLICATION_EXPLOIT_ATTEMPT",
            "title": "Web Application Tampering & Injection Attack",
            "required_signals": [
                {"SQL_INJECTION_PATTERN_DETECTED", "XSS_PROBE_PATTERN_DETECTED", "INPUT_FIELD_PROBE"}
            ],
            "reinforcing_signals": ["AMOUNT_MANIPULATION_ATTEMPT"],
            "severity": SeverityLevel.CRITICAL.value,
            "recommended_playbook": [
                "Validate input sanitization across customer memo and beneficiary name inputs.",
                "Isolate offending client session and terminate active database connections.",
                "Cross-check backend database logs for syntax errors or unexpected exceptions."
            ]
        }
    ]

    async def correlate_event(
        self,
        db: AsyncSession,
        new_event: SecurityViolationEvent
    ) -> Optional[Incident]:
        """
        Analyzes a newly ingested SecurityViolationEvent alongside recent session/customer history.
        Attaches the event to an existing active Incident if part of an ongoing storyline,
        or creates a unified Attack Storyline incident when a multi-stage correlation pattern matches.
        """
        now = utc_now()
        window_start = now - timedelta(minutes=self.CORRELATION_WINDOW_MINUTES)

        # 1. Gather recent violation events belonging to same customer, session, or IP
        query = select(SecurityViolationEvent).where(
            SecurityViolationEvent.created_at >= window_start
        )
        if new_event.customer_id:
            query = query.where(
                (SecurityViolationEvent.customer_id == new_event.customer_id) |
                (SecurityViolationEvent.session_id == new_event.session_id) |
                (SecurityViolationEvent.source_ip == new_event.source_ip)
            )
        elif new_event.session_id:
            query = query.where(SecurityViolationEvent.session_id == new_event.session_id)
        else:
            query = query.where(SecurityViolationEvent.source_ip == new_event.source_ip)

        query = query.order_by(SecurityViolationEvent.created_at.asc())
        res = await db.execute(query)
        recent_events = res.scalars().all()

        # Build set of event types seen in this correlation window
        event_types = {e.event_type for e in recent_events}
        event_types.add(new_event.event_type)

        # 2. Check if there is an existing ACTIVE (not resolved/dismissed) incident for this cluster
        active_incident: Optional[Incident] = None
        for ev in recent_events:
            if ev.incident_id:
                inc_res = await db.execute(
                    select(Incident).where(
                        Incident.id == ev.incident_id,
                        Incident.status.in_(["new", "investigating", "contained"])
                    )
                )
                existing_inc = inc_res.scalars().first()
                if existing_inc:
                    active_incident = existing_inc
                    break

        # 3. Match against Attack Storyline Patterns
        matched_pattern = None
        for pat in self.PATTERNS:
            req_signals = pat["required_signals"]
            # All required signal sets must have at least one match
            all_req_matched = all(any(s in event_types for s in sig_set) for sig_set in req_signals)
            if all_req_matched:
                matched_pattern = pat
                break

        sim_prefix = "[DEMO SIMULATION] " if new_event.is_simulation else ""

        # 4. If an active incident exists, UPDATE it rather than creating a duplicate
        if active_incident:
            new_event.incident_id = active_incident.id
            active_incident.last_seen = now
            
            # Elevate severity if new event is critical
            if new_event.severity == "critical" and active_incident.severity != "critical":
                active_incident.severity = "critical"
            
            # Incorporate new entity IDs
            current_entities = set(active_incident.affected_entities or [])
            if new_event.customer_id: current_entities.add(new_event.customer_id)
            if new_event.source_ip: current_entities.add(new_event.source_ip)
            if new_event.transaction_id: current_entities.add(new_event.transaction_id)
            active_incident.affected_entities = list(current_entities)

            # Update score
            active_incident.graph_risk_score = min(
                100.0,
                active_incident.graph_risk_score + float(new_event.risk_contribution)
            )

            # If an advanced multi-stage pattern was just unlocked, upgrade incident title
            if matched_pattern and "Sequence" not in active_incident.title and "Pattern" not in active_incident.title:
                active_incident.title = f"{sim_prefix}{matched_pattern['title']} (Customer: {new_event.customer_id or 'Unknown'})"
                active_incident.summary += f" | Correlated progression: {matched_pattern['category']} unlocked."

            # Add finding linking to existing incident
            meta = dict(new_event.event_metadata or {})
            if matched_pattern:
                meta["playbook"] = matched_pattern["recommended_playbook"]
                meta["pattern_category"] = matched_pattern["category"]

            finding = DetectionFinding(
                detector_type="hybrid",
                rule_or_model_name=new_event.detection_rule,
                severity=new_event.severity,
                title=f"{sim_prefix}{new_event.event_type} Linked to Incident",
                description=f"Correlated event '{new_event.event_type}' attached to ongoing attack storyline {active_incident.id}.",
                evidence_events=[new_event.event_id],
                affected_entity=new_event.customer_id or new_event.source_ip,
                confidence=0.96,
                incident_id=active_incident.id,
                metadata_info=meta
            )
            db.add(finding)
            await db.commit()
            return active_incident

        # 5. If no active incident exists, check if matched pattern warrants NEW Storyline Incident
        if matched_pattern:
            inc_title = f"{sim_prefix}{matched_pattern['title']} (Customer: {new_event.customer_id or 'Unknown'})"
            inc_summary = (
                f"Multi-stage {matched_pattern['category']} detected in {self.CORRELATION_WINDOW_MINUTES}m window. "
                f"Correlated {len(recent_events) + 1} events across session {new_event.session_id or 'N/A'}. "
                f"Recommended first step: {matched_pattern['recommended_playbook'][0]}"
            )

            all_entities = set()
            for e in recent_events + [new_event]:
                if e.customer_id: all_entities.add(e.customer_id)
                if e.source_ip: all_entities.add(e.source_ip)
                if e.transaction_id: all_entities.add(e.transaction_id)

            total_risk = sum(e.risk_contribution for e in recent_events) + new_event.risk_contribution
            capped_score = min(100.0, max(50.0, total_risk))

            incident = Incident(
                title=inc_title,
                summary=inc_summary,
                severity=matched_pattern["severity"],
                status="new",
                assigned_to="tier1_analyst",
                first_seen=recent_events[0].created_at if recent_events else now,
                last_seen=now,
                affected_entities=list(all_entities),
                threat_intel_matches=[],
                graph_risk_score=float(capped_score)
            )
            db.add(incident)
            await db.flush()

            # Attach incident ID to all correlated events in this storyline
            new_event.incident_id = incident.id
            for e in recent_events:
                if not e.incident_id:
                    e.incident_id = incident.id

            # Create primary Detection Finding
            finding = DetectionFinding(
                detector_type="hybrid",
                rule_or_model_name=f"RULE-CORRELATION-{matched_pattern['category']}",
                severity=matched_pattern["severity"],
                title=f"{sim_prefix}Unified Storyline: {matched_pattern['category']}",
                description=inc_summary,
                evidence_events=[e.event_id for e in recent_events + [new_event]],
                affected_entity=new_event.customer_id or new_event.source_ip,
                confidence=0.98,
                incident_id=incident.id,
                metadata_info={
                    "pattern_category": matched_pattern["category"],
                    "playbook": matched_pattern["recommended_playbook"],
                    "event_types": list(event_types)
                }
            )
            db.add(finding)
            await db.commit()
            return incident

        return None

storyline_engine = AttackStorylineEngine()

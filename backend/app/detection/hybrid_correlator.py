from typing import List, Dict, Any, Tuple
from collections import defaultdict
from datetime import datetime, timezone
from app.models.schemas import CanonicalEvent, SeverityLevel, IncidentStatus
from app.detection.rule_engine import rule_engine, RuleResult
from app.detection.ml_engine import ml_detector
from app.threat_intel.manager import threat_intel
import uuid

class HybridCorrelator:
    """
    Detector C: Fuses Rule findings, Machine Learning predictions, Threat Intelligence hits,
    and Graph-aware temporal entity clustering into fully correlated SOC Incidents.
    """
    def __init__(self):
        self.CORRELATION_WINDOW_SECONDS = 3600  # 1 hour window

    def process_and_correlate(
        self,
        events: List[CanonicalEvent]
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
        all_findings: List[Dict[str, Any]] = []

        # 1. Detector A: Rule-Based Detection
        rule_results: List[RuleResult] = rule_engine.evaluate(events)
        for r in rule_results:
            all_findings.append({
                "id": str(uuid.uuid4()),
                "detector_type": "rule",
                "rule_or_model_name": r.rule_id,
                "severity": r.severity.value,
                "title": r.title,
                "description": r.description,
                "evidence_events": r.evidence_events,
                "affected_entity": r.affected_entity,
                "confidence": r.confidence,
                "metadata": r.metadata,
                "created_at": datetime.now(timezone.utc).isoformat()
            })

        # 2. Detector B: Machine Learning Detection
        ml_results = ml_detector.predict_events(events)
        for m in ml_results:
            m["id"] = str(uuid.uuid4())
            m["created_at"] = datetime.now(timezone.utc).isoformat()
            if hasattr(m["severity"], "value"):
                m["severity"] = m["severity"].value
            all_findings.append(m)

        # 3. Threat Intelligence Matching
        ti_matches = threat_intel.match_events(events)
        for match in ti_matches:
            all_findings.append({
                "id": str(uuid.uuid4()),
                "detector_type": "threat_intel",
                "rule_or_model_name": f"IOC-MATCH-{match['threat_type'].upper()}",
                "severity": match["severity"],
                "title": f"Threat Intel Match: {match['threat_type'].replace('_', ' ').title()}",
                "description": f"Telemetry field '{match['matched_field']}' matched known indicator '{match['indicator_value']}' from {match['source']}.",
                "evidence_events": [match["event_id"]],
                "affected_entity": match["indicator_value"],
                "confidence": match["confidence"],
                "metadata": match,
                "created_at": datetime.now(timezone.utc).isoformat()
            })

        # 4. Hybrid Graph-Aware Entity Clustering into Incidents
        correlated_incidents = self._cluster_findings_into_incidents(all_findings, events, ti_matches)

        return all_findings, correlated_incidents, ti_matches

    def _cluster_findings_into_incidents(
        self,
        findings: List[Dict[str, Any]],
        events: List[CanonicalEvent],
        ti_matches: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        if not findings:
            return []

        event_time_map = {e.event_id: e.timestamp for e in events}

        entity_to_findings = defaultdict(list)
        for f in findings:
            ent = f.get("affected_entity") or "unattributed_entity"
            entity_to_findings[ent].append(f)

        incidents = []
        for entity, f_list in entity_to_findings.items():
            inc_id = str(uuid.uuid4())
            all_evidence_ids = []
            for f in f_list:
                all_evidence_ids.extend(f.get("evidence_events", []))
                f["incident_id"] = inc_id

            timestamps = [event_time_map[eid] for eid in all_evidence_ids if eid in event_time_map]
            first_seen = min(timestamps) if timestamps else datetime.now(timezone.utc)
            last_seen = max(timestamps) if timestamps else datetime.now(timezone.utc)

            has_crit = any(f["severity"] == "critical" for f in f_list)
            has_high = any(f["severity"] == "high" for f in f_list)
            inc_severity = "critical" if has_crit else ("high" if (has_high or len(f_list) > 2) else "medium")

            matched_iocs = [m["indicator_value"] for m in ti_matches if m.get("indicator_value") == entity or m.get("event_id") in all_evidence_ids]

            rule_count = sum(1 for f in f_list if f["detector_type"] == "rule")
            ml_count = sum(1 for f in f_list if f["detector_type"] == "ml")
            ti_count = sum(1 for f in f_list if f["detector_type"] == "threat_intel")

            summary = (
                f"Correlated security incident targeting '{entity}'. "
                f"Encompasses {len(f_list)} findings ({rule_count} Rule detections, {ml_count} ML detections, {ti_count} TI matches) "
                f"across {len(set(all_evidence_ids))} telemetry events."
            )

            incidents.append({
                "id": inc_id,
                "title": f"Incident Campaign: Activity on {entity}",
                "summary": summary,
                "status": IncidentStatus.NEW.value,
                "severity": inc_severity,
                "assigned_to": None,
                "findings_count": len(f_list),
                "first_seen": first_seen.isoformat(),
                "last_seen": last_seen.isoformat(),
                "affected_entities": [entity],
                "threat_intel_matches": list(set(matched_iocs)),
                "graph_risk_score": min(9.9, round(2.0 + (len(f_list) * 1.5) + (3.0 if inc_severity == 'critical' else 1.0), 2)),
                "findings": f_list,
                "created_at": datetime.now(timezone.utc).isoformat()
            })

        return incidents

hybrid_correlator = HybridCorrelator()

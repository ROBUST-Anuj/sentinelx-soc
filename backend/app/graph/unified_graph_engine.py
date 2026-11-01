"""
Unified Multi-Domain Attack Graph Engine.
Traverses and correlates entities across traditional telemetry, banking domain objects,
threat intelligence indicators, security violations, attack storylines, and containment actions.

Node Types:
- Customer
- BankAccount
- Beneficiary
- IPAddress
- Device
- Session
- Transaction
- SecurityViolation
- Incident
- ThreatIndicator
- ResponseAction

Edge Types:
- LOGGED_IN_FROM
- INITIATED
- TRANSFERRED_TO
- ASSOCIATED_WITH
- TRIGGERED
- CORRELATED_WITH
- MATCHED_INDICATOR
- RESPONDED_TO
"""

import networkx as nx
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.db_models import (
    Incident, DetectionFinding, SecurityViolationEvent, ResponsePlaybookAction,
    ThreatIndicator, BankAccount, Transfer, Event, User
)

class UnifiedAttackGraphEngine:
    def __init__(self):
        self.graph = nx.DiGraph()

    async def build_incident_graph(
        self,
        db: AsyncSession,
        incident_id: str
    ) -> Dict[str, Any]:
        """
        Builds a comprehensive, evidence-linked multi-domain graph for a specific incident.
        """
        self.graph.clear()

        # 1. Fetch Incident
        inc_res = await db.execute(select(Incident).where(Incident.id == incident_id))
        incident = inc_res.scalars().first()
        if not incident:
            return {"node_count": 0, "edge_count": 0, "nodes": [], "edges": []}

        inc_node = f"incident:{incident.id}"
        self.graph.add_node(
            inc_node,
            node_type="Incident",
            label=f"INC-{incident.id[:8]}",
            title=incident.title,
            severity=incident.severity,
            status=incident.status,
            risk_score=incident.graph_risk_score
        )

        # 2. Fetch Findings linked to Incident
        f_res = await db.execute(select(DetectionFinding).where(DetectionFinding.incident_id == incident.id))
        findings = f_res.scalars().all()

        for f in findings:
            f_node = f"finding:{f.id}"
            self.graph.add_node(
                f_node,
                node_type="Finding",
                label=f.title[:24] + "...",
                rule_name=f.rule_or_model_name,
                severity=f.severity,
                confidence=f.confidence
            )
            self.graph.add_edge(f_node, inc_node, relation="CORRELATED_WITH", evidence="Finding associated with incident cluster")

        # 3. Fetch linked Security Violation Events
        vio_res = await db.execute(
            select(SecurityViolationEvent).where(SecurityViolationEvent.incident_id == incident.id)
        )
        violations = vio_res.scalars().all()

        for v in violations:
            v_node = f"violation:{v.event_id}"
            self.graph.add_node(
                v_node,
                node_type="SecurityViolation",
                label=v.event_type,
                category=v.category,
                severity=v.severity,
                risk_score=v.risk_contribution
            )
            self.graph.add_edge(v_node, inc_node, relation="TRIGGERED", evidence="Telemetry event flagged during correlation window")

            # Link Customer
            if v.customer_id:
                cust_node = f"customer:{v.customer_id}"
                if not self.graph.has_node(cust_node):
                    self.graph.add_node(cust_node, node_type="Customer", label=v.customer_id, severity="medium")
                self.graph.add_edge(cust_node, v_node, relation="INITIATED", evidence="Customer account identity linked to telemetry")

            # Link Session
            if v.session_id:
                sess_node = f"session:{v.session_id}"
                if not self.graph.has_node(sess_node):
                    self.graph.add_node(sess_node, node_type="Session", label=v.session_id[:16], severity="medium")
                self.graph.add_edge(sess_node, v_node, relation="ASSOCIATED_WITH", evidence="Session token active during violation")
                if v.customer_id:
                    self.graph.add_edge(f"customer:{v.customer_id}", sess_node, relation="LOGGED_IN_FROM", evidence="Customer authenticated session")

            # Link IP Address
            if v.source_ip:
                ip_node = f"ip:{v.source_ip}"
                if not self.graph.has_node(ip_node):
                    self.graph.add_node(ip_node, node_type="IPAddress", label=v.source_ip, severity="medium")
                self.graph.add_edge(ip_node, v_node, relation="LOGGED_IN_FROM", evidence="Observed origin IP address")

            # Link Device
            if v.device_id:
                dev_node = f"device:{v.device_id[:16]}"
                if not self.graph.has_node(dev_node):
                    self.graph.add_node(dev_node, node_type="Device", label=v.device_id[:16], severity="low")
                self.graph.add_edge(dev_node, v_node, relation="ASSOCIATED_WITH", evidence="Client user-agent and device profile")

            # Link Transaction
            if v.transaction_id:
                tx_node = f"transaction:{v.transaction_id}"
                if not self.graph.has_node(tx_node):
                    self.graph.add_node(tx_node, node_type="Transaction", label=v.transaction_id[:12], severity="high")
                self.graph.add_edge(v_node, tx_node, relation="ASSOCIATED_WITH", evidence="Transaction under active security evaluation")

        # 4. Fetch related Bank Accounts and Transfers
        affected_entities = incident.affected_entities or []
        for ent in affected_entities:
            # Check if entity is account number
            if ent.startswith("ACT-"):
                acc_node = f"account:{ent}"
                if not self.graph.has_node(acc_node):
                    self.graph.add_node(acc_node, node_type="BankAccount", label=ent, severity="medium")
                self.graph.add_edge(acc_node, inc_node, relation="ASSOCIATED_WITH", evidence="Account listed in affected entities")

        # 5. Correlate with Threat Indicators (IP matches or restricted beneficiary)
        ti_res = await db.execute(select(ThreatIndicator).where(ThreatIndicator.is_active == True))
        indicators = ti_res.scalars().all()
        for ti in indicators:
            target_ip_node = f"ip:{ti.value}"
            if self.graph.has_node(target_ip_node):
                ti_node = f"threat_intel:{ti.id}"
                self.graph.add_node(
                    ti_node,
                    node_type="ThreatIndicator",
                    label=f"IOC: {ti.threat_type}",
                    value=ti.value,
                    severity=ti.severity,
                    source=ti.source
                )
                self.graph.add_edge(target_ip_node, ti_node, relation="MATCHED_INDICATOR", evidence=f"Origin IP matches active feed {ti.source}")

            # Check beneficiary match
            target_acc_node = f"account:{ti.value}"
            if self.graph.has_node(target_acc_node):
                ti_node = f"threat_intel:{ti.id}"
                self.graph.add_node(
                    ti_node,
                    node_type="ThreatIndicator",
                    label=f"Restricted Account: {ti.threat_type}",
                    value=ti.value,
                    severity=ti.severity,
                    source=ti.source
                )
                self.graph.add_edge(target_acc_node, ti_node, relation="MATCHED_INDICATOR", evidence="Beneficiary marked restricted in threat intel")

        # 6. Fetch Response Actions linked to Incident
        act_res = await db.execute(select(ResponsePlaybookAction).where(ResponsePlaybookAction.incident_id == incident.id))
        actions = act_res.scalars().all()
        for act in actions:
            act_node = f"action:{act.action_id}"
            self.graph.add_node(
                act_node,
                node_type="ResponseAction",
                label=act.action_type,
                status=act.status,
                risk_level=act.risk_level,
                severity="critical" if act.status == "EXECUTED" else "medium"
            )
            self.graph.add_edge(inc_node, act_node, relation="RESPONDED_TO", evidence=f"Containment action {act.status}")
            
            # Connect action to target entity
            target_ref = act.target_entity
            for prefix in ["session:", "account:", "ip:", "customer:", "transaction:"]:
                cand = f"{prefix}{target_ref}"
                if self.graph.has_node(cand):
                    self.graph.add_edge(act_node, cand, relation="RESPONDED_TO", evidence="Containment enforced directly on target")

        # Export formatted JSON
        nodes = []
        for n, d in self.graph.nodes(data=True):
            nodes.append({
                "id": n,
                "label": d.get("label", n),
                "type": d.get("node_type", "Entity"),
                "severity": d.get("severity", "low"),
                "risk_score": d.get("risk_score", 0.0),
                "metadata": {k: v for k, v in d.items() if k not in ["label", "node_type"]}
            })

        edges = []
        for u, v, d in self.graph.edges(data=True):
            edges.append({
                "source": u,
                "target": v,
                "relation": d.get("relation", "ASSOCIATED_WITH"),
                "evidence": d.get("evidence", "Observed relation")
            })

        return {
            "incident_id": incident.id,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "nodes": nodes,
            "edges": edges
        }

unified_graph_engine = UnifiedAttackGraphEngine()

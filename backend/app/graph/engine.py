import networkx as nx
from typing import List, Dict, Any, Tuple
from app.models.schemas import CanonicalEvent, SeverityLevel
import json

class AttackGraphEngine:
    """
    Constructs multi-entity attack graphs using NetworkX.
    Nodes represent entities (Host, User, IP, Process, Finding, Incident).
    Edges represent typed observed actions (AUTH_TO, EXEC_PROCESS, CONNECT_TO, TRIGGERED, PART_OF).
    Computes graph centrality, risk scores, and reconstructs incident timelines.
    """
    def __init__(self):
        self.graph = nx.DiGraph()

    def build_from_telemetry_and_findings(
        self,
        events: List[CanonicalEvent],
        findings: List[Dict[str, Any]],
        incident_id: str = None
    ) -> nx.DiGraph:
        self.graph.clear()
        
        # 1. Add Incident root if provided
        if incident_id:
            self.graph.add_node(
                f"incident:{incident_id}",
                node_type="incident",
                label=f"Incident {incident_id[:8]}",
                severity="high"
            )

        # 2. Add events and basic entity nodes
        for ev in events:
            ev_node = f"event:{ev.event_id}"
            self.graph.add_node(
                ev_node,
                node_type="event",
                label=ev.event_type,
                timestamp=ev.timestamp.isoformat(),
                severity=ev.severity.value
            )
            
            # Host entity
            if ev.host_id:
                host_node = f"host:{ev.host_id}"
                self.graph.add_node(host_node, node_type="host", label=ev.host_id)
                self.graph.add_edge(host_node, ev_node, relation="GENERATED_EVENT")
                
            # User entity
            if ev.user_id:
                user_node = f"user:{ev.user_id}"
                self.graph.add_node(user_node, node_type="user", label=ev.user_id)
                self.graph.add_edge(user_node, ev_node, relation="PERFORMED_BY")
                if ev.host_id:
                    self.graph.add_edge(user_node, f"host:{ev.host_id}", relation="AUTHENTICATED_ON")

            # Source IP entity
            if ev.src_ip:
                ip_node = f"ip:{ev.src_ip}"
                self.graph.add_node(ip_node, node_type="ip", label=ev.src_ip)
                self.graph.add_edge(ip_node, ev_node, relation="ORIGIN_IP")

            # Destination IP entity
            if ev.dst_ip:
                dst_node = f"ip:{ev.dst_ip}"
                self.graph.add_node(dst_node, node_type="ip", label=ev.dst_ip)
                self.graph.add_edge(ev_node, dst_node, relation="CONNECTED_TO")

            # Process entity
            if ev.process_name:
                proc_node = f"proc:{ev.process_name}"
                self.graph.add_node(proc_node, node_type="process", label=ev.process_name)
                self.graph.add_edge(ev_node, proc_node, relation="EXECUTED")

        # 3. Add Detection Findings
        for f in findings:
            f_id = f.get("id") or f.get("rule_or_model_name", "finding")
            f_node = f"finding:{f_id}"
            self.graph.add_node(
                f_node,
                node_type="finding",
                label=f.get("title", "Finding"),
                confidence=f.get("confidence", 0.8),
                severity=f.get("severity", "medium") if isinstance(f.get("severity"), str) else f.get("severity").value
            )
            
            # Link finding to evidence events
            for e_id in f.get("evidence_events", []):
                ev_ref = f"event:{e_id}"
                if self.graph.has_node(ev_ref):
                    self.graph.add_edge(ev_ref, f_node, relation="EVIDENCED_BY")
                    
            if incident_id:
                self.graph.add_edge(f_node, f"incident:{incident_id}", relation="CORRELATED_INTO")

        return self.graph

    def calculate_entity_risk_scores(self) -> Dict[str, float]:
        """Calculates normalized entity risk scores using PageRank centrality and finding weights"""
        if len(self.graph) == 0:
            return {}
        try:
            pagerank = nx.pagerank(self.graph, alpha=0.85)
        except Exception:
            pagerank = {node: 1.0 / len(self.graph) for node in self.graph.nodes()}
            
        risk_scores = {}
        for node, pr in pagerank.items():
            node_data = self.graph.nodes[node]
            ntype = node_data.get("node_type", "unknown")
            # Amplify risk if connected to critical/high findings
            finding_boost = 1.0
            if ntype in ["user", "host", "ip"]:
                neighbors = list(self.graph.neighbors(node)) + list(self.graph.predecessors(node))
                for n in neighbors:
                    if self.graph.nodes[n].get("node_type") == "finding":
                        sev = self.graph.nodes[n].get("severity", "low")
                        if sev in ["high", "critical"]:
                            finding_boost += 2.5
                        elif sev == "medium":
                            finding_boost += 1.5
            
            risk_scores[node] = round(min(10.0, pr * 100.0 * finding_boost), 2)
            
        return risk_scores

    def export_graph_json(self) -> Dict[str, Any]:
        """Converts graph to frontend-friendly Cytoscape/Vis.js nodes and edges"""
        risk_scores = self.calculate_entity_risk_scores()
        nodes = []
        for n, data in self.graph.nodes(data=True):
            nodes.append({
                "id": n,
                "label": data.get("label", n),
                "type": data.get("node_type", "entity"),
                "severity": data.get("severity", "low"),
                "risk_score": risk_scores.get(n, 0.0),
                "metadata": {k: v for k, v in data.items() if k not in ["label", "node_type"]}
            })
            
        edges = []
        for u, v, data in self.graph.edges(data=True):
            edges.append({
                "source": u,
                "target": v,
                "relation": data.get("relation", "ASSOCIATED_WITH")
            })
            
        return {
            "node_count": len(nodes),
            "edge_count": len(edges),
            "nodes": nodes,
            "edges": edges
        }

attack_graph_engine = AttackGraphEngine()

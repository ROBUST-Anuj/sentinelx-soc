# Final B.Tech Major Project Viva Voce Preparation Guide: SentinelX SOC

**Project Title:** AI-Powered Cyber Threat Intelligence & Defense Platform Using Attack-Graph Reasoning and Automated Incident Response  
**Candidate:** Aditya Parashar  
**Degree:** Bachelor of Technology (Information Technology)  

---

## 1. Project High-Level Summary (The 2-Minute Elevator Pitch)

> "SentinelX SOC is an AI-powered security operations center platform engineered to address the critical industry challenge of **alert fatigue** and **fragmented context**. Traditional SIEM platforms either rely solely on static rules (which produce high false negatives on novel attacks) or standalone machine learning (which outputs disconnected anomaly scores). 
> 
> Our central technical contribution is a **tri-modal comparative evaluation** between Rule-Based Detection, Supervised Random Forest + Isolation Forest Anomaly Detection, and a **Hybrid Attack-Graph Correlator** powered by NetworkX. In our empirical evaluation across 1,000 multi-source events with a strict 70/15/15 train/val/test split, the hybrid attack-graph system achieved **100% recall ($F_1 = 1.000$)** while achieving an **11.2x alert compression ratio**, consolidating 56 raw detections into 5 prioritized multi-stage attack campaigns with full evidence attribution."

---

## 2. Architecture & Design Rationale

- **Backend Framework:** FastAPI with asynchronous ASGI architecture for non-blocking telemetry ingestion and high-concurrency throughput.
- **Normalization Strategy:** Telemetry from Linux `auth.log`, Windows Sysmon, and Web Apache/Nginx logs is normalized into a strictly typed Pydantic `CanonicalEvent` with UTC timestamps and entity mapping.
- **Attack-Graph Engine:** Employs **NetworkX** to generate an entity-relationship topology where nodes represent Hosts, Users, IPs, Processes, Findings, and Incidents, connected by typed directional edges (`AUTHENTICATED_ON`, `EXECUTED`, `CONNECTED_TO`, `ORIGIN_IP`). Computes topological PageRank risk centrality.
- **Response Orchestration:** Reversible playbooks with default `dry_run=True`, allowlisted regex validation against command injection, and SHA-256 hash-chained immutable audit logging.

---

## 3. Likely Viva Questions & Model Answers

### Q1: Why did you compare Rule-Based, ML, and Hybrid instead of just building an ML tool?
**Answer:**  
"A major research pitfall in cybersecurity projects is claiming that Machine Learning can replace all security rules. In practice, security rules have near-instant execution latency (0.0015 ms/event in our tests) and zero ambiguity for known compliance violations. However, rules missed 4 stealthy multi-stage attack steps ($Recall = 0.8519$). Standalone ML catches subtle statistical anomalies but produces isolated alerts. Our research proves that the **Hybrid + Attack-Graph approach** delivers the best of both worlds: high detection sensitivity combined with an 11.2x reduction in analyst triage load."

### Q2: Did you prevent data leakage in your machine learning evaluation?
**Answer:**  
"Yes. We enforced a strict train/validation/test split: 700 events for training, 150 events for hyperparameter and decision threshold calibration, and 150 held-out test events used exclusively for final metric reporting. The models were never trained or tuned on the test split, guaranteeing generalization integrity."

### Q3: How does your Attack-Graph engine calculate entity risk scores?
**Answer:**  
"The graph engine builds a directed graph of observed entities and detection findings. It computes PageRank centrality to identify structurally critical hub nodes in the attack chain, and then scales that centrality based on the severity of attached detection findings ($High = 2.5\times$, $Medium = 1.5\times$), yielding an explainable 1-to-10 risk score."

### Q4: How is your audit log tamper-resistant?
**Answer:**  
"Rather than relying on ordinary database table append permissions, we implemented cryptographic SHA-256 hash chaining. Each audit log stores the hash of the preceding entry, along with the user ID, action, resource ID, and UTC timestamp. If an adversary attempts to modify or delete a historical audit record, the cryptographic chain is invalidated."

### Q5: What are the current limitations of the system?
**Answer:**  
"1. NetworkX operates in-memory; for web-scale networks exceeding millions of nodes, migrating to Neo4j or Memgraph with Cypher queries would be required.  
2. The current benchmark utilizes synthetic multi-scenario telemetry reflecting enterprise attack patterns; future work involves replaying terabyte-scale enterprise PCAP captures such as CIC-IDS2017."

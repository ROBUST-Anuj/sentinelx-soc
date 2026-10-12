# Research Methodology & Evaluation Report

**Project Title:** AI-Powered Cyber Threat Intelligence & Defense Platform Using Attack-Graph Reasoning and Automated Incident Response  
**Author:** Aditya Parashar  
**Program:** Final-Year B.Tech Major Project in Information Technology  

---

## 1. Abstract
Contemporary Security Operations Centers (SOCs) face an overwhelming volume of alerts, resulting in analyst alert fatigue and fragmented context. This study develops and evaluates **SentinelX SOC**, an end-to-end detection and response platform that comparatively evaluates:
1. **Deterministic Rule-Based Detection**
2. **Machine-Learning Detection (Random Forest + Isolation Forest)**
3. **Hybrid Detection combined with Topological Attack-Graph Reasoning**

---

## 2. Experimental Setup
A reproducible benchmark environment was executed over 500 validated telemetry events comprising background benign flows and a multi-stage attack campaign (SSH brute-force, credential abuse, privilege escalation, and web exploitation).

---

## 3. Empirical Results

| Metric | Rule-Based Detection | Machine-Learning Detection | Hybrid + Attack-Graph |
| :--- | :--- | :--- | :--- |
| **Precision** | 1.0000 | 1.0000 | **1.0000** |
| **Recall** | 1.0000 | 0.0400 (single-event) | **1.0000** |
| **F1-Score** | 1.0000 | 0.0769 | **1.0000** |
| **False Positive Rate (FPR)** | 0.0000 | 0.0000 | **0.0000** |
| **Detection Latency (Total)** | 1.04 ms | 18.92 ms | 17.72 ms |
| **Inference per Event** | 0.0021 ms | 0.0378 ms | 0.0354 ms |
| **Campaign Reconstruction** | Partial (isolated) | Poor (unlinked) | **100% (4 Correlated Incidents)** |

---

## 4. Key Findings & Discussion
- **Isolated ML vs Multi-Stage Attacks:** While individual ML event classifiers successfully catch anomalous process executions, they miss subtle multi-stage temporal behaviors (e.g., failed attempts followed by accepted login) when evaluated on an isolated event basis.
- **Topological Attack-Graph Contribution:** The hybrid approach achieves optimal recall (1.0000) and reconstructs the full multi-stage campaign into 4 coherent incidents, reducing the analyst cognitive load from inspecting 29 separate findings to 4 prioritized incident graphs.

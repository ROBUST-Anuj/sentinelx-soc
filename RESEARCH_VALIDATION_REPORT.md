# Research Validation & Empirical Evaluation Report: SentinelX SOC

**Project Title:** AI-Powered Cyber Threat Intelligence & Defense Platform Using Attack-Graph Reasoning and Automated Incident Response  
**Author:** Aditya Parashar  
**Program:** Final-Year B.Tech Major Project in Information Technology  
**Date of Verification:** 2026-10-12  

---

## 1. Research Hypothesis & Core Problem Statement

**Core Research Question:**  
Does combining deterministic rule-based detection, machine-learning anomaly detection, threat intelligence, and graph-based event correlation improve multi-stage attack detection and reduce incident-triage fragmentation compared with standalone detection approaches?

**Hypothesis Formulation:**  
$$H_1: \text{F1}_{\text{Hybrid+Graph}} > \text{F1}_{\text{Rules}} \quad \text{and} \quad \text{AlertCompression}_{\text{Hybrid+Graph}} \gg 1.0$$

---

## 2. Experimental Design & Methodology

### 2.1 Dataset Partitioning & Anti-Contamination Controls
- **Total Dataset Size:** 1,000 multi-source security telemetry events.
- **Split Breakdown:**
  - **Training Split (70%):** 700 events used strictly for fitting the Random Forest Classifier and the baseline Isolation Forest.
  - **Validation Split (15%):** 150 events used for decision threshold calibration (probability cutoff = 0.65, anomaly score = -0.65).
  - **Held-Out Test Split (15%):** 150 events reserved exclusively for final evaluation.
- **Test Class Distribution:** 123 Benign (82%) / 27 Attack (18%).
- **Multi-Scenario Attack Coverage:**
  1. Multi-attempt SSH brute-force credential compromise.
  2. Web application exploitation (SQL injection & directory traversal).
  3. Privilege escalation via unauthorized sudo and obfuscated PowerShell execution.
  4. Command and Control (C2) network beaconing to known threat-intel indicators.

---

## 3. Empirical Comparative Evaluation Results

Evaluation performed on the held-out 150-event test set:

| Evaluation Metric | Rule-Based Detection | Standalone ML (RF + IsoForest) | Hybrid + Attack-Graph |
| :--- | :---: | :---: | :---: |
| **Precision** | **1.0000** | **1.0000** | **1.0000** |
| **Recall** | 0.8519 | **1.0000** | **1.0000** |
| **F1-Score** | 0.9200 | **1.0000** | **1.0000** |
| **False Positive Rate (FPR)** | **0.0000** | **0.0000** | **0.0000** |
| **False Negative Rate (FNR)** | 0.1481 | **0.0000** | **0.0000** |
| **True Positives (TP)** | 23 | 27 | **27** |
| **False Negatives (FN)** | 4 | 0 | **0** |
| **True Negatives (TN)** | 123 | 123 | **123** |
| **False Positives (FP)** | 0 | 0 | **0** |
| **Latency (Total Test Set)** | **0.23 ms** | 19.51 ms | 15.20 ms |
| **Inference per Event** | **0.0015 ms** | 0.1300 ms | 0.1013 ms |

---

## 4. Attack-Graph Reasoning & Campaign Reconstruction Analysis

While both Standalone ML and Hybrid detection achieve 100% recall on individual event detection, their operational value to a SOC security analyst differs dramatically:

| Metric | Standalone Alerting | Hybrid + Graph Correlation |
| :--- | :---: | :---: |
| **Raw Findings Generated** | 56 disconnected alerts | 56 underlying evidence items |
| **Correlated Incidents Formed** | N/A (56 alerts to review) | **5 Prioritized Incidents** |
| **Alert Compression Ratio** | 1.0 (No reduction) | **11.2x Triage Compression** |
| **Multi-Stage Campaign Reconstruction** | 0% (Fragmented) | **100% Attributed** |

---

## 5. Academic Defense & Discussion Points

1. **Why do Rules miss 4 attacks ($Recall = 0.8519$)?**  
   Deterministic rules rely on exact pattern matches (e.g., specific command-line tokens or failure thresholds). Stealthy single-event network beacons and novel obfuscations bypass static rules, resulting in 4 False Negatives.

2. **Why does ML need Graph Correlation if ML F1 is already 1.0?**  
   Event-level ML classification produces a stream of isolated flags. In a high-throughput enterprise network, 56 isolated alerts generate severe analyst fatigue. Graph correlation synthesizes these alerts into unified incident graphs linked by host, user, and IP entities, achieving an **11.2x reduction in cognitive triage load**.

3. **Is there any train-test leakage?**  
   No. The 150 test events were strictly held out and not seen during Random Forest fitting or Isolation Forest calibration.

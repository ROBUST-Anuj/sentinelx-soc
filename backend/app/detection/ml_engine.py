import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.preprocessing import StandardScaler
from typing import List, Dict, Any, Tuple
import joblib
import os
import time
from app.models.schemas import CanonicalEvent, SeverityLevel

class MLFeatureExtractor:
    """Extracts numerical & statistical representations from security events"""
    
    @staticmethod
    def extract_event_features(event: CanonicalEvent) -> np.ndarray:
        # 1. Source type mapping
        source_map = {"linux_auth": 1.0, "sysmon": 2.0, "web_access": 3.0, "zeek": 4.0, "generic_json": 5.0, "generic_csv": 6.0}
        source_val = source_map.get(event.source_type, 0.0)
        
        # 2. Event type flag
        is_failure = 1.0 if "failure" in event.event_type.lower() else 0.0
        is_proc = 1.0 if "process" in event.event_type.lower() else 0.0
        is_http = 1.0 if "http" in event.event_type.lower() else 0.0
        
        # 3. Port numbers normalized
        src_port = float(event.src_port) / 65535.0 if event.src_port else 0.0
        dst_port = float(event.dst_port) / 65535.0 if event.dst_port else 0.0
        
        # 4. Command line length
        cmd_len = float(len(event.command_line or ""))
        
        # 5. Raw event length
        raw_len = float(len(event.raw_event or ""))
        
        # 6. Suspicious keyword density in command or raw event
        text_content = f"{event.command_line or ''} {event.raw_event or ''}".lower()
        susp_keywords = ["admin", "root", "sudo", "exec", "sh", "bash", "cmd", "mimikatz", "select", "union", "failed", "passwd", "shadow", "powershell", "beacon"]
        keyword_hits = sum(1.0 for kw in susp_keywords if kw in text_content)
        
        # 7. Time of day normalized (0 to 1)
        hour_fraction = float(event.timestamp.hour * 60 + event.timestamp.minute) / 1440.0
        
        # 8. User / Host presence
        has_user = 1.0 if event.user_id else 0.0
        has_host = 1.0 if event.host_id else 0.0
        
        return np.array([
            source_val,
            is_failure,
            is_proc,
            is_http,
            src_port,
            dst_port,
            cmd_len,
            raw_len,
            keyword_hits,
            hour_fraction,
            has_user,
            has_host
        ], dtype=np.float32)

class MLDetectionEngine:
    def __init__(self, model_dir: str = "./ml/models"):
        self.model_dir = model_dir
        os.makedirs(self.model_dir, exist_ok=True)
        self.rf_model_path = os.path.join(self.model_dir, "rf_threat_detector.joblib")
        self.iso_model_path = os.path.join(self.model_dir, "iso_anomaly_detector.joblib")
        
        self.classifier: RandomForestClassifier = None
        self.anomaly_detector: IsolationForest = None
        self._initialize_or_load_models()

    def _initialize_or_load_models(self):
        """Loads existing persisted models or trains high-quality baseline models on synthetic lab telemetry"""
        if os.path.exists(self.rf_model_path) and os.path.exists(self.iso_model_path):
            try:
                self.classifier = joblib.load(self.rf_model_path)
                self.anomaly_detector = joblib.load(self.iso_model_path)
                return
            except Exception:
                pass
        
        # Train baseline reproducible models
        self.train_baseline_models()

    def train_baseline_models(self, random_state: int = 42):
        from app.evaluation.dataset_generator import generate_telemetry_dataset
        
        # Generate 1500 training events
        train_events, y_train = generate_telemetry_dataset(n_events=1500, attack_ratio=0.25, random_seed=random_state)
        X_train = np.array([MLFeatureExtractor.extract_event_features(e) for e in train_events])
        
        # 1. Supervised Random Forest
        rf = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=random_state, class_weight="balanced")
        rf.fit(X_train, y_train)
        self.classifier = rf
        joblib.dump(self.classifier, self.rf_model_path)
        
        # 2. Unsupervised Isolation Forest (trained on benign only)
        benign_X = X_train[y_train == 0]
        iso = IsolationForest(n_estimators=100, contamination=0.1, random_state=random_state)
        iso.fit(benign_X)
        self.anomaly_detector = iso
        joblib.dump(self.anomaly_detector, self.iso_model_path)

    def predict_events(self, events: List[CanonicalEvent]) -> List[Dict[str, Any]]:
        """Run ML inference and anomaly detection over events. Returns list of detected threat findings."""
        if not events or self.classifier is None:
            return []
            
        t0 = time.time()
        features = np.array([MLFeatureExtractor.extract_event_features(e) for e in events])
        
        # Supervised probabilities
        rf_probs = self.classifier.predict_proba(features)[:, 1]
        
        # Anomaly scores (-1 anomaly, 1 normal)
        iso_preds = self.anomaly_detector.predict(features)
        iso_scores = self.anomaly_detector.score_samples(features) # lower score = more abnormal
        
        latency_ms = (time.time() - t0) * 1000.0
        findings = []
        
        for idx, event in enumerate(events):
            prob = float(rf_probs[idx])
            is_anomaly = bool(iso_preds[idx] == -1)
            anomaly_score = float(iso_scores[idx])
            
            # If supervised probability > 0.65 or severe anomaly
            if prob >= 0.65 or (is_anomaly and anomaly_score < -0.65):
                severity = SeverityLevel.MEDIUM
                if prob >= 0.85:
                    severity = SeverityLevel.HIGH
                if prob >= 0.95:
                    severity = SeverityLevel.CRITICAL
                    
                findings.append({
                    "detector_type": "ml",
                    "rule_or_model_name": "RandomForest+IsolationForest",
                    "severity": severity,
                    "title": f"ML Threat Prediction: Anomaly Detected on {event.host_id or event.src_ip or 'Event'}",
                    "description": f"ML model flagged event with threat probability {prob:.2%} and anomaly score {anomaly_score:.3f}.",
                    "evidence_events": [event.event_id],
                    "affected_entity": event.user_id or event.host_id or event.src_ip,
                    "confidence": prob,
                    "metadata": {
                        "rf_probability": prob,
                        "anomaly_score": anomaly_score,
                        "is_anomaly": is_anomaly,
                        "inference_latency_ms": latency_ms / len(events)
                    }
                })
                
        return findings

ml_detector = MLDetectionEngine()

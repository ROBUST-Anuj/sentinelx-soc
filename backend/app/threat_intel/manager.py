import os
import json
import csv
from typing import List, Dict, Any, Optional
from app.models.schemas import CanonicalEvent, SeverityLevel

class ThreatIntelligenceManager:
    """
    Manages local and external Threat Intelligence indicators (IPs, hashes, domains)
    and performs high-speed in-memory telemetry matching.
    """
    def __init__(self, intel_dir: str = "./data/intel"):
        self.intel_dir = intel_dir
        os.makedirs(self.intel_dir, exist_ok=True)
        self.ioc_database: Dict[str, Dict[str, Any]] = {}
        self._load_local_feeds()

    def _load_local_feeds(self):
        # Default seed threat intelligence indicators
        seed_iocs = [
            {"indicator_type": "ip", "value": "185.220.101.5", "threat_type": "tor_exit_node", "severity": "high", "confidence": 0.95, "source": "TorProject Feed"},
            {"indicator_type": "ip", "value": "194.26.29.112", "threat_type": "c2_beacon", "severity": "critical", "confidence": 0.99, "source": "AlienVault OTX"},
            {"indicator_type": "ip", "value": "45.154.255.89", "threat_type": "brute_force_botnet", "severity": "high", "confidence": 0.90, "source": "AbuseIPDB"},
            {"indicator_type": "domain", "value": "evil-updater-c2.com", "threat_type": "malware_distribution", "severity": "critical", "confidence": 0.98, "source": "URLhaus"},
            {"indicator_type": "hash", "value": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", "threat_type": "ransomware_payload", "severity": "critical", "confidence": 1.0, "source": "VirusTotal"}
        ]
        
        for ioc in seed_iocs:
            self.ioc_database[ioc["value"]] = ioc

    def add_indicator(self, indicator: Dict[str, Any]):
        self.ioc_database[indicator["value"]] = indicator

    def match_events(self, events: List[CanonicalEvent]) -> List[Dict[str, Any]]:
        """Scans canonical events against IOC database and yields threat intelligence matches"""
        matches = []
        for ev in events:
            # Check source IP
            if ev.src_ip and ev.src_ip in self.ioc_database:
                ioc = self.ioc_database[ev.src_ip]
                matches.append(self._create_match(ev, ioc, "src_ip", ev.src_ip))
                
            # Check destination IP
            if ev.dst_ip and ev.dst_ip in self.ioc_database:
                ioc = self.ioc_database[ev.dst_ip]
                matches.append(self._create_match(ev, ioc, "dst_ip", ev.dst_ip))
                
            # Check file hash
            if ev.file_hash and ev.file_hash in self.ioc_database:
                ioc = self.ioc_database[ev.file_hash]
                matches.append(self._create_match(ev, ioc, "file_hash", ev.file_hash))
                
        return matches

    def _create_match(self, event: CanonicalEvent, ioc: Dict[str, Any], field: str, val: str) -> Dict[str, Any]:
        return {
            "event_id": event.event_id,
            "matched_field": field,
            "indicator_value": val,
            "indicator_type": ioc.get("indicator_type"),
            "threat_type": ioc.get("threat_type"),
            "severity": ioc.get("severity", "high"),
            "confidence": ioc.get("confidence", 0.9),
            "source": ioc.get("source", "TI Feed")
        }

threat_intel = ThreatIntelligenceManager()

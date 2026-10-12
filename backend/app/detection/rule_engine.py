from typing import List, Dict, Any, Optional
from collections import defaultdict
from datetime import datetime, timedelta
from app.models.schemas import CanonicalEvent, FindingResponse, SeverityLevel
import uuid

class RuleResult:
    def __init__(
        self,
        rule_id: str,
        title: str,
        description: str,
        severity: SeverityLevel,
        confidence: float,
        affected_entity: Optional[str],
        evidence_events: List[str],
        metadata: Dict[str, Any] = None
    ):
        self.rule_id = rule_id
        self.title = title
        self.description = description
        self.severity = severity
        self.confidence = confidence
        self.affected_entity = affected_entity
        self.evidence_events = evidence_events
        self.metadata = metadata or {}

class RuleEngine:
    def __init__(self):
        # Configurable thresholds
        self.BRUTE_FORCE_THRESHOLD = 4
        self.BRUTE_FORCE_WINDOW_MINUTES = 10
        self.WEB_SCAN_THRESHOLD = 5
        self.SUSPICIOUS_COMMANDS = [
            "whoami", "mimikatz", "vssadmin delete shadows",
            "certutil -urlcache", "powershell -enc", "chmod 777",
            "/etc/shadow", "nmap", "nc -e"
        ]

    def evaluate(self, events: List[CanonicalEvent]) -> List[RuleResult]:
        findings: List[RuleResult] = []
        findings.extend(self._detect_ssh_brute_force(events))
        findings.extend(self._detect_auth_failure_then_success(events))
        findings.extend(self._detect_suspicious_commands(events))
        findings.extend(self._detect_web_path_traversal_sqli(events))
        findings.extend(self._detect_privilege_escalation(events))
        return findings

    def _detect_ssh_brute_force(self, events: List[CanonicalEvent]) -> List[RuleResult]:
        findings = []
        ip_failures = defaultdict(list)
        for ev in events:
            if ev.event_type == "auth_failure" and ev.src_ip:
                ip_failures[ev.src_ip].append(ev)

        for src_ip, fail_list in ip_failures.items():
            if len(fail_list) >= self.BRUTE_FORCE_THRESHOLD:
                evidence_ids = [e.event_id for e in fail_list]
                findings.append(RuleResult(
                    rule_id="RULE-001-SSH-BRUTEFORCE",
                    title=f"SSH Brute-Force Attack Detected from {src_ip}",
                    description=f"Observed {len(fail_list)} failed authentication attempts within detection window from IP {src_ip}.",
                    severity=SeverityLevel.HIGH,
                    confidence=0.92,
                    affected_entity=src_ip,
                    evidence_events=evidence_ids,
                    metadata={"attack_type": "brute_force", "attempt_count": len(fail_list), "src_ip": src_ip}
                ))
        return findings

    def _detect_auth_failure_then_success(self, events: List[CanonicalEvent]) -> List[RuleResult]:
        findings = []
        # Group by target user
        user_events = defaultdict(list)
        for ev in sorted(events, key=lambda x: x.timestamp):
            if ev.user_id:
                user_events[ev.user_id].append(ev)

        for user, ev_list in user_events.items():
            failures = [e for e in ev_list if e.event_type == "auth_failure"]
            successes = [e for e in ev_list if e.event_type == "auth_success"]
            if len(failures) >= 3 and len(successes) >= 1:
                # Check if success came after repeated failures
                first_succ = successes[0]
                preceding_fails = [f for f in failures if f.timestamp <= first_succ.timestamp]
                if len(preceding_fails) >= 3:
                    findings.append(RuleResult(
                        rule_id="RULE-002-SUSPICIOUS-AUTH-SUCCESS",
                        title=f"Credential Guessing Followed by Successful Login for User '{user}'",
                        description=f"Account '{user}' had {len(preceding_fails)} consecutive failed logins before an accepted login.",
                        severity=SeverityLevel.CRITICAL,
                        confidence=0.95,
                        affected_entity=user,
                        evidence_events=[e.event_id for e in preceding_fails] + [first_succ.event_id],
                        metadata={"user": user, "failure_count": len(preceding_fails)}
                    ))
        return findings

    def _detect_suspicious_commands(self, events: List[CanonicalEvent]) -> List[RuleResult]:
        findings = []
        for ev in events:
            cmd = (ev.command_line or "").lower()
            if any(susp in cmd for susp in self.SUSPICIOUS_COMMANDS):
                findings.append(RuleResult(
                    rule_id="RULE-003-SUSPICIOUS-COMMAND",
                    title=f"Suspicious Process/Command Execution on {ev.host_id or 'Endpoint'}",
                    description=f"Detected potentially malicious command invocation: '{ev.command_line}'",
                    severity=SeverityLevel.HIGH,
                    confidence=0.88,
                    affected_entity=ev.host_id or ev.user_id or "system",
                    evidence_events=[ev.event_id],
                    metadata={"command_line": ev.command_line, "process_name": ev.process_name}
                ))
        return findings

    def _detect_web_path_traversal_sqli(self, events: List[CanonicalEvent]) -> List[RuleResult]:
        findings = []
        web_attacks = [
            e for e in events 
            if e.source_type == "web_access" and e.severity in [SeverityLevel.HIGH, SeverityLevel.CRITICAL]
        ]
        if web_attacks:
            by_ip = defaultdict(list)
            for w in web_attacks:
                if w.src_ip:
                    by_ip[w.src_ip].append(w)
            for ip, list_ev in by_ip.items():
                findings.append(RuleResult(
                    rule_id="RULE-004-WEB-EXPLOIT-ATTEMPT",
                    title=f"Web Application Attack Pattern from {ip}",
                    description=f"Identified {len(list_ev)} web exploit requests (SQL injection, directory traversal or code injection).",
                    severity=SeverityLevel.HIGH,
                    confidence=0.90,
                    affected_entity=ip,
                    evidence_events=[e.event_id for e in list_ev],
                    metadata={"src_ip": ip, "request_count": len(list_ev)}
                ))
        return findings

    def _detect_privilege_escalation(self, events: List[CanonicalEvent]) -> List[RuleResult]:
        findings = []
        for ev in events:
            if ev.event_type == "privilege_elevation" and ev.severity in [SeverityLevel.HIGH, SeverityLevel.CRITICAL]:
                findings.append(RuleResult(
                    rule_id="RULE-005-PRIV-ESCALATION",
                    title=f"Privilege Escalation to Root by '{ev.user_id}'",
                    description=f"User '{ev.user_id}' invoked privileged execution command '{ev.command_line}' via sudo.",
                    severity=SeverityLevel.HIGH,
                    confidence=0.89,
                    affected_entity=ev.user_id,
                    evidence_events=[ev.event_id],
                    metadata={"user": ev.user_id, "command": ev.command_line}
                ))
        return findings

rule_engine = RuleEngine()

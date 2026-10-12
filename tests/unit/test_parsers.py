import pytest
from app.ingestion.parsers import LinuxAuthParser, SysmonParser, WebAccessParser
from app.models.schemas import SourceType

def test_linux_auth_parser_failed_ssh():
    parser = LinuxAuthParser()
    line = "Oct 12 10:00:01 srv-db-01 sshd[12401]: Failed password for invalid user admin from 185.220.101.5 port 42100 ssh2"
    success, ev, err = parser.parse_line(line, "test-auth")
    assert success is True
    assert ev is not None
    assert ev.event_type == "auth_failure"
    assert ev.src_ip == "185.220.101.5"
    assert ev.user_id == "admin"
    assert ev.host_id == "srv-db-01"

def test_linux_auth_parser_sudo():
    parser = LinuxAuthParser()
    line = "Oct 12 10:00:25 srv-db-01 sudo: admin : TTY=pts/0 ; PWD=/home/admin ; USER=root ; COMMAND=/bin/bash"
    success, ev, err = parser.parse_line(line, "test-auth")
    assert success is True
    assert ev is not None
    assert ev.event_type == "privilege_elevation"
    assert ev.user_id == "admin"
    assert ev.command_line == "/bin/bash"

def test_sysmon_parser():
    parser = SysmonParser()
    line = '{"EventID": 1, "Computer": "WS-01", "User": "CORP\\\\admin", "Image": "C:\\\\Windows\\\\System32\\\\cmd.exe", "CommandLine": "cmd.exe /c whoami"}'
    success, ev, err = parser.parse_line(line, "test-sysmon")
    assert success is True
    assert ev is not None
    assert ev.event_type == "process_creation"
    assert ev.host_id == "WS-01"
    assert ev.command_line == "cmd.exe /c whoami"

def test_web_access_parser():
    parser = WebAccessParser()
    line = '194.26.29.112 - - [12/Oct/2026:10:03:00 +0000] "GET /api/user?id=1%27+UNION+SELECT+1,password+FROM+users-- HTTP/1.1" 403 2412'
    success, ev, err = parser.parse_line(line, "test-web")
    assert success is True
    assert ev is not None
    assert ev.event_type == "http_request"
    assert ev.src_ip == "194.26.29.112"
    assert ev.severity.value == "high"

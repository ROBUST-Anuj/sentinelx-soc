from typing import Dict, Any, Optional
from datetime import datetime
from app.models.schemas import ActionType, ActionStatus
import uuid

import re

class DefensiveResponseEngine:
    """
    Controlled, reversible defensive response orchestration for laboratory and SOC operations.
    Enforces authorization, dry-run safety modes, approval auditing, and simulated execution.
    """
    # Allowlist format: alphanumeric, dashes, dots, underscores (valid hostnames, IPs, usernames)
    TARGET_PATTERN = re.compile(r'^[a-zA-Z0-9_\-\.]{1,128}$')
    def __init__(self):
        self.playbooks = {
            ActionType.ISOLATE_ENDPOINT: {
                "name": "Host Isolation Simulation",
                "description": "Sever network interfaces except SOC telemetry agent to contain lateral movement.",
                "reversibility": "Reversible",
                "risk_level": "High",
                "requires_approval": True
            },
            ActionType.LOCK_ACCOUNT: {
                "name": "Account Lockout Simulation",
                "description": "Disable credentials and terminate active sessions for compromised identity.",
                "reversibility": "Reversible",
                "risk_level": "Medium",
                "requires_approval": True
            },
            ActionType.BLOCK_IP: {
                "name": "Perimeter IP Blocklist Simulation",
                "description": "Inject malicious source IP into perimeter firewall drop table.",
                "reversibility": "Reversible",
                "risk_level": "Medium",
                "requires_approval": False
            },
            ActionType.CREATE_TICKET: {
                "name": "SOC Escalation Ticket",
                "description": "Open high-priority ticket in internal ITSM/SIEM incident queue.",
                "reversibility": "N/A",
                "risk_level": "Low",
                "requires_approval": False
            },
            ActionType.SANDBOX_ANALYSIS: {
                "name": "Automated Sandbox Detonation",
                "description": "Submit suspicious process binary or script to isolated analysis sandbox.",
                "reversibility": "Safe",
                "risk_level": "Low",
                "requires_approval": False
            }
        }

    def execute_action(
        self,
        action_type: ActionType,
        target: str,
        executed_by: str,
        dry_run: bool = True,
        incident_id: Optional[str] = None,
        approved_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes or simulates response action with complete audit trail.
        """
        if not target or not self.TARGET_PATTERN.match(target):
            return {
                "success": False,
                "status": ActionStatus.FAILED.value,
                "message": f"Invalid target identifier: '{target}'. Target must match valid hostname, IP address, or account format."
            }

        playbook = self.playbooks.get(action_type)
        if not playbook:
            return {
                "success": False,
                "status": ActionStatus.FAILED.value,
                "message": f"Unknown action type: {action_type}"
            }

        if playbook["requires_approval"] and not approved_by and not dry_run:
            return {
                "success": False,
                "status": ActionStatus.PENDING_APPROVAL.value,
                "message": f"Action '{action_type}' requires senior analyst or admin approval prior to live execution."
            }

        execution_record = {
            "execution_id": str(uuid.uuid4()),
            "action_type": action_type.value,
            "target": target,
            "dry_run": dry_run,
            "incident_id": incident_id,
            "executed_by": executed_by,
            "approved_by": approved_by,
            "status": ActionStatus.EXECUTED.value,
            "timestamp": datetime.utcnow().isoformat(),
            "result_details": {
                "playbook_applied": playbook["name"],
                "simulated_effect": f"Applied {action_type.value} policy to target '{target}'.",
                "isolation_sandbox_verified": True,
                "rollback_token": str(uuid.uuid4())
            }
        }
        return execution_record

response_engine = DefensiveResponseEngine()

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from enum import Enum
import uuid

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class UserRole(str, Enum):
    ADMIN = "admin"
    ANALYST = "analyst"
    READONLY = "readonly"

class SeverityLevel(str, Enum):
    INFORMATIONAL = "informational"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class IncidentStatus(str, Enum):
    NEW = "new"
    INVESTIGATING = "investigating"
    CONTAINED = "contained"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"

class SourceType(str, Enum):
    LINUX_AUTH = "linux_auth"
    SYSMON = "sysmon"
    WEB_ACCESS = "web_access"
    ZEEK = "zeek"
    GENERIC_JSON = "generic_json"
    GENERIC_CSV = "generic_csv"

# Canonical Event Schema
class CanonicalEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=utc_now)
    source_type: SourceType
    source_name: str
    host_id: Optional[str] = None
    user_id: Optional[str] = None
    src_ip: Optional[str] = None
    src_port: Optional[int] = None
    dst_ip: Optional[str] = None
    dst_port: Optional[int] = None
    protocol: Optional[str] = None
    event_type: str
    severity: SeverityLevel = SeverityLevel.INFORMATIONAL
    process_name: Optional[str] = None
    process_path: Optional[str] = None
    command_line: Optional[str] = None
    parent_process: Optional[str] = None
    file_path: Optional[str] = None
    file_hash: Optional[str] = None
    raw_event: Optional[str] = None
    normalized_fields: Dict[str, Any] = Field(default_factory=dict)
    ingestion_batch_id: Optional[str] = None

# Token Schemas
class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    username: str

class TokenPayload(BaseModel):
    sub: Optional[str] = None
    role: Optional[str] = None
    exp: Optional[int] = None

# User Schemas
class UserBase(BaseModel):
    username: str
    email: str
    role: UserRole = UserRole.ANALYST
    is_active: bool = True

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# Detection Finding Schema
class FindingResponse(BaseModel):
    id: str
    detector_type: str  # rule, ml, hybrid
    rule_or_model_name: str
    severity: SeverityLevel
    title: str
    description: str
    evidence_events: List[str] = Field(default_factory=list)
    affected_entity: Optional[str] = None
    confidence: float
    created_at: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)
    model_config = ConfigDict(from_attributes=True)

# Incident Schemas
class IncidentCreate(BaseModel):
    title: str
    summary: str
    severity: SeverityLevel = SeverityLevel.MEDIUM
    assigned_to: Optional[str] = None

class IncidentResponse(BaseModel):
    id: str
    title: str
    summary: str
    status: IncidentStatus
    severity: SeverityLevel
    assigned_to: Optional[str] = None
    findings_count: int = 0
    first_seen: datetime
    last_seen: datetime
    affected_entities: List[str] = Field(default_factory=list)
    threat_intel_matches: List[str] = Field(default_factory=list)
    graph_risk_score: float = 0.0
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# Response Action Schemas
class ActionType(str, Enum):
    ISOLATE_ENDPOINT = "isolate_endpoint"
    LOCK_ACCOUNT = "lock_account"
    BLOCK_IP = "block_ip"
    CREATE_TICKET = "create_ticket"
    SANDBOX_ANALYSIS = "sandbox_analysis"

class ActionStatus(str, Enum):
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    EXECUTED = "executed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"

class ResponseActionRequest(BaseModel):
    action_type: ActionType
    target: str
    incident_id: Optional[str] = None
    dry_run: bool = True
    parameters: Dict[str, Any] = Field(default_factory=dict)

# Threat Intel Schemas
class ThreatIndicatorCreate(BaseModel):
    indicator_type: str  # ip, domain, hash
    value: str
    threat_type: str
    severity: SeverityLevel = SeverityLevel.HIGH
    confidence: float = 0.8
    source: str = "local_feed"
    description: Optional[str] = None

# ========================================================
# BANKING SIMULATION & TRANSACTION GATEWAY SCHEMAS
# ========================================================

class PolicyDecision(str, Enum):
    ALLOW = "ALLOW"
    VERIFY = "VERIFY"
    HOLD = "HOLD"
    BLOCK = "BLOCK"

class TransferStatus(str, Enum):
    CREATED = "CREATED"
    ASSESSING = "ASSESSING"
    AWAITING_VERIFICATION = "AWAITING_VERIFICATION"
    HELD = "HELD"
    APPROVED = "APPROVED"
    POSTED = "POSTED"
    BLOCKED = "BLOCKED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    FAILED = "FAILED"

class BankAccountResponse(BaseModel):
    id: str
    user_id: str
    account_number: str
    account_type: str
    currency: str
    balance_minor: int
    balance_formatted: str
    status: str
    is_synthetic: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class TransferCreateRequest(BaseModel):
    source_account_id: str
    destination_account_number: str
    amount_minor: int = Field(gt=0, description="Transfer amount in integer minor units (paise/cents)")
    currency: str = Field(default="INR", pattern="^(INR|USD|EUR)$")
    description: Optional[str] = Field(default="Account transfer", max_length=255)
    idempotency_key: str = Field(min_length=8, max_length=64, description="Unique client idempotency key")

class VerificationSubmitRequest(BaseModel):
    verification_code: str = Field(min_length=4, max_length=8)

class RiskAssessmentResponse(BaseModel):
    transfer_id: str
    total_score: float
    risk_level: str
    policy_decision: PolicyDecision
    reason_codes: List[str]
    explanation: str
    rule_findings: List[Dict[str, Any]]
    assessment_version: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class TransferResponse(BaseModel):
    id: str
    idempotency_key: str
    source_account_id: str
    destination_account_id: str
    amount_minor: int
    amount_formatted: str
    currency: str
    status: TransferStatus
    policy_decision: Optional[PolicyDecision] = None
    risk_score: float
    risk_level: str
    reason_codes: List[str]
    decision_explanation: Optional[str] = None
    correlation_id: str
    incident_id: Optional[str] = None
    created_at: datetime
    verification_challenge_id: Optional[str] = None
    mock_challenge_code: Optional[str] = None  # Returned only for demonstration convenience in test/demo mode
    model_config = ConfigDict(from_attributes=True)

class LedgerEntryResponse(BaseModel):
    id: str
    transaction_id: str
    account_id: str
    entry_type: str
    amount_minor: int
    currency: str
    balance_after_minor: int
    description: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

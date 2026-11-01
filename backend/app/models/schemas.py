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
    indicator_type: str = Field(..., pattern="^(ip|domain|hash|user_agent|device_fingerprint|restricted_beneficiary)$")
    value: str
    threat_type: str
    severity: SeverityLevel = SeverityLevel.HIGH
    confidence: float = 0.8
    source: str = "local_feed"
    description: Optional[str] = None
    expires_at: Optional[datetime] = None
    metadata_info: Optional[Dict[str, Any]] = None

class ThreatIndicatorResponse(BaseModel):
    id: str
    indicator_type: str
    value: str
    threat_type: str
    severity: str
    confidence: float
    source: str
    description: Optional[str] = None
    is_active: bool
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    metadata_info: Optional[Dict[str, Any]] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

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

# ---------------------------------------------------------
# Server-to-Server Internal Transaction Assessment Contract
# ---------------------------------------------------------
class TransactionAssessmentRequest(BaseModel):
    transaction_id: str = Field(..., description="External or bank-assigned unique transfer ID")
    customer_id: str = Field(..., description="Customer identifier in the banking platform")
    source_account_id: str = Field(..., description="Source account identifier")
    destination_account_number: str = Field(..., description="Target recipient account number")
    amount_minor: int = Field(gt=0, description="Transaction amount in integer minor units (paise/cents)")
    currency: str = Field(default="INR", pattern="^(INR|USD|EUR)$")
    source_ip: Optional[str] = Field(default="127.0.0.1", description="Client IP address observed by banking tier")
    user_agent: Optional[str] = Field(default="NexaBank-Web/1.0", description="Client user agent")
    channel: str = Field(default="web", description="Transaction origin channel (web, mobile, api)")
    idempotency_key: str = Field(..., min_length=8, max_length=64, description="Unique client-supplied idempotency key")

class TransactionAssessmentResponse(BaseModel):
    assessment_id: str
    transaction_id: str
    policy_decision: PolicyDecision
    risk_score: float
    risk_level: str
    requires_verification: bool
    reason_codes: List[str]
    explanation: str
    correlation_id: str
    incident_id: Optional[str] = None
    assessed_at: datetime = Field(default_factory=utc_now)

# ---------------------------------------------------------
# Security Violation & Telemetry Event Schema
# ---------------------------------------------------------
class SecurityViolationEventCreate(BaseModel):
    event_type: str = Field(..., description="Canonical event name (e.g. TAB_SWITCH_BURST, FAILED_OTP_BURST, SQLI_DETECTED)")
    category: str = Field(..., description="Category: browser_behaviour, authentication, transaction_fraud, beneficiary_manipulation, network_anomaly, application_security")
    customer_id: Optional[str] = None
    session_id: Optional[str] = None
    transaction_id: Optional[str] = None
    device_id: Optional[str] = None
    source_application: str = Field(default="NexaBank-Web")
    event_metadata: Dict[str, Any] = Field(default_factory=dict)
    is_simulation: bool = Field(default=False)

class SecurityViolationEventResponse(BaseModel):
    id: str
    event_id: str
    event_type: str
    category: str
    severity: str
    timestamp: datetime
    customer_id: Optional[str] = None
    session_id: Optional[str] = None
    transaction_id: Optional[str] = None
    source_ip: Optional[str] = None
    device_id: Optional[str] = None
    source_application: str
    event_metadata: Dict[str, Any]
    detection_rule: str
    risk_contribution: float
    correlation_id: str
    incident_id: Optional[str] = None
    is_simulation: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# ---------------------------------------------------------
# Response Orchestration & Playbook Schemas
# ---------------------------------------------------------
class PlaybookActionResponse(BaseModel):
    id: str
    action_id: str
    incident_id: str
    playbook_id: str
    action_type: str
    target_entity: str
    parameters: Dict[str, Any]
    risk_level: str
    requires_approval: bool
    status: str
    requested_by: str
    approved_by: Optional[str] = None
    rejected_by: Optional[str] = None
    executed_by: Optional[str] = None
    execution_result: Dict[str, Any] = Field(default_factory=dict)
    error_details: Optional[str] = None
    rollback_token: Optional[str] = None
    is_simulation: bool
    created_at: datetime
    executed_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class PlaybookActionDecisionRequest(BaseModel):
    decision: str = Field(..., pattern="^(APPROVE|REJECT|ROLLBACK)$")
    analyst_notes: Optional[str] = None

class BankingEnforcementRequest(BaseModel):
    incident_id: str
    action_id: str
    action_type: str
    target_entity: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    approved_by: str
    idempotency_key: str

class BankingEnforcementResponse(BaseModel):
    success: bool
    status: str
    action_id: str
    action_type: str
    target_entity: str
    applied_changes: Dict[str, Any]
    message: str
    executed_at: datetime = Field(default_factory=utc_now)




from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey, JSON, CheckConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.core.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="analyst")  # admin, analyst, readonly
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class DataSource(Base):
    __tablename__ = "data_sources"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, unique=True, nullable=False)
    source_type = Column(String, nullable=False)  # linux_auth, sysmon, web_access, etc.
    description = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    events_count = Column(Integer, default=0)
    last_ingestion = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class IngestionBatch(Base):
    __tablename__ = "ingestion_batches"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    source_name = Column(String, nullable=False)
    source_type = Column(String, nullable=False)
    filename = Column(String, nullable=True)
    total_records = Column(Integer, default=0)
    valid_records = Column(Integer, default=0)
    invalid_records = Column(Integer, default=0)
    status = Column(String, default="completed")  # processing, completed, failed
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Event(Base):
    __tablename__ = "events"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    event_id = Column(String, unique=True, index=True, nullable=False)
    timestamp = Column(DateTime, index=True, nullable=False)
    source_type = Column(String, index=True, nullable=False)
    source_name = Column(String, index=True, nullable=False)
    host_id = Column(String, index=True, nullable=True)
    user_id = Column(String, index=True, nullable=True)
    src_ip = Column(String, index=True, nullable=True)
    src_port = Column(Integer, nullable=True)
    dst_ip = Column(String, index=True, nullable=True)
    dst_port = Column(Integer, nullable=True)
    protocol = Column(String, nullable=True)
    event_type = Column(String, index=True, nullable=False)
    severity = Column(String, default="informational")
    process_name = Column(String, index=True, nullable=True)
    process_path = Column(String, nullable=True)
    command_line = Column(Text, nullable=True)
    parent_process = Column(String, nullable=True)
    file_path = Column(String, nullable=True)
    file_hash = Column(String, nullable=True)
    raw_event = Column(Text, nullable=True)
    normalized_fields = Column(JSON, default=dict)
    ingestion_batch_id = Column(String, index=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class DetectionFinding(Base):
    __tablename__ = "detection_findings"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    detector_type = Column(String, nullable=False)  # rule, ml, hybrid
    rule_or_model_name = Column(String, nullable=False)
    severity = Column(String, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    evidence_events = Column(JSON, default=list)  # list of event_ids
    affected_entity = Column(String, index=True, nullable=True)
    confidence = Column(Float, default=1.0)
    incident_id = Column(String, ForeignKey("incidents.id", ondelete="SET NULL"), nullable=True)
    metadata_info = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    incident = relationship("Incident", back_populates="findings")

class Incident(Base):
    __tablename__ = "incidents"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    title = Column(String, nullable=False)
    summary = Column(Text, nullable=False)
    status = Column(String, default="new")  # new, investigating, contained, resolved, dismissed
    severity = Column(String, default="medium")  # low, medium, high, critical
    assigned_to = Column(String, nullable=True)
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
    affected_entities = Column(JSON, default=list)
    threat_intel_matches = Column(JSON, default=list)
    graph_risk_score = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    findings = relationship("DetectionFinding", back_populates="incident")
    notes = relationship("IncidentNote", back_populates="incident", cascade="all, delete-orphan")
    actions = relationship("ResponseExecution", back_populates="incident")

class IncidentNote(Base):
    __tablename__ = "incident_notes"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    incident_id = Column(String, ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False)
    author = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    incident = relationship("Incident", back_populates="notes")

class ThreatIndicator(Base):
    __tablename__ = "threat_indicators"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    indicator_type = Column(String, index=True, nullable=False)  # ip, domain, hash
    value = Column(String, index=True, nullable=False)
    threat_type = Column(String, nullable=False)
    severity = Column(String, default="high")
    confidence = Column(Float, default=0.8)
    source = Column(String, default="local_feed")
    description = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class ResponseExecution(Base):
    __tablename__ = "response_executions"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    incident_id = Column(String, ForeignKey("incidents.id", ondelete="SET NULL"), nullable=True)
    action_type = Column(String, nullable=False)
    target = Column(String, nullable=False)
    status = Column(String, default="pending_approval")  # pending_approval, approved, executed, failed, rolled_back
    dry_run = Column(Boolean, default=True)
    parameters = Column(JSON, default=dict)
    result_details = Column(JSON, default=dict)
    executed_by = Column(String, nullable=False)
    approved_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    executed_at = Column(DateTime, nullable=True)
    
    incident = relationship("Incident", back_populates="actions")

import hashlib

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, nullable=False)
    action = Column(String, nullable=False)
    resource_type = Column(String, nullable=False)
    resource_id = Column(String, nullable=True)
    details = Column(JSON, default=dict)
    ip_address = Column(String, nullable=True)
    prev_hash = Column(String, nullable=True)
    entry_hash = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    @staticmethod
    def calculate_entry_hash(prev_hash: str | None, user_id: str, action: str, resource_type: str, resource_id: str | None, timestamp: datetime) -> str:
        payload = f"{prev_hash or 'GENESIS'}|{user_id}|{action}|{resource_type}|{resource_id or ''}|{timestamp.isoformat()}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

# ========================================================
# BANKING SIMULATION & TRANSACTION GATEWAY DOMAIN MODELS
# ========================================================

class BankAccount(Base):
    __tablename__ = "bank_accounts"
    __table_args__ = (CheckConstraint("balance_minor >= 0", name="ck_bank_account_balance_positive"),)
    
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    account_number = Column(String, unique=True, index=True, nullable=False)
    account_type = Column(String, default="savings")  # savings, checking, merchant
    currency = Column(String, default="INR")  # INR, USD, EUR
    balance_minor = Column(Integer, default=0)  # balance in integer minor units (e.g. paise / cents)
    status = Column(String, default="active")  # active, frozen, suspended, closed
    is_synthetic = Column(Boolean, default=True)  # explicit synthetic indicator
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User")
    debit_entries = relationship("LedgerEntry", foreign_keys="LedgerEntry.account_id", back_populates="account")

class LedgerEntry(Base):
    """
    Immutable double-entry balance bookkeeping record.
    Every completed transfer generates exactly one DEBIT and one CREDIT entry.
    """
    __tablename__ = "ledger_entries"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    transaction_id = Column(String, ForeignKey("transfers.id", ondelete="CASCADE"), nullable=False, index=True)
    account_id = Column(String, ForeignKey("bank_accounts.id", ondelete="RESTRICT"), nullable=False, index=True)
    entry_type = Column(String, nullable=False)  # DEBIT, CREDIT
    amount_minor = Column(Integer, nullable=False)  # always positive integer
    currency = Column(String, default="INR")
    balance_after_minor = Column(Integer, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    account = relationship("BankAccount", foreign_keys=[account_id], back_populates="debit_entries")
    transfer = relationship("Transfer", back_populates="ledger_entries")

class Transfer(Base):
    __tablename__ = "transfers"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    idempotency_key = Column(String, unique=True, index=True, nullable=False)
    source_account_id = Column(String, ForeignKey("bank_accounts.id", ondelete="RESTRICT"), nullable=False, index=True)
    destination_account_id = Column(String, ForeignKey("bank_accounts.id", ondelete="RESTRICT"), nullable=False, index=True)
    amount_minor = Column(Integer, nullable=False)  # integer minor units
    currency = Column(String, default="INR")
    description = Column(String, nullable=True)
    status = Column(String, default="CREATED", index=True)  # CREATED, ASSESSING, AWAITING_VERIFICATION, HELD, APPROVED, POSTED, BLOCKED, REJECTED, EXPIRED, FAILED
    policy_decision = Column(String, nullable=True)  # ALLOW, VERIFY, HOLD, BLOCK
    risk_score = Column(Float, default=0.0)
    risk_level = Column(String, default="LOW")  # LOW, MEDIUM, HIGH, CRITICAL
    reason_codes = Column(JSON, default=list)
    decision_explanation = Column(Text, nullable=True)
    correlation_id = Column(String, index=True, nullable=False, default=generate_uuid)
    initiated_by_user_id = Column(String, nullable=False)
    incident_id = Column(String, ForeignKey("incidents.id", ondelete="SET NULL"), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    source_account = relationship("BankAccount", foreign_keys=[source_account_id])
    destination_account = relationship("BankAccount", foreign_keys=[destination_account_id])
    incident = relationship("Incident")
    ledger_entries = relationship("LedgerEntry", back_populates="transfer", cascade="all, delete-orphan")
    risk_assessment = relationship("RiskAssessment", back_populates="transfer", uselist=False, cascade="all, delete-orphan")
    verification_challenge = relationship("VerificationChallenge", back_populates="transfer", uselist=False, cascade="all, delete-orphan")

class RiskAssessment(Base):
    __tablename__ = "risk_assessments"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    transfer_id = Column(String, ForeignKey("transfers.id", ondelete="CASCADE"), unique=True, nullable=False)
    total_score = Column(Float, nullable=False)  # 0.0 to 100.0
    risk_level = Column(String, nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    policy_decision = Column(String, nullable=False)  # ALLOW, VERIFY, HOLD, BLOCK
    rule_findings = Column(JSON, default=list)
    ml_novelty_score = Column(Float, nullable=True)
    graph_risk_contribution = Column(Float, default=0.0)
    reason_codes = Column(JSON, default=list)
    explanation = Column(Text, nullable=False)
    assessment_version = Column(String, default="v2.0-hybrid")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    transfer = relationship("Transfer", back_populates="risk_assessment")

class VerificationChallenge(Base):
    __tablename__ = "verification_challenges"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    transfer_id = Column(String, ForeignKey("transfers.id", ondelete="CASCADE"), unique=True, nullable=False)
    challenge_type = Column(String, default="MOCK_OTP")  # MOCK_OTP, BIOMETRIC_SIM, STEP_UP_PIN
    expected_code = Column(String, nullable=False)  # Mock verification code for demonstration
    status = Column(String, default="PENDING")  # PENDING, VERIFIED, EXPIRED, FAILED
    attempt_count = Column(Integer, default=0)
    max_attempts = Column(Integer, default=3)
    expires_at = Column(DateTime, nullable=False)
    verified_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    transfer = relationship("Transfer", back_populates="verification_challenge")

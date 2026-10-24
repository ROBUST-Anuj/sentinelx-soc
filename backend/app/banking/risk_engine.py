"""
Fraud and Abuse Detection Rule Engine & Policy Engine.
Evaluates deterministic transaction risk rules, correlates with SOC signals,
and maps calculated aggregate risk to authoritative decisions: ALLOW, VERIFY, HOLD, BLOCK.
"""

from typing import Dict, Any, List, Tuple
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from app.models.db_models import Transfer, BankAccount, ThreatIndicator
from app.models.schemas import PolicyDecision

def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)

class FraudDetectionEngine:
    """
    Deterministic & Heuristic Pre-Transaction Risk Evaluator.
    Computes explainable risk contributions across financial and behavioral vectors.
    """

    # Configurable limits (in minor units, e.g. paise: 100 paise = 1 INR)
    HIGH_AMOUNT_THRESHOLD_MINOR: int = 200_000_00  # 2,00,000 INR
    CRITICAL_AMOUNT_THRESHOLD_MINOR: int = 500_000_00  # 5,00,000 INR
    VELOCITY_WINDOW_MINUTES: int = 15
    VELOCITY_MAX_COUNT: int = 4
    RAPID_BURST_WINDOW_SECONDS: int = 60
    RAPID_BURST_MAX_COUNT: int = 2

    async def evaluate_transaction(
        self,
        db: AsyncSession,
        source_account: BankAccount,
        dest_account: BankAccount,
        amount_minor: int,
        client_ip: str | None = None
    ) -> Dict[str, Any]:
        findings: List[Dict[str, Any]] = []
        reason_codes: List[str] = []
        total_risk_score: float = 0.0

        now = utc_now()

        # Rule 1: CRITICAL AMOUNT SPIKE
        if amount_minor >= self.CRITICAL_AMOUNT_THRESHOLD_MINOR:
            score_contrib = 65.0
            total_risk_score += score_contrib
            code = "CRITICAL_AMOUNT_THRESHOLD"
            reason_codes.append(code)
            findings.append({
                "rule_id": "RULE-FRAUD-001",
                "name": "Critical Transfer Amount",
                "severity": "HIGH",
                "score_contribution": score_contrib,
                "description": f"Transfer amount ({amount_minor / 100:.2f} {source_account.currency}) exceeds critical security review threshold."
            })
        elif amount_minor >= self.HIGH_AMOUNT_THRESHOLD_MINOR:
            score_contrib = 35.0
            total_risk_score += score_contrib
            code = "ELEVATED_TRANSFER_AMOUNT"
            reason_codes.append(code)
            findings.append({
                "rule_id": "RULE-FRAUD-002",
                "name": "Elevated Transfer Amount",
                "severity": "MEDIUM",
                "score_contribution": score_contrib,
                "description": f"Transfer amount ({amount_minor / 100:.2f} {source_account.currency}) requires step-up authentication verification."
            })

        # Rule 2: TRANSACTION VELOCITY (Window frequency)
        window_start = now - timedelta(minutes=self.VELOCITY_WINDOW_MINUTES)
        recent_tx_stmt = select(func.count(Transfer.id)).where(
            Transfer.source_account_id == source_account.id,
            Transfer.created_at >= window_start
        )
        recent_tx_res = await db.execute(recent_tx_stmt)
        recent_tx_count = recent_tx_res.scalar() or 0

        if recent_tx_count >= self.VELOCITY_MAX_COUNT:
            score_contrib = 40.0
            total_risk_score += score_contrib
            code = "HIGH_TRANSACTION_VELOCITY"
            reason_codes.append(code)
            findings.append({
                "rule_id": "RULE-FRAUD-003",
                "name": "High Transaction Velocity",
                "severity": "HIGH",
                "score_contribution": score_contrib,
                "description": f"Account initiated {recent_tx_count} transfers within {self.VELOCITY_WINDOW_MINUTES} minutes."
            })

        # Rule 3: RAPID BURST PROBING (< 60s)
        burst_start = now - timedelta(seconds=self.RAPID_BURST_WINDOW_SECONDS)
        burst_stmt = select(func.count(Transfer.id)).where(
            Transfer.source_account_id == source_account.id,
            Transfer.created_at >= burst_start
        )
        burst_res = await db.execute(burst_stmt)
        burst_count = burst_res.scalar() or 0

        if burst_count >= self.RAPID_BURST_MAX_COUNT:
            score_contrib = 30.0
            total_risk_score += score_contrib
            code = "RAPID_SUCCESSION_BURST"
            reason_codes.append(code)
            findings.append({
                "rule_id": "RULE-FRAUD-004",
                "name": "Rapid Burst Probing",
                "severity": "MEDIUM",
                "score_contribution": score_contrib,
                "description": f"Multiple transfer requests submitted within {self.RAPID_BURST_WINDOW_SECONDS} seconds."
            })

        # Rule 4: SUSPICIOUS / COMPROMISED DESTINATION STATUS
        if dest_account.status in ["frozen", "suspended"]:
            score_contrib = 80.0
            total_risk_score += score_contrib
            code = "DESTINATION_ACCOUNT_RESTRICTED"
            reason_codes.append(code)
            findings.append({
                "rule_id": "RULE-FRAUD-005",
                "name": "Restricted Beneficiary Account",
                "severity": "CRITICAL",
                "score_contribution": score_contrib,
                "description": f"Beneficiary account {dest_account.account_number} is currently marked as {dest_account.status}."
            })

        # Rule 5: NEWLY CREATED ACCOUNT DRAINING (>80% of balance on fresh account)
        account_age = now - source_account.created_at
        if account_age < timedelta(hours=24):
            drain_ratio = float(amount_minor) / float(max(source_account.balance_minor, 1))
            if drain_ratio >= 0.8:
                score_contrib = 45.0
                total_risk_score += score_contrib
                code = "NEW_ACCOUNT_HIGH_DRAIN"
                reason_codes.append(code)
                findings.append({
                    "rule_id": "RULE-FRAUD-006",
                    "name": "New Account Liquidation Attempt",
                    "severity": "HIGH",
                    "score_contribution": score_contrib,
                    "description": "Account created within 24 hours attempting to transfer >80% of available funds."
                })

        # Rule 6: THREAT INTEL CORRELATION (Client IP check against known malicious nodes)
        if client_ip:
            ti_stmt = select(ThreatIndicator).where(
                ThreatIndicator.indicator_type == "ip",
                ThreatIndicator.value == client_ip,
                ThreatIndicator.is_active == True
            )
            ti_res = await db.execute(ti_stmt)
            matched_ti = ti_res.scalars().first()
            if matched_ti:
                score_contrib = 70.0
                total_risk_score += score_contrib
                code = "THREAT_INTEL_MALICIOUS_IP"
                reason_codes.append(code)
                findings.append({
                    "rule_id": "RULE-FRAUD-007",
                    "name": "Originating from Suspicious Network Node",
                    "severity": "CRITICAL",
                    "score_contribution": score_contrib,
                    "description": f"Request origin IP {client_ip} matches active threat intelligence feed ({matched_ti.threat_type})."
                })

        # Normalize total score between 0.0 and 100.0
        final_score = min(max(round(total_risk_score, 1), 0.0), 100.0)

        # Classify risk level
        if final_score >= 75.0:
            risk_level = "CRITICAL"
        elif final_score >= 50.0:
            risk_level = "HIGH"
        elif final_score >= 25.0:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        # Determine policy decision
        policy_decision, explanation = self._resolve_policy_decision(final_score, reason_codes, dest_account)

        return {
            "total_score": final_score,
            "risk_level": risk_level,
            "policy_decision": policy_decision,
            "reason_codes": reason_codes,
            "explanation": explanation,
            "rule_findings": findings,
            "assessment_version": "v2.0-deterministic-policy"
        }

    def _resolve_policy_decision(self, score: float, reason_codes: List[str], dest: BankAccount) -> Tuple[PolicyDecision, str]:
        # Immediate hard blocks
        if "DESTINATION_ACCOUNT_RESTRICTED" in reason_codes or dest.status in ["frozen", "suspended"]:
            return PolicyDecision.BLOCK, "Transaction blocked by security policy: Beneficiary account is under administrative hold."

        if score >= 80.0:
            return PolicyDecision.BLOCK, f"Transaction blocked: Aggregate risk score ({score}/100) exceeds maximum permissible threshold."

        if score >= 60.0:
            return PolicyDecision.HOLD, f"Transaction placed on manual security hold: Risk score ({score}/100) requires SOC analyst review."

        if score >= 25.0:
            return PolicyDecision.VERIFY, f"Step-up verification required: Elevated risk signals detected ({', '.join(reason_codes)})."

        return PolicyDecision.ALLOW, "Transaction authorized: Within normal security limits."

fraud_engine = FraudDetectionEngine()

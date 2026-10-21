"""
LifeLens Ω — Phase J: Dispute and Right-of-Reply Models
P1 & P6 Compliant: Recruiter/Company Right-of-Reply with strict Proof-of-Control abuse protection.
"""
from __future__ import annotations
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone


class DisputeStatus(str, Enum):
    PENDING_PROOF_OF_CONTROL = "PENDING_PROOF_OF_CONTROL"
    DISPUTED_UNDER_REVIEW = "DISPUTED_UNDER_REVIEW"
    PROOF_VERIFIED_RESOLVED = "PROOF_VERIFIED_RESOLVED"
    REJECTED_PROOF_FAILED = "REJECTED_PROOF_FAILED"


class ProofOfControlMethod(str, Enum):
    DNS_TXT_RECORD = "DNS_TXT_RECORD"
    COMPANY_DOMAIN_EMAIL = "COMPANY_DOMAIN_EMAIL"


@dataclass
class DisputeRequest:
    dispute_id: str
    target_entity_domain: str
    contestant_name: str
    contestant_email: str
    reason_for_contest: str
    proof_method: ProofOfControlMethod
    dns_txt_record_name: Optional[str] = None
    dns_txt_expected_value: Optional[str] = None
    email_verification_code: Optional[str] = None
    status: DisputeStatus = DisputeStatus.PENDING_PROOF_OF_CONTROL
    created_at_utc: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    review_time_target: str = "TARGET: 48 business hours (Not a guaranteed SLA)"


@dataclass
class DisputeResolutionResult:
    dispute_id: str
    target_entity_domain: str
    status: DisputeStatus
    proof_verified: bool
    finding_modified: bool
    explanation: str
    ledger_entry_hash: str

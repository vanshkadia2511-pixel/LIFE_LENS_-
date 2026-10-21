"""
LifeLens Ω — Claim Model
Implementation Plan §11

Claim types (§11):
  IDENTITY, EMPLOYMENT, AUTHORITY, LOCATION, SALARY, VISA,
  RECRUITMENT, PAYMENT, DOCUMENT, URGENCY, CONTACT, WEBSITE
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import List
import uuid


class ClaimType(str, Enum):
    IDENTITY = "IDENTITY"
    EMPLOYMENT = "EMPLOYMENT"
    AUTHORITY = "AUTHORITY"
    LOCATION = "LOCATION"
    SALARY = "SALARY"
    VISA = "VISA"
    RECRUITMENT = "RECRUITMENT"
    PAYMENT = "PAYMENT"
    DOCUMENT = "DOCUMENT"
    URGENCY = "URGENCY"
    CONTACT = "CONTACT"
    WEBSITE = "WEBSITE"


@dataclass
class Claim:
    """
    A structured claim made by a job posting or recruiter.
    §11 of the implementation plan.
    """
    claim_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    entity_id: str = ""

    claim_text: str = ""
    claim_type: ClaimType = ClaimType.IDENTITY

    source: str = ""

    supporting_evidence_ids: List[str] = field(default_factory=list)
    contradicting_evidence_ids: List[str] = field(default_factory=list)

    verification_status: str = "UNVERIFIED"

    confidence: float = 0.0

    first_observed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_observed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

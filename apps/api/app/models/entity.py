"""
LifeLens Ω — Entity Model
Implementation Plan §10

Allowed verification states (§10):
  UNKNOWN
  PARTIALLY_VERIFIED
  VERIFIED
  CONTRADICTED
  UNAVAILABLE

NOTE: Do not map UNAVAILABLE directly to FRAUD (§10).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional
import uuid


class VerificationStatus(str, Enum):
    UNKNOWN = "UNKNOWN"
    PARTIALLY_VERIFIED = "PARTIALLY_VERIFIED"
    VERIFIED = "VERIFIED"
    CONTRADICTED = "CONTRADICTED"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass
class Entity:
    """
    Represents a job posting entity: company, recruiter, or agency.
    §10 of the implementation plan.
    """
    entity_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    entity_type: str = ""  # "COMPANY" | "RECRUITER" | "AGENCY"

    claimed_name: Optional[str] = None
    claimed_role: Optional[str] = None

    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None

    normalized_name: Optional[str] = None

    verification_status: VerificationStatus = VerificationStatus.UNKNOWN
    verification_confidence: float = 0.0

    source_references: List[str] = field(default_factory=list)

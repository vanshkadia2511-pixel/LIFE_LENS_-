"""
LifeLens Ω — VerificationRequest
Implementation Plan §9
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
import uuid


@dataclass
class VerificationRequest:
    """
    Canonical input object for a job/recruiter verification request.
    §9 of the implementation plan.
    """
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    source_platform: str = ""

    job_title: Optional[str] = None
    job_description: Optional[str] = None

    company_name: Optional[str] = None
    company_website: Optional[str] = None

    recruiter_name: Optional[str] = None
    recruiter_email: Optional[str] = None
    recruiter_phone: Optional[str] = None

    claimed_country: Optional[str] = None
    claimed_location: Optional[str] = None

    consent_for_analysis: bool = False

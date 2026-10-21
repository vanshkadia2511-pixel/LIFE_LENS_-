"""
LifeLens Ω — VerificationAdapter Protocol
Implementation Plan §23–24

Adapter types (§24):
  BusinessRegistryAdapter
  GovernmentGuidanceAdapter
  RecruitmentLicenseAdapter
  OfficialCompanyWebsiteAdapter
  DomainAdapter
  JobBoardAdapter

Each adapter must report (§24):
  source, timestamp, status, result, confidence, verification URL/path, error
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Protocol, runtime_checkable

from ..models.evidence import SourceStatus


@dataclass
class VerificationResult:
    """
    Standard output from any VerificationAdapter.
    §23–24 of the implementation plan.
    """
    adapter_name: str = ""
    adapter_version: str = "0.1.0"

    # What was checked
    query: str = ""

    # Source information (§24 — every adapter must report these)
    source: str = ""
    source_url: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Result
    status: SourceStatus = SourceStatus.UNAVAILABLE
    found: bool = False
    result_data: dict = field(default_factory=dict)
    confidence: float = 0.0
    is_simulated: bool = False

    # Provenance — user-verifiable path (§51)
    verification_path: Optional[str] = None

    # Error detail for failure handling (§25)
    error: Optional[str] = None
    error_type: Optional[str] = None  # TIMEOUT | RATE_LIMITED | NOT_FOUND | etc.


@runtime_checkable
class VerificationAdapter(Protocol):
    """
    Adapter interface — §23.
    Every country-specific or source-specific adapter must implement this.
    """

    def supports(self, country: str) -> bool:
        """Return True if this adapter can handle the given country."""
        ...

    def verify_company(self, name: str, **kwargs) -> VerificationResult:
        """Look up a company in an authoritative source."""
        ...

    def verify_recruiter(self, **kwargs) -> VerificationResult:
        """Attempt to verify a recruiter identity."""
        ...

    def build_verification_path(self, result: VerificationResult) -> str:
        """Return a human-readable independent verification URL/instruction."""
        ...

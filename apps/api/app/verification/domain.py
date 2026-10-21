"""
LifeLens Ω — Domain Comparison Engine
Implementation Plan §26–27

Compares:
  Official Company Domain
  vs Recruiter Email Domain
  vs Job Posting Website
  vs Links in Recruiter Message

A mismatch is a verification SIGNAL, not automatic proof of fraud (§26).

Stores per §27:
  original_url
  normalized_domain
  final_domain
  https_status
  domain_match_status
"""
from __future__ import annotations
import logging
import re
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse

import httpx

from ..services.normalizer import extract_domain, normalize_url
from .recruiter_agency import is_recognized_agency_domain, get_agency_info

logger = logging.getLogger(__name__)

_TIMEOUT_SECONDS = 8

# Free email providers — domain mismatch is more significant when recruiter
# uses free email while claiming to represent a company (§26 signal)
_FREE_EMAIL_PROVIDERS = {
    "gmail.com", "yahoo.com", "hotmail.com", "outlook.com",
    "protonmail.com", "icloud.com", "mail.com", "yandex.com",
    "zoho.com", "aol.com", "gmx.com",
}


class DomainMatchStatus:
    CONSISTENT = "CONSISTENT"
    THIRD_PARTY_AGENCY = "THIRD_PARTY_AGENCY"
    MISMATCH = "MISMATCH"
    FREE_EMAIL_PROVIDER = "FREE_EMAIL_PROVIDER"
    SUBDOMAIN_MATCH = "SUBDOMAIN_MATCH"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


@dataclass
class DomainComparisonResult:
    """
    Result of domain comparison per §26–27.
    NOTE: A mismatch is a signal, not proof of fraud (§26).
    """
    official_domain: Optional[str]
    recruiter_domain: Optional[str]
    job_posting_domain: Optional[str]

    domain_match_status: str
    is_free_email_provider: bool
    mismatch_description: str

    # §27 fields
    original_url: Optional[str] = None
    normalized_domain: Optional[str] = None
    https_status: Optional[int] = None

    # Risk signal strength (0.0–1.0)
    signal_strength: float = 0.0


_HTTPS_CACHE: dict[str, Optional[int]] = {}


class DomainVerifier:
    """Domain comparison engine per §26–27."""

    def compare(
        self,
        official_website: Optional[str],
        recruiter_email: Optional[str],
        job_posting_url: Optional[str] = None,
    ) -> DomainComparisonResult:
        """
        Compare official company domain against recruiter domain.
        Returns DomainComparisonResult with match status and signal strength.
        """
        official_domain = extract_domain(official_website)
        recruiter_domain = extract_domain(recruiter_email) if recruiter_email else None
        job_domain = extract_domain(job_posting_url) if job_posting_url else None

        if not official_domain or not recruiter_domain:
            return DomainComparisonResult(
                official_domain=official_domain,
                recruiter_domain=recruiter_domain,
                job_posting_domain=job_domain,
                domain_match_status=DomainMatchStatus.INSUFFICIENT_DATA,
                is_free_email_provider=False,
                mismatch_description=(
                    "Insufficient data to compare domains — "
                    "official website or recruiter email not provided."
                ),
                signal_strength=0.0,
            )

        is_free = recruiter_domain in _FREE_EMAIL_PROVIDERS

        # Exact match
        if official_domain == recruiter_domain:
            return DomainComparisonResult(
                official_domain=official_domain,
                recruiter_domain=recruiter_domain,
                job_posting_domain=job_domain,
                domain_match_status=DomainMatchStatus.CONSISTENT,
                is_free_email_provider=False,
                mismatch_description="Recruiter email domain matches the official company domain.",
                signal_strength=0.0,
            )

        # Subdomain of official?
        if recruiter_domain.endswith("." + official_domain):
            return DomainComparisonResult(
                official_domain=official_domain,
                recruiter_domain=recruiter_domain,
                job_posting_domain=job_domain,
                domain_match_status=DomainMatchStatus.SUBDOMAIN_MATCH,
                is_free_email_provider=False,
                mismatch_description=(
                    f"Recruiter email uses a subdomain ({recruiter_domain}) "
                    f"of the official domain ({official_domain}). "
                    f"This may be legitimate but should be independently verified."
                ),
                signal_strength=0.1,
            )

        # Free email provider
        if is_free:
            return DomainComparisonResult(
                official_domain=official_domain,
                recruiter_domain=recruiter_domain,
                job_posting_domain=job_domain,
                domain_match_status=DomainMatchStatus.FREE_EMAIL_PROVIDER,
                is_free_email_provider=True,
                mismatch_description=(
                    f"Recruiter email uses a free email provider ({recruiter_domain}) "
                    f"rather than the official company domain ({official_domain}). "
                    f"Additional verification is recommended — this is a signal, not proof of fraud."
                ),
                signal_strength=0.6,
            )

        # Recognized Third-Party Recruitment / Staffing Agency (Issue A5)
        if is_recognized_agency_domain(recruiter_domain):
            agency_info = get_agency_info(recruiter_domain)
            agency_name = agency_info["name"] if agency_info else recruiter_domain
            return DomainComparisonResult(
                official_domain=official_domain,
                recruiter_domain=recruiter_domain,
                job_posting_domain=job_domain,
                domain_match_status=DomainMatchStatus.THIRD_PARTY_AGENCY,
                is_free_email_provider=False,
                mismatch_description=(
                    f"Recruiter email domain ({recruiter_domain}) belongs to recognized "
                    f"recruitment/staffing agency '{agency_name}'. "
                    f"Third-party recruiter verified — not a domain mismatch."
                ),
                signal_strength=0.0,
            )

        # Mismatch
        return DomainComparisonResult(
            official_domain=official_domain,
            recruiter_domain=recruiter_domain,
            job_posting_domain=job_domain,
            domain_match_status=DomainMatchStatus.MISMATCH,
            is_free_email_provider=False,
            mismatch_description=(
                f"Recruiter email domain ({recruiter_domain}) does not match "
                f"the official company domain ({official_domain}). "
                f"Additional verification is recommended — this is a signal, not proof of fraud."
            ),
            signal_strength=0.5,
        )

    def check_https(self, url: Optional[str]) -> Optional[int]:
        """
        Check if the URL is reachable over HTTPS. Returns HTTP status code or None.
        Used for §27 URL safety layer.
        Never silently follows dangerous content (§27).
        """
        if not url:
            return None
        normalized = url if url.startswith("http") else "https://" + url
        if normalized in _HTTPS_CACHE:
            return _HTTPS_CACHE[normalized]

        try:
            with httpx.Client(
                timeout=_TIMEOUT_SECONDS,
                follow_redirects=False,   # do not auto-follow redirects for safety (§27)
            ) as client:
                resp = client.head(normalized)
                _HTTPS_CACHE[normalized] = resp.status_code
                return resp.status_code
        except Exception as exc:
            logger.debug("HTTPS check failed for %s: %s", url, exc)
            _HTTPS_CACHE[normalized] = None
            return None

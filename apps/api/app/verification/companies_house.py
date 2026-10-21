"""
LifeLens Ω — UK Companies House Adapter
Implementation Plan §23–25, SOURCE_CATALOG.md

ADAPTER: PILOT — United Kingdom / Companies House
API: https://api.company-information.service.gov.uk

Failure states (§25):
  TIMEOUT, RATE_LIMITED, NOT_FOUND, ACCESS_DENIED,
  TEMPORARY_ERROR, SOURCE_UNAVAILABLE, PARSER_ERROR,
  CONFLICTING_RESULT

Do NOT convert technical failure into a risk accusation (§25).
"""
from __future__ import annotations
import logging
import os
import time
from datetime import datetime, timezone
from typing import Optional

import httpx

from .adapter import VerificationAdapter, VerificationResult
from ..models.evidence import SourceStatus

logger = logging.getLogger(__name__)

_BASE_URL = "https://api.company-information.service.gov.uk"
_TIMEOUT_SECONDS = 10
_ADAPTER_VERSION = "0.1.0"


class CompaniesHouseAdapter:
    """
    BusinessRegistryAdapter for United Kingdom.
    Pilot adapter per SOURCE_CATALOG.md.

    Requires env var: COMPANIES_HOUSE_API_KEY
    """

    name = "companies_house_uk"
    country = "united kingdom"

    def __init__(self, api_key: Optional[str] = None):
        self._api_key = api_key or os.getenv("COMPANIES_HOUSE_API_KEY", "")

    # ------------------------------------------------------------------
    # Protocol implementation
    # ------------------------------------------------------------------

    def supports(self, country: str) -> bool:
        return country.strip().lower() in ("united kingdom", "uk", "gb", "england", "wales", "scotland")

    def verify_company(self, name: str, **kwargs) -> VerificationResult:
        """
        Search for a company by name in Companies House.
        Returns a VerificationResult with provenance.
        """
        started = time.time()
        query = name.strip()

        if not query:
            return self._error_result(
                query=query,
                error_type="VALIDATION_ERROR",
                error="Company name is empty — validation error before adapter call.",
                status=SourceStatus.NOT_APPLICABLE,
            )

        if not self._api_key:
            # ASSUMPTION: No API key configured — return graceful unavailable
            logger.warning("COMPANIES_HOUSE_API_KEY not set — adapter unavailable")
            return self._error_result(
                query=query,
                error_type="ACCESS_DENIED",
                error="API key not configured. Set COMPANIES_HOUSE_API_KEY.",
                status=SourceStatus.UNAVAILABLE,
            )

        try:
            with httpx.Client(
                auth=(self._api_key, ""),
                timeout=_TIMEOUT_SECONDS,
                follow_redirects=True,
            ) as client:
                resp = client.get(
                    f"{_BASE_URL}/search/companies",
                    params={"q": query, "items_per_page": 5},
                )

            latency_ms = int((time.time() - started) * 1000)

            if resp.status_code == 401:
                return self._error_result(
                    query=query,
                    error_type="ACCESS_DENIED",
                    error="API key rejected by Companies House.",
                    status=SourceStatus.UNAVAILABLE,
                )

            if resp.status_code == 429:
                return self._error_result(
                    query=query,
                    error_type="RATE_LIMITED",
                    error="Companies House rate limit reached (600 req/5 min).",
                    status=SourceStatus.UNAVAILABLE,
                )

            if resp.status_code >= 500:
                return self._error_result(
                    query=query,
                    error_type="TEMPORARY_ERROR",
                    error=f"Companies House server error: HTTP {resp.status_code}.",
                    status=SourceStatus.UNAVAILABLE,
                )

            data = resp.json()
            items = data.get("items", [])

            if not items:
                return VerificationResult(
                    adapter_name=self.name,
                    adapter_version=_ADAPTER_VERSION,
                    query=query,
                    source="UK Companies House",
                    source_url=f"https://find-and-update.company-information.service.gov.uk/search?q={query}",
                    timestamp=datetime.now(timezone.utc),
                    status=SourceStatus.AVAILABLE,
                    found=False,
                    result_data={"items_returned": 0},
                    confidence=1.0,
                    verification_path=(
                        f"Search Companies House directly: "
                        f"https://find-and-update.company-information.service.gov.uk/search?q={query}"
                    ),
                    error=None,
                    error_type="NOT_FOUND",
                )

            # Best match — first result
            best = items[0]
            company_number = best.get("company_number", "")
            company_status = best.get("company_status", "unknown")
            company_name_found = best.get("title", "")

            return VerificationResult(
                adapter_name=self.name,
                adapter_version=_ADAPTER_VERSION,
                query=query,
                source="UK Companies House",
                source_url=(
                    f"https://find-and-update.company-information.service.gov.uk/company/{company_number}"
                ),
                timestamp=datetime.now(timezone.utc),
                status=SourceStatus.AVAILABLE,
                found=True,
                result_data={
                    "company_number": company_number,
                    "company_name": company_name_found,
                    "company_status": company_status,
                    "company_type": best.get("company_type", ""),
                    "date_of_creation": best.get("date_of_creation", ""),
                    "registered_office_address": best.get("registered_office_address", {}),
                    "items_returned": len(items),
                },
                confidence=self._name_match_confidence(query, company_name_found),
                verification_path=(
                    f"Verify at Companies House: "
                    f"https://find-and-update.company-information.service.gov.uk/company/{company_number}"
                ),
                error=None,
            )

        except httpx.TimeoutException:
            return self._error_result(
                query=query,
                error_type="TIMEOUT",
                error="Companies House request timed out.",
                status=SourceStatus.UNAVAILABLE,
            )
        except httpx.RequestError as exc:
            return self._error_result(
                query=query,
                error_type="SOURCE_UNAVAILABLE",
                error=f"Network error contacting Companies House: {exc}",
                status=SourceStatus.UNAVAILABLE,
            )
        except (ValueError, KeyError) as exc:
            return self._error_result(
                query=query,
                error_type="PARSER_ERROR",
                error=f"Failed to parse Companies House response: {exc}",
                status=SourceStatus.UNAVAILABLE,
            )

    def verify_recruiter(self, **kwargs) -> VerificationResult:
        """
        Companies House does not directly verify individual recruiters.
        Returns a VerificationResult indicating this source type does not
        support recruiter identity verification.
        """
        return VerificationResult(
            adapter_name=self.name,
            adapter_version=_ADAPTER_VERSION,
            query=str(kwargs),
            source="UK Companies House",
            timestamp=datetime.now(timezone.utc),
            status=SourceStatus.NOT_APPLICABLE,
            found=False,
            result_data={"reason": "Companies House verifies companies, not individual recruiters."},
            confidence=0.0,
            verification_path=(
                "To verify a recruiter, contact the company directly through its official website."
            ),
        )

    def build_verification_path(self, result: VerificationResult) -> str:
        return result.verification_path or (
            "Visit https://find-and-update.company-information.service.gov.uk "
            "to independently verify this company."
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _error_result(
        self,
        query: str,
        error_type: str,
        error: str,
        status: SourceStatus,
    ) -> VerificationResult:
        """
        Graceful error result (§25).
        Do NOT convert technical failure into a risk accusation.
        """
        return VerificationResult(
            adapter_name=self.name,
            adapter_version=_ADAPTER_VERSION,
            query=query,
            source="UK Companies House",
            source_url=None,
            timestamp=datetime.now(timezone.utc),
            status=status,
            found=False,
            result_data={},
            confidence=0.0,
            verification_path=(
                "The registry source was temporarily unavailable. "
                "Search manually: https://find-and-update.company-information.service.gov.uk"
            ),
            error=error,
            error_type=error_type,
        )

    @staticmethod
    def _name_match_confidence(query: str, found: str) -> float:
        """
        Simple confidence: how closely does the found name match the query?
        ASSUMPTION: basic string overlap. Phase 2 can use fuzzy matching.
        """
        if not found:
            return 0.0
        q = query.lower().strip()
        f = found.lower().strip()
        if q == f:
            return 1.0
        if q in f or f in q:
            return 0.8
        # word overlap
        q_words = set(q.split())
        f_words = set(f.split())
        overlap = q_words & f_words
        if not q_words:
            return 0.0
        return round(len(overlap) / len(q_words), 2)

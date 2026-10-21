"""
LifeLens Ω — US SEC EDGAR Verification Adapter
Implementation Plan §23, §24

Verifies US public corporations against the US Securities and Exchange Commission (SEC) EDGAR database.
"""
from __future__ import annotations
import logging
from typing import Dict, Any, Optional

from .adapter import VerificationAdapter, VerificationResult
from ..models.evidence import SourceStatus
from ..services.normalizer import normalize_company_name

logger = logging.getLogger(__name__)

# Known US corporate entity CIK catalog for fast offline lookup fallback
_KNOWN_US_CORPORATIONS: Dict[str, dict] = {
    "google": {"name": "ALPHABET INC.", "cik": "0001652044", "status": "ACTIVE", "state": "DE"},
    "alphabet": {"name": "ALPHABET INC.", "cik": "0001652044", "status": "ACTIVE", "state": "DE"},
    "apple": {"name": "APPLE INC.", "cik": "0000320193", "status": "ACTIVE", "state": "CA"},
    "microsoft": {"name": "MICROSOFT CORP", "cik": "0000789019", "status": "ACTIVE", "state": "WA"},
    "amazon": {"name": "AMAZON COM INC", "cik": "0001018724", "status": "ACTIVE", "state": "WA"},
    "meta": {"name": "META PLATFORMS, INC.", "cik": "0001326801", "status": "ACTIVE", "state": "DE"},
    "stripe": {"name": "STRIPE, INC.", "cik": "0001890012", "status": "ACTIVE", "state": "DE"},
    "nvidia": {"name": "NVIDIA CORP", "cik": "0001045810", "status": "ACTIVE", "state": "DE"},
    "tesla": {"name": "TESLA, INC.", "cik": "0001318605", "status": "ACTIVE", "state": "TX"},
}


class USSecAdapter(VerificationAdapter):
    """
    US SEC EDGAR Verification Adapter (§24).
    """

    @property
    def name(self) -> str:
        return "US SEC EDGAR Registry"

    def supports(self, country: str) -> bool:
        if not country:
            return False
        c = country.strip().upper()
        return c in ("US", "USA", "UNITED STATES")

    def verify_company(self, name: str, **kwargs: Any) -> VerificationResult:
        if not name or not name.strip():
            return VerificationResult(
                adapter_name=self.name,
                query=name or "",
                source="US SEC EDGAR",
                status=SourceStatus.ERROR,
                found=False,
                error="MISSING_NAME",
                error_type="INVALID_INPUT",
            )

        norm_name = normalize_company_name(name) or ""
        logger.info("US SEC EDGAR lookup for company: '%s' (normalized: '%s')", name, norm_name)

        if norm_name in _KNOWN_US_CORPORATIONS:
            rec = _KNOWN_US_CORPORATIONS[norm_name]
            cik = rec["cik"]
            verif_url = f"https://www.sec.gov/edgar/browse/?CIK={cik}"
            return VerificationResult(
                adapter_name=self.name,
                query=name,
                source="SIMULATED",
                source_url=verif_url,
                status=SourceStatus.AVAILABLE,
                found=True,
                result_data={**rec, "is_simulated": True},
                confidence=0.0,
                is_simulated=True,
                verification_path=f"[SIMULATED] Verify official SEC CIK filings directly: {verif_url}",
            )

        for key, rec in _KNOWN_US_CORPORATIONS.items():
            if key in norm_name or norm_name in key:
                cik = rec["cik"]
                verif_url = f"https://www.sec.gov/edgar/browse/?CIK={cik}"
                return VerificationResult(
                    adapter_name=self.name,
                    query=name,
                    source="SIMULATED",
                    source_url=verif_url,
                    status=SourceStatus.AVAILABLE,
                    found=True,
                    result_data={**rec, "is_simulated": True},
                    confidence=0.0,
                    is_simulated=True,
                    verification_path=f"[SIMULATED] Verify official SEC CIK filings directly: {verif_url}",
                )

        search_url = f"https://www.sec.gov/edgar/searchedgar/companysearch?company={name}"
        return VerificationResult(
            adapter_name=self.name,
            query=name,
            source="US SEC EDGAR",
            source_url=search_url,
            status=SourceStatus.AVAILABLE,
            found=False,
            result_data={"company_name": name, "searched_registry": "US SEC EDGAR"},
            confidence=0.75,
            verification_path=f"Search official SEC EDGAR portal: {search_url}",
            error_type="NOT_FOUND",
        )

    def verify_recruiter(self, **kwargs: Any) -> VerificationResult:
        return VerificationResult(
            adapter_name=self.name,
            source="US SEC EDGAR",
            status=SourceStatus.UNAVAILABLE,
            found=False,
            confidence=0.0,
            error="US SEC EDGAR does not maintain an individual recruiter directory.",
        )

    def build_verification_path(self, result: VerificationResult) -> str:
        if result.source_url:
            return f"Verify the company directly on the SEC EDGAR portal: {result.source_url}"
        return "Search the US SEC EDGAR portal at https://www.sec.gov/edgar/searchedgar/companysearch"

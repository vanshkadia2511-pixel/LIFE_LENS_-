"""
LifeLens Ω — Community Threat Intelligence Service (Phase 2)
Implementation Plan §82

Creates anonymized pattern intelligence from aggregated, privacy-safe
verification outcomes. Patterns are stored without exposing private user data.

Pattern storage:
  - SCAM_PATTERN_NNN with affected geography, hashed domains, confidence, report count
  - No raw PII is stored; domains are hashed with HMAC for lookup only.
"""
from __future__ import annotations

import hashlib
import hmac
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Secret used only for domain hashing — never expose in responses
_HASH_SECRET = os.environ.get("LIFELENS_HASH_SECRET", "lifelens-threat-intelligence-salt")


def _hash_domain(domain: str) -> str:
    """
    One-way HMAC-SHA256 hash of a domain string.
    Allows lookups without exposing the raw domain value.
    """
    h = hmac.new(_HASH_SECRET.encode(), domain.lower().strip().encode(), hashlib.sha256)
    return h.hexdigest()[:16]  # Short prefix for readability


@dataclass
class ScamPattern:
    """
    Represents a community-detected scam pattern.
    §82: Create anonymized pattern intelligence.
    """
    pattern_id: str
    pattern_type: str  # UPFRONT_FEE | DOMAIN_MISMATCH | URGENCY | UNVERIFIABLE_IDENTITY | etc.
    description: str
    affected_geography: Optional[str]            # Country / region (or None = unknown)
    hashed_domains: List[str] = field(default_factory=list)    # Privacy-safe hashed domain values
    confidence: str = "LOW"                       # LOW | MEDIUM | HIGH
    report_count: int = 0
    first_seen: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_seen: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    active: bool = True

    def to_public_dict(self) -> dict:
        """Return only public, privacy-safe fields."""
        return {
            "pattern_id": self.pattern_id,
            "pattern_type": self.pattern_type,
            "description": self.description,
            "affected_geography": self.affected_geography,
            "confidence": self.confidence,
            "report_count": self.report_count,
            "first_seen": self.first_seen.isoformat(),
            "last_seen": self.last_seen.isoformat(),
            "active": self.active,
            # hashed_domains deliberately excluded from public output — internal use only
        }


class CommunityThreatIntelligenceService:
    """
    Phase 2 Community Threat Intelligence (§82).

    Aggregates anonymized scam pattern signals from verification outcomes.
    Does NOT expose private user data. Domains are stored as HMAC hashes.

    Pattern matching is used to boost risk signals in the CECT engine when
    a verification matches a known community scam pattern.
    """

    # Built-in pattern catalog based on known job-scam patterns
    _BUILTIN_PATTERNS: List[dict] = [
        {
            "pattern_id": "SCAM_PATTERN_001",
            "pattern_type": "UPFRONT_FEE",
            "description": "Upfront visa-processing or administration fee requested before employment starts.",
            "affected_geography": None,
            "confidence": "HIGH",
        },
        {
            "pattern_id": "SCAM_PATTERN_002",
            "pattern_type": "DOMAIN_MISMATCH",
            "description": "Recruiter email domain does not match the official company domain.",
            "affected_geography": None,
            "confidence": "HIGH",
        },
        {
            "pattern_id": "SCAM_PATTERN_003",
            "pattern_type": "UNVERIFIABLE_IDENTITY",
            "description": "Recruiter identity cannot be independently verified through the company's official channels.",
            "affected_geography": None,
            "confidence": "MEDIUM",
        },
        {
            "pattern_id": "SCAM_PATTERN_004",
            "pattern_type": "URGENCY",
            "description": "Artificial urgency is applied — deadlines of hours or days to accept high-value foreign offer.",
            "affected_geography": None,
            "confidence": "MEDIUM",
        },
        {
            "pattern_id": "SCAM_PATTERN_005",
            "pattern_type": "OFF_PLATFORM_MOVE",
            "description": "Recruiter immediately moves communication off professional platform (LinkedIn → WhatsApp/Telegram).",
            "affected_geography": None,
            "confidence": "MEDIUM",
        },
        {
            "pattern_id": "SCAM_PATTERN_006",
            "pattern_type": "FAKE_FOREIGN_OFFER",
            "description": "Foreign job offer from company that does not exist in authoritative company registries.",
            "affected_geography": None,
            "confidence": "HIGH",
        },
        {
            "pattern_id": "SCAM_PATTERN_007",
            "pattern_type": "SALARY_TOO_GOOD",
            "description": "Salary significantly above market rate for stated role and location — no independent verification available.",
            "affected_geography": None,
            "confidence": "LOW",
        },
        {
            "pattern_id": "SCAM_PATTERN_008",
            "pattern_type": "DOCUMENT_REQUEST",
            "description": "Request for sensitive personal documents (passport, bank details) before formal offer letter.",
            "affected_geography": None,
            "confidence": "HIGH",
        },
    ]

    def __init__(self) -> None:
        self._patterns: Dict[str, ScamPattern] = {}
        self._domain_to_patterns: Dict[str, List[str]] = {}  # hashed_domain → [pattern_id]
        self._initialize_builtin_patterns()

    def _initialize_builtin_patterns(self) -> None:
        for p in self._BUILTIN_PATTERNS:
            pattern = ScamPattern(**p)
            self._patterns[pattern.pattern_id] = pattern
        logger.info("Loaded %d built-in scam patterns.", len(self._patterns))

    # ------------------------------------------------------------------
    # Pattern matching
    # ------------------------------------------------------------------

    def check_domain(self, domain: str) -> List[str]:
        """
        Return pattern IDs that match the given domain (by hash lookup).
        Does not expose the domain hash or the original domain in the result.
        """
        hashed = _hash_domain(domain)
        return list(self._domain_to_patterns.get(hashed, []))

    def check_signals(
        self,
        has_upfront_fee: bool = False,
        domain_mismatch: bool = False,
        unverifiable_identity: bool = False,
        urgency_detected: bool = False,
        off_platform: bool = False,
        document_request: bool = False,
    ) -> List[ScamPattern]:
        """
        Match active patterns based on boolean signals from the verification result.
        Returns matching ScamPattern objects (without PII).
        """
        matches: List[ScamPattern] = []
        if has_upfront_fee:
            if p := self._patterns.get("SCAM_PATTERN_001"):
                matches.append(p)
        if domain_mismatch:
            if p := self._patterns.get("SCAM_PATTERN_002"):
                matches.append(p)
        if unverifiable_identity:
            if p := self._patterns.get("SCAM_PATTERN_003"):
                matches.append(p)
        if urgency_detected:
            if p := self._patterns.get("SCAM_PATTERN_004"):
                matches.append(p)
        if off_platform:
            if p := self._patterns.get("SCAM_PATTERN_005"):
                matches.append(p)
        if document_request:
            if p := self._patterns.get("SCAM_PATTERN_008"):
                matches.append(p)
        return [p for p in matches if p.active]

    def compute_threat_boost(self, matched_patterns: List[ScamPattern]) -> float:
        """
        §82: Pattern-based risk boost for CECT risk engine.
        Returns an additive boost (0.0 – 0.3) based on number and confidence of matched patterns.
        """
        if not matched_patterns:
            return 0.0
        score = 0.0
        for p in matched_patterns:
            if p.confidence == "HIGH":
                score += 0.10
            elif p.confidence == "MEDIUM":
                score += 0.06
            else:
                score += 0.03
        return min(0.30, round(score, 2))

    # ------------------------------------------------------------------
    # Pattern reporting (privacy-safe)
    # ------------------------------------------------------------------

    def report_pattern(
        self,
        pattern_type: str,
        geography: Optional[str] = None,
        domain: Optional[str] = None,
    ) -> str:
        """
        Accept an anonymized community report and update the relevant pattern counter.
        The domain is stored ONLY as an HMAC hash — never as raw text.
        Returns the matching pattern_id or 'UNKNOWN' if no pattern matches.
        """
        # Map signal type → pattern
        type_to_id = {
            "UPFRONT_FEE": "SCAM_PATTERN_001",
            "DOMAIN_MISMATCH": "SCAM_PATTERN_002",
            "UNVERIFIABLE_IDENTITY": "SCAM_PATTERN_003",
            "URGENCY": "SCAM_PATTERN_004",
            "OFF_PLATFORM_MOVE": "SCAM_PATTERN_005",
            "FAKE_FOREIGN_OFFER": "SCAM_PATTERN_006",
            "SALARY_TOO_GOOD": "SCAM_PATTERN_007",
            "DOCUMENT_REQUEST": "SCAM_PATTERN_008",
        }
        pattern_id = type_to_id.get(pattern_type.upper(), "UNKNOWN")
        if pattern_id == "UNKNOWN":
            logger.warning("Unknown pattern type reported: %s", pattern_type)
            return "UNKNOWN"

        pattern = self._patterns[pattern_id]
        pattern.report_count += 1
        pattern.last_seen = datetime.now(timezone.utc)
        if geography and not pattern.affected_geography:
            pattern.affected_geography = geography

        # Update confidence based on report count
        if pattern.report_count >= 20:
            pattern.confidence = "HIGH"
        elif pattern.report_count >= 5:
            pattern.confidence = "MEDIUM"

        # Store hashed domain only
        if domain:
            hashed = _hash_domain(domain)
            if hashed not in self._domain_to_patterns:
                self._domain_to_patterns[hashed] = []
            if pattern_id not in self._domain_to_patterns[hashed]:
                self._domain_to_patterns[hashed].append(pattern_id)
            if hashed not in pattern.hashed_domains:
                pattern.hashed_domains.append(hashed)

        logger.info("Pattern %s updated: report_count=%d", pattern_id, pattern.report_count)
        return pattern_id

    def list_active_patterns(self) -> List[dict]:
        """Return all active patterns as public, privacy-safe dicts."""
        return [p.to_public_dict() for p in self._patterns.values() if p.active]

    def get_pattern(self, pattern_id: str) -> Optional[dict]:
        """Return a single pattern by ID."""
        p = self._patterns.get(pattern_id)
        return p.to_public_dict() if p else None

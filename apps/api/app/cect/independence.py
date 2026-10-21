"""
LifeLens Ω — Evidence Independence Engine
Implementation Plan §14-E, §45, §60

Question: Is the evidence independent of the person making the claim? (§14-E)

Evidence dimensions (§45):
  Source Independence
  Source Authority
  Verifiability
  Freshness
  Relevance
  Consistency

Evidence priority order (§14-E):
  Authoritative public source (highest)
  → Official company source
  → Verified third-party source
  → Independent public source
  → Recruiter-provided evidence
  → Unverified screenshot / forwarded document (lowest)

Values are configuration-driven and empirically evaluated (§45).
"""
from __future__ import annotations
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import List

from ..models.evidence import Evidence, SourceStatus

logger = logging.getLogger(__name__)

# Source type → (independence, authority)
# ASSUMPTION: initial values; must be evaluated with test data (§45)
_SOURCE_DIMENSIONS: dict[str, tuple[float, float]] = {
    "REGISTRY": (1.0, 0.95),          # government registry — highest independence + authority
    "DOMAIN": (1.0, 0.70),            # automated check — independent
    "OFFICIAL_WEBSITE": (0.7, 0.80),  # company's own site — moderate independence
    "THIRD_PARTY": (0.6, 0.60),
    "JOB_BOARD": (0.5, 0.50),
    "RECRUITER_PROVIDED": (0.1, 0.20),
    "SCREENSHOT": (0.05, 0.10),
    "FORWARDED_DOCUMENT": (0.05, 0.10),
    "MANUAL": (0.3, 0.30),
}

_STALE_AFTER_HOURS = 24  # Evidence older than this is considered stale


@dataclass
class IndependenceResult:
    """Output of evidence independence analysis."""
    score: float              # 0.0 (all recruiter-provided) – 1.0 (all authoritative)
    findings: List[str] = field(default_factory=list)
    low_independence_evidence_ids: List[str] = field(default_factory=list)
    high_independence_evidence_ids: List[str] = field(default_factory=list)
    effective_participant_sources: Optional[int] = None
    rule_c_applied: bool = False


class EvidenceIndependenceEngine:
    """
    Evidence Independence Engine — §14-E, §45.
    Implements Rule C Evidence Independence for multi-participant sessions.

    The exact weight values are configuration-driven and must be
    empirically evaluated (§45).
    """

    def analyze(
        self,
        evidence_list: List[Evidence],
        participants: Optional[List[Any]] = None,
    ) -> IndependenceResult:
        rule_c_applied = False
        effective_participant_sources = None
        if not evidence_list:
            return IndependenceResult(
                score=0.0,
                findings=["No evidence collected — independence cannot be assessed."],
            )

        available = [
            e for e in evidence_list
            if e.source_status not in (SourceStatus.UNAVAILABLE, SourceStatus.NOT_APPLICABLE)
        ]

        if not available:
            return IndependenceResult(
                score=0.0,
                findings=[
                    "All evidence sources were unavailable. "
                    "Independence cannot be assessed — this does NOT indicate fraud."
                ],
            )

        weighted_sum = 0.0
        weight_total = 0.0
        low_ids: List[str] = []
        high_ids: List[str] = []
        findings: List[str] = []

        for e in available:
            if getattr(e, "is_simulated", False):
                # Simulated/mocked fallback evidence contributes zero evidence weight
                independence, authority = (0.0, 0.0)
                low_ids.append(e.evidence_id)
                findings.append(f"Evidence from {e.source_name} is SIMULATED (mocked fallback) and contributes 0 weight.")
                continue

            dims = _SOURCE_DIMENSIONS.get(
                e.source_type.upper(),
                (0.3, 0.3),  # default for unknown source types
            )
            independence, authority = dims

            # Freshness dimension (§45)
            age_hours = (datetime.now(timezone.utc) - e.captured_at.replace(tzinfo=e.captured_at.tzinfo or timezone.utc)).total_seconds() / 3600
            freshness = 1.0 if age_hours < _STALE_AFTER_HOURS else 0.5

            # Combined evidence strength
            strength = independence * authority * freshness

            weighted_sum += independence
            weight_total += 1.0

            if independence < 0.3:
                low_ids.append(e.evidence_id)
            elif independence >= 0.7:
                high_ids.append(e.evidence_id)

        score = weighted_sum / weight_total if weight_total > 0 else 0.0

        if score >= 0.7:
            findings.append(
                "Evidence is primarily sourced from independent, authoritative sources."
            )
        elif score >= 0.4:
            findings.append(
                "Evidence has moderate independence. "
                "Some evidence relies on recruiter-provided information. "
                "Seek additional independent verification."
            )
        else:
            findings.append(
                "Evidence independence is low — most evidence comes from the recruiter "
                "or from sources that could not be independently verified. "
                "This is a risk signal, not proof of fraud."
            )

        if low_ids:
            findings.append(
                f"{len(low_ids)} evidence item(s) have low independence "
                f"(recruiter-provided or unverified)."
            )

        if participants:
            from apps.api.app.integrations.meeting_providers import ParticipantIndependenceAnalyzer
            p_analyzer = ParticipantIndependenceAnalyzer()
            p_res = p_analyzer.analyze_participant_independence(participants)
            effective_participant_sources = p_res.effective_independent_source_count
            if p_res.has_shared_origin_cluster:
                rule_c_applied = True
                findings.append(
                    f"Rule C applied: {p_res.raw_participant_count} participants sharing join origin "
                    f"collapsed into {p_res.effective_independent_source_count} independent evidence source."
                )
            if not p_res.can_achieve_verified_trust:
                score = min(score, 0.45)
                findings.append(
                    "Verified-trust outcome blocked: No independently verified participant present (§Rule C)."
                )

        return IndependenceResult(
            score=round(score, 3),
            findings=findings,
            low_independence_evidence_ids=low_ids,
            high_independence_evidence_ids=high_ids,
            effective_participant_sources=effective_participant_sources,
            rule_c_applied=rule_c_applied,
        )

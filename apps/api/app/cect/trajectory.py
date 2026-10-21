"""
LifeLens Ω — Trajectory Engine
Implementation Plan §14-T, §47, §60

Phase 1: tracks risk escalation in the JOB/RECRUITER journey only (§14-T).
This does NOT prove fraud — it indicates the interaction has moved
toward higher-risk actions (§14-T).

Stage mapping (§47):
  Stage 1 — Job posting
  Stage 2 — Recruiter contact
  Stage 3 — Off-platform move
  Stage 4 — Sensitive document request
  Stage 5 — Payment request
  Stage 6 — Urgency / pressure

Trajectory output (§47):
  STABLE
  INCREASING
  HIGH_RISK_ESCALATION
  INSUFFICIENT_DATA
"""
from __future__ import annotations
import logging
from dataclasses import dataclass, field
from typing import List

from ..models.claim import Claim, ClaimType

logger = logging.getLogger(__name__)


class TrajectoryStatus:
    STABLE = "STABLE"
    INCREASING = "INCREASING"
    HIGH_RISK_ESCALATION = "HIGH_RISK_ESCALATION"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


@dataclass
class TrajectoryResult:
    """Output of trajectory analysis."""
    status: str               # see TrajectoryStatus
    score: float              # 0.0 (stable) – 1.0 (maximum escalation)
    stages_detected: List[str] = field(default_factory=list)
    findings: List[str] = field(default_factory=list)


class TrajectoryEngine:
    """
    Phase 1 trajectory engine.
    Identifies how many risk-escalation stages are present in the claims.
    §14-T, §47.

    NOTE: Trajectory output does NOT prove fraud (§14-T).
    It indicates an interaction has moved toward higher-risk actions.
    """

    # Stage → (claim types that indicate this stage, stage weight)
    _STAGES = [
        ("Stage 1 — Job posting",           [],                                    0.0),
        ("Stage 2 — Recruiter contact",     [ClaimType.CONTACT],                   0.1),
        ("Stage 3 — Off-platform move",     [ClaimType.CONTACT],                   0.2),
        ("Stage 4 — Sensitive doc request", [ClaimType.DOCUMENT],                  0.4),
        ("Stage 5 — Payment request",       [ClaimType.PAYMENT],                   0.7),
        ("Stage 6 — Urgency/pressure",      [ClaimType.URGENCY],                   0.3),
    ]

    def analyze(self, claims: List[Claim]) -> TrajectoryResult:
        claim_types = {c.claim_type for c in claims}
        stages_detected: List[str] = ["Stage 1 — Job posting"]  # always present
        findings: List[str] = []
        cumulative_score = 0.0

        has_payment = ClaimType.PAYMENT in claim_types
        has_document = ClaimType.DOCUMENT in claim_types
        has_contact = ClaimType.CONTACT in claim_types
        has_urgency = ClaimType.URGENCY in claim_types

        if has_contact:
            stages_detected.append("Stage 2 — Recruiter contact")
            # check for off-platform specifically
            off_platform_claims = [
                c for c in claims
                if c.claim_type == ClaimType.CONTACT
                and any(kw in c.claim_text.lower() for kw in
                        ["whatsapp", "telegram", "signal", "text me", "directly"])
            ]
            if off_platform_claims:
                stages_detected.append("Stage 3 — Off-platform move")
                cumulative_score += 0.2
                findings.append(
                    "Recruiter is requesting off-platform communication — "
                    "a trajectory escalation indicator."
                )

        if has_document:
            stages_detected.append("Stage 4 — Sensitive document request")
            cumulative_score += 0.4
            findings.append(
                "Sensitive document request detected. "
                "Do not provide passport, financial or ID documents until the recruiter "
                "is independently verified."
            )

        if has_payment:
            stages_detected.append("Stage 5 — Payment request")
            cumulative_score += 0.7
            findings.append(
                "Payment request detected. "
                "Legitimate employers do not require payment from candidates. "
                "Do not send money or enter payment details."
            )

        if has_urgency:
            stages_detected.append("Stage 6 — Urgency/pressure")
            cumulative_score += 0.3
            findings.append(
                "Urgency or time pressure detected — "
                "a common tactic to prevent careful verification."
            )

        # Normalize score to 0.0–1.0
        score = min(cumulative_score, 1.0)

        # Determine status
        if len(stages_detected) <= 1:
            status = TrajectoryStatus.INSUFFICIENT_DATA
            findings.append(
                "Only the initial job posting stage was detected — "
                "trajectory analysis requires more interaction data."
            )
        elif score >= 0.6:
            status = TrajectoryStatus.HIGH_RISK_ESCALATION
            findings.insert(0,
                "The interaction has escalated to high-risk stages "
                "(payment request and/or sensitive document request). "
                "Stop and verify independently before proceeding."
            )
        elif score >= 0.2:
            status = TrajectoryStatus.INCREASING
            findings.insert(0,
                "The interaction is showing increasing risk indicators. "
                "Verify the recruiter and company independently before continuing."
            )
        else:
            status = TrajectoryStatus.STABLE
            findings.insert(0, "No significant trajectory escalation detected.")

        return TrajectoryResult(
            status=status,
            score=round(score, 3),
            stages_detected=stages_detected,
            findings=findings,
        )

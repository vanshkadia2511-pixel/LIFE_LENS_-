"""
LifeLens Ω — Trust Trajectory Analyzer (Phase 2, §83)

Models the escalation trajectory of a recruitment interaction over time:
    Initial Contact → Trust Building → Off-Platform → Sensitive Info → Financial Request → Pressure

Instead of classifying one event as Safe/Scam, this models change over time.

Output trajectory:
    STABLE | INCREASING_RISK | HIGH_RISK_ESCALATION
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class TrajectoryStage(str, Enum):
    """
    §83: Interaction trajectory stages.
    These represent the natural progression of a recruitment scam.
    """
    INITIAL_CONTACT = "INITIAL_CONTACT"
    TRUST_BUILDING = "TRUST_BUILDING"
    OFF_PLATFORM_MOVE = "OFF_PLATFORM_MOVE"
    SENSITIVE_INFORMATION = "SENSITIVE_INFORMATION"
    FINANCIAL_REQUEST = "FINANCIAL_REQUEST"
    PRESSURE = "PRESSURE"


class TrajectoryLabel(str, Enum):
    """§83: Trajectory output labels."""
    STABLE = "STABLE"
    INCREASING_RISK = "INCREASING_RISK"
    HIGH_RISK_ESCALATION = "HIGH_RISK_ESCALATION"


# Stage ordering for severity calculation (higher = worse)
STAGE_SEVERITY: Dict[TrajectoryStage, int] = {
    TrajectoryStage.INITIAL_CONTACT: 0,
    TrajectoryStage.TRUST_BUILDING: 1,
    TrajectoryStage.OFF_PLATFORM_MOVE: 2,
    TrajectoryStage.SENSITIVE_INFORMATION: 3,
    TrajectoryStage.FINANCIAL_REQUEST: 4,
    TrajectoryStage.PRESSURE: 5,
}


@dataclass
class TrustTrajectoryEvent:
    """A single event in the interaction trajectory."""
    stage: TrajectoryStage
    signal: str           # Human-readable description of the observed signal
    observed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    confidence: float = 1.0


@dataclass
class TrustTrajectoryAssessment:
    """Full trajectory assessment output (§83)."""
    trajectory: TrajectoryLabel
    current_stage: TrajectoryStage
    stage_severity: int        # 0–5
    events: List[TrustTrajectoryEvent]
    stage_progression: List[str]   # ordered stage names observed
    trajectory_score: float        # 0.0 (stable) to 1.0 (full escalation)
    explanation: str
    signals_detected: List[str]
    recommended_action: str


class TrustTrajectoryAnalyzer:
    """
    §83 — Trust Trajectory Engine.

    Analyzes the current interaction signals to determine how far along the
    scam escalation trajectory the interaction has progressed.

    Stage progression:
    ─────────────────────────────────────────────────────
    INITIAL_CONTACT → TRUST_BUILDING → OFF_PLATFORM_MOVE
      → SENSITIVE_INFORMATION → FINANCIAL_REQUEST → PRESSURE
    ─────────────────────────────────────────────────────

    A trajectory is not about a single signal; it's about which stages have
    already been crossed relative to where the interaction currently stands.
    """

    def analyze(
        self,
        *,
        # Stage presence signals
        has_initial_contact: bool = True,
        has_trust_building_claims: bool = False,      # excessive rapport, personal stories
        has_moved_off_platform: bool = False,         # WhatsApp, Telegram, personal email
        has_requested_sensitive_info: bool = False,   # passport, SSN, bank account
        has_payment_request: bool = False,            # any upfront fee request
        has_pressure_tactics: bool = False,           # urgency, threats, deadlines
        # Optional context
        interaction_age_days: Optional[int] = None,
        claimed_country: Optional[str] = None,
    ) -> TrustTrajectoryAssessment:
        """
        Run the trajectory analysis and return a TrustTrajectoryAssessment.
        """
        events: List[TrustTrajectoryEvent] = []
        signals_detected: List[str] = []

        # Detect which stages are present
        if has_initial_contact:
            events.append(TrustTrajectoryEvent(
                stage=TrajectoryStage.INITIAL_CONTACT,
                signal="Recruiter has made initial contact.",
            ))

        if has_trust_building_claims:
            events.append(TrustTrajectoryEvent(
                stage=TrajectoryStage.TRUST_BUILDING,
                signal="Recruiter is engaging in excessive trust-building (personal stories, rapid familiarity).",
            ))
            signals_detected.append("Excessive trust-building behavior detected.")

        if has_moved_off_platform:
            events.append(TrustTrajectoryEvent(
                stage=TrajectoryStage.OFF_PLATFORM_MOVE,
                signal="Communication has moved off the professional platform (e.g., WhatsApp, Telegram, personal email).",
                confidence=0.9,
            ))
            signals_detected.append("Off-platform communication move detected.")

        if has_requested_sensitive_info:
            events.append(TrustTrajectoryEvent(
                stage=TrajectoryStage.SENSITIVE_INFORMATION,
                signal="Recruiter has requested sensitive personal information (passport, bank details, SSN).",
                confidence=0.95,
            ))
            signals_detected.append("Sensitive information request detected.")

        if has_payment_request:
            events.append(TrustTrajectoryEvent(
                stage=TrajectoryStage.FINANCIAL_REQUEST,
                signal="Recruiter has requested upfront payment (visa fee, processing fee, equipment deposit).",
                confidence=1.0,
            ))
            signals_detected.append("Financial / upfront payment request detected.")

        if has_pressure_tactics:
            events.append(TrustTrajectoryEvent(
                stage=TrajectoryStage.PRESSURE,
                signal="Pressure tactics in use — artificial deadlines, urgency, or consequences threatened.",
                confidence=1.0,
            ))
            signals_detected.append("Pressure / urgency tactics detected.")

        # Sort by stage severity to determine the highest stage reached
        sorted_events = sorted(events, key=lambda e: STAGE_SEVERITY[e.stage])
        stage_progression = [e.stage.value for e in sorted_events]

        if sorted_events:
            current_stage = sorted_events[-1].stage
        else:
            current_stage = TrajectoryStage.INITIAL_CONTACT

        severity = STAGE_SEVERITY[current_stage]
        # Trajectory score: linear mapping of severity to 0.0–1.0
        max_severity = max(STAGE_SEVERITY.values())
        trajectory_score = round(severity / max_severity, 2) if max_severity > 0 else 0.0

        # Determine trajectory label
        trajectory = self._compute_label(severity, events)

        # Build explanation
        explanation = self._build_explanation(trajectory, current_stage, signals_detected, interaction_age_days)
        recommended_action = self._recommended_action(trajectory, current_stage)

        return TrustTrajectoryAssessment(
            trajectory=trajectory,
            current_stage=current_stage,
            stage_severity=severity,
            events=events,
            stage_progression=stage_progression,
            trajectory_score=trajectory_score,
            explanation=explanation,
            signals_detected=signals_detected,
            recommended_action=recommended_action,
        )

    def _compute_label(self, severity: int, events: List[TrustTrajectoryEvent]) -> TrajectoryLabel:
        """§83: Map severity and events to one of: STABLE | INCREASING_RISK | HIGH_RISK_ESCALATION."""
        if severity >= 4:
            # Financial request or pressure = always HIGH_RISK_ESCALATION
            return TrajectoryLabel.HIGH_RISK_ESCALATION
        if severity >= 2:
            # Off-platform move or above = INCREASING_RISK
            return TrajectoryLabel.INCREASING_RISK
        if len(events) > 1 and severity >= 1:
            return TrajectoryLabel.INCREASING_RISK
        return TrajectoryLabel.STABLE

    def _build_explanation(
        self,
        trajectory: TrajectoryLabel,
        current_stage: TrajectoryStage,
        signals: List[str],
        interaction_age_days: Optional[int],
    ) -> str:
        """Generate a human-readable trajectory explanation."""
        stage_name = current_stage.value.replace("_", " ").title()
        age_note = f" The interaction is approximately {interaction_age_days} days old." if interaction_age_days else ""

        if trajectory == TrajectoryLabel.STABLE:
            return (
                f"The interaction appears to be at the {stage_name} stage and has not shown "
                f"escalating risk indicators.{age_note} Continue monitoring."
            )
        elif trajectory == TrajectoryLabel.INCREASING_RISK:
            signal_text = " ".join(signals) if signals else "Multiple warning indicators are present."
            return (
                f"The interaction has progressed to the {stage_name} stage, which indicates "
                f"increasing risk. {signal_text}{age_note} "
                f"Do not share sensitive information until independently verified."
            )
        else:  # HIGH_RISK_ESCALATION
            signal_text = " ".join(signals) if signals else "Critical warning indicators are present."
            return (
                f"HIGH RISK ESCALATION DETECTED. The interaction is at the {stage_name} stage — "
                f"this matches patterns of known employment scam trajectories. {signal_text}{age_note} "
                f"Do not send money or personal documents. Contact the company via its official website."
            )

    def _recommended_action(
        self,
        trajectory: TrajectoryLabel,
        current_stage: TrajectoryStage,
    ) -> str:
        """Return the recommended user action for this trajectory."""
        if trajectory == TrajectoryLabel.STABLE:
            return "Continue verification through official channels before sharing any personal information."
        elif trajectory == TrajectoryLabel.INCREASING_RISK:
            return (
                "Stop and independently verify: contact the company through its official website. "
                "Do NOT respond to the recruiter through off-platform channels."
            )
        else:
            return (
                "Do NOT send money, documents, or personal information. "
                "Contact the company directly via its official website. "
                "Consider reporting this interaction."
            )


def trajectory_assessment_to_dict(assessment: TrustTrajectoryAssessment) -> dict:
    """Serialize assessment for API responses."""
    return {
        "trajectory": assessment.trajectory.value,
        "current_stage": assessment.current_stage.value,
        "stage_severity": assessment.stage_severity,
        "trajectory_score": assessment.trajectory_score,
        "stage_progression": assessment.stage_progression,
        "signals_detected": assessment.signals_detected,
        "explanation": assessment.explanation,
        "recommended_action": assessment.recommended_action,
    }

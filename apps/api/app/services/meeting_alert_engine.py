"""
LifeLens Ω — Phase 3: Real-Time Meeting Alert Engine (§4.3)

Provides real-time alerts during video/audio meetings when authenticity
signals fall below safety thresholds. Integrates with the Media Authenticity
Provider abstraction (§99) and the CECT engine.

Architecture:
    Live Meeting Stream → Capture Frame/Audio
        → Consent Gate (§35)
        → MediaAuthenticityOrchestrator
        → Signal Evaluation
        → Alert Decision
        → User Notification
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

from .media_authenticity import (
    AuthenticityResult,
    AuthenticitySignal,
    MediaAuthenticityOrchestrator,
    MediaCapture,
    MediaType,
)

logger = logging.getLogger(__name__)


class AlertSeverity(str, Enum):
    """Severity levels for real-time meeting alerts."""
    INFO = "INFO"
    WARNING = "WARNING"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class MeetingAlert:
    """A single real-time alert generated during a meeting."""
    alert_id: str
    severity: AlertSeverity
    title: str
    message: str
    authenticity_signal: AuthenticitySignal
    confidence: float
    indicators: List[str]
    recommended_action: str
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    dismissed: bool = False

    def to_dict(self) -> dict:
        return {
            "alert_id": self.alert_id,
            "severity": self.severity.value,
            "title": self.title,
            "message": self.message,
            "authenticity_signal": self.authenticity_signal.value,
            "confidence": self.confidence,
            "indicators": self.indicators,
            "recommended_action": self.recommended_action,
            "generated_at": self.generated_at.isoformat(),
        }


class MeetingAlertEngine:
    """
    §4.3: Real-time meeting alert engine.

    Evaluates authenticity results from the media provider and generates
    structured alerts when synthetic media is detected during a live interaction.

    Thresholds:
        CRITICAL  → SYNTHETIC signal with confidence ≥ 0.80
        HIGH      → LIKELY_SYNTHETIC with confidence ≥ 0.65
        WARNING   → LIKELY_SYNTHETIC with confidence < 0.65 or UNCERTAIN
        INFO      → LIKELY_AUTHENTIC or AUTHENTIC (informational only)
    """

    CRITICAL_THRESHOLD = 0.80
    HIGH_THRESHOLD = 0.65

    def __init__(self, orchestrator: Optional[MediaAuthenticityOrchestrator] = None) -> None:
        self._orchestrator = orchestrator or MediaAuthenticityOrchestrator()
        self._alert_history: List[MeetingAlert] = []

    def evaluate(self, capture: MediaCapture) -> Optional[MeetingAlert]:
        """
        Evaluate a media capture and return a MeetingAlert if warranted.

        Returns None if the media is authentic or the provider is unavailable
        (consistent with §25 Failure Handling — do not alarm users without evidence).
        """
        result = self._orchestrator.analyze(capture)

        if not result.is_available:
            logger.debug("Media analysis unavailable — no alert generated.")
            return None

        alert = self._build_alert(result)
        if alert:
            self._alert_history.append(alert)
        return alert

    def _build_alert(self, result: AuthenticityResult) -> Optional[MeetingAlert]:
        """Map an AuthenticityResult to a MeetingAlert (or None if no alert needed)."""
        import uuid
        alert_id = f"alert-{uuid.uuid4().hex[:8]}"

        if result.signal == AuthenticitySignal.SYNTHETIC and result.confidence >= self.CRITICAL_THRESHOLD:
            return MeetingAlert(
                alert_id=alert_id,
                severity=AlertSeverity.CRITICAL,
                title="⛔ Synthetic Media Detected",
                message=(
                    f"The {result.media_type.value.lower()} in this meeting appears to be AI-generated "
                    f"or manipulated (confidence: {result.confidence:.0%}). "
                    "This may indicate a deepfake video call."
                ),
                authenticity_signal=result.signal,
                confidence=result.confidence,
                indicators=result.indicators,
                recommended_action=(
                    "Stop the meeting. Do not share personal information, make payments, "
                    "or comply with any requests. Verify the caller's identity through "
                    "an independent official channel (call their registered office number)."
                ),
            )

        elif result.signal in (AuthenticitySignal.SYNTHETIC, AuthenticitySignal.LIKELY_SYNTHETIC):
            severity = AlertSeverity.HIGH if result.confidence >= self.HIGH_THRESHOLD else AlertSeverity.WARNING
            return MeetingAlert(
                alert_id=alert_id,
                severity=severity,
                title="⚠️ Possible Synthetic Media Detected",
                message=(
                    f"The {result.media_type.value.lower()} in this meeting shows indicators "
                    f"of synthetic manipulation (confidence: {result.confidence:.0%}). "
                    "Exercise caution."
                ),
                authenticity_signal=result.signal,
                confidence=result.confidence,
                indicators=result.indicators,
                recommended_action=(
                    "Do not share sensitive documents or make payments during this call. "
                    "Request an alternative verification method (e.g., in-person meeting, "
                    "official company email confirmation)."
                ),
            )

        elif result.signal == AuthenticitySignal.UNCERTAIN:
            return MeetingAlert(
                alert_id=alert_id,
                severity=AlertSeverity.INFO,
                title="ℹ️ Media Authenticity Uncertain",
                message=(
                    f"Authenticity of the {result.media_type.value.lower()} could not be "
                    "conclusively determined. This does not mean the media is fake."
                ),
                authenticity_signal=result.signal,
                confidence=result.confidence,
                indicators=result.indicators,
                recommended_action=(
                    "Continue the meeting with standard caution. "
                    "Independently verify any significant claims made during this call."
                ),
            )

        # AUTHENTIC / LIKELY_AUTHENTIC — no alert needed
        return None

    def get_alert_history(self) -> List[dict]:
        return [a.to_dict() for a in self._alert_history]

    def get_session_summary(self) -> dict:
        """Return an authenticity summary for the full meeting session."""
        if not self._alert_history:
            return {
                "total_alerts": 0,
                "highest_severity": None,
                "session_verdict": "NO_CONCERNS_DETECTED",
                "recommendation": "No synthetic media indicators were detected during this session.",
            }
        severities = [a.severity for a in self._alert_history if not a.dismissed]
        order = [AlertSeverity.CRITICAL, AlertSeverity.HIGH, AlertSeverity.WARNING, AlertSeverity.INFO]
        highest = next((s for s in order if s in severities), AlertSeverity.INFO)

        verdict_map = {
            AlertSeverity.CRITICAL: "HIGH_RISK_SYNTHETIC_DETECTED",
            AlertSeverity.HIGH: "LIKELY_SYNTHETIC_DETECTED",
            AlertSeverity.WARNING: "UNCERTAIN_AUTHENTICITY",
            AlertSeverity.INFO: "INCONCLUSIVE",
        }
        return {
            "total_alerts": len(self._alert_history),
            "highest_severity": highest.value,
            "session_verdict": verdict_map[highest],
            "recommendation": self._alert_history[-1].recommended_action if self._alert_history else "",
        }

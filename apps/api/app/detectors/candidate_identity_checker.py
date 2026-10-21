"""
LifeLens Ω — Phase G: Employer-Side Candidate Identity Checks
Reverse-direction interview integrity checks (proxy candidate, audio-video desync,
virtual camera routing, background coaching).
Adheres strictly to Rule A (Never labels candidates "fake" or "cheater"; returns "Needs Verification")
and Rule B (telemetry/media signals capped and transparently provenanced).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class CandidateReport:
    candidate_id: str
    integrity_verdict: str  # Rule A: "Needs Verification", "Verification step completed", "Request looks high-risk"
    risk_score: float
    anomalies: List[str] = field(default_factory=list)
    telemetry_summary: Dict[str, Any] = field(default_factory=dict)
    recommendation: str = (
        "Session telemetry indicates technical variance. Conduct an interactive oral "
        "follow-up question or in-person verification step before making determinations."
    )


class CandidateIdentityChecker:
    """
    Evaluates employer-side candidate technical telemetry for interview proxy patterns
    without storing biometric templates or making defamatory accusations.
    """

    def evaluate_candidate_session(self, telemetry: Dict[str, Any]) -> CandidateReport:
        candidate_id = telemetry.get("candidate_id", "unknown_candidate")
        anomalies: List[str] = []
        score = 0.0

        desync_ms = telemetry.get("audio_video_desync_ms", 0)
        if desync_ms > 200:
            anomalies.append(f"High audio-video desync ({desync_ms}ms) indicative of virtual audio routing or proxy relay")
            score += 0.35

        tab_switches = telemetry.get("tab_switches_per_min", 0)
        if tab_switches >= 10:
            anomalies.append(f"Elevated tab switches ({tab_switches}/min) during assessment")
            score += 0.20

        if telemetry.get("multiple_faces_detected", False):
            anomalies.append("Multiple faces detected in camera frame during individual assessment")
            score += 0.30

        cadence_score = telemetry.get("unnatural_speech_cadence_score", 0.0)
        if cadence_score >= 0.70:
            anomalies.append(f"Unnatural speech cadence ({cadence_score:.2f}) consistent with text-to-speech or remote ear-piece prompter")
            score += 0.20

        if telemetry.get("virtual_webcam_driver", False):
            anomalies.append("Virtual webcam driver detected (OBS Virtual Camera / v4l2loopback)")
            score += 0.25

        risk_score = min(1.0, round(score, 2))

        if risk_score >= 0.50:
            integrity_verdict = "Needs Verification"
        elif risk_score >= 0.20:
            integrity_verdict = "Needs Verification"
        else:
            integrity_verdict = "Verification step completed"

        return CandidateReport(
            candidate_id=candidate_id,
            integrity_verdict=integrity_verdict,
            risk_score=risk_score,
            anomalies=anomalies,
            telemetry_summary={
                "audio_video_desync_ms": desync_ms,
                "tab_switches_per_min": tab_switches,
                "multiple_faces_detected": telemetry.get("multiple_faces_detected", False),
                "unnatural_speech_cadence_score": cadence_score,
            },
        )

"""
LifeLens Ω — Rule B Media Signal Cap & Rule A Person Labeling Tests
Phase A Item 4:
- Rule B: Media forensics (face/voice) is a LOW-WEIGHT signal with a hard cap on its
  contribution to final risk. It must never be the sole basis for a HIGH/CRITICAL result.
- Rule A: Never label a PERSON as 'fake', 'real', 'scammer', or 'verified human'.
  Allowed outputs: 'Needs Verification', 'Not independently verified',
  'Verification step completed', 'Request looks high-risk'.
- Heuristic audit: All heuristics explain what they actually measure;
  blinking regularity score cannot trigger standalone alarms.
"""
from datetime import datetime, timezone
import pytest

from apps.api.app.services.meeting_shield import (
    MeetingShieldOrchestrator,
    HEURISTIC_EXPLANATIONS,
)
from apps.api.app.cect.unified_reasoner import UnifiedCECTReasoner
from apps.api.app.models.request import VerificationRequest
from apps.api.app.risk.engine import RiskLevel


def test_rule_b_media_signals_cannot_solely_trigger_high_or_critical():
    """
    Asserts that active synthetic media alerts alone CANNOT escalate
    an otherwise legitimate / clean request to HIGH or CRITICAL risk.
    """
    shield = MeetingShieldOrchestrator()
    session = shield.start_session("Clean Interview with Deepfake Anomaly", user_consent=True)
    # Inject audio anomaly
    shield.ingest_audio_chunk(
        session_id=session.session_id,
        duration_ms=1000,
        spectral_flatness=0.9,
        pitch_variance=0.01,
        synthetic_voice_prob=0.95,
    )
    # Inject video anomaly
    shield.ingest_video_chunk(
        session_id=session.session_id,
        duration_ms=1000,
        lip_sync_error=0.85,
        facial_artifact_score=0.90,
        blinking_regularity_score=0.1,
    )

    reasoner = UnifiedCECTReasoner(meeting_shield=shield)
    clean_req = VerificationRequest(
        request_id="rule_b_clean_001",
        created_at=datetime.now(timezone.utc),
        job_title="Software Engineer",
        company_name="DeepMind Technologies Limited",
        company_website="https://deepmind.google",
        recruiter_name="DeepMind Careers",
        recruiter_email="careers@deepmind.google",
        claimed_country="GB",
        job_description="Standard software engineer role with official matching domains and verified presence.",
    )

    verdict_without_media = reasoner.evaluate_holistic_interaction(clean_req)
    base_score = verdict_without_media.overall_risk_score

    verdict_with_media = reasoner.evaluate_holistic_interaction(clean_req, meeting_session_id=session.session_id)
    boosted_score = verdict_with_media.overall_risk_score

    # 1. Hard cap check: delta must be <= 0.15
    delta = round(boosted_score - base_score, 3)
    assert delta <= 0.15, f"Rule B violation: Media risk boost {delta} exceeded hard cap of 0.15"

    # 2. Rule B gate: media alone CANNOT cause HIGH or CRITICAL
    assert verdict_with_media.overall_risk_level not in (RiskLevel.HIGH, RiskLevel.CRITICAL), (
        f"Rule B violation: Media alerts solely caused risk level to become {verdict_with_media.overall_risk_level}"
    )


def test_rule_a_verdict_vocabulary_enforcement():
    """
    Asserts that MeetingShield end_session safety_verdict outputs only Rule A permitted labels.
    """
    shield = MeetingShieldOrchestrator()
    
    # Clean session
    s1 = shield.start_session("Clean Session", user_consent=True)
    rep1 = shield.end_session(s1.session_id)
    assert rep1["safety_verdict"] == "Verification step completed"

    # Risky session
    s2 = shield.start_session("Risky Session", user_consent=True)
    shield.ingest_audio_chunk(s2.session_id, 1000, 0.9, 0.01, 0.95)
    rep2 = shield.end_session(s2.session_id)
    assert rep2["safety_verdict"] == "Request looks high-risk"

    ALLOWED_RULE_A_LABELS = {
        "Needs Verification",
        "Not independently verified",
        "Verification step completed",
        "Request looks high-risk",
    }
    assert rep1["safety_verdict"] in ALLOWED_RULE_A_LABELS
    assert rep2["safety_verdict"] in ALLOWED_RULE_A_LABELS


def test_blinking_regularity_score_cannot_trigger_standalone_alert():
    """
    Asserts that an abnormal blinking score alone with normal face/lip scores
    does NOT trigger any video deepfake alert.
    """
    shield = MeetingShieldOrchestrator()
    session = shield.start_session("Blink Test Session", user_consent=True)
    alert = shield.ingest_video_chunk(
        session_id=session.session_id,
        duration_ms=1000,
        lip_sync_error=0.1,             # normal
        facial_artifact_score=0.1,      # normal
        blinking_regularity_score=0.99, # abnormal blink rate
    )
    assert alert is None, "Blinking regularity score must NOT trigger standalone deepfake alert"


def test_heuristic_explanations_are_documented():
    """
    Verifies that all 6 heuristics have clear descriptions of what they actually measure.
    """
    expected_heuristics = [
        "spectral_flatness",
        "pitch_variance",
        "synthetic_voice_prob",
        "facial_artifact_score",
        "lip_sync_error",
        "blinking_regularity_score",
    ]
    for h in expected_heuristics:
        assert h in HEURISTIC_EXPLANATIONS
        assert len(HEURISTIC_EXPLANATIONS[h]) > 30

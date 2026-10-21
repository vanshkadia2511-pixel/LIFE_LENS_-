"""
LifeLens Ω — Phase E: Media Forensics & Calibration Test Suite
Tests:
- MediaAuthenticityProvider per-modality outputs with calibrated confidence
- Frequent INCONCLUSIVE verdict mapping for ambiguous/compressed media
- Expected Calibration Error (ECE) metric computation
- Rule B hard weight cap (max +0.15 risk boost in orchestrator and reasoner)
- Rule A compliance (never labels a person as fake or scammer)
- Executive reference biometric enrollment default status: NOT BUILT
"""
import pytest
from datetime import datetime, timezone

from apps.api.app.services.media_authenticity import (
    MediaAuthenticityOrchestrator,
    MockDeepfakeDetectionProvider,
    MediaCapture,
    MediaType,
    AuthenticitySignal,
    AuthenticityResult,
    compute_expected_calibration_error,
    ReferenceEnrollmentPolicy,
)


def test_media_authenticity_per_modality_outputs():
    """Verify provider outputs distinct per-modality signals (video, audio, image) with indicators."""
    provider = MockDeepfakeDetectionProvider()
    orchestrator = MediaAuthenticityOrchestrator(provider=provider)

    # Video modality
    video_capture = MediaCapture(
        media_type=MediaType.VIDEO,
        content_url="https://example.com/stream/deepfake_sample.mp4",
        user_consented=True,
    )
    v_res = orchestrator.analyze(video_capture)
    assert v_res.media_type == MediaType.VIDEO
    assert 0.0 <= v_res.confidence <= 1.0
    assert len(v_res.indicators) > 0
    assert "face_authenticity" in v_res.raw_scores or "lip_sync" in v_res.raw_scores

    # Audio modality
    audio_capture = MediaCapture(
        media_type=MediaType.AUDIO,
        content_url="https://example.com/stream/clone_voice.wav",
        user_consented=True,
    )
    a_res = orchestrator.analyze(audio_capture)
    assert a_res.media_type == MediaType.AUDIO
    assert 0.0 <= a_res.confidence <= 1.0
    assert len(a_res.indicators) > 0


def test_inconclusive_verdict_mapping_for_marginal_scores():
    """Verify that ambiguous, marginal, or uncalibrated signals map to INCONCLUSIVE (§Rule B)."""
    provider = MockDeepfakeDetectionProvider()

    # Borderline ambiguous video
    ambiguous_capture = MediaCapture(
        media_type=MediaType.VIDEO,
        content_url="https://example.com/stream/borderline_compressed.mp4",
        user_consented=True,
    )
    res = provider.analyze_video(ambiguous_capture)
    # Natural compression/borderline should yield INCONCLUSIVE or UNCERTAIN
    assert res.signal in (AuthenticitySignal.INCONCLUSIVE, AuthenticitySignal.UNCERTAIN)
    assert "inconclusive" in res.indicators[0].lower() or "uncertain" in res.indicators[0].lower()


def test_expected_calibration_error_computation():
    """Verify calculation of Expected Calibration Error (ECE) for model reliability assessment."""
    # Perfectly calibrated case (confidence == accuracy)
    confidences = [0.1, 0.2, 0.3, 0.7, 0.8, 0.9]
    labels = [0, 0, 0, 1, 1, 1]
    ece = compute_expected_calibration_error(confidences, labels, n_bins=5)
    assert 0.0 <= ece <= 0.25

    # Completely uncalibrated case (confidences opposite of labels)
    confidences_bad = [0.99, 0.95, 0.90, 0.05, 0.01]
    labels_bad = [0, 0, 0, 1, 1]
    ece_bad = compute_expected_calibration_error(confidences_bad, labels_bad, n_bins=5)
    assert ece_bad > 0.5


def test_rule_b_weight_cap_in_orchestrator():
    """Verify Rule B hard cap: media signals contribution is capped at max 0.15 boost."""
    orchestrator = MediaAuthenticityOrchestrator()

    # Even with SYNTHETIC signal and 1.0 confidence
    synthetic_res = AuthenticityResult(
        media_type=MediaType.VIDEO,
        signal=AuthenticitySignal.SYNTHETIC,
        confidence=1.0,
        provider_name="TestProvider",
        provider_version="1.0",
        analysis_latency_ms=10.0,
        consent_verified=True,
    )
    boost = orchestrator.get_risk_boost(synthetic_res)
    assert boost <= 0.15, f"Risk boost {boost} exceeded Rule B cap of 0.15"

    # INCONCLUSIVE / UNAVAILABLE should contribute zero or near-zero boost
    inconclusive_res = AuthenticityResult(
        media_type=MediaType.VIDEO,
        signal=AuthenticitySignal.INCONCLUSIVE,
        confidence=0.5,
        provider_name="TestProvider",
        provider_version="1.0",
        analysis_latency_ms=10.0,
        consent_verified=True,
    )
    assert orchestrator.get_risk_boost(inconclusive_res) <= 0.05


def test_rule_a_never_labels_person_as_fake():
    """Verify Rule A compliance: media analysis never describes a person as fake or real."""
    provider = MockDeepfakeDetectionProvider()
    capture = MediaCapture(
        media_type=MediaType.VIDEO,
        content_url="https://example.com/deepfake_test.mp4",
        user_consented=True,
    )
    res = provider.analyze_video(capture)

    forbidden_terms = ["fake person", "real person", "scammer", "fraudster", "verified human"]
    all_text = " ".join(res.indicators + [res.signal.value]).lower()
    for term in forbidden_terms:
        assert term not in all_text, f"Forbidden label '{term}' found in media output"


def test_executive_reference_enrollment_default_not_built():
    """Verify reference enrollment of real people's faces/voices is disabled / NOT BUILT by default."""
    policy = ReferenceEnrollmentPolicy()
    assert policy.is_built is False
    assert policy.status == "NOT_BUILT"
    assert "Requires explicit approved written privacy review" in policy.governance_rule
    with pytest.raises(NotImplementedError):
        policy.enroll_biometric_template("exec_01", b"dummy_audio_bytes")

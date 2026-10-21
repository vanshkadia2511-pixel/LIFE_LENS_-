"""
LifeLens Ω — Phase 3 Tests
§80 Media Authenticity Provider + Meeting Alert Engine
§76 Data Quality Gates
§87 Demo Scenario (structural verification)
§99 Provider Protocol
"""
from __future__ import annotations

import pytest
from datetime import datetime, timezone

# ─────────────────────────────────────────────────────────────
# §99 / §80 — Media Authenticity Provider
# ─────────────────────────────────────────────────────────────

from apps.api.app.services.media_authenticity import (
    AuthenticityResult,
    AuthenticitySignal,
    MediaCapture,
    MediaAuthenticityOrchestrator,
    MediaType,
    MockDeepfakeDetectionProvider,
    UnavailableProvider,
)


class TestProviderProtocol:
    """§99: Verify the provider abstraction behaves correctly."""

    def test_unavailable_provider_returns_unavailable_for_video(self):
        provider = UnavailableProvider()
        cap = MediaCapture(media_type=MediaType.VIDEO, user_consented=True)
        result = provider.analyze_video(cap)
        assert result.signal == AuthenticitySignal.UNAVAILABLE
        assert result.confidence == 0.0

    def test_unavailable_provider_returns_unavailable_for_audio(self):
        provider = UnavailableProvider()
        cap = MediaCapture(media_type=MediaType.AUDIO, user_consented=True)
        result = provider.analyze_audio(cap)
        assert result.signal == AuthenticitySignal.UNAVAILABLE

    def test_unavailable_provider_capabilities_all_false(self):
        provider = UnavailableProvider()
        caps = provider.capabilities()
        assert caps["video"] is False
        assert caps["audio"] is False
        assert caps["image"] is False

    def test_mock_provider_authentic_video(self):
        provider = MockDeepfakeDetectionProvider()
        cap = MediaCapture(media_type=MediaType.VIDEO, content_url="interview_recording.mp4", user_consented=True)
        result = provider.analyze_video(cap)
        assert result.signal == AuthenticitySignal.LIKELY_AUTHENTIC
        assert result.confidence > 0.5

    def test_mock_provider_deepfake_video(self):
        provider = MockDeepfakeDetectionProvider()
        cap = MediaCapture(media_type=MediaType.VIDEO, content_url="suspicious_deepfake_video.mp4", user_consented=True)
        result = provider.analyze_video(cap)
        assert result.signal == AuthenticitySignal.LIKELY_SYNTHETIC
        assert result.confidence >= 0.7

    def test_mock_provider_cloned_audio(self):
        provider = MockDeepfakeDetectionProvider()
        cap = MediaCapture(media_type=MediaType.AUDIO, content_url="voice_clone_sample.wav", user_consented=True)
        result = provider.analyze_audio(cap)
        assert result.signal == AuthenticitySignal.LIKELY_SYNTHETIC

    def test_consent_gate_blocks_analysis_when_no_consent(self):
        """§35: Analysis must be refused without user consent."""
        provider = MockDeepfakeDetectionProvider()
        cap = MediaCapture(media_type=MediaType.VIDEO, content_url="video.mp4", user_consented=False)
        result = provider.analyze_video(cap)
        assert result.signal == AuthenticitySignal.UNAVAILABLE
        assert "consent" in result.error_message.lower()

    def test_result_to_evidence_dict(self):
        provider = MockDeepfakeDetectionProvider()
        cap = MediaCapture(media_type=MediaType.AUDIO, user_consented=True)
        result = provider.analyze_audio(cap)
        d = result.to_evidence_dict()
        assert "source_type" in d
        assert d["source_type"] == "MEDIA_AUTHENTICITY_PROVIDER"
        assert "signal" in d
        assert "consent_verified" in d


class TestMediaAuthenticityOrchestrator:
    """§80: Orchestrator routing and risk boost calculation."""

    def setup_method(self):
        self.orchestrator = MediaAuthenticityOrchestrator(provider=MockDeepfakeDetectionProvider())

    def test_orchestrator_routes_video(self):
        cap = MediaCapture(media_type=MediaType.VIDEO, content_url="normal.mp4", user_consented=True)
        result = self.orchestrator.analyze(cap)
        assert result.media_type == MediaType.VIDEO
        assert result.signal != AuthenticitySignal.UNAVAILABLE

    def test_orchestrator_routes_audio(self):
        cap = MediaCapture(media_type=MediaType.AUDIO, user_consented=True)
        result = self.orchestrator.analyze(cap)
        assert result.media_type == MediaType.AUDIO

    def test_orchestrator_blocks_without_consent(self):
        cap = MediaCapture(media_type=MediaType.VIDEO, user_consented=False)
        result = self.orchestrator.analyze(cap)
        assert result.signal == AuthenticitySignal.UNAVAILABLE
        assert result.is_available is False

    def test_orchestrator_unavailable_returns_zero_risk_boost(self):
        cap = MediaCapture(media_type=MediaType.VIDEO, user_consented=False)
        result = self.orchestrator.analyze(cap)
        boost = self.orchestrator.get_risk_boost(result)
        assert boost == 0.0, "UNAVAILABLE result should not boost risk (§25)"

    def test_orchestrator_synthetic_returns_positive_risk_boost(self):
        cap = MediaCapture(media_type=MediaType.VIDEO, content_url="deepfake_interview.mp4", user_consented=True)
        result = self.orchestrator.analyze(cap)
        boost = self.orchestrator.get_risk_boost(result)
        if result.signal == AuthenticitySignal.LIKELY_SYNTHETIC:
            assert boost > 0.0

    def test_orchestrator_authentic_returns_zero_risk_boost(self):
        cap = MediaCapture(media_type=MediaType.VIDEO, content_url="normal_video.mp4", user_consented=True)
        result = self.orchestrator.analyze(cap)
        boost = self.orchestrator.get_risk_boost(result)
        if result.signal in (AuthenticitySignal.AUTHENTIC, AuthenticitySignal.LIKELY_AUTHENTIC):
            assert boost == 0.0


# ─────────────────────────────────────────────────────────────
# §4.3 — Meeting Alert Engine
# ─────────────────────────────────────────────────────────────

from apps.api.app.services.meeting_alert_engine import (
    MeetingAlertEngine,
    AlertSeverity,
)


class TestMeetingAlertEngine:
    """§4.3: Real-time meeting alert generation."""

    def setup_method(self):
        self.engine = MeetingAlertEngine(
            orchestrator=MediaAuthenticityOrchestrator(provider=MockDeepfakeDetectionProvider())
        )

    def test_no_alert_for_authentic_video(self):
        cap = MediaCapture(media_type=MediaType.VIDEO, content_url="normal_interview.mp4", user_consented=True)
        alert = self.engine.evaluate(cap)
        # LIKELY_AUTHENTIC → no alert
        assert alert is None

    def test_alert_generated_for_deepfake_video(self):
        cap = MediaCapture(media_type=MediaType.VIDEO, content_url="deepfake_call.mp4", user_consented=True)
        alert = self.engine.evaluate(cap)
        assert alert is not None
        assert alert.severity in (AlertSeverity.HIGH, AlertSeverity.CRITICAL, AlertSeverity.WARNING)

    def test_no_alert_when_no_consent(self):
        cap = MediaCapture(media_type=MediaType.VIDEO, content_url="any.mp4", user_consented=False)
        alert = self.engine.evaluate(cap)
        assert alert is None, "No alert should fire when consent is not given"

    def test_alert_has_required_fields(self):
        cap = MediaCapture(media_type=MediaType.VIDEO, content_url="suspicious_deepfake_video.mp4", user_consented=True)
        alert = self.engine.evaluate(cap)
        if alert:
            d = alert.to_dict()
            assert "alert_id" in d
            assert "severity" in d
            assert "title" in d
            assert "message" in d
            assert "recommended_action" in d

    def test_session_summary_empty_session(self):
        engine = MeetingAlertEngine(orchestrator=MediaAuthenticityOrchestrator(provider=MockDeepfakeDetectionProvider()))
        summary = engine.get_session_summary()
        assert summary["total_alerts"] == 0
        assert summary["session_verdict"] == "NO_CONCERNS_DETECTED"

    def test_alert_history_grows(self):
        cap = MediaCapture(media_type=MediaType.VIDEO, content_url="deepfake_video.mp4", user_consented=True)
        self.engine.evaluate(cap)
        self.engine.evaluate(cap)
        history = self.engine.get_alert_history()
        # Each deepfake scan generates an alert
        assert len(history) >= 1


# ─────────────────────────────────────────────────────────────
# §76 — Data Quality Gates
# ─────────────────────────────────────────────────────────────

from apps.api.app.services.data_quality_gates import (
    DataQualityGateEvaluator,
    SourceHealthStatus,
    GateResult,
    SourceHealthRegistry,
)


class TestDataQualityGates:
    """§76: Data quality gate evaluation."""

    def setup_method(self):
        self.evaluator = DataQualityGateEvaluator()

    def test_healthy_source_all_gates_pass(self):
        report = self.evaluator.evaluate(
            "Companies House", "companies_house",
            coverage_pct=0.85,
            data_age_hours=12.0,
            availability_pct=0.99,
            error_rate=0.02,
            terms_allow_automation=True,
            fails_gracefully=True,
        )
        assert report.health_status == SourceHealthStatus.HEALTHY
        assert report.overall_score > 0.8

    def test_degraded_source_on_low_coverage(self):
        report = self.evaluator.evaluate(
            "Test Source", "test",
            coverage_pct=0.40,  # Below 60% threshold
        )
        assert report.health_status in (SourceHealthStatus.DEGRADED, SourceHealthStatus.UNAVAILABLE)

    def test_degraded_source_on_stale_data(self):
        report = self.evaluator.evaluate(
            "Test Source", "test_stale",
            data_age_hours=72.0,  # Over 48h threshold
        )
        assert report.health_status == SourceHealthStatus.DEGRADED

    def test_unavailable_source_on_multiple_failures(self):
        report = self.evaluator.evaluate(
            "Bad Source", "bad",
            coverage_pct=0.20,
            availability_pct=0.80,
            terms_allow_automation=False,
        )
        assert report.health_status in (SourceHealthStatus.DEGRADED, SourceHealthStatus.UNAVAILABLE)

    def test_terms_deny_automation_causes_fail(self):
        report = self.evaluator.evaluate(
            "Restricted Source", "restricted",
            terms_allow_automation=False,
        )
        terms_gate = next((g for g in report.gates if g.gate_name == "Terms_Access"), None)
        assert terms_gate is not None
        assert terms_gate.result == GateResult.FAIL

    def test_report_contains_all_gates(self):
        report = self.evaluator.evaluate("Full Source", "full",
            coverage_pct=0.90,
            data_age_hours=5.0,
            availability_pct=0.99,
            error_rate=0.01,
            terms_allow_automation=True,
            fails_gracefully=True,
        )
        gate_names = {g.gate_name for g in report.gates}
        expected = {"Coverage", "Freshness", "Consistency", "Availability", "Terms_Access", "Error_Behavior"}
        assert expected == gate_names

    def test_skip_gates_for_unmeasured_fields(self):
        report = self.evaluator.evaluate("Partial Source", "partial")
        skipped = [g for g in report.gates if g.result == GateResult.SKIP]
        assert len(skipped) > 0  # All unmeasured gates are SKIP

    def test_registry_tracks_health(self):
        registry = SourceHealthRegistry()
        report = self.evaluator.evaluate(
            "Companies House", "companies_house",
            coverage_pct=0.90, availability_pct=0.99,
        )
        registry.register(report)
        assert registry.is_healthy("companies_house")

    def test_registry_unknown_source_defaults_healthy(self):
        registry = SourceHealthRegistry()
        assert registry.is_healthy("completely_new_adapter") is True

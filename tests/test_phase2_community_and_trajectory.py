"""
LifeLens Ω — Phase 2 Complete Tests
§82 Community Threat Intelligence
§83 Trust Trajectory
§70/71/73/75 Observability / Versioning / Kill Switches
"""
from __future__ import annotations

import pytest
from datetime import datetime, timezone

# ─────────────────────────────────────────────────────────────
# §82 — Community Threat Intelligence
# ─────────────────────────────────────────────────────────────

from apps.api.app.services.community_threat_intelligence import (
    CommunityThreatIntelligenceService,
    ScamPattern,
    _hash_domain,
)


class TestCommunityThreatIntelligence:
    """Tests for §82 Community Threat Intelligence."""

    def setup_method(self):
        self.svc = CommunityThreatIntelligenceService()

    def test_builtin_patterns_loaded(self):
        patterns = self.svc.list_active_patterns()
        assert len(patterns) >= 8, "At least 8 built-in scam patterns should be loaded"

    def test_all_patterns_are_public_safe(self):
        """Pattern public dicts must NOT expose hashed_domains."""
        for p in self.svc.list_active_patterns():
            assert "hashed_domains" not in p, "hashed_domains must not be in public output"
            assert "pattern_id" in p
            assert "pattern_type" in p
            assert "confidence" in p
            assert "report_count" in p

    def test_check_signals_domain_mismatch(self):
        matches = self.svc.check_signals(domain_mismatch=True)
        ids = [p.pattern_id for p in matches]
        assert "SCAM_PATTERN_002" in ids

    def test_check_signals_upfront_fee(self):
        matches = self.svc.check_signals(has_upfront_fee=True)
        ids = [p.pattern_id for p in matches]
        assert "SCAM_PATTERN_001" in ids

    def test_check_signals_multiple(self):
        matches = self.svc.check_signals(
            has_upfront_fee=True,
            domain_mismatch=True,
            urgency_detected=True,
        )
        assert len(matches) == 3

    def test_compute_threat_boost_zero_on_no_matches(self):
        boost = self.svc.compute_threat_boost([])
        assert boost == 0.0

    def test_compute_threat_boost_high_confidence(self):
        matches = self.svc.check_signals(has_upfront_fee=True, domain_mismatch=True)
        boost = self.svc.compute_threat_boost(matches)
        assert 0.0 < boost <= 0.30

    def test_report_pattern_increments_count(self):
        initial = self.svc.get_pattern("SCAM_PATTERN_001")["report_count"]
        self.svc.report_pattern("UPFRONT_FEE", geography="India")
        updated = self.svc.get_pattern("SCAM_PATTERN_001")["report_count"]
        assert updated == initial + 1

    def test_report_pattern_unknown_type_returns_unknown(self):
        result = self.svc.report_pattern("TOTALLY_MADE_UP")
        assert result == "UNKNOWN"

    def test_domain_hashing_is_deterministic(self):
        h1 = _hash_domain("example.com")
        h2 = _hash_domain("example.com")
        assert h1 == h2

    def test_domain_hashing_is_case_insensitive(self):
        h1 = _hash_domain("EXAMPLE.COM")
        h2 = _hash_domain("example.com")
        assert h1 == h2

    def test_domain_check_after_report(self):
        self.svc.report_pattern("UPFRONT_FEE", domain="scamdomain.biz")
        matches = self.svc.check_domain("scamdomain.biz")
        assert "SCAM_PATTERN_001" in matches

    def test_domain_check_raw_domain_not_stored(self):
        """The raw domain string must NOT appear anywhere in stored patterns."""
        self.svc.report_pattern("URGENCY", domain="rawdomain.test")
        for p in self.svc._patterns.values():
            for hd in p.hashed_domains:
                assert "rawdomain.test" not in hd, "Raw domain must not be stored"

    def test_confidence_upgrades_with_reports(self):
        for _ in range(25):
            self.svc.report_pattern("UPFRONT_FEE")
        p = self.svc.get_pattern("SCAM_PATTERN_001")
        assert p["confidence"] == "HIGH"

    def test_get_pattern_returns_none_for_invalid_id(self):
        result = self.svc.get_pattern("NOT_A_REAL_PATTERN")
        assert result is None


# ─────────────────────────────────────────────────────────────
# §83 — Trust Trajectory
# ─────────────────────────────────────────────────────────────

from apps.api.app.services.trust_trajectory import (
    TrustTrajectoryAnalyzer,
    TrajectoryLabel,
    TrajectoryStage,
    trajectory_assessment_to_dict,
)


class TestTrustTrajectory:
    """Tests for §83 Trust Trajectory Engine."""

    def setup_method(self):
        self.analyzer = TrustTrajectoryAnalyzer()

    def test_stable_initial_contact_only(self):
        result = self.analyzer.analyze(has_initial_contact=True)
        assert result.trajectory == TrajectoryLabel.STABLE
        assert result.current_stage == TrajectoryStage.INITIAL_CONTACT
        assert result.trajectory_score == 0.0

    def test_increasing_risk_off_platform(self):
        result = self.analyzer.analyze(
            has_initial_contact=True,
            has_moved_off_platform=True,
        )
        assert result.trajectory == TrajectoryLabel.INCREASING_RISK
        assert result.stage_severity >= 2

    def test_high_risk_payment_request(self):
        result = self.analyzer.analyze(
            has_initial_contact=True,
            has_payment_request=True,
        )
        assert result.trajectory == TrajectoryLabel.HIGH_RISK_ESCALATION
        assert result.current_stage == TrajectoryStage.FINANCIAL_REQUEST

    def test_high_risk_pressure_tactics(self):
        result = self.analyzer.analyze(
            has_initial_contact=True,
            has_pressure_tactics=True,
        )
        assert result.trajectory == TrajectoryLabel.HIGH_RISK_ESCALATION
        assert result.current_stage == TrajectoryStage.PRESSURE

    def test_full_escalation_path(self):
        """All stages active = maximum severity."""
        result = self.analyzer.analyze(
            has_initial_contact=True,
            has_trust_building_claims=True,
            has_moved_off_platform=True,
            has_requested_sensitive_info=True,
            has_payment_request=True,
            has_pressure_tactics=True,
        )
        assert result.trajectory == TrajectoryLabel.HIGH_RISK_ESCALATION
        assert result.trajectory_score == 1.0
        assert result.stage_severity == 5  # PRESSURE = 5

    def test_stage_progression_is_ordered(self):
        result = self.analyzer.analyze(
            has_initial_contact=True,
            has_moved_off_platform=True,
            has_payment_request=True,
        )
        # Stage progression should be in severity order
        stages_found = result.stage_progression
        assert stages_found[0] == TrajectoryStage.INITIAL_CONTACT.value
        # Last should be the highest severity stage
        assert stages_found[-1] == TrajectoryStage.FINANCIAL_REQUEST.value

    def test_signals_detected_populated(self):
        result = self.analyzer.analyze(
            has_moved_off_platform=True,
            has_payment_request=True,
        )
        assert len(result.signals_detected) >= 2

    def test_explanation_contains_stage(self):
        result = self.analyzer.analyze(
            has_payment_request=True,
        )
        assert "FINANCIAL" in result.explanation.upper() or "financial" in result.explanation.lower()

    def test_recommended_action_stable(self):
        result = self.analyzer.analyze()
        assert "official channels" in result.recommended_action.lower()

    def test_recommended_action_high_risk(self):
        result = self.analyzer.analyze(has_payment_request=True)
        assert "do not" in result.recommended_action.lower()

    def test_to_dict_serialization(self):
        result = self.analyzer.analyze(has_moved_off_platform=True)
        d = trajectory_assessment_to_dict(result)
        assert "trajectory" in d
        assert "current_stage" in d
        assert "trajectory_score" in d
        assert "explanation" in d
        assert "recommended_action" in d
        assert "events" not in d, "TrustTrajectoryEvent objects should not be in dict output"

    def test_interaction_age_in_explanation(self):
        result = self.analyzer.analyze(
            has_moved_off_platform=True,
            interaction_age_days=3,
        )
        assert "3" in result.explanation or "days" in result.explanation


# ─────────────────────────────────────────────────────────────
# §70/71/73/75 — Metrics, Versioning, Kill Switches
# ─────────────────────────────────────────────────────────────

from apps.api.app.services.metrics import MetricsService
from apps.api.app.services.versioning import (
    VersionManifest,
    KILL_SWITCHES,
    is_feature_enabled,
    disable_feature,
    enable_feature,
    list_kill_switches,
    CECT_VERSION,
)


class TestMetricsService:
    """Tests for §70/71 Observability."""

    def setup_method(self):
        self.m = MetricsService()

    def test_initial_state(self):
        assert self.m.request_count == 0
        assert self.m.verification_success_count == 0

    def test_record_request_increments_count(self):
        self.m.record_request("HIGH", 120.0, success=True)
        assert self.m.request_count == 1
        assert self.m.verification_success_count == 1

    def test_record_request_failure(self):
        self.m.record_request("UNKNOWN", 500.0, success=False)
        assert self.m.verification_failure_count == 1

    def test_risk_level_distribution_tracked(self):
        self.m.record_request("HIGH", 100.0, True)
        self.m.record_request("LOW", 80.0, True)
        self.m.record_request("HIGH", 110.0, True)
        dist = self.m.risk_level_distribution
        assert dist["HIGH"] == 2
        assert dist["LOW"] == 1

    def test_adapter_call_tracking(self):
        self.m.record_adapter_call("companies_house", 200.0, success=True)
        self.m.record_adapter_call("companies_house", 400.0, success=False)
        summary = self.m.get_summary()
        ch = summary["adapters"]["companies_house"]
        assert ch["call_count"] == 2
        assert ch["error_count"] == 1
        assert ch["error_rate"] == 0.5

    def test_feedback_distribution(self):
        self.m.record_feedback("CONFIRMED_SCAM")
        self.m.record_feedback("FALSE_POSITIVE")
        self.m.record_feedback("CONFIRMED_SCAM")
        dist = self.m.feedback_distribution
        assert dist["CONFIRMED_SCAM"] == 2
        assert dist["FALSE_POSITIVE"] == 1

    def test_explanation_open_tracking(self):
        self.m.record_explanation_opened()
        self.m.record_explanation_opened()
        assert self.m.explanation_open_count == 2

    def test_latency_percentiles_in_summary(self):
        for ms in [100, 200, 300, 400, 500]:
            self.m.record_request("MEDIUM", float(ms), True)
        summary = self.m.get_summary()
        assert summary["p50_latency_ms"] > 0
        assert summary["p95_latency_ms"] >= summary["p50_latency_ms"]

    def test_alert_fired_on_high_error_rate(self):
        """§71: Alert should fire when adapter error rate exceeds threshold."""
        for _ in range(8):
            self.m.record_adapter_call("bad_adapter", 100.0, success=False)
        alerts = self.m.get_recent_alerts()
        assert len(alerts) > 0
        assert any("bad_adapter" in a["component"] for a in alerts)


class TestVersionManifest:
    """Tests for §73 Model/Rule Versioning."""

    def test_version_manifest_fields(self):
        v = VersionManifest()
        assert v.cect_version == CECT_VERSION
        assert v.risk_config_version is not None
        assert v.extraction_version is not None

    def test_to_dict_contains_all_fields(self):
        d = VersionManifest().to_dict()
        required = [
            "cect_version", "risk_config_version", "extraction_version",
            "adapter_version", "source_version", "threat_intel_version", "trajectory_version",
        ]
        for field in required:
            assert field in d, f"Missing field: {field}"


class TestKillSwitches:
    """Tests for §75 Kill Switches."""

    def test_all_features_enabled_by_default(self):
        switches = list_kill_switches()
        for key, state in switches.items():
            assert state is True, f"Feature '{key}' should be enabled by default"

    def test_disable_feature(self):
        success = disable_feature("adapter.us_sec")
        assert success is True
        assert is_feature_enabled("adapter.us_sec") is False
        # Restore for other tests
        enable_feature("adapter.us_sec")

    def test_enable_feature_restores(self):
        disable_feature("feature.trust_graph")
        assert is_feature_enabled("feature.trust_graph") is False
        enable_feature("feature.trust_graph")
        assert is_feature_enabled("feature.trust_graph") is True

    def test_disable_unknown_feature_returns_false(self):
        result = disable_feature("does.not.exist")
        assert result is False

    def test_enable_unknown_feature_returns_false(self):
        result = enable_feature("does.not.exist")
        assert result is False

    def test_is_feature_enabled_defaults_to_true_for_unknown(self):
        """Unknown feature keys should default to enabled (fail-safe)."""
        result = is_feature_enabled("completely.unknown.key")
        assert result is True

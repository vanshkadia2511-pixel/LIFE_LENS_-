"""
LifeLens Ω — Phase L Test Suite: Pilot Readiness
Validates:
1. Campus placement-cell pilot kit documentation (explainer, consent form, feedback survey, ethics checklist, metrics plan).
2. Migration corridor advisories analysis table (terms of use, machine readability, no scraping before terms checked).
3. Privacy-preserving pilot analytics (aggregate counts only, salted-HMAC tokens, zero content/PII retention, consent gating).
"""
from __future__ import annotations
import os
from pathlib import Path
import pytest

from apps.api.app.services.analytics.pilot_analytics import (
    PilotAnalyticsService,
    PilotAggregateSummary,
    PrivacyViolationError,
    ConsentRequiredError,
)


class TestPhaseLPilotReadiness:
    """Verifies Phase L pilot readiness and governance assets."""

    def test_campus_placement_pilot_kit_documentation(self):
        """Verifies presence of the campus placement-cell pilot kit with all mandatory sections."""
        doc_path = Path("docs/CAMPUS_PLACEMENT_PILOT_KIT.md")
        assert doc_path.exists(), "CAMPUS_PLACEMENT_PILOT_KIT.md must exist"
        content = doc_path.read_text(encoding="utf-8")

        # Check required sections
        assert "One-Page Explainer" in content
        assert "Participant Consent Form Template" in content
        assert "Feedback Survey" in content
        assert "Ethics & Safety Checklist" in content
        assert "Metrics Plan" in content

        # Check principles P1-P6 and Rule A compliance
        assert "P1" in content
        assert "Rule A" in content or "Never labels a human" in content
        assert "Zero Biometric Collection" in content or "ZERO BIOMETRIC" in content

    def test_migration_corridor_advisories_table(self):
        """Verifies curated 5 migration corridors table with terms of use and machine readability."""
        doc_path = Path("docs/MIGRATION_CORRIDOR_ADVISORIES.md")
        assert doc_path.exists(), "MIGRATION_CORRIDOR_ADVISORIES.md must exist"
        content = doc_path.read_text(encoding="utf-8")

        # Must analyze between 3 and 5 migration corridors
        corridors = ["CORR-01", "CORR-02", "CORR-03", "CORR-04", "CORR-05"]
        for cid in corridors:
            assert cid in content, f"Missing corridor entry {cid} in table"

        # Check explicit columns and constraints
        assert "Terms of Use" in content
        assert "Machine Readability" in content
        assert "Scraping Status" in content
        assert "PROHIBITED" in content
        assert "confirm current" in content

    def test_pilot_analytics_consent_gate_enforcement(self):
        """Verifies analytics service rejects events when explicit consent is False."""
        service = PilotAnalyticsService(salt="test_salt_123")

        with pytest.raises(ConsentRequiredError, match="Explicit participant consent is mandatory"):
            service.record_event(
                raw_session_id="session_abc_999",
                event_type="CHECK_COMPLETED",
                metadata={"risk_category": "LOW"},
                has_explicit_consent=False,
            )

    def test_pilot_analytics_salted_hmac_session_tokens(self):
        """Verifies session tokens are irreversibly hashed and salt-isolated."""
        service1 = PilotAnalyticsService(salt="salt_alpha")
        service2 = PilotAnalyticsService(salt="salt_beta")

        token1 = service1.hash_session_id("student_device_101")
        token2 = service2.hash_session_id("student_device_101")

        # Same input with different salts must yield completely different hashes
        assert token1 != token2
        assert len(token1) == 64  # SHA-256 hex string
        assert "student_device" not in token1  # Irreversible

    def test_pilot_analytics_pii_and_content_rejection(self):
        """Verifies analytics rejects any attempt to pass message content, emails, or phone numbers."""
        service = PilotAnalyticsService()

        # 1. Prohibited message text key
        with pytest.raises(PrivacyViolationError, match="Prohibited PII key 'message_text'"):
            service.record_event(
                raw_session_id="sess_1",
                event_type="CHECK_COMPLETED",
                metadata={"message_text": "You have won a free iPhone!"},
                has_explicit_consent=True,
            )

        # 2. Embedded email pattern in value
        with pytest.raises(PrivacyViolationError, match="Prohibited email address pattern"):
            service.record_event(
                raw_session_id="sess_2",
                event_type="CHECK_COMPLETED",
                metadata={"target": "contact me at recruiter@fake-company.com"},
                has_explicit_consent=True,
            )

        # 3. Embedded phone pattern
        with pytest.raises(PrivacyViolationError, match="Prohibited telephone number pattern"):
            service.record_event(
                raw_session_id="sess_3",
                event_type="CHECK_COMPLETED",
                metadata={"phone_ref": "+1-800-555-0199"},
                has_explicit_consent=True,
            )

        # 4. Binary/media bytes
        with pytest.raises(PrivacyViolationError, match="Prohibited binary stream/media bytes"):
            service.record_event(
                raw_session_id="sess_4",
                event_type="CHECK_COMPLETED",
                metadata={"snapshot": b"\x89PNG\r\n\x1a\n..."},
                has_explicit_consent=True,
            )

    def test_pilot_analytics_aggregate_counts_only(self):
        """Verifies telemetry produces aggregate summary counts without individual details."""
        service = PilotAnalyticsService(salt="pilot_daily_salt")

        # Record consented safe check
        service.record_event(
            raw_session_id="student_1",
            event_type="CHECK_COMPLETED",
            metadata={"risk_category": "LOW", "signals_count": 1},
            has_explicit_consent=True,
        )

        # Record consented high-risk check
        service.record_event(
            raw_session_id="student_2",
            event_type="CHECK_COMPLETED",
            metadata={"risk_category": "HIGH", "signals_count": 4},
            has_explicit_consent=True,
        )

        # Record checklist actions
        service.record_event(
            raw_session_id="student_2",
            event_type="CHECKLIST_ACTION_COMPLETED",
            metadata={"action_type": "out_of_band_call"},
            has_explicit_consent=True,
        )
        service.record_event(
            raw_session_id="student_2",
            event_type="CHECKLIST_ACTION_COMPLETED",
            metadata={"action_type": "government_registry_lookup"},
            has_explicit_consent=True,
        )

        # Record dispute
        service.record_event(
            raw_session_id="recruiter_1",
            event_type="DISPUTE_SUBMITTED",
            metadata={"dispute_type": "domain_ownership"},
            has_explicit_consent=True,
        )

        summary = service.get_aggregate_summary()
        assert isinstance(summary, PilotAggregateSummary)
        assert summary.total_checks == 2
        assert summary.high_risk_flagged_count == 1
        assert summary.checklist_actions_completed == 2
        assert summary.verification_paths_taken["out_of_band_call"] == 1
        assert summary.verification_paths_taken["government_registry_lookup"] == 1
        assert summary.disputes_submitted == 1
        assert summary.unique_active_sessions_count == 3
        assert summary.provenance == "MEASURED"
        assert summary.privacy_mode == "SALTED_HMAC_AGGREGATE_ONLY"

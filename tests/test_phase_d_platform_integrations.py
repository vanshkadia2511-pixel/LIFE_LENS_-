"""
LifeLens Ω — Phase D: Platform Integrations & Rule C Test Suite
Tests:
- MeetingMediaProvider interface and SIMULATED provider tagging
- Rule C Evidence Independence (participants with shared origin count as ONE source)
- Rule C constraint: verified-trust outcome requires at least one independently verified participant
- Signals:
  * SIG_PARTICIPANTS_SHARED_ORIGIN
  * SIG_NO_INDEPENDENT_VERIFIED_PARTICIPANT
  * SIG_GUEST_JOIN_BURST
- Zoom RTMS adapter credential gating (disabled without approved credentials, risk_boost=0.0)
- Google Meet, Microsoft Teams, Cisco Webex stubs & Vendor Bot feature flag
- E2EE call coverage documented as Phase C Desktop Guard only
"""
import pytest
from datetime import datetime, timezone, timedelta

from apps.api.app.integrations.meeting_providers import (
    MeetingParticipant,
    ParticipantJoinEvent,
    SimulatedMeetingMediaProvider,
    ZoomRTMSAdapter,
    GoogleMeetProviderStub,
    MicrosoftTeamsProviderStub,
    CiscoWebexProviderStub,
    VendorMeetingBotAdapter,
    ParticipantIndependenceAnalyzer,
    MeetingMetadataSignals,
)
from apps.api.app.models.evidence import SourceStatus


def test_meeting_media_provider_interface_and_simulated_tagging():
    """Verify SIMULATED provider is explicitly tagged and carries zero evidence weight (§P4)."""
    provider = SimulatedMeetingMediaProvider()
    assert provider.is_simulated is True
    assert provider.provider_name == "SIMULATED_MEETING_PROVIDER"
    assert provider.source_tag == "SIMULATED"

    participants = provider.get_participants("meeting_test_01")
    assert len(participants) > 0
    for p in participants:
        assert isinstance(p, MeetingParticipant)


def test_rule_c_participants_shared_origin_counts_as_one_source():
    """
    Rule C: Participants who share the same join origin (same invite link, same host,
    same account-creation window) and vouch for each other count as ONE evidence source.
    """
    now = datetime.now(timezone.utc)
    # 4 participants, same join origin, vouching for each other
    shared_origin_id = "invite_shared_cluster_99"
    participants = [
        MeetingParticipant(
            participant_id=f"part_0{i}",
            display_name=f"Voucher {i}",
            is_authenticated=False,
            join_origin_id=shared_origin_id,
            account_created_window="SAME_DAY",
            joined_at=now + timedelta(seconds=i * 2),
            vouched_by_participant_ids=["part_01", "part_02", "part_03", "part_04"],
            independent_verified_callback=False,
        )
        for i in range(1, 5)
    ]

    analyzer = ParticipantIndependenceAnalyzer()
    res = analyzer.analyze_participant_independence(participants)

    # 4 participants count as only 1 independent evidence cluster
    assert res.effective_independent_source_count == 1
    assert res.raw_participant_count == 4
    assert res.has_shared_origin_cluster is True


def test_rule_c_verified_trust_blocked_without_independent_verified_participant():
    """
    Rule C: A 'verified-trust' outcome needs at least one independently verified participant
    (org-authenticated, or confirmed through an out-of-band callback).
    """
    now = datetime.now(timezone.utc)
    # All participants unverified
    unverified_participants = [
        MeetingParticipant(
            participant_id="part_u1",
            display_name="Guest User 1",
            is_authenticated=False,
            join_origin_id="link_a",
            joined_at=now,
            independent_verified_callback=False,
        ),
        MeetingParticipant(
            participant_id="part_u2",
            display_name="Guest User 2",
            is_authenticated=False,
            join_origin_id="link_b",
            joined_at=now,
            independent_verified_callback=False,
        ),
    ]

    analyzer = ParticipantIndependenceAnalyzer()
    res = analyzer.analyze_participant_independence(unverified_participants)
    assert res.can_achieve_verified_trust is False
    assert "At least one independently verified participant is required for verified-trust (§Rule C)" in res.verdict_blockers

    # Now add one org-authenticated participant
    verified_participants = unverified_participants + [
        MeetingParticipant(
            participant_id="part_v1",
            display_name="Enterprise Recruiter",
            is_authenticated=True,
            org_domain="canonical-corp.com",
            join_origin_id="sso_origin",
            joined_at=now,
            independent_verified_callback=True,
        )
    ]
    res_verified = analyzer.analyze_participant_independence(verified_participants)
    assert res_verified.can_achieve_verified_trust is True
    assert res_verified.has_independently_verified_participant is True


def test_participant_metadata_signals_detection():
    """
    Verify detection of:
    - SIG_PARTICIPANTS_SHARED_ORIGIN
    - SIG_NO_INDEPENDENT_VERIFIED_PARTICIPANT
    - SIG_GUEST_JOIN_BURST
    """
    now = datetime.now(timezone.utc)
    # 3 guest participants joining within 5 seconds on same origin
    burst_participants = [
        MeetingParticipant(
            participant_id=f"guest_{i}",
            display_name=f"Guest {i}",
            is_authenticated=False,
            join_origin_id="quick_link_123",
            account_created_window="SAME_HOUR",
            joined_at=now + timedelta(seconds=i * 2),
            independent_verified_callback=False,
        )
        for i in range(1, 4)
    ]

    detector = MeetingMetadataSignals()
    signals = detector.detect_signals(burst_participants)
    sig_names = [s.signal_name for s in signals]

    assert "SIG_PARTICIPANTS_SHARED_ORIGIN" in sig_names
    assert "SIG_NO_INDEPENDENT_VERIFIED_PARTICIPANT" in sig_names
    assert "SIG_GUEST_JOIN_BURST" in sig_names


def test_zoom_rtms_adapter_disabled_without_approved_credentials():
    """Verify Zoom RTMS adapter is strictly disabled without approved credentials (§P6)."""
    adapter = ZoomRTMSAdapter(credentials=None)
    assert adapter.is_enabled is False
    assert adapter.status == SourceStatus.UNAVAILABLE
    assert adapter.risk_boost == 0.0

    # Ensure checklist is provided for org/marketplace onboarding
    checklist = adapter.get_setup_checklist()
    assert len(checklist) >= 4
    assert any("ZOOM_RTMS_CLIENT_ID" in item for item in checklist)
    assert any("Server-to-Server OAuth" in item for item in checklist)


def test_meet_teams_webex_stubs_and_vendor_bot_feature_flag():
    """Verify vendor stubs are inactive and vendor bot abstraction is gated behind disabled flag."""
    meet = GoogleMeetProviderStub()
    teams = MicrosoftTeamsProviderStub()
    webex = CiscoWebexProviderStub()

    assert meet.is_enabled is False
    assert teams.is_enabled is False
    assert webex.is_enabled is False

    # Vendor bot adapter
    bot_adapter = VendorMeetingBotAdapter(feature_enabled=False)
    assert bot_adapter.is_enabled is False
    notice = bot_adapter.get_privacy_advisory()
    assert "Third-Party Data Handling Notice" in notice
    assert "Explicit user consent is mandatory" in notice


def test_e2ee_messaging_calls_documented_as_desktop_guard_only():
    """Verify WhatsApp, Telegram, Signal are explicitly documented to route through Phase C Desktop Guard."""
    provider = SimulatedMeetingMediaProvider()
    e2ee_doc = provider.get_e2ee_coverage_policy()
    assert "WhatsApp" in e2ee_doc
    assert "Telegram" in e2ee_doc
    assert "Signal" in e2ee_doc
    assert "Phase C Desktop Call Guard" in e2ee_doc
    assert "No scraping or encryption bypass" in e2ee_doc


def test_cect_engine_integrates_rule_c_participants():
    """Verify EvidenceIndependenceEngine integrates Rule C when participants are provided."""
    from apps.api.app.cect.independence import EvidenceIndependenceEngine
    from apps.api.app.models.evidence import Evidence, SourceStatus

    now = datetime.now(timezone.utc)
    engine = EvidenceIndependenceEngine()

    dummy_evidence = [
        Evidence(
            evidence_id="ev_01",
            source_type="REGISTRY",
            source_name="Test Registry",
            captured_at=now,
            source_status=SourceStatus.AVAILABLE,
            observed_value="active",
        )
    ]

    # Shared origin unverified participants
    participants = [
        MeetingParticipant(
            participant_id="p1",
            display_name="User 1",
            is_authenticated=False,
            join_origin_id="room_xyz",
            joined_at=now,
            vouched_by_participant_ids=["p2"],
        ),
        MeetingParticipant(
            participant_id="p2",
            display_name="User 2",
            is_authenticated=False,
            join_origin_id="room_xyz",
            joined_at=now,
            vouched_by_participant_ids=["p1"],
        ),
    ]

    res = engine.analyze(dummy_evidence, participants=participants)
    assert res.rule_c_applied is True
    assert res.effective_participant_sources == 1
    assert any("Rule C applied" in f for f in res.findings)
    assert any("Verified-trust outcome blocked" in f for f in res.findings)


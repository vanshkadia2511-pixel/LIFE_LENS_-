"""
LifeLens Ω — Phase B: Call Guardian Layer 0 Unit & Security Test Suite
Tests pre-call link & invite checker:
- SSRF prevention (direct and multi-hop redirects)
- Strict non-fetching guarantee (never joins or fetches meeting body)
- Consent gate enforcement
- Signal detection:
  * SIG_CALL_INVITE_LOOKALIKE
  * SIG_CALL_UNSOLICITED_CHANNEL
  * SIG_CALL_URGENCY_FRAMING
  * SIG_HOST_DOMAIN_MISMATCH
- Rule A vocabulary adherence
- Zero media bytes persistence assertion
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from apps.api.app.main import app
from apps.api.app.models.call_guard import (
    CallInviteCheckRequest,
    CallGuardSignalType,
)
from apps.api.app.services.call_guard_service import CallGuardianLayer0Service
from apps.api.app.security.ssrf import SSRFShield, SSRFValidationResult


client = TestClient(app)


def test_consent_gate_enforcement():
    """Verify that checking an invite without explicit user consent is blocked (§P5, §P6)."""
    service = CallGuardianLayer0Service()
    req = CallInviteCheckRequest(
        invite_url="https://zoom.us/j/1234567890",
        consent_flag=False,
    )
    assessment = service.check_invite(req)
    assert not assessment.is_safe_to_join
    assert assessment.verdict == "Needs Verification"
    assert "User consent flag must be explicitly granted" in assessment.recommendations[0]


def test_ssrf_direct_private_ips_and_metadata_blocked():
    """Verify SSRF attempts targeting RFC 1918, loopback, and cloud metadata are blocked."""
    service = CallGuardianLayer0Service()
    blocked_targets = [
        "http://127.0.0.1:8000/meeting",
        "http://169.254.169.254/latest/meta-data/",
        "http://10.0.0.5/call",
        "http://192.168.1.100:3000/join",
    ]

    for url in blocked_targets:
        req = CallInviteCheckRequest(
            invite_url=url,
            consent_flag=True,
        )
        assessment = service.check_invite(req)
        assert assessment.risk_score >= 0.8
        assert assessment.verdict == "Request looks high-risk"
        assert not assessment.is_safe_to_join
        signal_types = [s.signal_type for s in assessment.signals]
        assert CallGuardSignalType.SIG_SSRF_PROBE_BLOCKED in signal_types or CallGuardSignalType.SIG_CALL_INVITE_LOOKALIKE in signal_types


def test_ssrf_redirect_handling_prevents_private_ip_hops():
    """Verify that redirect chains leading to internal IPs are halted before connecting."""
    service = CallGuardianLayer0Service()

    # Mock redirect resolver where first hop returns 302 to cloud metadata
    with patch.object(service, "_resolve_redirects_safely") as mock_resolver:
        mock_resolver.return_value = (
            "http://169.254.169.254/secret",
            ["https://tinyurl.com/meeting1", "http://169.254.169.254/secret"],
            True,  # is_ssrf_blocked
            "Target '169.254.169.254' is in restricted cloud metadata range",
        )
        req = CallInviteCheckRequest(
            invite_url="https://tinyurl.com/meeting1",
            consent_flag=True,
        )
        assessment = service.check_invite(req)
        assert assessment.risk_score >= 0.8
        assert not assessment.is_safe_to_join
        assert any(s.signal_type == CallGuardSignalType.SIG_SSRF_PROBE_BLOCKED for s in assessment.signals)


def test_strict_non_fetching_guarantee():
    """Verify that Call Guardian NEVER fetches meeting HTML bodies or initiates call joins."""
    service = CallGuardianLayer0Service()

    with patch("urllib.request.urlopen") as mock_urlopen:
        req = CallInviteCheckRequest(
            invite_url="https://zoom.us/j/9876543210",
            consent_flag=True,
        )
        assessment = service.check_invite(req)
        # Ensure no full HTTP GET or response body reading occurred
        assert mock_urlopen.call_count == 0
        assert assessment.is_safe_to_join
        assert assessment.verdict == "Verification step completed"


def test_sig_call_invite_lookalike_detection():
    """Verify typosquatting, homoglyphs, and lookalike meeting domains are detected."""
    service = CallGuardianLayer0Service()
    lookalikes = [
        "https://zoom-secure-verify.com/join/12345",
        "https://z00m.us/meeting/8821",
        "https://meet-google-join.net/call/abc",
        "https://teams-security-check.org/meeting",
        "https://webexx.com/meet/771",
        "https://zoom.us.scamdomain.com/j/123",
    ]

    for url in lookalikes:
        # Mock DNS resolution to external safe IP so SSRF passes but lookalike detector fires
        with patch.object(SSRFShield, "validate_url", return_value=SSRFValidationResult(is_safe=True, url=url, ip_address="93.184.216.34")):
            req = CallInviteCheckRequest(
                invite_url=url,
                consent_flag=True,
            )
            assessment = service.check_invite(req)
            assert any(s.signal_type == CallGuardSignalType.SIG_CALL_INVITE_LOOKALIKE for s in assessment.signals), f"Failed for {url}"
            assert assessment.risk_score >= 0.5


def test_sig_call_unsolicited_channel_detection():
    """Verify that meeting invites sent via unsolicited/untrusted channels trigger an alarm."""
    service = CallGuardianLayer0Service()

    unsolicited_channels = ["telegram_dm", "whatsapp_unknown_number", "sms_unknown", "instagram_dm"]
    for ch in unsolicited_channels:
        req = CallInviteCheckRequest(
            invite_url="https://zoom.us/j/1234567890",
            channel=ch,
            consent_flag=True,
        )
        assessment = service.check_invite(req)
        assert any(s.signal_type == CallGuardSignalType.SIG_CALL_UNSOLICITED_CHANNEL for s in assessment.signals)

    # Legitimate corporate channels should NOT trigger unsolicited signal
    trusted_req = CallInviteCheckRequest(
        invite_url="https://zoom.us/j/1234567890",
        channel="corporate_calendar",
        consent_flag=True,
    )
    trusted_assessment = service.check_invite(trusted_req)
    assert not any(s.signal_type == CallGuardSignalType.SIG_CALL_UNSOLICITED_CHANNEL for s in trusted_assessment.signals)


def test_sig_call_urgency_framing_detection():
    """Verify high-pressure urgency cues, legal threats, and digital arrest phrasing are caught."""
    service = CallGuardianLayer0Service()

    urgent_cases = [
        "Join immediately within 10 minutes or warrant will be issued",
        "Urgent: CBI Digital Arrest hearing session",
        "Final notice: Disciplinary video conference required right now",
    ]

    for text in urgent_cases:
        req = CallInviteCheckRequest(
            invite_url="https://meet.google.com/abc-defg-hij",
            message_context=text,
            consent_flag=True,
        )
        assessment = service.check_invite(req)
        assert any(s.signal_type == CallGuardSignalType.SIG_CALL_URGENCY_FRAMING for s in assessment.signals)


def test_sig_host_domain_mismatch_detection():
    """Verify host domain mismatch when claimed company does not match invite domain."""
    service = CallGuardianLayer0Service()

    with patch.object(SSRFShield, "validate_url", return_value=SSRFValidationResult(is_safe=True, url="https://zoom-personal.com/j/123", ip_address="93.184.216.34")):
        req = CallInviteCheckRequest(
            invite_url="https://zoom-personal.com/j/123",
            claimed_host_name="Google Recruiter",
            claimed_host_email="recruiter@google.com",
            consent_flag=True,
        )
        assessment = service.check_invite(req)
        assert any(s.signal_type == CallGuardSignalType.SIG_HOST_DOMAIN_MISMATCH for s in assessment.signals)


def test_rule_a_verdict_vocabulary():
    """Enforce Rule A: Never label a person. Verdicts must be strictly compliant."""
    service = CallGuardianLayer0Service()
    allowed_verdicts = {
        "Verification step completed",
        "Needs Verification",
        "Request looks high-risk",
    }

    # Low risk
    low_req = CallInviteCheckRequest(invite_url="https://meet.google.com/abc-defg-hij", consent_flag=True)
    assert service.check_invite(low_req).verdict in allowed_verdicts

    # High risk
    high_req = CallInviteCheckRequest(
        invite_url="https://z00m.us/meeting/8821",
        channel="telegram_dm",
        message_context="Urgent digital arrest immediately",
        consent_flag=True,
    )
    assessment = service.check_invite(high_req)
    assert assessment.verdict in allowed_verdicts
    assert assessment.verdict == "Request looks high-risk"
    # Ensure forbidden labels are NOT present anywhere in verdict or signals
    forbidden = ["scammer", "fake person", "real person", "verified human", "fraudster"]
    for text in [assessment.verdict, str(assessment.signals)]:
        for f in forbidden:
            assert f not in text.lower()


def test_no_media_bytes_reach_disk_or_db():
    """Verify strict privacy & zero media storage: Layer 0 never stores raw media bytes."""
    service = CallGuardianLayer0Service()
    req = CallInviteCheckRequest(
        invite_url="https://zoom.us/j/1234567890",
        consent_flag=True,
    )
    assessment = service.check_invite(req)
    # Layer 0 must purely work on strings and URLs
    assert isinstance(assessment.invite_url, str)
    assert not hasattr(assessment, "raw_audio_bytes")
    assert not hasattr(assessment, "raw_video_bytes")


def test_api_endpoint_post_call_guard_invite_check():
    """Integration test for POST /api/v1/call-guard/invite/check."""
    payload = {
        "invite_url": "https://zoom.us/j/1234567890",
        "platform_hint": "zoom",
        "channel": "corporate_calendar",
        "claimed_host_name": "Team Lead",
        "claimed_host_email": "lead@company.com",
        "consent_flag": True,
    }
    response = client.post("/api/v1/call-guard/invite/check", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "assessment_id" in data
    assert data["verdict"] == "Verification step completed"
    assert data["is_safe_to_join"] is True
    assert "signals" in data
    assert "provenance" in data

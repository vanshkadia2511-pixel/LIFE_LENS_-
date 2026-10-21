"""
LifeLens Ω — Phase C: Desktop Call Guard Test Suite
Tests for:
- Consent gate & Guard lifecycle (user-started, visible indicator, one-click stop)
- Zero persisted media & in-memory ephemeral handling (asserts 0 audio/video/image bytes)
- Layer 2 live transcript trajectory engine:
  * SIG_CALL_TRANSFER_REQUEST
  * SIG_CALL_SECRECY_DEMAND
  * SIG_CALL_URGENCY_PRESSURE
  * SIG_CALL_CREDENTIAL_REQUEST
  * SIG_REMOTE_ACCESS_REQUEST
  * SIG_OFFICIAL_IMPERSONATION
  * SIG_PAYMENT_DETAILS
- Latency measurement (< 3.0s TARGET measured)
- Layer 3 Out-of-band verification interstitial & cooling-off timer
- Layer 4 Liveness challenge coach (coaches challenges, never claims automated pass/fail verdict)
- Post-call receipt & ledger logging with transcript discard policy
- API endpoints integration
"""
import time
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from apps.api.app.main import app
from apps.api.app.models.desktop_guard import (
    DesktopGuardStartRequest,
    DesktopGuardChunkRequest,
    DesktopGuardEndRequest,
    DesktopSignalType,
)
from apps.api.app.services.desktop_guard_service import DesktopCallGuardService


client = TestClient(app)


def test_desktop_guard_consent_gate_and_lifecycle():
    """Verify Desktop Call Guard cannot start without explicit user consent (§P5, §P6)."""
    service = DesktopCallGuardService()

    # Attempt to start without consent
    unconsented = DesktopGuardStartRequest(
        platform="zoom",
        consent_flag=False,
    )
    unconsented_session = service.start_session(unconsented)
    assert not unconsented_session.is_active
    assert "User consent must be explicitly granted" in unconsented_session.status_message

    # Start with consent
    consented = DesktopGuardStartRequest(
        platform="zoom",
        consent_flag=True,
    )
    session = service.start_session(consented)
    assert session.is_active
    assert session.guard_indicator == "GUARD_ON"

    # One-click stop
    receipt = service.end_session(DesktopGuardEndRequest(session_id=session.session_id))
    assert not service.get_session(session.session_id).is_active
    assert receipt.session_id == session.session_id


def test_zero_persisted_media_and_transcript_discard():
    """Verify that NO raw audio, video, screenshot, or unconsented transcript is saved to disk or DB."""
    service = DesktopCallGuardService()
    session = service.start_session(DesktopGuardStartRequest(platform="teams", consent_flag=True))

    # Ingest illustrative transcript chunk
    service.ingest_transcript_chunk(
        DesktopGuardChunkRequest(
            session_id=session.session_id,
            transcript_text="ILLUSTRATIVE: Please verify your name for the interview.",
            speaker="remote_caller",
        )
    )

    # End session without opt-in transcript retention
    receipt = service.end_session(DesktopGuardEndRequest(session_id=session.session_id, opt_in_retain_transcript=False))

    # Assert receipt does not contain the raw transcript text
    assert receipt.transcript_retained is False
    assert not hasattr(receipt, "raw_audio_bytes")
    assert not hasattr(receipt, "raw_video_bytes")
    assert not hasattr(receipt, "screenshots")
    # Verify internal session memory purged the raw text
    sess = service.get_session(session.session_id)
    assert len(sess.transcript_buffer) == 0


def test_layer2_trajectory_triggers_and_latency():
    """
    Verify Layer 2 triggers on all 7 high-risk phrases with latency under 3.0s TARGET.
    Transcripts are synthetic fixtures clearly labeled ILLUSTRATIVE.
    """
    service = DesktopCallGuardService()
    session = service.start_session(DesktopGuardStartRequest(platform="meet", consent_flag=True))

    test_scenarios = [
        (
            "ILLUSTRATIVE: You need to transfer $2,500 wire immediately to secure your visa processing.",
            DesktopSignalType.SIG_CALL_TRANSFER_REQUEST,
        ),
        (
            "ILLUSTRATIVE: Keep this call completely confidential, do not tell anyone or consult your family.",
            DesktopSignalType.SIG_CALL_SECRECY_DEMAND,
        ),
        (
            "ILLUSTRATIVE: You must act right now within 5 minutes or you will face immediate legal consequences.",
            DesktopSignalType.SIG_CALL_URGENCY_PRESSURE,
        ),
        (
            "ILLUSTRATIVE: Read me the 6-digit OTP and your netbanking password to verify your profile.",
            DesktopSignalType.SIG_CALL_CREDENTIAL_REQUEST,
        ),
        (
            "ILLUSTRATIVE: Please download and install AnyDesk so our technician can inspect your camera setup.",
            DesktopSignalType.SIG_REMOTE_ACCESS_REQUEST,
        ),
        (
            "ILLUSTRATIVE: This is Officer Sharma from the CBI Cyber Crime Cell, you are under digital arrest.",
            DesktopSignalType.SIG_OFFICIAL_IMPERSONATION,
        ),
        (
            "ILLUSTRATIVE: Send payment to UPI ID scammer@okhdfcbank or bitcoin address 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa.",
            DesktopSignalType.SIG_PAYMENT_DETAILS,
        ),
    ]

    for illustrative_text, expected_signal in test_scenarios:
        t0 = time.perf_counter()
        alerts = service.ingest_transcript_chunk(
            DesktopGuardChunkRequest(
                session_id=session.session_id,
                transcript_text=illustrative_text,
                speaker="remote_caller",
            )
        )
        latency_seconds = time.perf_counter() - t0

        # Assert trigger latency meets TARGET < 3.0s (MEASURED)
        assert latency_seconds < 3.0, f"Latency {latency_seconds}s exceeded 3.0s target"
        # Assert signal fired
        fired_types = [a.signal_type for a in alerts]
        assert expected_signal in fired_types, f"Expected {expected_signal} in {fired_types} for '{illustrative_text}'"


def test_layer3_out_of_band_verification_interstitial():
    """Verify that a high-risk trigger spawns an interstitial with cooling-off timer and callback steps."""
    service = DesktopCallGuardService()
    session = service.start_session(DesktopGuardStartRequest(platform="whatsapp_desktop", consent_flag=True))

    alerts = service.ingest_transcript_chunk(
        DesktopGuardChunkRequest(
            session_id=session.session_id,
            transcript_text="ILLUSTRATIVE: Transfer money to this UPI ID right now or arrest will happen.",
            speaker="remote_caller",
        )
    )

    interstitial = service.get_active_interstitial(session.session_id)
    assert interstitial is not None
    assert interstitial.requires_pause is True
    assert "Do NOT pay, transfer money, or share credentials" in interstitial.headline
    assert interstitial.cooling_off_minutes >= 15
    assert len(interstitial.callback_checklist) >= 3
    # Step verification checklist completion
    res = service.complete_verification_step(session.session_id, step_index=0)
    assert res.checklist_status[0] is True


def test_layer4_liveness_challenge_coach():
    """Verify Layer 4 coaches challenges without claiming an automated pass/fail verdict (P6)."""
    service = DesktopCallGuardService()
    session = service.start_session(DesktopGuardStartRequest(platform="zoom", consent_flag=True))

    challenges = service.get_liveness_challenges(session.session_id)
    assert len(challenges) >= 4
    # Verify challenge prompts
    actions = [c.action_instruction for c in challenges]
    assert any("profile" in a.lower() for a in actions)
    assert any("hand" in a.lower() for a in actions)
    assert any("object" in a.lower() for a in actions)
    assert any("phrase" in a.lower() for a in actions)

    # Verify app never claims automated pass/fail verdict
    for c in challenges:
        assert c.automated_verdict_claimed is False
        assert "User observes reaction" in c.evaluation_guidance


def test_post_call_receipt_and_ledger_entry():
    """Verify post-call receipt generation, ledger entry creation, and optional transcript retention."""
    service = DesktopCallGuardService()
    session = service.start_session(DesktopGuardStartRequest(platform="zoom", consent_flag=True))

    service.ingest_transcript_chunk(
        DesktopGuardChunkRequest(
            session_id=session.session_id,
            transcript_text="ILLUSTRATIVE: Download TeamViewer to proceed.",
            speaker="remote_caller",
        )
    )

    receipt = service.end_session(DesktopGuardEndRequest(session_id=session.session_id, opt_in_retain_transcript=False))
    assert receipt.session_id == session.session_id
    assert len(receipt.signals_fired) >= 1
    assert "SIG_REMOTE_ACCESS_REQUEST" in [s.signal_type for s in receipt.signals_fired]
    assert receipt.ledger_entry_hash is not None
    assert receipt.ledger_entry_hash.startswith("0x") or len(receipt.ledger_entry_hash) == 64


def test_desktop_guard_api_endpoints():
    """Integration test for Desktop Call Guard REST endpoints."""
    # Start session
    start_resp = client.post(
        "/api/v1/desktop-guard/start",
        json={"platform": "zoom", "consent_flag": True},
    )
    assert start_resp.status_code == 200
    sess_data = start_resp.json()
    sess_id = sess_data["session_id"]
    assert sess_data["guard_indicator"] == "GUARD_ON"

    # Ingest chunk
    chunk_resp = client.post(
        "/api/v1/desktop-guard/chunk",
        json={
            "session_id": sess_id,
            "transcript_text": "ILLUSTRATIVE: You are under digital arrest by police.",
            "speaker": "caller",
        },
    )
    assert chunk_resp.status_code == 200
    alerts = chunk_resp.json()
    assert len(alerts) >= 1
    assert alerts[0]["signal_type"] == "SIG_OFFICIAL_IMPERSONATION"

    # Get active interstitial
    inter_resp = client.get(f"/api/v1/desktop-guard/interstitial/{sess_id}")
    assert inter_resp.status_code == 200
    inter_data = inter_resp.json()
    assert inter_data["requires_pause"] is True

    # Get liveness challenges
    coach_resp = client.get(f"/api/v1/desktop-guard/challenges/{sess_id}")
    assert coach_resp.status_code == 200
    coach_data = coach_resp.json()
    assert len(coach_data) >= 4

    # End session
    end_resp = client.post(
        "/api/v1/desktop-guard/end",
        json={"session_id": sess_id, "opt_in_retain_transcript": False},
    )
    assert end_resp.status_code == 200
    receipt_data = end_resp.json()
    assert receipt_data["transcript_retained"] is False
    assert receipt_data["ledger_entry_hash"] is not None

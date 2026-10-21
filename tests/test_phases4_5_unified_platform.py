"""
LifeLens Ω — Comprehensive Unit & Integration Tests for Phase 4 & Phase 5
Implements test verification for §94, §99, §100, §101, §97, §98
"""
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from apps.api.app.main import app
from apps.api.app.services.meeting_shield import (
    MeetingShieldOrchestrator,
    ShieldAlertSeverity,
)
from apps.api.app.cect.unified_reasoner import UnifiedCECTReasoner
from apps.api.app.services.unified_trust_ledger import TrustIntegrityLedger
from apps.api.app.security.federated_privacy_sandbox import FederatedPrivacySandbox
from apps.api.app.models.request import VerificationRequest
from apps.api.app.risk.engine import RiskLevel

client = TestClient(app)


# --- Phase 4: Meeting Shield Unit Tests ---

def test_meeting_shield_session_lifecycle():
    shield = MeetingShieldOrchestrator(voice_clone_threshold=0.70, visual_artifact_threshold=0.65)
    
    # 1. Start session
    session = shield.start_session("Interview with TechCorp Recruiter", platform="Zoom", user_consent=True)
    assert session.is_active is True
    assert session.total_audio_chunks == 0
    assert session.total_video_chunks == 0

    # 2. Normal audio chunk (low synthetic prob) -> No alert
    alert1 = shield.ingest_audio_chunk(
        session_id=session.session_id,
        duration_ms=1000,
        spectral_flatness=0.30,
        pitch_variance=0.45,
        synthetic_voice_prob=0.15,
    )
    assert alert1 is None

    # 3. High synthetic voice chunk -> Triggers Alert
    alert2 = shield.ingest_audio_chunk(
        session_id=session.session_id,
        duration_ms=1000,
        spectral_flatness=0.85,
        pitch_variance=0.02,
        synthetic_voice_prob=0.92,
    )
    assert alert2 is not None
    assert alert2.severity == ShieldAlertSeverity.CRITICAL
    assert alert2.signal_name == "SYNTHETIC_VOICE_DETECTION"
    assert "Request caller to answer" in alert2.recommended_action

    # 4. Deepfake visual chunk -> Triggers Alert
    alert3 = shield.ingest_video_chunk(
        session_id=session.session_id,
        duration_ms=1000,
        lip_sync_error=0.88,
        facial_artifact_score=0.90,
        blinking_regularity_score=0.10,
    )
    assert alert3 is not None
    assert alert3.severity == ShieldAlertSeverity.CRITICAL
    assert alert3.signal_name == "VISUAL_DEEPFAKE_ARTIFACT"

    # 5. End session and review report
    report = shield.end_session(session.session_id)
    assert report["total_alerts"] == 2
    assert report["safety_verdict"] == "Request looks high-risk"
    assert report["total_audio_chunks_inspected"] == 2
    assert report["total_video_chunks_inspected"] == 1


def test_meeting_shield_consent_enforcement():
    shield = MeetingShieldOrchestrator()
    session = shield.start_session("Unconsented Meeting", user_consent=False)

    with pytest.raises(PermissionError, match="user consent not granted"):
        shield.ingest_audio_chunk(session.session_id, 1000, 0.5, 0.5, 0.8)


# --- Phase 5: Unified CECT Reasoner & Mental Model Tests ---

def test_unified_cect_reasoner_canonical_flow():
    reasoner = UnifiedCECTReasoner()
    
    # Clean request
    req = VerificationRequest(
        request_id="holistic_req_001",
        created_at=datetime.now(timezone.utc),
        job_title="Senior Python Backend Engineer",
        company_name="Acme Corporation Ltd",
        company_website="https://www.acme-corp.co.uk",
        recruiter_name="Sarah Jenkins",
        recruiter_email="sarah.jenkins@acme-corp.co.uk",
        claimed_country="GB",
        job_description="Standard engineering role with official corporate email and UK registry match.",
    )

    verdict = reasoner.evaluate_holistic_interaction(req)
    assert verdict.request_id == "holistic_req_001"
    assert "step_1_who" in verdict.mental_model_steps
    assert "step_2_claims" in verdict.mental_model_steps
    assert "step_3_evidence_sources" in verdict.mental_model_steps
    assert "step_10_verification_actions" in verdict.mental_model_steps
    assert verdict.overall_risk_level in (RiskLevel.LOW, RiskLevel.MEDIUM)
    assert len(verdict.empowerment_guidance) > 0


def test_unified_cect_reasoner_with_meeting_alerts():
    shield = MeetingShieldOrchestrator()
    session = shield.start_session("Sketchy Executive Interview", user_consent=True)
    shield.ingest_audio_chunk(session.session_id, 1000, 0.9, 0.01, 0.95)

    reasoner = UnifiedCECTReasoner(meeting_shield=shield)
    req = VerificationRequest(
        request_id="holistic_req_002",
        created_at=datetime.now(timezone.utc),
        job_title="Executive Advisor",
        company_name="Offshore Global Trading",
        company_website="http://offshore-trading-fake.com",
        recruiter_name="Anonymous Agent",
        recruiter_email="agent@gmail.com",
        claimed_country="GB",
        job_description="Urgent wire transfer processing required for relocation visa.",
    )

    verdict = reasoner.evaluate_holistic_interaction(req, meeting_session_id=session.session_id)
    assert verdict.overall_risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL)
    assert "Live audio/video stream shows synthetic deepfake artifacts" in verdict.primary_concerns
    assert "ALERTS_ACTIVE" in verdict.media_authenticity_status


# --- Phase 5: Cryptographic Trust Integrity Ledger Tests ---

def test_trust_integrity_ledger_immutability():
    ledger = TrustIntegrityLedger()
    assert len(ledger.chain) == 1  # Genesis
    assert ledger.verify_chain_integrity() is True

    # Record 3 events
    b1 = ledger.record_verification("req_101", "Company A", "LOW", 0.95)
    b2 = ledger.record_verification("req_102", "Company B", "HIGH", 0.85)
    b3 = ledger.record_verification("req_103", "Company C", "MEDIUM", 0.78)

    assert len(ledger.chain) == 4
    assert b2.previous_hash == b1.block_hash
    assert b3.previous_hash == b2.block_hash
    assert ledger.verify_chain_integrity() is True

    # Verify audit export
    trail = ledger.export_audit_trail()
    assert len(trail) == 4
    assert trail[1]["request_id"] == "req_101"

    # Tamper test: Corrupt block 2 payload and ensure chain detects tampering
    ledger.chain[2].risk_level = "TAMPERED_LEVEL"
    assert ledger.verify_chain_integrity() is False


# --- Phase 5: Federated Privacy Sandbox & Gate Validator Tests ---

def test_federated_privacy_sandbox_gate_criteria():
    sandbox = FederatedPrivacySandbox(min_sample_threshold=5, max_epsilon_budget=1.0)
    user_id = "usr_test_999"

    # 1. Without consent -> Fails gate
    gate = sandbox.validate_gate_criteria(user_id)
    assert gate.is_cleared is False
    assert any("Explicit user consent" in r for r in gate.rejection_reasons)

    # 2. Grant consent but insufficient samples (< 5) -> Fails gate
    sandbox.set_user_consent(user_id, True)
    sandbox.record_local_observation(user_id, {"latency_ms": 120.0})
    gate = sandbox.validate_gate_criteria(user_id)
    assert gate.is_cleared is False
    assert any("Insufficient sample size" in r for r in gate.rejection_reasons)


    # 3. Add sufficient samples (>= 5) -> Cleared gate
    for i in range(5):
        sandbox.record_local_observation(user_id, {"feature": float(i)})
    gate = sandbox.validate_gate_criteria(user_id)
    assert gate.is_cleared is True

    # 4. Compute DP update
    gradient = [0.2, 0.4, -0.1]
    update, gate_status = sandbox.compute_sanitized_update(user_id, gradient, delta_epsilon=0.2)
    assert update is not None
    assert gate_status.dp_epsilon_used == 0.2

    # 5. Poisoning defense test: Extreme gradient norm is rejected
    extreme_gradient = [100.0, -250.0, 50.0]
    bad_update, bad_gate = sandbox.compute_sanitized_update(user_id, extreme_gradient)
    assert bad_update is None
    assert bad_gate.poisoning_risk_flagged is True

    # 6. User Privacy Reset: purges all data
    assert sandbox.reset_user_baseline(user_id) is True
    post_reset_gate = sandbox.validate_gate_criteria(user_id)
    assert post_reset_gate.sample_size == 0


# --- FastAPI Endpoint Integration Tests ---

def test_api_meeting_shield_endpoints():
    # Start session
    resp = client.post("/api/v1/meeting-shield/session/start", json={
        "meeting_title": "Video Screening",
        "platform": "Teams",
        "user_consent": True,
    })
    assert resp.status_code == 200
    session_id = resp.json()["session_id"]

    # Ingest audio chunk
    resp_audio = client.post("/api/v1/meeting-shield/session/audio-chunk", json={
        "session_id": session_id,
        "synthetic_voice_prob": 0.89,
    })
    assert resp_audio.status_code == 200
    assert resp_audio.json()["alert_triggered"] is True

    # End session
    resp_end = client.post(f"/api/v1/meeting-shield/session/{session_id}/end")
    assert resp_end.status_code == 200
    assert resp_end.json()["total_alerts"] >= 1


def test_api_unified_verify_and_ledger_endpoints():
    resp = client.post("/api/v1/unified/verify", json={
        "request_id": "api_test_unified_001",
        "company_name": "Test Unified Labs",
        "job_title": "AI Researcher",
        "recruiter_email": "recruiter@test-unified-labs.org",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "verdict" in data
    assert "ledger_proof" in data
    assert data["ledger_proof"]["chain_valid"] is True

    # Check ledger audit endpoint
    ledger_resp = client.get("/api/v1/ledger/audit-trail")
    assert ledger_resp.status_code == 200
    assert ledger_resp.json()["chain_valid"] is True


def test_api_privacy_sandbox_endpoints():
    resp = client.post("/api/v1/privacy-sandbox/consent", json={
        "user_id": "api_user_42",
        "consent": True,
    })
    assert resp.status_code == 200
    assert resp.json()["consent_active"] is True

    reset_resp = client.post("/api/v1/privacy-sandbox/reset/api_user_42")
    assert reset_resp.status_code == 200
    assert reset_resp.json()["status"] == "purged"

"""
LifeLens Ω — Phase 4 & 5 API Router: Meeting Shield & Unified Trust Platform
Implements §94, §99, §100, §101, §97, §98
"""
from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

from apps.api.app.services.meeting_shield import MeetingShieldOrchestrator
from apps.api.app.cect.unified_reasoner import UnifiedCECTReasoner
from apps.api.app.services.unified_trust_ledger import TrustIntegrityLedger
from apps.api.app.security.federated_privacy_sandbox import FederatedPrivacySandbox
from apps.api.app.models.request import VerificationRequest

router = APIRouter(prefix="/api/v1", tags=["Phases 4 & 5: Meeting Shield & Unified Platform"])

# Singleton state orchestrators
meeting_shield = MeetingShieldOrchestrator()
unified_reasoner = UnifiedCECTReasoner(meeting_shield=meeting_shield)
trust_ledger = TrustIntegrityLedger()
privacy_sandbox = FederatedPrivacySandbox()


# --- Phase 4: Meeting Shield Schemas & Endpoints ---

class StartMeetingSessionRequest(BaseModel):
    meeting_title: str = Field(..., examples=["Technical Interview with Global HR"])
    platform: str = Field(default="Google Meet", examples=["Google Meet"])
    user_consent: bool = Field(default=True, examples=[True])


class IngestAudioChunkRequest(BaseModel):
    session_id: str
    duration_ms: int = 1000
    spectral_flatness: float = 0.45
    pitch_variance: float = 0.12
    synthetic_voice_prob: float = Field(..., ge=0.0, le=1.0)


class IngestVideoChunkRequest(BaseModel):
    session_id: str
    duration_ms: int = 1000
    lip_sync_error: float = Field(..., ge=0.0, le=1.0)
    facial_artifact_score: float = Field(..., ge=0.0, le=1.0)
    blinking_regularity_score: float = 0.85


@router.post("/meeting-shield/session/start")
def start_meeting_session(req: StartMeetingSessionRequest):
    session = meeting_shield.start_session(
        meeting_title=req.meeting_title,
        platform=req.platform,
        user_consent=req.user_consent,
    )
    return {
        "status": "active",
        "session_id": session.session_id,
        "meeting_title": session.meeting_title,
        "platform": session.platform,
        "consent_granted": session.user_consent_granted,
        "started_at": session.started_at.isoformat(),
    }


@router.post("/meeting-shield/session/audio-chunk")
def ingest_audio_chunk(req: IngestAudioChunkRequest):
    try:
        alert = meeting_shield.ingest_audio_chunk(
            session_id=req.session_id,
            duration_ms=req.duration_ms,
            spectral_flatness=req.spectral_flatness,
            pitch_variance=req.pitch_variance,
            synthetic_voice_prob=req.synthetic_voice_prob,
        )
        return {
            "status": "processed",
            "alert_triggered": alert is not None,
            "alert": alert.__dict__ if alert else None,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/meeting-shield/session/video-chunk")
def ingest_video_chunk(req: IngestVideoChunkRequest):
    try:
        alert = meeting_shield.ingest_video_chunk(
            session_id=req.session_id,
            duration_ms=req.duration_ms,
            lip_sync_error=req.lip_sync_error,
            facial_artifact_score=req.facial_artifact_score,
            blinking_regularity_score=req.blinking_regularity_score,
        )
        return {
            "status": "processed",
            "alert_triggered": alert is not None,
            "alert": alert.__dict__ if alert else None,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/meeting-shield/session/{session_id}/end")
def end_meeting_session(session_id: str):
    try:
        report = meeting_shield.end_session(session_id)
        return report
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


# --- Phase 5: Unified Platform, Trust Ledger, & Privacy Sandbox ---

class HolisticVerificationRequest(BaseModel):
    request_id: str
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    company_website: Optional[str] = None
    recruiter_name: Optional[str] = None
    recruiter_email: Optional[str] = None
    claimed_country: Optional[str] = "GB"
    job_description: Optional[str] = None
    meeting_session_id: Optional[str] = None


@router.post("/unified/verify")
def evaluate_unified_trust(req: HolisticVerificationRequest):
    """Executes full 10-step LifeLens Ω Mental Model (§101) & stores in Ledger (§100)."""
    verif_req = VerificationRequest(
        request_id=req.request_id,
        created_at=datetime.now(timezone.utc),
        job_title=req.job_title,
        company_name=req.company_name,
        company_website=req.company_website,
        recruiter_name=req.recruiter_name,
        recruiter_email=req.recruiter_email,
        claimed_country=req.claimed_country,
        job_description=req.job_description,
    )
    verdict = unified_reasoner.evaluate_holistic_interaction(
        request=verif_req,
        meeting_session_id=req.meeting_session_id,
    )

    # Record into Cryptographic Trust Integrity Ledger (§13, §100)
    block = trust_ledger.record_verification(
        request_id=verdict.request_id,
        entity_name=req.company_name or req.recruiter_name or "Unknown Entity",
        risk_level=verdict.overall_risk_level.value,
        confidence=verdict.overall_confidence,
    )

    return {
        "verdict": verdict.__dict__,
        "ledger_proof": {
            "block_index": block.index,
            "block_hash": block.block_hash,
            "previous_hash": block.previous_hash,
            "chain_valid": trust_ledger.verify_chain_integrity(),
        }
    }


@router.get("/ledger/audit-trail")
def get_ledger_audit_trail(request_id: Optional[str] = Query(None)):
    """Exports cryptographic verification audit trail (§88)."""
    return {
        "chain_valid": trust_ledger.verify_chain_integrity(),
        "total_blocks": len(trust_ledger.chain),
        "blocks": trust_ledger.export_audit_trail(request_id=request_id),
    }


class ConsentUpdateRequest(BaseModel):
    user_id: str
    consent: bool


@router.post("/privacy-sandbox/consent")
def update_privacy_consent(req: ConsentUpdateRequest):
    privacy_sandbox.set_user_consent(req.user_id, req.consent)
    gate = privacy_sandbox.validate_gate_criteria(req.user_id)
    return {
        "user_id": req.user_id,
        "consent_active": req.consent,
        "gate_status": gate.__dict__,
    }


@router.post("/privacy-sandbox/reset/{user_id}")
def reset_privacy_sandbox(user_id: str):
    privacy_sandbox.reset_user_baseline(user_id)
    return {
        "status": "purged",
        "user_id": user_id,
        "detail": "All local observation buffers and privacy consumption counters have been wiped.",
    }

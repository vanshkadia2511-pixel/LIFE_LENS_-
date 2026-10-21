"""
LifeLens Ω — Desktop Call Guard API Endpoints
Phase C: Local Platform-Agnostic Desktop Guard (/api/v1/desktop-guard/*)
"""
from __future__ import annotations
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
import logging

from apps.api.app.models.desktop_guard import (
    DesktopGuardStartRequest,
    DesktopGuardSessionState,
    DesktopGuardChunkRequest,
    DesktopGuardAlert,
    VerificationInterstitial,
    LivenessChallenge,
    DesktopGuardEndRequest,
    PostCallReceipt,
)
from apps.api.app.services.desktop_guard_service import DesktopCallGuardService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/desktop-guard",
    tags=["desktop-guard"],
)

desktop_guard_service = DesktopCallGuardService()


class VerifyStepRequest(BaseModel):
    session_id: str
    step_index: int


@router.post(
    "/start",
    response_model=DesktopGuardSessionState,
    summary="Start Desktop Call Guard Session",
    description="Initiates local call monitoring session. Requires explicit user consent (§P5/§P6).",
)
async def start_desktop_guard(req: DesktopGuardStartRequest) -> DesktopGuardSessionState:
    return desktop_guard_service.start_session(req)


@router.post(
    "/chunk",
    response_model=List[DesktopGuardAlert],
    summary="Ingest Local Transcript Chunk",
    description="Processes streaming transcript chunk through Layer 2 trajectory triggers in memory.",
)
async def ingest_chunk(req: DesktopGuardChunkRequest) -> List[DesktopGuardAlert]:
    return desktop_guard_service.ingest_transcript_chunk(req)


@router.get(
    "/interstitial/{session_id}",
    response_model=Optional[VerificationInterstitial],
    summary="Get Active Verification Interstitial",
    description="Returns Layer 3 pause interstitial and callback checklist if triggered.",
)
async def get_interstitial(session_id: str) -> Optional[VerificationInterstitial]:
    interstitial = desktop_guard_service.get_active_interstitial(session_id)
    if not interstitial:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active interstitial found for session",
        )
    return interstitial


@router.post(
    "/verify-step",
    summary="Complete Interstitial Verification Step",
    description="Updates verification checklist progress for human-in-the-loop decision (§P6).",
)
async def complete_verify_step(req: VerifyStepRequest):
    sess = desktop_guard_service.complete_verification_step(req.session_id, req.step_index)
    if not sess:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session or interstitial not found",
        )
    return {"status": "updated", "step_index": req.step_index}


@router.get(
    "/challenges/{session_id}",
    response_model=List[LivenessChallenge],
    summary="Get Liveness Challenges (Layer 4 Coach)",
    description="Suggests behavioral challenges to expose deepfakes without claiming automated pass/fail verdict (P6).",
)
async def get_challenges(session_id: str) -> List[LivenessChallenge]:
    return desktop_guard_service.get_liveness_challenges(session_id)


@router.post(
    "/end",
    response_model=PostCallReceipt,
    summary="End Desktop Call Guard Session & Generate Ledger Receipt",
    description="Terminates session, purges transcript from memory unless opted in, and logs cryptographic ledger entry.",
)
async def end_desktop_guard(req: DesktopGuardEndRequest) -> PostCallReceipt:
    return desktop_guard_service.end_session(req)

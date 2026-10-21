"""
LifeLens Ω — Call Guardian Layer 0 API Endpoints
POST /api/v1/call-guard/invite/check
"""
from __future__ import annotations
from fastapi import APIRouter, HTTPException, status
import logging

from apps.api.app.models.call_guard import (
    CallInviteCheckRequest,
    CallInviteAssessment,
)
from apps.api.app.services.call_guard_service import CallGuardianLayer0Service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/call-guard",
    tags=["call-guard"],
)

call_guard_service = CallGuardianLayer0Service()


@router.post(
    "/invite/check",
    response_model=CallInviteAssessment,
    summary="Check Meeting Invite Metadata (Layer 0 Pre-Call Inspector)",
    description=(
        "Inspects meeting links and invite metadata for SSRF risks, lookalikes, "
        "unsolicited arrival vectors, and high-urgency coercion. "
        "Never joins or downloads meeting stream contents. Consent-gated (§P5, §P6)."
    ),
)
async def check_call_invite(request: CallInviteCheckRequest) -> CallInviteAssessment:
    try:
        assessment = call_guard_service.check_invite(request)
        return assessment
    except Exception as exc:
        logger.error("Error inspecting call invite: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Call Guardian inspection error: {str(exc)}",
        )

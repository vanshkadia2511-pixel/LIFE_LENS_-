"""
LifeLens Ω — Verification API Endpoints
Implementation Plan §41, §59, §60, §68
"""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Dict, Optional
from fastapi import APIRouter, HTTPException, status
import logging

from ..models.request import VerificationRequest
from ..schemas.verification import (
    VerificationApiRequest,
    VerificationApiResponse,
    RiskSignalSchema,
    EvidenceCardSchema,
    CECTScoresSchema,
    ExplanationSchema,
    FeedbackApiRequest,
    FeedbackApiResponse,
)
from ..services.verification_service import VerificationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["verification"])
_service = VerificationService()

# In-memory store for fast retrieval of assessments and feedback
_ASSESSMENT_STORE: Dict[str, VerificationApiResponse] = {}
_FEEDBACK_STORE: Dict[str, dict] = {}


def _execute_verification(payload: VerificationApiRequest) -> VerificationApiResponse:
    req_id = payload.request_id or f"req-{uuid.uuid4().hex[:10]}"
    request_model = VerificationRequest(
        request_id=req_id,
        created_at=datetime.now(timezone.utc),
        source_platform=payload.source_platform or "Generic",
        job_title=payload.job_title,
        job_description=payload.job_description,
        company_name=payload.company_name,
        company_website=payload.company_website,
        recruiter_name=payload.recruiter_name,
        recruiter_email=payload.recruiter_email,
        recruiter_phone=payload.recruiter_phone,
        claimed_country=payload.claimed_country or "GB",
        claimed_location=payload.claimed_location,
        consent_for_analysis=payload.consent_for_analysis,
    )

    result = _service.process_verification(request_model)

    response = VerificationApiResponse(
        request_id=result.request_id,
        processed_at=result.processed_at.isoformat(),
        risk_level=result.risk_assessment.risk_level.value,
        risk_score=result.risk_assessment.risk_score,
        confidence=result.risk_assessment.confidence,
        cect_scores=CECTScoresSchema(
            coherence=result.cect_assessment.coherence_score,
            evidence_independence=result.cect_assessment.evidence_independence_score,
            consistency=result.cect_assessment.consistency_score,
            trajectory=result.cect_assessment.trajectory_score,
            confidence=result.cect_assessment.confidence,
        ),
        signals=[
            RiskSignalSchema(
                signal_id=s.signal_id,
                category=s.category,
                description=s.description,
                severity=s.severity.value,
                reliability=s.reliability,
                detected_by=s.detected_by,
                evidence_ids=s.evidence_ids,
            )
            for s in result.risk_assessment.signals
        ],
        primary_concerns=result.risk_assessment.primary_concerns,
        mitigating_factors=result.risk_assessment.mitigating_factors,
        explanation=ExplanationSchema(
            summary_headline=result.explanation.summary_headline,
            confidence_label=result.explanation.confidence_label,
            what_was_checked=result.explanation.what_was_checked,
            what_was_found=result.explanation.what_was_found,
            why_it_matters=result.explanation.why_it_matters,
            what_could_not_be_verified=result.explanation.what_could_not_be_verified,
            recommended_next_steps=result.explanation.recommended_next_steps,
            evidence_cards=[
                EvidenceCardSchema(
                    evidence_id=c.evidence_id,
                    source_name=c.source_name,
                    source_type=c.source_type,
                    observed_value=c.observed_value,
                    source_url=c.source_url,
                    source_authority=c.source_authority,
                    source_independence=c.source_independence,
                    user_verifiable=c.user_verifiable,
                    verification_path=c.verification_path,
                    captured_at=c.captured_at,
                    is_simulated=getattr(c, 'is_simulated', False),
                )
                for c in result.explanation.evidence_cards
            ],
            disclaimer=result.explanation.disclaimer,
        ),
    )

    # Store for later retrieval
    _ASSESSMENT_STORE[response.request_id] = response
    return response


@router.post(
    "/verify-job",
    response_model=VerificationApiResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify a job posting / recruiter offer for authenticity and risk",
)
async def verify_job(payload: VerificationApiRequest) -> VerificationApiResponse:
    try:
        return _execute_verification(payload)
    except Exception as exc:
        logger.exception("Error processing verification request: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Verification pipeline failed: {str(exc)}",
        )


@router.post(
    "/verify",
    response_model=VerificationApiResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify a job posting / recruiter offer (canonical endpoint — spec §41)",
)
async def verify(payload: VerificationApiRequest) -> VerificationApiResponse:
    """Canonical POST /api/v1/verify endpoint (Phase 1 alias, non-breaking)."""
    return await verify_job(payload)


@router.post(
    "/verifications",
    response_model=VerificationApiResponse,
    status_code=status.HTTP_200_OK,
    summary="Create a verification request (§41)",
)
async def create_verification(payload: VerificationApiRequest) -> VerificationApiResponse:
    return await verify_job(payload)


@router.get(
    "/verifications/{request_id}",
    response_model=VerificationApiResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve a previously processed verification by request ID (§41)",
)
async def get_verification(request_id: str) -> VerificationApiResponse:
    if request_id not in _ASSESSMENT_STORE:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Verification request '{request_id}' not found.",
        )
    return _ASSESSMENT_STORE[request_id]


@router.post(
    "/feedback",
    response_model=FeedbackApiResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit user feedback on verification accuracy (§41, §68)",
)
async def submit_feedback(payload: FeedbackApiRequest) -> FeedbackApiResponse:
    fb_id = f"fb-{uuid.uuid4().hex[:10]}"
    now_str = datetime.now(timezone.utc).isoformat()
    _FEEDBACK_STORE[fb_id] = {
        "feedback_id": fb_id,
        "request_id": payload.request_id,
        "feedback_type": payload.feedback_type,
        "comment": payload.comment,
        "confirmed_outcome": payload.confirmed_outcome,
        "created_at": now_str,
    }
    logger.info("Feedback recorded for request %s (Type: %s)", payload.request_id, payload.feedback_type)
    return FeedbackApiResponse(
        status="recorded",
        feedback_id=fb_id,
        request_id=payload.request_id,
        recorded_at=now_str,
    )

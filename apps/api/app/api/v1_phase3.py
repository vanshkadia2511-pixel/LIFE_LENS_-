"""
LifeLens Ω — Phase 3 API Endpoints (§80, §76, §87)

Provides:
  POST /api/v1/media/analyze          — §80 Submit media for authenticity analysis
  GET  /api/v1/media/session-summary  — §80 Session alert summary
  GET  /api/v1/media/alerts           — §80 Alert history
  POST /api/v1/quality-gates/evaluate — §76 Evaluate data quality gates for a source
  GET  /api/v1/quality-gates/status   — §76 Get current source health registry
  GET  /api/v1/demo/scenario          — §87 Run the canonical demo scenario
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from ..services.media_authenticity import (
    MediaCapture,
    MediaType,
    MediaAuthenticityOrchestrator,
    MockDeepfakeDetectionProvider,
)
from ..services.meeting_alert_engine import MeetingAlertEngine
from ..services.data_quality_gates import (
    DataQualityGateEvaluator,
    source_health_registry,
)

router = APIRouter(prefix="/api/v1", tags=["phase3", "media", "quality-gates", "demo"])

# Module-level singletons
_mock_provider = MockDeepfakeDetectionProvider()
_orchestrator = MediaAuthenticityOrchestrator(provider=_mock_provider)
_alert_engine = MeetingAlertEngine(orchestrator=_orchestrator)
_quality_evaluator = DataQualityGateEvaluator()


# ─────────────────────────────────────────────────────────────
# Pydantic schemas
# ─────────────────────────────────────────────────────────────

class MediaAnalyzeRequest(BaseModel):
    media_type: str          # VIDEO | AUDIO | IMAGE | SCREEN_CAPTURE
    content_url: Optional[str] = None
    duration_seconds: Optional[float] = None
    user_consented: bool = False


class QualityGateEvaluateRequest(BaseModel):
    source_name: str
    adapter_name: str
    coverage_pct: Optional[float] = None
    data_age_hours: Optional[float] = None
    availability_pct: Optional[float] = None
    error_rate: Optional[float] = None
    terms_allow_automation: Optional[bool] = None
    fails_gracefully: Optional[bool] = None


# ─────────────────────────────────────────────────────────────
# §80 — Media Authenticity Analysis
# ─────────────────────────────────────────────────────────────

@router.post(
    "/media/analyze",
    summary="§80 — Submit media capture for authenticity analysis",
    tags=["media"],
)
async def analyze_media(payload: MediaAnalyzeRequest) -> dict:
    """
    §80: Submit a media capture (video, audio, image) for authenticity analysis.
    Consent is required (§35). Returns authenticity signals for integration
    into the LifeLens evidence layer.
    """
    try:
        media_type = MediaType(payload.media_type.upper())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid media_type '{payload.media_type}'. Must be one of: VIDEO, AUDIO, IMAGE, SCREEN_CAPTURE.",
        )

    capture = MediaCapture(
        media_type=media_type,
        content_url=payload.content_url,
        duration_seconds=payload.duration_seconds,
        user_consented=payload.user_consented,
    )

    # Run through alert engine (which calls orchestrator internally)
    alert = _alert_engine.evaluate(capture)
    result = _orchestrator.analyze(capture)

    return {
        "result": result.to_evidence_dict(),
        "risk_boost": _orchestrator.get_risk_boost(result),
        "alert": alert.to_dict() if alert else None,
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
        "provider": result.provider_name,
    }


@router.get(
    "/media/alerts",
    summary="§80 — Get all real-time meeting alerts from this session",
    tags=["media"],
)
async def get_meeting_alerts() -> dict:
    return {
        "alerts": _alert_engine.get_alert_history(),
        "total": len(_alert_engine.get_alert_history()),
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
    }


@router.get(
    "/media/session-summary",
    summary="§80 — Get authenticity summary for the current meeting session",
    tags=["media"],
)
async def get_session_summary() -> dict:
    return {
        "summary": _alert_engine.get_session_summary(),
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
    }


# ─────────────────────────────────────────────────────────────
# §76 — Data Quality Gates
# ─────────────────────────────────────────────────────────────

@router.post(
    "/quality-gates/evaluate",
    summary="§76 — Evaluate data quality gates for a verification source",
    tags=["quality-gates"],
)
async def evaluate_quality_gate(payload: QualityGateEvaluateRequest) -> dict:
    """
    §76: Run data quality gates before registering a verification source for production use.
    Returns HEALTHY | DEGRADED | UNAVAILABLE based on gate outcomes.
    """
    report = _quality_evaluator.evaluate(
        source_name=payload.source_name,
        adapter_name=payload.adapter_name,
        coverage_pct=payload.coverage_pct,
        data_age_hours=payload.data_age_hours,
        availability_pct=payload.availability_pct,
        error_rate=payload.error_rate,
        terms_allow_automation=payload.terms_allow_automation,
        fails_gracefully=payload.fails_gracefully,
    )
    source_health_registry.register(report)
    return report.to_dict()


@router.get(
    "/quality-gates/status",
    summary="§76 — Get current health status of all registered verification sources",
    tags=["quality-gates"],
)
async def get_quality_gate_status() -> dict:
    return {
        "sources": source_health_registry.get_all_statuses(),
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
    }


# ─────────────────────────────────────────────────────────────
# §87 — Demo Scenario
# ─────────────────────────────────────────────────────────────

@router.get(
    "/demo/scenario",
    summary="§87 — Run the canonical LifeLens Ω demo scenario",
    tags=["demo"],
)
async def run_demo_scenario() -> dict:
    """
    §87: The canonical end-to-end demo scenario.

    A foreign job recruiter contacts a candidate:
        Job: Software Engineer — Country X
        Claim: Visa sponsorship included
        Recruiter: HR Manager, hr-careers@example-careers.com
        Official company: example.com

    LifeLens checks all claims, runs CECT, and returns the full
    explainable risk result showing why this is HIGH risk.
    """
    return {
        "scenario": "§87 — Foreign Job Offer with Recruiter Domain Mismatch",
        "input": {
            "job_title": "Software Engineer",
            "company_name": "ExampleCorp International",
            "company_website": "https://example.com",
            "recruiter_name": "HR Manager",
            "recruiter_email": "hr-careers@example-careers.com",
            "claimed_country": "AE",
            "visa_claim": "Visa sponsorship included.",
            "urgency": "Offer expires in 48 hours",
            "payment_requested": "USD 500 visa processing fee",
        },
        "verification_results": {
            "company_exists": "YES — ExampleCorp International is found in registry",
            "official_website": "YES — example.com is the official domain",
            "recruiter_identity": "NOT VERIFIED — no record of this recruiter on official channels",
            "domain_match": "NO — hr-careers@example-careers.com ≠ example.com",
            "visa_claim": "NOT INDEPENDENTLY VERIFIED — no government source confirms this",
            "urgency_detected": "YES — 48-hour deadline",
            "payment_request": "YES — $500 upfront fee requested",
        },
        "cect": {
            "coherence": "MEDIUM — company exists but contact details are inconsistent",
            "evidence_independence": "LOW — all positive evidence comes from the recruiter alone",
            "consistency": "LOW — email domain does not match official domain",
            "trajectory": "HIGH RISK — interaction has moved to financial request stage",
        },
        "community_patterns_matched": [
            "SCAM_PATTERN_001: Upfront visa-processing fee",
            "SCAM_PATTERN_002: Recruiter domain does not match official company domain",
            "SCAM_PATTERN_004: Artificial urgency detected",
        ],
        "trajectory": {
            "label": "HIGH_RISK_ESCALATION",
            "stages": ["INITIAL_CONTACT", "TRUST_BUILDING", "FINANCIAL_REQUEST"],
            "score": 0.8,
        },
        "final_result": {
            "risk": "HIGH",
            "confidence": "MEDIUM",
            "primary_concerns": [
                "Recruiter identity not independently verified.",
                "Recruiter domain (example-careers.com) differs from official company domain (example.com).",
                "Visa claim is not independently verified through government sources.",
                "Interaction has escalated to a financial request — $500 upfront fee.",
                "Artificial urgency: offer expires in 48 hours.",
            ],
            "recommended_next_steps": [
                "Contact ExampleCorp through its official website (example.com) directly.",
                "Do NOT send money or sensitive documents until the recruiter's identity is verified.",
                "Search for 'example-careers.com' to check if it is a known scam domain.",
                "Report this interaction if you believe it is fraudulent.",
            ],
            "disclaimer": (
                "This is an evidence-based risk assessment. LifeLens does not claim to detect all fraud. "
                "Always make your own independent verification before taking any financial action."
            ),
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "version": "0.3.0",
    }

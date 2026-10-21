"""
LifeLens Ω — Phase G: Detectors API Router
Exposes endpoints for the 7 new specialized threat detectors.
"""
from __future__ import annotations
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel, Field

from apps.api.app.detectors.tech_test_scanner import TechTestSafetyScanner
from apps.api.app.detectors.digital_arrest_pack import DigitalArrestPatternPack
from apps.api.app.detectors.candidate_identity_checker import CandidateIdentityChecker
from apps.api.app.detectors.voice_clone_flow import VoiceCloneProtectionFlow
from apps.api.app.detectors.quishing_upi_loan_checker import (
    QuishingChecker,
    UPICollectExplainer,
    FakeLoanAPKChecker,
)
from apps.api.app.detectors.investment_verifier import InvestmentPlatformVerifier
from apps.api.app.detectors.romance_pig_butchering import PigButcheringTrajectoryEngine

router = APIRouter(prefix="/api/v1/detectors", tags=["Phase G Detectors"])

_tech_scanner = TechTestSafetyScanner()
_digital_arrest = DigitalArrestPatternPack()
_candidate_checker = CandidateIdentityChecker()
_voice_flow = VoiceCloneProtectionFlow()
_upi_explainer = UPICollectExplainer()
_quishing = QuishingChecker()
_loan_apk = FakeLoanAPKChecker()
_invest_verifier = InvestmentPlatformVerifier()
_pig_butchering = PigButcheringTrajectoryEngine()


# ── Schemas ───────────────────────────────────────────────────────────────────

class TextCheckRequest(BaseModel):
    text: str = Field(..., description="Message text or transcript to analyze")

class UPIExplainRequest(BaseModel):
    message: str = Field(..., description="UPI message or notification text")
    claimed_amount: float = Field(0.0, description="Claimed cashback or transfer amount")
    is_collect_request: bool = Field(False, description="Whether incoming item is a Collect Request")

class CandidateTelemetryRequest(BaseModel):
    candidate_id: str
    audio_video_desync_ms: int = 0
    tab_switches_per_min: int = 0
    multiple_faces_detected: bool = False
    unnatural_speech_cadence_score: float = 0.0

class InvestmentVerifyRequest(BaseModel):
    platform_name: str
    domain: str
    domain_age_days: int = 365
    claimed_guaranteed_return_daily_percent: float = 0.0

class PigButcheringHistoryRequest(BaseModel):
    interactions: List[Dict[str, Any]] = Field(..., description="List of dicts with 'day' and 'text'")


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/tech-test/scan")
async def scan_tech_test_archive(file: UploadFile = File(...)):
    """Statically audits interview take-home zip archive without executing code (§STATIC ONLY)."""
    try:
        content = await file.read()
        res = _tech_scanner.scan_archive_bytes(content, filename=file.filename or "archive.zip")
        return {
            "archive_name": res.archive_name,
            "is_safe": res.is_safe,
            "risk_score": res.risk_score,
            "verdict": res.verdict,
            "risk_indicators": res.risk_indicators,
            "scanned_files": res.scanned_files,
            "execution_performed": res.execution_performed,
            "disclaimer": res.disclaimer,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to scan archive: {str(e)}")


@router.post("/digital-arrest/check")
async def check_digital_arrest(req: TextCheckRequest):
    """Detects digital arrest, CBI, police, customs, and Hinglish intimidation patterns."""
    res = _digital_arrest.evaluate_text(req.text)
    return {
        "text": res.text,
        "is_flagged": res.is_flagged,
        "risk_score": res.risk_score,
        "verdict": res.verdict,
        "matched_patterns": res.matched_patterns,
        "law_enforcement_note": res.law_enforcement_note,
    }


@router.post("/upi/explain")
async def explain_upi_request(req: UPIExplainRequest):
    """Explains UPI collect mechanics and flags 'Enter PIN to receive cashback' deception."""
    res = _upi_explainer.analyze_request(
        req.message,
        claimed_amount=req.claimed_amount,
        is_collect_request=req.is_collect_request,
    )
    return {
        "message": res.message,
        "is_deceptive": res.is_deceptive,
        "verdict": res.verdict,
        "risk_score": res.risk_score,
        "educational_warning": res.educational_warning,
        "key_takeaway": res.key_takeaway,
    }


@router.post("/candidate/evaluate")
async def evaluate_candidate(req: CandidateTelemetryRequest):
    """Evaluates employer-side candidate interview telemetry for proxy indicators."""
    res = _candidate_checker.evaluate_candidate_session(req.model_dump())
    return {
        "candidate_id": res.candidate_id,
        "integrity_verdict": res.integrity_verdict,
        "risk_score": res.risk_score,
        "anomalies": res.anomalies,
        "telemetry_summary": res.telemetry_summary,
        "recommendation": res.recommendation,
    }


@router.post("/investment/verify")
async def verify_investment_platform(req: InvestmentVerifyRequest):
    """Cross-references platform domain and yield claims against regulatory criteria."""
    res = _invest_verifier.verify_platform(req.model_dump())
    return {
        "platform_name": res.platform_name,
        "domain": res.domain,
        "is_registered": res.is_registered,
        "risk_score": res.risk_score,
        "verdict": res.verdict,
        "findings": res.findings,
        "regulatory_guidance": res.regulatory_guidance,
    }


@router.post("/pig-butchering/evaluate")
async def evaluate_pig_butchering_history(req: PigButcheringHistoryRequest):
    """Tracks multi-stage trajectory in romance / crypto arbitrage grooming conversations."""
    res = _pig_butchering.evaluate_history(req.interactions)
    return {
        "current_stage": res.current_stage,
        "overall_risk_score": res.overall_risk_score,
        "verdict": res.verdict,
        "stage_transitions": res.stage_transitions,
        "stage_history": res.stage_history,
        "intervention_recommendation": res.intervention_recommendation,
    }

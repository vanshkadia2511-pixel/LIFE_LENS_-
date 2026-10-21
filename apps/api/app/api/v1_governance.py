"""
LifeLens Ω — Phase J: Trust & Governance API Router
Exposes endpoints for:
- Dispute and right-of-reply submission & proof-of-control verification
- Calibration and ECE reporting per signal group
- Drift canary evaluation and recall alerting
- Public transparency reporting (MEASURED vs TARGET)
"""
from __future__ import annotations
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from apps.api.app.models.dispute import ProofOfControlMethod
from apps.api.app.services.governance.dispute_service import DisputeService
from apps.api.app.services.governance.calibration_reporter import CalibrationReportService
from apps.api.app.services.governance.drift_canary import DriftCanaryService
from apps.api.app.services.governance.transparency_service import TransparencyReportService
from apps.api.app.services.analytics.pilot_analytics import (
    PilotAnalyticsService,
    PrivacyViolationError,
    ConsentRequiredError,
)

router = APIRouter(prefix="/api/v1/governance", tags=["Phase J Trust & Governance"])

_dispute_service = DisputeService()
_calibration_service = CalibrationReportService()
_canary_service = DriftCanaryService()
_transparency_service = TransparencyReportService()
_pilot_service = PilotAnalyticsService()


# ── Schemas ───────────────────────────────────────────────────────────────────

class DisputeSubmitRequest(BaseModel):
    target_entity_domain: str
    contestant_name: str
    contestant_email: str
    reason_for_contest: str
    proof_method: str = "DNS_TXT_RECORD"  # "DNS_TXT_RECORD" | "COMPANY_DOMAIN_EMAIL"

class DisputeVerifyProofRequest(BaseModel):
    dispute_id: str
    submitted_proof_token: str

class PilotEventRequest(BaseModel):
    raw_session_id: str
    event_type: str  # "CHECK_COMPLETED" | "CHECKLIST_ACTION_COMPLETED" | "DISPUTE_SUBMITTED"
    metadata: Dict[str, Any] = Field(default_factory=dict)
    has_explicit_consent: bool = False


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/dispute/submit")
async def submit_dispute(req: DisputeSubmitRequest):
    """
    Submits a dispute contesting an adverse finding.
    Issues a proof-of-control challenge (DNS TXT or corporate email).
    """
    method = (
        ProofOfControlMethod.COMPANY_DOMAIN_EMAIL
        if req.proof_method == "COMPANY_DOMAIN_EMAIL"
        else ProofOfControlMethod.DNS_TXT_RECORD
    )
    res = _dispute_service.submit_dispute(
        target_entity_domain=req.target_entity_domain,
        contestant_name=req.contestant_name,
        contestant_email=req.contestant_email,
        reason_for_contest=req.reason_for_contest,
        proof_method=method,
    )
    return {
        "dispute_id": res.dispute_id,
        "target_entity_domain": res.target_entity_domain,
        "status": res.status.value,
        "proof_method": res.proof_method.value,
        "dns_txt_record_name": res.dns_txt_record_name,
        "dns_txt_expected_value": res.dns_txt_expected_value,
        "email_verification_code": res.email_verification_code,
        "review_time_target": res.review_time_target,
    }


@router.post("/dispute/verify-proof")
async def verify_dispute_proof(req: DisputeVerifyProofRequest):
    """
    Verifies proof of control. Adverse finding is adjusted ONLY if proof matches.
    """
    res = _dispute_service.verify_proof_of_control(
        dispute_id=req.dispute_id,
        submitted_proof_token=req.submitted_proof_token,
    )
    return {
        "dispute_id": res.dispute_id,
        "target_entity_domain": res.target_entity_domain,
        "status": res.status.value,
        "proof_verified": res.proof_verified,
        "finding_modified": res.finding_modified,
        "explanation": res.explanation,
        "ledger_entry_hash": res.ledger_entry_hash,
    }


@router.get("/calibration/report")
async def get_calibration_report():
    """
    Returns empirical Expected Calibration Error (ECE) and reliability curves per signal group.
    """
    calibrations = _calibration_service.get_comprehensive_calibration_report()
    return {
        "signal_groups": [
            {
                "signal_group_name": c.signal_group_name,
                "dataset_name": c.dataset_name,
                "dataset_split": c.dataset_split,
                "sample_size": c.sample_size,
                "expected_calibration_error": c.expected_calibration_error,
                "brier_score": c.brier_score,
                "metric_provenance": c.metric_provenance,
                "in_the_wild_caveat": c.in_the_wild_caveat,
                "reliability_curve": [
                    {
                        "bin_lower": b.bin_lower,
                        "bin_upper": b.bin_upper,
                        "avg_confidence": b.avg_confidence,
                        "observed_accuracy": b.observed_accuracy,
                        "sample_count": b.sample_count,
                    }
                    for b in c.reliability_curve
                ],
            }
            for c in calibrations
        ]
    }


@router.post("/drift-canary/run")
async def run_drift_canary():
    """
    Runs the drift canary set of novel scam phrasings and measures detector sensitivity.
    """
    res = _canary_service.run_canary_evaluation()
    return {
        "total_canaries": res.total_canaries,
        "detected_canaries": res.detected_canaries,
        "measured_recall": res.measured_recall,
        "target_threshold": res.target_threshold,
        "alert_triggered": res.alert_triggered,
        "missed_phrases": res.missed_phrases,
        "run_timestamp_utc": res.run_timestamp_utc,
        "audit_note": res.audit_note,
    }


@router.get("/transparency")
async def get_transparency():
    """
    Returns public transparency metrics comparing MEASURED vs TARGET metrics.
    """
    rep = _transparency_service.get_transparency_report()
    return {
        "metrics_comparison": [
            {
                "metric_name": m.metric_name,
                "target_value": m.target_value,
                "measured_value": m.measured_value,
                "dataset_and_split": m.dataset_and_split,
                "status": m.status,
            }
            for m in rep.metrics_comparison
        ],
        "known_limitations": rep.known_limitations,
        "unverified_hypotheses": rep.unverified_hypotheses,
        "compliance_standards": rep.compliance_standards,
    }


@router.post("/pilot/event")
async def record_pilot_event(req: PilotEventRequest):
    """
    Records privacy-preserving aggregate telemetry for campus and migration pilots.
    Rejects any PII or unconsented events.
    """
    try:
        _pilot_service.record_event(
            raw_session_id=req.raw_session_id,
            event_type=req.event_type,
            metadata=req.metadata,
            has_explicit_consent=req.has_explicit_consent,
        )
        return {"status": "RECORDED", "privacy_mode": "SALTED_HMAC_AGGREGATE_ONLY"}
    except ConsentRequiredError as ce:
        raise HTTPException(status_code=403, detail=str(ce))
    except PrivacyViolationError as pe:
        raise HTTPException(status_code=400, detail=str(pe))


@router.get("/pilot/summary")
async def get_pilot_summary():
    """
    Retrieves aggregate pilot telemetry metrics without any identifying details.
    """
    summary = _pilot_service.get_aggregate_summary()
    return {
        "total_checks": summary.total_checks,
        "high_risk_flagged_count": summary.high_risk_flagged_count,
        "checklist_actions_completed": summary.checklist_actions_completed,
        "verification_paths_taken": summary.verification_paths_taken,
        "disputes_submitted": summary.disputes_submitted,
        "unique_active_sessions_count": summary.unique_active_sessions_count,
        "provenance": summary.provenance,
        "privacy_mode": summary.privacy_mode,
    }

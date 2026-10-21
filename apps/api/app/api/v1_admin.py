"""
LifeLens Ω — Admin & Observability API Endpoints (§70, §71, §73, §75, §82)

Provides:
  GET  /api/v1/admin/metrics           — §70 telemetry summary
  GET  /api/v1/admin/alerts            — §71 recent alert list
  GET  /api/v1/admin/versions          — §73 version manifest
  GET  /api/v1/admin/kill-switches     — §75 list all kill switches
  POST /api/v1/admin/kill-switches/{key}/disable  — §75 disable a feature
  POST /api/v1/admin/kill-switches/{key}/enable   — §75 re-enable a feature
  GET  /api/v1/threat-intel/patterns   — §82 list active scam patterns
  GET  /api/v1/threat-intel/patterns/{pattern_id} — §82 single pattern
  POST /api/v1/threat-intel/report     — §82 anonymized community report
  POST /api/v1/trust-trajectory        — §83 analyze trajectory signals
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from ..services.metrics import metrics_service
from ..services.versioning import (
    CURRENT_VERSION_MANIFEST,
    list_kill_switches,
    disable_feature,
    enable_feature,
)
from ..services.community_threat_intelligence import CommunityThreatIntelligenceService
from ..services.trust_trajectory import TrustTrajectoryAnalyzer, trajectory_assessment_to_dict

router = APIRouter(prefix="/api/v1", tags=["admin", "threat-intel", "trust-trajectory"])

# Module-level service singletons
_threat_intel = CommunityThreatIntelligenceService()
_trajectory_analyzer = TrustTrajectoryAnalyzer()


# ─────────────────────────────────────────────────────────────
# Pydantic request/response schemas
# ─────────────────────────────────────────────────────────────

class ThreatReportRequest(BaseModel):
    pattern_type: str       # UPFRONT_FEE | DOMAIN_MISMATCH | URGENCY | etc.
    geography: Optional[str] = None
    domain: Optional[str] = None  # Will be HMAC-hashed before storage

class ThreatReportResponse(BaseModel):
    pattern_id: str
    message: str
    recorded_at: str


class TrustTrajectoryRequest(BaseModel):
    has_initial_contact: bool = True
    has_trust_building_claims: bool = False
    has_moved_off_platform: bool = False
    has_requested_sensitive_info: bool = False
    has_payment_request: bool = False
    has_pressure_tactics: bool = False
    interaction_age_days: Optional[int] = None
    claimed_country: Optional[str] = None


class KillSwitchActionResponse(BaseModel):
    feature_key: str
    enabled: bool
    message: str


# ─────────────────────────────────────────────────────────────
# §70 — Observability / Metrics
# ─────────────────────────────────────────────────────────────

@router.get(
    "/admin/metrics",
    summary="§70 — Full telemetry summary",
    tags=["admin"],
)
async def get_metrics() -> dict:
    return metrics_service.get_summary()


@router.get(
    "/admin/alerts",
    summary="§71 — Recent monitoring alerts",
    tags=["admin"],
)
async def get_alerts() -> dict:
    return {
        "alerts": metrics_service.get_recent_alerts(),
        "thresholds": {
            "adapter_error_rate": f"{int(metrics_service.__class__.__module__)}",
        },
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
    }


# ─────────────────────────────────────────────────────────────
# §73 — Version Manifest
# ─────────────────────────────────────────────────────────────

@router.get(
    "/admin/versions",
    summary="§73 — Model/Rule version manifest for reproducibility",
    tags=["admin"],
)
async def get_versions() -> dict:
    return CURRENT_VERSION_MANIFEST.to_dict()


# ─────────────────────────────────────────────────────────────
# §75 — Kill Switches
# ─────────────────────────────────────────────────────────────

@router.get(
    "/admin/kill-switches",
    summary="§75 — List all feature kill switches",
    tags=["admin"],
)
async def get_kill_switches() -> dict:
    return {
        "kill_switches": list_kill_switches(),
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
    }


@router.post(
    "/admin/kill-switches/{feature_key}/disable",
    response_model=KillSwitchActionResponse,
    summary="§75 — Disable a specific rule/adapter/feature",
    tags=["admin"],
)
async def kill_feature(feature_key: str) -> KillSwitchActionResponse:
    success = disable_feature(feature_key)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown feature key: '{feature_key}'. Use GET /admin/kill-switches to list valid keys.",
        )
    return KillSwitchActionResponse(
        feature_key=feature_key,
        enabled=False,
        message=f"Feature '{feature_key}' has been disabled.",
    )


@router.post(
    "/admin/kill-switches/{feature_key}/enable",
    response_model=KillSwitchActionResponse,
    summary="§75 — Re-enable a previously disabled feature",
    tags=["admin"],
)
async def restore_feature(feature_key: str) -> KillSwitchActionResponse:
    success = enable_feature(feature_key)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown feature key: '{feature_key}'. Use GET /admin/kill-switches to list valid keys.",
        )
    return KillSwitchActionResponse(
        feature_key=feature_key,
        enabled=True,
        message=f"Feature '{feature_key}' has been re-enabled.",
    )


# ─────────────────────────────────────────────────────────────
# §82 — Community Threat Intelligence
# ─────────────────────────────────────────────────────────────

@router.get(
    "/threat-intel/patterns",
    summary="§82 — List all active community scam patterns",
    tags=["threat-intel"],
)
async def list_threat_patterns() -> dict:
    return {
        "patterns": _threat_intel.list_active_patterns(),
        "total": len(_threat_intel.list_active_patterns()),
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
    }


@router.get(
    "/threat-intel/patterns/{pattern_id}",
    summary="§82 — Get a specific scam pattern by ID",
    tags=["threat-intel"],
)
async def get_threat_pattern(pattern_id: str) -> dict:
    p = _threat_intel.get_pattern(pattern_id)
    if not p:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pattern '{pattern_id}' not found.",
        )
    return p


@router.post(
    "/threat-intel/report",
    response_model=ThreatReportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="§82 — Submit an anonymized community threat report",
    tags=["threat-intel"],
)
async def report_threat_pattern(payload: ThreatReportRequest) -> ThreatReportResponse:
    """
    Submit an anonymized pattern report.
    The domain is HMAC-hashed before storage — the raw domain is never persisted (§82).
    """
    pattern_id = _threat_intel.report_pattern(
        pattern_type=payload.pattern_type,
        geography=payload.geography,
        domain=payload.domain,
    )
    return ThreatReportResponse(
        pattern_id=pattern_id,
        message=(
            "Report recorded. Thank you for contributing to community threat intelligence. "
            "No personal data was stored."
        ),
        recorded_at=datetime.now(timezone.utc).isoformat(),
    )


# ─────────────────────────────────────────────────────────────
# §83 — Trust Trajectory
# ─────────────────────────────────────────────────────────────

@router.post(
    "/trust-trajectory",
    summary="§83 — Analyze interaction trajectory for escalating risk",
    tags=["trust-trajectory"],
)
async def analyze_trust_trajectory(payload: TrustTrajectoryRequest) -> dict:
    """
    §83: Model the change over time in an interaction — from initial contact through
    trust-building, off-platform moves, sensitive information requests, financial
    requests, and pressure tactics.

    Returns: STABLE | INCREASING_RISK | HIGH_RISK_ESCALATION
    """
    assessment = _trajectory_analyzer.analyze(
        has_initial_contact=payload.has_initial_contact,
        has_trust_building_claims=payload.has_trust_building_claims,
        has_moved_off_platform=payload.has_moved_off_platform,
        has_requested_sensitive_info=payload.has_requested_sensitive_info,
        has_payment_request=payload.has_payment_request,
        has_pressure_tactics=payload.has_pressure_tactics,
        interaction_age_days=payload.interaction_age_days,
        claimed_country=payload.claimed_country,
    )
    return {
        "assessment": trajectory_assessment_to_dict(assessment),
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
        "analyzer_version": "0.2.0",
    }

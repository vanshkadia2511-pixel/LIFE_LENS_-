"""
LifeLens Ω — Phase 8: Production SRE & Observability API Router (§70, §71, §75, §76)

Endpoints:
  GET  /api/v1/sre/health             — Deep subsystem health check & readiness probe
  GET  /api/v1/sre/adapters           — Live adapter health matrix with kill switches
  POST /api/v1/sre/sentinel/audit     — Trigger automated Sentinel quality gate audit
  GET  /api/v1/sre/sentinel/history   — Audit trail of recent Sentinel runs
  GET  /api/v1/sre/alerts/evaluate    — Live evaluation against alerts.yml rules
  POST /api/v1/sre/chaos/inject       — Controlled chaos fault injection
  POST /api/v1/sre/chaos/reset        — Clear chaos faults and trigger self-healing
  GET  /api/v1/sre/telemetry          — High-level SRE operational overview
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from ..services.sre_sentinel import sre_sentinel
from ..services.metrics import metrics_service
from ..services.versioning import list_kill_switches

router = APIRouter(prefix="/api/v1/sre", tags=["sre", "observability"])


# ─────────────────────────────────────────────────────────────
# Request / Response Schemas
# ─────────────────────────────────────────────────────────────

class ChaosInjectRequest(BaseModel):
    adapter_key: str = Field(..., description="Adapter to fault, e.g. 'companies_house', 'us_sec'")
    fault_type: str = Field(default="ERROR_SPIKE", description="Fault type, e.g. ERROR_SPIKE, LATENCY_SPIKE")
    error_rate: float = Field(default=0.60, ge=0.0, le=1.0, description="Simulated error rate (0.0 to 1.0)")
    coverage_pct: float = Field(default=0.40, ge=0.0, le=1.0, description="Simulated coverage percentage")
    data_age_hours: float = Field(default=72.0, ge=0.0, description="Simulated data freshness age in hours")


class ChaosResetRequest(BaseModel):
    adapter_key: Optional[str] = Field(default=None, description="Adapter to reset, or null for all")


# ─────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────

@router.get(
    "/health",
    summary="§70 — Deep subsystem health check & readiness probe",
    tags=["sre"],
)
async def get_deep_health() -> Dict[str, Any]:
    """
    Evaluates API Gateway, Database pool, Redis Cache, ML Models,
    Registry Adapters, and Privacy Sandbox.
    """
    return sre_sentinel.get_subsystem_health()


@router.get(
    "/adapters",
    summary="§76 — Live adapter health matrix and kill switch status",
    tags=["sre"],
)
async def get_adapters_matrix() -> Dict[str, Any]:
    """Return health status, error rates, p95 latency, and kill-switch states for all 5 registries."""
    matrix = sre_sentinel.get_adapter_health_matrix()
    return {
        "adapters": matrix,
        "total": len(matrix),
        "healthy_count": sum(1 for a in matrix if a["health_status"] == "HEALTHY"),
        "active_kill_switches": list_kill_switches(),
    }


@router.post(
    "/sentinel/audit",
    summary="§76 — Trigger automated Sentinel quality gate audit",
    tags=["sre"],
)
async def trigger_sentinel_audit() -> Dict[str, Any]:
    """
    Run full data quality gate audit.
    Automatically trips kill-switches if error rates exceed 25%.
    Automatically auto-heals and re-enables kill-switches if adapters recover.
    """
    summary = sre_sentinel.run_health_audit()
    return {
        "audit_id": summary.audit_id,
        "audited_at": summary.audited_at,
        "total_sources": summary.total_sources,
        "healthy_sources": summary.healthy_sources,
        "degraded_sources": summary.degraded_sources,
        "unavailable_sources": summary.unavailable_sources,
        "tripped_kill_switches": summary.tripped_kill_switches,
        "restored_kill_switches": summary.restored_kill_switches,
        "source_reports": summary.source_reports,
    }


@router.get(
    "/sentinel/history",
    summary="§76 — Query history of Sentinel quality audits",
    tags=["sre"],
)
async def get_sentinel_history(limit: int = 10) -> Dict[str, Any]:
    """Return recent Sentinel audit history records."""
    history = sre_sentinel.get_audit_history(limit=limit)
    return {
        "audit_history": history,
        "count": len(history),
    }


@router.get(
    "/alerts/evaluate",
    summary="§71 — Real-time evaluation against alerts.yml rules",
    tags=["sre"],
)
async def evaluate_alerts() -> Dict[str, Any]:
    """
    Directly evaluates active metrics against:
    - APIDown
    - HighErrorRate
    - HighLatency
    - DatabaseConnectionPoolExhausted
    - HighMemoryUsage
    """
    evaluations = sre_sentinel.evaluate_alert_rules()
    firing = [e for e in evaluations if e.is_firing]
    return {
        "all_rules": [
            {
                "alert_name": e.alert_name,
                "expression": e.expression,
                "is_firing": e.is_firing,
                "status": e.status,
                "measured_value": e.measured_value,
                "threshold": e.threshold,
                "summary": e.summary,
            }
            for e in evaluations
        ],
        "firing_count": len(firing),
        "firing_alerts": [e.alert_name for e in firing],
    }


@router.post(
    "/chaos/inject",
    summary="Controlled chaos engineering fault injection",
    tags=["sre"],
)
async def inject_chaos(payload: ChaosInjectRequest) -> Dict[str, Any]:
    """
    Inject synthetic fault on a registry adapter to verify graceful degradation
    and automated kill switch tripping.
    """
    try:
        return sre_sentinel.inject_chaos_fault(
            adapter_key=payload.adapter_key,
            fault_type=payload.fault_type,
            error_rate=payload.error_rate,
            coverage_pct=payload.coverage_pct,
            data_age_hours=payload.data_age_hours,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.post(
    "/chaos/reset",
    summary="Clear chaos faults and trigger self-healing",
    tags=["sre"],
)
async def reset_chaos(payload: ChaosResetRequest) -> Dict[str, Any]:
    """Clear active chaos faults and re-evaluate adapters for auto-healing."""
    return sre_sentinel.reset_chaos_faults(adapter_key=payload.adapter_key)


@router.get(
    "/telemetry",
    summary="§70 — High-level SRE operational overview",
    tags=["sre"],
)
async def get_sre_telemetry() -> Dict[str, Any]:
    """Aggregated SRE telemetry including request counts, latency percentiles, and alerts."""
    summary = metrics_service.get_summary()
    deep_health = sre_sentinel.get_subsystem_health()
    evaluations = sre_sentinel.evaluate_alert_rules()

    return {
        "status": deep_health["status"],
        "ready": deep_health["ready"],
        "uptime_seconds": deep_health["uptime_seconds"],
        "request_count": summary["request_count"],
        "success_rate": summary["verification_success_rate"],
        "latency_percentiles_ms": {
            "p50": summary["p50_latency_ms"],
            "p95": summary["p95_latency_ms"],
            "p99": summary["p99_latency_ms"],
        },
        "firing_alerts": [e.alert_name for e in evaluations if e.is_firing],
        "recent_alerts": summary["recent_alerts"],
    }

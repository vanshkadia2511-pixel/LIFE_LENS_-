"""
LifeLens Ω — Phase 3: Data Quality Gates (§76)

Before any verification source is used in production, validate:
    Coverage, Freshness, Consistency, Availability, Terms/Access, Error Behavior

If a source is degraded: source status = DEGRADED
rather than silently producing false results (§76).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class SourceHealthStatus(str, Enum):
    """Health states for a verification source."""
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"      # §76: Degraded — reduced confidence, not disabled
    UNAVAILABLE = "UNAVAILABLE"  # Source is fully down
    UNKNOWN = "UNKNOWN"        # Not yet assessed


class GateResult(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    WARN = "WARN"
    SKIP = "SKIP"  # Gate not applicable for this source


@dataclass
class DataQualityGate:
    """A single quality gate criterion (§76)."""
    gate_name: str
    result: GateResult
    measured_value: Optional[str] = None
    threshold: Optional[str] = None
    notes: str = ""
    evaluated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class SourceQualityReport:
    """
    §76: Full quality report for a verification source.

    Gates evaluated:
        1. Coverage — what % of expected entities does this source cover?
        2. Freshness — how old is the data?
        3. Consistency — does the source return consistent results?
        4. Availability — what is the uptime/error rate?
        5. Terms / Access — are automated queries permitted?
        6. Error Behavior — does it fail gracefully or silently?
    """
    source_name: str
    source_adapter: str
    health_status: SourceHealthStatus
    gates: List[DataQualityGate] = field(default_factory=list)
    overall_score: float = 0.0    # 0.0 – 1.0
    degraded_since: Optional[datetime] = None
    notes: str = ""
    evaluated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "source_name": self.source_name,
            "source_adapter": self.source_adapter,
            "health_status": self.health_status.value,
            "overall_score": self.overall_score,
            "gates": [
                {
                    "gate_name": g.gate_name,
                    "result": g.result.value,
                    "measured_value": g.measured_value,
                    "threshold": g.threshold,
                    "notes": g.notes,
                }
                for g in self.gates
            ],
            "degraded_since": self.degraded_since.isoformat() if self.degraded_since else None,
            "notes": self.notes,
            "evaluated_at": self.evaluated_at.isoformat(),
        }


class DataQualityGateEvaluator:
    """
    §76: Evaluates data quality gates for verification sources.

    Usage:
        evaluator = DataQualityGateEvaluator()
        report = evaluator.evaluate("Companies House", "companies_house", metrics)
        if report.health_status == SourceHealthStatus.DEGRADED:
            # Signal DEGRADED in the verification result, not silently fail
    """

    # Thresholds — configurable per environment
    MIN_COVERAGE_PCT = 0.60       # Source must cover ≥60% of expected entities
    MAX_FRESHNESS_HOURS = 48.0    # Data must be ≤48h old
    MIN_AVAILABILITY_PCT = 0.95   # Source must be ≥95% available
    MAX_ERROR_RATE = 0.10         # Error rate must be ≤10%

    def evaluate(
        self,
        source_name: str,
        adapter_name: str,
        *,
        coverage_pct: Optional[float] = None,
        data_age_hours: Optional[float] = None,
        availability_pct: Optional[float] = None,
        error_rate: Optional[float] = None,
        terms_allow_automation: Optional[bool] = None,
        fails_gracefully: Optional[bool] = None,
    ) -> SourceQualityReport:
        """
        Run all applicable data quality gates and produce a health report.
        """
        gates: List[DataQualityGate] = []
        fail_count = 0
        warn_count = 0

        # Gate 1: Coverage
        if coverage_pct is not None:
            result = GateResult.PASS if coverage_pct >= self.MIN_COVERAGE_PCT else GateResult.FAIL
            if result == GateResult.FAIL:
                fail_count += 1
            gates.append(DataQualityGate(
                gate_name="Coverage",
                result=result,
                measured_value=f"{coverage_pct:.0%}",
                threshold=f"≥{self.MIN_COVERAGE_PCT:.0%}",
                notes="" if result == GateResult.PASS else "Low coverage — results may be incomplete.",
            ))
        else:
            gates.append(DataQualityGate(gate_name="Coverage", result=GateResult.SKIP, notes="Not measured."))

        # Gate 2: Freshness
        if data_age_hours is not None:
            result = GateResult.PASS if data_age_hours <= self.MAX_FRESHNESS_HOURS else GateResult.WARN
            if result == GateResult.WARN:
                warn_count += 1
            gates.append(DataQualityGate(
                gate_name="Freshness",
                result=result,
                measured_value=f"{data_age_hours:.1f}h",
                threshold=f"≤{self.MAX_FRESHNESS_HOURS:.0f}h",
                notes="" if result == GateResult.PASS else "Data is stale — freshness below threshold.",
            ))
        else:
            gates.append(DataQualityGate(gate_name="Freshness", result=GateResult.SKIP, notes="Not measured."))

        # Gate 3: Consistency (simplified: measured as 1 - error_rate proxy)
        gates.append(DataQualityGate(
            gate_name="Consistency",
            result=GateResult.PASS if error_rate is None or error_rate < 0.05 else GateResult.WARN,
            notes="Consistency inferred from low error rate." if error_rate is not None else "Not measured.",
        ))
        if error_rate is not None and error_rate >= 0.05:
            warn_count += 1

        # Gate 4: Availability
        if availability_pct is not None:
            result = GateResult.PASS if availability_pct >= self.MIN_AVAILABILITY_PCT else GateResult.FAIL
            if result == GateResult.FAIL:
                fail_count += 1
            gates.append(DataQualityGate(
                gate_name="Availability",
                result=result,
                measured_value=f"{availability_pct:.1%}",
                threshold=f"≥{self.MIN_AVAILABILITY_PCT:.0%}",
                notes="" if result == GateResult.PASS else "Source availability below threshold.",
            ))
        else:
            gates.append(DataQualityGate(gate_name="Availability", result=GateResult.SKIP, notes="Not measured."))

        # Gate 5: Terms / Access
        if terms_allow_automation is not None:
            result = GateResult.PASS if terms_allow_automation else GateResult.FAIL
            if not terms_allow_automation:
                fail_count += 1
            gates.append(DataQualityGate(
                gate_name="Terms_Access",
                result=result,
                measured_value=str(terms_allow_automation),
                notes="" if terms_allow_automation else "Automated access not permitted — adapter must not query this source.",
            ))
        else:
            gates.append(DataQualityGate(gate_name="Terms_Access", result=GateResult.SKIP, notes="Not assessed."))

        # Gate 6: Error Behavior
        if fails_gracefully is not None:
            result = GateResult.PASS if fails_gracefully else GateResult.FAIL
            if not fails_gracefully:
                fail_count += 1
            gates.append(DataQualityGate(
                gate_name="Error_Behavior",
                result=result,
                notes="" if fails_gracefully else "Source does not fail gracefully — may produce silent false results.",
            ))
        else:
            gates.append(DataQualityGate(gate_name="Error_Behavior", result=GateResult.SKIP, notes="Not assessed."))

        # Determine overall health (§76)
        if fail_count >= 2:
            health = SourceHealthStatus.UNAVAILABLE
        elif fail_count == 1 or warn_count >= 2:
            health = SourceHealthStatus.DEGRADED
        elif warn_count == 1:
            health = SourceHealthStatus.DEGRADED
        else:
            health = SourceHealthStatus.HEALTHY

        passed = sum(1 for g in gates if g.result == GateResult.PASS)
        total = sum(1 for g in gates if g.result != GateResult.SKIP)
        overall_score = round(passed / total, 2) if total > 0 else 0.0

        degraded_since = datetime.now(timezone.utc) if health == SourceHealthStatus.DEGRADED else None

        report = SourceQualityReport(
            source_name=source_name,
            source_adapter=adapter_name,
            health_status=health,
            gates=gates,
            overall_score=overall_score,
            degraded_since=degraded_since,
            notes=f"{fail_count} gate(s) failed, {warn_count} warning(s).",
        )

        if health != SourceHealthStatus.HEALTHY:
            logger.warning(
                "Source quality gate: %s is %s (score=%.2f, fails=%d, warns=%d)",
                source_name, health.value, overall_score, fail_count, warn_count,
            )

        return report


# Module-level registry — tracks health of all registered sources
class SourceHealthRegistry:
    """
    Central registry tracking data quality health of all verification sources.
    Used by adapters to check if a source is healthy before querying it.
    """

    def __init__(self) -> None:
        self._reports: Dict[str, SourceQualityReport] = {}

    def register(self, report: SourceQualityReport) -> None:
        self._reports[report.source_adapter] = report

    def is_healthy(self, adapter_name: str) -> bool:
        report = self._reports.get(adapter_name)
        if not report:
            return True  # Unknown sources are allowed by default
        return report.health_status == SourceHealthStatus.HEALTHY

    def get_status(self, adapter_name: str) -> SourceHealthStatus:
        report = self._reports.get(adapter_name)
        return report.health_status if report else SourceHealthStatus.UNKNOWN

    def get_all_statuses(self) -> dict:
        return {name: r.to_dict() for name, r in self._reports.items()}


# Singleton registry
source_health_registry = SourceHealthRegistry()

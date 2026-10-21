"""
LifeLens Ω — Observability & Metrics Service (§70, §71)

Tracks:
    request_count
    verification_success_rate
    adapter_error_rate
    adapter_latency
    p50/p95/p99 latency
    risk_level_distribution
    feedback_distribution
    explanation_open_rate
    verification_path_open_rate

Alert thresholds are configurable per environment (§71).
Does NOT collect raw private content.
"""
from __future__ import annotations

import logging
import os
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────
# Environment-configurable alert thresholds (§71)
# ─────────────────────────────────────────────────────────────

ALERT_ADAPTER_ERROR_RATE = float(os.environ.get("ALERT_ADAPTER_ERROR_RATE", "0.25"))   # 25%
ALERT_P95_LATENCY_MS = float(os.environ.get("ALERT_P95_LATENCY_MS", "5000"))          # 5s
ALERT_FALSE_POSITIVE_RATE = float(os.environ.get("ALERT_FALSE_POSITIVE_RATE", "0.10")) # 10%

from prometheus_client import (
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
    CONTENT_TYPE_LATEST,
)

# Isolated custom registry for LifeLens Ω
PROMETHEUS_REGISTRY = CollectorRegistry(auto_describe=True)
PROMETHEUS_CONTENT_TYPE = CONTENT_TYPE_LATEST

# Core API telemetry metrics
PROM_REQUESTS_TOTAL = Counter(
    "lifelens_requests_total",
    "Total HTTP requests received by LifeLens API",
    ["method", "endpoint", "status_code"],
    registry=PROMETHEUS_REGISTRY,
)

PROM_REQUEST_ERRORS_TOTAL = Counter(
    "lifelens_request_errors_total",
    "Total HTTP request errors encountered",
    ["method", "endpoint", "error_type"],
    registry=PROMETHEUS_REGISTRY,
)

PROM_REQUEST_DURATION_SECONDS = Histogram(
    "lifelens_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
    registry=PROMETHEUS_REGISTRY,
)

PROM_VERIFICATIONS_TOTAL = Counter(
    "lifelens_verifications_total",
    "Total CECT job and offer verifications executed",
    ["risk_level", "success"],
    registry=PROMETHEUS_REGISTRY,
)

PROM_DB_POOL_USAGE = Gauge(
    "lifelens_db_pool_usage",
    "Database connection pool saturation ratio (0.0 to 1.0)",
    registry=PROMETHEUS_REGISTRY,
)

PROM_PROCESS_RESIDENT_MEMORY = Gauge(
    "process_resident_memory_bytes",
    "Resident memory used by LifeLens process in bytes",
    registry=PROMETHEUS_REGISTRY,
)

PROM_SERVICE_UP = Gauge(
    "lifelens_service_up",
    "Service operational state (1 = healthy, 0 = down)",
    registry=PROMETHEUS_REGISTRY,
)

PROM_ADAPTER_CALLS_TOTAL = Counter(
    "lifelens_adapter_calls_total",
    "Total registry adapter invocations",
    ["adapter", "status"],
    registry=PROMETHEUS_REGISTRY,
)

PROM_ADAPTER_DURATION_SECONDS = Histogram(
    "lifelens_adapter_duration_seconds",
    "Registry adapter execution latency in seconds",
    ["adapter"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0),
    registry=PROMETHEUS_REGISTRY,
)

PROM_ADAPTER_HEALTH = Gauge(
    "lifelens_adapter_health",
    "Adapter operational health score (1.0 = Healthy, 0.5 = Degraded, 0.0 = Unavailable)",
    ["adapter"],
    registry=PROMETHEUS_REGISTRY,
)

PROM_KILL_SWITCH_ACTIVE = Gauge(
    "lifelens_kill_switch_active",
    "Status of LifeLens runtime kill switches (1.0 = Active/Enabled, 0.0 = Disabled)",
    ["feature_key"],
    registry=PROMETHEUS_REGISTRY,
)

# Initialize default states
PROM_SERVICE_UP.set(1.0)
PROM_DB_POOL_USAGE.set(0.12)  # nominal 12% baseline
PROM_PROCESS_RESIDENT_MEMORY.set(128 * 1024 * 1024)  # nominal 128 MB baseline



@dataclass
class AdapterMetrics:
    """Per-adapter telemetry."""
    adapter_name: str
    call_count: int = 0
    error_count: int = 0
    latencies_ms: List[float] = field(default_factory=list)

    def record_call(self, latency_ms: float, success: bool) -> None:
        self.call_count += 1
        self.latencies_ms.append(latency_ms)
        if not success:
            self.error_count += 1

    @property
    def error_rate(self) -> float:
        if self.call_count == 0:
            return 0.0
        return round(self.error_count / self.call_count, 4)

    def percentile(self, p: int) -> float:
        """Compute a latency percentile. p ∈ {50, 95, 99}."""
        if not self.latencies_ms:
            return 0.0
        sorted_lat = sorted(self.latencies_ms)
        idx = max(0, int(len(sorted_lat) * p / 100) - 1)
        return round(sorted_lat[idx], 2)

    def to_dict(self) -> dict:
        return {
            "adapter_name": self.adapter_name,
            "call_count": self.call_count,
            "error_count": self.error_count,
            "error_rate": self.error_rate,
            "p50_latency_ms": self.percentile(50),
            "p95_latency_ms": self.percentile(95),
            "p99_latency_ms": self.percentile(99),
        }


class MetricsService:
    """
    §70 — In-process observability store.
    Tracks aggregate metrics without persisting raw private content.
    """

    def __init__(self) -> None:
        self.request_count: int = 0
        self.verification_success_count: int = 0
        self.verification_failure_count: int = 0
        self.risk_level_distribution: Dict[str, int] = defaultdict(int)
        self.feedback_distribution: Dict[str, int] = defaultdict(int)
        self.explanation_open_count: int = 0
        self.verification_path_open_count: int = 0
        self._all_latencies_ms: List[float] = []
        self._adapter_metrics: Dict[str, AdapterMetrics] = {}
        self._alerts: List[dict] = []

    # ------------------------------------------------------------------
    # Recording methods
    # ------------------------------------------------------------------

    def record_request(self, risk_level: str, latency_ms: float, success: bool) -> None:
        """Record a completed verification request."""
        self.request_count += 1
        self._all_latencies_ms.append(latency_ms)
        if success:
            self.verification_success_count += 1
        else:
            self.verification_failure_count += 1
        self.risk_level_distribution[risk_level.upper()] += 1
        self._check_latency_alerts(latency_ms)
        try:
            PROM_VERIFICATIONS_TOTAL.labels(
                risk_level=risk_level.upper(),
                success=str(success).lower(),
            ).inc()
        except Exception:
            pass

    def record_adapter_call(self, adapter_name: str, latency_ms: float, success: bool) -> None:
        """Record a single adapter call."""
        if adapter_name not in self._adapter_metrics:
            self._adapter_metrics[adapter_name] = AdapterMetrics(adapter_name=adapter_name)
        self._adapter_metrics[adapter_name].record_call(latency_ms, success)
        self._check_adapter_error_alerts(adapter_name)
        try:
            PROM_ADAPTER_CALLS_TOTAL.labels(
                adapter=adapter_name,
                status="success" if success else "error",
            ).inc()
            PROM_ADAPTER_DURATION_SECONDS.labels(
                adapter=adapter_name,
            ).observe(max(0.0001, latency_ms / 1000.0))
        except Exception:
            pass

    def record_http_request(
        self,
        method: str,
        endpoint: str,
        status_code: int,
        duration_seconds: float,
    ) -> None:
        """Record HTTP request timing and status into Prometheus telemetry."""
        norm_method = method.upper()
        norm_endpoint = endpoint or "/"
        try:
            PROM_REQUESTS_TOTAL.labels(
                method=norm_method,
                endpoint=norm_endpoint,
                status_code=str(status_code),
            ).inc()
            PROM_REQUEST_DURATION_SECONDS.labels(
                method=norm_method,
                endpoint=norm_endpoint,
            ).observe(max(0.0001, duration_seconds))
            if status_code >= 400:
                PROM_REQUEST_ERRORS_TOTAL.labels(
                    method=norm_method,
                    endpoint=norm_endpoint,
                    error_type=f"HTTP_{status_code}",
                ).inc()
        except Exception as exc:
            logger.debug("Failed recording prometheus http request: %s", exc)

    def record_http_error(self, method: str, endpoint: str, error_type: str) -> None:
        """Record an unhandled exception or critical error."""
        try:
            PROM_REQUEST_ERRORS_TOTAL.labels(
                method=method.upper(),
                endpoint=endpoint or "/",
                error_type=error_type,
            ).inc()
        except Exception:
            pass

    def set_db_pool_usage(self, ratio: float) -> None:
        """Update DB pool connection ratio (0.0 to 1.0)."""
        PROM_DB_POOL_USAGE.set(max(0.0, min(1.0, float(ratio))))

    def set_memory_bytes(self, bytes_val: float) -> None:
        """Update resident memory usage."""
        PROM_PROCESS_RESIDENT_MEMORY.set(float(bytes_val))

    def set_adapter_health(self, adapter_name: str, score: float) -> None:
        """Update adapter health gauge (1.0 = healthy, 0.5 = degraded, 0.0 = unavailable)."""
        PROM_ADAPTER_HEALTH.labels(adapter=adapter_name).set(float(score))

    def set_kill_switch_metric(self, feature_key: str, active: bool) -> None:
        """Update kill switch state gauge."""
        PROM_KILL_SWITCH_ACTIVE.labels(feature_key=feature_key).set(1.0 if active else 0.0)

    def record_feedback(self, feedback_type: str) -> None:
        """Track user feedback distribution (§70)."""
        self.feedback_distribution[feedback_type.upper()] += 1

    def record_explanation_opened(self) -> None:
        self.explanation_open_count += 1

    def record_verification_path_opened(self) -> None:
        self.verification_path_open_count += 1

    # ------------------------------------------------------------------
    # Alert checking (§71)
    # ------------------------------------------------------------------

    def _check_adapter_error_alerts(self, adapter_name: str) -> None:
        """§71: Alert if adapter_error_rate > threshold."""
        m = self._adapter_metrics[adapter_name]
        if m.call_count >= 5 and m.error_rate > ALERT_ADAPTER_ERROR_RATE:
            self._raise_alert(
                level="WARNING",
                component=f"adapter.{adapter_name}",
                message=f"Adapter error rate {m.error_rate:.1%} exceeds threshold {ALERT_ADAPTER_ERROR_RATE:.1%}.",
            )

    def _check_latency_alerts(self, latency_ms: float) -> None:
        """§71: Alert if recent p95 latency exceeds threshold."""
        recent = self._all_latencies_ms[-100:]  # last 100 requests
        if len(recent) >= 20:
            sorted_lat = sorted(recent)
            p95 = sorted_lat[int(len(sorted_lat) * 0.95) - 1]
            if p95 > ALERT_P95_LATENCY_MS:
                self._raise_alert(
                    level="WARNING",
                    component="api.latency",
                    message=f"p95 latency {p95:.0f}ms exceeds threshold {ALERT_P95_LATENCY_MS:.0f}ms.",
                )

    def _raise_alert(self, level: str, component: str, message: str) -> None:
        """Record an alert. In production, this would call PagerDuty / Slack / etc."""
        alert = {
            "level": level,
            "component": component,
            "message": message,
            "raised_at": datetime.now(timezone.utc).isoformat(),
        }
        self._alerts.append(alert)
        logger.warning("[ALERT] %s — %s: %s", level, component, message)

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------

    def get_summary(self) -> dict:
        """§70: Return full telemetry summary."""
        total = self.request_count or 1  # avoid zero div
        success_rate = round(self.verification_success_count / total, 4)

        def percentile(lats: List[float], p: int) -> float:
            if not lats:
                return 0.0
            s = sorted(lats)
            return round(s[max(0, int(len(s) * p / 100) - 1)], 2)

        return {
            "request_count": self.request_count,
            "verification_success_rate": success_rate,
            "p50_latency_ms": percentile(self._all_latencies_ms, 50),
            "p95_latency_ms": percentile(self._all_latencies_ms, 95),
            "p99_latency_ms": percentile(self._all_latencies_ms, 99),
            "risk_level_distribution": dict(self.risk_level_distribution),
            "feedback_distribution": dict(self.feedback_distribution),
            "explanation_open_count": self.explanation_open_count,
            "verification_path_open_count": self.verification_path_open_count,
            "adapters": {name: m.to_dict() for name, m in self._adapter_metrics.items()},
            "recent_alerts": self._alerts[-10:],
        }

    def get_recent_alerts(self) -> List[dict]:
        return list(self._alerts[-20:])


# Module-level singleton — shared across the process
metrics_service = MetricsService()


def generate_prometheus_metrics() -> str:
    """Generate official Prometheus scrape text from the LifeLens registry."""
    return generate_latest(PROMETHEUS_REGISTRY).decode("utf-8")


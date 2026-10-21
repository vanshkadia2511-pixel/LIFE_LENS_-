"""
LifeLens Ω — Phase 8: Production Industrialization, Observability & Runtime SRE Test Suite
Evolved Blueprint Phase 8 (Months 25-26, §70–§76)

Tests:
1. Prometheus Scrape Exposition (/metrics) format validation matching prometheus.yml
2. Request Timing & Error Capture Middleware telemetry tracking
3. Deep Multi-Subsystem Health & Readiness Probes (/api/v1/sre/health)
4. Registry Quality Gates Health Matrix & Kill Switch Synchronization (/api/v1/sre/adapters)
5. Automated SRE Sentinel Quality Audit (/api/v1/sre/sentinel/audit)
6. Chaos Fault Injection & Automatic Circuit-Breaker Kill-Switch Tripping & Self-Healing
7. Prometheus Alert Rule Evaluator testing against alerts.yml definitions
8. SRE Telemetry & Operational Overview Endpoint (/api/v1/sre/telemetry)
9. Official Python Developer SDK SRE & Observability Integration
"""
import time
import pytest
from fastapi.testclient import TestClient

from apps.api.app.main import app
from apps.api.app.services.metrics import (
    metrics_service,
    generate_prometheus_metrics,
    PROMETHEUS_REGISTRY,
)
from apps.api.app.services.sre_sentinel import sre_sentinel, SubsystemStatus
from apps.api.app.services.versioning import is_feature_enabled, enable_feature
from src.sdk.client import LifeLensClient


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


class TestPrometheusMetricsExposition:
    """Tests for Prometheus /metrics scrape endpoint matching prometheus.yml."""

    def test_metrics_endpoint_returns_prometheus_format(self, client):
        resp = client.get("/metrics")
        assert resp.status_code == 200
        text = resp.text

        # Verify standard Prometheus header definitions
        assert "lifelens_requests_total" in text
        assert "lifelens_request_duration_seconds" in text
        assert "lifelens_service_up" in text
        assert "lifelens_db_pool_usage" in text
        assert "process_resident_memory_bytes" in text

    def test_middleware_tracks_requests_and_errors(self, client):
        # Fire requests to test middleware tracking
        client.get("/health")
        client.get("/api/v1/health")
        client.get("/nonexistent-endpoint-404")

        text = client.get("/metrics").text
        # Assert normalized path labeling and status codes
        assert 'endpoint="/health"' in text
        assert 'status_code="200"' in text
        assert "lifelens_request_errors_total" in text
        assert 'error_type="HTTP_404"' in text


class TestDeepSubsystemHealthAndReadiness:
    """Tests for deep subsystem health & readiness probes (/api/v1/sre/health)."""

    def test_sre_health_probe_structure(self, client):
        resp = client.get("/api/v1/sre/health")
        assert resp.status_code == 200
        data = resp.json()

        assert "status" in data
        assert data["status"] in ["HEALTHY", "DEGRADED"]
        assert data["ready"] is True
        assert data["uptime_seconds"] >= 0.0

        subsystems = {s["name"]: s for s in data["subsystems"]}
        expected = [
            "api_gateway",
            "database",
            "redis_cache",
            "ml_inference_engines",
            "registry_adapters",
            "federated_privacy_sandbox",
        ]
        for name in expected:
            assert name in subsystems
            assert subsystems[name]["status"] in ["HEALTHY", "DEGRADED"]
            assert subsystems[name]["latency_ms"] >= 0.0


class TestRegistryAdaptersAndQualityGates:
    """Tests for registry health matrix and kill switch synchronization (/api/v1/sre/adapters)."""

    def test_adapter_health_matrix_reports_all_registries(self, client):
        resp = client.get("/api/v1/sre/adapters")
        assert resp.status_code == 200
        data = resp.json()

        assert data["total"] == 5
        adapter_keys = [a["adapter_key"] for a in data["adapters"]]
        assert "companies_house" in adapter_keys
        assert "us_sec" in adapter_keys
        assert "india_mca" in adapter_keys
        assert "uae_ner" in adapter_keys
        assert "domain" in adapter_keys

        for a in data["adapters"]:
            assert a["health_status"] in ["HEALTHY", "DEGRADED", "UNAVAILABLE", "UNKNOWN"]
            assert "kill_switch_enabled" in a
            assert "error_rate" in a
            assert "p95_latency_ms" in a


class TestSRESentinelAuditAndCircuitTripping:
    """Tests for automated quality gate audits and self-healing circuit breakers (§71, §75, §76)."""

    def test_sentinel_audit_run_and_history(self, client):
        resp = client.post("/api/v1/sre/sentinel/audit")
        assert resp.status_code == 200
        data = resp.json()

        assert "audit_id" in data
        assert data["total_sources"] == 5
        assert data["healthy_sources"] >= 4
        assert "tripped_kill_switches" in data
        assert "source_reports" in data

        # Check history endpoint
        hist_resp = client.get("/api/v1/sre/sentinel/history")
        assert hist_resp.status_code == 200
        hist_data = hist_resp.json()
        assert hist_data["count"] > 0
        assert any(a["audit_id"] == data["audit_id"] for a in hist_data["audit_history"])

    def test_chaos_fault_injection_trips_kill_switch_and_auto_recovers(self, client):
        target_adapter = "companies_house"
        feature_key = f"adapter.{target_adapter}"

        # Ensure starting in enabled state
        enable_feature(feature_key)
        assert is_feature_enabled(feature_key) is True

        # 1. Inject fault: 70% error rate (exceeds ALERT_ADAPTER_ERROR_RATE = 25%)
        inject_payload = {
            "adapter_key": target_adapter,
            "fault_type": "ERROR_SPIKE",
            "error_rate": 0.70,
            "coverage_pct": 0.35,
            "data_age_hours": 96.0,
        }
        inj_resp = client.post("/api/v1/sre/chaos/inject", json=inject_payload)
        assert inj_resp.status_code == 200
        inj_data = inj_resp.json()

        # Sentinel audit ran and automatically tripped the kill-switch!
        assert feature_key in inj_data["sentinel_audit"]["tripped_kill_switches"]
        assert is_feature_enabled(feature_key) is False

        # Verify adapter is marked DEGRADED / UNAVAILABLE in matrix
        mat_resp = client.get("/api/v1/sre/adapters")
        adapter_entry = next(
            a for a in mat_resp.json()["adapters"] if a["adapter_key"] == target_adapter
        )
        assert adapter_entry["kill_switch_enabled"] is False
        assert adapter_entry["chaos_simulated"] is True

        # 2. Reset chaos fault and verify Sentinel auto-heals and re-enables adapter
        reset_resp = client.post("/api/v1/sre/chaos/reset", json={"adapter_key": target_adapter})
        assert reset_resp.status_code == 200
        reset_data = reset_resp.json()

        assert feature_key in reset_data["sentinel_audit"]["restored_kill_switches"]
        assert is_feature_enabled(feature_key) is True

        # Verify clean restored status
        mat_restored = client.get("/api/v1/sre/adapters")
        restored_entry = next(
            a for a in mat_restored.json()["adapters"] if a["adapter_key"] == target_adapter
        )
        assert restored_entry["kill_switch_enabled"] is True
        assert restored_entry["chaos_simulated"] is False


class TestPrometheusAlertRulesEvaluation:
    """Tests evaluating live telemetry against alerts.yml rules."""

    def test_evaluate_alerts_against_rules(self, client):
        resp = client.get("/api/v1/sre/alerts/evaluate")
        assert resp.status_code == 200
        data = resp.json()

        rule_names = [r["alert_name"] for r in data["all_rules"]]
        assert "APIDown" in rule_names
        assert "HighErrorRate" in rule_names
        assert "HighLatency" in rule_names
        assert "DatabaseConnectionPoolExhausted" in rule_names
        assert "HighMemoryUsage" in rule_names

        # In normal baseline conditions, APIDown is not firing
        api_down_rule = next(r for r in data["all_rules"] if r["alert_name"] == "APIDown")
        assert api_down_rule["is_firing"] is False
        assert api_down_rule["status"] == "OK"


class TestSRETelemetryAndSDK:
    """Tests for SRE telemetry overview and Python SDK integration."""

    def test_sre_telemetry_overview_endpoint(self, client):
        resp = client.get("/api/v1/sre/telemetry")
        assert resp.status_code == 200
        data = resp.json()

        assert "status" in data
        assert "ready" in data
        assert "request_count" in data
        assert "latency_percentiles_ms" in data
        assert "p95" in data["latency_percentiles_ms"]

    def test_python_sdk_sre_methods_integration(self):
        # Wire Python Developer SDK using test client transport
        sdk_client = LifeLensClient(api_key="ll_live_test_sre_key", base_url="http://testserver")
        with TestClient(app) as tc:
            sdk_client.client = tc

            # 1. Prometheus scrape text
            metrics_txt = sdk_client.get_metrics()
            assert "lifelens_requests_total" in metrics_txt

            # 2. Subsystem health
            deep_health = sdk_client.get_sre_health()
            assert deep_health["ready"] is True

            # 3. Adapters matrix
            adapters = sdk_client.get_sre_adapters()
            assert adapters["total"] == 5

            # 4. Sentinel audit
            audit_res = sdk_client.run_sentinel_audit()
            assert "audit_id" in audit_res

            # 5. Alert rules evaluation
            alerts_res = sdk_client.evaluate_alerts()
            assert "all_rules" in alerts_res

            # 6. Chaos injection and reset
            inj_res = sdk_client.inject_chaos("domain", fault_type="ERROR_SPIKE", error_rate=0.75)
            assert "Chaos fault" in inj_res["message"]
            reset_res = sdk_client.reset_chaos("domain")
            assert "cleared" in reset_res["message"]

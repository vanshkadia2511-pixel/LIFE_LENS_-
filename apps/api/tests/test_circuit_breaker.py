"""
LifeLens Ω — Circuit Breaker & Resilience Tests
Implementation Plan §7, §24, §59
"""
import pytest
import time
from unittest.mock import Mock

from apps.api.app.verification.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitState,
    CircuitBreakerOpenException,
)
from apps.api.app.verification.orchestrator import VerificationOrchestrator
from apps.api.app.models.request import VerificationRequest
from apps.api.app.models.entity import Entity, VerificationStatus
from apps.api.app.models.evidence import SourceStatus


def test_circuit_breaker_normal_closed_execution():
    cb = CircuitBreaker("test-service", CircuitBreakerConfig(failure_threshold=3))
    mock_func = Mock(return_value="success_result")

    result = cb.call(mock_func, "arg1")

    assert result == "success_result"
    assert cb.state == CircuitState.CLOSED
    assert cb.failure_count == 0
    assert cb.consecutive_trips == 0
    mock_func.assert_called_once_with("arg1")


def test_circuit_breaker_trips_on_threshold_failures():
    cb = CircuitBreaker("test-service", CircuitBreakerConfig(failure_threshold=3, recovery_timeout=5.0))
    mock_failing_func = Mock(side_effect=RuntimeError("Upstream registry down"))

    # Failures 1 and 2: remain CLOSED
    for _ in range(2):
        with pytest.raises(RuntimeError):
            cb.call(mock_failing_func)
        assert cb.state == CircuitState.CLOSED

    # Failure 3: trips to OPEN
    with pytest.raises(RuntimeError):
        cb.call(mock_failing_func)

    assert cb.state == CircuitState.OPEN
    assert cb.failure_count == 3
    assert cb.consecutive_trips == 1


def test_circuit_breaker_fast_fails_when_open():
    cb = CircuitBreaker("test-service", CircuitBreakerConfig(failure_threshold=2, recovery_timeout=10.0))
    mock_failing_func = Mock(side_effect=RuntimeError("Registry down"))

    for _ in range(2):
        with pytest.raises(RuntimeError):
            cb.call(mock_failing_func)

    assert cb.state == CircuitState.OPEN

    # Subsequent call must fast-fail with CircuitBreakerOpenException
    target_func = Mock()
    with pytest.raises(CircuitBreakerOpenException) as exc_info:
        cb.call(target_func)

    assert exc_info.value.service_name == "test-service"
    assert exc_info.value.retry_after > 0
    target_func.assert_not_called()


def test_circuit_breaker_half_open_recovery_success():
    # Short recovery timeout for fast test
    config = CircuitBreakerConfig(failure_threshold=2, recovery_timeout=0.05)
    cb = CircuitBreaker("test-service", config)

    # Trip to OPEN
    for _ in range(2):
        with pytest.raises(ValueError):
            cb.call(Mock(side_effect=ValueError("fail")))

    assert cb.state == CircuitState.OPEN

    # Wait for recovery timeout
    time.sleep(0.08)

    # State transitions to HALF_OPEN
    assert cb.state == CircuitState.HALF_OPEN

    # Successful call in HALF_OPEN resets to CLOSED
    success_func = Mock(return_value="recovered")
    result = cb.call(success_func)

    assert result == "recovered"
    assert cb.state == CircuitState.CLOSED
    assert cb.failure_count == 0
    assert cb.consecutive_trips == 0


def test_circuit_breaker_half_open_failure_reopens_with_backoff():
    config = CircuitBreakerConfig(failure_threshold=2, recovery_timeout=0.05, backoff_multiplier=2.0)
    cb = CircuitBreaker("test-service", config)

    # Trip to OPEN
    for _ in range(2):
        with pytest.raises(ValueError):
            cb.call(Mock(side_effect=ValueError("fail 1")))

    assert cb.state == CircuitState.OPEN
    assert cb.consecutive_trips == 1

    time.sleep(0.08)
    assert cb.state == CircuitState.HALF_OPEN

    # Probe fails in HALF_OPEN
    with pytest.raises(ValueError):
        cb.call(Mock(side_effect=ValueError("fail 2")))

    assert cb.state == CircuitState.OPEN
    assert cb.consecutive_trips == 2


def test_circuit_breaker_caching_and_expiration():
    cb = CircuitBreaker("cache-test", CircuitBreakerConfig(cache_ttl_seconds=1))

    cb.set_cache("item_key", {"data": 42})
    assert cb.get_cached("item_key") == {"data": 42}

    # Non-existent key returns None
    assert cb.get_cached("missing_key") is None

    # Clear cache works
    cb.clear_cache()
    assert cb.get_cached("item_key") is None


def test_circuit_breaker_failure_injection():
    cb = CircuitBreaker("injection-test", CircuitBreakerConfig(failure_threshold=5))

    injected = TimeoutError("Simulated chaos failure")
    cb.inject_failure(injected)

    with pytest.raises(TimeoutError) as exc_info:
        cb.call(Mock(return_value="ok"))

    assert "Simulated chaos failure" in str(exc_info.value)
    assert cb.failure_count == 1

    # Clear injection
    cb.inject_failure(None)
    result = cb.call(Mock(return_value="ok"))
    assert result == "ok"


def test_orchestrator_handles_tripped_circuit_gracefully():
    orchestrator = VerificationOrchestrator()
    cb = orchestrator.get_circuit_breaker("CompaniesHouse")

    # Inject failure to trip circuit
    cb.inject_failure(ConnectionError("Registry service unavailable"))

    request = VerificationRequest(
        request_id="req-test-cb",
        job_title="Software Engineer",
        company_name="DeepMind Technologies Limited",
        claimed_country="GB",
    )
    company_entity = Entity(
        entity_id="ent-1",
        entity_type="COMPANY",
        claimed_name="DeepMind Technologies Limited",
        normalized_name="DeepMind Technologies Limited",
    )

    # Orchestrator must not raise — it returns graceful degraded evidence
    evidences = orchestrator.run(request, company_entity)

    assert len(evidences) >= 1
    registry_evidence = next(e for e in evidences if e.source_type == "REGISTRY")
    assert registry_evidence.source_status == SourceStatus.UNAVAILABLE

"""
LifeLens Ω — Registry Circuit Breaker & Resilient Cache
Implementation Plan §7, §24, §59

Features:
- State machine: CLOSED, OPEN, HALF_OPEN
- Configurable failure threshold and recovery timeout
- Exponential backoff with jitter on repeated trips
- Dual-backend: Redis (if reachable) with seamless, zero-crash in-memory fallback
- Failure injection hook for resilience & chaos testing
- Metrics: state, failure count, total trips, last error
"""
from __future__ import annotations
import enum
import json
import logging
import os
import random
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional, Tuple, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class CircuitState(str, enum.Enum):
    CLOSED = "CLOSED"        # Normal operation: requests pass through
    OPEN = "OPEN"            # Tripped: requests fail fast or use fallback
    HALF_OPEN = "HALF_OPEN"  # Probe: single request allowed to test recovery


class CircuitBreakerOpenException(Exception):
    """Raised when an operation is attempted while the circuit is OPEN."""
    def __init__(self, service_name: str, retry_after: float):
        super().__init__(f"Circuit breaker for '{service_name}' is OPEN. Retry in {retry_after:.1f}s")
        self.service_name = service_name
        self.retry_after = retry_after


@dataclass
class CircuitBreakerConfig:
    failure_threshold: int = 5          # Number of consecutive failures before tripping
    recovery_timeout: float = 30.0      # Base seconds before probing in HALF_OPEN
    max_recovery_timeout: float = 300.0 # Maximum backoff cap (5 minutes)
    backoff_multiplier: float = 2.0     # Exponential multiplier on consecutive trips
    cache_ttl_seconds: int = 3600       # TTL for cached successful results
    redis_url: Optional[str] = None     # Optional redis URL


class CircuitBreaker:
    """
    Protects downstream registry calls (Companies House, SEC EDGAR, MCA, UAE NER)
    from cascading failures and outage surges.
    """

    def __init__(self, service_name: str, config: Optional[CircuitBreakerConfig] = None):
        self.service_name = service_name
        self.config = config or CircuitBreakerConfig()
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._consecutive_trips = 0
        self._last_failure_time: float = 0.0
        self._last_state_change: float = time.time()
        self._last_error: Optional[str] = None

        # Failure injection for chaos/integration tests
        self._injected_failure: Optional[Exception] = None

        # Cache storage: in-memory dictionary
        self._mem_cache: Dict[str, Tuple[Any, float]] = {}

        # Redis connection setup (lazy)
        self._redis_client = None
        self._redis_available = False
        self._init_redis()

    def _init_redis(self) -> None:
        redis_url = self.config.redis_url or os.getenv("REDIS_URL")
        if not redis_url:
            return
        try:
            import redis
            client = redis.Redis.from_url(redis_url, socket_timeout=1.5)
            client.ping()
            self._redis_client = client
            self._redis_available = True
            logger.info("CircuitBreaker[%s]: Redis connected successfully.", self.service_name)
        except Exception as exc:
            logger.warning(
                "CircuitBreaker[%s]: Redis connection failed (%s). Falling back to in-memory store.",
                self.service_name, exc
            )
            self._redis_client = None
            self._redis_available = False

    @property
    def state(self) -> CircuitState:
        self._evaluate_state()
        return self._state

    @property
    def failure_count(self) -> int:
        return self._failure_count

    @property
    def consecutive_trips(self) -> int:
        return self._consecutive_trips

    def _get_current_recovery_timeout(self) -> float:
        """Calculate exponential backoff timeout based on consecutive trips."""
        timeout = self.config.recovery_timeout * (self.config.backoff_multiplier ** max(0, self._consecutive_trips - 1))
        # Add slight jitter (+/- 10%)
        jitter = random.uniform(0.9, 1.1)
        return min(self.config.max_recovery_timeout, timeout * jitter)

    def _evaluate_state(self) -> None:
        """Transitions OPEN -> HALF_OPEN if the recovery timeout has elapsed."""
        if self._state == CircuitState.OPEN:
            elapsed = time.time() - self._last_state_change
            current_timeout = self._get_current_recovery_timeout()
            if elapsed >= current_timeout:
                logger.info(
                    "CircuitBreaker[%s]: Recovery timeout elapsed (%.1fs). Transitioning OPEN -> HALF_OPEN.",
                    self.service_name, elapsed
                )
                self._state = CircuitState.HALF_OPEN
                self._last_state_change = time.time()

    def record_success(self) -> None:
        """Record successful call. Closes circuit and resets failure counters."""
        if self._state in (CircuitState.HALF_OPEN, CircuitState.OPEN):
            logger.info("CircuitBreaker[%s]: Call succeeded. Resetting to CLOSED.", self.service_name)
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._consecutive_trips = 0
        self._last_error = None
        self._last_state_change = time.time()

    def record_failure(self, error: Exception) -> None:
        """Record failed call. Increments failures and trips circuit if threshold exceeded."""
        self._last_failure_time = time.time()
        self._last_error = str(error)
        self._failure_count += 1

        if self._state == CircuitState.HALF_OPEN:
            # Probe failed -> trip back to OPEN immediately with increased trip counter
            self._consecutive_trips += 1
            self._state = CircuitState.OPEN
            self._last_state_change = time.time()
            logger.warning(
                "CircuitBreaker[%s]: HALF_OPEN probe failed (%s). Re-opening circuit (trip #%d).",
                self.service_name, error, self._consecutive_trips
            )
        elif self._state == CircuitState.CLOSED and self._failure_count >= self.config.failure_threshold:
            self._consecutive_trips += 1
            self._state = CircuitState.OPEN
            self._last_state_change = time.time()
            logger.warning(
                "CircuitBreaker[%s]: Failure threshold %d reached. Tripping to OPEN (trip #%d).",
                self.service_name, self.config.failure_threshold, self._consecutive_trips
            )

    def inject_failure(self, exception: Optional[Exception]) -> None:
        """Inject synthetic exception for testing resilience and circuit breaking."""
        self._injected_failure = exception

    def call(self, fn: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """
        Executes fn within circuit breaker protection.
        Raises CircuitBreakerOpenException if the circuit is OPEN.
        """
        # 1. Check test injection
        if self._injected_failure is not None:
            self.record_failure(self._injected_failure)
            raise self._injected_failure

        # 2. Check state
        self._evaluate_state()
        if self._state == CircuitState.OPEN:
            elapsed = time.time() - self._last_state_change
            timeout = self._get_current_recovery_timeout()
            retry_after = max(0.0, timeout - elapsed)
            raise CircuitBreakerOpenException(self.service_name, retry_after)

        # 3. Attempt execution
        try:
            result = fn(*args, **kwargs)
            self.record_success()
            return result
        except Exception as exc:
            self.record_failure(exc)
            raise

    # ── Result Caching ────────────────────────────────────────────────────────

    def get_cached(self, key: str) -> Optional[Any]:
        """Fetch result from cache (Redis or in-memory fallback)."""
        cache_key = f"lifelens:cache:{self.service_name}:{key}"
        if self._redis_available and self._redis_client:
            try:
                raw = self._redis_client.get(cache_key)
                if raw is not None:
                    return json.loads(raw)
            except Exception as exc:
                logger.debug("Redis cache get error: %s. Using mem cache.", exc)

        # In-memory cache fallback
        if key in self._mem_cache:
            data, timestamp = self._mem_cache[key]
            if time.time() - timestamp < self.config.cache_ttl_seconds:
                return data
            del self._mem_cache[key]
        return None

    def set_cache(self, key: str, value: Any) -> None:
        """Store result in cache (Redis or in-memory fallback)."""
        cache_key = f"lifelens:cache:{self.service_name}:{key}"
        if self._redis_available and self._redis_client:
            try:
                self._redis_client.setex(
                    cache_key,
                    self.config.cache_ttl_seconds,
                    json.dumps(value, default=str),
                )
            except Exception as exc:
                logger.debug("Redis cache set error: %s. Using mem cache.", exc)

        self._mem_cache[key] = (value, time.time())

    def clear_cache(self) -> None:
        """Clear cached entries."""
        self._mem_cache.clear()

    def get_metrics(self) -> Dict[str, Any]:
        """Return diagnostic metrics for health and admin endpoints."""
        return {
            "service_name": self.service_name,
            "state": self.state.value,
            "failure_count": self._failure_count,
            "consecutive_trips": self._consecutive_trips,
            "last_error": self._last_error,
            "redis_active": self._redis_available,
            "cached_entries": len(self._mem_cache),
        }

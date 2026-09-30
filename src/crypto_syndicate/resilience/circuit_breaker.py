"""Hystrix-Style 3-State Circuit Breaker Pattern for On-Chain APIs.

Prevents cascading timeouts and thread exhaustion by failing fast (0ms)
when an external API (Solscan, GMGN, RPC) is down, rate-limited, or unauthorized.
"""

import time
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger("crypto_syndicate.resilience.circuit_breaker")


class CircuitBreakerOpenError(Exception):
    """Raised when an execution is attempted on an OPEN circuit."""
    pass


class CircuitBreaker:
    """Three-State Circuit Breaker: CLOSED -> OPEN -> HALF_OPEN."""

    def __init__(
        self,
        name: str,
        failure_threshold: int = 3,
        recovery_timeout: float = 30.0,
    ) -> None:
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout

        self.state: str = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self.failure_count: int = 0
        self.success_count: int = 0
        self.last_failure_time: float = 0.0
        self.last_state_change: float = time.time()
        self.total_trips: int = 0

    def can_execute(self) -> bool:
        """Check if request can proceed or must fail fast."""
        now = time.time()
        if self.state == "CLOSED":
            return True

        if self.state == "OPEN":
            if now - self.last_state_change >= self.recovery_timeout:
                self.state = "HALF_OPEN"
                self.last_state_change = now
                logger.info("Circuit [%s] entering HALF_OPEN (canary probe allowed)", self.name)
                return True
            return False

        if self.state == "HALF_OPEN":
            # Allow single canary request
            return True

        return True

    def record_success(self) -> None:
        """Record successful call; heals circuit back to CLOSED."""
        if self.state in ("HALF_OPEN", "OPEN"):
            logger.info("Circuit [%s] RECOVERED: Resetting to CLOSED", self.name)
        self.failure_count = 0
        self.success_count += 1
        self.state = "CLOSED"
        self.last_state_change = time.time()

    def record_failure(self, exc: Optional[Exception] = None) -> None:
        """Record failure; trips circuit to OPEN if threshold exceeded."""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.state == "HALF_OPEN":
            # Canary failed -> trip immediately back to OPEN with doubled recovery window
            self.state = "OPEN"
            self.last_state_change = time.time()
            self.total_trips += 1
            logger.warning(
                "Circuit [%s] canary failed (%s). Trip to OPEN for %.1fs",
                self.name, exc, self.recovery_timeout
            )
        elif self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            self.last_state_change = time.time()
            self.total_trips += 1
            logger.error(
                "Circuit [%s] TRIPPED to OPEN after %d consecutive failures. Fail fast for %.1fs (Last error: %s)",
                self.name, self.failure_count, self.recovery_timeout, exc
            )

    def status(self) -> Dict[str, Any]:
        """Return real-time circuit health telemetry."""
        return {
            "name": self.name,
            "state": self.state,
            "failures": self.failure_count,
            "successes": self.success_count,
            "trips": self.total_trips,
            "is_available": self.can_execute(),
            "time_in_state_s": round(time.time() - self.last_state_change, 1),
        }

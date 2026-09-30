"""High-precision, thread-safe Token Bucket rate limiter for API requests.

Configured for domain-specific tiers:
- Solscan: 10.0 RPS refill, burst capacity 15.0
- GMGN: 1.0 RPS refill, burst capacity 1.0
"""

import time
import threading
from typing import Optional, Dict


class RateLimitError(Exception):
    """Base exception for rate limiting errors."""
    pass


class RateLimitTimeoutError(RateLimitError):
    """Raised when waiting for rate limit tokens exceeds the specified timeout."""
    pass


class TokenBucketRateLimiter:
    """Thread-safe Token Bucket Rate Limiter.

    Tokens refill at refill_rate per second up to maximum capacity.
    Acquisition blocks until sufficient tokens are accumulated or timeout is reached.
    """

    def __init__(self, refill_rate: float, capacity: float, name: str = "default"):
        if refill_rate <= 0:
            raise ValueError(f"refill_rate must be positive, got {refill_rate}")
        if capacity <= 0:
            raise ValueError(f"capacity must be positive, got {capacity}")

        self.refill_rate = float(refill_rate)
        self.capacity = float(capacity)
        self.name = name
        self._tokens = float(capacity)
        self._last_refill = time.monotonic()
        self._lock = threading.RLock()

    @property
    def tokens(self) -> float:
        """Returns the current token balance after accounting for elapsed time."""
        with self._lock:
            self._refill()
            return self._tokens

    def _refill(self) -> None:
        """Refills tokens based on elapsed monotonic time."""
        now = time.monotonic()
        elapsed = now - self._last_refill
        if elapsed > 0:
            self._tokens = min(self.capacity, self._tokens + elapsed * self.refill_rate)
            self._last_refill = now

    def acquire(self, tokens: float = 1.0, timeout: Optional[float] = 60.0) -> bool:
        """Acquires tokens from the bucket, blocking if necessary.

        Args:
            tokens: Number of tokens to acquire (default: 1.0).
            timeout: Maximum seconds to wait before raising RateLimitTimeoutError.

        Returns:
            True if tokens were acquired.

        Raises:
            RateLimitTimeoutError: If timeout expires before tokens become available.
        """
        if tokens > self.capacity:
            raise ValueError(
                f"Requested tokens ({tokens}) exceed maximum bucket capacity ({self.capacity}) for {self.name}"
            )

        start_time = time.monotonic()

        with self._lock:
            while True:
                self._refill()

                if self._tokens >= tokens:
                    self._tokens -= tokens
                    return True

                needed = tokens - self._tokens
                wait_seconds = needed / self.refill_rate

                if timeout is not None:
                    spent = time.monotonic() - start_time
                    if spent + wait_seconds > timeout:
                        raise RateLimitTimeoutError(
                            f"Rate limit timeout ({timeout}s) exceeded for provider '{self.name}'. "
                            f"Needed {tokens} tokens, had {self._tokens:.2f}."
                        )

                # Sleep in short increments to allow early wakeups/state checks
                sleep_duration = min(wait_seconds, 0.05)
                # Release lock while sleeping so other threads can inspect or refill
                self._lock.release()
                try:
                    time.sleep(sleep_duration)
                finally:
                    self._lock.acquire()

    def try_acquire(self, tokens: float = 1.0) -> bool:
        """Attempts to acquire tokens immediately without blocking.

        Returns:
            True if acquired, False if insufficient tokens.
        """
        with self._lock:
            self._refill()
            if self._tokens >= tokens:
                self._tokens -= tokens
                return True
            return False

    def reset(self) -> None:
        """Resets bucket tokens to full capacity."""
        with self._lock:
            self._tokens = float(self.capacity)
            self._last_refill = time.monotonic()


PROVIDER_RATE_LIMITS: Dict[str, Dict[str, float]] = {
    "solscan": {"refill_rate": 10.0, "capacity": 15.0},
    "gmgn": {"refill_rate": 1.0, "capacity": 1.0},
    "default": {"refill_rate": 5.0, "capacity": 10.0},
}


def get_rate_limiter(provider: str) -> TokenBucketRateLimiter:
    """Factory creating configured rate limiter for a specific provider."""
    config = PROVIDER_RATE_LIMITS.get(provider.lower(), PROVIDER_RATE_LIMITS["default"])
    return TokenBucketRateLimiter(
        refill_rate=config["refill_rate"],
        capacity=config["capacity"],
        name=provider.lower(),
    )

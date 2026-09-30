"""Adaptive Token Bucket Rate Limiter and Decorrelated Jitter Backoff.

Ensures client-side requests never burst into provider-imposed 429 thresholds,
and distributes retries across the temporal spectrum to avoid synchronized thundering herds.
"""

import time
import random
import threading
import logging
from typing import Optional

logger = logging.getLogger("crypto_syndicate.resilience.rate_limiter")


class AdaptiveTokenBucket:
    """Thread-safe Token Bucket Rate Limiter with dynamic refill pacing."""

    def __init__(self, rate_per_second: float = 5.0, capacity: float = 10.0) -> None:
        self.rate = rate_per_second
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = time.time()
        self._lock = threading.Lock()

    def _refill(self) -> None:
        now = time.time()
        delta = now - self.last_update
        self.tokens = min(self.capacity, self.tokens + delta * self.rate)
        self.last_update = now

    def acquire(self, tokens: float = 1.0, block: bool = True, timeout: float = 5.0) -> bool:
        """Acquire token(s) to execute a request."""
        start_time = time.time()
        while True:
            with self._lock:
                self._refill()
                if self.tokens >= tokens:
                    self.tokens -= tokens
                    return True

                if not block:
                    return False

                # Calculate required sleep time
                needed = tokens - self.tokens
                sleep_time = needed / max(self.rate, 0.001)

            if time.time() - start_time + sleep_time > timeout:
                logger.warning("Rate limiter acquisition timed out after %.2fs", timeout)
                return False

            time.sleep(min(sleep_time, 0.1))

    def throttle(self, multiplier: float = 0.5) -> None:
        """Temporarily scale down rate after an external 429 signal."""
        with self._lock:
            self.rate = max(0.5, self.rate * multiplier)
            logger.info("Adaptive rate throttled to %.2f req/s", self.rate)

    def recover(self, multiplier: float = 1.1, max_rate: float = 10.0) -> None:
        """Gradually restore rate towards max_rate on sustained healthy calls."""
        with self._lock:
            if self.rate < max_rate:
                self.rate = min(max_rate, self.rate * multiplier)


class DecorrelatedJitter:
    """Full Decorrelated Jitter Algorithm for API Retries.
    
    Formula: sleep = min(max_sleep, random.uniform(base_sleep, prev_sleep * 3))
    Eliminates synchronized burst retry spikes.
    """

    def __init__(self, base_sleep: float = 0.5, max_sleep: float = 15.0) -> None:
        self.base_sleep = base_sleep
        self.max_sleep = max_sleep
        self.prev_sleep = base_sleep

    def next_sleep(self) -> float:
        """Compute next jittered sleep duration in seconds."""
        t = random.uniform(self.base_sleep, max(self.base_sleep, self.prev_sleep * 3.0))
        sleep_duration = min(self.max_sleep, t)
        self.prev_sleep = sleep_duration
        return sleep_duration

    def reset(self) -> None:
        """Reset backoff to base sleep."""
        self.prev_sleep = self.base_sleep

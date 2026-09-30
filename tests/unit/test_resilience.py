"""Unit tests for Circuit Breaker, Rate Limiter, Immutable Cache, and Smart Router."""

from pathlib import Path
import tempfile
import time
import pytest

from crypto_syndicate.resilience.circuit_breaker import CircuitBreaker
from crypto_syndicate.resilience.rate_limiter import AdaptiveTokenBucket, DecorrelatedJitter
from crypto_syndicate.resilience.cache import ImmutableOnChainCache
from crypto_syndicate.resilience.smart_router import SmartOnChainRouter


class TestCircuitBreaker:
    """Verify Hystrix-style 3-state circuit breaker mechanics."""

    def test_initial_state_closed(self):
        cb = CircuitBreaker(name="TEST_API", failure_threshold=3, recovery_timeout=0.2)
        assert cb.state == "CLOSED"
        assert cb.can_execute() is True

    def test_trip_to_open_after_threshold(self):
        cb = CircuitBreaker(name="TEST_API", failure_threshold=3, recovery_timeout=0.2)
        cb.record_failure(Exception("Err 1"))
        assert cb.state == "CLOSED"
        cb.record_failure(Exception("Err 2"))
        assert cb.state == "CLOSED"
        cb.record_failure(Exception("Err 3"))
        assert cb.state == "OPEN"
        assert cb.can_execute() is False  # Fast fail in 0ms!

    def test_recovery_half_open_and_healing(self):
        cb = CircuitBreaker(name="TEST_API", failure_threshold=2, recovery_timeout=0.1)
        cb.record_failure(Exception("Err 1"))
        cb.record_failure(Exception("Err 2"))
        assert cb.state == "OPEN"

        # Wait past recovery timeout
        time.sleep(0.12)
        assert cb.can_execute() is True
        assert cb.state == "HALF_OPEN"

        # Canary success heals circuit
        cb.record_success()
        assert cb.state == "CLOSED"
        assert cb.failure_count == 0

    def test_canary_failure_re_trips(self):
        cb = CircuitBreaker(name="TEST_API", failure_threshold=1, recovery_timeout=0.1)
        cb.record_failure(Exception("Err"))
        assert cb.state == "OPEN"

        time.sleep(0.12)
        assert cb.can_execute() is True  # enters HALF_OPEN
        assert cb.state == "HALF_OPEN"

        # Canary fails
        cb.record_failure(Exception("Canary drop"))
        assert cb.state == "OPEN"


class TestAdaptiveRateLimiter:
    """Verify Token Bucket rate limiting and jitter backoff."""

    def test_token_bucket_acquire(self):
        bucket = AdaptiveTokenBucket(rate_per_second=10.0, capacity=2.0)
        assert bucket.acquire(tokens=1.0) is True
        assert bucket.acquire(tokens=1.0) is True
        # Bucket exhausted -> non-blocking acquire should fail
        assert bucket.acquire(tokens=1.0, block=False) is False

    def test_throttle_and_recover(self):
        bucket = AdaptiveTokenBucket(rate_per_second=10.0, capacity=10.0)
        bucket.throttle(multiplier=0.5)
        assert bucket.rate == 5.0
        bucket.recover(multiplier=1.2, max_rate=10.0)
        assert bucket.rate == 6.0

    def test_decorrelated_jitter_bounds(self):
        jitter = DecorrelatedJitter(base_sleep=0.1, max_sleep=1.0)
        for _ in range(10):
            s = jitter.next_sleep()
            assert 0.1 <= s <= 1.0


class TestImmutableCache:
    """Verify Two-Tier Memory + SQLite cache."""

    @pytest.fixture
    def cache(self):
        with tempfile.TemporaryDirectory() as d:
            db_file = str(Path(d) / "test_cache.db")
            c = ImmutableOnChainCache(db_path=db_file)
            yield c
            c.close()

    def test_cache_set_get_immutable(self, cache):
        data = {"tx_hash": "0xabc", "amount_sol": 42.0}
        cache.set("tx:0xabc", data)

        # Retrieve
        cached = cache.get("tx:0xabc")
        assert cached == data
        stats = cache.stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 0
        assert stats["hit_rate_pct"] == 100.0

    def test_cache_miss_and_expiration(self, cache):
        assert cache.get("non_existent") is None
        assert cache.stats()["misses"] == 1

        # Expiring item
        cache.set("expiring_key", "temporary_data", ttl_seconds=0.05)
        assert cache.get("expiring_key") == "temporary_data"
        time.sleep(0.08)
        assert cache.get("expiring_key") is None


class TestSmartOnChainRouter:
    """Verify multi-provider router, fallback cascade, and health telemetry."""

    @pytest.fixture
    def router(self):
        with tempfile.TemporaryDirectory() as d:
            r = SmartOnChainRouter(cache_db_path=str(Path(d) / "router_cache.db"))
            yield r
            r.cache.close()

    def test_router_initialization_and_telemetry(self, router):
        telemetry = router.get_health_telemetry()
        assert "providers" in telemetry
        assert "cache" in telemetry
        assert "GMGN_CLI" in telemetry["providers"]
        assert "SOLSCAN_REST" in telemetry["providers"]
        assert telemetry["providers"]["GMGN_CLI"]["state"] == "CLOSED"

    def test_transfers_caching_layer(self, router):
        # Seed cache
        addr = "TestWallet123"
        transfers = [{"from_address": "Root1", "amount": 10.5}]
        router.cache.set(f"transfers:{addr}:50", transfers)

        # Fetch should hit cache at 0ms without hitting network
        result = router.fetch_transfers(addr, limit=50)
        assert result == transfers
        assert router.cache.stats()["hits"] == 1

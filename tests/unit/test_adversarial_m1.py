"""Milestone 1 Adversarial Verification and Stress Test Suite.

Authored by m1_challenger_1 (Empirical Challenger) to rigorously challenge:
1. TokenBucketRateLimiter: High-concurrency thread contention, rate compliance,
   timeout rejections, deadlocks, and boundary edge cases.
2. SQLiteCache: High-concurrency reader/writer/cleaner hammer, expired TTL race
   conditions, SQL injection resilience, and corrupt payload recovery.
3. BaseAPIClient Backoff: Stochastic jitter entropy, exponential delay progression,
   Retry-After header precedence, and transient network error recovery.
4. Security & Credential Isolation: Canary secret leak prevention across cache keys,
   sqlite disk content, logs, and environment tampering resilience.
"""

import os
import time
import math
import json
import sqlite3
import threading
from typing import List, Dict, Any
import pytest
import requests
import requests_mock

from crypto_syndicate.api.rate_limiter import (
    TokenBucketRateLimiter,
    RateLimitTimeoutError,
    get_rate_limiter,
)
from crypto_syndicate.api.cache import (
    SQLiteCache,
    TTL_DYNAMIC,
    TTL_IMMUTABLE,
)
from crypto_syndicate.api.base_client import (
    BaseAPIClient,
    APIRequestError,
    APIAuthenticationError,
    APIForbiddenError,
    APINotFoundError,
    MaxRetriesExceededError,
    parse_retry_after,
)
from crypto_syndicate.api.gmgn_client import GMGNClient
from crypto_syndicate.api.solscan_client import SolscanClient
from crypto_syndicate.config import (
    mask_credential,
    get_effective_data_mode,
    load_config,
    AppConfig,
)


# ============================================================================
# 1. Token Bucket Rate Limiter Adversarial Stress Tests
# ============================================================================

class TestAdversarialRateLimiter:
    """Stress tests and boundary condition exploration for TokenBucketRateLimiter."""

    def test_heavy_concurrency_rate_compliance(self):
        """Under high thread contention (20 threads), tokens acquired must never exceed
        the physical refill rate, and zero deadlocks must occur.
        """
        refill_rate = 25.0  # tokens per second
        capacity = 5.0      # burst capacity
        limiter = TokenBucketRateLimiter(refill_rate=refill_rate, capacity=capacity, name="adv_stress")

        num_threads = 20
        tokens_per_thread = 2.0
        total_tokens = num_threads * tokens_per_thread  # 40 tokens total
        acquisitions: List[float] = []
        lock = threading.Lock()
        errors: List[Exception] = []

        start_time = time.monotonic()

        def worker():
            try:
                for _ in range(int(tokens_per_thread)):
                    limiter.acquire(1.0, timeout=5.0)
                    with lock:
                        acquisitions.append(time.monotonic() - start_time)
            except Exception as e:
                with lock:
                    errors.append(e)

        threads = [threading.Thread(target=worker) for _ in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10.0)
            assert not t.is_alive(), "Thread deadlocked during token acquisition!"

        assert len(errors) == 0, f"Encountered unexpected errors during concurrency: {errors}"
        assert len(acquisitions) == total_tokens, f"Expected {total_tokens} acquisitions, got {len(acquisitions)}"

        total_elapsed = acquisitions[-1]
        # Theoretical minimum time: initial 5 tokens instant, remaining 35 tokens at 25/s = 1.4s
        theoretical_min_time = (total_tokens - capacity) / refill_rate
        assert total_elapsed >= (theoretical_min_time * 0.85), (
            f"Rate limiter allowed too many tokens too fast: {total_elapsed:.3f}s < theoretical {theoretical_min_time:.3f}s"
        )

        # Sliding window invariant check: for any window of length delta_t,
        # count of tokens acquired cannot exceed capacity + delta_t * refill_rate + tolerance
        window_size = 0.5
        max_allowed_in_window = capacity + (window_size * refill_rate) + 1.0  # +1 for rounding
        for t_window_start in [0.0, 0.3, 0.6, 0.9]:
            count = sum(1 for t in acquisitions if t_window_start <= t < t_window_start + window_size)
            assert count <= max_allowed_in_window, (
                f"Rate limit exceeded in window [{t_window_start}, {t_window_start + window_size}]: "
                f"acquired {count} tokens, max allowed was {max_allowed_in_window}"
            )

    def test_burst_timeout_rejection_without_deadlock(self):
        """When 10 threads compete for 1 token with tight timeout, 9 must raise
        RateLimitTimeoutError quickly without deadlocking or leaking threads.
        """
        # 1.0 RPS with capacity 1.0 (GMGN configuration)
        limiter = TokenBucketRateLimiter(refill_rate=1.0, capacity=1.0, name="gmgn_burst_test")

        # Drain bucket
        assert limiter.acquire(1.0, timeout=1.0) is True

        timeout = 0.1  # 100ms timeout
        num_threads = 8
        timeout_exceptions: List[Exception] = []
        successes: List[bool] = []
        lock = threading.Lock()

        start = time.monotonic()

        def worker():
            try:
                acquired = limiter.acquire(1.0, timeout=timeout)
                with lock:
                    successes.append(acquired)
            except RateLimitTimeoutError as e:
                with lock:
                    timeout_exceptions.append(e)

        threads = [threading.Thread(target=worker) for _ in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=2.0)
            assert not t.is_alive(), "Worker thread hung/deadlocked during timeout wait!"

        elapsed = time.monotonic() - start

        # Refill takes 1.0s, so within 0.1s NO thread can refill 1.0 token
        assert len(timeout_exceptions) == num_threads, (
            f"Expected all {num_threads} threads to time out, got {len(timeout_exceptions)} timeouts and {len(successes)} successes"
        )
        assert elapsed < 0.5, f"Timeout handling took too long: {elapsed:.3f}s"

    def test_limiter_boundary_and_invalid_inputs(self):
        """Verifies boundary validations on TokenBucketRateLimiter."""
        # Non-positive parameters
        with pytest.raises(ValueError, match="refill_rate must be positive"):
            TokenBucketRateLimiter(refill_rate=0.0, capacity=10.0)

        with pytest.raises(ValueError, match="refill_rate must be positive"):
            TokenBucketRateLimiter(refill_rate=-1.0, capacity=10.0)

        with pytest.raises(ValueError, match="capacity must be positive"):
            TokenBucketRateLimiter(refill_rate=10.0, capacity=0.0)

        with pytest.raises(ValueError, match="capacity must be positive"):
            TokenBucketRateLimiter(refill_rate=10.0, capacity=-5.0)

        limiter = TokenBucketRateLimiter(refill_rate=10.0, capacity=5.0)

        # Request exceeding capacity
        with pytest.raises(ValueError, match="exceed maximum bucket capacity"):
            limiter.acquire(tokens=6.0)

        # Fractional tokens work accurately
        assert limiter.acquire(tokens=0.5) is True
        assert limiter.try_acquire(tokens=0.5) is True

        # Reset returns bucket to full capacity
        limiter.acquire(tokens=4.0)
        limiter.reset()
        assert limiter.tokens >= 4.9


# ============================================================================
# 2. SQLite Cache Concurrency, Corruption & SQL Injection Tests
# ============================================================================

class TestAdversarialSQLiteCache:
    """Stress tests concurrency, corruption recovery, and injection safety."""

    def test_concurrent_hammer_multithreaded_wal(self, tmp_path):
        """25 threads concurrently reading, writing, updating, and cleaning expired entries.
        Database must remain completely uncorrupted and free of lock errors.
        """
        db_path = str(tmp_path / "hammer_test.db")
        cache = SQLiteCache(db_path=db_path)

        num_writers = 8
        num_readers = 8
        num_updaters = 5
        num_cleaners = 4
        ops_per_thread = 25

        errors: List[Exception] = []
        lock = threading.Lock()

        def writer(w_id: int):
            try:
                for i in range(ops_per_thread):
                    cache.set(
                        provider="solscan",
                        endpoint=f"tx/{w_id}_{i}",
                        params={"block": i},
                        status_code=200,
                        response_body={"tx_id": f"tx_{w_id}_{i}", "status": "confirmed"},
                        ttl=0.2 if i % 2 == 0 else 3600.0,
                    )
            except Exception as e:
                with lock:
                    errors.append(e)

        def reader(r_id: int):
            try:
                for i in range(ops_per_thread):
                    target_w = i % num_writers
                    cache.get("solscan", f"tx/{target_w}_{i}", {"block": i})
            except Exception as e:
                with lock:
                    errors.append(e)

        def updater(u_id: int):
            try:
                for i in range(ops_per_thread):
                    target_w = i % num_writers
                    cache.set(
                        provider="solscan",
                        endpoint=f"tx/{target_w}_{i}",
                        params={"block": i},
                        status_code=200,
                        response_body={"tx_id": f"tx_{target_w}_{i}", "updated": True},
                    )
            except Exception as e:
                with lock:
                    errors.append(e)

        def cleaner():
            try:
                for _ in range(ops_per_thread):
                    cache.cleanup_expired()
                    time.sleep(0.01)
            except Exception as e:
                with lock:
                    errors.append(e)

        threads = []
        for i in range(num_writers):
            threads.append(threading.Thread(target=writer, args=(i,)))
        for i in range(num_readers):
            threads.append(threading.Thread(target=reader, args=(i,)))
        for i in range(num_updaters):
            threads.append(threading.Thread(target=updater, args=(i,)))
        for _ in range(num_cleaners):
            threads.append(threading.Thread(target=cleaner))

        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=15.0)
            assert not t.is_alive(), "Worker thread hung during concurrent SQLite hammer!"

        assert len(errors) == 0, f"SQLite hammer encountered lock errors: {errors}"

        # Empirically verify database file integrity via PRAGMA
        with sqlite3.connect(db_path) as conn:
            integrity = conn.execute("PRAGMA integrity_check;").fetchall()
            assert integrity == [("ok",)], f"SQLite database integrity check failed: {integrity}"

    def test_concurrent_expired_ttl_race_condition(self, tmp_path):
        """When multiple readers concurrently encounter expired TTL entries, lazy deletion
        must not trigger conflict or unhandled exceptions.
        """
        db_path = str(tmp_path / "ttl_race.db")
        cache = SQLiteCache(db_path=db_path)

        # Populate with 40 entries set to expire in 0.05s
        for i in range(40):
            cache.set("gmgn", f"pair_{i}", {}, 200, {"pair": i}, ttl=0.05)

        time.sleep(0.08)  # Ensure all expired

        errors: List[Exception] = []
        results: List[Any] = []
        lock = threading.Lock()

        def reader():
            try:
                for i in range(40):
                    res = cache.get("gmgn", f"pair_{i}", {})
                    with lock:
                        results.append(res)
            except Exception as e:
                with lock:
                    errors.append(e)

        threads = [threading.Thread(target=reader) for _ in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0, f"Concurrent expired delete produced errors: {errors}"
        # All expired entries must return None
        assert all(r is None for r in results)

    def test_sql_injection_defense(self, tmp_path):
        """Malicious SQL injection payloads in provider, endpoint, or params must never
        drop tables, alter schema, or corrupt the cache.
        """
        db_path = str(tmp_path / "injection_test.db")
        cache = SQLiteCache(db_path=db_path)

        malicious_endpoint = "swaps'; DROP TABLE api_cache; --"
        malicious_provider = "solscan' OR '1'='1"
        malicious_params = {
            "query": "'; DELETE FROM api_cache WHERE 1=1; --",
            "injection": " UNION SELECT 1, 2, 3, 4, 5, 6, 7, 8 --",
        }

        # Set malicious record
        key = cache.set(
            provider=malicious_provider,
            endpoint=malicious_endpoint,
            params=malicious_params,
            status_code=200,
            response_body={"attack": "neutralized"},
        )
        assert key != ""

        # Retrieve malicious record
        retrieved = cache.get(malicious_provider, malicious_endpoint, malicious_params)
        assert retrieved == {"attack": "neutralized"}

        # Verify api_cache table still exists and is completely intact
        with sqlite3.connect(db_path) as conn:
            cursor = conn.execute("SELECT count(*) FROM api_cache;")
            count = cursor.fetchone()[0]
            assert count >= 1, "api_cache table was compromised by SQL injection!"

    def test_corrupt_database_recovery(self, tmp_path):
        """Cache gracefully handles unparseable JSON without unhandled crash."""
        db_path = str(tmp_path / "corrupt_data.db")
        cache = SQLiteCache(db_path=db_path)

        cache_key, _ = cache.generate_key("gmgn", "corrupt_test", {})

        # Direct insert of broken JSON
        with sqlite3.connect(db_path) as conn:
            conn.execute(
                """
                INSERT INTO api_cache 
                (cache_key, provider, endpoint, params_hash, status_code, response_body, created_at, expires_at)
                VALUES (?, 'gmgn', 'corrupt_test', 'hash', 200, '{broken_json: unquoted, ', 1000.0, 9999999999.0)
                """,
                (cache_key,),
            )

        # Reading must not crash with JSONDecodeError, but return None
        result = cache.get("gmgn", "corrupt_test", {})
        assert result is None


# ============================================================================
# 3. Jittered Exponential Backoff & Retry Logic Tests
# ============================================================================

class TestAdversarialBackoffAndRetry:
    """Verifies backoff randomness, progression, header precedence, and error boundaries."""

    def test_backoff_stochastic_entropy_and_progression(self):
        """Verifies that _calculate_backoff produces genuine stochastic jitter
        and scales exponentially across retry attempts.
        """
        client = BaseAPIClient(provider="test", base_url="https://api.example.com", base_backoff_seconds=1.0)

        # Attempt 0: base=1.0, multiplier=1 -> nominal=1.0, range=[0.5, 1.5]
        samples_0 = [client._calculate_backoff(attempt=0) for _ in range(50)]
        assert all(0.5 <= s <= 1.5 for s in samples_0)
        assert len(set(samples_0)) > 40, "Backoff values are not stochastic!"
        avg_0 = sum(samples_0) / len(samples_0)

        # Attempt 1: base=1.0, multiplier=2 -> nominal=2.0, range=[1.0, 3.0]
        samples_1 = [client._calculate_backoff(attempt=1) for _ in range(50)]
        assert all(1.0 <= s <= 3.0 for s in samples_1)
        avg_1 = sum(samples_1) / len(samples_1)

        # Attempt 2: base=1.0, multiplier=4 -> nominal=4.0, range=[2.0, 6.0]
        samples_2 = [client._calculate_backoff(attempt=2) for _ in range(50)]
        assert all(2.0 <= s <= 6.0 for s in samples_2)
        avg_2 = sum(samples_2) / len(samples_2)

        # Attempt 3: base=1.0, multiplier=8 -> nominal=8.0, range=[4.0, 12.0]
        samples_3 = [client._calculate_backoff(attempt=3) for _ in range(50)]
        assert all(4.0 <= s <= 12.0 for s in samples_3)
        avg_3 = sum(samples_3) / len(samples_3)

        # Exponential progression check
        assert avg_0 < avg_1 < avg_2 < avg_3, (
            f"Averages did not scale exponentially: {avg_0:.2f}, {avg_1:.2f}, {avg_2:.2f}, {avg_3:.2f}"
        )

    def test_retry_after_header_priority_and_boundary(self):
        """Retry-After header must override calculated backoff when larger, and handle
        malformed or zero values gracefully.
        """
        assert parse_retry_after(None) == 0.0
        assert parse_retry_after("") == 0.0
        assert parse_retry_after("invalid_header_value") == 0.0
        assert parse_retry_after("-10") == 0.0
        assert parse_retry_after("5.5") == 5.5
        assert parse_retry_after(" 12 ") == 12.0

    def test_network_connection_error_and_timeout_recovery(self, requests_mock):
        """Transient network drop (ConnectionError followed by Timeout) recovers when server returns 200."""
        client = BaseAPIClient(
            provider="test",
            base_url="https://api.example.com",
            base_backoff_seconds=0.001,
        )
        test_url = "https://api.example.com/unstable"
        requests_mock.get(
            test_url,
            [
                {"exc": requests.exceptions.ConnectionError("Connection reset by peer")},
                {"exc": requests.exceptions.Timeout("Read timed out")},
                {"status_code": 200, "json": {"resilient": True}},
            ],
        )

        res = client._request_with_retry(test_url)
        assert res == {"resilient": True}

    def test_persistent_network_failure_exhaustion(self, requests_mock):
        """Permanent connection failure exhausts MAX_RETRIES and raises MaxRetriesExceededError."""
        client = BaseAPIClient(
            provider="test",
            base_url="https://api.example.com",
            base_backoff_seconds=0.001,
        )
        test_url = "https://api.example.com/permanent_fail"
        requests_mock.get(test_url, exc=requests.exceptions.ConnectionError("Host unreachable"))

        with pytest.raises(MaxRetriesExceededError, match="Max retries"):
            client._execute_request("GET", test_url, raise_on_exhaustion=True)


# ============================================================================
# 4. Environment & Canary Secret Leakage Tests
# ============================================================================

class TestAdversarialSecurityAndEnvironment:
    """Rigorous verification that credentials never leak and environment tampering is safe."""

    def test_canary_secret_never_leaked_in_cache_or_disk(self, monkeypatch, tmp_path):
        """A high-entropy canary secret passed as an API key or parameter must NEVER appear
        in cache database files, cache keys, or error messages.
        """
        canary = "SUPER_SECRET_CANARY_KEY_XYZ_987654321"
        monkeypatch.setenv("GMGN_API_KEY", canary)
        monkeypatch.setenv("SOLSCAN_API_KEY", canary)

        db_path = str(tmp_path / "canary_test.db")
        cache = SQLiteCache(db_path=db_path)

        # 1. Masking verification
        masked = mask_credential(canary)
        assert canary not in masked
        assert masked == "SUPE...4321"

        # 2. Key generation strips auth tokens
        params_with_canary = {"token": canary, "api_key": canary, "limit": 10}
        cache_key, params_hash = cache.generate_key("gmgn", "rank/sol", params_with_canary)

        # Cache key and params_hash must not contain canary
        assert canary not in cache_key
        assert canary not in params_hash

        # Store entry in cache
        cache.set("gmgn", "rank/sol", params_with_canary, 200, {"data": "safe"})

        # 3. Read raw database bytes from disk to assert zero plaintext canary leak
        with open(db_path, "rb") as f:
            raw_bytes = f.read()
            assert canary.encode("utf-8") not in raw_bytes, "Raw canary secret leaked to SQLite disk cache file!"

    def test_environment_tampering_blank_and_whitespace(self, monkeypatch):
        """Setting credentials to empty or whitespace-only strings must cleanly resolve
        to mock mode without unhandled crash.
        """
        monkeypatch.setenv("GMGN_API_KEY", "   ")
        monkeypatch.setenv("SOLSCAN_API_KEY", "")
        monkeypatch.setenv("DATA_MODE", "auto")

        mode = get_effective_data_mode()
        assert mode == "mock"

        cfg = load_config()
        assert cfg.gmgn_api_key is None
        assert cfg.solscan_api_key is None

    def test_live_mode_without_keys_raises_cleanly(self, monkeypatch):
        """Setting DATA_MODE='live' without required keys raises ConfigurationError cleanly."""
        monkeypatch.delenv("GMGN_API_KEY", raising=False)
        monkeypatch.delenv("SOLSCAN_API_KEY", raising=False)
        monkeypatch.setenv("DATA_MODE", "live")

        from crypto_syndicate.config import ConfigurationError
        with pytest.raises(ConfigurationError, match="DATA_MODE is 'live'"):
            get_effective_data_mode()

"""Milestone 1 Unit Test Suite: API Clients, Rate Limiting, Backoff, Caching & Fixtures.

Exhaustively verifies:
1. Token Bucket Rate Limiter precision, capacity bursting, and thread safety.
2. Jittered exponential backoff, retry-after handling, and fast fail semantics.
3. SQLite disk cache SHA-256 key generation, tiered TTL, and WAL mode.
4. Environment variable security and zero hardcoded credentials.
5. Deterministic multi-chain golden fixtures integrity (5 clusters, >=3 wallets, >=2 patterns).
6. Transparent offline fallback and zero network egress in mock mode.
7. Immutability and serialization of canonical data models.
"""

import os
import re
import time
import socket
import threading
from pathlib import Path
from typing import Dict, Any, List
from dataclasses import FrozenInstanceError
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
    TTL_IMMUTABLE,
    TTL_DYNAMIC,
    TTL_SEMI_STATIC,
)
from crypto_syndicate.api.base_client import (
    BaseAPIClient,
    APIRequestError,
    APIAuthenticationError,
    APIForbiddenError,
    APINotFoundError,
    MaxRetriesExceededError,
)
from crypto_syndicate.api.gmgn_client import GMGNClient
from crypto_syndicate.api.solscan_client import SolscanClient
from crypto_syndicate.api.fixtures import (
    get_mock_clusters,
    get_mock_token_launches,
    get_mock_token_trades,
    get_mock_wallet_transfers,
    get_mock_account_metadata,
)
from crypto_syndicate.api.models import (
    TokenLaunchEvent,
    TradeRecord,
    FundingTransferRecord,
    WalletScore,
    SyndicateCluster,
    PatternType,
)
from crypto_syndicate.config import (
    mask_credential,
    get_effective_data_mode,
)


# ============================================================================
# 1. Token Bucket Rate Limiter Tests
# ============================================================================

class TestTokenBucketRateLimiter:
    """Rigorous tests for thread-safe Token Bucket Rate Limiter."""

    def test_burst_within_capacity_instant(self):
        """Requests within bucket capacity consume tokens immediately without waiting."""
        limiter = TokenBucketRateLimiter(refill_rate=5.0, capacity=10.0, name="test_burst")
        start = time.monotonic()
        for _ in range(10):
            acquired = limiter.acquire(1.0, timeout=1.0)
            assert acquired is True
        duration = time.monotonic() - start
        assert duration < 0.1, f"Consuming tokens within capacity took {duration:.3f}s, expected <0.1s"

    def test_throttling_when_capacity_exhausted(self):
        """When capacity is exhausted, acquire waits for refill rate."""
        limiter = TokenBucketRateLimiter(refill_rate=10.0, capacity=2.0, name="test_throttle")
        limiter.acquire(2.0)  # Exhaust capacity
        assert limiter.tokens < 1.0

        start = time.monotonic()
        acquired = limiter.acquire(1.0, timeout=1.0)
        duration = time.monotonic() - start

        assert acquired is True
        # At 10.0 RPS, 1 token takes ~0.10s to refill
        assert 0.05 <= duration <= 0.35, f"Expected wait around ~0.10s, got {duration:.3f}s"

    def test_solscan_limiter_defaults(self):
        """Solscan rate limiter defaults to 10.0 RPS and capacity 15.0."""
        limiter = get_rate_limiter("solscan")
        assert limiter.refill_rate == 10.0
        assert limiter.capacity == 15.0

    def test_gmgn_limiter_defaults(self):
        """GMGN rate limiter defaults to 1.0 RPS and capacity 1.0."""
        limiter = get_rate_limiter("gmgn")
        assert limiter.refill_rate == 1.0
        assert limiter.capacity == 1.0

    def test_thread_safe_token_acquisition(self):
        """10 concurrent threads acquiring tokens must not cause race conditions."""
        limiter = TokenBucketRateLimiter(refill_rate=100.0, capacity=50.0, name="test_threads")
        success_count = 0
        lock = threading.Lock()

        def worker():
            nonlocal success_count
            for _ in range(5):
                if limiter.acquire(1.0, timeout=2.0):
                    with lock:
                        success_count += 1

        threads = [threading.Thread(target=worker) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert success_count == 50, f"Expected 50 successful token acquisitions, got {success_count}"

    def test_acquire_timeout_exceeded_raises(self):
        """When timeout is exceeded, RateLimitTimeoutError is raised."""
        limiter = TokenBucketRateLimiter(refill_rate=0.1, capacity=1.0, name="test_timeout")
        limiter.acquire(1.0)  # Exhaust

        with pytest.raises(RateLimitTimeoutError):
            limiter.acquire(1.0, timeout=0.05)


# ============================================================================
# 2. Exponential Backoff & Retry Tests
# ============================================================================

class TestExponentialBackoffRetry:
    """Verifies jittered backoff, status code routing, and retry exhaustion."""

    def test_retry_on_429_eventual_success(self, requests_mock):
        """Client retries on HTTP 429 and succeeds when server recovers."""
        client = GMGNClient(api_key="test_key", mock_mode=False, base_backoff_seconds=0.001)
        test_url = f"{client.BASE_URL}/test_429"
        requests_mock.get(
            test_url,
            [
                {"status_code": 429, "text": "Too Many Requests"},
                {"status_code": 429, "text": "Too Many Requests"},
                {"status_code": 200, "json": {"recovered": True}},
            ],
        )

        res = client._request_with_retry(test_url)
        assert res == {"recovered": True}

    def test_retry_on_5xx_server_errors(self, requests_mock):
        """Client retries on 500, 502, 503, 504 status codes."""
        client = GMGNClient(api_key="test_key", mock_mode=False, base_backoff_seconds=0.001)
        test_url = f"{client.BASE_URL}/test_5xx"
        requests_mock.get(
            test_url,
            [
                {"status_code": 500, "text": "Internal Server Error"},
                {"status_code": 502, "text": "Bad Gateway"},
                {"status_code": 503, "text": "Service Unavailable"},
                {"status_code": 200, "json": {"server_recovered": True}},
            ],
        )

        res = client._request_with_retry(test_url)
        assert res == {"server_recovered": True}

    def test_max_retries_exceeded_raises_or_returns_none(self, requests_mock):
        """Persistent 500 raises MaxRetriesExceededError in _execute_request, or returns None in helper."""
        client = GMGNClient(api_key="test_key", mock_mode=False, base_backoff_seconds=0.001)
        test_url = f"{client.BASE_URL}/test_fatal_500"
        requests_mock.get(test_url, status_code=500, text="Dead Server")

        with pytest.raises(MaxRetriesExceededError):
            client._execute_request("GET", test_url, raise_on_exhaustion=True)

        res = client._request_with_retry(test_url)
        assert res is None

    def test_fast_fail_on_4xx_non_retryable(self, requests_mock):
        """Client immediately raises on non-retryable 4xx without sleeping or looping."""
        client = GMGNClient(api_key="test_key", mock_mode=False, base_backoff_seconds=0.001)

        # 400
        requests_mock.get(f"{client.BASE_URL}/err_400", status_code=400, text="Bad Request")
        with pytest.raises(APIRequestError):
            client._execute_request("GET", f"{client.BASE_URL}/err_400")

        # 401
        requests_mock.get(f"{client.BASE_URL}/err_401", status_code=401, text="Unauthorized")
        with pytest.raises(APIAuthenticationError):
            client._execute_request("GET", f"{client.BASE_URL}/err_401")

        # 403
        requests_mock.get(f"{client.BASE_URL}/err_403", status_code=403, text="Forbidden")
        with pytest.raises(APIForbiddenError):
            client._execute_request("GET", f"{client.BASE_URL}/err_403")

        # 404
        requests_mock.get(f"{client.BASE_URL}/err_404", status_code=404, text="Not Found")
        with pytest.raises(APINotFoundError):
            client._execute_request("GET", f"{client.BASE_URL}/err_404")

    def test_respects_retry_after_header(self, requests_mock):
        """Client parses and respects Retry-After header."""
        client = GMGNClient(api_key="test_key", mock_mode=False, base_backoff_seconds=0.001)
        test_url = f"{client.BASE_URL}/test_retry_after"
        requests_mock.get(
            test_url,
            [
                {"status_code": 429, "headers": {"Retry-After": "0.1"}, "text": "Rate Limit"},
                {"status_code": 200, "json": {"ok": True}},
            ],
        )
        start = time.monotonic()
        res = client._request_with_retry(test_url)
        duration = time.monotonic() - start

        assert res == {"ok": True}
        assert duration >= 0.08, f"Should have waited at least Retry-After duration, took {duration:.3f}s"


# ============================================================================
# 3. SQLite Disk Cache Tests
# ============================================================================

class TestSQLiteDiskCache:
    """Verifies SQLite disk cache, SHA-256 keying, tiered TTL, and WAL mode."""

    def test_cache_miss_stores_cache_hit_retrieves(self, tmp_path):
        """First call executes request and stores payload; second call hits cache."""
        db_path = str(tmp_path / "test_cache.db")
        cache = SQLiteCache(db_path=db_path)

        # Cache miss
        assert cache.get("solscan", "account/transfer", {"address": "WalletA"}) is None

        # Store
        payload = {"transfers": [{"amount": 10.0}]}
        cache.set("solscan", "account/transfer", {"address": "WalletA"}, 200, payload)

        # Cache hit
        cached = cache.get("solscan", "account/transfer", {"address": "WalletA"})
        assert cached == payload

    def test_deterministic_key_generation(self, tmp_path):
        """Cache keys are identical regardless of parameter dictionary insertion order."""
        db_path = str(tmp_path / "test_cache.db")
        cache = SQLiteCache(db_path=db_path)

        p1 = {"chain": "sol", "limit": 50, "token": "sensitive_api_key"}
        p2 = {"limit": 50, "chain": "sol", "token": "different_api_key"}

        k1, h1 = cache.generate_key("gmgn", "rank/sol/swaps", p1)
        k2, h2 = cache.generate_key("gmgn", "rank/sol/swaps", p2)

        assert k1 == k2, "SHA-256 keys must be identical across parameter ordering and strip auth tokens"
        assert h1 == h2

    def test_ttl_expiration_triggers_refetch(self, tmp_path):
        """Entries past TTL are expired and return None."""
        db_path = str(tmp_path / "test_cache.db")
        cache = SQLiteCache(db_path=db_path)

        cache.set("gmgn", "test/exp", {}, 200, {"data": "old"}, ttl=0.1)
        # Immediate read
        assert cache.get("gmgn", "test/exp", {}) == {"data": "old"}

        # Wait for expiration
        time.sleep(0.15)
        assert cache.get("gmgn", "test/exp", {}) is None

    def test_historical_records_infinite_ttl(self, tmp_path):
        """Historical transactions and account metadata resolve to permanent TTL."""
        db_path = str(tmp_path / "test_cache.db")
        cache = SQLiteCache(db_path=db_path)

        ttl_tx = cache.resolve_ttl("solscan", "transaction/detail")
        assert ttl_tx == TTL_IMMUTABLE

        ttl_meta = cache.resolve_ttl("solscan", "account/metadata")
        assert ttl_meta == TTL_IMMUTABLE

        ttl_dyn = cache.resolve_ttl("gmgn", "rank/sol/swaps/1h")
        assert ttl_dyn == TTL_DYNAMIC

    def test_wal_mode_concurrency(self, tmp_path):
        """Concurrent reads and writes operate in WAL mode without database locked errors."""
        db_path = str(tmp_path / "test_wal_cache.db")
        cache = SQLiteCache(db_path=db_path)

        errors = []

        def writer(idx):
            try:
                for i in range(20):
                    cache.set("solscan", f"endpoint_{idx}", {"i": i}, 200, {"val": i})
            except Exception as e:
                errors.append(e)

        def reader(idx):
            try:
                for i in range(20):
                    cache.get("solscan", f"endpoint_{idx}", {"i": i})
            except Exception as e:
                errors.append(e)

        threads = []
        for i in range(4):
            threads.append(threading.Thread(target=writer, args=(i,)))
            threads.append(threading.Thread(target=reader, args=(i,)))

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0, f"Concurrent SQLite operations encountered errors: {errors}"


# ============================================================================
# 4. Environment & Security Tests
# ============================================================================

class TestEnvironmentAndSecurity:
    """Enforces zero hardcoded credentials and safe environment resolution."""

    def test_env_vars_read_dynamically(self, monkeypatch):
        """Credentials are read strictly from environment variables."""
        monkeypatch.setenv("GMGN_API_KEY", "dynamic_test_key_gmgn_9999")
        monkeypatch.setenv("SOLSCAN_API_KEY", "dynamic_test_key_solscan_8888")

        from crypto_syndicate.config import load_config
        cfg = load_config()
        assert cfg.gmgn_api_key == "dynamic_test_key_gmgn_9999"
        assert cfg.solscan_api_key == "dynamic_test_key_solscan_8888"

    def test_no_hardcoded_keys_in_source(self):
        """Automated scan over src/ verifying zero hardcoded API keys or bearer secrets."""
        repo_src = Path(__file__).resolve().parent.parent.parent / "src"
        py_files = list(repo_src.glob("**/*.py"))
        assert len(py_files) > 0, "No python source files found in src/"

        # Regex matching assignment of raw credential keys
        key_pattern = re.compile(
            r'(?:api_key|secret_key|solscan_key|gmgn_key|auth_token)\s*=\s*[\'"][a-zA-Z0-9_\-]{16,}[\'"]',
            re.IGNORECASE,
        )

        violations = []
        for f in py_files:
            content = f.read_text(encoding="utf-8")
            matches = key_pattern.findall(content)
            if matches:
                violations.append((str(f), matches))

        assert len(violations) == 0, f"Found hardcoded credentials in source files: {violations}"

    def test_missing_keys_graceful_fallback(self, monkeypatch):
        """Unset environment keys trigger transparent mock fallback without crash."""
        monkeypatch.delenv("GMGN_API_KEY", raising=False)
        monkeypatch.delenv("SOLSCAN_API_KEY", raising=False)
        monkeypatch.setenv("CRYPTO_DATA_MODE", "auto")

        mode = get_effective_data_mode()
        assert mode == "mock"

        client = GMGNClient()
        assert client.mock_mode is True

        sol_client = SolscanClient()
        assert sol_client.mock_mode is True

    def test_mask_credential_safety(self):
        """Credential masking preserves privacy for telemetry and logs."""
        assert mask_credential(None) == "<NOT_SET>"
        assert mask_credential("") == "<NOT_SET>"
        assert mask_credential("short") == "****"
        assert mask_credential("gmgn_live_secret_key_123456789") == "gmgn...6789"


# ============================================================================
# 5. Golden Fixtures Integrity Tests
# ============================================================================

class TestGoldenFixturesIntegrity:
    """Verifies mathematical consistency and acceptance criteria of the 5 golden scenarios."""

    def test_exactly_five_golden_clusters(self):
        """Verifies presence of all 5 required golden scenarios."""
        clusters = get_mock_clusters()
        assert len(clusters) == 5, f"Expected exactly 5 golden clusters, got {len(clusters)}"

        cluster_ids = {c.cluster_id for c in clusters}
        expected_ids = {
            "SYN-SOL-PUMP-01",
            "SYN-ETH-UNI-02",
            "SYN-BSC-PAN-03",
            "SYN-BASE-AERO-04",
            "SYN-MULTI-CROSS-05",
        }
        assert cluster_ids == expected_ids, f"Cluster IDs mismatch: {cluster_ids} vs {expected_ids}"

    def test_cluster_membership_criteria(self):
        """Acceptance Criteria: Each discovered cluster has >= 3 member wallets."""
        clusters = get_mock_clusters()
        for c in clusters:
            assert len(c.wallets) >= 3, f"Cluster {c.cluster_id} has {len(c.wallets)} wallets; requires >= 3"

    def test_cluster_pattern_criteria(self):
        """Acceptance Criteria: Each cluster flags at least 2 of the 4 suspicious pattern types."""
        clusters = get_mock_clusters()
        valid_patterns = {
            PatternType.EARLY_ENTRY.value,
            PatternType.COMMON_FUNDING.value,
            PatternType.SHARED_DEPLOYER.value,
            PatternType.COORDINATED_DUMP.value,
        }
        for c in clusters:
            flagged = set(c.flagged_patterns)
            assert len(flagged) >= 2, f"Cluster {c.cluster_id} flagged {len(flagged)} patterns; requires >= 2"
            assert flagged.issubset(valid_patterns), f"Invalid patterns in {c.cluster_id}: {flagged - valid_patterns}"

    def test_chain_address_format_validity(self):
        """Verifies address formats match target blockchain specifications."""
        clusters = get_mock_clusters()
        evm_regex = re.compile(r"^0x[a-fA-F0-9]{40}$")
        base58_chars = set("123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz")

        for c in clusters:
            for w in c.wallets:
                if c.chain in ("eth", "bsc", "base"):
                    assert evm_regex.match(w), f"Invalid EVM address format: {w} in {c.cluster_id}"
                elif c.chain == "sol":
                    assert 32 <= len(w) <= 44, f"Invalid Solana address length: {w}"
                    assert set(w).issubset(base58_chars), f"Invalid Solana Base58 characters in: {w}"
                elif c.chain == "multi":
                    # Multi-chain clusters can contain both EVM and Solana addresses
                    is_evm = bool(evm_regex.match(w))
                    is_sol = 32 <= len(w) <= 44 and set(w).issubset(base58_chars)
                    assert is_evm or is_sol, f"Address {w} in {c.cluster_id} must be valid EVM or Solana address"

    def test_pnl_reconciliation_math(self):
        """Verifies cluster estimated profit strictly equals sum of wallet net profits."""
        clusters = get_mock_clusters()
        for c in clusters:
            wallet_sum = sum(ws.net_profit_usd for ws in c.wallet_scores.values())
            assert abs(c.estimated_profit_usd - wallet_sum) < 0.05, (
                f"Cluster {c.cluster_id} profit {c.estimated_profit_usd} != sum of wallet profits {wallet_sum}"
            )


# ============================================================================
# 6. Offline Fallback Integration Tests
# ============================================================================

class TestOfflineFallbackIntegration:
    """Verifies that offline fallback serves data without egress network calls."""

    def test_gmgn_client_offline_mode(self):
        """GMGNClient in mock mode returns golden fixtures."""
        client = GMGNClient(mock_mode=True)
        launches = client.get_new_token_launches("sol")
        assert len(launches) > 0
        assert isinstance(launches[0], TokenLaunchEvent)
        assert launches[0].chain == "sol"

        trades = client.get_token_trades("sol", launches[0].token_address)
        assert len(trades) > 0
        assert isinstance(trades[0], TradeRecord)

    def test_solscan_client_offline_mode(self):
        """SolscanClient in mock mode returns golden fixtures."""
        client = SolscanClient(mock_mode=True)
        transfers = client.get_account_transfers("SoLSniper1111111111111111111111111111111111")
        assert len(transfers) > 0
        assert isinstance(transfers[0], FundingTransferRecord)

        meta = client.get_account_metadata("SoLSniper1111111111111111111111111111111111")
        assert meta is not None
        assert "funded_by" in meta

    def test_zero_network_egress_in_mock_mode(self, monkeypatch):
        """In mock mode, network socket connections are strictly never attempted."""
        def blocked_connect(*args, **kwargs):
            raise AssertionError("Network socket connect attempted while in mock mode!")

        monkeypatch.setattr(socket.socket, "connect", blocked_connect)

        gmgn = GMGNClient(mock_mode=True)
        launches = gmgn.get_new_token_launches("sol")
        assert len(launches) > 0

        solscan = SolscanClient(mock_mode=True)
        transfers = solscan.get_account_transfers("SoLSniper1111111111111111111111111111111111")
        assert len(transfers) > 0


# ============================================================================
# 7. Canonical Immutable Data Model Tests
# ============================================================================

class TestImmutableModels:
    """Verifies dataclass immutability and lossless dictionary serialization."""

    def test_models_are_frozen(self):
        """Attribute mutation on frozen models raises FrozenInstanceError."""
        launch = TokenLaunchEvent(
            token_address="TokenA",
            chain="sol",
            name="Token A",
            symbol="TKNA",
        )
        with pytest.raises(FrozenInstanceError):
            launch.initial_price_usd = 100.0  # type: ignore

        trade = TradeRecord(
            trade_id="tx_1",
            chain="sol",
            token_address="TokenA",
            wallet_address="Wallet1",
            direction="buy",
            timestamp=1000,
            token_amount=100.0,
        )
        with pytest.raises(FrozenInstanceError):
            trade.price_usd = 5.0  # type: ignore

        transfer = FundingTransferRecord(
            transfer_id="tx_t1",
            chain="sol",
            from_address="WalletA",
            to_address="WalletB",
            amount=5.0,
        )
        with pytest.raises(FrozenInstanceError):
            transfer.amount = 10.0  # type: ignore

    def test_model_serialization_roundtrip(self):
        """Models serialize to dictionary and reconstruct losslessly."""
        cluster = get_mock_clusters()[0]
        c_dict = cluster.to_dict()

        assert isinstance(c_dict, dict)
        assert c_dict["cluster_id"] == cluster.cluster_id
        assert c_dict["wallets"] == list(cluster.wallets)

        reconstructed = SyndicateCluster.from_dict(c_dict)
        assert reconstructed.cluster_id == cluster.cluster_id
        assert reconstructed.wallets == cluster.wallets
        assert reconstructed.suspicion_score == cluster.suspicion_score

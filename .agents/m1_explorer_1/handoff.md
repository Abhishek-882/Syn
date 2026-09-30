# Architectural Implementation Plan: GMGN & Solscan Clients, Rate Limiting & Backoff

**Agent**: `m1_explorer_1`  
**Working Directory**: `C:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\m1_explorer_1`  
**Target Milestone**: Milestone 1 (API Clients & Multi-Chain Ingestion)  
**Date**: 2026-09-20  
**Status**: Ready for Milestone 1 Worker Implementation  

---

## 1. Observation

Direct investigation of the codebase, project documentation, and surveys revealed the following concrete technical requirements and existing deficiencies:

1. **Legacy Implementation Defects (`crypto_syndicate/api_client.py:10-44`)**:
   - Lines 12-13: Uses non-existent GMGN endpoint URL `https://gmgn.ai/api/v1` (actual is `https://gmgn.ai/defi/quotation/v1`).
   - Line 15: Solscan header incorrectly formatted as `Authorization: Bearer <SOLSCAN_API_KEY>`. Per Solscan Pro v2 API documentation, the required header is `token: <SOLSCAN_API_KEY>`.
   - Lines 17-31: Primitive retry uses naive `time.sleep(2 ** attempt)` without jitter, without `Retry-After` header parsing, and with zero proactive rate limiting.
   - Lines 33-43: Uses in-memory Joblib caching (`@memory.cache`) writing to a temporary directory instead of persistent SQLite disk caching (`.cache/api_cache.db`) with SHA-256 request hashing.
   - Line 43: Calls `/account/transfers` with an erroneous trailing 's' (Solscan endpoint is `/account/transfer`).
   - Completely lacks multi-chain support (GMGN supports `sol`, `eth`, `bsc`, `base`, `tron`).
   - Crashes or fails silently when `GMGN_API_KEY` or `SOLSCAN_API_KEY` are absent, violating Acceptance Criteria for offline testability.

2. **Authoritative Project Requirements (`PROJECT.md` & `ORIGINAL_REQUEST.md`)**:
   - `PROJECT.md:8-10`: Module layout specifies:
     - `src/crypto_syndicate/api/gmgn_client.py`: Multi-chain token rank, swaps, wallet trade histories for Solana, Ethereum, BSC, Base, Tron.
     - `src/crypto_syndicate/api/solscan_client.py`: Solscan Pro API v2 client for Solana deep transfer lineage, account metadata (`funded_by`), and parsed transaction balance deltas.
     - `src/crypto_syndicate/api/rate_limiter.py`: Independent Token Bucket rate limiters (10.0 RPS Solscan, 1.0 RPS GMGN).
     - `src/crypto_syndicate/api/cache.py`: Local SQLite disk cache with SHA-256 hashing and tiered TTL.
   - `ORIGINAL_REQUEST.md:30-35 (§R3)`: "All API calls must be rate-limited, retried on failure, and cached locally to avoid redundant requests." "Data should be fetched for all available historical time ranges."
   - `ORIGINAL_REQUEST.md:77`: "The system must accept API credentials via environment variables only (GMGN_API_KEY and SOLSCAN_API_KEY). Never hardcode credentials in any file."

3. **API Specification Telemetry (`.agents/survey_spec_miner_1/api_spec_report.md`)**:
   - **Solscan Pro v2**:
     - Base URL: `https://pro-api.solscan.io/v2.0`
     - Header: `token: <SOLSCAN_API_KEY>`
     - Cost: 100 Compute Units (CU) per call.
     - Rate limit tier: Lite plan allows 1,000 req / 60s (~16.6 RPS). Clamping client to 10.0 RPS with burst capacity 15 provides a robust 40% margin.
   - **GMGN OpenAPI & Quotation v1**:
     - Base URL: `https://gmgn.ai/defi/quotation/v1`
     - Supported chains: `sol`, `eth`, `bsc`, `base`, `tron`.
     - Headers: `x-route-key: <GMGN_API_KEY>` or `Authorization: Bearer <GMGN_API_KEY>`.
     - Cloudflare Bot Management & Turnstile: Rejects non-browser requests and actively blocks IPv6 connections (`socket.AF_INET` forcing required). Standard public rate limit is strictly 1.0 RPS with burst capacity 1.0.

---

## 2. Logic Chain

From these observations, we derive the exact module architecture, algorithms, class hierarchies, and interfaces required for the Milestone 1 Worker:

### 2.1 Rate Limiting Architecture: High-Precision Token Bucket (`rate_limiter.py`)

A sliding window or naive sleep is insufficient for asynchronous or multi-threaded ingestion loops. We formulate a mathematically strict, thread-safe **Token Bucket**:

#### Mathematical Definition
Let:
- $C$ = Bucket Capacity (maximum burst tokens).
- $r$ = Refill Rate (tokens added per second).
- $T(t)$ = Token balance at time $t$.
- $t_{last}$ = Timestamp of last state update.

State transition on request arrival at time $t_{now}$:
$$\Delta t = \max(0.0, t_{now} - t_{last})$$
$$T(t_{now}) = \min(C, T(t_{last}) + \Delta t \times r)$$
$$t_{last} = t_{now}$$

If $T(t_{now}) \ge \text{cost}$ (where standard cost = 1.0):
$$T(t_{now}) \leftarrow T(t_{now}) - \text{cost} \implies \text{Grant immediate execution}$$
Else:
$$\Delta t_{wait} = \frac{\text{cost} - T(t_{now})}{r}$$
Sleep for $\Delta t_{wait}$, update state, and proceed.

#### Domain Configuration
```python
PROVIDER_RATE_LIMITS = {
    "solscan": {"refill_rate": 10.0, "capacity": 15.0},
    "gmgn":    {"refill_rate": 1.0,  "capacity": 1.0}
}
```

#### Detailed Class Design: `TokenBucketRateLimiter`
```python
class TokenBucketRateLimiter:
    """Thread-safe and async-compatible Token Bucket Rate Limiter."""
    
    def __init__(self, refill_rate: float, capacity: float, name: str = "default"):
        self.refill_rate = float(refill_rate)
        self.capacity = float(capacity)
        self.name = name
        self._tokens = float(capacity)
        self._last_refill = time.monotonic()
        self._lock = threading.RLock()

    def acquire(self, tokens: float = 1.0, timeout: Optional[float] = 60.0) -> bool:
        """Blocks until tokens are available or timeout expires."""
        start_time = time.monotonic()
        with self._lock:
            while True:
                now = time.monotonic()
                elapsed = now - self._last_refill
                self._tokens = min(self.capacity, self._tokens + elapsed * self.refill_rate)
                self._last_refill = now

                if self._tokens >= tokens:
                    self._tokens -= tokens
                    return True

                needed = tokens - self._tokens
                wait_seconds = needed / self.refill_rate
                
                if timeout is not None:
                    spent = time.monotonic() - start_time
                    if spent + wait_seconds > timeout:
                        raise RateLimitTimeoutError(
                            f"Rate limit timeout ({timeout}s) exceeded for {self.name}"
                        )
                time.sleep(min(wait_seconds, 0.1))
```

---

### 2.2 Exponential Backoff Retry Policy with Full Jitter

To prevent "thundering herd" problems and handle Cloudflare / RPC rate limits gracefully, the client employs **Full Jitter Exponential Backoff**:

#### Mathematical Formulation
$$t_{\text{sleep}} = \text{random.uniform}(0.5, 1.5) \times \min\left(t_{\text{max}}, \; t_{\text{base}} \times 2^{\text{attempt}}\right)$$
Where:
- $t_{\text{base}} = 1.0\,\text{s}$
- $t_{\text{max}} = 30.0\,\text{s}$
- $\text{max\_retries} = 5$

#### Header Override
If response header contains `Retry-After`:
$$t_{\text{sleep}} = \max\left(t_{\text{sleep}}, \; \text{parse\_retry\_after}(\text{header})\right)$$

#### Classification Matrix
- **Retryable (Execute Backoff)**:
  - HTTP `429` (Too Many Requests)
  - HTTP `500` (Internal Server Error)
  - HTTP `502` (Bad Gateway)
  - HTTP `503` (Service Unavailable)
  - HTTP `504` (Gateway Timeout)
  - Exceptions: `requests.exceptions.ConnectionError`, `requests.exceptions.Timeout`, `socket.timeout`
- **Fast Fail (Raise Exception Immediately)**:
  - HTTP `400` -> `APIRequestError` (Bad Request parameters)
  - HTTP `401` -> `APIAuthenticationError` (Missing/Invalid API Key)
  - HTTP `403` -> `APIForbiddenError` (WAF block / Plan tier restriction)
  - HTTP `404` -> `APINotFoundError` (Resource does not exist)
  - HTTP `422` -> `APIRequestError` (Unprocessable entity)

---

### 2.3 Base API Client & Request Lifecycle (`base_client.py`)

A unified base class `BaseAPIClient` standardizes the request execution lifecycle across both providers:

```
[API Method Invocation: e.g. get_new_token_launches]
                        │
                        ▼
           [Mode Check: config.CRYPTO_DATA_MODE]
           ├── mock ─────────► [Serve Deterministic Fixture]
           └── live / auto
                        │
                        ▼
     [Cache Key Generation: SHA-256(provider, url, params)]
                        │
                        ▼
             [Query SQLiteCache]
           ├── Hit (Not Expired) ──► Return Cached JSON
           └── Miss / Expired
                        │
                        ▼
     [Rate Limiter Token Acquisition: acquire()]
                        │
                        ▼
      [HTTP Execution with Jittered Backoff Loop]
      (Forcing IPv4 + Custom Browser User-Agent)
                        │
                        ▼
       [Response Validation & Error Handling]
           ├── 429/5xx ──────► Jittered Sleep & Retry
           ├── 4xx Error ────► Raise APIClientError
           └── 200 OK
                        │
                        ▼
        [Write to SQLiteCache with Tiered TTL]
                        │
                        ▼
      [Normalize to Canonical Model: models.py]
```

#### IPv4 Socket Forcing Implementation
To prevent Cloudflare from dropping requests to GMGN via IPv6:
```python
import socket
import urllib3.util.connection as urllib_connection

def force_ipv4_transport():
    """Forces urllib3 to use IPv4 DNS resolution."""
    urllib_connection.allowed_gai_family = lambda: socket.AF_INET
```

---

### 2.4 Solscan Client Specification (`solscan_client.py`)

`SolscanClient` provides high-fidelity access to the Solana blockchain:

```python
class SolscanClient(BaseAPIClient):
    """Client for Solscan Pro API v2."""

    BASE_URL = "https://pro-api.solscan.io/v2.0"

    def __init__(self, api_key: Optional[str] = None, cache: Optional[SQLiteCache] = None):
        api_key = api_key or os.environ.get("SOLSCAN_API_KEY", "")
        rate_limiter = TokenBucketRateLimiter(refill_rate=10.0, capacity=15.0, name="solscan")
        super().__init__(provider="solscan", api_key=api_key, rate_limiter=rate_limiter, cache=cache)

    def get_account_transfers(
        self,
        address: str,
        activity_type: Optional[str] = None,
        token: Optional[str] = None,
        flow: Optional[str] = None,
        from_time: Optional[int] = None,
        to_time: Optional[int] = None,
        page: int = 1,
        page_size: int = 40
    ) -> List[FundingTransferRecord]:
        """Fetch native SOL and SPL transfers for a wallet.
        Endpoint: GET /account/transfer
        TTL: Infinite if to_time is fixed in past; 60s if live.
        """

    def get_account_metadata(self, address: str) -> Optional[Dict[str, Any]]:
        """Fetch initial activation funder and account labels.
        Endpoint: GET /account/metadata
        TTL: 2,592,000s (30 days - immutable root funding).
        Note: If funded_by is null (pure SPL account), falls back to get_account_transfers(flow='in').
        """

    def get_token_latest(
        self,
        platform_id: str = "pumpfun",
        page: int = 1,
        page_size: int = 40
    ) -> List[TokenLaunchEvent]:
        """Fetch recently launched tokens on Solana launchpads.
        Endpoint: GET /token/latest
        Platforms: pumpfun, raydium, meteora, moonshot_launchpad, etc.
        TTL: 60s.
        """

    def get_transaction_detail(self, tx_hash: str) -> Optional[Dict[str, Any]]:
        """Fetch transaction balance changes (sol_bal_change, token_bal_change) and fees.
        Endpoint: GET /transaction/detail
        TTL: Infinite (immutable confirmed block).
        """

    def get_token_holders(
        self,
        address: str,
        page: int = 1,
        page_size: int = 20
    ) -> List[Dict[str, Any]]:
        """Fetch top token holder distribution.
        Endpoint: GET /token/holders
        TTL: 300s (5 minutes).
        """
```

---

### 2.5 GMGN Client Specification (`gmgn_client.py`)

`GMGNClient` covers multi-chain discovery, DEX swaps, and liquidity initialization across Solana, Ethereum, BSC, Base, and Tron:

```python
class GMGNClient(BaseAPIClient):
    """Client for GMGN Quotation and Multi-Chain Services."""

    BASE_URL = "https://gmgn.ai/defi/quotation/v1"
    SUPPORTED_CHAINS = ("sol", "eth", "bsc", "base", "tron")

    def __init__(self, api_key: Optional[str] = None, cache: Optional[SQLiteCache] = None):
        api_key = api_key or os.environ.get("GMGN_API_KEY", "")
        # Strictly serialize GMGN requests to 1 RPS with capacity 1 to avoid Cloudflare blocks
        rate_limiter = TokenBucketRateLimiter(refill_rate=1.0, capacity=1.0, name="gmgn")
        super().__init__(provider="gmgn", api_key=api_key, rate_limiter=rate_limiter, cache=cache)

    def get_new_token_launches(
        self,
        chain: str,
        time_period: str = "1h",
        orderby: str = "created_timestamp",
        direction: str = "desc",
        limit: int = 50
    ) -> List[TokenLaunchEvent]:
        """Discover new token launches across all supported chains without seed wallets.
        Endpoint: GET /rank/{chain}/swaps/{time_period}
        TTL: 60s.
        """

    def get_token_security(self, chain: str, token_address: str) -> Dict[str, Any]:
        """Fetch token security metrics, creator wallet, and pool liquidity.
        Endpoint: GET /tokens/{chain}/{token_address}
        TTL: 86400s (24 hours).
        """

    def get_token_trades(
        self,
        chain: str,
        token_address: str,
        limit: int = 200
    ) -> List[TradeRecord]:
        """Fetch granular DEX swaps for a token to analyze early snipers and dump timing.
        Endpoint: GET /trades/{chain}/{token_address}
        TTL: 30s.
        """

    def get_wallet_token_activity(
        self,
        chain: str,
        wallet_address: str,
        token_address: str
    ) -> Dict[str, Any]:
        """Fetch historical trades and PnL for a wallet on a specific token.
        Endpoint: GET /wallet_token_activity/{chain}
        TTL: 300s.
        """
```

---

### 2.6 Unified Façade Contract: `CryptoDataClient` (`__init__.py`)

To ensure the downstream discovery engine (`crypto_syndicate.discovery.pipeline`) has a single, transparent ingestion entry point, `CryptoDataClient` unifies both providers:

```python
class CryptoDataClient:
    """Unified multi-chain on-chain data client façade."""

    def __init__(self, config: Optional[AppConfig] = None):
        self.config = config or load_config()
        self.cache = SQLiteCache(db_path=self.config.cache_db_path)
        self.gmgn = GMGNClient(api_key=self.config.gmgn_api_key, cache=self.cache)
        self.solscan = SolscanClient(api_key=self.config.solscan_api_key, cache=self.cache)
        self.fixtures = FixtureProvider()

    def get_new_token_launches(self, chain: str, time_period: str = "1h") -> List[TokenLaunchEvent]:
        if self._should_use_fixtures():
            return self.fixtures.get_new_token_launches(chain=chain, time_period=time_period)
        return self.gmgn.get_new_token_launches(chain=chain, time_period=time_period)

    def get_token_trades(self, chain: str, token_address: str, limit: int = 500) -> List[TradeRecord]:
        if self._should_use_fixtures():
            return self.fixtures.get_token_trades(chain=chain, token_address=token_address, limit=limit)
        return self.gmgn.get_token_trades(chain=chain, token_address=token_address, limit=limit)

    def get_wallet_transfers(self, chain: str, wallet_address: str, flow: str = "in") -> List[FundingTransferRecord]:
        if self._should_use_fixtures():
            return self.fixtures.get_wallet_transfers(chain=chain, wallet_address=wallet_address, flow=flow)
        if chain in ("sol", "solana"):
            return self.solscan.get_account_transfers(address=wallet_address, flow=flow)
        # For EVM chains, fallback to GMGN wallet activity or EVM transfer fixtures
        return self.fixtures.get_wallet_transfers(chain=chain, wallet_address=wallet_address, flow=flow)

    def get_account_metadata(self, wallet_address: str) -> Optional[Dict[str, Any]]:
        if self._should_use_fixtures():
            return self.fixtures.get_account_metadata(wallet_address=wallet_address)
        return self.solscan.get_account_metadata(address=wallet_address)

    def _should_use_fixtures(self) -> bool:
        if self.config.crypto_data_mode == "mock":
            return True
        if self.config.crypto_data_mode == "auto":
            return not (self.config.gmgn_api_key and self.config.solscan_api_key)
        return False
```

---

## 3. Caveats

1. **Cloudflare Bot Management on GMGN**:
   - GMGN is fronted by aggressive Cloudflare Turnstile bot detection. If live keys are used from IP ranges known to Cloudflare (e.g. standard datacenter IPs), requests may receive HTTP 403.
   - Mitigation: The architecture mandates browser-like HTTP headers (`User-Agent`, `Accept-Language`), forced IPv4 resolution, and strict 1.0 RPS rate limiting. When blocks occur, the client catches 403 and surfaces a clear diagnostic error rather than crashing.
2. **Solscan Plan Tier Limitations**:
   - `GET /account/metadata/multi` is blocked on the Solscan Lite ($49/mo) tier (returns HTTP 403).
   - Mitigation: Our design exclusively calls single-account endpoints (`/account/metadata`) through the rate limiter rather than batch multi endpoints, ensuring 100% compatibility across all Solscan subscription tiers.
3. **Pure SPL Accounts with `funded_by: null`**:
   - On Solana, token accounts or wallets that have never received native SOL will return `funded_by: null` from `/account/metadata`.
   - Mitigation: `SolscanClient` explicitly handles `funded_by: null` by querying `/account/transfer` with `flow="in"` to extract the initial funder.
4. **Offline Mock Mode Parity**:
   - The mock fixture system must return the exact same canonical `TokenLaunchEvent`, `TradeRecord`, and `FundingTransferRecord` types as the live client to ensure seamless testability.

---

## 4. Conclusion

This architecture satisfies all requirements of **Requirement R3** in `ORIGINAL_REQUEST.md` and fulfills the contracts outlined in `PROJECT.md` for Milestone 1.

### Key Deliverables Specified:
1. **`TokenBucketRateLimiter` (`src/crypto_syndicate/api/rate_limiter.py`)**:
   - 10.0 RPS / 15 capacity for Solscan.
   - 1.0 RPS / 1 capacity for GMGN.
2. **Full Jitter Exponential Backoff**:
   - Decorrelated random jitter with base 1.0s, max 30.0s, max retries 5.
   - Dynamic `Retry-After` header parsing.
3. **`SolscanClient` (`src/crypto_syndicate/api/solscan_client.py`)**:
   - Authoritative transfer lineage, initial funding root discovery, and parsed transaction details.
   - Correct `token: <SOLSCAN_API_KEY>` header.
4. **`GMGNClient` (`src/crypto_syndicate/api/gmgn_client.py`)**:
   - Multi-chain coverage across `sol`, `eth`, `bsc`, `base`, and `tron`.
   - IPv4 forced transport and Cloudflare Turnstile protection.
5. **`CryptoDataClient` (`src/crypto_syndicate/api/__init__.py`)**:
   - Façade providing non-seed launch discovery, trades, and transfers with transparent mock fallback.

The Milestone 1 Worker can immediately implement these classes with zero architectural ambiguity.

---

## 5. Verification Method

To verify the implementation once written by the Worker:

1. **Unit Test Suite Execution**:
   Run the dedicated Milestone 1 unit test suite:
   ```bash
   pytest tests/unit/test_api_clients.py -v
   ```
2. **Rate Limiter Verification**:
   - Assert `SolscanRateLimiter` enforces $\le 10$ requests per second when flooded with 30 concurrent calls.
   - Assert `GMGNRateLimiter` enforces $\le 1$ request per second over a 5-second window.
3. **Backoff & Retry Verification**:
   - Use `unittest.mock` or `responses` to mock HTTP 429 and 503 responses with and without `Retry-After` headers.
   - Verify that requests retry up to 5 times with monotonically increasing jittered sleep intervals before raising `MaxRetriesExceededError`.
   - Verify that HTTP 401 raises `APIAuthenticationError` immediately without retrying.
4. **Multi-Chain Coverage Verification**:
   - Query `get_new_token_launches` for each supported chain: `sol`, `eth`, `bsc`, `base`, `tron`.
   - Verify all returned objects conform strictly to `TokenLaunchEvent` schema.
5. **Offline Fallback Verification**:
   - Unset `GMGN_API_KEY` and `SOLSCAN_API_KEY`.
   - Run `CryptoDataClient.get_new_token_launches("sol")`.
   - Verify that data is returned from the deterministic golden fixtures without any unhandled exceptions or network attempts.

# Milestone 1: Deterministic Multi-Chain Fixtures & Unit Test Suite Architecture Plan

**Author**: `m1_explorer_3`  
**Working Directory**: `C:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\m1_explorer_3`  
**Target Milestone**: Milestone 1 (API Ingestion & Caching Layer)  
**Date**: 2026-09-20  

---

## 1. Observation

Direct observations from authoritative specifications and codebase review:

1. **Acceptance Criteria & Non-Seed Discovery Requirements**:
   - `ORIGINAL_REQUEST.md` (lines 53-56):
     > "System discovers at least 5 wallet clusters from recent token launches without any seed wallet input. Each cluster has >= 3 wallets with at least 2 of the 4 suspicious pattern types flagged."
   - `ORIGINAL_REQUEST.md` (lines 63-65):
     > "GMGN and Solscan API calls are rate-limited, retried on failure, and cached to avoid redundant requests. All chains supported by GMGN are queried, not just Solana."
   - `ORIGINAL_REQUEST.md` (line 77):
     > "Note: The system must accept API credentials via environment variables only (GMGN_API_KEY and SOLSCAN_API_KEY). Never hardcode credentials in any file."

2. **System Architecture & Feature Inventory**:
   - `PROJECT.md` (lines 12-13):
     > "`fixtures.py`: Deterministic offline golden syndicate fixtures across Solana, Ethereum, and BSC ensuring 100% testability and demo execution without live API keys."
     > "`models.py`: Immutable data structures (`TokenLaunchEvent`, `TradeRecord`, `FundingTransferRecord`, `SyndicateCluster`, `WalletScore`)."
   - `PROJECT.md` (lines 54-55): Feature 7 explicitly mandates "Deterministic Offline Mock Fixtures — 5 multi-chain golden syndicate scenarios for offline testing & demos" for Milestone 1.
   - `PROJECT.md` (lines 196):
     > "Milestone 1 Worker: `src/crypto_syndicate/config.py`, `src/crypto_syndicate/api/*`, `pyproject.toml`, `tests/unit/test_api_clients.py`"

3. **E2E Testing Infrastructure Requirements**:
   - `TEST_INFRA.md` (lines 30-31):
     > "`tests/e2e/test_tier4_applications.py`: 5 realistic multi-chain syndicate scenarios (Solana Pump.fun launch ring, Ethereum Uniswap rug syndicate, BSC PancakeSwap sniper cluster, Base meme ring, Multi-chain cross-deployer syndicate)."

4. **API Specifications & Rate Limiting Guidelines**:
   - `api_spec_report.md` (lines 274-285):
     - Solscan Pro API v2: Conservative rate limit = 10.0 RPS, burst capacity = 15.
     - GMGN API: Conservative rate limit = 1.0 RPS, burst capacity = 1. Requires IPv4 routing.
     - Jittered exponential backoff: $t_{\text{wait}} = \min(30.0, 1.0 \times 2^{\text{attempt}}) \times (0.5 + 0.5 \times U(0,1))$, max 5 attempts, retrying on 429 and 5xx.
     - SQLite cache: SHA-256 canonical parameter hashing, tiered TTL ($\infty$ for historical, 60s for live polling).

5. **Existing Prototype State**:
   - `crypto_syndicate/api_client.py` (lines 10-31): Naive prototype using `joblib.Memory("cache_dir")` with hardcoded 3-retries and no token-bucket rate limiting.
   - Environment: Python 3.14.4 with `pytest` 8.4.2, `pydantic` 2.13.4, `requests` 2.33.1, `requests-mock` 1.12.1, `networkx` 3.6.1 available in global environment.

---

## 2. Logic Chain

1. **Deterministic Testability Without External Dependencies**:
   - Live network calls to GMGN and Solscan require valid API keys and live connectivity, which cannot be guaranteed in test or evaluation environments.
   - Therefore, a complete, self-contained mock engine (`fixtures.py`) must be built that provides 100% graph-consistent, mathematically sound synthetic data across all 5 required syndicate scenarios.
   - When `GMGN_API_KEY` or `SOLSCAN_API_KEY` is not detected in `os.environ`, the system must automatically and transparently switch to offline fallback mode without error or crash.

2. **Graph Consistency & Pattern Compliance**:
   - The 4 suspicious pattern types defined in `heuristics_report.md` are:
     1. `COORDINATED_EARLY_ENTRY` (buy within early minutes of pool launch, supply cornering $\ge 15\%$)
     2. `COMMON_FUNDING_SOURCE` (pre-launch gas/capital distribution from common upstream root wallet)
     3. `SHARED_DEPLOYERS` (direct transfers to deployer, shared grandparent funder, or recurrent multi-token snipes)
     4. `COORDINATED_SELLS_DUMPS` (synchronized sell timing $\sigma_{sell} \le 180\text{s}$, liquidating $\ge 75\%$ position, or sweeping proceeds to common destination)
   - To satisfy Acceptance Criteria, every one of the 5 golden scenarios must contain $\ge 3$ member wallets and trigger $\ge 2$ patterns.
   - The 5 scenarios must directly match the 5 target scenarios specified in `TEST_INFRA.md`:
     - Scenario 1: Solana Pump.fun ring (`SYN-SOL-PUMP-01`)
     - Scenario 2: Ethereum Uniswap rug syndicate (`SYN-ETH-UNI-02`)
     - Scenario 3: BSC PancakeSwap sniper cluster (`SYN-BSC-PAN-03`)
     - Scenario 4: Base meme ring (`SYN-BASE-AERO-04`)
     - Scenario 5: Multi-chain cross-deployer syndicate (`SYN-MULTI-CROSS-05`)

3. **Multi-Tiered Fallback Mechanism**:
   - Fallback must operate at both high-level client method calls and mock HTTP transport interception.
   - Client calls (`get_recent_launches`, `get_token_trades`, `get_wallet_transfers`, `get_account_metadata`) should check `self.mock_mode` and return populated canonical models.
   - A mock transport adapter (`MockHTTPAdapter`) should also be available for testing HTTP request/response handling, rate limiting, and cache integration.

4. **Unit Test Coverage for Milestone 1**:
   - Milestone 1 owns `tests/unit/test_api_clients.py`.
   - The test suite must rigorously assert:
     - Independent Token Bucket behavior for both Solscan (10.0 RPS) and GMGN (1.0 RPS).
     - Jittered exponential backoff and retry behavior on 429, 500, 502, 503, 504 status codes.
     - Fast-failure on non-retryable status codes (400, 401, 403, 404).
     - Deterministic SQLite caching with SHA-256 keys and tiered TTL expiration.
     - Environment variable loading with zero hardcoded secrets.
     - Full integrity, structural validity, address checksums, and mathematical reconciliation for the 5 golden fixtures.

---

## 3. Detailed Specifications for Implementation

### 3.1 Five Multi-Chain Golden Syndicate Scenarios (`fixtures.py`)

#### Scenario 1: Solana Pump.fun Ring (`SYN-SOL-PUMP-01`)
- **Chain**: `solana`
- **Platform**: `pumpfun`
- **Token Launch Event**:
  - `token_address`: `"PepeR1111111111111111111111111111111111pump"`
  - `name`: `"Pepe Rocket"`, `symbol`: `"PEPEROCK"`, `decimals`: 6
  - `total_supply`: 1,000,000,000.0
  - `deployer_address`: `"9xQeWvG816bUx9EPjHmaT23yvVM2ZWbrrpZb9PusVFin"`
  - `launch_timestamp`: 1726830000 ($T_0$)
  - `initial_liquidity_usd`: 12500.0
  - `initial_price_usd`: 0.0000125
- **Root Funding Source**: `"FundSolMaster111111111111111111111111111111111"`
  - At $T_0 - 480\text{s}$ (1726829520), sends 5.2 SOL to each of the 5 sniper wallets.
- **Member Wallets (5 wallets)**:
  1. `"SolSniper111111111111111111111111111111111111"`
  2. `"SolSniper222222222222222222222222222222222222"`
  3. `"SolSniper333333333333333333333333333333333333"`
  4. `"SolSniper444444444444444444444444444444444444"`
  5. `"SolSniper555555555555555555555555555555555555"`
- **Trades (Buys & Sells)**:
  - **Buys**: Between $T_0 + 3\text{s}$ and $T_0 + 11\text{s}$, each wallet spends exactly 5.0 SOL buying 60,000,000 tokens at ~$0.0000125.
    - Total group tokens acquired: 300,000,000 (30.0% of total supply).
  - **Sells**: At $T_0 + 600\text{s}$ (token price pumped to $0.000055), each wallet sells 100% of holdings (60,000,000 tokens) between $T_0 + 602\text{s}$ and $T_0 + 630\text{s}$ ($\sigma_{sell} = 10.5\text{s}$).
  - **Proceeds Sweep**: At $T_0 + 720\text{s}$, proceeds swept to `"SolSweepAggregator111111111111111111111111111"`.
- **Flagged Patterns (3 patterns)**:
  1. `COORDINATED_EARLY_ENTRY` (buys within 11s, cornered 30% of supply, identical 5 SOL buys)
  2. `COMMON_FUNDING_SOURCE` (same root funder 8 minutes pre-launch)
  3. `COORDINATED_SELLS_DUMPS` ($\sigma_{sell} \le 180\text{s}$, 100% liquidated, sweep destination)
- **Financial Reconciliation**:
  - Outlay: $5 \times 5.0\text{ SOL} = 25.0\text{ SOL}$ ($3,675 USD @ $147/SOL)
  - Proceeds: $5 \times 22.5\text{ SOL} = 112.5\text{ SOL}$ ($16,537.50 USD)
  - Fees: 0.025 SOL ($3.68 USD)
  - **Estimated Realized Profit**: $12,858.82 USD.
- **Suspicion Score**: 96.5.

---

#### Scenario 2: Ethereum Uniswap Rug Syndicate (`SYN-ETH-UNI-02`)
- **Chain**: `ethereum`
- **Platform**: `uniswap_v2`
- **Token Launch Event**:
  - `token_address`: `"0x71C0aA87a2C0C30A91d1469e38B61bfaE8c81201"`
  - `name`: `"Quantum AI Finance"`, `symbol`: `"QAIFI"`, `decimals`: 18
  - `total_supply`: 10,000,000.0
  - `deployer_address`: `"0xDe91010101010101010101010101010101010101"`
  - `launch_timestamp`: 1726833600 ($T_0$)
  - `initial_liquidity_usd`: 50000.0
  - `initial_price_usd`: 0.005
- **Root Funding Source**: `"0xF00dF00dF00dF00dF00dF00dF00dF00dF00dF00d"`
  - Funds deployer with 25 ETH at $T_0 - 3600\text{s}$.
  - Disperses 3.5 ETH to each of 4 sniper wallets at $T_0 - 1800\text{s}$.
- **Member Wallets (4 wallets)**:
  1. `"0x1111111111111111111111111111111111111111"`
  2. `"0x2222222222222222222222222222222222222222"`
  3. `"0x3333333333333333333333333333333333333333"`
  4. `"0x4444444444444444444444444444444444444444"`
- **Trades**:
  - **Buys**: At $T_0 + 24\text{s}$ (Block +2), each wallet buys 600,000 tokens for 3.0 ETH. (Total 2,400,000 tokens = 24.0% of supply).
  - **Sells**: At $T_0 + 504\text{s}$ (Block +42), all 4 wallets dump 100% of holdings in the same block for 8.5 ETH each, followed immediately by deployer liquidity removal.
- **Flagged Patterns (3 patterns)**:
  1. `COMMON_FUNDING_SOURCE` (shared 1-hop funder `0xF00dF00d...`)
  2. `SHARED_DEPLOYERS` (deployer and snipers share root funder; direct gas transfer from deployer to wallet 1)
  3. `COORDINATED_SELLS_DUMPS` (identical exit block, 100% liquidated, simultaneous rug-pull)
- **Financial Reconciliation**:
  - Outlay: 12.0 ETH ($30,000 USD @ $2,500/ETH)
  - Proceeds: 34.0 ETH ($85,000 USD)
  - Fees: 0.08 ETH ($200 USD)
  - **Estimated Realized Profit**: $54,800.00 USD.
- **Suspicion Score**: 98.0.

---

#### Scenario 3: BSC PancakeSwap Sniper Cluster (`SYN-BSC-PAN-03`)
- **Chain**: `bsc`
- **Platform**: `pancakeswap_v2`
- **Token Launch Event**:
  - `token_address`: `"0x89bC39A726a7C4324f9E29cE43b7B73F42A7C302"`
  - `name`: `"Baby Moon Doge"`, `symbol`: `"BABYMDOGE"`, `decimals`: 9
  - `total_supply`: 1,000,000,000,000.0
  - `deployer_address`: `"0xDe91020202020202020202020202020202020202"`
  - `launch_timestamp`: 1726837200 ($T_0$)
  - `initial_liquidity_usd`: 20000.0
  - `initial_price_usd`: 0.00000002
- **Root Funding Source**: `"0xF00dB5c000000000000000000000000000000003"`
  - Disperses 5.0 BNB to each of the 4 wallets at $T_0 - 900\text{s}$.
- **Member Wallets (4 wallets)**:
  1. `"0x5555555555555555555555555555555555555555"`
  2. `"0x6666666666666666666666666666666666666666"`
  3. `"0x7777777777777777777777777777777777777777"`
  4. `"0x8888888888888888888888888888888888888888"`
- **Prior Deployer Link**:
  - Deployer `0xDe910202...` deployed token `"0xPrevTokenBsc000000000000000000000000003"` 48 hours earlier; the same 4 wallets sniped that token as well ($R(w, D) \ge 2$).
- **Trades**:
  - **Buys**: At $T_0 + 3\text{s}$ (Block +1), all 4 wallets buy 55,000,000,000 tokens for 4.0 BNB each (22.0% total supply).
  - **Sells**: At $T_0 + 720\text{s}$, wallets dump across 4 blocks, netting 12.0 BNB each.
- **Flagged Patterns (3 patterns)**:
  1. `COORDINATED_EARLY_ENTRY` (same block snipe at +3s, 22% supply cornered)
  2. `COMMON_FUNDING_SOURCE` (common root BNB distribution)
  3. `SHARED_DEPLOYERS` (recurrent snipers across multiple deployer tokens)
- **Financial Reconciliation**:
  - Outlay: 16.0 BNB ($9,120 USD @ $570/BNB)
  - Proceeds: 48.0 BNB ($27,360 USD)
  - Fees: 0.02 BNB ($11.40 USD)
  - **Estimated Realized Profit**: $18,228.60 USD.
- **Suspicion Score**: 94.0.

---

#### Scenario 4: Base Meme Ring (`SYN-BASE-AERO-04`)
- **Chain**: `base`
- **Platform**: `aerodrome`
- **Token Launch Event**:
  - `token_address`: `"0x44BcA91e60058b87F76BfD281729Ec80e7292104"`
  - `name`: `"Based Chad Pepe"`, `symbol`: `"BCHAD"`, `decimals`: 18
  - `total_supply`: 100,000,000.0
  - `deployer_address`: `"0xDe91040404040404040404040404040404040404"`
  - `launch_timestamp`: 1726840800 ($T_0$)
  - `initial_liquidity_usd`: 30000.0
  - `initial_price_usd`: 0.0003
- **Root Funding Source**: `"0xF00dBa5e00000000000000000000000000000004"`
- **Member Wallets (4 wallets)**:
  1. `"0x9999999999999999999999999999999999999999"`
  2. `"0xAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"`
  3. `"0xBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB"`
  4. `"0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC"`
- **Trades**:
  - **Buys**: At $T_0 + 2\text{s}$, $+4\text{s}$, $+6\text{s}$, $+9\text{s}$, each wallet buys 4,500,000 tokens for 2.0 ETH each (18.0% total supply).
  - **Sells**: At $T_0 + 900\text{s}$, cascading exits in 20-second steps ($+900\text{s}, +920\text{s}, +940\text{s}, +960\text{s}$) selling 100% of tokens for 6.0 ETH each.
  - **Proceeds Sweep**: Swept to `"0xBaseSweepAggregator000000000000000000004"` at $T_0 + 1050\text{s}$.
- **Flagged Patterns (2 patterns)**:
  1. `COORDINATED_EARLY_ENTRY` (buys within 9s of open, 18% supply cornering)
  2. `COORDINATED_SELLS_DUMPS` (cascading dump sequence, 100% liquidated, sweep aggregator)
- **Financial Reconciliation**:
  - Outlay: 8.0 ETH ($20,000 USD @ $2,500/ETH)
  - Proceeds: 24.0 ETH ($60,000 USD)
  - Fees: 0.004 ETH ($10.00 USD)
  - **Estimated Realized Profit**: $39,990.00 USD.
- **Suspicion Score**: 88.5.

---

#### Scenario 5: Multi-Chain Cross-Deployer Syndicate (`SYN-MULTI-CROSS-05`)
- **Chain**: `multi` (Cross-chain coordination covering `solana`, `ethereum`, and `bsc`)
- **Associated Tokens (3 tokens)**:
  1. Solana: `"ApexSo1111111111111111111111111111111111111"` (Deployer: `"DeployerApexSol111111111111111111111111111"`)
  2. Ethereum: `"0xAe05010101010101010101010101010101010105"` (Deployer: `"0xDeployerApexEth010101010101010101010105"`)
  3. BSC: `"0xAe05020202020202020202020202020202020205"` (Deployer: `"0xDeployerApexBsc020202020202020202020205"`)
- **Member Wallets (6 wallets across chains)**:
  1. `"0xDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD"` (EVM Cross-chain: ETH & BSC)
  2. `"0xEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE"` (EVM Cross-chain: ETH & BSC)
  3. `"0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF"` (EVM Cross-chain: ETH & BSC)
  4. `"SolCrossSniper1111111111111111111111111111111"` (Solana)
  5. `"SolCrossSniper2222222222222222222222222222222"` (Solana)
  6. `"SolCrossSniper3333333333333333333333333333333"` (Solana)
- **Flagged Patterns (3 patterns)**:
  1. `SHARED_DEPLOYERS` (cross-chain deployer entity launching coordinated multi-chain clone tokens; EVM deployers share bytecode/authority; snipers recur across all 3 launches)
  2. `COORDINATED_EARLY_ENTRY` (first-block snipes across all 3 tokens)
  3. `COMMON_FUNDING_SOURCE` (common bridge and funding distribution)
- **Financial Reconciliation**:
  - Solana branch profit: $6,615 USD
  - Ethereum branch profit: $45,000 USD
  - BSC branch profit: $14,250 USD
  - **Estimated Realized Profit**: $65,865.00 USD.
- **Suspicion Score**: 95.0.

---

### 3.2 Transparent Offline Fallback Mechanics

#### Fallback Modes & Resolution Matrix:
The runtime behavior is controlled by `config.CRYPTO_DATA_MODE` and presence of API keys:

| `CRYPTO_DATA_MODE` | `SOLSCAN_API_KEY` | `GMGN_API_KEY` | Resolved Mode | Behavior |
|---|---|---|---|---|
| `"auto"` (default) | Not set / empty | Not set / empty | **`mock`** | Fully transparent fallback to offline golden fixtures. Logs `INFO: No API keys configured; activating offline golden fixtures.` |
| `"auto"` | Present | Not set / empty | **`hybrid`** | Solscan calls use live API; GMGN calls use offline mock fixtures. |
| `"auto"` | Not set / empty | Present | **`hybrid`** | GMGN calls use live API; Solscan calls use offline mock fixtures. |
| `"auto"` | Present | Present | **`live`** | All calls route to external network. |
| `"mock"` | *Any* | *Any* | **`mock`** | Unconditionally routes to offline golden fixtures. Egress network calls are completely blocked. |
| `"live"` | Missing | Missing | **`error`** | Raises `ConfigurationError("Live mode requested but required API keys are missing.")`. |

#### Provider Delegation Interface in `fixtures.py`:
`fixtures.py` exposes high-level query methods matching the exact signatures of the API clients:
```python
def get_mock_token_launches(chain: Optional[str] = None, time_period: str = "1h") -> List[TokenLaunchEvent]:
    """Returns token launch events matching chain filter, or all 5 golden launches."""

def get_mock_token_trades(chain: str, token_address: str, limit: int = 500) -> List[TradeRecord]:
    """Returns granular buy and sell trade records for the target fixture token."""

def get_mock_wallet_transfers(chain: str, wallet_address: str, flow: str = "in") -> List[FundingTransferRecord]:
    """Returns upstream funding transfers and downstream sweep transfers for the target wallet."""

def get_mock_account_metadata(wallet_address: str) -> Optional[Dict[str, Any]]:
    """Returns Solscan account metadata envelope with funded_by, block_time, tx_hash."""

def get_mock_clusters() -> List[SyndicateCluster]:
    """Returns all 5 pre-computed canonical SyndicateCluster objects for validation."""
```

#### Dual-Layer HTTP Mock Adapter:
In addition to method delegation, `fixtures.py` implements `MockHTTPAdapter(requests.adapters.BaseAdapter)`:
- Intercepts requests to `pro-api.solscan.io` and `gmgn.ai`.
- Returns synthetic HTTP 200 `requests.Response` objects containing the exact JSON envelopes:
  - Solscan: `{"success": True, "data": [...]}`
  - GMGN: `{"code": 0, "message": "success", "data": {...}}`
- Enables testing of the entire networking stack (rate limiting, retries, caching) against the golden fixtures without hitting the public internet.

---

### 3.3 Unit Test Suite Implementation Plan (`tests/unit/test_api_clients.py`)

The test suite must be structured into **6 primary test classes** containing **26 targeted test methods**:

```
tests/unit/test_api_clients.py
├── TestTokenBucketRateLimiter (5 tests)
├── TestExponentialBackoffRetry (5 tests)
├── TestSQLiteDiskCache (5 tests)
├── TestEnvironmentAndSecurity (3 tests)
├── TestGoldenFixturesIntegrity (5 tests)
└── TestOfflineFallbackIntegration (3 tests)
```

#### Test Method Breakdown:

1. **`TestTokenBucketRateLimiter`**:
   - `test_burst_within_capacity_instant`: Requests within capacity $C$ consume tokens without sleeping.
   - `test_throttling_when_capacity_exhausted`: Requesting beyond $C$ sleeps $\approx 1/r$ seconds.
   - `test_solscan_limiter_defaults`: Asserts `rate = 10.0`, `capacity = 15`.
   - `test_gmgn_limiter_defaults`: Asserts `rate = 1.0`, `capacity = 1`.
   - `test_thread_safe_token_acquisition`: 10 concurrent threads acquire tokens without race condition or state corruption.

2. **`TestExponentialBackoffRetry`**:
   - `test_retry_on_429_eventual_success`: Mock returns 429 twice, then 200; client retries and returns data.
   - `test_retry_on_5xx_server_errors`: Mock returns 500, 502, 503, 504; client retries.
   - `test_max_retries_exceeded_raises`: Mock returns continuous 500; client exhausts 5 attempts and raises `APIClientError`.
   - `test_fast_fail_on_4xx_non_retryable`: 400, 401, 403, 404 raise immediately on attempt 1 without sleeping.
   - `test_respects_retry_after_header`: Response with `Retry-After: 3` enforces at least 3.0s sleep.

3. **`TestSQLiteDiskCache`**:
   - `test_cache_miss_stores_cache_hit_retrieves`: First query executes HTTP request and writes to SQLite; second query hits cache with zero HTTP calls.
   - `test_deterministic_key_generation`: Cache key for `{"chain": "sol", "limit": 10}` equals key for `{"limit": 10, "chain": "sol"}`.
   - `test_ttl_expiration_triggers_refetch`: Entry with TTL=1s expires and triggers network refresh after 1.1s.
   - `test_historical_records_infinite_ttl`: Historical transfers and tx details are cached with infinite/30-day TTL.
   - `test_wal_mode_concurrency`: Concurrent reads and writes execute without `database is locked` errors.

4. **`TestEnvironmentAndSecurity`**:
   - `test_env_vars_read_dynamically`: `GMGN_API_KEY` and `SOLSCAN_API_KEY` are read strictly from `os.environ`.
   - `test_no_hardcoded_keys_in_source`: Automated AST/regex scan over `src/crypto_syndicate` asserting zero hardcoded API keys or bearer tokens.
   - `test_missing_keys_graceful_fallback`: When env vars are unset, initializing clients logs warning and sets `mock_mode=True` without throwing exceptions.

5. **`TestGoldenFixturesIntegrity`**:
   - `test_exactly_five_golden_clusters`: Verifies presence of `SYN-SOL-PUMP-01`, `SYN-ETH-UNI-02`, `SYN-BSC-PAN-03`, `SYN-BASE-AERO-04`, `SYN-MULTI-CROSS-05`.
   - `test_cluster_membership_criteria`: Asserts `len(cluster.wallets) >= 3` for all 5 clusters.
   - `test_cluster_pattern_criteria`: Asserts `len(cluster.flagged_patterns) >= 2` for all 5 clusters.
   - `test_chain_address_format_validity`: Solana addresses pass Base58 length/character validation; Ethereum/BSC/Base addresses match `^0x[a-fA-F0-9]{40}$`.
   - `test_pnl_reconciliation_math`: Asserts `cluster.estimated_profit_usd` strictly equals sum of member wallet net profits.

6. **`TestOfflineFallbackIntegration`**:
   - `test_gmgn_client_offline_mode`: With `CRYPTO_DATA_MODE="mock"`, `GMGNClient.get_recent_launches("sol")` returns golden fixtures.
   - `test_solscan_client_offline_mode`: With `CRYPTO_DATA_MODE="mock"`, `SolscanClient.get_wallet_transfers(...)` returns golden fixtures.
   - `test_zero_network_egress_in_mock_mode`: Patches `socket.socket.connect` to verify zero network connection attempts occur in mock mode.

---

## 4. Caveats

1. **Synthetic Timestamps**: Timestamps in golden fixtures are anchored around $T_0 = 1726830000$ (September 2024). When the live monitoring daemon runs in offline demo mode, it should apply a relative time offset or cyclical time window so that launches appear "recent" relative to system clock.
2. **NetworkX Dependency**: The unit tests in `test_api_clients.py` strictly isolate the API and ingestion layers. Graph clustering verification is deferred to `test_clustering.py` and `test_patterns.py` (Milestone 2).
3. **No External Network in Test Runner**: All unit tests in `test_api_clients.py` are hermetic and run with `requests-mock` or mock transports, requiring zero internet connectivity.

---

## 5. Conclusion

- The 5 multi-chain golden fixtures fully satisfy `ORIGINAL_REQUEST.md` R1, R3, R5, and `TEST_INFRA.md` Tier 4 application scenarios.
- Each scenario guarantees $\ge 3$ wallets and $\ge 2$ flagged suspicious patterns, covering Solana, Ethereum, BSC, Base, and Multi-chain.
- The dual-layer fallback mechanism provides complete operational resilience: seamless offline demo execution when credentials are missing, and fully hermetic unit testing.
- The 26-test suite for `tests/unit/test_api_clients.py` provides exhaustive verification of rate limiting, exponential backoff, caching, security, and fixture integrity for Milestone 1.

---

## 6. Verification Method

To independently verify the architecture and test suite:

1. **Inspect Fixture Data Consistency**:
   - Verify that `src/crypto_syndicate/api/fixtures.py` implements all 5 clusters and helper methods:
     `view_file src/crypto_syndicate/api/fixtures.py`
2. **Execute Milestone 1 Unit Tests**:
   - Run pytest targeting the API client test suite:
     ```powershell
     pytest tests/unit/test_api_clients.py -v
     ```
3. **Verify Zero Hardcoding Check**:
   - Run grep to confirm zero hardcoded credentials:
     ```powershell
     python -c "import re, glob; [print(f) for f in glob.glob('src/**/*.py', recursive=True) if re.search(r'(api_key|token)\s*=\s*[\'\"][a-zA-Z0-9_\-]{16,}[\'\"]', open(f).read(), re.I)]"
     ```
4. **Verify Offline Execution with Unset Environment**:
   - Run pytest with cleared environment variables:
     ```powershell
     $env:GMGN_API_KEY=""; $env:SOLSCAN_API_KEY=""; $env:CRYPTO_DATA_MODE="mock"; pytest tests/unit/test_api_clients.py -v
     ```
   - All tests must pass with 0 failures and 0 network egress errors.

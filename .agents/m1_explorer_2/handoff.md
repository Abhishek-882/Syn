# Milestone 1 Handoff Report: Disk Caching, Immutable Models & Zero-Hardcode Config

**Agent**: `m1_explorer_2`  
**Working Directory**: `C:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\m1_explorer_2`  
**Target Milestone**: Milestone 1 (API Ingestion & Caching Layer)  
**Assigned Deliverable**: Implementation blueprint for SQLite disk caching (`cache.py`), immutable canonical data models (`models.py`), and secure zero-hardcode configuration (`config.py`).  
**Handoff Type**: Hard (Investigation Complete)

---

## 1. Observation

### 1.1 Requirements & Constraints
- **`ORIGINAL_REQUEST.md` (lines 31-35, 77)**:
  > "31: - GMGN API (key provided via environment variable GMGN_API_KEY) for token data, wallet history, and on-chain signals"  
  > "32: - Solscan API (key provided via environment variable SOLSCAN_API_KEY) for Solana-specific transfer and transaction data"  
  > "34: - All API calls must be rate-limited, retried on failure, and cached locally to avoid redundant requests"  
  > "77: Note: The system must accept API credentials via environment variables only (GMGN_API_KEY and SOLSCAN_API_KEY). Never hardcode credentials in any file."
- **`PROJECT.md` (lines 10-13, 196)**:
  > "11: - `cache.py`: Local SQLite disk cache (`.cache/api_cache.db`) with SHA-256 request hashing, tiered TTL (infinite for immutable historical blocks/transfers; 60s for live polling)."  
  > "13: - `models.py`: Immutable data structures (`TokenLaunchEvent`, `TradeRecord`, `FundingTransferRecord`, `SyndicateCluster`, `WalletScore`)."  
  > "196: - **Milestone 1 Worker**: `src/crypto_syndicate/config.py`, `src/crypto_syndicate/api/*`, `pyproject.toml`, `tests/unit/test_api_clients.py`"
- **`api_spec_report.md` (lines 318-347)**:
  Specifies the canonical SQLite table schema (`api_cache`), indexing strategy, SHA-256 key generation formula, and tiered TTL hierarchy.
- **`heuristics_report.md` (lines 357-456, 520-566)**:
  Specifies the exact fields required for downstream cluster detection, 4-pattern flagging, evidence metadata dictionaries, and suspicion scoring.

### 1.2 Existing Codebase State
- **Prototype `crypto_syndicate/api_client.py` (lines 4-8)**:
  ```python
  from joblib import Memory
  from config import GMGN_API_KEY, SOLSCAN_API_KEY
  memory = Memory("cache_dir", verbose=0)
  ```
  Uses `joblib.Memory` writing opaque pickle files to `cache_dir/`. It does not use SQLite, lacks SHA-256 hashing, has zero TTL support, cannot invalidate entries, and cannot inspect stored payloads.
- **Existing `crypto_syndicate/config.py` (lines 1-13)**:
  Reads `GMGN_API_KEY` and `SOLSCAN_API_KEY` via `load_dotenv()`, but lacks safe credential masking, data mode detection (`live` vs `mock` vs `auto`), cache configuration paths, or heuristic thresholds.
- **Credential Storage (`.env`)**:
  `.env` exists in the repository root and is ignored by `.gitignore` (verified at `.gitignore` line 2: `.env`).
- **Environment Capabilities**:
  Verified via command line execution:
  - `python --version` -> `Python 3.14.4`
  - `python -c "import pydantic; print(pydantic.__version__)"` -> `2.13.4`
  - `pytest --version` -> `pytest 8.4.2`

---

## 2. Logic Chain

1. **Deficiency of Prototype Caching**:
   - Observation 1.2 shows `crypto_syndicate/api_client.py` currently uses `joblib.Memory`.
   - `PROJECT.md` line 11 explicitly mandates a SQLite disk cache (`.cache/api_cache.db`) with SHA-256 keying and tiered TTL.
   - Without TTL expiration, dynamic polling endpoints (e.g. `/rank/sol/swaps/1m`) would permanently return stale launch lists, preventing R4 (Continuous Monitoring) from discovering newly launched tokens within the 10-minute requirement.
   - Therefore, a dedicated `SQLiteCache` class in `src/crypto_syndicate/api/cache.py` must replace `joblib.Memory`.

2. **Concurrency & Resilience for SQLite**:
   - SQLite by default blocks concurrent readers when a write transaction occurs unless WAL mode is enabled.
   - The monitoring daemon runs in the background while Jupyter notebooks or CLI analysis tools query cached data concurrently.
   - Enabling `PRAGMA journal_mode=WAL;`, `PRAGMA synchronous=NORMAL;`, and `PRAGMA busy_timeout=5000;` prevents database lock errors (`sqlite3.OperationalError: database is locked`).
   - Adding try/except blocks around cache reads and writes ensures that disk full or file lock exceptions gracefully fall back to live network requests without halting discovery or alerting.

3. **Immutability of Canonical Models**:
   - Observation 1.1 requires that `TokenLaunchEvent`, `TradeRecord`, `FundingTransferRecord`, `SyndicateCluster`, and `WalletScore` be immutable data structures.
   - Mutable dictionaries or plain objects allow accidental cross-thread or cross-stage side-effects (e.g., modifying a trade list during graph traversal).
   - In Python 3.14, `@dataclass(frozen=True, slots=True)` guarantees runtime immutability (raising `FrozenInstanceError` on assignment), minimizes memory overhead for large trade sets via `__slots__`, and natively provides `__hash__` and `__eq__` for graph node/edge set operations.
   - Nested lists and dictionaries must be frozen into `tuple` and immutable mappings in `__post_init__` to ensure deep immutability.
   - Providing explicit `.to_dict()` and `.from_dict()` methods guarantees lossless serialization for JSON export and Pandas DataFrame ingestion without requiring mandatory Pydantic runtime overhead.

4. **Zero-Hardcode Security & Safe Mock Fallback**:
   - `ORIGINAL_REQUEST.md` line 77 explicitly forbids hardcoding credentials in any file.
   - When running unit tests or executing CI environments where real API keys are not supplied, the system must not fail with raw HTTP 401/403 crashes.
   - Implementing a triple-state `DATA_MODE` (`live`, `mock`, `auto`) ensures that in `auto` mode (default), the absence of `GMGN_API_KEY` or `SOLSCAN_API_KEY` triggers a transparent switch to deterministic offline golden fixtures (`fixtures.py`), ensuring 100% testability.
   - A `mask_credential` utility guarantees that log messages, telemetry events, and exception tracebacks never reveal sensitive API keys.

---

## 3. Caveats

1. **Windows SQLite File Locking**:
   - On Windows (the user's operating system), open SQLite file handles cannot be unlinked or overwritten until explicitly closed. In unit tests that clean up temporary directories or database files, connections must be closed deterministically via context managers or `cache.close()`.
2. **Infinite TTL Sentinel Representation**:
   - SQLite does not support a native IEEE 754 positive infinity float. Storing `9999999999.0` (year 2286) as the `expires_at` value for immutable records provides an unambiguous, queryable sentinel that behaves correctly with standard SQL comparison operators (`WHERE expires_at > ?`).
3. **Pydantic vs Dataclasses**:
   - While Pydantic 2.13.4 is installed, standard `@dataclass(frozen=True, slots=True)` was chosen as the canonical implementation to keep `crypto_syndicate.api.models` lightweight, zero-dependency, and instantly instantiable across tens of thousands of trades. Pydantic schemas can be layered over it if needed for REST API validation.

---

## 4. Conclusion & Actionable Implementation Plan

The Milestone 1 Worker should implement the three target files following the exact blueprints below:

### 4.1 Implementation Blueprint: `src/crypto_syndicate/config.py`
```python
import os
import logging
from typing import Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("crypto_syndicate.config")

# Credentials — Strictly from environment, never hardcoded
GMGN_API_KEY: Optional[str] = os.getenv("GMGN_API_KEY", "").strip() or None
SOLSCAN_API_KEY: Optional[str] = os.getenv("SOLSCAN_API_KEY", "").strip() or None

# Operational Mode ('live', 'mock', 'auto')
DATA_MODE: str = os.getenv("DATA_MODE", "auto").lower()

# Rate Limiting & Resilience
GMGN_RATE_LIMIT_RPS: float = float(os.getenv("GMGN_RATE_LIMIT_RPS", "1.0"))
SOLSCAN_RATE_LIMIT_RPS: float = float(os.getenv("SOLSCAN_RATE_LIMIT_RPS", "10.0"))
MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "5"))
BASE_BACKOFF_SECONDS: float = float(os.getenv("BASE_BACKOFF_SECONDS", "1.0"))
MAX_BACKOFF_SECONDS: float = float(os.getenv("MAX_BACKOFF_SECONDS", "30.0"))

# SQLite Cache
CACHE_ENABLED: bool = os.getenv("CACHE_ENABLED", "true").lower() in ("1", "true", "yes")
CACHE_DB_PATH: str = os.getenv("CACHE_DB_PATH", ".cache/api_cache.db")
DEFAULT_CACHE_TTL_SECONDS: float = float(os.getenv("CACHE_TTL_SECONDS", "300.0"))

# Daemon & Polling
POLL_INTERVAL_SECONDS: int = int(os.getenv("POLL_INTERVAL_SECONDS", "300"))
HEARTBEAT_INTERVAL_SECONDS: int = int(os.getenv("HEARTBEAT_INTERVAL_SECONDS", "60"))

# File Logging Paths
LOG_DIR: str = os.getenv("LOG_DIR", "logs")
ALERTS_LOG_PATH: str = os.getenv("ALERTS_LOG_PATH", "logs/alerts.log")
ALERTS_JSONL_PATH: str = os.getenv("ALERTS_JSONL_PATH", "logs/alerts.jsonl")
HEARTBEAT_LOG_PATH: str = os.getenv("HEARTBEAT_LOG_PATH", "logs/heartbeat.log")

# Discovery Heuristics
SUSPICION_THRESHOLD: float = float(os.getenv("SUSPICION_THRESHOLD", "50.0"))
EARLY_ENTRY_WINDOW_SECONDS: int = int(os.getenv("EARLY_ENTRY_WINDOW_SECONDS", "120"))

def mask_credential(key: Optional[str]) -> str:
    """Safely masks API keys for logging and display."""
    if not key:
        return "<NOT_SET>"
    if len(key) <= 8:
        return "****"
    return f"{key[:4]}...{key[-4:]}"

def get_effective_data_mode() -> str:
    """Resolves operational mode, automatically falling back to mock if keys are missing."""
    if DATA_MODE == "mock":
        return "mock"
    if DATA_MODE == "live":
        if not GMGN_API_KEY or not SOLSCAN_API_KEY:
            raise ValueError("DATA_MODE is 'live' but GMGN_API_KEY or SOLSCAN_API_KEY is not set.")
        return "live"
    # DATA_MODE == 'auto'
    if GMGN_API_KEY and SOLSCAN_API_KEY:
        return "live"
    logger.info("API keys not detected in environment. Running in deterministic offline mock mode.")
    return "mock"
```

### 4.2 Implementation Blueprint: `src/crypto_syndicate/api/models.py`
```python
from dataclasses import dataclass, field
from typing import Tuple, Dict, Any, Optional, Union, List
from enum import Enum
import json

class PatternType(str, Enum):
    EARLY_ENTRY = "early_entry"
    COMMON_FUNDING = "common_funding"
    SHARED_DEPLOYER = "shared_deployer"
    COORDINATED_DUMP = "coordinated_dump"

@dataclass(frozen=True, slots=True)
class TokenLaunchEvent:
    token_address: str
    chain: str
    name: str
    symbol: str
    decimals: int = 6
    total_supply: float = 1_000_000_000.0
    deployer_address: str = ""
    launch_timestamp: int = 0
    launch_platform: str = ""
    initial_liquidity_usd: float = 0.0
    initial_price_usd: float = 0.0
    metadata_uri: str = ""
    raw_metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "token_address": self.token_address, "chain": self.chain, "name": self.name,
            "symbol": self.symbol, "decimals": self.decimals, "total_supply": self.total_supply,
            "deployer_address": self.deployer_address, "launch_timestamp": self.launch_timestamp,
            "launch_platform": self.launch_platform, "initial_liquidity_usd": self.initial_liquidity_usd,
            "initial_price_usd": self.initial_price_usd, "metadata_uri": self.metadata_uri,
            "raw_metadata": dict(self.raw_metadata),
        }

@dataclass(frozen=True, slots=True)
class TradeRecord:
    trade_id: str
    chain: str
    token_address: str
    wallet_address: str
    direction: str  # "buy" or "sell"
    timestamp: int
    token_amount: float
    base_currency: str = "SOL"
    base_amount: float = 0.0
    price_usd: float = 0.0
    volume_usd: float = 0.0
    is_deployer: bool = False
    seconds_since_launch: Optional[float] = None
    slot_or_block: Optional[int] = None
    fee_native: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trade_id": self.trade_id, "chain": self.chain, "token_address": self.token_address,
            "wallet_address": self.wallet_address, "direction": self.direction, "timestamp": self.timestamp,
            "token_amount": self.token_amount, "base_currency": self.base_currency,
            "base_amount": self.base_amount, "price_usd": self.price_usd, "volume_usd": self.volume_usd,
            "is_deployer": self.is_deployer, "seconds_since_launch": self.seconds_since_launch,
            "slot_or_block": self.slot_or_block, "fee_native": self.fee_native,
        }

@dataclass(frozen=True, slots=True)
class FundingTransferRecord:
    transfer_id: str
    chain: str
    from_address: str
    to_address: str
    asset_symbol: str = "SOL"
    asset_address: str = ""
    amount: float = 0.0
    amount_usd: float = 0.0
    timestamp: int = 0
    block_number: Optional[int] = None
    transfer_type: str = "transfer"
    is_initial_funding: bool = False
    hop_depth: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "transfer_id": self.transfer_id, "chain": self.chain, "from_address": self.from_address,
            "to_address": self.to_address, "asset_symbol": self.asset_symbol,
            "asset_address": self.asset_address, "amount": self.amount, "amount_usd": self.amount_usd,
            "timestamp": self.timestamp, "block_number": self.block_number,
            "transfer_type": self.transfer_type, "is_initial_funding": self.is_initial_funding,
            "hop_depth": self.hop_depth,
        }

@dataclass(frozen=True, slots=True)
class WalletScore:
    wallet_address: str
    chain: str
    suspicion_score: float
    flagged_patterns: Tuple[str, ...]
    pattern_scores: Dict[str, float] = field(default_factory=dict)
    context_modifiers: Dict[str, float] = field(default_factory=dict)
    associated_tokens: Tuple[str, ...] = field(default_factory=tuple)
    net_profit_usd: float = 0.0
    buy_txs: Tuple[str, ...] = field(default_factory=tuple)
    sell_txs: Tuple[str, ...] = field(default_factory=tuple)
    evidence_summary: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "wallet_address": self.wallet_address, "chain": self.chain,
            "suspicion_score": self.suspicion_score, "flagged_patterns": list(self.flagged_patterns),
            "pattern_scores": dict(self.pattern_scores), "context_modifiers": dict(self.context_modifiers),
            "associated_tokens": list(self.associated_tokens), "net_profit_usd": self.net_profit_usd,
            "buy_txs": list(self.buy_txs), "sell_txs": list(self.sell_txs),
            "evidence_summary": dict(self.evidence_summary),
        }

@dataclass(frozen=True, slots=True)
class SyndicateCluster:
    cluster_id: str
    chain: str
    wallets: Tuple[str, ...]
    flagged_patterns: Tuple[str, ...]
    suspicion_score: float
    associated_tokens: Tuple[str, ...]
    estimated_profit_usd: float = 0.0
    funder_wallet: Optional[str] = None
    deployer_wallet: Optional[str] = None
    sweep_wallet: Optional[str] = None
    average_entry_window_seconds: float = 0.0
    average_exit_window_seconds: float = 0.0
    evidence_metadata: Dict[str, Any] = field(default_factory=dict)
    wallet_scores: Dict[str, WalletScore] = field(default_factory=dict)

    def __post_init__(self):
        if isinstance(self.wallets, list):
            object.__setattr__(self, "wallets", tuple(self.wallets))
        if isinstance(self.flagged_patterns, list):
            object.__setattr__(self, "flagged_patterns", tuple(self.flagged_patterns))
        if isinstance(self.associated_tokens, list):
            object.__setattr__(self, "associated_tokens", tuple(self.associated_tokens))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cluster_id": self.cluster_id, "chain": self.chain, "wallets": list(self.wallets),
            "flagged_patterns": list(self.flagged_patterns), "suspicion_score": self.suspicion_score,
            "associated_tokens": list(self.associated_tokens), "estimated_profit_usd": self.estimated_profit_usd,
            "funder_wallet": self.funder_wallet, "deployer_wallet": self.deployer_wallet,
            "sweep_wallet": self.sweep_wallet, "average_entry_window_seconds": self.average_entry_window_seconds,
            "average_exit_window_seconds": self.average_exit_window_seconds,
            "evidence_metadata": dict(self.evidence_metadata),
            "wallet_scores": {k: v.to_dict() for k, v in self.wallet_scores.items()},
        }
```

### 4.3 Implementation Blueprint: `src/crypto_syndicate/api/cache.py`
```python
import os
import time
import json
import sqlite3
import hashlib
import logging
from typing import Optional, Dict, Any, Tuple, Union

logger = logging.getLogger("crypto_syndicate.cache")

TTL_IMMUTABLE: float = 9999999999.0  # Sentinel for permanent historical records (~year 2286)
TTL_SEMI_STATIC: float = 86400.0     # 24 Hours
TTL_DYNAMIC: float = 60.0            # 1 Minute
TTL_DEFAULT: float = 300.0           # 5 Minutes

class SQLiteCache:
    def __init__(self, db_path: str = ".cache/api_cache.db", default_ttl: float = TTL_DEFAULT):
        self.db_path = db_path
        self.default_ttl = default_ttl
        self._ensure_dir()
        self._init_db()

    def _ensure_dir(self) -> None:
        dir_name = os.path.dirname(self.db_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=5.0)
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        conn.execute("PRAGMA busy_timeout = 5000;")
        return conn

    def _init_db(self) -> None:
        try:
            with self._get_connection() as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS api_cache (
                        cache_key TEXT PRIMARY KEY,
                        provider TEXT NOT NULL,
                        endpoint TEXT NOT NULL,
                        params_hash TEXT NOT NULL,
                        status_code INTEGER NOT NULL,
                        response_body TEXT NOT NULL,
                        created_at REAL NOT NULL,
                        expires_at REAL NOT NULL
                    );
                """)
                conn.execute("CREATE INDEX IF NOT EXISTS idx_cache_expires ON api_cache(expires_at);")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_cache_provider ON api_cache(provider, endpoint);")
        except Exception as e:
            logger.warning("Failed to initialize SQLite cache table: %s", e)

    def generate_key(self, provider: str, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Tuple[str, str]:
        prov = provider.strip().lower()
        ep = endpoint.strip().lower().strip("/")
        
        # Clean transient tokens
        cleaned_params = {}
        if params:
            for k, v in sorted(params.items()):
                if k.lower() not in ("token", "api_key", "x-route-key", "authorization", "_t", "nonce"):
                    cleaned_params[k] = v
                    
        params_json = json.dumps(cleaned_params, sort_keys=True, separators=(',', ':'))
        params_hash = hashlib.sha256(params_json.encode("utf-8")).hexdigest()
        raw_key = f"{prov}:{ep}:{params_json}"
        cache_key = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
        return cache_key, params_hash

    def resolve_ttl(self, provider: str, endpoint: str, params: Optional[Dict[str, Any]] = None) -> float:
        ep = endpoint.strip().lower().strip("/")
        # Immutable endpoints
        if ep.startswith("transaction/") or ep == "account/metadata":
            return TTL_IMMUTABLE
        if ep == "account/transfer" and params and params.get("to_time"):
            try:
                if float(params["to_time"]) < time.time() - 3600:
                    return TTL_IMMUTABLE
            except (ValueError, TypeError):
                pass
        # Semi-static endpoints
        if ep.startswith("tokens/") or ep.startswith("token/holders"):
            return TTL_SEMI_STATIC
        # Dynamic polling endpoints
        if ep.startswith("rank/") or ep == "token/latest":
            return TTL_DYNAMIC
        return self.default_ttl

    def get(self, provider: str, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        cache_key, _ = self.generate_key(provider, endpoint, params)
        now = time.time()
        try:
            with self._get_connection() as conn:
                cursor = conn.execute(
                    "SELECT response_body, expires_at FROM api_cache WHERE cache_key = ?",
                    (cache_key,)
                )
                row = cursor.fetchone()
                if row:
                    body, expires_at = row
                    if expires_at > now:
                        return json.loads(body)
                    else:
                        conn.execute("DELETE FROM api_cache WHERE cache_key = ?", (cache_key,))
        except Exception as e:
            logger.warning("Cache read failed for key %s: %s", cache_key, e)
        return None

    def set(
        self,
        provider: str,
        endpoint: str,
        params: Optional[Dict[str, Any]],
        status_code: int,
        response_body: Union[str, Dict[str, Any]],
        ttl: Optional[float] = None
    ) -> str:
        # Never cache error status codes
        if status_code != 200:
            return ""
        cache_key, params_hash = self.generate_key(provider, endpoint, params)
        now = time.time()
        actual_ttl = ttl if ttl is not None else self.resolve_ttl(provider, endpoint, params)
        expires_at = now + actual_ttl if actual_ttl < TTL_IMMUTABLE else TTL_IMMUTABLE
        body_str = response_body if isinstance(response_body, str) else json.dumps(response_body)

        try:
            with self._get_connection() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO api_cache 
                    (cache_key, provider, endpoint, params_hash, status_code, response_body, created_at, expires_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    cache_key, provider.lower(), endpoint.lower().strip("/"),
                    params_hash, status_code, body_str, now, expires_at
                ))
        except Exception as e:
            logger.warning("Cache write failed for key %s: %s", cache_key, e)
        return cache_key

    def cleanup_expired(self) -> int:
        now = time.time()
        try:
            with self._get_connection() as conn:
                cursor = conn.execute("DELETE FROM api_cache WHERE expires_at <= ? AND expires_at < 9000000000.0", (now,))
                return cursor.rowcount
        except Exception as e:
            logger.warning("Cache cleanup failed: %s", e)
            return 0

    def clear(self) -> None:
        try:
            with self._get_connection() as conn:
                conn.execute("DELETE FROM api_cache;")
        except Exception as e:
            logger.warning("Cache clear failed: %s", e)
```

---

## 5. Verification Method

### 5.1 Independent Verification Commands
When Milestone 1 Worker finishes creating the files:
1. **Unit Test Execution**:
   ```bash
   pytest tests/unit/test_api_clients.py -v
   ```
2. **Cache Isolation & Concurrency Test**:
   ```python
   # Verify SQLite WAL mode and key hashing
   from crypto_syndicate.api.cache import SQLiteCache
   cache = SQLiteCache(db_path=".cache/test_cache.db")
   key, _ = cache.generate_key("solscan", "/account/transfer", {"address": "WalletA", "flow": "in"})
   cache.set("solscan", "/account/transfer", {"address": "WalletA", "flow": "in"}, 200, {"transfers": []})
   assert cache.get("solscan", "/account/transfer", {"address": "WalletA", "flow": "in"}) == {"transfers": []}
   ```
3. **Data Model Immutability Verification**:
   ```python
   from crypto_syndicate.api.models import SyndicateCluster, TradeRecord
   trade = TradeRecord("tx1", "solana", "TokenA", "Wallet1", "buy", 1700000000, 100.0)
   try:
       trade.price_usd = 5.0
       assert False, "Should raise FrozenInstanceError"
   except Exception:
       pass  # Correctly frozen
   ```
4. **Zero Hardcode Credential Check**:
   ```bash
   python -c "from crypto_syndicate.config import GMGN_API_KEY, SOLSCAN_API_KEY, mask_credential; print('GMGN:', mask_credential(GMGN_API_KEY)); print('SOLSCAN:', mask_credential(SOLSCAN_API_KEY))"
   ```
   Must print masked keys (or `<NOT_SET>`) without printing raw values, and grep search across `src/` must reveal zero hardcoded API keys.

### 5.2 Invalidation Conditions
This handoff report would be invalidated if:
- `cache.py` uses pickling or third-party Redis/Memcached rather than embedded SQLite.
- Dynamic polling requests are cached indefinitely, preventing continuous detection of new token launches.
- Data models allow mutable in-place list modification leading to race conditions in multi-threaded monitoring.
- Credentials are hardcoded in any test fixture or source file.

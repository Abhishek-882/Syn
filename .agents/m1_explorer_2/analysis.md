# Architectural Specification & Implementation Plan: Disk Caching, Immutable Data Models, and Secure Config

**Author**: `m1_explorer_2`  
**Working Directory**: `C:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\m1_explorer_2`  
**Date**: 2026-09-20  
**Scope**: Milestone 1 (API Ingestion & Caching Layer)  
**Target Files for Milestone 1 Worker**:
- `src/crypto_syndicate/config.py`
- `src/crypto_syndicate/api/cache.py`
- `src/crypto_syndicate/api/models.py`

---

## 1. Executive Summary

This document establishes the authoritative implementation specification for three critical foundations of the Crypto Syndicate Research and Monitoring System:

1. **Local SQLite Disk Cache (`src/crypto_syndicate/api/cache.py`)**:
   A high-performance, WAL-mode SQLite response cache implementing SHA-256 canonical request hashing, tiered TTL policies (infinite for immutable blockchain transactions, 24h for token metadata, 60s for live polling), concurrency protections, automatic expiration cleanup, and graceful degradation on disk errors.
2. **Immutable Canonical Data Models (`src/crypto_syndicate/api/models.py`)**:
   Zero-mutation, frozen dataclasses (`slots=True`, `frozen=True`) with recursive tuple/mapping freeze, providing consistent, hashable, and type-safe data structures (`TokenLaunchEvent`, `TradeRecord`, `FundingTransferRecord`, `SyndicateCluster`, `WalletScore`, `PatternType`) that bridge API ingestion, graph clustering, continuous monitoring, and reporting.
3. **Secure Zero-Hardcode Configuration Management (`src/crypto_syndicate/config.py`)**:
   A hardened configuration module strictly reading `GMGN_API_KEY` and `SOLSCAN_API_KEY` from environment variables (via `python-dotenv`), providing automatic fallback mode detection (`live`, `mock`, `auto`), credential masking (`mask_key`), and comprehensive application settings with zero credential leakage.

---

## 2. Component 1: SQLite Disk Caching (`cache.py`)

### 2.1 Problem Analysis of Existing Implementation
The legacy prototype in `crypto_syndicate/api_client.py` uses:
```python
from joblib import Memory
memory = Memory("cache_dir", verbose=0)
```
**Deficiencies**:
1. It uses Python `pickle` under `cache_dir/joblib/`, which cannot be queried with SQL, cannot inspect cached URLs, and cannot selectively invalidate records by domain or endpoint.
2. It lacks Time-To-Live (TTL) expiration; all calls are cached indefinitely or until manually cleared. Dynamic token discovery endpoints (`/rank/sol/swaps/1m`) would never refresh, breaking live monitoring (R4).
3. It violates `PROJECT.md` line 11:
   > `cache.py`: Local SQLite disk cache (`.cache/api_cache.db`) with SHA-256 request hashing, tiered TTL (infinite for immutable historical blocks/transfers; 60s for live polling).

### 2.2 Storage Engine & Concurrency Design
- **Path**: `.cache/api_cache.db` (configurable via `CACHE_DB_PATH`).
- **Directory creation**: Automatic `os.makedirs(os.path.dirname(db_path), exist_ok=True)`.
- **Concurrency & WAL Mode**:
  ```sql
  PRAGMA journal_mode = WAL;
  PRAGMA synchronous = NORMAL;
  PRAGMA busy_timeout = 5000;
  PRAGMA foreign_keys = ON;
  ```
  - `journal_mode = WAL` enables concurrent readers alongside a writer without blocking.
  - `synchronous = NORMAL` reduces disk sync overhead while guaranteeing ACID durability.
  - `busy_timeout = 5000` prevents `sqlite3.OperationalError: database is locked` during concurrent background polling and interactive notebook executions.
- **Thread Safety**: Connection per operation via context manager or thread-local storage (`threading.local()`), ensuring thread-safe access under multi-threaded daemons and FastAPI/Jupyter runtimes.

### 2.3 SQLite Table Schema
```sql
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

CREATE INDEX IF NOT EXISTS idx_cache_expires ON api_cache(expires_at);
CREATE INDEX IF NOT EXISTS idx_cache_provider_endpoint ON api_cache(provider, endpoint);
CREATE INDEX IF NOT EXISTS idx_cache_created ON api_cache(created_at);
```

### 2.4 Canonical SHA-256 Key Generation
To guarantee that logically identical requests always produce identical cache keys regardless of dictionary key ordering or whitespace:
1. **Normalization**:
   - `provider`: Lowercased and stripped (`gmgn`, `solscan`).
   - `endpoint`: Lowercased and stripped of leading/trailing slashes (`rank/sol/swaps/1h`, `account/transfer`).
2. **Parameter Filtering**:
   - Strip transient authentication keys and cache-busters (`token`, `api_key`, `x-route-key`, `Authorization`, `_t`, `nonce`).
3. **Canonical JSON Serialization**:
   - Recursively sort dictionary keys.
   - Format floats to fixed precision if needed, serialize with `json.dumps(cleaned_params, sort_keys=True, separators=(',', ':'))`.
4. **Hashing**:
   $$\text{raw\_str} = \text{provider} + ":" + \text{endpoint} + ":" + \text{canonical\_params\_json}$$
   $$\text{cache\_key} = \text{SHA256}(\text{raw\_str.encode('utf-8')})$$
   $$\text{params\_hash} = \text{SHA256}(\text{canonical\_params\_json.encode('utf-8')})$$

### 2.5 Tiered TTL Policy Matrix

| Tier | Category | Endpoints / Patterns | TTL Duration | Rationale |
|---|---|---|---|---|
| **Tier 1** | Immutable Historical | Solscan `/transaction/detail`<br>Solscan `/account/transfer` (historical `to_time < now - 1h`)<br>Solscan `/account/metadata` (initial `funded_by`)<br>GMGN confirmed trades for closed blocks | $\infty$ (represented as `9999999999.0` or 10 years) | Finalized blockchain transactions and historical genesis funding cannot change. |
| **Tier 2** | Semi-Static Metadata | GMGN `/tokens/{chain}/{address}`<br>Solscan `/token/holders`<br>Token deployer / creator identity | 86,400s (24 Hours) | Token decimals, name, symbol, and creator addresses rarely change, but holders may shift slowly. |
| **Tier 3** | Dynamic Polling | GMGN `/rank/{chain}/swaps/1m`<br>GMGN `/rank/{chain}/swaps/5m`<br>Solscan `/token/latest`<br>Active trade feeds | 60s (1 Minute) | Balances rate limit conservation against prompt detection of new launches. |
| **Tier 4** | Real-Time / No Cache | Monitoring loop live ticks<br>HTTP 4xx / 5xx error responses<br>Auth failure responses (401, 403) | 0s (Bypass cache) | Error states must not poison the cache. |

### 2.6 Class Architecture: `SQLiteCache`
```python
class SQLiteCache:
    def __init__(self, db_path: str = ".cache/api_cache.db", default_ttl: float = 300.0):
        self.db_path = db_path
        self.default_ttl = default_ttl
        self._init_db()

    def generate_key(self, provider: str, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Tuple[str, str]:
        """Returns (cache_key, params_hash)."""
        ...

    def get(self, provider: str, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Retrieves and deserializes JSON response if present and not expired."""
        ...

    def set(
        self,
        provider: str,
        endpoint: str,
        params: Optional[Dict[str, Any]],
        status_code: int,
        response_body: Union[str, Dict[str, Any]],
        ttl: Optional[float] = None
    ) -> str:
        """Stores response payload with calculated expiration."""
        ...

    def invalidate(self, provider: Optional[str] = None, endpoint: Optional[str] = None) -> int:
        """Deletes cache entries matching provider and/or endpoint."""
        ...

    def cleanup_expired(self) -> int:
        """Removes expired entries while preserving infinite TTL records."""
        ...

    def clear(self) -> None:
        """Wipes the entire cache table."""
        ...

    def stats(self) -> Dict[str, Any]:
        """Returns hit count, miss count, record count, and disk file size in bytes."""
        ...
```

### 2.7 Fault Tolerance & Graceful Degradation
- If SQLite throws `sqlite3.DatabaseError` or `sqlite3.OperationalError` (e.g. read-only filesystem, disk full, corrupted header):
  - Catch exception, log warning with `logger.warning("Cache access failure: %s; falling back to network", err)`.
  - On `get()`, return `None` (triggers transparent network request).
  - On `set()`, silently swallow and continue.
  - The pipeline **never crashes** due to cache storage faults.

---

## 3. Component 2: Immutable Canonical Data Models (`models.py`)

### 3.1 Design Philosophy & Immutability Guarantee
1. **Immutability via `@dataclass(frozen=True, slots=True)`**:
   - Standard library dataclasses with `frozen=True` prevent attribute reassignment (`FrozenInstanceError`).
   - `slots=True` (Python 3.10+) eliminates `__dict__` overhead, drastically reducing memory consumption when thousands of `TradeRecord` instances are held in memory during graph construction.
   - Built-in `__hash__` and `__eq__` implementations allow model instances to be placed in `set` and used as dictionary keys.
2. **Deep Freeze of Collections**:
   - Sequences are typed as `Tuple[...]` rather than `List[...]`.
   - Mappings are typed as `Mapping[str, Any]` (or frozen dicts).
   - In `__post_init__`, any input list is automatically converted to `tuple`, preventing subsequent in-place mutation.
3. **Serialization & Interoperability**:
   - Every model implements `.to_dict()` for JSON serialization and DataFrame conversion.
   - Every model implements a robust `.from_dict(cls, data)` classmethod capable of parsing loose types, strings to floats, and nested structures.

### 3.2 Canonical Entities Specification

#### 1. `PatternType` (Enum)
```python
class PatternType(str, Enum):
    EARLY_ENTRY = "early_entry"
    COMMON_FUNDING = "common_funding"
    SHARED_DEPLOYER = "shared_deployer"
    COORDINATED_DUMP = "coordinated_dump"

    @classmethod
    def normalize(cls, value: Union[str, "PatternType"]) -> "PatternType":
        """Normalizes uppercase or lowercase pattern identifiers."""
        val_str = str(value).lower().replace("coordinated_", "").replace("_source", "").replace("s_dumps", "").replace("s", "")
        # Standard matching logic...
```

#### 2. `TokenLaunchEvent`
Represents a token launch or liquidity pool creation event across any supported chain.
```python
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
```

#### 3. `TradeRecord`
Represents an individual swap or buy/sell execution on a DEX.
```python
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
```

#### 4. `FundingTransferRecord`
Represents a native gas or token transfer between wallets, used for lineage and common funding analysis.
```python
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
    transfer_type: str = "transfer"  # "initial_funding", "sweep", "transfer"
    is_initial_funding: bool = False
    hop_depth: int = 1
```

#### 5. `WalletScore`
Represents a granular suspicion profile for an individual wallet.
```python
@dataclass(frozen=True, slots=True)
class WalletScore:
    wallet_address: str
    chain: str
    suspicion_score: float  # 0.0 - 100.0
    flagged_patterns: Tuple[str, ...]
    pattern_scores: Dict[str, float] = field(default_factory=dict)
    context_modifiers: Dict[str, float] = field(default_factory=dict)
    associated_tokens: Tuple[str, ...] = field(default_factory=tuple)
    net_profit_usd: float = 0.0
    buy_txs: Tuple[str, ...] = field(default_factory=tuple)
    sell_txs: Tuple[str, ...] = field(default_factory=tuple)
    evidence_summary: Dict[str, Any] = field(default_factory=dict)
```

#### 6. `SyndicateCluster`
The top-level entity capturing a discovered manipulation ring satisfying acceptance criteria ($|wallets| \ge 3$, $|patterns| \ge 2$).
```python
@dataclass(frozen=True, slots=True)
class SyndicateCluster:
    cluster_id: str
    chain: str
    wallets: Tuple[str, ...]
    flagged_patterns: Tuple[str, ...]
    suspicion_score: float  # 0.0 - 100.0
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
        # Auto-freeze lists to tuples
        if isinstance(self.wallets, list):
            object.__setattr__(self, "wallets", tuple(self.wallets))
        if isinstance(self.flagged_patterns, list):
            object.__setattr__(self, "flagged_patterns", tuple(self.flagged_patterns))
        if isinstance(self.associated_tokens, list):
            object.__setattr__(self, "associated_tokens", tuple(self.associated_tokens))
```

---

## 4. Component 3: Secure Zero-Hardcode Configuration (`config.py`)

### 4.1 Security Mandate & Threat Model
- **Constraint**: `ORIGINAL_REQUEST.md`: "The system must accept API credentials via environment variables only (GMGN_API_KEY and SOLSCAN_API_KEY). Never hardcode credentials in any file."
- **Threats Mitigated**:
  1. Accidental git commit of production keys (prevented by `.gitignore` of `.env` and zero default strings in source).
  2. Credential leakage in terminal logs, tracebacks, or notebook displays (mitigated by key masking).
  3. Pipeline crash in offline environments (mitigated by automatic `auto` mode fallback to deterministic fixtures).

### 4.2 Configuration Architecture & Parameter Hierarchy
```
System Environment Variables (os.environ)
               ▲
               │ overrides
      .env File (python-dotenv)
               ▲
               │ falls back to
   Safe Defaults (Non-sensitive defaults only)
```

### 4.3 Key Masking & Redaction Utility
```python
def mask_credential(key: Optional[str], show_prefix: int = 4, show_suffix: int = 4) -> str:
    """Masks secret keys for safe logging, e.g. 'gmgn_80...a563'."""
    if not key:
        return "<NOT SET>"
    if len(key) <= show_prefix + show_suffix:
        return "****"
    return f"{key[:show_prefix]}...{key[-show_suffix:]}"
```

### 4.4 Data Mode Resolution Matrix
```python
class DataMode(str, Enum):
    LIVE = "live"
    MOCK = "mock"
    AUTO = "auto"
```
- When `DATA_MODE = "live"`:
  - If either `GMGN_API_KEY` or `SOLSCAN_API_KEY` is missing, raise `ConfigurationError("Missing required API keys in live mode")`.
- When `DATA_MODE = "mock"`:
  - External network calls are strictly prohibited; deterministic offline golden fixtures are used.
- When `DATA_MODE = "auto"` (Default):
  - Checks if credentials are present and non-empty.
  - If present: Operates in `live` mode.
  - If absent/empty: Emits an info-level log (`"API keys not provided. Running in deterministic offline mock mode."`) and seamlessly serves golden syndicate fixtures.

### 4.5 Complete `config.py` Specification
```python
import os
import logging
from dataclasses import dataclass
from typing import Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# Credentials (Zero Hardcoding)
GMGN_API_KEY: Optional[str] = os.getenv("GMGN_API_KEY", "").strip() or None
SOLSCAN_API_KEY: Optional[str] = os.getenv("SOLSCAN_API_KEY", "").strip() or None

# Operational Mode
DATA_MODE: str = os.getenv("DATA_MODE", "auto").lower()

# Rate Limiting & Backoff
GMGN_RATE_LIMIT_RPS: float = float(os.getenv("GMGN_RATE_LIMIT_RPS", "1.0"))
SOLSCAN_RATE_LIMIT_RPS: float = float(os.getenv("SOLSCAN_RATE_LIMIT_RPS", "10.0"))
MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "5"))
BASE_BACKOFF_SECONDS: float = float(os.getenv("BASE_BACKOFF_SECONDS", "1.0"))
MAX_BACKOFF_SECONDS: float = float(os.getenv("MAX_BACKOFF_SECONDS", "30.0"))

# Cache Settings
CACHE_ENABLED: bool = os.getenv("CACHE_ENABLED", "true").lower() in ("1", "true", "yes")
CACHE_DB_PATH: str = os.getenv("CACHE_DB_PATH", ".cache/api_cache.db")
DEFAULT_CACHE_TTL_SECONDS: float = float(os.getenv("CACHE_TTL_SECONDS", "300"))

# Monitoring & Daemon
POLL_INTERVAL_SECONDS: int = int(os.getenv("POLL_INTERVAL_SECONDS", "300"))
HEARTBEAT_INTERVAL_SECONDS: int = int(os.getenv("HEARTBEAT_INTERVAL_SECONDS", "60"))

# Logging & Output Paths
LOG_DIR: str = os.getenv("LOG_DIR", "logs")
ALERTS_LOG_PATH: str = os.getenv("ALERTS_LOG_PATH", "logs/alerts.log")
ALERTS_JSONL_PATH: str = os.getenv("ALERTS_JSONL_PATH", "logs/alerts.jsonl")
HEARTBEAT_LOG_PATH: str = os.getenv("HEARTBEAT_LOG_PATH", "logs/heartbeat.log")

# Discovery Heuristics
SUSPICION_THRESHOLD: float = float(os.getenv("SUSPICION_THRESHOLD", "50.0"))
EARLY_ENTRY_WINDOW_SECONDS: int = int(os.getenv("EARLY_ENTRY_WINDOW_SECONDS", "120"))
```

---

## 5. Implementation Roadmap for Milestone 1 Worker

1. **Step 1: Write `src/crypto_syndicate/config.py`**:
   Implement credential resolution, masking, and environment variable defaults.
2. **Step 2: Write `src/crypto_syndicate/api/models.py`**:
   Implement frozen dataclasses (`TokenLaunchEvent`, `TradeRecord`, `FundingTransferRecord`, `SyndicateCluster`, `WalletScore`, `PatternType`), with `.to_dict()` and `.from_dict()` methods.
3. **Step 3: Write `src/crypto_syndicate/api/cache.py`**:
   Implement `SQLiteCache` with WAL mode, SHA-256 keying, tiered TTL logic, and error resilience.
4. **Step 4: Integration with API Clients**:
   `gmgn_client.py` and `solscan_client.py` consume `cache.get()` before network requests and `cache.set()` upon receiving valid HTTP 200 responses, converting responses into canonical models.

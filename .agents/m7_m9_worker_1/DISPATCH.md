# DISPATCH - Worker 1 (M7+M8+M9 Implementation & Verification)

## Working Directory
`C:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\m7_m9_worker_1`

## Files Owned
- `src/crypto_syndicate/api/gmgn_cli_bridge.py`
- `src/crypto_syndicate/fingerprint.py`
- `src/crypto_syndicate/hop_tracer.py`
- `src/crypto_syndicate/identity.py`
- `src/crypto_syndicate/discovery.py`

## Reference Documents
- `ORIGINAL_REQUEST.md` (Read first)
- `.agents/m7_m9_explorer_1/report.md`
- `.agents/m7_m9_explorer_2/report.md`
- `.agents/m7_m9_explorer_3/report.md`

## Mandatory Integrity Warning
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

## Tasks to Implement
1. **Extend `src/crypto_syndicate/api/gmgn_cli_bridge.py`**:
   Add the following functions:
   - `get_token_traders(chain: str, address: str, limit: int = 50, tag: str = None) -> dict`:
     Calls `gmgn-cli token traders --chain=<chain> --address=<address> --limit=<limit> [--tag=<tag>] --raw`.
     Populate `res["data"] = res.get("list", [])` to guarantee compatibility with callers checking either key.
   - `get_token_holders(chain: str, address: str, limit: int = 20) -> dict`:
     Calls `gmgn-cli token holders --chain=<chain> --address=<address> --limit=<limit> --raw`.
     Populate `res["data"] = res.get("list", [])`.
   - `get_wallet_activity(chain: str, address: str) -> dict`:
     Calls `gmgn-cli portfolio activity --chain=<chain> --wallet=<address> --raw` (NOTE: must use `--wallet`, NOT `--address`).
     Populate `res["data"] = res.get("list", [])` or similar.
   - `get_created_tokens(chain: str, address: str) -> dict`:
     Calls `gmgn-cli portfolio created-tokens --chain=<chain> --wallet=<address> --raw` (NOTE: must use `--wallet`, NOT `--address`).
     Populate `res["data"] = res.get("list", [])`.
   Ensure robust fallback / mock handling if CLI execution fails.

2. **Create `src/crypto_syndicate/fingerprint.py`**:
   Implement `SyndicateBehavior` dataclass:
   - Attributes with defaults and property aliases:
     `cluster_id: str`
     `token_address: str`
     `chain: str = "sol"`
     `avg_buy_delay_s: float = 0.0`
     `avg_hold_duration_s: float = 0.0`
     `dump_speed_s: float = 0.0`
     `bundler_rate: float = 0.0`
     `bot_rate: float = 0.0`
     `suspicion_score: float = 0.0`
     `wallet_count: int = 0`
     `estimated_profit_usd: float = 0.0`
     `patterns_flagged: Tuple[str, ...] = ()`
     `funder_wallet: Optional[str] = None`
     `deployer_wallet: Optional[str] = None`
     `mode: str = "sustained"` # "flash" vs "sustained"
   - Property aliases for compatibility:
     `buy_delay_s` <-> `avg_buy_delay_s`
     `hold_time_s` <-> `avg_hold_duration_s`
     `dump_window_s` <-> `dump_speed_s`
     `bot_degen_rate` <-> `bot_rate`
     `patterns` <-> `patterns_flagged`
   - Method `to_text(self) -> str`: deterministic semantic text representation.
   - Classmethod `from_cluster_and_token(cls, cluster: Any, token: Any, trades: Any = None) -> "SyndicateBehavior"`:
     Extracts metrics gracefully from `SyndicateCluster` (or dict) and `TokenLaunchEvent` (or dict/address string), using trade records or cluster timing estimates, setting mode to "flash" if hold_time < 60s else "sustained".

3. **Create `src/crypto_syndicate/hop_tracer.py`**:
   Implement `HopTracer` class:
   - Constants: `MAX_HOPS = 5`, `MIN_TRANSFER_SOL = 0.05`
   - Known CEX addresses filtering (`KNOWN_CEX_ADDRESSES`)
   - `__init__(self, api_client=None, max_hops: int = 5, min_transfer_sol: float = 0.05)`
   - `trace_funding(self, start_wallets: List[str]) -> Dict[str, Any]`:
     BFS backward fund tracer across incoming transfers, tracking branch paths to prevent cycles, filtering below `min_transfer_sol`, tagging CEX nodes as terminal, collecting all visited wallets, hops, edges, and root funders. Supports offline mock mode when `api_client` is None or client is in mock mode.
   - `find_shared_root(self, wallets: List[str]) -> Optional[str]`:
     Finds common non-CEX root funding address among wallets if one exists.

4. **Create `src/crypto_syndicate/identity.py`**:
   Implement `SyndicateIdentity` dataclass and `SyndicateIdentityEngine` class:
   - `SyndicateIdentity`:
     `identity_id: str` (e.g. `SYND-XXXX`)
     `alias: str = ""`
     `primary_wallets: List[str] = field(default_factory=list)`
     `historical_tokens: List[str] = field(default_factory=list)`
     `behavior_profile: Optional[SyndicateBehavior] = None`
     `confidence_score: float = 0.60`
     `first_seen: float = field(default_factory=time.time)`
     `last_seen: float = field(default_factory=time.time)`
     `operation_count: int = 1`
     `known_funders: List[str] = field(default_factory=list)`
     `chains: List[str] = field(default_factory=lambda: ["sol"])`
     `metadata: Dict[str, Any] = field(default_factory=dict)`
     Dual property aliases: `known_wallets` <-> `primary_wallets`, `confidence` <-> `confidence_score`, `syndicate_id` <-> `identity_id`.
     `.to_dict()`, `.from_dict()`.
   - `SyndicateIdentityEngine`:
     `__init__(self, output_dir: str = "results", vector_store: Any = None, similarity_threshold: float = 0.82)`
     Methods:
     - `register_cluster(self, cluster: Any, token: Any = None, trades: Any = None, shared_funder: Optional[str] = None) -> SyndicateIdentity`
     - `match_syndicate(self, cluster: Any, behavior: Optional[SyndicateBehavior] = None, shared_funder: Optional[str] = None) -> Optional[SyndicateIdentity]`
     - `process(self, clusters: List[Any], tokens: Optional[Dict[str, Any]] = None, trades: Optional[Dict[str, Any]] = None) -> List[SyndicateIdentity]`
     - `get_all_identities(self) -> List[SyndicateIdentity]`
     - `get_watchlist(self, min_confidence: float = 0.70) -> List[str]`
     - `_load(self)` and `_save(self)`: atomic persistence to `syndicate_identities.json` via `.tmp` file and `os.replace`.

5. **Update scoring constants in `src/crypto_syndicate/discovery.py`**:
   Add and update the 9 constants at top of file:
   - `SNIPER_WINDOW_S = 30`
   - `EARLY_BUY_WINDOW = 300`
   - `FLASH_HOLD_MAX_S = 60`
   - `SUSTAINED_HOLD_MAX_S = 3600`
   - `DUMP_WINDOW_FLASH_S = 30`
   - `DUMP_WINDOW_S = 600`
   - `BUNDLER_THRESHOLD = 0.40`
   - `BOT_RATE_THRESHOLD = 0.60`
   - `MAX_HOPS = 5`
   **CRITICAL**: Keep aliases `EARLY_BUY_WINDOW_SECONDS = EARLY_BUY_WINDOW` and `DUMP_WINDOW_SECONDS = DUMP_WINDOW_S` to preserve compatibility with existing tests and codebase usages.

## Verification Requirements
Execute all 3 checks and capture exact output:
1. `python -m pytest tests/ -x -q` (all 234 tests must pass)
2. `python -c "from crypto_syndicate.fingerprint import SyndicateBehavior; from crypto_syndicate.hop_tracer import HopTracer; from crypto_syndicate.identity import SyndicateIdentityEngine; print('M7+M8+M9 imports OK')"` (with sys.path inserted)
3. `python -c "import sys; sys.path.insert(0,'src'); from crypto_syndicate.api.gmgn_cli_bridge import get_token_traders; r=get_token_traders('sol','4dNj3ykr7iHv2AfjgkC9YesgUvCZ4qEJ7beQxy3RZ3XX',5); print('traders:', len(r.get('data',[])))"`

Write a complete report to `.agents/m7_m9_worker_1/report.md` and `handoff.md`, and report all 3 check outputs in `send_message`.

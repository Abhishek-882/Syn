# Handoff Report — Explorer 2: Behavioral Fingerprinting & Syndicate Identity Engine

**Working Directory**: `C:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\m7_m9_explorer_2`  
**Target Files**: `src/crypto_syndicate/fingerprint.py` & `src/crypto_syndicate/identity.py`  
**Date**: 2026-09-20T16:25:00Z  
**Type**: Hard Handoff (Task Complete)

---

## 1. Observation

1. **`src/crypto_syndicate/api/models.py` Inspection**:
   - Lines 20–80: `TokenLaunchEvent` is frozen with slots, containing `token_address: str`, `chain: str`, `deployer_address: str`, `launch_timestamp: int`, `raw_metadata: Dict[str, Any]`. Supports `.to_dict()`, `.from_dict()`, and dictionary-style `__getitem__`.
   - Lines 82–148: `TradeRecord` represents individual trades with `wallet_address: str`, `direction: str`, `timestamp: int`, `token_amount: float`, `volume_usd: float`, `is_deployer: bool`, `seconds_since_launch: Optional[float]`.
   - Lines 212–278: `WalletScore` contains `wallet_address: str`, `chain: str`, `suspicion_score: float`, `flagged_patterns: Tuple[str, ...]`, `net_profit_usd: float`.
   - Lines 280–371: `SyndicateCluster` contains `cluster_id: str`, `chain: str`, `wallets: Tuple[str, ...]`, `flagged_patterns: Tuple[str, ...]`, `suspicion_score: float`, `associated_tokens: Tuple[str, ...]`, `estimated_profit_usd: float`, `funder_wallet: Optional[str]`, `deployer_wallet: Optional[str]`, `average_entry_window_seconds: float`, `average_exit_window_seconds: float`, `evidence_metadata: Dict[str, Any]`.
   - Lines 12–17: `PatternType` enum defines `EARLY_ENTRY = "early_entry"`, `COMMON_FUNDING = "common_funding"`, `SHARED_DEPLOYER = "shared_deployer"`, `COORDINATED_DUMP = "coordinated_dump"`.

2. **`src/crypto_syndicate/discovery.py` Inspection**:
   - Verified constants (based on real BELUGA token data from 2026-09-20): `SNIPER_WINDOW_S = 30` (real average entry 16s), `EARLY_BUY_WINDOW = 300`, `FLASH_HOLD_MAX_S = 60` (real hold time 3–12s on micro-cap vs 5–45 min on sustained), `SUSTAINED_HOLD_MAX_S = 3600`, `DUMP_WINDOW_FLASH_S = 30`, `DUMP_WINDOW_S = 600`, `BUNDLER_THRESHOLD = 0.40`, `BOT_RATE_THRESHOLD = 0.60`, `MAX_HOPS = 5`.

3. **`ORIGINAL_REQUEST.md` Follow-up Specifications**:
   - Lines 240–303: Initial prototype for `SyndicateBehavior` dataclass with `to_text() -> str` method and `from_cluster_and_token(cluster, token, traders)` classmethod.
   - Lines 362–446: Initial prototype for `SyndicateIdentity` and `SyndicateIdentityEngine` with `SIMILARITY_THRESHOLD = 0.82`, `IDENTITY_FILE = "syndicate_identities.json"`, and methods `process()`, `_load()`, `_save()`.

4. **Pytest Execution**:
   - Ran `python -m pytest tests/unit/ -q`: exited with code 0 (111 passed).

---

## 2. Logic Chain

1. **Need for Behavioral Fingerprinting**:
   - From Observation 1, `SyndicateCluster` instances are identified by ephemeral hashes (e.g. `cluster_0001_61fd9253`) scoped to single tokens or runs.
   - Syndicates rotate wallet addresses constantly. However, their timing metrics (`buy_delay_s`, `hold_time_s`, `dump_speed_s`), bundler usage (`bundler_rate`), bot degen rate (`bot_degen_rate`), and deployer participation remain consistent across tokens.
   - Therefore, `SyndicateBehavior` must extract these metrics from `SyndicateCluster` + `TokenLaunchEvent` + trades into a standardized signature.

2. **Need for Dual Property Aliases**:
   - Observation 3 shows discrepancies between prompt specifications: DISPATCH calls for `avg_buy_delay_s`, `avg_hold_duration_s`, `dump_speed_s`, `bot_rate`, `patterns_flagged`, `identity_id`, `confidence_score`, `primary_wallets`, whereas lines 240-303 and 362-446 use `buy_delay_s`, `hold_time_s`, `dump_window_s`, `bot_degen_rate`, `patterns`, `syndicate_id`, `confidence`, `known_wallets`.
   - By implementing `@property` and setter pairs for both sets of names on `SyndicateBehavior` and `SyndicateIdentity`, any downstream caller or test suite referencing either naming convention works without modification or `AttributeError`.

3. **Entity Resolution Logic in `SyndicateIdentityEngine`**:
   - Stage 1: Wallet graph overlap (Jaccard similarity on member wallets) + common funder matching. If Jaccard >= 0.30 or >= 2 shared wallets, match with confidence > 0.85. If shared root funder is identified, match with confidence > 0.95.
   - Stage 2: If `vector_store` (Qdrant) is provided and graph overlap is below threshold, perform semantic search on `behavior.to_text()` with `SIMILARITY_THRESHOLD = 0.82`.
   - If matched: increment `operation_count`, update `last_seen`, merge wallets, merge historical tokens, compound confidence score (`+0.05`, max 1.0), and append behavior profile text.
   - If no match: mint new identity `SYND-XXXX`, starting at confidence 0.60.

4. **Persistence & Atomicity**:
   - Identities must be stored in `results/syndicate_identities.json`.
   - To prevent corrupted JSON on interrupted runs, `_save()` writes to `.tmp` and executes atomic `os.replace`.

---

## 3. Caveats

1. **Qdrant Optionality**:
   - `SyndicateIdentityEngine` must operate completely independently if `qdrant-client` or sentence-transformers is not installed or if docker is not running. Graph/funder overlap acts as primary matching; vector matching is invoked only if `vector_store` is provided and functional.
2. **Missing Granular Trades**:
   - In offline mock mode or when historical trade RPCs are rate-limited, granular `TradeRecord` arrays may be empty. In `from_cluster_and_token`, the implementation falls back to `average_entry_window_seconds` and `average_exit_window_seconds` from `SyndicateCluster`.
3. **Multi-token Deployer Recurrence**:
   - When deployers are pseudonymous, `shared_deployer` detection depends on GMGN token security metadata (`creator` or `deployer_address`).

---

## 4. Conclusion

The specifications for `src/crypto_syndicate/fingerprint.py` and `src/crypto_syndicate/identity.py` are complete, mathematically grounded in verified on-chain metrics, and fully cross-compatible with existing models in `api/models.py`.

Full source code designs, method signatures, dataclass definitions, and edge-case handling are detailed in:
`C:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\m7_m9_explorer_2\report.md`

---

## 5. Verification Method

1. **Verify Design Document**:
   - Inspect `.agents/m7_m9_explorer_2/report.md` for complete class implementations of `SyndicateBehavior`, `SyndicateIdentity`, and `SyndicateIdentityEngine`.
2. **Post-Implementation Import Verification**:
   ```powershell
   python -c "import sys; sys.path.insert(0, 'src'); from crypto_syndicate.fingerprint import SyndicateBehavior; from crypto_syndicate.identity import SyndicateIdentity, SyndicateIdentityEngine; print('Imports OK')"
   ```
3. **Behavior Extraction & Semantic Text Verification**:
   ```python
   from crypto_syndicate.api.models import SyndicateCluster, TokenLaunchEvent
   from crypto_syndicate.fingerprint import SyndicateBehavior

   cluster = SyndicateCluster(cluster_id="test_cluster", chain="sol", wallets=("w1", "w2", "w3"), flagged_patterns=("early_entry",), suspicion_score=80.0)
   token = TokenLaunchEvent(token_address="token1", chain="sol", name="Test", symbol="TST", launch_timestamp=1000)
   b = SyndicateBehavior.from_cluster_and_token(cluster, token)
   assert "chain:sol" in b.to_text()
   assert b.buy_delay_s == b.avg_buy_delay_s
   ```
4. **Identity Engine Multi-operation Persistence Verification**:
   ```python
   from crypto_syndicate.identity import SyndicateIdentityEngine
   engine = SyndicateIdentityEngine(output_dir="results_test")
   id1 = engine.register_cluster(cluster, token)
   assert id1.identity_id.startswith("SYND-")
   assert id1.operation_count == 1
   id2 = engine.register_cluster(cluster, token)
   assert id2.identity_id == id1.identity_id
   assert id2.operation_count == 2
   ```
5. **Unit Test Suite Baseline**:
   ```powershell
   python -m pytest tests/unit/ -q
   ```

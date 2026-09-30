# Handoff Report: HopTracer Design & Test Suite Impact Analysis

**Agent:** Explorer 3 (`.agents/m7_m9_explorer_3`)  
**Handoff Type:** Hard (Task Complete)  
**Date:** 2026-09-20  

---

## 1. Observation

1. **Test Suite Baseline**:
   - Tool Command: `python -m pytest tests/ -x -q`
   - Result: Exited with code 0.
   - Test Collection: `tests/e2e/test_full_pipeline.py: 5`, `tests/e2e/test_tier1_features.py: 65`, `tests/e2e/test_tier2_boundaries.py: 30`, `tests/e2e/test_tier3_combinations.py: 15`, `tests/e2e/test_tier4_applications.py: 8`, `tests/unit/test_adversarial_m1.py: 14`, `tests/unit/test_adversarial_m1_c2.py: 31`, `tests/unit/test_api_clients.py: 30`, `tests/unit/test_discovery.py: 12`, `tests/unit/test_graph.py: 9`, `tests/unit/test_monitor.py: 7`, `tests/unit/test_report.py: 8`.
   - Total count: **234 passing tests**, 0 failures, 0 errors, 0 skips.

2. **Existing Constant Usage in `discovery.py`**:
   - Location: `src/crypto_syndicate/discovery.py:30-37`:
     ```python
     EARLY_BUY_WINDOW_SECONDS = 300
     DUMP_WINDOW_SECONDS = 600
     MIN_EARLY_BUYERS = 2
     SCORE_PER_PATTERN = 20
     SCORE_BONUS_ALL_PATTERNS = 10
     SCORE_BONUS_SIZE_5 = 5
     SCORE_BONUS_SIZE_10 = 10
     ```
   - Location: `src/crypto_syndicate/discovery.py:135`:
     ```python
     cutoff = (launch_time + EARLY_BUY_WINDOW_SECONDS) if launch_time > 0 else ...
     ```
   - Location: `src/crypto_syndicate/discovery.py:238`:
     ```python
     while j < len(sell_events) and sell_events[j][0] - start <= DUMP_WINDOW_SECONDS:
     ```

3. **Direct Test Dependencies on Constant Names**:
   - Location: `tests/unit/test_discovery.py:9-14`:
     ```python
     from crypto_syndicate.discovery import (
         DiscoveryPipeline,
         EARLY_BUY_WINDOW_SECONDS,
         DUMP_WINDOW_SECONDS,
         PatternType,
     )
     ```
   - `EARLY_BUY_WINDOW_SECONDS` and `DUMP_WINDOW_SECONDS` are explicitly imported as symbols by name.

4. **Test Assertions Sensitive to Window Durations**:
   - Location: `tests/unit/test_discovery.py:46-84` (`test_get_early_buyers_filters_by_window`):
     A mock buy trade is registered at `timestamp = launch_time + 100`. The test explicitly asserts `assert "wallet_early" in buyer_wallets`.
   - Location: `tests/unit/test_discovery.py:129-171` (`test_detect_coordinated_dumps_sliding_window`):
     Mock sell trades occur at `base_time + 50` and `base_time + 200` (time delta = 150 seconds). The test asserts `assert len(dumps) >= 1` and `assert "dump_wallet_1" in involved; assert "dump_wallet_2" in involved`.

5. **Existing Transfer Lineage & CEX Implementations**:
   - Location: `src/crypto_syndicate/api/solscan_client.py:70-135`:
     `get_account_transfers(self, address: str, ... flow: Optional[str] = None) -> List[FundingTransferRecord]`
     Returns list of `FundingTransferRecord` instances with fields `from_address`, `to_address`, `amount`, `amount_usd`, `timestamp`, `is_initial_funding`.
   - Location: `tests/e2e/test_tier1_features.py:192-198` & `tests/e2e/test_tier3_combinations.py:178-190`:
     Tests specifically assert known CEX hot wallets (e.g. `5tzFkiKscXBHgVXYR9qTJaMmk7p8XQzL7` Binance Solana, `0x28C6c06298d514Db089934071355E5743bf21d60` Binance EVM) must not cause false-positive clustering of disparate syndicates.

---

## 2. Logic Chain

1. **Step 1 (Name Aliasing)**:
   - *From Observation 3*: `tests/unit/test_discovery.py` directly imports `EARLY_BUY_WINDOW_SECONDS` and `DUMP_WINDOW_SECONDS`.
   - *Inference*: If either variable name is removed or renamed to `EARLY_BUY_WINDOW` or `DUMP_WINDOW_S` without maintaining the original name as an alias, Python will raise `ImportError` on loading the test module.
   - *Deduction*: `discovery.py` MUST define `EARLY_BUY_WINDOW_SECONDS = EARLY_BUY_WINDOW = 300` and `DUMP_WINDOW_SECONDS = DUMP_WINDOW_S = 600`.

2. **Step 2 (Early Buy Cutoff Scope)**:
   - *From Observation 4*: `test_get_early_buyers_filters_by_window` validates that a buy at `launch_time + 100s` is included as an early buyer.
   - *Inference*: If `get_early_buyers` is altered to use `SNIPER_WINDOW_S = 30` as its cutoff, a buy at `+100s` is rejected, causing `assert "wallet_early" in buyer_wallets` to fail. Furthermore, mock token fixtures define trades at +45s, +90s, +150s; a 30s cutoff causes `len(buyers) < MIN_EARLY_BUYERS (2)` to abort all token evaluations, cascading failures across 30+ downstream pipeline tests.
   - *Deduction*: `EARLY_BUY_WINDOW = 300` must remain the broad filtering cutoff in `get_early_buyers`. `SNIPER_WINDOW_S = 30` should be used as a behavioral tag (`is_sniper`) or fine-grained heuristic.

3. **Step 3 (Dump Window Scope)**:
   - *From Observation 4*: `test_detect_coordinated_dumps_sliding_window` groups sales at `+50s` and `+200s` (delta 150s).
   - *Inference*: If `detect_coordinated_dumps` has its default sliding window reduced to `DUMP_WINDOW_FLASH_S = 30`, 150s > 30s, causing 0 dump clusters to be detected and failing `assert len(dumps) >= 1`.
   - *Deduction*: `DUMP_WINDOW_S = 600` must remain the default window in `detect_coordinated_dumps`, while `DUMP_WINDOW_FLASH_S = 30` is used for Mode A flash dump analysis.

4. **Step 4 (HopTracer Graph Correctness)**:
   - *From Observation 5*: Solscan transfers can contain cycles ($A \to B \to A$) and common CEX deposit addresses.
   - *Inference*: Without path cycle tracking, BFS will enter infinite loops on cyclic transfers. Without CEX pruning, every wallet that withdrew from Binance will be identified as sharing the same syndicate root funder.
   - *Deduction*: `HopTracer` must maintain `path` tracking per BFS branch, prune known CEX addresses (`KNOWN_CEX_ADDRESSES`), and limit search depth to `MAX_HOPS = 5`.

---

## 3. Caveats

- **Live vs Mock Solscan Rate Limits**: In live production environments, multi-hop BFS across 5 hops can trigger multiple API calls if an account has many ancestors. While `HopTracer` includes an in-memory cache `self._cache`, a wide fan-out could consume API quota. In production, Solscan Pro's 10 RPS limit is guarded by `TokenBucketRateLimiter`, but depth 5 should be used judiciously.
- **Dynamic CEX Addresses**: The initial list of CEX addresses is hardcoded based on known high-volume Solana hot wallets (Binance, Coinbase, OKX, Bybit, KuCoin). In future iterations, dynamic CEX tagging via GMGN API tags (`maker_token_tags`) or Solscan account labels should supplement this static set.
- No other caveats.

---

## 4. Conclusion

1. **Test Suite Baseline is Healthy**: All 234 tests pass cleanly.
2. **HopTracer Design is Ready for Implementation**:
   - Specified in `src/crypto_syndicate/hop_tracer.py`.
   - Implements `HopTracer(api_client=None, max_hops=5, min_transfer_sol=0.05)`.
   - Provides `trace_funding(start_wallets)` and `find_shared_root(wallets)` with cycle prevention, CEX pruning, depth limits, and offline mock support.
3. **Safe Discovery Constants Update Plan**:
   - Adding the constants to `discovery.py` with backwards-compatible aliases (`EARLY_BUY_WINDOW_SECONDS = EARLY_BUY_WINDOW = 300` and `DUMP_WINDOW_SECONDS = DUMP_WINDOW_S = 600`) will cause **0 test regressions**.
   - Do NOT replace the 300s window in `get_early_buyers` with 30s, and do NOT replace the 600s window in `detect_coordinated_dumps` with 30s.

---

## 5. Verification Method

To independently verify all findings:

1. **Verify Baseline Test Suite**:
   ```powershell
   cd C:\Users\Asus\Documents\antigravity\hopeful-curie
   python -m pytest tests/ -x -q
   ```
   *Expected result*: `234 passed in ~25-35s`.

2. **Verify Constant Imports in Tests**:
   ```powershell
   python -c "from crypto_syndicate.discovery import EARLY_BUY_WINDOW_SECONDS, DUMP_WINDOW_SECONDS; print('Constants exist:', EARLY_BUY_WINDOW_SECONDS, DUMP_WINDOW_SECONDS)"
   ```
   *Expected result*: `Constants exist: 300 600`.

3. **Verify Report Artifact**:
   Inspect `.agents/m7_m9_explorer_3/report.md` for full implementation code and architectural breakdown.

4. **Invalidation Conditions**:
   - If `tests/unit/test_discovery.py` is modified to remove imports of `EARLY_BUY_WINDOW_SECONDS`, the backwards-compatibility alias caveat is relaxed.
   - If test count in `tests/` drops below 234, the baseline has regressed.

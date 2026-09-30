# DISPATCH: Worker 1 (M2-M6 Implementation, Hardening, and Test Authoring)

## MANDATORY INTEGRITY WARNING
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

## Context & References
- Read `ORIGINAL_REQUEST.md` at `C:\Users\Asus\Documents\antigravity\hopeful-curie\ORIGINAL_REQUEST.md`
- Read `PROJECT.md` at `C:\Users\Asus\Documents\antigravity\hopeful-curie\PROJECT.md`
- Read Explorer 1 handoff at: `C:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\m2_m6_explorer_1\handoff.md`
- Read Explorer 2 handoff at: `C:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\m2_m6_explorer_2\handoff.md`
- Read Explorer 3 handoff at: `C:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\m2_m6_explorer_3\handoff.md`

## Objectives

### 1. Codebase Hardening in `src/crypto_syndicate/`
1. **`src/crypto_syndicate/discovery.py`**:
   - Add `get_deployer(self, token: str, chain: str = "sol") -> str` using `get_token_security()`.
   - Add `score_cluster(self, cluster_wallets: List[str], patterns: Optional[List[str]] = None) -> float` strictly bounded in `[0.0, 100.0]`.
   - Normalize objects/dicts in `fetch_recent_launches`, `get_early_buyers`, `get_funding_sources`.
   - In `detect_coordinated_dumps`: fetch `get_token_trades` ONCE per token and filter in-memory by wallet to avoid $O(N)$ rate-limited calls.
   - Multi-chain support for funding sources in mock and live mode.
2. **`src/crypto_syndicate/graph.py`**:
   - Bulletproof WCC + Louvain clustering: small components (<6 nodes) or un-partitioned components treated as single clusters; for larger components, orphan Louvain communities (<3 nodes) reabsorbed into the adjacent valid community with maximum edge weight; singletons (isolated nodes) never cluster.
   - Fix co-buy edge updating: ensure `token` is appended to `shared_tokens` for both `(a, b)` and `(b, a)`.
   - Handle property aliases (`flagged_patterns` / `patterns_flagged` / `patterns`, `associated_tokens` / `tokens`).
3. **`src/crypto_syndicate/monitor.py`**:
   - Add `from dotenv import load_dotenv` and call `load_dotenv` at startup.
   - Atomic persistence for `seen_clusters.json` using `.tmp` and `os.replace`.
   - Heartbeat logging to `heartbeat.log` every 60 seconds with non-blocking sleep.
   - Fix line 63 profit string in alert logging (`f"Profit est: ${cluster.estimated_profit_usd:,.2f}\n"`).
   - Pass `mock_mode` to `DiscoveryPipeline`.
4. **`src/crypto_syndicate/report.py`**:
   - Embed D3 v7 minified source offline (e.g. vendored in `src/crypto_syndicate/d3_fallback.py` or directly in `report.py`) so offline reports never make network calls or fall back to `window.d3 = null`.
   - SANITIZE D3 source: ensure `https://d3js.org` is replaced with `offline-d3-v7` so `assert "d3js.org" not in content` in `test_f12_02` passes!
   - Update `generate_report(wallets, clusters, output_dir=".", output_file=None)` to accept `output_file` keyword argument as expected by `conftest.py`.
   - Normalize clusters and wallets whether passed as dataclasses or dicts.
   - Table header: use `<h2>Top Clusters (Suspicious Syndicates)</h2>`.
5. **`src/crypto_syndicate/run_analysis.py`**:
   - Robust `sys.path` and `.env` loading using `Path(__file__).resolve()`.
   - Pass `mock_mode=args.mock` to `MonitoringLoop`.
6. **`src/crypto_syndicate/api/models.py`**:
   - Add `def __contains__(self, key: str) -> bool: return key in self.to_dict()` to `SyndicateCluster`, `TokenLaunchEvent`, `TradeRecord`, `FundingTransferRecord`, `WalletScore`.
7. **`src/crypto_syndicate/api/gmgn_client.py` and `solscan_client.py`**:
   - Safe nested dictionary/list extractor so `{"data": []}` does not crash with `'list' object has no attribute 'get'`.

### 2. Comprehensive Test Suites Authoring
Create the following test files following the detailed test plans in Explorer 3's handoff:
1. `tests/unit/test_discovery.py` (unit tests for all stages of DiscoveryPipeline)
2. `tests/unit/test_graph.py` (unit tests for SyndicateGraph, WCC, Louvain, singletons, exports)
3. `tests/unit/test_monitor.py` (unit tests for MonitoringLoop, seen_clusters persistence, alerts, heartbeat)
4. `tests/unit/test_report.py` (unit tests for CSV, JSON, HTML with offline D3, signatures)
5. `tests/e2e/test_full_pipeline.py` (end-to-end pipeline test and CLI subprocess execution test)

### 3. Verification Commands
Run the following verification commands:
1. `python -m pytest tests/ -x -q` (all existing tests + new unit and E2E tests must pass)
2. `python src/crypto_syndicate/run_analysis.py --mock --chains sol --output results_verified` (must print "Syndicates found : 1" or >0)
3. `python src/crypto_syndicate/run_analysis.py --mock --chains sol,eth,bsc --output results_verified_multichain` (must print "Syndicates found : 3")

### 4. Output Deliverable
Write `handoff.md` in your working directory `.agents/m2_m6_worker_1/handoff.md` with:
- Summary of all code modifications
- Complete test execution logs with exact pass counts
- Verification command outputs

## 2026-09-20T14:00:34Z
Task assigned:
- Harden existing codebase files in src/crypto_syndicate/ (discovery.py, graph.py, monitor.py, report.py, run_analysis.py, api/models.py, api/gmgn_client.py, api/solscan_client.py)
- Author comprehensive tests: tests/unit/test_discovery.py, tests/unit/test_graph.py, tests/unit/test_monitor.py, tests/unit/test_report.py, tests/e2e/test_full_pipeline.py
- Run verification commands: pytest tests/ -x -q, run_analysis.py mock sol, run_analysis.py mock multichain
- Write handoff.md and send message to parent.


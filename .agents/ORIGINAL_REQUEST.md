# Original User Request

## Initial Request — 2026-09-20T12:55:07Z

Build an automated Solana/multi-chain on-chain syndicate research and monitoring system that discovers suspicious wallet clusters behind coordinated token launches, generates interactive wallet graph reports, and runs continuously alerting on new manipulation patterns.

Working directory: ~/teamwork_projects/crypto_syndicate_research

Integrity mode: development

---

## Requirements

### R1. Automated Suspicious Wallet Discovery
The system must automatically discover suspicious wallets from recent and historical token launches across all chains supported by GMGN (Solana, Ethereum, BSC, etc.) without requiring seed wallets. It must identify wallets that:
- Buy the same new token within minutes of launch (coordinated early entry)
- Are funded by the same source wallet before coordinated buys
- Share the same deployer wallet across multiple tokens
- Execute coordinated sells/dumps at the same time window

### R2. Wallet Cluster Graph & Transfer Maps
The system must produce an interactive Jupyter notebook with:
- Network graphs showing wallet-to-wallet funding relationships (edges = SOL/ETH transfers, nodes = wallets)
- Token launch timeline maps showing which wallets bought which tokens at what time
- Cluster detection to group related wallets into suspected syndicates
- Wallet scoring/ranking by suspicion level with supporting evidence

### R3. GMGN + Solscan API Integration
The system must use:
- GMGN API (key provided via environment variable GMGN_API_KEY) for token data, wallet history, and on-chain signals
- Solscan API (key provided via environment variable SOLSCAN_API_KEY) for Solana-specific transfer and transaction data
- Data should be fetched for all available historical time ranges
- All API calls must be rate-limited, retried on failure, and cached locally to avoid redundant requests

### R4. Continuous Monitoring Loop with Alerts
The system must include a live monitoring mode that:
- Polls for new token launches on a configurable interval (default: every 5 minutes)
- Detects syndicate patterns in real time as new tokens launch
- Logs alerts to a structured file (JSON + human-readable) when a new suspicious cluster is detected
- Can run as a background process alongside the Jupyter notebook

### R5. Research Report Generation
At the end of any analysis run, the system must auto-generate:
- A static HTML report with embedded wallet graphs and transfer maps
- A CSV/JSON export of all discovered suspicious wallets with evidence metadata
- A summary of detected syndicate clusters with estimated coordinated profit

---

## Acceptance Criteria

### Wallet Discovery
- [ ] System discovers at least 5 wallet clusters from recent token launches without any seed wallet input
- [ ] Each cluster has >= 3 wallets with at least 2 of the 4 suspicious pattern types flagged

### Graph Output
- [ ] Jupyter notebook renders interactive network graphs (zoom, click on node for wallet details)
- [ ] Transfer maps show timeline of buys/sells with token price overlay
- [ ] Clusters are visually distinct (color-coded by syndicate group)

### API Integration
- [ ] GMGN and Solscan API calls are rate-limited, retried on failure, and cached to avoid redundant requests
- [ ] All chains supported by GMGN are queried, not just Solana

### Monitoring
- [ ] Monitoring loop runs continuously without crashing, logging a heartbeat every minute
- [ ] Alert log is written in both JSON (machine-readable) and plain text (human-readable)
- [ ] New suspicious clusters detected within 10 minutes of a token launch

### Report
- [ ] HTML report is self-contained (no external dependencies) and opens in a browser
- [ ] CSV export includes: wallet address, chain, suspicion score, flagged patterns, associated tokens, estimated profit

---

Note: The system must accept API credentials via environment variables only (GMGN_API_KEY and SOLSCAN_API_KEY). Never hardcode credentials in any file.

## Follow-up — 2026-09-20T13:47:03Z

Status check only. Reply with exactly one line: 'Teamwork quota available - ready to build M3 through M6 milestones for crypto syndicate research system.' if you successfully receive this.

## Follow-up — 2026-09-20T13:48:33Z

Continue building the Crypto Syndicate Research System. Milestone 1 is complete with 50 passing tests. I have written draft implementations of M2-M6 directly, but they need to be improved, hardened, and fully tested by your team.

Working directory: C:\Users\Asus\Documents\antigravity\hopeful-curie

### What exists on disk

#### M1 (COMPLETE — production grade, do not break)
- src/crypto_syndicate/api/ (base_client.py, cache.py, fixtures.py, gmgn_client.py, models.py, rate_limiter.py, solscan_client.py)
- src/crypto_syndicate/config.py
- tests/ (conftest.py, e2e/test_tier1_features.py, e2e/test_tier2_boundaries.py, e2e/test_tier3_combinations.py, e2e/test_tier4_applications.py, unit/test_adversarial_m1.py)

#### M2-M6 (draft implementations — need hardening and tests)
- src/crypto_syndicate/discovery.py (6-stage pipeline draft)
- src/crypto_syndicate/graph.py (WCC + Louvain clustering draft)
- src/crypto_syndicate/monitor.py (monitoring loop with NDJSON alerts draft)
- src/crypto_syndicate/report.py (HTML/CSV/JSON reports with inline D3.js draft)
- src/crypto_syndicate/run_analysis.py (CLI entrypoint draft)

### Your task

Review the existing M2-M6 draft files in src/crypto_syndicate/, then:

1. Fix and harden each draft module to properly use M1 clients (GMGNClient, SolscanClient, their models). Read the M1 files first.
2. Key issues to fix in drafts:
   - discovery.py: ensure it uses GMGNClient.get_new_token_launches(), get_token_trades(), get_token_security() and SolscanClient.get_account_transfers() correctly with proper model parsing
   - graph.py: verify WCC→Louvain pipeline handles disconnected graphs and singleton nodes correctly
   - monitor.py: add proper import of dotenv load at startup, verify seen_clusters persistence works across restarts
   - report.py: D3 fetch may fail (Cloudflare blocks it) — embed D3 v7 source directly as a fallback string (minified, ~500KB)
   - run_analysis.py: ensure sys.path and dotenv loading works when run from any directory
3. Write comprehensive tests for M2-M6:
   - tests/unit/test_discovery.py — test all 6 pipeline stages with mock fixtures
   - tests/unit/test_graph.py — test WCC, Louvain, cluster building, D3 export
   - tests/unit/test_monitor.py — test alert writing, seen_clusters persistence, heartbeat
   - tests/unit/test_report.py — test CSV columns, JSON structure, HTML contains D3 script tag
   - tests/e2e/test_full_pipeline.py — end-to-end mock pipeline: discovery→graph→clusters→report
4. Verify everything passes:
   - Run: `cd C:\Users\Asus\Documents\antigravity\hopeful-curie && python -m pytest tests/ -x -q 2>&1`
   - All existing M1 tests must still pass
   - New M2-M6 tests must pass
5. Run the mock analysis to confirm end-to-end:
   - `python src\crypto_syndicate\run_analysis.py --mock --chains sol --output results_verified`
   - Must print: "Syndicates found: X" where X > 0

Report back with: test counts, pass/fail summary, and the output of the mock analysis run.

## Follow-up — 2026-09-20T14:06:37Z

Read `.agents/skills/crypto-syndicate-resume/SKILL.md` first for full project state.

One milestone remains incomplete:
- [ ] M2-M6 tests — unit + E2E test suites

All modules already exist in `src/crypto_syndicate/`. M1 has 50 passing tests in `tests/`. You need to write and verify tests for M2–M6.

## Your Task

First, run existing tests to confirm M1 still passes:
```
python -m pytest tests/ -x -q 2>&1 | tail -5
```

Then write these 5 test files (all use mock_mode=True via fixtures — no live API calls):

### tests/unit/test_discovery.py
Test `DiscoveryPipeline` in mock_mode=True:
- `test_fetch_recent_launches_returns_list` — returns list of TokenLaunchEvent
- `test_get_early_buyers_filters_by_window` — only buyers within 300s of launch_time
- `test_get_early_buyers_deduplicates_wallets` — same wallet only once
- `test_detect_coordinated_dumps_sliding_window` — finds overlapping 10-min sell windows
- `test_score_wallet_single_pattern` — score = 20 for 1 pattern
- `test_score_wallet_all_four_patterns` — score = 80 + 10 bonus = 90
- `test_score_wallet_capped_at_100` — never exceeds 100
- `test_run_pipeline_mock_returns_wallets` — pipeline(mock) returns >0 wallets
- `test_run_pipeline_populates_funding_relationships` — funding_relationships list populated
- `test_run_pipeline_all_wallets_have_suspicion_score` — every wallet has suspicion_score >= 0

### tests/unit/test_graph.py
Test `SyndicateGraph`:
- `test_build_graph_adds_wallet_nodes` — nodes created for each wallet
- `test_build_graph_co_buy_edges` — wallets sharing token get co_buy edge
- `test_build_graph_funding_edges` — funding relationships become directed edges
- `test_build_graph_empty_input` — no crash on empty wallets list
- `test_detect_clusters_returns_syndicate_clusters` — clusters returned for connected mock graph
- `test_detect_clusters_min_size_3` — no cluster with < 3 members
- `test_detect_clusters_empty_graph` — returns [] on empty graph
- `test_export_graph_json_structure` — returns dict with 'nodes' and 'links' keys
- `test_export_graph_json_node_has_cluster_id` — each node has cluster_id field

### tests/unit/test_monitor.py
Test `MonitoringLoop`:
- `test_init_creates_output_dir` — output_dir created on init
- `test_load_seen_clusters_empty_file` — handles missing seen_clusters.json gracefully
- `test_write_alert_appends_to_json` — alert written to alerts.json as valid NDJSON line
- `test_write_alert_appends_to_log` — alert written to alerts.log as human-readable line
- `test_save_and_reload_seen_clusters` — seen_clusters persists across instances

### tests/unit/test_report.py
Test `generate_report`:
- `test_generate_report_creates_csv` — wallets.csv created with correct columns
- `test_generate_report_creates_json` — clusters.json valid JSON, list type
- `test_generate_report_creates_html` — report.html created
- `test_csv_has_correct_columns` — headers: wallet_address, chain, suspicion_score, patterns_flagged, associated_tokens, estimated_profit_usd
- `test_html_contains_d3_script` — report.html contains '<script>' tag
- `test_html_contains_graph_data` — report.html contains 'graphData'
- `test_report_empty_inputs` — no crash with empty wallets and clusters lists

### tests/e2e/test_full_pipeline.py
End-to-end test using mock_mode=True throughout:
- `test_full_pipeline_mock_sol` — runs discovery→graph→clusters→report for sol chain, asserts wallets>0, report files created
- `test_full_pipeline_reports_exist` — CSV, JSON, HTML all created after full run
- `test_full_pipeline_no_crash_empty_results` — pipeline with no data doesn't crash
- `test_cli_mock_run` — subprocess call to `python src/crypto_syndicate/run_analysis.py --mock --chains sol --output results_test` returns exit code 0

## After writing all tests:

1. Run: `python -m pytest tests/ -x -q 2>&1` — ALL tests must pass (M1 + new M2-M6 tests)
2. Run: `python src\crypto_syndicate\run_analysis.py --mock --chains sol --output results_final` — must print 'Syndicates found: X' where X > 0
3. Report: exact test counts (X passed, Y failed) and the mock analysis output line

IMPORTANT: Do not modify any existing M1 source or test files. Only add new test files.

## Follow-up — 2026-09-20T16:18:28Z

New priority task. We just verified real on-chain data and have corrected constants. Build M7+M8+M9 with these exact specs.

Working dir: C:\Users\Asus\Documents\antigravity\hopeful-curie

## Critical: Fix CLI Bridge First (TODAY priority)
Extend `src/crypto_syndicate/api/gmgn_cli_bridge.py` to support these new commands that work NOW:

```python
def gmgn_cli_call(args: list) -> dict:
    """Already exists — call via npx.cmd"""

# ADD these helper functions:
def get_token_traders(chain: str, address: str, limit: int = 50, tag: str = None) -> dict:
    """gmgn-cli token traders --chain=X --address=Y --limit=Z [--tag=bundler] --raw"""
    args = ['token', 'traders', f'--chain={chain}', f'--address={address}', f'--limit={limit}', '--raw']
    if tag: args += [f'--tag={tag}']
    return gmgn_cli_call(args)

def get_token_holders(chain: str, address: str, limit: int = 20) -> dict:
    """gmgn-cli token holders --chain=X --address=Y --limit=Z --raw"""
    return gmgn_cli_call(['token', 'holders', f'--chain={chain}', f'--address={address}', f'--limit={limit}', '--raw'])

def get_wallet_activity(chain: str, address: str) -> dict:
    """gmgn-cli portfolio activity --chain=X --address=Y --raw"""
    return gmgn_cli_call(['portfolio', 'activity', f'--chain={chain}', f'--address={address}', '--raw'])

def get_created_tokens(chain: str, address: str) -> dict:
    """gmgn-cli portfolio created-tokens --chain=X --address=Y --raw"""
    return gmgn_cli_call(['portfolio', 'created-tokens', f'--chain={chain}', f'--address={address}', '--raw'])
```

## Create src/crypto_syndicate/fingerprint.py
Behavioral fingerprint using REAL verified constants:

```python
from dataclasses import dataclass
from typing import List

@dataclass
class SyndicateBehavior:
    chain: str
    mode: str                       # "flash" or "sustained"
    buy_delay_s: float              # seconds after launch (real avg: 16s)
    hold_time_s: float              # seconds held (real: 3-12s flash, 5-45min sustained)
    bundler_rate: float             # 0-1 (real: 0.515 on BELUGA)
    bot_degen_rate: float           # 0-1 (real: 0.667)
    wallet_count: int
    dump_window_s: float            # 30s flash, 600s sustained
    is_deployer_buying: bool        # creator+bundler tag present
    fresh_wallet_ratio: float       # fraction of is_new=true wallets
    patterns: List[str]

    def to_text(self) -> str:
        return (
            f"chain:{self.chain} mode:{self.mode} "
            f"buy_delay:{self.buy_delay_s:.0f}s hold:{self.hold_time_s:.0f}s "
            f"bundler:{self.bundler_rate:.2f} bots:{self.bot_degen_rate:.2f} "
            f"wallets:{self.wallet_count} dump_window:{self.dump_window_s:.0f}s "
            f"deployer_buys:{self.is_deployer_buying} fresh:{self.fresh_wallet_ratio:.2f} "
            f"patterns:{'|'.join(sorted(self.patterns))}"
        )

    @classmethod
    def from_cluster_and_token(cls, cluster: dict, token: dict, traders: list) -> 'SyndicateBehavior':
        """Extract behavior from gmgn-cli data."""
        launch_ts = token.get('creation_timestamp', 0)
        delays = []
        holds = []
        fresh_count = 0
        deployer_buying = False
        for t in traders:
            s = t.get('start_holding_at', 0)
            e = t.get('end_holding_at', 0)
            tags = t.get('maker_token_tags', [])
            if s > launch_ts > 0: delays.append(s - launch_ts)
            if e > s > 0: holds.append(e - s)
            if t.get('is_new'): fresh_count += 1
            if 'creator' in tags and 'bundler' in tags: deployer_buying = True

        avg_delay = sum(delays)/len(delays) if delays else 30
        avg_hold  = sum(holds)/len(holds) if holds else 7
        mode = "flash" if avg_hold < 120 else "sustained"
        return cls(
            chain=token.get('chain', 'sol'),
            mode=mode,
            buy_delay_s=avg_delay,
            hold_time_s=avg_hold,
            bundler_rate=token.get('bundler_rate', 0),
            bot_degen_rate=token.get('bot_degen_rate', 0),
            wallet_count=len(traders),
            dump_window_s=30 if mode == "flash" else 600,
            is_deployer_buying=deployer_buying,
            fresh_wallet_ratio=fresh_count/max(len(traders),1),
            patterns=cluster.get('flagged_patterns', [])
        )
```

## Create src/crypto_syndicate/hop_tracer.py
BFS multi-hop fund tracer (MAX_HOPS=5):

```python
from collections import deque
from typing import Dict, Set, List, Tuple, Optional

class HopTracer:
    MAX_HOPS = 5
    MIN_TRANSFER_SOL = 0.05

    def __init__(self, solscan_client):
        self.client = solscan_client
        self._cache: Dict[str, list] = {}

    def find_shared_root(self, wallets: List[str]) -> dict:
        """BFS from each wallet back to find shared upstream funder."""
        all_ancestors: Dict[str, Set[str]] = {}
        for w in wallets:
            ancestors = self._bfs_ancestors(w)
            all_ancestors[w] = ancestors

        if not all_ancestors: return {}
        sets = list(all_ancestors.values())
        common = sets[0].copy()
        for s in sets[1:]: common &= s

        return {
            "shared_funders": sorted(common),
            "wallet_ancestors": {k: sorted(v) for k, v in all_ancestors.items()},
            "confidence": len(common) / max(len(wallets), 1)
        }

    def _bfs_ancestors(self, start: str) -> Set[str]:
        visited: Set[str] = set()
        queue = deque([(start, 0)])
        ancestors: Set[str] = set()
        while queue:
            addr, depth = queue.popleft()
            if addr in visited or depth >= self.MAX_HOPS: continue
            visited.add(addr)
            for funder, amount in self._get_funders(addr):
                if amount >= self.MIN_TRANSFER_SOL:
                    ancestors.add(funder)
                    queue.append((funder, depth + 1))
        return ancestors

    def _get_funders(self, wallet: str) -> List[Tuple[str, float]]:
        if wallet not in self._cache:
            try:
                transfers = self.client.get_account_transfers(wallet, flow="in")
                self._cache[wallet] = [(t.from_address, t.amount) for t in transfers]
            except Exception:
                self._cache[wallet] = []
        return self._cache[wallet]
```

## Create src/crypto_syndicate/identity.py
Persistent identity engine (SYND-XXXX IDs):

```python
import json, time, uuid
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Set, Optional

@dataclass
class SyndicateIdentity:
    syndicate_id: str
    first_seen: float
    last_seen: float
    operation_count: int
    known_wallets: List[str]
    known_funders: List[str]
    known_chains: List[str]
    total_profit_usd: float
    confidence: float
    behavior_texts: List[str]       # past behavior descriptions for Qdrant matching
    notes: str = ""

class SyndicateIdentityEngine:
    SIMILARITY_THRESHOLD = 0.82
    IDENTITY_FILE = "syndicate_identities.json"

    def __init__(self, output_dir: str = "results", vector_store=None):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.vector_store = vector_store
        self.identities: Dict[str, SyndicateIdentity] = self._load()

    def process(self, cluster: dict, behavior_text: str) -> SyndicateIdentity:
        best_id = None
        if self.vector_store:
            matches = self.vector_store.find_similar(behavior_text)
            for m in matches:
                if m.get("similarity", 0) >= self.SIMILARITY_THRESHOLD:
                    sid = m.get("syndicate_id")
                    if sid and sid in self.identities:
                        best_id = self.identities[sid]
                        break

        wallets = list(cluster.get("wallets", []))
        if best_id:
            best_id.operation_count += 1
            best_id.last_seen = time.time()
            best_id.known_wallets = list(set(best_id.known_wallets + wallets))
            best_id.confidence = min(1.0, best_id.confidence + 0.05)
            best_id.total_profit_usd += cluster.get("estimated_profit_usd", 0)
            best_id.behavior_texts.append(behavior_text)
            print(f"⚠️  RETURNING SYNDICATE: {best_id.syndicate_id} (op #{best_id.operation_count})")
            identity = best_id
        else:
            sid = f"SYND-{len(self.identities)+1:04d}"
            identity = SyndicateIdentity(
                syndicate_id=sid, first_seen=time.time(), last_seen=time.time(),
                operation_count=1, known_wallets=wallets, known_funders=[],
                known_chains=[cluster.get("chain","sol")],
                total_profit_usd=cluster.get("estimated_profit_usd",0),
                confidence=0.6, behavior_texts=[behavior_text]
            )
            self.identities[sid] = identity
            print(f"🆕 NEW SYNDICATE: {sid}")

        self._save()
        return identity

    def get_watchlist(self) -> List[dict]:
        return [{"syndicate_id": i.syndicate_id, "funder": f,
                 "ops": i.operation_count, "profit": i.total_profit_usd}
                for i in self.identities.values() for f in i.known_funders]

    def _load(self) -> Dict:
        p = self.output_dir / self.IDENTITY_FILE
        if p.exists():
            raw = json.loads(p.read_text())
            return {k: SyndicateIdentity(**v) for k, v in raw.items()}
        return {}

    def _save(self):
        p = self.output_dir / self.IDENTITY_FILE
        p.write_text(json.dumps({k: asdict(v) for k, v in self.identities.items()}, indent=2))
```

## Updated scoring constants in discovery.py
Add these at the top of discovery.py:
```python
# Verified constants from real on-chain data (BELUGA, Pump.fun, 2026-09-20)
SNIPER_WINDOW_S     = 30    # < 30s after launch = coordinated sniper
EARLY_BUY_WINDOW    = 300   # broad suspicious window
FLASH_HOLD_MAX_S    = 60    # Mode A: micro-cap, hold < 60s
SUSTAINED_HOLD_MAX_S = 3600 # Mode B: established token, hold < 1hr
DUMP_WINDOW_FLASH_S = 30    # Mode A coordinated sell window
DUMP_WINDOW_S       = 600   # Mode B 10-min sell window (existing)
BUNDLER_THRESHOLD   = 0.40  # token bundler_rate > 40% = strong signal
BOT_RATE_THRESHOLD  = 0.60  # bot_degen_rate > 60% = likely coordinated
MAX_HOPS            = 5     # BFS fund tracer depth
```

## After writing all files:
1. Run: `python -m pytest tests/ -x -q` — all 234 must still pass
2. Run: `python -c "from crypto_syndicate.fingerprint import SyndicateBehavior; from crypto_syndicate.hop_tracer import HopTracer; from crypto_syndicate.identity import SyndicateIdentityEngine; print('M7+M8+M9 imports OK')"` (from src/ with sys.path)
3. Test CLI bridge: `python -c "import sys; sys.path.insert(0,'src'); from crypto_syndicate.api.gmgn_cli_bridge import get_token_traders; r=get_token_traders('sol','4dNj3ykr7iHv2AfjgkC9YesgUvCZ4qEJ7beQxy3RZ3XX',5); print('traders:', len(r.get('data',[])))"`
4. Report exact output of all 3 checks.



## 2026-09-21T02:44:42Z

Autonomous multi-agent system that explores deployed web platforms, systematically clicks and tests every interactive element, logs all failures, and executes a closed-loop remediation plan.

Working directory: c:\Users\Asus\Documents\antigravity\hopeful-curie
Integrity mode: development

## Requirements

### R1. Autonomous Element Discovery & Button Sweep
The system must automatically crawl the deployed web application (http://localhost:8000/web/syndicate_3d_visualizer.html), identify every clickable element (native buttons, ARIA interactive elements, navigation chips, stage pills, sliders, filter tags, KPI cards, and modals), and execute clicks with pointer collision and interception detection.

### R2. Comprehensive Failure Logging
Any unhandled JavaScript errors, console errors, 404/500 network asset failures, or pointer interception timeouts must be recorded into a structured, machine-readable log (
esults/web_verification_failures.json) capturing the selector, error type, element bounding box, and DOM snapshot.

### R3. Closed-Loop Remediation Planning & Verification
When failures are logged, an agent must formulate a root-cause remediation plan, apply the surgical code fixes, and re-run the exploration sweep until 100% of interactive controls pass with zero failures.

### R4. Multi-Agent Pipeline Verification
Orchestrate multi-perspective verification using specialized roles:
- Interactive Crawler Agent: Discovers DOM selectors and executes sequential click passes.
- Visual Regression Judge: Captures screenshots across viewport resolutions and checks layout aesthetics.
- Network & State Auditor: Validates console errors, telemetry data, and network requests.

## Acceptance Criteria

### Automated Sweep Verification
- [ ] Automated headless browser navigates to the deployed URL and crawls 100% of discovered interactive selectors.
- [ ] Pointer collisions and element overlaps are detected and recorded with exact pixel coordinates.


## 2026-09-21T02:44:42Z

Autonomous multi-agent system that explores deployed web platforms, systematically clicks and tests every interactive element, logs all failures, and executes a closed-loop remediation plan.

Working directory: c:\Users\Asus\Documents\antigravity\hopeful-curie
Integrity mode: development

## Requirements

### R1. Autonomous Element Discovery & Button Sweep
The system must automatically crawl the deployed web application (http://localhost:8000/web/syndicate_3d_visualizer.html), identify every clickable element (native buttons, ARIA interactive elements, navigation chips, stage pills, sliders, filter tags, KPI cards, and modals), and execute clicks with pointer collision and interception detection.

### R2. Comprehensive Failure Logging
Any unhandled JavaScript errors, console errors, 404/500 network asset failures, or pointer interception timeouts must be recorded into a structured, machine-readable log (
esults/web_verification_failures.json) capturing the selector, error type, element bounding box, and DOM snapshot.

### R3. Closed-Loop Remediation Planning & Verification
When failures are logged, an agent must formulate a root-cause remediation plan, apply the surgical code fixes, and re-run the exploration sweep until 100% of interactive controls pass with zero failures.

### R4. Multi-Agent Pipeline Verification
Orchestrate multi-perspective verification using specialized roles:
- Interactive Crawler Agent: Discovers DOM selectors and executes sequential click passes.
- Visual Regression Judge: Captures screenshots across viewport resolutions and checks layout aesthetics.
- Network & State Auditor: Validates console errors, telemetry data, and network requests.

## Acceptance Criteria

### Automated Sweep Verification
- [ ] Automated headless browser navigates to the deployed URL and crawls 100% of discovered interactive selectors.
- [ ] Pointer collisions and element overlaps are detected and recorded with exact pixel coordinates.
- [ ] Failure log schema captures timestamps, selectors, error descriptions, and DOM snapshots.
- [ ] Remediator agent reads failure log and successfully resolves pointer collisions or click errors.
- [ ] Final verification pass confirms 36/36 interactive elements pass with 0 failures and 0 console errors.


## 2026-09-21T03:01:24Z

PAUSE INSTRUCTION: The user has requested to pause all agent operations for 4 hours (quota recovery / cooldown timer). Do not proceed with further executions, API queries, or sweeps right now. Please hold your current state and pause for 4 hours. When the 4-hour window concludes, you will resume and continue your assigned tasks.

## 2026-09-21T07:29:58Z

Autonomous multi-agent system that explores deployed web platforms, systematically clicks and tests every interactive element, logs all failures, and executes a closed-loop remediation plan.

Working directory: `c:\Users\Asus\Documents\antigravity\hopeful-curie`
Integrity mode: development

## Requirements

### R1. Autonomous Element Discovery & Button Sweep
The system must automatically crawl the deployed web application (`http://localhost:8000/web/syndicate_3d_visualizer.html`), identify every clickable element (native buttons, ARIA interactive elements, navigation chips, stage pills, sliders, filter tags, KPI cards, and modals), and execute clicks with pointer collision and interception detection.

### R2. Comprehensive Failure Logging
Any unhandled JavaScript errors, console errors, 404/500 network asset failures, or pointer interception timeouts must be recorded into a structured, machine-readable log (`results/web_verification_failures.json`) capturing the selector, error type, element bounding box, and DOM snapshot.

### R3. Closed-Loop Remediation Planning & Verification
When failures are logged, an agent must formulate a root-cause remediation plan, apply the surgical code fixes, and re-run the exploration sweep until 100% of interactive controls pass with zero failures.

### R4. Multi-Agent Pipeline Verification
Orchestrate multi-perspective verification using specialized roles:
- Interactive Crawler Agent: Discovers DOM selectors and executes sequential click passes.
- Visual Regression Judge: Captures screenshots across viewport resolutions and checks layout aesthetics.
- Network & State Auditor: Validates console errors, telemetry data, and network requests.

## Acceptance Criteria

### Automated Sweep Verification
- [ ] Automated headless browser navigates to the deployed URL and crawls 100% of discovered interactive selectors.
- [ ] Pointer collisions and element overlaps are detected and recorded with exact pixel coordinates.
- [ ] Failure log schema captures timestamps, selectors, error descriptions, and DOM snapshots.
- [ ] Remediator agent reads failure log and successfully resolves pointer collisions or click errors.
- [ ] Final verification pass confirms 36/36 interactive elements pass with 0 failures and 0 console errors.

## 2026-09-21T07:31:22Z

USER DIRECTIVE: Check the project artifacts and history up to the pause point:
- Milestones M1, M2, and M3 are already completed and recorded in `PROJECT.md`.
- Headless crawler sweep passed 36/36 elements with 0 errors in `results/web_verification_failures.json`.
- All 321/321 repository tests are passing.
- Live HTTP server (port 8000) and live scanner daemon are active.

Resume orchestration directly from this verified state instead of repeating completed work from scratch. If you find any doubts, inconsistencies, or unverified claims, you have full authority to re-verify or restart any phase.

## 2026-09-21T08:58:53Z

Build the Crypto Syndicate Research System's next milestone:
**M12 — Jito Bundle Detector** (`jito_detector.py`) — a full-heuristic detection module
combining canonical Jito tip account matching, inner CPI transfer pattern analysis,
bundle_id correlation, and timing analysis.
**BEFORE any code is written**, three browser UX-explorer agents must perform exhaustive
exploration of the deployed visualizer as "Syndicate Hunter (power user)" personas,
write detailed review reports, and those reports drive both the upgrade plan and M12 integration.

Working directory: `C:\Users\Asus\Documents\antigravity\hopeful-curie`
Integrity mode: development

---

## Context

- All prior milestones M1–M11.7 are complete. **321/321 tests passing (zero failures)**.
- Live platform is at `http://localhost:8000/web/syndicate_3d_visualizer.html`
  (served by `python -m http.server 8000` from the working directory).
- If the HTTP server is not running, start it before browser exploration.
- Full resume context: `.agents/skills/crypto-syndicate-resume/SKILL.md`
- Architecture: `src/crypto_syndicate/` (always use this, not `crypto_syndicate/`).

---

## Requirements

### R1. Three-Agent UX Audit (Browser Agents — Persona: Syndicate Hunter Power User)

Spawn **3 independent browser agents**. Each agent explores
`http://localhost:8000/web/syndicate_3d_visualizer.html` as a **Syndicate Hunter power user**
who wants: fast keyboard shortcuts, filter recall, batch export, alert tuning, and maximum
information density. Each agent must:

1. Navigate the full site from scratch (no prior context).
2. Attempt EVERY interactive element: health chips, tag filters, radar cards, dossier views,
   timeline pills and scrubber, play/pause, CL4R1T4S mode, copy toast, export markdown,
   reset view, command deck collapse/expand.
3. Take a screenshot at **every distinct interaction step** (minimum 30 screenshots).
4. Write a detailed **power-user review report** covering:
   - What worked perfectly
   - What was confusing, missing, or frustrating from a power-user's POV
   - Specific UI/UX improvement requests (keyboard shortcuts, data density, export options, etc.)
   - A 1–10 score for: usability, data density, interaction speed, power-user features
5. Save their report to `results/ux_audit/agent_{1,2,3}_review.md`.

The three agents must explore **independently** with no cross-communication during exploration.

### R2. Synthesis & Upgrade Plan

After all 3 audit reports are complete:
1. Synthesize the 3 reports into a unified `results/ux_audit/synthesis_upgrade_plan.md`.
2. Identify the top 5 highest-impact UX improvements wanted by a power user (prioritized by
   frequency across reports and estimated implementation effort).
3. Implement those improvements in `web/syndicate_3d_visualizer.html` (and any supporting
   Python/JS files). Zero placeholders — every planned improvement must be shipped.
4. All 321 pytest tests must continue to pass after changes (`python -m pytest tests/ -q`).

### R3. M12 — Jito Bundle Detector (`src/crypto_syndicate/jito_detector.py`)

Implement `jito_detector.py` as a **standalone pure-library module** (no network I/O directly;
receives transaction data from caller). Requirements:

- **Canonical tip account matching**: detect transfers to any of the 8 known Jito tip accounts:
  `96gYZGLnJeTa9AGEefvjNArMBUwEpzDQRNSCGVFmhEEq`,
  `HFqU5x63VTqvQss8hp11i4wVV8bD44PvwucfZ2bU7gRe`,
  `Cw8CFyM9FkoMi7K7Crf6HNQqf4uEMzpKw6QNghXLvLkY`,
  `ADaUMid9yfUytqMBgopwjb2DTLSokTSzL1sMaC9jnwRv`,
  `DfXygSm4jCyNCybVYYK6DwvWqjKee8pbDmJGcLWNDXjh`,
  `ADuUkR4vqLUMWXxW9gh6D6L8pMSawimctcNZ5pGwDcEt`,
  `DttWaMuVvTiduZRnguLF7jNxTgiMBZ1hyflaDeKd1qRv`,
  `3AVi9Tg9Uo68tJfuvoKvqKNWKkC5wPdSSdeBnizKZ6dW`.
- **Inner CPI transfer pattern**: detect bundles via CPI transfer sequences where a "tip"
  inner instruction sends SOL to one of the above accounts without appearing in the outer
  instruction set.
- **bundle_id correlation**: if bundle_id metadata is present on the transaction, use it
  as a hard confirmation signal.
- **Timing analysis**: flag transactions that arrive within a 400ms slot window alongside
  known tip-touching transactions (co-slot bundling heuristic).
- **Confidence scoring**: return a `JitoDetectionResult` dataclass with fields:
  `is_jito_bundle` (bool), `confidence` (0.0–1.0), `signals` (list of str describing
  which signals fired), `tip_account_matched` (Optional[str]), `bundle_id` (Optional[str]).
- **Integration**: `scanner.py` and `fingerprint.py` must call `jito_detector.detect(tx)`
  and attach the result to `TradeRecord` and `SyndicateBehavior` respectively.
- **Fixtures**: add at least 5 known Jito bundle fixtures and 5 known non-bundle fixtures
  to `src/crypto_syndicate/api/fixtures.py`.
- **Tests**: add adversarial + unit tests for `jito_detector.py` — minimum 25 new test cases
  covering true positives (all 4 signal types), true negatives, edge cases (partial signals,
  missing bundle_id, timing only), and confidence thresholds.

### R4. Visualizer Integration (Jito Bundle Display)

After M12 is implemented:
- The radar feed alert cards must display a `🎯 JITO BUNDLE` badge when `is_jito_bundle=True`.
- The dossier view must show the `confidence` score and fired `signals` list.
- The telemetry HUD must add a live counter: `[JITO: N bundles detected]`.
- All new UI elements must pass the exhaustive browser re-verification (minimum 30 steps,
  per-step screenshots stored in `results/screenshots/steps/`).

### R5. Final Full-Suite Verification

After all code changes:
1. `python -m pytest tests/ -q` must pass **100% of tests** (321 original + ≥25 new M12 tests).
2. Run `python .agents/skills/post-deploy-web-exploring/scripts/exhaustive_step_explorer.py`
   and confirm **30/30 steps pass** (0 failures, 0 console errors).
3. A browser agent must do a final live exploration pass and confirm the Jito badge, dossier
   signals, and HUD counter all display real data from the running scanner.

---

## Acceptance Criteria

### UX Audit
- [ ] 3 independent browser agent reviews saved to `results/ux_audit/agent_{1,2,3}_review.md`
- [ ] Each review has ≥30 screenshots and scores usability, data density, interaction speed, power-user features
- [ ] `results/ux_audit/synthesis_upgrade_plan.md` lists top 5 improvements with priority ranking

### UX Upgrades
- [ ] All top-5 power-user improvements implemented in `web/syndicate_3d_visualizer.html`
- [ ] Zero 321-test regressions after UI changes

### M12 Implementation
- [ ] `src/crypto_syndicate/jito_detector.py` exists with `JitoDetectionResult` dataclass and `detect(tx)` function
- [ ] All 8 canonical tip accounts are hardcoded as constants
- [ ] `scanner.py` and `fingerprint.py` call `jito_detector.detect()` and attach results
- [ ] ≥5 Jito bundle fixtures + ≥5 non-bundle fixtures in `fixtures.py`
- [ ] ≥25 new tests added; `python -m pytest tests/ -q` passes 100% (all original + new)

### Visualizer Integration
- [ ] `🎯 JITO BUNDLE` badge visible on radar alert cards when bundle detected
- [ ] Dossier shows confidence score and signals list
- [ ] HUD shows live `[JITO: N bundles]` counter

### Final Verification
- [ ] `python -m pytest tests/ -q` → 100% pass (≥346 tests)
- [ ] `exhaustive_step_explorer.py` → 30/30 pass, 0 console errors
- [ ] Final browser agent confirms live Jito display with real scanner data


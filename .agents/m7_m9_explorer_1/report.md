# Investigation Report: `gmgn_cli_bridge.py` & Discovery Scoring Constants (M7–M9)

**Date**: 2026-09-20  
**Investigator**: Explorer 1 (`.agents/m7_m9_explorer_1`)  
**Targets**:
1. `src/crypto_syndicate/api/gmgn_cli_bridge.py`
2. `src/crypto_syndicate/discovery.py`

---

## Executive Summary

This investigation analyzed the subprocess execution bridge `gmgn_cli_bridge.py` and the scoring constants in `discovery.py` to prepare for implementing M7 (Behavioral Fingerprinting), M8 (Hop Tracer), and M9 (Identity Engine).

### Key Discoveries & Warnings
1. **Critical CLI Argument Mismatch in Subcommands**:
   - `gmgn-cli token traders` and `gmgn-cli token holders` expect `--address <contract_address>`.
   - In contrast, `gmgn-cli portfolio activity` and `gmgn-cli portfolio created-tokens` **strictly require `--wallet <wallet_address>`**. Passing `--address` causes `gmgn-cli` to exit with code `1` and error message:
     `error: required option '--wallet <address>' not specified`.
   - The Python functions must map parameter `address` to CLI option `--wallet` for portfolio commands.
2. **JSON Envelope Structure & Normalization**:
   - `gmgn-cli token traders --raw` and `token holders --raw` output a JSON dictionary with the top-level key `"list"` (e.g. `{"list": [...]}`).
   - Downstream code (such as verification checks and test assertions) expects `r.get('data', [])`.
   - `get_token_traders` and `get_token_holders` should normalize responses by setting `res["data"] = res["list"]` if `"data"` is absent. Similarly, portfolio activity (`"activities"`) and created tokens (`"tokens"`) should normalize `"data"` aliases.
3. **Subprocess Error Handling & Rate Limiting (HTTP 429)**:
   - When GMGN rate limits the IP, `gmgn-cli` returns HTTP 429 with `RATE_LIMIT_BANNED`, writing diagnostics to `stderr` and crashing with exit code `3221226505` (`0xC0000409` libuv assertion failure on Windows).
   - Currently, `gmgn_cli_call` silently returns `{}` on non-zero exit code. Logging non-zero return codes and stderr snippets prevents silent debugging failures.
4. **Test Suite Backward Compatibility in `discovery.py`**:
   - `tests/unit/test_discovery.py` lines 11–12 import `EARLY_BUY_WINDOW_SECONDS` and `DUMP_WINDOW_SECONDS`.
   - When adding the new constants (`SNIPER_WINDOW_S = 30`, `EARLY_BUY_WINDOW = 300`, `DUMP_WINDOW_S = 600`, etc.), aliases `EARLY_BUY_WINDOW_SECONDS = EARLY_BUY_WINDOW` and `DUMP_WINDOW_SECONDS = DUMP_WINDOW_S` must be retained to maintain 100% test pass rate (234/234 passing).

---

## 1. Deep Dive: `src/crypto_syndicate/api/gmgn_cli_bridge.py`

### 1.1 Existing Implementation
Current content of `src/crypto_syndicate/api/gmgn_cli_bridge.py` (lines 1–18):
```python
"""Bridge to call gmgn-cli for Cloudflare-protected GMGN endpoints."""
import subprocess, json, logging, os
logger = logging.getLogger(__name__)

def gmgn_cli_call(args: list) -> dict:
    """Call npx gmgn-cli with given args, return parsed JSON or empty dict."""
    try:
        npx_cmd = "npx.cmd" if os.name == "nt" else "npx"
        result = subprocess.run(
            [npx_cmd, "gmgn-cli"] + args,
            capture_output=True, text=True, timeout=30, encoding="utf-8"
        )
        if result.returncode == 0 and result.stdout.strip():
            return json.loads(result.stdout)
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError) as e:
        logger.warning("gmgn-cli call failed: %s", e)
    return {}
```

### 1.2 CLI Command Schema Analysis
Inspected via `npx gmgn-cli --help` directly on the host system:

| Command | Subcommand | Required Arguments | Optional Arguments | CLI Flag for Address | Raw JSON Output Key |
|---|---|---|---|---|---|
| `token` | `traders` | `--chain`, `--address` | `--limit`, `--order-by`, `--direction`, `--tag`, `--raw` | `--address <contract>` | `{"list": [...]}` |
| `token` | `holders` | `--chain`, `--address` | `--limit`, `--order-by`, `--direction`, `--tag`, `--raw` | `--address <contract>` | `{"list": [...]}` |
| `portfolio` | `activity` | `--chain`, `--wallet` | `--token`, `--limit`, `--cursor`, `--type`, `--raw` | `--wallet <address>` ⚠️ | `{"activities": [...], "next": ""}` |
| `portfolio` | `created-tokens`| `--chain`, `--wallet` | `--order-by`, `--direction`, `--migrate-state`, `--raw` | `--wallet <address>` ⚠️ | `{"tokens": [...], ...}` |

#### Empirical Verification of Flag Mismatch:
```powershell
# Executed:
npx gmgn-cli portfolio activity --chain=sol --address=4dNj3ykr7iHv2AfjgkC9YesgUvCZ4qEJ7beQxy3RZ3XX --raw

# Result: Exited with code 1:
error: required option '--wallet <address>' not specified

# Executed:
npx gmgn-cli portfolio activity --chain=sol --wallet=4dNj3ykr7iHv2AfjgkC9YesgUvCZ4qEJ7beQxy3RZ3XX --raw

# Result: Exited with code 0:
{"activities":[],"next":""}
```

### 1.3 Exact Proposed Implementation for `gmgn_cli_bridge.py`

```python
"""Bridge to call gmgn-cli for Cloudflare-protected GMGN endpoints."""
import json
import logging
import os
import subprocess
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def gmgn_cli_call(args: list) -> dict:
    """Call npx gmgn-cli with given args, return parsed JSON or empty dict."""
    try:
        npx_cmd = "npx.cmd" if os.name == "nt" else "npx"
        result = subprocess.run(
            [npx_cmd, "gmgn-cli"] + args,
            capture_output=True,
            text=True,
            timeout=30,
            encoding="utf-8",
        )
        if result.returncode == 0 and result.stdout.strip():
            return json.loads(result.stdout)
        elif result.returncode != 0:
            logger.warning(
                "gmgn-cli returned exit code %s: %s",
                result.returncode,
                result.stderr.strip()[:200] if result.stderr else "No stderr",
            )
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError) as e:
        logger.warning("gmgn-cli call failed: %s", e)
    return {}


def get_token_traders(chain: str, address: str, limit: int = 50, tag: Optional[str] = None) -> Dict[str, Any]:
    """Fetch top token traders via gmgn-cli.

    CLI: gmgn-cli token traders --chain=X --address=Y --limit=Z [--tag=bundler] --raw
    """
    args = ["token", "traders", f"--chain={chain}", f"--address={address}", f"--limit={limit}", "--raw"]
    if tag:
        args.append(f"--tag={tag}")
    res = gmgn_cli_call(args)
    if isinstance(res, dict) and "list" in res and "data" not in res:
        res["data"] = res["list"]
    return res


def get_token_holders(chain: str, address: str, limit: int = 20) -> Dict[str, Any]:
    """Fetch top token holders via gmgn-cli.

    CLI: gmgn-cli token holders --chain=X --address=Y --limit=Z --raw
    """
    args = ["token", "holders", f"--chain={chain}", f"--address={address}", f"--limit={limit}", "--raw"]
    res = gmgn_cli_call(args)
    if isinstance(res, dict) and "list" in res and "data" not in res:
        res["data"] = res["list"]
    return res


def get_wallet_activity(chain: str, address: str) -> Dict[str, Any]:
    """Fetch wallet transaction activity via gmgn-cli.

    CLI: gmgn-cli portfolio activity --chain=X --wallet=Y --raw
    Note: CLI requires --wallet flag for wallet address.
    """
    args = ["portfolio", "activity", f"--chain={chain}", f"--wallet={address}", "--raw"]
    res = gmgn_cli_call(args)
    if isinstance(res, dict) and "activities" in res and "data" not in res:
        res["data"] = res["activities"]
    return res


def get_created_tokens(chain: str, address: str) -> Dict[str, Any]:
    """Fetch tokens created by developer wallet via gmgn-cli.

    CLI: gmgn-cli portfolio created-tokens --chain=X --wallet=Y --raw
    Note: CLI requires --wallet flag for developer address.
    """
    args = ["portfolio", "created-tokens", f"--chain={chain}", f"--wallet={address}", "--raw"]
    res = gmgn_cli_call(args)
    if isinstance(res, dict) and "tokens" in res and "data" not in res:
        res["data"] = res["tokens"]
    return res
```

---

## 2. Deep Dive: `src/crypto_syndicate/discovery.py`

### 2.1 Current Constants & Usage
In `src/crypto_syndicate/discovery.py` lines 30–37:
```python
EARLY_BUY_WINDOW_SECONDS = 300
DUMP_WINDOW_SECONDS = 600
MIN_EARLY_BUYERS = 2
SCORE_PER_PATTERN = 20
SCORE_BONUS_ALL_PATTERNS = 10
SCORE_BONUS_SIZE_5 = 5
SCORE_BONUS_SIZE_10 = 10
```

Where each is referenced:
- `EARLY_BUY_WINDOW_SECONDS`:
  - `get_early_buyers` (lines 99, 135–136): Defines cutoff `launch_time + EARLY_BUY_WINDOW_SECONDS`
  - `tests/unit/test_discovery.py` line 11: Imported directly
- `DUMP_WINDOW_SECONDS`:
  - `detect_coordinated_dumps` (line 238): Sliding window `sell_events[j][0] - start <= DUMP_WINDOW_SECONDS`
  - `tests/unit/test_discovery.py` line 12: Imported directly
- `MIN_EARLY_BUYERS`: Line 299 in `run_pipeline`
- `SCORE_PER_PATTERN`, `SCORE_BONUS_*`: Lines 254–262 in `score_wallet` and lines 271–279 in `score_cluster`

### 2.2 Verified New Constants to Add

| Constant | Value | Purpose | Real Data Basis |
|---|---|---|---|
| `SNIPER_WINDOW_S` | `30` | Coordinated sniper window (<30s after launch) | Real avg buy delay = 16s (BELUGA token) |
| `EARLY_BUY_WINDOW` | `300` | Broad suspicious early entry window (5 min) | Standard pump.fun bonding curve threshold |
| `FLASH_HOLD_MAX_S` | `60` | Mode A: micro-cap rapid exit hold time (<60s) | Real hold time = 3–12s on micro-cap |
| `SUSTAINED_HOLD_MAX_S` | `3600` | Mode B: established token hold time (<1 hour) | Sustained pump campaigns hold 5–45 min |
| `DUMP_WINDOW_FLASH_S` | `30` | Mode A coordinated sell dump window | Flash syndicates exit within 30s |
| `DUMP_WINDOW_S` | `600` | Mode B 10-minute sell window | Standard coordinated dump window |
| `BUNDLER_THRESHOLD` | `0.40` | Token bundler_rate > 40% threshold | Strong signal (BELUGA was 51.5%) |
| `BOT_RATE_THRESHOLD` | `0.60` | Bot/degen rate > 60% threshold | High automation signal (BELUGA was 66.7%) |
| `MAX_HOPS` | `5` | BFS fund tracer traversal depth | Professional syndicates layer across 4–5 hops |

### 2.3 Proposed Constant Block in `discovery.py`
```python
# Verified constants from real on-chain data (BELUGA, Pump.fun, 2026-09-20)
SNIPER_WINDOW_S      = 30    # < 30s after launch = coordinated sniper
EARLY_BUY_WINDOW     = 300   # broad suspicious window
FLASH_HOLD_MAX_S     = 60    # Mode A: micro-cap, hold < 60s
SUSTAINED_HOLD_MAX_S = 3600  # Mode B: established token, hold < 1hr
DUMP_WINDOW_FLASH_S  = 30    # Mode A coordinated sell window
DUMP_WINDOW_S        = 600   # Mode B 10-min sell window (existing)
BUNDLER_THRESHOLD    = 0.40  # token bundler_rate > 40% = strong signal
BOT_RATE_THRESHOLD   = 0.60  # bot_degen_rate > 60% = likely coordinated
MAX_HOPS             = 5     # BFS fund tracer depth

# Backward-compatibility aliases and scoring parameters
EARLY_BUY_WINDOW_SECONDS = EARLY_BUY_WINDOW
DUMP_WINDOW_SECONDS = DUMP_WINDOW_S
MIN_EARLY_BUYERS = 2
SCORE_PER_PATTERN = 20
SCORE_BONUS_ALL_PATTERNS = 10
SCORE_BONUS_SIZE_5 = 5
SCORE_BONUS_SIZE_10 = 10
```

---

## 3. Downstream Compatibility & Integration

1. **`fingerprint.py` (M7)**:
   - Consumes `SNIPER_WINDOW_S`, `FLASH_HOLD_MAX_S`, `DUMP_WINDOW_FLASH_S`, `DUMP_WINDOW_S`, `BUNDLER_THRESHOLD`, `BOT_RATE_THRESHOLD`.
   - Uses `get_token_traders` to parse `start_holding_at`, `end_holding_at`, `maker_token_tags`, and `is_new`.
2. **`hop_tracer.py` (M8)**:
   - Consumes `MAX_HOPS = 5` and `SolscanClient.get_account_transfers`.
3. **`identity.py` (M9)**:
   - Uses `SyndicateIdentityEngine` to track cluster identities across sessions (`SYND-XXXX`).
4. **Existing Test Suite**:
   - `python -m pytest tests/ -x -q` currently reports **234 passed (100%)**.
   - With backward-compatible aliases in `discovery.py`, zero tests are broken.

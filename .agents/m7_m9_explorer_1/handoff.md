# Handoff Report: `gmgn_cli_bridge.py` & Discovery Scoring Constants (M7–M9)

## 1. Observation
- **Current Bridge File (`src/crypto_syndicate/api/gmgn_cli_bridge.py:1-18`)**:
  - Implements `gmgn_cli_call(args: list) -> dict` via `subprocess.run([npx_cmd, "gmgn-cli"] + args, capture_output=True, text=True, timeout=30, encoding="utf-8")`.
  - On Windows, uses `"npx.cmd"`.
  - Helper functions `get_token_traders`, `get_token_holders`, `get_wallet_activity`, and `get_created_tokens` do NOT currently exist.
- **`npx gmgn-cli` Subcommand Specifications**:
  - `token traders` takes `--chain`, `--address`, `--limit`, `--tag`, `--raw`. Outputs `{"list": [...]}`.
  - `token holders` takes `--chain`, `--address`, `--limit`, `--tag`, `--raw`. Outputs `{"list": [...]}`.
  - `portfolio activity` takes `--chain`, `--wallet`, `--raw`. Outputs `{"activities": [...], "next": ""}`.
  - `portfolio created-tokens` takes `--chain`, `--wallet`, `--raw`. Outputs `{"tokens": [...], ...}`.
  - Directly verified: Executing `npx gmgn-cli portfolio activity --chain=sol --address=... --raw` fails with exit code 1 and verbatim message:
    `error: required option '--wallet <address>' not specified`.
  - Directly verified: Executing with `--wallet=...` exits code 0 with valid JSON.
- **Current Discovery Constants (`src/crypto_syndicate/discovery.py:30-37`)**:
  - Contains `EARLY_BUY_WINDOW_SECONDS = 300`, `DUMP_WINDOW_SECONDS = 600`, `MIN_EARLY_BUYERS = 2`, `SCORE_PER_PATTERN = 20`, `SCORE_BONUS_ALL_PATTERNS = 10`, `SCORE_BONUS_SIZE_5 = 5`, `SCORE_BONUS_SIZE_10 = 10`.
  - Does NOT yet contain `SNIPER_WINDOW_S`, `EARLY_BUY_WINDOW`, `FLASH_HOLD_MAX_S`, `SUSTAINED_HOLD_MAX_S`, `DUMP_WINDOW_FLASH_S`, `DUMP_WINDOW_S`, `BUNDLER_THRESHOLD`, `BOT_RATE_THRESHOLD`, `MAX_HOPS`.
- **Existing Test Dependencies (`tests/unit/test_discovery.py:11-12`)**:
  - Explicitly imports: `from crypto_syndicate.discovery import DiscoveryPipeline, EARLY_BUY_WINDOW_SECONDS, DUMP_WINDOW_SECONDS, PatternType`.
  - Baseline test suite execution: `python -m pytest tests/ -x -q` passed with `234 passed in 23.36s (100%)`.

## 2. Logic Chain
1. *Observation*: `gmgn-cli portfolio activity` and `gmgn-cli portfolio created-tokens` fail if `--address` is passed instead of `--wallet`.
   *Inference*: The Python functions `get_wallet_activity(chain: str, address: str)` and `get_created_tokens(chain: str, address: str)` must format the subprocess arguments with `f"--wallet={address}"`, even though the Python function parameter is named `address`.
2. *Observation*: Raw output of `token traders` has key `"list"`, while `ORIGINAL_REQUEST.md` line 466 checks `r.get('data', [])`.
   *Inference*: Setting `res["data"] = res["list"]` in `get_token_traders` and `get_token_holders` ensures dual compatibility with both callers expecting `'data'` and callers expecting `'list'`.
3. *Observation*: When GMGN API rate limits an IP, `gmgn-cli` outputs HTTP 429 to stderr and exits with non-zero code (`3221226505`).
   *Inference*: `gmgn_cli_call` should log the non-zero exit code and stderr so errors are visible rather than silently returning `{}`.
4. *Observation*: `tests/unit/test_discovery.py` imports `EARLY_BUY_WINDOW_SECONDS` and `DUMP_WINDOW_SECONDS`.
   *Inference*: Setting `EARLY_BUY_WINDOW_SECONDS = EARLY_BUY_WINDOW` and `DUMP_WINDOW_SECONDS = DUMP_WINDOW_S` guarantees that all 234 existing unit/e2e tests continue to pass without modification.

## 3. Caveats
1. **GMGN IP Rate Limiting**: GMGN OpenAPI enforces aggressive rate limits (~1 RPS). Rapid sequential calls via `gmgn-cli` trigger temporary IP bans (2–5 minutes). The rate limiter in `gmgn_client.py` (`TokenBucketRateLimiter(refill_rate=1.0)`) or mock fallbacks must be respected.
2. **Windows libuv Assertion on Subprocess Exit**: When `npx gmgn-cli` encounters an immediate network error/ban, Node's libuv on Windows sometimes throws `Assertion failed: !(handle->flags & UV_HANDLE_CLOSING)`. `gmgn_cli_call` handles this via subprocess return code checks and returns `{}` safely.
3. **Mock Fallback Coverage**: The CLI bridge directly invokes the system's `npx gmgn-cli`. In unit test environments where `mock_mode=True`, tests should mock `gmgn_cli_call` or use existing fixtures to avoid live CLI calls.

## 4. Conclusion
1. `src/crypto_syndicate/api/gmgn_cli_bridge.py` should be updated with:
   - Enhanced `gmgn_cli_call` with stderr logging on non-zero exit code.
   - `get_token_traders(chain: str, address: str, limit: int = 50, tag: str = None) -> dict`
   - `get_token_holders(chain: str, address: str, limit: int = 20) -> dict`
   - `get_wallet_activity(chain: str, address: str) -> dict` (using `--wallet`)
   - `get_created_tokens(chain: str, address: str) -> dict` (using `--wallet`)
   - Dual-envelope normalization (`res['data'] = res['list']` / `'activities'` / `'tokens'`).
2. `src/crypto_syndicate/discovery.py` should be updated with:
   - The 9 verified constants: `SNIPER_WINDOW_S = 30`, `EARLY_BUY_WINDOW = 300`, `FLASH_HOLD_MAX_S = 60`, `SUSTAINED_HOLD_MAX_S = 3600`, `DUMP_WINDOW_FLASH_S = 30`, `DUMP_WINDOW_S = 600`, `BUNDLER_THRESHOLD = 0.40`, `BOT_RATE_THRESHOLD = 0.60`, `MAX_HOPS = 5`.
   - Backward-compatibility aliases `EARLY_BUY_WINDOW_SECONDS` and `DUMP_WINDOW_SECONDS`.

## 5. Verification Method
1. **Unit and E2E Tests**:
   `python -m pytest tests/ -x -q`
   Must pass 234/234 tests.
2. **CLI Bridge Imports & Signature Verification**:
   ```powershell
   python -c "import sys; sys.path.insert(0,'src'); from crypto_syndicate.api.gmgn_cli_bridge import get_token_traders, get_token_holders, get_wallet_activity, get_created_tokens; print('CLI bridge functions loaded OK')"
   ```
3. **Discovery Constants Verification**:
   ```powershell
   python -c "import sys; sys.path.insert(0,'src'); from crypto_syndicate.discovery import SNIPER_WINDOW_S, EARLY_BUY_WINDOW, FLASH_HOLD_MAX_S, SUSTAINED_HOLD_MAX_S, DUMP_WINDOW_FLASH_S, DUMP_WINDOW_S, BUNDLER_THRESHOLD, BOT_RATE_THRESHOLD, MAX_HOPS, EARLY_BUY_WINDOW_SECONDS, DUMP_WINDOW_SECONDS; print('All 9 constants + aliases OK')"
   ```
4. **Live CLI Call Verification** (when not rate-limited):
   ```powershell
   python -c "import sys; sys.path.insert(0,'src'); from crypto_syndicate.api.gmgn_cli_bridge import get_wallet_activity, get_created_tokens; print(get_wallet_activity('sol', '4dNj3ykr7iHv2AfjgkC9YesgUvCZ4qEJ7beQxy3RZ3XX')); print(get_created_tokens('sol', '4dNj3ykr7iHv2AfjgkC9YesgUvCZ4qEJ7beQxy3RZ3XX'))"
   ```

# DISPATCH - Explorer 1 (gmgn_cli_bridge & discovery constants)

## Working Directory
`C:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\m7_m9_explorer_1`

## Objectives
1. Inspect `src/crypto_syndicate/api/gmgn_cli_bridge.py`:
   - Study current `gmgn_cli_call` implementation, subprocess handling, error handling, JSON parsing, mock fallbacks.
   - Investigate exact CLI arguments and options for gmgn-cli for:
     * `get_token_traders(chain: str, address: str, limit: int = 50, tag: str = None) -> dict`
     * `get_token_holders(chain: str, address: str, limit: int = 20) -> dict`
     * `get_wallet_activity(chain: str, address: str) -> dict`
     * `get_created_tokens(chain: str, address: str) -> dict`
   - Also note fallback / error-handling behavior if gmgn-cli returns an error or empty data or is offline.
2. Inspect `src/crypto_syndicate/discovery.py`:
   - Locate current scoring constants at top of file.
   - Check where each constant is used.
   - Verify constants to update:
     * `SNIPER_WINDOW_S = 30`
     * `EARLY_BUY_WINDOW = 300`
     * `FLASH_HOLD_MAX_S = 60`
     * `SUSTAINED_HOLD_MAX_S = 3600`
     * `DUMP_WINDOW_FLASH_S = 30`
     * `DUMP_WINDOW_S = 600`
     * `BUNDLER_THRESHOLD = 0.40`
     * `BOT_RATE_THRESHOLD = 0.60`
     * `MAX_HOPS = 5`
3. Write your report to `.agents/m7_m9_explorer_1/report.md` and `handoff.md`.

## 2026-09-20T16:21:14Z
You are an Explorer agent. Your working directory is C:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\m7_m9_explorer_1.
Read C:\Users\Asus\Documents\antigravity\hopeful-curie\ORIGINAL_REQUEST.md.
Read C:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\skills\crypto-syndicate-resume\SKILL.md.
Read your dispatch file at C:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\m7_m9_explorer_1\DISPATCH.md.

Inspect:
1. `src/crypto_syndicate/api/gmgn_cli_bridge.py`:
   - Study current `gmgn_cli_call` implementation, subprocess handling, and what arguments it expects.
   - Investigate how gmgn-cli CLI commands are structured (e.g. `npx gmgn-cli ...`).
   - Specify the exact implementation for:
     * `get_token_traders(chain: str, address: str, limit: int = 50, tag: str = None) -> dict`
     * `get_token_holders(chain: str, address: str, limit: int = 20) -> dict`
     * `get_wallet_activity(chain: str, address: str) -> dict`
     * `get_created_tokens(chain: str, address: str) -> dict`
2. `src/crypto_syndicate/discovery.py`:
   - Check current scoring constants at top of file.
   - Verify changes required:
     * `SNIPER_WINDOW_S = 30`
     * `EARLY_BUY_WINDOW = 300`
     * `FLASH_HOLD_MAX_S = 60`
     * `SUSTAINED_HOLD_MAX_S = 3600`
     * `DUMP_WINDOW_FLASH_S = 30`
     * `DUMP_WINDOW_S = 600`
     * `BUNDLER_THRESHOLD = 0.40`
     * `BOT_RATE_THRESHOLD = 0.60`
     * `MAX_HOPS = 5`

Write a comprehensive investigation report to `.agents/m7_m9_explorer_1/report.md` and complete handoff in `.agents/m7_m9_explorer_1/handoff.md`. Notify caller with send_message when done.

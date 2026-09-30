# DISPATCH LOG

## 2026-09-20T16:18:28Z
You are the Project Orchestrator for the Crypto Syndicate Research System.
Your identity: teamwork_preview_orchestrator_4
Your working directory: C:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\orchestrator_4
Project root: C:\Users\Asus\Documents\antigravity\hopeful-curie
Authoritative user request: C:\Users\Asus\Documents\antigravity\hopeful-curie\ORIGINAL_REQUEST.md
Resume state: C:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\skills\crypto-syndicate-resume\SKILL.md

Read `.agents/skills/crypto-syndicate-resume/SKILL.md` first for full project state.

New priority task: Build M7+M8+M9 with exact specs from verified real on-chain data and corrected constants.

## Tasks:
1. Extend `src/crypto_syndicate/api/gmgn_cli_bridge.py` to add:
   - `get_token_traders(chain: str, address: str, limit: int = 50, tag: str = None) -> dict`
   - `get_token_holders(chain: str, address: str, limit: int = 20) -> dict`
   - `get_wallet_activity(chain: str, address: str) -> dict`
   - `get_created_tokens(chain: str, address: str) -> dict`
2. Create `src/crypto_syndicate/fingerprint.py` (SyndicateBehavior dataclass with `to_text()` and `from_cluster_and_token()` classmethod).
3. Create `src/crypto_syndicate/hop_tracer.py` (HopTracer class with BFS multi-hop fund tracer, MAX_HOPS=5, MIN_TRANSFER_SOL=0.05).
4. Create `src/crypto_syndicate/identity.py` (SyndicateIdentity dataclass and SyndicateIdentityEngine class).
5. Update scoring constants at top of `src/crypto_syndicate/discovery.py`:
   - `SNIPER_WINDOW_S = 30`
   - `EARLY_BUY_WINDOW = 300`
   - `FLASH_HOLD_MAX_S = 60`
   - `SUSTAINED_HOLD_MAX_S = 3600`
   - `DUMP_WINDOW_FLASH_S = 30`
   - `DUMP_WINDOW_S = 600`
   - `BUNDLER_THRESHOLD = 0.40`
   - `BOT_RATE_THRESHOLD = 0.60`
   - `MAX_HOPS = 5`

## After writing all files:
1. Run: `python -m pytest tests/ -x -q` — all 234 must still pass.
2. Run: `python -c "from crypto_syndicate.fingerprint import SyndicateBehavior; from crypto_syndicate.hop_tracer import HopTracer; from crypto_syndicate.identity import SyndicateIdentityEngine; print('M7+M8+M9 imports OK')"` (from src/ with sys.path).
3. Test CLI bridge: `python -c "import sys; sys.path.insert(0,'src'); from crypto_syndicate.api.gmgn_cli_bridge import get_token_traders; r=get_token_traders('sol','4dNj3ykr7iHv2AfjgkC9YesgUvCZ4qEJ7beQxy3RZ3XX',5); print('traders:', len(r.get('data',[])))"`.
4. Report exact output of all 3 checks.

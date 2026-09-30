# Rule: Autonomous Syndicate Keeper & Dynamic Wallet Sync Guardrails

## 1. Continuous Dynamic Discovery & Auto-Sync
- Whenever tracking on-chain entities, deployers, and pump/dump tokens, the platform MUST maintain an autonomous Keeper (`src/crypto_syndicate/keeper.py`).
- Static offline fixtures must NEVER be left un-synchronized when fresh on-chain token launches occur.
- Newly discovered deployers, tokens, and funding paths must be automatically persisted to `results/syndicate_identities.json`, `results/wallets.csv`, and `results/live_dexscreener_syndicate_tokens.json`.

## 2. Server Clock Drift Tolerance & Dynamic Calibration
- Any client calling time-sensitive APIs (such as GMGN OpenAPI with $\pm 5\text{s}$ windows) MUST dynamically calibrate against HTTP `Date` or NTP time.
- Machine clocks frequently drift by 10 to 30 seconds; never assume the host system clock is perfectly synchronized to UTC.
- If a 401 `AUTH_TIMESTAMP_EXPIRED` occurs, the system MUST re-calibrate immediately and retry with calibrated time.

## 3. Historical Track Record Standard (Recent-First Ranking)
- All historical token endpoints (`/api/token-history`) and UI tables must:
  1. Rank tokens chronologically descending by release date (most recent first at Rank #1).
  2. Display both peak All-Time High (ATH) Market Cap and Current Market Cap in USD.
  3. Include verified 1-click execution links to DexScreener (`https://dexscreener.com/solana/{address}`) and GMGN (`https://gmgn.ai/sol/token/{address}`).
  4. Display peak multiplier gain ($X$) and drawdown percentage from ATH.

## 4. Multi-Wallet Syndicate Auto-Extraction Invariant
- Whenever a syndicate token is discovered or ingested:
  1. The system MUST NOT restrict attribution to a single creator/deployer wallet.
  2. The system MUST automatically trace and extract all associated syndicate wallets:
     - **Genesis Funder & Intermediaries**: The CEX hot wallet or funding anchor and any intermediate funding hops.
     - **Co-Slot Jito Bundlers**: Wallets executing bundled swaps in the launch slot (co-slot timing $\le 400\text{ms}$).
     - **Coordinated Early Snipers**: Wallets purchasing within the initial sniper window ($t \le 30\text{s}$).
  3. All extracted wallets MUST be automatically registered in `results/syndicate_identities.json` (under `known_wallets` and `primary_wallets`) and appended to `results/wallets.csv` with their respective suspicion scores and pattern tags (`cex_funding`, `early_sniper`, `jito_bundler`).

## 5. Autonomous Server Daemon Lifecycle
- When `src/crypto_syndicate/server.py` boots, it MUST automatically spawn the `SyndicateKeeper` background daemon loop.
- The keeper loop must continuously scan watched deployers and live DEX/pump feeds without requiring manual API triggers or user prompts.
- When new tokens or wallets are discovered, the server MUST immediately broadcast an SSE event to update all active mobile and desktop terminals in real time.

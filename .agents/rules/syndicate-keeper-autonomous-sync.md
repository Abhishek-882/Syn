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

## 6. Turbo Multi-Source Scanning & Profit Qualification Filter
- The Keeper scanner MUST operate at an accelerated cadence (default: 15s interval) to capture fleeting Solana meme tokens before rug events occur.
- **Deployer Profit Qualification**: To avoid wastefully scanning dormant wallets, deployers must possess $\ge \$5.00$ USD in historical profit to qualify for the active scan queue.
- **Round-Robin Batched Scanning**: Eligible deployers are partitioned into rotating batches (default: 5 batches), cycling through one batch per cycle. Full deployer coverage is achieved every $\sim 75\text{s}$.
- **Multi-Source Discovery Engine**:
  - **Solscan Pro API v2** (`/token/latest?platform_id=pumpfun` with JWT authentication): Provides instant detection of fresh Pump.fun tokens at creation time.
  - **GMGN OpenAPI**: Enriches discovered tokens with verified ATH market cap, dev funding source, and holder distribution.
  - **DexScreener API**: Provides liquidity pair verification and search fallback.

## 7. Forward-Tracing Syndicate Network Expansion
- Every 2 minutes (every 8th keeper cycle), the system MUST execute forward-tracing network expansion:
  - From known syndicate deployers, trace outgoing transfers ($\ge 0.1\text{ SOL}$) via Solscan.
  - Check whether recipient wallets have deployed token pairs.
  - Any confirmed token creator is automatically added to the active deployer watchlist and its tokens are ingested.
  - Newly discovered wallets and deployers are immediately written to `results/syndicate_identities.json` and `results/wallets.csv`, feeding directly into the next scan cycle.


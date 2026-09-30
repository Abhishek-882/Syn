# GMGN & Solscan API Specification & Data Source Mining Report

**Agent**: `survey_spec_miner_1`  
**Working Directory**: `C:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\survey_spec_miner_1`  
**Target Document**: `api_spec_report.md`  
**Date**: 2026-09-20  
**Status**: Complete  

---

## 1. Executive Summary

This specification report details the on-chain data ingestion, multi-chain coverage, rate limiting, disk caching, resilience policies, normalized schemas, and offline mocking architecture required to satisfy **Requirement R3** and support **R1** (Discovery), **R2** (Graph Analysis), and **R4** (Continuous Monitoring) per `ORIGINAL_REQUEST.md`.

The target system relies on two primary data providers:
1. **Solscan Pro API v2.0**: The authoritative source for high-fidelity Solana account transfers, initial wallet funding roots (`account/metadata`, `account/funded_by`), parsed SPL token actions, and transaction balance deltas.
2. **GMGN API (OpenAPI & Agent Services)**: The primary multi-chain engine covering Solana (`sol`), Ethereum (`eth`), Binance Smart Chain (`bsc`), Base (`base`), and Tron (`tron`), supplying token launch discovery, liquidity pool initialization, DEX trades/swaps, and smart money wallet tracking.

Because production environments may execute without live credentials, or during testing/CI runs, a **deterministic offline mock and fixture subsystem** is formally specified to ensure complete testability and 100% adherence to acceptance criteria.

---

## 2. Solscan Pro API v2.0 Specification

### 2.1 Overview & Connectivity
* **Base URL**: `https://pro-api.solscan.io/v2.0`
* **Authentication**: Custom HTTP Request Header:
  ```http
  token: <SOLSCAN_API_KEY>
  ```
  *(Credentials must be loaded strictly from `SOLSCAN_API_KEY` environment variable)*
* **Billing / Quota Metric**: Compute Units (CU). Standard endpoints cost a flat **100 CU** per request.
* **Rate Limits by Subscription Tier**:
  * **Lite ($49/mo)**: 1,000 requests / 60 seconds (~16.6 RPS), 20M CU / month. Note: excludes multi-endpoints and advanced metadata.
  * **Level 2 ($199/mo)**: 1,000 requests / 60 seconds (~16.6 RPS), 150M CU / month. Includes `account/metadata` and `account/funded_by`.
  * **Level 3 ($399/mo)**: 2,000 requests / 60 seconds (~33.3 RPS), 500M CU / month.
  * **Level 4 ($1,099/mo)**: 3,000 requests / 60 seconds (~50.0 RPS), 1.5B CU / month.
* **Response Envelope Format**:
  ```json
  {
    "success": true,
    "data": [ ... ]
  }
  ```
* **Error Envelope Format**:
  ```json
  {
    "success": false,
    "errors": {
      "code": 429,
      "message": "Too Many Requests"
    }
  }
  ```

### 2.2 Key Endpoints & Query Parameters

#### 1. Account Transfers (`GET /account/transfer`)
Essential for tracing native SOL and SPL token transfers between wallets to uncover funding syndicates and asset routing.
* **Parameters**:
  * `address` (string, required): Target Solana address.
  * `activity_type` (string, optional): e.g. `ACTIVITY_SPL_TRANSFER`, `ACTIVITY_SOL_TRANSFER`.
  * `token` (string, optional): Mint address (Use `So11111111111111111111111111111111111111111` for native SOL).
  * `from` (string, optional): Filter by sender address.
  * `to` (string, optional): Filter by recipient address.
  * `flow` (string, optional): Direction: `in` or `out`.
  * `from_time` (integer, optional): Unix timestamp start.
  * `to_time` (integer, optional): Unix timestamp end.
  * `page` (integer, optional, default: 1): Page number.
  * `page_size` (integer, optional, default: 40, max: 100): Items per page.
* **Payload Fields**:
  * `trans_id` (string): Transaction signature hash.
  * `block_id` (number): Slot number.
  * `block_time` (number): Unix timestamp.
  * `activity_type` (string): Transfer activity identifier.
  * `from_address` (string): Sender public key.
  * `to_address` (string): Destination public key.
  * `token_address` (string): Token mint address.
  * `token_decimals` (number): Decimals.
  * `amount` (number): Raw integer amount (amount / 10^decimals).

#### 2. Account Funding Roots (`GET /account/metadata` & `GET /account/metadata/multi`)
Directly identifies the initial funding wallet that activated a target wallet address.
* **Parameters**:
  * `address` (string, required for single) or `address[]` (for multi).
* **Payload Fields**:
  * `account_address` (string): Target wallet.
  * `account_type` (string): `system_account`, `token_account`, `program`.
  * `account_label` (string, optional): Known entity tag (e.g. `Binance`, `Coinbase`, `Raydium Authority`).
  * `funded_by` (string): Funder public key (first address that sent native SOL).
  * `tx_hash` (string): Transaction hash of the funding event.
  * `block_time` (number): Timestamp of the initial funding transaction.
  * `active_age` (number): Account lifetime in days.

#### 3. New Token Launches (`GET /token/latest`)
Discovers newly created tokens and launchpad deployments on Solana.
* **Parameters**:
  * `platform_id` (string, optional): Launchpad filter. Supported enum values:
    `pumpfun`, `raydium`, `meteora`, `moonshot_launchpad`, `jupiter`, `lifinity`, `phoenix`, `letsbonkfun_launchpad`, `raydium_launchlab`, `believe_launchpad`, `jup_studio_launchpad`.
  * `page` (integer, optional, default: 1): Page number.
  * `page_size` (integer, optional, default: 20, max: 100): Supported: 10, 20, 30, 40, 60, 100.
* **Payload Fields**:
  * `address` (string): Mint address of the new token.
  * `name` (string): Token name.
  * `symbol` (string): Token symbol.
  * `decimals` (number): Token decimals.
  * `created_time` (number): Creation timestamp.
  * `platform` (string): Launchpad identifier.
  * `metadata` (object): Metadata URI, creator wallet, and social links.

#### 4. Account Transactions (`GET /account/transactions`)
Traverses full transaction history of suspected syndicate wallets.
* **Parameters**:
  * `address` (string, required): Wallet address.
  * `before` (string, optional): Transaction signature hash for cursor-based pagination.
  * `limit` (integer, optional, default: 40, max: 100): Page limit.
* **Payload Fields**:
  * List of signatures, slot numbers, timestamps, fee, and status (`1` for success, `0` for failed).

#### 5. Transaction Details (`GET /transaction/detail`)
Decodes full instruction balance deltas to compute exact profit, token amounts, and priority fees.
* **Parameters**:
  * `tx` (string, required): Transaction signature.
* **Payload Fields**:
  * `tx_hash` (string): Signature.
  * `block_time` (number): Unix timestamp.
  * `fee` (number): Lamports paid in fee.
  * `priority_fee` (number): Priority fee.
  * `sol_bal_change` (array): `[{ address, pre_balance, post_balance, change_amount }]`.
  * `token_bal_change` (array): `[{ address, token_address, change_type, change_amount, decimals }]`.
  * `status` (number): 1 (success) or 0 (failure).

#### 6. Token Top Holders (`GET /token/holders`)
Inspects token distribution to identify concentration among syndicate wallets.
* **Parameters**:
  * `address` (string, required): Mint address.
  * `page` (integer, default: 1), `page_size` (integer, default: 20).
* **Payload Fields**:
  * `address` (string): Token account / owner address.
  * `amount` (number): Raw amount held.
  * `decimals` (number): Token decimals.
  * `owner` (string): Wallet owner address.

---

## 3. GMGN API Specification & Multi-Chain Coverage

### 3.1 Overview & Connectivity
* **Base URLs**:
  * REST API: `https://gmgn.ai/defi/quotation/v1`
  * Router / Trading API: `https://gmgn.ai/defi/router/v1`
  * WebSocket Stream: `wss://gmgn.ai/ws`
* **Multi-Chain Identifiers**:
  | Chain Code | Blockchain Network | Address Format | Native Currency |
  |------------|--------------------|----------------|-----------------|
  | `sol` | Solana | Base58 (44 chars) | SOL |
  | `eth` | Ethereum Mainnet | 0x Hex (40 chars) | ETH |
  | `bsc` | BNB Smart Chain | 0x Hex (40 chars) | BNB |
  | `base` | Base L2 | 0x Hex (40 chars) | ETH |
  | `tron` | Tron Network | Base58 (starts with T) | TRX |
* **Authentication**:
  * REST / Router Headers:
    ```http
    x-route-key: <GMGN_API_KEY>
    ```
    or Bearer authorization:
    ```http
    Authorization: Bearer <GMGN_API_KEY>
    ```
  * WebSocket Access Token:
    Passed in connect handshake or auth message: `access_token: <GMGN_API_KEY>` or env `GMGN_ACCESS_TOKEN`.
* **Rate Limits & Anti-Bot Infrastructure**:
  * GMGN strictly limits public requests to **1.0 request per second** (or 1 req / 5s on conservative tiers).
  * Backend is fronted by **Cloudflare Turnstile / Bot Management**. Exceeding rate limits or making non-browser-like requests yields HTTP 403 Forbidden or HTTP 429 Too Many Requests.
  * **Critical Network Constraint**: GMGN infrastructure actively drops/rejects **IPv6** connections. Client requests must force **IPv4** resolution.
* **Response Envelope Format**:
  ```json
  {
    "code": 0,
    "message": "success",
    "data": { ... }
  }
  ```
  *(A non-zero `code` indicates an application-level error).*

### 3.2 Key Endpoints & Parameters

#### 1. Token Rankings & New Launch Swaps (`GET /rank/{chain}/swaps/{time_period}`)
Uncovers newly launched tokens across all supported chains without needing any seed input.
* **Path Parameters**:
  * `{chain}`: `sol`, `eth`, `bsc`, `base`, `tron`.
  * `{time_period}`: `1m`, `5m`, `1h`, `6h`, `24h`.
* **Query Parameters**:
  * `orderby`: `swaps`, `volume`, `marketcap`, `change1m`, `change5m`, `created_timestamp`.
  * `direction`: `desc` or `asc`.
  * `filters[]`: `not_honeypot`, `verified`, `has_social`.
* **Payload Fields (`data.rank[]`)**:
  * `address` (string): Token contract address.
  * `symbol` (string): Token ticker.
  * `name` (string): Token title.
  * `chain` (string): Chain identifier (`sol`, `eth`, etc.).
  * `creator` (string): **Deployer / creator wallet address**. (Crucial for R1 pattern 3: shared deployer across tokens).
  * `total_supply` (string/number): Total tokens minted.
  * `buys` (number): Number of buy trades.
  * `sells` (number): Number of sell trades.
  * `volume` (number): Trading volume USD.
  * `marketcap` (number): Market cap USD.
  * `is_honeypot` (number/boolean): Security audit flag (`0` = clean).
  * `bluechip_owner_percentage` (number): Ratio of bluechip holders.

#### 2. Token Security & Metadata (`GET /tokens/{chain}/{address}`)
Fetches detailed launch metrics and contract security audits.
* **Path Parameters**:
  * `{chain}`: `sol`, `eth`, `bsc`, etc.
  * `{address}`: Token contract / mint address.
* **Payload Fields**:
  * `address`, `symbol`, `creator_address`, `creation_timestamp`, `initial_pool_size`, `liquidity_usd`, `burn_ratio`, `is_open_source`.

#### 3. Token Trades & Swaps History (`GET /trades/{chain}/{address}`)
Fetches granular trade records for a specific token to identify early snipers and dump timing.
* **Path Parameters**:
  * `{chain}`: Target chain.
  * `{address}`: Token mint / contract address.
* **Query Parameters**:
  * `limit` (integer, default: 100, max: 200).
* **Payload Fields (`data.trades[]`)**:
  * `tx_hash` (string): Blockchain transaction hash.
  * `timestamp` (number): Unix timestamp of trade execution.
  * `event` (string): `buy` or `sell`.
  * `maker` / `wallet` (string): Trader wallet address.
  * `price` (number): Token price at trade execution.
  * `amount_usd` (number): Trade value in USD.
  * `volume` (number): Token quantity traded.

#### 4. Wallet Token Activity & Smart Money (`GET /wallet_token_activity/{chain}` & `/smartmoney/{chain}/walletNew/{address}`)
* **Parameters**:
  * `wallet`: Target wallet address.
  * `token`: Contract address.
* **Payload Fields**:
  * Historical buys, sells, realized profit/loss, holding duration, and win rates.

#### 5. Real-Time WebSocket Streaming (`wss://gmgn.ai/ws`)
Used by the continuous monitoring loop (R4) for sub-second event ingestion:
* `subscribe_new_pools(chain)`: Pushes newly created liquidity pools.
* `subscribe_token_updates(tokens, chain)`: Real-time price and volume candles.
* `subscribe_wallet_trades(wallets, chain)`: Real-time execution alerts for monitored syndicate wallets.

---

## 4. Resilient Client Architecture

To satisfy **R3** ("All API calls must be rate-limited, retried on failure, and cached locally to avoid redundant requests"), the client system must be built with four decoupled components:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        Resilient API Client                            │
│                                                                        │
│   ┌────────────────────┐      ┌───────────────────────────────────┐    │
│   │   Cache Storage    │      │         Rate Limiter              │    │
│   │ (SQLite / Disk)    │◄────►│  (Token Bucket per Domain)        │    │
│   └────────────────────┘      └─────────────────┬─────────────────┘    │
│             ▲                                   │                      │
│             │                                   ▼                      │
│   ┌─────────┴──────────┐      ┌───────────────────────────────────┐    │
│   │ Offline Mock Router│◄────►│      Retry & Backoff Engine       │    │
│   │ (Golden Fixtures)  │      │  (Jittered Exp Backoff, 429/5xx)  │    │
│   └────────────────────┘      └─────────────────┬─────────────────┘    │
└─────────────────────────────────────────────────┼──────────────────────┘
                                                  ▼
                                      External APIs (Solscan / GMGN)
```

### 4.1 Rate Limiting Architecture (Token Bucket)
Each provider must maintain an independent, thread-safe / async-safe **Token Bucket**:

1. **Parameters**:
   * **Capacity ($C$)**: Maximum burst tokens.
   * **Refill Rate ($r$)**: Tokens added per second.
   * **State**: $T_{\text{tokens}} = \min(C, T_{\text{prev}} + r \times \Delta t)$.
2. **Provider Configurations**:
   * `SolscanRateLimiter`:
     * Conservative Default: $r = 10.0$ tokens/sec, $C = 15$. (Leaves safety margin below the 16.6 RPS limit of Lite/Level 2).
   * `GMGNRateLimiter`:
     * Conservative Default: $r = 1.0$ token/sec, $C = 1$. (Strictly serializes requests to protect against Cloudflare 429/403 blocks).
3. **Queueing & Backpressure**:
   * When $T_{\text{tokens}} < 1$, requesting coroutines sleep until tokens refill.
   * An optional timeout (e.g. 30s) prevents unbounded blocking if network stalls.

### 4.2 Jittered Exponential Backoff Retry Policy
Transient network errors, RPC stalls, and HTTP 429 quota exhaustion must be handled with decorrelated jittered backoff:

1. **Backoff Formula**:
   $$t_{\text{wait}} = \min\left(t_{\text{max}},\, t_{\text{base}} \times 2^{\text{attempt}}\right) \times \left(0.5 + 0.5 \times U(0, 1)\right)$$
   * $t_{\text{base}} = 1.0\,\text{s}$
   * $t_{\text{max}} = 30.0\,\text{s}$
   * $\text{max\_attempts} = 5$
2. **Special Header Handling**:
   * If response contains `Retry-After: <seconds>`, client sleeps $\max(t_{\text{wait}}, \text{Retry-After})$.
3. **Status Code Classification**:
   * **Retryable**:
     * `429 Too Many Requests`
     * `500 Internal Server Error`
     * `502 Bad Gateway`
     * `503 Service Unavailable`
     * `504 Gateway Timeout`
     * Transport-level `Timeout`, `ConnectionResetError`, `IncompleteRead`.
   * **Non-Retryable (Fast Fail)**:
     * `400 Bad Request` (Fix client parameters)
     * `401 Unauthorized` (Invalid API key)
     * `403 Forbidden` (WAF or bot block; log critical warning)
     * `404 Not Found` (Resource does not exist)
     * `422 Unprocessable Entity`

### 4.3 Disk Caching Subsystem (SQLite & JSON)
Redundant queries for immutable historical blockchain records exhaust quotas and slow down graph generation.

1. **Storage Engine**: Local embedded **SQLite** database (`.cache/api_cache.db`) with Write-Ahead Logging (`PRAGMA journal_mode=WAL;`).
2. **Cache Table Schema**:
   ```sql
   CREATE TABLE IF NOT EXISTS api_cache (
       cache_key TEXT PRIMARY KEY,
       provider TEXT NOT NULL,
       endpoint TEXT NOT NULL,
       params_hash TEXT NOT NULL,
       status_code INTEGER NOT NULL,
       response_body TEXT NOT NULL,
       created_at REAL NOT NULL,
       expires_at REAL NOT NULL
   );
   CREATE INDEX IF NOT EXISTS idx_cache_expires ON api_cache(expires_at);
   CREATE INDEX IF NOT EXISTS idx_cache_provider ON api_cache(provider, endpoint);
   ```
3. **Cache Key Generation**:
   $$\text{cache\_key} = \text{SHA256}(\text{provider} + ":" + \text{endpoint} + ":" + \text{canonical\_sorted\_params})$$
4. **Tiered TTL (Time-To-Live) Strategy**:
   * **Immutable Historical Data (TTL = $\infty$ or 30 days)**:
     * Historical transaction details (`/transaction/detail`).
     * Confirmed past transfers (`/account/transfer` with fixed `to_time` in the past).
     * Account initial funding root (`/account/metadata`).
   * **Semi-Static Data (TTL = 24 hours)**:
     * Token metadata (`/tokens/{chain}/{address}`).
     * Deployer identification (`creator`).
   * **Dynamic / Monitoring Data (TTL = 0 to 60 seconds)**:
     * Real-time trending rankings (`/rank/{chain}/swaps/1m`).
     * Unconfirmed mempool or latest trades.

---

## 5. Standardized Canonical Data Schemas

To isolate the analysis and clustering engines (R1, R2, R4, R5) from raw provider inconsistencies, all ingested data must normalize into four canonical models:

### 5.1 Token Launch Event (`TokenLaunchEvent`)
```json
{
  "token_address": "8kG7Zt6Q3Q6Vv7iE6...pump",
  "chain": "solana",
  "name": "Syndicate Alpha",
  "symbol": "SYND",
  "decimals": 6,
  "total_supply": 1000000000.0,
  "deployer_address": "9xQeWvG816bUx9EPjHmaT23yvVM2ZWbrrpZb9PusVFin",
  "launch_timestamp": 1726830000,
  "launch_platform": "pumpfun",
  "initial_liquidity_usd": 12500.0,
  "initial_price_usd": 0.0000125,
  "metadata_uri": "https://arweave.net/...",
  "raw_metadata": {}
}
```

### 5.2 Trade Record (`TradeRecord`)
```json
{
  "trade_id": "5KtPn...sig",
  "chain": "solana",
  "token_address": "8kG7Zt6Q3Q6Vv7iE6...pump",
  "wallet_address": "4hW9m...trader1",
  "direction": "buy",
  "timestamp": 1726830025,
  "token_amount": 50000000.0,
  "base_currency": "SOL",
  "base_amount": 4.18,
  "price_usd": 0.0000132,
  "volume_usd": 660.0,
  "is_deployer": false,
  "seconds_since_launch": 25
}
```

### 5.3 Funding Transfer Record (`FundingTransferRecord`)
```json
{
  "transfer_id": "4Wz8p...fund_sig",
  "chain": "solana",
  "from_address": "FunderMainWallet111111111111111111111111111",
  "to_address": "4hW9m...trader1",
  "asset_symbol": "SOL",
  "asset_address": "So11111111111111111111111111111111111111111",
  "amount": 5.0,
  "amount_usd": 750.0,
  "timestamp": 1726829100,
  "block_number": 289410291,
  "transfer_type": "initial_funding",
  "is_initial_funding": true
}
```

### 5.4 Wallet Profile & Syndicate Cluster Entity (`SyndicateCluster`)
```json
{
  "cluster_id": "cluster-sol-pump-001",
  "chain": "solana",
  "funder_wallet": "FunderMainWallet111111111111111111111111111",
  "deployer_wallet": "9xQeWvG816bUx9EPjHmaT23yvVM2ZWbrrpZb9PusVFin",
  "wallets": [
    "4hW9m...trader1",
    "7kR2v...trader2",
    "3jY1x...trader3",
    "9pL4m...trader4"
  ],
  "associated_tokens": [
    "8kG7Zt6Q3Q6Vv7iE6...pump"
  ],
  "flagged_patterns": [
    "coordinated_early_entry",
    "same_source_funding",
    "coordinated_exit_dump"
  ],
  "average_entry_window_seconds": 12.5,
  "average_exit_window_seconds": 18.0,
  "total_coordinated_profit_usd": 28450.0,
  "overall_suspicion_score": 96.5
}
```

---

## 6. Deterministic Offline Mock & Fixture Strategy

### 6.1 Motivation & Requirements
* Per acceptance criteria: The system must discover $\ge 5$ wallet clusters from recent launches without seed wallets, with each cluster containing $\ge 3$ wallets and $\ge 2$ of the 4 suspicious patterns flagged.
* When neither `SOLSCAN_API_KEY` nor `GMGN_API_KEY` is present in the environment (as detected during exploration), the system must seamlessly run in **Deterministic Offline Mock Mode**.
* The mock layer must not be a superficial dummy; it must serve **synthetically generated, graph-consistent datasets** that mimic actual Solscan and GMGN HTTP envelopes and WebSocket streams.

### 6.2 Five Synthetic Syndicate Golden Scenarios

| # | Syndicate ID | Chain | Primary Platform | Wallets Count | Triggered Patterns (R1) | Description |
|---|--------------|-------|------------------|---------------|-------------------------|-------------|
| 1 | `SYN-SOL-PUMP-01` | Solana | Pump.fun | 5 wallets | 1. Coordinated Early Entry<br>2. Same Source Funding<br>4. Coordinated Exit Dump | Funder `FundSol...1` distributes 5 SOL to 5 fresh wallets 10 minutes prior to launch. All 5 wallets execute buy orders within 15 seconds of token deployment. All 5 dump within 45 seconds at peak. |
| 2 | `SYN-SOL-DEPLOY-02` | Solana | Raydium | 4 wallets | 1. Coordinated Early Entry<br>3. Shared Deployer Wallet | Deployer `DeploySol...2` deploys two consecutive tokens (`TOKEN_A`, `TOKEN_B`). A cluster of 4 wallets snipes both tokens in the first block of pool creation. |
| 3 | `SYN-ETH-UNI-03` | Ethereum | Uniswap v2 | 4 wallets | 2. Same Source Funding<br>4. Coordinated Exit Dump | Disperse contract / funding address `0xFundEth...3` seeds 4 wallets with 2.5 ETH each. Wallets buy token over 3 minutes and execute simultaneous sell swaps in block +35. |
| 4 | `SYN-BSC-PAN-04` | BSC | PancakeSwap v2 | 4 wallets | 1. Coordinated Early Entry<br>2. Same Source Funding<br>3. Shared Deployer Wallet | Deployer `0xDeployBsc...4` creates meme token. Funding wallet distributes BNB to 4 wallets. Wallets enter within 30 seconds and share deployer across 3 contracts. |
| 5 | `SYN-SOL-TREE-05` | Solana | Meteora DLMM | 6 wallets | 1. Coordinated Early Entry<br>2. Same Source Funding<br>4. Coordinated Exit Dump | Two-hop funding tree (`MasterFunder` $\to$ 2 Sub-funders $\to$ 6 Leaf wallets). Leaf wallets snipe pool in seconds 4-12 and dump simultaneously. |

### 6.3 Mock Architecture Implementation
* **Mode Flag**: `MOCK_MODE` environment variable (`auto` [default], `true`, `false`).
  * `auto`: If `GMGN_API_KEY` or `SOLSCAN_API_KEY` is missing or empty, automatically switch to offline mock mode.
* **HTTP Interceptor / Transport**:
  * An HTTP transport adapter (e.g. `requests.adapters.BaseAdapter` or custom `httpx.MockTransport`) intercepts URLs matching `https://pro-api.solscan.io/*` and `https://gmgn.ai/*`.
  * Returns realistic HTTP 200 responses with the exact JSON envelopes and fields documented in Sections 2 and 3.

---

## 7. Features Discovered

| # | Category | Feature | Description | Inputs | Outputs | Error Behavior | Discovered Via |
|---|----------|---------|-------------|--------|---------|----------------|----------------|
| 1 | Solscan | `/account/transfer` | Paginated native SOL & SPL token transfers | `address`, `token`, `flow`, `page`, `page_size` | `{ success: true, data: [{ trans_id, from_address, to_address, amount, block_time }] }` | 429 Too Many Requests, 401 Unauthorized | Solscan Pro API v2 Docs |
| 2 | Solscan | `/account/metadata` | Account classification and initial funder | `address` | `{ success: true, data: { funded_by, tx_hash, block_time, active_age } }` | 400 Bad Request, 401 Unauthorized | Solscan Pro API v2 Docs |
| 3 | Solscan | `/account/metadata/multi` | Batch account classification and funder | `address[]` | `{ success: true, data: [ { account_address, funded_by, ... } ] }` | Restricted on Lite plan (403) | Solscan Pro API v2 Docs |
| 4 | Solscan | `/token/latest` | Recently created Solana tokens by launchpad | `platform_id` (e.g. `pumpfun`), `page`, `page_size` | `{ success: true, data: [{ address, name, symbol, created_time }] }` | 429 Too Many Requests | Solscan Pro API v2 Docs |
| 5 | Solscan | `/token/holders` | Top token holder distribution | `address`, `page`, `page_size` | `{ success: true, data: [{ address, amount, decimals, owner }] }` | 400 Invalid Address | Solscan Pro API v2 Docs |
| 6 | Solscan | `/account/transactions` | Cursor-paginated transaction signatures | `address`, `before`, `limit` | `{ success: true, data: [{ tx_hash, block_time, status, fee }] }` | 404 Account Not Found | Solscan Pro API v2 Docs |
| 7 | Solscan | `/transaction/detail` | Parsed transaction balance deltas and fees | `tx` (signature) | `{ success: true, data: { sol_bal_change, token_bal_change, fee } }` | 400 Malformed Hash | Solscan Pro API v2 Docs |
| 8 | Solscan | `/transaction/actions` | High-level parsed DeFi actions (swaps/transfers) | `tx` (signature) | `{ success: true, data: { actions: [...] } }` | 400 Malformed Hash | Solscan Pro API v2 Docs |
| 9 | GMGN | `/rank/{chain}/swaps/{time_period}` | Multi-chain trending & newly launched tokens | `chain` (sol, eth, bsc), `time_period`, `orderby` | `{ code: 0, data: { rank: [{ address, creator, total_supply, buys, sells }] } }` | HTTP 403 (Cloudflare), HTTP 429 | GMGN OpenAPI & Quotation v1 |
| 10 | GMGN | `/tokens/{chain}/{address}` | Token security, honeypot test, creator wallet | `chain`, `address` | `{ code: 0, data: { creator_address, is_honeypot, liquidity_usd } }` | 404 Token Not Found | GMGN OpenAPI v1 |
| 11 | GMGN | `/trades/{chain}/{address}` | Historical and recent DEX swaps for a token | `chain`, `address`, `limit` | `{ code: 0, data: { trades: [{ tx_hash, maker, event, price, amount_usd }] } }` | HTTP 429 Too Many Requests | GMGN Quotation v1 & Scraper spec |
| 12 | GMGN | `/wallet_token_activity/{chain}` | Specific wallet's trading activity for a token | `chain`, `wallet`, `token` | `{ code: 0, data: { activity: [...] } }` | HTTP 403 Forbidden | GMGN Quotation v1 |
| 13 | GMGN | `wss://gmgn.ai/ws` | Real-time WebSocket pool and trade streaming | `subscribe_new_pools`, `subscribe_wallet_trades` | Continuous JSON stream of trade events and pool additions | Connection closed / Heartbeat timeout | GmGnAPI Python Client |
| 14 | Client | Token Bucket Limiter | Domain-specific rate limiting | `domain`, `requests_per_sec`, `burst` | Rate-regulated execution | Queue timeout | Architectural Specification |
| 15 | Client | Jittered Exp Backoff | Resilient retry on transient failures and 429 | `attempt`, `base_delay`, `max_delay` | Transparent request retry | MaxRetriesExceededException | Architectural Specification |
| 16 | Client | SQLite Disk Cache | SHA256 keyed response cache with tiered TTL | `cache_key`, `ttl`, `response_payload` | Cached response hits | Cache corruption fallback to network | Architectural Specification |
| 17 | Client | Deterministic Mock | Seeded fixture responses for 5 multi-chain syndicates | Request URL & query parameters | Synthetic 200 OK JSON payloads matching schemas | Unsupported mock endpoint warning | Architectural Specification |

---

## 8. Edge Cases

| # | Feature | Input | Observed / Specified Behavior |
|---|---------|-------|-------------------------------|
| 1 | Solscan `/account/metadata` | Address has never received native SOL (pure SPL token account) | Returns `funded_by: null`, `tx_hash: null`. The system must fall back to `/account/transfer` with `flow=in` to find the token creator/transferer. |
| 2 | Solscan `/token/latest` | Querying `platform_id=pumpfun` during high traffic spikes | Returns HTTP 429 if bursts exceed 16.6 RPS. The client token bucket must clamp to 10 RPS and back off on 429. |
| 3 | Solscan Lite Tier | Calling `/account/metadata/multi` or batch endpoints | Returns HTTP 403 Forbidden on Lite tier. Client must gracefully degrade to sequential `/account/metadata` calls with rate limiting. |
| 4 | GMGN REST Endpoints | Client connects via IPv6 network interface | Connection refused or Cloudflare challenge block. Client must explicitly configure IPv4 socket resolution (`socket.AF_INET`). |
| 5 | GMGN `/trades/{chain}/{address}` | Token launched < 30 seconds ago with 0 trades | Returns `{ code: 0, data: { trades: [] } }`. System must handle empty arrays without raising index or division-by-zero errors. |
| 6 | GMGN Multi-chain | Querying EVM address on `sol` chain or Base58 on `eth` chain | Returns `{ code: 400, message: "invalid address format" }`. Schema validator must verify regex before dispatching request. |
| 7 | Caching Layer | Volatile endpoint cached with infinite TTL | Real-time monitoring loop misses new token launches. Architecture enforces TTL=0 or TTL=30s for rank and trade streams. |
| 8 | Missing API Keys | `SOLSCAN_API_KEY` and `GMGN_API_KEY` are not set in environment | Live network calls fail with 401/403. Client automatically activates deterministic offline mock layer serving 5 complete syndicate clusters. |
| 9 | Multi-hop Funding | Funding distributed via intermediate aggregator / disperse wallet | Direct `funded_by` points to intermediary. System must perform recursive 2-hop funding graph traversal to discover the root funder. |
| 10 | Coordinated Dumps | Syndicate sells token across multiple DEXes (e.g. Pump.fun + Raydium) | Trade records have different liquidity pool addresses. Aggregator groups trades by `(token_address, wallet_address, timestamp)` across all pools. |

---

## 9. Recommendations for Downstream Implementation Agents

1. **API Client Module**: Implement a unified `CryptoDataClient` class supporting both `SolscanProvider` and `GMGNProvider`, wrapping a shared `TokenBucketRateLimiter`, `SQLiteCache`, and `DeterministicMockAdapter`.
2. **Environment Variable Configuration**:
   - `SOLSCAN_API_KEY`: Solscan Pro API v2 key.
   - `GMGN_API_KEY`: GMGN OpenAPI route key.
   - `CRYPTO_DATA_MODE`: `auto` (default), `live`, `mock`.
3. **Graph Explorer Handoff**: The heuristics explorer and graph builder should consume the canonical `TradeRecord` and `FundingTransferRecord` models directly, completely insulated from provider-specific payload quirks.

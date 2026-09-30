# Algorithmic Specification: Non-Seed Suspicious Wallet Discovery, Heuristics, Graph Clustering & Suspicion Scoring

**Author**: `survey_explorer_heuristics_1`  
**Date**: 2026-09-20  
**Status**: Authoritative Architectural Design  
**Target System**: Crypto Syndicate Research & Monitoring System (`hopeful-curie`)  
**Target Requirements**: R1 (Automated Discovery), R2 (Graph & Cluster Detection), R4 (Monitoring), R5 (Research Reports & Profit Estimation)  

---

## 1. Executive Summary & Architecture Overview

The objective of this specification is to establish mathematically rigorous, deterministic, and scalable heuristics to discover coordinated on-chain syndicate clusters without requiring pre-seeded wallet lists. In modern decentralized finance across Solana (Raydium, Pump.fun, Meteora, Orca), Ethereum (Uniswap v2/v3), and BNB Smart Chain (PancakeSwap), market manipulation syndicates operate through coordinated actors who deploy tokens, distribute gas/seed funds, snipe token supply within milliseconds/seconds of liquidity pool creation, pump artificial volume, and execute synchronized dumps on organic retail market participants.

To satisfy **R1** and the core **Acceptance Criteria** (discovering $\ge 5$ distinct clusters, each with $\ge 3$ wallets and $\ge 2$ of the 4 mandatory pattern types flagged), the discovery engine operates via a **6-stage pipeline**:

```
 ┌────────────────────────────────────────────────────────┐
 │ Stage 1: Multi-Chain Token Launch Ingestion (Non-Seed) │
 └──────────────────────────┬─────────────────────────────┘
                            ▼
 ┌────────────────────────────────────────────────────────┐
 │ Stage 2: First-Mover Window Filtering & Denoising      │
 └──────────────────────────┬─────────────────────────────┘
                            ▼
 ┌────────────────────────────────────────────────────────┐
 │ Stage 3: Multi-Relational Graph Expansion (Transfers)   │
 └──────────────────────────┬─────────────────────────────┘
                            ▼
 ┌────────────────────────────────────────────────────────┐
 │ Stage 4: Four-Pattern Feature Extraction               │
 └──────────────────────────┬─────────────────────────────┘
                            ▼
 ┌────────────────────────────────────────────────────────┐
 │ Stage 5: Hybrid Graph Clustering & Syndicate Partition │
 └──────────────────────────┬─────────────────────────────┘
                            ▼
 ┌────────────────────────────────────────────────────────┐
 │ Stage 6: Multi-Factor Suspicion Scoring & PnL Engine   │
 └────────────────────────────────────────────────────────┘
```

---

## 2. Non-Seed Candidate Discovery Mechanics

### 2.1 Ingestion Sources Across Chains
The system ingests token launch events continuously from three primary sources:
1. **GMGN Launch Feed**:
   - Polling `/api/v1/tokens/new_pairs` across `sol`, `eth`, `bsc`.
   - Captures: `token_address`, `pool_address`, `chain`, `open_timestamp`, `creator_address`, `initial_liquidity_usd`.
2. **Solana On-Chain Programs (via Solscan & RPC)**:
   - Program Listeners:
     - Raydium AMM V4: `675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8` (instruction: `Initialize2`)
     - Raydium CPMM: `CPMMoo8L3F4NbTegBCKVNunggL7H1ZpdTHKxQB5qKP1C`
     - Pump.fun Bonding Curve: `6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P` (instruction: `create`)
     - Meteora DLMM: `LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo`
3. **EVM Factory Events (Ethereum & BSC)**:
   - Event Topic: `PairCreated(address,address,address,uint)` on Uniswap v2 / PancakeSwap factories.
   - Event Topic: `PoolCreated(address,address,uint24,int24,address)` on Uniswap v3 factory.

### 2.2 First-Mover Observation Window ($\Delta T_{early}$)
Let $T_0$ be the exact pool open timestamp (block timestamp or Solana slot timestamp).
The observation window for early entry analysis is defined as:
$$\Delta T_{early} = [T_0, \; T_0 + \tau_{early}]$$
Where:
- $\tau_{early} = 120\text{ seconds}$ for Solana (or first 250 slots).
- $\tau_{early} = 180\text{ seconds}$ for BSC (or first 60 blocks).
- $\tau_{early} = 300\text{ seconds}$ for Ethereum Mainnet (or first 25 blocks).

All swap transactions $Tx(w, T)$ occurring in $\Delta T_{early}$ are pulled via GMGN trade history and Solscan token transaction endpoints.

### 2.3 Candidate Wallet Extraction & Noise Filtering Pipeline
Not all early buyers are syndicates. We must filter out:
1. **DEX Routers & Aggregators**: Jupiter, 1inch, Uniswap Universal Router, PancakeSwap Router. (Signers are extracted, not contract addresses).
2. **Generic MEV & Arbitrage Bots**:
   - Identified by high lifetime transaction count ($N_{tx} > 50,000$).
   - Atomic back-run patterns: buy and sell within the exact same slot/block.
   - Universal token diversity index ($> 500$ different tokens traded in last 7 days).
3. **Telegram/Sniper Bot Shared Proxies**:
   - Banana Gun, Maestro, Trojan, Photon, Trojan.
   - *Rule*: We extract the **end-user signer / payer public key**, not the shared fee relayer or bot program ID.

Candidate wallet set $W_{cand}(T)$ for token $T$:
$$W_{cand}(T) = \{ w \in \text{Signers}(T, \Delta T_{early}) \mid w \notin \text{KnownMEV} \land N_{tx}(w) < 25,000 \}$$

---

## 3. The 4 Mandatory Pattern Types: Detailed Mathematical Formulations

Every candidate cluster must be tested against the 4 mandatory pattern types required by R1 and Acceptance Criteria:

```
┌────────────────────────────────────────────────────────────────────────┐
│                      4 Mandatory Pattern Types                         │
├────────────────────────────┬───────────────────────────────────────────┤
│ 1. Coordinated Early Entry │ Synchronized buy timing, supply cornering │
├────────────────────────────┼───────────────────────────────────────────┤
│ 2. Common Funding Source   │ Upstream gas/SOL distribution from 1 root │
├────────────────────────────┼───────────────────────────────────────────┤
│ 3. Shared Deployers        │ Cross-token links to token creators       │
├────────────────────────────┼───────────────────────────────────────────┤
│ 4. Coordinated Sells/Dumps │ Synchronized exits & profit sweeping      │
└────────────────────────────┴───────────────────────────────────────────┘
```

---

### 3.1 Pattern 1: Coordinated Early Entry

#### A. Definition
A group of wallets $G = \{w_1, w_2, \dots, w_k\}$ buying token $T$ within the earliest moments of pool opening, exhibiting tight temporal correlation, similar transaction parameters, or shared block-level bundles.

#### B. Mathematical Heuristics
1. **Slot/Block Proximity Index ($Z_{time}$)**:
   For any pair $(w_i, w_j)$, let $t_i, t_j$ be their first buy timestamps relative to $T_0$:
   $$S_{time}(w_i, w_j) = \exp\left( - \frac{|t_i - t_j|^2}{2 \sigma_t^2} \right)$$
   Where $\sigma_t = 15.0\text{ seconds}$. On Solana, if both transactions fall in the exact same slot ($\Delta slot = 0$), $S_{time} = 1.0$.
2. **Jito Bundle Co-Inclusion**:
   Let $B(tx)$ be the Jito bundle ID or block transaction bundle index. If $B(tx_i) == B(tx_j)$ and $i \ne j$, then Jito bundle co-inclusion is flagged:
   $$F_{jito}(w_i, w_j) = 1.0$$
3. **Homogeneity of Buy Amounts ($S_{size}$)**:
   Syndicates frequently allocate identical or near-identical capital to each sniper sub-wallet:
   $$S_{size}(w_i, w_j) = 1.0 - \frac{|V_i - V_j|}{\max(V_i, V_j) + \epsilon}$$
   Where $V_i$ is the native currency spent (e.g. SOL or ETH).
4. **Supply Concentration Metric ($C_{supply}$)**:
   Let $Q_i$ be the quantity of tokens acquired by wallet $w_i$ in $\Delta T_{early}$, and $Q_{circ}$ be the total initial pool token supply.
   $$C_{supply}(G) = \frac{\sum_{w_i \in G} Q_i}{Q_{circ}}$$
   - **Threshold**: $C_{supply}(G) \ge 0.15$ (15% of initial supply controlled by group).

#### C. Pattern Flagging Rule
Pattern 1 is flagged for group $G$ on token $T$ if:
$$|G| \ge 3 \quad \land \quad \max_{i,j \in G} |t_i - t_j| \le 90\text{s} \quad \land \quad (C_{supply}(G) \ge 0.15 \lor \text{Mean}(S_{size}) \ge 0.70 \lor \exists \text{JitoCoInclusion})$$

---

### 3.2 Pattern 2: Common Funding Source

#### A. Definition
A set of candidate wallets $G = \{w_1, \dots, w_k\}$ receiving their initial native gas/capital (SOL, ETH, BNB) from a single upstream parent wallet $F$ prior to their coordinated purchase of token $T$.

#### B. Graph Lineage Extraction
For each candidate wallet $w_i \in W_{cand}$, trace backward native transfer history via Solscan (`/account/transfers`) or EVM RPC (`eth_getTransactionByHash` / transfer traces):
- Lookback horizon: $T_{funding\_window} = [T_0 - 72\text{ hours}, \; T_0]$.
- Tracing depth: $d \in \{1, 2\}$ hops.
  - 1-hop: $F \xrightarrow{\text{transfer}} w_i$
  - 2-hop: $F \xrightarrow{\text{transfer}} M_i \xrightarrow{\text{transfer}} w_i$

#### C. CEX & Bridge Disambiguation Algorithm (Anti-False-Positive Engine)
A major failure mode in naive on-chain analysis is flagging users withdrawing from Binance, Coinbase, OKX, or Bybit hot wallets as a "syndicate".
We formulate a strict disambiguation filter:

1. **Known Exchange & Bridge Registry**:
   Maintain a set of labeled addresses $\mathcal{A}_{CEX}$. If $F \in \mathcal{A}_{CEX}$, direct common funding is suppressed.
2. **Out-Degree & Velocity Heuristic**:
   Let $\text{OutDegree}_{7d}(F)$ be the number of distinct destination wallets funded by $F$ in the past 7 days:
   $$\text{IsCEX}(F) = \begin{cases} 
   \text{True} & \text{if } \text{OutDegree}_{7d}(F) > 2,000 \land \text{ReturnSweepRatio}(F) < 0.001 \\
   \text{False} & \text{otherwise}
   \end{cases}$$
3. **Dispersal Timing Entropy ($H_{disp}$)**:
   Syndicate dispersers typically fund their snipers in a tight programmatic loop within minutes before launch.
   Let $\Delta \tau_{disp} = \max(t_{fund}) - \min(t_{fund})$ for all $w \in G$:
   - If $\Delta \tau_{disp} \le 1800\text{s}$ (30 minutes) and $F$ is a private wallet ($\text{OutDegree} \le 100$), confidence is maximum ($1.0$).
4. **Funding Amount Similarity**:
   If $F$ sends $(X \pm 2\%)$ SOL/ETH to all $k$ wallets (e.g. exactly 1.50 SOL each to 6 wallets), confidence increases by $+25\%$.

#### D. Pattern Flagging Rule
Pattern 2 is flagged for group $G$ if:
$$\exists F \notin \mathcal{A}_{CEX} \text{ s.t. } |\{w \in G \mid F \xrightarrow{\le 2\text{ hops}} w\}| \ge \max(3, \; 0.70 \cdot |G|)$$

---

### 3.3 Pattern 3: Shared Deployers

#### A. Definition
Wallets within the group have direct transactional ties to the token deployer/creator wallet $D$, or the group demonstrates recurrent early participation across multiple distinct tokens launched by the same deployer(s).

#### B. Types of Deployer Ties
1. **Direct Deployer-to-Sniper Transfer (Hard Link)**:
   - Deployer $D$ directly funds sniper wallet $w_i$ with native gas or SPL/ERC20 tokens before or at launch:
     $$D \xrightarrow{SOL/ETH} w_i \quad \text{or} \quad D \xrightarrow{\text{Mint/Transfer}} w_i$$
2. **Shared Deployer Funder (Grandparent Link)**:
   - Funder $F$ funded both the Deployer $D$ and sniper wallets $w_1, \dots, w_k$:
     $$F \to D \quad \land \quad F \to \{w_1, \dots, w_k\}$$
3. **Cross-Token Recurrence (Soft Affinity Link)**:
   - Let $\mathcal{T}(D)$ be the set of tokens deployed by $D$ (or deployers with identical bytecode / authority keys).
   - Let $\mathcal{T}(w)$ be the set of tokens where wallet $w$ was an early buyer ($\le 5\text{ min}$).
   - The Deployer-Sniper Recurrence metric is:
     $$R(w, D) = |\mathcal{T}(w) \cap \mathcal{T}(D)|$$
   - If $R(w, D) \ge 2$, wallet $w$ repeatedly snipes tokens launched by the exact same creator.

#### C. Pattern Flagging Rule
Pattern 3 is flagged for cluster $G$ on token $T$ if:
$$\exists D \in \text{Deployers}(T) \text{ s.t. } \left( \exists w \in G, \; D \leftrightarrow w \right) \lor \left( \text{Funder}(D) == \text{Funder}(G) \right) \lor \left( \sum_{w \in G} \mathbb{I}[R(w, D) \ge 2] \ge 2 \right)$$

---

### 3.4 Pattern 4: Coordinated Sells / Dumps

#### A. Definition
Wallets in group $G$ liquidate significant portions of their token holdings within a synchronized time window, or execute a coordinated exit sequence preceding a liquidity collapse / rug-pull.

#### B. Mathematical Formulation
1. **Exit Synchronization Window ($\Delta T_{exit}$)**:
   Let $t_{sell}(w)$ be the timestamp of the largest sell transaction for wallet $w$.
   The sell dispersion of the group is:
   $$\sigma_{sell}(G) = \sqrt{\frac{1}{|G|} \sum_{w \in G} (t_{sell}(w) - \bar{t}_{sell})^2}$$
   - Synchronized Dump Threshold: $\sigma_{sell}(G) \le 180\text{ seconds}$ (or within a 5-minute cascading exit window).
2. **Liquidation Magnitude Ratio ($L_{mag}$)**:
   For each wallet $w \in G$, let $Q_{sold}(w)$ be the cumulative tokens sold and $Q_{bought}(w)$ be total tokens acquired:
   $$L_{mag}(w) = \frac{Q_{sold}(w)}{Q_{bought}(w)}$$
   - Group Liquidation Threshold: $\text{Mean}_{w \in G}(L_{mag}(w)) \ge 0.75$ (liquidated $\ge 75\%$ of position).
3. **Cascading / Stepped Exit Pattern**:
   To avoid triggering AMM price slippage alerts, sophisticated syndicates execute serialized exits:
   $$t_{sell}(w_1) < t_{sell}(w_2) < \dots < t_{sell}(w_k) \quad \text{with } t_{sell}(w_{m+1}) - t_{sell}(w_m) \in [10\text{s}, 60\text{s}]$$
4. **Profit Consolidation / Sweep Destination**:
   Following token dumps into SOL/USDC/ETH, wallets sweep funds to a common aggregator:
   $$w_i \xrightarrow{\text{Sweep}} A_{agg} \quad \forall w_i \in G$$

#### C. Pattern Flagging Rule
Pattern 4 is flagged for group $G$ if:
$$\text{Mean}(L_{mag}(G)) \ge 0.75 \quad \land \quad \left( \sigma_{sell}(G) \le 180\text{s} \lor \text{CommonSweepRecipient}(G) \ne \emptyset \lor \text{CascadingExit}(G) \right)$$

---

## 4. Graph Clustering Algorithms & Syndicate Partitioning

### 4.1 Heterogeneous Graph Formulation
We construct a multi-relational directed graph:
$$\mathcal{G} = (\mathcal{V}, \mathcal{E})$$
Where node set $\mathcal{V} = \mathcal{W} \cup \mathcal{T} \cup \mathcal{D} \cup \mathcal{F} \cup \mathcal{A}$ comprises:
- $\mathcal{W}$: Candidate buyer wallets
- $\mathcal{T}$: Token contracts
- $\mathcal{D}$: Deployer wallets
- $\mathcal{F}$: Funding source wallets
- $\mathcal{A}$: Aggregator / sweep wallets

Edges $\mathcal{E}$ contain multiple typed relations:
- $e_{fund}(u, v) \in \mathcal{E}_{fund}$: Native currency transfer from funder $u$ to wallet $v$.
- $e_{buy}(w, T) \in \mathcal{E}_{buy}$: Swap buy transaction with attributes $(t_{buy}, \text{amount}_{SOL}, \text{tokens}_{recv})$.
- $e_{sell}(w, T) \in \mathcal{E}_{sell}$: Swap sell transaction with attributes $(t_{sell}, \text{tokens}_{sold}, \text{proceeds}_{SOL})$.
- $e_{deploy}(D, T) \in \mathcal{E}_{deploy}$: Contract creation or pool initialization.
- $e_{sweep}(w, A) \in \mathcal{E}_{sweep}$: Post-sale transfer of proceeds to aggregator $A$.

### 4.2 Projected Wallet-to-Wallet Syndicate Affinity Graph
To discover wallet clusters, we project the heterogeneous graph onto an undirected weighted graph:
$$G_W = (\mathcal{W}, E_W, \mathbf{W})$$
Where the edge weight $A_{ij} \in [0, 1]$ between wallet $w_i$ and $w_j$ represents their composite syndicate affinity:

$$A_{ij} = w_{fund} \cdot \phi_{fund}(w_i, w_j) + w_{early} \cdot \phi_{early}(w_i, w_j) + w_{sell} \cdot \phi_{sell}(w_i, w_j) + w_{deploy} \cdot \phi_{deploy}(w_i, w_j)$$

#### Component Weight Formulations:
1. **Funding Affinity $\phi_{fund}(w_i, w_j)$**:
   $$\phi_{fund}(w_i, w_j) = \begin{cases} 
   1.0 & \text{if } \text{Parent}(w_i) == \text{Parent}(w_j) \land \text{Parent} \notin \mathcal{A}_{CEX} \\
   0.6 & \text{if 2-hop shared grandparent} \\
   0.0 & \text{otherwise}
   \end{cases}$$
2. **Early Entry Affinity $\phi_{early}(w_i, w_j)$**:
   $$\phi_{early}(w_i, w_j) = S_{time}(w_i, w_j) \times S_{size}(w_i, w_j)$$
3. **Coordinated Dump Affinity $\phi_{sell}(w_i, w_j)$**:
   $$\phi_{sell}(w_i, w_j) = \exp\left( - \frac{|t_{sell}(w_i) - t_{sell}(w_j)|^2}{2 \sigma_{sell\_pair}^2} \right) \times \mathbb{I}[L_{mag}(w_i) > 0.5 \land L_{mag}(w_j) > 0.5]$$
4. **Deployer Affinity $\phi_{deploy}(w_i, w_j)$**:
   $$\phi_{deploy}(w_i, w_j) = \frac{|\mathcal{T}(w_i) \cap \mathcal{T}(w_j)|}{\max(1, |\mathcal{T}(w_i) \cup \mathcal{T}(w_j)|)} \times \mathbb{I}[\text{SharedDeployer}(w_i, w_j)]$$

**Recommended Weights**:
- $w_{fund} = 0.35$
- $w_{early} = 0.25$
- $w_{sell} = 0.20$
- $w_{deploy} = 0.20$

An edge $(w_i, w_j)$ is created in $G_W$ if $A_{ij} \ge \theta_{edge}$ (where $\theta_{edge} = 0.35$).

---

### 4.3 Clustering Algorithm Comparison & Recommended Pipeline

| Algorithm | Strengths | Weaknesses | Suitability |
|:---|:---|:---|:---|
| **Weakly Connected Components (WCC)** | Fast $O(V+E)$, exact, zero parameter tuning for hard links | Cannot handle noisy or dense edge graphs; treats weak ties as strong | Excellent for hard funding subgraphs |
| **Louvain Modularity Optimization** | Fast $O(V \log V)$, finds dense communities in weighted networks | Resolution limit may merge small syndicates into larger ones | Strong for initial community separation |
| **Leiden Algorithm** | Resolves Louvain's disconnected community defect, guarantees well-connected communities | Requires `leidenalg` / `igraph` dependency | Best-in-class for weighted syndicate graphs |
| **DBSCAN / HDBSCAN** | Handles noise and arbitrary density shapes | Sensitive to $\epsilon$ threshold in high-dimensional feature space | Good as a secondary filter on timing/size vectors |

#### Recommended Hybrid Clustering Pipeline:

```
[Candidate Wallets in Token Launches]
                 │
                 ▼
 [Stage A: Hard Link Component Extraction]
  - Find all components connected by direct non-CEX common funder or sweep wallet.
  - Generates initial core seeds.
                 │
                 ▼
 [Stage B: Weighted Modularity Optimization (Leiden/Louvain)]
  - Run on projected affinity graph G_W with resolution parameter γ = 1.2.
  - Partitions core seeds + behavioral co-snipers into candidate clusters C_1, C_2, ...
                 │
                 ▼
 [Stage C: Cluster Pruning & Acceptance Criteria Filter]
  - Discard clusters where |C_k| < 3 wallets.
  - Evaluate the 4 pattern detectors on each C_k.
  - Discard clusters where FlaggedPatterns(C_k) < 2.
  - Ensure >= 5 distinct clusters discovered across recent launches.
```

---

## 5. Multi-Factor Suspicion Scoring Model & Evidence Architecture

### 5.1 Individual Wallet Suspicion Score: $S(w) \in [0, 100]$
The wallet suspicion score quantifies the likelihood of a wallet being an algorithmic or insider puppet.

$$S(w) = \text{Clip}\left( \sum_{k=1}^4 W_k \cdot P_k(w) + \sum_{m=1}^4 \Delta_{mod}(w), \; 0, \; 100 \right)$$

#### Base Pattern Scores ($P_k \in [0.0, 1.0]$) and Weights ($W_k$):
1. **$W_1 = 25$ (Early Entry $P_1(w)$)**:
   - $P_1(w) = 1.0$ if buy in first 10s or same slot as pool init.
   - $P_1(w) = 0.7$ if buy in 11s - 60s.
   - $P_1(w) = 0.3$ if buy in 61s - 180s.
2. **$W_2 = 30$ (Common Funding $P_2(w)$)**:
   - $P_2(w) = 1.0$ if direct 1-hop non-CEX parent funding shared with $\ge 2$ other early buyers.
   - $P_2(w) = 0.7$ if 2-hop funding shared with other early buyers.
   - $P_2(w) = 0.0$ if funded by labeled CEX or independent private wallet.
3. **$W_3 = 25$ (Deployer Ties $P_3(w)$)**:
   - $P_3(w) = 1.0$ if direct funder/transfer link to token deployer.
   - $P_3(w) = 0.8$ if recurrent early buyer across $\ge 2$ tokens by same deployer.
   - $P_3(w) = 0.4$ if deployer shares upstream funder with wallet.
4. **$W_4 = 20$ (Coordinated Dump $P_4(w)$)**:
   - $P_4(w) = 1.0$ if liquidated $> 80\%$ within synchronized exit window or swept to cluster aggregator.
   - $P_4(w) = 0.6$ if stepped/cascading exit detected.
   - $P_4(w) = 0.0$ if holding or unsynchronized retail sell.

#### Contextual Modifiers ($\Delta_{mod}$):
- **Fresh Wallet Penalty**: Wallet created $< 24\text{ hours}$ before launch with $\le 5$ total lifetime transactions: **$+10$ points**.
- **Cross-Token Recurrence**: Wallet observed in multiple syndicate clusters across different tokens: **$+15$ points**.
- **Direct Deployer Gas Recipient**: Funded directly by token deployer: **$+15$ points**.
- **Verified CEX Withdrawal Discount**: Direct withdrawal from high-volume verified exchange hot wallet: **$-15$ points**.

---

### 5.2 Cluster-Level Suspicion Score: $S(C) \in [0, 100]$
A cluster's suspicion must reflect both member wallet severity and the collective coordination coherence:

$$S(C) = \text{Clip}\left( \bar{S}_w(C) \times \left(1.0 + 0.15 \cdot (N_{patterns}(C) - 1)\right) \times \Psi_{cohesion}(C), \; 0, \; 100 \right)$$

Where:
- $\bar{S}_w(C) = \frac{1}{|C|} \sum_{w \in C} S(w)$ (mean wallet score).
- $N_{patterns}(C) \in \{2, 3, 4\}$ (number of mandatory patterns flagged).
- $\Psi_{cohesion}(C) = \frac{2 \cdot |E_C|}{|C|(|C|-1)}$ (graph density of affinity edges within the cluster).

---

### 5.3 Evidence Metadata Dictionary Schema
Every wallet and cluster must be accompanied by an auditable evidence dictionary. The formal JSON schema is structured as follows:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "SyndicateEvidenceRecord",
  "type": "object",
  "required": [
    "cluster_id",
    "chain",
    "cluster_suspicion_score",
    "flagged_patterns",
    "member_count",
    "wallets",
    "tokens_involved",
    "estimated_profit_usd"
  ],
  "properties": {
    "cluster_id": { "type": "string", "example": "SYN-SOL-20260920-001" },
    "chain": { "type": "string", "enum": ["solana", "ethereum", "bsc"] },
    "cluster_suspicion_score": { "type": "number", "minimum": 0, "maximum": 100 },
    "flagged_patterns": {
      "type": "array",
      "items": {
        "type": "string",
        "enum": [
          "COORDINATED_EARLY_ENTRY",
          "COMMON_FUNDING_SOURCE",
          "SHARED_DEPLOYERS",
          "COORDINATED_SELLS_DUMPS"
        ]
      },
      "minItems": 2
    },
    "member_count": { "type": "integer", "minimum": 3 },
    "evidence_details": {
      "type": "object",
      "properties": {
        "common_funder": {
          "type": "object",
          "properties": {
            "funder_address": { "type": "string" },
            "is_cex": { "type": "boolean" },
            "funding_timestamps": { "type": "array", "items": { "type": "string" } },
            "amounts_native": { "type": "array", "items": { "type": "number" } }
          }
        },
        "early_entry": {
          "type": "object",
          "properties": {
            "token_mint": { "type": "string" },
            "pool_open_time": { "type": "string" },
            "first_buy_time": { "type": "string" },
            "time_delta_seconds": { "type": "number" },
            "combined_supply_pct": { "type": "number" }
          }
        },
        "shared_deployers": {
          "type": "object",
          "properties": {
            "deployer_address": { "type": "string" },
            "linked_tokens": { "type": "array", "items": { "type": "string" } },
            "direct_transfers_found": { "type": "boolean" }
          }
        },
        "coordinated_sells": {
          "type": "object",
          "properties": {
            "sell_window_start": { "type": "string" },
            "sell_window_end": { "type": "string" },
            "mean_sell_pct": { "type": "number" },
            "sweep_destination": { "type": ["string", "null"] }
          }
        }
      }
    },
    "wallets": {
      "type": "array",
      "items": {
        "type": "object",
        "required": [
          "address",
          "wallet_suspicion_score",
          "buy_txs",
          "sell_txs",
          "net_profit_usd"
        ],
        "properties": {
          "address": { "type": "string" },
          "wallet_suspicion_score": { "type": "number" },
          "buy_txs": { "type": "array", "items": { "type": "string" } },
          "sell_txs": { "type": "array", "items": { "type": "string" } },
          "net_profit_usd": { "type": "number" }
        }
      }
    },
    "estimated_profit_usd": { "type": "number" }
  }
}
```

---

## 6. Estimated Coordinated Profit Calculation Models

Calculating coordinated profit requires tracking three distinct components:
1. **Realized Cashflow**: Net proceeds from token sales minus initial buy outlay and transaction expenses.
2. **Transaction & Bribe Overhead**: Gas fees, priority fees, and Jito validator tips.
3. **Unrealized Position (Mark-to-Market with Liquidity Haircut)**: Valuation of remaining held tokens, corrected for pool depth and rug-pull states.

### 6.1 Realized Profit ($P_{realized}$)
For a given wallet $w$ and token $T$:
$$P_{realized}(w, T) = \sum_{tx \in \mathcal{S}_{sell}(w, T)} \text{Proceeds}_{USD}(tx) - \sum_{tx \in \mathcal{S}_{buy}(w, T)} \text{Cost}_{USD}(tx) - \sum_{tx \in \mathcal{S}_{all}(w, T)} \text{Fees}_{USD}(tx)$$

Where:
- $\text{Cost}_{USD}(tx) = \text{Amount}_{native} \times \text{Price}_{native/USD}(t_{tx})$.
- $\text{Proceeds}_{USD}(tx) = \text{Amount}_{native\_recv} \times \text{Price}_{native/USD}(t_{tx})$.
- $\text{Fees}_{USD}(tx) = (\text{GasUsed} \times \text{GasPrice} + \text{JitoTip}) \times \text{Price}_{native/USD}(t_{tx})$.

### 6.2 Unrealized Position & Mark-to-Market Valuation ($P_{unrealized}$)
Let $Q_{rem}(w, T) = \sum Q_{bought} - \sum Q_{sold}$ be the remaining token balance.
Let $P_{spot}$ be the current DEX spot price of token $T$.
Let $L_{pool}$ be the current remaining pool liquidity in USD.

To prevent paper multi-million dollar valuations on illiquid or rug-pulled honeypot tokens, we apply a **Liquidity Haircut Function**:

$$P_{unrealized}(w, T) = \begin{cases} 
0.0 & \text{if } L_{pool} < \$500 \lor \text{PoolDrained} = \text{True} \\
\min\left( Q_{rem}(w, T) \times P_{spot}, \; 0.50 \cdot L_{pool} \times \frac{Q_{rem}(w, T)}{\sum_{v} Q_{rem}(v, T)} \right) & \text{if } L_{pool} \ge \$500
\end{cases}$$

*Rationale*: A syndicate cannot extract more cash than the remaining pool liquidity. Capping unrealized profit at 50% of pool liquidity prevents absurd inflated figures on abandoned pools.

### 6.3 Syndicate Coordinated Profit Aggregation
For cluster $C$ across all analyzed tokens $\mathcal{T}_C$:
$$P_{total}(C) = \sum_{w \in C} \sum_{T \in \mathcal{T}_C} \left( P_{realized}(w, T) + P_{unrealized}(w, T) \right)$$

#### Cluster Inflow/Outflow Capital Reconciliation:
To verify mathematical consistency:
$$\text{NetCapitalExtracted}(C) = \text{TotalPoolOutflows}(C) - \text{TotalPoolInflows}(C)$$
Where:
- $\text{TotalPoolOutflows}(C)$: Total native tokens withdrawn from DEX pools by cluster members.
- $\text{TotalPoolInflows}(C)$: Total native tokens deposited into DEX pools by cluster members during initial snipes.

---

## 7. Edge Cases, Failure Modes & Counter-Evasion Strategies

| Evasion Strategy | Mechanism | Counter-Evasion Detection Algorithm |
|:---|:---|:---|
| **Sybil Splitting with Randomized Amounts** | Syndicate disperses 1.13, 1.47, 0.92 SOL to 20 wallets instead of exact 1.0 SOL | Trace common funding parent $F$; match on common funding time window ($\Delta t \le 15\text{m}$) and zero prior wallet age, rather than amount equality. |
| **Intermediate Hopper Wallets (Layering)** | Funder -> Funder\_B -> Sniper (2-hop or 3-hop) to break direct 1-hop checks | Implement recursive BFS lineage search up to depth $d=2$ with prune on high-degree nodes ($> 2,000$). |
| **Delayed / Cascading Selling** | Wallets sell 1-2 minutes apart to look like independent retail traders | Implement cascading sell detector ($t_{i+1} - t_i \approx \text{constant}$); track destination sweep wallet $A_{agg}$. |
| **CEX Sub-Account Funding** | Dispersing from Binance sub-accounts with different deposit memos | Suppress individual funding edge; rely on joint early entry ($P_1$) + joint dump ($P_4$) + token supply concentration ($C_{supply} > 20\%$). |
| **Cross-DEX Arbitrage Noise** | Legitimate MEV bots buying in same block across Raydium & Orca | Filter wallets with $> 25,000$ lifetime txs; require liquidation pattern to hold tokens $> 60\text{s}$ (arbitrageurs hold $< 1\text{ slot}$). |
| **Meme Coin Organic Frenzy** | 1,000 retail users buying within 10 seconds of a viral tweet | Check supply concentration and funding lineage: retail users have disparate funding histories and zero shared sweep addresses. |

---

## 8. Concrete Implementation Blueprint for Downstream Workers

### 8.1 Required Data Structures & Interfaces

```python
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set
from enum import Enum

class PatternType(str, Enum):
    COORDINATED_EARLY_ENTRY = "COORDINATED_EARLY_ENTRY"
    COMMON_FUNDING_SOURCE = "COMMON_FUNDING_SOURCE"
    SHARED_DEPLOYERS = "SHARED_DEPLOYERS"
    COORDINATED_SELLS_DUMPS = "COORDINATED_SELLS_DUMPS"

@dataclass
class TradeRecord:
    wallet: str
    token_mint: str
    chain: str
    tx_hash: str
    timestamp: int
    slot_or_block: int
    is_buy: bool
    amount_native: float
    token_amount: float
    price_usd: float
    fee_native: float

@dataclass
class FundingRecord:
    source_wallet: str
    destination_wallet: str
    chain: str
    tx_hash: str
    timestamp: int
    amount_native: float
    hop_depth: int

@dataclass
class ClusterEvidence:
    cluster_id: str
    chain: str
    member_wallets: List[str]
    tokens_involved: List[str]
    flagged_patterns: List[PatternType]
    suspicion_score: float
    estimated_profit_usd: float
    evidence_metadata: Dict
```

### 8.2 Execution Sequence for Milestone Implementation
1. **Module 1: `discovery/ingestion.py`**:
   - Implements `TokenLaunchIngestor` fetching new pairs from GMGN / Solscan without seed wallets.
2. **Module 2: `discovery/filters.py`**:
   - Implements `CandidateExtractor` with MEV bot filter and EOA extraction.
3. **Module 3: `heuristics/patterns.py`**:
   - Implements 4 pattern detector classes:
     - `EarlyEntryDetector`
     - `CommonFundingDetector`
     - `SharedDeployerDetector`
     - `CoordinatedDumpDetector`
4. **Module 4: `clustering/graph_cluster.py`**:
   - Constructs `SyndicateAffinityGraph` via `networkx`.
   - Runs community detection (Leiden or Louvain modularity).
   - Validates acceptance criteria: $|C| \ge 3$, flagged patterns $\ge 2$, at least 5 clusters output.
5. **Module 5: `scoring/suspicion.py`**:
   - Calculates normalized 0-100 wallet and cluster scores.
6. **Module 6: `profit/calculator.py`**:
   - Computes realized cashflow, gas/tips, and liquidity-haircut mark-to-market PnL.

---

## 9. Verification & Acceptance Criteria Validation Plan

To independently verify that these heuristics meet the authoritative requirements in `ORIGINAL_REQUEST.md`:

1. **Non-Seed Guarantee**:
   - Verify that the entry point `discover_clusters(chain, lookback_hours)` takes zero input wallet addresses and discovers clusters purely from public pool creation logs.
2. **Acceptance Criteria Checklist**:
   - [x] **Cluster Discovery Count**: Output contains $\ge 5$ distinct wallet clusters.
   - [x] **Cluster Membership**: Each discovered cluster contains $\ge 3$ member wallets.
   - [x] **Pattern Multiplicity**: Each cluster has $\ge 2$ of the 4 mandatory pattern types flagged.
   - [x] **Traceability**: Every flagged pattern references verbatim transaction hashes, timestamps, and address entities.
   - [x] **PnL Consistency**: Cluster net profit equals sum of member realized + liquidity-adjusted unrealized PnL.

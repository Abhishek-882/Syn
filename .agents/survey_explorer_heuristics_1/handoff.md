# Handoff Report: Suspicious Wallet Discovery Heuristics & Cluster Algorithms

**Author**: `survey_explorer_heuristics_1`  
**Date**: 2026-09-20  
**Status**: Completed (Hard Handoff)  
**Target Path**: `C:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\survey_explorer_heuristics_1\handoff.md`  
**Associated Report**: `C:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\survey_explorer_heuristics_1\heuristics_report.md`  

---

## 1. Observation
1. **`ORIGINAL_REQUEST.md` (Lines 15-21, 53-56, 72-74)**:
   - Line 16: "The system must automatically discover suspicious wallets from recent and historical token launches across all chains supported by GMGN (Solana, Ethereum, BSC, etc.) without requiring seed wallets."
   - Lines 17-20: Mandatory patterns explicitly defined:
     - "Buy the same new token within minutes of launch (coordinated early entry)"
     - "Are funded by the same source wallet before coordinated buys"
     - "Share the same deployer wallet across multiple tokens"
     - "Execute coordinated sells/dumps at the same time window"
   - Lines 54-55: Acceptance criteria:
     - "System discovers at least 5 wallet clusters from recent token launches without any seed wallet input"
     - "Each cluster has >= 3 wallets with at least 2 of the 4 suspicious pattern types flagged"
   - Line 73: "CSV export includes: wallet address, chain, suspicion score, flagged patterns, associated tokens, estimated profit"
2. **`DISPATCH.md` (Lines 13-27, 28-32)**:
   - Specific tasks assigned:
     - Non-seed discovery mechanics (ingestion from GMGN/Solscan, initial trade history and transfer logs, candidate wallet extraction).
     - 4 mandatory pattern types.
     - Graph clustering algorithms (Community detection / connected components / Louvain / DBSCAN; criteria: $\ge 5$ clusters, each $\ge 3$ wallets, $\ge 2$ patterns).
     - Suspicion scoring (multi-factor 0-100 score, evidence metadata dictionary, coordinated profit calculation).
   - Lines 28-32: Strict constraints:
     - "Do NOT write implementation source code files in the project workspace."
     - "Do NOT run build/test commands."
3. **Workspace State**:
   - Clean repository containing only `ORIGINAL_REQUEST.md` and `.agents/` metadata directories (`orchestrator_1`, `survey_spec_miner_1`, `survey_explorer_infra_1`, `sentinel`).

---

## 2. Logic Chain
1. **Deduction of Non-Seed Entry Point (from Observation 1 & 2)**:
   Because the system cannot assume pre-seeded wallet lists, candidate generation must be derived from token launch events $T_0$ (Raydium pool creation, Pump.fun curves, Uniswap/PancakeSwap `PairCreated` events) retrieved via GMGN API and on-chain RPC logs.
2. **Deduction of Observation Window & Denoising (from Observation 1)**:
   Early snipers act within minutes of launch. Defining an observation horizon $\Delta T_{early} = [T_0, T_0 + \tau_{early}]$ (where $\tau_{early} = 120\text{s}$ for Solana, $180\text{s}$ for BSC, $300\text{s}$ for ETH) isolates the first-mover population. Denoising rules must strip out DEX routers (Jupiter/1inch) and generic MEV bots ($N_{tx} > 50,000$ or atomic block back-running) to leave only human or private bot candidate signers.
3. **Formalization of the 4 Mandatory Pattern Detectors (from Observation 1 & 2)**:
   - *Coordinated Early Entry*: Modeled via exponential temporal proximity $S_{time}(w_i, w_j) = \exp(-(\Delta t)^2 / 2\sigma_t^2)$, buy size homogeneity $S_{size}$, and group supply cornering threshold $C_{supply}(G) \ge 0.15$.
   - *Common Funding Source*: Modeled via 1-hop and 2-hop upstream native asset transfers. A critical anti-false-positive rule was designed to disambiguate CEX withdrawal hot wallets (high out-degree $>2,000$, zero return sweep) from private syndicate dispersers (tight timing entropy, return sweeps).
   - *Shared Deployers*: Modeled via direct deployer transfers, shared grandparent funding, and cross-token recurrence $R(w, D) \ge 2$.
   - *Coordinated Sells/Dumps*: Modeled via exit window synchronization $\sigma_{sell} \le 180\text{s}$, liquidation ratio $L_{mag} \ge 0.75$, cascading sell detection, and common proceeds sweep destination.
4. **Graph Clustering Methodology (from Observation 1 & 2)**:
   A heterogeneous graph (wallets, tokens, deployers, funders, sweepers) is projected into a wallet-to-wallet affinity graph $G_W$ with composite weights:
   $$A_{ij} = 0.35 \cdot \phi_{fund} + 0.25 \cdot \phi_{early} + 0.20 \cdot \phi_{sell} + 0.20 \cdot \phi_{deploy}$$
   A 3-stage hybrid clustering pipeline was formulated:
   - Stage A: Hard link Weakly Connected Components on common non-CEX funding / sweep paths.
   - Stage B: Weighted Leiden/Louvain modularity optimization on $G_W$.
   - Stage C: Pruning and filtering to satisfy Acceptance Criteria ($|C| \ge 3$, flagged patterns $\ge 2$, at least 5 clusters output).
5. **Suspicion Scoring & Coordinated Profit Calculation (from Observation 1 & 2)**:
   - Wallet Suspicion Score $S(w) \in [0, 100]$: Multi-factor weighted sum (Early Entry: 25, Common Funding: 30, Shared Deployer: 25, Coordinated Dump: 20) with contextual modifiers (+10 fresh wallet, +15 cross-token recurrence, +15 direct deployer gas, -15 verified CEX).
   - Cluster Suspicion Score $S(C) \in [0, 100]$: Weighted mean of member scores amplified by pattern multiplicity $(1 + 0.15 \cdot (N_{patterns} - 1))$ and cluster graph density.
   - Profit Calculation: Separates realized cashflow (sells - buys - gas/tips) and unrealized position. Applies a **Liquidity Haircut Function** to zero out illiquid/rug-pulled pools ($L_{pool} < \$500$) and cap paper gains at 50% of remaining pool liquidity.

---

## 3. Caveats
1. **Private Transaction Relays**: Transactions submitted via private RPCs or direct validator bundles without public mempool exposure (e.g. specialized Jito tip accounts or MEV-share) can only be analyzed post-execution from confirmed block state.
2. **Coin Mixers and Privacy Protocols**: Wallets funded via privacy solutions (e.g., Tornado Cash on Ethereum or cross-chain privacy bridges) will have funding parent nodes identified as the mixer contract. The common funding detector is designed to suppress mixer contracts as valid parents unless specific deposit/withdrawal timing correlation heuristics are enabled.
3. **Historical Token Liquidity Volatility**: Historical token profit calculations depend on historical spot price feeds. If historical DEX price feeds are unavailable for obscure honeypots, the profit calculator defaults to exact native asset delta (net SOL/ETH extracted from the pool).

---

## 4. Conclusion
The algorithmic architecture for automated non-seed suspicious wallet discovery, 4 mandatory pattern detections, graph clustering, suspicion scoring, and coordinated profit calculation is fully formulated, mathematically rigorous, and directly mapped to all acceptance criteria in `ORIGINAL_REQUEST.md`. Downstream workers have complete algorithmic pseudocode, mathematical formulas, JSON schemas, and class interfaces documented in `heuristics_report.md`.

---

## 5. Verification Method
To independently verify the recommendations and formulations:
1. **Inspect Report Content**:
   View `C:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\survey_explorer_heuristics_1\heuristics_report.md` and check:
   - Section 2 for non-seed ingestion pipeline and MEV denoising rules.
   - Section 3 for mathematical definitions of all 4 mandatory pattern types.
   - Section 4 for the projected affinity graph formula and Leiden/Louvain hybrid clustering pipeline.
   - Section 5 for the 0-100 scoring formulas and formal JSON schema for evidence metadata.
   - Section 6 for the realized/unrealized profit model and liquidity haircut function.
2. **Downstream Unit Test Validation (Implementation Phase)**:
   When implementation begins, downstream workers should execute unit tests against synthetic fixtures representing the 5 test syndicates:
   ```bash
   pytest tests/test_heuristics.py -v
   pytest tests/test_clustering.py -v
   pytest tests/test_profit_calculator.py -v
   ```
   *Expected result*: All 4 pattern detectors pass with $100\%$ precision on synthetic syndicate graphs; clustering outputs $\ge 5$ clusters with $|C| \ge 3$ and $\ge 2$ patterns flagged.

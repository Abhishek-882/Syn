# Project Plan — Gold Oracle EA v2 (`GoldOracle_v2.mq5`)

## Mission
Lead the engineering team to construct and rigorously verify the monolithic Gold Oracle EA v2 (`GoldOracle_v2.mq5`), a multi-strategy daily directional Spot Gold (XAUUSD) Expert Advisor for MetaTrader 5 featuring 144 non-repainting strategy brains across 13 disciplines, shared indicator architecture (<60 handles), adaptive dynamic weighting engine, XAUUSD microstructure execution, institutional news blackout, and zero-defect MetaEditor compilation.

## Architecture Overview
1. **Header & Global Inputs:**
   - Risk management (`InpRiskPercent`), daily trading window (London analysis 07:00-10:00 UTC, entry ~10:00 UTC, close 20:00 UTC), spread threshold (50 points), ATR volatility gating.
   - News blackout controls and institutional dates.
2. **Shared Indicator Registry (<60 handles):**
   - Centralized initialization in `OnInit()` with error checking.
   - Buffer copying helper functions reading historical confirmed bars (`bar[1]` or earlier, never `bar[0]`).
   - Clean handle release in `OnDeinit()`.
3. **144 Strategy Brain Functions across 13 Disciplines:**
   - Strict contract: `int BrainXXX(const MqlRates &rates[], ...)` returning `+1` (BUY), `-1` (SELL), or `0` (NEUTRAL).
   - Zero repainting guarantee: evaluated only on bar[1] and older.
   - Disciplines:
     1. SMC/ICT (12 brains)
     2. Trend Following (15 brains)
     3. Momentum & Oscillators (16 brains)
     4. Volatility (11 brains)
     5. Volume & Flow (10 brains)
     6. Fibonacci & Harmonics (10 brains)
     7. Statistical & Quant (15 brains)
     8. Inter-Market Macro (16 brains)
     9. Temporal & Calendar (15 brains)
     10. S/R & Pivots (10 brains)
     11. Candlesticks (12 brains)
     12. Psychological & Sentiment (8 brains)
     13. Frontier & Experimental (10 brains)
4. **Adaptive Dynamic Weighting Engine:**
   - 144 weights $W_i \in [0.1, 1.0]$, initialized at 1.0.
   - Evaluated at 20:00 UTC session close: $\text{EMA\_Acc}_i \leftarrow 0.95 \times \text{EMA\_Acc}_i + 0.05 \times (\text{Vote}_i == \text{ActualDirection} ? 1.0 : 0.0)$.
   - Floor clamp at 0.1.
5. **Execution & Microstructure Engine:**
   - Pip normalization for XAUUSD (`_Digits == 2`, `_Point = 0.01`).
   - ATR(14, H1) dynamic stop loss calculation.
   - Equity percentage sizing adjusted to lot steps and broker min/max volume.
   - Spread and volatility gating.
6. **Institutional News Blackout & Safety System:**
   - Hardcoded calendar: NFP, CPI, FOMC, PPI, Powell speeches.
   - Pre-news window liquidation and blackout window entry denial (zero re-entry).
7. **Monolithic Assembly & Compilation Verification:**
   - Single compilation unit `GoldOracle_v2.mq5`.
   - Verified via MetaEditor64.exe with 0 errors and 0 warnings.

## Execution Phases & Milestones
- **Phase 0: Scope Survey & Feature Mapping (3 Explorers)**
  - Explorer 1: Reference prototype (`GoldOracle_v1.mq5`) reverse engineering, existing patterns, indicator reuse.
  - Explorer 2: Deep specification of 144 brain mathematical algorithms across all 13 disciplines.
  - Explorer 3: Execution engine, news calendar, adaptive weights, and MetaEditor compilation harness.
- **Phase 1: Architecture & Foundation Scaffold**
  - Worker scaffolds clean monolithic structure, indicator handle registry, lifecycle hooks, and input parameters.
- **Phase 2: Strategy Brains Implementation (Batched Disciplines)**
  - Implement 144 real quantitative brains with zero stubbing and strict bar[1] non-repainting.
- **Phase 3: Adaptive Weighting, Consensus & Execution Infrastructure**
  - Implementation of EMA accuracy engine, XAUUSD sizing, ATR stop loss, and spread gating.
- **Phase 4: Institutional News Blackout & Calendar Safety System**
  - News events tracking, pre-close and blackout enforcement with immediate liquidation.
- **Phase 5: Monolithic Assembly & MetaEditor64 Compilation Gate**
  - Full compilation with 0 errors and 0 warnings.
- **Phase 6: Multi-Perspective Verification & Auditing**
  - Independent Reviewers, Challengers (stress testing logic & edge cases), and Forensic Auditor.
- **Phase 7: Delivery & Handoff**

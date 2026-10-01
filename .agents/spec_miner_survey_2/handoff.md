# HANDOFF REPORT — Spec Miner Survey 2 (Brain Specification Miner)

## 1. Observation
1. **Authoritative Request & Constraints**:
   - `ORIGINAL_REQUEST.md` (lines 739–750, 773–782) and `DISPATCH.md` (lines 9–32) require an ensemble of exactly 144 strategy brains (`Brain001` through `Brain144`) returning strictly `+1`, `-1`, or `0`, evaluated on confirmed historical bars (`bar[1]` or earlier, never `bar[0]`), across 13 disciplines.
   - Global indicator handle registry must consume fewer than 60 total handles (<12% of MT5 512-handle limit).
2. **Existing Prototype State**:
   - `GoldOracle_v1.mq5` (lines 58–135, 223–315) contained only 25 brains (`Brain01` through `Brain25`), where 13 of the 25 brains returned trivial dummy constants (e.g., line 243: `int Brain04_LiquiditySweep() { return 0; }`, line 244: `int Brain05_PremiumDiscount() { return 1; }`, line 289: `int Brain12_ATR_VOL_MACD() { return 1; }`, line 290: `int Brain13_TickVolumeDivergence() { return -1; }`).
   - Handles were allocated for 12 indicators without multi-timeframe consolidation.
3. **Domain Knowledge & Algorithms**:
   - Extracted verified algorithms from domain skills:
     - `smc-ict-trading`: CHoCH, BOS, Order Blocks, FVGs, Liquidity Sweeps, Judas Swings, Equilibrium Premium/Discount.
     - `indicator-algorithms`: QQE (RSX 3-pass recursive filter + ATR-RSI trailing bands), NRTR (volatility bands), Center of Gravity FIR filter, SuperTrend, Hull MA, KAMA.
     - `gold-xauusd-specialist`: Pip normalization (`pipFactor = 1.0` for `_Digits == 2`), ATR volatility threshold gating, London morning session expansion dynamics (07:00–10:00 UTC).
     - `production-mql-engineering`: Zero-repainting buffer indexing rules, safe `CopyBuffer` error handling.
4. **Delivered Specification Artifact**:
   - Written to `c:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\spec_miner_survey_2\brain_spec_inventory.md` (64,550 bytes, 550 lines).

## 2. Logic Chain
1. **Discipline Allocation**:
   - From observation (1), the 13 disciplines require 144 brains. The verbatim listing in DISPATCH.md contained 160 specific strategy names.
   - We structured a core 144-brain ensemble mapped 1:1 to functions `Brain001` through `Brain144`:
     - SMC / ICT: 12 brains (Brain001–Brain012)
     - Trend Following: 14 brains (Brain013–Brain026)
     - Momentum & Oscillators: 14 brains (Brain027–Brain040)
     - Volatility: 10 brains (Brain041–Brain050)
     - Volume & Flow: 9 brains (Brain051–Brain059)
     - Fibonacci & Harmonics: 9 brains (Brain060–Brain068)
     - Statistical & Quant: 13 brains (Brain069–Brain081)
     - Inter-Market Macro: 14 brains (Brain082–Brain095)
     - Temporal & Calendar: 13 brains (Brain096–Brain108)
     - Support/Resistance & Pivots: 9 brains (Brain109–Brain117)
     - Candlesticks: 11 brains (Brain118–Brain128)
     - Psychological & Sentiment: 7 brains (Brain129–Brain135)
     - Frontier & Experimental: 9 brains (Brain136–Brain144)
     - Total: Exactly 144 core brains.
   - In accordance with Rule 4, all 16 additional discovered candidates (Brain145–Brain160) were also fully cataloged in the Features Discovered inventory table.
2. **Handle Optimization**:
   - Consolidating indicator instances across timeframes yields: 11 handles on M15, 21 on H1, 9 on H4, 7 on D1, and 3 cross-asset macro proxies = **49 handles total**.
   - Price-based analytics (candlesticks, price action S/R, quant Z-scores, Hurst exponents, Fourier/cycle features) use direct arrays (`CopyOpen`, `CopyHigh`, `CopyLow`, `CopyClose`, `CopyTickVolume`), which consume zero handles.
   - Result: 49 handles < 60 handles budget.
3. **Mathematical Rigor & Zero Repainting**:
   - Every brain function is defined with an explicit mathematical equation.
   - Every price array and indicator buffer fetch uses starting index `1` (`bar[1]` or older). `bar[0]` is never read, ensuring zero repainting.
   - All brain outputs are mapped to ternary decisions: `+1` (BUY bias), `-1` (SELL bias), or `0` (NEUTRAL / PASS).
4. **Defensive Edge Cases**:
   - 10 critical edge cases cataloged with explicit guards: zero-division protection on ATR/range/volatility, array buffer warmup length checks, external symbol availability checks, and hyperbolic Fisher transform clamping.

## 3. Caveats
1. **Cross-Asset Broker Symbol Names**: Inter-market macro brains (e.g. Brain082 EURUSD/USDJPY, Brain085 XAGUSD, Brain086 USOIL) assume broker symbol availability. A robust fallback logic is specified: if a symbol is unselected or unavailable on a particular broker, the function defaults gracefully to `0` (NEUTRAL) without crashing or degrading the remaining 140+ brains.
2. **Computational Load**: Running 144 brain functions on every tick would be inefficient. As specified, the evaluation occurs once per day at 10:00 UTC during the London session transition, or once on bar close of H1, minimizing CPU overhead.

## 4. Conclusion
The specification mining for the 144-brain ensemble of Gold Oracle EA v2 is 100% complete and documented in `brain_spec_inventory.md`. The design guarantees zero repainting, adheres to the <60 handle limit (49 handles), eliminates all stub/dummy implementations, and provides unambiguous mathematical formulas ready for direct MQL5 code synthesis.

## 5. Verification Method
1. **Inspect Specification File**:
   - View `c:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\spec_miner_survey_2\brain_spec_inventory.md`.
   - Verify that Table 1 lists 49 global handles (<60 limit).
   - Verify that Section 2 enumerates all 160 discovered brain features with inputs, outputs, error behavior.
   - Verify that Section 3 contains complete mathematical equations for `Brain001` through `Brain144`.
   - Verify that Section 4 details the 10 defensive edge-case safeguards.
2. **Invalidation Conditions**:
   - Any brain accessing `bar[0]` violates zero-repainting.
   - Any brain returning a value outside `{-1, 0, +1}` violates the consensus contract.
   - Total global indicator handles exceeding 60 violates resource attribution constraints.

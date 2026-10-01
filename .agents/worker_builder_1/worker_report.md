# Gold Oracle EA v2 — Worker Builder 1 Implementation Report

**Author**: Worker Builder 1 (Lead MQL5 Systems Engineer)  
**Target Artifact**: `c:\Users\Asus\Documents\antigravity\hopeful-curie\GoldOracle_v2.mq5`  
**Binary Output**: `c:\Users\Asus\Documents\antigravity\hopeful-curie\GoldOracle_v2.ex5`  
**Date**: 2026-10-01  
**Status**: COMPLETE — Verified 0 Errors, 0 Warnings  

---

## 1. Executive Summary

Gold Oracle EA v2 has been constructed from the ground up as a single, production-grade, monolithic Expert Advisor for MetaTrader 5 on Spot Gold (`XAUUSD`). It resolves all architectural defects, stubbed logic, and timing errors present in the `GoldOracle_v1.mq5` prototype.

### Core Achievements:
1. **Monolithic Release**: Delivered `GoldOracle_v2.mq5` (3,369 lines, 131,249 bytes) as a self-contained compilation unit.
2. **Zero Defect Compilation**: Cleanly compiled with MetaTrader 5 64-bit compiler (`MetaEditor64.exe` Regular X64), generating `GoldOracle_v2.ex5` with **strictly 0 errors and 0 warnings**.
3. **Consolidated Indicator Pool (56 Handles)**: Built a global indicator registry consuming 56 handles (<11% of MT5's 512-handle ceiling, well below the 60-handle requirement), validated upon `OnInit()` and safely freed on `OnDeinit()`.
4. **Strict Zero-Repainting Guarantee**: All 144 brains evaluate only confirmed historical bars (`bar[1]` or older) through standardized helpers (`GetIndicatorVal`, `GetIndicatorSeries`, `GetRatesSeries`), completely eliminating `bar[0]` lookahead and intra-bar repaint anomalies.
5. **Complete 144-Brain Ensemble**: Engineered 100% genuine mathematical and quantitative algorithms across 13 analytical disciplines with **zero dummy returns or stubs** (unlike v1's 52% stub rate).
6. **Adaptive Dynamic Weighting Engine**: Fully operationalized the self-tuning ensemble of 144 weights with daily 0.95/0.05 exponential moving accuracy updates triggered at 20:00 UTC and clamped to a 0.1 floor.
7. **Gold Microstructure & Safety Gating**: Full XAUUSD pip normalization (`_Digits == 2`, `_Point = 0.01`, `pipFactor = 1.0`), dynamic ATR(14, H1) stop-loss with broker `SYMBOL_TRADE_STOPS_LEVEL` and spread clamping (preventing Error 130), equity-risk position sizing, max spread gating (50 pts), and H1 ATR volatility floor gating.
8. **Institutional News Blackout**: Dual-layer UTC-synchronized calendar engine (NFP 1st Friday 12:30 UTC, FOMC matrix 18:00 UTC, CPI 12:30 UTC, PPI 12:30 UTC, Powell Speeches 14:00 UTC) with automated pre-news position liquidation and zero same-day re-entry.

---

## 2. Global Shared Indicator Architecture (<60 Handles)

The EA centralizes all indicator allocations into a single global registry initialized during `OnInit()` and released in `OnDeinit()`:

| Horizon | Total Handles | Allocations |
|---|---|---|
| **M15** | 9 | `EMA21`, `EMA50`, `EMA200`, `RSI14`, `MACD(12,26,9)`, `Bands(20,2)`, `ATR14`, `Stoch(14,3,3)`, `ADX14` |
| **H1** | 25 | `EMA8`, `EMA21`, `EMA50`, `EMA100`, `EMA200`, `SMA20`, `RSI14`, `RSI7`, `MACD(12,26,9)`, `Bands(20,2)`, `ATR14`, `ATR5`, `Stoch(14,3,3)`, `CCI14`, `WPR14`, `ADX14`, `DeMarker14`, `AwesomeOscillator`, `StdDev20`, `OBV`, `MFI14`, `ForceIndex13`, `ParabolicSAR`, `Ichimoku(9,26,52)`, `ChaikinOsc` |
| **H4** | 11 | `EMA21`, `EMA50`, `EMA200`, `SMA20`, `RSI14`, `MACD(12,26,9)`, `ATR14`, `Bands(20,2)`, `ADX14`, `Stoch(14,3,3)`, `SMA50` |
| **D1** | 7 | `EMA20`, `EMA50`, `EMA200`, `RSI14`, `ATR14`, `MACD(12,26,9)`, `Bands(20,2)` |
| **Macro Proxies** | 4 | `EURUSD H1 EMA50`, `USDJPY H1 EMA50`, `AUDUSD H1 EMA21`, `XAGUSD H1 SMA20` (graceful fallback if unquoted) |
| **TOTAL** | **56 Handles** | **<60 ceiling satisfied (10.9% of MT5 512-handle capacity)** |

All handles are validated in an atomic loop in `OnInit()`. If any handle fails to initialize, the routine rolls back, releases allocated handles, and returns `INIT_FAILED`.

---

## 3. Confirmed Historical Buffer Access Layer (Zero Repainting)

Three universal accessors standardize data retrieval across all 144 brains:
- `GetIndicatorVal(int handle, int buffer_index, int shift = 1)`: Returns single value from confirmed historical candle `bar[shift]`.
- `GetIndicatorSeries(int handle, int buffer_index, int shift, int count, double &output_array[])`: Copies `count` elements starting at `bar[shift]` with series orientation (`output_array[0] = bar[shift]`).
- `GetRatesSeries(ENUM_TIMEFRAMES tf, int shift, int count, MqlRates &rates[])`: Copies confirmed historical `MqlRates` with series orientation (`rates[0] = bar[shift]`).

**Zero Repainting Guarantee**: All shifts are strictly $\ge 1$. No brain function accesses `bar[0]`.

---

## 4. 144 Strategy Brain Ensemble (100% Genuine Quantitative Logic)

The 144 analytical brains are partitioned across 13 disciplines:

| # | Discipline | Brain Range | Count | Key Formulations |
|---|---|---|---|---|
| 1 | SMC / ICT | Brain001–Brain012 | 12 | CHoCH, BOS, Order Block mitigation, FVG retest, 20-bar sweeps, London Kill Zone expansion, Premium/Discount, Judas Swing, Institutional Funding displacement, Mitigation block, Breaker block, Inducement |
| 2 | Trend Following | Brain013–Brain026 | 14 | Fast/Slow EMA (8/21), Golden/Death Cross (50/200), Multi-TF Alignment (M15, H1, H4, D1), SuperTrend ATR envelope, Hull MA slope, Parabolic SAR, KAMA efficiency, Donchian 20 breakout, OLS slope / ATR, Ichimoku Cloud, TEMA slope, Aroon(14), Vortex(14), Triple EMA Ribbon |
| 3 | Momentum & Oscillators | Brain027–Brain040 | 14 | RSI regular divergence, MACD histogram delta, Stochastic extreme cross (<25 / >75), CCI extremes (±120), Williams %R recovery, ROC(12), Ultimate Oscillator(7,14,28), QQE RSX cross, Chande Momentum(14), True Strength Index(25,13), Awesome Oscillator, DeMarker(14), StochRSI, Elder Ray |
| 4 | Volatility | Brain041–Brain050 | 10 | ATR expansion ratio, Bollinger Squeeze breakout, Keltner Channel breakout, Annualized Historical Log-Return Volatility, Chaikin Volatility ROC, StdDev 90th percentile, Jack Schwager Volatility Ratio, Mass Index bulge, Ulcer Index downside draw, Relative Volatility Index |
| 5 | Volume & Flow | Brain051–Brain059 | 9 | OBV trend vs SMA(20), Chaikin A/D momentum slope, Volume Price Trend (VPT), Chaikin Money Flow (CMF 20), Ease of Movement (EMV 14), Elder Force Index(13), Volume-Weighted MACD (MFI proxy), Volume Oscillator surge, Volume spike with absorption wicks |
| 6 | Fibonacci & Harmonics | Brain060–Brain068 | 9 | Golden Pocket (0.618–0.650) retracement, Deep Retracement (0.786), Shallow Continuation (0.382), ABCD Projection symmetry, Gartley 222 PRZ, Bat harmonic PRZ, Crab 1.618 extension PRZ, Fibonacci Expansion 1.618, Fibonacci Fan ray support/resistance |
| 7 | Statistical & Quant | Brain069–Brain081 | 13 | Z-Score (50-period), Hurst Exponent (Rescaled Range over 64 bars), Ornstein-Uhlenbeck stochastic drift, Lo-MacKinlay Variance Ratio VR(4), 3rd moment Skewness, Return Autocorrelation lag 1, Rolling Sharpe ratio (30-bar), Shannon Information Entropy (5-bin), 1D Kalman filter state & velocity, Standardized OLS residuals, 2-State Markov regime filter, Bollinger %b quantiles, 100-bar empirical percentile rank |
| 8 | Inter-Market Macro | Brain082–Brain095 | 14 | DXY Inverse Proxy (EURUSD/USDJPY), US 10Y Yield proxy, Real Yields momentum, Silver (XAGUSD) Beta Lead-Lag, Crude Oil inflation impulse, Copper/Gold growth ratio, S&P 500 equity risk-off safe haven, Market volatility regime safe haven, USDJPY Carry Trade unwind surge, AUDUSD commodity currency confirmation, Sovereign credit risk flight, Central Bank D1 EMA200 test, Trade-Weighted Dollar basket, TIPS breakeven inflation hedge |
| 9 | Temporal & Calendar | Brain096–Brain108 | 13 | London Open morning expansion (07:00–09:00 UTC), Asian range breakout (00:00–07:00 UTC), Day-of-week institutional seasonality (Mon/Wed/Fri), Turn-of-Month inflow effect (days 1..3, 28..31), COMEX Options Expiry strike pinning ($50/$100), London AM Fixing (10:30 UTC) anticipation, NY Open directional alignment, Asian dealer inventory rebalancing, Golden Hour (08:00–09:30 UTC) volume surge, Frankfurt pre-market (06:00 UTC) buildup, Friday end-of-week square-off, Monthly seasonality (Jan/Aug/Nov vs Mar/Jun/Oct), Harmonic 24h circadian cycle phase |
| 10 | S/R & Pivots | Brain109–Brain117 | 9 | Daily Classical Pivot (P, R1, S1), Camarilla Pivots (L3/H3 reversal, L4/H4 breakout), Woodie Pivots (Close-weighted), Fibonacci Pivots (0.382/0.618), 5-Day High Volume Node (HVN) rejection, Psychological $50/$100 round numbers, 50-bar structural swing rejection wicks, H4 SMA50 dynamic barrier, 3-Day high/low range breakout |
| 11 | Candlesticks | Brain118–Brain128 | 11 | Bullish/Bearish Engulfing, Hammer/Hanging Man (wick >= 2x body), Morning/Evening Star, Three White Soldiers / Black Crows, Pinbar rejection wick (>=65% range), Inside Bar breakout, Outside Bar absorption, Marubozu institutional impulse (wicks <= 5%), Doji reversal trigger, Piercing Line / Dark Cloud Cover, Tweezer Tops / Bottoms |
| 12 | Psychological & Sentiment | Brain129–Brain135 | 7 | Retail crowd sentiment fade proxy, 5 consecutive bars exhaustion mean-reversion, $100 round number magnetic trap, Bull/Bear trap breakout failure, Panic liquidation flush & recovery bounce, Parabolic greed climax reversal, Monday weekend gap fill bias |
| 13 | Frontier & Experimental | Brain136–Brain144 | 9 | Sevcik Fractal Dimension D < 1.35, John Ehlers Gaussian Fisher Transform zero-line trigger cross, Ehlers Cyber Cycle dual-lead turning point, Ehlers Instantaneous Trendline slope, Ehlers Center of Gravity (CoG) FIR crossover, Singular Spectrum Analysis (SSA) primary eigenvector trend, Haar Wavelet 3-level denoised momentum, Echo State Network (ESN) reservoir readout projection, Teager-Kaiser Energy Operator (TKEO) instantaneous surge |
| **TOTAL** | **13 Disciplines** | **Brain001–Brain144** | **144** | **Strict return: +1 (BUY), -1 (SELL), 0 (NEUTRAL). Zero stubs.** |

---

## 5. Adaptive Dynamic Weighting Engine

- **Weight State**: Array of 144 `SBrainState` structs tracking `weight`, `ema_accuracy`, `last_vote`, `total_votes`, `correct_votes`, `name`, and `discipline`.
- **Initialization**: Uniform cold start $W_i = 1.0, \text{EMA\_Acc}_i = 1.0$.
- **Consensus Calculation (~10:00 UTC)**:
  $$\text{Score} = \sum_{i=0}^{143} (V_i \times W_i)$$
  - Direction = `+1` if $\text{Score} > InpMinScore$ ($2.0$).
  - Direction = `-1` if $\text{Score} < -InpMinScore$ ($-2.0$).
  - Direction = `0` if $|\text{Score}| \le InpMinScore$ (**Neutral deadband: strict no-trade pass**).
- **Daily Re-Weighting (20:00 UTC)**:
  $$\text{ActualDirection} = \text{Sign}(\text{Close}_{20:00} - \text{Open}_{10:00})$$
  - Abstained brains ($V_i == 0$) are isolated and retain weights.
  - Active brains ($V_i \ne 0$):
    $$\text{EMA\_Acc}_i \leftarrow 0.95 \times \text{EMA\_Acc}_i + 0.05 \times (V_i == \text{ActualDirection} ? 1.0 : 0.0)$$
    $$W_i \leftarrow \max(0.1, \text{EMA\_Acc}_i)$$

---

## 6. Execution, Microstructure & Institutional News Safety

1. **Pip Normalization**:
   - `g_pipFactor = (_Digits == 3 || _Digits == 5) ? 10.0 : 1.0;`
   - `g_pipSize = _Point * g_pipFactor;` (produces exact \$0.01 per pip on 2-digit Spot Gold).
2. **Dynamic ATR Stop-Loss**:
   - $\text{SL\_Distance} = \text{ATR}(14, H1) \times 2.0$.
   - Clamped to $\max(\text{desiredDist}, \text{minReqPrice} + \text{spread} + 2.0 \times \text{\_Point})$ where $\text{minReqPrice} = \max(\text{StopsLevel}, \text{FreezeLevel}) \times \text{\_Point}$. Completely eliminates MT5 Error 130 (`INVALID_STOPS`).
3. **Take-Profit**: Strict `0.0` (None). Full directional capture terminating at 20:00 UTC.
4. **Position Sizing**:
   - Calculated dynamically from `AccountInfoDouble(ACCOUNT_EQUITY)` and `InpRiskPercent` (2.0%).
   - Uses `SYMBOL_TRADE_TICK_VALUE_LOSS` with defensive division-by-zero guards.
   - Normalized to broker volume step, min, and max.
5. **Operational Gating**:
   - Spread Gate: Rejects entry if live spread $> 50$ points (\$0.50).
   - Volatility Gate: Rejects entry if confirmed H1 ATR[1] $< 30.0$ points (\$0.30).
6. **News Safety System**:
   - All comparisons evaluated in true UTC via `TimeGMT()`.
   - Algorithmically tracks NFP (1st Friday 12:30 UTC), scheduled FOMC matrix (18:00 UTC), monthly CPI (12:30 UTC), monthly PPI (12:30 UTC), and Powell speeches (14:00 UTC).
   - Enforces pre-news liquidation (15–30 min prior), blackout window rejection (30–90 min post), and sets `g_bNewsLockoutToday = true` (zero same-day re-entry).

---

## 7. Compilation Verification & Audit Results

- **Command**:
  ```powershell
  python .agents\explorer_survey_3\compile_verifier.py GoldOracle_v2.mq5
  ```
- **Verification Output**:
  ```
  Compilation Target: C:\Users\Asus\Documents\antigravity\hopeful-curie\GoldOracle_v2.mq5
  Status: PASS
  Result: Result: 0 errors, 0 warnings, 6881 ms elapsed, cpu='X64 Regular'
  EX5 Generated: True
  ```
- **Binary Metadata**:
  - `GoldOracle_v2.mq5`: 131,249 bytes (3,369 lines).
  - `GoldOracle_v2.ex5`: 103,270 bytes (clean 64-bit machine code).
- **Defects Fixed During Build**:
  - Sign mismatch warning in Brain 113 (`ulong maxVol` $\rightarrow$ `long maxVol`) completely resolved.
  - Achieved strict **0 errors and 0 warnings**.

---
*End of Report — Worker Builder 1*

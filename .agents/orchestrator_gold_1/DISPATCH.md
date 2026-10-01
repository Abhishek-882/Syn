# DISPATCH — Orchestrator Gold 1

## Mission
Build and rigorously verify **Gold Oracle EA v2** (`GoldOracle_v2.mq5`), a multi-strategy daily directional Spot Gold (XAUUSD) Expert Advisor for MetaTrader 5 powered by a consensus ensemble of 144 independent analytical brain functions with self-learning adaptive weights.

## Working Directory & Metadata
- Orchestrator Working Directory: `c:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\orchestrator_gold_1`
- Target Artifact: `c:\Users\Asus\Documents\antigravity\hopeful-curie\GoldOracle_v2.mq5`
- Reference Prototype: `c:\Users\Asus\Documents\antigravity\hopeful-curie\GoldOracle_v1.mq5`
- Verbatim User Request: `c:\Users\Asus\Documents\antigravity\hopeful-curie\ORIGINAL_REQUEST.md`

## Key Specifications & Architecture Requirements

### R1. Complete 144 Strategy Brain Ensemble
The system must implement 144 independent, pure, non-repainting predictive brain functions (`Brain001` through `Brain144`) returning strictly `+1`, `-1`, or `0`, evaluated on confirmed historical bars (`bar[1]` or earlier, never `bar[0]`).
- **13 Disciplines Breakdown:**
  1. SMC / ICT (12 brains): CHoCH, BOS, Order Blocks, FVGs, Liquidity Sweeps, Kill Zones, Premium/Discount, Judas Swings, Institutional Funding, Mitigations, Breaker Blocks, Inducements.
  2. Trend Following (15 brains): Fast/Slow EMAs, EMA 50/200 Golden Cross, Multi-timeframe trend alignment (M15/H1/H4/D1), SuperTrend, Hull MA, Parabolic SAR, KAMA, Donchian channels, Linear regression slopes, Ichimoku Kinko Hyo, TEMA, Aroon, Vortex, Trend Exhaustion, Triple EMA.
  3. Momentum & Oscillators (16 brains): RSI divergence, MACD histogram momentum, Stochastic crossovers, CCI extremes, Williams %R, ROC, Ultimate Oscillator, QQE signal, Chande Momentum, TSI, Awesome Oscillator, DeMarker, CMO, StochRSI, Money Flow Oscillator, Elder Ray.
  4. Volatility (11 brains): ATR expansion/contraction, Bollinger Band squeeze & breakout, Keltner Channel breakouts, Historical Volatility bands, Chaikin Volatility, Standard Deviation extremes, Volatility ratio, Mass Index, Ulcer Index, Average True Range channels, Relative Volatility Index.
  5. Volume & Flow (10 brains): On-Balance Volume (OBV) trend, Tick volume accumulation, Volume Price Trend (VPT), Chaikin Money Flow (CMF), Ease of Movement, Force Index, Volume Weighted MACD, Negative/Positive Volume Index, Volume oscillator, Volume spike exhaustion.
  6. Fibonacci & Harmonics (10 brains): Golden pocket (0.618-0.65) retracement, 0.786 deep retracement, 0.382 shallow continuation, ABCD harmonic projections, Gartley pattern detection, Bat pattern bias, Crab extension, Fibonacci expansion levels, Fan angles, Time zone intervals.
  7. Statistical & Quant (15 brains): Z-score of price vs mean, Hurst exponent persistence/mean-reversion, Ornstein-Uhlenbeck drift, Variance ratio test, Skewness & Kurtosis tail risk, Autocorrelation lag 1, Rolling Sharpe momentum, Shannon entropy, Kalman filter tracking, Cointegration proxy, Quantile regression bias, Standardized residuals, Markov state switching proxy, Bollinger %b quantiles, Empirical distribution percentiles.
  8. Inter-Market Macro (16 brains): DXY inverse correlation proxy, US 10Y Treasury yield inverse proxy, Real yields proxy, Silver (XAGUSD) beta lead-lag proxy, Crude Oil inflation proxy, Copper growth proxy, SP500 risk-on/risk-off sentiment, VIX volatility regime proxy, USDJPY FX liquidity proxy, AUDUSD commodity currency proxy, Emerging market currency stress, Central bank gold purchasing impulse, Trade-weighted USD momentum, TIPS breakeven inflation proxy, Commodity index momentum, Sovereign credit risk proxy.
  9. Temporal & Calendar (15 brains): London morning open expansion (07:00-10:00 UTC), Asia high/low range breakout, Day of week seasonality (Monday bias, Friday liquidation bias), Turn-of-month effect, Triple witching / options expiry proxy, London fixing (15:00 UTC) anticipation, New York open crossover (13:30 UTC), Overnight inventory rebalancing, Golden hour institutional flow, Pre-market London buildup, End-of-week positioning, Holiday liquidity drain, Monthly seasonality bias, Quarter-end rebalancing, Intraday cycle phase.
  10. Support/Resistance & Pivots (10 brains): Daily classical pivot points (P, R1, S1), Camarilla pivot levels (H3/H4, L3/L4), Woodie pivot bias, Fibonacci pivot levels, High-volume node (HVN) S/R, Round psychological numbers ($10, $50, $100 levels), Swing high/low structural rejection, Dynamic moving average S/R, Multi-day range extremes, Opening range high/low test.
  11. Candlesticks (12 brains): Bullish/Bearish Engulfing, Hammer / Hanging Man, Morning / Evening Star, Three White Soldiers / Black Crows, Pinbar / Rejection Wick, Inside Bar breakout, Outside Bar absorption, Marubozu momentum impulse, Doji reversal trigger, Piercing Line / Dark Cloud Cover, Tweezer tops/bottoms, Three Line Strike.
  12. Psychological & Sentiment (8 brains): Retail trader positioning sentiment proxy (fade extreme one-sided crowd), Consecutive bull/bear bars exhaustion, Round number magnetic trap, Trap breakout failure, Panic liquidation bounce, Greed expansion climax, Climax volume absorption, Weekend gap fill expectation.
  13. Frontier & Experimental (10 brains): Fractal dimension indicator, Ehlers Fisher Transform, Cyber Cycle phase indicator, Instantaneous Trendline, Center of Gravity oscillator, Singular Spectrum Analysis proxy, Wavelet transform decomposition proxy, Echo state network proxy, Algorithmic order flow imbalance proxy, Nonlinear energy operator.
- **Shared Indicator Architecture:** All standard indicator handles must be initialized once globally during `OnInit()` and released in `OnDeinit()`. Total handle count must remain under 60 handles (<12% of MT5 512-handle limit). Multiple brains must share the same indicator buffers across timeframes (M15, H1, H4, D1).

### R2. Adaptive Dynamic Weighting Engine
Each strategy brain possesses an adaptive weight $W_i \in [0.1, 1.0]$ initialized at 1.0 (cold start).
Following each trading day at 20:00 UTC:
- The actual daily market vector is evaluated: $\text{Sign}(\text{Close}_{20:00} - \text{Open}_{10:00})$.
- For every brain that cast a non-zero vote:
  $$\text{EMA\_Acc}_i \leftarrow 0.95 \times \text{EMA\_Acc}_i + 0.05 \times (\text{Vote}_i == \text{ActualDirection} ? 1.0 : 0.0)$$
  $$W_i \leftarrow \max(0.1, \text{EMA\_Acc}_i)$$
- Weights dynamically self-tune over a 30-day half-life, amplifying high-accuracy brains while suppressing deteriorating strategies without hard-deleting them.

### R3. Gold Microstructure & Execution Infrastructure
- **Pip Normalization:** Account for XAUUSD digit conventions (`_Digits == 2`, `_Point = 0.01`, `pipFactor = 1.0`). Never hardcode 0.0001 forex multipliers.
- **Dynamic ATR Stop-Loss:** Calculated as $\text{ATR}(14, H1) \times 2.0$, clamped to broker `SYMBOL_TRADE_STOPS_LEVEL`.
- **Take-Profit:** None. Full directional capture terminating at 20:00 UTC.
- **Position Sizing:** Risk-based percentage of account equity (input parameter `InpRiskPercent`, default 2.0%) normalized to `SYMBOL_VOLUME_MIN`, `SYMBOL_VOLUME_MAX`, and `SYMBOL_VOLUME_STEP`.
- **Spread & Volatility Gating:** Blocks entries if spread exceeds threshold (50 points) or if market is frozen (H1 ATR < minimum threshold).

### R4. Institutional News Blackout & Safety System
- Hardcoded institutional calendar tracking NFP (first Friday 12:30 UTC), CPI (12:30 UTC), FOMC (Wednesday 18:00 UTC), PPI, and Fed Chair speeches.
- Enforces an automated pre-news closure window (15–30 min prior) and blackout window (30–90 min post).
- Immediate liquidation of open positions upon entering a blackout window with strict zero re-entry enforcement for the day.

### R5. Monolithic Architecture & Zero-Defect Compilation
- Delivered as a single, fully integrated, production-grade MetaTrader 5 Expert Advisor (`GoldOracle_v2.mq5`).
- Strictly zero errors, zero warnings on MetaEditor compilation.

## MetaEditor Compilation Tool
Execute compilation via:
```powershell
Start-Process -FilePath "C:\Program Files\MetaTrader 5\MetaEditor64.exe" -ArgumentList '/compile:"c:\Users\Asus\Documents\antigravity\hopeful-curie\GoldOracle_v2.mq5" /log:"c:\Users\Asus\Documents\antigravity\hopeful-curie\scratch\compile.log"' -Wait -NoNewWindow
```
Read log with Python (`encoding='utf-16'`). Verify 0 errors, 0 warnings!

## Skills Available in System
- `production-mql-engineering`
- `gold-xauusd-specialist`
- `smc-ict-trading`
- `indicator-algorithms`
- `trailing-stop-systems`
- `large-ea-architecture`
- `cognitive-ea-forensics`
- `ea-backtest-forensics`

## Instructions
1. Decompose the implementation into structured subtasks across specialized workers.
2. Maintain `plan.md` and `progress.md` in `.agents/orchestrator_gold_1/`.
3. Verify all 144 brains, compilation, consensus logic, weight engine, and news blackout.
4. Report completion when fully verified with zero defects.

## 2026-10-01T13:01:12Z - User Request
You are the Project Orchestrator for Gold Oracle EA v2.
Working directory: c:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\orchestrator_gold_1
Target EA: c:\Users\Asus\Documents\antigravity\hopeful-curie\GoldOracle_v2.mq5
Authoritative request: c:\Users\Asus\Documents\antigravity\hopeful-curie\ORIGINAL_REQUEST.md
Full dispatch instructions: c:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\orchestrator_gold_1\DISPATCH.md
Reference prototype: c:\Users\Asus\Documents\antigravity\hopeful-curie\GoldOracle_v1.mq5

Your mission:
Lead the team of specialized subagents to construct and rigorously verify the monolithic Gold Oracle EA v2 (GoldOracle_v2.mq5) with:
1. Complete 144 strategy brains across 13 analytical disciplines returning strictly +1, -1, or 0, with zero repainting (strictly bar[1] or earlier).
2. Shared indicator architecture (<60 handles globally initialized in OnInit and released in OnDeinit).
3. Adaptive dynamic weighting engine (EMA accuracy 0.95/0.05, W in [0.1, 1.0]).
4. Gold microstructure & execution infrastructure (pip normalization for XAUUSD, ATR SL, equity % position sizing, spread/volatility gating).
5. Institutional news blackout & safety system (NFP, CPI, FOMC, PPI, Powell speeches, zero re-entry).
6. Zero errors, zero warnings on MetaEditor compilation (MetaEditor64.exe).
7. Rigorous verification across all acceptance criteria.

Maintain plan.md and progress.md in your working directory. Keep steady progress, update progress.md frequently, and send message when ready for victory audit.

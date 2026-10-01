# Gold Oracle EA — CSO Strategy Charter & Quality Gate System
**Document ID**: CSO-CHARTER-2026-V1  
**Author**: E01 — Chief Strategy Officer (CSO)  
**Target System**: Gold Oracle EA v2 (XAUUSD Daily Directional Multi-Brain Engine)  
**Pipeline Wave**: Wave 0 Foundation & Wave 1 Handoff  
**Status**: APPROVED & OPERATIONAL  

---

## 1. Executive Mandate & Strategic Vision

The Gold Oracle EA is an institutional-grade, multi-agent algorithmic system operating on **XAUUSD (Gold)**. The system is engineered around a single, uncompromising daily objective:

> **"Predict by 10:00 UTC whether Gold will close HIGHER (+1) or LOWER (-1) at 20:00 UTC."**

As Chief Strategy Officer (CSO), my mandate is to govern the strategy architecture, enforce rigorous quality gates, eliminate curve-fitting, guarantee dimensional market coverage across 144 independent strategy brains, and establish strict prioritization for strategy research, reasoning, and engineering.

### Core Strategic Axioms
1. **Purity of Voting**: Every brain function outputs strictly `+1` (Bullish), `-1` (Bearish), or `0` (Neutral/No Opinion). No brain executes trades, calculates lot sizes, or manages stops.
2. **Temporal Alignment**: All inputs, indicators, and price actions analyzed must be strictly finalized before 10:00 UTC on the day of entry. Zero look-ahead bias is tolerated.
3. **Confirmed Bar Rule**: No indicator or price structure calculation may query bar `0` (the active forming candle). All logic must reference bar `1` (last closed bar) or older to guarantee 100% non-repainting signals.
4. **Adaptive Meritocracy**: Brains do not have fixed dogma; they are dynamically weighted via exponential moving average (EMA) accuracy tracking. Weak or regime-degraded brains are automatically down-weighted towards a 0.10 floor, while regime-aligned brains scale towards 1.0.
5. **Robustness Over Complexity**: If a strategy cannot be defended on first principles of market microstructure, institutional order flow, or macroeconomic mechanics, it is rejected regardless of backtest performance.

---

## 2. Review & Audit of the 144 Strategy Universe

The Gold Oracle universe encompasses **144 independent strategies categorized across 13 distinct market dimensions (A01 to M10)**. Below is the formal CSO strategic audit for each category:

### Category A: Smart Money Concepts / ICT (12 Strategies — A01 to A12)
*Focus: Institutional order flow footprints, structural breaks, and liquidity engineering.*
- **A01: CHoCH Detector** — H1 Change of Character during London session (07:00–10:00 UTC). Identifies structural pivot failures signaling intraday trend shifts.
- **A02: BOS Continuation** — H1 Break of Structure in the direction of the higher-timeframe trend. Captures momentum continuation.
- **A03: Order Block Demand** — Unmitigated bullish OB on H1/H4 formed before impulse. Serves as institutional buying support.
- **A04: Order Block Supply** — Unmitigated bearish OB on H1/H4 formed before downward impulse. Acts as institutional sell wall.
- **A05: Fair Value Gap (FVG) Imbalance** — 3-bar displacement gap (`Low[i-1] > High[i+1]` or vice versa). Evaluates price seeking liquidity to balance inefficiency.
- **A06: Asian Range Liquidity Sweep** — London price grabs liquidity beyond Asian High (00:00–07:00 UTC) and closes back inside (Bearish sweep) or below Asian Low (Bullish sweep).
- **A07: Premium / Discount Equilibrium** — Position of price relative to the 50% midpoint of the previous 5-day / D1 swing range. Discount (<50%) favors longs; Premium (>50%) favors shorts.
- **A08: Equal Highs / Lows Magnet (EQH/EQL)** — Clusters of double/triple equal highs or lows within 50 points, acting as liquidity pools attracting price.
- **A09: Market Structure Shift (MSS)** — Liquidity sweep immediately followed by an aggressive displacement CHoCH on H1. High-conviction reversal signal.
- **A10: Optimal Trade Entry (OTE)** — Fibonacci 62%–79% retracement of the dominant H4 impulse leg.
- **A11: Breaker Block Transition** — Violated Order Block flipping from demand to supply (bearish breaker) or supply to demand (bullish breaker).
- **A12: Wyckoff Phase Classification** — Structural Spring / Upthrust after Distribution (UTAD) on D1/H4 swing ranges.

### Category B: Trend Following (15 Strategies — B01 to B15)
*Focus: Macro and intermediate drift direction, moving average channels, and momentum continuation.*
- **B01: EMA Golden / Death Cross** — H4 EMA 50 vs EMA 200 orientation. The primary macro baseline.
- **B02: EMA Ribbon Alignment** — 6-EMA ribbon (8, 13, 21, 34, 55, 89) on H1. Unanimous bullish stack = +1; bearish stack = -1; tangled = 0.
- **B03: Ichimoku Kumo Cloud** — H4 price relative to Senkou Span A and B. Above cloud = +1; below cloud = -1; inside cloud = 0.
- **B04: Ichimoku TK Cross** — H4 Tenkan-sen (9) crossed above/below Kijun-sen (26).
- **B05: Supertrend Direction** — H4 Supertrend (ATR 10, Multiplier 3.0). Discrete trend regime tracker.
- **B06: Parabolic SAR** — H4 SAR dot position relative to price.
- **B07: ADX Directional Index** — H4 ADX(14) > 25 threshold confirming trend strength with +DI / -DI dominance.
- **B08: Aroon Oscillator** — Aroon(25) on H4. Aroon Up > 70 with Aroon Down < 30 = Bullish; inverse = Bearish.
- **B09: NRTR Trend State** — Nick Rypock Trailing Reverse algorithm (ATR-based dynamic support/resistance step filter).
- **B10: Donchian Channel Breakout** — 20-period H4 high/low band breakout state.
- **B11: Keltner Channel Envelope** — H4 Close relative to EMA(20) +/- 2.0*ATR(10) channels.
- **B12: Linear Regression Slope** — 50-bar Linear Regression line slope on H4.
- **B13: Heikin-Ashi Sequence** — 3 consecutive confirmed bullish/bearish Heikin-Ashi candles on H4.
- **B14: Hull Moving Average (HMA)** — HMA(20) on H4 first-derivative slope (low-lag trend filter).
- **B15: Kaufman Adaptive MA (KAMA)** — KAMA(10, 2, 30) slope on H4, adapting to market noise ratio.

### Category C: Momentum & Oscillators (16 Strategies — C01 to C16)
*Focus: Velocity of price displacement, cyclical overextension, and momentum divergence.*
- **C01: RSI Trend Bias** — H4 RSI(14) above/below 50 centerline.
- **C02: RSI Swing Divergence** — Classic regular divergence between H4 Price pivots and RSI(14) pivots.
- **C03: MACD Histogram Acceleration** — H4 MACD (12, 26, 9) histogram slope: positive and expanding = +1; negative and contracting = -1.
- **C04: MACD Signal Line Cross** — H4 MACD main line vs signal line crossover state.
- **C05: Stochastic Reversal** — Stoch(14, 3, 3) on H4 crossing upward from oversold (<20) or downward from overbought (>80).
- **C06: CCI Extremes** — Commodity Channel Index CCI(20) on H4 crossing from beyond +/-100 boundaries.
- **C07: Williams %R** — %R(14) on H4 exiting deep overbought (-20) or oversold (-80) levels.
- **C08: Money Flow Index (MFI)** — Volume-weighted RSI MFI(14) on H4 relative to 50 midpoint and trajectory.
- **C09: Quantitative Qualitative Estimation (QQE)** — Full 6-step RSX smoothing with dynamic ATR trailing bands (non-TEMA).
- **C10: Tom DeMark Range Expansion Index (TD REI)** — DeMark 8-bar arithmetic oscillator detecting true exhaustion.
- **C11: Rate of Change (ROC)** — ROC(12) on H4 crossing zero line.
- **C12: Awesome Oscillator (AO)** — Bill Williams AO (SMA 5 vs SMA 34) zero-line cross and saucer patterns.
- **C13: Elder Ray Bulls / Bears Power** — 13-period EMA with Bull Power (High - EMA) and Bear Power (Low - EMA) balance.
- **C14: RSI-EMA Crossover** — RSI(14) crossing above/below its own 9-period EMA signal line.
- **C15: Momentum Indicator Slope** — 10-period standard Momentum on H4 slope and level.
- **C16: Triple RSI Multi-Timeframe Confluence** — H1, H4, and D1 RSI(14) all simultaneously agreeing (>50 for Buy, <50 for Sell).

### Category D: Volatility Analysis (11 Strategies — D01 to D11)
*Focus: Band compression, expansion dynamics, and volatility regime classification.*
- **D01: Bollinger Bands Position** — H4 Close relative to BB(20, 2.0) centerline and outer bands.
- **D02: BB Squeeze Breakout (John Carter TTM Squeeze)** — BB(20, 2.0) inside Keltner(20, 1.5*ATR) indicating energy buildup, voting on breakout direction.
- **D03: ATR Expansion Impulse** — ATR(14) on H1 expanding above its 20-period SMA in conjunction with London impulse direction.
- **D04: ATR VOL MACD** — Moving average convergence divergence applied directly to ATR timeseries.
- **D05: Chaikin Volatility** — Rate of change of the High-Low spread over 10 periods.
- **D06: ATR Channel Position** — Price position across multi-tiered ATR bands (1x, 2x, 3x ATR).
- **D07: BB Width Percentile** — Relative band width ranking over 100 bars (volatility regime classification).
- **D08: ADR Utilization Ratio** — Session range at 10:00 UTC divided by 14-day Average Daily Range (ADR). Identifies expansion headroom.
- **D09: Volatility Regime Classifier** — H4 ATR(14) above/below its 50-period SMA (trending vs mean-reverting environment).
- **D10: Standard Deviation Velocity** — Rate of change of 20-period price standard deviation.
- **D11: Keltner-BB Overlap State** — Multi-band structural envelope state.

### Category E: Volume Analysis (10 Strategies — E01 to E10)
*Focus: Tick volume dynamics, accumulation/distribution, and volume-price divergences.*
- **E01: On-Balance Volume (OBV) Trend** — H4 OBV swing high/low structure.
- **E02: Volume-Price Trend (VPT)** — VPT slope and zero-line cross on H4.
- **E03: Accumulation / Distribution (A/D)** — Chaikin A/D line directional slope on H4.
- **E04: Chaikin Money Flow (CMF)** — CMF(20) on H4 (>0 indicates net buying volume).
- **E05: Elder Force Index** — Force Index(13) on H4 smoothed by 13-period EMA.
- **E06: Tick Volume Divergence** — Price making higher swing highs on H1 while tick volume makes lower highs.
- **E07: Volume Climax Exhaustion** — Volume spike > 2.5x 20-SMA with long rejection wick during London session.
- **E08: Ease of Movement (EMV)** — EMV(14) on H4 quantifying price movement efficiency per volume unit.
- **E09: Volume Oscillator** — Fast tick volume MA (5) vs Slow tick volume MA (20) spread.
- **E10: Session Volume Ratio** — London morning tick volume (07:00–10:00 UTC) vs Asian volume (00:00–07:00 UTC) ratio.

### Category F: Fibonacci & Harmonic Patterns (10 Strategies — F01 to F10)
*Focus: Structural retracement ratios, geometric price symmetry, and harmonic completion zones.*
- **F01: Fibonacci Retracement Bounce** — Price reaction at 50.0% / 61.8% golden ratios of the prior D1/H4 impulse leg.
- **F02: Fibonacci Extension Target Magnet** — 127.2% and 161.8% expansion targets acting as price attractors.
- **F03: Fibonacci Daily Pivots** — Pivot calculations utilizing 0.382, 0.618, and 1.000 Fibonacci range multipliers.
- **F04: Fibonacci Moving Average Channels** — Moving average envelope bands displaced by Fibonacci percentages of ATR.
- **F05: Harmonic Gartley Pattern** — Geometric M/W pattern with 0.618 B-point and 0.786 D-point completion.
- **F06: Harmonic Butterfly Pattern** — Extended pattern with 0.786 B-point and 1.272 D-point extension.
- **F07: Harmonic Bat Pattern** — 0.382/0.500 B-point and 0.886 D-point PRZ (Potential Reversal Zone).
- **F08: AB=CD Measured Move** — Equality of impulse legs (CD length and time matching AB).
- **F09: Fibonacci Temporal Clusters** — Fibonacci bar count intervals (21, 34, 55, 89 bars) from major swing pivots.
- **F10: Golden Ratio Range Level** — Major range expansion pegged to the 1.618 geometric constant.

### Category G: Statistical & Quantitative (15 Strategies — G01 to G15)
*Focus: Distributional properties, mean reversion metrics, mathematical stationarity, and time series physics.*
- **G01: Z-Score Mean Reversion** — Standard score of current price relative to 20-day SMA (`Z = (Close - SMA) / StdDev`). Fades extreme `|Z| > 2.0`.
- **G02: Hurst Exponent (H)** — Rescaled range (R/S) analysis over 100 bars: `H > 0.55` indicates persistence (trend following); `H < 0.45` indicates anti-persistence (mean reversion).
- **G03: Return Autocorrelation** — Lag-1 Pearson autocorrelation of daily log returns over 30 days.
- **G04: Regression Channel Slope** — 50-bar D1 Linear Regression line angle and R-squared fit.
- **G05: Lo-MacKinlay Variance Ratio** — Ratio of 2-period variance to 1-period variance assessing random walk rejection.
- **G06: Return Distribution Skewness** — Third standardized moment of returns over 20 days.
- **G07: Return Distribution Kurtosis** — Fourth standardized moment measuring tail risk and probability of explosive directional moves.
- **G08: Moving Average Velocity & Acceleration** — First and second derivatives of the 20-day SMA.
- **G09: Cumulative N-Day Return Momentum** — Aggregate return over the prior 5 trading sessions.
- **G10: Consecutive Days Exhaustion** — 3 or more consecutive up/down D1 closes triggering conditional mean reversion.
- **G11: Opening Range Relative Position** — Position of today's open within yesterday's High-Low range (top quartile = bullish bias).
- **G12: Daily Gap Fill / Continuation Dynamics** — Direction and magnitude of the midnight/session open gap.
- **G13: Range Expansion Exhaustion** — Previous day range > 1.8x 10-day ATR signaling trend exhaustion / pause.
- **G14: Distance from 50-Day Moving Average** — Percentage price displacement from 50-day SMA.
- **G15: DeMark Sequential Setup (TD Setup)** — 9 consecutive closes higher/lower than the close 4 bars prior.

### Category H: Inter-Market & Macro Correlation (16 Strategies — H01 to H16)
*Focus: Cross-asset transmission channels, currency dominance, real yields, and global risk sentiment.*
- **H01: US Dollar Index (DXY / EURUSD Proxy) Inverse** — Inverse relationship between USD strength and Gold.
- **H02: US 10-Year Nominal Yield** — Yield direction as an opportunity cost driver for non-yielding bullion.
- **H03: Real Yield Proxy** — Nominal yield minus inflation breakeven trend.
- **H04: S&P 500 Risk Appetite (US500)** — Equity market risk-on vs safe-haven risk-off capital rotation.
- **H05: CBOE Volatility Index (VIX) Fear Gauge** — Safe-haven bid acceleration when implied equity volatility spikes.
- **H06: Crude Oil (WTI / Brent) Inflation Transmission** — Energy price momentum as a precursor to gold inflation hedging.
- **H07: Silver / Gold Ratio (GSR)** — Relative performance of industrial/monetary metals.
- **H08: Copper / Gold Ratio** — "Dr. Copper" economic growth barometer vs Gold safe-haven reserve.
- **H09: USDJPY Transmission Channel** — Global interest rate differential proxy and safe-haven liquidity flow.
- **H10: EURUSD Anchor Correlation** — Primary counterweight to DXY pricing.
- **H11: Bitcoin (BTCUSD) Digital Store-of-Value Flow** — Correlation / liquidity competition between modern and traditional stores of value.
- **H12: Sovereign Bond Market Flight** — Flight-to-safety signals derived from long-term treasury/bund proxies.
- **H13: Swiss Franc (USDCHF) Safe Haven Alignment** — Currency safe-haven confirmation.
- **H14: Australian Dollar (AUDUSD) Commodity Proxy** — High-beta commodity currency linkage.
- **H15: Emerging Market Stress Indicator** — EM currency stress (e.g. USDMXN/USDZAR) driving systemic safe-haven buying.
- **H16: Cross-Asset Momentum Consensus** — Meta-model synthesizing directional alignment across 5 primary macro proxies.

### Category I: Temporal & Calendar Effects (15 Strategies — I01 to I15)
*Focus: Institutional calendar cycles, session timing mechanics, fixings, and macroeconomic event drift.*
- **I01: Day-of-Week Institutional Drift** — Empirical weekday performance characteristics (e.g. Tuesday trend day vs Friday profit-taking).
- **I02: Monthly Seasonality Cycle** — Historical monthly tendencies (e.g. January structural inflows vs summer consolidation).
- **I03: London AM Gold Fix Directional Flow** — Pre-fixing order flow positioning ahead of the 10:30 UTC LBMA benchmark.
- **I04: Asian Session Range Breakout** — Direction of the London breakout of the 00:00–07:00 UTC Asian High-Low envelope.
- **I05: First London Hour Directional Continuity** — Directional continuation of the initial London open bar (07:00–08:00 UTC).
- **I06: NFP Week Pre-Positioning** — Institutional flow patterns during Non-Farm Payrolls week.
- **I07: FOMC Cycle Drift** — Pre-Federal Open Market Committee drift dynamics.
- **I08: Month-End Portfolio Rebalancing Flow** — Flow distortions during the final 3 trading sessions of each calendar month.
- **I09: Quarter-End Asset Allocation Effect** — Institutional rebalancing across quarterly accounting closes.
- **I10: COMEX Options Expiry Gravitational Pull** — Pinning and gravitational drift toward strike clustering.
- **I11: Monday Open Gap Directional Bias** — Weekend geopolitical pricing resolution through Monday opening gaps.
- **I12: Pre-Holiday Liquidity Drain** — Systematic drift preceding major US/UK bank holidays.
- **I13: CPI Week Momentum Positioning** — Pre-inflation report drift.
- **I14: Seasonal Tax & Physical Flow** — Spring tax liquidity absorption and autumn Indian festival physical demand cycles.
- **I15: Year-End "Santa Claus" Rally** — Systematic late-Q4 gold allocation flows.

### Category J: Pivot & Support / Resistance (10 Strategies — J01 to J10)
*Focus: Geometric price levels, institutional benchmark pivots, and order book reaction zones.*
- **J01: Classic Floor Trader Daily Pivot** — Price relative to `P = (H + L + C) / 3`.
- **J02: Fibonacci Daily Pivot Levels** — Pivots weighted by Fibonacci displacement ratios.
- **J03: Camarilla Equation Pivots** — Intraday mean reversion levels (L3/H3) and breakout triggers (L4/H4).
- **J04: Weekly Benchmark Pivot Bias** — Orientation relative to the higher-timeframe weekly pivot.
- **J05: Monthly Structural Pivot Bias** — Long-term macro pivot orientation.
- **J06: Previous Day High / Low (PDH/PDL) Breakout** — Breakout or rejection relative to prior day extremes.
- **J07: Previous Week High / Low (PWH/PWL) Structure** — Major multi-day liquidity boundary reactions.
- **J08: Institutional Round Number Magnet ($50/$100)** — Psychological round numbers acting as liquidity magnets or rejection barriers.
- **J09: Multi-Touch Horizontal S/R Bounce** — Swing levels verified by 3 or more independent touches on H4.
- **J10: Floor Trader Pivots with Midpoints (M1–M4)** — Sub-pivot reactions for refined intraday bias.

### Category K: Candlestick Pattern Recognition (12 Strategies — K01 to K12)
*Focus: Pure OHLC geometric bar relationships, exhaustion wicks, and institutional absorption patterns.*
- **K01: Bullish / Bearish Engulfing** — Confirmed D1/H4 engulfing bar absorbing the preceding candle body.
- **K02: Pin Bar / Hammer Rejection** — Long rejection wick (>60% of total candle length) with small body at key S/R.
- **K03: Morning Star / Evening Star** — 3-bar reversal cluster signifying momentum transition.
- **K04: Three White Soldiers / Three Black Crows** — Consecutive strong-bodied trend candles demonstrating institutional conviction.
- **K05: Doji Indecision at Structural Extremes** — Indecision candle resolving in the direction of the subsequent breakout.
- **K06: Inside Bar London Breakout** — D1 Inside Bar followed by London session boundary breakout.
- **K07: Marubozu Momentum Impulse** — Wide-range candle with negligible wicks (<5% of body) indicating one-sided order flow.
- **K08: Tweezer Tops / Bottoms** — Exact matching highs or lows across consecutive D1 candles.
- **K09: Dark Cloud Cover / Piercing Line** — 50%+ penetration into prior candle body.
- **K10: Harami Structural Pause** — Inside body reversal or continuation setup.
- **K11: Rising Three / Falling Three Methods** — 5-candle trend continuation structure.
- **K12: Abandoned Baby Island Reversal** — Rare exhaustion gap, doji, and subsequent reverse gap on D1.

### Category L: Psychological & Sentiment Modeling (8 Strategies — L01 to L08)
*Focus: Crowd overextension, panic liquidation, contrarian traps, and market consensus divergence.*
- **L01: Contrarian Extreme Run** — Fading consecutive 5-day directional runs where retail sentiment reaches peak euphoria/despair.
- **L02: Volatility Contraction Calm (Quiet Trap)** — Multi-day compressed ATR preceding explosive institutional release.
- **L03: Panic Candle Climax Reversal** — Wide-range candle (>3x ATR) with massive closing rejection wick indicating retail capitulation.
- **L04: Failed Breakout (Bull / Bear Trap)** — Price penetrates key horizontal resistance/support but violently closes back inside.
- **L05: Multiple Level Rejection Absorption** — Persistent failure to penetrate a level, indicating passive limit order absorption.
- **L06: Dual Oscillator Exhaustion** — Simultaneous extreme readings on RSI (>75/<25) and MACD histogram.
- **L07: Consensus Divergence** — When standard indicators show unanimous bullishness but price action stagnates or distributes.
- **L08: Session Gap Fill Gravitational Bias** — Probability of unfilled session gaps acting as mean-reversion magnets.

### Category M: Experimental & Quantitative Edge (10 Strategies — M01 to M10)
*Focus: Frontier mathematical physics, information theory, cyclical oddities, and contrarian meta-models.*
- **M01: Lunar Synodic Phase Cycle** — Astronomical full/new moon gravitational and sentiment correlation on precious metals.
- **M02: Calendar Day Prime Modulo Cycles** — Mathematical prime modulo periodicity testing non-linear market cycles.
- **M03: Price Terminal Digit Clustering** — Statistical clustering and symmetry of terminal cents (.00, .50, .80) in gold closes.
- **M04: Mandelbrot Fractal Dimension (D)** — Box-counting / Sevcik fractal dimension of H1 price curves.
- **M05: Shannon Information Entropy** — Information entropy of price return states measuring market disorder vs structured trend.
- **M06: Candle Body-to-Range Golden Sequence** — Fibonacci sequence ratios applied to successive candle dimensions.
- **M07: Price Memory Horizon Resonance** — Historical price cluster resonance at exact 20, 50, and 100-day lookback intervals.
- **M08: Volume-Weighted Center of Mass (VWAP Centroid)** — 20-day volume/tick weighted price equilibrium acting as a gravitational anchor.
- **M09: Calendar Day Parity Drift** — Odd vs Even day statistical return distribution (isolated experimental noise control).
- **M10: Inverse Meta-Consensus (The Heretic Brain)** — Contrarian meta-brain: if >80% of all other brains agree on a direction, votes the exact OPPOSITE direction.

---

## 3. Dimensional Market Coverage Validation

To ensure the 144 strategy brains form a robust, non-redundant ensemble, the CSO has mapped every strategy to the **13 Essential Market Dimensions**:

| Dimension | Strategy Category | Brain IDs | Brain Count | System Weight | Dimensional Role |
|---|---|---|---|---|---|
| **1. Price Structure & SMC** | Cat A | A01–A12 | 12 | 8.33% | Institutional footprint, liquidity pools, structural breaks |
| **2. Trend & Directional Drift** | Cat B | B01–B15 | 15 | 10.42% | Intermediate & macro trend vector identification |
| **3. Momentum & Velocity** | Cat C | C01–C16 | 16 | 11.11% | Speed of price displacement, cyclical oscillator extremes |
| **4. Volatility & Energy** | Cat D | D01–D11 | 11 | 7.64% | Market compression, expansion readiness, regime state |
| **5. Order Flow & Volume** | Cat E | E01–E10 | 10 | 6.94% | Tick volume accumulation, distribution, volume climaxes |
| **6. Geometric / Fibonacci** | Cat F | F01–F10 | 10 | 6.94% | Structural ratios, golden spirals, harmonic patterns |
| **7. Statistical / Quantitative** | Cat G | G01–G15 | 15 | 10.42% | Mean reversion, stationarity, return moments, Z-scores |
| **8. Macro / Inter-Market** | Cat H | H01–H16 | 16 | 11.11% | DXY, yields, equities, commodities, cross-asset flow |
| **9. Temporal & Calendar** | Cat I | I01–I15 | 15 | 10.42% | London fix, session breakouts, day-of-week, seasonality |
| **10. Support, Resistance & Pivots**| Cat J | J01–J10 | 10 | 6.94% | Floor pivots, previous day/week boundaries, round levels |
| **11. Candlestick Anatomy** | Cat K | K01–K12 | 12 | 8.33% | Japanese price action patterns, rejection wicks, bodies |
| **12. Psychological / Sentiment** | Cat L | L01–L08 | 8 | 5.56% | Contrarian crowd exhaustion, bull/bear traps, calm before storm |
| **13. Frontier / Experimental** | Cat M | M01–M10 | 10 | 6.94% | Fractal dimension, entropy, lunar cycles, inverse consensus |
| **TOTAL** | **13 Categories** | **A01–M10** | **144** | **100.0%** | **Complete Multi-Dimensional Ensemble** |

### Coverage Audit Verdict
1. **Zero Blind Spots**: The architecture evaluates Gold across microstructure (SMC/Order Flow), macroeconomics (Inter-market), physics/mathematics (Statistical/Entropy), geometry (Fibonacci/Harmonics), and human psychology (Sentiment/Temporal).
2. **Category Balance**: No single category exceeds 11.11% of the total vote pool. The largest categories (Momentum: 16, Inter-Market: 16, Trend: 15, Statistical: 15, Temporal: 15) represent the empirical primary drivers of Gold's daily drift.
3. **Contrarian Safeguard**: Psychological (Cat L) and Experimental (Cat M, specifically M10) provide vital negative correlation to prevent runaway groupthink during regime transitions.

---

## 4. The 5 Strategy Quality Gates & Anti-Overfit Architecture

Before any strategy may transition from Strategy Research to Engineering and Integration, it must pass all **Five CSO Quality Gates**:

```
[ Research Specification ]
            │
            ▼
┌───────────────────────────────────────┐
│ GATE 1: Theoretical & Causal Basis    │  Reject pure curve-fits lacking market logic
└──────────────────┬────────────────────┘
                   │ Pass
                   ▼
┌───────────────────────────────────────┐
│ GATE 2: Parameter Parsimony (Max 3)   │  No magic numbers; standard parameters only
└──────────────────┬────────────────────┘
                   │ Pass
                   ▼
┌───────────────────────────────────────┐
│ GATE 3: Structural Independence       │  Cross-correlation check (<85% collinearity)
└──────────────────┬────────────────────┘
                   │ Pass
                   ▼
┌───────────────────────────────────────┐
│ GATE 4: Execution & Data Feasibility  │  Pure MQL5, confirmed bar[1], shared handles
└──────────────────┬────────────────────┘
                   │ Pass
                   ▼
┌───────────────────────────────────────┐
│ GATE 5: Gold Domain Stress & Regimes  │  Safe-haven, session, news, spread awareness
└──────────────────┬────────────────────┘
                   │ Pass
                   ▼
[ Approved for Engineering (B01-B47) ]
```

### Gate 1: Theoretical & Causal Basis (First Principles)
- **Mandate**: Every strategy must possess an identifiable causal driver rooted in market microstructure, macroeconomic capital flow, liquidity engineering, or statistical physics.
- **Rejection Rule**: Reject any rule derived purely from data mining (e.g. "Buy if RSI is between 43.2 and 47.1 on Thursdays").
- **Exemption**: Experimental category (M01–M10) strategies are explicitly classified as exploratory hypotheses, governed by strict adaptive weight suppression if unvalidated.

### Gate 2: Parameter Parsimony & Degree of Freedom Limits
- **Parameter Ceiling**: A maximum of **3 tunable parameters** per brain.
- **Standard Baseline**: All indicators MUST utilize universally recognized default periods:
  - RSI = 14
  - MACD = 12, 26, 9
  - Stochastic = 14, 3, 3
  - Moving Averages = 8, 13, 21, 34, 50, 55, 89, 144, 200 (Fibonacci / classic)
  - Bollinger Bands = 20, 2.0
  - ATR = 14
- **Parameter Sensitivity Invariance**: If altering an indicator period by +/-15% (e.g. RSI 14 to 12 or 16) causes the signal to invert or collapse, the strategy fails Gate 2.

### Gate 3: Structural Independence & Collinearity Budgeting
- **Expected Agreement Rate Threshold**: Any two strategies exhibiting `>85%` historical vote alignment are flagged as redundant.
- **Resolution**:
  - Distinct Timeframe / Formula: Retain both if they evaluate different time horizons (e.g., B01 H4 EMA cross vs B02 H1 Ribbon).
  - Pure Redundancy: Merge or modify one to capture a distinct nuance (e.g., convert a binary moving average check into a velocity or distance check).

### Gate 4: Execution Feasibility & Zero-Leakage Protocol
- **Strict Bar Reference**: Signals MUST only access closed candles: `bar[1]` or older. Any brain accessing `bar[0]` is immediately disqualified.
- **Pure MQL5 Compatibility**: All calculations must execute natively in MQL5 without third-party DLLs, Python bridges, or WebRequest runtime dependencies.
- **Shared Handle Architecture Compliance**: All indicators must reference centralized global handles created in `OnInit()` to prevent handle exhaustion (>512 MT5 limit).

### Gate 5: Gold Domain Stress & Regime Robustness
- **Regime Evaluation**: The strategy must have a designated performance thesis across all 4 Gold regimes:
  1. *Macro Trending* (Fed easing or aggressive hiking: 2020, 2022, 2024)
  2. *Extended Range Consolidation* (2021 sideways chop)
  3. *Volatile Geopolitical Crisis* (Safe-haven liquidity spikes)
  4. *Low-Volatility Summer Lull* (Thin Asian/European liquidity)
- **Gold Mechanics**: Strategy logic must respect Gold's specific contract specification (`_Digits == 2`, `_Point == 0.01`, `pipFactor = 1.0`).

---

## 5. Wave 1 Prioritization & Implementation Directives

Wave 1 launches the foundational core of the Gold Oracle: **Category A (SMC/ICT, 12 strategies)** and **Category B (Trend Following, 15 strategies)**, totaling **27 strategy brains**.

### Wave 1 Strategy Classification & Prioritization Matrix

| Strategy ID | Strategy Name | Tier | Primary Timeframe | Indicators / Data Needed | Complexity | CSO Action Directive |
|---|---|---|---|---|---|---|
| **A01** | CHoCH Detector | **Tier 1** | H1 / M15 | Raw OHLC (3-bar swing pivots) | Medium | Core structural reversal anchor. Require 20-bar lookback. |
| **A02** | BOS Continuation | **Tier 1** | H1 | Raw OHLC (Swing breaks) | Low | Core trend continuation. Confirmed close through swing high/low. |
| **A03** | Order Block Demand | **Tier 1** | H4 / H1 | Raw OHLC + Volume | Medium | Unmitigated bullish OB formed prior to bullish impulse. |
| **A04** | Order Block Supply | **Tier 1** | H4 / H1 | Raw OHLC + Volume | Medium | Unmitigated bearish OB formed prior to downward impulse. |
| **A05** | Fair Value Gap Fill | **Tier 2** | H1 | Raw OHLC (3-candle imbalance) | Low | 3-bar displacement gap detection. Test if price is within gap. |
| **A06** | Asian Liquidity Sweep | **Tier 1** | M15 / H1 | Raw OHLC (00:00–07:00 UTC range) | Medium | London sweep of Asian high/low and rejection back into range. |
| **A07** | Premium / Discount Zone| **Tier 2** | D1 / H4 | 5-day / D1 swing range midpoint | Low | Macro context filter. Above 50% = Sell bias; Below 50% = Buy bias. |
| **A08** | Equal Highs/Lows Magnet| **Tier 2** | H1 | Swing highs/lows within 50 pts | Medium | Unswept liquidity pools acting as directional magnets. |
| **A09** | Market Structure Shift | **Tier 1** | H1 | A06 Sweep + A01 CHoCH combo | High | High-conviction reversal: sweep + displacement CHoCH. |
| **A10** | Optimal Trade Entry | **Tier 2** | H4 | H4 swing impulse + Fib 62-79% | Medium | Retracement into golden zone during active trend. |
| **A11** | Breaker Block | **Tier 3** | H1 | Violated Order Block coordinates | High | Track failed OBs flipping polarity. |
| **A12** | Wyckoff Phase | **Tier 3** | D1 | D1 range swing extremes | High | D1 Spring / UTAD detection. Needs long history check. |
| **B01** | EMA Golden/Death Cross | **Tier 1** | H4 | `iMA(PERIOD_H4, 50)`, `iMA(PERIOD_H4, 200)` | Low | Baseline macro trend anchor. Clean binary signal. |
| **B02** | EMA Ribbon Alignment | **Tier 1** | H1 | 6 EMAs (8, 13, 21, 34, 55, 89) | Medium | Unanimous trend alignment. All aligned = strong bias. |
| **B03** | Ichimoku Cloud | **Tier 2** | H4 | `iIchimoku(PERIOD_H4, 9, 26, 52)` | Low | Cloud position filter (Senkou Span A/B). |
| **B04** | Ichimoku TK Cross | **Tier 2** | H4 | `iIchimoku(PERIOD_H4, 9, 26, 52)` | Low | Tenkan/Kijun cross signal on H4. |
| **B05** | Supertrend Direction | **Tier 1** | H4 | Native MQL5 Supertrend (10, 3.0) | Medium | Implement ATR-based Supertrend without repainting. |
| **B06** | Parabolic SAR | **Tier 2** | H4 | `iSAR(PERIOD_H4, 0.02, 0.2)` | Low | Standard acceleration factor SAR position. |
| **B07** | ADX Directional Index | **Tier 1** | H4 | `iADX(PERIOD_H4, 14)` | Low | ADX > 25 threshold with +DI / -DI dominance. |
| **B08** | Aroon Oscillator | **Tier 2** | H4 | Native Aroon(25) computation | Medium | Aroon Up vs Down over 25 H4 bars. |
| **B09** | NRTR Trend State | **Tier 1** | H4 | Native Nick Rypock Trailing Reverse| Medium | Dynamic ATR-stepped trailing channel trend state. |
| **B10** | Donchian Channel Break | **Tier 2** | H4 | 20-period High/Low bands | Low | 20-bar channel breakout continuation. |
| **B11** | Keltner Channel Slope | **Tier 2** | H4 | EMA(20) +/- 2.0*ATR(10) | Medium | Price envelope penetration and channel slope. |
| **B12** | Linear Regression Slope| **Tier 1** | H4 | Native LinReg 50-bar calculation | Medium | Pure least-squares regression line slope. |
| **B13** | Heikin-Ashi Sequence | **Tier 2** | H4 | Native HA candle transformation | Low | 3 consecutive confirmed color bars. |
| **B14** | Hull Moving Average | **Tier 1** | H4 | Native HMA(20) calculation | Medium | Low-lag WMA(sqrt(period)) trend slope. |
| **B15** | Kaufman Adaptive MA | **Tier 2** | H4 | Native KAMA(10, 2, 30) calculation| Medium | Efficiency-ratio weighted adaptive slope. |

### Tier Breakdown
- **Tier 1: Core Institutional Anchors (11 Strategies)**:
  - SMC: `A01`, `A02`, `A03`, `A04`, `A06`, `A09`
  - Trend: `B01`, `B02`, `B05`, `B07`, `B09`, `B12`, `B14`
  *Role*: Form the high-conviction backbone of the Gold Oracle. These strategies possess the strongest empirical documentation and clearest causality.
- **Tier 2: Confirmation & Secondary Filters (12 Strategies)**:
  - SMC: `A05`, `A07`, `A08`, `A10`
  - Trend: `B03`, `B04`, `B06`, `B08`, `B10`, `B11`, `B13`, `B15`
  *Role*: Provide multi-angle confirmation, range exhaustion filtering, and structural boundaries.
- **Tier 3: Complex / High Scrutiny (4 Strategies)**:
  - SMC: `A11`, `A12`
  - Trend: None (all trend models are proven)
  *Role*: High algorithmic complexity. Must be scrutinized by the Chief Reasoning Officer (CRO) and QA team to ensure deterministic execution and zero repainting.

---

## 6. Wave 1 Indicator Handle Registry

To ensure the CEngO (E02) and Builders construct an optimal, leak-proof system, the CSO establishes the **Mandatory Indicator Handle Registry for Wave 1**:

```mql5
// ============================================================================
// WAVE 1 MANDATORY INDICATOR HANDLES (OnInit Initialized)
// ============================================================================
int g_h_ema50_h4;       // B01: EMA 50 on H4
int g_h_ema200_h4;      // B01: EMA 200 on H4
int g_h_ema8_h1;        // B02: Ribbon EMA 8
int g_h_ema13_h1;       // B02: Ribbon EMA 13
int g_h_ema21_h1;       // B02: Ribbon EMA 21
int g_h_ema34_h1;       // B02: Ribbon EMA 34
int g_h_ema55_h1;       // B02: Ribbon EMA 55
int g_h_ema89_h1;       // B02: Ribbon EMA 89
int g_h_ichimoku_h4;    // B03, B04: Ichimoku (9, 26, 52) on H4
int g_h_sar_h4;         // B06: Parabolic SAR (0.02, 0.2) on H4
int g_h_adx14_h4;       // B07: ADX(14) on H4
int g_h_atr14_h4;       // B05, B09, B11: Shared ATR(14) on H4
int g_h_atr14_h1;       // General volatility / Execution SL anchor
int g_h_ema20_h4;       // B11: Keltner centerline EMA(20) on H4

// NOTE: B05 (Supertrend), B08 (Aroon), B09 (NRTR), B12 (LinReg),
// B14 (HMA), B15 (KAMA), and ALL Category A (SMC) functions calculate
// natively from price arrays via CopyHigh/Low/Close without external handles!
```

---

## 7. Gold Domain Realities & Execution Standards

Every strategy researcher, reasoner, and engineer must adhere to the following non-negotiable physical realities of Gold:

1. **Session Volatility Profile**:
   - Asian Session (00:00–07:00 UTC): Typically consolidates within a 50–120 pip range. Liquidity is thin; spreads widen to 30–80 points.
   - London Session (07:00–10:00 UTC): Institutional open in London triggers directional expansion, hunting Asian liquidity pools. **This is our analysis window.**
   - NY Overlap (13:00–17:00 UTC): Peak institutional volume, maximum daily displacement, and primary profit-realization window. **This is our trade run window.**
   - Session Close (20:00 UTC): Liquidity dries up; positions are forcibly terminated.
2. **Spread Gating**:
   - Typical institutional Gold spread is 12–25 points during London/NY.
   - A hard spread gate of `30.0 points` (0.30 USD) is enforced before any trade entry at 10:00 UTC.
3. **ATR Normalization**:
   - Gold volatility varies by regime: normal H1 ATR is 40–80 pips ($0.40–$0.80); high volatility news days reach 150–300+ pips.
   - Fixed-pip logic is strictly prohibited. All stop losses and buffer zones must scale with `ATR(14, H1)`.

---

## 8. Handoff Protocol to Divisions 2, 3, and 4

1. **To Strategy Research (Division 2 — Category Leads R-Lead-A & R-Lead-B)**:
   - Proceed with detailed research and MQL5 pseudocode generation for Wave 1 (A01–A12, B01–B15).
   - Enforce the 7-Point Research Specification format on all subagent outputs.
2. **To Deep Reasoning (Division 3 — CRO E04 & T01–T25)**:
   - Audit Wave 1 strategies against the Gate 1–5 criteria.
   - Specifically cross-examine Tier 3 strategies (`A11 Breaker Block`, `A12 Wyckoff Phase`) for repainting and lookback edge cases.
3. **To Engineering (Division 4 — CEngO E02 & Builders)**:
   - Ensure the Shared Handle Registry is implemented in `OnInit()` and verified before compiling brain functions.
   - Enforce function signature standard: `int Brain[ID]_[Name]()` returning only `+1`, `-1`, or `0`.

---
*Signed and Enacted,*  
**E01 — Chief Strategy Officer (CSO)**  
*Gold Oracle Executive Council*

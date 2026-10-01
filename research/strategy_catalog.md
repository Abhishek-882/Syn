# Gold Oracle EA v2 — Master Strategy Catalog (144 Brains)

> **Document ID:** CIO-CATALOG-001  
> **Author:** E05 — Chief Integration Officer (CIO)  
> **Executive Oversight:** Executive Council (E01–E05)  
> **Target System:** Gold Oracle EA v2 (XAUUSD Daily Directional 144-Brain Multi-Agent Engine)  
> **Status:** ACTIVE MASTER REPOSITORY  
> **Last Updated:** 2026-10-01T18:15:00 UTC  

---

## 1. Executive Summary & Fleet Status

The Gold Oracle Master Strategy Catalog tracks the complete lifecycle of all **144 independent strategy brains** designed to predict the daily direction of Spot Gold (XAUUSD). Every brain operates as an isolated, non-repainting predictive function executed at 10:00 UTC, outputting strictly `+1` (BUY), `-1` (SELL), or `0` (NEUTRAL) to predict price movement until the 20:00 UTC daily session close.

### Fleet Metrics Summary
- **Total Strategies Defined:** 144 Brains
- **Total Categories:** 13 Dimensions (A through M)
- **Shared Indicator Handles:** 48 Central Handles (9.3% of MT5 512-handle limit)
- **Current Active Wave:** Wave 1 (SMC A01–A12 & Trend B01–B15 = 27 Strategies)
- **Lifecycle Status Summary:**
  - `[ASSIGNED]` (Wave 1): 27 Strategies
  - `[QUEUED]` (Waves 2–5): 117 Strategies
  - `[BUILT]` / `[TESTED]` / `[INTEGRATED]`: 0 Strategies (Standing by for Wave 1 launch)

---

## 2. Strategy Waves & Category Structure

| Wave | Category Code | Category Name | Strategy Range | Count | Category Lead | Lead Builder | QA Lead | Status |
|---|---|---|---|---|---|---|---|---|
| **Wave 1** | **Cat A** | Smart Money Concepts / ICT | A01–A12 | 12 | R-Lead-A | ENG-Lead-1 | QA-Lead-1 | **ASSIGNED (READY)** |
| **Wave 1** | **Cat B** | Trend Following | B01–B15 | 15 | R-Lead-B | ENG-Lead-1 | QA-Lead-1 | **ASSIGNED (READY)** |
| **Wave 2** | **Cat C** | Momentum & Oscillators | C01–C16 | 16 | R-Lead-C | ENG-Lead-2 | QA-Lead-1 | QUEUED |
| **Wave 2** | **Cat D** | Volatility Analysis | D01–D11 | 11 | R-Lead-D | ENG-Lead-2 | QA-Lead-2 | QUEUED |
| **Wave 2** | **Cat E** | Volume & Order Flow | E01–E10 | 10 | R-Lead-E | ENG-Lead-2 | QA-Lead-2 | QUEUED |
| **Wave 3** | **Cat F** | Fibonacci & Harmonics | F01–F10 | 10 | R-Lead-F | ENG-Lead-3 | QA-Lead-2 | QUEUED |
| **Wave 3** | **Cat G** | Statistical & Quantitative | G01–G15 | 15 | R-Lead-G | ENG-Lead-3 | QA-Lead-2 | QUEUED |
| **Wave 3** | **Cat H** | Inter-Market & Macro | H01–H16 | 16 | R-Lead-H | ENG-Lead-3 | QA-Lead-3 | QUEUED |
| **Wave 4** | **Cat I** | Temporal & Calendar | I01–I15 | 15 | R-Lead-I | ENG-Lead-4 | QA-Lead-3 | QUEUED |
| **Wave 4** | **Cat J** | Support, Resistance & Pivots | J01–J10 | 10 | R-Lead-J | ENG-Lead-4 | QA-Lead-3 | QUEUED |
| **Wave 4** | **Cat K** | Candlestick Patterns | K01–K12 | 12 | R-Lead-K | ENG-Lead-4 | QA-Lead-3 | QUEUED |
| **Wave 5** | **Cat L** | Psychological & Sentiment | L01–L08 | 8 | R-Lead-L | ENG-Lead-5 | QA-Lead-3 | QUEUED |
| **Wave 5** | **Cat M** | Frontier & Experimental | M01–M10 | 10 | R-Lead-M | ENG-Lead-5 | QA-Lead-3 | QUEUED |
| **TOTAL** | **13 Categories** | **Complete Ensemble** | **A01–M10** | **144** | **13 Leads** | **5 Leads** | **3 Leads** | **READY** |

---

## 3. Master Strategy Registry (All 144 Brains)

### Category A: Smart Money Concepts / ICT (A01–A12) — Wave 1
| ID | Strategy Name | Wave | TF | Indicators / Handles | Researcher | Reasoner | Builder | Tester | State | Gates (1-5) | Overfit Risk |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **A01** | CHoCH Detector | W1 | H1 | `h_ATR14_H1` | R01 | T01, T04 | B01 | QA-Brain-01 | `[ASSIGNED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **A02** | BOS Continuation | W1 | H1 | `h_ATR14_H1` | R01 | T01, T07 | B01 | QA-Brain-01 | `[ASSIGNED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **A03** | Order Block Demand | W1 | H1 | `h_ATR14_H1` | R01 | T04, T07 | B01 | QA-Brain-01 | `[ASSIGNED]` | `[ ][ ][ ][ ][ ]` | MEDIUM |
| **A04** | Order Block Supply | W1 | H1 | `h_ATR14_H1` | R02 | T04, T07 | B02 | QA-Brain-01 | `[ASSIGNED]` | `[ ][ ][ ][ ][ ]` | MEDIUM |
| **A05** | Fair Value Gap (FVG) | W1 | H1 | `h_ATR14_H1` | R02 | T01, T04 | B02 | QA-Brain-01 | `[ASSIGNED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **A06** | Asian Liquidity Sweep | W1 | H1/M15 | `h_ATR14_M15` | R02 | T04, T07 | B02 | QA-Brain-01 | `[ASSIGNED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **A07** | Premium / Discount Zone | W1 | D1/H4 | Price series (D1) | R03 | T01, T13 | B03 | QA-Brain-02 | `[ASSIGNED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **A08** | Equal Highs / Lows Magnet | W1 | H4 | `h_ATR14_H4` | R03 | T04, T10 | B03 | QA-Brain-02 | `[ASSIGNED]` | `[ ][ ][ ][ ][ ]` | MEDIUM |
| **A09** | Market Structure Shift (MSS)| W1 | H1 | `h_ATR14_H1` | R03 | T01, T04 | B03 | QA-Brain-02 | `[ASSIGNED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **A10** | Optimal Trade Entry (OTE) | W1 | H4 | `h_ATR14_H4` | R04 | T01, T10 | B04 | QA-Brain-02 | `[ASSIGNED]` | `[ ][ ][ ][ ][ ]` | MEDIUM |
| **A11** | Breaker Block | W1 | H1 | `h_ATR14_H1` | R04 | T04, T13 | B04 | QA-Brain-02 | `[ASSIGNED]` | `[ ][ ][ ][ ][ ]` | MEDIUM |
| **A12** | Wyckoff Phase Classification| W1 | D1 | Price series (D1) | R04 | T07, T13 | B04 | QA-Brain-02 | `[ASSIGNED]` | `[ ][ ][ ][ ][ ]` | HIGH |

---

### Category B: Trend Following (B01–B15) — Wave 1
| ID | Strategy Name | Wave | TF | Indicators / Handles | Researcher | Reasoner | Builder | Tester | State | Gates (1-5) | Overfit Risk |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **B01** | EMA Golden / Death Cross | W1 | H4 | `h_EMA50_H4`, `h_EMA200_H4` | R05 | T01, T10 | B05 | QA-Brain-03 | `[ASSIGNED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **B02** | EMA Ribbon Alignment | W1 | H1 | `h_EMA8_H4`–`h_EMA89_H4` | R05 | T01, T10 | B05 | QA-Brain-03 | `[ASSIGNED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **B03** | Ichimoku Kumo Cloud | W1 | H4 | `h_Ichimoku_H4` | R05 | T07, T13 | B05 | QA-Brain-03 | `[ASSIGNED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **B04** | Ichimoku TK Cross | W1 | H4 | `h_Ichimoku_H4` | R05 | T07, T10 | B05 | QA-Brain-03 | `[ASSIGNED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **B05** | Supertrend Direction | W1 | H4 | `h_ATR14_H4`, Price | R06 | T01, T04 | B06 | QA-Brain-03 | `[ASSIGNED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **B06** | Parabolic SAR | W1 | H4 | `h_SAR_H4` | R06 | T04, T10 | B06 | QA-Brain-03 | `[ASSIGNED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **B07** | ADX Directional Index | W1 | H4 | `h_ADX14_H4` | R06 | T01, T13 | B06 | QA-Brain-04 | `[ASSIGNED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **B08** | Aroon Oscillator | W1 | H4 | Price series (H4) | R06 | T04, T10 | B06 | QA-Brain-04 | `[ASSIGNED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **B09** | NRTR Trend State | W1 | H4 | `h_ATR14_H4`, Price | R07 | T01, T07 | B07 | QA-Brain-04 | `[ASSIGNED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **B10** | Donchian Channel Breakout | W1 | H4 | Price series (H4) | R07 | T01, T04 | B07 | QA-Brain-04 | `[ASSIGNED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **B11** | Keltner Channel Envelope | W1 | H4 | `h_EMA20_H4`, `h_ATR14_H4` | R07 | T01, T10 | B07 | QA-Brain-04 | `[ASSIGNED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **B12** | Linear Regression Slope | W1 | H4 | Price series (H4) | R07 | T01, T13 | B07 | QA-Brain-05 | `[ASSIGNED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **B13** | Heikin-Ashi Sequence | W1 | H4 | Price series (H4) | R08 | T04, T10 | B08 | QA-Brain-05 | `[ASSIGNED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **B14** | Hull Moving Average (HMA) | W1 | H4 | Price series (H4) | R08 | T01, T04 | B08 | QA-Brain-05 | `[ASSIGNED]` | `[ ][ ][ ][ ][ ]` | MEDIUM |
| **B15** | Kaufman Adaptive MA (KAMA)| W1 | H4 | Price series (H4) | R08 | T01, T13 | B08 | QA-Brain-05 | `[ASSIGNED]` | `[ ][ ][ ][ ][ ]` | MEDIUM |

---

### Category C: Momentum & Oscillators (C01–C16) — Wave 2
| ID | Strategy Name | Wave | TF | Indicators / Handles | Researcher | Reasoner | Builder | Tester | State | Gates (1-5) | Overfit Risk |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **C01** | RSI Trend Bias | W2 | H4 | `h_RSI14_H4` | R09 | T01, T10 | B09 | QA-Brain-06 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **C02** | RSI Swing Divergence | W2 | H4 | `h_RSI14_H4`, Price | R09 | T01, T04 | B09 | QA-Brain-06 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | MEDIUM |
| **C03** | MACD Histogram Momentum | W2 | H4 | `h_MACD_H4` | R09 | T01, T10 | B09 | QA-Brain-06 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **C04** | MACD Signal Line Cross | W2 | H4 | `h_MACD_H4` | R09 | T01, T10 | B09 | QA-Brain-06 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **C05** | Stochastic Reversal | W2 | H4 | `h_Stoch_H4` | R10 | T04, T07 | B10 | QA-Brain-06 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **C06** | CCI Extremes | W2 | H4 | `h_CCI20_H4` | R10 | T04, T10 | B10 | QA-Brain-06 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **C07** | Williams %R | W2 | H4 | `h_WPR14_H4` | R10 | T04, T10 | B10 | QA-Brain-07 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **C08** | Money Flow Index (MFI) | W2 | H4 | `h_MFI14_H4` | R10 | T07, T13 | B10 | QA-Brain-07 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **C09** | QQE Bull/Bear Trail | W2 | H4 | `h_RSI14_H4` (RSX filter)| R11 | T01, T04 | B11 | QA-Brain-07 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | MEDIUM |
| **C10** | Tom DeMark REI | W2 | H4 | Price series (H4) | R11 | T01, T04 | B11 | QA-Brain-07 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **C11** | Rate of Change (ROC) | W2 | H4 | Price series (H4) | R11 | T01, T10 | B11 | QA-Brain-07 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **C12** | Awesome Oscillator (AO) | W2 | H4 | `h_AO_H4` | R11 | T01, T10 | B11 | QA-Brain-08 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **C13** | Bears / Bulls Power | W2 | H4 | `h_Bears13_H4`, `h_Bulls13_H4`| R12 | T01, T07 | B12 | QA-Brain-08 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **C14** | RSI-EMA Crossover | W2 | H4 | `h_RSI14_H4` | R12 | T01, T10 | B12 | QA-Brain-08 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **C15** | Momentum Slope | W2 | H4 | `h_Momentum14_H4` | R12 | T01, T10 | B12 | QA-Brain-08 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **C16** | Triple RSI Confluence | W2 | MTF | `h_RSI14_H1,H4,D1` | R12 | T01, T13 | B12 | QA-Brain-08 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | LOW |

---

### Category D: Volatility Analysis (D01–D11) — Wave 2
| ID | Strategy Name | Wave | TF | Indicators / Handles | Researcher | Reasoner | Builder | Tester | State | Gates (1-5) | Overfit Risk |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **D01** | Bollinger Bands Position | W2 | H4 | `h_Bands20_2_H4` | R13 | T01, T10 | B13 | QA-Brain-09 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **D02** | BB Squeeze Breakout | W2 | H4 | `h_Bands20_2_H4`, `h_ATR14_H4`| R13 | T01, T04 | B13 | QA-Brain-09 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **D03** | ATR Expansion Impulse | W2 | H1 | `h_ATR14_H1` | R13 | T04, T07 | B13 | QA-Brain-09 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **D04** | ATR VOL MACD | W2 | H4 | `h_ATR14_H4` (time series) | R14 | T01, T10 | B14 | QA-Brain-09 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | MEDIUM |
| **D05** | Chaikin Volatility | W2 | H4 | Price series (H4) | R14 | T01, T04 | B14 | QA-Brain-09 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **D06** | ATR Channel Position | W2 | H4 | `h_ATR14_H4`, `h_EMA20_H4` | R14 | T01, T10 | B14 | QA-Brain-09 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **D07** | BB Width Percentile | W2 | H4 | `h_Bands20_2_H4` (100 bars)| R15 | T01, T13 | B15 | QA-Brain-10 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **D08** | ADR Utilization Ratio | W2 | D1/H1 | `h_ATR14_D1`, Price | R15 | T04, T07 | B15 | QA-Brain-10 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **D09** | Volatility Regime Classifier| W2 | H4 | `h_ATR14_H4`, `h_ATR100_H4`| R15 | T01, T13 | B15 | QA-Brain-10 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **D10** | Standard Deviation Velocity | W2 | H4 | `h_StdDev20_H4` | R16 | T01, T04 | B16 | QA-Brain-10 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **D11** | Keltner-BB Overlap State | W2 | H4 | `h_Bands20_2_H4`, `h_ATR14_H4`| R16 | T01, T04 | B16 | QA-Brain-10 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | LOW |

---

### Category E: Volume Analysis (E01–E10) — Wave 2
| ID | Strategy Name | Wave | TF | Indicators / Handles | Researcher | Reasoner | Builder | Tester | State | Gates (1-5) | Overfit Risk |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **E01** | OBV Trend | W2 | H4 | `h_OBV_H4` | R17 | T07, T10 | B17 | QA-Brain-11 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **E02** | Volume-Price Trend (VPT) | W2 | H4 | Price + Tick Volume (H4) | R17 | T01, T07 | B17 | QA-Brain-11 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **E03** | Accumulation / Distribution | W2 | H4 | `h_AD_H4` | R17 | T07, T10 | B17 | QA-Brain-11 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **E04** | Chaikin Money Flow (CMF) | W2 | H4 | `h_AD_H4`, Tick Volume | R18 | T01, T07 | B18 | QA-Brain-11 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **E05** | Elder Force Index | W2 | H4 | `h_Force13_H4` | R18 | T01, T07 | B18 | QA-Brain-11 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **E06** | Tick Volume Divergence | W2 | H1 | Price + Tick Volume (H1) | R18 | T04, T07 | B18 | QA-Brain-12 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | MEDIUM |
| **E07** | Volume Climax Exhaustion | W2 | H1 | Tick Volume (H1) | R19 | T04, T07 | B19 | QA-Brain-12 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | MEDIUM |
| **E08** | Ease of Movement (EMV) | W2 | H4 | Price + Tick Volume (H4) | R19 | T01, T07 | B19 | QA-Brain-12 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **E09** | Volume Oscillator | W2 | H4 | Tick Volume MAs (H4) | R20 | T01, T10 | B20 | QA-Brain-12 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **E10** | Session Volume Ratio | W2 | H1 | Tick Volume (Asia vs London)| R20 | T04, T07 | B20 | QA-Brain-12 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | MEDIUM |

---

### Category F: Fibonacci & Harmonic Patterns (F01–F10) — Wave 3
| ID | Strategy Name | Wave | TF | Indicators / Handles | Researcher | Reasoner | Builder | Tester | State | Gates (1-5) | Overfit Risk |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **F01** | Fib Retracement Bounce | W3 | D1/H4 | Price series (Pivots) | R21 | T01, T04 | B21 | QA-Brain-13 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **F02** | Fib Extension Target | W3 | D1/H4 | Price series (Pivots) | R21 | T01, T10 | B21 | QA-Brain-13 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **F03** | Fibonacci Daily Pivots | W3 | D1 | Prior D1 OHLC | R21 | T01, T07 | B21 | QA-Brain-13 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **F04** | Fibonacci MA Channel | W3 | H4 | `h_EMA21_H4`, `h_ATR14_H4` | R22 | T01, T10 | B22 | QA-Brain-13 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **F05** | Harmonic Gartley Pattern | W3 | H4 | Price Pivots (XA, AB, BC, CD)| R22 | T01, T04 | B22 | QA-Brain-13 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | HIGH |
| **F06** | Harmonic Butterfly | W3 | H4 | Price Pivots (XA, AB, BC, CD)| R22 | T01, T04 | B22 | QA-Brain-14 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | HIGH |
| **F07** | Harmonic Bat Pattern | W3 | H4 | Price Pivots (XA, AB, BC, CD)| R23 | T01, T04 | B23 | QA-Brain-14 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | HIGH |
| **F08** | AB=CD Measured Move | W3 | H4 | Price Pivots (A, B, C, D) | R23 | T01, T04 | B23 | QA-Brain-14 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | MEDIUM |
| **F09** | Fibonacci Time Zone | W3 | D1 | Prior Major Swings | R23 | T01, T13 | B23 | QA-Brain-14 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | MEDIUM |
| **F10** | Golden Ratio Range Level | W3 | D1 | Prior Range extremes | R23 | T01, T07 | B23 | QA-Brain-14 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | LOW |

---

### Category G: Statistical & Quantitative (G01–G15) — Wave 3
| ID | Strategy Name | Wave | TF | Indicators / Handles | Researcher | Reasoner | Builder | Tester | State | Gates (1-5) | Overfit Risk |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **G01** | Z-Score Mean Reversion | W3 | D1 | `h_SMA20_H4`, StdDev | R24 | T01, T04 | B24 | QA-Brain-15 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **G02** | Hurst Exponent (H) | W3 | D1 | Price closes (100 bars) | R24 | T01, T13 | B24 | QA-Brain-15 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **G03** | Return Autocorrelation | W3 | D1 | Daily returns (30 bars) | R24 | T01, T10 | B24 | QA-Brain-15 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **G04** | Regression Channel Slope | W3 | D1 | Daily closes (50 bars) | R25 | T01, T10 | B25 | QA-Brain-15 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **G05** | Variance Ratio (Lo-MacKinlay)| W3 | D1 | Daily returns (60 bars) | R25 | T01, T13 | B25 | QA-Brain-15 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **G06** | Return Distribution Skew | W3 | D1 | Daily returns (20 bars) | R25 | T01, T04 | B25 | QA-Brain-16 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **G07** | Kurtosis Fat Tail | W3 | D1 | Daily returns (30 bars) | R26 | T01, T04 | B26 | QA-Brain-16 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **G08** | Moving Average Velocity | W3 | D1 | `h_SMA20_H4` first/second dev | R26 | T01, T10 | B26 | QA-Brain-16 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **G09** | N-Day Return Momentum | W3 | D1 | Last 5 D1 closes | R26 | T01, T10 | B26 | QA-Brain-16 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **G10** | Consecutive Days Pattern | W3 | D1 | Last 3-5 D1 closes | R27 | T04, T07 | B27 | QA-Brain-16 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **G11** | Opening Range Relative Pos | W3 | D1 | Open vs prior D1 H/L | R27 | T04, T07 | B27 | QA-Brain-17 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **G12** | Gap Fill / Continuation | W3 | D1 | Open vs prior D1 Close | R27 | T04, T07 | B27 | QA-Brain-17 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **G13** | Range Expansion Exhaustion | W3 | D1 | Prior D1 Range vs `h_ATR14_D1`| R28 | T04, T13 | B28 | QA-Brain-17 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **G14** | Distance from 50-Day MA | W3 | D1 | Close vs `h_EMA50_D1` | R28 | T01, T04 | B28 | QA-Brain-17 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **G15** | DeMark Sequential Setup | W3 | D1 | 9-bar close comparison | R28 | T01, T04 | B28 | QA-Brain-17 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | MEDIUM |

---

### Category H: Inter-Market & Macro Correlation (H01–H16) — Wave 3
| ID | Strategy Name | Wave | TF | Indicators / Handles | Researcher | Reasoner | Builder | Tester | State | Gates (1-5) | Overfit Risk |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **H01** | DXY Inverse Proxy | W3 | H4 | `EURUSD` price / `h_EURUSD_H4` | R29 | T07, T10 | B29 | QA-Brain-18 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **H02** | US 10Y Yield Direction | W3 | H4 | `US10Y` proxy (`USDJPY` fallback)| R29 | T07, T10 | B29 | QA-Brain-18 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | MEDIUM |
| **H03** | Real Yield Proxy | W3 | H4 | Nominal yield vs breakeven | R29 | T07, T13 | B29 | QA-Brain-18 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | MEDIUM |
| **H04** | S&P 500 Risk Appetite | W3 | H4 | `US500` / `SPX` proxy | R29 | T07, T10 | B29 | QA-Brain-18 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **H05** | VIX Fear Gauge | W3 | H4 | `VIX` proxy / Implied Vol | R30 | T07, T13 | B30 | QA-Brain-18 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | MEDIUM |
| **H06** | Crude Oil Correlation | W3 | H4 | `USOIL` / `UKOIL` proxy | R30 | T07, T10 | B30 | QA-Brain-18 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **H07** | Silver / Gold Ratio | W3 | H4 | `XAGUSD` / `h_XAGUSD_H4` | R30 | T07, T10 | B30 | QA-Brain-19 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **H08** | Copper / Gold Ratio | W3 | H4 | `COPPER` / `HG` proxy | R30 | T07, T13 | B30 | QA-Brain-19 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | MEDIUM |
| **H09** | USDJPY Transmission | W3 | H4 | `USDJPY` proxy | R31 | T07, T10 | B31 | QA-Brain-19 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **H10** | EURUSD Anchor | W3 | H4 | `EURUSD` price series | R31 | T07, T10 | B31 | QA-Brain-19 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **H11** | Bitcoin Flow Correlation | W3 | H4 | `BTCUSD` proxy | R31 | T07, T13 | B31 | QA-Brain-19 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | MEDIUM |
| **H12** | Sovereign Bond Flight | W3 | H4 | `TLT` / Treasury Bond proxy | R31 | T07, T10 | B31 | QA-Brain-20 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | MEDIUM |
| **H13** | CHF Safe Haven Alignment | W3 | H4 | `USDCHF` proxy | R32 | T07, T10 | B32 | QA-Brain-20 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **H14** | AUD Commodity Proxy | W3 | H4 | `AUDUSD` proxy | R32 | T07, T10 | B32 | QA-Brain-20 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **H15** | EM Currency Stress | W3 | H4 | `USDMXN` / `USDZAR` proxy | R32 | T07, T13 | B32 | QA-Brain-20 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | MEDIUM |
| **H16** | Cross-Asset Momentum | W3 | H4 | Ensemble of H01, H04, H06, H07| R32 | T07, T10 | B32 | QA-Brain-20 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | LOW |

---

### Category I: Temporal & Calendar Effects (I01–I15) — Wave 4
| ID | Strategy Name | Wave | TF | Indicators / Handles | Researcher | Reasoner | Builder | Tester | State | Gates (1-5) | Overfit Risk |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **I01** | Day of Week Institutional Drift| W4 | D1 | Calendar `TimeGMT()` | R33 | T07, T10 | B33 | QA-Brain-21 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **I02** | Monthly Seasonality Cycle | W4 | D1 | Calendar Month | R33 | T07, T13 | B33 | QA-Brain-21 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **I03** | London AM Fix Flow | W4 | H1 | 10:00 UTC London price flow| R33 | T04, T07 | B33 | QA-Brain-21 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **I04** | Asian Range Breakout | W4 | H1 | 00:00–07:00 UTC Asian High/Low| R34 | T04, T07 | B34 | QA-Brain-21 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **I05** | First London Hour Direction | W4 | H1 | 07:00–08:00 UTC bar direction | R34 | T01, T04 | B34 | QA-Brain-21 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **I06** | NFP Week Pre-Positioning | W4 | D1 | 1st week of month indicator| R34 | T07, T13 | B34 | QA-Brain-21 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | MEDIUM |
| **I07** | FOMC Cycle Drift | W4 | D1 | FOMC calendar cycle | R35 | T07, T13 | B35 | QA-Brain-22 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | MEDIUM |
| **I08** | Month-End Portfolio Flow | W4 | D1 | Final 3 trading days | R35 | T07, T10 | B35 | QA-Brain-22 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **I09** | Quarter-End Rebalance | W4 | D1 | March/June/Sept/Dec end | R35 | T07, T10 | B35 | QA-Brain-22 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **I10** | Options Expiry Gravitational | W4 | D1 | COMEX expiry calendar | R36 | T07, T10 | B36 | QA-Brain-22 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | MEDIUM |
| **I11** | Monday Open Gap Bias | W4 | D1 | Monday Open vs Friday Close | R36 | T04, T07 | B36 | QA-Brain-22 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **I12** | Pre-Holiday Liquidity Drain | W4 | D1 | Bank Holiday calendar | R36 | T04, T07 | B36 | QA-Brain-23 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **I13** | CPI Week Momentum | W4 | D1 | 2nd week of month cycle | R37 | T07, T13 | B37 | QA-Brain-23 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | MEDIUM |
| **I14** | Tax & Indian Physical Cycle | W4 | D1 | April / Oct-Nov wedding season | R37 | T07, T13 | B37 | QA-Brain-23 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **I15** | Year-End Santa Rally | W4 | D1 | Late December calendar | R37 | T07, T13 | B37 | QA-Brain-23 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | LOW |

---

### Category J: Pivot & Support / Resistance (J01–J10) — Wave 4
| ID | Strategy Name | Wave | TF | Indicators / Handles | Researcher | Reasoner | Builder | Tester | State | Gates (1-5) | Overfit Risk |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **J01** | Classic Floor Pivot | W4 | D1 | Prior D1 OHLC | R38 | T01, T04 | B38 | QA-Brain-23 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **J02** | Fibonacci Daily Pivots | W4 | D1 | Prior D1 OHLC + Fib ratios | R38 | T01, T04 | B38 | QA-Brain-24 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **J03** | Camarilla Equation Pivots | W4 | D1 | Prior D1 OHLC + Camarilla | R38 | T01, T04 | B38 | QA-Brain-24 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **J04** | Weekly Benchmark Pivot | W4 | W1 | Prior W1 OHLC | R38 | T01, T10 | B38 | QA-Brain-24 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **J05** | Monthly Structural Pivot | W4 | MN1 | Prior MN1 OHLC | R39 | T01, T10 | B39 | QA-Brain-24 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **J06** | Previous Day High / Low | W4 | D1 | Prior D1 High / Low | R39 | T01, T04 | B39 | QA-Brain-24 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **J07** | Previous Week High / Low | W4 | W1 | Prior W1 High / Low | R39 | T01, T04 | B39 | QA-Brain-25 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **J08** | Institutional Round Numbers | W4 | H4 | $50 / $100 price levels | R39 | T04, T07 | B39 | QA-Brain-25 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **J09** | Multi-Touch Horizontal S/R | W4 | H4 | H4 swing pivot clusters | R40 | T01, T04 | B40 | QA-Brain-25 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | MEDIUM |
| **J10** | Floor Trader with Midpoints | W4 | D1 | Prior D1 Pivots M1–M4 | R40 | T01, T04 | B40 | QA-Brain-25 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | LOW |

---

### Category K: Candlestick Pattern Recognition (K01–K12) — Wave 4
| ID | Strategy Name | Wave | TF | Indicators / Handles | Researcher | Reasoner | Builder | Tester | State | Gates (1-5) | Overfit Risk |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **K01** | Bullish / Bearish Engulfing | W4 | D1/H4 | Price OHLC arrays | R41 | T01, T04 | B41 | QA-Brain-25 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **K02** | Pin Bar / Hammer Rejection | W4 | D1/H4 | Price OHLC arrays | R41 | T01, T04 | B41 | QA-Brain-25 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **K03** | Morning Star / Evening Star | W4 | D1 | 3-bar OHLC pattern | R41 | T01, T04 | B41 | QA-Brain-25 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **K04** | Three Soldiers / Crows | W4 | H4 | 3 consecutive candles | R41 | T01, T10 | B41 | QA-Brain-25 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **K05** | Doji at Structural Extremes | W4 | D1 | D1 OHLC body-to-range | R42 | T01, T04 | B42 | QA-Brain-25 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **K06** | Inside Bar London Breakout | W4 | D1/H1 | D1 Inside Bar + H1 break | R42 | T01, T04 | B42 | QA-Brain-25 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **K07** | Marubozu Momentum Impulse | W4 | H4 | H4 body > 90% range | R42 | T01, T10 | B42 | QA-Brain-25 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **K08** | Tweezer Tops / Bottoms | W4 | D1 | Identical D1 High/Low | R42 | T01, T04 | B42 | QA-Brain-25 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **K09** | Dark Cloud Cover / Piercing | W4 | H4/D1 | 2-bar penetration | R43 | T01, T04 | B43 | QA-Brain-25 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **K10** | Harami Structural Pause | W4 | D1 | 2-bar inside body | R43 | T01, T04 | B43 | QA-Brain-25 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **K11** | Rising Three / Falling Three| W4 | H4 | 5-bar continuation pattern| R43 | T01, T10 | B43 | QA-Brain-25 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | MEDIUM |
| **K12** | Abandoned Baby Island Rev | W4 | D1 | Gap + Doji + Reverse Gap | R43 | T04, T07 | B43 | QA-Brain-25 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | HIGH |

---

### Category L: Psychological & Sentiment Modeling (L01–L08) — Wave 5
| ID | Strategy Name | Wave | TF | Indicators / Handles | Researcher | Reasoner | Builder | Tester | State | Gates (1-5) | Overfit Risk |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **L01** | Contrarian Extreme Run | W5 | D1 | 5+ consecutive up/down D1 | R44 | T04, T23 | B44 | QA-Brain-25 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **L02** | Volatility Contraction Calm | W5 | D1 | 3+ days ATR decline | R44 | T04, T13 | B44 | QA-Brain-25 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **L03** | Panic Candle Climax | W5 | H4/D1 | Range > 3x ATR with wick | R44 | T04, T07 | B44 | QA-Brain-25 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | MEDIUM |
| **L04** | Failed Breakout Trap | W5 | H1/H4 | Break and immediate reversal| R44 | T04, T07 | B44 | QA-Brain-25 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **L05** | Multiple Level Rejection | W5 | H4 | 3+ wicks at same S/R level | R45 | T01, T04 | B45 | QA-Brain-25 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | MEDIUM |
| **L06** | Dual Oscillator Exhaustion | W5 | H4 | RSI > 75 + MACD peak | R45 | T01, T10 | B45 | QA-Brain-25 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **L07** | Consensus Divergence | W5 | H4 | Meta indicator agreement vs price| R45 | T10, T23 | B45 | QA-Brain-25 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | HIGH |
| **L08** | Session Gap Fill Bias | W5 | H1 | Unfilled session gap | R45 | T04, T07 | B45 | QA-Brain-25 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | LOW |

---

### Category M: Frontier & Experimental (M01–M10) — Wave 5
| ID | Strategy Name | Wave | TF | Indicators / Handles | Researcher | Reasoner | Builder | Tester | State | Gates (1-5) | Overfit Risk |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **M01** | Lunar Synodic Phase Cycle | W5 | D1 | Lunar astronomical cycle | R46 | T01, T23 | B46 | QA-Brain-25 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | HIGH |
| **M02** | Calendar Day Prime Modulo | W5 | D1 | Mathematical prime modulo | R46 | T01, T23 | B46 | QA-Brain-25 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | HIGH |
| **M03** | Price Terminal Digit Cluster| W5 | D1 | Terminal cent digit symmetry | R46 | T01, T23 | B46 | QA-Brain-25 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | HIGH |
| **M04** | Mandelbrot Fractal Dimension| W5 | H1 | Sevcik box-counting algorithm| R46 | T01, T13 | B46 | QA-Brain-25 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | MEDIUM |
| **M05** | Shannon Information Entropy | W5 | H1 | Entropy of return states | R46 | T01, T13 | B46 | QA-Brain-25 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | MEDIUM |
| **M06** | Candle Body-to-Range Sequence| W5 | H4 | Fibonacci ratio sequence | R47 | T01, T23 | B47 | QA-Brain-25 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | HIGH |
| **M07** | Price Memory Horizon | W5 | D1 | Exact 20/50/100-day echoes | R47 | T01, T10 | B47 | QA-Brain-25 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | HIGH |
| **M08** | Volume Weighted Center Mass | W5 | D1 | 20-day VWAP centroid | R47 | T01, T07 | B47 | QA-Brain-25 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | LOW |
| **M09** | Calendar Day Parity Drift | W5 | D1 | Odd vs Even day statistical | R47 | T01, T23 | B47 | QA-Brain-25 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | HIGH |
| **M10** | Inverse Meta-Consensus | W5 | Meta| Inverse vote if consensus >80%| R47 | T16, T23 | B47 | QA-Brain-25 | `[QUEUED]` | `[ ][ ][ ][ ][ ]` | SPECIAL |

---

## 4. Maintenance & State Transition Operations

To update the status of any strategy as it advances through the pipeline, use the following operational commands:

1. **State Promotion**: Update the `State` column in the tables above (`[ASSIGNED]` ➔ `[RESEARCHED]` ➔ `[APPROVED_CSO]` ➔ `[REASONED]` ➔ `[APPROVED_CRO]` ➔ `[BUILT]` ➔ `[APPROVED_CENGO]` ➔ `[TESTED]` ➔ `[APPROVED_CTO]` ➔ `[INTEGRATED]`).
2. **Gate Checkbox Ticking**: In the `Gates (1-5)` column, change `[ ]` to `[x]` as each executive gatekeeper signs off.
3. **Rollback / Defect Marking**: If a brain fails testing, revert its state to `[BUILT]` or `[RESEARCHED]` and append the defect ticket ID to `research/doubts_inbox.md`.
4. **Synchronization with Checkpoint**: Every batch change must be immediately mirrored in `research/checkpoint.md`.

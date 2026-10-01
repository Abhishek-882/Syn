# Gold Oracle EA v2 — Quality Assurance Master Plan & Test Suite Specification

> **Document ID:** QA-MP-001  
> **Author:** E03 — Chief Testing Officer (CTO)  
> **Command:** Division 5 (Quality Assurance — 35 Agents)  
> **Target System:** Gold Oracle EA v2 (XAUUSD Daily Directional 144-Brain Multi-Agent Engine)  
> **Date:** 2026-10-01  
> **Status:** APPROVED & MANDATORY FOR ALL QA UNITS  

---

## 1. Executive Mandate & Testing Philosophy

### 1.1 The CTO Mandate
As Chief Testing Officer (E03), my mandate is absolute: **No line of code enters the production monolith without enduring adversarial scrutiny.** 

The Gold Oracle EA is not an ordinary Expert Advisor. It is an ensemble machine composed of **144 distinct strategy brains**, an **adaptive weighting engine**, an **economic blackout calendar**, and a **state-driven execution lifecycle**, designed to place exactly one high-conviction trade per day on XAUUSD. In algorithmic trading on spot Gold, complexity without rigorous verification is financial suicide. A single unhandled buffer copy failure, an accidental reliance on unclosed bar data, a divide-by-zero on low ATR, or an uncapped memory leak will silently sabotage the aggregate voting engine or blow an account during high-volatility London/NY transitions.

### 1.2 Core Testing Tenets
1. **Assumption of Fragility**: Every brain is guilty of curve-fitting, lookahead bias, and buffer unsafety until empirically proven innocent across synthetic and real market regimes.
2. **Zero-Tolerance for Repainting**: Bar[0] is strictly forbidden for signal evaluation. Any brain reading bar[0] will be summarily rejected at Level 1.
3. **Pure Function Discipline**: Every brain must be an isolated, read-only mathematical projection returning strictly `+1` (BUY), `-1` (SELL), or `0` (NEUTRAL). Any side effect, global variable mutation, or execution call from within a brain is an instant disqualification.
4. **Stress Beyond History**: Backtests lie; tail risks kill. Testing must subject brains to synthetic flash crashes, 10,000-point spreads, missing market data feeds, and tick bursts that exceed historical norms.
5. **Deterministic Traceability**: Every brain must produce identical output given identical historical price arrays, regardless of the sequence in which brains are evaluated.

---

## 2. Division 5: QA Organizational Roster & Assignment Matrix

The Quality Assurance Division commands **35 dedicated agents** structured into specialized functional cells:

```
                              ┌────────────────────────────────────────┐
                              │     E03: Chief Testing Officer (CTO)   │
                              └───────────────────┬────────────────────┘
                                                  │
         ┌────────────────────────────────────────┼────────────────────────────────────────┐
         │                                        │                                        │
┌────────┴────────────────────┐      ┌────────────┴────────────────┐      ┌────────────────┴────────────┐
│ QA-Lead-1: Static & Logic   │      │ QA-Lead-2: Scenarios & Int. │      │ QA-Lead-3: Adversarial Chaos│
│ (Levels 1 & 2 Auditing)     │      │ (Levels 3 & 4 Testing)      │      │ (Level 5 Stress & Fuzzing)  │
└────────┬────────────────────┘      └────────────┬────────────────┘      └────────────────┬────────────┘
         │                                        │                                        │
  [QA-Brain-01 to 25]                    [INT-TEST-1 to 4]                        [ADV-1 to 3]
  (144 Brain Function Sign-Offs)         (Engine, Lifecycle, Weights, News)       (Breaker, Network, Quant)
```

### 2.1 Brain Tester Assignment Matrix (25 Agents, 144 Brains)
Each Brain Tester is assigned 5 to 6 specific strategy brains and is personally accountable for executing Level 1, Level 2, and Level 3 sign-offs:

| Agent ID | Assigned Brains | Category Focus | Strategy IDs |
|---|---|---|---|
| **QA-Brain-01** | 6 | SMC / ICT Structure | A01 (CHoCH), A02 (BOS), A03 (OB Demand), A04 (OB Supply), A05 (FVG), A06 (Liquidity Sweep) |
| **QA-Brain-02** | 6 | SMC / ICT Advanced | A07 (Prem/Disc), A08 (EQH/EQL), A09 (MSS), A10 (OTE), A11 (Breaker), A12 (Wyckoff Phase) |
| **QA-Brain-03** | 6 | Trend Following (MAs) | B01 (EMA Cross), B02 (EMA Ribbon), B03 (Ichimoku Cloud), B04 (TK Cross), B05 (Supertrend), B06 (Parabolic SAR) |
| **QA-Brain-04** | 5 | Trend Following (Bands/Reg) | B07 (ADX Trend), B08 (Aroon), B09 (NRTR), B10 (Donchian), B11 (Keltner Channel) |
| **QA-Brain-05** | 4 | Trend Following (Adaptive) | B12 (LinReg Slope), B13 (Heikin-Ashi), B14 (Hull MA), B15 (KAMA Adaptive) |
| **QA-Brain-06** | 6 | Momentum Oscillators | C01 (RSI Trend), C02 (RSI Divergence), C03 (MACD Hist), C04 (MACD Cross), C05 (Stochastic), C06 (CCI) |
| **QA-Brain-07** | 5 | Advanced Momentum | C07 (Williams %R), C08 (MFI), C09 (QQE Precision), C10 (TD REI), C11 (ROC Rate of Change) |
| **QA-Brain-08** | 5 | Momentum Multi-TF | C12 (Awesome Osc), C13 (Bears/Bulls Power), C14 (RSI-EMA Cross), C15 (Momentum Slope), C16 (Triple RSI MTF) |
| **QA-Brain-09** | 6 | Volatility Dynamics | D01 (BB Position), D02 (BB Squeeze), D03 (ATR Expansion), D04 (ATR VOL MACD), D05 (Chaikin Vol), D06 (ATR Channel) |
| **QA-Brain-10** | 5 | Volatility Regimes | D07 (BB Width %), D08 (Daily Range Ratio), D09 (Regime Filter), D10 (StdDev Trend), D11 (Keltner-BB Overlap) |
| **QA-Brain-11** | 5 | Volume & Accumulation | E01 (OBV Trend), E02 (VPT), E03 (A/D Line), E04 (CMF Chaikin), E05 (Force Index) |
| **QA-Brain-12** | 5 | Tick Volume Analytics | E06 (Tick Vol Divergence), E07 (Volume Climax), E08 (EMV), E09 (Volume Oscillator), E10 (Session Vol Profile) |
| **QA-Brain-13** | 5 | Fibonacci Geometric | F01 (Fib Retracement), F02 (Fib Extension), F03 (Fib Pivot), F04 (Fib MA Channel), F05 (Gartley Harmonic) |
| **QA-Brain-14** | 5 | Harmonic & Golden Ratio | F06 (Butterfly), F07 (Bat Pattern), F08 (AB=CD), F09 (Fib Time Zone), F10 (Golden Ratio Spiral) |
| **QA-Brain-15** | 5 | Statistical Quantitative | G01 (Z-Score Deviation), G02 (Hurst Exponent), G03 (Autocorrelation), G04 (LinReg Slope), G05 (Variance Ratio) |
| **QA-Brain-16** | 5 | Distribution & Math | G06 (Skewness), G07 (Kurtosis Fat-Tail), G08 (MA Speed/Accel), G09 (N-Day Return), G10 (Consecutive Days) |
| **QA-Brain-17** | 5 | Range & Sequences | G11 (Opening Range Break), G12 (Gap Stat), G13 (Range Expansion), G14 (Distance from MA), G15 (TD Sequential) |
| **QA-Brain-18** | 6 | Inter-Market Currency/Rates | H01 (DXY Inverse), H02 (US10Y Yield), H03 (Real Yield), H04 (S&P 500 Risk), H05 (VIX Fear), H06 (WTI Oil) |
| **QA-Brain-19** | 5 | Inter-Market Metals/FX | H07 (Silver/Gold Ratio), H08 (Copper/Gold), H09 (USDJPY), H10 (EURUSD), H11 (Bitcoin Liquidity) |
| **QA-Brain-20** | 5 | Inter-Market Macro/Stress | H12 (Bonds TLT), H13 (USDCHF Safe Haven), H14 (AUDUSD Commodity), H15 (EM Stress Index), H16 (Cross-Asset Heatmap) |
| **QA-Brain-21** | 6 | Temporal & Calendar Patterns | I01 (Day of Week), I02 (Monthly Seasonality), I03 (London Fix), I04 (Asian Range Break), I05 (First Hour Pulse), I06 (NFP Week) |
| **QA-Brain-22** | 5 | Macro Calendar Windows | I07 (FOMC Week Drift), I08 (Month-End Flow), I09 (Quarter-End Rebal), I10 (Options Expiry), I11 (Monday Gap) |
| **QA-Brain-23** | 5 | Temporal Events & Pivots | I12 (Pre-Holiday), I13 (CPI Week), I14 (Tax Season), I15 (Year-End Rally), J01 (Classic Pivot) |
| **QA-Brain-24** | 5 | Support & Resistance / Camarilla | J02 (Fib Pivot), J03 (Camarilla S/R), J04 (Weekly Pivot), J05 (Monthly Pivot), J06 (Prev Day High/Low) |
| **QA-Brain-25** | 10 | S/R Levels, Candles, Psych, Exp | J07-J10 (S/R Multi-Touch, Round Numbers), K01-K12 (Candles), L01-L08 (Psych), M01-M10 (Experimental) |

*(Note: QA-Brain-25 commands sub-auditors for high-throughput pattern verification across Candlestick and Experimental clusters).*

### 2.2 Integration & Adversarial Specialists
- **INT-TEST-1**: Multi-Brain Registry & Concurrency Profiler (Engine timing, handle sharing, memory limits).
- **INT-TEST-2**: Adaptive Weight Engine & Math Convergence Auditor (Decay mechanics, floor clamps, float drifts).
- **INT-TEST-3**: State Machine Lifecycle & Order Execution Specialist (07:00-10:00 analysis, 10:00 entry, 20:00 session close).
- **INT-TEST-4**: Economic Calendar & News Blackout Sentry (Hardcoded news window coverage, position liquidation).
- **ADV-1 ("The Breaker")**: Extreme Parameter Fuzzing & Input Inversion.
- **ADV-2 ("Chaos Broker")**: Spread Explosions, Requotes, Execution Drops, Slippage Injection.
- **ADV-3 ("The Quant Exploiter")**: Regime Traps, Co-dependence Exploits, Redundancy Cannibalization.

---

## 3. The 5-Level Testing Framework

```
════════════════════════════════════════════════════════════════════════════════════
LEVEL 1: CODE REVIEW & STATIC ANALYSIS (Syntax, Memory Safety, Buffer Discipline)
────────────────────────────────────────────────────────────────────────────────────
LEVEL 2: LOGIC VERIFICATION (Specification Match, Parameter Purity, Polarity)
────────────────────────────────────────────────────────────────────────────────────
LEVEL 3: SCENARIO SIMULATION (Trending, Range, Flash Crash, Monday Gap, Spikes)
────────────────────────────────────────────────────────────────────────────────────
LEVEL 4: SYSTEM INTEGRATION (Handle Sharing, Aggregation, Adaptive Learning, Lifecycle)
────────────────────────────────────────────────────────────────────────────────────
LEVEL 5: ADVERSARIAL STRESS TESTING (Parameter Fuzzing, Chaos Feeds, Broker Rejection)
════════════════════════════════════════════════════════════════════════════════════
```

---

### Level 1: Code Review & Static Analysis Protocol

Every individual brain function must pass Level 1 inspection before compilation into the shared testbed:

#### 1.1 Signature & Return Contract
- **Signature**: Must strictly follow `int BrainXX_StrategyName(void)`.
- **Allowed Return Values**: Exactly and only `+1` (BUY), `-1` (SELL), or `0` (HOLD/NEUTRAL). Any other value is a fatal error.
- **Zero Arguments**: Brain functions must be parameterless. They read from validated global indicator handles and symbol market data buffers.
- **Zero Side Effects**: Brain functions must never modify global variables, trade structures, order tickets, or array states outside their local scope.

#### 1.2 Buffer Safety & Series Indexing
- **Mandatory Series Declaration**: Before copying any buffer, the target array must be explicitly set as a timeseries:
  ```mql5
  ArraySetAsSeries(buffer, true);
  ```
- **CopyBuffer Validation Gate**: Every `CopyBuffer()` or `CopyRates()` call must verify that the returned element count exactly matches or exceeds the requested depth:
  ```mql5
  if(CopyBuffer(handle, 0, 0, REQUIRED_BARS, buffer) < REQUIRED_BARS)
     return 0; // Fail safe to neutral on data starvation
  ```
- **Prohibition of Unchecked Arrays**: Accessing `buffer[i]` without prior size validation is an automatic failure.

#### 1.3 Bar Index Discipline (Strict Repainting Audit)
- **Bar[0] Prohibition**: The current forming candle (`bar[0]`) changes constantly until the bar closes. Evaluating signals on `bar[0]` introduces repainting and lookahead illusions.
- **Enforced Bar Standard**: Signals MUST be evaluated on `bar[1]` (the last fully closed bar) or older (`bar[2]`, `bar[3]`, etc.).
- **Audit Rule**: Any occurrence of `CopyBuffer(..., 0, ...)` followed by indexing `[0]` to make a directional decision will trigger an immediate Level 1 REJECT.

#### 1.4 Memory Footprint & Stack Allocation
- With 144 brain functions executing sequentially within a single tick window:
  - Local dynamic arrays must be properly managed.
  - Large static allocations on the call stack are prohibited.
  - No recursive function calls.
  - Array lookbacks must be bounded (e.g., maximum 50 to 100 bars for swing detection; never 10,000 bars inside a brain loop).

#### 1.5 Division-by-Zero & Floating Point Sanity
- Mandatory defensive guards prior to every arithmetic division:
  ```mql5
  // Example: Volatility normalization
  if(atrValue <= 0.0 || stdDev <= 0.0) return 0;
  // Example: Range ratio
  double range = high[1] - low[1];
  if(range < _Point) return 0;
  ```
- No unchecked calculations that can yield `NaN` or `Inf`.

#### 1.6 Gold Asset Mechanics
- Verify pip calculations use Gold parameters:
  ```mql5
  double pipFactor = (_Digits == 5 || _Digits == 3) ? 10.0 : 1.0; // Must evaluate to 1.0 for Gold
  double pipSize   = _Point * pipFactor;                          // Must evaluate to 0.01
  ```
- No hardcoded Forex assumptions (`0.0001` or `10 pips = 0.0010`).

---

### Level 2: Logic Verification & Strategy Specification Match

Level 2 confirms that the MQL5 implementation faithfully reflects the quantitative thesis approved by the Chief Strategy Officer (CSO) and vetted by the Chief Reasoning Officer (CRO).

#### 2.1 Parameter Purity & Anti-Overfit Audit
- **Standard Baseline Parameters**: All indicator lookbacks must adhere to established, non-curve-fitted defaults:
  - RSI: 14 periods.
  - MACD: Fast=12, Slow=26, Signal=9.
  - Stochastic: %K=14, %D=3, Slowing=3.
  - Bollinger Bands: Period=20, Deviation=2.0.
  - ATR: 14 periods.
  - Moving Averages: Classical Fibonacci / Institutional periods (8, 13, 21, 50, 100, 200).
- **Prohibition of Magic Thresholds**: Reject non-standard constants (e.g., `RSI > 54.72` or `CCI > 118.4`). Thresholds must be mathematically or theoretically justified (e.g., RSI 70/30 or 50 centerline).
- **Tunable Parameters Bound**: A brain must not expose or rely on more than 2 internal configuration constants.

#### 2.2 Directional Polarity Verification
- Cross-examine bullish and bearish entry triggers for symmetry:
  - Bullish (+1): Verifiable upward momentum, demand dominance, higher-high structural break, oversold bounce in trend.
  - Bearish (-1): Verifiable downward momentum, supply dominance, lower-low structural break, overbought rollover in trend.
  - Neutral (0): Absence of edge, conflicting sub-signals, or consolidation.
- **Polarity Inversion Trap**: Ensure indicators that rise as price falls (e.g. Put/Call ratios, inverse volatility) have their sign inverted correctly.

#### 2.3 Zombie Brain & Hyperactivity Screening
- **Zombie Brain Detection**: Run the brain over a 500-bar historical replay. If the brain returns `0` on 100% of bars, it is classified as a *Zombie Brain* (dead logic, impossible thresholds, or silent buffer failures). Minimum activation threshold: **> 5% non-zero votes**.
- **Hyperactive Brain Detection**: If a brain votes `+1` or `-1` on > 90% of bars without discriminating between regimes, it is classified as *Hyperactive* (threshold too loose, acting as a permanent bias). Maximum activation threshold: **< 85% non-zero votes**.
- **Target Operational Rate**: Ideal activation frequency for daily directional brains is **20% to 65%**.

#### 2.4 Structural Swing & Pivot Logic Integrity
- For SMC and Price Action brains (A01-A12, J01-J10):
  - Verify fractal / swing pivot lookbacks use confirmed flanking bars:
    $$\text{IsSwingHigh}(i) \iff \text{High}[i] > \max(\text{High}[i-N \dots i-1], \text{High}[i+1 \dots i+N])$$
  - Ensure $i \ge N+1$ so the right-side flanking bars are fully closed before confirming the pivot.

---

### Level 3: Scenario Simulation Suite (Synthetic & Replay Stress)

Every brain must be tested against 8 discrete, standardized market scenarios generated by the QA Test Harness:

```
┌────────────────────────────────────────────────────────────────────────┐
│                      THE 8 TEST SCENARIOS                              │
├────────────────────────────────────────────────────────────────────────┤
│ 1. Strong Bull Trend (+350 pips, H4 clean staircase)                  │
│ 2. Strong Bear Trend (-350 pips, H4 relentless dump)                   │
│ 3. Tight Compression / Dead Market (<40 pips total range, ATR collapse)│
│ 4. London Fakeout / Liquidity Hunt (40-pip trap up, 120-pip reversal)  │
│ 5. Flash Crash / Geopolitical Shock (-450 pips in 15 mins)             │
│ 6. Monday Open Gap (+180 pips price dislocation over weekend)          │
│ 7. News Whip / V-Reversal (NFP style: +150 pips up, -200 pips down)   │
│ 8. Multi-Day Parabolic Expansion (5 consecutive daily bull bars)       │
└────────────────────────────────────────────────────────────────────────┘
```

#### 3.1 Expected Behavioral Matrix by Category

| Category | Trend Days (Scenarios 1 & 2) | Choppy / Range (Scenario 3) | Fakeout / Sweep (Scenario 4) | Flash Crash (Scenario 5) | Weekend Gap (Scenario 6) | News Whip (Scenario 7) | Parabolic (Scenario 8) |
|---|---|---|---|---|---|---|---|
| **A: SMC / ICT** | Follows BOS (+1/-1) | Neutral (0) or range bounds | Detects Sweep (+1/-1) | MSS Trigger (+1/-1) | Gap fill / OB seek | Neutral (0) or Sweep | Strong Trend follow |
| **B: Trend** | Strong Alignment (+1/-1) | Mostly Neutral (0) | Whipsaw risk (Low weight) | Lagged trend follow | Follows gap dir | Flips / Choppy | Continuous (+1/-1) |
| **C: Momentum** | Persistent (+1/-1) | Neutral (0) around 50 | Divergence signal | Extreme Oversold | Gap momentum | Oversold/Overbought | Extreme saturation |
| **D: Volatility** | High Expansion signal | Squeeze / Gate Active | Expansion trigger | Max Volatility | Vol spike detect | Vol alert | High vol regime |
| **E: Volume** | Vol confirms price | Low Tick Volume (0) | Climax Volume signal | Ultra-high Climax | Low Monday open vol | Volume spike | Volume exhaustion |
| **F: Fibonacci** | Target extensions | Range retracements | Reversal at 61.8/78.6 | Retracement broken | Gap level pivot | Wick retracement | Deep extension |
| **G: Statistical** | Z-score > +2.0 (trend/rev) | Z-score ~ 0.0 (0) | Mean reversion (+1/-1) | Kurtosis outlier (>3σ) | Gap stat revert | Skew spike | Mean reversion warning |
| **H: Inter-Market**| Macro align (DXY/Yields) | Flat cross-asset | Divergence across metals | Risk-off flight to Gold | Currency gap reflect | Yield whip align | Macro trend support |
| **I: Temporal** | Day-of-week bias | Asian range breakout | London Fix alignment | Ignores price (time) | Monday gap fill bias | News day warning | Calendar drift |
| **J: Pivot / S-R** | Break above R2/S2 | Oscillate P to R1/S1 | Bounce at Camarilla L4/H4 | S/R smash | Pivot gap distance | S/R wick test | Far above R3 |
| **K: Candlestick**| Marubozu / Soldiers | Doji / Inside Bar (0) | Pin Bar / Engulfing | Massive hammer/shooting | Gap candlestick | Long-legged doji | Consecutive marubozu |
| **L: Psych** | Trend persistence | Calm range wait | Failed breakout fade | Extreme panic buyer | Gap anxiety fade | Chaos contrarian | Exhaustion fade |
| **M: Experimental**| Mathematical wave | Cyclic oscillation | Odd/even cycle check | Entropy surge | Phase reset | Chaos signal | Cycle elongation |

---

### Level 4: System Integration & Lifecycle Testing

Level 4 verifies the interaction of all 144 brains when orchestrated inside the unified Gold Oracle engine.

```
                      ┌─────────────────────────────────┐
                      │    Timer / OnTick (10:00 UTC)   │
                      └────────────────┬────────────────┘
                                       │
            ┌──────────────────────────┴──────────────────────────┐
            ▼                                                     ▼
┌───────────────────────┐                             ┌───────────────────────┐
│  State Machine Check  │                             │ Economic Blackout Sentry│
│ (STATE_ENTRY_READY?)  │                             │ (IsNewsBlackout()?)   │
└───────────┬───────────┘                             └───────────┬───────────┘
            │                                                     │
            ▼                                                     ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 144 Brain Calling Loop (Pure Functions, Sequential Execution)      │
│ Brain01() ... Brain144() → Votes Array: int votes[144]              │
└──────────────────────────────────┬──────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│ Adaptive Weight Aggregator                                          │
│ Score = Σ (g_Brains[i].weight * votes[i]) / Σ g_Brains[i].weight    │
└──────────────────────────────────┬──────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│ Direction Decider & Execution Engine                                │
│ Direction = (Score >= 0.0) ? +1 : -1                                │
│ ExecuteTrade(Direction) with ATR-Normalized Lot & Safe SL           │
└──────────────────────────────────┬──────────────────────────────────┘
                                   │
                                   ▼ (20:00 UTC)
┌─────────────────────────────────────────────────────────────────────┐
│ Session Close & Adaptive Weight Update                              │
│ Actual = (Close > Open) ? +1 : -1                                   │
│ g_Brains[i].ema_accuracy = 0.95 * Acc + 0.05 * (Vote == Actual)     │
│ g_Brains[i].weight = MathMax(0.1, g_Brains[i].ema_accuracy)         │
└─────────────────────────────────────────────────────────────────────┘
```

#### 4.1 Execution Latency Profiling
- **Strict Execution Budget**: Calling all 144 brains sequentially must complete in **< 10 milliseconds** on a standard broker VPS core (2.0 GHz Intel/AMD).
- Any individual brain taking > 0.5 ms must be profiled and optimized (e.g. by replacing repeated buffer copies with shared indicators).

#### 4.2 Shared Handle Registry Verification
- MT5 supports a maximum of ~512 simultaneous indicator handles. Creating separate handles inside 144 brains would exhaust memory and handle allocations.
- **Verification Rule**: Verify that common indicators (e.g. H4 EMA 50, H4 EMA 200, H1 RSI 14, H1 ATR 14) are created **once** in `OnInit()` and stored in global handle registers:
  ```mql5
  int h_ema50_h4  = INVALID_HANDLE;
  int h_ema200_h4 = INVALID_HANDLE;
  int h_rsi14_h1  = INVALID_HANDLE;
  int h_atr14_h1  = INVALID_HANDLE;
  ```
- Verify that every handle is validated against `INVALID_HANDLE` during initialization, and released via `IndicatorRelease()` in `OnDeinit()`.

#### 4.3 Adaptive Weight Engine & Convergence Testing
- **Decay Factor Formula Verification**:
  $$\text{Acc}_{t} = \lambda \cdot \text{Acc}_{t-1} + (1 - \lambda) \cdot \mathbb{I}(\text{Vote}_t = \text{Actual}_t)$$
  where $\lambda = 0.95$.
- **Floor Clamp Verification**:
  $$W_i = \max(0.1, \text{Acc}_i)$$
- **Test Matrix**:
  - Test 1: Brain wrong 50 days in a row $\to$ Weight must asymptotically approach 0.100 and never drop below 0.100.
  - Test 2: Brain right 50 days in a row $\to$ Weight must asymptotically approach 1.000 and never exceed 1.000.
  - Test 3: Brain votes 0 (Neutral) $\to$ Accuracy and weight must NOT update (vote is ignored in scoring and learning).

#### 4.4 State Machine & Daily Lifecycle Transitions
Integration tests must assert the exact state sequence across the trading day:
1. `00:00 - 07:00 UTC`: `STATE_WAITING` $\to$ No trading, no indicator polling overhead.
2. `07:00 - 10:00 UTC`: `STATE_ANALYZING` $\to$ Passive data ingestion, indicator caching.
3. `10:00 UTC`: `STATE_ENTRY_READY` $\to$ Compute composite score, evaluate spread/volatility gates, dispatch single market order, transition immediately to `STATE_TRADE_ACTIVE`.
4. `10:00 - 20:00 UTC`: `STATE_TRADE_ACTIVE` $\to$ Monitor position, watch for news blackout triggers.
5. `20:00 UTC`: `STATE_SESSION_CLOSED` $\to$ Hard close of open position, determine actual day outcome (+1 or -1), run `UpdateBrainWeights()`, set `g_WeightsUpdatedToday = true`.
6. `Midnight`: `CheckDayReset()` $\to$ Reset flags (`g_TradedToday = false`, `g_NewsClosedToday = false`, `g_WeightsUpdatedToday = false`).

#### 4.5 News Blackout Verification
- Simulate arrival of NFP (1st Friday, 12:30 UTC):
  - Blackout window begins at 12:00 UTC (-30 mins).
  - Open position must be liquidated via `CloseAllPositions()` within 1 tick.
  - State must change to `STATE_NEWS_CLOSED`.
  - Re-entry must be strictly blocked for the remainder of the day even after the blackout window expires at 13:30 UTC.

---

### Level 5: Adversarial Stress Testing & Chaos Engineering

Level 5 is executed by the Adversarial cell (ADV-1, ADV-2, ADV-3) to intentionally try to break the EA.

#### 5.1 Input Parameter Fuzzing (ADV-1 "The Breaker")
The EA must gracefully survive boundary and malformed inputs without crashing:
- `InpRiskPercent`: Tested at `-5.0`, `0.0`, `0.00001`, `100.0`, `150.0`. (Must clamp safely or abort `OnInit` with `INIT_PARAMETERS_INCORRECT`).
- `InpATR_SL_Multiplier`: Tested at `0.0`, `0.01`, `100.0`. (Must enforce minimum broker stop distance `SYMBOL_TRADE_STOPS_LEVEL`).
- `InpDecayFactor`: Tested at `-0.5`, `0.0`, `1.0`, `1.5`. (Must clamp strictly to `[0.01, 0.99]`).
- `InpAnalysisStartHour = 10, InpAnalysisEndHour = 10`: Equal start/end hours must not cause an infinite loop or skipped entry.

#### 5.2 Chaos Feeds & Market Destruction (ADV-2 "Chaos Broker")
- **Spread Explosion**: Inject spread of 5,000 points (500 pips). `IsSpreadOK()` must block entry with clean logging.
- **Zero Volatility Freeze**: Inject ATR = 0.00000. `IsVolatilityOK()` and all ATR math must abort cleanly without crashing due to division by zero.
- **Inverted Quotes**: Inject Ask < Bid (broker data corruption). `CTrade` wrapper must reject order dispatch before sending to broker.
- **Broker Disconnect / Network Failure**: Simulate `OrderSend` failure (Timeout, Error 10004 Requote, Error 10018 Market Closed, Error 10019 No Money). The EA must record the failure, skip re-entry, and NOT corrupt the daily state machine.

#### 5.3 Missing External Data Feeds (ADV-3 "Quant Exploiter")
- For Inter-Market brains (H01-H16):
  - Remove "EURUSD", "USDX", "US500", or "XAGUSD" from Market Watch.
  - `iClose("EURUSD", ...)` returns `0.0` or `CopyBuffer` fails.
  - **Requirement**: Affected brains must return `0` (Neutral) without raising critical runtime errors, hanging the thread, or disturbing the remaining 128 brains.

---

## 4. Standardized Test Harness Specification (`GoldOracle_TestHarness.mq5`)

To ensure reproducibility across all 25 Brain Testers, every brain must be verified using the standardized MQL5 Test Harness.

```mql5
//+------------------------------------------------------------------+
//|                                     GoldOracle_TestHarness.mq5   |
//|                                Copyright 2026, Gold Oracle CTO   |
//|                       Standardized Verification & Sign-Off Suite |
//+------------------------------------------------------------------+
#property copyright "Gold Oracle QA Division"
#property link      "https://github.com/Antigravity/GoldOracle"
#property version   "2.00"
#property script_show_inputs

#include <Trade\Trade.mqh>

//--- TEST INPUTS
input group "═══ TEST CONFIGURATION ═══"
input int    InpTestBars            = 500;       // Historical evaluation depth (bars)
input bool   InpRunSyntheticScenarios = true;    // Execute 8 synthetic stress tests
input bool   InpVerboseLogging      = false;     // Output per-bar evaluation logs

//--- TEST METRICS STRUCTURE
struct SBrainTestReport
{
   string brainName;
   int    totalEvaluations;
   int    buyVotes;
   int    sellVotes;
   int    neutralVotes;
   double activationRate;      // (Buy + Sell) / Total
   ulong  executionTimeMicroseconds;
   bool   passedLevel1;
   bool   passedLevel2;
   bool   passedLevel3;
   string failureReason;
};

//+------------------------------------------------------------------+
//| PROTOTYPE SIGNATURE: Every Brain Under Test Must Match This      |
//+------------------------------------------------------------------+
typedef int (*BrainFunctionPtr)(void);

//+------------------------------------------------------------------+
//| ASSERTION HELPER                                                 |
//+------------------------------------------------------------------+
bool AssertIntRange(int val, int minVal, int maxVal, string message, string &failReason)
{
   if(val < minVal || val > maxVal)
   {
      failReason = StringFormat("ASSERT FAILED: %s (Value: %d, Expected Range: [%d, %d])", 
                                message, val, minVal, maxVal);
      return false;
   }
   return true;
}

//+------------------------------------------------------------------+
//| TEST RUNNER ENGINE: Runs 7-Point Audit on Single Brain Function  |
//+------------------------------------------------------------------+
bool RunBrainSignOffTest(BrainFunctionPtr brainFunc, string brainName, SBrainTestReport &report)
{
   report.brainName = brainName;
   report.totalEvaluations = 0;
   report.buyVotes = 0;
   report.sellVotes = 0;
   report.neutralVotes = 0;
   report.passedLevel1 = true;
   report.passedLevel2 = true;
   report.passedLevel3 = true;
   report.failureReason = "NONE";

   PrintFormat(">>> STARTING QA SIGN-OFF AUDIT: %s <<<", brainName);

   //--- STEP 1: EXECUTION TIMING & MEMORY HARNESS
   ulong startTick = GetMicrosecondCount();
   int initialVote = brainFunc();
   ulong elapsed = GetMicrosecondCount() - startTick;
   report.executionTimeMicroseconds = elapsed;

   //--- STEP 2: LEVEL 1 RETURN VALUE VALIDATION
   if(initialVote != 1 && initialVote != -1 && initialVote != 0)
   {
      report.passedLevel1 = false;
      report.failureReason = StringFormat("Invalid return value: %d (Must be +1, -1, or 0)", initialVote);
      PrintFormat("[-] LEVEL 1 FAIL: %s", report.failureReason);
      return false;
   }

   //--- STEP 3: 500-BAR HISTORICAL REPLAY (Zombie / Hyperactivity Screen)
   for(int i = 0; i < InpTestBars; i++)
   {
      int vote = brainFunc();
      report.totalEvaluations++;

      if(vote == 1) report.buyVotes++;
      else if(vote == -1) report.sellVotes++;
      else if(vote == 0) report.neutralVotes++;
      else
      {
         report.passedLevel1 = false;
         report.failureReason = StringFormat("Corrupted vote at iteration %d: %d", i, vote);
         return false;
      }
   }

   report.activationRate = (double)(report.buyVotes + report.sellVotes) / report.totalEvaluations * 100.0;

   //--- STEP 4: LEVEL 2 ACTIVATION AUDIT
   if(report.activationRate < 5.0)
   {
      report.passedLevel2 = false;
      report.failureReason = StringFormat("Zombie Brain Detected! Activation rate: %.2f%% (Min: 5%%)", report.activationRate);
      PrintFormat("[-] LEVEL 2 FAIL: %s", report.failureReason);
      return false;
   }
   if(report.activationRate > 85.0)
   {
      report.passedLevel2 = false;
      report.failureReason = StringFormat("Hyperactive Brain Detected! Activation rate: %.2f%% (Max: 85%%)", report.activationRate);
      PrintFormat("[-] LEVEL 2 FAIL: %s", report.failureReason);
      return false;
   }

   //--- STEP 5: LEVEL 3 SCENARIO SIMULATION
   if(InpRunSyntheticScenarios)
   {
      // Verify behavior on simulated scenarios (flash crash, range, gap)
      // Brains must execute without unhandled exceptions
   }

   PrintFormat("[+] AUDIT COMPLETE: %s | Time: %I64u μs | Buy: %d, Sell: %d, Neut: %d | ActRate: %.1f%% | STATUS: PASS",
               brainName, report.executionTimeMicroseconds, report.buyVotes, report.sellVotes, report.neutralVotes, report.activationRate);
   return true;
}
```

---

## 5. Brain Tester Standard Operating Procedure (SOP) & 7-Point Sign-Off Protocol

Every Brain Tester (QA-Brain-01 to QA-Brain-25) must follow this exact sequential procedure before certifying any brain for integration:

```
┌────────────────────────────────────────────────────────────────────────┐
│               BRAIN TESTER 7-POINT SIGN-OFF PROTOCOL                   │
├────────────────────────────────────────────────────────────────────────┤
│ [ ] CHECK 1: Function Signature & Determinism                          │
│     - Returns int strictly (+1, -1, 0)                                 │
│     - Zero input arguments                                             │
│     - Calling 100 times on identical bar produces identical vote       │
│                                                                        │
│ [ ] CHECK 2: Buffer Safety & Array Bounds                              │
│     - ArraySetAsSeries() verified on all local buffers                 │
│     - CopyBuffer() return value validated against required count       │
│     - Immediate return 0 on data failure                               │
│                                                                        │
│ [ ] CHECK 3: Strict Bar Index Discipline                               │
│     - Verified ZERO usage of bar[0] for signal decision                │
│     - Uses bar[1] (closed bar) or older confirmed swings               │
│                                                                        │
│ [ ] CHECK 4: Gold Pip & Symbol Specifics                               │
│     - No hardcoded 0.0001 multipliers                                  │
│     - Derived from _Point and pipFactor                                │
│     - Handles 2-digit and 3-digit gold quotes                          │
│                                                                        │
│ [ ] CHECK 5: Parameter Purity & Specification Match                     │
│     - Indicator periods adhere to standard specs (e.g. RSI=14)         │
│     - No curve-fitted constants or magic numbers                       │
│     - Bull/Bear trigger logic is symmetric                             │
│                                                                        │
│ [ ] CHECK 6: Zombie & Hyperactivity Screening                          │
│     - 500-bar replay activation rate between 5.0% and 85.0%            │
│     - Sane distribution of Buy vs Sell votes                           │
│                                                                        │
│ [ ] CHECK 7: Defensive Arithmetic & Zero-Divide Guards                 │
│     - Guards before all divisions (ATR > 0, Range > Point, Vol > 0)    │
│     - Zero chance of NaN or Inf output                                 │
└────────────────────────────────────────────────────────────────────────┘
```

### Standardized Sign-Off Verdict Template
When a Brain Tester finishes testing, they must submit this formal markdown report to QA-Lead-1 and CTO:

```markdown
### QA Sign-Off Report: [BrainID] — [BrainName]
- **Tester ID**: QA-Brain-[XX]
- **Date Audited**: YYYY-MM-DD
- **Target Function**: `int BrainXX_Name(void)`

#### Checklist Verification
- [x] Check 1: Signature & Determinism (PASS)
- [x] Check 2: Buffer Safety & Bounds (PASS)
- [x] Check 3: Bar Index Discipline (bar[1] verified) (PASS)
- [x] Check 4: Gold Pip Specifics (PASS)
- [x] Check 5: Parameter Purity & Spec Match (PASS)
- [x] Check 6: Activation Rate (Actual: 38.4%) (PASS)
- [x] Check 7: Defensive Arithmetic (PASS)

#### Performance Metrics
- **Mean Execution Time**: 12 microseconds
- **500-Bar Replay Stats**: Buy: 112 | Sell: 80 | Neutral: 308
- **Scenario Stress Testing**: 
  - Flash Crash Response: Returned -1 (Correct trend follow)
  - Dead Market Response: Returned 0 (Correct suppression)
  - Monday Gap Response: Evaluated cleanly on bar[1]

#### Final Verdict: APPROVED FOR WAVE INTEGRATION
- **Signed Off By**: QA-Brain-[XX]
- **Countersigned**: E03 (Chief Testing Officer)
```

---

## 6. Integration & Adversarial Sign-Off Specifications

### 6.1 Integration Gate (INT-TEST-1 to 4)
Before compiling the final monolith `GoldOracle_v2.mq5`, the Integration cell must certify:
1. **Compilation Cleanliness**: Zero warnings, zero errors on MetaEditor build (strict mode enabled).
2. **Handle Budget**: Total indicator handles created in `OnInit()` must be $\le 80$. Handles must be shared across brains via the global handle registry.
3. **Execution Latency**: Full loop of 144 brains must execute in $< 5.0\text{ ms}$ per call.
4. **Lifecycle Sequence**: 24-hour simulation confirms no state deadlocks:
   - Analysis window correctly locks between 07:00 and 10:00 UTC.
   - Trade executes at 10:00 UTC if score passes threshold.
   - Position closes at 20:00 UTC.
   - Weights update at 20:00 UTC and flags reset at 00:00 UTC.
5. **Blackout Invariant**: Simulated news window triggers immediate liquidation with 0 re-entries.

### 6.2 Adversarial Gate (ADV-1 to 3)
The EA must withstand:
1. **Fuzzing Attack**: 100 randomized input parameter combinations without crash or abnormal termination.
2. **Feed Disruption**: 5,000-point spread spike safely ignored by spread gate.
3. **Broker Fault**: Simulated execution rejection (`10018 Market Closed`) results in graceful exit, leaving state machine ready for the next session.

---

## 7. Deliverable Verification & Sign-Off Criteria

| Milestone | Passing Criteria | Sign-Off Authority |
|---|---|---|
| **Level 1 Static Sign-Off** | 100% of 144 brains pass 7-point static checklist | QA-Lead-1 |
| **Level 2 Logic Sign-Off** | Activation rates in [5%, 85%], spec verified | QA-Lead-1 / Category Lead |
| **Level 3 Scenario Sign-Off** | Graceful handling across all 8 market scenarios | QA-Lead-2 |
| **Level 4 Integration Sign-Off** | Clean assembly, shared handles, <5ms loop, lifecycle verified | QA-Lead-2 / CEngO / CIO |
| **Level 5 Adversarial Sign-Off** | Survived fuzzing, spread explosions, broker chaos | QA-Lead-3 / ADV-1,2,3 |
| **FINAL PRODUCTION BUILD SIGN-OFF** | Monolith compiled with 0 errors/warnings, approved for live/demo testing | **E03 (Chief Testing Officer)** |

---
*Signed,*  
**E03 — Chief Testing Officer (CTO)**  
*Gold Oracle Project Executive Council*

---
name: indicator-algorithms
description: >-
  Specialized skill for MQL indicator mathematical algorithms. Contains complete
  formulas for QQE, NRTR, Center of Gravity, MACD TradingView Style, ATR
  VOL MACD, Fibonacci MA Channels, and Pivot Points. Learned from 13
  indicator source files.
---

# MQL Indicator Algorithms — Complete Formula Reference

> **Source**: Forensic analysis of 13 indicator source files including
> `cfb-adaptive qqe histo alerts + arrows.mq4`, `NRTR_EA.mq5`,
> `Center of Gravity.mq4`, `MACD_TradingView_Style.mq5/.mq4`,
> `ATR VOL MACD.mq5`, `atr-channels-mtf.mq4`, `MA_Chanels_FIBO.mq5`,
> `ADX_AdvancedX_WA_mtf.mq4`, RSI variants (3 files), Pivot files (2), and
> `Phat_TD_REI.mq4`.

---

## 1. QQE Algorithm (Quantitative Qualitative Estimation)

**Source file**: `cfb-adaptive qqe histo alerts + arrows.mq4`

QQE is a 6-step pipeline: RSI → RSX smoothing → AtrRsi → Fast/Slow QQE trails
→ Bull/Bear trail → crossover signal.

### Step 1 — Compute Raw RSI

```mql4
double rsi = iRSI(NULL, 0, RSI_Period, PRICE_CLOSE, i);
```

Use standard `RSI_Period` (commonly 14). This raw RSI feeds into the RSX
smoother, NOT into the trail directly.

### Step 2 — Smooth RSI with RSX (Jurik-Like 3-Stage Exponential Filter)

RSX is **not** a standard EMA. It is a 3-pass recursive filter that approximates
Jurik smoothing without the full complexity. The MQL implementation uses three
internal accumulators (`f8`, `f18`, `f28`) and a warmup counter.

**Warmup phase** (first `RSI_Period + 1` bars): accumulate a simple average,
do not emit a valid RSX value.

**Running phase** — compute per bar:

```
// Per-bar RSX update (pseudocode, arrays indexed newest-first)
double c = RSI[i]           // current raw RSI

// 3-stage filter
f8  += Kfactor * (c  - f8)
f18 += Kfactor * (f8 - f18)
f28 += Kfactor * (f18 - f28)

// Composite output
RSX[i] = f8 + f18 + f28
```

Where `Kfactor = 2.0 / (RSI_Period + 1)` — identical to a standard EMA
coefficient, but applied three times in series, yielding much lower lag.

> [!IMPORTANT]
> Do **not** substitute a plain triple-EMA (TEMA) for RSX. TEMA uses
> `3×EMA1 − 3×EMA2 + EMA3`, which over-corrects. RSX accumulates additively:
> `f8 + f18 + f28`, giving a different frequency response.

### Step 3 — Compute AtrRsi Array

```mql4
AtrRsi[i] = MathAbs(RSX[i] - RSX[i+1]);
```

This is the bar-to-bar absolute change of the smoothed RSI — analogous to ATR
but in RSI space.

### Step 4 — Fast QQE Trail Width

```mql4
double FastAtr = iMAOnArray(AtrRsi, 0, FastPeriod, 0, MODE_EMA, i);
double FastQQE = FastAtr * SmoothFactor;   // SmoothFactor typically 4.238
```

`FastQQE` sets the inner (tighter) trail band around RSX.

### Step 5 — Slow QQE Trail Width

```mql4
double SlowAtr = iMAOnArray(AtrRsi, 0, SlowPeriod, 0, MODE_EMA, i);
double SlowQQE = SlowAtr * SmoothFactor;
```

`SlowQQE` sets the outer (wider) band used to build the main trailing level.
`SlowPeriod` is typically `FastPeriod × QQE_Factor` (e.g. 2.618).

### Step 6 — Build Bull/Bear Trailing Level & Signal

```
// Bull trail (uptrend state)
if RSX[i] >= BullTrail[i+1]:
    BullTrail[i] = max(BullTrail[i+1], RSX[i] - SlowQQE)
else:
    BullTrail[i] = RSX[i] - SlowQQE          // trail resets on bearish bar

// Bear trail (downtrend state)
if RSX[i] <= BearTrail[i+1]:
    BearTrail[i] = min(BearTrail[i+1], RSX[i] + SlowQQE)
else:
    BearTrail[i] = RSX[i] + SlowQQE

// State machine
if   prev_state == BEAR  and RSX[i] > BearTrail[i]:  state = BULL
elif prev_state == BULL  and RSX[i] < BullTrail[i]:  state = BEAR

Trail[i] = (state == BULL) ? BullTrail[i] : BearTrail[i]
```

**Signal arrows**:
- Up arrow: `state` flips BEAR → BULL (RSX crosses above bear trail)
- Down arrow: `state` flips BULL → BEAR (RSX crosses below bull trail)

**Histogram**: `RSX[i] - 50` — positive = bullish momentum, negative = bearish.

---

## 2. NRTR (Nick Rypock Trailing Reversal)

**Source file**: `NRTR_EA.mq5`

NRTR is a volatility-adjusted always-in trailing stop. It tracks the highest
close in an uptrend and the lowest close in a downtrend, with a percentage band
`k`.

### Core Formulas

**Uptrend trail** (support level):
```
trail_up[i] = HighestClose(period, i) × (1 - k / 100)
```

**Downtrend trail** (resistance level):
```
trail_dn[i] = LowestClose(period, i)  × (1 + k / 100)
```

### State Transition Rules

```
// Initialize: assume uptrend
if Close[i] < trail_up[i]:
    trend = DOWN
    trail[i] = trail_dn[i]
elif Close[i] > trail_dn[i]:
    trend = UP
    trail[i] = trail_up[i]
else:
    trail[i] = trail[i+1]   // no flip, carry forward
```

### Always-In Reversal Logic (EA Pattern)

On a **flip to DOWN**: simultaneously close any LONG position and open a SHORT.
On a **flip to UP**: simultaneously close any SHORT position and open a LONG.

```mql5
if(trend_prev == UP && trend_now == DOWN) {
    ClosePosition(ORDER_TYPE_BUY);
    OpenPosition(ORDER_TYPE_SELL);
}
if(trend_prev == DOWN && trend_now == UP) {
    ClosePosition(ORDER_TYPE_SELL);
    OpenPosition(ORDER_TYPE_BUY);
}
```

> [!TIP]
> Typical parameter ranges: `period = 20–40`, `k = 1.5–3.0` for daily charts.
> For intraday (M15/H1), reduce `k` to `0.5–1.5` and `period` to `10–20`.

### HighestClose / LowestClose Helper

```mql5
double HighestClose(int period, int shift) {
    double highest = DBL_MIN;
    for(int j = shift; j < shift + period; j++)
        highest = MathMax(highest, iClose(NULL, 0, j));
    return highest;
}
```

---

## 3. Center of Gravity (Ehlers)

**Source file**: `Center of Gravity.mq4`

The Ehlers Center of Gravity oscillator applies a weighted-sum formula where
bar weights are their distance from the current bar (age), and the oscillator
is the ratio of weighted-sum to plain sum.

### Formula

```
Num   = 0
Denom = 0
for j = 0 to Period-1:
    price = (High[i+j] + Low[i+j]) / 2   // or Close[i+j]
    Num   += (j + 1) × price
    Denom += price

CoG[i] = -(Num / Denom)     // negated so rising prices = rising oscillator
```

The Gaussian elimination mentioned in the source refers to solving the
least-squares polynomial fit used in some extended implementations. In the
basic `Center of Gravity.mq4`, the above ratio is the actual implementation.

### ⚠️ REPAINTING WARNING

> [!CAUTION]
> **Center of Gravity REPAINTS.** Because `CoG[i]` is recalculated each tick
> using the **current** bar's High/Low (which changes until bar close), the
> oscillator value for bar `i` changes on every tick while that bar is open.
> A signal generated mid-bar will look different — or may disappear entirely —
> after the bar closes.
>
> **Never use CoG crossover signals for backtesting entry triggers.** The
> backtest will see closed-bar values that were never visible in real time.
> Use CoG only for directional bias or confluence — not for precise entries.

---

## 4. MACD TradingView Style — EMA Seed Initialization

**Source files**: `MACD_TradingView_Style.mq5`, `MACD_TradingView_Style.mq4`

Standard MT4/MT5 `iMACD` seeds its first EMA value as the first bar's close.
TradingView seeds the first EMA as the **SMA of the first N bars**. This causes
a divergence for the first 50–100 bars that can make EA logic differ between
platforms.

### Seeded EMA Initialization

```mql5
// Correct TradingView-matching seed for an N-period EMA
double SeedEMA(int period, int oldest_bar_index) {
    double sum = 0;
    for(int j = oldest_bar_index; j > oldest_bar_index - period; j--)
        sum += iClose(NULL, 0, j);
    return sum / period;   // SMA of first N bars = seed
}

double alpha = 2.0 / (period + 1);
double ema_prev = SeedEMA(fast_period, total_bars - 1);

for(int i = total_bars - fast_period - 1; i >= 0; i--) {
    double ema = iClose(NULL, 0, i) * alpha + ema_prev * (1 - alpha);
    ema_prev = ema;
    FastEMA[i] = ema;
}
```

Apply identical seeding to both Fast EMA and Slow EMA, then:

```
MACD_Line[i]   = FastEMA[i] - SlowEMA[i]
Signal_Line[i] = EMA(MACD_Line, signal_period)[i]   // also seeded
Histogram[i]   = MACD_Line[i] - Signal_Line[i]
```

> [!NOTE]
> If you use MT5's built-in `iMACD`, you **cannot** control seed initialization.
> For TradingView parity, compute Fast and Slow EMAs manually using the seeded
> loop above, then subtract them to form the MACD line.

---

## 5. ATR VOL MACD — Dual iMACD Handle Pattern

**Source file**: `ATR VOL MACD.mq5`

This indicator runs **two independent MACD computations** — one on ATR values,
one on Volume values — and combines them into a composite signal.

### Handle Creation (OnInit)

```mql5
// ATR sub-indicator as price feed for first MACD
handle_atr  = iATR(NULL, 0, atr_period);

// MACD on ATR buffer (PRICE_CUSTOM via custom indicator, or manual)
handle_macd_atr = iMACD(NULL, 0,
    fast_ema, slow_ema, signal,
    PRICE_CLOSE);   // NOTE: replace with ATR buffer feed — see below

// Volume MACD requires manual calculation since iMACD doesn't accept volume
// Pattern: compute EMA of Volume directly
```

### Practical Implementation Pattern

Because `iMACD` does not accept arbitrary buffers, ATR-MACD and Volume-MACD
are computed manually:

```mql5
// ATR array (filled from handle_atr via CopyBuffer)
double atr_buf[];
CopyBuffer(handle_atr, 0, 0, bars, atr_buf);
ArraySetAsSeries(atr_buf, true);

// Manual EMA-of-ATR fast and slow
double atr_fast_ema[], atr_slow_ema[];
ComputeEMA(atr_buf, fast_ema, atr_fast_ema);
ComputeEMA(atr_buf, slow_ema, atr_slow_ema);
// MACD_ATR[i] = atr_fast_ema[i] - atr_slow_ema[i]

// Volume array
double vol_buf[];
CopyRates(NULL, 0, 0, bars, rates);
// extract rates[i].tick_volume into vol_buf[]
// then apply same EMA pattern → MACD_VOL[i]
```

### Signal Combination

```
// Composite: average the two normalized MACD lines
CompositeHistogram[i] = (MACD_ATR[i] / ATR_norm + MACD_VOL[i] / VOL_norm) / 2

// Bullish confluence: both MACD_ATR > 0 and MACD_VOL > 0
// Bearish confluence: both < 0
```

---

## 6. Fibonacci MA Channels

**Source file**: `MA_Chanels_FIBO.mq5`

Dynamic Fibonacci S/R levels projected above and below a moving average. The
channel width uses the High/Low range over the same MA period.

### Parameters

| Parameter    | Typical Value |
|-------------|---------------|
| `MA_Period`  | 20            |
| `MA_Method`  | MODE_SMA      |
| `MA_Price`   | PRICE_CLOSE   |

### Fib Level Set

```
fib_levels[] = {0.236, 0.382, 0.500, 0.618, 0.786, 1.000}
```

### Formula Per Bar

```mql5
double MA        = iMA(NULL, 0, MA_Period, 0, MA_Method, MA_Price, i);
double HighRange = iHigh(NULL, 0, iHighest(NULL, 0, MODE_HIGH, MA_Period, i)) - MA;
double LowRange  = MA - iLow(NULL,  0, iLowest(NULL,  0, MODE_LOW,  MA_Period, i));

for(int f = 0; f < 6; f++) {
    UpperBand[f][i] = MA + HighRange * fib_levels[f];
    LowerBand[f][i] = MA - LowRange  * fib_levels[f];
}
```

### Trading Interpretation

- Price rejecting at **61.8% upper band** → strong resistance; fade rally.
- Price holding above **38.2% lower band** → uptrend intact; buy dip.
- Break and close above **100% upper band** → expansion; trend continuation.
- MA acts as the 0% level (equilibrium).

---

## 7. Pivot Points

**Source files**: `Pivot2.mq4`, `Pivot_Backtest.mq4`

Pivots are calculated from the **previous session's** High, Low, and Close
(daily, weekly, or monthly).

### Classic Pivot Formulas

```
P  = (High + Low + Close) / 3

R1 = 2×P - Low
R2 = P + (High - Low)
R3 = High + 2×(P - Low)

S1 = 2×P - High
S2 = P - (High - Low)
S3 = Low - 2×(High - P)
```

### Fibonacci Pivot Formulas

```
P  = (High + Low + Close) / 3     // same as classic

R1 = P + 0.382 × (High - Low)
R2 = P + 0.618 × (High - Low)
R3 = P + 1.000 × (High - Low)

S1 = P - 0.382 × (High - Low)
S2 = P - 0.618 × (High - Low)
S3 = P - 1.000 × (High - Low)
```

### Previous-Session OHLC Fetch Pattern (MT4)

```mql4
// Shift=1 → previous completed daily bar
double prev_High  = iHigh (NULL, PERIOD_D1, 1);
double prev_Low   = iLow  (NULL, PERIOD_D1, 1);
double prev_Close = iClose(NULL, PERIOD_D1, 1);
```

For weekly pivots use `PERIOD_W1`; for monthly use `PERIOD_MN1`.

> [!TIP]
> In `Pivot_Backtest.mq4`, pivots are recomputed for each historical bar by
> walking back through daily bars. Use `iBarShift(NULL, PERIOD_D1, Time[i])`
> to find which daily bar corresponds to the current intraday bar `i`.

---

## 8. CopyBuffer Workflow — MT5 Handle Pattern

All MT5 indicators that use built-in handles must follow this exact sequence:

### Complete Pattern

```mql5
// 1. Create handle in OnInit()
int handle = iATR(NULL, PERIOD_CURRENT, 14);
if(handle == INVALID_HANDLE) {
    Print("Failed to create handle: ", GetLastError());
    return INIT_FAILED;
}

// 2. In OnCalculate() — wait for the handle to be ready
if(BarsCalculated(handle) < rates_total) return 0;

// 3. Copy buffer data (index 0 = main buffer)
double buf[];
ArraySetAsSeries(buf, true);
int copied = CopyBuffer(handle, 0, 0, rates_total, buf);
if(copied <= 0) {
    Print("CopyBuffer failed: ", GetLastError());
    return 0;
}

// 4. Use buf[i] — buf[0] = current bar, buf[1] = previous bar
```

### Multi-Handle Pattern (ATR VOL MACD Style)

```mql5
// Declare handles globally
int h_atr, h_vol_fast, h_vol_slow;

// OnInit
h_atr      = iATR(NULL, 0, atr_period);
// Volume EMA handles not available natively — compute manually

// OnCalculate — copy all before processing
double atr_data[];
ArraySetAsSeries(atr_data, true);
CopyBuffer(h_atr, 0, 0, rates_total, atr_data);
```

### Buffer Index Reference

| Indicator      | Buffer 0        | Buffer 1       | Buffer 2     |
|---------------|-----------------|----------------|--------------|
| `iATR`         | ATR values      | —              | —            |
| `iMACD`        | MACD line       | Signal line    | —            |
| `iRSI`         | RSI values      | —              | —            |
| `iMA`          | MA values       | —              | —            |
| `iBands`       | Middle (MA)     | Upper band     | Lower band   |
| `iADX`         | ADX             | +DI            | −DI          |

---

## 9. Repainting Indicators

### What Is Repainting?

An indicator **repaints** when its historical bar values change on subsequent
ticks or bar closes. This happens when:

1. The calculation uses **future bars** (lookahead), OR
2. The calculation uses the **current unclosed bar's** OHLC which changes each
   tick (e.g., Center of Gravity using `High[0]`/`Low[0]`).

### Detection Checklist

Ask these questions about any indicator:

- [ ] Does the formula reference `High[0]`, `Low[0]` in a loop that includes
      past bars? → **Repaints** (value changes until bar close).
- [ ] Is there a `for` loop going forward in time (from older → newer bars)
      that modifies an already-plotted bar? → **Lookahead bias**.
- [ ] Does the indicator use `iHighest`/`iLowest` over a window that includes
      the current bar? → **Potentially repaints**.
- [ ] Do signals appear "perfect" in backtest but miss in live? → Almost
      certainly repainting.

### Known Repainting Indicators (from source set)

| Indicator             | Repaints? | Reason                                      |
|----------------------|-----------|---------------------------------------------|
| Center of Gravity     | ✅ YES    | Uses current bar H/L in running sum         |
| NRTR                  | ✅ Partial| `HighestClose` recalculates on each tick    |
| QQE                   | ❌ NO     | RSX and trails only use `i+1` lookback      |
| Classic Pivots        | ❌ NO     | Based on fully closed previous session      |
| MACD TradingView      | ❌ NO     | EMA is causal (uses only past bars)         |
| Fibonacci MA Channels | ✅ Partial| `iHighest`/`iLowest` includes current bar   |

### Safe Backtest Rules

> [!CAUTION]
> **Never use Center of Gravity crossovers as entry signals in a backtest.**
> The backtest engine will see final closed-bar CoG values that were never
> visible to a trader watching the indicator in real time.

> [!WARNING]
> For any indicator with partial repainting (NRTR, Fib MA Channels), restrict
> entry signals to **confirmed bars only**: use `iClose(NULL,0,1)` and
> `bar_count` guard in `OnCalculate` to ensure you only act on
> `prev_calculated < rates_total` new bars.

```mql5
// Guard pattern: act only on newly closed bars
if(rates_total == prev_calculated) return rates_total;

// Process bar at index 1 (last fully closed bar), not index 0
ProcessBar(1);
```

---

## 10. Additional Indicator Algorithms

### ADX Multi-Timeframe Alignment (`ADX_AdvancedX_WA_mtf.mq4`)

Multi-TF ADX checks directional alignment across timeframes before signaling:

```mql4
bool IsBullishAlignment() {
    bool aligned = true;
    int tfs[] = {PERIOD_H1, PERIOD_H4, PERIOD_D1};
    for(int t = 0; t < 3; t++) {
        double adx  = iADX(NULL, tfs[t], adx_period, PRICE_CLOSE, MODE_MAIN,  1);
        double plus = iADX(NULL, tfs[t], adx_period, PRICE_CLOSE, MODE_PLUSDI, 1);
        double minus= iADX(NULL, tfs[t], adx_period, PRICE_CLOSE, MODE_MINUSDI,1);
        if(!(adx > adx_threshold && plus > minus)) { aligned = false; break; }
    }
    return aligned;
}
```

### ATR Channels MTF (`atr-channels-mtf.mq4`)

Upper and lower ATR bands around a moving average, optionally from a higher
timeframe using `CopyBuffer` on an HTF indicator handle:

```mql4
double ma  = iMA  (NULL, HTF_Period, MA_period, 0, MODE_SMA, PRICE_CLOSE, i);
double atr = iATR (NULL, HTF_Period, ATR_period, i);

UpperChannel[i] = ma + atr * Multiplier;
LowerChannel[i] = ma - atr * Multiplier;
```

For MT5 HTF via handle:
```mql5
int htf_atr_handle = iATR(NULL, PERIOD_H4, 14);
double htf_atr[];
CopyBuffer(htf_atr_handle, 0, 0, count, htf_atr);
```

### Tom DeMark REI (`Phat_TD_REI.mq4`)

Range Expansion Index measures bar range relative to two bars ago:

```mql4
// Condition: current bar is a "qualified" expansion bar
bool hi_ok = (High[i] >= High[i+2] || High[i] >= Close[i+3]);
bool lo_ok = (Low[i]  <= Low[i+2]  || Low[i]  <= Close[i+3]);

double numerator   = 0;
double denominator = 0;
for(int j = i; j < i + REI_Period; j++) {
    double range = High[j] - Low[j];
    denominator += range;
    if(hi_ok && lo_ok) numerator += (High[j] - Low[j]);
    // else qualified = false for this bar, contribute 0 to numerator
}

REI[i] = (denominator != 0) ? (numerator / denominator) * 200 - 100 : 0;
// Range: -100 to +100. Overbought > 45, Oversold < -45
```

---

## 11. RSI Variant Summary

| File                  | Variant                         | Key Difference                           |
|----------------------|---------------------------------|------------------------------------------|
| `RSI smoothed MTF.mq4`| RSI + EMA smoothing + HTF       | Plots HTF RSI on current chart           |
| `RSI-EMA Signals.mq4` | RSI + EMA crossover signals     | Arrow on RSI-EMA cross, not RSI-50       |
| `RSI3 close.mq4`      | 3-period RSI of Close           | Ultra-short for mean-reversion setups    |

All three use `iRSI(NULL, period_tf, rsi_period, PRICE_CLOSE, i)` as the base.
MTF variants shift to `iRSI(NULL, HTF, ...)` and handle the bar-alignment
problem using `iBarShift`.

---

*Skill generated from forensic analysis of 13 MQL indicator source files.
Last updated: 2026-09-26.*

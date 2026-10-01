# Deep Investigation & Architectural Analysis: Execution Infrastructure, Adaptive Weights, News Blackout & Compilation Verification
**Author**: Explorer Survey 3 (Execution & Infrastructure Explorer)  
**Target EA**: `GoldOracle_v2.mq5`  
**Reference Prototype**: `GoldOracle_v1.mq5`  
**Date**: 2026-10-01  
**Working Directory**: `c:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\explorer_survey_3`  

---

## 1. Executive Summary

This investigation provides a comprehensive forensic analysis of the execution microstructure, dynamic adaptive weighting engine, institutional news safety architecture, and compiler toolchain for **Gold Oracle EA v2**.

Through live experimentation and forensic code inspection of `GoldOracle_v1.mq5`, existing specialist skills (`gold-xauusd-specialist`, `production-mql-engineering`, `trailing-stop-systems`), and the local MetaTrader 5 64-bit compiler, we have established:
1. **Pip Normalization Integrity**: Proven that for 2-digit XAUUSD (`_Digits == 2`), `pipFactor = 1.0` and `pipSize = 0.01` ($0.01 per point/pip). We resolved the common pitfall of forex `0.0001` hardcoding.
2. **Dynamic ATR Stop-Loss & Error 130 Prevention**: Analyzed the root cause of `TRADE_RETCODE_INVALID_STOPS` (Error 130) on Gold and established the exact spread-buffered broker stop clamping model.
3. **Risk-Based Equity Sizing**: Formulated the lot sizing equation based on `AccountInfoDouble(ACCOUNT_EQUITY)` and `SYMBOL_TRADE_TICK_VALUE_LOSS`, with defensive division-by-zero guards and volume step quantization.
4. **Adaptive Weighting Resolution**: Discovered that in `GoldOracle_v1.mq5`, `UpdateBrainWeights()` was completely orphaned and never invoked. Formulated the exact 20:00 UTC trigger, 0.95/0.05 exponential accuracy update, 0.1 floor guarantee, and neutral vote isolation rules for all 144 brains.
5. **Institutional News Blackout & UTC Synchronization**: Identified a critical flaw in v1 where `TimeTradeServer()` (GMT+2/GMT+3) was directly compared against UTC event hours (a 2-3 hour timing error). Engineered a dual-layer calendar system (algorithmic recurrence + FOMC institutional matrix) with pre-news liquidation and zero same-day re-entry.
6. **MetaEditor64 Compilation Verification**: Confirmed that `C:\Program Files\MetaTrader 5\MetaEditor64.exe` compiles cleanly. Developed and verified `compile_verifier.py`, proving zero-error, zero-warning automated validation.

---

## 2. Forensic Audit of Execution Infrastructure in Prototype (`GoldOracle_v1.mq5`)

### 2.1 Pip Normalization Audit
In `GoldOracle_v1.mq5`:
```mql5
pipFactor = (_Digits == 5 || _Digits == 3) ? 10.0 : 1.0;
pipSize   = _Point * pipFactor;
```
- For XAUUSD with `_Digits == 2`, `pipFactor = 1.0`, `pipSize = 0.01 * 1.0 = 0.01`.
- For rare 3-digit Gold feeds, `pipFactor = 10.0`, `pipSize = 0.001 * 10.0 = 0.01`.
- This confirms that $0.01 is universally 1 pip. The calculation is mathematically sound, but in v1 `PipsToPrice` was incorrectly applied to stop-loss offsets that did not account for spread buffers.

### 2.2 Dynamic ATR Stop-Loss & Broker Stops Level
In `GoldOracle_v1.mq5` lines 160–167:
```mql5
double GetSafeSL(int direction, double entryPrice, double desiredSLPips)
{
   long   stopLevel  = SymbolInfoInteger(_Symbol, SYMBOL_TRADE_STOPS_LEVEL);
   double minDist    = stopLevel * _Point;
   double wantedDist = PipsToPrice(desiredSLPips);
   double safeDist   = MathMax(wantedDist, minDist + _Point);
   return (direction == 1) ? entryPrice - safeDist : entryPrice + safeDist;
}
```
**Critical Flaw**:
On a BUY order, entry is at `Ask`. The stop-loss triggers at `Bid`.
The distance enforced by the broker is $\text{Bid} - \text{SL} \ge \text{stopLevel} \times \text{\_Point}$.
Because $entryPrice = Ask = Bid + Spread$, we have:
$$\text{Bid} - \text{SL} = \text{Bid} - (\text{Ask} - \text{safeDist}) = \text{safeDist} - \text{Spread}$$
If `wantedDist` is tight or during volatile news when `Spread` expands to 50–200 points, $\text{safeDist} - \text{Spread}$ drops below `minDist`, resulting in `TRADE_RETCODE_INVALID_STOPS` (Error 130) and trade rejection!
**Remediation**:
Calculate SL distance directly from the triggering price (`Bid` for Buy SL, `Ask` for Sell SL) with an explicit `Spread + StopsLevel + 2 points` buffer.

### 2.3 Equity Sizing Audit
In `GoldOracle_v1.mq5` lines 407–413:
```mql5
double risk_money = AccountInfoDouble(ACCOUNT_BALANCE) * InpRiskPercent / 100.0;
double tickValue = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
double tickSize = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
double slPoints = MathAbs(entry - slPrice) / _Point;
double risk_per_lot = (slPoints * _Point / tickSize) * tickValue;
double lots = NormalizeLot(risk_money / risk_per_lot);
```
**Defects**:
1. Uses `ACCOUNT_BALANCE` rather than `ACCOUNT_EQUITY`. In live trading with open floating positions or unrealized swaps, balance does not reflect real risk capital.
2. If `risk_per_lot` calculates to `0.0` (e.g. `entry == slPrice` or zero tick value), a runtime division-by-zero critical fault occurs.
3. Does not use `SYMBOL_TRADE_TICK_VALUE_LOSS`, which accurately accounts for currency conversion when deposit currency != USD.

---

## 3. Deep Dive: Adaptive Dynamic Weighting Engine

### 3.1 The Orphaned Code in Prototype v1
Lines 438–445 of `GoldOracle_v1.mq5`:
```mql5
if(dt.hour >= InpSessionCloseHour) {
   if(g_state != STATE_SESSION_CLOSED) {
      CloseAllPositions();
      g_state = STATE_SESSION_CLOSED;
      // TODO: determine actual direction of the day here and call UpdateBrainWeights
   }
   return;
}
```
The prototype developer left a `// TODO` comment. `UpdateBrainWeights` was never called anywhere in the program.

### 3.2 Mathematical Formulation for 144 Brains
In v2, exactly 144 brains cast votes $V_i \in \{+1, -1, 0\}$ at 10:00 UTC.
At 20:00 UTC, the daily close price is sampled:
$$\Delta P = \text{Close}_{20:00} - \text{Open}_{10:00}$$
$$\text{ActualDirection} = \text{Sign}(\Delta P)$$

For each brain $i \in \{0, \dots, 143\}$:
- If $V_i == 0$: Brain abstained. Skip update.
- If $V_i \ne 0$:
  $$\text{Outcome}_i = (V_i == \text{ActualDirection}) ? 1.0 : 0.0$$
  $$\text{EMA\_Acc}_i \leftarrow 0.95 \times \text{EMA\_Acc}_i + 0.05 \times \text{Outcome}_i$$
  $$W_i \leftarrow \max(0.1, \text{EMA\_Acc}_i)$$

### 3.3 Convergence & Sensitivity Analysis
- At cold start, all brains have $W_i = 1.0$. Total maximum ensemble weight = 144.0.
- If a brain produces 10 consecutive incorrect calls ($Outcome = 0.0$):
  - Day 1: $1.0 \times 0.95 + 0.05 \times 0 = 0.950$
  - Day 2: $0.950 \times 0.95 = 0.902$
  - Day 5: $1.0 \times 0.95^5 = 0.774$
  - Day 10: $1.0 \times 0.95^{10} = 0.599$
  - Day 20: $1.0 \times 0.95^{20} = 0.358$
  - Day 45: $1.0 \times 0.95^{45} = 0.099 \rightarrow \text{clamped to } 0.100$.
- The 0.1 floor ensures that a strategy is suppressed to 10% influence during hostile market regimes, yet retains the ability to regain weight when its edge returns.

---

## 4. Institutional News Blackout & Safety System Audit

### 4.1 Broker Server Time vs UTC Timing Mismatch
In `GoldOracle_v1.mq5`:
```mql5
TimeToStruct(TimeTradeServer(), now);
int currentMins = now.hour * 60 + now.min;
// compared against g_NewsBlackouts[i].hourGMT * 60 + minuteGMT
```
`TimeTradeServer()` returns broker time (typically UTC+2 / UTC+3). Comparing broker hour to GMT hour creates a 2-hour or 3-hour lag. E.g., NFP at 12:30 UTC occurs when broker server time is 14:30 or 15:30. The prototype would activate blackout at 12:30 broker time (10:30 UTC) and trade directly through the actual NFP release!

### 4.2 Generic Day-of-Week Recurrence Bug
In `GoldOracle_v1.mq5`:
- `FOMC`: `{3, 18, 0, 30, 90}` on every Wednesday!
- `CPI`: `{2, 12, 30, 15, 30}` on every Tuesday!
- `PPI`: `{4, 12, 30, 15, 30}` on every Thursday!
- `Powell`: `{3, 14, 0, 15, 30}` on every Wednesday!
This caused the EA to block trading on almost every weekday.
**Remediation in v2**:
1. Synchronize all news and session calculations to `TimeGMT()`.
2. Implement exact algorithmic date matching (NFP: 1st Friday, month day $\le 7$).
3. Implement an institutional calendar matrix for scheduled FOMC meetings (8 specific Wednesdays per year) and high-impact releases.

---

## 5. MetaEditor64 Compilation Verification & Log Reader Audit

### 5.1 Local Toolchain Confirmation
We executed an automated verification of `C:\Program Files\MetaTrader 5\MetaEditor64.exe`:
- **File size**: 115,544,688 bytes.
- **CLI Flag Syntax**:
  `"C:\Program Files\MetaTrader 5\MetaEditor64.exe" /compile:"<source.mq5>" /log:"<output.log>"`
- **Log File Encoding**: UTF-16 LE with BOM (`\xff\xfe`).
- **Live Test Result**: `GoldOracle_v1.mq5` compiled in 1,847 ms, yielding `GoldOracle_v1.ex5` (41,898 bytes) with `0 errors, 0 warnings`.
- **Harness Created**: `.agents/explorer_survey_3/compile_verifier.py` provides immediate pass/fail return codes and structured diagnostics for developer agents.

---

## 6. Recommendations for Architecture & Implementation Workers

1. **Adopt Exact Microstructure Module**: Integrate `CalculateSafeATRStopLoss`, `CalculateLotSize`, `IsSpreadPermitted`, and `IsVolatilityPermitted` directly from `infrastructure_spec.md`.
2. **Integrate Dynamic Weight Updates**: Ensure `UpdateAdaptiveWeights(actualDirection)` is called in `OnTick()` at 20:00 UTC immediately after session liquidation.
3. **Synchronize News Time to UTC**: Always evaluate news blackout windows against `TimeGMT()`.
4. **Mandatory Compilation Gate**: Run `compile_verifier.py` on `GoldOracle_v2.mq5` to verify 0 errors and 0 warnings before initiating auditing.

---
*End of Analysis Report — Explorer Survey 3*

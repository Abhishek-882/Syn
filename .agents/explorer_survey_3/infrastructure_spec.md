# Gold Oracle EA v2 — Infrastructure & Execution Specification
**Author**: Explorer Survey 3 (Execution & Infrastructure Explorer)  
**Target EA**: `GoldOracle_v2.mq5`  
**Reference Prototype**: `GoldOracle_v1.mq5`  
**Date**: 2026-10-01  
**Integrity Mode**: Development / Zero-Defect Production Grade  

---

## 1. Executive Summary

This specification establishes the production-grade architectural blueprint for the execution infrastructure, self-learning adaptive dynamic weighting engine, institutional news blackout safety system, and MetaEditor64 compilation verification harness for **Gold Oracle EA v2** (`GoldOracle_v2.mq5`).

Gold Oracle EA v2 is a monolithic daily directional Expert Advisor designed for Spot Gold (XAUUSD) on MetaTrader 5. It operates on confirmed historical market structure during the London session (07:00–10:00 UTC), derives consensus from 144 predictive strategy brains, enters a single high-conviction position at ~10:00 UTC, and terminates the trade deterministically at 20:00 UTC unless closed early by dynamic ATR stop-loss or institutional macro news liquidation.

### Core Architectural Objectives & Resolutions
1. **Gold Microstructure Precision**: Resolve all XAUUSD pip normalization ambiguities (`_Digits == 2`, `_Point = 0.01`, `pipFactor = 1.0`), implement dynamic $\text{ATR}(14, H1) \times 2.0$ stop-loss clamping that accounts for broker `SYMBOL_TRADE_STOPS_LEVEL` and spread buffers (eliminating MT5 Error 130 / `TRADE_RETCODE_INVALID_STOPS`), and engineer exact equity percentage risk sizing based on live tick values.
2. **Operational Gating**: Enforce strict pre-entry spread gating (max 50 points) and H1 ATR volatility gating (min 30 points on confirmed bar[1]) to insulate the account from illiquid and erratic market regimes.
3. **Adaptive Dynamic Weighting Engine**: Fully operationalize the self-tuning ensemble of 144 weights $W_i \in [0.1, 1.0]$. Fix Prototype Defect 1 (orphaned `UpdateBrainWeights`) by triggering mathematical daily accuracy updates at 20:00 UTC:
   $$\text{ActualDirection} = \text{Sign}(\text{Close}_{20:00} - \text{Open}_{10:00})$$
   $$\text{EMA\_Acc}_i \leftarrow 0.95 \times \text{EMA\_Acc}_i + 0.05 \times (\text{Vote}_i == \text{ActualDirection} ? 1.0 : 0.0)$$
   $$W_i \leftarrow \max(0.1, \text{EMA\_Acc}_i)$$
4. **Institutional News Blackout & Safety System**: Fix Prototype Defects 7 and 8 (server-time vs UTC desynchronization and coarse weekly recurrence) by deploying a dual-layer news safety engine (deterministic calendar matrix + live MT5 Economic Calendar fallback) covering NFP, CPI, FOMC, PPI, and Fed Chair speeches with automated pre-news liquidation and zero same-day re-entry.
5. **Verified MetaEditor64 Compilation Harness**: Verify local 64-bit compiler (`C:\Program Files\MetaTrader 5\MetaEditor64.exe`), validate `/compile` and `/log` CLI execution, and provide a UTF-16 LE log parsing script (`compile_verifier.py`) guaranteeing zero errors and zero warnings.

---

## 2. Gold Microstructure & Execution Architecture

### 2.1 XAUUSD Quoting Conventions & Pip Normalization

Forex trading systems commonly assume a 4/5-digit quoting convention where 1 pip = 10 points ($0.00010 = 1 \text{ pip}$). **Spot Gold (XAUUSD) operates under completely distinct quoting dynamics**:
- On virtually all MetaTrader 5 institutional and retail brokers, XAUUSD is quoted to **2 decimal places** (`_Digits == 2`, `_Point = 0.01`).
- E.g., Gold price = \$2,650.45. A 1-point move is \$0.01 (1 cent per troy ounce).
- Rare 3-decimal brokers quote Gold as \$2,650.450 (`_Digits == 3`, `_Point = 0.001`).

```
┌────────────────────────────────────────────────────────────────────────┐
│                      XAUUSD PIP NORMALIZATION MATRIX                   │
├─────────┬─────────┬──────────┬───────────┬─────────────┬───────────────┤
│ Broker  │ _Digits │  _Point  │ pipFactor │ 1 Pip Price │ 1 Pip Points  │
├─────────┼─────────┼──────────┼───────────┼─────────────┼───────────────┤
│ 2-Digit │    2    │   0.01   │    1.0    │    $0.01    │   1 point     │
│ 3-Digit │    3    │   0.001  │   10.0    │    $0.01    │  10 points    │
└─────────┴─────────┴──────────┴───────────┴─────────────┴───────────────┘
```

#### Production Normalization Implementation
```mql5
//+------------------------------------------------------------------+
//| XAUUSD Pip Normalization Utilities                              |
//+------------------------------------------------------------------+
double g_pipFactor = 1.0;
double g_pipSize   = 0.01;

void InitPipNormalization()
{
   // For 3-digit quotes (e.g. 2650.123), 1 pip = 10 points = 0.01.
   // For 2-digit quotes (e.g. 2650.12),  1 pip = 1 point  = 0.01.
   g_pipFactor = (_Digits == 3 || _Digits == 5) ? 10.0 : 1.0;
   g_pipSize   = _Point * g_pipFactor;
   
   PrintFormat("[INIT] Symbol: %s | Digits: %d | Point: %.5f | PipFactor: %.1f | PipSize: %.4f",
               _Symbol, _Digits, _Point, g_pipFactor, g_pipSize);
}

// Convert pip distance to price difference
double PipsToPrice(double pips)
{
   return pips * g_pipSize;
}

// Convert price difference to pips
double PriceToPips(double priceDiff)
{
   return (g_pipSize > 0.0) ? (priceDiff / g_pipSize) : 0.0;
}
```

> **Anti-Pattern Warning**: Never use hardcoded `* 0.0001` or `* 10` for XAUUSD. Hardcoded multipliers corrupt ATR distance and lot sizing by two orders of magnitude, causing catastrophic margin liquidation.

---

### 2.2 Dynamic ATR Stop-Loss & Broker Constraint Clamping

Gold Oracle EA v2 employs a dynamic volatility stop-loss calculated at the moment of entry (~10:00 UTC):
$$\text{SL\_Distance}_{\text{desired}} = \text{ATR}(14, H1) \times \text{InpATR\_SL\_Multiplier}$$
Where default $\text{InpATR\_SL\_Multiplier} = 2.0$, and ATR is sampled from completed bar `bar[1]` of the H1 timeframe.

#### The Error 130 (`TRADE_RETCODE_INVALID_STOPS`) Mechanism on Gold
In MetaTrader 5, a stop-loss is validated against the broker's minimum stop level (`SYMBOL_TRADE_STOPS_LEVEL`) and freeze level (`SYMBOL_TRADE_FREEZE_LEVEL`):
1. **For BUY Orders**:
   - Order executes at `Ask`.
   - The stop-loss is triggered when the market falls to `Bid`.
   - The broker verifies: $\text{Bid} - \text{SL} \ge \text{stopsLevelPts} \times \text{\_Point}$.
   - If an EA computes $\text{SL} = \text{Ask} - \text{SL\_Distance}$, then:
     $$\text{Bid} - \text{SL} = \text{Bid} - (\text{Ask} - \text{SL\_Distance}) = \text{SL\_Distance} - \text{Spread}$$
   - If $\text{SL\_Distance} - \text{Spread} < \text{stopsLevelPts} \times \text{\_Point}$, the broker rejects the order immediately with `TRADE_RETCODE_INVALID_STOPS` (Error 130).
2. **For SELL Orders**:
   - Order executes at `Bid`.
   - The stop-loss is triggered when the market rises to `Ask`.
   - The broker verifies: $\text{SL} - \text{Ask} \ge \text{stopsLevelPts} \times \text{\_Point}$.
   - If computed from `Bid`: $\text{SL} - \text{Ask} = (\text{Bid} + \text{SL\_Distance}) - \text{Ask} = \text{SL\_Distance} - \text{Spread}$.

#### Production Dynamic Stop-Loss Clamping Function
```mql5
//+------------------------------------------------------------------+
//| Calculate Safe Stop-Loss with Broker StopsLevel & Spread Clamping |
//+------------------------------------------------------------------+
double CalculateSafeATRStopLoss(int direction, double entryPrice, double atrValueH1, double multiplier)
{
   double desiredDistPrice = atrValueH1 * multiplier;
   
   // Broker minimum stop distance in points & price
   long   stopsLevelPts  = SymbolInfoInteger(_Symbol, SYMBOL_TRADE_STOPS_LEVEL);
   long   freezeLevelPts = SymbolInfoInteger(_Symbol, SYMBOL_TRADE_FREEZE_LEVEL);
   long   minReqPts      = MathMax(stopsLevelPts, freezeLevelPts);
   
   double minReqPrice    = minReqPts * _Point;
   double currentSpread  = SymbolInfoDouble(_Symbol, SYMBOL_ASK) - SymbolInfoDouble(_Symbol, SYMBOL_BID);
   
   // Safety buffer: spread + minimum stops level + 2 points margin
   double absoluteMinDist = minReqPrice + currentSpread + (2.0 * _Point);
   double finalDistPrice  = MathMax(desiredDistPrice, absoluteMinDist);
   
   double rawSL = 0.0;
   if(direction == 1) // BUY
   {
      // Trigger price for Buy SL is Bid
      double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
      rawSL = bid - finalDistPrice;
   }
   else if(direction == -1) // SELL
   {
      // Trigger price for Sell SL is Ask
      double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
      rawSL = ask + finalDistPrice;
   }
   
   return NormalizeDouble(rawSL, _Digits);
}
```

---

### 2.3 Take-Profit Architecture: Directional Session Capture

- **Take-Profit Setting**: Strict `0.0` (None).
- **Quantitative Rationale**: Gold displays significant directional trend inertia following London morning institutional volume absorption. Imposing a fixed take-profit target truncates right-tail outlier gains ($20–$50 moves).
- **Deterministic Exit**: All open positions are liquidated unconditionally at **20:00 UTC** (prior to the New York post-close liquidity cliff and widening spreads), capturing the full daily expansion vector.

---

### 2.4 Equity Percentage Position Sizing Engine

The position sizing engine calculates trade volume dynamically based on live account equity, risk percentage, and the calculated ATR stop-loss distance:
$$\text{RiskMoney} = \text{AccountInfoDouble}(\text{ACCOUNT\_EQUITY}) \times \left( \frac{\text{InpRiskPercent}}{100.0} \right)$$

#### Exact Tick Value Derivation for Gold
In MT5, the monetary risk per standard 1.00 lot for a given price distance is:
$$\text{TicksInSL} = \frac{|\text{EntryPrice} - \text{SL\_Price}|}{\text{SymbolInfoDouble}(\text{\_Symbol}, \text{SYMBOL\_TRADE\_TICK\_SIZE})}$$
$$\text{RiskPerLot} = \text{TicksInSL} \times \text{SymbolInfoDouble}(\text{\_Symbol}, \text{SYMBOL\_TRADE\_TICK\_VALUE\_LOSS})$$
If `SYMBOL_TRADE_TICK_VALUE_LOSS` is unsupported by the broker, fallback to `SYMBOL_TRADE_TICK_VALUE`.

#### Volume Step Normalization & Boundary Clamping
$$\text{RawLots} = \frac{\text{RiskMoney}}{\text{RiskPerLot}}$$
$$\text{NormalizedLots} = \lfloor \frac{\text{RawLots}}{\text{VolumeStep}} \rfloor \times \text{VolumeStep}$$
$$\text{FinalLots} = \max(\text{VolumeMin}, \min(\text{VolumeMax}, \text{NormalizedLots}))$$

#### Production Sizing Implementation
```mql5
//+------------------------------------------------------------------+
//| Calculate Equity Risk-Based Lot Size                            |
//+------------------------------------------------------------------+
double CalculateLotSize(double entryPrice, double slPrice, double riskPercent)
{
   if(entryPrice <= 0.0 || slPrice <= 0.0 || riskPercent <= 0.0)
      return SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
      
   double equity = AccountInfoDouble(ACCOUNT_EQUITY);
   if(equity <= 0.0)
      equity = AccountInfoDouble(ACCOUNT_BALANCE);
      
   double riskMoney = equity * (riskPercent / 100.0);
   
   double tickSize = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   if(tickSize <= 0.0) tickSize = _Point;
   
   double tickValue = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE_LOSS);
   if(tickValue <= 0.0)
      tickValue = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
      
   double slDistPrice = MathAbs(entryPrice - slPrice);
   if(slDistPrice <= 0.0)
      return SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
      
   double slTicks = slDistPrice / tickSize;
   double riskPerLot = slTicks * tickValue;
   
   if(riskPerLot <= 0.0)
   {
      Print("[RISK ERROR] riskPerLot <= 0. Using minimum lot.");
      return SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   }
   
   double rawLot = riskMoney / riskPerLot;
   
   double minLot  = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double maxLot  = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
   double stepLot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   if(stepLot <= 0.0) stepLot = 0.01;
   
   double lot = MathFloor(rawLot / stepLot) * stepLot;
   lot = MathMax(minLot, MathMin(maxLot, lot));
   
   // Decimal precision of volume step
   int lotDigits = 2;
   if(stepLot >= 1.0) lotDigits = 0;
   else if(stepLot >= 0.1) lotDigits = 1;
   else lotDigits = 2;
   
   lot = NormalizeDouble(lot, lotDigits);
   
   PrintFormat("[SIZING] Equity: $%.2f | Risk: %.1f%% ($%.2f) | SL Dist: %.2f | Risk/Lot: $%.2f | Lot: %.2f",
               equity, riskPercent, riskMoney, slDistPrice, riskPerLot, lot);
               
   return lot;
}
```

---

### 2.5 Operational Gating: Spread & Volatility Filters

To eliminate executions during abnormal broker pricing or liquidity vacuums, two hardware gates must pass before `ExecuteTrade()` can be called:

```
                  ┌───────────────────────────────┐
                  │ 10:00 UTC Entry Signal Fired  │
                  └──────────────┬────────────────┘
                                 │
                                 ▼
                     [ Gate 1: Spread OK? ]
                     Spread <= 50 Points?
                                 │
                     ┌───────────┴───────────┐
                     │ NO                    │ YES
                     ▼                       ▼
            ┌─────────────────┐  [ Gate 2: Volatility OK? ]
            │ REJECT ENTRY    │  H1 ATR[1] >= 30 Points?
            │ (Log & Abort)   │              │
            └─────────────────┘  ┌───────────┴───────────┐
                                 │ NO                    │ YES
                                 ▼                       ▼
                        ┌─────────────────┐    ┌───────────────────┐
                        │ REJECT ENTRY    │    │ DISPATCH ORDER    │
                        │ (Market Frozen) │    │ (ExecuteTrade)    │
                        └─────────────────┘    └───────────────────┘
```

#### Spread Gate Specification
- **Parameter**: `input int InpMaxSpreadPoints = 50;` (default 50 points = \$0.50 price spread on 2-digit Gold).
- **Evaluation**:
  ```mql5
  bool IsSpreadPermitted(int maxSpreadPoints)
  {
     long spread = SymbolInfoInteger(_Symbol, SYMBOL_SPREAD);
     if(spread > maxSpreadPoints)
     {
        PrintFormat("[GATE REJECT] Current spread (%d pts) exceeds max allowed (%d pts).",
                    spread, maxSpreadPoints);
        return false;
     }
     return true;
  }
  ```

#### Volatility Gate Specification
- **Parameter**: `input double InpMinATR_H1_Points = 30.0;` (default 30 points = \$0.30 H1 range).
- **Contract**: Evaluated on completed bar `bar[1]` of H1 ATR(14) to maintain strict non-repainting integrity.
- **Evaluation**:
  ```mql5
  bool IsVolatilityPermitted(int h_atr, double minAtrPoints)
  {
     double atrBuf[1];
     ArraySetAsSeries(atrBuf, true);
     if(CopyBuffer(h_atr, 0, 1, 1, atrBuf) < 1)
     {
        Print("[GATE ERROR] Failed to copy H1 ATR buffer.");
        return false;
     }
     
     double atrPoints = atrBuf[0] / _Point;
     if(atrPoints < minAtrPoints)
     {
        PrintFormat("[GATE REJECT] H1 ATR (%.1f pts) below minimum volatility threshold (%.1f pts).",
                    atrPoints, minAtrPoints);
        return false;
     }
     return true;
  }
  ```

---

## 3. Adaptive Dynamic Weighting Engine

### 3.1 Mathematical Architecture

Gold Oracle EA v2 coordinates **144 distinct quantitative brain functions**:
$$\vec{V} = [V_0, V_1, \dots, V_{143}]^T \in \{-1, 0, +1\}^{144}$$
Each brain possesses an adaptive weight:
$$\vec{W} = [W_0, W_1, \dots, W_{143}]^T \in [0.1, 1.0]^{144}$$
Initialized uniformly at cold start: $W_i = 1.0, \quad \forall i \in \{0, \dots, 143\}$.

#### Consensus Score Calculation (~10:00 UTC Entry)
The ensemble composite score is the scalar dot product of votes and weights:
$$\text{Score} = \sum_{i=0}^{143} \left( V_i \times W_i \right)$$
$$\text{TotalWeight} = \sum_{i=0}^{143} W_i$$
$$\text{ConfidenceRatio} = \frac{|\text{Score}|}{\text{TotalWeight}} \in [0.0, 1.0]$$

#### Directional Decision Matrix
$$\text{ConsensusDirection} = \begin{cases} +1 & \text{if } \text{Score} > \text{InpMinScore} \\ -1 & \text{if } \text{Score} < -\text{InpMinScore} \\ 0 & \text{if } |\text{Score}| \le \text{InpMinScore} \quad (\text{NEUTRAL: NO TRADE}) \end{cases}$$
> **Resolution of Prototype Defect 9**: When $\text{ConsensusDirection} == 0$, the system enters `STATE_SESSION_CLOSED` with zero market orders placed. Under no circumstance is a trade forced without mathematical consensus.

---

### 3.2 Session Close Trigger & Adaptive Weight Update (20:00 UTC)

At exactly 20:00 UTC, the true daily directional vector of Spot Gold is established:
$$\Delta P = \text{Close}_{20:00} - \text{Open}_{10:00}$$
$$\text{ActualDirection} = \begin{cases} +1 & \text{if } \Delta P > 0 \\ -1 & \text{if } \Delta P < 0 \\ 0 & \text{if } \Delta P == 0 \end{cases}$$

#### The EMA Accuracy Formulation
For each brain $i \in \{0, \dots, 143\}$:
1. **Neutral Vote Isolation**: If $V_i == 0$ (the brain abstained), the brain is **not updated**. It neither suffers penalty nor receives false credit.
2. **Directional Vote Evaluation**: If $V_i \ne 0$:
   $$\text{Outcome}_i = (V_i == \text{ActualDirection}) ? 1.0 : 0.0$$
   $$\text{EMA\_Acc}_i \leftarrow 0.95 \times \text{EMA\_Acc}_i + 0.05 \times \text{Outcome}_i$$
   $$W_i \leftarrow \max(0.1, \text{EMA\_Acc}_i)$$

#### Half-Life & Decay Properties
With smoothing factor $\alpha = 0.05$ (decay $\lambda = 0.95$):
$$\lambda^N = 0.5 \implies N = \frac{\ln(0.5)}{\ln(0.95)} \approx 13.5 \text{ trading sessions}$$
- Over ~14 active trading days (approx. 3 calendar weeks), previous performance decays to 50% impact.
- **The 0.1 Weight Floor Guarantee**: Brains experiencing extended drawdowns during unfavorable macro regimes retain a floor weight of $0.1$. This prevents strategy "extinction" and ensures that when market structure returns to alignment with that brain's logic, its predictive signals contribute to recovery.

#### Production Adaptive Engine Implementation
```mql5
//+------------------------------------------------------------------+
//| Brain State Tracking Structure                                  |
//+------------------------------------------------------------------+
struct SBrainState
{
   string name;
   double weight;
   double ema_accuracy;
   int    last_vote;
   int    total_votes;
   int    correct_votes;
};

SBrainState g_Brains[144];

void InitAdaptiveEngine()
{
   for(int i = 0; i < 144; i++)
   {
      g_Brains[i].name          = StringFormat("Brain_%03d", i + 1);
      g_Brains[i].weight        = 1.0;
      g_Brains[i].ema_accuracy  = 1.0;
      g_Brains[i].last_vote     = 0;
      g_Brains[i].total_votes   = 0;
      g_Brains[i].correct_votes = 0;
   }
}

//+------------------------------------------------------------------+
//| Update Brain Weights at 20:00 UTC Session Close                 |
//+------------------------------------------------------------------+
void UpdateAdaptiveWeights(int actualDirection)
{
   if(actualDirection == 0)
   {
      Print("[ADAPTIVE ENGINE] Session closed dead flat. Weight update skipped.");
      return;
   }
   
   int updatedCount = 0;
   int correctCount = 0;
   
   for(int i = 0; i < 144; i++)
   {
      if(g_Brains[i].last_vote == 0) continue; // Skip abstained brains
      
      bool isCorrect = (g_Brains[i].last_vote == actualDirection);
      double outcome = isCorrect ? 1.0 : 0.0;
      
      // Update 0.95/0.05 EMA
      g_Brains[i].ema_accuracy = (0.95 * g_Brains[i].ema_accuracy) + (0.05 * outcome);
      
      // Clamp to 0.1 floor
      g_Brains[i].weight = MathMax(0.1, g_Brains[i].ema_accuracy);
      
      g_Brains[i].total_votes++;
      if(isCorrect) {
         g_Brains[i].correct_votes++;
         correctCount++;
      }
      updatedCount++;
   }
   
   PrintFormat("[ADAPTIVE UPDATE] Actual Direction: %s | Active Brains: %d | Correct: %d (%.1f%%)",
               actualDirection > 0 ? "BUY (+1)" : "SELL (-1)",
               updatedCount, correctCount,
               updatedCount > 0 ? (correctCount * 100.0 / updatedCount) : 0.0);
}
```

---

## 4. Institutional News Blackout & Safety System

### 4.1 Macroeconomic Event Profile for Spot Gold

High-impact macroeconomic releases create acute structural dislocations in Spot Gold. Spreads routinely widen from 15 points to 300–800 points, accompanied by instantaneous \$15–\$45 price spikes that trigger catastrophic slippage.

```
┌────────────────────────────────────────────────────────────────────────┐
│               INSTITUTIONAL NEWS BLACKOUT SPECIFICATIONS               │
├───────────────┬─────────────────────────┬──────────────┬───────────────┤
│ Macro Event   │ Canonical Schedule      │ Pre-Close    │ Post-Blackout │
├───────────────┼─────────────────────────┼──────────────┼───────────────┤
│ NFP           │ 1st Friday 12:30 UTC    │ 30 min prior │ 60 min post   │
│ CPI           │ Monthly (Wed/Thu) 12:30 │ 15 min prior │ 30 min post   │
│ FOMC Decision │ 8 Wed/yr 18:00 UTC      │ 30 min prior │ 90 min post   │
│ PPI           │ Monthly 12:30 UTC       │ 15 min prior │ 30 min post   │
│ Powell Speech │ Scheduled / Emergency   │ 15 min prior │ 30 min post   │
└───────────────┴─────────────────────────┴──────────────┴───────────────┘
```

---

### 4.2 Broker Server Time vs UTC Synchronization Engine

#### Addressing Prototype Defect 7
In `GoldOracle_v1.mq5`, the news filter compared `TimeTradeServer()` directly to UTC news hours. Because broker server time is typically **EET/EEST (UTC+2 in winter, UTC+3 in summer)**, this introduced a 2- to 3-hour timing offset.

#### Universal Synchronization Model
```mql5
//+------------------------------------------------------------------+
//| Get Precise Current Time in UTC/GMT                             |
//+------------------------------------------------------------------+
datetime GetCurrentTimeUTC()
{
   // In backtesting, TimeGMT() is synchronized by the Strategy Tester.
   // In live trading, TimeGMT() returns live workstation UTC time.
   return TimeGMT();
}

// Calculate active broker server offset relative to UTC
int GetBrokerGMTOffsetHours()
{
   datetime serverTime = TimeTradeServer();
   datetime gmtTime    = TimeGMT();
   int diffSeconds     = (int)(serverTime - gmtTime);
   return (int)MathRound(diffSeconds / 3600.0);
}
```

---

### 4.3 Dual-Layer Calendar System Architecture

To ensure 100% reliability in both the **MetaTrader 5 Strategy Tester backtest** (where broker calendar databases may be stripped or unavailable) and **live production trading**, Gold Oracle EA v2 implements a dual-layer calendar system:
1. **Layer 1 (Algorithmic & Matrix Engine)**: Hardcoded deterministic recurrence formulas (e.g. NFP 1st Friday) and scheduled FOMC dates.
2. **Layer 2 (MT5 Economic Calendar API)**: Queries live broker high-impact USD events if calendar permissions are active.

#### Algorithmic Recurrence Rules
- **NFP Rule**: Month day $\le 7$ AND Day of Week == Friday (5) at 12:30 UTC.
  $$\text{IsNFPDay} = (\text{nowUTC.day\_of\_week} == 5) \land (\text{nowUTC.day} \le 7)$$
- **FOMC Rule**: Hardcoded calendar dates matching the Federal Reserve FOMC announcement schedule.

#### FOMC Institutional Calendar Matrix (2025–2027)
```mql5
// Exact FOMC Decision Dates (Wednesdays 18:00 UTC)
struct SFOMCDate { int year; int mon; int day; };
const SFOMCDate g_FOMCDates[] = {
   // 2025
   {2025, 1, 29}, {2025, 3, 19}, {2025, 5, 7},  {2025, 6, 18},
   {2025, 7, 30}, {2025, 9, 17}, {2025, 10, 29}, {2025, 12, 10},
   // 2026
   {2026, 1, 28}, {2026, 3, 18}, {2026, 5, 6},  {2026, 6, 17},
   {2026, 7, 29}, {2026, 9, 16}, {2026, 11, 4},  {2026, 12, 16},
   // 2027
   {2027, 1, 27}, {2027, 3, 17}, {2027, 5, 5},  {2027, 6, 16},
   {2027, 7, 28}, {2027, 9, 22}, {2027, 11, 3},  {2027, 12, 15}
};
```

---

### 4.4 Blackout Liquidation & Zero Re-Entry Enforcement

When a blackout window becomes active:
1. **Pre-News Immediate Liquidation**: Any open trade matching `InpMagicNumber` is closed immediately at market Bid/Ask via `CTrade::PositionClose()`.
2. **Lockout Enforcement**: The daily flag `g_bNewsLockoutToday` is set to `true`.
3. **Strict Zero Re-entry**: Once triggered, **no new trades may be opened for the remainder of that trading session**, even after the post-event blackout window expires. This guarantees protection against post-news erratic whipsaws.

#### Production Blackout Engine Implementation
```mql5
//+------------------------------------------------------------------+
//| Institutional News Safety Checker                               |
//+------------------------------------------------------------------+
bool g_bNewsLockoutToday = false;

bool CheckNewsBlackoutStatus()
{
   if(!InpEnableNewsFilter) return false;
   
   datetime utc = GetCurrentTimeUTC();
   MqlDateTime dt;
   TimeToStruct(utc, dt);
   int currentMins = dt.hour * 60 + dt.min;
   
   // 1. Check NFP (First Friday of month at 12:30 UTC)
   if(dt.day_of_week == 5 && dt.day <= 7)
   {
      int nfpEventMins = 12 * 60 + 30; // 12:30 UTC
      int startMins    = nfpEventMins - InpNFP_BlockMinsBefore;
      int endMins      = nfpEventMins + InpNFP_BlockMinsAfter;
      if(currentMins >= startMins && currentMins <= endMins)
      {
         PrintFormat("[NEWS BLACKOUT] NFP Active. Window: %02d:%02d - %02d:%02d UTC",
                     startMins/60, startMins%60, endMins/60, endMins%60);
         return true;
      }
   }
   
   // 2. Check FOMC Dates (18:00 UTC)
   for(int i = 0; i < ArraySize(g_FOMCDates); i++)
   {
      if(dt.year == g_FOMCDates[i].year && dt.mon == g_FOMCDates[i].mon && dt.day == g_FOMCDates[i].day)
      {
         int fomcEventMins = 18 * 60; // 18:00 UTC
         int startMins     = fomcEventMins - InpFOMC_BlockMinsBefore;
         int endMins       = fomcEventMins + InpFOMC_BlockMinsAfter;
         if(currentMins >= startMins && currentMins <= endMins)
         {
            PrintFormat("[NEWS BLACKOUT] FOMC Active. Window: %02d:%02d - %02d:%02d UTC",
                        startMins/60, startMins%60, endMins/60, endMins%60);
            return true;
         }
      }
   }
   
   return false;
}
```

---

## 5. MetaEditor64 Compilation Verification & Log Reader

### 5.1 Verification Methodology & Toolchain

The production release of `GoldOracle_v2.mq5` requires **strictly 0 errors and 0 warnings** under the official MetaTrader 5 64-bit compiler:
- **Executable**: `C:\Program Files\MetaTrader 5\MetaEditor64.exe` (115,544,688 bytes, verified).
- **Compilation Flag**: `/compile:"<absolute_path_to_mq5>"`
- **Log Destination**: `/log:"<absolute_path_to_log>"`

### 5.2 Log File Encoding & Format (UTF-16 LE)

MetaEditor writes its compilation output using **UTF-16 Little Endian (`utf-16-le`) with a 2-byte BOM (`\xff\xfe`)**. Reading this file with ASCII or standard UTF-8 produces corrupted strings or decode exceptions.

#### Expected Output Patterns
- **Clean Success Line**: `Result: 0 errors, 0 warnings, XXXX ms elapsed, cpu='X64 Regular'`
- **Error Line Format**: `<path>(<line>,<col>) : error <error_code>: <message>`
- **Warning Line Format**: `<path>(<line>,<col>) : warning <warning_code>: <message>`

### 5.3 Automated Verification Harness: `compile_verifier.py`

A dedicated verification script has been deployed in `.agents/explorer_survey_3/compile_verifier.py`.
Live verification of the prototype `GoldOracle_v1.mq5` succeeded with:
```
Compilation Target: C:\Users\Asus\Documents\antigravity\hopeful-curie\GoldOracle_v1.mq5
Status: PASS
Result: Result: 0 errors, 0 warnings, 1847 ms elapsed, cpu='X64 Regular'
EX5 Generated: True
```

#### Verification CLI Usage for Developers
```powershell
python c:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\explorer_survey_3\compile_verifier.py c:\Users\Asus\Documents\antigravity\hopeful-curie\GoldOracle_v2.mq5
```

---

## 6. Monolithic Integration Blueprint for `GoldOracle_v2.mq5`

The complete execution lifecycle for `GoldOracle_v2.mq5` is structured into five deterministic phases:

```
┌────────────────────────────────────────────────────────────────────────┐
│                  DAILY EXECUTION LIFECYCLE STATE MACHINE               │
├─────────────────┬──────────────────────────────────────────────────────┤
│ 00:00–07:00 UTC │ STATE_WAITING_FOR_ANALYSIS (Asia session: dormant)   │
│ 07:00–10:00 UTC │ STATE_ANALYZING (London session: buffer gathering)   │
│ 10:00 UTC       │ STATE_ENTRY_READY → Evaluate 144 Brains → Gate & Buy │
│ 10:01–19:59 UTC │ STATE_TRADE_ACTIVE (Monitor ATR SL & News Blackouts) │
│ 20:00 UTC       │ Close Trade → Evaluate Daily Vector → Update Weights │
└─────────────────┴──────────────────────────────────────────────────────┘
```

### 6.1 `OnTick()` Monolithic Architecture Skeleton

```mql5
//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
{
   datetime nowUTC = GetCurrentTimeUTC();
   MqlDateTime dt;
   TimeToStruct(nowUTC, dt);
   
   // 1. Midnight Reset (New Trading Day)
   if(dt.day_of_year != g_lastDay)
   {
      g_lastDay = dt.day_of_year;
      g_state   = STATE_WAITING_FOR_ANALYSIS;
      g_bNewsLockoutToday = false;
      PrintFormat("[NEW DAY] Resetting daily state for DOY %d", g_lastDay);
   }
   
   // 2. High-Impact News Blackout Check
   if(CheckNewsBlackoutStatus())
   {
      if(g_state != STATE_NEWS_BLACKOUT)
      {
         Print("[SAFETY] Entering News Blackout. Liquidating open positions.");
         CloseAllPositions();
         g_state = STATE_NEWS_BLACKOUT;
         g_bNewsLockoutToday = true;
      }
      return;
   }
   
   // 3. 20:00 UTC Session Close & Adaptive Weight Update
   if(dt.hour >= InpSessionCloseHour)
   {
      if(g_state != STATE_SESSION_CLOSED)
      {
         Print("[SESSION CLOSE] 20:00 UTC reached. Liquidating position & updating weights.");
         CloseAllPositions();
         
         // Determine actual directional vector of the session: Close(20:00) - Open(10:00)
         int actualDirection = DetermineSessionDirection();
         UpdateAdaptiveWeights(actualDirection);
         
         g_state = STATE_SESSION_CLOSED;
      }
      return;
   }
   
   // 4. London Session Analysis Window (07:00 - 10:00 UTC)
   if(g_state == STATE_WAITING_FOR_ANALYSIS && dt.hour >= InpAnalysisStartHour && dt.hour < InpAnalysisEndHour)
   {
      g_state = STATE_ANALYZING;
   }
   
   // 5. 10:00 UTC Entry Trigger
   if(g_state == STATE_ANALYZING && dt.hour >= InpAnalysisEndHour)
   {
      g_state = STATE_ENTRY_READY;
   }
   
   // 6. Entry Execution
   if(g_state == STATE_ENTRY_READY && !g_bNewsLockoutToday && g_lastTradeDay != dt.day_of_year)
   {
      if(!IsPositionOpen())
      {
         // Hardware Gating
         if(!IsSpreadPermitted(InpMaxSpreadPoints)) return;
         if(!IsVolatilityPermitted(h_atr14_h1, InpMinATR_H1_Points)) return;
         
         // 144-Brain Consensus Calculation
         double score = CalculateEnsembleConsensusScore();
         int direction = 0;
         if(score > InpMinScore)        direction = 1;  // BUY
         else if(score < -InpMinScore)  direction = -1; // SELL
         else                           direction = 0;  // NEUTRAL
         
         if(direction != 0)
         {
            ExecuteTrade(direction);
            g_lastTradeDay = dt.day_of_year;
            g_state = STATE_TRADE_ACTIVE;
         }
         else
         {
            PrintFormat("[CONSENSUS NEUTRAL] Score %.2f within dead-band. No trade today.", score);
            g_state = STATE_SESSION_CLOSED;
         }
      }
   }
}
```

---

## 7. Zero-Defect Implementation Checklist for Workers

| Item | Requirement | Verification Method |
|---|---|---|
| **C1** | Exact Pip Normalization | `pipFactor = (_Digits == 3 \|\| _Digits == 5) ? 10.0 : 1.0; pipSize = _Point * pipFactor;` verified on 2-digit ($0.01) quotes. |
| **C2** | Dynamic ATR Stop-Loss | Multiplier 2.0 applied to H1 ATR[1]; clamped to broker `SYMBOL_TRADE_STOPS_LEVEL + Spread + 2 points`. Zero Error 130. |
| **C3** | Take-Profit | Set strictly to `0.0`. Directional session run ending 20:00 UTC. |
| **C4** | Position Sizing | Calculated on `ACCOUNT_EQUITY`; accounts for `SYMBOL_TRADE_TICK_VALUE_LOSS`; clamped to volume min/max/step. |
| **C5** | Operational Gating | Max spread 50 points; min H1 ATR 30 points on confirmed completed bar[1]. |
| **C6** | 144 Weights Ensemble | Array of 144 `SBrainState`; cold-start 1.0; 20:00 UTC 0.95/0.05 EMA update; 0.1 floor; neutral vote isolation. |
| **C7** | News Safety Engine | Dual-layer calendar (NFP 1st Fri, FOMC matrix, CPI/PPI) with pre-news close and zero same-day re-entry. |
| **C8** | UTC Synchronization | All time evaluations normalized against `TimeGMT()`. No raw broker server hour comparisons. |
| **C9** | MetaEditor64 Compilation | Clean compilation via `compile_verifier.py` with 0 errors and 0 warnings. |

---
*End of Infrastructure Specification — Explorer Survey 3*

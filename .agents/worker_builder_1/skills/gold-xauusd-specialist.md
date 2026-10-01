---
name: gold-xauusd-specialist
description: >-
  Specialized skill for Gold (XAUUSD) trading in MQL4/MQL5. Covers pip
  normalization, spread management, session filters, ATR volatility gating,
  partial close patterns, daily trade limits, and Gold-specific EA design.
  Learned from 6+ Gold-specialist source files.
---

# Gold / XAUUSD Specialist — MQL4/MQL5 Skill

> Distilled from forensic analysis of: **Gold Master Pro.mq5**, **Gold Scalper.mq5**,
> **OSOK Gold Killer.mq5**, **Gold Reaper (MT4+MT5)**, **Aegis Quantum Lite.mq5**,
> **Aura Systems Final.mq5**.

---

## 1. Pip Normalization for XAUUSD

### Why Gold Is Different

Most Forex pairs have `_Digits == 4` (e.g. EURUSD 1.1234) or `_Digits == 5`
(5-digit broker: 1.12345). The standard pip-factor idiom used in Forex EAs is:

```mql5
// Standard Forex idiom — DO NOT use as-is for Gold
double pipFactor = (_Digits == 5 || _Digits == 3) ? 10.0 : 1.0;
```

**Gold (XAUUSD) is quoted to 2 decimal places** (e.g. 1923.45) on virtually every
broker — so `_Digits == 2`. The condition `_Digits == 5 || _Digits == 3` evaluates
`false`, making `pipFactor = 1.0`. **This is correct for Gold — do not change it.**

| Symbol    | Typical _Digits | _Point   | pipFactor | 1 pip value |
|-----------|-----------------|----------|-----------|-------------|
| EURUSD    | 5               | 0.00001  | 10        | 0.0001      |
| USDJPY    | 3               | 0.001    | 10        | 0.01        |
| **XAUUSD**| **2**           | **0.01** | **1**     | **0.01**    |
| XAGUSD    | 3               | 0.001    | 10        | 0.01        |

```mql5
// Gold-correct pip normalization
double pipFactor  = (_Digits == 5 || _Digits == 3) ? 10.0 : 1.0; // → 1.0 for Gold
double pipSize    = _Point * pipFactor;  // 0.01 * 1 = 0.01

// Convert a pip count to price distance
double PipsToPrice(double pips) { return pips * pipSize; }

// Usage
double sl_price = Bid - PipsToPrice(30);  // 30-pip SL on a Buy
double tp_price = Ask + PipsToPrice(60);  // 60-pip TP on a Buy
```

> [!IMPORTANT]
> **Never hard-code `* 0.0001`** for XAUUSD. Always derive the pip size from
> `_Point` so the EA works on both 2-digit and any future re-quoted feed.

---

## 2. Spread Management

Gold spread is highly variable. Entering during high-spread windows destroys the
risk/reward ratio of any fixed-pip strategy.

### Typical XAUUSD Spread Ranges

| Session          | Typical Spread (points) | Action              |
|------------------|-------------------------|---------------------|
| Asian (00-07 UTC)| 50 – 200+               | **Avoid entries**   |
| London (07-10 UTC)| 15 – 40                | Breakout only       |
| NY Open (13-16 UTC)| 10 – 30               | **Primary window**  |
| NY Afternoon     | 20 – 60                 | Trend continuation  |
| News events      | 200 – 1000+             | **Hard block**      |

```mql5
// Input parameter (from OSOK Gold Killer: InpMaxSpreadPips = 100)
input double InpMaxSpreadPips = 30.0;   // Tighter default for Gold Master Pro style

bool IsSpreadOK()
{
   double spreadPoints = (double)SymbolInfoInteger(_Symbol, SYMBOL_SPREAD);
   double spreadPips   = spreadPoints / pipFactor;  // pipFactor=1 for Gold,
                                                     // so spread in points == pips
   if(spreadPips > InpMaxSpreadPips)
   {
      Print("Spread too wide: ", spreadPips, " pips. Max allowed: ", InpMaxSpreadPips);
      return false;
   }
   return true;
}
```

> [!TIP]
> **OSOK Gold Killer** uses `InpMaxSpreadPips = 100` because it targets high-volatility
> breakouts where wide spread is acceptable. **Gold Master Pro** and **Aegis Quantum**
> use tighter gates (30–50 pts) suited to trend-following entries.

---

## 3. ATR Volatility Gate

Never trade Gold in dead markets. Use ATR(14) on the signal timeframe to gate entries.

```mql5
input int    ATR_Period    = 14;
input double ATR_Threshold = 50.0;  // Minimum ATR in points to permit entry

int atrHandle;
double atr[];

int OnInit()
{
   atrHandle = iATR(_Symbol, PERIOD_M15, ATR_Period);
   ArraySetAsSeries(atr, true);
   return INIT_SUCCEEDED;
}

bool IsVolatilityOK()
{
   if(CopyBuffer(atrHandle, 0, 0, 3, atr) < 3) return false;

   // atr[1] = last closed candle's ATR value (in price units, e.g. 0.85)
   // Convert to points: divide by _Point
   double atrPoints = atr[1] / _Point;

   if(atrPoints < ATR_Threshold)
   {
      Print("ATR too low: ", atrPoints, " pts. Min: ", ATR_Threshold);
      return false;  // Market is too quiet — skip entry
   }
   return true;
}
```

**Gold Master Pro** uses ATR(14) on M15. Empirically, when ATR(14) on M15 drops below
50 points (~\$0.50 per pip move), price is ranging and the 30-pip SL gets hit by noise.

---

## 4. Gold Master Pro — Complete Entry Logic

Signal chain: **M15 EMA(50) trend direction → M5 RSI(14) pullback confirmation → ATR gate → Spread gate → Session gate**

```mql5
// ─── Inputs (Gold Master Pro defaults) ───────────────────────────────────────
input int    EMA_Period      = 50;
input int    RSI_Period      = 14;
input double RSI_Buy_Level   = 40.0;   // RSI must be <= 40 for Buy pullback
input double RSI_Sell_Level  = 60.0;   // RSI must be >= 60 for Sell pullback
input double FixedSL_Pips    = 30.0;
input double FixedTP_Pips    = 60.0;
input int    SessionStart    = 7;      // UTC hour
input int    SessionEnd      = 13;     // UTC hour

// ─── Indicator handles ────────────────────────────────────────────────────────
int  emaHandleM15, rsiHandleM5;
double emaM15[], rsiM5[];

int OnInit()
{
   emaHandleM15 = iMA(_Symbol, PERIOD_M15, EMA_Period, 0, MODE_EMA, PRICE_CLOSE);
   rsiHandleM5  = iRSI(_Symbol, PERIOD_M5, RSI_Period, PRICE_CLOSE);
   atrHandle    = iATR(_Symbol, PERIOD_M15, ATR_Period);

   ArraySetAsSeries(emaM15, true);
   ArraySetAsSeries(rsiM5,  true);
   ArraySetAsSeries(atr,    true);
   return INIT_SUCCEEDED;
}

// ─── Session filter ───────────────────────────────────────────────────────────
bool IsSessionActive()
{
   MqlDateTime dt;
   TimeToStruct(TimeGMT(), dt);
   return (dt.hour >= SessionStart && dt.hour < SessionEnd);
}

// ─── Signal function ──────────────────────────────────────────────────────────
// Returns  1 = Buy signal
//         -1 = Sell signal
//          0 = No signal
int GetSignal()
{
   if(!IsSessionActive())  return 0;
   if(!IsSpreadOK())       return 0;
   if(!IsVolatilityOK())   return 0;

   // Populate buffers (need 2 bars minimum for confirmation)
   if(CopyBuffer(emaHandleM15, 0, 0, 3, emaM15) < 3) return 0;
   if(CopyBuffer(rsiHandleM5,  0, 0, 3, rsiM5)  < 3) return 0;

   double price = SymbolInfoDouble(_Symbol, SYMBOL_BID);

   // ── Buy logic: price above EMA50 (uptrend) AND RSI pulled back below 40 ──
   if(price > emaM15[1] && rsiM5[1] <= RSI_Buy_Level)
      return 1;

   // ── Sell logic: price below EMA50 (downtrend) AND RSI bounced above 60 ──
   if(price < emaM15[1] && rsiM5[1] >= RSI_Sell_Level)
      return -1;

   return 0;
}
```

---

## 5. Session Filter Reference Table

```
UTC Hour │ 00  01  02  03  04  05  06  07  08  09  10  11  12  13  14  15  16  17
─────────┼─────────────────────────────────────────────────────────────────────────
Session  │ ◄────────── ASIA ──────────► ◄── LONDON ──► ◄────────── NEW YORK ──────►
Gold Action│ ✗ AVOID     ✗ AVOID       ⚡ BREAKOUT    ✓ MAIN TREND  ✓ TREND  ~ FADE
```

| Session      | UTC Range | Gold Behavior                          | Recommended Action         |
|--------------|-----------|----------------------------------------|----------------------------|
| **Asia**     | 00–07     | Narrow range, high spread, thin liquidity | Avoid all entries       |
| **London**   | 07–10     | Breakout of Asian range, sharp moves   | Breakout strategies only   |
| **London→NY**| 10–13     | Overlap, institutional flow            | Trend continuation         |
| **NY Open**  | 13–16     | Highest volume, tightest spread        | **Primary entry window**   |
| **NY PM**    | 16–20     | Trend continuation or reversal         | Scale-outs, no new entries |
| **NY Close** | 20–24     | Gap risk building, spread widens       | Close all positions        |

**Gold Master Pro** uses `SessionStart=7, SessionEnd=13` UTC — covers London open
through NY open, capturing the highest-probability directional moves.

---

## 6. Partial Close Pattern

Gold strategies commonly take profits in stages. The **Gold Master Pro** approach:
close 50% at 30 pips, move SL to break-even + 5 pips.

```mql5
input double PartialClosePips = 30.0;   // First target
input double BEPlusPips       = 5.0;    // SL moved to open + this value after partial

void ManagePartialClose(ulong ticket)
{
   if(!PositionSelectByTicket(ticket)) return;

   double openPrice  = PositionGetDouble(POSITION_PRICE_OPEN);
   double currentSL  = PositionGetDouble(POSITION_SL);
   double currentTP  = PositionGetDouble(POSITION_TP);
   double lots       = PositionGetDouble(POSITION_VOLUME);
   long   posType    = PositionGetInteger(POSITION_TYPE);

   double partialTarget, newSL;

   if(posType == POSITION_TYPE_BUY)
   {
      partialTarget = openPrice + PipsToPrice(PartialClosePips);
      newSL         = openPrice + PipsToPrice(BEPlusPips);

      // Only act once: when current SL is still original (below open)
      if(SymbolInfoDouble(_Symbol, SYMBOL_BID) >= partialTarget && currentSL < openPrice)
      {
         double halfLots = NormalizeDouble(lots / 2.0,
                              (int)SymbolInfoInteger(_Symbol, SYMBOL_VOLUME_STEP > 0.01 ? 2 : 1));

         // Close half the position
         MqlTradeRequest req = {}; MqlTradeResult res = {};
         req.action   = TRADE_ACTION_DEAL;
         req.symbol   = _Symbol;
         req.volume   = halfLots;
         req.type     = ORDER_TYPE_SELL;
         req.price    = SymbolInfoDouble(_Symbol, SYMBOL_BID);
         req.position = ticket;
         req.comment  = "Partial close 50%";
         OrderSend(req, res);

         // Move SL to BE + 5 pips
         MqlTradeRequest modReq = {}; MqlTradeResult modRes = {};
         modReq.action   = TRADE_ACTION_SLTP;
         modReq.symbol   = _Symbol;
         modReq.position = ticket;
         modReq.sl       = newSL;
         modReq.tp       = currentTP;
         OrderSend(modReq, modRes);
      }
   }
   // Mirror logic for SELL positions (swap bid/ask, invert directions)
}
```

---

## 7. Daily Trade Limits & Profit Targets

```mql5
// ─── Inputs ───────────────────────────────────────────────────────────────────
input int    MaxTradesPerDay       = 3;      // Gold Master Pro default
input double DailyProfitTargetUSD = 100.0;  // Stop trading after this daily P&L

// ─── State ────────────────────────────────────────────────────────────────────
int    g_TodayTrades  = 0;
double g_TodayProfit  = 0.0;
datetime g_LastDay    = 0;

void UpdateDailyCounters()
{
   MqlDateTime now;
   TimeToStruct(TimeCurrent(), now);
   datetime today = StringToTime(StringFormat("%04d.%02d.%02d", now.year, now.mon, now.day));

   if(today != g_LastDay)          // New day — reset counters
   {
      g_LastDay     = today;
      g_TodayTrades = 0;
      g_TodayProfit = 0.0;
   }

   // Tally closed P&L from history
   HistorySelect(today, TimeCurrent());
   g_TodayProfit = 0.0;
   for(int i = 0; i < HistoryDealsTotal(); i++)
   {
      ulong ticket = HistoryDealGetTicket(i);
      if(HistoryDealGetString(ticket, DEAL_SYMBOL) != _Symbol) continue;
      if(HistoryDealGetInteger(ticket, DEAL_ENTRY) == DEAL_ENTRY_OUT)
      {
         g_TodayProfit  += HistoryDealGetDouble(ticket, DEAL_PROFIT)
                         + HistoryDealGetDouble(ticket, DEAL_SWAP)
                         + HistoryDealGetDouble(ticket, DEAL_COMMISSION);
         g_TodayTrades++;
      }
   }
}

bool CanOpenNewTrade()
{
   UpdateDailyCounters();
   if(g_TodayTrades >= MaxTradesPerDay)
   {
      Print("Daily trade limit reached: ", g_TodayTrades, "/", MaxTradesPerDay);
      return false;
   }
   if(g_TodayProfit >= DailyProfitTargetUSD)
   {
      Print("Daily profit target hit: $", g_TodayProfit, ". No more entries.");
      return false;
   }
   return true;
}
```

---

## 8. OSOK Grid Parameters & Max Exposure

**OSOK Gold Killer** uses a stepped grid with zone-based lot scaling:

```mql5
// ─── OSOK Grid Inputs ────────────────────────────────────────────────────────
input double InpLotFactor      = 1.60;   // Multiplier per grid leg
input int    InpMaxZoneLegs    = 8;      // Maximum open grid positions
input double InpZoneStep       = 25.0;  // Grid step in pips (= 0.25 price for Gold)
input double InpDailyTargetPct = 10.0;  // Close all when daily profit >= 10% of equity
input double InpBaseLot        = 0.01;  // Starting lot size

// ─── Max exposure calculator ─────────────────────────────────────────────────
void PrintMaxExposure()
{
   double totalLots = 0.0;
   double lot       = InpBaseLot;
   double totalZoneSize = 0.0;

   Print("=== OSOK Grid Exposure Analysis ===");
   for(int leg = 0; leg < InpMaxZoneLegs; leg++)
   {
      totalLots     += lot;
      totalZoneSize += InpZoneStep * leg;  // Distance from first entry
      PrintFormat("Leg %d: %.2f lots | Cumulative: %.2f lots | Zone range: %.1f pips",
                  leg + 1, lot, totalLots, totalZoneSize);
      lot = NormalizeDouble(lot * InpLotFactor, 2);
   }

   // At 1.60x per leg, leg 8 lot = 0.01 * 1.60^7 ≈ 0.27 lots
   // Total worst-case: ~0.64 lots across 175 pips zone
   // At Gold ~$10/pip per 0.1 lot → ~$64/pip total exposure at max grid
   PrintFormat(">>> MAX LOTS: %.2f | MAX ZONE: %.1f pips", totalLots, totalZoneSize);
}

bool IsGridSafe()
{
   if(PositionsTotal() >= InpMaxZoneLegs)
   {
      Print("Grid full: ", PositionsTotal(), " legs open. No new entries.");
      return false;
   }
   double equity   = AccountInfoDouble(ACCOUNT_EQUITY);
   double balance  = AccountInfoDouble(ACCOUNT_BALANCE);
   double ddPct    = (balance - equity) / balance * 100.0;
   if(ddPct > 20.0)  // Hard stop: >20% floating DD on Gold grid = abort
   {
      Print("CRITICAL: Drawdown ", ddPct, "% exceeds 20%. Halting grid.");
      return false;
   }
   return true;
}
```

> [!CAUTION]
> **InpLotFactor = 1.60** compounds aggressively. At 8 legs the final lot is
> `0.01 × 1.60^7 ≈ 0.27`. On a \$1,000 account this risks account wipe if Gold
> runs 175 pips against the grid. Always pair with a hard daily loss limit.

---

## 9. News Sensitivity & Mandatory Blackout

Gold reacts violently to macroeconomic releases. Minimum observed spikes:

| Event          | Typical Gold Spike | Direction  | Blackout Required |
|----------------|--------------------|------------|-------------------|
| NFP (1st Fri)  | 100 – 300 pips     | Both ways  | –30 min / +60 min |
| FOMC Statement | 150 – 500 pips     | Both ways  | –30 min / +90 min |
| CPI            | 80 – 200 pips      | Inverse USD| –15 min / +30 min |
| Powell Speech  | 50 – 150 pips      | Both ways  | Duration + 30 min |
| Geopolitical   | 200 – 1000 pips    | Safe-haven bid | Unpredictable |

```mql5
// Simple time-based news blackout (pair with an economic calendar feed for production)
// Blackout windows stored as GMT hours + minutes of known weekly events

struct SNewsWindow { int dayOfWeek; int hourGMT; int minuteGMT; int minsBeforeBlock; int minsAfterBlock; };

SNewsWindow g_NewsBlackouts[] =
{
   // dayOfWeek: 0=Sun,1=Mon,...5=Fri
   {5, 12, 30, 30, 60},   // NFP: typically 1st Friday 12:30 UTC — block 12:00-13:30
   {3, 18,  0, 30, 90},   // FOMC: typically Wednesday 18:00 UTC — block 17:30-19:30
   {2, 12, 30, 15, 30}    // CPI: typically 2nd/3rd Tue 12:30 UTC — block 12:15-13:00
};

bool IsNewsBlackout()
{
   MqlDateTime now;
   TimeToStruct(TimeGMT(), now);
   int currentMins = now.hour * 60 + now.min;

   for(int i = 0; i < ArraySize(g_NewsBlackouts); i++)
   {
      if(now.day_of_week != g_NewsBlackouts[i].dayOfWeek) continue;
      int eventMins  = g_NewsBlackouts[i].hourGMT * 60 + g_NewsBlackouts[i].minuteGMT;
      int blockStart = eventMins - g_NewsBlackouts[i].minsBeforeBlock;
      int blockEnd   = eventMins + g_NewsBlackouts[i].minsAfterBlock;
      if(currentMins >= blockStart && currentMins <= blockEnd)
      {
         Print("News blackout active. Event at ", g_NewsBlackouts[i].hourGMT,
               ":", g_NewsBlackouts[i].minuteGMT, " UTC.");
         return true;
      }
   }
   return false;
}
```

---

## 10. Known Gold-Specific Pitfalls

### 10.1 Weekend / Session-Open Gap Risk
Gold opens Sunday ~21:00 UTC. Gaps of 30–150 pips are common after geopolitical
weekend events. **Gold Reaper** mitigates this with virtual SL/TP managed in code
(no broker-side stops that could be skipped over during gaps).

```mql5
// Virtual SL check — run on every tick instead of relying on broker stop-out
void CheckVirtualStops(ulong ticket, double virtualSL, double virtualTP)
{
   if(!PositionSelectByTicket(ticket)) return;
   long posType = PositionGetInteger(POSITION_TYPE);
   double bid   = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   double ask   = SymbolInfoDouble(_Symbol, SYMBOL_ASK);

   bool slHit = (posType == POSITION_TYPE_BUY && bid <= virtualSL) ||
                (posType == POSITION_TYPE_SELL && ask >= virtualSL);
   bool tpHit = (posType == POSITION_TYPE_BUY && bid >= virtualTP) ||
                (posType == POSITION_TYPE_SELL && ask <= virtualTP);

   if(slHit || tpHit)
   {
      MqlTradeRequest req = {}; MqlTradeResult res = {};
      req.action   = TRADE_ACTION_DEAL;
      req.symbol   = _Symbol;
      req.volume   = PositionGetDouble(POSITION_VOLUME);
      req.type     = (posType == POSITION_TYPE_BUY) ? ORDER_TYPE_SELL : ORDER_TYPE_BUY;
      req.price    = (posType == POSITION_TYPE_BUY) ? bid : ask;
      req.position = ticket;
      req.comment  = slHit ? "Virtual SL" : "Virtual TP";
      OrderSend(req, res);
   }
}
```

### 10.2 Broker Minimum Stop Distance
During volatile Gold sessions, many brokers dynamically increase the minimum
stop distance (freeze zone). Always validate SL distance after calculating it:

```mql5
double GetSafeSL(int direction, double entryPrice, double desiredSLPips)
{
   long   stopLevel  = SymbolInfoInteger(_Symbol, SYMBOL_TRADE_STOPS_LEVEL);
   double minDist    = stopLevel * _Point;
   double wantedDist = PipsToPrice(desiredSLPips);
   double safeDist   = MathMax(wantedDist, minDist + _Point);  // At least 1 point buffer

   return (direction == 1) ? entryPrice - safeDist
                           : entryPrice + safeDist;
}
```

### 10.3 Spread Spike During Events
**OSOK Gold Killer** allows `InpMaxSpreadPips=100` for high-volatility breakout
plays. For trend-following EAs (Gold Master Pro, Aegis Quantum), use 30–50 pt max.
Log spread violations — if 80%+ of entry attempts are blocked by spread, the
`InpMaxSpreadPips` is too tight for that broker/session combination.

### 10.4 Lot Normalization on Gold
Gold's minimum lot step is typically `0.01` but volume step rounding errors cause
`OrderSend` rejections. Always normalize:

```mql5
double NormalizeLot(double rawLot)
{
   double minLot  = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double maxLot  = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
   double lotStep = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   double lot     = MathFloor(rawLot / lotStep) * lotStep;
   return MathMax(minLot, MathMin(maxLot, lot));
}
```

---

## 11. Library Reference: LotSizing.mqh & TrailingStop.mqh for Gold

### LotSizing.mqh — Recommended Functions

| Function              | Gold Usage                                        |
|-----------------------|---------------------------------------------------|
| `CalcRiskLot()`       | Pass `FixedSL_Pips=30` and `RiskPct` for position sizing |
| `CalcFixedLot()`      | Used by Gold Scalper (`tp_dollars=2.0, sl_dollars=1.5`)  |
| `NormalizeLot()`      | Always call before `OrderSend` on Gold            |
| `GetMaxGridLot()`     | OSOK pattern: cap cumulative grid exposure        |

```mql5
// Example: Risk-based lot sizing for Gold (30-pip SL)
// Assumes LotSizing.mqh provides CalcRiskLot(symbol, sl_pips, risk_pct)
double lots = CalcRiskLot(_Symbol, FixedSL_Pips, 1.0);   // 1% risk per trade
lots        = NormalizeLot(lots);
```

### TrailingStop.mqh — Recommended Functions

| Function                    | Gold Usage                                              |
|-----------------------------|---------------------------------------------------------|
| `TrailATR()`                | Aura Systems Final: H4 ATR trail after D1 trend lock-in |
| `TrailFixed()`              | Gold Scalper: `trail_start=1.5` dollars, step=0.5 dollars |
| `TrailBreakEven()`          | Gold Master Pro: move SL to BE after partial close      |
| `TrailBasket()`             | Gold Reaper: single trail on aggregate basket P&L       |

```mql5
// Gold Scalper dollar-based trail (trail_start=1.5, step=0.5)
// Assumes TrailingStop.mqh provides TrailFixed(ticket, start_pips, step_pips)
double startPips = (1.5 / SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE))
                   * SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE) / _Point;
TrailFixed(posTicket, startPips, startPips / 3.0);

// Aegis Quantum Lite: trail only after 1 candle confirmation
// OneEntryPerCandle guard (reset flag on new M5 bar)
static datetime g_LastBarTime = 0;
if(iTime(_Symbol, PERIOD_M5, 0) != g_LastBarTime)
{
   g_LastBarTime    = iTime(_Symbol, PERIOD_M5, 0);
   g_EntryThisBar   = false;
}
```

---

## Quick Reference Cheat Sheet

```
┌─────────────────────────────────────────────────────────────┐
│              GOLD (XAUUSD) EA PARAMETER DEFAULTS            │
├──────────────────────┬──────────────────────────────────────┤
│ _Digits              │ 2  (_Point = 0.01)                   │
│ pipFactor            │ 1.0  (not 10x like Forex)            │
│ pipSize              │ 0.01                                 │
│ FixedSL_Pips         │ 30  (= $0.30 distance)               │
│ FixedTP_Pips         │ 60  (1:2 RR minimum)                 │
│ ATR_Threshold        │ 50 pts (M15 ATR)                     │
│ MaxSpread (trend)    │ 30 pts                               │
│ MaxSpread (breakout) │ 100 pts                              │
│ Session (UTC)        │ 07:00 – 13:00                        │
│ MaxTradesPerDay      │ 3                                    │
│ PartialClose         │ 50% at 30 pips                       │
│ BE after partial     │ Open + 5 pips                        │
│ News blackout        │ NFP: –30/+60 min | FOMC: –30/+90 min│
│ Grid multiplier      │ 1.60× per leg (OSOK)                 │
│ Max grid legs        │ 8 (OSOK)                             │
│ Grid step            │ 25 pips (OSOK)                       │
└──────────────────────┴──────────────────────────────────────┘
```

---

*This skill was distilled from forensic analysis of 6 Gold-specialist EA source files.
For general MQL5 architecture, EA lifecycle, and indicator patterns, see the parent
`production-mql-engineering` skill.*

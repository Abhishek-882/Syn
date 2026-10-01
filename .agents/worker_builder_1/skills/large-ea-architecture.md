---
name: large-ea-architecture
description: >-
  Specialized skill for complex, large-scale EA architecture patterns in MQL4/MQL5.
  Covers multi-mode grid systems (Beast EA), GUI dashboard design (BigRise EA),
  multi-timeframe filtering (Kirin EA), advanced money management (Gold Hunt EA),
  stealth order masking, and EABuilder/FxDreema generated patterns. Learned from
  Beast EA (312KB), BigRise EA (149KB), Kirin EA (181KB), Gold Hunt EA (493KB),
  EuroScalper, AGI_FX v2, EA_TheOne, Ea_Scalper_FX_Finist.
---

# Large-Scale EA Architecture — Specialized Skill

> **Learned from**: Agent A analysis of 8 large, multi-strategy Expert Advisors
> Beast EA (312KB), Gold Hunt EA (493KB), Kirin EA (181KB), BigRise EA (149KB)
> EuroScalper, AGI_FX v2, EA_TheOne, Ea_Scalper_FX_Finist

---

## Architecture Concept Map

```
Large EA Architecture Patterns
├── Multi-Mode Grid (Beast EA — Steve Hopwood)
│   ├── WhiteBox mode: trend-following grid
│   ├── CounterTrend mode: fades extreme moves
│   ├── Re-Entry Line logic: dynamic level recalculation
│   ├── WinUser32.mqh + stdlib.mqh dependency
│   └── Basket equity trail across all positions
│
├── GUI Panel System (BigRise EA)
│   ├── Object-oriented UI components
│   ├── Rectangle label background panels
│   ├── Real-time P&L display per position
│   └── ChartRedraw() batching (one call per tick)
│
├── Multi-TF Kirin Dashboard (Kirin EA)
│   ├── Queries indicators across ALL timeframes
│   ├── Alignment matrix: M1/M5/M15/H1/H4/D1
│   ├── Only trade when N/6 timeframes agree
│   └── Color-coded dashboard per TF direction
│
├── EABuilder / FxDreema Architecture (Gold Hunt EA)
│   ├── Block-chain generated modular code
│   ├── Labouchere, D'Alembert, 1-3-2-6 MM
│   ├── DrawObject() chart markers for every trade
│   └── Extremely defensive error handling blocks
│
└── Scalper Architecture (AK-47, Ea_Scalper_FX_Finist)
    ├── Spread gate before every order
    ├── Slippage parameter explicitly set
    ├── Tick-level entry precision
    └── No open overnight positions
```

---

## Beast EA — Multi-Mode Grid Architecture

```mql4
// Steve Hopwood's "The Beast" — key parameters extracted:
extern bool   WhiteBox      = true;   // true=trend, false=countertrend
extern bool   CounterTrend  = false;  // fade momentum instead
extern int    GridSize       = 50;    // pip spacing between grid levels
extern double LotSize        = 0.01;  // base lot
extern double MaxLots        = 5.0;   // maximum total lots exposure

// Re-Entry Line Pattern:
// After a position is closed at profit, calculate a new re-entry level
// based on the market structure (recent high/low + buffer)
double CalcReEntryLine(bool isBuy)
{
   if(isBuy)
      return NormalizeDouble(iLow(NULL, 0, 1) - GridSize * Point, Digits);
   else
      return NormalizeDouble(iHigh(NULL, 0, 1) + GridSize * Point, Digits);
}

// Countertrend Mode:
// Opens positions AGAINST the current trend
// Uses equity-based close: close ALL when basket profit >= target
// Much more dangerous — requires tighter equity stops
```

---

## BigRise EA — GUI Dashboard Architecture (MT4)

```mql4
// Object-Oriented UI pattern used in BigRise EA:

// Initialize all objects once in OnInit()
void CreateDashboard()
{
   // Background rectangle
   ObjectCreate("bg_panel", OBJ_LABEL, 0, 0, 0);
   ObjectSet("bg_panel", OBJPROP_XDISTANCE, 10);
   ObjectSet("bg_panel", OBJPROP_YDISTANCE, 30);

   // P&L label
   ObjectCreate("lbl_pnl", OBJ_LABEL, 0, 0, 0);
   ObjectSet("lbl_pnl", OBJPROP_CORNER, CORNER_LEFT_UPPER);
   ObjectSetString(0, "lbl_pnl", OBJPROP_TEXT, "P&L: $0.00");
   ObjectSetInteger(0, "lbl_pnl", OBJPROP_COLOR, clrWhite);
}

// Update only text content in OnTick() — NOT recreate objects
void UpdateDashboard()
{
   double totalPnl = CalculateTotalPnL();
   string pnlText  = StringFormat("P&L: $%.2f", totalPnl);
   ObjectSetString(0, "lbl_pnl", OBJPROP_TEXT, pnlText);
   // ONE ChartRedraw call at end — never per object
   ChartRedraw(0);
}
```

---

## Kirin EA — Multi-Timeframe Alignment Matrix

```mql4
// Query indicator value on each timeframe:
// Returns signal direction: 1=bull, -1=bear, 0=neutral

int GetTFSignal(int period)
{
   double maFast = iMA(NULL, period, FastMA, 0, MODE_EMA, PRICE_CLOSE, 0);
   double maSlow = iMA(NULL, period, SlowMA, 0, MODE_EMA, PRICE_CLOSE, 0);
   if(maFast > maSlow) return 1;
   if(maFast < maSlow) return -1;
   return 0;
}

// Build alignment score across 6 timeframes
int GetAlignmentScore()
{
   int score = 0;
   int tfs[] = {PERIOD_M1, PERIOD_M5, PERIOD_M15, PERIOD_H1, PERIOD_H4, PERIOD_D1};
   for(int i = 0; i < 6; i++)
      score += GetTFSignal(tfs[i]);
   return score;  // +6 = all bull, -6 = all bear, anything else = mixed
}

// Only trade when strongly aligned
void CheckEntry()
{
   int score = GetAlignmentScore();
   if(score >= MinAlignment)     OpenBuy();   // e.g., MinAlignment = 4
   if(score <= -MinAlignment)    OpenSell();
}
```

---

## Gold Hunt EA — EABuilder/FxDreema Block Patterns

```mql4
// EABuilder/FxDreema generated code characteristics:
// 1. Massive defensive error checking after every OrderSend
// 2. Chart object annotation for every trade event
// 3. MM algorithms as isolated function blocks

// Labouchere block (isolated MM function):
double GetLabouchereLot()
{
   if(seqSize == 0) ResetSequence();  // Goal reached, restart
   if(seqSize == 1) return seqArr[0] * BaseLot;
   return (seqArr[0] + seqArr[seqSize-1]) * BaseLot;
}

void AfterLabouchere(bool won)
{
   if(won)
   {
      // Remove first and last from sequence
      ArrayCopy(seqArr, seqArr, 0, 1, seqSize-2);
      seqSize -= 2;
   }
   else
   {
      // Append the last bet to end of sequence
      seqArr[seqSize] = seqArr[0] + seqArr[seqSize-1];
      seqSize++;
   }
}
```

---

## Virtual SL/TP — Stealth Order Masking

```mql4
// Gold Hunt EA, Gold Reaper: hide SL/TP from broker
// Useful when brokers widen spread to trigger stops
// WARNING: if connection drops, positions have no protection!

double vSL[], vTP[];  // Stored in-memory

void CheckVirtual()
{
   for(int i = OrdersTotal()-1; i >= 0; i--)
   {
      OrderSelect(i, SELECT_BY_POS, MODE_TRADES);
      if(OrderMagicNumber() != MagicNumber) continue;
      double bid = MarketInfo(OrderSymbol(), MODE_BID);
      double ask = MarketInfo(OrderSymbol(), MODE_ASK);
      int    idx = GetTicketIndex(OrderTicket());

      if(OrderType() == OP_BUY)
      {
         if(bid >= vTP[idx]) { OrderClose(OrderTicket(), OrderLots(), bid, 3); }
         if(bid <= vSL[idx]) { OrderClose(OrderTicket(), OrderLots(), bid, 3); }
      }
   }
}
```

---

## Multi-Symbol Management Pattern

```mql5
// Scan all market watch symbols (Beast EA multi-pair approach)
void ScanAllSymbols()
{
   int total = SymbolsTotal(true);  // true = only market watch symbols
   for(int i = 0; i < total; i++)
   {
      string sym = SymbolName(i, true);
      // Apply strategy to each symbol with its own magic number
      int symMagic = MagicBase + i;
      CheckAndTradeSymbol(sym, symMagic);
   }
}
```

---

## EABuilder-Generated Code Signatures

When you see these patterns, the EA was likely generated by EABuilder or FxDreema:
1. Every `OrderSend()` followed by `if(ticket < 0) { Print("Error: ", GetLastError()); }`
2. Lot sizing as separate `CalculateLots()` function returning `NormalizeDouble()`
3. `ObjectCreate("Trade_" + TimeToStr(TimeCurrent()), OBJ_ARROW, ...)` chart markers
4. Trailing stop as a standalone `ManageTrail()` function called at top of `start()`
5. Global arrays for sequence management (Labouchere, 1-3-2-6)

---

## Library Reference

- `lib/shared/LotSizing.mqh` → `LotMartingale()`, `LotGrid()`
- `lib/shared/TrailingStop.mqh` → `GetBasketProfit()`, `CloseBasketIfProfit()`

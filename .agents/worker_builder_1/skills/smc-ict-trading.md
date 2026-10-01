---
name: smc-ict-trading
description: >-
  Specialized skill for Smart Money Concepts (SMC) and ICT (Inner Circle Trader)
  methodology in MQL4/MQL5. Covers CHoCH, BOS, Order Blocks, Fair Value Gaps,
  Kill Zones, Judas Swing setups, Premium/Discount zones, and multi-timeframe bias.
  Learned from deep forensic analysis of: Bread & Butter Engine EA, SmartMoneyConcepts
  V5 (LuxAlgo port), Smart Money Order Block, KCI Embedded Sniper, Gold Breakout EA,
  XAUUSD Retest EA, Hand of God EA.
---

# SMC / ICT Trading — Specialized Skill

> **Learned from**: 7 source files forensically analyzed by Agent C
> Bread & Butter Engine EA, SmartMoneyConcepts V5, Smart Money Order Block (197 KB),
> KCI Embedded Sniper, Gold Breakout, XAUUSD Retest, Hand of God EA

---

## Core Concept Map

```
ICT / SMC Methodology
├── Market Structure
│   ├── Swing Highs / Swing Lows (HH, HL, LH, LL)
│   ├── Break of Structure (BOS) — trend continuation break
│   ├── Change of Character (CHoCH) — first counter-trend break
│   │   ├── Internal CHoCH (short lookback, early signal)
│   │   └── Swing CHoCH (longer lookback, confirmed reversal)
│   ├── Ex-Guard Logic — prevents double-counting CHoCH on major pivots
│   └── Equal Highs / Equal Lows — liquidity pool detection
├── Order Flow
│   ├── Liquidity Sweeps (stop hunts above EQH / below EQL)
│   ├── Order Blocks (OB) — last opposing candle before impulse
│   │   ├── Bullish OB = last bearish candle before bullish BOS
│   │   ├── Bearish OB = last bullish candle before bearish BOS
│   │   ├── Internal OBs (short-term, teal/orange)
│   │   └── Swing OBs (major institutional, deep blue/red)
│   └── Fair Value Gaps (FVG / Imbalance)
│       ├── Bullish FVG: Low[i-1] > High[i+1]
│       └── Bearish FVG: High[i-1] < Low[i+1]
├── Bias Determination
│   ├── Higher Timeframe (HTF) bias via swing structure
│   ├── Current Timeframe (CTF) CHoCH direction
│   ├── Intra Timeframe (ITF) internal structure
│   └── Dashboard display: CHoCH Bullish/Bearish per TF
├── Trade Setup (Judas Swing — Bread & Butter Engine)
│   ├── Step 1: Identify Kill Zone (London 02-05 NY, NY 08:20-11 NY)
│   ├── Step 2: Track session High/Low → calculate Equilibrium (midpoint)
│   ├── Step 3: Wait for Sweep (price grabs liquidity at session extreme)
│   ├── Step 4: Confirm MSS (Market Structure Shift — CHoCH after sweep)
│   └── Step 5: Enter at MSS level, SL beyond swept extreme + buffer
└── Premium / Discount Zones
    ├── Equilibrium = (Range High + Range Low) / 2
    ├── Premium (sell zone) = price > 50% of range
    ├── Discount (buy zone) = price < 50% of range
    └── OTE (Optimal Trade Entry) = 61.8%–78.6% Fibonacci level
```

---

## The Judas Swing — Full Implementation

**Source**: Bread & Butter Engine EA (Allan Munene Mutiiria)

```mql5
// COMPLETE JUDAS SWING ENTRY SEQUENCE:

// 1. Session Management
void UpdateSessionState()
{
   // Track active Kill Zone (London/NY/Asia)
   // Record session High and Low as price develops
   // Compute Equilibrium = (sessionHigh + sessionLow) / 2
}

// 2. Liquidity Sweep Detection
bool SweepDone(bool isBullish)
{
   // Bullish sweep: price traded below session LOW (sweeps sell stops)
   //   then closes back above session LOW
   // Bearish sweep: price traded above session HIGH (sweeps buy stops)
   //   then closes back below session HIGH
   if(isBullish)
      return (g_lowestLow < g_sessionLow && Close[0] > g_sessionLow);
   else
      return (g_highestHigh > g_sessionHigh && Close[0] < g_sessionHigh);
}

// 3. Market Structure Shift (MSS) — CHoCH after sweep
void TryArm()
{
   // ARM the EA once sweep is confirmed
   // Record g_mssLevel = last significant swing low (for bull sweep)
   //   = last significant swing high (for bear sweep)
   // g_setupExtreme = the swept price level (SL anchor)
}

bool CheckArmedForEntry()
{
   // ENTRY: price closes THROUGH g_mssLevel
   // Bull: Close > g_mssLevel (swept lows, price now breaking above prev swing)
   // Bear: Close < g_mssLevel
   return (g_armed && Close[0] > g_mssLevel);
}

// 4. Stop Loss placement
double GetStructuralSL(bool isBuy, int bufferPoints)
{
   // SL = swept extreme + buffer
   // For bull entry: SL = g_setupExtreme (session low that was swept) - buffer
   return isBuy
      ? g_setupExtreme - bufferPoints * _Point
      : g_setupExtreme + bufferPoints * _Point;
}

// 5. Take Profit via Risk:Reward ratio
double GetTP(double entry, double sl, double rrRatio)
{
   double risk = MathAbs(entry - sl);
   return entry + (entry > sl ? 1 : -1) * risk * rrRatio;
}
```

---

## Order Block Detection (Smart Money Order Block — 197 KB)

```mql5
// BULLISH ORDER BLOCK:
// = Last bearish candle before the impulse that caused an upward BOS

// ENGULFING IMBALANCE VALIDATION (from Smart_Money_Order_Block_Choc):
// The OB is only valid if the impulse candle LEFT BEHIND an FVG
// (meaning the move was so strong it skipped price — institutional)
bool IsValidBullOB(int obBar, int bsBar)
{
   // Check FVG left behind by impulse:
   // Low[obBar-1] should be > High[bsBar+1] (gap between OB's left neighbor and impulse's right)
   bool fvgPresent = iLow(NULL, 0, obBar-1) >= iHigh(NULL, 0, bsBar+1);
   return fvgPresent;
}

// MITIGATION:
// OB is "used up" when price enters its body
// High/Low mode: mitigated when price enters OB top (bull) or bottom (bear)
// Close mode: mitigated only when price CLOSES inside OB body
```

---

## Ex-Guard Logic (SmartMoneyConcepts V5 — LuxAlgo port)

The most sophisticated pattern: prevents counting an internal CHoCH that occurs **exactly on a major swing pivot** — which would be double-counted as both internal and swing structure.

```mql5
// Ex-Guard ensures internal CHoCH ≠ swing pivot level
// pivHLevel = current internal pivot high being tested
// swPivH_ex = the last confirmed SWING pivot high
if(pivHLevel != swPivH_ex)  // Only count if NOT on exact swing pivot
{
   // Valid internal CHoCH — record and draw
   DrawInternalCHoCH(pivHLevel, "CHoCH");
}
```

---

## Multi-Timeframe Bias Dashboard

**Source**: SmartMoneyConcepts V5 (InpHTFPeriod, InpITFPeriod)

```mql5
// Three timeframe levels tracked simultaneously:
// HTF (Higher): H4 by default
// CTF (Current): your chart timeframe
// ITF (Intra): M15 by default

string GetBias(ENUM_TIMEFRAMES tf)
{
   // Run swing detection on each TF independently
   // Return "Bullish CHoCH" / "Bearish CHoCH" / "Bullish BOS" etc.
   // Displayed in dashboard panel
}
// Entry only when HTF bias aligns with CTF CHoCH direction
```

---

## Kill Zone Reference

| Session | New York Time | Character |
|---------|--------------|-----------|
| **Asia** | 20:00 – 00:00 | Range formation, liquidity builds |
| **London** | 02:00 – 05:00 | Range expansion, London banks push price |
| **New York** | 08:20 – 11:00 | Highest volume, true direction revealed |
| **London Close** | 11:00 – 12:00 | Partial reversal, position squaring |

---

## Library Reference

Use `lib/shared/SMCStructure.mqh`:
- `IsSwingHigh/Low()` — pivot detection
- `DetectStructureBreak()` — CHoCH / BOS
- `DetectBullFVG/BearFVG()` — FVG with mitigation
- `CheckOBMitigation()` — OB zone tracking
- `CalcPDZones()` — Equilibrium + OTE levels
- `IsInKillZone()` — Kill zone time gate
- `IsEqualHigh/Low()` — EQH/EQL liquidity pools

---

## ⚠️ Pitfalls

1. **CHoCH ≠ BOS**: CHoCH is the FIRST counter-trend break (reversal signal). BOS is continuation.
2. **Sweep required before MSS**: Entry without a confirmed sweep is premature.
3. **OB without FVG**: OBs validated by an engulfing imbalance are higher probability.
4. **HTF bias flip**: Always re-check HTF bias after it fires — if it flips during setup, disarm.
5. **InpMaxWaitBars**: Cap the number of bars the EA waits for an MSS after sweep — stale sweeps fail.

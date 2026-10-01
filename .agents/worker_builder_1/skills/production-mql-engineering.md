---
name: production-mql-engineering
description: >-
  Deep MQL4/MQL5 Expert Advisor and Indicator engineering skill built from
  forensic analysis of 57+ source files. Covers EA architecture (scalping,
  grid/martingale, SMC/ICT, arbitrage, hedging), indicator algorithms (QQE,
  NRTR, FVG, CHoCH/BOS, Order Blocks), Gold-specific XAUUSD patterns, MT4 vs
  MT5 API differences, and a reusable code library (LotSizing, TrailingStop,
  SMCStructure). Activate when writing, debugging, analyzing, or reviewing any
  MetaTrader EA or indicator source code.
---

# Production MQL Engineering Skill

> **Synthesized from 57 MQ4/MQ5 source files** — Beast EA, Gold Reaper (611 KB),
> cm_EA_TrailingStop (910 KB), SmartMoneyConcepts V5, Bread & Butter Engine,
> Arbitrage EA, Hon-Matrix, NRTR EA, AK-47 Scalper, EuroScalper, and more.
> The largest dataset of production MQL source code analyzed by this agent.

---

## When to Use This Skill

| Trigger | Example Prompt |
|---------|---------------|
| Writing a new EA | "Write an EA that trades the London kill zone using SMC" |
| Debugging an existing EA | "My OrderModify returns Error 130, fix it" |
| Explaining MQL concepts | "What is CHoCH vs BOS in Smart Money Concepts?" |
| Analyzing source code | "Reverse engineer this Gold EA and explain its logic" |
| Building indicators | "Create a QQE indicator in MQL5" |
| Risk management | "Add martingale lot sizing to my EA" |
| MT4 → MT5 migration | "Port this MQ4 EA to MT5" |
| Gold / XAUUSD EAs | "Fix the pip calculation for Gold" |

---

## 🏗️ Core Library Files

Located in `skills/production-mql-engineering/lib/shared/`:

| File | Contents |
|------|---------|
| `LotSizing.mqh` | Fixed, Risk%, ATR, Martingale, Labouchere, D'Alembert lot sizing |
| `TrailingStop.mqh` | Classic trail, Break-even, ATR chandelier, NRTR, Basket trail |
| `SMCStructure.mqh` | Swing pivots, CHoCH/BOS, FVG, Order Blocks, Kill Zones, OTE |

---

## 📚 Reference Documents

All in `skills/production-mql-engineering/references/`:

| Reference | Topic |
|-----------|-------|
| `concept_tree.md` | **Master knowledge taxonomy** — all patterns traced to source files |
| `strategy_patterns.md` | EA strategy archetypes with code excerpts |
| `indicator_algorithms.md` | Full indicator formula extraction (QQE, NRTR, CoG, MACD TV Style) |
| `mql4_vs_mql5.md` | API migration guide with side-by-side code |
| `risk_management.md` | Lot sizing, trailing, drawdown control patterns |
| `gold_xauusd_patterns.md` | Gold-specific pip, spread, session, and news patterns |
| `aura_systems_reverse.md` | Complete reverse engineering of Aura Systems EA v1.25/v1.26/Final |

---

## ⚡ Quick Reference: Most Common Patterns

### 1. Lot Sizing (Risk % of Balance)
```mql5
// From: Gold Master Pro, Bread & Butter Engine, AK-47 Scalper
double lot = (AccountInfoDouble(ACCOUNT_BALANCE) * riskPercent / 100.0)
             / (slPips * pipFactor * pointValue);
lot = NormalizeDouble(MathMax(minLot, MathMin(maxLot, lot)), lotDecimals);
```

### 2. ATR-Based Stop Loss
```mql5
// From: Gold Master Pro (ATR_Period_M15=14, ATR_Threshold=50 pts)
double atr[];
ArraySetAsSeries(atr, true);
CopyBuffer(atr_handle, 0, 0, 2, atr);
double sl = atr[1] * 1.5;  // 1.5× ATR as stop distance
```

### 3. Kill Zone Time Filter
```mql5
// From: Bread & Butter Engine
// London: 02:00-05:00 NY, New York: 08:20-11:00 NY
bool InKillZone(int startH, int startM, int endH, int endM, int gmtOffset)
{
   MqlDateTime dt; TimeToStruct(TimeCurrent(), dt);
   int nyH = (dt.hour - gmtOffset - 5 + 24) % 24;
   int now = nyH * 60 + dt.min;
   return (now >= startH*60+startM && now < endH*60+endM);
}
```

### 4. Break-Even Stop
```mql5
// From: Gold Master Pro, cm_EA_TrailingStopOrders
if(position.Type() == POSITION_TYPE_BUY && Bid - pos_open >= triggerPips * pip)
{
   double newSL = pos_open + bufferPips * pip;
   if(newSL > position.StopLoss())
      trade.PositionModify(ticket, newSL, position.TakeProfit());
}
```

### 5. Swing Pivot Detection (SMC)
```mql5
// From: SmartMoneyConcepts V5, Bread & Butter Engine
bool IsSwingHigh(const double &h[], int i, int strength=5)
{
   for(int j=i-strength; j<=i+strength; j++)
      if(j!=i && h[j]>=h[i]) return false;
   return true;
}
```

### 6. Martingale Lot Grid
```mql5
// From: Beast EA, BigRise EA, Gold Hunt EA, OSOK Gold Killer
// lot_n = baseLot * multiplier^level (OSOK: mult=1.6, max 8 legs)
double lot = NormalizeDouble(baseLot * MathPow(multiplier, level), 2);
```

### 7. Prevent Error 130 (Invalid Stops)
```mql5
// From: cm_EA_TrailingStopOrders — ALWAYS check before OrderModify
double minStop = SymbolInfoInteger(_Symbol, SYMBOL_TRADE_STOPS_LEVEL)
                 * SymbolInfoDouble(_Symbol, SYMBOL_POINT);
if(type == POSITION_TYPE_BUY && Bid - newSL < minStop) return; // Too close
```

### 8. Gold/XAUUSD Pip Normalization
```mql5
// From: Aura Systems, Gold Master Pro
// XAUUSD has 2 digits: _Point=0.01, PipFactor=1 (1 pip = 0.01 = 1 point)
// Forex 5-digit: _Point=0.00001, PipFactor=10 (1 pip = 10 points)
double pipFactor = (_Digits == 5 || _Digits == 3) ? 10.0 : 1.0;
double pipValue  = SymbolInfoDouble(_Symbol, SYMBOL_POINT) * pipFactor;
```

---

## 🗂️ Strategy Classification Index

### Scalping EAs
| EA | Key Features |
|----|-------------|
| AK-47 Scalper | SL=3.5 pips, TP=7 pips, RSI+MA, time filter, spread gate |
| EuroScalper | Multi-currency grid scalper, aggressive position stacking |
| Gold Scalper | XAUUSD, ATR-filtered, London/NY session only |
| YMS Scalper | Simple MA-cross, fixed SL/TP, low latency design |
| Ea_Scalper_FX_Finist | Spread-aware scalper, fast market order execution |

### Grid / Martingale EAs
| EA | Key Features |
|----|-------------|
| Beast EA | Multi-pair, basket equity trail, complex grid recovery |
| BigRise EA | Progressive lot grid, GUI dashboard, trend filter |
| Gold Hunt EA | **Labouchere/D'Alembert/1-3-2-6** money management systems |
| Kirin EA | Fixed-step grid, multi-timeframe trend filter |
| OSOK Gold Killer | XAUUSD grid, 1.6× multiplier, 8 max legs, 25-pip spacing |
| Gold Reaper | Virtual SL/TP, aggressive grid + martingale, Gold specialist |

### Smart Money Concepts (ICT/SMC) EAs
| EA | Key Features |
|----|-------------|
| Bread & Butter Engine | Judas Swing: Kill Zone → Sweep → MSS → Entry |
| KCI Embedded Sniper | MA(200) + KCI(WPR) + ATR trailing |
| Smart Money OB | Order Block detection with FVG imbalance validation |
| XAUUSD Retest | Gold SMC retest entries at OB/FVG levels |

### Trend Following EAs
| EA | Key Features |
|----|-------------|
| NRTR EA | Always-in-market, reverses on NRTR flip |
| AGI FX v2 | Multi-indicator trend confluence |
| EA_TheOne | Trend + grid hybrid |
| Fortune MT5 | Trend-following with ATR stops |
| TradeBreakOut | Simple breakout of daily high/low |

### Arbitrage / Hedging EAs
| EA | Key Features |
|----|-------------|
| Arbitrage EA | Dual-pair synthetic spread deviation trading |
| Hedge Positions | Counter-position on drawdown (2× lot coefficient) |
| MForex 1.02 | Arbitrage-style multi-pair management |

### Multi-System EAs
| EA | Key Features |
|----|-------------|
| Aura Systems 1.25/1.26/Final | 4 simultaneous systems, H4 fractal integrity check |
| Hon-Matrix | 3-layer: News + Regime + Technical |
| Quantum Queen X 4.3 | Multi-strategy basket manager |
| SuperBot V4 | Combined trend + grid approach |

---

## 🎯 Aura Systems Deep Architecture (User's Own EA)

> Full reverse engineering in `references/aura_systems_reverse.md`

**System 3 — Fractal Integrity Check** (most novel pattern):
```mql5
// Step 1: Find fractal candidate (iHigh prominence check)
// Step 2: Verify left AND right depth > 100 pips (reject minor wicks)
// Step 3: Check H4 fractal aligns with unpenetrated Daily High
bool is_d1_low = (iLow(NULL, PERIOD_D1, d1_shift) == d1_hl_value);
// Step 4: Only then arm the pending stop order
```

**Temporal Entry System**:
- Fixed entry times (`entry_minutes`) + cancel window (`cancel_minutes`)
- Uses `K_Lookback` to find recent price extreme
- Verifies extreme via `V_Lookback` (confirmation bars)
- Places pending stop order at the extreme

**Lot Calculation** (equity-risk based):
```mql5
double risk_money = AccountInfoDouble(ACCOUNT_EQUITY) * cfg.risk_percent / 100.0;
double lot = risk_money / risk_per_lot;  // risk_per_lot = pip_value × sl_pips
```

---

## 🔧 CLI Tools

Located in `skills/production-mql-engineering/scripts/`:

### `mql_analyzer.py` — Analyze any MQL source file
```bash
python scripts/mql_analyzer.py --file "MyEA.mq5" --output report.json
python scripts/mql_analyzer.py --dir "C:/EAs" --format markdown
```
Extracts: inputs, indicators, lot sizing method, stop type, strategy class.

### `concept_extractor.py` — Generate concept tree from source dir
```bash
python scripts/concept_extractor.py --dir "C:/EAs" --output concept_tree.md
python scripts/concept_extractor.py --dir "C:/EAs" --format json
```
Classifies all EAs/indicators into the taxonomy automatically. Detected 91/99 concepts across 57 files.

---

## 📂 Specialized Per-Concept Skills

Located in `skills/production-mql-engineering/specialized/`:

Each specialized skill is a **deep-dive into one specific concept**, learned from forensic analysis of the relevant source files.

| Skill | Source Files | Focus |
|-------|------------|-------|
| [`smc-ict-trading`](specialized/smc-ict-trading/SKILL.md) | Bread & Butter Engine, SMC V5, Smart Money OB, KCI Sniper | Judas Swing, CHoCH/BOS, OB, FVG, Kill Zones |
| [`grid-martingale-systems`](specialized/grid-martingale-systems/SKILL.md) | Beast EA, Gold Hunt EA, Gold Reaper, OSOK, BigRise, Kirin | All lot progressions incl. Labouchere, D'Alembert, 1-3-2-6 |
| [`gold-xauusd-specialist`](specialized/gold-xauusd-specialist/SKILL.md) | Gold Master Pro, Gold Scalper, OSOK, Gold Reaper, Aura | Pip normalization, ATR gate, session filter, partial close |
| [`trailing-stop-systems`](specialized/trailing-stop-systems/SKILL.md) | cm_EA_TrailingStop (910KB!), NRTR EA, Gold Reaper, AK-47 | Step trail, BE, ATR chandelier, NRTR, basket equity trail |
| [`arbitrage-hedging`](specialized/arbitrage-hedging/SKILL.md) | Arbitrage EA, Hedge EA, Hon-Matrix (266KB), MForex | Pair arbitrage, hedge neutralization, 3-layer architecture |
| [`indicator-algorithms`](specialized/indicator-algorithms/SKILL.md) | QQE, NRTR, CoG, MACD TV Style, ATR VOL MACD, Pivots | Full mathematical formulas for 13 indicator algorithms |
| [`large-ea-architecture`](specialized/large-ea-architecture/SKILL.md) | Beast EA (312KB), Gold Hunt EA (493KB), Kirin, BigRise | Multi-mode grid, GUI dashboard, MTF matrix, EABuilder patterns |

---

## 🧠 Indicator Formula Quick Reference

| Indicator | Core Formula |
|-----------|-------------|
| **QQE** | RSX(RSI) → AtrRsi smoothing → Trail levels |
| **NRTR** | `trail = highest × (1 − k/100)` / `trail = lowest × (1 + k/100)` |
| **Center of Gravity** | Gaussian elimination oscillator (**repaints**) |
| **MACD TV Style** | Standard MACD with EMA seed initialization (matches TradingView) |
| **ATR Channel** | `Upper = MA + ATR × mult` / `Lower = MA − ATR × mult` |
| **Pivot** | `P = (H+L+C)/3`, `R1 = 2P−L`, `S1 = 2P−H` |
| **Bollinger** | `BB = MA ± StdDev × 2` |
| **EQH/EQL** | `|H1 − H2| < ATR × threshold` (threshold = 0.1 typical) |

---

## ⚠️ Known Pitfalls & Anti-Patterns

1. **Error 130 (Invalid Stops)**: Always check `SYMBOL_TRADE_STOPS_LEVEL` before modifying SL/TP
2. **Martingale blow-up risk**: OSOK's 8 legs at 1.6× = 26× base lot at max drawdown
3. **Center of Gravity repaints**: Never use as a historical signal in backtesting
4. **Gold pip confusion**: XAUUSD requires `pipFactor=1` not `10` (2-digit broker quote)
5. **MT5 netting accounts**: On netting brokers, multiple positions per symbol are impossible —
   check `ACCOUNT_MARGIN_MODE` at init
6. **Virtual SL/TP exposure**: Positions without real broker stops are vulnerable to
   internet disconnection (Gold Reaper pattern — high risk in live trading)
7. **MACD TV Style drift**: Without EMA seeding, MACD will diverge from TradingView
   values for the first N bars (warm-up period mismatch)
8. **Enum index drift in `.set` files**: Reordering enum variants silently corrupts MT5
   Strategy Tester parameter mapping without compiler errors. Always preserve enum index values.

---

## 🛡️ Multi-Strategy Milestone Pinning & Isolation Protocol

When building, maintaining, or harmonizing multi-system Expert Advisors (e.g., combining independent breakout, session, and swing systems):

1. **Explicit Module Isolation**:
   - Shared entry handlers (`OnTick()`, `OnTimer()`, `OnTradeTransaction()`) must route directly to strategy-specific handlers without state bleeding.
   - Avoid generic overrides in shared functions (`GetReferenceRange`, `BuildBuyLevels`, `PlaceSystemOrders`, `ManageTrailing`). Branch explicitly per system ID:
     ```mql5
     if(cfg.id == 1 || cfg.id == 2)
       {
        // Pinned to exact verified breakout logic
        return GetStandardReferenceRange(cfg, highest, lowest);
       }
     ```

2. **Preserve Validated Milestone Baselines**:
   - When a specific strategy achieves a verified performance milestone (e.g. Strategy 4 at +$5,343 in `Aura_Systems_5k (1).mq5`), treat that code as an immutable baseline.
   - Do NOT bundle experimental upgrades (e.g. Multi-level London Re-Arming) into the baseline without an explicit toggle and separate validation.

3. **Enum Backward Compatibility Guarantee**:
   - Never reorder enum values saved in `.set` preset files or terminal profiles:
     ```mql5
     enum ENUM_RISK_TYPE
       {
        RISK_FIXED_LOT = 0,
        RISK_PERCENT   = 1,
        RISK_USD       = 2
       };
     ```


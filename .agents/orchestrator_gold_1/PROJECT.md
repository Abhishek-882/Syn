# Project: Gold Oracle EA v2 (`GoldOracle_v2.mq5`)

## Architecture
Gold Oracle EA v2 is an institutional-grade, daily directional Expert Advisor for Spot Gold (XAUUSD) on MetaTrader 5. It is built as a single monolithic compilation unit (`GoldOracle_v2.mq5`) consisting of:
1. **Global Configuration & Inputs:** User inputs for risk (`InpRiskPercent`), daily operational window (analysis 07:00–10:00 UTC, trade entry 10:00 UTC, session close 20:00 UTC), spread ceiling (50 pts), and volatility floor.
2. **Global Shared Indicator Architecture (49 Handles):** Consolidated across M15 (11), H1 (21), H4 (9), D1 (5), and Cross-Asset Proxies (3). Consumes only 9.57% of MT5's 512-handle capacity (<60 limit). Initialized in `OnInit()`, validated, and released in `OnDeinit()`.
3. **Confirmed Historical Buffer Access Helper Layer:** `GetIndicatorVal`, `GetIndicatorSeries`, `GetRatesSeries` reading strictly confirmed `bar[1]` or older (`ArraySetAsSeries(..., true)`), guaranteeing zero repainting and eliminating lookahead bias.
4. **144 Strategy Brain Ensemble:** 144 pure, isolated analytical functions (`Brain001` to `Brain144`) returning strictly `+1` (BUY), `-1` (SELL), or `0` (NEUTRAL) across 13 disciplines.
5. **Adaptive Dynamic Weighting Engine:** 144 weights initialized at 1.0. At 20:00 UTC daily session close, evaluates actual market direction $\text{Sign}(\text{Close}_{20:00} - \text{Open}_{10:00})$, updates exponential accuracy:
   $$\text{EMA\_Acc}_i \leftarrow 0.95 \times \text{EMA\_Acc}_i + 0.05 \times (\text{Vote}_i == \text{ActualDirection} ? 1.0 : 0.0)$$
   $$W_i \leftarrow \max(0.1, \text{EMA\_Acc}_i)$$
   Abstained brains ($V_i == 0$) are isolated and retain weights.
6. **Execution & Microstructure Engine:**
   - XAUUSD pip normalization (`_Digits == 2`, `_Point = 0.01`, `pipFactor = 1.0`).
   - Dynamic ATR(14, H1) stop loss with broker `SYMBOL_TRADE_STOPS_LEVEL` and spread clamping.
   - Sizing based on `ACCOUNT_EQUITY` % with division-by-zero guards.
   - Pre-trade gating: Spread gate (<50 points) and Volatility gate (H1 ATR > minimum).
7. **Institutional News Blackout & Safety System:**
   - Dual-layer calendar (algorithmic NFP 1st Friday, FOMC matrix, CPI, PPI, Powell speeches) evaluated in true UTC via `TimeGMT()`.
   - Pre-news window liquidation and blackout entry rejection with zero same-day re-entry.
8. **Monolithic Build & Verification:**
   - Single compilation unit `GoldOracle_v2.mq5`.
   - Verified via `MetaEditor64.exe` with 0 errors and 0 warnings.

---

## Feature Inventory

| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Shared Indicator Registry | 49 global handles across M15, H1, H4, D1 (<60 limit) | M1 | Survey 1, 2 |
| 2 | Buffer Access Protocol | Helper functions reading strictly bar[1] (zero repainting) | M1 | Survey 1, 2 |
| 3 | Core State Machine & Lifecycle | State transitions, OnInit validation, OnDeinit release | M1 | Survey 1, 3 |
| 4 | SMC / ICT Brains (12) | Brain001 to Brain012: CHoCH, BOS, OB, FVG, Sweeps, KillZones | M2 | Survey 2 |
| 5 | Trend Following Brains (15) | Brain013 to Brain027: EMAs, GoldenCross, MTF, SuperTrend, KAMA | M2 | Survey 2 |
| 6 | Momentum & Oscillators (16) | Brain028 to Brain043: RSI, MACD, Stoch, CCI, QQE, TSI, AO | M2 | Survey 2 |
| 7 | Volatility Brains (11) | Brain044 to Brain054: ATR, Bollinger, Keltner, Chaikin, RVI | M2 | Survey 2 |
| 8 | Volume & Flow Brains (10) | Brain055 to Brain064: OBV, Tick Vol, VPT, CMF, Force Index | M3 | Survey 2 |
| 9 | Fibonacci & Harmonics (10) | Brain065 to Brain074: Golden Pocket, Deep Retracement, Gartley | M3 | Survey 2 |
| 10 | Statistical & Quant Brains (15) | Brain075 to Brain089: Z-Score, Hurst, Ornstein-Uhlenbeck, Kalman | M3 | Survey 2 |
| 11 | Inter-Market Macro Brains (16) | Brain090 to Brain105: DXY, Yields, Silver Beta, Oil, SP500, VIX | M3 | Survey 2 |
| 12 | Temporal & Calendar Brains (15) | Brain106 to Brain120: London Open, Asia Breakout, Day Seasonality | M3 | Survey 2 |
| 13 | Support/Resistance & Pivots (10) | Brain121 to Brain130: Daily Pivots, Camarilla, Woodie, HVN | M4 | Survey 2 |
| 14 | Candlestick Pattern Brains (12) | Brain131 to Brain142: Engulfing, Hammer, Star, Pinbar, Marubozu | M4 | Survey 2 |
| 15 | Psychological & Sentiment (8) | Brain143 to Brain150: Crowd Fade, Trap Failure, Panic Bounce | M4 | Survey 2 |
| 16 | Frontier & Experimental (10) | Brain151 to Brain160: Fractal Dimension, Ehlers Fisher, SSA | M4 | Survey 2 |
| 17 | Dynamic Weighting Engine | EMA 0.95/0.05 update, 20:00 UTC trigger, 0.1 floor | M5 | Survey 3 |
| 18 | Consensus Calculator | Weighted voting score $\sum (V_i \times W_i)$, neutral deadband | M5 | Survey 3 |
| 19 | XAUUSD Pip Normalization | Digits==2, Point==0.01, pipFactor==1.0 | M5 | Survey 3 |
| 20 | Dynamic ATR Stop Loss | ATR(14, H1)*2.0 with StopsLevel & spread clamping | M5 | Survey 3 |
| 21 | Equity % Position Sizing | Risk % of Account Equity with step/min/max normalization | M5 | Survey 3 |
| 22 | Spread & Volatility Gating | Spread < 50 pts, H1 ATR > threshold on bar[1] | M5 | Survey 3 |
| 23 | Institutional News Blackout | NFP, CPI, FOMC, PPI, Powell speeches, UTC time, zero re-entry | M5 | Survey 3 |
| 24 | Monolithic Assembly & Build | Full `GoldOracle_v2.mq5` assembly & MetaEditor64 compilation | M6 | Survey 3 |
| 25 | E2E Stress & Adversarial Audit | Verification across all 144 brains, execution & forensics | M7 | Survey 1, 2, 3 |

---

## Milestones

| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Scaffold & Shared Indicator Architecture | Base EA structure, 49 handles in OnInit/OnDeinit, safe bar[1] buffer helpers | None | PLANNED |
| M2 | Strategy Brains Batch 1 (54 brains) | Disciplines 1–4: SMC/ICT (12), Trend (15), Momentum (16), Volatility (11) | M1 | PLANNED |
| M3 | Strategy Brains Batch 2 (67 brains) | Disciplines 5–9: Volume (10), Fibonacci (10), Quant (15), Macro (16), Temporal (16) | M1 | PLANNED |
| M4 | Strategy Brains Batch 3 (23 brains) | Disciplines 10–13: S/R & Pivots (10), Candlesticks (12), Sentiment (8), Frontier (10) (mapped to 144 core brains) | M1 | PLANNED |
| M5 | Execution, Weights & News Blackout | Adaptive weighting engine, consensus calculator, XAUUSD sizing, news calendar | M1 | PLANNED |
| M6 | Monolithic Integration & MetaEditor Compile | Integrate M1-M5 into `GoldOracle_v2.mq5`, compile with MetaEditor64 (0 err, 0 warn) | M1, M2, M3, M4, M5 | PLANNED |
| M7 | Multi-Perspective Verification & Audit | Reviewers, Challengers (stress test logic/data), Forensic Integrity Auditor | M6 | PLANNED |

---

## Interface Contracts

### 1. Strategy Brain Signature
Every brain function adheres strictly to:
```mql5
int BrainXXX();
```
- **Return Values:** Strictly `+1` (BUY bias), `-1` (SELL bias), or `0` (NEUTRAL / ABSTAIN).
- **Rule:** Evaluates only confirmed historical bars (`bar[1]` or older). Never reads `bar[0]`.

### 2. Strategy Brain Definition Structure
```mql5
struct StrategyBrain
{
   int    id;
   string name;
   string discipline;
   double weight;        // initialized to 1.0, clamped to [0.1, 1.0]
   double ema_accuracy;  // initialized to 1.0
   int    last_vote;     // +1, -1, or 0
};
extern StrategyBrain g_Brains[144];
```

### 3. Buffer Access Protocol
```mql5
double GetIndicatorVal(int handle, int buffer_num, int shift);
bool   GetIndicatorSeries(int handle, int buffer_num, int count, double &buf[]);
bool   GetRatesSeries(ENUM_TIMEFRAMES tf, int count, MqlRates &rates[]);
```
- `shift >= 1` always.

### 4. Consensus & Weight Update
```mql5
double CalculateConsensus(int &direction, int &buyVotes, int &sellVotes, int &neutralVotes);
void   UpdateBrainWeights(int actualDirection);
```

### 5. Execution & Gating
```mql5
bool   IsSpreadOK(int maxSpreadPoints = 50);
bool   IsVolatilityOK(double minATRPoints = 30);
double CalculateLotSize(double entryPrice, double slPrice, double riskPercent);
double GetDynamicATRStopLoss(int direction, double entryPrice);
bool   IsNewsBlackoutActive(datetime gmtTime);
```

---

## Code Layout
- Target: `c:\Users\Asus\Documents\antigravity\hopeful-curie\GoldOracle_v2.mq5`
- Monolithic structure:
  - Header, properties, includes (`<Trade\Trade.mqh>`).
  - Inputs (Core, Session, Adaptive, News, Risk).
  - Global variables, Brain definitions, Indicator handles.
  - Indicator Initialization & Release (`InitSharedIndicators`, `ReleaseSharedIndicators`).
  - Safe Buffer Copying Helper Functions.
  - 144 Strategy Brain Functions (grouped cleanly by 13 disciplines).
  - Consensus & Adaptive Weighting Engine.
  - Microstructure Execution & Gating Functions.
  - Institutional News Blackout Calendar & Checks.
  - Standard MQL5 Event Handlers (`OnInit`, `OnDeinit`, `OnTick`).

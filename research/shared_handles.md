# Gold Oracle EA — Shared Indicator Handle Architecture & Engineering Standards

> **Author**: E02 — Chief Engineering Officer (CEngO)  
> **Project**: Gold Oracle EA v2 (XAUUSD Daily Directional Multi-Agent Engine)  
> **Status**: APPROVED ENGINEERING SPECIFICATION  
> **Target Platform**: MetaTrader 5 (MQL5)  
> **Audience**: Division 4 (Engineering Leads, Brain Builders B01–B47, Infrastructure Builders INFRA-1–3), Division 5 (QA)

---

## 1. Executive Engineering Directive

The Gold Oracle EA incorporates **144 independent analytical brain functions** voting concurrently to determine the daily directional bias for Gold (XAUUSD). 

In naive implementations, 144 strategies instantiating their own private indicator handles would spawn hundreds of duplicate handles, quickly exhausting MetaTrader 5's internal handle table (which hard-caps at **~512 handles per MQL5 program**), causing catastrophic initialization crashes (`INIT_FAILED`), memory bloat, and tick execution degradation.

As Chief Engineering Officer, I mandate a **Centralized Shared Indicator Handle Architecture**:
1. **Zero Private Handles**: Brain functions **must never** call `iMA()`, `iRSI()`, `iATR()`, `iBands()`, or any indicator creation function inside their body.
2. **Central Registry in Global Scope**: All indicators are created exactly **once** during `OnInit()` in a unified global registry.
3. **Handle Budget**: The entire 144-brain architecture is serviced by **48 shared handles** (~9.3% of the MT5 limit), leaving massive headroom for broker overhead, secondary symbols, and infrastructure.
4. **Clean Lifecycle**: Every handle is validated at startup and deterministically freed during `OnDeinit()` via `IndicatorRelease()`.
5. **Strict Execution Standard**: Every brain must be pure, thread-safe, evaluate only closed bars (`bar[1]`), use local series buffers, and adhere to Gold-specific pip normalization.

---

## 2. MT5 Handle Architecture & Lifecycle Engine

### 2.1 The Handle Budget

| Category | Brains Covered | Handles Required | Notes |
|---|---|---|---|
| **Category A: SMC / ICT** | A01–A12 (12) | 2 | Pure price action; shares H1/M15 ATR handles for swing tolerance. |
| **Category B: Trend Following** | B01–B15 (15) | 16 | Shared EMAs, SMAs, Ichimoku, SAR, ADX on H4/H1/D1. |
| **Category C: Momentum & Oscillators** | C01–C16 (16) | 14 | Shared RSIs (M15, H1, H4, D1), MACD, Stoch, CCI, WPR, MFI, AO, Bears/Bulls. |
| **Category D: Volatility** | D01–D11 (11) | 8 | Shared ATRs (M15, H1, H4, D1, 100-period H4), Bollinger Bands (H4, H1), StdDev. |
| **Category E: Volume** | E01–E10 (10) | 3 | OBV, A/D, Force Index (Tick Volume basis). |
| **Category F: Fibonacci & Harmonic** | F01–F10 (10) | 0 | Pure geometric price swing math using shared price buffers. |
| **Category G: Statistical / Quant** | G01–G15 (15) | 0 | Pure mathematical calculations on OHLC arrays and shared MA/ATR values. |
| **Category H: Inter-Market Macro** | H01–H16 (16) | 4 | Secondary symbol handles (EURUSD, XAGUSD); graceful fallback. |
| **Category I: Temporal / Calendar** | I01–I15 (15) | 0 | Pure calendar/session math via `MqlDateTime` & `TimeGMT()`. |
| **Category J: Pivot / S-R** | J01–J10 (10) | 0 | Mathematical pivot levels calculated from prior D1/W1/MN1 bars. |
| **Category K: Candlesticks** | K01–K12 (12) | 0 | Pure pattern matching on H4/D1 OHLC arrays. |
| **Category L: Psychological** | L01–L08 (8) | 0 | Meta-analysis and price exhaustion patterns; uses shared ATR. |
| **Category M: Experimental** | M01–M10 (10) | 0 | Mathematical algorithms, lunar cycles, and contrarian consensus. |
| **Infrastructure / Execution** | INFRA-1–3 | 1 | ATR(14, M15) for execution spread/volatility gating. |
| **TOTAL UNIQUE HANDLES** | **144 Brains** | **48 Handles** | **<10% of MT5 Limit (512)** |

---

## 3. Master Shared Handle Registry

All 48 handles are declared globally in Section 4 of the master EA.

```mql5
// ==============================================================================
// SECTION 4: GLOBAL SHARED INDICATOR HANDLES REGISTRY
// ==============================================================================

// --- Group 1: Moving Averages (Trend & S/R) ---
int h_EMA8_H4       = INVALID_HANDLE;  // EMA Ribbon Fast
int h_EMA13_H4      = INVALID_HANDLE;  // EMA Ribbon
int h_EMA20_H4      = INVALID_HANDLE;  // Short Trend / Keltner Middle
int h_EMA21_H4      = INVALID_HANDLE;  // Fibonacci MA
int h_EMA34_H4      = INVALID_HANDLE;  // Fibonacci MA / Ribbon
int h_EMA50_H4      = INVALID_HANDLE;  // Institutional Medium Trend H4
int h_EMA55_H4      = INVALID_HANDLE;  // Fibonacci MA
int h_EMA89_H4      = INVALID_HANDLE;  // Fibonacci MA
int h_EMA200_H4     = INVALID_HANDLE;  // Institutional Long Trend H4
int h_SMA20_H4      = INVALID_HANDLE;  // Baseline SMA / Z-score baseline
int h_SMA50_H4      = INVALID_HANDLE;  // Baseline SMA
int h_SMA200_H4     = INVALID_HANDLE;  // Baseline 200 SMA
int h_EMA50_H1      = INVALID_HANDLE;  // Institutional Medium Trend H1
int h_EMA200_H1     = INVALID_HANDLE;  // Institutional Long Trend H1
int h_EMA50_D1      = INVALID_HANDLE;  // Macro Trend D1
int h_EMA200_D1     = INVALID_HANDLE;  // Macro Baseline D1

// --- Group 2: Oscillators & Momentum ---
int h_RSI14_M15     = INVALID_HANDLE;  // Pullback confirmation (Gold Master Pro style)
int h_RSI14_H1      = INVALID_HANDLE;  // Intermediate momentum / Triple RSI
int h_RSI14_H4      = INVALID_HANDLE;  // Core Momentum H4 (C01, C02, C09, C14)
int h_RSI14_D1      = INVALID_HANDLE;  // Macro Momentum / Triple RSI
int h_MACD_H4       = INVALID_HANDLE;  // MACD (12, 26, 9) H4
int h_MACD_H1       = INVALID_HANDLE;  // MACD (12, 26, 9) H1
int h_Stoch_H4      = INVALID_HANDLE;  // Stochastic (14, 3, 3) H4
int h_CCI20_H4      = INVALID_HANDLE;  // Commodity Channel Index (20) H4
int h_WPR14_H4      = INVALID_HANDLE;  // Williams %R (14) H4
int h_MFI14_H4      = INVALID_HANDLE;  // Money Flow Index (14, TICK) H4
int h_AO_H4         = INVALID_HANDLE;  // Awesome Oscillator H4
int h_Bears13_H4    = INVALID_HANDLE;  // Bears Power (13) H4
int h_Bulls13_H4    = INVALID_HANDLE;  // Bulls Power (13) H4
int h_Momentum14_H4 = INVALID_HANDLE;  // Momentum (14) H4

// --- Group 3: Volatility, Bands & Envelope Systems ---
int h_ATR14_M15     = INVALID_HANDLE;  // Execution volatility gate / Gold Master Pro
int h_ATR14_H1      = INVALID_HANDLE;  // Trade SL calculation / Breakout filter
int h_ATR14_H4      = INVALID_HANDLE;  // Core H4 Volatility & Trailing Band
int h_ATR14_D1      = INVALID_HANDLE;  // Macro Volatility Normalizer
int h_ATR100_H4     = INVALID_HANDLE;  // Long-term ATR Baseline for Regime Detection
int h_Bands20_2_H4  = INVALID_HANDLE;  // Bollinger Bands (20, 2.0) H4
int h_Bands20_2_H1  = INVALID_HANDLE;  // Bollinger Bands (20, 2.0) H1
int h_StdDev20_H4   = INVALID_HANDLE;  // Standard Deviation (20) H4
int h_ADX14_H4      = INVALID_HANDLE;  // Trend Strength ADX (14) H4
int h_SAR_H4        = INVALID_HANDLE;  // Parabolic SAR (0.02, 0.2) H4
int h_Ichimoku_H4   = INVALID_HANDLE;  // Ichimoku Kinko Hyo (9, 26, 52) H4

// --- Group 4: Volume Dynamics (Tick Volume) ---
int h_OBV_H4        = INVALID_HANDLE;  // On-Balance Volume (TICK) H4
int h_AD_H4         = INVALID_HANDLE;  // Accumulation/Distribution (TICK) H4
int h_Force13_H4    = INVALID_HANDLE;  // Force Index (13, EMA, TICK) H4

// --- Group 5: Inter-Market Secondary Symbols (Optional / Graceful Fallback) ---
int h_EURUSD_EMA50  = INVALID_HANDLE;  // USD Proxy Trend
int h_EURUSD_RSI14  = INVALID_HANDLE;  // USD Proxy Momentum
int h_XAGUSD_EMA50  = INVALID_HANDLE;  // Silver Trend (Gold/Silver Lead)
int h_XAGUSD_RSI14  = INVALID_HANDLE;  // Silver Momentum
```

---

### 3.1 Handle Allocation & Consumer Matrix

The following table details every handle, its exact constructor, and every brain that consumes it:

| # | Global Handle Identifier | MQL5 Constructor Call | Primary Consuming Brains |
|---|---|---|---|
| 1 | `h_EMA8_H4` | `iMA(_Symbol, PERIOD_H4, 8, 0, MODE_EMA, PRICE_CLOSE)` | B02 (Ribbon), F04 (MA Channels) |
| 2 | `h_EMA13_H4` | `iMA(_Symbol, PERIOD_H4, 13, 0, MODE_EMA, PRICE_CLOSE)` | B02 (Ribbon), F04 (MA Channels) |
| 3 | `h_EMA20_H4` | `iMA(_Symbol, PERIOD_H4, 20, 0, MODE_EMA, PRICE_CLOSE)` | B11 (Keltner Mid), D06 (ATR Channel) |
| 4 | `h_EMA21_H4` | `iMA(_Symbol, PERIOD_H4, 21, 0, MODE_EMA, PRICE_CLOSE)` | B02 (Ribbon), F04 (Fib Channel) |
| 5 | `h_EMA34_H4` | `iMA(_Symbol, PERIOD_H4, 34, 0, MODE_EMA, PRICE_CLOSE)` | B02 (Ribbon), F04 (Fib Channel) |
| 6 | `h_EMA50_H4` | `iMA(_Symbol, PERIOD_H4, 50, 0, MODE_EMA, PRICE_CLOSE)` | B01, B02, C14, G08, G14, T13 |
| 7 | `h_EMA55_H4` | `iMA(_Symbol, PERIOD_H4, 55, 0, MODE_EMA, PRICE_CLOSE)` | B02 (Ribbon), F04 (Fib Channel) |
| 8 | `h_EMA89_H4` | `iMA(_Symbol, PERIOD_H4, 89, 0, MODE_EMA, PRICE_CLOSE)` | F04 (Fib Channel) |
| 9 | `h_EMA200_H4` | `iMA(_Symbol, PERIOD_H4, 200, 0, MODE_EMA, PRICE_CLOSE)` | B01, B02, G14 (MA Distance) |
| 10 | `h_SMA20_H4` | `iMA(_Symbol, PERIOD_H4, 20, 0, MODE_SMA, PRICE_CLOSE)` | G01 (Z-Score Baseline) |
| 11 | `h_SMA50_H4` | `iMA(_Symbol, PERIOD_H4, 50, 0, MODE_SMA, PRICE_CLOSE)` | B01, G08 |
| 12 | `h_SMA200_H4` | `iMA(_Symbol, PERIOD_H4, 200, 0, MODE_SMA, PRICE_CLOSE)` | B01 (Golden Cross/Death Cross) |
| 13 | `h_EMA50_H1` | `iMA(_Symbol, PERIOD_H1, 50, 0, MODE_EMA, PRICE_CLOSE)` | B01, A09, Gold Master Pro Filter |
| 14 | `h_EMA200_H1` | `iMA(_Symbol, PERIOD_H1, 200, 0, MODE_EMA, PRICE_CLOSE)` | B01, G14 |
| 15 | `h_EMA50_D1` | `iMA(_Symbol, PERIOD_D1, 50, 0, MODE_EMA, PRICE_CLOSE)` | B01, T13 (Macro Trend) |
| 16 | `h_EMA200_D1` | `iMA(_Symbol, PERIOD_D1, 200, 0, MODE_EMA, PRICE_CLOSE)` | B01, T13 (Macro Trend) |
| 17 | `h_RSI14_M15` | `iRSI(_Symbol, PERIOD_M15, 14, PRICE_CLOSE)` | C16 (Triple RSI), INFRA-1 |
| 18 | `h_RSI14_H1` | `iRSI(_Symbol, PERIOD_H1, 14, PRICE_CLOSE)` | C16 (Triple RSI), A01 filter |
| 19 | `h_RSI14_H4` | `iRSI(_Symbol, PERIOD_H4, 14, PRICE_CLOSE)` | C01, C02, C09 (QQE Seed), C14, C16 |
| 20 | `h_RSI14_D1` | `iRSI(_Symbol, PERIOD_D1, 14, PRICE_CLOSE)` | C16 (Triple RSI Macro) |
| 21 | `h_MACD_H4` | `iMACD(_Symbol, PERIOD_H4, 12, 26, 9, PRICE_CLOSE)` | C03 (Histogram), C04 (Cross), D04 |
| 22 | `h_MACD_H1` | `iMACD(_Symbol, PERIOD_H1, 12, 26, 9, PRICE_CLOSE)` | C03, C04 |
| 23 | `h_Stoch_H4` | `iStochastic(_Symbol, PERIOD_H4, 14, 3, 3, MODE_SMA, STO_LOWHIGH)` | C05 (Stochastic Momentum) |
| 24 | `h_CCI20_H4` | `iCCI(_Symbol, PERIOD_H4, 20, PRICE_TYPICAL)` | C06 (Commodity Channel Index) |
| 25 | `h_WPR14_H4` | `iWPR(_Symbol, PERIOD_H4, 14)` | C07 (Williams %R) |
| 26 | `h_MFI14_H4` | `iMFI(_Symbol, PERIOD_H4, 14, VOLUME_TICK)` | C08 (Money Flow Index) |
| 27 | `h_AO_H4` | `iAO(_Symbol, PERIOD_H4)` | C12 (Awesome Oscillator) |
| 28 | `h_Bears13_H4` | `iBearsPower(_Symbol, PERIOD_H4, 13)` | C13 (Bears Power) |
| 29 | `h_Bulls13_H4` | `iBullsPower(_Symbol, PERIOD_H4, 13)` | C13 (Bulls Power) |
| 30 | `h_Momentum14_H4` | `iMomentum(_Symbol, PERIOD_H4, 14, PRICE_CLOSE)` | C11 (ROC), C15 (Momentum Slope) |
| 31 | `h_ATR14_M15` | `iATR(_Symbol, PERIOD_M15, 14)` | INFRA-1 (Execution Volatility Gate) |
| 32 | `h_ATR14_H1` | `iATR(_Symbol, PERIOD_H1, 14)` | INFRA-1 (SL Sizing), D03, D09 |
| 33 | `h_ATR14_H4` | `iATR(_Symbol, PERIOD_H4, 14)` | B05, B11, D03, D06, D09, G14 |
| 34 | `h_ATR14_D1` | `iATR(_Symbol, PERIOD_D1, 14)` | D08, D09, G13 (Range Expansion) |
| 35 | `h_ATR100_H4` | `iATR(_Symbol, PERIOD_H4, 100)` | D09 (Regime Baseline Classifier) |
| 36 | `h_Bands20_2_H4` | `iBands(_Symbol, PERIOD_H4, 20, 0, 2.0, PRICE_CLOSE)` | D01, D02 (TTM Squeeze), D07, D11 |
| 37 | `h_Bands20_2_H1` | `iBands(_Symbol, PERIOD_H1, 20, 0, 2.0, PRICE_CLOSE)` | D01, D02 |
| 38 | `h_StdDev20_H4` | `iStdDev(_Symbol, PERIOD_H4, 20, 0, MODE_SMA, PRICE_CLOSE)` | D10 (StdDev Trend), G01 (Z-Score) |
| 39 | `h_ADX14_H4` | `iADX(_Symbol, PERIOD_H4, 14)` | B07 (ADX Trend Strength), T13 |
| 40 | `h_SAR_H4` | `iSAR(_Symbol, PERIOD_H4, 0.02, 0.2)` | B06 (Parabolic SAR) |
| 41 | `h_Ichimoku_H4` | `iIchimoku(_Symbol, PERIOD_H4, 9, 26, 52)` | B03 (Cloud), B04 (TK Cross) |
| 42 | `h_OBV_H4` | `iOBV(_Symbol, PERIOD_H4, VOLUME_TICK)` | E01 (On-Balance Volume) |
| 43 | `h_AD_H4` | `iAD(_Symbol, PERIOD_H4, VOLUME_TICK)` | E03 (Accumulation/Distribution) |
| 44 | `h_Force13_H4` | `iForce(_Symbol, PERIOD_H4, 13, MODE_EMA, VOLUME_TICK)` | E05 (Force Index) |
| 45 | `h_EURUSD_EMA50` | `iMA("EURUSD", PERIOD_H4, 50, 0, MODE_EMA, PRICE_CLOSE)` | H01 (USD Trend Proxy), H10 |
| 46 | `h_EURUSD_RSI14` | `iRSI("EURUSD", PERIOD_H4, 14, PRICE_CLOSE)` | H01, H10 |
| 47 | `h_XAGUSD_EMA50` | `iMA("XAGUSD", PERIOD_H4, 50, 0, MODE_EMA, PRICE_CLOSE)` | H07 (Silver/Gold Correlation) |
| 48 | `h_XAGUSD_RSI14` | `iRSI("XAGUSD", PERIOD_H4, 14, PRICE_CLOSE)` | H07 (Silver Momentum Divergence) |

---

### 3.2 Centralized Handle Initialization & Validation Engine

To guarantee rock-solid runtime stability, handles are initialized through a dedicated helper that prints human-readable diagnostics on failure.

```mql5
// Helper function to safely initialize and log handle status
int SafeInitHandle(string name, int handle)
{
   if(handle == INVALID_HANDLE)
   {
      PrintFormat("[FATAL CRITICAL] Failed to create indicator handle: %s. Error: %d", name, GetLastError());
      return INVALID_HANDLE;
   }
   return handle;
}

// Master Initialization routine called from OnInit()
bool InitSharedHandles()
{
   Print("[INIT] Initializing 48 Shared Indicator Handles...");

   // Group 1: Moving Averages
   h_EMA8_H4       = SafeInitHandle("h_EMA8_H4",       iMA(_Symbol, PERIOD_H4, 8,   0, MODE_EMA, PRICE_CLOSE));
   h_EMA13_H4      = SafeInitHandle("h_EMA13_H4",      iMA(_Symbol, PERIOD_H4, 13,  0, MODE_EMA, PRICE_CLOSE));
   h_EMA20_H4      = SafeInitHandle("h_EMA20_H4",      iMA(_Symbol, PERIOD_H4, 20,  0, MODE_EMA, PRICE_CLOSE));
   h_EMA21_H4      = SafeInitHandle("h_EMA21_H4",      iMA(_Symbol, PERIOD_H4, 21,  0, MODE_EMA, PRICE_CLOSE));
   h_EMA34_H4      = SafeInitHandle("h_EMA34_H4",      iMA(_Symbol, PERIOD_H4, 34,  0, MODE_EMA, PRICE_CLOSE));
   h_EMA50_H4      = SafeInitHandle("h_EMA50_H4",      iMA(_Symbol, PERIOD_H4, 50,  0, MODE_EMA, PRICE_CLOSE));
   h_EMA55_H4      = SafeInitHandle("h_EMA55_H4",      iMA(_Symbol, PERIOD_H4, 55,  0, MODE_EMA, PRICE_CLOSE));
   h_EMA89_H4      = SafeInitHandle("h_EMA89_H4",      iMA(_Symbol, PERIOD_H4, 89,  0, MODE_EMA, PRICE_CLOSE));
   h_EMA200_H4     = SafeInitHandle("h_EMA200_H4",     iMA(_Symbol, PERIOD_H4, 200, 0, MODE_EMA, PRICE_CLOSE));
   h_SMA20_H4      = SafeInitHandle("h_SMA20_H4",      iMA(_Symbol, PERIOD_H4, 20,  0, MODE_SMA, PRICE_CLOSE));
   h_SMA50_H4      = SafeInitHandle("h_SMA50_H4",      iMA(_Symbol, PERIOD_H4, 50,  0, MODE_SMA, PRICE_CLOSE));
   h_SMA200_H4     = SafeInitHandle("h_SMA200_H4",     iMA(_Symbol, PERIOD_H4, 200, 0, MODE_SMA, PRICE_CLOSE));
   h_EMA50_H1      = SafeInitHandle("h_EMA50_H1",      iMA(_Symbol, PERIOD_H1, 50,  0, MODE_EMA, PRICE_CLOSE));
   h_EMA200_H1     = SafeInitHandle("h_EMA200_H1",     iMA(_Symbol, PERIOD_H1, 200, 0, MODE_EMA, PRICE_CLOSE));
   h_EMA50_D1      = SafeInitHandle("h_EMA50_D1",      iMA(_Symbol, PERIOD_D1, 50,  0, MODE_EMA, PRICE_CLOSE));
   h_EMA200_D1     = SafeInitHandle("h_EMA200_D1",     iMA(_Symbol, PERIOD_D1, 200, 0, MODE_EMA, PRICE_CLOSE));

   // Group 2: Oscillators & Momentum
   h_RSI14_M15     = SafeInitHandle("h_RSI14_M15",     iRSI(_Symbol, PERIOD_M15, 14, PRICE_CLOSE));
   h_RSI14_H1      = SafeInitHandle("h_RSI14_H1",      iRSI(_Symbol, PERIOD_H1,  14, PRICE_CLOSE));
   h_RSI14_H4      = SafeInitHandle("h_RSI14_H4",      iRSI(_Symbol, PERIOD_H4,  14, PRICE_CLOSE));
   h_RSI14_D1      = SafeInitHandle("h_RSI14_D1",      iRSI(_Symbol, PERIOD_D1,  14, PRICE_CLOSE));
   h_MACD_H4       = SafeInitHandle("h_MACD_H4",       iMACD(_Symbol, PERIOD_H4, 12, 26, 9, PRICE_CLOSE));
   h_MACD_H1       = SafeInitHandle("h_MACD_H1",       iMACD(_Symbol, PERIOD_H1, 12, 26, 9, PRICE_CLOSE));
   h_Stoch_H4      = SafeInitHandle("h_Stoch_H4",      iStochastic(_Symbol, PERIOD_H4, 14, 3, 3, MODE_SMA, STO_LOWHIGH));
   h_CCI20_H4      = SafeInitHandle("h_CCI20_H4",      iCCI(_Symbol, PERIOD_H4, 20, PRICE_TYPICAL));
   h_WPR14_H4      = SafeInitHandle("h_WPR14_H4",      iWPR(_Symbol, PERIOD_H4, 14));
   h_MFI14_H4      = SafeInitHandle("h_MFI14_H4",      iMFI(_Symbol, PERIOD_H4, 14, VOLUME_TICK));
   h_AO_H4         = SafeInitHandle("h_AO_H4",         iAO(_Symbol, PERIOD_H4));
   h_Bears13_H4    = SafeInitHandle("h_Bears13_H4",    iBearsPower(_Symbol, PERIOD_H4, 13));
   h_Bulls13_H4    = SafeInitHandle("h_Bulls13_H4",    iBullsPower(_Symbol, PERIOD_H4, 13));
   h_Momentum14_H4 = SafeInitHandle("h_Momentum14_H4", iMomentum(_Symbol, PERIOD_H4, 14, PRICE_CLOSE));

   // Group 3: Volatility & System
   h_ATR14_M15     = SafeInitHandle("h_ATR14_M15",     iATR(_Symbol, PERIOD_M15, 14));
   h_ATR14_H1      = SafeInitHandle("h_ATR14_H1",      iATR(_Symbol, PERIOD_H1,  14));
   h_ATR14_H4      = SafeInitHandle("h_ATR14_H4",      iATR(_Symbol, PERIOD_H4,  14));
   h_ATR14_D1      = SafeInitHandle("h_ATR14_D1",      iATR(_Symbol, PERIOD_D1,  14));
   h_ATR100_H4     = SafeInitHandle("h_ATR100_H4",     iATR(_Symbol, PERIOD_H4, 100));
   h_Bands20_2_H4  = SafeInitHandle("h_Bands20_2_H4",  iBands(_Symbol, PERIOD_H4, 20, 0, 2.0, PRICE_CLOSE));
   h_Bands20_2_H1  = SafeInitHandle("h_Bands20_2_H1",  iBands(_Symbol, PERIOD_H1, 20, 0, 2.0, PRICE_CLOSE));
   h_StdDev20_H4   = SafeInitHandle("h_StdDev20_H4",   iStdDev(_Symbol, PERIOD_H4, 20, 0, MODE_SMA, PRICE_CLOSE));
   h_ADX14_H4      = SafeInitHandle("h_ADX14_H4",      iADX(_Symbol, PERIOD_H4, 14));
   h_SAR_H4        = SafeInitHandle("h_SAR_H4",        iSAR(_Symbol, PERIOD_H4, 0.02, 0.2));
   h_Ichimoku_H4   = SafeInitHandle("h_Ichimoku_H4",   iIchimoku(_Symbol, PERIOD_H4, 9, 26, 52));

   // Group 4: Volume Dynamics
   h_OBV_H4        = SafeInitHandle("h_OBV_H4",        iOBV(_Symbol, PERIOD_H4, VOLUME_TICK));
   h_AD_H4         = SafeInitHandle("h_AD_H4",         iAD(_Symbol, PERIOD_H4, VOLUME_TICK));
   h_Force13_H4    = SafeInitHandle("h_Force13_H4",    iForce(_Symbol, PERIOD_H4, 13, MODE_EMA, VOLUME_TICK));

   // Verify Core Gold Handles (Failure is non-recoverable)
   if(h_EMA50_H4 == INVALID_HANDLE || h_EMA200_H4 == INVALID_HANDLE ||
      h_RSI14_H4 == INVALID_HANDLE || h_MACD_H4   == INVALID_HANDLE ||
      h_ATR14_H1 == INVALID_HANDLE || h_ATR14_M15 == INVALID_HANDLE ||
      h_Bands20_2_H4 == INVALID_HANDLE)
   {
      Print("[FATAL] Core Gold indicator handle creation failed. Aborting initialization.");
      return false;
   }

   // Group 5: Inter-Market Handles (Secondary Symbols - Optional)
   InitSecondaryHandles();

   Print("[INIT] Shared Indicator Handles successfully initialized and verified.");
   return true;
}
```

---

### 3.3 Deterministic Release Protocol (`OnDeinit`)

To guarantee zero memory leaks and prevent orphan handles upon EA removal or recompilation, every handle is safely released:

```mql5
void SafeReleaseHandle(int &handle)
{
   if(handle != INVALID_HANDLE)
   {
      IndicatorRelease(handle);
      handle = INVALID_HANDLE;
   }
}

void ReleaseSharedHandles()
{
   Print("[DEINIT] Releasing all 48 shared indicator handles...");

   // Group 1
   SafeReleaseHandle(h_EMA8_H4);   SafeReleaseHandle(h_EMA13_H4);  SafeReleaseHandle(h_EMA20_H4);
   SafeReleaseHandle(h_EMA21_H4);  SafeReleaseHandle(h_EMA34_H4);  SafeReleaseHandle(h_EMA50_H4);
   SafeReleaseHandle(h_EMA55_H4);  SafeReleaseHandle(h_EMA89_H4);  SafeReleaseHandle(h_EMA200_H4);
   SafeReleaseHandle(h_SMA20_H4);  SafeReleaseHandle(h_SMA50_H4);  SafeReleaseHandle(h_SMA200_H4);
   SafeReleaseHandle(h_EMA50_H1);  SafeReleaseHandle(h_EMA200_H1);
   SafeReleaseHandle(h_EMA50_D1);  SafeReleaseHandle(h_EMA200_D1);

   // Group 2
   SafeReleaseHandle(h_RSI14_M15); SafeReleaseHandle(h_RSI14_H1);  SafeReleaseHandle(h_RSI14_H4);
   SafeReleaseHandle(h_RSI14_D1);  SafeReleaseHandle(h_MACD_H4);   SafeReleaseHandle(h_MACD_H1);
   SafeReleaseHandle(h_Stoch_H4);  SafeReleaseHandle(h_CCI20_H4);  SafeReleaseHandle(h_WPR14_H4);
   SafeReleaseHandle(h_MFI14_H4);  SafeReleaseHandle(h_AO_H4);     SafeReleaseHandle(h_Bears13_H4);
   SafeReleaseHandle(h_Bulls13_H4);SafeReleaseHandle(h_Momentum14_H4);

   // Group 3
   SafeReleaseHandle(h_ATR14_M15); SafeReleaseHandle(h_ATR14_H1);  SafeReleaseHandle(h_ATR14_H4);
   SafeReleaseHandle(h_ATR14_D1);  SafeReleaseHandle(h_ATR100_H4); SafeReleaseHandle(h_Bands20_2_H4);
   SafeReleaseHandle(h_Bands20_2_H1); SafeReleaseHandle(h_StdDev20_H4); SafeReleaseHandle(h_ADX14_H4);
   SafeReleaseHandle(h_SAR_H4);    SafeReleaseHandle(h_Ichimoku_H4);

   // Group 4
   SafeReleaseHandle(h_OBV_H4);    SafeReleaseHandle(h_AD_H4);     SafeReleaseHandle(h_Force13_H4);

   // Group 5
   SafeReleaseHandle(h_EURUSD_EMA50); SafeReleaseHandle(h_EURUSD_RSI14);
   SafeReleaseHandle(h_XAGUSD_EMA50); SafeReleaseHandle(h_XAGUSD_RSI14);

   Print("[DEINIT] All indicator handles successfully released.");
}
```

---

## 4. Strict MQL5 Brain Coding Standards

All 47 Brain Builders and 5 Engineering Leads must strictly comply with the following 5 rules. **Any PR or code submission violating these rules will be rejected by CEngO.**

### 4.1 Universal Brain Function Signature

Every brain function must strictly follow this exact signature:

```mql5
int Brain[XX]_[StrategyName]()
```

- **Return Type**: `int` (strictly `+1`, `-1`, or `0`).
- **Parameters**: `void` (no input parameters).
- **Naming Pattern**: `Brain01_CHoCH`, `Brain13_EMACross`, `Brain45_QQE_Momentum`, etc.
- **Pure Analysis**: A brain function **must never**:
  - Mutate any global state or variables (e.g. `g_EntryPrice`, `g_TradedToday`).
  - Place, modify, or close trades (`OrderSend`, `PositionClose`, etc.).
  - Rely on static variables that store state between calls (must be deterministic for the given bar).
  - Call `Print()` on every tick (only log during debug mode or initialization).

### 4.2 Return Value Semantic Contract

| Return Value | Signal State | Interpretation for Daily Gold Direction |
|---|---|---|
| `+1` | **BULLISH** | Conviction for Gold expansion UP during the London/NY session |
| `-1` | **BEARISH** | Conviction for Gold expansion DOWN during the London/NY session |
| `0` | **NEUTRAL** | No edge, ranging/dead market, conflicting indicators, or buffer copy error |

> [!CAUTION]
> Under no circumstances may a brain return values like `2`, `-2`, `100`, or `false`. If a strategy logic cannot establish an edge, it **must** return `0`.

---

### 4.3 Buffer Safety & Array Handling Protocol

Buffer under-runs and uninitialized series indexing are the #1 cause of MT5 EA crashes (`array out of range`).

1. **Mandatory `ArraySetAsSeries(buf, true)`**:
   Every local dynamic array (`double buf[]`) **must** be explicitly flagged as a series array before copying data. This ensures index `[0]` is current, `[1]` is the previous closed bar, `[2]` is two bars ago, etc.
2. **Safe `CopyBuffer` / `CopyHigh` Validation**:
   Never assume data copying succeeded. Check the return code against requested bar count:
   ```mql5
   double rsi[];
   ArraySetAsSeries(rsi, true);
   if(CopyBuffer(h_RSI14_H4, 0, 0, 3, rsi) < 3) 
      return 0; // Return neutral safely if history is loading
   ```
3. **Local Scope Isolation**:
   Arrays used for buffer copies must be **local variables** within the brain function. Never use shared global arrays to prevent race conditions or data corruption between brain evaluations.

---

### 4.4 The Strict Execution Bar Rule (`bar[1]` Confirmed)

**Never use `bar[0]` for signals.**

```mql5
// ❌ REJECTED — REPAINTING BUG
if(rsi[0] > 70.0) return -1; // rsi[0] is fluctuating on every tick!

// ✅ APPROVED — CONFIRMED BAR
if(rsi[1] > 70.0) return -1; // rsi[1] is locked and final!
```

- In MetaTrader 5, `bar[0]` represents the currently forming candle. Its High, Low, Close, and associated indicator values change with every incoming tick.
- Evaluating `bar[0]` causes **intra-bar repainting**, where an EA votes BUY at 09:15 UTC, only for the candle to close as a bearish hammer at 10:00 UTC.
- Every indicator check, price comparison, candlestick detection, and structural swing check **must** evaluate `bar[1]` (the last finalized candle) and older (`bar[2]`, `bar[3]`, etc.).

---

### 4.5 Standard Reference Implementation for Brain Builders

Here is the authoritative template that all Brain Builders must follow:

```mql5
//+------------------------------------------------------------------+
//| Brain 28: RSI Momentum Exhaustion Filter                         |
//| Category: C (Momentum)                                           |
//| Consumer of: h_RSI14_H4                                          |
//+------------------------------------------------------------------+
int Brain28_RSI_Momentum()
{
   // 1. Allocate local series buffer
   double rsi[];
   ArraySetAsSeries(rsi, true);

   // 2. Fetch exactly 3 confirmed bars from the shared global handle
   // Buffer 0 = RSI main line
   if(CopyBuffer(h_RSI14_H4, 0, 0, 4, rsi) < 4)
      return 0; // Insufficient history — vote neutral

   // 3. Evaluate confirmed bars: rsi[1] is last closed H4 bar
   // Bullish momentum: RSI crossing above 50 or bouncing from oversold (<35)
   if(rsi[1] > 50.0 && rsi[2] <= 50.0)
      return 1; // Bullish momentum shift

   if(rsi[1] < 50.0 && rsi[2] >= 50.0)
      return -1; // Bearish momentum shift

   // Overbought / Oversold exhaustion reversal
   if(rsi[1] <= 30.0 && rsi[1] > rsi[2])
      return 1; // Oversold recovery BUY

   if(rsi[1] >= 70.0 && rsi[1] < rsi[2])
      return -1; // Overbought exhaustion SELL

   return 0; // No conviction
}
```

---

## 5. Gold (XAUUSD) Specific Engineering Standards

Trading Gold (XAUUSD) is fundamentally different from trading Forex pairs. The following standards are hardcoded into the infrastructure and enforced across all brains.

### 5.1 Pip Normalization Specification

On virtually all retail and institutional MT5 brokers:
- Gold quotes to **2 decimal places** (`_Digits == 2`).
- The broker tick point is **0.01** (`_Point == 0.01`).
- Therefore: **1 Pip = $0.01 price movement = 1 Point**.

In standard Forex EAs, code often uses `(_Digits == 5 || _Digits == 3) ? 10.0 : 1.0;`. For Gold, `_Digits` is `2`, so `pipFactor` correctly evaluates to `1.0`.

```mql5
// ==============================================================================
// SECTION 5.1: GOLD PIP NORMALIZATION CONSTANTS & HELPERS
// ==============================================================================
double g_PipFactor = 1.0;
double g_PipSize   = 0.01;

void InitGoldPipNormalization()
{
   // For Forex: 5 or 3 digits -> factor is 10.0
   // For Gold (2 digits): factor is strictly 1.0
   g_PipFactor = (_Digits == 5 || _Digits == 3) ? 10.0 : 1.0;
   g_PipSize   = _Point * g_PipFactor; // Always 0.01 for Gold
}

// Convert a pip distance to price distance
double PipsToPrice(double pips)
{
   return pips * g_PipSize;
}

// Convert a price difference to pips
double PriceToPips(double priceDistance)
{
   return priceDistance / g_PipSize;
}
```

> [!IMPORTANT]
> **Zero Tolerance Rule**: Never write `* 0.0001` or `/ 10` in any Gold calculation. Always multiply pip quantities by `g_PipSize` or call `PipsToPrice()`.

---

### 5.2 Spread Gating Protocol

Gold spread fluctuates violently (from 10–25 points during London/NY open to 200–500+ points during news and rollover). Entering a trade with blown spread destroys expectancy.

```mql5
input double InpMaxSpreadPips = 35.0; // Maximum allowed spread for entry (in pips)

bool IsSpreadOK()
{
   long spreadPoints = SymbolInfoInteger(_Symbol, SYMBOL_SPREAD);
   double spreadPips = (double)spreadPoints / g_PipFactor;

   if(spreadPips > InpMaxSpreadPips)
   {
      PrintFormat("[SPREAD GATE] Current spread %.1f pips exceeds max threshold %.1f pips. Entry blocked.",
                  spreadPips, InpMaxSpreadPips);
      return false;
   }
   return true;
}
```

---

### 5.3 Volatility Gating Protocol

Dead markets lead to choppy whipsaws. Before placing the daily 10:00 UTC trade, the execution engine verifies that market energy is sufficient using the shared `h_ATR14_M15` handle.

```mql5
input double InpMinATR_M15_Pips = 40.0; // Minimum M15 ATR required to trade (in pips)

bool IsVolatilityOK()
{
   double atrBuf[];
   ArraySetAsSeries(atrBuf, true);

   if(CopyBuffer(h_ATR14_M15, 0, 0, 3, atrBuf) < 3)
      return false;

   // Convert ATR (price units, e.g. 0.85) to pips
   double atrPips = PriceToPips(atrBuf[1]);

   if(atrPips < InpMinATR_M15_Pips)
   {
      PrintFormat("[VOLATILITY GATE] M15 ATR is %.1f pips (minimum required: %.1f pips). Market dead — skipping trade.",
                  atrPips, InpMinATR_M15_Pips);
      return false;
   }
   return true;
}
```

---

### 5.4 Stop Level & Safe Stop Loss Engine (Error 130 Prevention)

Brokers dynamically widen the minimum stop distance (`SYMBOL_TRADE_STOPS_LEVEL`) during volatile sessions. Placing an SL inside this distance triggers MT5 **Error 130 (TRADE_RETCODE_INVALID_STOPS)** and causes order rejection.

```mql5
double GetSafeSL(int direction, double entryPrice, double desiredSLPips)
{
   long stopLevelPoints = SymbolInfoInteger(_Symbol, SYMBOL_TRADE_STOPS_LEVEL);
   double minDistance   = stopLevelPoints * _Point;
   double wantedDistance= PipsToPrice(desiredSLPips);

   // Add a safety buffer of at least 2 points beyond broker stop level
   double safeDistance  = MathMax(wantedDistance, minDistance + (2.0 * _Point));

   if(direction == 1) // BUY
      return NormalizeDouble(entryPrice - safeDistance, _Digits);
   else               // SELL
      return NormalizeDouble(entryPrice + safeDistance, _Digits);
}
```

---

### 5.5 Institutional Lot Size & Volume Normalization

Gold lot sizes must be precisely clamped to broker minimums, maximums, and volume step increments:

```mql5
double NormalizeLot(double rawLot)
{
   double minLot  = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double maxLot  = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
   double lotStep = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);

   if(lotStep <= 0.0) lotStep = 0.01;

   // Round down to nearest step increment to avoid margin surprises
   double lot = MathFloor(rawLot / lotStep) * lotStep;

   // Clamp within broker limits
   lot = MathMax(minLot, MathMin(maxLot, lot));

   // Determine decimal places for formatting
   int decimals = (lotStep < 0.1) ? 2 : 1;
   return NormalizeDouble(lot, decimals);
}

double CalcRiskLot(double riskPercent, double slPriceDistance)
{
   double equity    = AccountInfoDouble(ACCOUNT_EQUITY);
   double riskMoney = equity * (riskPercent / 100.0);

   double tickValue = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
   double tickSize  = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);

   if(tickSize <= 0.0 || tickValue <= 0.0 || slPriceDistance <= 0.0)
      return SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);

   double slTicks = slPriceDistance / tickSize;
   double rawLot  = riskMoney / (slTicks * tickValue);

   return NormalizeLot(rawLot);
}
```

---

## 6. Category H: Secondary Symbol Handling & Broker Aliasing

Category H strategies (H01–H16) evaluate inter-market relationships (USD, Silver, Oil, Bonds, Equities).

### 6.1 The Broker Symbol Aliasing Problem
Brokers name secondary instruments differently:
- Silver: `XAGUSD`, `SILVER`, `XAGUSD.m`, `XAGUSD_i`, `XAGUSDpro`.
- Euro/USD: `EURUSD`, `EURUSD.m`, `EURUSD_i`.
- Oil: `USOIL`, `WTI`, `XTIUSD`, `CRUDE`.

### 6.2 The Auto-Resolver Pattern
Before attempting to fetch data, the EA queries the broker terminal for matching symbols and enables them in Market Watch via `SymbolSelect()`.

```mql5
string ResolveSymbolName(string baseSymbol)
{
   // 1. Check exact match
   if(SymbolInfoInteger(baseSymbol, SYMBOL_SELECT))
      return baseSymbol;

   // 2. Check with chart symbol suffix
   string currentSymbol = _Symbol;
   int dotPos = StringFind(currentSymbol, ".");
   int underPos = StringFind(currentSymbol, "_");

   if(dotPos > 0)
   {
      string suffix = StringSubstr(currentSymbol, dotPos);
      string candidate = baseSymbol + suffix;
      if(SymbolSelect(candidate, true)) return candidate;
   }
   if(underPos > 0)
   {
      string suffix = StringSubstr(currentSymbol, underPos);
      string candidate = baseSymbol + suffix;
      if(SymbolSelect(candidate, true)) return candidate;
   }

   // 3. Fallback: Search Market Watch
   for(int i = 0; i < SymbolsTotal(false); i++)
   {
      string s = SymbolName(i, false);
      if(StringFind(s, baseSymbol) >= 0)
      {
         SymbolSelect(s, true);
         return s;
      }
   }

   PrintFormat("[WARNING] Secondary symbol %s not found on this broker.", baseSymbol);
   return "";
}

// Graceful Secondary Handle Initialization
void InitSecondaryHandles()
{
   string eurSymbol = ResolveSymbolName("EURUSD");
   if(eurSymbol != "")
   {
      h_EURUSD_EMA50 = iMA(eurSymbol, PERIOD_H4, 50, 0, MODE_EMA, PRICE_CLOSE);
      h_EURUSD_RSI14 = iRSI(eurSymbol, PERIOD_H4, 14, PRICE_CLOSE);
   }

   string xagSymbol = ResolveSymbolName("XAGUSD");
   if(xagSymbol != "")
   {
      h_XAGUSD_EMA50 = iMA(xagSymbol, PERIOD_H4, 50, 0, MODE_EMA, PRICE_CLOSE);
      h_XAGUSD_RSI14 = iRSI(xagSymbol, PERIOD_H4, 14, PRICE_CLOSE);
   }
}
```

> [!TIP]
> **Graceful Degradation Guarantee**: If any secondary symbol is unavailable on a specific broker, its handle remains `INVALID_HANDLE`. Any Category H brain depending on it will immediately detect `handle == INVALID_HANDLE` or `CopyBuffer < N` and **gracefully return 0 (neutral)** without crashing the EA.

---

## 7. Master Monolithic Structure & Verification Standards

The final build file `GoldOracle_v2.mq5` will compile cleanly under MetaEditor with **ZERO ERRORS and ZERO WARNINGS**.

### 7.1 Monolithic Source Code Section Layout

```
Section 1:  File Header, Version, Build Directives & #property Directives
Section 2:  Standard Library Includes (#include <Trade\Trade.mqh>)
Section 3:  User Input Parameters (Risk, Time, ATR Multipliers, Thresholds)
Section 4:  Global Variables, Shared Handle Registry & Struct Definitions
Section 5:  Gold-Specific Normalization & Broker Helper Functions
Section 6:  Hardcoded News Calendar Blackout Engine
Section 7:  Category A: SMC / ICT Brain Functions (A01–A12)
Section 8:  Category B: Trend Following Brain Functions (B01–B15)
Section 9:  Category C: Momentum & Oscillators Brain Functions (C01–C16)
Section 10: Category D: Volatility Brain Functions (D01–D11)
Section 11: Category E: Volume Dynamics Brain Functions (E01–E10)
Section 12: Category F: Fibonacci & Harmonic Brain Functions (F01–F10)
Section 13: Category G: Statistical & Mathematical Brain Functions (G01–G15)
Section 14: Category H: Inter-Market Correlation Brain Functions (H01–H16)
Section 15: Category I: Temporal & Calendar Brain Functions (I01–I15)
Section 16: Category J: Pivot & S-R Brain Functions (J01–J10)
Section 17: Category K: Candlestick Pattern Brain Functions (K01–K12)
Section 18: Category L: Psychological & Sentiment Brain Functions (L01–L08)
Section 19: Category M: Experimental & Mad Scientist Brain Functions (M01–M10)
Section 20: Adaptive Weighting & Exponential Smoothing Engine
Section 21: Composite Score Aggregation & Majority Voting Logic
Section 22: Order Execution & Safe Stop Loss Engine
Section 23: Finite State Machine & Daily Lifecycle Dispatcher
Section 24: MetaTrader 5 Event Handlers (OnInit, OnDeinit, OnTick)
```

### 7.2 Pre-Flight Engineering Checklist for Brain Builders

Before any brain code is integrated:
1. `[ ]` Function signature matches `int BrainXX_Name()`.
2. `[ ]` No indicator initialization (`iMA`, `iRSI`, etc.) inside the brain function.
3. `[ ]` Array set as series (`ArraySetAsSeries(buf, true)`).
4. `[ ]` `CopyBuffer` / `CopyHigh` / `CopyLow` checked for sufficient return count.
5. `[ ]` Only closed bars evaluated (`bar[1]` or older; zero use of `bar[0]`).
6. `[ ]` Returns only `+1`, `-1`, or `0`.
7. `[ ]` Zero division guards on all ratios and differences.
8. `[ ]` Pure function — no modifications to global variables.

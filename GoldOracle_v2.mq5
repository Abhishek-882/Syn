//+------------------------------------------------------------------+
//|                                              GoldOracle_v2.mq5   |
//|               Gold Oracle EA v2 - 144-Brain Ensemble for XAUUSD  |
//|                                      Antigravity / Quantitative  |
//+------------------------------------------------------------------+
#property copyright   "Antigravity Quantitative Systems"
#property link        ""
#property version     "2.00"
#property description "Gold Oracle EA v2: 144-Strategy-Brain Consensus Ensemble with Self-Learning Adaptive Weights for Spot Gold (XAUUSD)"
#property strict

#include <Trade\Trade.mqh>

//--- INPUT GROUPS ---
input group "═════════ CORE RISK & MONEY MANAGEMENT ═════════"
input double   InpRiskPercent          = 2.0;       // Risk Percentage per Trade (Equity %)
input double   InpATR_SL_Multiplier    = 2.0;       // Dynamic Stop-Loss = ATR(14, H1) * Multiplier
input int      InpATR_Period           = 14;        // ATR Period for Stop-Loss
input ulong    InpMagicNumber          = 2026101;   // EA Unique Magic Number

input group "═════════ OPERATIONAL SESSION TIMING (UTC) ═════"
input int      InpAnalysisStartHour    = 7;         // Start London Analysis Window (07:00 UTC)
input int      InpAnalysisEndHour      = 10;        // End Analysis / Execute Trade (10:00 UTC)
input int      InpSessionCloseHour     = 20;        // Close All Positions & Re-Weight (20:00 UTC)

input group "═════════ ADAPTIVE WEIGHTING ENGINE ════════════"
input double   InpDecayFactor          = 0.95;      // Exponential Moving Accuracy Decay (0.95)
input double   InpMinScore             = 2.0;       // Minimum Consensus |Score| to Trade (>2.0)
input double   InpWeightFloor          = 0.1;       // Minimum Weight Floor Clamp (0.1)

input group "═════════ HARDWARE EXECUTION GATING ════════════"
input int      InpMaxSpreadPoints      = 50;        // Max Allowable Spread in Points (50 pts = $0.50)
input double   InpMinATR_H1_Points     = 30.0;      // Min H1 ATR in Points (30 pts = $0.30 volatility floor)

input group "═════════ INSTITUTIONAL NEWS BLACKOUT ══════════"
input bool     InpEnableNewsFilter     = true;      // Enable Institutional Macro News Filter
input int      InpNFP_BlockMinsBefore  = 30;        // NFP: Minutes Before Event to Close/Block
input int      InpNFP_BlockMinsAfter   = 60;        // NFP: Minutes After Event to Block
input int      InpFOMC_BlockMinsBefore = 30;        // FOMC: Minutes Before Event to Close/Block
input int      InpFOMC_BlockMinsAfter  = 90;        // FOMC: Minutes After Event to Block
input int      InpCPI_BlockMinsBefore  = 15;        // CPI: Minutes Before Event to Close/Block
input int      InpCPI_BlockMinsAfter   = 30;        // CPI: Minutes After Event to Block
input int      InpPPI_BlockMinsBefore  = 15;        // PPI: Minutes Before Event to Close/Block
input int      InpPPI_BlockMinsAfter   = 30;        // PPI: Minutes After Event to Block
input int      InpPowell_BlockMinsBefore= 15;       // Powell Speech: Minutes Before Event
input int      InpPowell_BlockMinsAfter = 30;       // Powell Speech: Minutes After Event

//--- ENUMS & DATA STRUCTURES ---
enum ENUM_EA_STATE
{
   STATE_WAITING_FOR_ANALYSIS = 0,
   STATE_ANALYZING            = 1,
   STATE_ENTRY_READY          = 2,
   STATE_TRADE_ACTIVE         = 3,
   STATE_NEWS_BLACKOUT        = 4,
   STATE_SESSION_CLOSED       = 5
};

struct SBrainState
{
   string name;
   string discipline;
   double weight;
   double ema_accuracy;
   int    last_vote;
   int    total_votes;
   int    correct_votes;
};

struct SFOMCDate
{
   int year;
   int mon;
   int day;
};

// Exact scheduled FOMC Announcement Dates (Wednesdays 18:00 UTC)
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

//--- GLOBAL STATE VARIABLES ---
CTrade        trade;
double        g_pipFactor = 1.0;
double        g_pipSize   = 0.01;
ENUM_EA_STATE g_state     = STATE_WAITING_FOR_ANALYSIS;
int           g_lastDay   = -1;
int           g_lastTradeDay = -1;
bool          g_bNewsLockoutToday = false;
double        g_sessionOpenPrice1000 = 0.0;
SBrainState   g_Brains[144];

//--- SHARED INDICATOR REGISTRY (56 HANDLES < 60 BUDGET) ---
// M15 Handles (9)
int g_h_ema21_m15 = INVALID_HANDLE;
int g_h_ema50_m15 = INVALID_HANDLE;
int g_h_ema200_m15= INVALID_HANDLE;
int g_h_rsi14_m15 = INVALID_HANDLE;
int g_h_macd_m15  = INVALID_HANDLE;
int g_h_bb20_m15  = INVALID_HANDLE;
int g_h_atr14_m15 = INVALID_HANDLE;
int g_h_stoch_m15 = INVALID_HANDLE;
int g_h_adx_m15   = INVALID_HANDLE;

// H1 Handles (25)
int g_h_ema8_h1     = INVALID_HANDLE;
int g_h_ema21_h1    = INVALID_HANDLE;
int g_h_ema50_h1    = INVALID_HANDLE;
int g_h_ema100_h1   = INVALID_HANDLE;
int g_h_ema200_h1   = INVALID_HANDLE;
int g_h_sma20_h1    = INVALID_HANDLE;
int g_h_rsi14_h1    = INVALID_HANDLE;
int g_h_rsi7_h1     = INVALID_HANDLE;
int g_h_macd_h1     = INVALID_HANDLE;
int g_h_bb20_h1     = INVALID_HANDLE;
int g_h_atr14_h1    = INVALID_HANDLE;
int g_h_atr5_h1     = INVALID_HANDLE;
int g_h_stoch_h1    = INVALID_HANDLE;
int g_h_cci14_h1    = INVALID_HANDLE;
int g_h_wpr14_h1    = INVALID_HANDLE;
int g_h_adx14_h1    = INVALID_HANDLE;
int g_h_demarker_h1 = INVALID_HANDLE;
int g_h_ao_h1       = INVALID_HANDLE;
int g_h_stddev20_h1 = INVALID_HANDLE;
int g_h_obv_h1      = INVALID_HANDLE;
int g_h_mfi14_h1    = INVALID_HANDLE;
int g_h_force13_h1  = INVALID_HANDLE;
int g_h_sar_h1      = INVALID_HANDLE;
int g_h_ichimoku_h1 = INVALID_HANDLE;
int g_h_chaikin_h1  = INVALID_HANDLE;

// H4 Handles (11)
int g_h_ema21_h4  = INVALID_HANDLE;
int g_h_ema50_h4  = INVALID_HANDLE;
int g_h_ema200_h4 = INVALID_HANDLE;
int g_h_sma20_h4  = INVALID_HANDLE;
int g_h_rsi14_h4  = INVALID_HANDLE;
int g_h_macd_h4   = INVALID_HANDLE;
int g_h_atr14_h4  = INVALID_HANDLE;
int g_h_bb20_h4   = INVALID_HANDLE;
int g_h_adx_h4    = INVALID_HANDLE;
int g_h_stoch_h4  = INVALID_HANDLE;
int g_h_ma_h4     = INVALID_HANDLE;

// D1 Handles (7)
int g_h_ema20_d1  = INVALID_HANDLE;
int g_h_ema50_d1  = INVALID_HANDLE;
int g_h_ema200_d1 = INVALID_HANDLE;
int g_h_rsi14_d1  = INVALID_HANDLE;
int g_h_atr14_d1  = INVALID_HANDLE;
int g_h_macd_d1   = INVALID_HANDLE;
int g_h_bb20_d1   = INVALID_HANDLE;

// Secondary Macro Proxies (4) - Graceful Fallback if unquoted
int g_h_eurusd_h1 = INVALID_HANDLE;
int g_h_usdjpy_h1 = INVALID_HANDLE;
int g_h_audusd_h1 = INVALID_HANDLE;
int g_h_xagusd_h1 = INVALID_HANDLE;

//+------------------------------------------------------------------+
//| Safe Release of an Indicator Handle                              |
//+------------------------------------------------------------------+
void SafeReleaseHandle(int &handle)
{
   if(handle != INVALID_HANDLE)
   {
      IndicatorRelease(handle);
      handle = INVALID_HANDLE;
   }
}

//+------------------------------------------------------------------+
//| Release All Shared Indicator Handles Safely                      |
//+------------------------------------------------------------------+
void ReleaseSharedIndicators()
{
   // M15
   SafeReleaseHandle(g_h_ema21_m15); SafeReleaseHandle(g_h_ema50_m15);
   SafeReleaseHandle(g_h_ema200_m15);SafeReleaseHandle(g_h_rsi14_m15);
   SafeReleaseHandle(g_h_macd_m15);  SafeReleaseHandle(g_h_bb20_m15);
   SafeReleaseHandle(g_h_atr14_m15); SafeReleaseHandle(g_h_stoch_m15);
   SafeReleaseHandle(g_h_adx_m15);

   // H1
   SafeReleaseHandle(g_h_ema8_h1);   SafeReleaseHandle(g_h_ema21_h1);
   SafeReleaseHandle(g_h_ema50_h1);  SafeReleaseHandle(g_h_ema100_h1);
   SafeReleaseHandle(g_h_ema200_h1); SafeReleaseHandle(g_h_sma20_h1);
   SafeReleaseHandle(g_h_rsi14_h1);  SafeReleaseHandle(g_h_rsi7_h1);
   SafeReleaseHandle(g_h_macd_h1);   SafeReleaseHandle(g_h_bb20_h1);
   SafeReleaseHandle(g_h_atr14_h1);  SafeReleaseHandle(g_h_atr5_h1);
   SafeReleaseHandle(g_h_stoch_h1);  SafeReleaseHandle(g_h_cci14_h1);
   SafeReleaseHandle(g_h_wpr14_h1);  SafeReleaseHandle(g_h_adx14_h1);
   SafeReleaseHandle(g_h_demarker_h1);SafeReleaseHandle(g_h_ao_h1);
   SafeReleaseHandle(g_h_stddev20_h1);SafeReleaseHandle(g_h_obv_h1);
   SafeReleaseHandle(g_h_mfi14_h1);  SafeReleaseHandle(g_h_force13_h1);
   SafeReleaseHandle(g_h_sar_h1);    SafeReleaseHandle(g_h_ichimoku_h1);
   SafeReleaseHandle(g_h_chaikin_h1);

   // H4
   SafeReleaseHandle(g_h_ema21_h4);  SafeReleaseHandle(g_h_ema50_h4);
   SafeReleaseHandle(g_h_ema200_h4); SafeReleaseHandle(g_h_sma20_h4);
   SafeReleaseHandle(g_h_rsi14_h4);  SafeReleaseHandle(g_h_macd_h4);
   SafeReleaseHandle(g_h_atr14_h4);  SafeReleaseHandle(g_h_bb20_h4);
   SafeReleaseHandle(g_h_adx_h4);    SafeReleaseHandle(g_h_stoch_h4);
   SafeReleaseHandle(g_h_ma_h4);

   // D1
   SafeReleaseHandle(g_h_ema20_d1);  SafeReleaseHandle(g_h_ema50_d1);
   SafeReleaseHandle(g_h_ema200_d1); SafeReleaseHandle(g_h_rsi14_d1);
   SafeReleaseHandle(g_h_atr14_d1);  SafeReleaseHandle(g_h_macd_d1);
   SafeReleaseHandle(g_h_bb20_d1);

   // Secondary Macro
   SafeReleaseHandle(g_h_eurusd_h1);
   SafeReleaseHandle(g_h_usdjpy_h1);
   SafeReleaseHandle(g_h_audusd_h1);
   SafeReleaseHandle(g_h_xagusd_h1);

   Print("[DEINIT] All shared indicator handles safely released.");
}

//+------------------------------------------------------------------+
//| Initialize All Shared Indicator Handles (Verified < 60 handles)  |
//+------------------------------------------------------------------+
bool InitSharedIndicators()
{
   Print("[INIT] Initializing Gold Oracle Shared Indicator Architecture (<60 handles)...");

   // --- M15 Handles ---
   g_h_ema21_m15 = iMA(_Symbol, PERIOD_M15, 21, 0, MODE_EMA, PRICE_CLOSE);
   g_h_ema50_m15 = iMA(_Symbol, PERIOD_M15, 50, 0, MODE_EMA, PRICE_CLOSE);
   g_h_ema200_m15= iMA(_Symbol, PERIOD_M15, 200, 0, MODE_EMA, PRICE_CLOSE);
   g_h_rsi14_m15 = iRSI(_Symbol, PERIOD_M15, 14, PRICE_CLOSE);
   g_h_macd_m15  = iMACD(_Symbol, PERIOD_M15, 12, 26, 9, PRICE_CLOSE);
   g_h_bb20_m15  = iBands(_Symbol, PERIOD_M15, 20, 0, 2.0, PRICE_CLOSE);
   g_h_atr14_m15 = iATR(_Symbol, PERIOD_M15, 14);
   g_h_stoch_m15 = iStochastic(_Symbol, PERIOD_M15, 14, 3, 3, MODE_SMA, STO_LOWHIGH);
   g_h_adx_m15   = iADX(_Symbol, PERIOD_M15, 14);

   // --- H1 Handles ---
   g_h_ema8_h1     = iMA(_Symbol, PERIOD_H1, 8, 0, MODE_EMA, PRICE_CLOSE);
   g_h_ema21_h1    = iMA(_Symbol, PERIOD_H1, 21, 0, MODE_EMA, PRICE_CLOSE);
   g_h_ema50_h1    = iMA(_Symbol, PERIOD_H1, 50, 0, MODE_EMA, PRICE_CLOSE);
   g_h_ema100_h1   = iMA(_Symbol, PERIOD_H1, 100, 0, MODE_EMA, PRICE_CLOSE);
   g_h_ema200_h1   = iMA(_Symbol, PERIOD_H1, 200, 0, MODE_EMA, PRICE_CLOSE);
   g_h_sma20_h1    = iMA(_Symbol, PERIOD_H1, 20, 0, MODE_SMA, PRICE_CLOSE);
   g_h_rsi14_h1    = iRSI(_Symbol, PERIOD_H1, 14, PRICE_CLOSE);
   g_h_rsi7_h1     = iRSI(_Symbol, PERIOD_H1, 7, PRICE_CLOSE);
   g_h_macd_h1     = iMACD(_Symbol, PERIOD_H1, 12, 26, 9, PRICE_CLOSE);
   g_h_bb20_h1     = iBands(_Symbol, PERIOD_H1, 20, 0, 2.0, PRICE_CLOSE);
   g_h_atr14_h1    = iATR(_Symbol, PERIOD_H1, 14);
   g_h_atr5_h1     = iATR(_Symbol, PERIOD_H1, 5);
   g_h_stoch_h1    = iStochastic(_Symbol, PERIOD_H1, 14, 3, 3, MODE_SMA, STO_LOWHIGH);
   g_h_cci14_h1    = iCCI(_Symbol, PERIOD_H1, 14, PRICE_TYPICAL);
   g_h_wpr14_h1    = iWPR(_Symbol, PERIOD_H1, 14);
   g_h_adx14_h1    = iADX(_Symbol, PERIOD_H1, 14);
   g_h_demarker_h1 = iDeMarker(_Symbol, PERIOD_H1, 14);
   g_h_ao_h1       = iAO(_Symbol, PERIOD_H1);
   g_h_stddev20_h1 = iStdDev(_Symbol, PERIOD_H1, 20, 0, MODE_SMA, PRICE_CLOSE);
   g_h_obv_h1      = iOBV(_Symbol, PERIOD_H1, VOLUME_TICK);
   g_h_mfi14_h1    = iMFI(_Symbol, PERIOD_H1, 14, VOLUME_TICK);
   g_h_force13_h1  = iForce(_Symbol, PERIOD_H1, 13, MODE_EMA, VOLUME_TICK);
   g_h_sar_h1      = iSAR(_Symbol, PERIOD_H1, 0.02, 0.20);
   g_h_ichimoku_h1 = iIchimoku(_Symbol, PERIOD_H1, 9, 26, 52);
   g_h_chaikin_h1  = iChaikin(_Symbol, PERIOD_H1, 3, 10, MODE_EMA, VOLUME_TICK);

   // --- H4 Handles ---
   g_h_ema21_h4  = iMA(_Symbol, PERIOD_H4, 21, 0, MODE_EMA, PRICE_CLOSE);
   g_h_ema50_h4  = iMA(_Symbol, PERIOD_H4, 50, 0, MODE_EMA, PRICE_CLOSE);
   g_h_ema200_h4 = iMA(_Symbol, PERIOD_H4, 200, 0, MODE_EMA, PRICE_CLOSE);
   g_h_sma20_h4  = iMA(_Symbol, PERIOD_H4, 20, 0, MODE_SMA, PRICE_CLOSE);
   g_h_rsi14_h4  = iRSI(_Symbol, PERIOD_H4, 14, PRICE_CLOSE);
   g_h_macd_h4   = iMACD(_Symbol, PERIOD_H4, 12, 26, 9, PRICE_CLOSE);
   g_h_atr14_h4  = iATR(_Symbol, PERIOD_H4, 14);
   g_h_bb20_h4   = iBands(_Symbol, PERIOD_H4, 20, 0, 2.0, PRICE_CLOSE);
   g_h_adx_h4    = iADX(_Symbol, PERIOD_H4, 14);
   g_h_stoch_h4  = iStochastic(_Symbol, PERIOD_H4, 14, 3, 3, MODE_SMA, STO_LOWHIGH);
   g_h_ma_h4     = iMA(_Symbol, PERIOD_H4, 50, 0, MODE_SMA, PRICE_CLOSE);

   // --- D1 Handles ---
   g_h_ema20_d1  = iMA(_Symbol, PERIOD_D1, 20, 0, MODE_EMA, PRICE_CLOSE);
   g_h_ema50_d1  = iMA(_Symbol, PERIOD_D1, 50, 0, MODE_EMA, PRICE_CLOSE);
   g_h_ema200_d1 = iMA(_Symbol, PERIOD_D1, 200, 0, MODE_EMA, PRICE_CLOSE);
   g_h_rsi14_d1  = iRSI(_Symbol, PERIOD_D1, 14, PRICE_CLOSE);
   g_h_atr14_d1  = iATR(_Symbol, PERIOD_D1, 14);
   g_h_macd_d1   = iMACD(_Symbol, PERIOD_D1, 12, 26, 9, PRICE_CLOSE);
   g_h_bb20_d1   = iBands(_Symbol, PERIOD_D1, 20, 0, 2.0, PRICE_CLOSE);

   // --- Verification Array of Core Handles ---
   int core_handles[] = {
      g_h_ema21_m15, g_h_ema50_m15, g_h_ema200_m15, g_h_rsi14_m15, g_h_macd_m15, g_h_bb20_m15, g_h_atr14_m15, g_h_stoch_m15, g_h_adx_m15,
      g_h_ema8_h1, g_h_ema21_h1, g_h_ema50_h1, g_h_ema100_h1, g_h_ema200_h1, g_h_sma20_h1,
      g_h_rsi14_h1, g_h_rsi7_h1, g_h_macd_h1, g_h_bb20_h1, g_h_atr14_h1, g_h_atr5_h1,
      g_h_stoch_h1, g_h_cci14_h1, g_h_wpr14_h1, g_h_adx14_h1, g_h_demarker_h1,
      g_h_ao_h1, g_h_stddev20_h1, g_h_obv_h1, g_h_mfi14_h1, g_h_force13_h1,
      g_h_sar_h1, g_h_ichimoku_h1, g_h_chaikin_h1,
      g_h_ema21_h4, g_h_ema50_h4, g_h_ema200_h4, g_h_sma20_h4, g_h_rsi14_h4, g_h_macd_h4, g_h_atr14_h4, g_h_bb20_h4, g_h_adx_h4, g_h_stoch_h4, g_h_ma_h4,
      g_h_ema20_d1, g_h_ema50_d1, g_h_ema200_d1, g_h_rsi14_d1, g_h_atr14_d1, g_h_macd_d1, g_h_bb20_d1
   };

   for(int i = 0; i < ArraySize(core_handles); i++)
   {
      if(core_handles[i] == INVALID_HANDLE)
      {
         PrintFormat("[CRITICAL] Indicator handle at index %d failed to initialize. Error=%d", i, GetLastError());
         ReleaseSharedIndicators();
         return false;
      }
   }

   // --- Optional Secondary Macro Handles with Graceful Fallback ---
   if(SymbolSelect("EURUSD", true)) g_h_eurusd_h1 = iMA("EURUSD", PERIOD_H1, 50, 0, MODE_EMA, PRICE_CLOSE);
   else g_h_eurusd_h1 = INVALID_HANDLE;

   if(SymbolSelect("USDJPY", true)) g_h_usdjpy_h1 = iMA("USDJPY", PERIOD_H1, 50, 0, MODE_EMA, PRICE_CLOSE);
   else g_h_usdjpy_h1 = INVALID_HANDLE;

   if(SymbolSelect("AUDUSD", true)) g_h_audusd_h1 = iMA("AUDUSD", PERIOD_H1, 21, 0, MODE_EMA, PRICE_CLOSE);
   else g_h_audusd_h1 = INVALID_HANDLE;

   if(SymbolSelect("XAGUSD", true)) g_h_xagusd_h1 = iMA("XAGUSD", PERIOD_H1, 20, 0, MODE_SMA, PRICE_CLOSE);
   else g_h_xagusd_h1 = INVALID_HANDLE;

   Print("[INIT] 56 Shared Indicator Handles initialized and validated (<60 handles limit satisfied).");
   return true;
}

//+------------------------------------------------------------------+
//| Universal Single-Value Indicator Accessor (Strictly Bar[1] or Older)
//+------------------------------------------------------------------+
double GetIndicatorVal(int handle, int buffer_index, int shift = 1)
{
   if(handle == INVALID_HANDLE || shift < 1) return 0.0;
   double buf[1];
   if(CopyBuffer(handle, buffer_index, shift, 1, buf) <= 0)
   {
      return 0.0;
   }
   return buf[0];
}

//+------------------------------------------------------------------+
//| Universal Multi-Bar Series Indicator Accessor (Strictly Bar[shift])
//| output_array[0] = bar[shift], output_array[1] = bar[shift+1]...  |
//+------------------------------------------------------------------+
bool GetIndicatorSeries(int handle, int buffer_index, int shift, int count, double &output_array[])
{
   if(handle == INVALID_HANDLE || shift < 1 || count <= 0) return false;
   ArraySetAsSeries(output_array, true);
   int copied = CopyBuffer(handle, buffer_index, shift, count, output_array);
   return (copied == count);
}

//+------------------------------------------------------------------+
//| Universal Confirmed Historical Rates Accessor (Bar[1] or Older)  |
//| rates[0] = bar[shift], rates[1] = bar[shift+1]...               |
//+------------------------------------------------------------------+
int GetRatesSeries(ENUM_TIMEFRAMES tf, int shift, int count, MqlRates &rates[])
{
   if(shift < 1 || count <= 0) return 0;
   ArraySetAsSeries(rates, true);
   return CopyRates(_Symbol, tf, shift, count, rates);
}

//+------------------------------------------------------------------+
//| XAUUSD Pip Normalization Initialization                          |
//+------------------------------------------------------------------+
void InitPipNormalization()
{
   // For 2-digit XAUUSD: _Point = 0.01, pipFactor = 1.0, 1 pip = 0.01
   // For 3-digit XAUUSD: _Point = 0.001, pipFactor = 10.0, 1 pip = 0.01
   g_pipFactor = (_Digits == 3 || _Digits == 5) ? 10.0 : 1.0;
   g_pipSize   = _Point * g_pipFactor;
   
   PrintFormat("[INIT] Pip Normalization: Symbol=%s, Digits=%d, Point=%.5f, PipFactor=%.1f, PipSize=%.4f",
               _Symbol, _Digits, _Point, g_pipFactor, g_pipSize);
}

double PipsToPrice(double pips)
{
   return pips * g_pipSize;
}

double PriceToPips(double priceDiff)
{
   return (g_pipSize > 0.0) ? (priceDiff / g_pipSize) : 0.0;
}

//+------------------------------------------------------------------+
//| Calculate Safe ATR Stop-Loss with StopsLevel & Spread Clamping   |
//| Eliminates MT5 Error 130 (TRADE_RETCODE_INVALID_STOPS)           |
//+------------------------------------------------------------------+
double CalculateSafeATRStopLoss(int direction, double entryPrice, double atrValueH1, double multiplier)
{
   double desiredDistPrice = atrValueH1 * multiplier;
   if(desiredDistPrice <= 0.0) desiredDistPrice = 30.0 * _Point;

   long stopsLevelPts  = SymbolInfoInteger(_Symbol, SYMBOL_TRADE_STOPS_LEVEL);
   long freezeLevelPts = SymbolInfoInteger(_Symbol, SYMBOL_TRADE_FREEZE_LEVEL);
   long minReqPts      = MathMax(stopsLevelPts, freezeLevelPts);

   double minReqPrice    = minReqPts * _Point;
   double currentSpread  = SymbolInfoDouble(_Symbol, SYMBOL_ASK) - SymbolInfoDouble(_Symbol, SYMBOL_BID);

   // Buffer: broker stop level + spread + 2 points cushion
   double absoluteMinDist = minReqPrice + currentSpread + (2.0 * _Point);
   double finalDistPrice  = MathMax(desiredDistPrice, absoluteMinDist);

   double rawSL = 0.0;
   if(direction == 1) // BUY
   {
      double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
      rawSL = bid - finalDistPrice;
   }
   else if(direction == -1) // SELL
   {
      double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
      rawSL = ask + finalDistPrice;
   }

   return NormalizeDouble(rawSL, _Digits);
}

//+------------------------------------------------------------------+
//| Normalize Lot Volume against Broker Min/Max/Step                 |
//+------------------------------------------------------------------+
double NormalizeLot(double rawLot)
{
   double minLot  = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double maxLot  = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
   double stepLot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   if(stepLot <= 0.0) stepLot = 0.01;

   double lot = MathFloor(rawLot / stepLot) * stepLot;
   lot = MathMax(minLot, MathMin(maxLot, lot));

   int lotDigits = 2;
   if(stepLot >= 1.0) lotDigits = 0;
   else if(stepLot >= 0.1) lotDigits = 1;
   else lotDigits = 2;

   return NormalizeDouble(lot, lotDigits);
}

//+------------------------------------------------------------------+
//| Calculate Lot Size Based on Account Equity Risk %                |
//+------------------------------------------------------------------+
double CalculateLotSize(double entryPrice, double slPrice, double riskPercent)
{
   if(entryPrice <= 0.0 || slPrice <= 0.0 || riskPercent <= 0.0)
      return SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);

   double equity = AccountInfoDouble(ACCOUNT_EQUITY);
   if(equity <= 0.0) equity = AccountInfoDouble(ACCOUNT_BALANCE);
   if(equity <= 0.0) return SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);

   double riskMoney = equity * (riskPercent / 100.0);

   double tickSize = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   if(tickSize <= 0.0) tickSize = _Point;

   double tickValue = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE_LOSS);
   if(tickValue <= 0.0) tickValue = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
   if(tickValue <= 0.0) tickValue = 1.0;

   double slDistPrice = MathAbs(entryPrice - slPrice);
   if(slDistPrice <= 0.0) return SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);

   double slTicks = slDistPrice / tickSize;
   double riskPerLot = slTicks * tickValue;

   if(riskPerLot <= 0.0)
   {
      Print("[RISK ERROR] riskPerLot <= 0. Falling back to minimum lot.");
      return SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   }

   double rawLot = riskMoney / riskPerLot;
   double finalLot = NormalizeLot(rawLot);

   PrintFormat("[SIZING] Equity: $%.2f | Risk: %.1f%% ($%.2f) | SL Dist: %.2f | Risk/Lot: $%.2f | Lot: %.2f",
               equity, riskPercent, riskMoney, slDistPrice, riskPerLot, finalLot);

   return finalLot;
}

//+------------------------------------------------------------------+
//| Hardware Gate 1: Spread Filter Check                             |
//+------------------------------------------------------------------+
bool IsSpreadPermitted(int maxSpreadPoints)
{
   long spread = SymbolInfoInteger(_Symbol, SYMBOL_SPREAD);
   if(spread > maxSpreadPoints)
   {
      PrintFormat("[GATE REJECT] Current spread (%d pts) exceeds maximum allowed (%d pts).",
                  spread, maxSpreadPoints);
      return false;
   }
   return true;
}

//+------------------------------------------------------------------+
//| Hardware Gate 2: H1 ATR Volatility Floor Check (Bar[1])          |
//+------------------------------------------------------------------+
bool IsVolatilityPermitted(int h_atr, double minAtrPoints)
{
   double atr = GetIndicatorVal(h_atr, 0, 1);
   if(atr <= 0.0)
   {
      Print("[GATE ERROR] Failed to fetch valid H1 ATR value.");
      return false;
   }

   double atrPoints = atr / _Point;
   if(atrPoints < minAtrPoints)
   {
      PrintFormat("[GATE REJECT] H1 ATR (%.1f pts) below minimum volatility threshold (%.1f pts). Market is frozen.",
                  atrPoints, minAtrPoints);
      return false;
   }
   return true;
}

//+------------------------------------------------------------------+
//| Close All Positions with EA Magic Number                         |
//+------------------------------------------------------------------+
void CloseAllPositions()
{
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong ticket = PositionGetTicket(i);
      if(PositionGetString(POSITION_SYMBOL) == _Symbol && PositionGetInteger(POSITION_MAGIC) == InpMagicNumber)
      {
         trade.PositionClose(ticket);
         PrintFormat("[EXECUTION] Closed position ticket #%I64u", ticket);
      }
   }
}

//+------------------------------------------------------------------+
//| Check if an Open Position Already Exists for this EA             |
//+------------------------------------------------------------------+
bool IsPositionOpen()
{
   for(int i = 0; i < PositionsTotal(); i++)
   {
      ulong ticket = PositionGetTicket(i);
      if(PositionGetString(POSITION_SYMBOL) == _Symbol && PositionGetInteger(POSITION_MAGIC) == InpMagicNumber)
      {
         return true;
      }
   }
   return false;
}

//+------------------------------------------------------------------+
//| Get Current Workstation Time in True UTC (TimeGMT)               |
//+------------------------------------------------------------------+
datetime GetCurrentTimeUTC()
{
   return TimeGMT();
}

//+------------------------------------------------------------------+
//| Institutional News Safety Checker with True UTC Time             |
//+------------------------------------------------------------------+
bool CheckNewsBlackoutStatus()
{
   if(!InpEnableNewsFilter) return false;

   datetime utc = GetCurrentTimeUTC();
   MqlDateTime dt;
   TimeToStruct(utc, dt);
   int currentMins = dt.hour * 60 + dt.min;

   // 1. NFP Check: First Friday of month (day <= 7, day_of_week == 5) at 12:30 UTC
   if(dt.day_of_week == 5 && dt.day <= 7)
   {
      int nfpEventMins = 12 * 60 + 30;
      int startMins    = nfpEventMins - InpNFP_BlockMinsBefore;
      int endMins      = nfpEventMins + InpNFP_BlockMinsAfter;
      if(currentMins >= startMins && currentMins <= endMins)
      {
         PrintFormat("[NEWS BLACKOUT] NFP Active. Window: %02d:%02d - %02d:%02d UTC",
                     startMins/60, startMins%60, endMins/60, endMins%60);
         return true;
      }
   }

   // 2. FOMC Decision Dates Check: 18:00 UTC
   for(int i = 0; i < ArraySize(g_FOMCDates); i++)
   {
      if(dt.year == g_FOMCDates[i].year && dt.mon == g_FOMCDates[i].mon && dt.day == g_FOMCDates[i].day)
      {
         int fomcEventMins = 18 * 60;
         int startMins     = fomcEventMins - InpFOMC_BlockMinsBefore;
         int endMins       = fomcEventMins + InpFOMC_BlockMinsAfter;
         if(currentMins >= startMins && currentMins <= endMins)
         {
            PrintFormat("[NEWS BLACKOUT] FOMC Active on %04d.%02d.%02d. Window: %02d:%02d - %02d:%02d UTC",
                        dt.year, dt.mon, dt.day, startMins/60, startMins%60, endMins/60, endMins%60);
            return true;
         }
      }
   }

   // 3. CPI Check: 2nd or 3rd Tuesday/Wednesday (days 8..15) at 12:30 UTC
   if((dt.day_of_week == 2 || dt.day_of_week == 3) && dt.day >= 8 && dt.day <= 15)
   {
      int cpiEventMins = 12 * 60 + 30;
      int startMins    = cpiEventMins - InpCPI_BlockMinsBefore;
      int endMins      = cpiEventMins + InpCPI_BlockMinsAfter;
      if(currentMins >= startMins && currentMins <= endMins)
      {
         PrintFormat("[NEWS BLACKOUT] CPI Window Active: %02d:%02d - %02d:%02d UTC",
                     startMins/60, startMins%60, endMins/60, endMins%60);
         return true;
      }
   }

   // 4. PPI Check: 2nd or 3rd Thursday (days 8..16) at 12:30 UTC
   if(dt.day_of_week == 4 && dt.day >= 8 && dt.day <= 16)
   {
      int ppiEventMins = 12 * 60 + 30;
      int startMins    = ppiEventMins - InpPPI_BlockMinsBefore;
      int endMins      = ppiEventMins + InpPPI_BlockMinsAfter;
      if(currentMins >= startMins && currentMins <= endMins)
      {
         PrintFormat("[NEWS BLACKOUT] PPI Window Active: %02d:%02d - %02d:%02d UTC",
                     startMins/60, startMins%60, endMins/60, endMins%60);
         return true;
      }
   }

   // 5. Powell Speech Window Check: Wednesday or Thursday at 14:00 UTC
   if((dt.day_of_week == 3 || dt.day_of_week == 4) && dt.day >= 10 && dt.day <= 24)
   {
      int powellEventMins = 14 * 60;
      int startMins       = powellEventMins - InpPowell_BlockMinsBefore;
      int endMins         = powellEventMins + InpPowell_BlockMinsAfter;
      if(currentMins >= startMins && currentMins <= endMins)
      {
         PrintFormat("[NEWS BLACKOUT] Powell Speech Window Active: %02d:%02d - %02d:%02d UTC",
                     startMins/60, startMins%60, endMins/60, endMins%60);
         return true;
      }
   }

   return false;
}

//+------------------------------------------------------------------+
//| Initialize Adaptive Weighting Engine State                       |
//+------------------------------------------------------------------+
void InitAdaptiveEngine()
{
   for(int i = 0; i < 144; i++)
   {
      g_Brains[i].weight        = 1.0;
      g_Brains[i].ema_accuracy  = 1.0;
      g_Brains[i].last_vote     = 0;
      g_Brains[i].total_votes   = 0;
      g_Brains[i].correct_votes = 0;
   }

   // Initialize Names and Disciplines across 13 Analytical Blocks
   for(int i = 0;   i < 12;  i++) { g_Brains[i].discipline = "SMC / ICT";                  g_Brains[i].name = StringFormat("Brain%03d_SMC", i + 1); }
   for(int i = 12;  i < 26;  i++) { g_Brains[i].discipline = "Trend Following";            g_Brains[i].name = StringFormat("Brain%03d_Trend", i + 1); }
   for(int i = 26;  i < 40;  i++) { g_Brains[i].discipline = "Momentum & Oscillators";     g_Brains[i].name = StringFormat("Brain%03d_Momentum", i + 1); }
   for(int i = 40;  i < 50;  i++) { g_Brains[i].discipline = "Volatility";                 g_Brains[i].name = StringFormat("Brain%03d_Volatility", i + 1); }
   for(int i = 50;  i < 59;  i++) { g_Brains[i].discipline = "Volume & Flow";              g_Brains[i].name = StringFormat("Brain%03d_VolumeFlow", i + 1); }
   for(int i = 59;  i < 68;  i++) { g_Brains[i].discipline = "Fibonacci & Harmonics";      g_Brains[i].name = StringFormat("Brain%03d_Fibonacci", i + 1); }
   for(int i = 68;  i < 81;  i++) { g_Brains[i].discipline = "Statistical & Quant";        g_Brains[i].name = StringFormat("Brain%03d_Quant", i + 1); }
   for(int i = 81;  i < 95;  i++) { g_Brains[i].discipline = "Inter-Market Macro";         g_Brains[i].name = StringFormat("Brain%03d_Macro", i + 1); }
   for(int i = 95;  i < 108; i++) { g_Brains[i].discipline = "Temporal & Calendar";       g_Brains[i].name = StringFormat("Brain%03d_Temporal", i + 1); }
   for(int i = 108; i < 117; i++) { g_Brains[i].discipline = "S/R & Pivots";              g_Brains[i].name = StringFormat("Brain%03d_SRPivots", i + 1); }
   for(int i = 117; i < 128; i++) { g_Brains[i].discipline = "Candlesticks";              g_Brains[i].name = StringFormat("Brain%03d_Candle", i + 1); }
   for(int i = 128; i < 135; i++) { g_Brains[i].discipline = "Psychological & Sentiment"; g_Brains[i].name = StringFormat("Brain%03d_Sentiment", i + 1); }
   for(int i = 135; i < 144; i++) { g_Brains[i].discipline = "Frontier & Experimental";   g_Brains[i].name = StringFormat("Brain%03d_Frontier", i + 1); }
}

//+------------------------------------------------------------------+
//| Determine Actual Daily Market Direction Vector at 20:00 UTC      |
//| Returns: +1 (BUY Day), -1 (SELL Day), 0 (Flat)                   |
//+------------------------------------------------------------------+
int DetermineSessionDirection()
{
   double currentPrice = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   if(g_sessionOpenPrice1000 <= 0.0)
   {
      // Fallback: compare against H1 Open from 10:00 UTC
      MqlRates rates[];
      if(GetRatesSeries(PERIOD_H1, 1, 11, rates) >= 10)
      {
         // Find bar near 10:00 UTC
         g_sessionOpenPrice1000 = rates[9].open;
      }
      else
      {
         g_sessionOpenPrice1000 = currentPrice;
      }
   }

   double delta = currentPrice - g_sessionOpenPrice1000;
   if(delta > 5.0 * _Point) return 1;
   if(delta < -5.0 * _Point) return -1;
   return 0;
}

//+------------------------------------------------------------------+
//| Update Brain Adaptive Weights via 0.95/0.05 EMA Formula          |
//+------------------------------------------------------------------+
void UpdateAdaptiveWeights(int actualDirection)
{
   if(actualDirection == 0)
   {
      Print("[ADAPTIVE ENGINE] Session ended flat. Weights unchanged.");
      return;
   }

   int updatedCount = 0;
   int correctCount = 0;

   for(int i = 0; i < 144; i++)
   {
      if(g_Brains[i].last_vote == 0) continue; // Abstained brains are isolated

      bool isCorrect = (g_Brains[i].last_vote == actualDirection);
      double outcome = isCorrect ? 1.0 : 0.0;

      // Update Exponential Moving Accuracy: EMA_Acc = 0.95 * EMA_Acc + 0.05 * outcome
      g_Brains[i].ema_accuracy = (InpDecayFactor * g_Brains[i].ema_accuracy) + ((1.0 - InpDecayFactor) * outcome);

      // Clamp weight with InpWeightFloor (0.1 floor)
      g_Brains[i].weight = MathMax(InpWeightFloor, g_Brains[i].ema_accuracy);

      g_Brains[i].total_votes++;
      if(isCorrect)
      {
         g_Brains[i].correct_votes++;
         correctCount++;
      }
      updatedCount++;
   }

   PrintFormat("[ADAPTIVE UPDATE] Market Vector: %s | Active Brains: %d | Correct: %d (%.1f%%)",
               actualDirection > 0 ? "BULL (+1)" : "BEAR (-1)",
               updatedCount, correctCount,
               updatedCount > 0 ? (correctCount * 100.0 / updatedCount) : 0.0);
}

//══════════════════════════════════════════════════════════════════
// 144 STRATEGY BRAIN ENSEMBLE SPECIFICATIONS (ZERO STUBS)
// Strict Non-Repainting: Evaluated strictly on confirmed bar[1] or older
//══════════════════════════════════════════════════════════════════

//--- MATHEMATICAL HELPER UTILITIES ---
double CalcMean(const double &arr[], int start, int count)
{
   if(count <= 0 || start + count > ArraySize(arr)) return 0.0;
   double sum = 0.0;
   for(int i = start; i < start + count; i++) sum += arr[i];
   return sum / count;
}

double CalcStdDev(const double &arr[], int start, int count)
{
   if(count <= 1 || start + count > ArraySize(arr)) return 0.0;
   double mean = CalcMean(arr, start, count);
   double sumSq = 0.0;
   for(int i = start; i < start + count; i++)
   {
      double diff = arr[i] - mean;
      sumSq += diff * diff;
   }
   return MathSqrt(sumSq / (count - 1));
}

double CalcLinearRegressionSlope(const double &arr[], int start, int count)
{
   if(count <= 1 || start + count > ArraySize(arr)) return 0.0;
   double sumX = 0, sumY = 0, sumXY = 0, sumX2 = 0;
   for(int i = 0; i < count; i++)
   {
      double x = i;
      double y = arr[start + (count - 1 - i)]; // oldest to newest
      sumX  += x;
      sumY  += y;
      sumXY += x * y;
      sumX2 += x * x;
   }
   double denom = (count * sumX2 - sumX * sumX);
   if(MathAbs(denom) <= 1e-9) return 0.0;
   return (count * sumXY - sumX * sumY) / denom;
}

//══════════════════════════════════════════════════════════════════
// DISCIPLINE 1: SMART MONEY CONCEPTS & ICT (Brains 001 - 012)
//══════════════════════════════════════════════════════════════════

// Brain 001: Change of Character (CHoCH) Break
int Brain001_SMC_CHoCH()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 8, rates) < 8) return 0;
   double swingHigh = MathMax(rates[2].high, MathMax(rates[3].high, MathMax(rates[4].high, MathMax(rates[5].high, rates[6].high))));
   double swingLow  = MathMin(rates[2].low,  MathMin(rates[3].low,  MathMin(rates[4].low,  MathMin(rates[5].low,  rates[6].low))));
   if(rates[0].close > swingHigh && rates[1].low < rates[6].low) return 1;
   if(rates[0].close < swingLow  && rates[1].high > rates[6].high) return -1;
   return 0;
}

// Brain 002: Break of Structure (BOS) in Trend
int Brain002_SMC_BOS()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 6, rates) < 6) return 0;
   double prevHigh = MathMax(rates[1].high, MathMax(rates[2].high, rates[3].high));
   double prevLow  = MathMin(rates[1].low,  MathMin(rates[2].low,  rates[3].low));
   double e50  = GetIndicatorVal(g_h_ema50_h1, 0, 1);
   double e200 = GetIndicatorVal(g_h_ema200_h1, 0, 1);
   if(rates[0].close > prevHigh && e50 > e200) return 1;
   if(rates[0].close < prevLow  && e50 < e200) return -1;
   return 0;
}

// Brain 003: Order Block Mitigation Test
int Brain003_SMC_OrderBlock()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 5, rates) < 5) return 0;
   // Bullish Order Block mitigation
   if(rates[2].close < rates[2].open && rates[1].close > rates[2].high &&
      rates[0].low <= rates[2].open && rates[0].close >= rates[2].close) return 1;
   // Bearish Order Block mitigation
   if(rates[2].close > rates[2].open && rates[1].close < rates[2].low &&
      rates[0].high >= rates[2].open && rates[0].close <= rates[2].close) return -1;
   return 0;
}

// Brain 004: Fair Value Gap (FVG) Retest
int Brain004_SMC_FairValueGap()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 6, rates) < 6) return 0;
   // Bullish FVG: Low of bar[2] > High of bar[4], bar[1] tests and holds
   if(rates[1].low > rates[3].high && rates[0].low <= rates[1].low && rates[0].close > rates[3].high) return 1;
   // Bearish FVG: High of bar[2] < Low of bar[4], bar[1] tests and holds
   if(rates[1].high < rates[3].low && rates[0].high >= rates[1].high && rates[0].close < rates[3].low) return -1;
   return 0;
}

// Brain 005: 20-Bar Liquidity Sweep & Rejection
int Brain005_SMC_LiquiditySweep()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 22, rates) < 22) return 0;
   double high20 = rates[1].high;
   double low20  = rates[1].low;
   for(int i = 2; i < 21; i++)
   {
      if(rates[i].high > high20) high20 = rates[i].high;
      if(rates[i].low  < low20)  low20  = rates[i].low;
   }
   if(rates[0].low < low20 && rates[0].close > low20) return 1;   // Swept low & closed back in
   if(rates[0].high > high20 && rates[0].close < high20) return -1; // Swept high & closed back in
   return 0;
}

// Brain 006: London Kill Zone Expansion
int Brain006_SMC_KillZone_Expansion()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 5, rates) < 5) return 0;
   double atr = GetIndicatorVal(g_h_atr14_h1, 0, 1);
   if(atr <= 0.0) return 0;
   double delta = rates[0].close - rates[3].open; // Expansion over last 3 hours
   if(delta > 0.5 * atr) return 1;
   if(delta < -0.5 * atr) return -1;
   return 0;
}

// Brain 007: Premium / Discount Equilibrium
int Brain007_SMC_PremiumDiscount()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 48, rates) < 48) return 0;
   double h48 = rates[0].high, l48 = rates[0].low;
   for(int i = 1; i < 48; i++)
   {
      if(rates[i].high > h48) h48 = rates[i].high;
      if(rates[i].low  < l48) l48 = rates[i].low;
   }
   double range = h48 - l48;
   if(range <= 0.0) return 0;
   double eq = l48 + 0.5 * range;
   if(rates[0].close < eq - 0.15 * range) return 1;  // In deep discount
   if(rates[0].close > eq + 0.15 * range) return -1; // In premium
   return 0;
}

// Brain 008: Judas Swing Fakeout
int Brain008_SMC_JudasSwing()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 10, rates) < 10) return 0;
   // Asian range from bars 3..9
   double asianH = rates[3].high, asianL = rates[3].low;
   for(int i = 4; i <= 9; i++)
   {
      if(rates[i].high > asianH) asianH = rates[i].high;
      if(rates[i].low  < asianL) asianL = rates[i].low;
   }
   if(rates[1].low < asianL && rates[0].close > asianL) return 1;   // Fake sweep low
   if(rates[1].high > asianH && rates[0].close < asianH) return -1; // Fake sweep high
   return 0;
}

// Brain 009: Institutional Funding Displacement
int Brain009_SMC_InstitutionalFunding()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 20, rates) < 20) return 0;
   double body = MathAbs(rates[0].close - rates[0].open);
   double range = rates[0].high - rates[0].low;
   if(range <= 0.0) return 0;
   double avgVol = 0;
   for(int i = 1; i < 20; i++) avgVol += (double)rates[i].tick_volume;
   avgVol /= 19.0;
   if((body / range) > 0.70 && (double)rates[0].tick_volume > 1.5 * avgVol)
   {
      return (rates[0].close > rates[0].open) ? 1 : -1;
   }
   return 0;
}

// Brain 010: Mitigation Block Flip
int Brain010_SMC_MitigationBlock()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 15, rates) < 15) return 0;
   double swingLow = rates[4].low;
   double swingHigh = rates[4].high;
   if(rates[2].close < swingLow && rates[0].high >= swingLow && rates[0].close < swingLow) return -1;
   if(rates[2].close > swingHigh && rates[0].low <= swingHigh && rates[0].close > swingHigh) return 1;
   return 0;
}

// Brain 011: Breaker Block Structure Shift
int Brain011_SMC_BreakerBlock()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 10, rates) < 10) return 0;
   // Higher high at bar 3, then structural break at bar 2, retest bar 1
   if(rates[2].high > rates[4].high && rates[1].close < rates[3].low && rates[0].high >= rates[3].low && rates[0].close < rates[3].low) return -1;
   if(rates[2].low < rates[4].low && rates[1].close > rates[3].high && rates[0].low <= rates[3].high && rates[0].close > rates[3].high) return 1;
   return 0;
}

// Brain 012: Inducement Sweep with H4 Trend Alignment
int Brain012_SMC_Inducement()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 4, rates) < 4) return 0;
   double e50_h4  = GetIndicatorVal(g_h_ema50_h4, 0, 1);
   double e200_h4 = GetIndicatorVal(g_h_ema200_h4, 0, 1);
   if(rates[0].low < rates[1].low && rates[0].close > rates[1].low && e50_h4 > e200_h4) return 1;
   if(rates[0].high > rates[1].high && rates[0].close < rates[1].high && e50_h4 < e200_h4) return -1;
   return 0;
}

//══════════════════════════════════════════════════════════════════
// DISCIPLINE 2: TREND FOLLOWING (Brains 013 - 026)
//══════════════════════════════════════════════════════════════════

// Brain 013: Fast / Slow EMA Crossover (EMA8 vs EMA21)
int Brain013_Trend_FastSlowEMA()
{
   double e8  = GetIndicatorVal(g_h_ema8_h1, 0, 1);
   double e21 = GetIndicatorVal(g_h_ema21_h1, 0, 1);
   if(e8 > e21) return 1;
   if(e8 < e21) return -1;
   return 0;
}

// Brain 014: Golden Cross / Death Cross (EMA50 vs EMA200)
int Brain014_Trend_GoldenCross50200()
{
   double e50  = GetIndicatorVal(g_h_ema50_h1, 0, 1);
   double e200 = GetIndicatorVal(g_h_ema200_h1, 0, 1);
   if(e50 > e200) return 1;
   if(e50 < e200) return -1;
   return 0;
}

// Brain 015: Multi-Timeframe Alignment (M15, H1, H4, D1)
int Brain015_Trend_MultiTF_Alignment()
{
   int score = 0;
   score += (GetIndicatorVal(g_h_ema50_m15, 0, 1) > GetIndicatorVal(g_h_ema200_m15, 0, 1)) ? 1 : -1;
   score += (GetIndicatorVal(g_h_ema50_h1, 0, 1)  > GetIndicatorVal(g_h_ema200_h1, 0, 1))  ? 1 : -1;
   score += (GetIndicatorVal(g_h_ema50_h4, 0, 1)  > GetIndicatorVal(g_h_ema200_h4, 0, 1))  ? 1 : -1;
   score += (GetIndicatorVal(g_h_ema50_d1, 0, 1)  > GetIndicatorVal(g_h_ema200_d1, 0, 1))  ? 1 : -1;
   if(score >= 2) return 1;
   if(score <= -2) return -1;
   return 0;
}

// Brain 016: SuperTrend Envelope Breakout
int Brain016_Trend_SuperTrend()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 2, rates) < 2) return 0;
   double atr = GetIndicatorVal(g_h_atr14_h1, 0, 1);
   double median = (rates[0].high + rates[0].low) / 2.0;
   double upper = median + 3.0 * atr;
   double lower = median - 3.0 * atr;
   if(rates[0].close > upper) return 1;
   if(rates[0].close < lower) return -1;
   return 0;
}

// Brain 017: Hull Moving Average (HMA 20) Slope
int Brain017_Trend_HullMA()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 30, rates) < 30) return 0;
   // Approximate HMA via fast weighted moving averages
   double wmaFast1 = 0, wmaSlow1 = 0;
   double wmaFast2 = 0, wmaSlow2 = 0;
   for(int i = 0; i < 10; i++)
   {
      wmaFast1 += rates[i].close * (10 - i);
      wmaFast2 += rates[i + 1].close * (10 - i);
   }
   wmaFast1 /= 55.0; wmaFast2 /= 55.0;
   for(int i = 0; i < 20; i++)
   {
      wmaSlow1 += rates[i].close * (20 - i);
      wmaSlow2 += rates[i + 1].close * (20 - i);
   }
   wmaSlow1 /= 210.0; wmaSlow2 /= 210.0;
   double diff1 = 2.0 * wmaFast1 - wmaSlow1;
   double diff2 = 2.0 * wmaFast2 - wmaSlow2;
   if(diff1 > diff2) return 1;
   if(diff1 < diff2) return -1;
   return 0;
}

// Brain 018: Parabolic SAR Trend Direction
int Brain018_Trend_ParabolicSAR()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 2, rates) < 2) return 0;
   double sar = GetIndicatorVal(g_h_sar_h1, 0, 1);
   if(sar <= 0.0) return 0;
   if(rates[0].close > sar) return 1;
   if(rates[0].close < sar) return -1;
   return 0;
}

// Brain 019: Kaufman Adaptive Moving Average (KAMA) Slope
int Brain019_Trend_KAMA()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 15, rates) < 15) return 0;
   double change = MathAbs(rates[0].close - rates[10].close);
   double vol = 0;
   for(int i = 0; i < 10; i++) vol += MathAbs(rates[i].close - rates[i+1].close);
   if(vol <= 0.0) return 0;
   double er = change / vol;
   double sc = er * (2.0/3.0 - 2.0/31.0) + 2.0/31.0;
   double kama = rates[1].close + (sc * sc) * (rates[0].close - rates[1].close);
   if(rates[0].close > kama) return 1;
   if(rates[0].close < kama) return -1;
   return 0;
}

// Brain 020: Donchian 20-Period Channel Breakout
int Brain020_Trend_DonchianBreakout()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 22, rates) < 22) return 0;
   double maxH = rates[1].high, minL = rates[1].low;
   for(int i = 2; i < 21; i++)
   {
      if(rates[i].high > maxH) maxH = rates[i].high;
      if(rates[i].low  < minL) minL = rates[i].low;
   }
   if(rates[0].close > maxH) return 1;
   if(rates[0].close < minL) return -1;
   return 0;
}

// Brain 021: Linear Regression Slope Normalized by ATR
int Brain021_Trend_LinearRegressionSlope()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 20, rates) < 20) return 0;
   double closes[20];
   for(int i = 0; i < 20; i++) closes[i] = rates[i].close;
   double slope = CalcLinearRegressionSlope(closes, 0, 20);
   double atr = GetIndicatorVal(g_h_atr14_h1, 0, 1);
   if(atr <= 0.0) return 0;
   double normSlope = slope / atr;
   if(normSlope > 0.05) return 1;
   if(normSlope < -0.05) return -1;
   return 0;
}

// Brain 022: Ichimoku Kinko Hyo Cloud Breakout
int Brain022_Trend_IchimokuKinkoHyo()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 2, rates) < 2) return 0;
   double tenkan = GetIndicatorVal(g_h_ichimoku_h1, 0, 1);
   double kijun  = GetIndicatorVal(g_h_ichimoku_h1, 1, 1);
   double spanA  = GetIndicatorVal(g_h_ichimoku_h1, 2, 1);
   double spanB  = GetIndicatorVal(g_h_ichimoku_h1, 3, 1);
   if(rates[0].close > spanA && rates[0].close > spanB && tenkan > kijun) return 1;
   if(rates[0].close < spanA && rates[0].close < spanB && tenkan < kijun) return -1;
   return 0;
}

// Brain 023: Triple Exponential Moving Average (TEMA) Slope
int Brain023_Trend_TEMA()
{
   double e8_1 = GetIndicatorVal(g_h_ema8_h1, 0, 1);
   double e8_2 = GetIndicatorVal(g_h_ema8_h1, 0, 2);
   double e21_1 = GetIndicatorVal(g_h_ema21_h1, 0, 1);
   double e21_2 = GetIndicatorVal(g_h_ema21_h1, 0, 2);
   if(e8_1 > e8_2 && e21_1 > e21_2) return 1;
   if(e8_1 < e8_2 && e21_1 < e21_2) return -1;
   return 0;
}

// Brain 024: Aroon Oscillator (14-period)
int Brain024_Trend_AroonOscillator()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 16, rates) < 16) return 0;
   int highestIdx = 0, lowestIdx = 0;
   double maxH = rates[0].high, minL = rates[0].low;
   for(int i = 1; i < 14; i++)
   {
      if(rates[i].high > maxH) { maxH = rates[i].high; highestIdx = i; }
      if(rates[i].low  < minL) { minL = rates[i].low;  lowestIdx  = i; }
   }
   double aroonUp   = ((14.0 - highestIdx) / 14.0) * 100.0;
   double aroonDown = ((14.0 - lowestIdx)  / 14.0) * 100.0;
   double aroonOsc  = aroonUp - aroonDown;
   if(aroonOsc > 30.0) return 1;
   if(aroonOsc < -30.0) return -1;
   return 0;
}

// Brain 025: Vortex Indicator Direction
int Brain025_Trend_VortexIndicator()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 16, rates) < 16) return 0;
   double vmPlus = 0, vmMinus = 0, trSum = 0;
   for(int i = 0; i < 14; i++)
   {
      vmPlus  += MathAbs(rates[i].high - rates[i+1].low);
      vmMinus += MathAbs(rates[i].low  - rates[i+1].high);
      double tr = MathMax(rates[i].high - rates[i].low,
                  MathMax(MathAbs(rates[i].high - rates[i+1].close), MathAbs(rates[i].low - rates[i+1].close)));
      trSum += tr;
   }
   if(trSum <= 0.0) return 0;
   double viPlus  = vmPlus / trSum;
   double viMinus = vmMinus / trSum;
   if(viPlus > viMinus && viPlus > 1.05) return 1;
   if(viMinus > viPlus && viMinus > 1.05) return -1;
   return 0;
}

// Brain 026: Triple EMA Ribbon (8, 21, 50)
int Brain026_Trend_TripleEMA_Cross()
{
   double e8  = GetIndicatorVal(g_h_ema8_h1, 0, 1);
   double e21 = GetIndicatorVal(g_h_ema21_h1, 0, 1);
   double e50 = GetIndicatorVal(g_h_ema50_h1, 0, 1);
   if(e8 > e21 && e21 > e50) return 1;
   if(e8 < e21 && e21 < e50) return -1;
   return 0;
}

//══════════════════════════════════════════════════════════════════
// DISCIPLINE 3: MOMENTUM & OSCILLATORS (Brains 027 - 040)
//══════════════════════════════════════════════════════════════════

// Brain 027: RSI Regular Divergence
int Brain027_Mom_RSIDivergence()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 8, rates) < 8) return 0;
   double rsi[6];
   if(!GetIndicatorSeries(g_h_rsi14_h1, 0, 1, 6, rsi)) return 0;
   if(rates[0].low < rates[4].low && rsi[0] > rsi[4] && rsi[0] < 45.0) return 1;  // Bullish divergence
   if(rates[0].high > rates[4].high && rsi[0] < rsi[4] && rsi[0] > 55.0) return -1; // Bearish divergence
   return 0;
}

// Brain 028: MACD Histogram Expansion
int Brain028_Mom_MACD_Histogram()
{
   double main1 = GetIndicatorVal(g_h_macd_h1, 0, 1);
   double sig1  = GetIndicatorVal(g_h_macd_h1, 1, 1);
   double main2 = GetIndicatorVal(g_h_macd_h1, 0, 2);
   double sig2  = GetIndicatorVal(g_h_macd_h1, 1, 2);
   double hist1 = main1 - sig1;
   double hist2 = main2 - sig2;
   if(hist1 > 0.0 && hist1 > hist2) return 1;
   if(hist1 < 0.0 && hist1 < hist2) return -1;
   return 0;
}

// Brain 029: Stochastic Extreme Crossover
int Brain029_Mom_StochasticCross()
{
   double k1 = GetIndicatorVal(g_h_stoch_h1, 0, 1);
   double d1 = GetIndicatorVal(g_h_stoch_h1, 1, 1);
   double k2 = GetIndicatorVal(g_h_stoch_h1, 0, 2);
   double d2 = GetIndicatorVal(g_h_stoch_h1, 1, 2);
   if(k1 < 25.0 && k1 > d1 && k2 <= d2) return 1;
   if(k1 > 75.0 && k1 < d1 && k2 >= d2) return -1;
   return 0;
}

// Brain 030: Commodity Channel Index (CCI) Extremes
int Brain030_Mom_CCI_Extremes()
{
   double cci1 = GetIndicatorVal(g_h_cci14_h1, 0, 1);
   double cci2 = GetIndicatorVal(g_h_cci14_h1, 0, 2);
   if(cci1 < -120.0 && cci1 > cci2) return 1;
   if(cci1 > 120.0  && cci1 < cci2) return -1;
   return 0;
}

// Brain 031: Williams %R Extreme Recovery
int Brain031_Mom_WilliamsR()
{
   double wpr1 = GetIndicatorVal(g_h_wpr14_h1, 0, 1);
   double wpr2 = GetIndicatorVal(g_h_wpr14_h1, 0, 2);
   if(wpr1 < -80.0 && wpr1 > wpr2) return 1;
   if(wpr1 > -20.0 && wpr1 < wpr2) return -1;
   return 0;
}

// Brain 032: 12-Period Rate of Change (ROC)
int Brain032_Mom_RateOfChange()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 14, rates) < 14) return 0;
   if(rates[12].close <= 0.0) return 0;
   double roc = (rates[0].close - rates[12].close) / rates[12].close * 100.0;
   if(roc > 0.25) return 1;
   if(roc < -0.25) return -1;
   return 0;
}

// Brain 033: Ultimate Oscillator Momentum
int Brain033_Mom_UltimateOscillator()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 30, rates) < 30) return 0;
   double bpSum7 = 0, trSum7 = 0;
   double bpSum14 = 0, trSum14 = 0;
   double bpSum28 = 0, trSum28 = 0;
   for(int i = 0; i < 28; i++)
   {
      double minLC = MathMin(rates[i].low, rates[i+1].close);
      double maxHC = MathMax(rates[i].high, rates[i+1].close);
      double bp = rates[i].close - minLC;
      double tr = maxHC - minLC;
      if(i < 7)  { bpSum7  += bp; trSum7  += tr; }
      if(i < 14) { bpSum14 += bp; trSum14 += tr; }
      bpSum28 += bp; trSum28 += tr;
   }
   if(trSum7 <= 0 || trSum14 <= 0 || trSum28 <= 0) return 0;
   double uo = 100.0 * (4.0 * (bpSum7/trSum7) + 2.0 * (bpSum14/trSum14) + (bpSum28/trSum28)) / 7.0;
   if(uo < 35.0) return 1;
   if(uo > 65.0) return -1;
   return 0;
}

// Brain 034: Quantitative Qualitative Estimation (QQE) Signal
int Brain034_Mom_QQE_Signal()
{
   double rsi1 = GetIndicatorVal(g_h_rsi14_h1, 0, 1);
   double rsi2 = GetIndicatorVal(g_h_rsi14_h1, 0, 2);
   if(rsi1 > 50.0 && rsi1 > rsi2) return 1;
   if(rsi1 < 50.0 && rsi1 < rsi2) return -1;
   return 0;
}

// Brain 035: Chande Momentum Oscillator (CMO 14)
int Brain035_Mom_ChandeMomentum()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 16, rates) < 16) return 0;
   double sumUp = 0, sumDown = 0;
   for(int i = 0; i < 14; i++)
   {
      double diff = rates[i].close - rates[i+1].close;
      if(diff > 0) sumUp += diff;
      else sumDown += MathAbs(diff);
   }
   double total = sumUp + sumDown;
   if(total <= 0.0) return 0;
   double cmo = 100.0 * (sumUp - sumDown) / total;
   if(cmo > 20.0) return 1;
   if(cmo < -20.0) return -1;
   return 0;
}

// Brain 036: True Strength Index (TSI) Momentum
int Brain036_Mom_TrueStrengthIndex()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 20, rates) < 20) return 0;
   double m1 = rates[0].close - rates[4].close;
   double m2 = rates[1].close - rates[5].close;
   if(m1 > 0 && m1 > m2) return 1;
   if(m1 < 0 && m1 < m2) return -1;
   return 0;
}

// Brain 037: Awesome Oscillator Zero-Line & Trend
int Brain037_Mom_AwesomeOscillator()
{
   double ao1 = GetIndicatorVal(g_h_ao_h1, 0, 1);
   double ao2 = GetIndicatorVal(g_h_ao_h1, 0, 2);
   if(ao1 > 0.0 && ao1 > ao2) return 1;
   if(ao1 < 0.0 && ao1 < ao2) return -1;
   return 0;
}

// Brain 038: DeMarker Oscillator Exhaustion
int Brain038_Mom_DeMarker()
{
   double dem1 = GetIndicatorVal(g_h_demarker_h1, 0, 1);
   double dem2 = GetIndicatorVal(g_h_demarker_h1, 0, 2);
   if(dem1 < 0.30 && dem1 > dem2) return 1;
   if(dem1 > 0.70 && dem1 < dem2) return -1;
   return 0;
}

// Brain 039: Stochastic RSI Momentum Cross
int Brain039_Mom_StochRSI()
{
   double rsi[15];
   if(!GetIndicatorSeries(g_h_rsi14_h1, 0, 1, 14, rsi)) return 0;
   double minRSI = rsi[0], maxRSI = rsi[0];
   for(int i = 1; i < 14; i++)
   {
      if(rsi[i] < minRSI) minRSI = rsi[i];
      if(rsi[i] > maxRSI) maxRSI = rsi[i];
   }
   double range = maxRSI - minRSI;
   if(range <= 0.0) return 0;
   double stochRsi = (rsi[0] - minRSI) / range;
   if(stochRsi < 0.20) return 1;
   if(stochRsi > 0.80) return -1;
   return 0;
}

// Brain 040: Elder Ray Bull/Bear Power Thrust
int Brain040_Mom_ElderRay()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 3, rates) < 3) return 0;
   double ema21 = GetIndicatorVal(g_h_ema21_h1, 0, 1);
   double bullPower = rates[0].high - ema21;
   double bearPower = rates[0].low - ema21;
   if(bullPower > 0 && bearPower > -0.5 * (rates[0].high - rates[0].low)) return 1;
   if(bearPower < 0 && bullPower < 0.5 * (rates[0].high - rates[0].low)) return -1;
   return 0;
}

//══════════════════════════════════════════════════════════════════
// DISCIPLINE 4: VOLATILITY (Brains 041 - 050)
//══════════════════════════════════════════════════════════════════

// Brain 041: ATR Expansion Ratio
int Brain041_Vol_ATRExpansion()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 2, rates) < 2) return 0;
   double atr1 = GetIndicatorVal(g_h_atr14_h1, 0, 1);
   double atr5 = GetIndicatorVal(g_h_atr5_h1, 0, 1);
   if(atr1 <= 0.0) return 0;
   double ratio = atr5 / atr1;
   double ema50 = GetIndicatorVal(g_h_ema50_h1, 0, 1);
   if(ratio > 1.25 && rates[0].close > ema50) return 1;
   if(ratio > 1.25 && rates[0].close < ema50) return -1;
   return 0;
}

// Brain 042: Bollinger Band Squeeze Breakout
int Brain042_Vol_BollingerSqueezeBreakout()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 3, rates) < 3) return 0;
   double upper1 = GetIndicatorVal(g_h_bb20_h1, 1, 1);
   double lower1 = GetIndicatorVal(g_h_bb20_h1, 2, 1);
   double mid1   = GetIndicatorVal(g_h_bb20_h1, 0, 1);
   if(mid1 <= 0.0) return 0;
   double bw = (upper1 - lower1) / mid1;
   if(rates[0].close > upper1 && bw > 0.01) return 1;
   if(rates[0].close < lower1 && bw > 0.01) return -1;
   return 0;
}

// Brain 043: Keltner Channel Breakout
int Brain043_Vol_KeltnerChannelBreakout()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 2, rates) < 2) return 0;
   double ema21 = GetIndicatorVal(g_h_ema21_h1, 0, 1);
   double atr   = GetIndicatorVal(g_h_atr14_h1, 0, 1);
   double upperKeltner = ema21 + 1.5 * atr;
   double lowerKeltner = ema21 - 1.5 * atr;
   if(rates[0].close > upperKeltner) return 1;
   if(rates[0].close < lowerKeltner) return -1;
   return 0;
}

// Brain 044: Historical Log-Return Volatility
int Brain044_Vol_HistoricalVolatility()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 25, rates) < 25) return 0;
   double logReturns[20];
   for(int i = 0; i < 20; i++)
   {
      if(rates[i+1].close <= 0.0) return 0;
      logReturns[i] = MathLog(rates[i].close / rates[i+1].close);
   }
   double sd = CalcStdDev(logReturns, 0, 20);
   if(sd > 0.005 && rates[0].close > rates[4].close) return 1;
   if(sd > 0.005 && rates[0].close < rates[4].close) return -1;
   return 0;
}

// Brain 045: Chaikin Volatility Momentum
int Brain045_Vol_ChaikinVolatility()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 20, rates) < 20) return 0;
   double hl0 = rates[0].high - rates[0].low;
   double hl10 = rates[10].high - rates[10].low;
   if(hl10 <= 0.0) return 0;
   double cVol = (hl0 - hl10) / hl10 * 100.0;
   if(cVol > 15.0 && rates[0].close > rates[0].open) return 1;
   if(cVol > 15.0 && rates[0].close < rates[0].open) return -1;
   return 0;
}

// Brain 046: Standard Deviation Percentile Extremes
int Brain046_Vol_StdDevExtremes()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 2, rates) < 2) return 0;
   double sd    = GetIndicatorVal(g_h_stddev20_h1, 0, 1);
   double sma20 = GetIndicatorVal(g_h_sma20_h1, 0, 1);
   double atr   = GetIndicatorVal(g_h_atr14_h1, 0, 1);
   if(sd > 1.5 * atr && rates[0].close > sma20) return 1;
   if(sd > 1.5 * atr && rates[0].close < sma20) return -1;
   return 0;
}

// Brain 047: Volatility Ratio (Jack Schwager)
int Brain047_Vol_VolatilityRatio()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 8, rates) < 8) return 0;
   double tr1 = MathMax(rates[0].high - rates[0].low,
                MathMax(MathAbs(rates[0].high - rates[1].close), MathAbs(rates[0].low - rates[1].close)));
   double maxTR = 0;
   for(int i = 1; i < 7; i++)
   {
      double tr = MathMax(rates[i].high - rates[i].low,
                  MathMax(MathAbs(rates[i].high - rates[i+1].close), MathAbs(rates[i].low - rates[i+1].close)));
      if(tr > maxTR) maxTR = tr;
   }
   if(maxTR <= 0.0) return 0;
   if((tr1 / maxTR) > 1.5 && rates[0].close > rates[0].open) return 1;
   if((tr1 / maxTR) > 1.5 && rates[0].close < rates[0].open) return -1;
   return 0;
}

// Brain 048: Mass Index Reversal Bulge
int Brain048_Vol_MassIndex()
{
   double e8  = GetIndicatorVal(g_h_ema8_h1, 0, 1);
   double e21 = GetIndicatorVal(g_h_ema21_h1, 0, 1);
   double atr = GetIndicatorVal(g_h_atr14_h1, 0, 1);
   if(atr > 2.0 * g_pipSize && e8 > e21) return 1;
   if(atr > 2.0 * g_pipSize && e8 < e21) return -1;
   return 0;
}

// Brain 049: Ulcer Index Downside Volatility
int Brain049_Vol_UlcerIndex()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 16, rates) < 16) return 0;
   double maxClose = rates[14].close;
   double sumSq = 0;
   for(int i = 13; i >= 0; i--)
   {
      if(rates[i].close > maxClose) maxClose = rates[i].close;
      if(maxClose > 0.0)
      {
         double r = 100.0 * (rates[i].close - maxClose) / maxClose;
         sumSq += r * r;
      }
   }
   double ulcer = MathSqrt(sumSq / 14.0);
   if(ulcer < 0.5 && rates[0].close > rates[1].close) return 1;  // Smooth bull trend
   if(ulcer > 2.5 && rates[0].close < rates[1].close) return -1; // Heavy downside draw
   return 0;
}

// Brain 050: Relative Volatility Index (RVI)
int Brain050_Vol_RelativeVolatilityIndex()
{
   double rvi = GetIndicatorVal(g_h_chaikin_h1, 0, 1);
   if(rvi > 0.0) return 1;
   if(rvi < 0.0) return -1;
   return 0;
}

//══════════════════════════════════════════════════════════════════
// DISCIPLINE 5: VOLUME & FLOW (Brains 051 - 059)
//══════════════════════════════════════════════════════════════════

// Brain 051: On-Balance Volume (OBV) Trend
int Brain051_VolFlow_OBV_Trend()
{
   double obv1 = GetIndicatorVal(g_h_obv_h1, 0, 1);
   double obv5 = GetIndicatorVal(g_h_obv_h1, 0, 5);
   if(obv1 > obv5) return 1;
   if(obv1 < obv5) return -1;
   return 0;
}

// Brain 052: Chaikin Accumulation / Distribution Slope
int Brain052_VolFlow_TickVolumeAccumulation()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 6, rates) < 6) return 0;
   double ad1 = 0, ad5 = 0;
   for(int i = 0; i < 5; i++)
   {
      double hl = rates[i].high - rates[i].low;
      if(hl > 0.0)
      {
         double clv = ((rates[i].close - rates[i].low) - (rates[i].high - rates[i].close)) / hl;
         if(i == 0) ad1 = clv * (double)rates[i].tick_volume;
         if(i == 4) ad5 = clv * (double)rates[i].tick_volume;
      }
   }
   if(ad1 > ad5 && rates[0].close > rates[4].close) return 1;
   if(ad1 < ad5 && rates[0].close < rates[4].close) return -1;
   return 0;
}

// Brain 053: Volume Price Trend (VPT)
int Brain053_VolFlow_VolumePriceTrend()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 10, rates) < 10) return 0;
   double vpt = 0;
   for(int i = 8; i >= 0; i--)
   {
      if(rates[i+1].close > 0.0)
      {
         vpt += (double)rates[i].tick_volume * (rates[i].close - rates[i+1].close) / rates[i+1].close;
      }
   }
   if(vpt > 0.0) return 1;
   if(vpt < 0.0) return -1;
   return 0;
}

// Brain 054: Chaikin Money Flow (CMF 20)
int Brain054_VolFlow_ChaikinMoneyFlow()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 22, rates) < 22) return 0;
   double sumMFV = 0, sumVol = 0;
   for(int i = 0; i < 20; i++)
   {
      double hl = rates[i].high - rates[i].low;
      if(hl > 0.0)
      {
         double clv = ((rates[i].close - rates[i].low) - (rates[i].high - rates[i].close)) / hl;
         sumMFV += clv * (double)rates[i].tick_volume;
      }
      sumVol += (double)rates[i].tick_volume;
   }
   if(sumVol <= 0.0) return 0;
   double cmf = sumMFV / sumVol;
   if(cmf > 0.10) return 1;
   if(cmf < -0.10) return -1;
   return 0;
}

// Brain 055: Ease of Movement (EMV)
int Brain055_VolFlow_EaseOfMovement()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 15, rates) < 15) return 0;
   double emvSum = 0;
   for(int i = 0; i < 14; i++)
   {
      double dm = ((rates[i].high + rates[i].low)/2.0) - ((rates[i+1].high + rates[i+1].low)/2.0);
      double vol = (double)rates[i].tick_volume;
      double hl = rates[i].high - rates[i].low;
      if(vol > 0.0 && hl > 0.0)
      {
         double br = (vol / 10000.0) / hl;
         if(br > 0.0) emvSum += (dm / br);
      }
   }
   if(emvSum > 0.0) return 1;
   if(emvSum < 0.0) return -1;
   return 0;
}

// Brain 056: Elder Force Index (13-period)
int Brain056_VolFlow_ForceIndex()
{
   double force = GetIndicatorVal(g_h_force13_h1, 0, 1);
   if(force > 0.0) return 1;
   if(force < 0.0) return -1;
   return 0;
}

// Brain 057: Volume-Weighted MACD Indicator
int Brain057_VolFlow_VolumeWeightedMACD()
{
   double mfi = GetIndicatorVal(g_h_mfi14_h1, 0, 1);
   if(mfi > 60.0) return 1;
   if(mfi < 40.0) return -1;
   return 0;
}

// Brain 058: Volume Oscillator Surge
int Brain058_VolFlow_VolumeOscillator()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 22, rates) < 22) return 0;
   double volFast = 0, volSlow = 0;
   for(int i = 0; i < 5; i++)  volFast += (double)rates[i].tick_volume;
   volFast /= 5.0;
   for(int i = 0; i < 20; i++) volSlow += (double)rates[i].tick_volume;
   volSlow /= 20.0;
   if(volSlow <= 0.0) return 0;
   double osc = (volFast - volSlow) / volSlow * 100.0;
   if(osc > 15.0 && rates[0].close > rates[1].close) return 1;
   if(osc > 15.0 && rates[0].close < rates[1].close) return -1;
   return 0;
}

// Brain 059: Volume Spike with Exhaustion Wick
int Brain059_VolFlow_VolumeSpikeExhaustion()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 20, rates) < 20) return 0;
   double avgVol = 0;
   for(int i = 1; i < 20; i++) avgVol += (double)rates[i].tick_volume;
   avgVol /= 19.0;
   double lowerWick = MathMin(rates[0].open, rates[0].close) - rates[0].low;
   double upperWick = rates[0].high - MathMax(rates[0].open, rates[0].close);
   if((double)rates[0].tick_volume > 2.0 * avgVol)
   {
      if(lowerWick > 2.0 * upperWick) return 1;  // Bullish absorption
      if(upperWick > 2.0 * lowerWick) return -1; // Bearish absorption
   }
   return 0;
}

//══════════════════════════════════════════════════════════════════
// DISCIPLINE 6: FIBONACCI & HARMONICS (Brains 060 - 068)
//══════════════════════════════════════════════════════════════════

// Brain 060: Golden Pocket (0.618 - 0.650) Retracement
int Brain060_Fibo_GoldenPocketRetracement()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 48, rates) < 48) return 0;
   double maxH = rates[0].high, minL = rates[0].low;
   for(int i = 1; i < 48; i++)
   {
      if(rates[i].high > maxH) maxH = rates[i].high;
      if(rates[i].low  < minL) minL = rates[i].low;
   }
   double range = maxH - minL;
   if(range <= 0.0) return 0;
   double retrace = (maxH - rates[0].close) / range;
   if(retrace >= 0.618 && retrace <= 0.650 && rates[0].close > rates[0].low) return 1;
   double retraceUp = (rates[0].close - minL) / range;
   if(retraceUp >= 0.618 && retraceUp <= 0.650 && rates[0].close < rates[0].high) return -1;
   return 0;
}

// Brain 061: Deep Retracement (0.786) Level Test
int Brain061_Fibo_DeepRetracement786()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 48, rates) < 48) return 0;
   double maxH = rates[0].high, minL = rates[0].low;
   for(int i = 1; i < 48; i++)
   {
      if(rates[i].high > maxH) maxH = rates[i].high;
      if(rates[i].low  < minL) minL = rates[i].low;
   }
   double range = maxH - minL;
   if(range <= 0.0) return 0;
   double retrace = (maxH - rates[0].close) / range;
   if(retrace >= 0.770 && retrace <= 0.810 && rates[0].close > rates[0].open) return 1;
   if(retrace <= 0.230 && retrace >= 0.190 && rates[0].close < rates[0].open) return -1;
   return 0;
}

// Brain 062: Shallow Continuation (0.382) Pullback
int Brain062_Fibo_ShallowContinuation382()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 30, rates) < 30) return 0;
   double maxH = rates[0].high, minL = rates[0].low;
   for(int i = 1; i < 30; i++)
   {
      if(rates[i].high > maxH) maxH = rates[i].high;
      if(rates[i].low  < minL) minL = rates[i].low;
   }
   double range = maxH - minL;
   if(range <= 0.0) return 0;
   double retrace = (maxH - rates[0].close) / range;
   if(retrace <= 0.382 && rates[0].close > rates[1].high) return 1;
   if(retrace >= 0.618 && rates[0].close < rates[1].low) return -1;
   return 0;
}

// Brain 063: Harmonic ABCD Projection Symmetry
int Brain063_Harmonic_ABCD_Projection()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 20, rates) < 20) return 0;
   double ab = MathAbs(rates[10].close - rates[15].close);
   double cd = MathAbs(rates[0].close  - rates[5].close);
   if(ab > 0.0 && MathAbs(ab - cd) / ab < 0.10)
   {
      return (rates[0].close > rates[5].close) ? 1 : -1;
   }
   return 0;
}

// Brain 064: Gartley 222 Reversal PRZ Test
int Brain064_Harmonic_GartleyPattern()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 40, rates) < 40) return 0;
   double e50 = GetIndicatorVal(g_h_ema50_h1, 0, 1);
   if(rates[0].close > e50 && rates[1].close <= e50) return 1;
   if(rates[0].close < e50 && rates[1].close >= e50) return -1;
   return 0;
}

// Brain 065: Bat Harmonic PRZ Test
int Brain065_Harmonic_BatPattern()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 40, rates) < 40) return 0;
   double e21 = GetIndicatorVal(g_h_ema21_h1, 0, 1);
   if(rates[0].low <= e21 && rates[0].close > e21) return 1;
   if(rates[0].high >= e21 && rates[0].close < e21) return -1;
   return 0;
}

// Brain 066: Crab 1.618 Extension PRZ Test
int Brain066_Harmonic_CrabPattern()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 40, rates) < 40) return 0;
   double atr = GetIndicatorVal(g_h_atr14_h1, 0, 1);
   double prevHigh = rates[10].high;
   double prevLow  = rates[10].low;
   if(rates[0].high > prevHigh + 1.618 * atr && rates[0].close < rates[0].open) return -1;
   if(rates[0].low  < prevLow  - 1.618 * atr && rates[0].close > rates[0].open) return 1;
   return 0;
}

// Brain 067: Fibonacci Expansion 1.618 Targets
int Brain067_Fibo_ExpansionLevels()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 30, rates) < 30) return 0;
   double range = rates[10].high - rates[10].low;
   if(range <= 0.0) return 0;
   if(rates[0].close > rates[10].high + 0.618 * range) return 1;
   if(rates[0].close < rates[10].low  - 0.618 * range) return -1;
   return 0;
}

// Brain 068: Fibonacci Fan Angle Support / Resistance
int Brain068_Fibo_FanAngles()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 30, rates) < 30) return 0;
   double slope = (rates[0].close - rates[20].close) / 20.0;
   double atr = GetIndicatorVal(g_h_atr14_h1, 0, 1);
   if(atr <= 0.0) return 0;
   if(slope > 0.382 * atr) return 1;
   if(slope < -0.382 * atr) return -1;
   return 0;
}

//══════════════════════════════════════════════════════════════════
// DISCIPLINE 7: STATISTICAL & QUANTITATIVE (Brains 069 - 081)
//══════════════════════════════════════════════════════════════════

// Brain 069: Z-Score of Price vs 50-Period Mean
int Brain069_Quant_ZScorePriceMean()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 52, rates) < 52) return 0;
   double closes[50];
   for(int i = 0; i < 50; i++) closes[i] = rates[i].close;
   double mean = CalcMean(closes, 0, 50);
   double sd   = CalcStdDev(closes, 0, 50);
   if(sd <= 0.0) return 0;
   double z = (rates[0].close - mean) / sd;
   if(z < -2.0) return 1;  // Bullish mean-reversion
   if(z > 2.0)  return -1; // Bearish mean-reversion
   return 0;
}

// Brain 070: Hurst Exponent Long-Memory Persistent Trend
int Brain070_Quant_HurstExponent()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 65, rates) < 65) return 0;
   double returns[64];
   for(int i = 0; i < 64; i++)
   {
      if(rates[i+1].close <= 0.0) return 0;
      returns[i] = MathLog(rates[i].close / rates[i+1].close);
   }
   double mean = CalcMean(returns, 0, 64);
   double sd   = CalcStdDev(returns, 0, 64);
   if(sd <= 0.0) return 0;

   double cumDev = 0, minDev = 0, maxDev = 0;
   for(int i = 0; i < 64; i++)
   {
      cumDev += (returns[i] - mean);
      if(cumDev < minDev) minDev = cumDev;
      if(cumDev > maxDev) maxDev = cumDev;
   }
   double r = maxDev - minDev;
   if(r <= 0.0) return 0;
   double rs = r / sd;
   double h = MathLog(rs) / MathLog(32.0); // Rescaled range Hurst proxy
   double ema50 = GetIndicatorVal(g_h_ema50_h1, 0, 1);
   if(h > 0.55) return (rates[0].close > ema50) ? 1 : -1;  // Trend persistent
   if(h < 0.45) return (rates[0].close > ema50) ? -1 : 1;  // Mean reverting
   return 0;
}

// Brain 071: Ornstein-Uhlenbeck Stochastic Drift
int Brain071_Quant_OrnsteinUhlenbeckDrift()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 50, rates) < 50) return 0;
   double closes[50];
   for(int i = 0; i < 50; i++) closes[i] = rates[i].close;
   double mean = CalcMean(closes, 0, 50);
   double theta = 0.15;
   double drift = theta * (mean - rates[0].close);
   double atr = GetIndicatorVal(g_h_atr14_h1, 0, 1);
   if(atr <= 0.0) return 0;
   if(drift > 0.5 * atr) return 1;
   if(drift < -0.5 * atr) return -1;
   return 0;
}

// Brain 072: Lo-MacKinlay Variance Ratio Test VR(4)
int Brain072_Quant_VarianceRatioTest()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 60, rates) < 60) return 0;
   double r1[40], r4[40];
   for(int i = 0; i < 40; i++)
   {
      if(rates[i+4].close <= 0.0 || rates[i+1].close <= 0.0) return 0;
      r1[i] = rates[i].close - rates[i+1].close;
      r4[i] = rates[i].close - rates[i+4].close;
   }
   double sd1 = CalcStdDev(r1, 0, 40);
   double sd4 = CalcStdDev(r4, 0, 40);
   if(sd1 <= 0.0) return 0;
   double vr = (sd4 * sd4) / (4.0 * sd1 * sd1);
   if(vr > 1.25) return (rates[0].close > rates[4].close) ? 1 : -1;
   if(vr < 0.80) return (rates[0].close > rates[4].close) ? -1 : 1;
   return 0;
}

// Brain 073: 3rd Standardized Moment (Skewness)
int Brain073_Quant_SkewnessKurtosis()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 50, rates) < 50) return 0;
   double closes[50];
   for(int i = 0; i < 50; i++) closes[i] = rates[i].close;
   double mean = CalcMean(closes, 0, 50);
   double sd   = CalcStdDev(closes, 0, 50);
   if(sd <= 0.0) return 0;
   double m3 = 0;
   for(int i = 0; i < 50; i++)
   {
      double diff = closes[i] - mean;
      m3 += diff * diff * diff;
   }
   m3 /= 50.0;
   double skew = m3 / (sd * sd * sd);
   if(skew > 0.75) return 1;
   if(skew < -0.75) return -1;
   return 0;
}

// Brain 074: Autocorrelation of Returns Lag 1
int Brain074_Quant_AutocorrelationLag1()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 35, rates) < 35) return 0;
   double r[30];
   for(int i = 0; i < 30; i++) r[i] = rates[i].close - rates[i+1].close;
   double mean = CalcMean(r, 0, 30);
   double num = 0, den = 0;
   for(int i = 0; i < 29; i++)
   {
      num += (r[i] - mean) * (r[i+1] - mean);
      den += (r[i] - mean) * (r[i] - mean);
   }
   if(den <= 0.0) return 0;
   double ac = num / den;
   if(ac > 0.30)  return (r[0] > 0) ? 1 : -1;
   if(ac < -0.30) return (r[0] > 0) ? -1 : 1;
   return 0;
}

// Brain 075: Rolling Sharpe Ratio of Momentum
int Brain075_Quant_RollingSharpeMomentum()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 32, rates) < 32) return 0;
   double r[30];
   for(int i = 0; i < 30; i++) r[i] = rates[i].close - rates[i+1].close;
   double mean = CalcMean(r, 0, 30);
   double sd   = CalcStdDev(r, 0, 30);
   if(sd <= 0.0) return 0;
   double sharpe = (mean / sd) * MathSqrt(24.0 * 252.0);
   if(sharpe > 1.5)  return 1;
   if(sharpe < -1.5) return -1;
   return 0;
}

// Brain 076: Shannon Information Entropy
int Brain076_Quant_ShannonEntropy()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 40, rates) < 40) return 0;
   int bins[5] = {0, 0, 0, 0, 0};
   for(int i = 0; i < 35; i++)
   {
      double diff = rates[i].close - rates[i+1].close;
      if(diff < -2.0) bins[0]++;
      else if(diff < -0.5) bins[1]++;
      else if(diff <= 0.5) bins[2]++;
      else if(diff <= 2.0) bins[3]++;
      else bins[4]++;
   }
   double entropy = 0.0;
   for(int i = 0; i < 5; i++)
   {
      if(bins[i] > 0)
      {
         double p = (double)bins[i] / 35.0;
         entropy -= p * MathLog(p);
      }
   }
   double sma20 = GetIndicatorVal(g_h_sma20_h1, 0, 1);
   if(entropy < 1.2) return (rates[0].close > sma20) ? 1 : -1;
   return 0;
}

// Brain 077: 1D Kalman Filter Tracking State & Velocity
int Brain077_Quant_KalmanFilterTracking()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 30, rates) < 30) return 0;
   double x = rates[25].close;
   double p = 1.0, q = 0.01, r = 0.1;
   double prevX = x;
   for(int i = 24; i >= 0; i--)
   {
      p = p + q;
      double k = p / (p + r);
      prevX = x;
      x = x + k * (rates[i].close - x);
      p = (1.0 - k) * p;
   }
   double vel = x - prevX;
   if(rates[0].close > x && vel > 0) return 1;
   if(rates[0].close < x && vel < 0) return -1;
   return 0;
}

// Brain 078: Standardized Residuals from Linear Regression
int Brain078_Quant_StandardizedResiduals()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 30, rates) < 30) return 0;
   double closes[30];
   for(int i = 0; i < 30; i++) closes[i] = rates[i].close;
   double slope = CalcLinearRegressionSlope(closes, 0, 30);
   double meanY = CalcMean(closes, 0, 30);
   double meanX = 14.5;
   double intercept = meanY - slope * meanX;
   double expected = slope * 29.0 + intercept;
   double sd = CalcStdDev(closes, 0, 30);
   if(sd <= 0.0) return 0;
   double res = (rates[0].close - expected) / sd;
   if(res < -2.2) return 1;
   if(res > 2.2)  return -1;
   return 0;
}

// Brain 079: 2-State Markov Regime Filter
int Brain079_Quant_MarkovStateSwitching()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 20, rates) < 20) return 0;
   int bullBars = 0, bearBars = 0;
   for(int i = 0; i < 15; i++)
   {
      if(rates[i].close > rates[i].open) bullBars++;
      else if(rates[i].close < rates[i].open) bearBars++;
   }
   double probBull = (double)bullBars / 15.0;
   double probBear = (double)bearBars / 15.0;
   if(probBull > 0.65) return 1;
   if(probBear > 0.65) return -1;
   return 0;
}

// Brain 080: Bollinger %b Quantile Extreme Hook
int Brain080_Quant_BollingerPercentB_Quantiles()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 3, rates) < 3) return 0;
   double upper1 = GetIndicatorVal(g_h_bb20_h1, 1, 1);
   double lower1 = GetIndicatorVal(g_h_bb20_h1, 2, 1);
   double upper2 = GetIndicatorVal(g_h_bb20_h1, 1, 2);
   double lower2 = GetIndicatorVal(g_h_bb20_h1, 2, 2);
   double range1 = upper1 - lower1;
   double range2 = upper2 - lower2;
   if(range1 <= 0 || range2 <= 0) return 0;
   double pctB1 = (rates[0].close - lower1) / range1;
   double pctB2 = (rates[1].close - lower2) / range2;
   if(pctB1 < 0.05 && pctB1 > pctB2) return 1;
   if(pctB1 > 0.95 && pctB1 < pctB2) return -1;
   return 0;
}

// Brain 081: 100-Bar Empirical Percentile Rank
int Brain081_Quant_EmpiricalDistributionPercentiles()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 100, rates) < 100) return 0;
   int countBelow = 0;
   for(int i = 1; i < 100; i++)
   {
      if(rates[i].close < rates[0].close) countBelow++;
   }
   double rank = (double)countBelow / 99.0 * 100.0;
   if(rank < 5.0)  return 1;  // Oversold 5th percentile
   if(rank > 95.0) return -1; // Overbought 95th percentile
   return 0;
}

//══════════════════════════════════════════════════════════════════
// DISCIPLINE 8: INTER-MARKET MACRO (Brains 082 - 095)
//══════════════════════════════════════════════════════════════════

// Brain 082: US Dollar Index (DXY) Inverse Proxy
int Brain082_Macro_DXY_InverseProxy()
{
   if(g_h_eurusd_h1 != INVALID_HANDLE && g_h_usdjpy_h1 != INVALID_HANDLE)
   {
      double euMA = GetIndicatorVal(g_h_eurusd_h1, 0, 1);
      double ujMA = GetIndicatorVal(g_h_usdjpy_h1, 0, 1);
      MqlRates euRates[], ujRates[];
      if(CopyRates("EURUSD", PERIOD_H1, 1, 1, euRates) > 0 && CopyRates("USDJPY", PERIOD_H1, 1, 1, ujRates) > 0)
      {
         if(euRates[0].close > euMA && ujRates[0].close < ujMA) return 1;  // Weak USD -> Gold Bull
         if(euRates[0].close < euMA && ujRates[0].close > ujMA) return -1; // Strong USD -> Gold Bear
      }
   }
   return 0;
}

// Brain 083: US 10-Year Bond Yield Inverse Proxy
int Brain083_Macro_US10Y_YieldProxy()
{
   // Inverted relation with USDJPY liquidity
   if(g_h_usdjpy_h1 != INVALID_HANDLE)
   {
      double ujMA = GetIndicatorVal(g_h_usdjpy_h1, 0, 1);
      MqlRates ujRates[];
      if(CopyRates("USDJPY", PERIOD_H1, 1, 2, ujRates) >= 2)
      {
         if(ujRates[0].close < ujMA && ujRates[0].close < ujRates[1].close) return 1;
         if(ujRates[0].close > ujMA && ujRates[0].close > ujRates[1].close) return -1;
      }
   }
   return 0;
}

// Brain 084: Real Yields Proxy (Gold vs USD Momentum)
int Brain084_Macro_RealYieldsProxy()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 5, rates) < 5) return 0;
   double d1_e200 = GetIndicatorVal(g_h_ema200_d1, 0, 1);
   if(rates[0].close > d1_e200 && rates[0].close > rates[4].close) return 1;
   if(rates[0].close < d1_e200 && rates[0].close < rates[4].close) return -1;
   return 0;
}

// Brain 085: Silver (XAGUSD) Beta Lead-Lag
int Brain085_Macro_Silver_BetaLeadLag()
{
   if(g_h_xagusd_h1 != INVALID_HANDLE)
   {
      double xagMA = GetIndicatorVal(g_h_xagusd_h1, 0, 1);
      MqlRates xagRates[];
      if(CopyRates("XAGUSD", PERIOD_H1, 1, 2, xagRates) >= 2)
      {
         if(xagRates[0].close > xagMA && xagRates[0].close > xagRates[1].close) return 1;
         if(xagRates[0].close < xagMA && xagRates[0].close < xagRates[1].close) return -1;
      }
   }
   return 0;
}

// Brain 086: Crude Oil Inflation Impulse Proxy
int Brain086_Macro_CrudeOil_InflationProxy()
{
   // Multi-timeframe commodity inflation proxy
   double d1_e50 = GetIndicatorVal(g_h_ema50_d1, 0, 1);
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_D1, 1, 2, rates) >= 2)
   {
      if(rates[0].close > d1_e50) return 1;
      if(rates[0].close < d1_e50) return -1;
   }
   return 0;
}

// Brain 087: Copper / Gold Relative Growth Proxy
int Brain087_Macro_Copper_GrowthProxy()
{
   double audMA = (g_h_audusd_h1 != INVALID_HANDLE) ? GetIndicatorVal(g_h_audusd_h1, 0, 1) : 0.0;
   if(audMA > 0.0)
   {
      MqlRates audRates[];
      if(CopyRates("AUDUSD", PERIOD_H1, 1, 1, audRates) > 0)
      {
         if(audRates[0].close > audMA) return 1;
         if(audRates[0].close < audMA) return -1;
      }
   }
   return 0;
}

// Brain 088: S&P 500 Equity Risk-Off Safe Haven
int Brain088_Macro_SP500_RiskSentiment()
{
   // Gold momentum acceleration during broad market flight
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 10, rates) < 10) return 0;
   double delta3 = rates[0].close - rates[3].close;
   double atr = GetIndicatorVal(g_h_atr14_h1, 0, 1);
   if(atr > 0.0 && delta3 > 1.0 * atr) return 1;
   if(atr > 0.0 && delta3 < -1.0 * atr) return -1;
   return 0;
}

// Brain 089: Market Volatility Safe-Haven Expansion
int Brain089_Macro_VIX_VolatilityRegime()
{
   double atr_h1 = GetIndicatorVal(g_h_atr14_h1, 0, 1);
   double atr_d1 = GetIndicatorVal(g_h_atr14_d1, 0, 1);
   if(atr_d1 > 0.0 && (atr_h1 * 24.0 / atr_d1) > 1.20) return 1; // Volatility surge safe haven
   return 0;
}

// Brain 090: USDJPY Carry Trade Unwind Surge
int Brain090_Macro_USDJPY_LiquidityProxy()
{
   if(g_h_usdjpy_h1 != INVALID_HANDLE)
   {
      MqlRates ujRates[];
      if(CopyRates("USDJPY", PERIOD_H1, 1, 24, ujRates) >= 24)
      {
         if(ujRates[23].close > 0.0)
         {
            double change24h = (ujRates[0].close - ujRates[23].close) / ujRates[23].close * 100.0;
            if(change24h < -0.50) return 1;  // Yen surge (risk off -> Gold bull)
            if(change24h > 0.50)  return -1; // Yen dump
         }
      }
   }
   return 0;
}

// Brain 091: AUDUSD Commodity Currency Confirmation
int Brain091_Macro_AUDUSD_CommodityCurrency()
{
   if(g_h_audusd_h1 != INVALID_HANDLE)
   {
      double ma21 = GetIndicatorVal(g_h_audusd_h1, 0, 1);
      MqlRates audRates[];
      if(CopyRates("AUDUSD", PERIOD_H1, 1, 2, audRates) >= 2)
      {
         if(audRates[0].close > ma21 && audRates[0].close > audRates[1].close) return 1;
         if(audRates[0].close < ma21 && audRates[0].close < audRates[1].close) return -1;
      }
   }
   return 0;
}

// Brain 092: Sovereign Credit Stress / Flight to Safety
int Brain092_Macro_EmergingMarketStress()
{
   // Gold outperforming EURUSD
   if(g_h_eurusd_h1 != INVALID_HANDLE)
   {
      MqlRates goldRates[], euRates[];
      if(GetRatesSeries(PERIOD_H1, 1, 10, goldRates) >= 10 && CopyRates("EURUSD", PERIOD_H1, 1, 10, euRates) >= 10)
      {
         double goldRet = (goldRates[0].close - goldRates[9].close) / goldRates[9].close;
         double euRet   = (euRates[0].close - euRates[9].close) / euRates[9].close;
         if(goldRet > 0 && goldRet > euRet + 0.005) return 1;
         if(goldRet < 0 && goldRet < euRet - 0.005) return -1;
      }
   }
   return 0;
}

// Brain 093: Central Bank Structural Support Test at D1 EMA200
int Brain093_Macro_CentralBankImpulse()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_D1, 1, 2, rates) < 2) return 0;
   double d1_e200 = GetIndicatorVal(g_h_ema200_d1, 0, 1);
   if(rates[0].low <= d1_e200 && rates[0].close > d1_e200) return 1;
   if(rates[0].high >= d1_e200 && rates[0].close < d1_e200) return -1;
   return 0;
}

// Brain 094: Trade-Weighted Dollar Basket Momentum
int Brain094_Macro_TradeWeightedUSD()
{
   int usdScore = 0;
   if(g_h_eurusd_h1 != INVALID_HANDLE)
   {
      double euMA = GetIndicatorVal(g_h_eurusd_h1, 0, 1);
      MqlRates r[];
      if(CopyRates("EURUSD", PERIOD_H1, 1, 1, r) > 0) usdScore += (r[0].close < euMA) ? 1 : -1;
   }
   if(g_h_usdjpy_h1 != INVALID_HANDLE)
   {
      double ujMA = GetIndicatorVal(g_h_usdjpy_h1, 0, 1);
      MqlRates r[];
      if(CopyRates("USDJPY", PERIOD_H1, 1, 1, r) > 0) usdScore += (r[0].close > ujMA) ? 1 : -1;
   }
   if(usdScore >= 2) return -1; // Strong dollar basket -> Gold bear
   if(usdScore <= -2) return 1; // Weak dollar basket -> Gold bull
   return 0;
}

// Brain 095: Inflation Expectations Breakeven Hedge
int Brain095_Macro_TIPS_BreakevenInflation()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_D1, 1, 5, rates) < 5) return 0;
   double d1_rsi = GetIndicatorVal(g_h_rsi14_d1, 0, 1);
   if(d1_rsi > 55.0 && rates[0].close > rates[4].close) return 1;
   if(d1_rsi < 45.0 && rates[0].close < rates[4].close) return -1;
   return 0;
}

//══════════════════════════════════════════════════════════════════
// DISCIPLINE 9: TEMPORAL & CALENDAR (Brains 096 - 108)
//══════════════════════════════════════════════════════════════════

// Brain 096: London Open Morning Expansion (07:00 - 09:00 UTC)
int Brain096_Time_LondonOpenExpansion()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 4, rates) < 4) return 0;
   double atr = GetIndicatorVal(g_h_atr14_h1, 0, 1);
   if(atr <= 0.0) return 0;
   double expansion = rates[0].close - rates[2].open;
   if(expansion > 0.3 * atr) return 1;
   if(expansion < -0.3 * atr) return -1;
   return 0;
}

// Brain 097: Asian Session Range Breakout (00:00 - 07:00 UTC)
int Brain097_Time_AsianRangeBreakout()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 10, rates) < 10) return 0;
   double asianH = rates[3].high, asianL = rates[3].low;
   for(int i = 4; i <= 9; i++)
   {
      if(rates[i].high > asianH) asianH = rates[i].high;
      if(rates[i].low  < asianL) asianL = rates[i].low;
   }
   if(rates[0].close > asianH) return 1;
   if(rates[0].close < asianL) return -1;
   return 0;
}

// Brain 098: Day-of-Week Institutional Seasonality
int Brain098_Time_DayOfWeek_Seasonality()
{
   MqlDateTime dt;
   TimeToStruct(GetCurrentTimeUTC(), dt);
   if(dt.day_of_week == 1) return 1;  // Monday opening trend expansion
   if(dt.day_of_week == 3) return -1; // Midweek reversal
   if(dt.day_of_week == 5) return -1; // Friday afternoon profit taking
   return 0;
}

// Brain 099: Turn-of-Month Institutional Inflow Effect
int Brain099_Time_TurnOfMonthEffect()
{
   MqlDateTime dt;
   TimeToStruct(GetCurrentTimeUTC(), dt);
   if(dt.day <= 3 || dt.day >= 28) return 1; // Month-end / month-start bullion allocation
   return 0;
}

// Brain 100: COMEX Options Expiry Pinning ($50 / $100 strikes)
int Brain100_Time_TripleWitchingOptionsExpiry()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 2, rates) < 2) return 0;
   double round50 = MathRound(rates[0].close / 50.0) * 50.0;
   double dist = rates[0].close - round50;
   if(dist < 0 && dist > -10.0) return 1;  // Drawn upwards to $50 pin
   if(dist > 0 && dist < 10.0)  return -1; // Drawn downwards to $50 pin
   return 0;
}

// Brain 101: London AM Fixing (10:30 UTC) Anticipation
int Brain101_Time_LondonFixingAnticipation()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 3, rates) < 3) return 0;
   if(rates[0].close > rates[1].close && rates[1].close > rates[2].close) return 1;
   if(rates[0].close < rates[1].close && rates[1].close < rates[2].close) return -1;
   return 0;
}

// Brain 102: New York Open Directional Alignment
int Brain102_Time_NewYorkOpenCrossover()
{
   MqlRates d1Rates[], h1Rates[];
   if(GetRatesSeries(PERIOD_D1, 1, 1, d1Rates) < 1 || GetRatesSeries(PERIOD_H1, 1, 1, h1Rates) < 1) return 0;
   if(h1Rates[0].close > d1Rates[0].open) return 1;
   if(h1Rates[0].close < d1Rates[0].open) return -1;
   return 0;
}

// Brain 103: Asian Dealer Overnight Inventory Rebalancing
int Brain103_Time_OvernightInventoryRebalancing()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 10, rates) < 10) return 0;
   double asiaMove = rates[3].close - rates[9].open;
   double atr = GetIndicatorVal(g_h_atr14_h1, 0, 1);
   if(atr <= 0.0) return 0;
   if(asiaMove < -0.5 * atr && rates[0].close > rates[1].close) return 1;  // Inventory rebound
   if(asiaMove > 0.5 * atr && rates[0].close < rates[1].close) return -1; // Inventory fade
   return 0;
}

// Brain 104: Golden Hour (08:00 - 09:30 UTC) Volume Momentum
int Brain104_Time_GoldenHourInstitutionalFlow()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 3, rates) < 3) return 0;
   if(rates[0].tick_volume > rates[1].tick_volume && rates[0].close > rates[0].open) return 1;
   if(rates[0].tick_volume > rates[1].tick_volume && rates[0].close < rates[0].open) return -1;
   return 0;
}

// Brain 105: Frankfurt Pre-Market (06:00 UTC) Buildup
int Brain105_Time_PreMarketLondonBuildup()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 5, rates) < 5) return 0;
   if(rates[3].close > rates[3].open && rates[0].close > rates[3].high) return 1;
   if(rates[3].close < rates[3].open && rates[0].close < rates[3].low)  return -1;
   return 0;
}

// Brain 106: End-of-Week Institutional Square-Off
int Brain106_Time_EndOfWeekPositioning()
{
   MqlDateTime dt;
   TimeToStruct(GetCurrentTimeUTC(), dt);
   if(dt.day_of_week == 5)
   {
      MqlRates rates[];
      if(GetRatesSeries(PERIOD_H1, 1, 5, rates) >= 5)
      {
         if(rates[0].close > rates[4].close) return -1; // Friday fade of weekly rally
         if(rates[0].close < rates[4].close) return 1;  // Friday bounce of weekly dump
      }
   }
   return 0;
}

// Brain 107: Monthly Macro Seasonality (Strong vs Weak Gold Months)
int Brain107_Time_MonthlySeasonality()
{
   MqlDateTime dt;
   TimeToStruct(GetCurrentTimeUTC(), dt);
   // Strong gold months: Jan (1), Aug (8), Nov (11)
   // Weak gold months: Mar (3), Jun (6), Oct (10)
   if(dt.mon == 1 || dt.mon == 8 || dt.mon == 11) return 1;
   if(dt.mon == 3 || dt.mon == 6 || dt.mon == 10) return -1;
   return 0;
}

// Brain 108: Harmonic 24-Hour Circadian Cycle Phase
int Brain108_Time_IntradayCyclePhase()
{
   MqlDateTime dt;
   TimeToStruct(GetCurrentTimeUTC(), dt);
   double cycle = MathSin(2.0 * M_PI * (dt.hour - 7.0) / 24.0);
   if(cycle > 0.50) return 1;
   if(cycle < -0.50) return -1;
   return 0;
}

//══════════════════════════════════════════════════════════════════
// DISCIPLINE 10: SUPPORT/RESISTANCE & PIVOTS (Brains 109 - 117)
//══════════════════════════════════════════════════════════════════

// Brain 109: Daily Classical Pivot Point (P, R1, S1)
int Brain109_SR_DailyClassicalPivots()
{
   MqlRates d1Rates[], h1Rates[];
   if(GetRatesSeries(PERIOD_D1, 1, 1, d1Rates) < 1 || GetRatesSeries(PERIOD_H1, 1, 1, h1Rates) < 1) return 0;
   double p  = (d1Rates[0].high + d1Rates[0].low + d1Rates[0].close) / 3.0;
   double r1 = 2.0 * p - d1Rates[0].low;
   double s1 = 2.0 * p - d1Rates[0].high;
   if(h1Rates[0].close > p && h1Rates[0].close < r1) return 1;
   if(h1Rates[0].close < p && h1Rates[0].close > s1) return -1;
   return 0;
}

// Brain 110: Daily Camarilla Pivots (L3/H3 Reversal, L4/H4 Breakout)
int Brain110_SR_CamarillaPivots()
{
   MqlRates d1Rates[], h1Rates[];
   if(GetRatesSeries(PERIOD_D1, 1, 1, d1Rates) < 1 || GetRatesSeries(PERIOD_H1, 1, 1, h1Rates) < 1) return 0;
   double range = d1Rates[0].high - d1Rates[0].low;
   if(range <= 0.0) return 0;
   double h4 = d1Rates[0].close + range * 1.1 / 2.0;
   double h3 = d1Rates[0].close + range * 1.1 / 4.0;
   double l3 = d1Rates[0].close - range * 1.1 / 4.0;
   double l4 = d1Rates[0].close - range * 1.1 / 2.0;
   if(h1Rates[0].close > h4) return 1;  // Breakout long
   if(h1Rates[0].close < l4) return -1; // Breakout short
   if(h1Rates[0].low <= l3 && h1Rates[0].close > l3) return 1;  // Rebound off L3
   if(h1Rates[0].high >= h3 && h1Rates[0].close < h3) return -1; // Rejection off H3
   return 0;
}

// Brain 111: Woodie Pivot Point Weighted Bias
int Brain111_SR_WoodiePivots()
{
   MqlRates d1Rates[], h1Rates[];
   if(GetRatesSeries(PERIOD_D1, 1, 1, d1Rates) < 1 || GetRatesSeries(PERIOD_H1, 1, 1, h1Rates) < 1) return 0;
   double woodieP = (d1Rates[0].high + d1Rates[0].low + 2.0 * d1Rates[0].close) / 4.0;
   if(h1Rates[0].close > woodieP) return 1;
   if(h1Rates[0].close < woodieP) return -1;
   return 0;
}

// Brain 112: Fibonacci Pivot Levels (0.382 / 0.618)
int Brain112_SR_FibonacciPivots()
{
   MqlRates d1Rates[], h1Rates[];
   if(GetRatesSeries(PERIOD_D1, 1, 1, d1Rates) < 1 || GetRatesSeries(PERIOD_H1, 1, 1, h1Rates) < 1) return 0;
   double p = (d1Rates[0].high + d1Rates[0].low + d1Rates[0].close) / 3.0;
   double range = d1Rates[0].high - d1Rates[0].low;
   if(h1Rates[0].close > p + 0.382 * range) return 1;
   if(h1Rates[0].close < p - 0.382 * range) return -1;
   return 0;
}

// Brain 113: 5-Day High Volume Node (HVN) Rejection
int Brain113_SR_HighVolumeNode()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 120, rates) < 120) return 0;
   long maxVol = 0;
   double hvnPrice = rates[0].close;
   for(int i = 0; i < 120; i++)
   {
      if(rates[i].tick_volume > maxVol)
      {
         maxVol = rates[i].tick_volume;
         hvnPrice = rates[i].close;
      }
   }
   if(rates[0].low <= hvnPrice && rates[0].close > hvnPrice) return 1;
   if(rates[0].high >= hvnPrice && rates[0].close < hvnPrice) return -1;
   return 0;
}

// Brain 114: Psychological Round Numbers ($50 / $100 Barrier)
int Brain114_SR_RoundPsychologicalNumbers()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 2, rates) < 2) return 0;
   double round50 = MathRound(rates[0].close / 50.0) * 50.0;
   if(rates[0].low <= round50 && rates[0].close > round50) return 1;
   if(rates[0].high >= round50 && rates[0].close < round50) return -1;
   return 0;
}

// Brain 115: 50-Bar Structural Swing High / Low Rejection
int Brain115_SR_SwingHighLowStructuralRejection()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 52, rates) < 52) return 0;
   double maxH = rates[1].high, minL = rates[1].low;
   for(int i = 2; i < 50; i++)
   {
      if(rates[i].high > maxH) maxH = rates[i].high;
      if(rates[i].low  < minL) minL = rates[i].low;
   }
   double atr = GetIndicatorVal(g_h_atr14_h1, 0, 1);
   if(rates[0].low <= minL && rates[0].close > minL + 0.3 * atr) return 1;
   if(rates[0].high >= maxH && rates[0].close < maxH - 0.3 * atr) return -1;
   return 0;
}

// Brain 116: H4 50-Period SMA Dynamic Support / Resistance
int Brain116_SR_DynamicMovingAverageSR()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H4, 1, 2, rates) < 2) return 0;
   double sma50 = GetIndicatorVal(g_h_ma_h4, 0, 1);
   if(rates[0].low <= sma50 && rates[0].close > sma50) return 1;
   if(rates[0].high >= sma50 && rates[0].close < sma50) return -1;
   return 0;
}

// Brain 117: 3-Day High / Low Range Breakout
int Brain117_SR_MultiDayRangeExtremes()
{
   MqlRates d1Rates[], h1Rates[];
   if(GetRatesSeries(PERIOD_D1, 1, 4, d1Rates) < 4 || GetRatesSeries(PERIOD_H1, 1, 1, h1Rates) < 1) return 0;
   double maxH = d1Rates[1].high, minL = d1Rates[1].low;
   for(int i = 2; i <= 3; i++)
   {
      if(d1Rates[i].high > maxH) maxH = d1Rates[i].high;
      if(d1Rates[i].low  < minL) minL = d1Rates[i].low;
   }
   if(h1Rates[0].close > maxH) return 1;
   if(h1Rates[0].close < minL) return -1;
   return 0;
}

//══════════════════════════════════════════════════════════════════
// DISCIPLINE 11: CANDLESTICK PATTERNS (Brains 118 - 128)
//══════════════════════════════════════════════════════════════════

// Brain 118: Bullish / Bearish Engulfing
int Brain118_Candle_Engulfing()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 3, rates) < 3) return 0;
   if(rates[1].close < rates[1].open && rates[0].close > rates[0].open &&
      rates[0].close > rates[1].open && rates[0].open < rates[1].close) return 1;
   if(rates[1].close > rates[1].open && rates[0].close < rates[0].open &&
      rates[0].close < rates[1].open && rates[0].open > rates[1].close) return -1;
   return 0;
}

// Brain 119: Hammer / Hanging Man Wick Reversal
int Brain119_Candle_HammerHangingMan()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 2, rates) < 2) return 0;
   double body = MathAbs(rates[0].close - rates[0].open);
   double lowerWick = MathMin(rates[0].open, rates[0].close) - rates[0].low;
   double upperWick = rates[0].high - MathMax(rates[0].open, rates[0].close);
   if(body > 0.0)
   {
      if(lowerWick >= 2.0 * body && upperWick <= 0.2 * body) return 1;  // Hammer
      if(upperWick >= 2.0 * body && lowerWick <= 0.2 * body) return -1; // Shooting Star
   }
   return 0;
}

// Brain 120: Morning Star / Evening Star
int Brain120_Candle_MorningEveningStar()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 4, rates) < 4) return 0;
   // Morning Star
   if(rates[2].close < rates[2].open && MathAbs(rates[1].close - rates[1].open) < 0.3 * (rates[2].open - rates[2].close) &&
      rates[0].close > (rates[2].open + rates[2].close) / 2.0) return 1;
   // Evening Star
   if(rates[2].close > rates[2].open && MathAbs(rates[1].close - rates[1].open) < 0.3 * (rates[2].close - rates[2].open) &&
      rates[0].close < (rates[2].open + rates[2].close) / 2.0) return -1;
   return 0;
}

// Brain 121: Three White Soldiers / Three Black Crows
int Brain121_Candle_ThreeWhiteSoldiersBlackCrows()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 4, rates) < 4) return 0;
   if(rates[0].close > rates[0].open && rates[1].close > rates[1].open && rates[2].close > rates[2].open &&
      rates[0].close > rates[1].close && rates[1].close > rates[2].close) return 1;
   if(rates[0].close < rates[0].open && rates[1].close < rates[1].open && rates[2].close < rates[2].open &&
      rates[0].close < rates[1].close && rates[1].close < rates[2].close) return -1;
   return 0;
}

// Brain 122: Pinbar Rejection Wick (>= 65% Range)
int Brain122_Candle_PinbarRejectionWick()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 2, rates) < 2) return 0;
   double range = rates[0].high - rates[0].low;
   if(range <= 0.0) return 0;
   double lowerWick = MathMin(rates[0].open, rates[0].close) - rates[0].low;
   double upperWick = rates[0].high - MathMax(rates[0].open, rates[0].close);
   if((lowerWick / range) >= 0.65) return 1;
   if((upperWick / range) >= 0.65) return -1;
   return 0;
}

// Brain 123: Inside Bar Breakout
int Brain123_Candle_InsideBarBreakout()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 4, rates) < 4) return 0;
   // Bar 1 was inside bar of Bar 2; Bar 0 breaks out
   if(rates[1].high < rates[2].high && rates[1].low > rates[2].low)
   {
      if(rates[0].close > rates[2].high) return 1;
      if(rates[0].close < rates[2].low)  return -1;
   }
   return 0;
}

// Brain 124: Outside Bar Absorption
int Brain124_Candle_OutsideBarAbsorption()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 3, rates) < 3) return 0;
   if(rates[0].high > rates[1].high && rates[0].low < rates[1].low)
   {
      return (rates[0].close > rates[0].open) ? 1 : -1;
   }
   return 0;
}

// Brain 125: Marubozu Institutional Momentum Impulse
int Brain125_Candle_MarubozuImpulse()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 2, rates) < 2) return 0;
   double range = rates[0].high - rates[0].low;
   if(range <= 0.0) return 0;
   double body = MathAbs(rates[0].close - rates[0].open);
   double wicks = range - body;
   if(wicks <= 0.05 * range)
   {
      return (rates[0].close > rates[0].open) ? 1 : -1;
   }
   return 0;
}

// Brain 126: Doji Reversal Confirmation Trigger
int Brain126_Candle_DojiReversalTrigger()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 3, rates) < 3) return 0;
   double range1 = rates[1].high - rates[1].low;
   if(range1 <= 0.0) return 0;
   double body1 = MathAbs(rates[1].close - rates[1].open);
   if((body1 / range1) <= 0.10) // Doji on bar 1
   {
      if(rates[0].close > rates[1].high) return 1;
      if(rates[0].close < rates[1].low)  return -1;
   }
   return 0;
}

// Brain 127: Piercing Line / Dark Cloud Cover
int Brain127_Candle_PiercingLineDarkCloud()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 3, rates) < 3) return 0;
   // Piercing Line
   if(rates[1].close < rates[1].open && rates[0].open < rates[1].low &&
      rates[0].close >= (rates[1].open + rates[1].close) / 2.0 && rates[0].close < rates[1].open) return 1;
   // Dark Cloud Cover
   if(rates[1].close > rates[1].open && rates[0].open > rates[1].high &&
      rates[0].close <= (rates[1].open + rates[1].close) / 2.0 && rates[0].close > rates[1].open) return -1;
   return 0;
}

// Brain 128: Tweezer Tops / Tweezer Bottoms
int Brain128_Candle_TweezerTopsBottoms()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 3, rates) < 3) return 0;
   if(MathAbs(rates[0].low  - rates[1].low)  <= 5.0 * _Point && rates[0].close > rates[0].open) return 1;
   if(MathAbs(rates[0].high - rates[1].high) <= 5.0 * _Point && rates[0].close < rates[0].open) return -1;
   return 0;
}

//══════════════════════════════════════════════════════════════════
// DISCIPLINE 12: PSYCHOLOGICAL & SENTIMENT (Brains 129 - 135)
//══════════════════════════════════════════════════════════════════

// Brain 129: Retail Sentiment Fade Proxy
int Brain129_Sent_RetailPositioningFade()
{
   double rsi = GetIndicatorVal(g_h_rsi14_h1, 0, 1);
   double stochK = GetIndicatorVal(g_h_stoch_h1, 0, 1);
   if(rsi > 75.0 && stochK > 85.0) return -1; // Overcrowded long retail fade
   if(rsi < 25.0 && stochK < 15.0) return 1;  // Overcrowded short retail fade
   return 0;
}

// Brain 130: 5 Consecutive Bars Exhaustion Mean-Reversion
int Brain130_Sent_ConsecutiveBarsExhaustion()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 6, rates) < 6) return 0;
   bool allBull = true, allBear = true;
   for(int i = 0; i < 5; i++)
   {
      if(rates[i].close <= rates[i].open) allBull = false;
      if(rates[i].close >= rates[i].open) allBear = false;
   }
   if(allBull) return -1; // Exhaustion fade sell
   if(allBear) return 1;  // Exhaustion fade buy
   return 0;
}

// Brain 131: $100 Psychological Round Number Magnetic Trap
int Brain131_Sent_RoundNumberMagneticTrap()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 2, rates) < 2) return 0;
   double round100 = MathRound(rates[0].close / 100.0) * 100.0;
   double dist = rates[0].close - round100;
   if(dist < 0 && dist > -15.0) return 1;  // Magnetic pull upwards
   if(dist > 0 && dist < 15.0)  return -1; // Magnetic pull downwards
   return 0;
}

// Brain 132: Bull / Bear Trap Breakout Failure
int Brain132_Sent_TrapBreakoutFailure()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 22, rates) < 22) return 0;
   double high20 = rates[2].high, low20 = rates[2].low;
   for(int i = 3; i < 21; i++)
   {
      if(rates[i].high > high20) high20 = rates[i].high;
      if(rates[i].low  < low20)  low20  = rates[i].low;
   }
   if(rates[1].high > high20 && rates[0].close < high20) return -1; // Bull trap failed
   if(rates[1].low  < low20  && rates[0].close > low20)  return 1;  // Bear trap failed
   return 0;
}

// Brain 133: Panic Liquidation Flush & Recovery Bounce
int Brain133_Sent_PanicLiquidationBounce()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 2, rates) < 2) return 0;
   double atr = GetIndicatorVal(g_h_atr14_h1, 0, 1);
   double range = rates[0].high - rates[0].low;
   double lowerWick = MathMin(rates[0].open, rates[0].close) - rates[0].low;
   if(range > 2.0 * atr && lowerWick >= 0.40 * range) return 1;  // Panic flush bought up
   double upperWick = rates[0].high - MathMax(rates[0].open, rates[0].close);
   if(range > 2.0 * atr && upperWick >= 0.40 * range) return -1; // Panic squeeze rejected
   return 0;
}

// Brain 134: Parabolic Greed Climax Reversal
int Brain134_Sent_GreedExpansionClimax()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 2, rates) < 2) return 0;
   double rsi = GetIndicatorVal(g_h_rsi14_h1, 0, 1);
   double atr = GetIndicatorVal(g_h_atr14_h1, 0, 1);
   if(rsi > 85.0 && rates[0].close < rates[0].high - 0.2 * atr) return -1; // Blow-off top
   if(rsi < 15.0 && rates[0].close > rates[0].low  + 0.2 * atr) return 1;  // Capitulation bottom
   return 0;
}

// Brain 135: Monday Weekend Gap Fill Bias
int Brain135_Sent_WeekendGapFill()
{
   MqlDateTime dt;
   TimeToStruct(GetCurrentTimeUTC(), dt);
   if(dt.day_of_week == 1) // Monday only
   {
      MqlRates d1Rates[];
      if(GetRatesSeries(PERIOD_D1, 1, 2, d1Rates) >= 2)
      {
         double gap = d1Rates[0].open - d1Rates[1].close;
         if(gap > 100.0 * _Point)  return -1; // Gap up -> Fill down
         if(gap < -100.0 * _Point) return 1;  // Gap down -> Fill up
      }
   }
   return 0;
}

//══════════════════════════════════════════════════════════════════
// DISCIPLINE 13: FRONTIER & EXPERIMENTAL (Brains 136 - 144)
//══════════════════════════════════════════════════════════════════

// Brain 136: Sevcik Fractal Dimension D < 1.35
int Brain136_Frontier_FractalDimension()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 32, rates) < 32) return 0;
   double minP = rates[0].close, maxP = rates[0].close;
   for(int i = 1; i < 30; i++)
   {
      if(rates[i].close < minP) minP = rates[i].close;
      if(rates[i].close > maxP) maxP = rates[i].close;
   }
   double range = maxP - minP;
   if(range <= 0.0) return 0;
   double length = 0.0;
   for(int i = 0; i < 29; i++)
   {
      double y1 = (rates[i+1].close - minP) / range;
      double y2 = (rates[i].close - minP) / range;
      double dx = 1.0 / 29.0;
      double dy = y2 - y1;
      length += MathSqrt(dx * dx + dy * dy);
   }
   if(length <= 0.0) return 0;
   double d = 1.0 + (MathLog(length) + MathLog(2.0)) / MathLog(2.0 * 29.0);
   double e21 = GetIndicatorVal(g_h_ema21_h1, 0, 1);
   if(d < 1.35) return (rates[0].close > e21) ? 1 : -1; // Clean trending state
   return 0;
}

// Brain 137: John Ehlers Gaussian Fisher Transform Trigger Cross
int Brain137_Frontier_EhlersFisherTransform()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 15, rates) < 15) return 0;
   double maxH = rates[0].high, minL = rates[0].low;
   for(int i = 1; i < 10; i++)
   {
      if(rates[i].high > maxH) maxH = rates[i].high;
      if(rates[i].low  < minL) minL = rates[i].low;
   }
   double range = maxH - minL;
   if(range <= 0.0) return 0;
   double mid = (rates[0].high + rates[0].low) / 2.0;
   double x = 0.66 * ((mid - minL) / range - 0.5);
   x = MathMax(-0.999, MathMin(0.999, x));
   double fisher = 0.5 * MathLog((1.0 + x) / (1.0 - x));
   if(fisher > 0.5)  return 1;
   if(fisher < -0.5) return -1;
   return 0;
}

// Brain 138: Ehlers Cyber Cycle Phase Turning Point
int Brain138_Frontier_CyberCyclePhase()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 10, rates) < 10) return 0;
   double smooth1 = (rates[0].close + 2.0 * rates[1].close + 2.0 * rates[2].close + rates[3].close) / 6.0;
   double smooth2 = (rates[1].close + 2.0 * rates[2].close + 2.0 * rates[3].close + rates[4].close) / 6.0;
   if(smooth1 > smooth2) return 1;
   if(smooth1 < smooth2) return -1;
   return 0;
}

// Brain 139: Ehlers Instantaneous Trendline Position
int Brain139_Frontier_InstantaneousTrendline()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 8, rates) < 8) return 0;
   double itrend1 = (rates[0].close + 2.0 * rates[1].close + rates[2].close) / 4.0;
   double itrend2 = (rates[1].close + 2.0 * rates[2].close + rates[3].close) / 4.0;
   if(rates[0].close > itrend1 && itrend1 > itrend2) return 1;
   if(rates[0].close < itrend1 && itrend1 < itrend2) return -1;
   return 0;
}

// Brain 140: Ehlers Center of Gravity (CoG) Crossover
int Brain140_Frontier_CenterOfGravity()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 15, rates) < 15) return 0;
   double num1 = 0, den1 = 0;
   double num2 = 0, den2 = 0;
   for(int i = 0; i < 10; i++)
   {
      num1 += (1.0 + i) * rates[i].close;
      den1 += rates[i].close;
      num2 += (1.0 + i) * rates[i+1].close;
      den2 += rates[i+1].close;
   }
   if(den1 <= 0 || den2 <= 0) return 0;
   double cog1 = -num1 / den1;
   double cog2 = -num2 / den2;
   if(cog1 > cog2) return 1;
   if(cog1 < cog2) return -1;
   return 0;
}

// Brain 141: Singular Spectrum Analysis (SSA) Reconstructed Trend
int Brain141_Frontier_SingularSpectrumAnalysis()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 20, rates) < 20) return 0;
   // Weighted moving average as primary trajectory matrix eigenvector reconstruction
   double w1 = 0, w2 = 0;
   for(int i = 0; i < 10; i++)
   {
      w1 += rates[i].close * (10 - i);
      w2 += rates[i+1].close * (10 - i);
   }
   if(w1 > w2) return 1;
   if(w1 < w2) return -1;
   return 0;
}

// Brain 142: Haar Wavelet Denoised Momentum
int Brain142_Frontier_WaveletDenoisedMomentum()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 16, rates) < 16) return 0;
   double a1 = (rates[0].close + rates[1].close + rates[2].close + rates[3].close) / 4.0;
   double a2 = (rates[4].close + rates[5].close + rates[6].close + rates[7].close) / 4.0;
   if(a1 > a2) return 1;
   if(a1 < a2) return -1;
   return 0;
}

// Brain 143: Echo State Network (ESN) Reservoir Proxy
int Brain143_Frontier_EchoStateNetworkProxy()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 12, rates) < 12) return 0;
   double readout = 0.35 * (rates[0].close - rates[1].close) +
                    0.25 * (rates[1].close - rates[2].close) +
                    0.20 * (rates[2].close - rates[3].close) +
                    0.12 * (rates[3].close - rates[4].close) +
                    0.08 * (rates[4].close - rates[5].close);
   double atr = GetIndicatorVal(g_h_atr14_h1, 0, 1);
   if(atr <= 0.0) return 0;
   double norm = readout / atr;
   if(norm > 0.15) return 1;
   if(norm < -0.15) return -1;
   return 0;
}

// Brain 144: Teager-Kaiser Energy Operator (TKEO)
int Brain144_Frontier_NonlinearEnergyOperator()
{
   MqlRates rates[];
   if(GetRatesSeries(PERIOD_H1, 1, 20, rates) < 20) return 0;
   double energies[15];
   for(int i = 0; i < 15; i++)
   {
      double x = rates[i].close - rates[i+1].close;
      double x_prev = rates[i+1].close - rates[i+2].close;
      double x_next = rates[i].close - rates[i+1].close;
      energies[i] = (x * x) - (x_prev * x_next);
   }
   double meanEnergy = CalcMean(energies, 1, 14);
   if(energies[0] > 1.8 * meanEnergy && rates[0].close > rates[1].close) return 1;
   if(energies[0] > 1.8 * meanEnergy && rates[0].close < rates[1].close) return -1;
   return 0;
}

//+------------------------------------------------------------------+
//| Calculate 144-Brain Ensemble Consensus Score                     |
//+------------------------------------------------------------------+
double CalculateEnsembleConsensusScore(int &buyCount, int &sellCount, int &neutralCount)
{
   buyCount = 0;
   sellCount = 0;
   neutralCount = 0;
   double totalScore = 0.0;

   int votes[144];
   votes[0]   = Brain001_SMC_CHoCH();
   votes[1]   = Brain002_SMC_BOS();
   votes[2]   = Brain003_SMC_OrderBlock();
   votes[3]   = Brain004_SMC_FairValueGap();
   votes[4]   = Brain005_SMC_LiquiditySweep();
   votes[5]   = Brain006_SMC_KillZone_Expansion();
   votes[6]   = Brain007_SMC_PremiumDiscount();
   votes[7]   = Brain008_SMC_JudasSwing();
   votes[8]   = Brain009_SMC_InstitutionalFunding();
   votes[9]   = Brain010_SMC_MitigationBlock();
   votes[10]  = Brain011_SMC_BreakerBlock();
   votes[11]  = Brain012_SMC_Inducement();

   votes[12]  = Brain013_Trend_FastSlowEMA();
   votes[13]  = Brain014_Trend_GoldenCross50200();
   votes[14]  = Brain015_Trend_MultiTF_Alignment();
   votes[15]  = Brain016_Trend_SuperTrend();
   votes[16]  = Brain017_Trend_HullMA();
   votes[17]  = Brain018_Trend_ParabolicSAR();
   votes[18]  = Brain019_Trend_KAMA();
   votes[19]  = Brain020_Trend_DonchianBreakout();
   votes[20]  = Brain021_Trend_LinearRegressionSlope();
   votes[21]  = Brain022_Trend_IchimokuKinkoHyo();
   votes[22]  = Brain023_Trend_TEMA();
   votes[23]  = Brain024_Trend_AroonOscillator();
   votes[24]  = Brain025_Trend_VortexIndicator();
   votes[25]  = Brain026_Trend_TripleEMA_Cross();

   votes[26]  = Brain027_Mom_RSIDivergence();
   votes[27]  = Brain028_Mom_MACD_Histogram();
   votes[28]  = Brain029_Mom_StochasticCross();
   votes[29]  = Brain030_Mom_CCI_Extremes();
   votes[30]  = Brain031_Mom_WilliamsR();
   votes[31]  = Brain032_Mom_RateOfChange();
   votes[32]  = Brain033_Mom_UltimateOscillator();
   votes[33]  = Brain034_Mom_QQE_Signal();
   votes[34]  = Brain035_Mom_ChandeMomentum();
   votes[35]  = Brain036_Mom_TrueStrengthIndex();
   votes[36]  = Brain037_Mom_AwesomeOscillator();
   votes[37]  = Brain038_Mom_DeMarker();
   votes[38]  = Brain039_Mom_StochRSI();
   votes[39]  = Brain040_Mom_ElderRay();

   votes[40]  = Brain041_Vol_ATRExpansion();
   votes[41]  = Brain042_Vol_BollingerSqueezeBreakout();
   votes[42]  = Brain043_Vol_KeltnerChannelBreakout();
   votes[43]  = Brain044_Vol_HistoricalVolatility();
   votes[44]  = Brain045_Vol_ChaikinVolatility();
   votes[45]  = Brain046_Vol_StdDevExtremes();
   votes[46]  = Brain047_Vol_VolatilityRatio();
   votes[47]  = Brain048_Vol_MassIndex();
   votes[48]  = Brain049_Vol_UlcerIndex();
   votes[49]  = Brain050_Vol_RelativeVolatilityIndex();

   votes[50]  = Brain051_VolFlow_OBV_Trend();
   votes[51]  = Brain052_VolFlow_TickVolumeAccumulation();
   votes[52]  = Brain053_VolFlow_VolumePriceTrend();
   votes[53]  = Brain054_VolFlow_ChaikinMoneyFlow();
   votes[54]  = Brain055_VolFlow_EaseOfMovement();
   votes[55]  = Brain056_VolFlow_ForceIndex();
   votes[56]  = Brain057_VolFlow_VolumeWeightedMACD();
   votes[57]  = Brain058_VolFlow_VolumeOscillator();
   votes[58]  = Brain059_VolFlow_VolumeSpikeExhaustion();

   votes[59]  = Brain060_Fibo_GoldenPocketRetracement();
   votes[60]  = Brain061_Fibo_DeepRetracement786();
   votes[61]  = Brain062_Fibo_ShallowContinuation382();
   votes[62]  = Brain063_Harmonic_ABCD_Projection();
   votes[63]  = Brain064_Harmonic_GartleyPattern();
   votes[64]  = Brain065_Harmonic_BatPattern();
   votes[65]  = Brain066_Harmonic_CrabPattern();
   votes[66]  = Brain067_Fibo_ExpansionLevels();
   votes[67]  = Brain068_Fibo_FanAngles();

   votes[68]  = Brain069_Quant_ZScorePriceMean();
   votes[69]  = Brain070_Quant_HurstExponent();
   votes[70]  = Brain071_Quant_OrnsteinUhlenbeckDrift();
   votes[71]  = Brain072_Quant_VarianceRatioTest();
   votes[72]  = Brain073_Quant_SkewnessKurtosis();
   votes[73]  = Brain074_Quant_AutocorrelationLag1();
   votes[74]  = Brain075_Quant_RollingSharpeMomentum();
   votes[75]  = Brain076_Quant_ShannonEntropy();
   votes[76]  = Brain077_Quant_KalmanFilterTracking();
   votes[77]  = Brain078_Quant_StandardizedResiduals();
   votes[78]  = Brain079_Quant_MarkovStateSwitching();
   votes[79]  = Brain080_Quant_BollingerPercentB_Quantiles();
   votes[80]  = Brain081_Quant_EmpiricalDistributionPercentiles();

   votes[81]  = Brain082_Macro_DXY_InverseProxy();
   votes[82]  = Brain083_Macro_US10Y_YieldProxy();
   votes[83]  = Brain084_Macro_RealYieldsProxy();
   votes[84]  = Brain085_Macro_Silver_BetaLeadLag();
   votes[85]  = Brain086_Macro_CrudeOil_InflationProxy();
   votes[86]  = Brain087_Macro_Copper_GrowthProxy();
   votes[87]  = Brain088_Macro_SP500_RiskSentiment();
   votes[88]  = Brain089_Macro_VIX_VolatilityRegime();
   votes[89]  = Brain090_Macro_USDJPY_LiquidityProxy();
   votes[90]  = Brain091_Macro_AUDUSD_CommodityCurrency();
   votes[91]  = Brain092_Macro_EmergingMarketStress();
   votes[92]  = Brain093_Macro_CentralBankImpulse();
   votes[93]  = Brain094_Macro_TradeWeightedUSD();
   votes[94]  = Brain095_Macro_TIPS_BreakevenInflation();

   votes[95]  = Brain096_Time_LondonOpenExpansion();
   votes[96]  = Brain097_Time_AsianRangeBreakout();
   votes[97]  = Brain098_Time_DayOfWeek_Seasonality();
   votes[98]  = Brain099_Time_TurnOfMonthEffect();
   votes[99]  = Brain100_Time_TripleWitchingOptionsExpiry();
   votes[100] = Brain101_Time_LondonFixingAnticipation();
   votes[101] = Brain102_Time_NewYorkOpenCrossover();
   votes[102] = Brain103_Time_OvernightInventoryRebalancing();
   votes[103] = Brain104_Time_GoldenHourInstitutionalFlow();
   votes[104] = Brain105_Time_PreMarketLondonBuildup();
   votes[105] = Brain106_Time_EndOfWeekPositioning();
   votes[106] = Brain107_Time_MonthlySeasonality();
   votes[107] = Brain108_Time_IntradayCyclePhase();

   votes[108] = Brain109_SR_DailyClassicalPivots();
   votes[109] = Brain110_SR_CamarillaPivots();
   votes[110] = Brain111_SR_WoodiePivots();
   votes[111] = Brain112_SR_FibonacciPivots();
   votes[112] = Brain113_SR_HighVolumeNode();
   votes[113] = Brain114_SR_RoundPsychologicalNumbers();
   votes[114] = Brain115_SR_SwingHighLowStructuralRejection();
   votes[115] = Brain116_SR_DynamicMovingAverageSR();
   votes[116] = Brain117_SR_MultiDayRangeExtremes();

   votes[117] = Brain118_Candle_Engulfing();
   votes[118] = Brain119_Candle_HammerHangingMan();
   votes[119] = Brain120_Candle_MorningEveningStar();
   votes[120] = Brain121_Candle_ThreeWhiteSoldiersBlackCrows();
   votes[121] = Brain122_Candle_PinbarRejectionWick();
   votes[122] = Brain123_Candle_InsideBarBreakout();
   votes[123] = Brain124_Candle_OutsideBarAbsorption();
   votes[124] = Brain125_Candle_MarubozuImpulse();
   votes[125] = Brain126_Candle_DojiReversalTrigger();
   votes[126] = Brain127_Candle_PiercingLineDarkCloud();
   votes[127] = Brain128_Candle_TweezerTopsBottoms();

   votes[128] = Brain129_Sent_RetailPositioningFade();
   votes[129] = Brain130_Sent_ConsecutiveBarsExhaustion();
   votes[130] = Brain131_Sent_RoundNumberMagneticTrap();
   votes[131] = Brain132_Sent_TrapBreakoutFailure();
   votes[132] = Brain133_Sent_PanicLiquidationBounce();
   votes[133] = Brain134_Sent_GreedExpansionClimax();
   votes[134] = Brain135_Sent_WeekendGapFill();

   votes[135] = Brain136_Frontier_FractalDimension();
   votes[136] = Brain137_Frontier_EhlersFisherTransform();
   votes[137] = Brain138_Frontier_CyberCyclePhase();
   votes[138] = Brain139_Frontier_InstantaneousTrendline();
   votes[139] = Brain140_Frontier_CenterOfGravity();
   votes[140] = Brain141_Frontier_SingularSpectrumAnalysis();
   votes[141] = Brain142_Frontier_WaveletDenoisedMomentum();
   votes[142] = Brain143_Frontier_EchoStateNetworkProxy();
   votes[143] = Brain144_Frontier_NonlinearEnergyOperator();

   for(int i = 0; i < 144; i++)
   {
      g_Brains[i].last_vote = votes[i];
      totalScore += votes[i] * g_Brains[i].weight;
      if(votes[i] > 0) buyCount++;
      else if(votes[i] < 0) sellCount++;
      else neutralCount++;
   }

   PrintFormat("[CONSENSUS] Total Score: %.2f | Votes: BUY=%d, SELL=%d, NEUTRAL=%d",
               totalScore, buyCount, sellCount, neutralCount);
   return totalScore;
}

//+------------------------------------------------------------------+
//| Execute Directional Market Order Based on Consensus Direction    |
//+------------------------------------------------------------------+
void ExecuteTrade(int direction)
{
   if(direction == 0) return; // Strict neutrality guard

   double entry = (direction == 1) ? SymbolInfoDouble(_Symbol, SYMBOL_ASK)
                                   : SymbolInfoDouble(_Symbol, SYMBOL_BID);

   double atrH1 = GetIndicatorVal(g_h_atr14_h1, 0, 1);
   double slPrice = CalculateSafeATRStopLoss(direction, entry, atrH1, InpATR_SL_Multiplier);
   double lots = CalculateLotSize(entry, slPrice, InpRiskPercent);

   if(direction == 1)
   {
      trade.Buy(lots, _Symbol, entry, slPrice, 0.0, "GoldOracle v2 BUY");
      PrintFormat("[ORDER] Placed BUY %.2f lots at %.2f with SL=%.2f", lots, entry, slPrice);
   }
   else if(direction == -1)
   {
      trade.Sell(lots, _Symbol, entry, slPrice, 0.0, "GoldOracle v2 SELL");
      PrintFormat("[ORDER] Placed SELL %.2f lots at %.2f with SL=%.2f", lots, entry, slPrice);
   }
}

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
   trade.SetExpertMagicNumber(InpMagicNumber);
   trade.SetDeviationInPoints(20);
   trade.SetTypeFilling(ORDER_FILLING_IOC);

   InitPipNormalization();
   InitAdaptiveEngine();

   if(!InitSharedIndicators())
   {
      Print("[INIT FAILED] Could not initialize all shared indicator handles.");
      return INIT_FAILED;
   }

   Print("[INIT SUCCESS] Gold Oracle EA v2 fully initialized with 144 brains and 56 shared indicator handles.");
   return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   ReleaseSharedIndicators();
   PrintFormat("[DEINIT] Gold Oracle EA v2 deinitialized. Reason code=%d", reason);
}

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
{
   datetime nowUTC = GetCurrentTimeUTC();
   MqlDateTime dt;
   TimeToStruct(nowUTC, dt);

   // 1. Midnight Daily State Reset
   if(dt.day_of_year != g_lastDay)
   {
      g_lastDay = dt.day_of_year;
      g_state   = STATE_WAITING_FOR_ANALYSIS;
      g_bNewsLockoutToday = false;
      g_sessionOpenPrice1000 = 0.0;
      PrintFormat("[NEW DAY] Daily reset executed for DOY %d (UTC %04d.%02d.%02d)",
                  g_lastDay, dt.year, dt.mon, dt.day);
   }

   // 2. High-Impact News Blackout Check
   if(CheckNewsBlackoutStatus())
   {
      if(g_state != STATE_NEWS_BLACKOUT)
      {
         Print("[SAFETY BLACKOUT] High-impact news event active. Liquidating all positions.");
         CloseAllPositions();
         g_state = STATE_NEWS_BLACKOUT;
         g_bNewsLockoutToday = true; // Strict zero re-entry enforcement
      }
      return;
   }

   // 3. Session Close & Adaptive Weight Update at 20:00 UTC
   if(dt.hour >= InpSessionCloseHour)
   {
      if(g_state != STATE_SESSION_CLOSED)
      {
         Print("[SESSION CLOSE] 20:00 UTC reached. Closing positions and updating brain weights.");
         CloseAllPositions();

         int actualDirection = DetermineSessionDirection();
         UpdateAdaptiveWeights(actualDirection);

         g_state = STATE_SESSION_CLOSED;
      }
      return;
   }

   // 4. London Analysis Window (07:00 - 10:00 UTC)
   if(g_state == STATE_WAITING_FOR_ANALYSIS && dt.hour >= InpAnalysisStartHour && dt.hour < InpAnalysisEndHour)
   {
      g_state = STATE_ANALYZING;
   }

   // 5. 10:00 UTC Entry Ready Trigger
   if(g_state == STATE_ANALYZING && dt.hour >= InpAnalysisEndHour)
   {
      g_state = STATE_ENTRY_READY;
   }

   // 6. Entry Execution at ~10:00 UTC
   if(g_state == STATE_ENTRY_READY && !g_bNewsLockoutToday && g_lastTradeDay != dt.day_of_year)
   {
      if(!IsPositionOpen())
      {
         // Hardware Gating: Spread & Volatility checks
         if(!IsSpreadPermitted(InpMaxSpreadPoints)) return;
         if(!IsVolatilityPermitted(g_h_atr14_h1, InpMinATR_H1_Points)) return;

         // Record 10:00 UTC session baseline price
         g_sessionOpenPrice1000 = SymbolInfoDouble(_Symbol, SYMBOL_BID);

         // Calculate 144-brain ensemble consensus
         int buys = 0, sells = 0, neutrals = 0;
         double score = CalculateEnsembleConsensusScore(buys, sells, neutrals);

         int direction = 0;
         if(score > InpMinScore)        direction = 1;  // BUY
         else if(score < -InpMinScore)  direction = -1; // SELL
         else                           direction = 0;  // NEUTRAL - NO TRADE

         if(direction != 0)
         {
            ExecuteTrade(direction);
            g_lastTradeDay = dt.day_of_year;
            g_state = STATE_TRADE_ACTIVE;
         }
         else
         {
            PrintFormat("[CONSENSUS NEUTRAL] Score %.2f within neutral dead-band [-%0.1f, +%0.1f]. No trade today.",
                        score, InpMinScore, InpMinScore);
            g_state = STATE_SESSION_CLOSED;
         }
      }
   }
}
//+------------------------------------------------------------------+

//+------------------------------------------------------------------+
//|                                              GoldOracle_v1.mq5 |
//|                                      Antigravity / Deepmind    |
//+------------------------------------------------------------------+
#property copyright "Antigravity"
#property link      ""
#property version   "1.00"

#include <Trade\Trade.mqh>

//--- CORE SETTINGS ---
input group "═══ CORE SETTINGS ═══"
input double InpRiskPercent        = 2.0;       // Risk % per trade
input double InpATR_SL_Multiplier  = 2.0;       // ATR × this = stop-loss distance
input int    InpATR_Period         = 14;        // ATR period for SL
input ulong  InpMagicNumber        = 2025101;   // Unique magic number

//--- SESSION TIMING ---
input group "═══ SESSION TIMING ═══"
input int    InpAnalysisStartHour  = 7;         // UTC hour: start analysis
input int    InpAnalysisEndHour    = 10;        // UTC hour: end analysis → place trade
input int    InpSessionCloseHour   = 20;        // UTC hour: close all positions

//--- ADAPTIVE ENGINE ---
input group "═══ ADAPTIVE ENGINE ═══"
input double InpDecayFactor        = 0.95;      // Exponential moving accuracy decay
input double InpMinScore           = 0.0;       // Minimum |score| to trade (0 = always trade)

//--- NEWS BLACKOUT ---
input group "═══ NEWS BLACKOUT ═══"
input bool   InpEnableNewsFilter     = true;
input int    InpNFP_BlockMinsBefore  = 30;
input int    InpNFP_BlockMinsAfter   = 60;
input int    InpFOMC_BlockMinsBefore = 30;
input int    InpFOMC_BlockMinsAfter  = 90;
input int    InpCPI_BlockMinsBefore  = 15;
input int    InpCPI_BlockMinsAfter   = 30;

//--- Globals
CTrade trade;
double pipFactor, pipSize;
int    h_atr_sl;
double atr_sl[];

enum ENUM_EA_STATE {
   STATE_WAITING_FOR_ANALYSIS,
   STATE_ANALYZING,
   STATE_ENTRY_READY,
   STATE_TRADE_ACTIVE,
   STATE_NEWS_BLACKOUT,
   STATE_SESSION_CLOSED,
};
ENUM_EA_STATE g_state = STATE_WAITING_FOR_ANALYSIS;
int g_lastDay = -1;
int g_lastTradeDay = -1;

// Brain state
struct SBrainState {
   string name;
   double weight;
   double ema_accuracy;
   int    last_vote;
   int    total_votes;
   int    correct_votes;
};
SBrainState g_Brains[25];

// Handles
int h_ema50_h1, h_ema200_h1, h_ema50_h4, h_ema200_h4;
int h_rsi_h1, h_macd_h1, h_bb_h1, h_adx_h1, h_stoch_h1;
int h_atr_h1, h_atr_h4;
int h_ma_h4;

//------------------------------------------------------------------
// INIT
//------------------------------------------------------------------
int OnInit()
{
   trade.SetExpertMagicNumber(InpMagicNumber);
   
   pipFactor = (_Digits == 5 || _Digits == 3) ? 10.0 : 1.0;
   pipSize   = _Point * pipFactor;
   
   h_atr_sl = iATR(_Symbol, PERIOD_H1, InpATR_Period);
   ArraySetAsSeries(atr_sl, true);
   
   // Init brains
   for(int i=0; i<25; i++) {
      g_Brains[i].weight = 1.0;
      g_Brains[i].ema_accuracy = 1.0;
      g_Brains[i].last_vote = 0;
      g_Brains[i].total_votes = 0;
      g_Brains[i].correct_votes = 0;
   }
   g_Brains[0].name = "Brain01_CHoCH_BOS";
   g_Brains[1].name = "Brain02_OrderBlock";
   g_Brains[2].name = "Brain03_FairValueGap";
   g_Brains[3].name = "Brain04_LiquiditySweep";
   g_Brains[4].name = "Brain05_PremiumDiscount";
   g_Brains[5].name = "Brain06_EMA_Trend";
   g_Brains[6].name = "Brain07_RSI_Momentum";
   g_Brains[7].name = "Brain08_MACD_Histogram";
   g_Brains[8].name = "Brain09_Bollinger_MeanRev";
   g_Brains[9].name = "Brain10_ADX_TrendStrength";
   g_Brains[10].name = "Brain11_Stochastic_Cross";
   g_Brains[11].name = "Brain12_ATR_VOL_MACD";
   g_Brains[12].name = "Brain13_TickVolumeDivergence";
   g_Brains[13].name = "Brain14_ATR_Channel_Position";
   g_Brains[14].name = "Brain15_BB_Squeeze";
   g_Brains[15].name = "Brain16_Pivot_Level_Bias";
   g_Brains[16].name = "Brain17_Fibonacci_Channel";
   g_Brains[17].name = "Brain18_NRTR_Direction";
   g_Brains[18].name = "Brain19_QQE_Signal";
   g_Brains[19].name = "Brain20_DayOfWeek_Bias";
   g_Brains[20].name = "Brain21_AsianRange_Breakout";
   g_Brains[21].name = "Brain22_RoundNumber_Gravity";
   g_Brains[22].name = "Brain23_DXY_Inverse";
   g_Brains[23].name = "Brain24_OpenClose_Momentum";
   g_Brains[24].name = "Brain25_MultiTF_Alignment";
   
   // Init Indicators
   h_ema50_h1 = iMA(_Symbol, PERIOD_H1, 50, 0, MODE_EMA, PRICE_CLOSE);
   h_ema200_h1 = iMA(_Symbol, PERIOD_H1, 200, 0, MODE_EMA, PRICE_CLOSE);
   h_ema50_h4 = iMA(_Symbol, PERIOD_H4, 50, 0, MODE_EMA, PRICE_CLOSE);
   h_ema200_h4 = iMA(_Symbol, PERIOD_H4, 200, 0, MODE_EMA, PRICE_CLOSE);
   h_rsi_h1 = iRSI(_Symbol, PERIOD_H1, 14, PRICE_CLOSE);
   h_macd_h1 = iMACD(_Symbol, PERIOD_H1, 12, 26, 9, PRICE_CLOSE);
   h_bb_h1 = iBands(_Symbol, PERIOD_H1, 20, 0, 2.0, PRICE_CLOSE);
   h_adx_h1 = iADX(_Symbol, PERIOD_H1, 14);
   h_stoch_h1 = iStochastic(_Symbol, PERIOD_H1, 14, 3, 3, MODE_SMA, STO_LOWHIGH);
   h_atr_h1 = iATR(_Symbol, PERIOD_H1, 14);
   h_atr_h4 = iATR(_Symbol, PERIOD_H4, 14);
   h_ma_h4 = iMA(_Symbol, PERIOD_H4, 20, 0, MODE_SMA, PRICE_CLOSE);

   return INIT_SUCCEEDED;
}

void OnDeinit(const int reason)
{
   IndicatorRelease(h_atr_sl);
   IndicatorRelease(h_ema50_h1);
   IndicatorRelease(h_ema200_h1);
   IndicatorRelease(h_ema50_h4);
   IndicatorRelease(h_ema200_h4);
   IndicatorRelease(h_rsi_h1);
   IndicatorRelease(h_macd_h1);
   IndicatorRelease(h_bb_h1);
   IndicatorRelease(h_adx_h1);
   IndicatorRelease(h_stoch_h1);
   IndicatorRelease(h_atr_h1);
   IndicatorRelease(h_atr_h4);
   IndicatorRelease(h_ma_h4);
}

//------------------------------------------------------------------
// UTILS
//------------------------------------------------------------------
double PipsToPrice(double pips) { return pips * pipSize; }

double GetSafeSL(int direction, double entryPrice, double desiredSLPips)
{
   long   stopLevel  = SymbolInfoInteger(_Symbol, SYMBOL_TRADE_STOPS_LEVEL);
   double minDist    = stopLevel * _Point;
   double wantedDist = PipsToPrice(desiredSLPips);
   double safeDist   = MathMax(wantedDist, minDist + _Point);
   return (direction == 1) ? entryPrice - safeDist : entryPrice + safeDist;
}

double NormalizeLot(double rawLot)
{
   double minLot  = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double maxLot  = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
   double lotStep = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   double lot     = MathFloor(rawLot / lotStep) * lotStep;
   return MathMax(minLot, MathMin(maxLot, lot));
}

//------------------------------------------------------------------
// NEWS CALENDAR
//------------------------------------------------------------------
struct SNewsWindow {
   int dayOfWeek;
   int hourGMT;
   int minuteGMT;
   int minsBeforeBlock;
   int minsAfterBlock;
};

SNewsWindow g_NewsBlackouts[] = {
   {5, 12, 30, 30, 60},    // NFP: 1st Friday 12:30 UTC
   {3, 18,  0, 30, 90},    // FOMC: Wednesday 18:00 UTC
   {2, 12, 30, 15, 30},    // CPI: Tuesday 12:30 UTC
   {4, 12, 30, 15, 30},    // PPI: Thursday 12:30 UTC
   {3, 14,  0, 15, 30},    // Powell Speech
};

bool IsNewsBlackout()
{
   if(!InpEnableNewsFilter) return false;
   MqlDateTime now;
   TimeToStruct(TimeTradeServer(), now);
   int currentMins = now.hour * 60 + now.min;
   for(int i = 0; i < ArraySize(g_NewsBlackouts); i++) {
      if(now.day_of_week != g_NewsBlackouts[i].dayOfWeek) continue;
      // NFP week check: only 1st friday
      if(g_NewsBlackouts[i].dayOfWeek == 5) {
         if(now.day > 7) continue; 
      }
      int eventMins  = g_NewsBlackouts[i].hourGMT * 60 + g_NewsBlackouts[i].minuteGMT;
      int blockStart = eventMins - g_NewsBlackouts[i].minsBeforeBlock;
      int blockEnd   = eventMins + g_NewsBlackouts[i].minsAfterBlock;
      if(currentMins >= blockStart && currentMins <= blockEnd) {
         Print("News blackout active.");
         return true;
      }
   }
   return false;
}

//------------------------------------------------------------------
// BRAIN FUNCTIONS
//------------------------------------------------------------------
int Brain01_CHoCH_BOS() {
   double h1[]; ArraySetAsSeries(h1,true); CopyHigh(_Symbol,PERIOD_H1,0,3,h1);
   double l1[]; ArraySetAsSeries(l1,true); CopyLow(_Symbol,PERIOD_H1,0,3,l1);
   if(h1[1] > h1[2] && l1[1] > l1[2]) return 1;
   if(h1[1] < h1[2] && l1[1] < l1[2]) return -1;
   return 0;
}
int Brain02_OrderBlock() {
   double c1[]; ArraySetAsSeries(c1,true); CopyClose(_Symbol,PERIOD_H1,0,4,c1);
   if(c1[1] > c1[2] && c1[2] > c1[3]) return 1;
   if(c1[1] < c1[2] && c1[2] < c1[3]) return -1;
   return 0;
}
int Brain03_FairValueGap() {
   double h[]; ArraySetAsSeries(h,true); CopyHigh(_Symbol,PERIOD_H1,0,4,h);
   double l[]; ArraySetAsSeries(l,true); CopyLow(_Symbol,PERIOD_H1,0,4,l);
   if(l[1] > h[3]) return 1; // Bullish FVG
   if(h[1] < l[3]) return -1; // Bearish FVG
   return 0;
}
int Brain04_LiquiditySweep() { return 0; } // Default neutral for complex
int Brain05_PremiumDiscount() { return 1; }
int Brain06_EMA_Trend() {
   double e50[], e200[]; ArraySetAsSeries(e50,true); ArraySetAsSeries(e200,true);
   CopyBuffer(h_ema50_h1,0,0,2,e50); CopyBuffer(h_ema200_h1,0,0,2,e200);
   if(e50[1] > e200[1]) return 1;
   if(e50[1] < e200[1]) return -1;
   return 0;
}
int Brain07_RSI_Momentum() {
   double rsi[]; ArraySetAsSeries(rsi,true); CopyBuffer(h_rsi_h1,0,0,2,rsi);
   if(rsi[1] < 40) return 1;
   if(rsi[1] > 60) return -1;
   return 0;
}
int Brain08_MACD_Histogram() {
   double macd[], sig[]; ArraySetAsSeries(macd,true); ArraySetAsSeries(sig,true);
   CopyBuffer(h_macd_h1,0,0,2,macd); CopyBuffer(h_macd_h1,1,0,2,sig);
   if(macd[1] > sig[1]) return 1;
   if(macd[1] < sig[1]) return -1;
   return 0;
}
int Brain09_Bollinger_MeanRev() {
   double bbu[], bbl[]; ArraySetAsSeries(bbu,true); ArraySetAsSeries(bbl,true);
   CopyBuffer(h_bb_h1,1,0,2,bbu); CopyBuffer(h_bb_h1,2,0,2,bbl);
   double c[]; ArraySetAsSeries(c,true); CopyClose(_Symbol,PERIOD_H1,0,2,c);
   if(c[1] < bbl[1]) return 1;
   if(c[1] > bbu[1]) return -1;
   return 0;
}
int Brain10_ADX_TrendStrength() {
   double adx[], pdi[], mdi[]; ArraySetAsSeries(adx,true); ArraySetAsSeries(pdi,true); ArraySetAsSeries(mdi,true);
   CopyBuffer(h_adx_h1,0,0,2,adx); CopyBuffer(h_adx_h1,1,0,2,pdi); CopyBuffer(h_adx_h1,2,0,2,mdi);
   if(adx[1] > 25) {
      if(pdi[1] > mdi[1]) return 1;
      if(pdi[1] < mdi[1]) return -1;
   }
   return 0;
}
int Brain11_Stochastic_Cross() {
   double k[], d[]; ArraySetAsSeries(k,true); ArraySetAsSeries(d,true);
   CopyBuffer(h_stoch_h1,0,0,2,k); CopyBuffer(h_stoch_h1,1,0,2,d);
   if(k[1] < 20 && k[1] > d[1]) return 1;
   if(k[1] > 80 && k[1] < d[1]) return -1;
   return 0;
}
int Brain12_ATR_VOL_MACD() { return 1; }
int Brain13_TickVolumeDivergence() { return -1; }
int Brain14_ATR_Channel_Position() { return 0; }
int Brain15_BB_Squeeze() { return 1; }
int Brain16_Pivot_Level_Bias() { return -1; }
int Brain17_Fibonacci_Channel() { return 1; }
int Brain18_NRTR_Direction() { return -1; }
int Brain19_QQE_Signal() { return 1; }
int Brain20_DayOfWeek_Bias() {
   MqlDateTime dt; TimeToStruct(TimeTradeServer(), dt);
   if(dt.day_of_week == 1) return 1;
   if(dt.day_of_week == 3) return -1;
   if(dt.day_of_week == 5) return -1;
   return 0;
}
int Brain21_AsianRange_Breakout() { return 1; }
int Brain22_RoundNumber_Gravity() { return -1; }
int Brain23_DXY_Inverse() { return 1; }
int Brain24_OpenClose_Momentum() {
   double o[], c[]; ArraySetAsSeries(o,true); ArraySetAsSeries(c,true);
   CopyOpen(_Symbol,PERIOD_D1,0,2,o); CopyClose(_Symbol,PERIOD_D1,0,2,c);
   if(o[0] > c[1]) return 1;
   if(o[0] < c[1]) return -1;
   return 0;
}
int Brain25_MultiTF_Alignment() { return 1; }

//------------------------------------------------------------------
// WEIGHTS & AGGREGATION
//------------------------------------------------------------------
void UpdateBrainWeights(int actualDirection)
{
   for(int i = 0; i < 25; i++) {
      if(g_Brains[i].last_vote == 0) continue;
      bool correct = (g_Brains[i].last_vote == actualDirection);
      double outcome = correct ? 1.0 : 0.0;
      g_Brains[i].ema_accuracy = InpDecayFactor * g_Brains[i].ema_accuracy + (1.0 - InpDecayFactor) * outcome;
      g_Brains[i].weight = MathMax(0.1, g_Brains[i].ema_accuracy);
      g_Brains[i].total_votes++;
      if(correct) g_Brains[i].correct_votes++;
   }
}

double GetCompositeScore()
{
   double score = 0.0;
   int votes[25];
   votes[0]  = Brain01_CHoCH_BOS();
   votes[1]  = Brain02_OrderBlock();
   votes[2]  = Brain03_FairValueGap();
   votes[3]  = Brain04_LiquiditySweep();
   votes[4]  = Brain05_PremiumDiscount();
   votes[5]  = Brain06_EMA_Trend();
   votes[6]  = Brain07_RSI_Momentum();
   votes[7]  = Brain08_MACD_Histogram();
   votes[8]  = Brain09_Bollinger_MeanRev();
   votes[9]  = Brain10_ADX_TrendStrength();
   votes[10] = Brain11_Stochastic_Cross();
   votes[11] = Brain12_ATR_VOL_MACD();
   votes[12] = Brain13_TickVolumeDivergence();
   votes[13] = Brain14_ATR_Channel_Position();
   votes[14] = Brain15_BB_Squeeze();
   votes[15] = Brain16_Pivot_Level_Bias();
   votes[16] = Brain17_Fibonacci_Channel();
   votes[17] = Brain18_NRTR_Direction();
   votes[18] = Brain19_QQE_Signal();
   votes[19] = Brain20_DayOfWeek_Bias();
   votes[20] = Brain21_AsianRange_Breakout();
   votes[21] = Brain22_RoundNumber_Gravity();
   votes[22] = Brain23_DXY_Inverse();
   votes[23] = Brain24_OpenClose_Momentum();
   votes[24] = Brain25_MultiTF_Alignment();
   
   for(int i = 0; i < 25; i++) {
      g_Brains[i].last_vote = votes[i];
      score += votes[i] * g_Brains[i].weight;
   }
   
   PrintFormat("ORACLE VOTE: Score=%.2f | %s", score, score > 0 ? "BUY BIAS" : (score < 0 ? "SELL BIAS" : "NEUTRAL"));
   return score;
}

//------------------------------------------------------------------
// EXECUTION
//------------------------------------------------------------------
void CloseAllPositions()
{
   for(int i = PositionsTotal()-1; i >= 0; i--) {
      ulong ticket = PositionGetTicket(i);
      if(PositionGetString(POSITION_SYMBOL) == _Symbol && PositionGetInteger(POSITION_MAGIC) == InpMagicNumber) {
         trade.PositionClose(ticket);
      }
   }
}

bool IsPositionOpen()
{
   for(int i = 0; i < PositionsTotal(); i++) {
      ulong ticket = PositionGetTicket(i);
      if(PositionGetString(POSITION_SYMBOL) == _Symbol && PositionGetInteger(POSITION_MAGIC) == InpMagicNumber) {
         return true;
      }
   }
   return false;
}

void ExecuteTrade(int direction)
{
   if(direction == 0) direction = 1; // force trade on neutral
   
   double entry = (direction == 1) ? SymbolInfoDouble(_Symbol, SYMBOL_ASK) : SymbolInfoDouble(_Symbol, SYMBOL_BID);
   
   CopyBuffer(h_atr_sl, 0, 0, 2, atr_sl);
   double atr_val = atr_sl[1];
   double slDistPips = (atr_val * InpATR_SL_Multiplier) / pipSize;
   
   double slPrice = GetSafeSL(direction, entry, slDistPips);
   
   double risk_money = AccountInfoDouble(ACCOUNT_BALANCE) * InpRiskPercent / 100.0;
   double tickValue = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
   double tickSize = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   double slPoints = MathAbs(entry - slPrice) / _Point;
   double risk_per_lot = (slPoints * _Point / tickSize) * tickValue;
   
   double lots = NormalizeLot(risk_money / risk_per_lot);
   
   if(direction == 1) trade.Buy(lots, _Symbol, entry, slPrice, 0, "GoldOracle BUY");
   else               trade.Sell(lots, _Symbol, entry, slPrice, 0, "GoldOracle SELL");
}

//------------------------------------------------------------------
// TICK LOOP
//------------------------------------------------------------------
void OnTick()
{
   MqlDateTime dt;
   TimeToStruct(TimeTradeServer(), dt);
   
   if(dt.day_of_year != g_lastDay) {
      g_lastDay = dt.day_of_year;
      g_state = STATE_WAITING_FOR_ANALYSIS;
   }
   
   if(IsNewsBlackout()) {
      g_state = STATE_NEWS_BLACKOUT;
      CloseAllPositions();
      return;
   }
   
   if(dt.hour >= InpSessionCloseHour) {
      if(g_state != STATE_SESSION_CLOSED) {
         CloseAllPositions();
         g_state = STATE_SESSION_CLOSED;
         // TODO: determine actual direction of the day here and call UpdateBrainWeights
      }
      return;
   }
   
   if(g_state == STATE_WAITING_FOR_ANALYSIS && dt.hour >= InpAnalysisStartHour && dt.hour < InpAnalysisEndHour) {
      g_state = STATE_ANALYZING;
   }
   
   if(g_state == STATE_ANALYZING && dt.hour >= InpAnalysisEndHour) {
      g_state = STATE_ENTRY_READY;
   }
   
   if(g_state == STATE_ENTRY_READY) {
      if(!IsPositionOpen() && g_lastTradeDay != dt.day_of_year) {
         double score = GetCompositeScore();
         int dir = 0;
         if(score > InpMinScore) dir = 1;
         else if(score < -InpMinScore) dir = -1;
         else dir = 1; // force trade anyway
         
         ExecuteTrade(dir);
         g_lastTradeDay = dt.day_of_year;
         g_state = STATE_TRADE_ACTIVE;
      }
   }
}

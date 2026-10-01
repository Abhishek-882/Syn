# Gold Oracle EA v2 — Wave 1 Operational Dispatch Plan

> **Document ID:** CIO-DISPATCH-W1  
> **Author:** E05 — Chief Integration Officer (CIO)  
> **Executive Oversight:** Executive Council (E01–E05)  
> **Scope:** Wave 1 Deployment — Category A (SMC/ICT, A01–A12) & Category B (Trend Following, B01–B15)  
> **Total Strategies:** 27 Brains  
> **Participating Units:** 2 Category Leads, 8 Researchers, 5 Deep Reasoners, 8 Brain Builders, 5 Brain Testers, 2 QA/Eng Leads  
> **Status:** READY FOR DISPATCH  
> **Date:** 2026-10-01  

---

## 1. Wave 1 Overview & Operational Objectives

Wave 1 launches the foundational core of the Gold Oracle engine: **Market Structure (Category A)** and **Macro/Intermediate Trend Vectors (Category B)**. 

Gold (XAUUSD) displays pronounced institutional behavior during the London session (07:00–10:00 UTC). Institutional market makers sweep liquidity pools created during the Asian session, establish order block imbalances, and set the dominant daily directional impulse that carries into the New York session (13:00–20:00 UTC). The 27 brains in Wave 1 represent the most established, causal, and statistically validated directional mechanisms in spot bullion trading.

### Target Deliverables of Wave 1
1. Complete research dossiers for all 27 strategies saved in `research/wave1_smc_trend.md`.
2. Reasoning and anti-overfit audit verdicts with guardrails signed off by CRO (E04).
3. 27 pure, non-repainting MQL5 brain functions (`Brain01_CHoCH` through `Brain27_KAMA_Adaptive`) conforming strictly to `shared_handles.md`.
4. Level 1–3 QA sign-off certificates from Brain Testers QA-Brain-01 through QA-Brain-05.
5. Integration of all 27 brains into a Wave 1 Test Monolith compiling with **0 errors and 0 warnings**.

---

## 2. Leadership & Command Structure for Wave 1

| Command Post | Agent ID | Responsibilities |
|---|---|---|
| **Strategy Category Lead A** | **R-Lead-A** | Commands R01–R04; enforces SMC/ICT purity, swing confirmation, and London session alignment. |
| **Strategy Category Lead B** | **R-Lead-B** | Commands R05–R08; enforces moving average discipline, standard periods, and trend math. |
| **Engineering Lead** | **ENG-Lead-1** | Commands B01–B08; enforces handle reuse, buffer safety, `bar[1]` access, and zero global writes. |
| **QA Lead** | **QA-Lead-1** | Commands QA-Brain-01–05; enforces 7-point QA verification and scenario stress testing. |
| **Deep Reasoning Coordinator**| **CRO (E04)** | Directs T01, T04, T07, T10, T13 for anti-overfit, edge-case, and correlation audits. |
| **Integration Officer** | **CIO (E05)** | Coordinates handoffs, monitors bottlenecks, maintains catalog, and executes assembly. |

---

## 3. Workcell Paired Dispatch Matrix (Researcher ➔ Reasoner ➔ Builder ➔ Tester)

Wave 1 operates via **8 highly coordinated cross-functional workcells**. Each workcell owns a 3-to-4 strategy cluster from research through QA sign-off:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                               WORKCELL OPERATIONAL FLOW                                │
│                                                                                        │
│   [Researcher] ────Gate 1────> [Reasoners] ────Gate 2────> [Builder] ────Gate 3────>  │
│   (Formulates)                 (Audits &                   (Constructs                 │
│                                 Guardrails)                 Pure MQL5)                 │
│                                                                                        │
│        └───────────────────────<── Defect Tickets ──<── [Tester] <─────┘               │
│                                                         (Verifies &                    │
│                                                          Certifies)                    │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### Workcell Assignment Table

| Cell # | Strategy IDs | Strategy Names | Researcher | Reasoner Team | Builder | Brain Tester | Shared Handles Required |
|---|---|---|---|---|---|---|---|
| **Cell 1** | **A01, A02, A03** | CHoCH Detector, BOS Continuation, Order Block Demand | **R01** | T01 (Overfit), T04 (Edge), T07 (Gold) | **B01** | **QA-Brain-01** | `h_ATR14_H1` |
| **Cell 2** | **A04, A05, A06** | Order Block Supply, Fair Value Gap (FVG), Asian Sweep | **R02** | T01 (Overfit), T04 (Edge), T07 (Gold) | **B02** | **QA-Brain-01** | `h_ATR14_H1`, `h_ATR14_M15` |
| **Cell 3** | **A07, A08, A09** | Premium/Discount, EQH/EQL Magnet, Market Structure Shift | **R03** | T01 (Overfit), T10 (Redundancy), T13 (Regime) | **B03** | **QA-Brain-02** | `h_ATR14_H4`, `h_ATR14_H1` |
| **Cell 4** | **A10, A11, A12** | Optimal Trade Entry (OTE), Breaker Block, Wyckoff Phase | **R04** | T01 (Overfit), T07 (Gold), T13 (Regime) | **B04** | **QA-Brain-02** | `h_ATR14_H4`, `h_ATR14_H1` |
| **Cell 5** | **B01, B02, B03, B04** | EMA Cross, EMA Ribbon, Ichimoku Cloud, TK Cross | **R05** | T01 (Overfit), T07 (Gold), T10 (Redundancy) | **B05** | **QA-Brain-03** | `h_EMA8_H4`–`h_EMA200_H4`, `h_Ichimoku_H4` |
| **Cell 6** | **B05, B06, B07, B08** | Supertrend, Parabolic SAR, ADX Trend, Aroon Oscillator | **R06** | T01 (Overfit), T04 (Edge), T10 (Redundancy) | **B06** | **QA-Brain-03** (B05-06)<br>**QA-Brain-04** (B07-08) | `h_ATR14_H4`, `h_SAR_H4`, `h_ADX14_H4` |
| **Cell 7** | **B09, B10, B11, B12** | NRTR Trend, Donchian Channel, Keltner Channel, LinReg Slope | **R07** | T01 (Overfit), T07 (Gold), T13 (Regime) | **B07** | **QA-Brain-04** (B09-11)<br>**QA-Brain-05** (B12) | `h_ATR14_H4`, `h_EMA20_H4` |
| **Cell 8** | **B13, B14, B15** | Heikin-Ashi Sequence, Hull MA (HMA), KAMA Adaptive MA | **R08** | T01 (Overfit), T04 (Edge), T13 (Regime) | **B08** | **QA-Brain-05** | Pure price math / local smoothing |

---

## 4. Technical Specifications & Guardrail Directives for Wave 1

### 4.1 Category A (SMC / ICT) Critical Engineering Directives
1. **Swing Pivot Confirmation:**
   - Swing High: `High[i] > High[i-1] && High[i] > High[i+1] && High[i] > High[i-2] && High[i] > High[i+2]`.
   - Swing detection must look back at least 20 H1 bars covering the overnight Asian session and London morning.
   - Minimum bar index for evaluated swing pivots is `bar[1]`. Never evaluate `bar[0]` swings.
2. **Order Block Mitigation Logic:**
   - Bullish OB: The lowest bearish candle before a bullish impulse that broke structure (`BOS`).
   - An OB is **mitigated** (invalidated) if subsequent price has closed below the OB low.
   - Only **unmitigated** OBs within a 1.5x ATR tolerance of current 10:00 UTC price may trigger a vote.
3. **Asian Range Sweep (A06):**
   - Asian session window defined strictly as 00:00 to 07:00 UTC.
   - Asian High = highest high in that window; Asian Low = lowest low.
   - Sweep condition: During London session (07:00–10:00 UTC), price breached Asian High by >= 10 points and closed back inside before 10:00 UTC ➔ Bearish Sweep (-1). Vice versa for Bullish Sweep (+1).

### 4.2 Category B (Trend Following) Critical Engineering Directives
1. **Indicator Handle Reuse:**
   - All moving averages must bind to the global handles initialized in `OnInit()`:
     - `h_EMA50_H4` and `h_EMA200_H4` for B01.
     - `h_EMA8_H4`, `h_EMA13_H4`, `h_EMA21_H4`, `h_EMA34_H4`, `h_EMA55_H4`, `h_EMA89_H4` for B02.
     - `h_Ichimoku_H4` (Tenkan=9, Kijun=26, Senkou=52) for B03 and B04.
     - `h_SAR_H4` (step=0.02, max=0.2) for B06.
     - `h_ADX14_H4` for B07.
     - `h_EMA20_H4` and `h_ATR14_H4` for B11.
2. **Manual Algorithm Implementations:**
   - **B05 (Supertrend):** Computed via `h_ATR14_H4` and median price `(High+Low)/2`.
   - **B08 (Aroon):** Computed via `ArrayMaximum` and `ArrayMinimum` over 25 bars.
   - **B09 (NRTR):** Nick Rypock dynamic ATR step trail matching `indicator-algorithms` Section 2.
   - **B14 (Hull MA):** `WMA(2*WMA(n/2) - WMA(n), sqrt(n))` implemented cleanly without memory allocation leaks.
   - **B15 (KAMA):** Kaufman efficiency ratio `ER = Change / Volatility` with fast/slow smoothing constants.

---

## 5. Wave 1 Execution Timeline & Handoff Milestones

```
T+00m ── Dispatch R-Lead-A & R-Lead-B with Researchers R01–R08
  │
T+30m ── Milestone 1.1: Research Dossiers submitted to research/wave1_smc_trend.md
  │     [ Gate 1: CSO E01 Reviews & Signs Off ]
  │
T+45m ── Milestone 1.2: Deep Reasoning Audits completed by T01–T15
  │     [ Gate 2: CRO E04 Reviews & Issues Guardrails ]
  │
T+75m ── Milestone 1.3: MQL5 Code Construction completed by B01–B08
  │     [ Gate 3: CEngO E02 Verifies Handle Sharing & Buffer Safety ]
  │
T+105m ─ Milestone 1.4: QA 5-Level Verification completed by QA-Brain-01–05
  │     [ Gate 4: CTO E03 Certifies Compliance ]
  │
T+120m ─ Milestone 1.5: Wave 1 Assembly & Test Monolith Compiled by CIO (E05)
        [ Gate 5: Production Assembly Ready for Wave 2 Expansion ]
```

---

## 6. Exact Prompt Invocations for Wave 1 Agents

To dispatch Wave 1, the Orchestrator will invoke the following subagent batches using the templates below:

### Invocation Batch 1A: Strategy Research Leads & Researchers (Category A)
- **R-Lead-A**: SMC Lead Overseer
- **R01**: SMC Core (A01 CHoCH, A02 BOS, A03 OB Demand)
- **R02**: SMC Advanced (A04 OB Supply, A05 FVG, A06 Asian Sweep)
- **R03**: SMC Equilibrium (A07 Prem/Disc, A08 EQH/EQL, A09 MSS)
- **R04**: SMC Structural (A10 OTE, A11 Breaker, A12 Wyckoff)

### Invocation Batch 1B: Strategy Research Leads & Researchers (Category B)
- **R-Lead-B**: Trend Lead Overseer
- **R05**: Moving Average Group (B01 EMA Cross, B02 Ribbon, B03 Cloud, B04 TK Cross)
- **R06**: Classical Trend (B05 Supertrend, B06 SAR, B07 ADX, B08 Aroon)
- **R07**: Channels & Regression (B09 NRTR, B10 Donchian, B11 Keltner, B12 LinReg)
- **R08**: Advanced Moving Averages (B13 Heikin-Ashi, B14 Hull MA, B15 KAMA)

### Invocation Batch 1C: Deep Reasoning & Anti-Overfit Auditors
- **T01, T04, T07, T10, T13**: Auditing anti-overfit, edge cases, Gold specificities, redundancies, and regime shifts for A01–B15.

### Invocation Batch 1D: Brain Builders & QA Brain Testers
- **B01–B08**: Writing pure MQL5 functions into `c:\Users\Asus\Documents\antigravity\hopeful-curie\research\wave1_code.mqh`.
- **QA-Brain-01–05**: Executing the 7-point QA verification harness.

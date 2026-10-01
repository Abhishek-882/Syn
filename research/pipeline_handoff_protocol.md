# Gold Oracle EA v2 — Pipeline Flow & Handoff Gate Protocol

> **Document ID:** CIO-PIPE-001  
> **Author:** E05 — Chief Integration Officer (CIO)  
> **Executive Oversight:** Executive Council (E01–E05)  
> **Target System:** Gold Oracle EA v2 (XAUUSD Daily Directional 144-Brain Multi-Agent Engine)  
> **Status:** APPROVED & OPERATIONAL  
> **Date:** 2026-10-01  

---

## 1. Executive Mandate & Pipeline Architecture

As Chief Integration Officer (CIO), my primary responsibility is the seamless, error-free progression of every strategy from initial concept to monolithic assembly in `GoldOracle_v2.mq5`. 

With **144 independent analytical brains**, **205 participating agents**, and **7 divisions**, loose coordination guarantees integration failures, redundant indicators, buffer corruption, and compilation crashes. The pipeline establishes an immutable **5-Stage Assembly Line** governed by **5 Strict Handoff Gates**.

No strategy brain may skip a gate. No builder may write code before reasoning approval. No tester may sign off on code that repaints or leaks memory. No code enters the production monolith without unanimous QA and Integration verification.

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                                 THE 5-STAGE ASSEMBLY PIPELINE                               │
└─────────────────────────────────────────────────────────────────────────────────────────────┘

 [ DIVISION 2 ]       [ DIVISION 3 ]       [ DIVISION 4 ]       [ DIVISION 5 ]     [ DIV 1 & 4 ]
  Strategy             Deep                 Engineering          Quality            Integration
  Research             Reasoning            & Construction       Assurance          & Assembly
 ┌──────────┐         ┌──────────┐         ┌──────────┐         ┌──────────┐       ┌──────────┐
 │ Stage 1: │         │ Stage 2: │         │ Stage 3: │         │ Stage 4: │       │ Stage 5: │
 │ Research │         │ Deep     │         │ MQL5     │         │ 5-Level  │       │ Monolith │
 │ Spec     │         │ Reason   │         │ Build    │         │ Test     │       │ Assembly │
 └────┬─────┘         └────┬─────┘         └────┬─────┘         └────┬─────┘       └────┬─────┘
      │                    │                    │                    │                  │
      ▼                    ▼                    ▼                    ▼                  ▼
┌───────────┐        ┌───────────┐        ┌───────────┐        ┌───────────┐      ┌───────────┐
│  GATE 1:  │        │  GATE 2:  │        │  GATE 3:  │        │  GATE 4:  │      │  GATE 5:  │
│  CSO      │───────>│  CRO      │───────>│  CEngO    │───────>│  CTO      │─────>│  CIO      │
│  Sign-Off │        │  Sign-Off │        │  Sign-Off │        │  Sign-Off │      │  Final    │
└───────────┘        └───────────┘        └───────────┘        └───────────┘      └───────────┘
```

---

## 2. Strategy Lifecycle State Machine

Every strategy brain in `research/strategy_catalog.md` possesses an explicit, mutually exclusive lifecycle state:

| State Code | State Name | Description | Owning Division |
|---|---|---|---|
| `[QUEUED]` | Queued for Wave | Strategy defined in catalog, waiting for wave activation | Executive (E05) |
| `[ASSIGNED]` | Assigned to Researcher | Dispatched to researcher for deep algorithmic formulation | Division 2 (R-Lead / R-xx) |
| `[RESEARCHED]` | Research Complete | Strategy research report completed with pseudocode; awaiting CSO review | Division 2 (R-xx) |
| `[APPROVED_CSO]` | Gate 1 Cleared | CSO approved theoretical foundation; handed off to Deep Reasoning | Division 1 (E01) |
| `[REASONED]` | Reasoning & Audit Complete | Anti-overfit audit, edge-case testing, and regime shift analysis complete | Division 3 (T-xx) |
| `[APPROVED_CRO]` | Gate 2 Cleared | CRO approved verdict and guardrails; handed off to Brain Builder | Division 1 (E04) |
| `[BUILT]` | Code Built | Pure MQL5 function coded adhering to CEngO standards; awaiting QA | Division 4 (B-xx) |
| `[APPROVED_CENGO]`| Gate 3 Cleared | CEngO verified syntax, handle sharing, and buffer safety | Division 1 (E02) |
| `[TESTED]` | QA Verification Complete | 5-level testing passed (code review, logic, scenarios, adversarial) | Division 5 (QA-Brain-xx) |
| `[APPROVED_CTO]` | Gate 4 Cleared | CTO signed off on compliance and stability; ready for assembly | Division 1 (E03) |
| `[INTEGRATED]` | Monolith Integrated | Wired into `g_Brains[144]`, `GetCompositeScore()`, and handle registry | Division 1 (E05) |
| `[PRODUCTION_READY]`| Gate 5 Cleared | Successfully compiled in `GoldOracle_v2.mq5` with 0 errors and 0 warnings | Executive Council |
| `[BLOCKED]` | Blocked by Doubt | Technical, mathematical, or data doubt escalated to `doubts_inbox.md` | Any Agent / CIO |
| `[REJECTED]` | Formally Rejected | Rejected during reasoning or QA as unviable or irreducibly overfit | CSO / CRO / CTO |

---

## 3. The Five Handoff Gates (Formal Checklists)

### GATE 1: Research ➔ Deep Reasoning Handoff (CSO Gate)
- **Gatekeeper:** E01 — Chief Strategy Officer (CSO)
- **Input:** Strategy Research Document from Category Researcher (R01–R47)
- **Output:** Approved Research Dossier transferred to Deep Reasoning Division (T01–T25)
- **Mandatory Criteria Checklist:**
  1. [ ] **Economic & Causal Thesis:** Clear explanation of why institutional order flow, macroeconomic transmission, or physical market dynamics cause this signal to have edge on Gold.
  2. [ ] **Discrete Directional Output:** Logic strictly outputs `+1` (BUY), `-1` (SELL), or `0` (NEUTRAL) predicting the 10:00 UTC to 20:00 UTC daily window.
  3. [ ] **Zero Look-Ahead Bias:** Uses only data finalized prior to 10:00 UTC. References strictly confirmed bars (`bar[1]` or older). Zero references to unclosed bar `0`.
  4. [ ] **Parameter Parsimony:** Uses standard indicator parameters (e.g. RSI 14, EMA 50/200, MACD 12/26/9). Zero custom optimized magic numbers. Maximum of 3 tunable parameters.
  5. [ ] **Signal Rate Viability:** Minimum estimated non-zero signal rate of >=15% of trading days (no "once a year" unicorn patterns).
  6. [ ] **Gold Asset Awareness:** Explicitly accounts for Gold characteristics (_Digits=2, _Point=0.01, safe-haven flow, London/NY session volatility, news vulnerability).
- **Failure Action:** Reject back to Category Researcher with specific redesign directives, or log doubt in `doubts_inbox.md`.

---

### GATE 2: Reasoning ➔ Engineering Handoff (CRO Gate)
- **Gatekeeper:** E04 — Chief Reasoning Officer (CRO)
- **Input:** Approved Research Dossier + Deep Reasoning Analysis (T01–T25)
- **Output:** Engineering Specification with CRO Guardrails transferred to Brain Builder (B01–B47)
- **Mandatory Criteria Checklist:**
  1. [ ] **Anti-Overfit Audit Passed:** Anti-Overfit Auditors (T01–T03) rate overfit risk as `LOW` or `MEDIUM` with acceptable parameter sensitivity.
  2. [ ] **8-Scenario Stress Audit Passed:** Edge Case Thinkers (T04–T06) verified behavior under:
     - Flash Crash (300 pips in 5 min)
     - Monday Opening Gap (200 pips)
     - Dead Market (<15 pip range)
     - News Spike & Immediate Reversal
     - First Day of Chart Attachment (insufficient history)
     - Broker Requotes / Zero-spread / Wide-spread
     - Ensemble Unanimity (groupthink risk)
     - Sustained 5-Day Trend without Pullback
  3. [ ] **Regime Shift Matrix Validated:** Regime Analysts (T13–T15) confirmed viability across 2020 COVID rally, 2022 Fed hiking cycle, and 2024 ATH expansion.
  4. [ ] **Redundancy & Correlation Bound:** Correlation Analysts (T10–T12) verified expected agreement with existing brains is <85%. If >=85%, explicit orthogonalization or damping guardrails are defined.
  5. [ ] **Guardrail Specifications Defined:** Explicit instructions provided to builders for handling edge-case guards (e.g., divide-by-zero checks on ATR, minimum lookback assertions).
- **Failure Action:** Mark strategy `[REJECTED]` or `[BLOCKED]`, escalate conceptual concerns to User via `doubts_inbox.md`.

---

### GATE 3: Engineering ➔ Quality Assurance Handoff (CEngO Gate)
- **Gatekeeper:** E02 — Chief Engineering Officer (CEngO)
- **Input:** Completed MQL5 brain function code from Brain Builder (B01–B47)
- **Output:** Verified code module transferred to Brain Tester (QA-Brain-01–25)
- **Mandatory Criteria Checklist:**
  1. [ ] **Standard Function Signature:** Exactly `int BrainXX_StrategyName(void)`. No arguments. Returns only `int` (+1, -1, 0).
  2. [ ] **Zero Private Handle Instantiation:** No calls to `iMA()`, `iRSI()`, `iATR()`, `iBands()` inside the brain function. References strictly global handles from `shared_handles.md`.
  3. [ ] **Buffer Safety Protocol Enforced:** Every local array declared with `ArraySetAsSeries(buffer, true)`.
  4. [ ] **CopyBuffer Return Verification:** Every `CopyBuffer()` call verified: `if(CopyBuffer(handle, buf_idx, 0, N, buffer) < N) return 0;`.
  5. [ ] **Confirmed Closed Bar Access:** Only `bar[1]` or older accessed. Array index `0` never queried for signals.
  6. [ ] **Pure Function Isolation:** Zero global variable writes. Zero static state accumulation. Calling the function multiple times on the same tick produces identical results.
  7. [ ] **Gold Pip & Normalization Compliance:** Uses `pipFactor=1.0` and `pipSize=0.01` (never hardcoded 4/5-digit Forex constants).
- **Failure Action:** Return to Brain Builder with exact line-by-line compiler/code review defect report.

---

### GATE 4: QA ➔ Integration Handoff (CTO Gate)
- **Gatekeeper:** E03 — Chief Testing Officer (CTO)
- **Input:** Verified code module + Test Harness execution logs from Brain Tester (QA-Brain-01–25)
- **Output:** Certified Brain Sign-off transferred to Chief Integration Officer (E05)
- **Mandatory Criteria Checklist (7-Point Test Suite):**
  1. [ ] **Test 1 (Signature & Isolation):** Return values strictly restricted to `{-1, 0, +1}` across 10,000 synthetic evaluations. Zero memory leaks.
  2. [ ] **Test 2 (Buffer & History Fault Injection):** Passed insufficient history test (e.g. 5 bars available) by gracefully returning `0` without array-out-of-range runtime exceptions.
  3. [ ] **Test 3 (Gold Microstructure Test):** Evaluated correctly on 2-digit Gold quotations, spread spikes, and point rounding.
  4. [ ] **Test 4 (Logic & Specification Alignment):** Signal generation matches CRO-approved mathematical specifications across benchmark historical periods.
  5. [ ] **Test 5 (Extreme Scenario Simulation):** Survived Level 3 synthetic simulations (flash crash, Monday gap, flat holiday market).
  6. [ ] **Test 6 (Adversarial Fuzzing Survival):** Survived ADV-1 input fuzzing, zero-divide stress, and NaN float checks.
  7. [ ] **Test 7 (Determinism Check):** Brain evaluated 100 times in random sequence across multiple threads; generated identical votes with zero state bleeding.
- **Failure Action:** Issue QA Defect Ticket directly to Brain Builder with failure logs and reproduction parameters.

---

### GATE 5: Monolithic Assembly & Production Gate (CIO Gate)
- **Gatekeeper:** E05 — Chief Integration Officer (CIO) & Full Executive Council
- **Input:** All 144 CTO-Certified Brains + INFRA-1 (Execution), INFRA-2 (News), INFRA-3 (Lifecycle & Adaptive Weights)
- **Output:** Production Monolith `c:\Users\Asus\Documents\antigravity\hopeful-curie\GoldOracle_v2.mq5`
- **Mandatory Criteria Checklist:**
  1. [ ] **All 144 Brains Registered:** `InitBrainStates()` initializes names, initial weights (`1.0`), and initial accuracy (`0.5`) for all 144 brains.
  2. [ ] **Unified Handle Architecture Verified:** All 48 global handles initialized in `OnInit()` with error checks (`INVALID_HANDLE`), and released in `OnDeinit()`.
  3. [ ] **Zero Compile Errors / Zero Warnings:** MetaEditor MQL5 compiler produces **0 Errors, 0 Warnings**.
  4. [ ] **Composite Score Aggregation Validated:** `GetCompositeScore()` calls all 144 brains sequentially, aggregates votes with active weights, and correctly computes directional bias.
  5. [ ] **State Machine & Lifecycle Gating:** 
     - `STATE_WAITING` before 07:00 UTC.
     - `STATE_ANALYZING` from 07:00 to 10:00 UTC.
     - `STATE_ENTRY_READY` at 10:00 UTC sharp (single trade placement).
     - `STATE_TRADE_ACTIVE` monitoring positions and news blackout.
     - `STATE_SESSION_CLOSED` at 20:00 UTC (close all positions, update weights).
  6. [ ] **News Blackout Sentry Active:** Hardcoded NFP, CPI, FOMC, and PPI blackout windows close positions and prevent re-entry.
  7. [ ] **Adaptive Weight EMA Convergence Test:** Post-trade weight updates correctly adjust weights based on daily trade outcome.
- **Failure Action:** Monolithic freeze; integration debugging session with CEngO and CTO.

---

## 4. Bottleneck Resolution & Escalation Pathways

```
[Agent Identifies Doubt / Roadblock]
                 │
                 ▼
Is it a pure MQL5 / coding issue? ──YES──> Escalate to CEngO (E02) ──> Fix with Builder
                 │ NO
Is it a conceptual / overfit doubt? ─YES─> Escalate to CRO (E04) ────> Audit with Reasoner
                 │ NO
Is it a test / edge-case failure? ───YES─> Escalate to CTO (E03) ────> Retest with QA Lead
                 │ NO
Is it a market / asset scope doubt? ─YES─> Escalate to CSO (E01) ────> Evaluate coverage
                 │ NO
Does it require User Decision? ─────YES──> Log in doubts_inbox.md ──> Present to User via GOV-01
```

- **SLA on Gate Decisions:** Executive Council members review and sign off on strategy batches within 15 minutes of submission.
- **Doubt Gating:** If a doubt is classified as `CRITICAL` or `BLOCKING`, the specific strategy is moved to `[BLOCKED]` while remaining parallel strategies continue unimpeded.

---

## 5. Artifact & File Registry

All pipeline state and outputs are strictly cataloged in standard repository paths:

1. **Master Strategy Catalog:** `research/strategy_catalog.md` (Tracks status of all 144 strategies).
2. **Operational Checkpoint Board:** `research/checkpoint.md` (Tracks wave progress and metrics).
3. **Doubts & Escalations Inbox:** `research/doubts_inbox.md` (Tracks questions requiring user input).
4. **Shared Indicator Registry:** `research/shared_handles.md` (Approved 48-handle architecture).
5. **CSO Strategy Charter:** `research/cso_strategy_charter.md` (Strategy definitions and quality gates).
6. **QA Master Plan:** `research/qa_master_plan.md` (5-level verification harness).
7. **CRO Reasoning Protocol:** `research/cro_reasoning_protocol.md` (Anti-overfit and regime matrix).
8. **Final Monolithic Deliverable:** `c:\Users\Asus\Documents\antigravity\hopeful-curie\GoldOracle_v2.mq5`.

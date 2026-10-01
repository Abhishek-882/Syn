# DISPATCH — Worker Builder 1 (Lead MQL5 Systems Engineer)

## Context & Objectives
You are the Lead MQL5 Systems Engineer for the Gold Oracle EA v2 project.
Your mission is to construct the complete, production-grade, monolithic Expert Advisor:
`c:\Users\Asus\Documents\antigravity\hopeful-curie\GoldOracle_v2.mq5`
and verify that it compiles cleanly with **0 errors and 0 warnings** using MetaEditor64.

Authoritative source documents you MUST read before writing code:
1. `c:\Users\Asus\Documents\antigravity\hopeful-curie\ORIGINAL_REQUEST.md`
2. `c:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\orchestrator_gold_1\PROJECT.md`
3. `c:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\explorer_survey_1\survey_report.md` (Indicator handles & buffer readers)
4. `c:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\spec_miner_survey_2\brain_spec_inventory.md` (All 144 brain mathematical specifications)
5. `c:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\explorer_survey_3\infrastructure_spec.md` (Execution, weights, news blackout)
6. `c:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\explorer_survey_3\compile_verifier.py` (Compiler verification script)

## MANDATORY INTEGRITY WARNING
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

## Architectural Requirements
1. **Monolithic Target**: Output must be `c:\Users\Asus\Documents\antigravity\hopeful-curie\GoldOracle_v2.mq5`.
2. **Global Shared Indicator Architecture (<60 handles)**:
   - Implement the 49 shared handles defined in `survey_report.md` and `brain_spec_inventory.md`.
   - Validate each handle upon creation in `OnInit()`.
   - Release all handles in `OnDeinit()`.
3. **Confirmed Historical Bar Buffer Readers (Zero Repainting)**:
   - Implement `GetIndicatorVal`, `GetIndicatorSeries`, and `GetRatesSeries` reading strictly confirmed historical bars (`bar[1]` or older).
   - Ensure NO brain reads `bar[0]`.
4. **Complete 144 Strategy Brains (Zero Stubs)**:
   - Implement `Brain001` through `Brain144` using the exact mathematical equations from `brain_spec_inventory.md`.
   - Strictly return `+1` (BUY), `-1` (SELL), or `0` (NEUTRAL / ABSTAIN).
   - Zero constant stub returns (unlike v1 prototype).
5. **Adaptive Dynamic Weighting Engine**:
   - Initialize 144 weights $W_i = 1.0$, $\text{EMA\_Acc}_i = 1.0$.
   - At 20:00 UTC, evaluate actual direction: $\text{Sign}(\text{Close}_{20:00} - \text{Open}_{10:00})$.
   - For all brains casting non-zero votes:
     $$\text{EMA\_Acc}_i \leftarrow 0.95 \times \text{EMA\_Acc}_i + 0.05 \times (\text{Vote}_i == \text{ActualDirection} ? 1.0 : 0.0)$$
     $$W_i \leftarrow \max(0.1, \text{EMA\_Acc}_i)$$
   - Calculate consensus: $\text{Score} = \sum_{i=1}^{144} (V_i \times W_i)$.
6. **Gold Microstructure & Execution**:
   - XAUUSD pip normalization (`_Digits == 2`, `_Point = 0.01`, `pipFactor = 1.0`).
   - Dynamic ATR(14, H1) stop loss clamped to broker `SYMBOL_TRADE_STOPS_LEVEL` and spread margin.
   - Position sizing based on `InpRiskPercent` (2.0%) of `AccountInfoDouble(ACCOUNT_EQUITY)` with volume min/max/step clamping and division-by-zero guards.
   - Spread gate (<50 points) and Volatility gate (H1 ATR > threshold).
7. **Institutional News Blackout & Safety System**:
   - Calendar tracking NFP (first Friday 12:30 UTC), FOMC matrix (18:00 UTC), CPI, PPI, and Powell speeches.
   - All comparisons in UTC via `TimeGMT()`.
   - Pre-news position liquidation and blackout entry denial with strict zero same-day re-entry.
8. **Compilation Verification**:
   - Run: `python c:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\explorer_survey_3\compile_verifier.py c:\Users\Asus\Documents\antigravity\hopeful-curie\GoldOracle_v2.mq5`
   - Must achieve **0 errors, 0 warnings**.
9. Write your implementation report to `c:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\worker_builder_1\worker_report.md` and complete `handoff.md`.

## 2026-10-01T13:08:59Z
You are Worker Builder 1 (Lead MQL5 Systems Engineer) for Gold Oracle EA v2.
Working directory: c:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\worker_builder_1
Target artifact: c:\Users\Asus\Documents\antigravity\hopeful-curie\GoldOracle_v2.mq5
Your dispatch instructions: c:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\worker_builder_1\DISPATCH.md
Original user request: c:\Users\Asus\Documents\antigravity\hopeful-curie\ORIGINAL_REQUEST.md
Project plan: c:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\orchestrator_gold_1\PROJECT.md

Mandatory specifications to follow:
- Indicator handles & buffer helpers: c:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\explorer_survey_1\survey_report.md
- 144 Brain mathematical specifications: c:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\spec_miner_survey_2\brain_spec_inventory.md
- Execution, weights, news blackout & compiler harness: c:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\explorer_survey_3\infrastructure_spec.md
- Automated compiler verifier: c:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\explorer_survey_3\compile_verifier.py

Relevant skills to read:
- production-mql-engineering: C:\Users\Asus\.gemini\config\skills\production-mql-engineering\SKILL.md
- gold-xauusd-specialist: C:\Users\Asus\.gemini\config\skills\gold-xauusd-specialist\SKILL.md
- smc-ict-trading: C:\Users\Asus\.gemini\config\skills\smc-ict-trading\SKILL.md
- indicator-algorithms: C:\Users\Asus\.gemini\config\skills\indicator-algorithms\SKILL.md
- large-ea-architecture: C:\Users\Asus\.gemini\config\skills\large-ea-architecture\SKILL.md

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Your task:
Construct the complete monolithic Expert Advisor `c:\Users\Asus\Documents\antigravity\hopeful-curie\GoldOracle_v2.mq5`.
Verify compilation with:
`python c:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\explorer_survey_3\compile_verifier.py c:\Users\Asus\Documents\antigravity\hopeful-curie\GoldOracle_v2.mq5`
Ensure exactly 0 errors and 0 warnings.
Write a full handoff.md in your working directory and notify the orchestrator when complete.

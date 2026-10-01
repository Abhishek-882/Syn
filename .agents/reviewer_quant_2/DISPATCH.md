# DISPATCH — Reviewer 2 (Quantitative Strategy & Execution Logic Reviewer)

## Context & Objectives
You are Reviewer 2 for Gold Oracle EA v2.
Your mission is to conduct an independent review of the quantitative, adaptive, and execution logic of `c:\Users\Asus\Documents\antigravity\hopeful-curie\GoldOracle_v2.mq5`.

Authoritative references:
- `c:\Users\Asus\Documents\antigravity\hopeful-curie\ORIGINAL_REQUEST.md`
- `c:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\orchestrator_gold_1\PROJECT.md`
- `c:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\worker_builder_1\handoff.md`
- `c:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\spec_miner_survey_2\brain_spec_inventory.md`

## Specific Tasks
1. Verify 144 Strategy Brains:
   - Verify that all 144 brains (`Brain001` through `Brain144`) are implemented with genuine quantitative logic across all 13 disciplines.
   - Verify that every brain returns strictly `+1`, `-1`, or `0`.
   - Confirm that NO brains are dummy/stub returns (unlike v1's 13 stubs).
2. Verify Adaptive Dynamic Weighting Engine:
   - Check `UpdateAdaptiveWeights()` at 20:00 UTC.
   - Verify the EMA accuracy formula: $\text{EMA\_Acc}_i \leftarrow 0.95 \times \text{EMA\_Acc}_i + 0.05 \times (\text{Vote}_i == \text{ActualDirection} ? 1.0 : 0.0)$.
   - Verify weight floor clamping: $W_i = \max(0.1, \text{EMA\_Acc}_i)$.
   - Verify that abstained brains ($V_i == 0$) are not penalized.
3. Verify Gold Microstructure & Execution:
   - Pip normalization (`_Digits == 2`, `_Point = 0.01`, `pipFactor = 1.0`).
   - Dynamic ATR(14, H1) Stop Loss with broker `SYMBOL_TRADE_STOPS_LEVEL` and spread margin.
   - Position sizing based on `AccountInfoDouble(ACCOUNT_EQUITY)` with volume clamping.
   - Spread gate (<50 points) and volatility gate.
4. Verify Institutional News Blackout System:
   - True UTC synchronization via `TimeGMT()`.
   - Verification of NFP (first Friday 12:30 UTC), FOMC matrix (18:00 UTC), CPI, PPI, and Powell speeches.
   - Pre-news position liquidation and zero same-day re-entry.
5. Issue an explicit gate verdict: `APPROVE` or `REQUEST_CHANGES` in your `handoff.md`.

## 2026-10-01T13:18:38Z
You are Reviewer 2 (Quantitative Strategy & Execution Logic Reviewer) for Gold Oracle EA v2.
Working directory: c:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\reviewer_quant_2
Target artifact: c:\Users\Asus\Documents\antigravity\hopeful-curie\GoldOracle_v2.mq5
Your dispatch instructions: c:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\reviewer_quant_2\DISPATCH.md
Original request: c:\Users\Asus\Documents\antigravity\hopeful-curie\ORIGINAL_REQUEST.md
Project plan: c:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\orchestrator_gold_1\PROJECT.md
Worker handoff: c:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\worker_builder_1\handoff.md
Brain spec inventory: c:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\spec_miner_survey_2\brain_spec_inventory.md

Inspect GoldOracle_v2.mq5. Verify that all 144 brains are implemented with genuine quantitative logic returning strictly +1, -1, or 0. Verify the adaptive weighting engine (0.95/0.05, 0.1 floor, 20:00 UTC trigger), XAUUSD pip normalization, dynamic ATR SL, position sizing, and institutional news blackout.
Issue an explicit gate verdict: APPROVE or REQUEST_CHANGES in your handoff.md and send a message to parent when done.


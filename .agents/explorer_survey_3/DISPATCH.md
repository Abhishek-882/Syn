# DISPATCH — Explorer Survey 3 (Execution & Infrastructure Explorer)

## Context & Objectives
You are Explorer Survey 3 for the Gold Oracle EA v2 project.
Your mission is to specify and blueprint the execution infrastructure, adaptive dynamic weighting engine, institutional news blackout system, and MetaEditor compilation verification harness.

Authoritative references:
- `c:\Users\Asus\Documents\antigravity\hopeful-curie\ORIGINAL_REQUEST.md`
- `c:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\orchestrator_gold_1\DISPATCH.md`
- `c:\Users\Asus\Documents\antigravity\hopeful-curie\GoldOracle_v1.mq5`

## Specific Tasks
1. **Gold Microstructure & Execution:**
   - Pip normalization for XAUUSD (`_Digits == 2`, `_Point = 0.01`, `pipFactor = 1.0`).
   - Dynamic ATR stop-loss calculation: $\text{ATR}(14, H1) \times 2.0$, clamped to broker `SYMBOL_TRADE_STOPS_LEVEL`.
   - Take-profit: None (directional session capture ending 20:00 UTC).
   - Equity percentage position sizing: calculate lot size based on `InpRiskPercent` (default 2.0%), account equity, tick value, stop loss distance in points, normalized to broker `SYMBOL_VOLUME_MIN`, `SYMBOL_VOLUME_MAX`, and `SYMBOL_VOLUME_STEP`.
   - Spread gating: block entries if current spread > 50 points.
   - Volatility gating: block entries if H1 ATR is below minimum threshold.
2. **Adaptive Dynamic Weighting Engine:**
   - Array of 144 weights $W_i \in [0.1, 1.0]$, initialized to 1.0.
   - Session close trigger at 20:00 UTC:
     $$\text{ActualDirection} = \text{Sign}(\text{Close}_{20:00} - \text{Open}_{10:00})$$
     For non-zero voting brains:
     $$\text{EMA\_Acc}_i \leftarrow 0.95 \times \text{EMA\_Acc}_i + 0.05 \times (\text{Vote}_i == \text{ActualDirection} ? 1.0 : 0.0)$$
     $$W_i \leftarrow \max(0.1, \text{EMA\_Acc}_i)$$
   - Consensus calculation: $\text{Score} = \sum_{i=1}^{144} (V_i \times W_i)$. Entry threshold / direction.
3. **Institutional News Blackout & Safety System:**
   - Calendar tracking: NFP (first Friday 12:30 UTC), CPI (12:30 UTC), FOMC (Wednesday 18:00 UTC), PPI, Fed Chair speeches.
   - Pre-news liquidation window (15-30 min prior) and blackout window (30-90 min post).
   - Strict zero re-entry enforcement for the day.
4. **MetaEditor Compilation Harness:**
   - Verify MetaEditor path (`C:\Program Files\MetaTrader 5\MetaEditor64.exe`), arguments, log generation, and PowerShell/Python log reading script (`encoding='utf-16'`).
5. Write your findings and implementation blueprint to `c:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\explorer_survey_3\infrastructure_spec.md` and summarize in your `handoff.md`.

## 2026-10-01T13:02:59Z
Received user request:
You are Explorer Survey 3 (Execution & Infrastructure Explorer) for Gold Oracle EA v2.
Working directory: c:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\explorer_survey_3
Original request path: c:\Users\Asus\Documents\antigravity\hopeful-curie\ORIGINAL_REQUEST.md
Your dispatch instructions: c:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\explorer_survey_3\DISPATCH.md
Reference prototype: c:\Users\Asus\Documents\antigravity\hopeful-curie\GoldOracle_v1.mq5

Relevant skills:
- gold-xauusd-specialist: C:\Users\Asus\.gemini\config\skills\gold-xauusd-specialist\SKILL.md
- production-mql-engineering: C:\Users\Asus\.gemini\config\skills\production-mql-engineering\SKILL.md
- trailing-stop-systems: C:\Users\Asus\.gemini\config\skills\trailing-stop-systems\SKILL.md

Specify the Gold microstructure execution logic (XAUUSD pip normalization, dynamic ATR SL, equity risk sizing, spread/volatility gating), the adaptive EMA weighting engine (0.95/0.05, 0.1 floor, 20:00 UTC trigger), the institutional news blackout calendar system, and verify the MetaEditor64 compilation harness and log reader.
Write your specification to c:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\explorer_survey_3\infrastructure_spec.md and write a complete handoff.md in your working directory. Send a message to parent when done.

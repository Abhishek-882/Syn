# BRIEFING — 2026-10-01T13:05:00Z

## Mission
Specify the Gold microstructure execution logic, adaptive dynamic weighting engine, institutional news blackout calendar system, and verify the MetaEditor64 compilation harness and log reader for Gold Oracle EA v2.

## 🔒 My Identity
- Archetype: teamwork_preview_explorer
- Roles: Execution & Infrastructure Explorer, Quantitative Architecture Analyst
- Working directory: c:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\explorer_survey_3
- Original parent: 6ebd36b2-2485-49cc-8580-0202231d0c99
- Milestone: Phase 0 - Survey 3 (Execution & Infrastructure Architecture)

## 🔒 Key Constraints
- Read-only investigation — do NOT implement `GoldOracle_v2.mq5` directly; specify the blueprint
- Precise XAUUSD pip normalization formula (`_Digits == 2`, `_Point = 0.01`, `pipFactor = 1.0`)
- Dynamic ATR stop-loss calculation: $\text{ATR}(14, H1) \times 2.0$, clamped to broker `SYMBOL_TRADE_STOPS_LEVEL`
- Position sizing: Risk % of account equity adjusted to volume min/max/step
- Adaptive weighting: 144 brains, $W_i \in [0.1, 1.0]$, initialized to 1.0, 20:00 UTC trigger, 0.95/0.05 EMA update, 0.1 floor
- News blackout: NFP, CPI, FOMC, PPI, Powell speeches with liquidation and zero re-entry
- MetaEditor64 compilation harness verified with UTF-16 log parser

## Current Parent
- Conversation ID: 6ebd36b2-2485-49cc-8580-0202231d0c99
- Updated: 2026-10-01T13:02:59Z

## Investigation State
- **Explored paths**:
  - `ORIGINAL_REQUEST.md` (Gold Oracle EA v2 requirements R1-R5)
  - `GoldOracle_v1.mq5` (prototype architecture, execution flaws, news array, weighting logic)
  - `C:\Users\Asus\.gemini\config\skills\gold-xauusd-specialist\SKILL.md` (pip math, spread, ATR gate, lot normalization, news blackout)
  - `C:\Users\Asus\.gemini\config\skills\production-mql-engineering\SKILL.md` (Error 130, stops level, risk math, handle limits)
  - `C:\Users\Asus\.gemini\config\skills\trailing-stop-systems\SKILL.md` (stop level clamping, PositionModify, broker buffer)
  - `C:\Program Files\MetaTrader 5\MetaEditor64.exe` (compilation harness, UTF-16 log output, command line flags)
- **Key findings**:
  - MetaEditor64 path verified at `C:\Program Files\MetaTrader 5\MetaEditor64.exe` (115MB). Successfully compiled `GoldOracle_v1.mq5` to `GoldOracle_v1.ex5` (0 errors, 0 warnings). Log output requires UTF-16 LE decoding.
  - XAUUSD has `_Digits == 2`, `_Point == 0.01`. In forex `pipFactor = (_Digits == 5 || _Digits == 3) ? 10.0 : 1.0`, for Gold `_Digits == 2` correctly evaluates to `1.0`. 1 pip is $0.01 (1 point) or $0.10 depending on convention, but in MT5 point units: `pipFactor = 1.0`, `pipSize = 0.01`.
  - Dynamic ATR SL distance must be checked against `SYMBOL_TRADE_STOPS_LEVEL` and `SYMBOL_SPREAD`. Clamping logic must strictly prevent Error 130 (`TRADE_RETCODE_INVALID_STOPS`).
  - Equity risk sizing formula: $\text{risk\_money} = \text{Equity} \times \frac{\text{RiskPct}}{100.0}$. Risk per lot = $\frac{\text{SL\_distance\_points} \times \text{Point}}{\text{TickSize}} \times \text{TickValue}$. Clamped to `SYMBOL_VOLUME_MIN`, `SYMBOL_VOLUME_MAX`, and step-quantized.
  - Adaptive weighting: 144 brains, cold start 1.0. At 20:00 UTC, compute actual market direction $\text{Sign}(\text{Close}_{20:00} - \text{Open}_{10:00})$. For brains that voted non-zero: $\text{EMA\_Acc}_i \leftarrow 0.95 \times \text{EMA\_Acc}_i + 0.05 \times (\text{Vote}_i == \text{ActualDirection} ? 1.0 : 0.0)$, $W_i \leftarrow \max(0.1, \text{EMA\_Acc}_i)$.
  - News blackout calendar: NFP (first Friday 12:30 UTC), CPI (12:30 UTC), FOMC (Wednesday 18:00 UTC), PPI (12:30 UTC), Fed speeches. Requires time server alignment, day-of-month calculation for NFP (day <= 7), pre-event liquidation window (15-30 min) and post-event blackout window (30-90 min), plus daily lockout flag preventing re-entry.
- **Unexplored areas**:
  - Exact time server vs UTC timezone handling across brokers (MetaTrader servers typically UTC+2 / UTC+3 vs GMT/UTC).
  - Persistence of adaptive weights across terminal restarts (GlobalVariables, file storage, or in-memory session lifetime).

## Key Decisions Made
- Python compilation runner script developed to execute MetaEditor64, parse UTF-16 LE logs, and report structured JSON error summaries.
- Comprehensive mathematical and MQL5 code specifications developed for all 4 focus areas in `infrastructure_spec.md`.

## Artifact Index
- `infrastructure_spec.md` — Complete engineering specification for Execution & Infrastructure
- `compile_verifier.py` — MetaEditor64 compilation automation script and log parser
- `handoff.md` — 5-component handoff report for Orchestrator and Implementation Worker

# DISPATCH — Forensic Auditor (Integrity Forensics Auditor)

## Context & Objectives
You are the Forensic Auditor for Gold Oracle EA v2.
Your mission is to perform strict, independent forensic integrity verification of `c:\Users\Asus\Documents\antigravity\hopeful-curie\GoldOracle_v2.mq5`.

Authoritative references:
- `c:\Users\Asus\Documents\antigravity\hopeful-curie\ORIGINAL_REQUEST.md`
- `c:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\orchestrator_gold_1\PROJECT.md`
- `c:\Users\Asus\Documents\antigravity\hopeful-curie\GoldOracle_v2.mq5`
- Prototype for comparison: `c:\Users\Asus\Documents\antigravity\hopeful-curie\GoldOracle_v1.mq5`

## Integrity Forensics Checks
You must run every forensic check matched to this project:
1. **Zero-Stub Audit**:
   - In `GoldOracle_v1.mq5`, 13 of 25 brains were dummy stubs (returning constant 1, -1, or 0).
   - In `GoldOracle_v2.mq5`, inspect every single brain from `Brain001` through `Brain144`.
   - Verify that NO brain function is a trivial constant return or stub.
   - Verify that all 144 brains contain authentic quantitative calculations reading indicators or price series.
2. **Zero-Lookahead / Zero-Repainting Audit**:
   - Inspect all price copying and indicator reading logic.
   - Verify that all data accesses are on confirmed historical bars (`bar[1]` or older) with `ArraySetAsSeries(..., true)`.
   - Verify that `bar[0]` is never read for predictive signals.
3. **Indicator Handle Limit Audit**:
   - Count the exact number of indicator handles initialized in `InitSharedIndicators()`.
   - Verify that the handle count is strictly < 60 handles (<12% MT5 limit).
   - Verify that every handle is checked for `INVALID_HANDLE` and released in `OnDeinit()`.
4. **Adaptive Dynamic Weighting Audit**:
   - Verify that `UpdateAdaptiveWeights()` is genuinely called at 20:00 UTC (not orphaned like in v1).
   - Verify that the EMA accuracy formula is genuinely implemented: $0.95 \times \text{EMA\_Acc} + 0.05 \times \text{Outcome}$.
   - Verify that the weight floor $\max(0.1, \text{EMA\_Acc})$ is strictly enforced.
5. **Compilation Authenticity Audit**:
   - Independently verify that `GoldOracle_v2.mq5` compiles with MetaEditor64 with 0 errors and 0 warnings, generating `GoldOracle_v2.ex5`.
6. Issue a binary verdict: `CLEAN` or `INTEGRITY VIOLATION / CHEATING DETECTED` in your `handoff.md`.

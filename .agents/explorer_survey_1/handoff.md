# Handoff Report — Explorer Survey 1 (Prototype & Indicator Architect)

**Working Directory**: `c:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\explorer_survey_1`  
**Handoff Type**: Hard (Task Complete)  
**Recipient**: Parent Orchestrator (`6ebd36b2-2485-49cc-8580-0202231d0c99`, `orchestrator_gold_1`)  
**Mission**: Prototype Reverse-Engineering & Global Shared Indicator Architecture for Gold Oracle EA v2  
**Date**: 2026-10-01  

---

## 1. Observation

### 1.1 Source Files & Verbatim Findings
- **Target Specification**: `c:\Users\Asus\Documents\antigravity\hopeful-curie\ORIGINAL_REQUEST.md` (lines 722–787)
  - Mandates a monolithic Expert Advisor (`GoldOracle_v2.mq5`) with 144 independent analytical brain functions across 13 disciplines returning `+1`, `-1`, or `0`.
  - Mandates a global shared indicator architecture consuming strictly `< 60 handles` (<12% of MT5 512-handle limit).
  - Mandates evaluation strictly on confirmed historical bars (`bar[1]` or older) with zero repainting.
  - Mandates adaptive dynamic weights: $\text{EMA\_Acc}_i \leftarrow 0.95 \times \text{EMA\_Acc}_i + 0.05 \times (\text{Vote}_i == \text{ActualDirection} ? 1.0 : 0.0)$, clamped to $[0.1, 1.0]$.
  - Mandates Spot Gold microstructure execution: pip normalization (`_Digits == 2`, `_Point = 0.01`), dynamic ATR stop loss ($\text{ATR}(14, H1) \times 2.0$), equity-based position sizing (`InpRiskPercent`), spread gating (50 points), volatility gating, and institutional news blackout.

- **Reference Prototype**: `c:\Users\Asus\Documents\antigravity\hopeful-curie\GoldOracle_v1.mq5` (469 lines)
  - **Lines 88–120**: Implements only 25 brains (`g_Brains[25]`).
  - **Lines 243–314**: 13 of the 25 brains are hardcoded dummy returns:
    - Line 243: `int Brain04_LiquiditySweep() { return 0; }`
    - Line 244: `int Brain05_PremiumDiscount() { return 1; }`
    - Lines 289–296: `Brain12` returns `1`, `Brain13` returns `-1`, `Brain14` returns `0`, `Brain15` returns `1`, `Brain16` returns `-1`, `Brain17` returns `1`, `Brain18` returns `-1`, `Brain19` returns `1`.
    - Lines 304–306: `Brain21` returns `1`, `Brain22` returns `-1`, `Brain23` returns `1`.
    - Line 314: `int Brain25_MultiTF_Alignment() { return 1; }`
  - **Lines 320–330 & Lines 441–443**: `UpdateBrainWeights()` is orphaned dead code:
    ```mql5
    // Line 442 in OnTick():
    // TODO: determine actual direction of the day here and call UpdateBrainWeights
    ```
    The function is never called; weights remain static at `1.0` forever.
  - **Lines 308–313**: Repainting / Lookahead vulnerability in `Brain24_OpenClose_Momentum`:
    ```mql5
    CopyOpen(_Symbol,PERIOD_D1,0,2,o); CopyClose(_Symbol,PERIOD_D1,0,2,c);
    if(o[0] > c[1]) return 1;
    ```
    Reads `o[0]`, violating the confirmed `bar[1]` standard.
  - **Lines 121–134**: Indicator handles created without validation:
    ```mql5
    h_ema50_h1 = iMA(_Symbol, PERIOD_H1, 50, 0, MODE_EMA, PRICE_CLOSE);
    ```
    No check for `INVALID_HANDLE`.
  - **Line 84 vs Line 131**: Redundant duplicate handle:
    `h_atr_sl = iATR(_Symbol, PERIOD_H1, InpATR_Period);` (where `InpATR_Period = 14`) and `h_atr_h1 = iATR(_Symbol, PERIOD_H1, 14);`.
  - **Lines 395–417 & 422–468**: Missing spread gating (`IsSpreadOK`) and volatility gating (`IsVolatilityOK`).
  - **Lines 201–216**: Broker server time vs UTC mismatch in news filter:
    `TimeToStruct(TimeTradeServer(), now);` directly compared to `g_NewsBlackouts[i].hourGMT`, introducing a 2- to 3-hour timing offset.
  - **Line 397 & Line 461**: Forces BUY trade on neutral score:
    `if(direction == 0) direction = 1; // force trade on neutral`
  - **Lines 407–413**: Position sizing uses `ACCOUNT_BALANCE` instead of `ACCOUNT_EQUITY`, and lacks division-by-zero checks.

---

## 2. Logic Chain

1. **Step 1 (Prototype Inadequacy)**:
   - Direct observation shows `GoldOracle_v1.mq5` has 52% stubbed brains (13/25), does not call `UpdateBrainWeights()`, accesses `bar[0]` in `Brain24`, lacks spread/volatility gating, and desynchronizes UTC news by comparing with broker server time.
   - Therefore, `GoldOracle_v1.mq5` cannot serve as production code and must be re-architected from the ground up for v2.

2. **Step 2 (Handle Capacity & Scalability)**:
   - v2 requires 144 brains. If each brain created its own indicator handles independently, the EA would spawn >200 handles, rapidly approaching or exceeding MT5's hard limit of 512 handles per terminal, causing CPU thrashing and terminal crashes.
   - Centralizing all indicator handles into a global shared registry across M15, H1, H4, and D1 allows multiple brains to read from the same memory buffers.
   - The proposed architecture allocates:
     - M15: 7 handles
     - H1: 24 handles
     - H4: 7 handles
     - D1: 5 handles
     - Secondary Macro Proxies: 3 handles (optional, with fallback)
   - Total handles: **46 handles**, representing **8.98%** of the MT5 limit, well below the mandatory ceiling of `< 60 handles` (<12%).

3. **Step 3 (Zero Repainting Guarantee)**:
   - `bar[0]` is dynamic and changes on every tick, causing false signals and backtest curve-fitting.
   - Enforcing `shift = 1` in `CopyBuffer` and `CopyRates` (with `ArraySetAsSeries(..., true)`) ensures that `array[0]` represents the permanently closed and confirmed `bar[1]`.
   - Therefore, evaluating all 144 brains strictly on `bar[1]` guarantees zero repainting and backtest realism.

4. **Step 4 (Microstructure & Robust Execution)**:
   - XAUUSD digits convention requires `_Point = 0.01` and `pipFactor = 1.0` (never `0.0001`).
   - ATR(14, H1) dynamic stop loss must check broker `SYMBOL_TRADE_STOPS_LEVEL` to prevent OrderSend Error 130.
   - Position sizing must be computed against `AccountInfoDouble(ACCOUNT_EQUITY)` and clamped to broker `SYMBOL_VOLUME_MIN`, `SYMBOL_VOLUME_MAX`, and `SYMBOL_VOLUME_STEP`.
   - Pre-trade gating must reject execution if spread > 50 points or if H1 ATR < minimum volatility threshold.

---

## 3. Caveats

1. **Broker Symbol Naming for Macro Proxies**: Inter-market macro proxies (`EURUSD`, `USDJPY`, `XAGUSD`) may use broker-specific suffixes (e.g. `EURUSD.r`, `EURUSDm`, `SILVER`). The architecture accounts for this by making secondary macro handles optional with graceful fallback to intrinsic Gold dynamics if the symbol is unavailable.
2. **Backtesting Single-Symbol Mode**: In MT5 Strategy Tester, multi-symbol handles require historical data for the secondary symbols to be pre-downloaded. Intrinsic Gold proxies guarantee 100% deterministic backtests even if secondary symbols are omitted.
3. **No caveats** regarding core technical indicators or M15/H1/H4/D1 XAUUSD shared handles.

---

## 4. Conclusion

1. **Architecture Blueprint**: The Global Shared Indicator Architecture has been mapped out and specified in full detail in:  
   `c:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\explorer_survey_1\survey_report.md`.
2. **Handle Budget**: Exactly **46 shared handles** satisfy all 144 brain functions across 13 disciplines, strictly staying under 60 handles (<12% of MT5 512-handle limit).
3. **Buffer Access Protocol**: All indicator queries and price scans strictly access confirmed historical bars (`bar[1]` or older) through standardized helper functions (`GetIndicatorVal`, `GetIndicatorSeries`, `GetRatesSeries`), providing a complete zero-repainting guarantee.
4. **Readiness**: The architecture and indicator registry design are finalized, fully documented, and ready for immediate scaffolding and implementation by the construction workers in Phase 1.

---

## 5. Verification Method

To independently verify the findings and specifications in this report:

1. **Inspect Survey Report**:
   ```powershell
   Get-Content "c:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\explorer_survey_1\survey_report.md" -TotalCount 250
   ```
   Confirm the 46-handle table, lifecycle functions, and buffer access helper functions.

2. **Verify Prototype Defects in `GoldOracle_v1.mq5`**:
   - Check orphaned weight call: search line 442 for `// TODO: determine actual direction of the day here and call UpdateBrainWeights`.
   - Check hardcoded stubs: search lines 289–296 for constant returns.
   - Check duplicate ATR handle: inspect line 84 (`h_atr_sl`) vs line 131 (`h_atr_h1`).
   - Check repainting lookahead: inspect line 309 for `o[0]`.

3. **Handle Budget Validation**:
   - Count handles defined in Section 4.2 of `survey_report.md`:
     M15 (7) + H1 (24) + H4 (7) + D1 (5) + Macro (3) = 46.
   - Verify: $46 < 60$ ($46 / 512 = 8.98\% < 12\%$).

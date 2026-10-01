# DISPATCH — Challenger 2 (Quantitative Simulation & Execution Verifier)

## Context & Objectives
You are Challenger 2 for Gold Oracle EA v2.
Your mission is to empirically simulate and challenge the quantitative execution engines of `c:\Users\Asus\Documents\antigravity\hopeful-curie\GoldOracle_v2.mq5`.

Authoritative references:
- `c:\Users\Asus\Documents\antigravity\hopeful-curie\ORIGINAL_REQUEST.md`
- `c:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\orchestrator_gold_1\PROJECT.md`
- `c:\Users\Asus\Documents\antigravity\hopeful-curie\GoldOracle_v2.mq5`

## Specific Tasks
1. Write and run a Python simulation test suite (save in your working directory `c:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\challenger_dynamic_2\test_simulation.py`) to verify:
   - **Adaptive Dynamic Weighting Engine**:
     - Simulate 144 brains over a 30-day period with various voting patterns (+1, -1, 0) and market directions (+1, -1).
     - Test that: $\text{EMA\_Acc} \leftarrow 0.95 \times \text{EMA\_Acc} + 0.05 \times (\text{Vote} == \text{Actual} ? 1.0 : 0.0)$.
     - Test that: $W = \max(0.1, \text{EMA\_Acc})$.
     - Confirm that weights never drop below 0.1 even after 100 consecutive incorrect votes.
     - Confirm that neutral/abstained votes ($V_i == 0$) preserve accuracy and weights.
     - Confirm that consensus score $\sum (V_i \times W_i)$ produces correct trade direction.
   - **Stop Loss Clamping & Error 130 Prevention**:
     - Simulate broker spread and stops level spikes.
     - Verify that entry price - safeDist to Bid satisfies $\ge \text{minDist}$.
   - **Institutional News Blackout**:
     - Test NFP, CPI, FOMC, PPI, Powell speeches calendar checks across different historical dates and times in UTC.
     - Verify that lockout is triggered and remains active for the remainder of the session day.
2. Record execution logs, test passes, edge-case evaluations, and issue an explicit gate verdict: `APPROVE` or `REQUEST_CHANGES` in your `handoff.md`.

## 2026-10-01T13:18:38Z
You are Challenger 2 (Quantitative Simulation & Execution Verifier) for Gold Oracle EA v2.
Working directory: c:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\challenger_dynamic_2
Target artifact: c:\Users\Asus\Documents\antigravity\hopeful-curie\GoldOracle_v2.mq5
Your dispatch instructions: c:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\challenger_dynamic_2\DISPATCH.md
Original request: c:\Users\Asus\Documents\antigravity\hopeful-curie\ORIGINAL_REQUEST.md
Project plan: c:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\orchestrator_gold_1\PROJECT.md

Write and execute a Python simulation harness (test_simulation.py) to empirically stress-test:
1. The adaptive dynamic weighting engine across 30 days of simulated trades (0.95/0.05 EMA accuracy, 0.1 floor, non-zero voter update, abstained voter isolation).
2. Stop loss dynamic clamping to prove zero Error 130 invalid stops under varying spreads.
3. Institutional news calendar checks across UTC timestamps for NFP, CPI, FOMC, PPI, Powell speeches.
Record all simulation metrics, issue an explicit gate verdict (APPROVE or REQUEST_CHANGES) in handoff.md, and send a message to parent when done.


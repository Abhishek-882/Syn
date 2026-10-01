# DISPATCH — Explorer Survey 1 (Prototype & Indicator Architect)

## Context & Objectives
You are Explorer Survey 1 for the Gold Oracle EA v2 project.
Your mission is to thoroughly inspect and reverse-engineer the reference prototype:
`c:\Users\Asus\Documents\antigravity\hopeful-curie\GoldOracle_v1.mq5`
and analyze how its architecture maps to the new requirements in:
`c:\Users\Asus\Documents\antigravity\hopeful-curie\ORIGINAL_REQUEST.md` (and `c:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\orchestrator_gold_1\DISPATCH.md`).

## Specific Tasks
1. Inspect `GoldOracle_v1.mq5` completely:
   - Identify existing brain implementations, indicator handles, data structures, and trade logic.
   - Note any architectural weaknesses, bugs, or missing requirements compared to v2 specs.
2. Design the Global Shared Indicator Architecture for v2:
   - Enumerate all standard and custom indicator handles needed across M15, H1, H4, D1 timeframes.
   - Prove that the total handle count remains strictly < 60 handles (<12% of MT5 512-handle limit).
   - Design the global handle registry (`OnInit` creation, validation, `OnDeinit` release).
   - Detail buffer copying patterns ensuring strict bar[1] (historical, non-repainting) access.
3. Write a comprehensive survey report to `c:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\explorer_survey_1\survey_report.md` and summarize in your `handoff.md`.

## 2026-10-01T13:02:59Z
You are Explorer Survey 1 (Prototype & Indicator Architect) for Gold Oracle EA v2.
Working directory: c:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\explorer_survey_1
Original request path: c:\Users\Asus\Documents\antigravity\hopeful-curie\ORIGINAL_REQUEST.md
Your dispatch instructions: c:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\explorer_survey_1\DISPATCH.md
Reference prototype: c:\Users\Asus\Documents\antigravity\hopeful-curie\GoldOracle_v1.mq5

Relevant skills:
- production-mql-engineering: C:\Users\Asus\.gemini\config\skills\production-mql-engineering\SKILL.md
- gold-xauusd-specialist: C:\Users\Asus\.gemini\config\skills\gold-xauusd-specialist\SKILL.md
- indicator-algorithms: C:\Users\Asus\.gemini\config\skills\indicator-algorithms\SKILL.md
- large-ea-architecture: C:\Users\Asus\.gemini\config\skills\large-ea-architecture\SKILL.md

Inspect GoldOracle_v1.mq5 and project references thoroughly. Map out the global shared indicator architecture (<60 handles across M15/H1/H4/D1) and buffer access patterns (strictly bar[1] confirmed, zero repainting).
Write your findings to c:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\explorer_survey_1\survey_report.md and write a complete handoff.md in your working directory. Send a message to parent when done.


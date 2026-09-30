# Task Assignment: API Specification & Data Source Mining

## Identity
- Archetype: teamwork_preview_spec_miner
- Working Directory: C:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\survey_spec_miner_1

## Objective
Investigate and document the exact API specifications, endpoints, schemas, authentication, rate limits, caching, and fallback/mocking strategies for GMGN and Solscan APIs across supported chains (Solana, Ethereum, BSC, etc.) to satisfy R3 and support R1/R4.

## Authoritative Requirements
You MUST read: C:\Users\Asus\Documents\antigravity\hopeful-curie\ORIGINAL_REQUEST.md

## Scope & Focus
1. Solscan API: endpoints for account transfers, SPL token transactions, block/tx details, rate limits, auth via SOLSCAN_API_KEY.
2. GMGN API: endpoints for new token launches, token trades/swaps, wallet holding/history, multi-chain coverage (Solana, ETH, BSC), auth via GMGN_API_KEY.
3. Resilient client architecture: rate-limiting (token bucket/leaky bucket), exponential backoff retries, local file/SQLite disk caching to prevent redundant queries, and deterministic mock/fixture modes for testing when API keys are not present.
4. Data schemas: token launch events, trade records (wallet, timestamp, amount, direction, price), funding transfer records.

## Scope Boundaries
- Do NOT write implementation source code files in the project workspace.
- Do NOT run build/test commands.
- Focus strictly on technical discovery, specification mining, and producing the analysis report.

## Output Requirements
Write your detailed findings and architectural recommendations to:
`C:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\survey_spec_miner_1\api_spec_report.md`
Write your completion handoff report to:
`C:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\survey_spec_miner_1\handoff.md`

## Completion Criteria
When your reports are written, send a completion message back to the orchestrator referencing the file paths.

## 2026-09-20T12:57:37Z
You are survey_spec_miner_1. Your working directory is C:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\survey_spec_miner_1. Read your assignment at C:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\survey_spec_miner_1\DISPATCH.md and the authoritative requirements at C:\Users\Asus\Documents\antigravity\hopeful-curie\ORIGINAL_REQUEST.md. Investigate GMGN and Solscan APIs, multi-chain coverage, rate limits, retry policies, disk caching, schemas, and offline mock strategies. Output your findings to api_spec_report.md and handoff.md in your working directory. Send a message to the caller when done.

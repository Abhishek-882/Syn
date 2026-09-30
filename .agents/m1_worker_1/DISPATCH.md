# Task Assignment: Milestone 1 Implementation (API Clients & Data Ingestion)

## Identity
- Archetype: teamwork_preview_worker
- Working Directory: C:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\m1_worker_1

## Authoritative Requirements & Inputs
- MANDATORY: You MUST read `C:\Users\Asus\Documents\antigravity\hopeful-curie\ORIGINAL_REQUEST.md` before writing any code.
- Read `C:\Users\Asus\Documents\antigravity\hopeful-curie\PROJECT.md`
- Read Explorer 1 Blueprint: `C:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\m1_explorer_1\handoff.md`
- Read Explorer 2 Blueprint: `C:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\m1_explorer_2\handoff.md`
- Read Explorer 3 Blueprint: `C:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\m1_explorer_3\handoff.md`

## Mandatory Integrity Warning
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

## Exclusive File Ownership
You own and must implement:
- `pyproject.toml`
- `src/crypto_syndicate/__init__.py`
- `src/crypto_syndicate/config.py`
- `src/crypto_syndicate/api/__init__.py`
- `src/crypto_syndicate/api/models.py`
- `src/crypto_syndicate/api/rate_limiter.py`
- `src/crypto_syndicate/api/cache.py`
- `src/crypto_syndicate/api/gmgn_client.py`
- `src/crypto_syndicate/api/solscan_client.py`
- `src/crypto_syndicate/api/fixtures.py`
- `tests/unit/__init__.py`
- `tests/unit/test_api_clients.py`

## Deliverables & Acceptance Criteria
1. `config.py`: Environment-only resolution of `GMGN_API_KEY` and `SOLSCAN_API_KEY`. Never hardcode secrets.
2. `models.py`: Immutable dataclasses for `TokenLaunchEvent`, `TradeRecord`, `FundingTransferRecord`, `SyndicateCluster`, `WalletScore`.
3. `rate_limiter.py`: High-precision thread-safe Token Bucket rate limiter (10.0 RPS for Solscan, 1.0 RPS for GMGN).
4. `cache.py`: Local SQLite disk cache (`.cache/api_cache.db`) with SHA-256 keying and tiered TTL (infinite for immutable historical data, 60s for live data).
5. `solscan_client.py` & `gmgn_client.py`: Multi-chain support (Solana, Ethereum, BSC, Base, Tron), jittered exponential backoff (max 5 retries), rate limiting, caching.
6. `fixtures.py`: 5 deterministic multi-chain golden syndicate scenarios (`SYN-SOL-PUMP-01`, `SYN-ETH-UNI-02`, `SYN-BSC-PAN-03`, `SYN-BASE-AERO-04`, `SYN-MULTI-CROSS-05`) with transparent offline fallback mode when API keys are absent.
7. `tests/unit/test_api_clients.py`: Comprehensive unit test suite covering rate limiting, backoff, caching, models, and fixture data.
8. Execute tests: Run `pytest tests/unit/test_api_clients.py -v` and record output.

## Output Requirements
Write your completion handoff report to:
`C:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\m1_worker_1\handoff.md`
Include build/test commands executed and results obtained.

## 2026-09-20T13:14:22Z
You are m1_worker_1. Your working directory is C:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\m1_worker_1. Read your assignment at C:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\m1_worker_1\DISPATCH.md, C:\Users\Asus\Documents\antigravity\hopeful-curie\ORIGINAL_REQUEST.md, C:\Users\Asus\Documents\antigravity\hopeful-curie\PROJECT.md, and the explorer reports in .agents/m1_explorer_1/handoff.md, .agents/m1_explorer_2/handoff.md, and .agents/m1_explorer_3/handoff.md.

MANDATORY INTEGRITY WARNING: DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Implement Milestone 1 files exclusively: pyproject.toml, src/crypto_syndicate/config.py, models.py, rate_limiter.py, cache.py, gmgn_client.py, solscan_client.py, fixtures.py, and tests/unit/test_api_clients.py. Run pytest tests/unit/test_api_clients.py -v, document passing test results in handoff.md, and notify the caller when done.

# E2E Test Infra: Crypto Syndicate Research and Monitoring System

## Test Philosophy
- Opaque-box, requirement-driven. Derived strictly from `ORIGINAL_REQUEST.md` and user-facing specifications without internal module dependencies.
- Methodology: Systematic 4-tier testing hierarchy (Category-Partition, Boundary Value Analysis, Pairwise Combinatorial Testing, Real-World Workload Testing).

## Feature Inventory & Test Coverage Plan
| # | Feature | Source (Requirement) | Tier 1 (Min 5) | Tier 2 (Min 5) | Tier 3 (Pairwise) | Tier 4 (App Scenarios) |
|---|---------|----------------------|:--------------:|:--------------:|:-----------------:|:----------------------:|
| F1 | Multi-Chain Non-Seed Discovery | ORIGINAL_REQUEST §R1 | 5 | 5 | ✓ | ✓ |
| F2 | Coordinated Early Entry Detection | ORIGINAL_REQUEST §R1 | 5 | 5 | ✓ | ✓ |
| F3 | Common Funding Source Detection | ORIGINAL_REQUEST §R1 | 5 | 5 | ✓ | ✓ |
| F4 | Shared Deployer Detection | ORIGINAL_REQUEST §R1 | 5 | 5 | ✓ | ✓ |
| F5 | Coordinated Exit Dump Detection | ORIGINAL_REQUEST §R1 | 5 | 5 | ✓ | ✓ |
| F6 | Interactive Network Graph & Click HUD | ORIGINAL_REQUEST §R2 | 5 | 5 | ✓ | ✓ |
| F7 | Dual-Panel Timeline Map | ORIGINAL_REQUEST §R2 | 5 | 5 | ✓ | ✓ |
| F8 | GMGN & Solscan API Integration | ORIGINAL_REQUEST §R3 | 5 | 5 | ✓ | ✓ |
| F9 | Rate Limiting, Backoff & Caching | ORIGINAL_REQUEST §R3 | 5 | 5 | ✓ | ✓ |
| F10 | Continuous Polling Daemon | ORIGINAL_REQUEST §R4 | 5 | 5 | ✓ | ✓ |
| F11 | 60s Heartbeat & Dual Alert Logs | ORIGINAL_REQUEST §R4 | 5 | 5 | ✓ | ✓ |
| F12 | Self-Contained Offline HTML Report | ORIGINAL_REQUEST §R5 | 5 | 5 | ✓ | ✓ |
| F13 | CSV & JSON Exports with Evidence Metadata | ORIGINAL_REQUEST §R5 | 5 | 5 | ✓ | ✓ |

## Test Architecture
- **Test Runner**: Pytest invoking CLI commands, exported reports, generated notebook runs, and monitor logs.
- **Pass/Fail Semantics**: Zero non-zero exit codes, zero schema validation errors, zero unhandled exceptions.
- **Directory Layout**:
  - `tests/e2e/test_tier1_features.py`: Feature coverage (>=65 tests across 13 core features).
  - `tests/e2e/test_tier2_boundaries.py`: Boundary and corner cases (empty responses, 429 rate limits, huge graphs, single-wallet syndicates, zero profit, missing env vars).
  - `tests/e2e/test_tier3_combinations.py`: Cross-feature pairwise interactions (API cache + discovery, discovery + notebook rendering, daemon + alerting + HTML export).
  - `tests/e2e/test_tier4_applications.py`: 5 realistic multi-chain syndicate scenarios (Solana Pump.fun launch ring, Ethereum Uniswap rug syndicate, BSC PancakeSwap sniper cluster, Base meme ring, Multi-chain cross-deployer syndicate).

## Acceptance Criteria Checklist (Hard Requirements)
- [ ] System discovers at least 5 wallet clusters from recent token launches without any seed wallet input
- [ ] Each cluster has >= 3 wallets with at least 2 of the 4 suspicious pattern types flagged
- [ ] Jupyter notebook renders interactive network graphs (zoom, click on node for wallet details)
- [ ] Transfer maps show timeline of buys/sells with token price overlay
- [ ] Clusters are visually distinct (color-coded by syndicate group)
- [ ] GMGN and Solscan API calls are rate-limited, retried on failure, and cached to avoid redundant requests
- [ ] All chains supported by GMGN are queried, not just Solana
- [ ] Monitoring loop runs continuously without crashing, logging a heartbeat every minute
- [ ] Alert log is written in both JSON (machine-readable) and plain text (human-readable)
- [ ] New suspicious clusters detected within 10 minutes of a token launch
- [ ] HTML report is self-contained (no external dependencies) and opens in a browser
- [ ] CSV export includes: wallet address, chain, suspicion score, flagged patterns, associated tokens, estimated profit
- [ ] API credentials accepted via environment variables only (GMGN_API_KEY and SOLSCAN_API_KEY) — never hardcoded

## Coordination Artifact
Upon completion of the test suite, publish `TEST_READY.md` containing test invocation instructions and tier coverage metrics.

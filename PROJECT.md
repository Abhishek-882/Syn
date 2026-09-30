# Project: Crypto Syndicate Research System — M12 Jito Bundle Detector & Power-User UX Upgrades

## Architecture
- **Web Visualizer**: `http://localhost:8000/web/syndicate_3d_visualizer.html` (served via Python HTTP server on port 8000). Three.js r128 3D scene, OrbitControls, 5-lobe cognitive UI, command deck, telemetry HUD, 4D timeline scrubber, dossier panel.
- **M12 Jito Bundle Detector**: `src/crypto_syndicate/jito_detector.py`
  - Pure-library module (no direct network I/O).
  - 8 canonical tip accounts (`96gYZGLnJeTa9AGEefvjNArMBUwEpzDQRNSCGVFmhEEq`, `HFqU5x63VTqvQss8hp11i4wVV8bD44PvwucfZ2bU7gRe`, `Cw8CFyM9FkoMi7K7Crf6HNQqf4uEMzpKw6QNghXLvLkY`, `ADaUMid9yfUytqMBgopwjb2DTLSokTSzL1sMaC9jnwRv`, `DfXygSm4jCyNCybVYYK6DwvWqjKee8pbDmJGcLWNDXjh`, `ADuUkR4vqLUMWXxW9gh6D6L8pMSawimctcNZ5pGwDcEt`, `DttWaMuVvTiduZRnguLF7jNxTgiMBZ1hyflaDeKd1qRv`, `3AVi9Tg9Uo68tJfuvoKvqKNWKkC5wPdSSdeBnizKZ6dW`).
  - Inner CPI transfer analysis (SOL transfers to tip accounts in inner instructions).
  - Bundle ID correlation (hard confirmation when metadata present).
  - Timing analysis (400ms slot window heuristic).
  - Confidence scoring returning `JitoDetectionResult`.
- **System Integration**:
  - `src/crypto_syndicate/scanner.py`: Calls `jito_detector.detect(tx)` and attaches result to `TradeRecord`.
  - `src/crypto_syndicate/fingerprint.py`: Attaches bundle behavior to `SyndicateBehavior`.
  - `src/crypto_syndicate/api/fixtures.py`: >=5 Jito bundle fixtures and >=5 non-bundle fixtures.
  - `tests/unit/test_jito_detector.py`: >=25 unit and adversarial tests.
- **Visualizer Integration**:
  - Radar alert cards: `🎯 JITO BUNDLE` badge.
  - Dossier panel: Confidence score & signals list.
  - Telemetry HUD: `[JITO: N bundles detected]` counter.
- **Verification Harness**:
  - Playwright browser scripts in `.agents/skills/post-deploy-web-exploring/scripts/`.
  - `exhaustive_step_explorer.py` (30/30 workflow steps).
  - Pytest test suite (>=346 passing tests).

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Three-Agent UX Audit | 3 independent browser agents audit visualizer with Syndicate Hunter persona, capturing >=30 screenshots each | M12-Phase 1 | ORIGINAL_REQUEST §R1 |
| 2 | UX Synthesis & Upgrade Plan | Synthesize 3 audit reports, identify top 5 power-user improvements | M12-Phase 2 | ORIGINAL_REQUEST §R2 |
| 3 | Visualizer Power-User Upgrades | Implement top 5 UX improvements in visualizer with zero placeholders | M12-Phase 2 | ORIGINAL_REQUEST §R2 |
| 4 | Canonical Tip Account Matching | Match transfers against all 8 known Jito tip accounts | M12-Phase 3 | ORIGINAL_REQUEST §R3 |
| 5 | Inner CPI Transfer Detection | Detect SOL transfers to tip accounts appearing inside CPI instructions | M12-Phase 3 | ORIGINAL_REQUEST §R3 |
| 6 | Bundle ID Correlation | Hard confirmation signal when bundle_id metadata is present | M12-Phase 3 | ORIGINAL_REQUEST §R3 |
| 7 | 400ms Timing Slot Analysis | Detect co-slot transactions arriving within 400ms of tip transfers | M12-Phase 3 | ORIGINAL_REQUEST §R3 |
| 8 | JitoDetectionResult Dataclass | Return structured result with is_jito_bundle, confidence, signals, tip_account, bundle_id | M12-Phase 3 | ORIGINAL_REQUEST §R3 |
| 9 | Scanner & Fingerprint Integration | Wire detect() into scanner.py and fingerprint.py | M12-Phase 3 | ORIGINAL_REQUEST §R3 |
| 10 | Mock Fixtures for Bundles | Add >=5 bundle + >=5 non-bundle fixtures to api/fixtures.py | M12-Phase 3 | ORIGINAL_REQUEST §R3 |
| 11 | Comprehensive Jito Tests | Add >=25 unit & adversarial tests covering TP, TN, edge cases, thresholds | M12-Phase 3 | ORIGINAL_REQUEST §R3 |
| 12 | Radar Card Jito Badge | Display 🎯 JITO BUNDLE badge on radar cards when detected | M12-Phase 4 | ORIGINAL_REQUEST §R4 |
| 13 | Dossier Jito Signals & Confidence | Display confidence score and signals list in dossier view | M12-Phase 4 | ORIGINAL_REQUEST §R4 |
| 14 | Telemetry HUD Jito Counter | Display live counter [JITO: N bundles detected] in HUD | M12-Phase 4 | ORIGINAL_REQUEST §R4 |
| 15 | Browser Step Re-verification | >=30 step browser re-verification with screenshots in results/screenshots/steps/ | M12-Phase 4 | ORIGINAL_REQUEST §R4 |
| 16 | Full Test Suite Pass | >=346 tests pass in pytest (321 existing + >=25 M12) | M12-Phase 5 | ORIGINAL_REQUEST §R5 |
| 17 | Exhaustive 30-Step Explorer Pass | 30/30 steps pass with 0 failures, 0 console errors | M12-Phase 5 | ORIGINAL_REQUEST §R5 |
| 18 | Live Browser Verification & Audit | Live browser verification with real scanner data and forensic integrity audit | M12-Phase 5 | ORIGINAL_REQUEST §R5 |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M12-P1 | Three-Agent UX Audit | 3 independent browser agents (Syndicate Hunter persona), >=30 screenshots each, save to `results/ux_audit/agent_{1,2,3}_review.md` | none | IN_PROGRESS |
| M12-P2 | Synthesis & UX Upgrades | Synthesize reports into `results/ux_audit/synthesis_upgrade_plan.md`, implement top 5 power-user improvements, verify 321 tests pass | M12-P1 | PLANNED |
| M12-P3 | M12 Jito Bundle Detector | `src/crypto_syndicate/jito_detector.py`, scanner/fingerprint integration, fixtures, >=25 tests | M12-P2 | PLANNED |
| M12-P4 | Visualizer Integration | Radar card badge, dossier signals/confidence, HUD counter, >=30 step re-verification | M12-P3 | PLANNED |
| M12-P5 | Final Verification & Audit | >=346 pytest tests pass, 30/30 exhaustive steps pass, live scanner confirmation, forensic audit | M12-P4 | PLANNED |

## Interface Contracts
### `jito_detector.py` Interface
```python
@dataclass
class JitoDetectionResult:
    is_jito_bundle: bool
    confidence: float
    signals: List[str]
    tip_account_matched: Optional[str] = None
    bundle_id: Optional[str] = None

def detect(tx: dict, slot_context: Optional[dict] = None) -> JitoDetectionResult:
    ...
```

### `results/ux_audit/` Artifacts
- `agent_1_review.md`, `agent_2_review.md`, `agent_3_review.md`: Independent power-user reviews with usability, data density, interaction speed, power-user feature ratings (1–10) and screenshot catalogs.
- `synthesis_upgrade_plan.md`: Cross-agent consensus, ranked top 5 upgrades with implementation specifications.

## Code Layout
- `src/crypto_syndicate/jito_detector.py`: Jito bundle detector pure library module.
- `src/crypto_syndicate/scanner.py`: Live scanner calling Jito detector.
- `src/crypto_syndicate/fingerprint.py`: Behavioral fingerprint incorporating bundle features.
- `src/crypto_syndicate/api/fixtures.py`: Test fixtures including Jito bundles and non-bundles.
- `tests/unit/test_jito_detector.py`: Unit and adversarial test suite for Jito detection.
- `web/syndicate_3d_visualizer.html`: Cyber-forensic 3D visualizer UI with power-user upgrades and Jito indicators.
- `results/ux_audit/`: UX audit reviews, screenshots, and synthesis upgrade plan.
- `results/screenshots/steps/`: Exhaustive 30-step verification screenshots.

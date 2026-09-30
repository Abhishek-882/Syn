# DISPATCH — 2026-09-21T09:00:00Z

You are the Project Orchestrator (orchestrator_7) for the following mission:

MISSION:
Execute the user request for **M12 — Jito Bundle Detector** and the **Three-Agent UX Audit & Upgrades** as recorded in `ORIGINAL_REQUEST.md`.

Working directory for this orchestrator: `c:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\orchestrator_7`
Project root: `c:\Users\Asus\Documents\antigravity\hopeful-curie`
Path to ORIGINAL_REQUEST.md: `c:\Users\Asus\Documents\antigravity\hopeful-curie\ORIGINAL_REQUEST.md`

## Context & Baseline
- All prior milestones M1–M11.7 are complete. 321/321 tests passing (zero failures).
- Live platform URL: `http://localhost:8000/web/syndicate_3d_visualizer.html`
- HTTP server on port 8000 is running (task-39).
- Resume reference: `.agents/skills/crypto-syndicate-resume/SKILL.md`
- Primary architecture directory: `src/crypto_syndicate/` (always use this, never the old root crypto_syndicate/).

## Execution Phases

### Phase 1: Three-Agent UX Audit (Browser Agents — Persona: Syndicate Hunter Power User)
Spawn 3 independent browser agents (with clean working directories in `.agents/ux_agent_1`, `.agents/ux_agent_2`, `.agents/ux_agent_3`).
Each explores `http://localhost:8000/web/syndicate_3d_visualizer.html` independently:
- Persona: Syndicate Hunter power user (wants fast keyboard shortcuts, filter recall, batch export, alert tuning, maximum data density).
- Attempt EVERY interactive element: health chips, tag filters, radar cards, dossier views, timeline pills and scrubber, play/pause, CL4R1T4S mode, copy toast, export markdown, reset view, command deck collapse/expand.
- Take a screenshot at EVERY distinct interaction step (minimum 30 screenshots each, stored in `results/ux_audit/agent_{1,2,3}_screenshots/` or similar).
- Write power-user review report covering:
  1. What worked perfectly
  2. What was confusing, missing, or frustrating
  3. Specific UI/UX improvement requests
  4. 1–10 scores for: usability, data density, interaction speed, power-user features
- Save reports to `results/ux_audit/agent_{1,2,3}_review.md`.

### Phase 2: Synthesis & Upgrade Plan
1. Synthesize the 3 reports into `results/ux_audit/synthesis_upgrade_plan.md`.
2. Identify the top 5 highest-impact UX improvements wanted by a power user.
3. Implement those improvements in `web/syndicate_3d_visualizer.html` (and supporting files). Zero placeholders.
4. Verify all 321 tests continue to pass (`python -m pytest tests/ -q`).

### Phase 3: M12 — Jito Bundle Detector (`src/crypto_syndicate/jito_detector.py`)
Implement `jito_detector.py` as a standalone pure-library module:
- Canonical tip account matching: all 8 Jito tip accounts:
  - `96gYZGLnJeTa9AGEefvjNArMBUwEpzDQRNSCGVFmhEEq`
  - `HFqU5x63VTqvQss8hp11i4wVV8bD44PvwucfZ2bU7gRe`
  - `Cw8CFyM9FkoMi7K7Crf6HNQqf4uEMzpKw6QNghXLvLkY`
  - `ADaUMid9yfUytqMBgopwjb2DTLSokTSzL1sMaC9jnwRv`
  - `DfXygSm4jCyNCybVYYK6DwvWqjKee8pbDmJGcLWNDXjh`
  - `ADuUkR4vqLUMWXxW9gh6D6L8pMSawimctcNZ5pGwDcEt`
  - `DttWaMuVvTiduZRnguLF7jNxTgiMBZ1hyflaDeKd1qRv`
  - `3AVi9Tg9Uo68tJfuvoKvqKNWKkC5wPdSSdeBnizKZ6dW`
- Inner CPI transfer pattern: detect transfers where inner instruction sends SOL to tip account without appearing in outer instructions.
- bundle_id correlation: hard confirmation if metadata present.
- Timing analysis: flag transactions within 400ms slot window alongside known tip-touching transactions.
- Confidence scoring: `JitoDetectionResult` dataclass (`is_jito_bundle`, `confidence`, `signals`, `tip_account_matched`, `bundle_id`).
- Integration:
  - `scanner.py` and `fingerprint.py` call `jito_detector.detect(tx)` and attach results to `TradeRecord` and `SyndicateBehavior`.
- Fixtures:
  - Add ≥5 known Jito bundle fixtures and ≥5 non-bundle fixtures to `src/crypto_syndicate/api/fixtures.py`.
- Tests:
  - Add adversarial + unit tests: minimum 25 new tests in `tests/unit/test_jito_detector.py` (true positives, true negatives, edge cases, thresholds).

### Phase 4: Visualizer Integration (Jito Bundle Display)
- Radar feed alert cards: display `🎯 JITO BUNDLE` badge when `is_jito_bundle=True`.
- Dossier view: display `confidence` score and fired `signals` list.
- Telemetry HUD: live counter `[JITO: N bundles detected]`.
- Re-run browser verification (minimum 30 steps with per-step screenshots in `results/screenshots/steps/`).

### Phase 5: Final Full-Suite Verification
1. `python -m pytest tests/ -q` passes 100% (≥346 tests).
2. `python .agents/skills/post-deploy-web-exploring/scripts/exhaustive_step_explorer.py` passes 30/30 steps (0 failures, 0 console errors).
3. Browser agent confirms live Jito display with real scanner data.

Initialize your BRIEFING.md and progress.md immediately, spawn subagents as needed, and report back when victory is claimed so that the independent Victory Auditor can be triggered.

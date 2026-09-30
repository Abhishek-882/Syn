---
name: post-deploy-web-exploring
description: >
  Autonomous end-to-end exploration, exhaustive interactive button sweeps,
  failure logging, and remediation planning for deployed web applications,
  dashboards, and visualizers. Activate after deploying or modifying web interfaces.
---

# Post-Deploy Web Exploration & Interactive Sweeper

This skill provides an automated, programmatic testing harness that explores any deployed web application, discovers all clickable elements, tests their interaction, records every failure, and drives a closed-loop remediation workflow.

## 1. When to Use

Activate this skill whenever:
- A web interface, dashboard, visualizer, or data application has been created or modified.
- A local HTTP server is running (e.g. `http://localhost:8000/...`).
- You need to guarantee 100% of buttons, chips, sliders, pills, and cards function without pointer interception, JavaScript errors, or silent failures.

## 2. Element Discovery Taxonomy

The crawler script systematically discovers and categorizes all actionable DOM elements:
- **Buttons**: `button`, `input[type="button"]`, `input[type="submit"]`, `[role="button"]`
- **Navigation Chips & Tags**: `.health-chip`, `.tag-chip`, `.backlink-pill`
- **Timeline & Transport**: `.stage-pill`, `#play-pause-btn`, `input[type="range"]`
- **Radar & Metric Cards**: `.kpi-card`, `.alert-card`, `.telemetry-row`
- **Modal & Deck Toggles**: `.plaque-close-btn`, `#deck-toggle-btn`, `#clarity-btn`, `#reset-cam-btn`

## 3. Running the Exploration Harness

Run the automated exploration crawler via PowerShell:

```powershell
python .agents/skills/post-deploy-web-exploring/scripts/web_explorer.py --url "http://localhost:8000/web/syndicate_3d_visualizer.html" --output "results/web_verification_failures.json"
```

### Options:
- `--url`: Target web application URL (required).
- `--output`: Path to write the JSON failure report (default: `results/web_verification_failures.json`).
- `--timeout`: Maximum milliseconds to wait per click action (default: 3000ms).
- `--screenshot-dir`: Directory to save verification screenshots (default: `results/screenshots`).

## 4. Failure Logging Schema

When a failure occurs, the crawler writes an entry to `results/web_verification_failures.json`:

```json
{
  "total_elements_discovered": 28,
  "total_tested": 28,
  "passed": 27,
  "failed": 1,
  "failures": [
    {
      "selector": "#play-pause-btn",
      "text": "▶ PLAY",
      "error_type": "POINTER_INTERCEPTION",
      "message": "<div id=\"curatorial-plaque\"> intercepts pointer events",
      "bounding_box": {"x": 320, "y": 850, "width": 64, "height": 28},
      "console_errors": [],
      "timestamp": "2026-09-21T08:12:00Z"
    }
  ]
}
```

## 5. Autonomous Remediation Protocol

1. **Read Log**: Parse `results/web_verification_failures.json`.
2. **Isolate Root Cause**:
   - `POINTER_INTERCEPTION`: Check CSS coordinates (`top`, `bottom`, `left`, `right`) and `z-index` collisions.
   - `JAVASCRIPT_ERROR`: Check missing DOM elements or unhandled promises in the console error list.
   - `TIMEOUT`: Check if the element was hidden (`display: none`, `opacity: 0`, or off-screen).
3. **Apply Fix**: Modify the source code using `replace_file_content`.
4. **Re-Execute Sweep**: Re-run `web_explorer.py` until `failed == 0`.

## 6. Mandatory `/browser` Multi-Stage Visual Verification Protocol

Whenever a deploy occurs, you MUST invoke `/browser` or launch a browser agent (`browser` subagent / Playwright) to navigate the deployed URL and capture screenshots (`ss`) at each defined milestone stage:

1. **Stage 1 — Station Baseline Overview**:
   - URL: `http://localhost:<port>/path`
   - Capture: `results/screenshots/initial_state.png`
   - Verify: 3D canvas / WebGL initialization, gimbal telemetry HUD, top status bar, and radar feed.
2. **Stage 2 — Level 1 Click-to-Explain Flyouts**:
   - Action: Click infrastructure health chips (`[CACHE: ...]`, `[GMGN: ...]`) or KPI badges.
   - Capture: `results/screenshots/stage_B_explain_chip.png`
   - Verify: Slide-out curatorial plaque opens in plain-English explainer mode with live dynamic telemetry.
3. **Stage 3 — 4D Timeline Chronological Replay**:
   - Action: Click attack sequence pills (e.g. `[SNIPERS (T+13s)]`, `[BUNDLE (T+16s)]`).
   - Capture: `results/screenshots/stage_C_timeline_snipe.png`
   - Verify: Timeline scrubber synchronizes, stage explanation renders, and 3D node focus highlights activate.
4. **Stage 4 — Level 2 Synaptic Backlinks & Kinetic Glide**:
   - Action: Click alert card to load dossier, then click entity backlink pill (`[Wallet: ...]`, `[Funder: ...]`).
   - Capture: `results/screenshots/stage_D_dossier_glide.png`
   - Verify: Camera executes smooth 800ms kinetic glide to the target node, followed by an arrival neuron pulse.
5. **Stage 5 — Post-Sweep Integrity**:
   - Action: Complete 100% interactive button sweep.
   - Capture: `results/screenshots/post_sweep_state.png`
   - Verify: UI layout remains intact, no detached DOM nodes, no unhandled console errors, and no modal traps.

## 7. Exhaustive Multi-Step Explorer Harness

To verify complex single-page apps with 3D canvases, timeline scrubbers, and slide-out dossiers:

```powershell
python .agents/skills/post-deploy-web-exploring/scripts/exhaustive_step_explorer.py
```

This script systematically executes 30 distinct workflow steps:
- Verifies DOM state mutations (e.g. `explain-title` updated, `copy-toast` rendered, timeline time synchronized).
- Records high-res screenshots for each step into `results/screenshots/steps/` (e.g. `01_baseline_overview.png` through `30_command_deck_restored.png`).
- Emits `results/screenshots/exhaustive_steps_report.json` with 100% pass criteria.

## 8. Multi-Agent Persona UX Audit Protocol

Prior to major milestone builds or UI refactors, deploy 3 independent browser agents:
1. **Persona Conditioning**: E.g. "Syndicate Hunter power user" demanding high keyboard shortcut efficiency, filter persistence, dense telemetry, and rapid export.
2. **Unbiased Independent Runs**: Agents explore without cross-talk and save reports to `results/ux_audit/agent_{1,2,3}_review.md` with $\ge$30 screenshots each.
3. **Synthesis**: Synthesize common friction points into `results/ux_audit/synthesis_upgrade_plan.md` to prioritize the top-5 UX fixes for the release.



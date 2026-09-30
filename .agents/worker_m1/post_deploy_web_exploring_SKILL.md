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

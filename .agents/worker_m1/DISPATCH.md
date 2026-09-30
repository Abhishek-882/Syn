# Dispatch Task: Worker Milestone 1

## Role
teamwork_preview_worker (Exploration Harness & Failure Logging Engineer)

## Objective
Enhance and harden `.agents/skills/post-deploy-web-exploring/scripts/web_explorer.py` to satisfy requirements R1 and R2 from `ORIGINAL_REQUEST.md`.

## Specific Requirements
1. **Resilient Dynamic Locator Resolution**:
   - In `web_explorer.py`, avoid saving stale locator references in `discovered_locators`. Store selector, index, text, and metadata, and dynamically resolve `page.locator(sel).nth(idx)` during the click sweep with retry logic if an element is temporarily re-rendering.
2. **Network Asset Failure Monitoring (R2)**:
   - Listen to `page.on("response", ...)` to record any 404/500 HTTP failures in `network_errors`.
3. **DOM Snapshot Capture (R2)**:
   - When an element fails (click timeout, pointer interception, JS error), capture its `outerHTML` or parent container DOM snapshot into `dom_snapshot`.
4. **Schema Conformance (R2)**:
   - Standardize keys in `failure_item`:
     `selector`, `text`, `error_type`, `message`, `bounding_box` (with x, y, width, height), `dom_snapshot`, `console_errors`, `timestamp` (ISO-8601 string format).
   - In root json output, include `total_elements_discovered`, `total_tested`, `passed`, `failed`, `console_errors_count`, `page_errors_count`, `network_errors_count`, `failures`, `console_errors`, `network_errors`.
5. **Pointer Collision & Interception Detection (R1)**:
   - Ensure pointer interception exceptions are cleanly captured with exact element bounding box coordinates.
6. **Verification Run**:
   - Run the enhanced `web_explorer.py` against `http://localhost:8000/web/syndicate_3d_visualizer.html`.
   - Verify that output conforms to the schema in `results/web_verification_failures.json`.

## Write Ownership
You own exclusively:
- `c:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\skills\post-deploy-web-exploring\scripts\web_explorer.py`
- `c:\Users\Asus\Documents\antigravity\hopeful-curie\results\web_verification_failures.json`

DO NOT modify `web/syndicate_3d_visualizer.html` in this milestone (that is owned by Milestone 2).

## Mandatory Integrity Warning
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

## Inputs
- `c:\Users\Asus\Documents\antigravity\hopeful-curie\ORIGINAL_REQUEST.md`
- `c:\Users\Asus\Documents\antigravity\hopeful-curie\PROJECT.md`
- `c:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\explorer_survey_2\analysis.md`
- `c:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\skills\post-deploy-web-exploring\scripts\web_explorer.py`

## Deliverables
- Working directory: `c:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\worker_m1`
- Log your progress in `c:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\worker_m1\progress.md`
- Deliver a comprehensive handoff in `c:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\worker_m1\handoff.md` with build/run verification outputs.
- Send completion message to parent orchestrator (`36ab40e6-0e20-4a26-9b0f-c61a24c1ed6a`).

# Rule: Mandatory Post-Deploy Web Exploration & Button Sweep

Whenever a web platform, visualizer, dashboard (HTML/JS/React/Streamlit), or interactive data application is created, edited, or deployed:

1. **Mandatory Automated Exploration**:
   - You MUST NOT conclude or declare a deployment complete until an automated headless browser (e.g. Playwright) navigates to the deployed URL.
   - You MUST systematically discover and click **every interactive element**: native buttons (`button`, `input[type="button"]`), ARIA roles (`[role="button"]`, `[role="tab"]`), navigation chips, stage pills, sliders, filter tags, KPI cards, table rows, and modal dialogs.

2. **Pointer Interception & Collision Check**:
   - You MUST verify that floating docks, plaques, headers, banners, and toasts do not physically overlap or intercept pointer events for other clickable controls.
   - Any click attempt that times out due to pointer interception is treated as a critical UI defect.

3. **Structured Failure Logging**:
   - Any unhandled JavaScript error, 404/500 asset request, failed element click, or pointer interception timeout MUST be recorded into a structured failure log (`results/web_verification_failures.json` or `results/web_verification_failures.log`).
   - Never suppress UI errors, swallow exceptions silently, or fail to report broken buttons.

4. **Remediation Loop**:
   - If any failure is detected, you MUST generate an immediate root cause analysis (RCA) and remediation plan, apply the fix to the source code, and re-run the exploration sweep until 100% of interactive controls pass with zero failures.

5. **Mandatory Exhaustive Step-by-Step Exploration & Per-Step Screenshots**:
   - You MUST NOT declare web testing complete with quick samples or superficial button passes.
   - You MUST execute an **Exhaustive Multi-Step Exploration Script** covering 100% of distinct user workflows:
     1. Provider resilience & circuit breaker explain cards
     2. Telemetry HUD and camera metrics
     3. Category tag filtering and visual pruning
     4. Entity selection, dossier flyouts, and kinetic camera glides
     5. Action controls (clipboard copy, markdown export) with toast validation
     6. Plaque dismissals and viewport clearance
     7. 4D timeline chronological jump pills and range slider scrubbing
     8. Timeline transport playback & pause cycles
     9. Visual modes (CL4R1T4S CRT phosphor, reset view)
     10. Collapsible responsive docks and multi-resolution viewports
   - A numbered screenshot MUST be captured for **every single workflow step** into `results/screenshots/steps/` (e.g. `01_...png` through `30_...png`).
   - A structured report (`exhaustive_steps_report.json`) must record duration, action description, DOM reaction verification, and screenshot path for every step. Zero errors allowed.

6. **Pre-Implementation Persona-Driven Multi-Agent UX Audits**:
   - Before implementing major feature upgrades or milestone releases, deploy at least 3 independent browser agents conditioned as the target user persona (e.g., "Syndicate Hunter power user").
   - Each agent independently explores the live interface from scratch, logs usability friction, data density, interaction speed, and missing capabilities.
   - Audit reports must be saved to `results/ux_audit/agent_{1,2,3}_review.md` and synthesized into a prioritized Top-5 Upgrade Plan before code changes begin.


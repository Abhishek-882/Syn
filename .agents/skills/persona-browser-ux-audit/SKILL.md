---
name: persona-browser-ux-audit
description: >-
  Multi-agent persona-driven browser UX exploration, per-step screenshot logging,
  and closed-loop UI upgrade synthesis for web applications and dashboards.
---

# Persona-Driven Browser UX Audit & Closed-Loop Sprint Workflow

A standardized, multi-agent protocol for evaluating deployed web platforms, dashboards, and visualizers through the lens of specific real-world user personas before and after feature development.

## 1. Core Workflow Architecture

```
Deploy Web App / Visualizer (http://localhost:8000/...)
                    │
                    ▼
[Phase 1] Multi-Agent Persona Audit
  ├── ux_agent_1: "Syndicate Hunter" (Forensic Speed & Power User)
  ├── ux_agent_2: "Analytical Auditor" (Data Density & Completeness)
  └── ux_agent_3: "Novice Trader" (Intuitive Navigation & Clarity)
  * Each agent executes >=30 interactive steps via Playwright
  * Every single interaction step captures a numbered screenshot (01_...png)
  * Independent review reports generated in results/ux_audit/
                    │
                    ▼
[Phase 2] Synthesis & Top-5 Upgrade Backlog
  * Cross-correlate friction points, omissions, and common complaints
  * Synthesize into results/ux_audit/synthesis_upgrade_plan.md
  * Prioritize Top 5 highest-impact usability and power-user features
                    │
                    ▼
[Phase 3] Code Implementation & Feature Build
  * Implement Top 5 UI upgrades (shortcuts, search, batch export, telemetry)
  * Build underlying backend / library modules
  * Integrate live streaming and event bindings
                    │
                    ▼
[Phase 4] Automated 30-Step Verification Sweep
  * Run exhaustive_step_explorer.py headless Playwright sweep
  * Verify 30/30 steps pass with 0 console errors and 0 pointer collisions
  * Refresh all 30 numbered screenshots
                    │
                    ▼
[Phase 5] Zero-Regression Full Test Verification
  * Run full repository test suite (python -m pytest tests/ -q)
  * Verify 100% passing across all existing and new tests
```

---

## 2. Persona Profiles Taxonomy

When dispatching explorer subagents, condition each agent with an explicit behavioral persona:

### A. The "Syndicate Hunter" (Power User)
- **Mindset**: Relentless, high-frequency operator investigating suspicious on-chain launches.
- **Expectations**: Global keyboard shortcuts (Space, Esc, 1-4, R, C, /), instant search filtering, monospace tables, 1-click batch export (CSV/JSON), dense telemetry HUDs, zero UI fluff or unnecessary modals.
- **Rubric Focus**: Interaction Speed & Power-User Capabilities.

### B. The "Analytical Auditor" (Compliance / Investigator)
- **Mindset**: Meticulous compliance auditor cross-referencing multi-hop transaction lineages and proof-of-funds.
- **Expectations**: Verifiable data provenance, real non-mock cache stats, transparent fee calculations, raw address copy buttons, clean Markdown export for forensic reports.
- **Rubric Focus**: Data Density, Accuracy, and Evidence Traceability.

### C. The "First-Time Analyst" (Onboarding & Usability)
- **Mindset**: Junior analyst evaluating the platform for the first time.
- **Expectations**: Clear visual hierarchy, plain-English click-to-explain cards, kinetic camera glides that clarify 3D spatial connections, obvious status indicators.
- **Rubric Focus**: Usability, Intuitiveness, and Error Prevention.

---

## 3. Standardized Execution Harness (Playwright)

Every audit agent must execute its sweep programmatically via Playwright to ensure deterministic, reproducible results:

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1920, "height": 1080})
    
    # Collect console and page errors
    console_errors = []
    page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
    page.on("pageerror", lambda err: console_errors.append(str(err)))

    page.goto("http://localhost:8000/web/syndicate_3d_visualizer.html", wait_until="networkidle")

    # Capture numbered step screenshot on every action
    page.screenshot(path="results/ux_audit/agent_X_screenshots/01_baseline.png")
```

---

## 4. Power-User Scorecard Rubric

Each review report (`results/ux_audit/agent_{i}_review.md`) must rate the platform across 4 dimensions on a scale of 1.0 to 10.0:

| Category | Description | Benchmark Criteria |
|:---|:---|:---|
| **Usability** | Ergonomics, layout consistency, clarity | Clean geometry, zero overlapping text, zero pointer collisions. |
| **Data Density** | Information per pixel on standard viewports | Tickers, wallet counts, bundler rates surfaced without extra clicks. |
| **Interaction Speed** | Response time, 3D camera physics, FPS | 60 FPS target, instant filtering, fluid <1s camera glides. |
| **Power-User Features** | Keyboard hotkeys, search, batch export | Full hotkey engine, real-time search, 1-click batch download suite. |

---

## 5. Synthesis Rules

1. **Consensus Over Outliers**: Only promote an improvement to the Top 5 Backlog if at least 2 of the 3 independent audit agents flagged the same operational deficit.
2. **Actionable Implementation Steps**: Every item in `synthesis_upgrade_plan.md` must have explicit DOM selector targets, keyboard keybindings, or data schemas specified before implementation commences.
3. **Zero Regressions**: Feature code must never break existing spatial mechanics or API contracts.

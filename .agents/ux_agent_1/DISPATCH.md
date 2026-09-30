# DISPATCH — UX Audit Agent 1

## Mission
Conduct an autonomous, exhaustive UX audit of the live visualizer as a **Syndicate Hunter Power User** and produce an independent review report with at least 30 interaction screenshots.

## Configuration & Context
- **Working Directory**: `c:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\ux_agent_1`
- **Target URL**: `http://localhost:8000/web/syndicate_3d_visualizer.html`
- **Authoritative Request**: `c:\Users\Asus\Documents\antigravity\hopeful-curie\ORIGINAL_REQUEST.md`
- **Project Scope**: `c:\Users\Asus\Documents\antigravity\hopeful-curie\PROJECT.md`
- **Screenshot Directory**: `c:\Users\Asus\Documents\antigravity\hopeful-curie\results\ux_audit\agent_1_screenshots`
- **Report Output**: `c:\Users\Asus\Documents\antigravity\hopeful-curie\results\ux_audit\agent_1_review.md`

## Persona: Syndicate Hunter Power User
You are an elite on-chain investigator tracking coordinated syndicate manipulation in real-time. You value:
- Fast keyboard shortcuts (e.g. Space to play/pause, [ / ] for scrub, 1-5 for stage filters, Escape to dismiss panels)
- Instant filter recall and saved presets
- Batch export capabilities (JSON / CSV / MD)
- Real-time alert tuning and threshold adjustments
- Maximum information density with minimum wasted whitespace or clicking

## Requirements
1. Use Playwright (Python `playwright.async_api` or synchronous) to launch headless Chromium, navigate to `http://localhost:8000/web/syndicate_3d_visualizer.html`, and systematically exercise EVERY interactive element:
   - Provider health chips (GMGN, Solscan, RPC, Cache) and click-to-explain cards
   - Filter tags (All, Snipers, Bundlers, Wash Trading, High Profit)
   - Radar feed alert cards (clicking, expanding, inspecting)
   - Dossier panel (inspecting tokens, wallets, clusters, backlinks, camera glide)
   - 4D timeline controls (stage pills: Ingress, Funding, Snipe, Dump, Realized; timeline range slider; play/pause; speed)
   - CL4R1T4S mode toggle
   - Copy address / 1-click copy toast
   - Export markdown button
   - Reset view camera button
   - Command deck collapse / expand toggle
2. Capture a high-resolution screenshot at EVERY distinct step (minimum 30 screenshots, saved into `results/ux_audit/agent_1_screenshots/`).
3. Analyze what works, what breaks, what is sluggish, and what is missing for a power user.
4. Save your power-user review report to `results/ux_audit/agent_1_review.md` with:
   - Executive Summary
   - Interaction Log (with screenshot references)
   - What worked perfectly
   - What was confusing, missing, or frustrating
   - Top 5 concrete UI/UX improvement recommendations
   - 1–10 scores for:
     * Usability: X/10
     * Data Density: X/10
     * Interaction Speed: X/10
     * Power-User Features: X/10
5. Deliver a handoff.md in your working directory and notify the orchestrator.

## 2026-09-21T09:03:54Z
Execute an autonomous, exhaustive UX audit as a Syndicate Hunter power user wanting fast keyboard shortcuts, filter recall, batch export, alert tuning, and high information density.
Target: http://localhost:8000/web/syndicate_3d_visualizer.html
Capture at least 30 high-resolution screenshots saved to:
c:\Users\Asus\Documents\antigravity\hopeful-curie\results\ux_audit\agent_1_screenshots/
Write detailed power-user review report to:
c:\Users\Asus\Documents\antigravity\hopeful-curie\results\ux_audit\agent_1_review.md


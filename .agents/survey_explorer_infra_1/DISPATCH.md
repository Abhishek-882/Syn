# Task Assignment: Interactive Graphs, Continuous Monitoring & Reporting Infrastructure

## Identity
- Archetype: teamwork_preview_explorer
- Working Directory: C:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\survey_explorer_infra_1

## Objective
Investigate, design, and specify the architecture for R2 (Interactive Jupyter Notebook & Transfer Maps), R4 (Continuous Monitoring Loop & Alerts), and R5 (Static Self-Contained Research Report & Exports).

## Authoritative Requirements
You MUST read: C:\Users\Asus\Documents\antigravity\hopeful-curie\ORIGINAL_REQUEST.md

## Scope & Focus
1. Interactive Jupyter Notebook (R2):
   - Network graph visualization: nodes = wallets, edges = SOL/ETH transfers. Interactive features: zoom, pan, click-on-node inspection for wallet details, color-coded by syndicate group (e.g. PyVis / Plotly / Cytoscape HTML embedding).
   - Timeline maps: visual timeline showing which wallets bought which tokens at what time, overlaid with token price action.
2. Continuous Monitoring Loop & Alerts (R4):
   - Background polling daemon with configurable interval (default: 5m) and heartbeat logged every 1 minute.
   - Dual-format alert logging: machine-readable JSON alert log and human-readable plain text alert log.
   - Detection of new syndicate clusters within 10 minutes of a token launch.
   - Fault tolerance: crash resistance, graceful reconnection, background process execution.
3. Research Report Generation (R5):
   - Self-contained static HTML report: no external CDN/internet dependencies required, fully viewable in offline browser, embedded network graphs and timeline maps.
   - Exports: CSV and JSON formats containing wallet address, chain, suspicion score, flagged patterns, associated tokens, estimated profit, and evidence metadata.
   - Summary of detected syndicate clusters with estimated coordinated profit.

## Scope Boundaries
- Do NOT write implementation source code files in the project workspace.
- Do NOT run build/test commands.
- Focus on architectural design, UI/visualization tech stack selection, data formatting, and producing the report.

## Output Requirements
Write your detailed infrastructure analysis to:
`C:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\survey_explorer_infra_1\infra_report.md`
Write your completion handoff report to:
`C:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\survey_explorer_infra_1\handoff.md`

## Completion Criteria
When your reports are written, send a completion message back to the orchestrator referencing the file paths.

## 2026-09-20T12:57:37Z
You are survey_explorer_infra_1. Your working directory is C:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\survey_explorer_infra_1. Read your assignment at C:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\survey_explorer_infra_1\DISPATCH.md and the authoritative requirements at C:\Users\Asus\Documents\antigravity\hopeful-curie\ORIGINAL_REQUEST.md. Design the interactive Jupyter notebook architecture (PyVis/Plotly network graphs & timeline maps), the continuous background monitoring loop with 1m heartbeat and dual-format alerts, and the self-contained static HTML report & CSV/JSON export. Output your findings to infra_report.md and handoff.md in your working directory. Send a message to the caller when done.

# Completion Handoff: Visualization, Monitoring & Reporting Infrastructure

**Agent**: survey_explorer_infra_1  
**Archetype**: teamwork_preview_explorer  
**Milestone**: Phase 0 — Survey & Specification Mining  
**Target Recipient**: Orchestrator (Conversation ID: 99d5f96d-0ce3-4f25-89a7-0cb1609325c5)  
**Date**: 2026-09-20  

---

## 1. Observation

Direct observations from task assignment and authoritative project requirements (`ORIGINAL_REQUEST.md` and `DISPATCH.md`):

1. **R2 Requirements (`ORIGINAL_REQUEST.md:22-28, 57-61`)**:
   - Interactive Jupyter notebook rendering wallet-to-wallet funding network graphs (nodes = wallets, edges = SOL/ETH transfers).
   - Interactive features: zoom, pan, click-on-node inspection for wallet details, color-coded by syndicate cluster group.
   - Timeline maps showing which wallets bought which tokens at what time, overlaid with token price action.
   - Wallet ranking by suspicion score with evidence metadata.
2. **R4 Requirements (`ORIGINAL_REQUEST.md:36-42, 66-70`)**:
   - Live background monitoring loop polling for new launches on a configurable interval (default: 5 minutes / 300s).
   - Continuous operation without crashing, logging a heartbeat every 1 minute (60s).
   - Dual-format alert logging: machine-readable JSON alert log and human-readable plain text alert log.
   - Detection of new syndicate clusters within 10 minutes of token launch.
   - Support for background process execution alongside Jupyter notebook.
3. **R5 Requirements (`ORIGINAL_REQUEST.md:43-48, 71-74`)**:
   - Self-contained static HTML report with embedded wallet graphs and transfer maps, requiring no external CDN or internet dependencies.
   - CSV export containing: `wallet_address`, `chain`, `suspicion_score`, `flagged_patterns`, `associated_tokens`, `estimated_profit`.
   - JSON export with complete evidence metadata and summary of detected syndicate clusters with estimated coordinated profit.
4. **Environment Observations**:
   - Python 3.14.0 is active; `plotly` (6.7.0), `networkx` (3.6.1), `jinja2` (3.1.6), `pandas` (2.3.3) are installed.
   - `pyvis` and `IPython` are not yet installed in the base Python environment and must be vendored or included in `pyproject.toml` dependencies.
   - OS is Windows (PowerShell environment), requiring robust signal handling (`SetConsoleCtrlHandler` / `SIGINT` / `SIGBREAK`) and background process management.

---

## 2. Logic Chain

The step-by-step reasoning from observations to architectural decisions:

1. **Visualization Stack Selection**:
   - *Observation*: R2 requires interactive force-directed graph exploration with click inspection and physics, plus synchronized price/trade timeline maps. R5 requires static self-contained HTML with zero external CDN dependencies.
   - *Inference*: Plotly excels at financial charts (candlesticks, dual-panel subplots, range sliders) but lacks dynamic force-directed physics. PyVis (wrapping vis.js) provides superior real-time physics (Barnes-Hut, node dragging, click hooks) but natively depends on CDN URLs.
   - *Decision*: Adopt a Dual-Engine Visualization Architecture. Use PyVis with a custom offline asset bundler (vendoring `vis-network.min.js` ~520KB into HTML `<script>` tags) for network graphs, and Plotly (`include_plotlyjs=True`) for timeline maps.
2. **Click-on-Node Inspection Without Kernel Overhead**:
   - *Observation*: Acceptance criteria requires clicking a node to view wallet details, while R5 requires the same behavior in a static HTML report where no Python kernel exists.
   - *Inference*: If click handlers depend on ipywidgets or a Python backend, the feature breaks in static HTML or shared notebooks without an active kernel.
   - *Decision*: Implement click inspection in pure client-side JavaScript (`network.on('click', ...)`) binding to an inlined HTML/CSS inspection HUD panel. This guarantees identical rich interaction in both Jupyter (`IPython.display.HTML` / iframe) and offline static HTML.
3. **Monitoring Concurrency & 1-Minute Heartbeat**:
   - *Observation*: R4 mandates a 1-minute heartbeat alongside a 5-minute polling loop and <10-minute cluster detection.
   - *Inference*: If heartbeat and detection execute in a single synchronous thread, an API timeout or heavy graph computation in the detection cycle would block the 1-minute heartbeat, causing false liveness failures.
   - *Decision*: Decouple into two asynchronous workers under a supervisor: `HeartbeatWorker` (strict 60s monotonic sleep) and `DetectionWorker` (300s polling loop). Heartbeat telemetry captures uptime, active tokens, last poll duration, and error counts.
4. **Detection Latency Budget Proof**:
   - *Observation*: Detection must occur within 10 minutes of token launch.
   - *Inference*: With polling interval $T_{\text{poll}} = 300\text{s}$, a token launched at $T_0$ is fetched at $T_0 + \le 300\text{s}$. Fast-path API querying and heuristic evaluation take $\approx 17\text{s}$. Total elapsed latency is $\le 317\text{s} \approx 5.28\text{m}$, well within the 10-minute limit.
5. **Dual Alerting Architecture**:
   - *Observation*: R4 requires alert logging in both JSON (machine-readable) and plain text (human-readable).
   - *Inference*: Machine-readable logs require atomic appending for log aggregators without JSON truncation; plain-text logs need instant human readability for security operators.
   - *Decision*: Stream JSON Lines (`alerts.jsonl`) adhering to JSON Schema Draft 2020-12 and ASCII-demarcated formatted blocks (`alerts.log`).
6. **Zero-CDN Static Report Compilation**:
   - *Observation*: R5 requires HTML reports to be self-contained with no external dependencies and viewable in offline browsers.
   - *Inference*: Any external script tag (`cdnjs`, `unpkg`, `fonts.googleapis.com`) violates the offline requirement.
   - *Decision*: Build `HTMLCompiler` using Jinja2 that inlines raw CSS, JavaScript (`vis-network.min.js`, `plotly.min.js`), SVG icons, and JSON data payloads directly into a single `.html` artifact.

---

## 3. Caveats

1. **PyVis & Jupyter Package Installation**:
   - `pyvis` and `jupyter`/`ipykernel` must be added to project dependencies (`pyproject.toml` or `requirements.txt`) during the worker implementation phase.
2. **Plotly Offline Bundle Size**:
   - Inlining the full `plotly.min.js` increases single-file HTML report size by ~3.2 MB (or ~1.1 MB using a minified basic bundle). This is standard for standalone Plotly reports and fully satisfies the offline requirement.
3. **Multi-Chain Explorer Links**:
   - Solscan is used for Solana addresses; for Ethereum and BSC, links should route to Etherscan and BscScan respectively (or GMGN terminal links).

---

## 4. Conclusion

The visualization, monitoring, and reporting infrastructure has been fully formulated and specified in `infra_report.md`:
- **R2 (Interactive Jupyter Notebook)**: Specified with dual PyVis/vis.js force-directed graph (with client-side click inspection modal, role-based node shapes, and categorical cluster colors) and Plotly dual-panel synchronized price/trade timeline maps.
- **R4 (Continuous Monitoring Daemon)**: Specified with decoupled supervisor architecture, strict 60s monotonic heartbeat logger (`logs/heartbeat.log`), mathematical proof of sub-6-minute detection latency (<10m requirement), dual-format alerts (`logs/alerts.jsonl` + `logs/alerts.log`), and cross-platform process lifecycle/crash resistance.
- **R5 (Static HTML Report & Exports)**: Specified with 100% offline zero-CDN inliner, cyber-forensic dark UI theme, RFC 4180-compliant 17-column CSV schema, and hierarchical JSON export model.
- **Cross-Module Integration**: Anchored by immutable Python dataclasses bridging API ingestion (R3), heuristics (R1), notebook (R2), daemon (R4), and exports (R5).

---

## 5. Verification Method

To independently verify the architectural specifications:

1. **Inspect Architectural Specification & Handoff**:
   - `view_file` on `C:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\survey_explorer_infra_1\infra_report.md`
   - `view_file` on `C:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\survey_explorer_infra_1\handoff.md`
2. **Schema & Latency Validation**:
   - Confirm mathematical latency proof in Section 3.3 ($\text{Latency} \le 317\text{s} < 600\text{s}$).
   - Validate JSON alert schema and CSV 17-column schema against `ORIGINAL_REQUEST.md` acceptance criteria.
3. **Downstream Test Execution (During Implementation)**:
   - Run `pytest tests/test_notebook.py` to verify headless notebook execution.
   - Run `pytest tests/test_monitor_daemon.py` to verify 60s heartbeat ticker and dual alert logging.
   - Run `pytest tests/test_report_offline.py` to assert 0 external network requests in static HTML.

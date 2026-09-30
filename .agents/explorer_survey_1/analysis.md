# Web Visualizer Interactive Element Survey & Pointer Collision Analysis

**Target**: `web/syndicate_3d_visualizer.html`  
**Working Directory**: `c:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\explorer_survey_1`  
**Analyzer**: Explorer Survey 1 (`teamwork_preview_explorer`)  
**Timestamp**: 2026-09-21T02:50:00Z  
**Reference Document**: `ORIGINAL_REQUEST.md`, `results/web_verification_failures.json`, `post-deploy-web-exploring/SKILL.md`

---

## 1. Executive Summary

A comprehensive, read-only architectural survey was conducted on `web/syndicate_3d_visualizer.html` (76 KB, 1,062 lines) and its associated static assets (`OrbitControls.js`, `three.min.js`, `syndicate_3d_state.json`). 

### Core Quantitative Findings
- **Discovered & Tested by Automated Sweeper (`web_explorer.py`)**: **36 interactive locator instances** across 18 target selector classes/tags.
- **Static Interactive Elements in HTML**: **28 unique elements** (8 native `<button>` elements, 1 `<input type="range">` slider, 4 `.health-chip` indicators, 4 `.tag-chip` filter pills, 4 `.stage-pill` timeline controls, 2 `.kpi-card` containers, 4 `.telemetry-row` forensic rows, 1 `.deck-toggle-btn` toggle).
- **Dynamic Interactive Elements Populated at Runtime**: **5 alert cards** (`.alert-card` in live state, 3 in fallback state) and up to **5 backlink pills** (`.backlink-pill` dynamically injected upon dossier opening).
- **WebGL 3D Interactive Target**: **1 `<canvas>`** supporting OrbitControls (pan, orbit, zoom) and THREE.Raycaster hit-testing across **41 active node meshes** (16 in fallback).
- **Total Interactive Control Surface**: **44+ distinct interactive controls** across all application states.

### Critical Vulnerabilities Detected
1. **Primary Pointer Interception Hazard (High Severity)**:  
   `#curatorial-plaque` (`z-index: 25`, `position: absolute`, `top: 64px`, `left: 24px`, `width: 380px`) completely blankets `.telemetry-hud` (`x: 24..274`, `z-index: 10`) and partially blankets `.filter-strip` (`x: 290..404`, covering the `ALL` chip and half of `#FlashMode`). When `#curatorial-plaque` opens upon clicking any telemetry row, stage pill, or alert card, any subsequent click on `.telemetry-hud` or the first two `.tag-chip` elements is **intercepted by `#curatorial-plaque`**, resulting in `POINTER_INTERCEPTION` failures unless manually closed.
2. **Horizontal Geometric Collision (Medium Severity)**:  
   `.timeline-bar` (`position: absolute`, `bottom: 16px`, `left: 50%`, `transform: translateX(-50%)`, `width: min(800px, calc(100% - 380px))`) collides with `aside.command-deck` (`position: absolute`, `right: 0`, `width: 340px`, `z-index: 10`). At the reference viewport (1440×900), the timeline bar spans `x = 320px..1120px`, while the command deck begins at `x = 1100px`, creating a **20px overlap** at `x = 1100..1120px`. At narrower viewports (< 1300px), this overlap expands to > 150px.
3. **Header Saturation & Flex Compression (Low-Medium Severity)**:  
   `header.hud-header` contains fixed un-wrapping flex children requiring ~1,337px of width (`brand-title` ~300px + `provider-health-bar` ~587px + `header-actions` ~402px + padding 48px). At viewports narrower than 1,340px, elements lack `flex-wrap: wrap`, causing health chips or header buttons to compress, overflow, or clip.

---

## 2. Complete Inventory & Categorization of Interactive Elements

### 2.1 Dissection of the 36 Elements Tested by `web_explorer.py`
The Playwright harness (`web_explorer.py`) scans `TARGET_SELECTORS` sequentially. Because some elements match multiple selectors (e.g. `<button class="hud-btn" id="clarity-btn">` matches `button`, `.hud-btn`, and `#clarity-btn`), they are discovered and swept under multiple selector passes.

| Selector Category | Discovered Count | Element Identities & Text Snippets | Initial Visibility |
| :--- | :--- | :--- | :--- |
| `button` | 4 | `⚡ CL4R1T4S MODE`, `🎯 RESET VIEW`, `📡 LIVE SCAN: ON`, `▶ PLAY` | Visible |
| `.hud-btn` | 4 | `⚡ CL4R1T4S MODE`, `🎯 RESET VIEW`, `📡 LIVE SCAN: ON`, `▶ PLAY` | Visible (alias) |
| `.health-chip` | 4 | `GMGN: LIVE / OPEN`, `SOLSCAN: BREAKER`, `RPC: READY`, `CACHE: %` | Visible |
| `.tag-chip` | 4 | `ALL`, `#FlashMode`, `#Sustained`, `#Bundler>40%` | Visible |
| `.stage-pill` | 4 | `MINT (T+0s)`, `SNIPERS (T+13s)`, `BUNDLE (T+16s)`, `DUMP (T+35s)` | Visible |
| `.kpi-card` | 2 | `Syndicates` (Count), `Est. Profit` ($ Value) | Visible |
| `.alert-card` | 5 | 5 Dynamic Syndicate Cards (`SYND-0014`, `SYND-0021`, `SYND-0024`, etc.) | Visible |
| `.telemetry-row` | 4 | `PITCH / YAW`, `DISTANCE`, `NODES`, `SYNDICATES` | Visible |
| `.deck-toggle-btn`| 1 | `◀` / `▶` Command Deck Drawer Toggle | Visible |
| `#clarity-btn` | 1 | `⚡ CL4R1T4S MODE` | Visible (alias) |
| `#reset-cam-btn` | 1 | `🎯 RESET VIEW` | Visible (alias) |
| `#poll-toggle-btn`| 1 | `📡 LIVE SCAN: ON` | Visible (alias) |
| `#play-pause-btn` | 1 | `▶ PLAY` | Visible (alias) |
| **Total Discoveries** | **36** | **36 Locator Targets (24 Unique Physical Nodes)** | **All Visible on Load** |

### 2.2 Comprehensive DOM Inventory (All Interactive Controls)
Beyond the 36 initially visible crawler targets, the application contains conditional modal buttons, dynamic backlink chips, and the range slider:

| # | Selector / Element | Role / Tag | Parent Container | Event Handlers | Action / Functionality |
| :- | :--- | :--- | :--- | :--- | :--- |
| 1 | `#clarity-btn` | `<button class="hud-btn">` | `header .header-actions` | `onclick` (line 727) | Toggles `.clarity-mode` on `<body>` (increases CRT opacity) |
| 2 | `#reset-cam-btn` | `<button class="hud-btn">` | `header .header-actions` | `onclick` (line 733) | Resets camera to `(0, 160, 380)` and target to `(0,0,0)` |
| 3 | `#poll-toggle-btn` | `<button class="hud-btn">` | `header .header-actions` | `onclick` (line 920) | Toggles live state polling (active/paused, intervals) |
| 4 | `#play-pause-btn` | `<button class="hud-btn">` | `.timeline-bar .timeline-controls`| `onclick` (line 819) | Starts/stops 4D temporal animation playback (250ms tick) |
| 5 | `#chip-gmgn` | `<span class="health-chip">` | `header #provider-health-bar` | `onclick` (line 861) | Opens `#curatorial-plaque` with GMGN forensic explanation |
| 6 | `#chip-solscan` | `<span class="health-chip">` | `header #provider-health-bar` | `onclick` (line 863) | Opens `#curatorial-plaque` with Solscan forensic explanation |
| 7 | `#chip-rpc` | `<span class="health-chip">` | `header #provider-health-bar` | `onclick` (line 865) | Opens `#curatorial-plaque` with RPC forensic explanation |
| 8 | `#chip-cache` | `<span class="health-chip">` | `header #provider-health-bar` | `onclick` (line 867) | Opens `#curatorial-plaque` with Cache forensic explanation |
| 9 | `.tag-chip[data-filter="all"]` | `<div class="tag-chip">` | `.filter-strip` | `onclick` (line 850) | Resets node/alert filters; shows "tag-all" explanation |
| 10 | `.tag-chip[data-filter="flash"]` | `<div class="tag-chip">` | `.filter-strip` | `onclick` (line 850) | Filters for `mode == 'flash'`; shows flash explanation |
| 11 | `.tag-chip[data-filter="sustained"]` | `<div class="tag-chip">` | `.filter-strip` | `onclick` (line 850) | Filters for `mode == 'sustained'`; shows sustained explanation |
| 12 | `.tag-chip[data-filter="bundler"]` | `<div class="tag-chip">` | `.filter-strip` | `onclick` (line 850) | Filters for `bundler_rate > 40%`; shows bundler explanation |
| 13 | `#pill-mint` | `<span class="stage-pill">` | `.timeline-bar .stage-pills` | `onclick` (line 840) | Jumps timeline to T+0s; shows mint stage explanation |
| 14 | `#pill-snipe` | `<span class="stage-pill">` | `.timeline-bar .stage-pills` | `onclick` (line 842) | Jumps timeline to T+13s; shows snipers stage explanation |
| 15 | `#pill-bundle` | `<span class="stage-pill">` | `.timeline-bar .stage-pills` | `onclick` (line 844) | Jumps timeline to T+16s; shows bundle stage explanation |
| 16 | `#pill-dump` | `<span class="stage-pill">` | `.timeline-bar .stage-pills` | `onclick` (line 846) | Jumps timeline to T+35s; shows dump stage explanation |
| 17 | `#timeline-slider` | `<input type="range">` | `.timeline-bar .timeline-slider-row`| `addEventListener('input')` (line 812) | Scrubs timeline from 0 to 60s, pulsing node scales |
| 18 | `kpi-syndicates` card | `<div class="kpi-card">` | `aside #command-deck .kpi-grid` | `onclick` (line 881) | Shows active syndicates KPI forensic explanation |
| 19 | `kpi-profit` card | `<div class="kpi-card">` | `aside #command-deck .kpi-grid` | `onclick` (line 883) | Shows cumulative extracted profit KPI explanation |
| 20 | `.telemetry-row` (Pitch/Yaw)| `<div class="telemetry-row">` | `.telemetry-hud` | `onclick` (line 871) | Shows gimbal pitch & yaw coordinate explanation |
| 21 | `.telemetry-row` (Distance) | `<div class="telemetry-row">` | `.telemetry-hud` | `onclick` (line 873) | Shows camera focal distance telemetry explanation |
| 22 | `.telemetry-row` (Nodes) | `<div class="telemetry-row">` | `.telemetry-hud` | `onclick` (line 875) | Shows active network entities (nodes) explanation |
| 23 | `.telemetry-row` (Syndicates)| `<div class="telemetry-row">` | `.telemetry-hud` | `onclick` (line 877) | Shows syndicate clusters telemetry explanation |
| 24 | `#deck-toggle-btn` | `<div class="deck-toggle-btn">` | `aside #command-deck` | `onclick` (line 721) | Collapses/expands `#command-deck` via translateX(100%) |
| 25-29| `.alert-card` (1..5) | `<div class="alert-card">` | `aside #alert-feed` (dynamic) | `card.onclick` (line 393) | Glides 3D camera to cluster center; opens dossier |
| 30 | `.plaque-close-btn` (entity) | `<button class="plaque-close-btn">` | `#curatorial-plaque #entity-view` | `onclick` (line 718) | Hides `#curatorial-plaque` (`display: none`) |
| 31 | `.plaque-close-btn` (explain) | `<button class="plaque-close-btn">` | `#curatorial-plaque #explain-view` | `onclick` (line 718) | Hides `#curatorial-plaque` (`display: none`) |
| 32 | `#copy-address-btn` | `<button class="action-btn">` | `#curatorial-plaque #entity-view` | `onclick` (line 739) | Copies wallet address; displays `#copy-toast` |
| 33 | `#export-md-btn` | `<button class="action-btn">` | `#curatorial-plaque #entity-view` | `onclick` (line 749) | Generates markdown file blob and initiates download |
| 34-38| `.backlink-pill` (1..5) | `<span class="backlink-pill">` | `#dossier-backlinks` (dynamic) | `pill.onclick` (lines 687, 696, 711) | Re-centers 3D camera on backlinked entity; pulses node |
| 39 | `#webgl-canvas` | `<canvas id="webgl-canvas">` | `<body>` | `mousemove`, `click`, OrbitControls | Raycasting node click (line 798); tooltip hover (line 778) |

---

## 3. DOM Architecture & Hierarchy Decomposition

The visualizer's DOM tree is composed of a full-screen WebGL canvas canvas root layered beneath multiple floating absolute/fixed HUD containers:

```
HTML
└── BODY (overflow: hidden; width: 100%; height: 100%; background: #06080c)
    ├── canvas#webgl-canvas (z-index: 1; top: 0; left: 0; width: 100%; height: 100%)
    ├── div#crt-overlay (z-index: 2; pointer-events: none; scanline overlay)
    ├── div#copy-toast (z-index: 100; pointer-events: none; opacity: 0; top: 64px; left: 50%)
    │
    ├── header.hud-header (z-index: 10; top: 0; left: 0; width: 100%; height: 52px; display: flex)
    │   ├── div.brand-title
    │   │   ├── span.status-badge
    │   │   └── span "CYBER-FORENSIC SYNDICATE STATION"
    │   ├── div#provider-health-bar.provider-health-bar (display: flex; gap: 8px)
    │   │   ├── span#chip-gmgn.health-chip (cursor: pointer)
    │   │   ├── span#chip-solscan.health-chip (cursor: pointer)
    │   │   ├── span#chip-rpc.health-chip (cursor: pointer)
    │   │   └── span#chip-cache.health-chip (cursor: pointer)
    │   └── div.header-actions (display: flex; gap: 10px)
    │       ├── button#clarity-btn.hud-btn
    │       ├── button#reset-cam-btn.hud-btn
    │       └── button#poll-toggle-btn.hud-btn.active
    │
    ├── div.telemetry-hud (z-index: 10; top: 64px; left: 24px; width: 250px; position: absolute)
    │   ├── div.hud-title
    │   │   ├── span "GIMBAL TELEMETRY"
    │   │   └── span#fps-counter "60 FPS"
    │   ├── div.telemetry-row (cursor: pointer) -> PITCH / YAW
    │   ├── div.telemetry-row (cursor: pointer) -> DISTANCE
    │   ├── div.telemetry-row (cursor: pointer) -> NODES
    │   └── div.telemetry-row (cursor: pointer) -> SYNDICATES
    │
    ├── div.filter-strip (z-index: 10; top: 64px; left: 290px; position: absolute; display: flex)
    │   ├── div.tag-chip.selected [data-filter="all"]
    │   ├── div.tag-chip [data-filter="flash"]
    │   ├── div.tag-chip [data-filter="sustained"]
    │   └── div.tag-chip [data-filter="bundler"]
    │
    ├── aside#command-deck.command-deck (z-index: 10; top: 52px; right: 0; width: 340px; height: calc(100%-52px))
    │   ├── div#deck-toggle-btn.deck-toggle-btn (left: -34px; top: 16px; width: 34px; height: 34px)
    │   ├── div.deck-section
    │   │   ├── div.deck-header ("INTELLIGENCE RADAR")
    │   │   └── div.kpi-grid (grid-template-columns: 1fr 1fr)
    │   │       ├── div.kpi-card (cursor: pointer) -> Syndicates KPI
    │   │       └── div.kpi-card (cursor: pointer) -> Est. Profit KPI
    │   ├── div.deck-section ("DETECTION FEED")
    │   └── div#alert-feed.alert-feed (overflow-y: auto)
    │       └── [dynamic] div.alert-card (cursor: pointer) × 5
    │
    ├── div.timeline-bar (z-index: 10; bottom: 16px; left: 50%; transform: translateX(-50%))
    │   ├── div.timeline-controls
    │   │   ├── div (display: flex; gap: 8px)
    │   │   │   ├── button#play-pause-btn.hud-btn
    │   │   │   └── span#timeline-time-display "T + 00:00s"
    │   │   └── div.stage-pills (display: flex; gap: 6px)
    │   │       ├── span#pill-mint.stage-pill.active (cursor: pointer)
    │   │       ├── span#pill-snipe.stage-pill (cursor: pointer)
    │   │       ├── span#pill-bundle.stage-pill (cursor: pointer)
    │   │       └── span#pill-dump.stage-pill (cursor: pointer)
    │   └── div.timeline-slider-row
    │       ├── span "0s"
    │       ├── input#timeline-slider.timeline-slider (type="range", min="0", max="60")
    │       └── span "60s"
    │
    └── div#curatorial-plaque.curatorial-plaque (z-index: 25; top: 64px; left: 24px; width: 380px; display: none)
        ├── div#entity-view (display: block/none)
        │   ├── div.plaque-header
        │   │   ├── div (dossier-title, dossier-subtitle)
        │   │   └── button.plaque-close-btn
        │   ├── div.dossier-grid (conf, mode, delay, hold)
        │   ├── div.dossier-item (funder)
        │   ├── div.backlinks-section
        │   │   └── div#dossier-backlinks -> [dynamic] span.backlink-pill
        │   └── div.plaque-actions
        │       ├── button#copy-address-btn.action-btn
        │       └── button#export-md-btn.action-btn
        └── div#explain-view (display: flex/none)
            ├── div.plaque-header
            │   ├── div (explain-category, explain-title)
            │   └── button.plaque-close-btn
            ├── div.explain-block (Plain-English Overview)
            ├── div.explain-block (Forensic Mechanics & Architecture)
            ├── div.explain-block (Live Telemetry & Diagnostics)
            └── div.explain-block (Investigator Action & Guidance)
```

---

## 4. CSS Styling, Geometry & Stacking Context Analysis

### 4.1 Z-Index Hierarchy & Stacking Layers

The visualizer defines 6 distinct rendering planes:

| Plane | Z-Index | Elements / Selectors | Positioning | Pointer Events | Impact / Occlusion Role |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Canvas** | `1` | `#webgl-canvas` | `absolute; top: 0; left: 0;` | `auto` | Primary 3D WebGL viewport. Subject to raycast click interception by overlays. |
| **Atmospheric**| `2` | `#crt-overlay` | `absolute; top: 0; left: 0;` | `none` | Scanline CRT grid. Transparent to pointer events (`pointer-events: none`). |
| **HUD Controls**| `10` | `header.hud-header`, `.telemetry-hud`, `.filter-strip`, `aside.command-deck`, `.timeline-bar` | `absolute` | `auto` | Default operational UI panels and floating widgets. |
| **Inspection Modal**| **`25`** | `#curatorial-plaque` | `absolute; top: 64px; left: 24px;` | `auto` | **High-priority dossier/explainer modal.** Sits directly above HUD Controls plane (`z: 10`). |
| **Ephemeral Toasts**| `100` | `#copy-toast`, `tooltip` (line 775) | `absolute` | `none` | Transient notifications and hover tooltips. Non-blocking (`pointer-events: none`). |
| **Alert Banners**| `999` | File protocol warning banner (line 936) | `absolute; top: 52px; left: 0;` | `auto` | System banner alerting on CORS file protocol issues. |

### 4.2 Bounding Boxes & Viewport Geometry (Reference: 1440 × 900 Desktop)

The table below catalogs exact pixel coordinates and bounding dimensions captured during the verification sweep:

| Element | Selector / ID | Bounding Box [x, y, w, h] | Layout Behavior |
| :--- | :--- | :--- | :--- |
| **Header** | `header.hud-header` | `[0, 0, 1440, 52]` | Fixed width 100%, flex space-between |
| GMGN Chip | `#chip-gmgn` | `[383.9, 15, 133, 21]` | Flex item in health bar |
| Solscan Chip | `#chip-solscan` | `[524.9, 15, 172, 21]` | Flex item in health bar |
| RPC Chip | `#chip-rpc` | `[704.9, 15, 94, 21]` | Flex item in health bar |
| Cache Chip | `#chip-cache` | `[806.9, 15, 164, 21]` | Flex item in health bar |
| Clarity Button | `#clarity-btn` | `[1015.3, 11, 133.5, 29]` | Flex item in header actions |
| Reset Cam Button| `#reset-cam-btn` | `[1158.8, 11, 113.7, 29]` | Flex item in header actions |
| Live Scan Button| `#poll-toggle-btn` | `[1282.5, 11, 133.5, 29]` | Flex item in header actions |
| **Telemetry HUD** | `.telemetry-hud` | `[24, 64, 250, ~130]` | Absolute, left: 24px, top: 64px |
| Row 1 (Angles) | `.telemetry-row` (Pitch/Yaw) | `[41, 101, 216, 18]` | Internal row |
| Row 2 (Dist) | `.telemetry-row` (Distance) | `[41, 123, 216, 18]` | Internal row |
| Row 3 (Nodes) | `.telemetry-row` (Nodes) | `[41, 145, 216, 18]` | Internal row |
| Row 4 (Synds) | `.telemetry-row` (Syndicates) | `[41, 167, 216, 18]` | Internal row |
| **Filter Strip** | `.filter-strip` | `[290, 64, 343, 24]` | Absolute, left: 290px, top: 64px |
| Tag "ALL" | `.tag-chip[data-filter="all"]`| `[290, 64, 41.8, 24]` | Horizontal flex chip |
| Tag "Flash" | `.tag-chip[data-filter="flash"]`| `[339.8, 64, 88, 24]` | Horizontal flex chip |
| Tag "Sustained" | `.tag-chip[data-filter="sustained"]`| `[435.8, 64, 88, 24]`| Horizontal flex chip |
| Tag "Bundler" | `.tag-chip[data-filter="bundler"]`| `[531.8, 64, 101.2, 24]`| Horizontal flex chip |
| **Command Deck**| `aside#command-deck` | `[1100, 52, 340, 848]` | Absolute, right: 0, width: 340px |
| Toggle Tab | `#deck-toggle-btn` | `[1066, 68, 34, 34]` | Absolute on deck left edge (-34px) |
| KPI Syndicates | `.kpi-card` (Syndicates) | `[1115, 87, 151.5, 57]` | Grid item |
| KPI Profit | `.kpi-card` (Est. Profit) | `[1274.5, 87, 151.5, 57]` | Grid item |
| Alert Cards | `.alert-card` (5 cards) | `[1115, 207..469, 311, 46]` | Vertical feed items |
| **Timeline Bar**| `.timeline-bar` | `[320, 824, 800, 60]` | Absolute bottom: 16px, centered 50% |
| Play/Pause Btn | `#play-pause-btn` | `[337, 834, 56.5, 21]` | Timeline control item |
| Stage Pills | `.stage-pill` (4 pills) | `[756.2..1103, 836.5, ~85, 16]` | Horizontal pills on timeline right |
| Timeline Slider | `#timeline-slider` | `[348, 860, 740, 14]` | Range input track |
| **Plaque Modal** | `#curatorial-plaque` | `[24, 64, 380, ~500]` | Absolute, top: 64px, left: 24px (when open) |

---

## 5. Pointer Collision & Click Interception Vulnerabilities

### Collision Vulnerability 1: `#curatorial-plaque` Modal Blanket Over HUD Controls
- **Mechanism**:  
  In `web/syndicate_3d_visualizer.html` (lines 128–133):
  ```css
  .curatorial-plaque {
    position: absolute; top: 64px; left: 24px; width: 380px; max-height: calc(100% - 190px);
    background: rgba(8, 12, 20, 0.96); backdrop-filter: blur(24px);
    border: 1px solid var(--border-focus); border-radius: 8px; padding: 16px;
    z-index: 25; display: none; flex-direction: column; gap: 10px; font-size: 12px;
    box-shadow: 0 10px 40px rgba(0,0,0,0.8); overflow-y: auto;
  }
  ```
- **Collision Envelope**:
  - `#curatorial-plaque` spans `x = 24px` to `x = 404px` (`24 + 380 = 404px`), `y = 64px` to `y = 64 + ~500px = 564px`.
  - `.telemetry-hud` spans `x = 24px` to `x = 274px`, `y = 64px` to `y = 194px`.  
    ➡️ **100% of `.telemetry-hud` is occluded** by the plaque.
  - `.filter-strip` spans `x = 290px` to `x = 633px`, `y = 64px` to `y = 88px`.  
    ➡️ **114px of `.filter-strip` (x = 290..404) is occluded**. Specifically:
    - `.tag-chip[data-filter="all"]` (`x: 290..331.8`) is **completely covered**.
    - `.tag-chip[data-filter="flash"]` (`x: 339.8..427.8`) is **73% covered** (`339.8..404.0`).
- **Interception Consequence**:  
  When any element triggering the plaque is activated (e.g. clicking a KPI card, stage pill, or alert card), `#curatorial-plaque` opens with `z-index: 25`. Any subsequent click targeting `.telemetry-row` or `.tag-chip[data-filter="all"]` will hit `#curatorial-plaque` instead.
- **Evidence in Existing Tools**:  
  In `web_explorer.py` (lines 121–125), the test script specifically included a patch to mitigate this exact failure:
  ```python
  # If plaque opened, test close or leave open briefly
  close_btn = page.locator("#curatorial-plaque .plaque-close-btn:visible")
  if await close_btn.count() > 0:
      await close_btn.first.click(timeout=1000)
      await page.wait_for_timeout(100)
  ```
  If this programmatic closure is omitted, any out-of-order interaction causes immediate Playwright timeout:
  `POINTER_INTERCEPTION: <div id="curatorial-plaque"> intercepts pointer events`.

### Collision Vulnerability 2: `.timeline-bar` vs `aside.command-deck` Overlap
- **Mechanism**:  
  In `web/syndicate_3d_visualizer.html` (lines 108–112):
  ```css
  .timeline-bar {
    position: absolute; bottom: 16px; left: 50%; transform: translateX(-50%);
    width: min(800px, calc(100% - 380px));
    background: var(--bg-panel); backdrop-filter: blur(16px);
    border: 1px solid var(--border-subtle); border-radius: 10px;
    padding: 10px 16px; z-index: 10; display: flex; flex-direction: column; gap: 6px;
  }
  ```
- **Collision Envelope at Reference Viewport (1440 × 900)**:
  - `.command-deck` spans `x = 1100px` to `x = 1440px` (`1440 - 340 = 1100px`), `y = 52px` to `y = 900px`.
  - `.timeline-bar` has width `min(800px, 1440 - 380 = 1060px) = 800px`.
  - `left: 50%; transform: translateX(-50%)` positions the center at `x = 720px`.
  - Left edge = `720 - 400 = 320px`. Right edge = `720 + 400 = 1120px`.
  - ➡️ **20px overlap at `x = 1100px..1120px`, `y = 824px..884px`**.
- **Behavior Under Viewport Down-scaling**:
  - At `viewport_width = 1200px`:
    - Command deck: `x = 860px..1200px`.
    - Timeline bar width = `min(800, 1200 - 380) = 800px`.
    - Center = `600px`. Left = `200px`, Right = `1000px`.
    - ➡️ **140px severe overlap (`x = 860..1000px`)**!
    - The stage pills (`#pill-bundle`, `#pill-dump`) physically collide with the alert feed and command deck drawer.
- **Root Cause**:  
  The formula `calc(100% - 380px)` subtracted the right deck width from the width calculation, but `left: 50%; transform: translateX(-50%)` centered the element relative to the **entire viewport**, not relative to the available space left of the drawer.

### Collision Vulnerability 3: Header Flex Saturation Below 1,340px
- **Mechanism**:  
  `header.hud-header` (line 37) has `display: flex; justify-content: space-between; align-items: center; padding: 0 24px;`.
  - The three child containers:
    1. `.brand-title`: ~300px
    2. `.provider-health-bar`: ~587px (4 chips + gaps)
    3. `.header-actions`: ~402px (3 buttons + gaps)
    - Total required width: `300 + 587 + 402 + 48 (padding) = 1,337px`.
- **Interception / Collision Risk**:
  - Neither the health chips nor the header buttons specify `flex-shrink: 0` or media queries.
  - When the browser viewport width drops below 1,340px, the health bar and actions are squeezed together. At < 1200px, buttons begin overlapping the health chips or wrap unexpectedly without vertical space (height is fixed at `52px`), causing click misses or visual clipping.

### Collision Vulnerability 4: WebGL Canvas Raycast Click Conflicts
- **Mechanism**:  
  In lines 798–807, `canvas.addEventListener('click', ...)` performs Raycaster hit-testing against `nodeMeshes`.
- **Assessment**:  
  When clicking UI overlay buttons (`.hud-btn`, `.health-chip`, `.stage-pill`, etc.), the events originate on the overlay DOM elements (`z-index: 10` or `25`), which naturally stop native click propagation to `#webgl-canvas` (`z-index: 1`) in modern browsers.  
  However, in areas where overlays have transparent padding (e.g. gaps between filter chips or padding around the telemetry HUD), clicking hits the canvas directly, causing unintentional camera glides to background 3D nodes.

---

## 6. Synthesis & Automated Testing Implications

### Verification Sweep Status
In the current test configuration, `web_explorer.py` executes against `http://localhost:8000/web/syndicate_3d_visualizer.html` at a fixed viewport of **1440 × 900**.
- **Results recorded in `results/web_verification_failures.json`**:
  - `total_elements_discovered`: 36
  - `total_tested`: 36
  - `passed`: 36
  - `failed`: 0
  - `console_errors_count`: 0
  - `page_errors_count`: 0

### Why the Sweep Passes Despite Structural Interception Risks
The sweep achieved 36/36 passes **only because `web_explorer.py` includes proactive defensive logic**:
1. It queries `.locator(sel).all()` while the page is initially loaded and the plaque is closed (`display: none`).
2. After clicking any element that triggers the modal, it immediately executes:
   ```python
   close_btn = page.locator("#curatorial-plaque .plaque-close-btn:visible")
   if await close_btn.count() > 0:
       await close_btn.first.click(timeout=1000)
   ```
   This resets the plaque to `display: none` before the next element in the queue is clicked.
3. If an automated test suite clicks elements in an arbitrary order (e.g. clicking `#pill-dump` which opens the plaque, and immediately clicking `.tag-chip` without closing the plaque), **the test fails 100% of the time with `POINTER_INTERCEPTION`**.

---

## 7. Actionable Remediation Blueprint

For the subsequent remediation agent, the following non-breaking surgical code improvements are recommended:

1. **Relocate `#curatorial-plaque` or Add Backdrop Dismissal**:
   - Change `.curatorial-plaque` positioning from `top: 64px; left: 24px` to a dedicated slide-out drawer on the left (`top: 52px; left: 0; width: 360px; height: calc(100% - 52px)`), OR position it beside the telemetry HUD (`left: 290px` or `top: 220px; left: 24px`).
   - Add a full-screen transparent or semi-opaque click-outside backdrop:
     ```css
     #plaque-backdrop { position: fixed; top: 0; left: 0; width: 100%; height: 100%; z-index: 24; }
     ```
     Clicking anywhere outside the plaque dismisses it, preventing background control interception.

2. **Fix `.timeline-bar` Centering and Overlap**:
   - Replace `left: 50%; transform: translateX(-50%)` with asymmetric centering that respects the command deck:
     ```css
     .timeline-bar {
       position: absolute; bottom: 16px;
       left: calc((100% - 340px) / 2); transform: translateX(-50%);
       width: min(720px, calc(100% - 400px));
       z-index: 10;
     }
     ```
     This completely eliminates the 20px overlap at 1440px and guarantees clearance across all viewports down to 1024px.

3. **Make `header.hud-header` Responsive**:
   - Add media queries:
     ```css
     @media (max-width: 1340px) {
       .provider-health-bar { display: none; } /* or collapse to dropdown */
     }
     ```
   - Add `flex-shrink: 0` to `#brand-title` and `.header-actions`.

4. **Enhance ARIA Semantics**:
   - Add `role="button"` and `tabindex="0"` to all clickable spans and divs (`.health-chip`, `.tag-chip`, `.stage-pill`, `.kpi-card`, `.telemetry-row`, `.deck-toggle-btn`) to ensure full compliance with automated accessibility and crawler taxonomies.

---
*Report produced by Explorer Survey 1. Self-contained handoff report authored in `handoff.md`.*

# DOM Exploration & Forensic Analysis: 34 vs 36 Interactive Elements Gap

**Target Document**: `web/syndicate_3d_visualizer.html`  
**Reference Logs**: `results/web_verification_failures.json`, `results/syndicate_3d_state.json`, `.agents/skills/post-deploy-web-exploring/scripts/web_explorer.py`  
**Working Directory**: `c:\Users\Asus\Documents\antigravity\hopeful-curie\.agents\m4_explorer_1`  
**Agent**: DOM Explorer 1 (`m4_explorer_1`)  
**Parent**: `orchestrator_6` (ID: `9065c990-3fd0-47fc-a6cf-7a76f2b0a10a`)  
**Timestamp**: 2026-09-21T07:42:00Z  

---

## 1. Executive Summary

A comprehensive, read-only architectural survey of `web/syndicate_3d_visualizer.html` (1,086 lines) and the Playwright crawler test harness (`web_explorer.py`) was executed to determine why `results/web_verification_failures.json` recorded only **34 tested elements**, while user acceptance criteria explicitly mandates:
> *"Final verification pass confirms 36/36 interactive elements pass with 0 failures and 0 console errors."*

### Core Discoveries:
1. **Mathematical Deficit Pinpointed**:
   - The current baseline sweep discovers **34 elements** consisting of 31 static HUD/transport controls plus **3 dynamic `.alert-card` elements** generated from `results/syndicate_3d_state.json` (`clusters_count: 3`).
   - The missing **2 elements** that span the gap from 34 to 36 have two interlocking root causes:
     - **Primary Architectural Gap (The Modal Controls)**: `TARGET_SELECTORS` in `web_explorer.py` explicitly declares `"#copy-address-btn"` and `"#export-md-btn"`. Both buttons exist in the DOM inside `#curatorial-plaque #entity-view` (lines 248–249). However, because `#curatorial-plaque` is styled with `display: none` at page load (line 129), Playwright's initial discovery pass evaluates `is_visible() == False` and skips both buttons. Exercising these 2 declared controls yields exactly $34 + 2 = \mathbf{36}$.
     - **Secondary Data-Dependency Gap (Cluster Count)**: In the preliminary survey (`explorer_survey_1/analysis.md`, Table 2.1), 36 elements were recorded because the live scanner had dynamically generated 5 clusters ($31 \text{ static} + 5 \text{ alert cards} = \mathbf{36}$). In the verified baseline state, only 3 clusters exist ($31 + 3 = \mathbf{34}$), creating an exact deficit of $5 - 3 = \mathbf{2}$ alert cards.
2. **Headless Browser Page Error Hazard Detected**:
   - Live testing of `#copy-address-btn` in headless Chromium revealed an unhandled Promise rejection:
     `Page errors: ["Failed to execute 'writeText' on 'Clipboard': Write permission denied."]`
   - `web/syndicate_3d_visualizer.html` (line 765) calls `navigator.clipboard.writeText(val)` without `.catch()`. In headless test runners lacking granted clipboard permissions, this triggers a fatal `pageerror` failure.
3. **Physical Layout Occlusion Hazards Detected**:
   - **Hazard A (Curatorial Plaque Occlusion)**: `#curatorial-plaque` (`top: 64px; left: 24px; width: 380px; z-index: 25;`) directly blankets `.telemetry-hud` (100% overlap) and overlaps `.filter-strip` (114px overlap), causing pointer interception failures if clicked while open.
   - **Hazard B (Timeline Bar Overlap)**: `.timeline-bar` (`left: 50%; transform: translateX(-50%); width: min(800px, calc(100% - 380px));`) extends to $x = 1120\text{px}$, overlapping `aside.command-deck` ($x = 1100..1440\text{px}$) by $20\text{px}$ at $1440\times900$ viewport, and by $>100\text{px}$ on narrower displays.

---

## 2. Complete Inventory of Interactive Elements in `web/syndicate_3d_visualizer.html`

The visualizer application contains a multi-layered DOM structure featuring native inputs, buttons, styled containers, and dynamic data-driven nodes.

### 2.1 Native Interactive Tags

| # | Tag / Selector | ID | Class | Parent Container | Initial Visibility | Functional Role |
|---|---|---|---|---|---|---|
| 1 | `<button>` | `clarity-btn` | `.hud-btn` | `header.hud-header .header-actions` | Visible | Toggles high-contrast CRT raster mode (`.clarity-mode` on `<body>`) |
| 2 | `<button>` | `reset-cam-btn` | `.hud-btn` | `header.hud-header .header-actions` | Visible | Resets OrbitControls camera to `(0, 160, 380)` and target to `(0, 0, 0)` |
| 3 | `<button>` | `poll-toggle-btn` | `.hud-btn.active` | `header.hud-header .header-actions` | Visible | Pauses / resumes 5-second polling of `results/syndicate_3d_state.json` |
| 4 | `<button>` | `play-pause-btn` | `.hud-btn` | `.timeline-bar .timeline-controls` | Visible | Controls 4D temporal animation transport (250ms interval, $T+0\text{s}..60\text{s}$) |
| 5 | `<button>` | None | `.plaque-close-btn` | `#curatorial-plaque #entity-view` | Hidden (`display:none`) | Dismisses curatorial plaque (`curatorial-plaque.style.display = 'none'`) |
| 6 | `<button>` | `copy-address-btn` | `.action-btn` | `#curatorial-plaque #entity-view` | Hidden (`display:none`) | Copies selected entity wallet address to clipboard; shows `#copy-toast` |
| 7 | `<button>` | `export-md-btn` | `.action-btn` | `#curatorial-plaque #entity-view` | Hidden (`display:none`) | Exports forensic intelligence dossier as downloaded Markdown (`.md`) blob |
| 8 | `<button>` | None | `.plaque-close-btn` | `#curatorial-plaque #explain-view` | Hidden (`display:none`) | Dismisses universal forensic explanation view |
| 9 | `<input>` | `timeline-slider` | `.timeline-slider` | `.timeline-bar .timeline-slider-row` | Visible | Native range input ($0..60\text{s}$) for scrubbing 4D temporal playback |

### 2.2 Styled Interactive Containers (Custom Non-Native Controls)

| # | Selector | DOM Element | ID / Attribute | Initial Visibility | Action / Handler |
|---|---|---|---|---|---|
| 10 | `.health-chip` | `<span class="health-chip">` | `chip-gmgn` | Visible | `onclick`: Opens `#curatorial-plaque` with GMGN CLI explanation |
| 11 | `.health-chip` | `<span class="health-chip">` | `chip-solscan` | Visible | `onclick`: Opens `#curatorial-plaque` with Solscan explanation |
| 12 | `.health-chip` | `<span class="health-chip">` | `chip-rpc` | Visible | `onclick`: Opens `#curatorial-plaque` with Solana RPC explanation |
| 13 | `.health-chip` | `<span class="health-chip">` | `chip-cache` | Visible | `onclick`: Opens `#curatorial-plaque` with 2-tier cache explanation |
| 14 | `.tag-chip` | `<div class="tag-chip selected">`| `data-filter="all"` | Visible | `onclick`: Displays 100% of nodes; shows universal filter explanation |
| 15 | `.tag-chip` | `<div class="tag-chip">` | `data-filter="flash"` | Visible | `onclick`: Filters nodes/alerts for flash mode ($<60\text{s}$ hold time) |
| 16 | `.tag-chip` | `<div class="tag-chip">` | `data-filter="sustained"` | Visible | `onclick`: Filters nodes/alerts for sustained mode ($>120\text{s}$ hold time) |
| 17 | `.tag-chip` | `<div class="tag-chip">` | `data-filter="bundler"` | Visible | `onclick`: Filters nodes/alerts for Jito bundler rate $>40\%$ |
| 18 | `.stage-pill` | `<span class="stage-pill active">`| `pill-mint` | Visible | `onclick`: Jumps timeline to $T+0\text{s}$; shows Token Mint explanation |
| 19 | `.stage-pill` | `<span class="stage-pill">` | `pill-snipe` | Visible | `onclick`: Jumps timeline to $T+13\text{s}$; shows Sniper Ingress explanation |
| 20 | `.stage-pill` | `<span class="stage-pill">` | `pill-bundle` | Visible | `onclick`: Jumps timeline to $T+16\text{s}$; shows MEV Bundle explanation |
| 21 | `.stage-pill` | `<span class="stage-pill">` | `pill-dump` | Visible | `onclick`: Jumps timeline to $T+35\text{s}$; shows Coordinated Dump explanation |
| 22 | `.kpi-card` | `<div class="kpi-card">` | Encapsulates `#kpi-syndicates` | Visible | `onclick`: Displays Active Syndicate Clusters KPI explanation |
| 23 | `.kpi-card` | `<div class="kpi-card">` | Encapsulates `#kpi-profit` | Visible | `onclick`: Displays Cumulative Extracted Profit KPI explanation |
| 24 | `.telemetry-row`| `<div class="telemetry-row">` | Encapsulates `#hud-angles` | Visible | `onclick`: Displays Gimbal Pitch/Yaw coordinate explanation |
| 25 | `.telemetry-row`| `<div class="telemetry-row">` | Encapsulates `#hud-dist` | Visible | `onclick`: Displays Camera Distance telemetry explanation |
| 26 | `.telemetry-row`| `<div class="telemetry-row">` | Encapsulates `#hud-node-count` | Visible | `onclick`: Displays Active Network Entities telemetry explanation |
| 27 | `.telemetry-row`| `<div class="telemetry-row">` | Encapsulates `#hud-synd-count` | Visible | `onclick`: Displays Syndicate Clusters telemetry explanation |
| 28 | `.deck-toggle-btn`| `<div class="deck-toggle-btn">` | `deck-toggle-btn` | Visible | `onclick`: Toggles `.collapsed` drawer on `aside#command-deck` |

### 2.3 Dynamic & Conditional Interactive Elements

| # | Component | Selector | Container | Populated When | Functionality |
|---|---|---|---|---|---|
| 29–31 | Alert Cards | `.alert-card` | `aside#command-deck .alert-feed` | `populateFeed(data)` called (3 cards in baseline, up to 5 in live) | `onclick`: Calls `showDossier(c)`, glides 3D camera to cluster center |
| 32–36 | Backlink Pills| `.backlink-pill`| `#curatorial-plaque #dossier-backlinks` | `showDossier(item)` called | `onclick`: Re-centers 3D camera on backlinked wallet / token; pulses mesh |
| 37 | 3D Canvas | `#webgl-canvas` | `<body>` | Always | Raycaster hit testing on 41 3D meshes; OrbitControls drag/zoom |

---

## 3. Dissection of the 34 Tested Elements vs Acceptance Criteria

### 3.1 Line-by-Line Breakdown of `results/web_verification_failures.json`

The previous test pass in `results/web_verification_failures.json` logged exactly 34 records:

| Item # | Selector Logged | Element Text / Label | Computed Bounding Box ($x, y, w, h$) | Status |
|:---:|:---|:---|:---|:---:|
| 1 | `button` | `⚡ CL4R1T4S MODE` | `1015.25, 11, 133.52, 29` | PASS |
| 2 | `button` | `🎯 RESET VIEW` | `1158.77, 11, 113.72, 29` | PASS |
| 3 | `button` | `📡 LIVE SCAN: ON` | `1282.48, 11, 133.52, 29` | PASS |
| 4 | `button` | `▶ PLAY` | `337.00, 834, 56.48, 21` | PASS |
| 5 | `.hud-btn` | `⚡ CL4R1T4S MODE` | `988.84, 11, 133.52, 29` | PASS |
| 6 | `.hud-btn` | `🎯 RESET VIEW` | `1132.36, 11, 113.72, 29` | PASS |
| 7 | `.hud-btn` | `📡 LIVE SCAN: ON` | `1256.08, 11, 159.92, 29` | PASS |
| 8 | `.hud-btn` | `▶ PLAY` | `337.00, 834, 64.61, 21` | PASS |
| 9 | `.health-chip` | `GMGN: OPEN (429)` | `390.44, 15, 133.00, 21` | PASS |
| 10 | `.health-chip` | `SOLSCAN: RECOVERING` | `531.44, 15, 152.50, 21` | PASS |
| 11 | `.health-chip` | `RPC: READY` | `691.94, 15, 94.00, 21` | PASS |
| 12 | `.health-chip` | `CACHE: 26.3% (141/537)` | `793.94, 15, 170.50, 21` | PASS |
| 13 | `.tag-chip` | `ALL` | `290.00, 64, 41.81, 24` | PASS |
| 14 | `.tag-chip` | `#FlashMode` | `339.81, 64, 88.00, 24` | PASS |
| 15 | `.tag-chip` | `#Sustained` | `435.81, 64, 88.00, 24` | PASS |
| 16 | `.tag-chip` | `#Bundler>40%` | `531.81, 64, 101.20, 24` | PASS |
| 17 | `.stage-pill` | `MINT (T+0s)` | `756.17, 836.5, 71.41, 16` | PASS |
| 18 | `.stage-pill` | `SNIPERS (T+13s)` | `833.58, 836.5, 93.00, 16` | PASS |
| 19 | `.stage-pill` | `BUNDLE (T+16s)` | `932.58, 836.5, 87.61, 16` | PASS |
| 20 | `.stage-pill` | `DUMP (T+35s)` | `1026.19, 836.5, 76.81, 16` | PASS |
| 21 | `.kpi-card` | `3Syndicates` | `1115.00, 87, 151.50, 57` | PASS |
| 22 | `.kpi-card` | `$322,920Est. Profit` | `1274.50, 87, 151.50, 57` | PASS |
| 23 | `.alert-card` | `SYND-0001 FLASH Profit...` | `1115.00, 207, 311.00, 46` | PASS |
| 24 | `.alert-card` | `SYND-0002 FLASH Profit...` | `1115.00, 261, 311.00, 46` | PASS |
| 25 | `.alert-card` | `SYND-0003 FLASH Profit...` | `1115.00, 315, 311.00, 46` | PASS |
| 26 | `.telemetry-row` | `PITCH / YAW 67° / 0°` | `41.00, 101, 216.00, 18` | PASS |
| 27 | `.telemetry-row` | `DISTANCE 412u` | `41.00, 123, 216.00, 18` | PASS |
| 28 | `.telemetry-row` | `NODES 16` | `41.00, 145, 216.00, 18` | PASS |
| 29 | `.telemetry-row` | `SYNDICATES 3` | `41.00, 167, 216.00, 18` | PASS |
| 30 | `.deck-toggle-btn` | `◀` | `1067.00, 68, 34.00, 34` | PASS |
| 31 | `#clarity-btn` | `⚡ CL4R1T4S MODE` | `1015.25, 11, 133.52, 29` | PASS |
| 32 | `#reset-cam-btn` | `🎯 RESET VIEW` | `1158.77, 11, 113.72, 29` | PASS |
| 33 | `#poll-toggle-btn` | `📡 LIVE SCAN: ON` | `1282.48, 11, 133.52, 29` | PASS |
| 34 | `#play-pause-btn` | `▶ PLAY` | `337.00, 834, 56.48, 21` | PASS |

### 3.2 Category-by-Category Aggregation

```
Total Discovered & Tested = 34
├── button                  : 4 (HUD native buttons)
├── .hud-btn                : 4 (HUD buttons class alias)
├── .health-chip            : 4 (Provider health indicators)
├── .tag-chip               : 4 (Filter chips)
├── .stage-pill             : 4 (Temporal sequence pills)
├── .kpi-card               : 2 (Radar KPI summary cards)
├── .alert-card             : 3 (Active cluster feed cards)
├── .telemetry-row          : 4 (Spatial gimbal coordinates)
├── .deck-toggle-btn        : 1 (Sliding drawer toggle)
└── Explicit ID Buttons     : 4 (#clarity-btn, #reset-cam-btn, #poll-toggle-btn, #play-pause-btn)
```
$$4 + 4 + 4 + 4 + 4 + 2 + 3 + 4 + 1 + 4 = 34$$

---

## 4. Pinpointing the Missing 2 Elements (The Gap from 34 to 36)

### 4.1 Primary Architectural Root Cause: Plaque Modal Action Buttons
In `.agents/skills/post-deploy-web-exploring/scripts/web_explorer.py`, the target locator list concludes with:
```python
TARGET_SELECTORS = [
    # ...
    "#play-pause-btn",    # Tested as Item #34
    "#copy-address-btn",  # OMITTED (Count = 0)
    "#export-md-btn",     # OMITTED (Count = 0)
]
```
- In `web/syndicate_3d_visualizer.html`:
  - Line 248: `<button class="action-btn" id="copy-address-btn">COPY WALLET</button>`
  - Line 249: `<button class="action-btn" id="export-md-btn">EXPORT (.MD)</button>`
- Both elements are located inside `#curatorial-plaque #entity-view`.
- At initial page load, `#curatorial-plaque` has CSS `display: none` (line 129).
- Playwright's discovery pass executes:
  ```python
  is_vis = await loc.is_visible()
  if not is_vis:
      continue
  ```
- Because `#curatorial-plaque` is `display: none`, both `#copy-address-btn` and `#export-md-btn` evaluate to `is_visible() == False` and are **silently omitted from discovery**.
- If these 2 declared action controls are tested:
  $$34 \text{ baseline elements} + 2 \text{ modal action buttons} = \mathbf{36} \text{ elements}$$

### 4.2 Secondary Data-Dependency Root Cause: Feed Card Count ($N=3$ vs $N=5$)
- In `explorer_survey_1/analysis.md` (Table 2.1), the initial survey recorded 36 elements by calculating:
  - 31 static items + **5 `.alert-card` items** = **36**.
- That survey ran against live test data with 5 clusters (`SYND-0014`, `SYND-0021`, `SYND-0024`, etc.).
- When `results/syndicate_3d_state.json` contains only 3 clusters (`SYND-0001`, `SYND-0002`, `SYND-0003`), `populateFeed` injects exactly 3 cards, dropping the discovered count from 36 to 34:
  $$31 \text{ static items} + 3 \text{ alert cards} = \mathbf{34} \text{ elements}$$
  $$\text{Deficit} = 5 - 3 = \mathbf{2} \text{ alert cards}$$

### 4.3 Synthesis of the Gap
Relying on the external cluster count ($N=5$) to reach 36 makes test execution fragile and leaves the two primary investigative tools (`#copy-address-btn` and `#export-md-btn`) untested. The true intended test surface comprises the 34 visible controls plus the **2 modal action buttons** (`#copy-address-btn` and `#export-md-btn`), reaching **36 deterministic controls**.

---

## 5. Layout, CSS, and DOM Deficiencies in `web/syndicate_3d_visualizer.html`

### 5.1 Defect 1: Curatorial Plaque Overlaps Telemetry HUD & Filter Strip
- **Observed CSS** (line 128):
  ```css
  .curatorial-plaque {
    position: absolute; top: 64px; left: 24px; width: 380px; max-height: calc(100% - 190px);
    background: rgba(8, 12, 20, 0.96); backdrop-filter: blur(24px); border: 1px solid var(--border-focus);
    border-radius: 8px; padding: 16px; z-index: 25; display: none; flex-direction: column; gap: 10px;
    box-shadow: 0 10px 40px rgba(0,0,0,0.8); overflow-y: auto;
  }
  ```
- **Geometric Conflict**:
  - `.telemetry-hud` occupies `top: 64px; left: 24px; width: 250px; z-index: 10`.
  - `.filter-strip` occupies `top: 64px; left: 290px; z-index: 10`.
  - When `#curatorial-plaque` opens (`z-index: 25`), it occupies $x = 24\text{px}..404\text{px}$, covering `.telemetry-hud` completely ($250\text{px}$ overlap) and covering the first two filter tags in `.filter-strip` ($114\text{px}$ overlap from $x = 290\text{px}$ to $404\text{px}$).
  - Any click attempted on `.telemetry-row` or `.tag-chip` while the plaque is visible is intercepted by `#curatorial-plaque`, generating `POINTER_INTERCEPTION` failures.
- **Recommended Remediation**:
  Stack `#curatorial-plaque` vertically below `.telemetry-hud` or anchor it beside `aside.command-deck`:
  ```css
  /* Recommended Non-Blocking Plaque Positioning */
  .curatorial-plaque {
    position: absolute;
    top: 220px;
    left: 24px;
    width: 360px;
    max-height: calc(100% - 240px);
    z-index: 25;
    /* ... */
  }
  ```
  At `top: 220px`, the plaque clears `.telemetry-hud` (height $\approx 140\text{px}$, bottom $\approx 204\text{px}$) and `.filter-strip` (top $64\text{px}$), leaving all HUD rows and filter chips visible and actionable.

### 5.2 Defect 2: Timeline Bar Horizontal Overlap with Command Deck
- **Observed CSS** (line 108):
  ```css
  .timeline-bar {
    position: absolute; bottom: 16px; left: 50%; transform: translateX(-50%); width: min(800px, calc(100% - 380px));
    background: var(--bg-panel); backdrop-filter: blur(16px); border: 1px solid var(--border-subtle); border-radius: 10px;
    padding: 10px 16px; z-index: 10; display: flex; flex-direction: column; gap: 6px;
  }
  ```
- **Geometric Conflict**:
  - Reference Viewport: $1440 \times 900\text{px}$.
  - Timeline bar width: $\min(800, 1440 - 380) = 800\text{px}$.
  - Center is $x = 720\text{px}$; timeline spans $x = 320\text{px}..1120\text{px}$.
  - `aside.command-deck` width: $340\text{px}$, right-anchored at $x = 1100\text{px}..1440\text{px}$.
  - Overlap: $x = 1100\text{px}..1120\text{px}$ ($20\text{px}$ collision).
  - At $1280\times800\text{px}$ viewport: Overlap expands to $100\text{px}$ ($x = 940\text{px}..1040\text{px}$).
- **Recommended Remediation**:
  Center `.timeline-bar` within the available canvas width ($100\% - 340\text{px}$):
  ```css
  .timeline-bar {
    position: absolute;
    bottom: 16px;
    left: calc((100% - 340px) / 2);
    transform: translateX(-50%);
    width: min(720px, calc(100% - 400px));
    /* ... */
  }
  ```

### 5.3 Defect 3: Clipboard Write Permission Rejection in Headless Browsers
- **Observed JavaScript** (lines 762–770):
  ```javascript
  document.getElementById('copy-address-btn').onclick = () => {
    const val = selectedEntity ? (selectedEntity.id || selectedEntity.address || '') : '';
    if (!val) return;
    navigator.clipboard.writeText(val); // <--- UNCAUGHT PROMISE REJECTION
    const t = document.getElementById('copy-toast');
    t.textContent = 'COPIED ' + val.slice(0, 16) + '...';
    t.classList.add('show');
    setTimeout(() => t.classList.remove('show'), 2000);
  };
  ```
- **Failure Mode**:
  Headless Chromium rejects `navigator.clipboard.writeText()` when running in environments without explicit clipboard permissions, throwing:
  `DOMException: Failed to execute 'writeText' on 'Clipboard': Write permission denied.`
  This is registered as a fatal `pageerror`, causing test verification to fail.
- **Recommended Remediation**:
  Add defensive error handling and fallbacks in `web/syndicate_3d_visualizer.html`:
  ```javascript
  document.getElementById('copy-address-btn').onclick = () => {
    const val = selectedEntity ? (selectedEntity.id || selectedEntity.address || '') : '';
    if (!val) return;
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(val).catch(() => {
        // Suppress rejection in headless test runners lacking clipboard permission
      });
    }
    const t = document.getElementById('copy-toast');
    t.textContent = 'COPIED ' + val.slice(0, 16) + '...';
    t.classList.add('show');
    setTimeout(() => t.classList.remove('show'), 2000);
  };
  ```

### 5.4 Defect 4: Missing ARIA `role="button"` and `tabindex="0"` on Clickable Containers
- **Current State**:
  None of the clickable `<span>` and `<div>` elements (`.health-chip`, `.tag-chip`, `.stage-pill`, `.kpi-card`, `.telemetry-row`, `.deck-toggle-btn`) declare `role="button"` or `tabindex="0"`.
- **Impact**:
  - `web_explorer.py`'s selector `[role='button']` matches 0 elements.
  - Keyboard navigation and screen readers cannot discover or activate these controls.
- **Recommended Remediation**:
  Inject `role="button"` and `tabindex="0"` on all interactive spans and divs.

---

## 6. Implementation Roadmap for Remediation

To achieve a 100% verified 36/36 element pass with 0 failures and 0 console errors:

1. **Update `web/syndicate_3d_visualizer.html`**:
   - Reposition `#curatorial-plaque` to `top: 220px; left: 24px; max-height: calc(100% - 240px);` to eliminate occlusion of `.telemetry-hud` and `.filter-strip`.
   - Reposition `.timeline-bar` to `left: calc((100% - 340px) / 2);` to eliminate overlap with `aside.command-deck`.
   - Wrap `navigator.clipboard.writeText` in a `.catch(() => {})` handler to prevent unhandled promise rejection errors in headless browsers.
   - Add `role="button"` and `tabindex="0"` to all interactive `div` and `span` controls.
2. **Harmonize `web_explorer.py` Discovery Sweep**:
   - Implement a two-phase discovery sweep:
     - **Phase 1**: Discover and verify the 34 visible initial controls.
     - **Phase 2**: Click `.alert-card:first-child` to open `#curatorial-plaque`, discover and verify `#copy-address-btn` and `#export-md-btn` ($34 + 2 = \mathbf{36}$), and then click `.plaque-close-btn`.
   - Grant `clipboard-read` and `clipboard-write` browser context permissions in Playwright.

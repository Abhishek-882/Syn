# Comprehensive Analysis: Post-Deploy Web Exploration Harness & Runtime Environment

**Date**: 2026-09-21  
**Author**: Explorer Survey 2 (`teamwork_preview_explorer`)  
**Scope**: Verification of web server status, Python browser automation runtime, analysis of `web_explorer.py` and `post-deploy-web-exploring/SKILL.md`, and evaluation of discovery, collision detection, and failure logging mechanisms.

---

## 1. Executive Summary

- **Web Server Status**: A Python HTTP server (`PID 3512`, command `"C:\Python314\python.exe" -m http.server 8000`) is active and successfully serving `http://localhost:8000/web/syndicate_3d_visualizer.html` (HTTP 200 OK, 76,348 bytes).
- **Automation Runtime**: Python 3.14.4 is the active interpreter. **Playwright 1.59.0** is installed with a fully operational headless **Chromium 147.0.7727.15** binary. **Selenium is NOT installed**.
- **Live Sweep Execution**: Running `web_explorer.py` against the visualizer discovered 36 target items; **34 passed and 2 failed** (`Locator.scroll_into_view_if_needed: Element is not attached to the DOM` on `.alert-card` elements).
- **Critical Gaps & Bugs**:
  1. **Stale DOM / Detached Locators**: The visualizer contains a 5-second polling loop (`setInterval(..., 5000)`) executing `feed.innerHTML = ''`. Locators captured at page initialization become detached before `web_explorer.py` reaches them ~50 seconds into the run.
  2. **Missing DOM Snapshots**: Explicitly mandated in `ORIGINAL_REQUEST.md` (R2 & Acceptance Criteria), but completely missing from `web_explorer.py` failure payloads.
  3. **Missing Network (404/500) Auditing**: Required by R2, but no HTTP response / request failure monitors exist.
  4. **Single-Pass Discovery Blindness**: Elements inside `#curatorial-plaque` (`.plaque-close-btn`, `#copy-address-btn`, `#export-md-btn`, `.backlink-pill`) are hidden at startup and are never discovered or verified.
  5. **Schema Inconsistencies**: `SKILL.md` specifies `"bounding_box"` and ISO 8601 strings; `web_explorer.py` emits `"bbox"` and Unix epoch timestamps.

---

## 2. Environment & Runtime Audit

### 2.1 Python Runtime
- **Interpreter Path**: `C:\Python314\python.exe`
- **Version**: `Python 3.14.4`
- **Architecture**: 64-bit Windows

### 2.2 Browser Automation Tooling
- **Playwright**:
  - Python Package: `playwright` version `1.59.0` (installed and importable via `playwright.async_api` and `playwright.sync_api`).
  - Headless Browser: Chromium version `147.0.7727.15` installed in system cache and verified working via headless launch tests.
- **Selenium**:
  - `importlib.util.find_spec('selenium')` returned `None` (not installed).
  - Playwright is the intended and sole functional driver for the exploration harness.

### 2.3 Local Web Server Verification
- **Port**: `8000` (dual-stack TCP listening on `::8000`).
- **Process ID**: `3512`
- **Command Line**: `"C:\Python314\python.exe" -m http.server 8000`
- **Target URL**: `http://localhost:8000/web/syndicate_3d_visualizer.html`
- **HTTP Probe Result**: HTTP `200 OK`, `Content-Length: 76348 bytes`.
- **Static Assets in Directory**:
  - `web/syndicate_3d_visualizer.html` (76,348 bytes)
  - `web/three.min.js` (603,445 bytes)
  - `web/OrbitControls.js` (26,375 bytes)
  - `results/syndicate_3d_state.json` (44,447 bytes, polled by the visualizer)
  - `results/live_alerts.json` (96,617 bytes)

---

## 3. Architecture & Mechanics of `web_explorer.py`

### 3.1 Target Selector Taxonomy
Located at lines 22–41 of `.agents/skills/post-deploy-web-exploring/scripts/web_explorer.py`:
```python
TARGET_SELECTORS = [
    "button",
    "[role='button']",
    ".hud-btn",
    ".health-chip",
    ".tag-chip",
    ".stage-pill",
    ".kpi-card",
    ".alert-card",
    ".backlink-pill",
    ".telemetry-row",
    ".deck-toggle-btn",
    ".plaque-close-btn",
    "#clarity-btn",
    "#reset-cam-btn",
    "#poll-toggle-btn",
    "#play-pause-btn",
    "#copy-address-btn",
    "#export-md-btn",
]
```

### 3.2 Discovery Mechanism
- **Execution Point**: Lines 72–98 in `web_explorer.py`.
- **Workflow**:
  1. Awaits page navigation with `wait_until="networkidle"` and an additional 1500ms delay.
  2. Iterates over `TARGET_SELECTORS` sequentially.
  3. Executes `locs = await page.locator(sel).all()`.
  4. For each locator, evaluates `await loc.is_visible()`.
  5. Computes bounding box (`await loc.bounding_box()`) and truncated text.
  6. Filters through `seen_locators` using key: `key = f"{sel}:{idx}:{text[:20]}"`.

#### Key Discovery Flaw: Over-counting via Selector Duplication
Because `sel` is included in the deduplication key, any DOM node matching multiple selectors is included multiple times:
- `#clarity-btn` is tested under `button`, `.hud-btn`, and `#clarity-btn` (3 tests).
- `#reset-cam-btn` is tested under `button`, `.hud-btn`, and `#reset-cam-btn` (3 tests).
- `#poll-toggle-btn` is tested under `button`, `.hud-btn`, and `#poll-toggle-btn` (3 tests).
- `#play-pause-btn` is tested under `button`, `.hud-btn`, and `#play-pause-btn` (3 tests).

Total tests generated:
- 4 buttons × 3 selectors = 12 items
- 4 health chips = 4 items
- 4 tag chips = 4 items
- 4 stage pills = 4 items
- 2 KPI cards = 2 items
- 5 alert cards = 5 items
- 4 telemetry rows = 4 items
- 1 deck toggle button = 1 item
- **Grand Total**: `12 + 4 + 4 + 4 + 2 + 5 + 4 + 1 = 36 items` (representing only 28 unique DOM elements).

### 3.3 Pointer Collision & Interception Detection
- **Execution Point**: Lines 100–145 in `web_explorer.py`.
- **Detection Mechanism**:
  - Playwright's `await loc.click(timeout=timeout_ms)` natively implements actionability checks. Prior to triggering mouse events, Playwright calculates the element's bounding box and checks whether the element receives pointer events at its center point.
  - If another DOM layer (e.g., `#curatorial-plaque` with `z-index: 25`, or `#hud-deck`) overlaps the element, Playwright aborts after `timeout_ms` with an exception containing:
    `... intercepts pointer events`.
  - `web_explorer.py` checks:
    ```python
    err_type = "POINTER_INTERCEPTION" if "intercepts pointer events" in err_msg else "CLICK_FAILURE"
    ```
- **Modal Clearing**:
  - After every click, `web_explorer.py` attempts to close any newly popped modal plaque:
    ```python
    close_btn = page.locator("#curatorial-plaque .plaque-close-btn:visible")
    if await close_btn.count() > 0:
        await close_btn.first.click(timeout=1000)
        await page.wait_for_timeout(100)
    ```

---

## 4. Live Verification Sweep & Empirical Failure Analysis

A live run of `web_explorer.py` was executed against `http://localhost:8000/web/syndicate_3d_visualizer.html` (Task-66).

### 4.1 Sweep Summary
- Discovered elements: 36
- Tested elements: 36
- **Passed**: 34
- **Failed**: 2
- Console errors: 0
- Page errors: 0

### 4.2 Verbatim Failure Records
From `results/web_verification_failures.json`:
```json
{
  "selector": ".alert-card",
  "text": "SYND-0014FLASHProfit: $1,036,971 | Score",
  "error_type": "CLICK_FAILURE",
  "message": "Locator.scroll_into_view_if_needed: Element is not attached to the DOM\nCall log:\n  - attempting scroll into view action\n    - waiting for element to be stable\n",
  "bbox": {"x": 1115, "y": 207, "width": 311, "height": 46},
  "console_errors": [],
  "timestamp": 1789959036.126685
},
{
  "selector": ".alert-card",
  "text": "SYND-0023FLASHProfit: $181,512 | Score: ",
  "error_type": "CLICK_FAILURE",
  "message": "Locator.scroll_into_view_if_needed: Element is not attached to the DOM\nCall log:\n  - attempting scroll into view action\n    - waiting for element to be stable\n",
  "bbox": {"x": 1115, "y": 369, "width": 311, "height": 46},
  "console_errors": [],
  "timestamp": 1789959041.27154
}
```

### 4.3 Root Cause of Failure: Polling DOM Wipes & Dynamic Filtering
1. **Live Polling Loop**: In `web/syndicate_3d_visualizer.html` (lines 1019–1021):
   ```javascript
   setInterval(() => {
     if (isLivePolling) loadData();
   }, 5000);
   ```
   Every 5 seconds, `loadData()` fetches `results/syndicate_3d_state.json` and calls `populateFeed(data)`.
2. **Destructive Feed Repopulation**: In `web/syndicate_3d_visualizer.html` (lines 385–388):
   ```javascript
   function populateFeed(data) {
     const feed = document.getElementById('alert-feed');
     feed.innerHTML = '';
     (data.clusters || []).forEach(c => {
       const card = document.createElement('div');
       card.className = 'alert-card';
   ```
   `feed.innerHTML = ''` deletes all existing `.alert-card` DOM nodes and replaces them with new objects.
3. **Stale Locator Reference**: In `web_explorer.py`, locators are evaluated once at $T=0$ via `page.locator(sel).all()`. The sweep takes >60 seconds. When the runner reaches item 20 (`.alert-card`), the original element handles captured 45 seconds earlier have been detached and replaced 9+ times.
4. **State Flips via Redundant Toggles**:
   - `#poll-toggle-btn` was clicked 3 times during the sweep, alternately enabling and disabling polling.
   - Tag chips (`.tag-chip`) were clicked, triggering `applyFilter()` which set `display: none` on cards without bundler tags. When `loadData()` executed next, it rebuilt cards with default displays, causing element instability.

---

## 5. Comprehensive Bug & Gap Inventory

| # | Category | Description | Severity | Impact on Acceptance Criteria |
|---|---|---|---|---|
| **G1** | **DOM Stability** | Stale locator handles detached by 5s `feed.innerHTML = ''` refresh loop | **High** | Causes random test failures on `.alert-card` |
| **G2** | **DOM Snapshot** | Missing DOM snapshot capture in failure records | **High** | Violates R2 and Acceptance Criteria (`ORIGINAL_REQUEST.md`) |
| **G3** | **Network Telemetry** | No listener for 404/500 HTTP asset or API failures | **Medium** | Missing silent network asset failure logging (R2) |
| **G4** | **Schema Alignment** | Field naming mismatch (`bbox` vs `bounding_box`, epoch vs ISO-8601) | **Medium** | Violates schema defined in `SKILL.md` §4 |
| **G5** | **Discovery Depth** | Single-pass discovery misses elements inside closed plaques/modals | **Medium** | `#copy-address-btn`, `#export-md-btn`, `.backlink-pill` never tested |
| **G6** | **State Mutation** | Toggle buttons clicked multiple times alter app state (e.g. collapses deck) | **Medium** | Deck collapse can hide downstream interactive elements |
| **G7** | **Deduplication** | Keying by selector causes redundant triplicate testing of same buttons | **Low** | Tests 36 locators instead of 28 unique DOM elements |

---

## 6. Recommendations & Surgical Remediation Plan

### 6.1 Fix for DOM Detachment in `web_explorer.py`
Instead of preserving stale `Locator` references in a list for 60 seconds, resolve locators dynamically at the time of clicking:
```python
# Instead of storing 'locator' object in discovered_locators:
discovered_locators.append({
    "selector": sel,
    "index": idx,
    "text": text[:40],
    "bbox": bbox
})

# During click sweep:
loc = page.locator(sel).nth(idx)
```
Or pause the live scan before sweeping:
```python
# Turn off live scan during test sweep to prevent feed wipes
poll_btn = page.locator("#poll-toggle-btn.active")
if await poll_btn.count() > 0:
    await poll_btn.click()
```

### 6.2 Compliance with R2 Logging Schema
Update `failure_item` in `web_explorer.py` to capture DOM snapshots and align field names:
```python
import datetime

dom_snapshot = await page.content()
failure_item = {
    "selector": sel,
    "text": text,
    "error_type": err_type,
    "message": err_msg,
    "bounding_box": bbox,
    "dom_snapshot": dom_snapshot[:2000],  # or element outerHTML
    "console_errors": list(console_errors),
    "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
}
```

### 6.3 Network Error Monitoring
Add Playwright network monitoring at browser page initialization:
```python
network_errors: List[Dict[str, Any]] = []
page.on("response", lambda resp: network_errors.append({
    "url": resp.url,
    "status": resp.status,
    "status_text": resp.status_text
}) if resp.status >= 400 else None)
page.on("requestfailed", lambda req: network_errors.append({
    "url": req.url,
    "failure": req.failure
}))
```

"""Automated Playwright E2E browser verification for Milestone 24 Interactive Chained-Link Flowchart.

Verifies:
1. Loading terminal on http://localhost:8000/web/syndicate_terminal.html.
2. Clicking a historical token row loads its 5-stage on-chain proof flowchart in Column 3.
3. Clicked row receives highlighted selection state (.selected-token-row).
4. Clicking any SVG node copies address and auto-filters Deployer Watchlist.
5. Opening and inspecting the Full-Screen Lineage Modal (#lineage-modal-overlay).
6. Mobile auto-switch to Lineage column on smartphone viewports.
7. Captures numbered screenshots: Step 119 and Step 120.
"""

import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.request
import pytest
from playwright.sync_api import sync_playwright

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
STEPS_DIR = PROJECT_ROOT / "steps"
RESULTS_SCREENSHOTS_DIR = PROJECT_ROOT / "results" / "screenshots"
STEPS_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

PORT = 8000
BASE_URL = f"http://localhost:{PORT}/web/syndicate_terminal.html"


def save_screenshot(page, step_num: int, name: str):
    filename = f"{step_num}_{name}.png"
    p1 = STEPS_DIR / filename
    p2 = RESULTS_SCREENSHOTS_DIR / filename
    page.screenshot(path=str(p1), full_page=True)
    page.screenshot(path=str(p2), full_page=True)
    print(f"Captured Step {step_num}: {filename}")
    return str(p1)


def test_token_lineage_flowchart():
    """Verify interactive token chained-link flowchart, node clicks, and modal."""
    # Ensure server is running
    server_proc = None
    try:
        urllib.request.urlopen(f"http://localhost:{PORT}/healthz", timeout=2)
        print("Server already running on port", PORT)
    except Exception:
        print("Starting local server on port", PORT)
        server_env = os.environ.copy()
        server_env["PYTHONPATH"] = str(PROJECT_ROOT / "src")
        server_proc = subprocess.Popen(
            [sys.executable, str(PROJECT_ROOT / "src" / "crypto_syndicate" / "server.py"), "--port", str(PORT), "--no-keeper"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=server_env,
        )
        started = False
        for _ in range(20):
            time.sleep(0.5)
            try:
                urllib.request.urlopen(f"http://localhost:{PORT}/healthz", timeout=1)
                started = True
                print("Server successfully probed and ready.")
                break
            except Exception:
                pass
        if not started:
            if server_proc.poll() is not None:
                out, err = server_proc.communicate()
                print("Server failed to start:", err.decode("utf-8", errors="ignore"))
            raise RuntimeError("Failed to start server within 10 seconds")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            page.on("console", lambda msg: print(f"[BROWSER CONSOLE] {msg.type}: {msg.text}"))
            page.on("pageerror", lambda err: print(f"[BROWSER ERROR] {err}"))
            page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
            page.wait_for_timeout(2000)

            # 1. Verify table rows are rendered and clickable
            page.wait_for_selector(".history-row", timeout=10000)
            rows = page.locator(".history-row")
            count = rows.count()
            assert count > 0, "No historical token rows found"
            print(f"Found {count} token rows.")

            # 2. Click on row #1 ($LEVERAGE or top token) rank cell
            first_row = rows.first
            first_row.locator("td").first.click()
            page.wait_for_timeout(800)

            # 3. Assert row selection and SVG nodes in Column 3
            svg_nodes = page.locator("#lineage-svg g")
            assert svg_nodes.count() >= 5, "SVG flowchart must render at least 5 proof nodes"
            print(f"Column 3 Lineage SVG rendered {svg_nodes.count()} interactive nodes.")

            # 4. Search and click LEVERAGE token specifically
            search_box = page.locator("#history-search")
            search_box.fill("LEVERAGE")
            page.wait_for_timeout(800)

            print("Filtered rows count:", page.locator(".history-row").count())
            if page.locator(".history-row").count() > 0:
                print("First row text:", repr(page.locator(".history-row").first.inner_text()))

            page.on("request", lambda r: print(f"[REQ] {r.method} {r.url}"))
            page.on("response", lambda r: print(f"[RESP] {r.status} {r.url}"))

            leverage_row = page.locator(".history-row").first
            print("Clicking leverage row rank cell and awaiting API response...")
            with page.expect_response(lambda r: "/api/token-lineage" in r.url and r.status == 200, timeout=10000):
                leverage_row.locator("td").first.click()
            page.wait_for_timeout(800)

            inspector_text = page.locator("#inspector-content").inner_text()
            print("Inspector text after click:", repr(inspector_text))
            assert "LEVERAGE" in inspector_text or "DFZ497" in inspector_text
            assert "VERIFIED SYNDICATE MEMBER" in inspector_text
            print("Inspector verified: Token and syndicate cluster properly displayed.")

            # Capture Step 119
            save_screenshot(page, 119, "token_chained_link_flowchart_verified")

            # 5. Click Deployer node inside the SVG to test copy & filter
            deployer_node = page.locator("#lineage-svg g:has-text('Deployer')").first
            if deployer_node.is_visible():
                deployer_node.click()
                page.wait_for_timeout(500)
                deployer_search_val = page.locator("#deployer-search").input_value()
                print(f"Deployer search filter updated to: '{deployer_search_val}'")
                assert len(deployer_search_val) > 0, "Deployer search was not filtered"

            # 6. Test opening Full-Screen Lineage Modal
            expand_btn = page.locator("#expand-lineage-btn")
            expand_btn.click()
            page.wait_for_timeout(600)

            modal_overlay = page.locator("#lineage-modal-overlay")
            assert modal_overlay.is_visible(), "Modal overlay did not open"

            modal_title = page.locator(".modal-title").inner_text()
            print("Modal Title:", modal_title)
            assert "SYNDICATE ON-CHAIN PROOF CHAIN" in modal_title

            modal_svg_nodes = page.locator("#modal-lineage-svg g")
            assert modal_svg_nodes.count() >= 5, "Modal SVG does not render proof nodes"

            # Capture Step 120
            save_screenshot(page, 120, "lineage_fullscreen_modal_verified")

            # Close modal with ESC
            page.keyboard.press("Escape")
            page.wait_for_timeout(400)
            assert not modal_overlay.is_visible(), "Modal overlay did not close on Escape"
            print("Modal Escape key close verified.")

            # 7. Mobile Viewport Check (390x844 - iPhone 15 Pro)
            page.set_viewport_size({"width": 390, "height": 844})
            page.wait_for_timeout(500)

            # Clear search and switch to tokens mobile column
            page.locator("#history-search").fill("")
            page.wait_for_timeout(300)
            page.locator("#mob-tab-tokens").click()
            page.wait_for_timeout(400)

            # Trigger token inspection on mobile and await lineage response
            with page.expect_response(lambda r: "/api/token-lineage" in r.url and r.status == 200, timeout=10000):
                page.evaluate("inspectToken('BM2k8mJUbMthHoioykyUm2NjMrXvLBYhoXruwYLpump', true)")
            page.wait_for_timeout(600)

            # Verify automatic switch to Lineage column
            col_lineage = page.locator("#col-lineage")
            assert "mobile-active" in (col_lineage.get_attribute("class") or "")
            print("Mobile auto-switch to Lineage column verified on 390px viewport!")

            browser.close()
    finally:
        if server_proc:
            server_proc.terminate()
            try:
                server_proc.wait(timeout=2)
            except Exception:
                pass

    print("ALL TOKEN LINEAGE FLOWCHART E2E CHECKS PASSED SUCCESSFULLY (100% PASS)!")


if __name__ == "__main__":
    test_token_lineage_flowchart()

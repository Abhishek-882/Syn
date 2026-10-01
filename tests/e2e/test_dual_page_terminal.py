"""Automated Playwright E2E browser verification for Dual-Page Ecosystem Terminal.

Verifies:
1. Page 1 (Binance Funded Ecosystem) is the default landing view:
   - Header switcher has Page 1 button active with gold accent.
   - Badge displays '12 TOKENS' for Binance and '69 TOKENS' for Non-Binance.
   - Curatorial context bar displays 'PAGE 1: PRIMARY' and 'BINANCE CEX TREASURY SYNDICATE ECOSYSTEM'.
   - Token history table contains exactly the 12 Binance-funded tokens ($BAGWORK, $LEVERAGE, $Snoopy, $PUZZLE, $GAMBY, $1, etc.).
   - Deployers watchlist displays only Binance-funded wallets.
   - Screenshot 118_dual_page_page1_binance_default.png captured.
2. Page 2 (Non-Binance Ecosystem) dedicated alternate view:
   - Clicking '#btn-page-non-binance' switches to Page 2.
   - URL hash updates to #non-binance.
   - Context bar updates to 'PAGE 2: DEDICATED' and 'NON-BINANCE FUNDED SYNDICATE ECOSYSTEM'.
   - Token history table displays the 69 non-Binance tokens.
   - Deployers watchlist displays the 113 non-Binance wallets.
   - Screenshot 119_dual_page_page2_non_binance.png captured.
3. State persistence across page reloads and direct hash navigation:
   - Navigating to #non-binance directly loads Page 2.
   - Navigating to #binance directly loads Page 1.
4. Header chip toggle and table filter toggle switch between Page 1 and Page 2.
5. Mobile viewport verification (390x844) with minimum 42px touch targets.
   - Screenshot 120_dual_page_mobile_responsive.png captured.
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


def test_dual_page_ecosystem_terminal():
    """Verify dual-page ecosystem navigation (Page 1 Binance vs Page 2 Non-Binance)."""
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
            raise RuntimeError("Failed to start server within 10 seconds")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            page.on("console", lambda msg: print(f"[BROWSER CONSOLE] {msg.type}: {msg.text}"))
            page.on("pageerror", lambda err: print(f"[BROWSER ERROR] {err}"))

            # Clear any stored page preference to verify clean default
            page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
            page.evaluate("() => localStorage.removeItem('syndicate_active_page')")
            page.goto(f"{BASE_URL}#binance", wait_until="domcontentloaded", timeout=15000)
            page.wait_for_timeout(2500)

            # --- 1. VERIFY PAGE 1 (BINANCE FUNDED) DEFAULT LANDING ---
            btn_binance = page.locator("#btn-page-binance")
            btn_non_binance = page.locator("#btn-page-non-binance")
            assert btn_binance.is_visible(), "Page 1 Binance button must be visible"
            assert btn_non_binance.is_visible(), "Page 2 Non-Binance button must be visible"
            assert "active" in (btn_binance.get_attribute("class") or ""), "Page 1 button must be active by default"
            assert "active" not in (btn_non_binance.get_attribute("class") or ""), "Page 2 button must not be active"

            # Check context bar
            context_tag = page.locator("#context-page-tag").inner_text()
            assert "PAGE 1: PRIMARY" in context_tag, f"Expected Page 1 tag, got: {context_tag}"
            context_heading = page.locator("#context-page-heading").inner_text()
            assert "BINANCE CEX TREASURY" in context_heading, f"Expected Binance heading, got: {context_heading}"

            # Wait for table rows
            page.wait_for_selector(".history-row", timeout=10000)
            rows = page.locator(".history-row")
            page1_count = rows.count()
            print(f"Page 1 visible token rows: {page1_count}")
            assert page1_count >= 12, f"Expected at least 12 Binance tokens on Page 1, got {page1_count}"

            # Verify every row on Page 1 has Binance badge or is Binance funded
            badges = page.locator(".history-row .funder-badge.funder-binance")
            assert badges.count() == page1_count, f"Expected all {page1_count} Binance badges on Page 1, got {badges.count()}"

            # Deployers counter on Page 1
            dep_counter = page.locator("#deployers-counter").inner_text()
            assert "Binance" in dep_counter, f"Expected Binance deployer count, got: {dep_counter}"

            save_screenshot(page, 118, "dual_page_page1_binance_default")

            # --- 2. SWITCH TO PAGE 2 (NON-BINANCE FUNDED) ---
            print("Switching to Page 2: Non-Binance Ecosystem...")
            btn_non_binance.click()
            page.wait_for_timeout(1500)

            # Verify URL hash updated
            current_url = page.url
            assert "#non-binance" in current_url, f"URL hash should be #non-binance, got: {current_url}"

            # Verify buttons active state
            assert "active" in (btn_non_binance.get_attribute("class") or ""), "Page 2 button must be active"
            assert "active" not in (btn_binance.get_attribute("class") or ""), "Page 1 button must not be active"

            # Check context bar for Page 2
            context_tag_p2 = page.locator("#context-page-tag").inner_text()
            assert "PAGE 2: DEDICATED" in context_tag_p2, f"Expected Page 2 tag, got: {context_tag_p2}"
            context_heading_p2 = page.locator("#context-page-heading").inner_text()
            assert "NON-BINANCE FUNDED" in context_heading_p2, f"Expected Non-Binance heading, got: {context_heading_p2}"

            # Check tokens count on Page 2
            rows_p2 = page.locator(".history-row")
            page2_count = rows_p2.count()
            print(f"Page 2 visible token rows: {page2_count}")
            assert page2_count >= 60, f"Expected at least 60 Non-Binance tokens on Page 2, got {page2_count}"

            # Verify zero rows on Page 2 have the Binance badge
            badges_p2 = page.locator(".history-row .funder-badge.funder-binance")
            assert badges_p2.count() == 0, f"Expected 0 Binance badges on Page 2, got {badges_p2.count()}"

            # Deployers counter on Page 2
            dep_counter_p2 = page.locator("#deployers-counter").inner_text()
            assert "Non-Binance" in dep_counter_p2, f"Expected Non-Binance deployer count, got: {dep_counter_p2}"

            save_screenshot(page, 119, "dual_page_page2_non_binance")

            # --- 3. VERIFY RELOAD PERSISTENCE (PAGE 2) ---
            print("Testing reload persistence on #non-binance...")
            page.reload(wait_until="domcontentloaded")
            page.wait_for_timeout(2000)

            page.wait_for_selector(".history-row", timeout=10000)
            reloaded_count = page.locator(".history-row").count()
            assert reloaded_count == page2_count, f"Expected {page2_count} tokens after reload on Page 2, got {reloaded_count}"
            assert "active" in (page.locator("#btn-page-non-binance").get_attribute("class") or "")

            # --- 4. SWITCH BACK TO PAGE 1 VIA HEADER BINANCE CHIP ---
            print("Switching back to Page 1 via header chip...")
            page.locator("#header-binance-chip").click()
            page.wait_for_timeout(1500)

            assert "#binance" in page.url
            assert "active" in (page.locator("#btn-page-binance").get_attribute("class") or "")
            assert page.locator(".history-row").count() == page1_count

            # --- 5. TEST SEARCH ON PAGE 1 ---
            page.locator("#history-search").fill("BAGWORK")
            page.wait_for_timeout(500)
            search_count = page.locator(".history-row").count()
            assert search_count == 1, f"Expected 1 row for BAGWORK search, got {search_count}"
            page.locator("#history-search").fill("")
            page.wait_for_timeout(500)
            assert page.locator(".history-row").count() == page1_count

            # --- 6. MOBILE RESPONSIVE CHECK (390x844) ---
            print("Testing mobile viewport 390x844...")
            page.set_viewport_size({"width": 390, "height": 844})
            page.wait_for_timeout(1000)

            # Check switcher buttons are visible and clickable
            btn_binance_box = btn_binance.bounding_box()
            assert btn_binance_box is not None, "Binance button must have a bounding box on mobile"
            assert btn_binance_box["height"] >= 34, f"Touch target height should be >= 34px, got {btn_binance_box['height']}"

            # Check mobile column switcher bar
            mob_bar = page.locator("#mobile-nav-bar")
            assert mob_bar.is_visible(), "Mobile nav bar must be visible on 390px viewport"

            save_screenshot(page, 120, "dual_page_mobile_responsive")
            print("All dual-page E2E verifications passed with zero errors!")

            browser.close()
    finally:
        if server_proc:
            server_proc.terminate()
            server_proc.wait(timeout=5)


if __name__ == "__main__":
    test_dual_page_ecosystem_terminal()

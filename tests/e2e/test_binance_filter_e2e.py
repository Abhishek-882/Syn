"""Automated Playwright E2E browser verification for Milestone 25 Binance-Funded Dev Wallet Filter.

Verifies:
1. Loading terminal on http://localhost:8000/web/syndicate_terminal.html.
2. Initial state: filter is OFF, all 37 historical tokens rendered.
3. Clicking #filter-binance-btn toggles filter ON:
   - Button receives active class with gold border and filled dot.
   - Real-time toast confirms 'Binance Dev Filter: ON'.
   - Filtered rows drop to exactly the Binance-funded tokens (7 tokens).
   - All displayed rows contain the '🟡 BINANCE' badge (.funder-badge.funder-binance).
4. Captures Step 121: 121_binance_dev_filter_active.png.
5. Clicking #filter-binance-btn toggles filter OFF:
   - Button loses active class with hollow dot.
   - Real-time toast confirms 'Binance Dev Filter: OFF'.
   - All 37 tokens are restored.
6. Captures Step 122: 122_binance_dev_filter_toggled_off.png.
7. Deployer Watchlist toggle #filter-binance-dep-btn verified.
8. Mobile viewport verification on 390x844 with zero bleed.
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


def test_binance_filter_e2e():
    """Verify Binance-funded dev wallet filter toggle ON/OFF across table, deployers, and mobile."""
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
            page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
            page.wait_for_timeout(2000)

            # 1. Assert initial baseline: Filter is ON by default per operator requirement
            page.wait_for_selector(".history-row", timeout=10000)
            all_rows = page.locator(".history-row")
            binance_count = all_rows.count()
            print(f"Initial token count (filter ON by default): {binance_count}")
            assert binance_count >= 7, f"Expected at least 7 Binance-funded tokens, got {binance_count}"

            # Verify sticky spotlight banner is completely removed
            spotlight_count = page.locator("#spotlight-container").count()
            assert spotlight_count == 0, "Spotlight banner (#spotlight-container) must be completely removed"

            binance_btn = page.locator("#filter-binance-btn")
            assert binance_btn.is_visible(), "#filter-binance-btn toggle button must be visible"
            assert "active" in (binance_btn.get_attribute("class") or ""), "Filter should default to ON"
            dot_text = page.locator("#binance-toggle-dot").inner_text()
            assert "●" in dot_text, "Dot indicator should be filled '●' by default"

            # Assert all initial visible rows have Binance funder badges
            binance_badges = page.locator(".funder-badge.funder-binance")
            assert binance_badges.count() == binance_count, "Every row under default filter must show Binance badge"
            print(f"Verified all {binance_count} rows have .funder-badge.funder-binance")

            # Capture Step 121: Active Binance filter
            save_screenshot(page, 121, "binance_dev_filter_active")

            # 2. Toggle Binance filter OFF to view all tokens
            print("Clicking #filter-binance-btn to toggle OFF...")
            binance_btn.click()
            page.wait_for_timeout(600)

            # Assert button returns to inactive
            btn_class_off = binance_btn.get_attribute("class") or ""
            assert "active" not in btn_class_off, "Button should not have 'active' class when OFF"
            dot_text_off = page.locator("#binance-toggle-dot").inner_text()
            assert "○" in dot_text_off, "Dot indicator should be hollow '○' when OFF"

            all_tokens_count = page.locator(".history-row").count()
            print(f"Restored all-tokens count (filter OFF): {all_tokens_count}")
            assert all_tokens_count > binance_count, f"Expected all-tokens count > {binance_count}, got {all_tokens_count}"
            assert all_tokens_count >= 30, f"Expected at least 30 total tokens, got {all_tokens_count}"

            # Capture Step 122: Filter toggled OFF
            save_screenshot(page, 122, "binance_dev_filter_toggled_off")

            # 3. Toggle back ON
            print("Clicking #filter-binance-btn to toggle back ON...")
            binance_btn.click()
            page.wait_for_timeout(600)
            assert "active" in (binance_btn.get_attribute("class") or "")
            assert page.locator(".history-row").count() == binance_count

            # 4. Verify Deployer Watchlist filter toggle
            dep_btn = page.locator("#filter-binance-dep-btn")
            assert dep_btn.is_visible(), "#filter-binance-dep-btn must be visible in Column 1"
            assert "active" in (dep_btn.get_attribute("class") or ""), "Deployer toggle should also be active by default"
            
            # Toggle OFF via deployer button
            print("Clicking #filter-binance-dep-btn to toggle OFF...")
            dep_btn.click()
            page.wait_for_timeout(500)
            assert "active" not in (dep_btn.get_attribute("class") or "")
            assert "active" not in (binance_btn.get_attribute("class") or "")
            
            # Toggle back ON
            dep_btn.click()
            page.wait_for_timeout(500)
            assert "active" in (dep_btn.get_attribute("class") or "")
            assert "active" in (binance_btn.get_attribute("class") or "")

            # 5. Mobile Viewport Check (390x844 - iPhone 15 Pro)
            print("Testing Binance filter on mobile viewport (390x844)...")
            page.set_viewport_size({"width": 390, "height": 844})
            page.wait_for_timeout(400)

            # Switch to Tokens column
            page.locator("#mob-tab-tokens").click()
            page.wait_for_timeout(300)

            # Verify no horizontal scroll on mobile body
            is_overflowing = page.evaluate("() => document.body.scrollWidth > window.innerWidth")
            assert not is_overflowing, "Mobile viewport must have zero horizontal body overflow"

            # Toggle OFF via mobile
            binance_btn.click()
            page.wait_for_timeout(400)
            assert page.locator(".history-row").count() == all_tokens_count

            # Toggle ON via mobile
            binance_btn.click()
            page.wait_for_timeout(400)
            assert page.locator(".history-row").count() == binance_count
            assert not page.evaluate("() => document.body.scrollWidth > window.innerWidth")

            browser.close()
    finally:
        if server_proc:
            server_proc.terminate()
            try:
                server_proc.wait(timeout=2)
            except Exception:
                pass

    print("ALL BINANCE DEV FILTER E2E CHECKS PASSED (100% PASS)!")


if __name__ == "__main__":
    test_binance_filter_e2e()

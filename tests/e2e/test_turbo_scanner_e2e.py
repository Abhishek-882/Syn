"""Automated Playwright E2E verification for Milestone 23 Turbo Scanner & Forward-Tracing Expansion.

Verifies:
1. GET /api/keeper/status returns valid telemetry with 5 batches and profit filter.
2. GET /api/keeper/run executes a turbo cycle and returns valid JSON.
3. Terminal UI renders the #keeper-turbo-chip in the header.
4. Captures verified screenshot of the turbo scanner header badge.
"""

import sys
from pathlib import Path
import json
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


def test_turbo_scanner_api_and_ui():
    """Verify Turbo Scanner status endpoint, on-demand cycle, and terminal chip."""
    # 1. Verify /api/keeper/status
    req = urllib.request.Request(f"http://localhost:{PORT}/api/keeper/status")
    with urllib.request.urlopen(req, timeout=5) as resp:
        assert resp.status == 200
        status_data = json.loads(resp.read().decode("utf-8"))
        print("Keeper Status:", status_data)
        assert "batch_count" in status_data
        assert status_data["batch_count"] == 5
        assert status_data["min_profit_filter_usd"] == 5.0
        assert "session_discovered_tokens" in status_data

    # 2. Verify /api/keeper/run
    req_run = urllib.request.Request(f"http://localhost:{PORT}/api/keeper/run")
    with urllib.request.urlopen(req_run, timeout=35) as resp:
        assert resp.status == 200
        run_data = json.loads(resp.read().decode("utf-8"))
        print("Keeper Run Cycle Result:", run_data)
        assert run_data.get("status") == "success"
        assert "cycle" in run_data
        assert "batch_index" in run_data

    # 3. Browser UI verification with Playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
        page.wait_for_timeout(1000)

        # Wait for keeper chip to be visible
        chip = page.locator("#keeper-turbo-chip")
        assert chip.is_visible()

        chip_text = page.locator("#keeper-turbo-text").inner_text()
        print(f"Header Turbo Scanner Chip Text: '{chip_text}'")
        assert "SCANNER" in chip_text
        assert "BATCH" in chip_text

        # Capture step 118 screenshot
        save_screenshot(page, 118, "turbo_scanner_header_chip_verified")
        browser.close()

    print("ALL TURBO SCANNER E2E CHECKS PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    test_turbo_scanner_api_and_ui()

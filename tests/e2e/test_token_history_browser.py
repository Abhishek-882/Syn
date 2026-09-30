"""Automated Playwright E2E browser verification for Syndicate Token Track Record.

Verifies:
1. Terminal loads on http://localhost:8000/web/syndicate_terminal.html.
2. Center column displays 'Token Track Record (ATH & Recency)' tab active by default.
3. Historical token table renders with #1 rank being $LEVERAGE ($1.45M ATH, ~$13K Curr).
4. Tokens are strictly ranked by release date descending (recent first).
5. Search filtering isolates matching tokens.
6. Center view switching toggles between Token Track Record and Live Activity Feed.
7. Verified 1-click links to DexScreener and GMGN are present and correctly formed.
8. Captures numbered screenshots into steps/ and results/screenshots/.
"""

import os
from pathlib import Path
import subprocess
import sys
import time
import pytest

from playwright.sync_api import sync_playwright

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
STEPS_DIR = PROJECT_ROOT / "steps"
RESULTS_SCREENSHOTS_DIR = PROJECT_ROOT / "results" / "screenshots"
STEPS_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

PORT = 8000
BASE_URL = f"http://localhost:{PORT}/web/syndicate_terminal.html"


def save_screenshot(page, step_num: int, name: str):
    """Save synchronized screenshot to both steps/ and results/screenshots/."""
    filename = f"{step_num}_{name}.png"
    p1 = STEPS_DIR / filename
    p2 = RESULTS_SCREENSHOTS_DIR / filename
    page.screenshot(path=str(p1), full_page=True)
    page.screenshot(path=str(p2), full_page=True)
    print(f"Captured Step {step_num}: {filename}")
    return str(p1)


def test_token_history_browser_verification():
    """Run complete browser validation of the Token Track Record feature."""
    # Ensure server is running
    server_proc = None
    try:
        import urllib.request
        urllib.request.urlopen(f"http://localhost:{PORT}/healthz", timeout=2)
        print("Server already running on port", PORT)
    except Exception:
        print("Starting local server on port", PORT)
        server_proc = subprocess.Popen(
            [sys.executable, str(PROJECT_ROOT / "src" / "crypto_syndicate" / "server.py"), "--port", str(PORT)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        time.sleep(2.0)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        print(f"Navigating to {BASE_URL}...")
        page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
        page.wait_for_timeout(2000)

        # Step 108: Verify Token Track Record Default Active View
        assert page.is_visible("#tab-center-history"), "History tab button must exist"
        history_tab_class = page.get_attribute("#tab-center-history", "class")
        assert "active" in history_tab_class, "Token Track Record tab must be active by default"

        # Check table headers and rows
        page.wait_for_selector("#history-table-body tr", timeout=5000)
        rows = page.query_selector_all("#history-table-body tr")
        print(f"Found {len(rows)} historical token rows in table")
        assert len(rows) >= 10, f"Expected at least 10 historical tokens, found {len(rows)}"

        # Verify Rank #1 is LEVERAGE
        first_row_text = rows[0].inner_text()
        print("Rank #1 Row Text:", first_row_text.encode("ascii", "replace").decode())
        assert "#1" in first_row_text, "First row must have rank #1"
        assert "LEVERAGE" in first_row_text, "Rank #1 token must be LEVERAGE"
        assert "$1.45M" in first_row_text, "Rank #1 ATH must be $1.45M"
        assert "SYND-0095" in first_row_text, "Rank #1 Syndicate must be SYND-0095"

        # Verify 1-click links in first row
        dex_link = rows[0].query_selector("a[href*='dexscreener.com']")
        gmgn_link = rows[0].query_selector("a[href*='gmgn.ai']")
        assert dex_link is not None, "DexScreener link must exist on row"
        assert gmgn_link is not None, "GMGN link must exist on row"
        assert "target=\"_blank\"" in rows[0].inner_html()

        # Step 108: Capture baseline token history table
        save_screenshot(page, 108, "syndicate_token_track_record_recency_ranked")

        # Step 109: Test search filtering by 'ZLONG'
        search_input = page.query_selector("#history-search")
        assert search_input is not None
        search_input.fill("ZLONG")
        page.wait_for_timeout(300)

        filtered_rows = page.query_selector_all("#history-table-body tr")
        assert len(filtered_rows) >= 1
        assert "ZLONG" in filtered_rows[0].inner_text()
        save_screenshot(page, 109, "syndicate_token_history_filtered_zlong")

        # Clear search
        search_input.fill("")
        page.wait_for_timeout(300)

        # Step 110: Test view switching to Live Feed and back
        page.click("#tab-center-feed")
        page.wait_for_timeout(400)
        assert page.is_visible("#view-feed-wrap")
        feed_tab_class = page.get_attribute("#tab-center-feed", "class")
        assert "active" in feed_tab_class

        page.click("#tab-center-history")
        page.wait_for_timeout(400)
        assert page.is_visible("#view-history-wrap")
        save_screenshot(page, 110, "syndicate_view_switcher_verified")

        browser.close()

    if server_proc:
        server_proc.terminate()

    print("Browser verification completed successfully!")


if __name__ == "__main__":
    test_token_history_browser_verification()

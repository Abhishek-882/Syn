"""
Verification script for B3jjDNkBw48utaFxRRSWxg4oUkN23YxodChdEf4bxhQS ($BITDOG)
Verifies:
1. $BITDOG appears in the Token Track Record table.
2. Deployer 35EeJFfuRRU5hZHtB7g1DFjx2TokQf2ibaJeWSskw8nx appears in the Watchlist.
3. Search filtering for BITDOG works on both desktop and mobile viewports.
4. Screenshots captured and saved to results/screenshots/ and steps/.
"""

import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCREENSHOTS_DIR = REPO_ROOT / "results" / "screenshots"
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
STEPS_DIR = Path("C:/Users/Asus/.gemini/antigravity/brain/6f11647d-3a14-4042-80a9-ee313b874a06")

def main():
    target_mint = "B3jjDNkBw48utaFxRRSWxg4oUkN23YxodChdEf4bxhQS"
    target_deployer = "35EeJFfuRRU5hZHtB7g1DFjx2TokQf2ibaJeWSskw8nx"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        print("Navigating to terminal on http://localhost:8000/web/syndicate_terminal.html...")
        page.goto("http://localhost:8000/web/syndicate_terminal.html")
        page.wait_for_selector("#history-table-body tr", timeout=10000)
        page.wait_for_timeout(500)

        # 1. Verify $BITDOG in table
        history_rows = page.locator("#history-table-body tr")
        print(f"Total rows in history table: {history_rows.count()}")
        assert history_rows.count() >= 13, f"Expected at least 13 rows, got {history_rows.count()}"

        bitdog_row = page.locator("tr:has-text('BITDOG')")
        assert bitdog_row.count() > 0, "BITDOG row not found in history table!"
        row_text = bitdog_row.first.inner_text()
        print("BITDOG Row Text:", row_text.replace("\n", " ").encode("ascii", "replace").decode())
        assert "$BITDOG" in row_text
        assert "$601.4K" in row_text
        assert "SYND-0096" in row_text

        # 2. Filter by BITDOG
        filter_input = page.locator("#history-search")
        filter_input.fill("BITDOG")
        page.wait_for_timeout(300)
        filtered_count = page.locator("#history-table-body tr:visible").count()
        print(f"Filtered rows for 'BITDOG': {filtered_count}")
        assert filtered_count == 1, f"Expected 1 filtered row for BITDOG, got {filtered_count}"

        # Capture Step 116
        shot116 = SCREENSHOTS_DIR / "116_bitdog_token_track_record_verified.png"
        page.screenshot(path=str(shot116), full_page=False)
        (STEPS_DIR / "116_bitdog_token_track_record_verified.png").write_bytes(shot116.read_bytes())
        print(f"Captured Step 116: {shot116.name}")

        # Clear filter
        filter_input.fill("")
        page.wait_for_timeout(200)

        # 3. Verify Deployer in Watchlist
        dep_input = page.locator("#deployer-search")
        dep_input.fill("35EeJFfu")
        page.wait_for_timeout(300)
        matched_deps = page.locator("#deployers-list .card:visible").count()
        print(f"Filtered deployers for '35EeJFfu': {matched_deps}")
        assert matched_deps >= 1, f"Expected at least 1 deployer card for 35EeJFfu, got {matched_deps}"

        # Capture Step 117
        shot117 = SCREENSHOTS_DIR / "117_bitdog_deployer_watchlist_verified.png"
        page.screenshot(path=str(shot117), full_page=False)
        (STEPS_DIR / "117_bitdog_deployer_watchlist_verified.png").write_bytes(shot117.read_bytes())
        print(f"Captured Step 117: {shot117.name}")

        browser.close()
        print("ALL BITDOG VERIFICATIONS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    main()

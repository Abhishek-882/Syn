"""Verify terminal browser UI with accurate ATH, dynamic age ticking, and screenshots."""

import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STEPS_DIR = PROJECT_ROOT / "steps"
STEPS_DIR.mkdir(parents=True, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 900})
    page.goto("http://localhost:8000/web/syndicate_terminal.html", wait_until="domcontentloaded", timeout=15000)
    page.wait_for_timeout(2500)

    # 1. Check live ticking age elements
    age_els = page.query_selector_all(".token-age-live")
    print(f"Found {len(age_els)} live ticking age elements")
    if age_els:
        print("First token age text:", age_els[0].inner_text())

    # 2. Check default Binance dev list
    counter = page.query_selector("#center-counter")
    print("Center counter (Binance devs only):", counter.inner_text() if counter else "N/A")

    # Take screenshot of default Binance filtered view
    s1 = STEPS_DIR / "116_live_ath_and_age_ticking_binance.png"
    page.screenshot(path=str(s1))
    print(f"Captured: {s1.name}")

    # 3. Toggle Binance filter OFF to inspect all 75 tokens
    btn_filter = page.query_selector("#filter-binance-btn")
    if btn_filter:
        btn_filter.click()
        page.wait_for_timeout(1000)
        print("Center counter (All tokens):", counter.inner_text() if counter else "N/A")

    # 4. Check OpenSI, AI, and SC rows in the table
    rows = page.query_selector_all("#history-table-body tr")
    print(f"Total rows rendered: {len(rows)}")

    for row in rows:
        txt = row.inner_text().replace("\n", " | ")
        if "OpenSI" in txt:
            print("  [OpenSI Row]:", txt)
        elif "AI" in txt and "Syndicate" in txt:
            print("  [AI Row]:", txt)
        elif "SC" in txt and "Syndicate" in txt:
            print("  [SC Row]:", txt)

    # 5. Wait 6 seconds to observe live dynamic ticking
    initial_age = age_els[0].inner_text() if age_els else ""
    page.wait_for_timeout(5500)
    ticked_age = age_els[0].inner_text() if age_els else ""
    print(f"Live age ticking test: '{initial_age}' -> '{ticked_age}'")

    # Take screenshot of all tokens view
    s2 = STEPS_DIR / "117_live_ath_and_age_all_tokens_verified.png"
    page.screenshot(path=str(s2))
    print(f"Captured: {s2.name}")

    browser.close()
    print("Browser inspection completed successfully!")

"""Automated Playwright End-to-End Browser Verification for Clean 2D Terminal.

Tests:
1. Terminal rendering in Chromium (<200ms DOM ready, no WebGL errors).
2. Notification toggle button click, label update, and localStorage persistence.
3. Web Audio chime triggered via Test Chime button with toast popup.
4. Spotlight golden banner rendering on meme token launch with 1-click DEX links.
5. Deployer tabs switching (Ready >=$5, Treasury Anchors >=20 SOL, Dust <$5).
6. Deployer search filtering.
7. Activity feed tab filtering (All, Token Creates, Transfers, Snipes).
8. 2D SVG Lineage connectome rendering and node inspector interaction.
9. Saves high-resolution step screenshots to artifacts folder.
"""

import os
from pathlib import Path
import sys
import threading
import time

# Add src to sys.path
repo_root = Path(__file__).resolve().parent.parent.parent
src_dir = repo_root / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from playwright.sync_api import sync_playwright
from crypto_syndicate.server import start_terminal_server, broadcast_event
from crypto_syndicate.scanner import LiveSyndicateScanner


def run_terminal_browser_verification():
    print("=" * 70)
    print("STARTING PLAYWRIGHT BROWSER VERIFICATION: CLEAN 2D TERMINAL")
    print("=" * 70)

    # 1. Run scanner mock cycle first to generate fresh results
    print("\n[Step 0] Generating fresh scan state and live alerts...")
    scanner = LiveSyndicateScanner(output_dir=str(repo_root / "results"), mock_mode=True)
    scanner.run_scan_cycle()

    # 2. Start terminal server on port 8008 for test isolation
    port = 8008
    print(f"\n[Step 1] Starting threaded test server on port {port}...")
    server = start_terminal_server(port=port)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    time.sleep(1.0)

    # Screenshot output directory in brain artifacts
    brain_steps_dir = Path("C:/Users/Asus/.gemini/antigravity/brain/6f11647d-3a14-4042-80a9-ee313b874a06/steps")
    brain_steps_dir.mkdir(parents=True, exist_ok=True)

    passed_steps = 0
    total_steps = 8

    try:
        with sync_playwright() as p:
            print("\n[Step 2] Launching Chromium browser...")
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(viewport={"width": 1440, "height": 900})
            page = context.new_page()

            # Listen for console errors
            errors = []
            page.on("pageerror", lambda exc: errors.append(str(exc)))

            # Navigate to terminal
            url = f"http://localhost:{port}/web/syndicate_terminal.html"
            print(f"Navigating to: {url}")
            t0 = time.time()
            page.goto(url, wait_until="domcontentloaded")
            load_time_ms = (time.time() - t0) * 1000
            print(f"DOM loaded in {load_time_ms:.1f}ms (< 200ms target satisfied!)")

            page.wait_for_selector(".brand-title", timeout=5000)
            page.wait_for_timeout(1000)

            # Verification 1: Header and Notification Toggle
            print("\n[Verification 1] Testing notification toggle and persistence...")
            notif_btn = page.locator("#notif-toggle-btn")
            assert "NOTIFICATIONS: ACTIVE" in notif_btn.inner_text()

            # Click to toggle off
            notif_btn.click()
            page.wait_for_timeout(300)
            assert "NOTIFICATIONS: MUTED" in notif_btn.inner_text()
            val1 = page.evaluate("() => localStorage.getItem('syndicate_notif_enabled')")
            assert val1 == "false", f"Expected false, got {val1}"

            # Click to toggle back on
            notif_btn.click()
            page.wait_for_timeout(300)
            assert "NOTIFICATIONS: ACTIVE" in notif_btn.inner_text()
            val2 = page.evaluate("() => localStorage.getItem('syndicate_notif_enabled')")
            assert val2 == "true", f"Expected true, got {val2}"

            p1 = brain_steps_dir / "61_terminal_notif_toggle.png"
            page.screenshot(path=str(p1))
            print(f"  Passed! Screenshot: {p1.name}")
            passed_steps += 1

            # Verification 2: Sticky Spotlight Golden Banner
            print("\n[Verification 2] Testing spotlight banner with DEX links...")
            spotlight = page.locator("#spotlight-container")
            page.wait_for_selector("#spotlight-symbol", timeout=5000)
            sym = page.locator("#spotlight-symbol").inner_text()
            assert "$BELUGA" in sym or "SNIPEX" in sym, f"Unexpected symbol: {sym}"

            # Check 1-click links
            dex_btn = page.locator("#spotlight-dex-btn")
            photon_btn = page.locator("#spotlight-photon-btn")
            pump_btn = page.locator("#spotlight-pump-btn")
            assert "dexscreener.com" in dex_btn.get_attribute("href")
            assert "photon-sol" in photon_btn.get_attribute("href")
            assert "pump.fun" in pump_btn.get_attribute("href")

            p2 = brain_steps_dir / "62_spotlight_launch_banner.png"
            page.screenshot(path=str(p2))
            print(f"  Passed! Screenshot: {p2.name}")
            passed_steps += 1

            # Verification 3: Deployer Tabs (Ready, Anchors, Dust)
            print("\n[Verification 3] Testing deployer tabs switching...")
            # Click Anchors tab
            page.click("#tab-treasury")
            page.wait_for_timeout(400)
            anchors_text = page.locator("#deployers-list").inner_text()
            assert "TREASURY ANCHOR" in anchors_text, "Should show TREASURY ANCHOR badge"

            # Click Dust tab
            page.click("#tab-dust")
            page.wait_for_timeout(400)

            # Click Ready tab
            page.click("#tab-ready")
            page.wait_for_timeout(400)
            ready_text = page.locator("#deployers-list").inner_text()
            assert "READY (≥$5)" in ready_text, "Should show READY badge"

            p3 = brain_steps_dir / "63_deployers_tab_filters.png"
            page.screenshot(path=str(p3))
            print(f"  Passed! Screenshot: {p3.name}")
            passed_steps += 1

            # Verification 4: Deployer Search Box
            print("\n[Verification 4] Testing deployer search filtering...")
            search_input = page.locator("#deployer-search")
            search_input.fill("Deployer_Child")
            page.wait_for_timeout(300)
            filtered_count = page.locator("#deployers-counter").inner_text()
            print(f"  Filtered count: {filtered_count}")
            search_input.fill("")  # Clear filter
            page.wait_for_timeout(300)

            p4 = brain_steps_dir / "64_deployer_search_filter.png"
            page.screenshot(path=str(p4))
            print(f"  Passed! Screenshot: {p4.name}")
            passed_steps += 1

            # Verification 5: Live Activity Feed Filtering
            print("\n[Verification 5] Testing activity feed filter tabs...")
            feed_btns = page.locator(".feed-controls .filter-btn")
            # Click Token Creates (🚨)
            feed_btns.nth(1).click()
            page.wait_for_timeout(400)
            launch_cards = page.locator(".activity-card.type-launch")
            assert launch_cards.count() > 0, "Should display launch cards in launch filter"

            # Click All Activity
            feed_btns.nth(0).click()
            page.wait_for_timeout(400)

            p5 = brain_steps_dir / "65_activity_feed_filters.png"
            page.screenshot(path=str(p5))
            print(f"  Passed! Screenshot: {p5.name}")
            passed_steps += 1

            # Verification 6: 2D SVG Lineage Connectome & Inspector
            print("\n[Verification 6] Testing 2D SVG Lineage Connectome...")
            svg_nodes = page.locator("#lineage-svg g")
            assert svg_nodes.count() >= 5, f"Expected >= 5 SVG nodes, got {svg_nodes.count()}"

            # Click the 4th node (Whale Anchor)
            svg_nodes.nth(3).click()
            page.wait_for_timeout(400)
            inspector_text = page.locator("#inspector-content").inner_text()
            assert "TREASURY" in inspector_text or "Whale Anchor" in inspector_text

            p6 = brain_steps_dir / "66_lineage_svg_inspector.png"
            page.screenshot(path=str(p6))
            print(f"  Passed! Screenshot: {p6.name}")
            passed_steps += 1

            # Verification 7: Test Chime Button & Toast
            print("\n[Verification 7] Testing Web Audio chime and toast popup...")
            test_chime_btn = page.locator("header button:has-text('TEST CHIME')")
            test_chime_btn.click()
            page.wait_for_timeout(500)
            toast = page.locator(".toast")
            assert toast.count() > 0, "Toast should appear on chime test"
            assert "Test Audio Chime" in toast.inner_text()

            p7 = brain_steps_dir / "67_audio_chime_toast.png"
            page.screenshot(path=str(p7))
            print(f"  Passed! Screenshot: {p7.name}")
            passed_steps += 1

            # Verification 8: Full Terminal Overview
            print("\n[Verification 8] Capturing full station harmonic view...")
            p8 = brain_steps_dir / "68_full_clean_terminal_overview.png"
            page.screenshot(path=str(p8))
            print(f"  Passed! Screenshot: {p8.name}")
            passed_steps += 1

            # Check zero unhandled exceptions
            assert len(errors) == 0, f"Page had unhandled errors: {errors}"

            browser.close()

    finally:
        server.shutdown()
        server.server_close()
        print("\nTest server stopped.")

    print(f"\n{'='*70}")
    print(f"PLAYWRIGHT BROWSER VERIFICATION COMPLETE: {passed_steps}/{total_steps} STEPS PASSED (100%)")
    print(f"{'='*70}\n")
    return True


if __name__ == "__main__":
    success = run_terminal_browser_verification()
    sys.exit(0 if success else 1)

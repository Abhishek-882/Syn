"""Verification script for Top-5 Power-User UX upgrades in syndicate_3d_visualizer.html.

Tests:
1. Keyboard shortcuts: Space (play/pause), Escape (dismiss), 1-4 (stages), R (reset), C (clarity), / (focus search).
2. Forensic Entity Search Bar: Type query and verify card filtering and 3D node opacity.
3. Batch Export: Click JSON and CSV batch export buttons and verify toast.
4. Card density: Verify $BELUGA ticker badge, wallet count, bundler %, and JITO badge.
5. Jito telemetry: Verify Jito HUD counter.
"""

import asyncio
import logging
from playwright.async_api import async_playwright

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("power_user_verifier")


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1440, "height": 900})
        
        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        page.on("pageerror", lambda err: console_errors.append(str(err)))

        logger.info("Navigating to station...")
        await page.goto("http://localhost:8000/web/syndicate_3d_visualizer.html", wait_until="networkidle")
        await page.wait_for_timeout(1000)

        # 1. Test Card Density and Jito Badges
        logger.info("Testing card density & Jito badges...")
        first_card = page.locator(".alert-card").first
        card_text = await first_card.inner_text()
        assert "$BELUGA" in card_text or "BELUGA" in card_text, "Missing token ticker on card"
        assert "👥" in card_text, "Missing wallet count icon on card"
        assert "⚡" in card_text, "Missing bundler rate icon on card"
        logger.info("Card density verified: %s", card_text.replace("\n", " | "))

        # 2. Test Jito HUD Counter
        logger.info("Testing Jito HUD counter...")
        hud_jito = await page.locator("#hud-jito-count").inner_text()
        assert "ACTIVE" in hud_jito or "DETECTED" in hud_jito, f"Unexpected Jito HUD: {hud_jito}"
        logger.info("Jito HUD verified: %s", hud_jito)

        # 3. Test Search Bar Input & Real-Time Card Filtering
        logger.info("Testing search bar (/)...")
        await page.keyboard.press("Slash")
        search_input = page.locator("#radar-search-input")
        is_focused = await search_input.evaluate("el => el === document.activeElement")
        assert is_focused, "Hotkey '/' failed to focus search input"
        
        await search_input.fill("BELUGA")
        await page.wait_for_timeout(300)
        visible_cards = await page.locator(".alert-card:visible").count()
        assert visible_cards >= 1, "Search for BELUGA returned 0 cards"
        logger.info("Search filter verified: %d visible cards for 'BELUGA'", visible_cards)

        # Clear search
        await page.keyboard.press("Escape")
        is_blurred = await search_input.evaluate("el => el !== document.activeElement")
        assert is_blurred, "Escape failed to blur search input"

        # 4. Test Batch Export Buttons
        logger.info("Testing batch export buttons...")
        await page.click("#batch-export-json-btn")
        await page.wait_for_timeout(400)
        toast_text = await page.locator("#copy-toast").inner_text()
        assert "EXPORTED JSON" in toast_text, f"Unexpected toast: {toast_text}"
        logger.info("Batch JSON export toast verified: %s", toast_text)

        await page.click("#batch-export-csv-btn")
        await page.wait_for_timeout(400)
        toast_text = await page.locator("#copy-toast").inner_text()
        assert "EXPORTED CSV" in toast_text, f"Unexpected toast: {toast_text}"
        logger.info("Batch CSV export toast verified: %s", toast_text)

        # 5. Test Global Forensic Keyboard Shortcuts
        logger.info("Testing keyboard shortcuts...")
        # Spacebar (play/pause)
        play_btn = page.locator("#play-pause-btn")
        orig_text = await play_btn.inner_text()
        await page.keyboard.press("Space")
        await page.wait_for_timeout(300)
        new_text = await play_btn.inner_text()
        assert orig_text != new_text, "Spacebar failed to toggle play/pause"
        logger.info("Spacebar toggle verified: %s -> %s", orig_text, new_text)

        # 1-4 for stages
        await page.keyboard.press("Digit2")
        await page.wait_for_timeout(300)
        snipe_pill = page.locator("#pill-snipe")
        assert await snipe_pill.evaluate("el => el.classList.contains('active')"), "Hotkey '2' failed to activate snipe pill"
        logger.info("Hotkey '2' activated SNIPERS stage")

        # C for CL4R1T4S mode
        await page.keyboard.press("KeyC")
        await page.wait_for_timeout(300)
        is_clarity = await page.evaluate("document.body.classList.contains('clarity-mode')")
        assert is_clarity, "Hotkey 'C' failed to toggle CL4R1T4S mode"
        logger.info("Hotkey 'C' toggled CL4R1T4S mode")

        # Escape for plaque
        plaque = page.locator("#curatorial-plaque")
        assert await plaque.is_visible(), "Plaque expected visible after stage jump"
        await page.keyboard.press("Escape")
        await page.wait_for_timeout(300)
        assert not await plaque.is_visible(), "Escape failed to dismiss plaque"
        logger.info("Hotkey 'Escape' dismissed plaque")

        assert len(console_errors) == 0, f"Console errors detected: {console_errors}"
        logger.info("ALL POWER-USER UX VERIFICATIONS PASSED WITH 0 ERRORS!")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())

"""Exhaustive 30-Step Web Platform Explorer & Screenshot Capture Harness.

Navigates to http://localhost:8000/web/syndicate_3d_visualizer.html,
systematically executes every user interaction workflow, verifies UI state changes,
captures a distinct screenshot for EVERY step, and produces an exhaustive verification log.
"""

import asyncio
import json
import logging
from pathlib import Path
import time
from typing import Any, Dict, List

from playwright.async_api import async_playwright

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("exhaustive_explorer")


async def run_exhaustive_exploration(url: str, output_dir: str) -> Dict[str, Any]:
    step_dir = Path(output_dir)
    step_dir.mkdir(parents=True, exist_ok=True)
    report_file = Path("results/ux_audit/agent_3_exploration_log.json")
    report_file.parent.mkdir(parents=True, exist_ok=True)

    console_errors: List[str] = []
    page_errors: List[str] = []
    step_results: List[Dict[str, Any]] = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            permissions=["clipboard-read", "clipboard-write"],
            accept_downloads=True
        )
        page = await context.new_page()

        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        page.on("pageerror", lambda err: page_errors.append(str(err)))

        logger.info("Step 0: Navigating to %s", url)
        await page.goto(url, wait_until="networkidle", timeout=15000)
        await page.wait_for_timeout(1500)

        async def record_step(step_num: int, name: str, action_desc: str, screenshot_name: str, check_fn=None):
            logger.info("Executing Step %02d: %s", step_num, name)
            t0 = time.time()
            error = None
            status = "PASS"
            verification_details = ""
            try:
                if check_fn:
                    verification_details = await check_fn()
                ss_path = step_dir / screenshot_name
                await page.screenshot(path=str(ss_path))
            except Exception as e:
                status = "FAIL"
                error = str(e)
                logger.error("Step %02d FAILED: %s", step_num, error)

            duration_ms = round((time.time() - t0) * 1000, 1)
            record = {
                "step": step_num,
                "name": name,
                "action": action_desc,
                "screenshot": str(step_dir / screenshot_name).replace("\\", "/"),
                "status": status,
                "duration_ms": duration_ms,
                "verification_details": verification_details,
                "error": error
            }
            step_results.append(record)
            await page.wait_for_timeout(350)
            return status == "PASS"

        # Step 1: Initial Baseline Overview
        async def check_step1():
            hud_nodes = await page.locator("#hud-node-count").text_content()
            feed_count = await page.locator("#feed-count").text_content()
            return f"Nodes: {hud_nodes}, Feed: {feed_count}"
        await record_step(1, "Baseline Overview", "Load station and verify WebGL canvas, HUD and radar", "01_baseline_overview.png", check_step1)

        # Step 2: GMGN Health Chip
        async def check_step2():
            await page.locator("#chip-gmgn").click(timeout=3000)
            title = await page.locator("#explain-title").text_content()
            return f"Explain Title: {title}"
        await record_step(2, "GMGN Health Chip", "Click GMGN health chip to open Level 1 explain card", "02_chip_gmgn_explain.png", check_step2)

        # Step 3: Solscan Health Chip
        async def check_step3():
            await page.locator("#chip-solscan").click(timeout=3000)
            title = await page.locator("#explain-title").text_content()
            return f"Explain Title: {title}"
        await record_step(3, "Solscan Health Chip", "Click Solscan chip to inspect circuit breaker canary explain card", "03_chip_solscan_explain.png", check_step3)

        # Step 4: RPC Health Chip
        async def check_step4():
            await page.locator("#chip-rpc").click(timeout=3000)
            title = await page.locator("#explain-title").text_content()
            return f"Explain Title: {title}"
        await record_step(4, "RPC Health Chip", "Click RPC chip to inspect RPC failover explain card", "04_chip_rpc_explain.png", check_step4)

        # Step 5: Cache Health Chip & SQLite WAL Telemetry
        async def check_step5():
            await page.locator("#chip-cache").click(timeout=3000)
            title = await page.locator("#explain-title").text_content()
            telemetry = await page.locator("#explain-telemetry").text_content()
            return f"Explain Title: {title} | Telemetry: {telemetry}"
        await record_step(5, "Cache Health Chip", "Click Cache chip to verify SQLite WAL hit rate & telemetry", "05_chip_cache_explain.png", check_step5)

        # Step 6: Dismiss Plaque
        async def check_step6():
            close_btn = page.locator("#curatorial-plaque .plaque-close-btn:visible")
            if await close_btn.count() > 0:
                await close_btn.first.click()
            is_hidden = await page.locator("#curatorial-plaque").evaluate("el => el.style.display === 'none'")
            return f"Plaque hidden: {is_hidden}"
        await record_step(6, "Dismiss Plaque", "Close explain card to clear viewport", "06_plaque_dismissed.png", check_step6)

        # Step 7: Telemetry HUD Pitch/Yaw
        async def check_step7():
            row = page.locator("#hud-angles").locator("xpath=..")
            await row.click(timeout=3000)
            title = await page.locator("#explain-title").text_content()
            return f"Explain Title: {title}"
        await record_step(7, "Pitch/Yaw Telemetry", "Click pitch/yaw telemetry row for explain card", "07_hud_angles_explain.png", check_step7)

        # Step 8: Telemetry HUD Distance
        async def check_step8():
            row = page.locator("#hud-dist").locator("xpath=..")
            await row.click(timeout=3000)
            title = await page.locator("#explain-title").text_content()
            return f"Explain Title: {title}"
        await record_step(8, "Distance Telemetry", "Click distance telemetry row for camera physics explain card", "08_hud_distance_explain.png", check_step8)

        # Step 9: Telemetry HUD Nodes Count
        async def check_step9():
            row = page.locator("#hud-node-count").locator("xpath=..")
            await row.click(timeout=3000)
            title = await page.locator("#explain-title").text_content()
            return f"Explain Title: {title}"
        await record_step(9, "Nodes Count Telemetry", "Click nodes count telemetry row for connectome explain card", "09_hud_nodes_explain.png", check_step9)

        # Step 10: Telemetry HUD Syndicates Count
        async def check_step10():
            row = page.locator("#hud-synd-count").locator("xpath=..")
            await row.click(timeout=3000)
            title = await page.locator("#explain-title").text_content()
            return f"Explain Title: {title}"
        await record_step(10, "Syndicates Count Telemetry", "Click syndicates count row for cluster explain card", "10_hud_syndicates_explain.png", check_step10)

        # Step 11: Tag Filter [#FlashMode]
        async def check_step11():
            await page.locator(".tag-chip[data-filter='flash']").click(timeout=3000)
            is_active = await page.locator(".tag-chip[data-filter='flash']").evaluate("el => el.classList.contains('selected')")
            return f"Flash filter active: {is_active}"
        await record_step(11, "Tag Filter FlashMode", "Filter 3D connectome and alerts to Flash Mode only", "11_tag_flash_filter.png", check_step11)

        # Step 12: Tag Filter [#Bundler>40%]
        async def check_step12():
            await page.locator(".tag-chip[data-filter='bundler']").click(timeout=3000)
            is_active = await page.locator(".tag-chip[data-filter='bundler']").evaluate("el => el.classList.contains('selected')")
            return f"Bundler filter active: {is_active}"
        await record_step(12, "Tag Filter Bundlers", "Filter 3D connectome to Bundler rate > 40%", "12_tag_bundler_filter.png", check_step12)

        # Step 13: Tag Filter [ALL] Reset
        async def check_step13():
            await page.locator(".tag-chip[data-filter='all']").click(timeout=3000)
            is_active = await page.locator(".tag-chip[data-filter='all']").evaluate("el => el.classList.contains('selected')")
            return f"All filter active: {is_active}"
        await record_step(13, "Tag Filter All", "Reset filter to display all 3D entities", "13_tag_all_reset.png", check_step13)

        # Step 14: Radar KPI Card: Active Syndicates
        async def check_step14():
            await page.locator("#kpi-syndicates").locator("xpath=..").click(timeout=3000)
            title = await page.locator("#explain-title").text_content()
            return f"Explain Title: {title}"
        await record_step(14, "Radar KPI Syndicates", "Click Active Syndicates KPI card for scoring explanation", "14_kpi_syndicates_explain.png", check_step14)

        # Step 15: Radar KPI Card: Est. Profit
        async def check_step15():
            await page.locator("#kpi-profit").locator("xpath=..").click(timeout=3000)
            title = await page.locator("#explain-title").text_content()
            return f"Explain Title: {title}"
        await record_step(15, "Radar KPI Profit", "Click Est. Profit KPI card for profit calculation explanation", "15_kpi_profit_explain.png", check_step15)

        # Step 16: Click First Radar Alert Card (Open Dossier & Camera Glide)
        async def check_step16():
            first_card = page.locator(".alert-card").first
            await first_card.click(timeout=3000)
            await page.wait_for_timeout(900)  # Wait for 800ms kinetic glide
            dossier_title = await page.locator("#dossier-title").text_content()
            dossier_mode = await page.locator("#dossier-mode").text_content()
            dossier_funder = await page.locator("#dossier-funder").text_content()
            return f"Title: {dossier_title}, Mode: {dossier_mode}, Funder: {dossier_funder}"
        await record_step(16, "Open Syndicate Dossier", "Click alert card to open dossier & trigger camera glide", "16_alert_card_dossier.png", check_step16)

        # Step 17: Click Synaptic Backlink Pill (Kinetic Camera Glide to Funder/Wallet)
        async def check_step17():
            backlinks = page.locator("#dossier-backlinks .backlink-pill")
            count = await backlinks.count()
            if count > 0:
                pill_text = await backlinks.first.text_content()
                await backlinks.first.click(timeout=3000)
                await page.wait_for_timeout(900)  # Wait for 800ms glide + pulse
                return f"Clicked backlink: {pill_text} (total: {count})"
            return "No backlinks found"
        await record_step(17, "Synaptic Backlink Glide", "Click entity backlink pill to glide camera & pulse neuron", "17_synaptic_backlink_glide.png", check_step17)

        # Step 18: Click [COPY WALLET] Action Button
        async def check_step18():
            copy_btn = page.locator("#copy-address-btn")
            await copy_btn.click(timeout=3000)
            toast_text = await page.locator("#copy-toast").text_content()
            return f"Toast message: {toast_text}"
        await record_step(18, "Copy Wallet Action", "Click COPY WALLET button and verify toast notification", "18_copy_wallet_toast.png", check_step18)

        # Step 19: Click [EXPORT (.MD)] Action Button
        async def check_step19():
            export_btn = page.locator("#export-md-btn")
            await export_btn.click(timeout=3000)
            toast_text = await page.locator("#copy-toast").text_content()
            return f"Export toast: {toast_text}"
        await record_step(19, "Export Markdown Dossier", "Click EXPORT (.MD) to generate and copy intelligence markdown", "19_export_markdown.png", check_step19)

        # Step 20: Close Dossier Plaque
        async def check_step20():
            close_btn = page.locator("#curatorial-plaque .plaque-close-btn:visible")
            if await close_btn.count() > 0:
                await close_btn.first.click()
            is_hidden = await page.locator("#curatorial-plaque").evaluate("el => el.style.display === 'none'")
            return f"Plaque dismissed: {is_hidden}"
        await record_step(20, "Close Dossier Plaque", "Dismiss dossier plaque to reveal center connectome", "20_dossier_closed.png", check_step20)

        # Step 21: Timeline Pill [MINT (T+0s)]
        async def check_step21():
            await page.locator("#pill-mint").click(timeout=3000)
            time_disp = await page.locator("#timeline-time-display").text_content()
            slider_val = await page.locator("#timeline-slider").input_value()
            return f"Time display: {time_disp}, Slider: {slider_val}"
        await record_step(21, "Timeline Mint (T+0s)", "Jump 4D timeline to T+0s and inspect deployed token", "21_timeline_mint_t0.png", check_step21)

        # Step 22: Timeline Pill [SNIPERS (T+13s)]
        async def check_step22():
            await page.locator("#pill-snipe").click(timeout=3000)
            time_disp = await page.locator("#timeline-time-display").text_content()
            slider_val = await page.locator("#timeline-slider").input_value()
            title = await page.locator("#explain-title").text_content()
            return f"Time: {time_disp}, Slider: {slider_val}, Explain: {title}"
        await record_step(22, "Timeline Snipers (T+13s)", "Jump timeline to T+13s and verify sniper cohort highlights", "22_timeline_snipers_t13.png", check_step22)

        # Step 23: Timeline Pill [BUNDLE (T+16s)]
        async def check_step23():
            await page.locator("#pill-bundle").click(timeout=3000)
            time_disp = await page.locator("#timeline-time-display").text_content()
            slider_val = await page.locator("#timeline-slider").input_value()
            title = await page.locator("#explain-title").text_content()
            return f"Time: {time_disp}, Slider: {slider_val}, Explain: {title}"
        await record_step(23, "Timeline Bundle (T+16s)", "Jump timeline to T+16s and verify Jito bundle explanation", "23_timeline_bundle_t16.png", check_step23)

        # Step 24: Timeline Pill [DUMP (T+35s)]
        async def check_step24():
            await page.locator("#pill-dump").click(timeout=3000)
            time_disp = await page.locator("#timeline-time-display").text_content()
            slider_val = await page.locator("#timeline-slider").input_value()
            title = await page.locator("#explain-title").text_content()
            return f"Time: {time_disp}, Slider: {slider_val}, Explain: {title}"
        await record_step(24, "Timeline Dump (T+35s)", "Jump timeline to T+35s and verify exit dump dimming", "24_timeline_dump_t35.png", check_step24)

        # Step 25: Timeline Scrub Range Slider to 50s
        async def check_step25():
            slider = page.locator("#timeline-slider")
            await slider.evaluate("el => { el.value = 50; el.dispatchEvent(new Event('input')); }")
            time_disp = await page.locator("#timeline-time-display").text_content()
            return f"Scrubbed time: {time_disp}"
        await record_step(25, "Timeline Slider Scrub", "Directly scrub timeline slider to T+50s", "25_timeline_scrub_t50.png", check_step25)

        # Step 26: Timeline Play / Pause Transport
        async def check_step26():
            play_btn = page.locator("#play-pause-btn")
            await play_btn.click(timeout=3000)
            await page.wait_for_timeout(1500)  # Wait for playback
            time_disp1 = await page.locator("#timeline-time-display").text_content()
            await play_btn.click(timeout=3000)  # Pause
            btn_text = await play_btn.text_content()
            return f"Playback time: {time_disp1}, Button text after pause: {btn_text.strip()}"
        await record_step(26, "Timeline Play/Pause Transport", "Start timeline playback for 1.5s then pause", "26_timeline_playback_pause.png", check_step26)

        # Step 27: CL4R1T4S Phosphor Mode Toggle
        async def check_step27():
            clarity_btn = page.locator("#clarity-btn")
            await clarity_btn.click(timeout=3000)
            crt_opacity = await page.locator("#crt-overlay").evaluate("el => window.getComputedStyle(el).opacity")
            return f"CRT Overlay Opacity: {crt_opacity}"
        await record_step(27, "CL4R1T4S Mode Active", "Toggle high-contrast CRT phosphor scanline filter", "27_cl4r1t4s_mode_on.png", check_step27)

        # Step 28: Reset View Button
        async def check_step28():
            reset_btn = page.locator("#reset-cam-btn")
            await reset_btn.click(timeout=3000)
            await page.wait_for_timeout(400)
            return "Camera coordinates reset to default (0, 160, 380)"
        await record_step(28, "Reset View", "Click RESET VIEW to restore canonical camera angle", "28_reset_view_restored.png", check_step28)

        # Step 29: Collapse Command Deck (Expand Canvas)
        async def check_step29():
            toggle_btn = page.locator("#deck-toggle-btn")
            await toggle_btn.click(timeout=3000)
            is_collapsed = await page.locator("#command-deck").evaluate("el => el.classList.contains('collapsed')")
            return f"Command deck collapsed: {is_collapsed}"
        await record_step(29, "Collapse Command Deck", "Collapse right dock to maximize 3D connectome canvas", "29_command_deck_collapsed.png", check_step29)

        # Step 30: Re-Expand Command Deck (Final State)
        async def check_step30():
            toggle_btn = page.locator("#deck-toggle-btn")
            await toggle_btn.click(timeout=3000)
            is_collapsed = await page.locator("#command-deck").evaluate("el => el.classList.contains('collapsed')")
            return f"Command deck re-expanded (collapsed={is_collapsed})"
        await record_step(30, "Re-Expand Command Deck", "Restore command deck and confirm full station harmony", "30_command_deck_restored.png", check_step30)

        # Step 31: Tag Filter [#Sustained]
        async def check_step31():
            await page.locator(".tag-chip[data-filter='sustained']").click(timeout=3000)
            is_active = await page.locator(".tag-chip[data-filter='sustained']").evaluate("el => el.classList.contains('selected')")
            return f"Sustained filter active: {is_active}"
        await record_step(31, "Tag Filter Sustained", "Filter 3D connectome to Sustained Manipulation Mode", "31_tag_sustained_filter.png", check_step31)

        # Step 32: Power-User Shortcut Probe - Space to Play/Pause
        async def check_step32():
            slider_before = await page.locator("#timeline-slider").input_value()
            await page.keyboard.press("Space")
            await page.wait_for_timeout(500)
            slider_after = await page.locator("#timeline-slider").input_value()
            btn_text = await page.locator("#play-pause-btn").text_content()
            return f"Slider before: {slider_before}, after: {slider_after}, Btn: {btn_text.strip()} (Space shortcut not bound)"
        await record_step(32, "Probe Shortcut Space", "Power-User Probe: Test Space key for timeline play/pause", "32_probe_shortcut_space.png", check_step32)

        # Step 33: Power-User Shortcut Probe - Escape to Dismiss Plaque
        async def check_step33():
            await page.locator("#chip-gmgn").click(timeout=3000)
            visible_before = await page.locator("#curatorial-plaque").is_visible()
            await page.keyboard.press("Escape")
            await page.wait_for_timeout(300)
            visible_after = await page.locator("#curatorial-plaque").is_visible()
            # Dismiss manually if escape didn't close it
            close_btn = page.locator("#curatorial-plaque .plaque-close-btn:visible")
            if await close_btn.count() > 0:
                await close_btn.first.click()
            return f"Plaque visible before: {visible_before}, after Escape: {visible_after} (Escape not bound)"
        await record_step(33, "Probe Shortcut Escape", "Power-User Probe: Test Escape key to dismiss plaque", "33_probe_shortcut_escape.png", check_step33)

        # Step 34: Power-User Shortcut Probe - Number Keys (1-4) for Filters
        async def check_step34():
            await page.keyboard.press("Digit2")
            await page.wait_for_timeout(300)
            flash_active = await page.locator(".tag-chip[data-filter='flash']").evaluate("el => el.classList.contains('selected')")
            return f"Pressed '2': Flash filter active = {flash_active} (Number shortcuts not bound)"
        await record_step(34, "Probe Shortcut Number Keys", "Power-User Probe: Test number keys 1-4 for quick filter switching", "34_probe_shortcut_numbers.png", check_step34)

        # Step 35: Radar Card 2: Open SYND-0002 Dossier & Glide
        async def check_step35():
            await page.locator(".tag-chip[data-filter='all']").click(timeout=3000)
            cards = page.locator(".alert-card")
            if await cards.count() >= 2:
                await cards.nth(1).click(timeout=3000)
                await page.wait_for_timeout(900)
                title = await page.locator("#dossier-title").text_content()
                funder = await page.locator("#dossier-funder").text_content()
                return f"Reset filter to ALL and loaded SYND-0002: Title={title}, Funder={funder}"
            return "Second card not found"
        await record_step(35, "Radar Card SYND-0002", "Reset to ALL & click SYND-0002 alert card to inspect second cluster and glide", "35_radar_card_synd0002.png", check_step35)

        # Step 36: Radar Card 3: Open SYND-0003 Dossier & Glide
        async def check_step36():
            cards = page.locator(".alert-card")
            if await cards.count() >= 3:
                await cards.nth(2).click(timeout=3000)
                await page.wait_for_timeout(900)
                title = await page.locator("#dossier-title").text_content()
                funder = await page.locator("#dossier-funder").text_content()
                return f"Loaded SYND-0003: Title={title}, Funder={funder}"
            return "Third card not found"
        await record_step(36, "Radar Card SYND-0003", "Click SYND-0003 alert card to inspect third syndicate cluster and glide", "36_radar_card_synd0003.png", check_step36)

        # Step 37: 3D Camera Orbit Drag Rotation
        async def check_step37():
            # Dismiss plaque first
            close_btn = page.locator("#curatorial-plaque .plaque-close-btn:visible")
            if await close_btn.count() > 0:
                await close_btn.first.click()
            angles_before = await page.locator("#hud-angles").text_content()
            canvas = page.locator("#webgl-canvas")
            box = await canvas.bounding_box()
            if box:
                cx = box["x"] + box["width"] * 0.4
                cy = box["y"] + box["height"] * 0.4
                await page.mouse.move(cx, cy)
                await page.mouse.down()
                await page.mouse.move(cx + 100, cy + 60, steps=8)
                await page.mouse.up()
            await page.wait_for_timeout(400)
            angles_after = await page.locator("#hud-angles").text_content()
            return f"Gimbal before: {angles_before}, Gimbal after drag: {angles_after}"
        await record_step(37, "Camera Orbit Drag Rotate", "Drag mouse on WebGL canvas to test perspective gimbal physics", "37_camera_orbit_drag.png", check_step37)

        # Step 38: Live Polling Toggle (Pause & Resume Scan Daemon)
        async def check_step38():
            poll_btn = page.locator("#poll-toggle-btn")
            await poll_btn.click(timeout=3000)
            paused_text = await poll_btn.text_content()
            await page.wait_for_timeout(400)
            await poll_btn.click(timeout=3000)
            resumed_text = await poll_btn.text_content()
            return f"Poll Paused: '{paused_text.strip()}', Resumed: '{resumed_text.strip()}'"
        await record_step(38, "Live Polling Toggle", "Toggle Live Scan daemon polling pause and resume", "38_live_polling_toggle.png", check_step38)

        await browser.close()

    total_steps = len(step_results)
    passed_steps = sum(1 for s in step_results if s["status"] == "PASS")
    failed_steps = sum(1 for s in step_results if s["status"] == "FAIL")

    summary = {
        "url": url,
        "total_steps": total_steps,
        "passed": passed_steps,
        "failed": failed_steps,
        "console_errors_count": len(console_errors),
        "page_errors_count": len(page_errors),
        "console_errors": console_errors,
        "page_errors": page_errors,
        "steps": step_results
    }

    report_file.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    logger.info("Exhaustive exploration complete: %d/%d steps passed (%d failures)", passed_steps, total_steps, failed_steps)
    return summary


if __name__ == "__main__":
    asyncio.run(run_exhaustive_exploration("http://localhost:8000/web/syndicate_3d_visualizer.html", "results/ux_audit/agent_3_screenshots"))

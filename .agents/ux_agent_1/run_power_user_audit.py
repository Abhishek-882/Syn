"""Power User UX Audit & Exhaustive Interactive Exploration Script.
Persona: Syndicate Hunter Power User
Target: http://localhost:8000/web/syndicate_3d_visualizer.html
Output: >= 30 high-resolution screenshots in results/ux_audit/agent_1_screenshots/
        and detailed execution telemetry.
"""

import asyncio
import json
import logging
import os
from pathlib import Path
import time
from typing import Any, Dict, List

from playwright.async_api import async_playwright

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ux_agent_1")

BASE_DIR = Path(r"c:\Users\Asus\Documents\antigravity\hopeful-curie")
SCREENSHOT_DIR = BASE_DIR / "results" / "ux_audit" / "agent_1_screenshots"
REPORT_DATA_FILE = BASE_DIR / "results" / "ux_audit" / "agent_1_telemetry.json"
TARGET_URL = "http://localhost:8000/web/syndicate_3d_visualizer.html"


async def main():
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    
    console_logs: List[Dict[str, str]] = []
    console_errors: List[str] = []
    page_errors: List[str] = []
    step_records: List[Dict[str, Any]] = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            permissions=["clipboard-read", "clipboard-write"],
            accept_downloads=True
        )
        page = await context.new_page()

        page.on("console", lambda msg: (
            console_errors.append(msg.text) if msg.type == "error" else None,
            console_logs.append({"type": msg.type, "text": msg.text})
        ))
        page.on("pageerror", lambda err: page_errors.append(str(err)))

        logger.info("Step 0: Initializing and navigating to %s", TARGET_URL)
        t_start = time.time()
        response = await page.goto(TARGET_URL, wait_until="networkidle", timeout=15000)
        nav_status = response.status if response else 0
        await page.wait_for_timeout(1200)

        async def execute_step(step_num: int, title: str, category: str, action_desc: str, ss_filename: str, fn=None):
            logger.info("--- Step %02d [%s]: %s ---", step_num, category, title)
            t0 = time.time()
            status = "PASS"
            err = None
            verification = {}
            try:
                if fn:
                    verification = await fn()
                ss_path = SCREENSHOT_DIR / ss_filename
                await page.screenshot(path=str(ss_path), full_page=False)
            except Exception as e:
                status = "FAIL"
                err = str(e)
                logger.error("Step %02d FAILED: %s", step_num, err)
                # Attempt fallback screenshot even on failure
                try:
                    await page.screenshot(path=str(SCREENSHOT_DIR / f"fail_{ss_filename}"), full_page=False)
                except Exception:
                    pass

            duration_ms = round((time.time() - t0) * 1000, 1)
            record = {
                "step": step_num,
                "title": title,
                "category": category,
                "action": action_desc,
                "screenshot": ss_filename,
                "status": status,
                "duration_ms": duration_ms,
                "verification": verification,
                "error": err
            }
            step_records.append(record)
            await page.wait_for_timeout(250)
            return record

        # Step 1: Baseline Overview
        async def step_1():
            hud_nodes = await page.locator("#hud-node-count").text_content()
            hud_synd = await page.locator("#hud-synd-count").text_content()
            fps = await page.locator("#fps-counter").text_content()
            feed_count = await page.locator("#feed-count").text_content()
            return {"hud_nodes": hud_nodes, "hud_synd": hud_synd, "fps": fps, "feed_count": feed_count}
        await execute_step(1, "Baseline Station Overview", "INIT", "Verify WebGL 3D constellation, HUD telemetry, and intelligence radar deck", "step_01_baseline_overview.png", step_1)

        # Step 2: GMGN Health Chip
        async def step_2():
            await page.locator("#chip-gmgn").click(timeout=3000)
            title = await page.locator("#explain-title").text_content()
            cat = await page.locator("#explain-category").text_content()
            tel = await page.locator("#explain-telemetry").text_content()
            return {"category": cat, "title": title, "telemetry": tel}
        await execute_step(2, "GMGN Provider Health Inspection", "INFRASTRUCTURE", "Click GMGN health chip to view circuit breaker state and telemetry", "step_02_chip_gmgn_inspect.png", step_2)

        # Step 3: Solscan Health Chip
        async def step_3():
            await page.locator("#chip-solscan").click(timeout=3000)
            title = await page.locator("#explain-title").text_content()
            tel = await page.locator("#explain-telemetry").text_content()
            return {"title": title, "telemetry": tel}
        await execute_step(3, "Solscan Breaker Health Inspection", "INFRASTRUCTURE", "Click Solscan chip to inspect canary recovery and circuit breaker", "step_03_chip_solscan_inspect.png", step_3)

        # Step 4: RPC Health Chip
        async def step_4():
            await page.locator("#chip-rpc").click(timeout=3000)
            title = await page.locator("#explain-title").text_content()
            tel = await page.locator("#explain-telemetry").text_content()
            return {"title": title, "telemetry": tel}
        await execute_step(4, "Solana Direct RPC Inspection", "INFRASTRUCTURE", "Click Solana RPC chip to inspect validator direct fallback status", "step_04_chip_rpc_inspect.png", step_4)

        # Step 5: Cache Health Chip
        async def step_5():
            await page.locator("#chip-cache").click(timeout=3000)
            title = await page.locator("#explain-title").text_content()
            tel = await page.locator("#explain-telemetry").text_content()
            cache_val = await page.locator("#cache-hit-val").text_content()
            return {"title": title, "telemetry": tel, "cache_hit_val": cache_val}
        await execute_step(5, "Cache & WAL Telemetry Inspection", "INFRASTRUCTURE", "Click Cache chip to verify SQLite WAL hit rate and LRU metrics", "step_05_chip_cache_inspect.png", step_5)

        # Step 6: Dismiss Plaque (UI Clearing)
        async def step_6():
            close_btn = page.locator("#curatorial-plaque .plaque-close-btn:visible")
            if await close_btn.count() > 0:
                await close_btn.first.click()
            disp = await page.locator("#curatorial-plaque").evaluate("el => el.style.display")
            return {"plaque_display": disp}
        await execute_step(6, "Dismiss Flyout Plaque", "VIEWPORT", "Close explanatory plaque to restore unobstructed 3D constellation view", "step_06_plaque_dismissed.png", step_6)

        # Step 7: Pitch/Yaw Telemetry Row
        async def step_7():
            row = page.locator("#hud-angles").locator("xpath=..")
            await row.click(timeout=3000)
            title = await page.locator("#explain-title").text_content()
            tel = await page.locator("#explain-telemetry").text_content()
            return {"title": title, "telemetry": tel}
        await execute_step(7, "Pitch/Yaw Gimbal Telemetry", "TELEMETRY", "Click Pitch/Yaw telemetry row to inspect spherical coordinates explanation", "step_07_telemetry_angles.png", step_7)

        # Step 8: Distance Telemetry Row
        async def step_8():
            row = page.locator("#hud-dist").locator("xpath=..")
            await row.click(timeout=3000)
            title = await page.locator("#explain-title").text_content()
            tel = await page.locator("#explain-telemetry").text_content()
            return {"title": title, "telemetry": tel}
        await execute_step(8, "Distance Telemetry Row", "TELEMETRY", "Click Distance row to verify camera focal Euclidean distance explanation", "step_08_telemetry_dist.png", step_8)

        # Step 9: Active Nodes Telemetry Row
        async def step_9():
            row = page.locator("#hud-node-count").locator("xpath=..")
            await row.click(timeout=3000)
            title = await page.locator("#explain-title").text_content()
            tel = await page.locator("#explain-telemetry").text_content()
            return {"title": title, "telemetry": tel}
        await execute_step(9, "Connectome Nodes Telemetry", "TELEMETRY", "Click Nodes row to inspect network connectome entity taxonomy", "step_09_telemetry_nodes.png", step_9)

        # Step 10: Syndicates Count Telemetry Row
        async def step_10():
            row = page.locator("#hud-synd-count").locator("xpath=..")
            await row.click(timeout=3000)
            title = await page.locator("#explain-title").text_content()
            tel = await page.locator("#explain-telemetry").text_content()
            return {"title": title, "telemetry": tel}
        await execute_step(10, "Syndicates Count Telemetry", "TELEMETRY", "Click Syndicates row to inspect cluster identity classification", "step_10_telemetry_syndicates.png", step_10)

        # Step 11: Tag Filter [#FlashMode]
        async def step_11():
            chip = page.locator(".tag-chip[data-filter='flash']")
            await chip.click(timeout=3000)
            selected = await chip.evaluate("el => el.classList.contains('selected')")
            cards_visible = await page.locator(".alert-card:visible").count()
            return {"flash_selected": selected, "cards_visible": cards_visible}
        await execute_step(11, "Filter: #FlashMode Activation", "FILTERS", "Filter 3D connectome and alerts to ultra-fast flash attacks (<60s)", "step_11_filter_flashmode.png", step_11)

        # Step 12: Tag Filter [#Sustained]
        async def step_12():
            chip = page.locator(".tag-chip[data-filter='sustained']")
            await chip.click(timeout=3000)
            selected = await chip.evaluate("el => el.classList.contains('selected')")
            cards_visible = await page.locator(".alert-card:visible").count()
            return {"sustained_selected": selected, "cards_visible": cards_visible}
        await execute_step(12, "Filter: #Sustained Activation", "FILTERS", "Filter 3D connectome and alerts to sustained multi-stage manipulation", "step_12_filter_sustained.png", step_12)

        # Step 13: Tag Filter [#Bundler>40%]
        async def step_13():
            chip = page.locator(".tag-chip[data-filter='bundler']")
            await chip.click(timeout=3000)
            selected = await chip.evaluate("el => el.classList.contains('selected')")
            cards_visible = await page.locator(".alert-card:visible").count()
            return {"bundler_selected": selected, "cards_visible": cards_visible}
        await execute_step(13, "Filter: #Bundler>40% Activation", "FILTERS", "Filter 3D connectome to atomic Jito bundle concentrations (>40%)", "step_13_filter_bundler.png", step_13)

        # Step 14: Tag Filter [ALL] Reset
        async def step_14():
            chip = page.locator(".tag-chip[data-filter='all']")
            await chip.click(timeout=3000)
            selected = await chip.evaluate("el => el.classList.contains('selected')")
            cards_visible = await page.locator(".alert-card:visible").count()
            return {"all_selected": selected, "cards_visible": cards_visible}
        await execute_step(14, "Filter Reset: ALL Entities", "FILTERS", "Reset behavioral filters to reveal 100% of discovered entities", "step_14_filter_all_reset.png", step_14)

        # Step 15: Radar KPI Card: Active Syndicates
        async def step_15():
            await page.locator("#kpi-syndicates").locator("xpath=..").click(timeout=3000)
            title = await page.locator("#explain-title").text_content()
            tel = await page.locator("#explain-telemetry").text_content()
            return {"title": title, "telemetry": tel}
        await execute_step(15, "KPI Card: Active Syndicates", "RADAR", "Inspect Active Syndicates KPI scoring logic and telemetry", "step_15_kpi_syndicates.png", step_15)

        # Step 16: Radar KPI Card: Est. Profit
        async def step_16():
            await page.locator("#kpi-profit").locator("xpath=..").click(timeout=3000)
            title = await page.locator("#explain-title").text_content()
            tel = await page.locator("#explain-telemetry").text_content()
            return {"title": title, "telemetry": tel}
        await execute_step(16, "KPI Card: Estimated Extracted Profit", "RADAR", "Inspect Est Profit KPI formula and cumulative USD valuation", "step_16_kpi_profit.png", step_16)

        # Step 17: Radar Feed Alert Card Click (Open Dossier & Camera Glide)
        async def step_17():
            first_card = page.locator(".alert-card").first
            await first_card.click(timeout=3000)
            await page.wait_for_timeout(950)  # Wait for 800ms kinetic glide
            title = await page.locator("#dossier-title").text_content()
            mode = await page.locator("#dossier-mode").text_content()
            conf = await page.locator("#dossier-conf").text_content()
            delay = await page.locator("#dossier-delay").text_content()
            hold = await page.locator("#dossier-hold").text_content()
            funder = await page.locator("#dossier-funder").text_content()
            backlinks = await page.locator("#dossier-backlinks .backlink-pill").count()
            return {
                "title": title, "mode": mode, "conf": conf, "delay": delay,
                "hold": hold, "funder": funder, "backlinks_count": backlinks
            }
        await execute_step(17, "Open Syndicate Dossier via Alert Card", "DOSSIER", "Click alert card, trigger 800ms kinetic camera glide, and verify dossier fields", "step_17_alert_card_dossier.png", step_17)

        # Step 18: Synaptic Backlink Click (Glide to Funder/Wallet)
        async def step_18():
            backlinks = page.locator("#dossier-backlinks .backlink-pill")
            count = await backlinks.count()
            clicked_text = ""
            if count > 0:
                clicked_text = await backlinks.first.text_content()
                await backlinks.first.click(timeout=3000)
                await page.wait_for_timeout(950)  # Wait for 800ms glide + pulse
            new_title = await page.locator("#dossier-title").text_content()
            new_subtitle = await page.locator("#dossier-subtitle").text_content()
            return {"clicked_backlink": clicked_text, "new_title": new_title, "new_subtitle": new_subtitle}
        await execute_step(18, "Synaptic Backlink Traversal", "DOSSIER", "Click backlink pill to execute camera glide and trigger neuron pulse", "step_18_synaptic_backlink_glide.png", step_18)

        # Step 19: Copy Wallet / Entity Address
        async def step_19():
            btn = page.locator("#copy-address-btn")
            await btn.click(timeout=3000)
            toast_text = await page.locator("#copy-toast").text_content()
            toast_show = await page.locator("#copy-toast").evaluate("el => el.classList.contains('show')")
            return {"toast_text": toast_text, "toast_show": toast_show}
        await execute_step(19, "Copy Wallet Action Button", "INTERACTION", "Click COPY WALLET button and verify clipboard notification toast", "step_19_copy_wallet_toast.png", step_19)

        # Step 20: Export Markdown Dossier Button
        async def step_20():
            async with page.expect_download() as download_info:
                await page.locator("#export-md-btn").click(timeout=3000)
            download = await download_info.value
            dl_path = download.suggested_filename
            return {"suggested_filename": dl_path}
        await execute_step(20, "Export Intelligence Markdown (.MD)", "EXPORT", "Click EXPORT (.MD) to generate and trigger forensic dossier download", "step_20_export_markdown.png", step_20)

        # Step 21: Dismiss Dossier Plaque
        async def step_21():
            close_btn = page.locator("#curatorial-plaque .plaque-close-btn:visible")
            if await close_btn.count() > 0:
                await close_btn.first.click()
            disp = await page.locator("#curatorial-plaque").evaluate("el => el.style.display")
            return {"plaque_display": disp}
        await execute_step(21, "Dismiss Dossier Plaque", "VIEWPORT", "Close dossier plaque to inspect full 3D constellation layout", "step_21_dossier_dismissed.png", step_21)

        # Step 22: Timeline Pill [MINT (T+0s)]
        async def step_22():
            await page.locator("#pill-mint").click(timeout=3000)
            disp = await page.locator("#timeline-time-display").text_content()
            val = await page.locator("#timeline-slider").input_value()
            title = await page.locator("#explain-title").text_content()
            return {"time_disp": disp, "slider_val": val, "explain_title": title}
        await execute_step(22, "Timeline Jump: MINT (T+0s)", "TIMELINE", "Jump 4D timeline to contract deployment at T+0s", "step_22_timeline_mint_t0.png", step_22)

        # Step 23: Timeline Pill [SNIPERS (T+13s)]
        async def step_23():
            await page.locator("#pill-snipe").click(timeout=3000)
            disp = await page.locator("#timeline-time-display").text_content()
            val = await page.locator("#timeline-slider").input_value()
            title = await page.locator("#explain-title").text_content()
            return {"time_disp": disp, "slider_val": val, "explain_title": title}
        await execute_step(23, "Timeline Jump: SNIPERS (T+13s)", "TIMELINE", "Jump 4D timeline to sniper ingress block at T+13s", "step_23_timeline_snipers_t13.png", step_23)

        # Step 24: Timeline Pill [BUNDLE (T+16s)]
        async def step_24():
            await page.locator("#pill-bundle").click(timeout=3000)
            disp = await page.locator("#timeline-time-display").text_content()
            val = await page.locator("#timeline-slider").input_value()
            title = await page.locator("#explain-title").text_content()
            return {"time_disp": disp, "slider_val": val, "explain_title": title}
        await execute_step(24, "Timeline Jump: BUNDLE (T+16s)", "TIMELINE", "Jump 4D timeline to MEV atomic bundle confirmation at T+16s", "step_24_timeline_bundle_t16.png", step_24)

        # Step 25: Timeline Pill [DUMP (T+35s)]
        async def step_25():
            await page.locator("#pill-dump").click(timeout=3000)
            disp = await page.locator("#timeline-time-display").text_content()
            val = await page.locator("#timeline-slider").input_value()
            title = await page.locator("#explain-title").text_content()
            return {"time_disp": disp, "slider_val": val, "explain_title": title}
        await execute_step(25, "Timeline Jump: DUMP (T+35s)", "TIMELINE", "Jump 4D timeline to coordinated liquidation at T+35s", "step_25_timeline_dump_t35.png", step_25)

        # Step 26: Timeline Range Slider Manual Scrub (T+50s)
        async def step_26():
            slider = page.locator("#timeline-slider")
            await slider.evaluate("el => { el.value = 50; el.dispatchEvent(new Event('input')); }")
            disp = await page.locator("#timeline-time-display").text_content()
            return {"scrubbed_time": disp}
        await execute_step(26, "Timeline Manual Scrubber", "TIMELINE", "Directly scrub timeline slider to T+50s and verify state updates", "step_26_timeline_slider_scrub.png", step_26)

        # Step 27: Timeline Play/Pause Transport
        async def step_27():
            btn = page.locator("#play-pause-btn")
            await btn.click(timeout=3000)
            await page.wait_for_timeout(1400)
            t_mid = await page.locator("#timeline-time-display").text_content()
            await btn.click(timeout=3000)
            btn_txt = await btn.text_content()
            return {"mid_play_time": t_mid, "btn_text_after_pause": btn_txt.strip()}
        await execute_step(27, "Timeline Playback Transport", "TIMELINE", "Start live 4D timeline chronological replay and pause", "step_27_timeline_play_pause.png", step_27)

        # Step 28: CL4R1T4S Phosphor Mode Toggle
        async def step_28():
            btn = page.locator("#clarity-btn")
            await btn.click(timeout=3000)
            is_active = await btn.evaluate("el => el.classList.contains('active')")
            crt_opacity = await page.locator("#crt-overlay").evaluate("el => window.getComputedStyle(el).opacity")
            return {"clarity_active": is_active, "crt_opacity": crt_opacity}
        await execute_step(28, "CL4R1T4S CRT Phosphor Mode", "THEME", "Toggle high-contrast CRT phosphor scanline filter mode", "step_28_cl4r1t4s_mode_on.png", step_28)

        # Step 29: Reset View Camera Angle
        async def step_29():
            btn = page.locator("#reset-cam-btn")
            await btn.click(timeout=3000)
            await page.wait_for_timeout(400)
            angles = await page.locator("#hud-angles").text_content()
            dist = await page.locator("#hud-dist").text_content()
            return {"angles": angles, "dist": dist}
        await execute_step(29, "Camera Reset View Action", "SPATIAL", "Restore default canonical camera viewpoint (0, 160, 380)", "step_29_camera_reset_view.png", step_29)

        # Step 30: Live Scan Polling Toggle
        async def step_30():
            btn = page.locator("#poll-toggle-btn")
            await btn.click(timeout=3000)
            status_paused = await btn.text_content()
            await page.wait_for_timeout(300)
            await btn.click(timeout=3000)
            status_resumed = await btn.text_content()
            return {"status_paused": status_paused.strip(), "status_resumed": status_resumed.strip()}
        await execute_step(30, "Live Polling Stream Toggle", "STREAMING", "Toggle live telemetry scanner background polling loop", "step_30_live_scan_toggle.png", step_30)

        # Step 31: Command Deck Collapse
        async def step_31():
            btn = page.locator("#deck-toggle-btn")
            await btn.click(timeout=3000)
            collapsed = await page.locator("#command-deck").evaluate("el => el.classList.contains('collapsed')")
            return {"deck_collapsed": collapsed}
        await execute_step(31, "Command Deck Collapse", "LAYOUT", "Collapse right intelligence radar deck to expand 3D canvas", "step_31_command_deck_collapsed.png", step_31)

        # Step 32: Command Deck Re-Expand
        async def step_32():
            btn = page.locator("#deck-toggle-btn")
            await btn.click(timeout=3000)
            collapsed = await page.locator("#command-deck").evaluate("el => el.classList.contains('collapsed')")
            return {"deck_collapsed": collapsed}
        await execute_step(32, "Command Deck Re-Expand", "LAYOUT", "Re-expand intelligence radar deck and restore dual-panel station layout", "step_32_command_deck_restored.png", step_32)

        # Step 33: Power User Keyboard Shortcut Test: Spacebar (Play/Pause)
        async def step_33():
            t_before = await page.locator("#timeline-time-display").text_content()
            await page.keyboard.press("Space")
            await page.wait_for_timeout(600)
            t_after = await page.locator("#timeline-time-display").text_content()
            btn_txt = await page.locator("#play-pause-btn").text_content()
            # Press Space again to see if it toggles
            await page.keyboard.press("Space")
            return {
                "spacebar_tested": True,
                "time_before": t_before,
                "time_after": t_after,
                "btn_text": btn_txt.strip(),
                "shortcut_handled": t_before != t_after
            }
        await execute_step(33, "Power-User Test: Spacebar Play/Pause", "KEYBOARD_SHORTCUTS", "Press Spacebar to test native keyboard playback transport", "step_33_poweruser_spacebar.png", step_33)

        # Step 34: Power User Keyboard Shortcut Test: Escape Key (Dismiss Modal/Plaque)
        async def step_34():
            # Open plaque first
            await page.locator("#chip-cache").click(timeout=3000)
            disp_before = await page.locator("#curatorial-plaque").evaluate("el => el.style.display")
            await page.keyboard.press("Escape")
            await page.wait_for_timeout(300)
            disp_after = await page.locator("#curatorial-plaque").evaluate("el => el.style.display")
            return {
                "escape_tested": True,
                "plaque_before": disp_before,
                "plaque_after": disp_after,
                "dismissed_by_escape": disp_after == "none"
            }
        await execute_step(34, "Power-User Test: Escape Key Dismiss", "KEYBOARD_SHORTCUTS", "Press Escape key to test modal/plaque dismissal shortcut", "step_34_poweruser_escape_key.png", step_34)

        # Step 35: Power User Keyboard Shortcut Test: Number Keys 1-4 for Stage Jump
        async def step_35():
            await page.keyboard.press("Digit2")
            await page.wait_for_timeout(300)
            val_after_2 = await page.locator("#timeline-slider").input_value()
            await page.keyboard.press("Digit3")
            await page.wait_for_timeout(300)
            val_after_3 = await page.locator("#timeline-slider").input_value()
            return {
                "number_keys_tested": True,
                "val_after_digit2": val_after_2,
                "val_after_digit3": val_after_3,
                "number_keys_handled": val_after_2 == "13" or val_after_3 == "16"
            }
        await execute_step(35, "Power-User Test: Number Keys (1-4)", "KEYBOARD_SHORTCUTS", "Press digits 1-4 to test rapid timeline phase navigation", "step_35_poweruser_number_keys.png", step_35)

        # Step 36: Power User Interaction Test: 3D Canvas Orbit Drag & Node Inspection
        async def step_36():
            canvas_box = await page.locator("#webgl-canvas").bounding_box()
            if canvas_box:
                cx = canvas_box["x"] + canvas_box["width"] * 0.4
                cy = canvas_box["y"] + canvas_box["height"] * 0.5
                await page.mouse.move(cx, cy)
                await page.mouse.down()
                await page.mouse.move(cx + 120, cy - 80, steps=10)
                await page.mouse.up()
                await page.wait_for_timeout(500)
            angles = await page.locator("#hud-angles").text_content()
            dist = await page.locator("#hud-dist").text_content()
            return {"orbit_dragged": True, "new_angles": angles, "new_dist": dist}
        await execute_step(36, "Power-User Test: 3D Canvas Orbit Drag", "CANVAS_INTERACTION", "Drag WebGL canvas with mouse to test OrbitControls responsiveness and telemetry updates", "step_36_poweruser_orbit_drag.png", step_36)

        await browser.close()

    total_steps = len(step_records)
    passed_steps = sum(1 for s in step_records if s["status"] == "PASS")
    failed_steps = sum(1 for s in step_records if s["status"] == "FAIL")

    telemetry_output = {
        "url": TARGET_URL,
        "total_steps": total_steps,
        "passed": passed_steps,
        "failed": failed_steps,
        "console_errors_count": len(console_errors),
        "page_errors_count": len(page_errors),
        "console_errors": console_errors,
        "page_errors": page_errors,
        "steps": step_records
    }

    REPORT_DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    REPORT_DATA_FILE.write_text(json.dumps(telemetry_output, indent=2), encoding="utf-8")
    logger.info("UX Audit complete: %d steps executed (%d passed, %d failed). Telemetry saved.", total_steps, passed_steps, failed_steps)
    return telemetry_output


if __name__ == "__main__":
    asyncio.run(main())

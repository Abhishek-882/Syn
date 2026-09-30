"""UX Audit Agent 2 - Autonomous Playwright Exploration Script.

Persona: Syndicate Hunter Power User
Target: http://localhost:8000/web/syndicate_3d_visualizer.html
Output Screenshots: results/ux_audit/agent_2_screenshots/
Output Report Data: results/ux_audit/agent_2_step_log.json
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
logger = logging.getLogger("ux_agent_2")


async def run_audit():
    base_dir = Path(r"c:\Users\Asus\Documents\antigravity\hopeful-curie")
    ss_dir = base_dir / "results" / "ux_audit" / "agent_2_screenshots"
    ss_dir.mkdir(parents=True, exist_ok=True)
    log_file = base_dir / "results" / "ux_audit" / "agent_2_step_log.json"

    url = "http://localhost:8000/web/syndicate_3d_visualizer.html"

    console_logs: List[Dict[str, str]] = []
    page_errors: List[str] = []
    step_results: List[Dict[str, Any]] = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Power user wide viewport
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            permissions=["clipboard-read", "clipboard-write"],
            accept_downloads=True
        )
        page = await context.new_page()

        page.on("console", lambda msg: console_logs.append({"type": msg.type, "text": msg.text}))
        page.on("pageerror", lambda err: page_errors.append(str(err)))

        logger.info("Navigating to %s", url)
        t_nav_start = time.time()
        await page.goto(url, wait_until="networkidle", timeout=15000)
        nav_duration_ms = round((time.time() - t_nav_start) * 1000, 1)
        await page.wait_for_timeout(1500)

        async def record_step(step_num: int, name: str, action_desc: str, ss_filename: str, check_fn=None):
            logger.info("Step %02d: %s", step_num, name)
            t0 = time.time()
            error = None
            status = "PASS"
            details = {}
            try:
                if check_fn:
                    res = await check_fn()
                    if isinstance(res, dict):
                        details = res
                    else:
                        details = {"info": str(res)}
                await page.wait_for_timeout(200)
                ss_path = ss_dir / ss_filename
                await page.screenshot(path=str(ss_path), full_page=False)
            except Exception as e:
                status = "FAIL"
                error = str(e)
                logger.error("Step %02d FAILED: %s", step_num, error)

            duration_ms = round((time.time() - t0) * 1000, 1)
            record = {
                "step": step_num,
                "name": name,
                "action": action_desc,
                "screenshot": ss_filename,
                "status": status,
                "duration_ms": duration_ms,
                "details": details,
                "error": error
            }
            step_results.append(record)
            await page.wait_for_timeout(250)
            return status == "PASS"

        # Step 1: Initial Baseline Load
        async def step_1():
            nodes = await page.locator("#hud-node-count").text_content()
            synds = await page.locator("#hud-synd-count").text_content()
            feed_cnt = await page.locator("#feed-count").text_content()
            profit = await page.locator("#kpi-profit").text_content()
            fps = await page.locator("#fps-counter").text_content()
            return {
                "nav_duration_ms": nav_duration_ms,
                "nodes": nodes,
                "syndicates": synds,
                "feed": feed_cnt,
                "profit": profit,
                "fps": fps
            }
        await record_step(1, "Baseline Station Overview", "Initial load, 1080p full dashboard baseline overview", "01_baseline_overview.png", step_1)

        # Step 2: GMGN Health Chip
        async def step_2():
            await page.locator("#chip-gmgn").click(timeout=3000)
            title = await page.locator("#explain-title").text_content()
            telemetry = await page.locator("#explain-telemetry").text_content()
            return {"title": title, "telemetry": telemetry}
        await record_step(2, "GMGN Provider Health Chip", "Click GMGN health chip to view breaker status & telemetry", "02_chip_gmgn_explain.png", step_2)

        # Step 3: Solscan Health Chip
        async def step_3():
            await page.locator("#chip-solscan").click(timeout=3000)
            title = await page.locator("#explain-title").text_content()
            telemetry = await page.locator("#explain-telemetry").text_content()
            return {"title": title, "telemetry": telemetry}
        await record_step(3, "Solscan Provider Health Chip", "Click Solscan chip to view circuit breaker canary status", "03_chip_solscan_explain.png", step_3)

        # Step 4: RPC Health Chip
        async def step_4():
            await page.locator("#chip-rpc").click(timeout=3000)
            title = await page.locator("#explain-title").text_content()
            telemetry = await page.locator("#explain-telemetry").text_content()
            return {"title": title, "telemetry": telemetry}
        await record_step(4, "RPC Provider Health Chip", "Click RPC chip to view validator direct connection status", "04_chip_rpc_explain.png", step_4)

        # Step 5: Cache Health Chip
        async def step_5():
            await page.locator("#chip-cache").click(timeout=3000)
            title = await page.locator("#explain-title").text_content()
            telemetry = await page.locator("#explain-telemetry").text_content()
            hit_val = await page.locator("#cache-hit-val").text_content()
            return {"title": title, "telemetry": telemetry, "hit_val": hit_val}
        await record_step(5, "Cache Health Chip & WAL Stats", "Click Cache chip to verify SQLite WAL hit rate and total queries", "05_chip_cache_explain.png", step_5)

        # Step 6: Dismiss Explainer Plaque
        async def step_6():
            close_btn = page.locator("#curatorial-plaque .plaque-close-btn:visible").first
            await close_btn.click(timeout=3000)
            hidden = await page.locator("#curatorial-plaque").evaluate("el => el.style.display === 'none'")
            return {"hidden": hidden}
        await record_step(6, "Dismiss Explainer Plaque", "Close explanation plaque via header cross button", "06_plaque_dismissed.png", step_6)

        # Step 7: Telemetry HUD: Pitch / Yaw
        async def step_7():
            await page.locator("#hud-angles").locator("xpath=..").click(timeout=3000)
            title = await page.locator("#explain-title").text_content()
            angles = await page.locator("#hud-angles").text_content()
            return {"title": title, "angles": angles}
        await record_step(7, "HUD Pitch/Yaw Telemetry", "Click Pitch/Yaw telemetry metric for coordinate explainer", "07_hud_angles_explain.png", step_7)

        # Step 8: Telemetry HUD: Distance
        async def step_8():
            await page.locator("#hud-dist").locator("xpath=..").click(timeout=3000)
            title = await page.locator("#explain-title").text_content()
            dist = await page.locator("#hud-dist").text_content()
            return {"title": title, "distance": dist}
        await record_step(8, "HUD Distance Telemetry", "Click camera distance telemetry metric for distance explainer", "08_hud_distance_explain.png", step_8)

        # Step 9: Telemetry HUD: Nodes
        async def step_9():
            await page.locator("#hud-node-count").locator("xpath=..").click(timeout=3000)
            title = await page.locator("#explain-title").text_content()
            nodes = await page.locator("#hud-node-count").text_content()
            return {"title": title, "nodes": nodes}
        await record_step(9, "HUD Nodes Count Telemetry", "Click active nodes telemetry metric for entity classification", "09_hud_nodes_explain.png", step_9)

        # Step 10: Telemetry HUD: Syndicates
        async def step_10():
            await page.locator("#hud-synd-count").locator("xpath=..").click(timeout=3000)
            title = await page.locator("#explain-title").text_content()
            synds = await page.locator("#hud-synd-count").text_content()
            return {"title": title, "syndicates": synds}
        await record_step(10, "HUD Syndicates Count Telemetry", "Click syndicates count metric for cluster classification", "10_hud_syndicates_explain.png", step_10)

        # Step 11: Tag Filter: #FlashMode
        async def step_11():
            chip = page.locator(".tag-chip[data-filter='flash']")
            await chip.click(timeout=3000)
            selected = await chip.evaluate("el => el.classList.contains('selected')")
            visible_cards = await page.locator(".alert-card:visible").count()
            return {"selected": selected, "visible_cards": visible_cards}
        await record_step(11, "Tag Filter: #FlashMode", "Activate #FlashMode filter to isolate sub-60s attacks", "11_tag_flash_filter.png", step_11)

        # Step 12: Tag Filter: #Sustained
        async def step_12():
            chip = page.locator(".tag-chip[data-filter='sustained']")
            await chip.click(timeout=3000)
            selected = await chip.evaluate("el => el.classList.contains('selected')")
            visible_cards = await page.locator(".alert-card:visible").count()
            return {"selected": selected, "visible_cards": visible_cards}
        await record_step(12, "Tag Filter: #Sustained", "Activate #Sustained filter for long-term multi-wallet wash rings", "12_tag_sustained_filter.png", step_12)

        # Step 13: Tag Filter: #Bundler>40%
        async def step_13():
            chip = page.locator(".tag-chip[data-filter='bundler']")
            await chip.click(timeout=3000)
            selected = await chip.evaluate("el => el.classList.contains('selected')")
            visible_cards = await page.locator(".alert-card:visible").count()
            return {"selected": selected, "visible_cards": visible_cards}
        await record_step(13, "Tag Filter: #Bundler>40%", "Activate #Bundler>40% filter for heavy MEV bundled launches", "13_tag_bundler_filter.png", step_13)

        # Step 14: Tag Filter: ALL Reset
        async def step_14():
            chip = page.locator(".tag-chip[data-filter='all']")
            await chip.click(timeout=3000)
            selected = await chip.evaluate("el => el.classList.contains('selected')")
            visible_cards = await page.locator(".alert-card:visible").count()
            return {"selected": selected, "visible_cards": visible_cards}
        await record_step(14, "Tag Filter: ALL Reset", "Reset filter to restore full 100% connectome visibility", "14_tag_all_reset.png", step_14)

        # Step 15: Radar KPI: Active Syndicates
        async def step_15():
            await page.locator("#kpi-syndicates").locator("xpath=..").click(timeout=3000)
            title = await page.locator("#explain-title").text_content()
            return {"title": title}
        await record_step(15, "Radar KPI: Active Syndicates", "Inspect scoring criteria for verified active syndicates", "15_kpi_syndicates_explain.png", step_15)

        # Step 16: Radar KPI: Est. Profit
        async def step_16():
            await page.locator("#kpi-profit").locator("xpath=..").click(timeout=3000)
            title = await page.locator("#explain-title").text_content()
            return {"title": title}
        await record_step(16, "Radar KPI: Est. Profit", "Inspect extracted capital computation and reference pricing", "16_kpi_profit_explain.png", step_16)

        # Step 17: Click First Radar Alert Card (SYND-0001)
        async def step_17():
            first_card = page.locator(".alert-card").first
            await first_card.click(timeout=3000)
            await page.wait_for_timeout(900)  # Wait for 800ms kinetic camera glide
            title = await page.locator("#dossier-title").text_content()
            mode = await page.locator("#dossier-mode").text_content()
            conf = await page.locator("#dossier-conf").text_content()
            funder = await page.locator("#dossier-funder").text_content()
            return {"title": title, "mode": mode, "confidence": conf, "funder": funder}
        await record_step(17, "Radar Alert Card: Open Dossier & Glide", "Click SYND-0001 alert card to trigger kinetic glide and populate dossier", "17_alert_card_dossier.png", step_17)

        # Step 18: Dossier Panel Metrics Verification
        async def step_18():
            delay = await page.locator("#dossier-delay").text_content()
            hold = await page.locator("#dossier-hold").text_content()
            backlinks = await page.locator("#dossier-backlinks .backlink-pill").count()
            return {"buy_delay": delay, "hold_time": hold, "backlink_count": backlinks}
        await record_step(18, "Dossier Panel Metrics Inspection", "Inspect buy delay, hold time, and linked entity backlinks", "18_dossier_metrics_inspection.png", step_18)

        # Step 19: Synaptic Backlink Pill 1 (Glide to Wallet & Pulse)
        async def step_19():
            backlinks = page.locator("#dossier-backlinks .backlink-pill")
            count = await backlinks.count()
            if count > 0:
                first_pill = backlinks.first
                txt = await first_pill.text_content()
                await first_pill.click(timeout=3000)
                await page.wait_for_timeout(900)  # Wait for glide + pulse
                title = await page.locator("#dossier-title").text_content()
                subtitle = await page.locator("#dossier-subtitle").text_content()
                return {"clicked_pill": txt, "new_title": title, "new_subtitle": subtitle}
            return {"warning": "No backlinks found"}
        await record_step(19, "Synaptic Backlink Glide: Wallet", "Click first backlink pill to orbit camera and pulse individual wallet neuron", "19_synaptic_backlink_wallet.png", step_19)

        # Step 20: Synaptic Backlink Pill 2 (Glide to Syndicate / Funder)
        async def step_20():
            backlinks = page.locator("#dossier-backlinks .backlink-pill")
            count = await backlinks.count()
            if count > 0:
                # Look for a syndicate or funder pill
                chosen = None
                for i in range(count):
                    pill = backlinks.nth(i)
                    t = await pill.text_content()
                    if "Syndicate" in t or "Funder" in t:
                        chosen = pill
                        break
                if not chosen:
                    chosen = backlinks.first
                txt = await chosen.text_content()
                await chosen.click(timeout=3000)
                await page.wait_for_timeout(900)
                title = await page.locator("#dossier-title").text_content()
                return {"clicked_pill": txt, "title": title}
            return {"warning": "No secondary backlinks found"}
        await record_step(20, "Synaptic Backlink Glide: Cluster/Funder", "Click secondary backlink pill to traverse network relationship", "20_synaptic_backlink_cluster.png", step_20)

        # Step 21: Action: Copy Wallet Address
        async def step_21():
            copy_btn = page.locator("#copy-address-btn")
            await copy_btn.click(timeout=3000)
            toast = page.locator("#copy-toast")
            is_visible = await toast.evaluate("el => el.classList.contains('show')")
            toast_text = await toast.text_content()
            return {"toast_shown": is_visible, "toast_text": toast_text}
        await record_step(21, "Copy Wallet Action & Toast", "Click COPY WALLET button and confirm toast notification triggers", "21_copy_wallet_toast.png", step_21)

        # Step 22: Action: Export Markdown Dossier
        async def step_22():
            export_btn = page.locator("#export-md-btn")
            # Listen for download
            async with page.expect_download(timeout=4000) as download_info:
                await export_btn.click(timeout=3000)
            download = await download_info.value
            download_path = download.suggested_filename
            return {"suggested_filename": download_path}
        await record_step(22, "Export Markdown Intelligence Dossier", "Click EXPORT (.MD) to generate downloadable forensic investigation markdown", "22_export_markdown_dossier.png", step_22)

        # Step 23: Dismiss Dossier Plaque
        async def step_23():
            close_btn = page.locator("#curatorial-plaque .plaque-close-btn:visible").first
            await close_btn.click(timeout=3000)
            hidden = await page.locator("#curatorial-plaque").evaluate("el => el.style.display === 'none'")
            return {"hidden": hidden}
        await record_step(23, "Dismiss Dossier Plaque", "Dismiss dossier plaque to reveal unobstructed 3D connectome", "23_dossier_dismissed.png", step_23)

        # Step 24: 4D Timeline: Stage Pill MINT (T+0s)
        async def step_24():
            await page.locator("#pill-mint").click(timeout=3000)
            time_disp = await page.locator("#timeline-time-display").text_content()
            slider_val = await page.locator("#timeline-slider").input_value()
            title = await page.locator("#explain-title").text_content()
            return {"time": time_disp, "slider": slider_val, "explain": title}
        await record_step(24, "Timeline Stage: MINT (T+0s)", "Jump 4D timeline to T+0s deployment block and open explainer", "24_timeline_mint_t0.png", step_24)

        # Step 25: 4D Timeline: Stage Pill SNIPERS (T+13s)
        async def step_25():
            await page.locator("#pill-snipe").click(timeout=3000)
            time_disp = await page.locator("#timeline-time-display").text_content()
            slider_val = await page.locator("#timeline-slider").input_value()
            title = await page.locator("#explain-title").text_content()
            return {"time": time_disp, "slider": slider_val, "explain": title}
        await record_step(25, "Timeline Stage: SNIPERS (T+13s)", "Jump timeline to T+13s sniper ingress block and verify node emission glow", "25_timeline_snipers_t13.png", step_25)

        # Step 26: 4D Timeline: Stage Pill BUNDLE (T+16s)
        async def step_26():
            await page.locator("#pill-bundle").click(timeout=3000)
            time_disp = await page.locator("#timeline-time-display").text_content()
            slider_val = await page.locator("#timeline-slider").input_value()
            title = await page.locator("#explain-title").text_content()
            return {"time": time_disp, "slider": slider_val, "explain": title}
        await record_step(26, "Timeline Stage: BUNDLE (T+16s)", "Jump timeline to T+16s atomic Jito MEV bundle confirmation block", "26_timeline_bundle_t16.png", step_26)

        # Step 27: 4D Timeline: Stage Pill DUMP (T+35s)
        async def step_27():
            await page.locator("#pill-dump").click(timeout=3000)
            time_disp = await page.locator("#timeline-time-display").text_content()
            slider_val = await page.locator("#timeline-slider").input_value()
            title = await page.locator("#explain-title").text_content()
            return {"time": time_disp, "slider": slider_val, "explain": title}
        await record_step(27, "Timeline Stage: DUMP (T+35s)", "Jump timeline to T+35s coordinated liquidation dump block", "27_timeline_dump_t35.png", step_27)

        # Step 28: 4D Timeline: Manual Slider Scrub to T+24s
        async def step_28():
            slider = page.locator("#timeline-slider")
            await slider.evaluate("el => { el.value = 24; el.dispatchEvent(new Event('input')); }")
            time_disp = await page.locator("#timeline-time-display").text_content()
            return {"time_disp": time_disp}
        await record_step(28, "Timeline Slider Scrub: T+24s", "Directly scrub temporal slider to T+24s mid-pump phase", "28_timeline_scrub_t24.png", step_28)

        # Step 29: 4D Timeline: Manual Slider Scrub to T+48s
        async def step_29():
            slider = page.locator("#timeline-slider")
            await slider.evaluate("el => { el.value = 48; el.dispatchEvent(new Event('input')); }")
            time_disp = await page.locator("#timeline-time-display").text_content()
            return {"time_disp": time_disp}
        await record_step(29, "Timeline Slider Scrub: T+48s", "Directly scrub temporal slider to T+48s post-dump decay phase", "29_timeline_scrub_t48.png", step_29)

        # Step 30: 4D Timeline: Transport Playback Start
        async def step_30():
            play_btn = page.locator("#play-pause-btn")
            await play_btn.click(timeout=3000)
            await page.wait_for_timeout(1200)
            time_disp = await page.locator("#timeline-time-display").text_content()
            btn_txt = await play_btn.text_content()
            return {"time_disp": time_disp, "btn_text": btn_txt.strip()}
        await record_step(30, "Timeline Transport: Play Active", "Engage automated timeline simulation transport playback", "30_timeline_play_active.png", step_30)

        # Step 31: 4D Timeline: Transport Playback Pause
        async def step_31():
            play_btn = page.locator("#play-pause-btn")
            await play_btn.click(timeout=3000)
            time_disp = await page.locator("#timeline-time-display").text_content()
            btn_txt = await play_btn.text_content()
            return {"paused_time": time_disp, "btn_text": btn_txt.strip()}
        await record_step(31, "Timeline Transport: Paused", "Pause timeline simulation transport at current frame", "31_timeline_paused.png", step_31)

        # Step 32: Header Action: CL4R1T4S Phosphor Mode ON
        async def step_32():
            clarity_btn = page.locator("#clarity-btn")
            await clarity_btn.click(timeout=3000)
            opacity = await page.locator("#crt-overlay").evaluate("el => window.getComputedStyle(el).opacity")
            has_class = await page.evaluate("() => document.body.classList.contains('clarity-mode')")
            return {"crt_opacity": opacity, "has_clarity_class": has_class}
        await record_step(32, "CL4R1T4S Mode: Active", "Engage high-contrast phosphor CRT scanline filter mode", "32_cl4r1t4s_mode_on.png", step_32)

        # Step 33: Header Action: CL4R1T4S Phosphor Mode OFF
        async def step_33():
            clarity_btn = page.locator("#clarity-btn")
            await clarity_btn.click(timeout=3000)
            opacity = await page.locator("#crt-overlay").evaluate("el => window.getComputedStyle(el).opacity")
            has_class = await page.evaluate("() => document.body.classList.contains('clarity-mode')")
            return {"crt_opacity": opacity, "has_clarity_class": has_class}
        await record_step(33, "CL4R1T4S Mode: Deactivated", "Revert to standard clean WebGL viewport rendering", "33_cl4r1t4s_mode_off.png", step_33)

        # Step 34: Header Action: RESET VIEW Camera
        async def step_34():
            reset_btn = page.locator("#reset-cam-btn")
            await reset_btn.click(timeout=3000)
            await page.wait_for_timeout(350)
            dist = await page.locator("#hud-dist").text_content()
            angles = await page.locator("#hud-angles").text_content()
            return {"distance": dist, "angles": angles}
        await record_step(34, "Reset Camera View", "Click RESET VIEW to restore canonical orbit coordinates", "34_reset_view_restored.png", step_34)

        # Step 35: Header Action: LIVE SCAN Toggle (Pause)
        async def step_35():
            poll_btn = page.locator("#poll-toggle-btn")
            await poll_btn.click(timeout=3000)
            btn_txt = await poll_btn.text_content()
            is_active = await poll_btn.evaluate("el => el.classList.contains('active')")
            return {"button_text": btn_txt.strip(), "active": is_active}
        await record_step(35, "Live Scan: Paused", "Pause live polling to lock station state for freeze-frame analysis", "35_live_scan_paused.png", step_35)

        # Step 36: Header Action: LIVE SCAN Toggle (Resume)
        async def step_36():
            poll_btn = page.locator("#poll-toggle-btn")
            await poll_btn.click(timeout=3000)
            btn_txt = await poll_btn.text_content()
            is_active = await poll_btn.evaluate("el => el.classList.contains('active')")
            return {"button_text": btn_txt.strip(), "active": is_active}
        await record_step(36, "Live Scan: Resumed", "Resume real-time background daemon polling", "36_live_scan_resumed.png", step_36)

        # Step 37: Command Deck: Collapse Right Dock
        async def step_37():
            toggle_btn = page.locator("#deck-toggle-btn")
            await toggle_btn.click(timeout=3000)
            is_collapsed = await page.locator("#command-deck").evaluate("el => el.classList.contains('collapsed')")
            return {"collapsed": is_collapsed}
        await record_step(37, "Collapse Command Deck", "Collapse right dock to maximize 3D connectome canvas area", "37_command_deck_collapsed.png", step_37)

        # Step 38: 3D Canvas Orbit Drag Navigation
        async def step_38():
            # Drag canvas from center to rotate 3D view
            box = await page.locator("#webgl-canvas").bounding_box()
            cx, cy = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
            await page.mouse.move(cx, cy)
            await page.mouse.down()
            await page.mouse.move(cx + 180, cy - 70, steps=10)
            await page.mouse.up()
            await page.wait_for_timeout(400)
            angles = await page.locator("#hud-angles").text_content()
            return {"rotated_angles": angles}
        await record_step(38, "3D Canvas Orbit Drag", "Perform 3D mouse drag rotation to inspect spatial cluster layout", "38_canvas_orbit_drag.png", step_38)

        # Step 39: 3D Canvas Raycaster Hover Tooltip
        async def step_39():
            # Hover over a known node position (near center)
            box = await page.locator("#webgl-canvas").bounding_box()
            cx, cy = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
            # Slight offset to hit node mesh
            await page.mouse.move(cx + 40, cy + 20)
            await page.wait_for_timeout(300)
            tooltip_visible = await page.evaluate("() => { const t = document.querySelector('div[style*=\"position: absolute\"][style*=\"z-index: 100\"]'); return t ? t.style.display : 'none'; }")
            return {"tooltip_display": tooltip_visible}
        await record_step(39, "3D Canvas Raycaster Hover", "Hover mouse over canvas to verify Raycaster interaction & hover tooltip", "39_canvas_raycaster_hover.png", step_39)

        # Step 40: Command Deck: Re-Expand Right Dock
        async def step_40():
            toggle_btn = page.locator("#deck-toggle-btn")
            await toggle_btn.click(timeout=3000)
            is_collapsed = await page.locator("#command-deck").evaluate("el => el.classList.contains('collapsed')")
            return {"collapsed": is_collapsed}
        await record_step(40, "Re-Expand Command Deck", "Restore intelligence radar and detection feed dock", "40_command_deck_restored.png", step_40)

        # Step 41: Power-User Test: Spacebar Keyboard Shortcut for Play/Pause
        async def step_41():
            # Check if Spacebar toggles playback
            initial_state = await page.locator("#play-pause-btn").text_content()
            await page.keyboard.press("Space")
            await page.wait_for_timeout(400)
            after_state = await page.locator("#play-pause-btn").text_content()
            # If no change, document as missing shortcut!
            toggled = (initial_state.strip() != after_state.strip())
            return {
                "initial_btn": initial_state.strip(),
                "after_space_btn": after_state.strip(),
                "spacebar_supported": toggled
            }
        await record_step(41, "Power-User Shortcut: Spacebar", "Test Spacebar hotkey to toggle timeline playback", "41_shortcut_spacebar_test.png", step_41)

        # Step 42: Power-User Test: Escape Key to Dismiss Plaque
        async def step_42():
            # First open plaque
            await page.locator("#chip-gmgn").click(timeout=3000)
            is_open_before = await page.locator("#curatorial-plaque").evaluate("el => el.style.display !== 'none'")
            # Press Escape
            await page.keyboard.press("Escape")
            await page.wait_for_timeout(400)
            is_open_after = await page.locator("#curatorial-plaque").evaluate("el => el.style.display !== 'none'")
            dismissed = (is_open_before and not is_open_after)
            # If not dismissed, manually close for next steps
            if is_open_after:
                close_btn = page.locator("#curatorial-plaque .plaque-close-btn:visible").first
                await close_btn.click()
            return {
                "open_before": is_open_before,
                "open_after_escape": is_open_after,
                "escape_supported": dismissed
            }
        await record_step(42, "Power-User Shortcut: Escape Key", "Test Escape hotkey to dismiss open plaques and modals", "42_shortcut_escape_test.png", step_42)

        # Step 43: Power-User Test: Number Keys 1-4 for Timeline Stages
        async def step_43():
            initial_time = await page.locator("#timeline-time-display").text_content()
            await page.keyboard.press("2")
            await page.wait_for_timeout(400)
            time_after_2 = await page.locator("#timeline-time-display").text_content()
            key_supported = (initial_time != time_after_2)
            return {
                "initial_time": initial_time,
                "time_after_key_2": time_after_2,
                "number_keys_supported": key_supported
            }
        await record_step(43, "Power-User Shortcut: Number Keys 1-4", "Test Number keys 1-4 for instant jumping across timeline stages", "43_shortcut_numbers_test.png", step_43)

        await browser.close()

    total = len(step_results)
    passed = sum(1 for s in step_results if s["status"] == "PASS")
    failed = sum(1 for s in step_results if s["status"] == "FAIL")

    summary = {
        "url": url,
        "total_steps": total,
        "passed": passed,
        "failed": failed,
        "console_errors_count": len([c for c in console_logs if c["type"] == "error"]),
        "console_warnings_count": len([c for c in console_logs if c["type"] == "warning"]),
        "page_errors_count": len(page_errors),
        "console_logs": console_logs,
        "page_errors": page_errors,
        "steps": step_results
    }

    log_file.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    logger.info("Audit run finished: %d/%d passed (%d failed)", passed, total, failed)
    return summary


if __name__ == "__main__":
    asyncio.run(run_audit())

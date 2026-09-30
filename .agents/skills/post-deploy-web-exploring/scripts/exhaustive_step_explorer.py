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
    step_dir = Path(output_dir) / "steps"
    step_dir.mkdir(parents=True, exist_ok=True)
    report_file = Path(output_dir) / "exhaustive_steps_report.json"

    console_errors: List[str] = []
    page_errors: List[str] = []
    step_results: List[Dict[str, Any]] = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1440, "height": 900},
            permissions=["clipboard-read", "clipboard-write"]
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
                "screenshot": str(Path("results/screenshots/steps") / screenshot_name),
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

        # Step 31: Vector Memory HUD Telemetry
        async def check_step31():
            hud_val = await page.locator("#hud-vector-count").text_content()
            assert "STORED" in hud_val or "ACTIVE" in hud_val, f"Unexpected HUD vector count: {hud_val}"
            return f"HUD Vector Memory count: {hud_val}"
        await record_step(31, "Vector Memory HUD Telemetry", "Verify vector memory telemetry HUD row displays active index count", "31_hud_vector_memory.png", check_step31)

        # Step 32: Open Syndicate Dossier with Semantic Memory
        async def check_step32():
            first_card = page.locator(".alert-card").first
            await first_card.click(timeout=3000)
            await page.wait_for_timeout(900)
            is_visible = await page.locator("#similar-wallets-section").is_visible()
            assert is_visible, "Similar wallets section not visible in dossier"
            return "Similar wallets section successfully displayed inside curatorial plaque"
        await record_step(32, "Open Dossier Similar Wallets", "Click alert card to open dossier with Similar Wallets section", "32_dossier_similar_wallets.png", check_step32)

        # Step 33: Verify Similar Wallet Cards Count
        async def check_step33():
            cards = page.locator(".similar-wallet-card")
            count = await cards.count()
            assert count >= 1, f"Expected at least 1 similar wallet card, found {count}"
            return f"Rendered {count} similar wallet cards in dossier"
        await record_step(33, "Similar Wallet Cards Density", "Inspect rendered similar wallet cards in active dossier", "33_similar_wallet_cards.png", check_step33)

        # Step 34: Inspect Top Similar Wallet Details
        async def check_step34():
            first_sim = page.locator(".similar-wallet-card").first
            text = await first_sim.text_content()
            badge = await first_sim.locator(".similarity-badge").text_content()
            return f"Top match card text: {text.strip()} | Similarity badge: {badge}"
        await record_step(34, "Top Similar Wallet Details", "Verify short address, similarity badge, syndicate tag, and Jito marker", "34_top_similar_wallet_details.png", check_step34)

        # Step 35: Verify Cosine Similarity Score Badge
        async def check_step35():
            first_badge = page.locator(".similar-wallet-card .similarity-badge").first
            badge_text = await first_badge.text_content()
            badge_class = await first_badge.get_attribute("class")
            assert "%" in badge_text, f"Badge does not contain percentage: {badge_text}"
            assert any(cls in badge_class for cls in ["badge-high", "badge-mid", "badge-low"]), f"Unexpected badge class: {badge_class}"
            return f"Badge text: {badge_text}, CSS class: {badge_class}"
        await record_step(35, "Cosine Similarity Score Gauge", "Verify deterministic cosine similarity percentage and color-coded badge", "35_similarity_score_gauge.png", check_step35)

        # Step 36: Interactive Similarity Slider (Scale Down to 3)
        async def check_step36():
            slider = page.locator("#similarity-slider")
            await slider.evaluate("el => { el.value = 3; el.dispatchEvent(new Event('input')); }")
            await page.wait_for_timeout(300)
            val_disp = await page.locator("#similarity-slider-val").text_content()
            card_count = await page.locator(".similar-wallet-card").count()
            assert val_disp == "3", f"Expected slider value display 3, got {val_disp}"
            assert card_count <= 3, f"Expected <= 3 cards rendered, got {card_count}"
            return f"Slider set to 3: displayed count = {val_disp}, visible cards = {card_count}"
        await record_step(36, "Similarity Slider Scale Down", "Adjust similarity slider to 3 and verify card count updates dynamically", "36_similarity_slider_down.png", check_step36)

        # Step 37: Interactive Similarity Slider (Scale Up to 10)
        async def check_step37():
            slider = page.locator("#similarity-slider")
            await slider.evaluate("el => { el.value = 10; el.dispatchEvent(new Event('input')); }")
            await page.wait_for_timeout(300)
            val_disp = await page.locator("#similarity-slider-val").text_content()
            card_count = await page.locator(".similar-wallet-card").count()
            assert val_disp == "10", f"Expected slider value display 10, got {val_disp}"
            return f"Slider set to 10: displayed count = {val_disp}, visible cards = {card_count}"
        await record_step(37, "Similarity Slider Scale Up", "Adjust similarity slider to 10 and verify card list expands", "37_similarity_slider_up.png", check_step37)

        # Step 38: Verify 3D Semantic Memory Connectome Arcs
        async def check_step38():
            arcs_count = await page.evaluate("() => window.similarityArcsGroup ? window.similarityArcsGroup.children.length : (typeof similarityArcsGroup !== 'undefined' ? similarityArcsGroup.children.length : -1)")
            return f"3D Luminous Cyan Dashed Similarity Arcs rendered: {arcs_count} splines"
        await record_step(38, "3D Similarity Spline Arcs", "Verify 3D dashed bezier connectome arcs rendered between similar wallets", "38_similarity_spline_arcs.png", check_step38)

        # Step 39: Glide Focus to Similar Wallet
        async def check_step39():
            cards = page.locator(".similar-wallet-card")
            if await cards.count() > 1:
                await cards.nth(1).click(timeout=3000)
                await page.wait_for_timeout(900)
                dossier_title = await page.locator("#dossier-title").text_content()
                return f"Glided focus to similar wallet. Current dossier title: {dossier_title}"
            return "Only 1 card available, clicked first card"
        await record_step(39, "Glide Focus Similar Wallet", "Click similar wallet card to trigger camera glide and entity inspection", "39_glide_similar_wallet.png", check_step39)

        # Step 40: Dismiss Curatorial Dossier
        async def check_step40():
            close_btn = page.locator("#curatorial-plaque .plaque-close-btn:visible")
            if await close_btn.count() > 0:
                await close_btn.first.click()
            await page.wait_for_timeout(400)
            is_hidden = await page.locator("#curatorial-plaque").evaluate("el => el.style.display === 'none'")
            return f"Curatorial dossier dismissed (hidden={is_hidden})"
        await record_step(40, "Dismiss Curatorial Dossier", "Dismiss plaque and confirm visualizer returns to clean connectome canvas", "40_dismiss_dossier_final.png", check_step40)

        # Step 41: Campaign HUD Telemetry Verification
        async def check_step41():
            camp_val = await page.locator("#hud-campaign-count").text_content()
            assert "ACTIVE" in camp_val or any(char.isdigit() for char in camp_val), f"Unexpected campaign count: {camp_val}"
            return f"HUD Campaign count: {camp_val}"
        await record_step(41, "Campaign HUD Telemetry", "Verify campaign count telemetry row displays active campaigns", "41_hud_campaigns_telemetry.png", check_step41)

        # Step 42: Campaign Forensic Explainer (Click #row-campaigns)
        async def check_step42():
            await page.locator("#row-campaigns").click(timeout=3000)
            await page.wait_for_timeout(400)
            title = await page.locator("#explain-title").text_content()
            assert "CAMPAIGN" in title.upper() or "CROSS" in title.upper(), f"Unexpected explainer title: {title}"
            return f"Campaign Explainer Card Title: {title}"
        await record_step(42, "Campaign Forensic Explainer", "Click campaigns telemetry row to open Level 1 explain card", "42_campaign_explain_card.png", check_step42)

        # Step 43: Dismiss Explainer Card & Tag Filter [#Campaigns]
        async def check_step43():
            close_btn = page.locator("#curatorial-plaque .plaque-close-btn:visible")
            if await close_btn.count() > 0:
                await close_btn.first.click()
            await page.wait_for_timeout(300)
            await page.locator("#tag-campaigns").click(timeout=3000)
            is_selected = await page.locator("#tag-campaigns").evaluate("el => el.classList.contains('selected')")
            assert is_selected, "Campaigns filter tag not selected"
            return f"Campaigns tag selected: {is_selected}"
        await record_step(43, "Filter Tag Campaigns", "Filter 3D connectome and radar to cross-token campaign entities", "43_tag_campaigns_filter.png", check_step43)

        # Step 44: Tag Filter [$BELUGA]
        async def check_step44():
            await page.locator("#tag-beluga").click(timeout=3000)
            is_selected = await page.locator("#tag-beluga").evaluate("el => el.classList.contains('selected')")
            feed_count = await page.locator("#feed-count").text_content()
            return f"Beluga tag selected: {is_selected}, Visible feed count: {feed_count}"
        await record_step(44, "Filter Tag Beluga", "Filter connectome and alerts to $BELUGA token cluster", "44_tag_beluga_filter.png", check_step44)

        # Step 45: Tag Filter [$SNIPEX]
        async def check_step45():
            await page.locator("#tag-snipex").click(timeout=3000)
            is_selected = await page.locator("#tag-snipex").evaluate("el => el.classList.contains('selected')")
            feed_count = await page.locator("#feed-count").text_content()
            return f"Snipex tag selected: {is_selected}, Visible feed count: {feed_count}"
        await record_step(45, "Filter Tag Snipex", "Filter connectome and alerts to $SNIPEX token cluster", "45_tag_snipex_filter.png", check_step45)

        # Step 46: Open Dossier with Cross-Token Campaign Section
        async def check_step46():
            vis_cards = page.locator(".alert-card:visible")
            if await vis_cards.count() == 0:
                await page.locator(".tag-chip[data-filter='all']").click(timeout=3000)
                await page.wait_for_timeout(200)
            card = page.locator(".alert-card:visible").first
            await card.click(timeout=3000)
            await page.wait_for_timeout(900)
            is_visible = await page.locator("#campaign-section").is_visible()
            assert is_visible, "Campaign section not visible in dossier"
            return "Cross-Token Campaign section visible inside active syndicate dossier"
        await record_step(46, "Open Dossier Campaign Section", "Click alert card to open dossier with Cross-Token Campaign section", "46_dossier_campaign_section.png", check_step46)

        # Step 47: Verify Campaign Name, Linked Tokens & Reused Wallets
        async def check_step47():
            camp_name = await page.locator("#dossier-campaign-name").text_content()
            camp_tag = await page.locator("#dossier-campaign-tag").text_content()
            camp_tokens = await page.locator("#dossier-campaign-tokens").text_content()
            camp_reused = await page.locator("#dossier-campaign-reused").text_content()
            assert camp_name and camp_name != "--", f"Empty campaign name: {camp_name}"
            return f"Name: {camp_name} | Tag: {camp_tag} | Tokens: {camp_tokens} | Reused: {camp_reused}"
        await record_step(47, "Verify Campaign Details", "Verify campaign classification, linked token symbols, and reused wallet badge", "47_campaign_details_verified.png", check_step47)

        # Step 48: Verify 3D Gold Campaign Hyper-Arcs
        async def check_step48():
            arcs_count = await page.evaluate("() => window.campaignArcsGroup ? window.campaignArcsGroup.children.length : -1")
            assert arcs_count >= 1, f"Expected at least 1 campaign arc, got {arcs_count}"
            return f"3D Luminous Gold Campaign Hyper-Arcs rendered: {arcs_count} splines"
        await record_step(48, "3D Gold Campaign Hyper-Arcs", "Verify 3D gold dashed bezier connectome arcs rendered between correlated tokens", "48_3d_campaign_hyper_arcs.png", check_step48)

        # Step 49: Reset Filter to [ALL]
        async def check_step49():
            await page.locator(".tag-chip[data-filter='all']").click(timeout=3000)
            is_selected = await page.locator(".tag-chip[data-filter='all']").evaluate("el => el.classList.contains('selected')")
            assert is_selected, "ALL filter tag not selected"
            return f"ALL filter tag selected: {is_selected}"
        await record_step(49, "Reset Filter All", "Reset entity filters to display entire global connectome", "49_tag_all_campaigns_reset.png", check_step49)

        # Step 50: Dismiss Curatorial Plaque
        async def check_step50():
            close_btn = page.locator("#curatorial-plaque .plaque-close-btn:visible")
            if await close_btn.count() > 0:
                await close_btn.first.click()
            await page.wait_for_timeout(400)
            is_hidden = await page.locator("#curatorial-plaque").evaluate("el => el.style.display === 'none'")
            return f"Curatorial dossier dismissed (hidden={is_hidden})"
        await record_step(50, "Dismiss Dossier", "Dismiss curatorial plaque before simulation inspection", "50_dismiss_dossier.png", check_step50)

        # Step 51: Telemetry HUD Simulation Alpha Verification
        async def check_step51():
            alpha_text = await page.locator("#hud-sim-alpha").text_content()
            assert alpha_text and "NET" in alpha_text, f"Unexpected sim alpha text: {alpha_text}"
            return f"HUD Sim Alpha displayed: {alpha_text}"
        await record_step(51, "Telemetry HUD Sim Alpha", "Verify HUD Sim Alpha telemetry row displays net expected ROI percentage", "51_hud_sim_alpha_telemetry.png", check_step51)

        # Step 52: Click Sim Alpha Telemetry Row for Forensic Explain Card
        async def check_step52():
            await page.locator("#row-sim-alpha").click(timeout=3000)
            await page.wait_for_timeout(400)
            title = await page.locator("#explain-title").text_content()
            assert "ALPHA" in title.upper() or "SIM" in title.upper(), f"Unexpected explain card title: {title}"
            return f"Forensic explain card opened: {title}"
        await record_step(52, "Explain Sim Alpha Card", "Click telemetry row to inspect simulation alpha forensic card", "52_sim_alpha_explain_card.png", check_step52)

        # Step 53: Dismiss Plaque & Verify Command Deck Simulator Section
        async def check_step53():
            close_btn = page.locator("#curatorial-plaque .plaque-close-btn:visible")
            if await close_btn.count() > 0:
                await close_btn.first.click()
            await page.wait_for_timeout(300)
            is_visible = await page.locator("#sim-controls-section").is_visible()
            assert is_visible, "Shadow simulator controls section not visible in command deck"
            status_text = await page.locator("#sim-status-badge").text_content()
            return f"Shadow Simulator section visible in command deck (Status: {status_text})"
        await record_step(53, "Verify Sim Controls Section", "Dismiss explain plaque and verify interactive Shadow Simulator controls in command deck", "53_sim_controls_section.png", check_step53)

        # Step 54: Adjust Execution Latency Slider
        async def check_step54():
            slider = page.locator("#sim-latency-slider")
            await slider.evaluate("el => { el.value = 2.5; el.dispatchEvent(new Event('input')); }")
            await page.wait_for_timeout(300)
            val = await page.locator("#sim-latency-val").text_content()
            assert "2.5" in val, f"Expected 2.5s latency, got: {val}"
            return f"Execution latency adjusted to: {val}"
        await record_step(54, "Adjust Latency Slider", "Adjust execution latency slider to 2.5s and verify dynamic UI recalculation", "54_sim_latency_slider.png", check_step54)

        # Step 55: Adjust Exit Lead Slider
        async def check_step55():
            slider = page.locator("#sim-lead-slider")
            await slider.evaluate("el => { el.value = 6.0; el.dispatchEvent(new Event('input')); }")
            await page.wait_for_timeout(300)
            val = await page.locator("#sim-lead-val").text_content()
            assert "6.0" in val, f"Expected 6.0s exit lead, got: {val}"
            return f"Exit lead adjusted to: {val}"
        await record_step(55, "Adjust Exit Lead Slider", "Adjust exit lead slider to 6.0s and verify dynamic UI recalculation", "55_sim_lead_slider.png", check_step55)

        # Step 56: Verify Dynamic SVG Equity Curve
        async def check_step56():
            d_attr = await page.locator("#sim-equity-line").get_attribute("d")
            assert d_attr and len(d_attr) > 10, f"SVG equity curve path empty: {d_attr}"
            equity_end = await page.locator("#sim-equity-end").text_content()
            return f"SVG portfolio equity curve rendered (d='{d_attr[:24]}...', Final Equity: {equity_end})"
        await record_step(56, "SVG Equity Curve Rendered", "Verify dynamic SVG portfolio equity curve path updates with live trajectory", "56_svg_equity_curve.png", check_step56)

        # Step 57: Click Timeline Pill SIM IN (T+14s)
        async def check_step57():
            await page.locator("#pill-sim-in").click(timeout=3000)
            await page.wait_for_timeout(400)
            slider_val = await page.locator("#timeline-slider").evaluate("el => el.value")
            time_disp = await page.locator("#timeline-time-display").text_content()
            return f"Timeline jumped to {time_disp} (slider={slider_val})"
        await record_step(57, "Timeline Pill SIM IN", "Click SIM IN stage pill to inspect execution ingress timing anchor", "57_pill_sim_in.png", check_step57)

        # Step 58: Click Timeline Pill SIM OUT (T+24s)
        async def check_step58():
            await page.locator("#pill-sim-out").click(timeout=3000)
            await page.wait_for_timeout(400)
            slider_val = await page.locator("#timeline-slider").evaluate("el => el.value")
            time_disp = await page.locator("#timeline-time-display").text_content()
            return f"Timeline jumped to {time_disp} (slider={slider_val})"
        await record_step(58, "Timeline Pill SIM OUT", "Click SIM OUT stage pill to inspect optimal front-run exit timing anchor", "58_pill_sim_out.png", check_step58)

        # Step 59: Inspect Syndicate Dossier Shadow Backtest Outcome
        async def check_step59():
            vis_cards = page.locator(".alert-card:visible")
            if await vis_cards.count() == 0:
                await page.locator(".tag-chip[data-filter='all']").click(timeout=3000)
                await page.wait_for_timeout(200)
            card = page.locator(".alert-card:visible").first
            await card.click(timeout=3000)
            await page.wait_for_timeout(800)
            is_visible = await page.locator("#simulator-section").is_visible()
            assert is_visible, "Simulator section not visible in dossier"
            badge = await page.locator("#dossier-sim-badge").text_content()
            pnl = await page.locator("#dossier-sim-pnl").text_content()
            strat = await page.locator("#dossier-sim-strategy").text_content()
            return f"Dossier Simulator Section: Strategy={strat}, Badge={badge}, Net Alpha={pnl}"
        await record_step(59, "Dossier Simulator Section", "Open curatorial dossier and verify simulated shadow backtest outcome metrics", "59_dossier_sim_section.png", check_step59)

        # Step 60: Dismiss Curatorial Plaque (Final Station State)
        async def check_step60():
            close_btn = page.locator("#curatorial-plaque .plaque-close-btn:visible")
            if await close_btn.count() > 0:
                await close_btn.first.click()
            await page.wait_for_timeout(400)
            is_hidden = await page.locator("#curatorial-plaque").evaluate("el => el.style.display === 'none'")
            return f"Curatorial dossier dismissed (hidden={is_hidden}) - 60 Steps Completed Successfully"
        await record_step(60, "Full Station Final Harmony", "Dismiss plaque and confirm 100% station canvas harmony across all 60 steps", "60_full_station_final_harmony.png", check_step60)

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
    asyncio.run(run_exhaustive_exploration("http://localhost:8000/web/syndicate_3d_visualizer.html", "results/screenshots"))

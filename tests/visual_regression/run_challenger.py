import json
import os
import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

VIEWPORTS = [
    {"name": "desktop_1440x900", "width": 1440, "height": 900},
    {"name": "laptop_1280x800", "width": 1280, "height": 800},
    {"name": "tablet_1024x768", "width": 1024, "height": 768},
    {"name": "mobile_375x812", "width": 375, "height": 812}
]

URL = "http://localhost:8000/web/syndicate_3d_visualizer.html"
OUTPUT_DIR = Path("results/screenshots/challenger")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
REPORT_PATH = Path("results/visual_regression_challenger.json")


def compute_box(handle):
    if not handle:
        return None
    try:
        if handle.count() == 0:
            return None
        box = handle.first.bounding_box()
        if not box:
            return None
        return {
            "x": round(box["x"], 2),
            "y": round(box["y"], 2),
            "width": round(box["width"], 2),
            "height": round(box["height"], 2),
            "right": round(box["x"] + box["width"], 2),
            "bottom": round(box["y"] + box["height"], 2)
        }
    except Exception:
        return None


def compute_overlap(box_a, box_b):
    if not box_a or not box_b:
        return {"overlap_x": 0, "overlap_y": 0, "collides": False, "clearance_x": 9999}
    overlap_x = max(0.0, min(box_a["right"], box_b["right"]) - max(box_a["x"], box_b["x"]))
    overlap_y = max(0.0, min(box_a["bottom"], box_b["bottom"]) - max(box_a["y"], box_b["y"]))
    collides = (overlap_x > 0.0) and (overlap_y > 0.0)
    
    # Horizontal clearance
    if box_a["right"] <= box_b["x"]:
        clearance_x = round(box_b["x"] - box_a["right"], 2)
    elif box_b["right"] <= box_a["x"]:
        clearance_x = round(box_a["x"] - box_b["right"], 2)
    else:
        clearance_x = round(-overlap_x, 2)
        
    return {
        "overlap_x": round(overlap_x, 2),
        "overlap_y": round(overlap_y, 2),
        "collides": collides,
        "clearance_x": clearance_x
    }


def test_viewport(browser, vp_info):
    vp_name = vp_info["name"]
    w, h = vp_info["width"], vp_info["height"]
    print(f"=== Testing Viewport: {vp_name} ({w}x{h}) ===")

    console_errors = []
    page_errors = []

    context = browser.new_context(
        viewport={"width": w, "height": h},
        permissions=["clipboard-read", "clipboard-write"]
    )
    page = context.new_page()
    page.on("console", lambda msg: console_errors.append(f"[{msg.type.upper()}] {msg.text}") if msg.type == "error" else None)
    page.on("pageerror", lambda err: page_errors.append(str(err)))

    page.goto(URL, wait_until="networkidle", timeout=10000)
    page.wait_for_timeout(1500)

    # 1. Baseline screenshot
    baseline_ss = str(OUTPUT_DIR / f"{vp_name}_baseline.png")
    page.screenshot(path=baseline_ss, full_page=False)

    # Elements
    timeline_el = page.locator(".timeline-bar")
    deck_el = page.locator("aside.command-deck")
    telemetry_el = page.locator(".telemetry-hud")
    filter_el = page.locator(".filter-strip")
    plaque_el = page.locator("#curatorial-plaque")

    timeline_box = compute_box(timeline_el)
    deck_box = compute_box(deck_el)
    telemetry_box = compute_box(telemetry_el)
    filter_box = compute_box(filter_el)

    # Timeline vs Command Deck collision analysis
    timeline_deck_overlap = compute_overlap(timeline_box, deck_box)

    # Verify clearance >= 20px
    clearance_compliant = (timeline_deck_overlap["clearance_x"] >= 20.0) and not timeline_deck_overlap["collides"]

    # 2. Click .alert-card to open curatorial-plaque
    alert_cards = page.locator(".alert-card")
    alert_card_count = alert_cards.count()
    alert_clicked = False
    alert_click_error = None
    plaque_opened = False

    if alert_card_count > 0:
        try:
            alert_cards.first.click(timeout=3000)
            alert_clicked = True
            page.wait_for_timeout(500)
            plaque_opened = page.evaluate("() => { const p = document.getElementById('curatorial-plaque'); return p && window.getComputedStyle(p).display !== 'none'; }")
        except Exception as e:
            alert_click_error = str(e)
    else:
        try:
            page.evaluate("() => { if (window.showDossier) window.showDossier({ id: 'TEST_SYND', label: 'Test Cluster', confidence: 0.95, mode: 'flash', average_entry_window_seconds: 14.2, average_exit_window_seconds: 7.8 }); }")
            page.wait_for_timeout(500)
            plaque_opened = page.evaluate("() => { const p = document.getElementById('curatorial-plaque'); return p && window.getComputedStyle(p).display !== 'none'; }")
        except Exception as e:
            alert_click_error = f"Direct call error: {e}"

    plaque_box = compute_box(plaque_el) if plaque_opened else None
    plaque_ss = str(OUTPUT_DIR / f"{vp_name}_plaque_open.png")
    page.screenshot(path=plaque_ss, full_page=False)

    # Occlusion analysis: curatorial-plaque vs telemetry-hud
    plaque_telemetry_overlap = compute_overlap(plaque_box, telemetry_box) if plaque_box else None

    # Occlusion analysis: curatorial-plaque vs filter-strip
    plaque_filter_overlap = compute_overlap(plaque_box, filter_box) if plaque_box else None

    # ElementFromPoint checks at key telemetry and filter coordinates
    point_occlusion_telemetry = None
    if telemetry_box and plaque_box:
        cx = telemetry_box["x"] + telemetry_box["width"] / 2.0
        cy = telemetry_box["bottom"] - 10.0
        el_at_pt = page.evaluate("""(pt) => {
            const el = document.elementFromPoint(pt.x, pt.y);
            return el ? { tag: el.tagName, id: el.id, className: el.className } : null;
        }""", {"x": cx, "y": cy})
        point_occlusion_telemetry = el_at_pt

    point_occlusion_filter = None
    if filter_box and plaque_box:
        fx = filter_box["x"] + 20.0
        fy = filter_box["y"] + 10.0
        el_at_filter = page.evaluate("""(pt) => {
            const el = document.elementFromPoint(pt.x, pt.y);
            return el ? { tag: el.tagName, id: el.id, className: el.className } : null;
        }""", {"x": fx, "y": fy})
        point_occlusion_filter = el_at_filter

    # 3. Interactive controls clickability and pointer interception sweep
    click_results = {}
    controls_to_test = [
        ("header_clarity_btn", "#clarity-btn"),
        ("header_reset_cam_btn", "#reset-cam-btn"),
        ("header_poll_toggle_btn", "#poll-toggle-btn"),
        ("chip_gmgn", "#chip-gmgn"),
        ("chip_solscan", "#chip-solscan"),
        ("chip_rpc", "#chip-rpc"),
        ("chip_cache", "#chip-cache"),
        ("filter_chip_all", ".tag-chip[data-filter='all']"),
        ("filter_chip_flash", ".tag-chip[data-filter='flash']"),
        ("filter_chip_sustained", ".tag-chip[data-filter='sustained']"),
        ("filter_chip_bundler", ".tag-chip[data-filter='bundler']"),
        ("timeline_play_pause", "#play-pause-btn"),
        ("timeline_stage_snipe", "#pill-snipe"),
        ("timeline_stage_bundle", "#pill-bundle"),
        ("timeline_stage_dump", "#pill-dump"),
        ("timeline_stage_mint", "#pill-mint"),
        ("deck_kpi_card_1", ".kpi-card:nth-child(1)"),
        ("deck_kpi_card_2", ".kpi-card:nth-child(2)"),
        ("deck_toggle_btn", "#deck-toggle-btn"),
    ]

    for name, sel in controls_to_test:
        loc = page.locator(sel)
        if loc.count() > 0:
            try:
                loc.first.click(timeout=1500)
                click_results[name] = {"status": "SUCCESS", "error": None}
            except Exception as e:
                click_results[name] = {"status": "FAILED", "error": str(e)}
        else:
            click_results[name] = {"status": "NOT_FOUND", "error": None}

    # Test plaque actions when plaque is open
    plaque_controls = [
        ("plaque_copy_address", "#copy-address-btn"),
        ("plaque_export_md", "#export-md-btn"),
        ("plaque_close_btn", ".plaque-close-btn"),
    ]
    for name, sel in plaque_controls:
        loc = page.locator(sel)
        if loc.count() > 0:
            try:
                loc.first.click(timeout=1500)
                click_results[name] = {"status": "SUCCESS", "error": None}
            except Exception as e:
                click_results[name] = {"status": "FAILED", "error": str(e)}
        else:
            click_results[name] = {"status": "NOT_FOUND", "error": None}

    page.wait_for_timeout(200)
    plaque_closed = page.evaluate("() => { const p = document.getElementById('curatorial-plaque'); return !p || window.getComputedStyle(p).display === 'none'; }")

    final_ss = str(OUTPUT_DIR / f"{vp_name}_final.png")
    page.screenshot(path=final_ss, full_page=False)

    context.close()

    result = {
        "viewport": vp_info,
        "boxes": {
            "timeline_bar": timeline_box,
            "command_deck": deck_box,
            "telemetry_hud": telemetry_box,
            "filter_strip": filter_box,
            "curatorial_plaque": plaque_box
        },
        "timeline_vs_deck": {
            "overlap": timeline_deck_overlap,
            "clearance_px": timeline_deck_overlap["clearance_x"],
            "clearance_compliant": clearance_compliant
        },
        "plaque_vs_telemetry": {
            "overlap": plaque_telemetry_overlap,
            "point_element": point_occlusion_telemetry
        },
        "plaque_vs_filter": {
            "overlap": plaque_filter_overlap,
            "point_element": point_occlusion_filter
        },
        "alert_interaction": {
            "alert_card_count": alert_card_count,
            "alert_clicked": alert_clicked,
            "alert_click_error": alert_click_error,
            "plaque_opened": plaque_opened,
            "plaque_closed_by_btn": plaque_closed
        },
        "click_results": click_results,
        "console_errors": console_errors,
        "page_errors": page_errors,
        "screenshots": {
            "baseline": baseline_ss,
            "plaque_open": plaque_ss,
            "final": final_ss
        }
    }
    return result


def main():
    print("Starting Visual Regression Challenger Suite across 4 viewports...")
    results = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        for vp in VIEWPORTS:
            res = test_viewport(browser, vp)
            results[vp["name"]] = res
        browser.close()

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"All viewports tested! Report saved to: {REPORT_PATH}")


if __name__ == "__main__":
    main()

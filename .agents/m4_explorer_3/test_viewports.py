import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

VIEWPORTS = [
    {"name": "1440x900", "width": 1440, "height": 900},
    {"name": "1280x800", "width": 1280, "height": 800},
    {"name": "1024x768", "width": 1024, "height": 768},
    {"name": "375x812", "width": 375, "height": 812},
]

async def capture_all():
    out_dir = Path("results/screenshots")
    out_dir.mkdir(parents=True, exist_ok=True)
    url = "http://localhost:8000/web/syndicate_3d_visualizer.html"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        for vp in VIEWPORTS:
            page = await browser.new_page(viewport={"width": vp["width"], "height": vp["height"]})
            await page.goto(url, wait_until="networkidle", timeout=15000)
            await page.wait_for_timeout(1000)
            
            # Inspect layout metrics
            metrics = await page.evaluate("""() => {
                const header = document.querySelector('header.hud-header');
                const telemetry = document.querySelector('.telemetry-hud');
                const filters = document.querySelector('.filter-strip');
                const deck = document.querySelector('aside.command-deck');
                const timeline = document.querySelector('.timeline-bar');
                
                function getRect(el) {
                    if (!el) return null;
                    const r = el.getBoundingClientRect();
                    return { x: r.x, y: r.y, width: r.width, height: r.height, right: r.right, bottom: r.bottom };
                }
                
                return {
                    window: { width: window.innerWidth, height: window.innerHeight },
                    header: getRect(header),
                    telemetry: getRect(telemetry),
                    filters: getRect(filters),
                    deck: getRect(deck),
                    timeline: getRect(timeline),
                    deckCollapsed: deck ? deck.classList.contains('collapsed') : null
                };
            }""")
            
            file_name = f"viewport_{vp['name']}.png"
            target_path = out_dir / file_name
            await page.screenshot(path=str(target_path))
            print(f"Captured {file_name} ({vp['width']}x{vp['height']}):")
            print(f"  Header width: {metrics['header']['width'] if metrics['header'] else None}")
            print(f"  Telemetry: {metrics['telemetry']}")
            print(f"  Filters: {metrics['filters']}")
            print(f"  Command Deck: {metrics['deck']}")
            print(f"  Timeline Bar: {metrics['timeline']}")
            await page.close()
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(capture_all())

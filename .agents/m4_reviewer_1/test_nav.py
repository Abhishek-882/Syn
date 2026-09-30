import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(
            viewport={"width": 1440, "height": 900},
            permissions=["clipboard-read", "clipboard-write"]
        )
        page = await ctx.new_page()
        
        pending_requests = set()
        page.on("request", lambda r: pending_requests.add(r.url))
        page.on("requestfinished", lambda r: pending_requests.discard(r.url))
        page.on("requestfailed", lambda r: (print(f"FAILED REQ: {r.url} - {r.failure}"), pending_requests.discard(r.url)))
        
        print("Navigating with networkidle...")
        try:
            await page.goto("http://localhost:8000/web/syndicate_3d_visualizer.html", wait_until="networkidle", timeout=8000)
            print("Navigation succeeded with networkidle!")
        except Exception as e:
            print(f"Navigation timed out with networkidle: {e}")
            print("Pending requests at timeout:")
            for req in pending_requests:
                print(" - ", req)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())

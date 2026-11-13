import asyncio
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from playwright.async_api import async_playwright
from scripts.e2e_auth_helper import authenticate_session

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1400, "height": 900})
        
        ok = await authenticate_session(page, "skumar", "skumar@123")
        if not ok:
            print("Auth failed!")
            await browser.close()
            return
            
        await page.wait_for_timeout(2000)
        
        # Click Pre-IPO DRHP in sidebar
        nav_items = page.locator("[data-testid='stSidebarNav'] a, a:has-text('Pre-IPO DRHP Intelligence')")
        count = await nav_items.count()
        clicked = False
        for i in range(count):
            item = nav_items.nth(i)
            text = await item.inner_text()
            if "Pre-IPO DRHP" in text:
                await item.click()
                clicked = True
                break
                
        if not clicked:
            link = page.locator("a:has-text('Pre-IPO DRHP Intelligence')").first
            await link.click()
            
        await page.wait_for_timeout(4000)
        
        # Ensure Hindustan Coca-Cola is selected in selectbox
        sb = page.locator("div[data-testid='stSelectbox']:has-text('Select Target DRHP')").first
        # If it's already selected or not, take screenshot
        out_path = r"C:\Users\hemas\.gemini\antigravity\brain\f6978611-2b08-4fd9-8af9-7b703ed76b10\verified_hccb_hero_fix.png"
        await page.screenshot(path=out_path, full_page=False)
        print("Screenshot saved to", out_path)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())

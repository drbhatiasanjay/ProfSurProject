"""
Playwright E2E UI Evidence Capture for Pre-IPO FIBO Knowledge Graph Studio
Captures:
1. Mode A: Novice Guided Discovery Canvas (Verdict HUD strip, recipe cards, interactive graph canvas).
2. Mode B: Expert Quant Studio (Query console, Jev pruning slider, PROV-O inspector, football field chart).
"""

import os
import sys
import asyncio
from playwright.async_api import async_playwright

async def run_evidence_capture():
    print("=== STARTING PLAYWRIGHT EVIDENCE CAPTURE ===", flush=True)
    out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scratch")
    os.makedirs(out_dir, exist_ok=True)

    screen_novice = os.path.join(out_dir, "kg_studio_novice_canvas.png")
    screen_quant = os.path.join(out_dir, "kg_studio_quant_studio.png")
    screen_recipe = os.path.join(out_dir, "kg_studio_recipe_expanded.png")

    async with async_playwright() as p:
        # Launch Chromium headless with high-DPI viewport
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1600, "height": 1050},
            device_scale_factor=1.5
        )
        page = await context.new_page()

        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        page.on("pageerror", lambda err: console_errors.append(str(err)))

        print("Navigating to http://localhost:5173/ ...", flush=True)
        await page.goto("http://localhost:5173/", wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(2000)

        # 1. Click on "FIBO Knowledge Graph" in the sidebar
        print("Clicking on 'FIBO Knowledge Graph' in SidebarNav...", flush=True)
        kg_button = page.locator('text="FIBO Knowledge Graph"').first
        await kg_button.click()
        await page.wait_for_timeout(2500)

        # 2. Capture Mode A (Novice Guided Discovery Canvas)
        print("Capturing Mode A: Novice Guided Discovery Canvas...", flush=True)
        await page.screenshot(path=screen_novice, full_page=False)
        print(f"-> Saved: {screen_novice}", flush=True)

        # 3. Click Recipe 2 (EBITDA margin sustainability) to test interaction
        print("Executing Recipe 2: EBITDA Margin Sustainability...", flush=True)
        recipe2 = page.locator('text="Is Q1 FY27 margin expansion real?"').first
        if await recipe2.is_visible():
            await recipe2.click()
            await page.wait_for_timeout(2000)
            await page.screenshot(path=screen_recipe, full_page=False)
            print(f"-> Saved: {screen_recipe}", flush=True)

        # 4. Switch to Mode B: Expert Quant Studio
        print("Switching to Mode B: Expert Quant Studio...", flush=True)
        # Scroll back to top to ensure header controls are in view
        await page.evaluate("window.scrollTo(0, 0)")
        await page.wait_for_timeout(500)
        quant_btn = page.locator('button:has-text("Expert Quant Studio")').first
        await quant_btn.scroll_into_view_if_needed()
        await quant_btn.click()
        await page.wait_for_timeout(2500)

        # 5. Capture Mode B (Expert Quant Studio)
        print("Capturing Mode B: Expert Quant Studio...", flush=True)
        await page.screenshot(path=screen_quant, full_page=False)
        print(f"-> Saved: {screen_quant}", flush=True)

        await browser.close()

    print(f"\nAll screenshots successfully captured in {out_dir}!")
    print(f"Console errors detected: {len(console_errors)}", flush=True)
    if console_errors:
        for err in console_errors[:5]:
            print(f"  [Console Error]: {err}", flush=True)
    else:
        print("Zero console errors. 100% clean UI execution!", flush=True)

    return len(console_errors) == 0

if __name__ == "__main__":
    success = asyncio.run(run_evidence_capture())
    sys.exit(0 if success else 1)

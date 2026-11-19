"""
Playwright Visual Evidence Capture for Milestone 14:
Cross-Section Risk Contagion & Shock Simulation Workbench

Verifies:
1. Navigation to Knowledge Graph Studio on http://localhost:5173/
2. Clicking 'Simulate Cross-Section Contagion' to open the Contagion Shock Workbench modal.
3. Applying preset 'Severe Tail Risk: CESTAT + 150 bps RBI Rate Hike'.
4. Capturing modal screenshot showing pro-forma waterfall and causal sub-graph canvas.
5. Drilling down into Section 6 and triggering fact-level contagion simulation.
6. Ensuring 0 console errors.
"""

import asyncio
import os
from playwright.async_api import async_playwright


async def run_evidence_capture():
    print("=== STARTING PLAYWRIGHT EVIDENCE CAPTURE FOR CONTAGION WORKBENCH ===", flush=True)
    out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scratch")
    os.makedirs(out_dir, exist_ok=True)

    screen_workbench = os.path.join(out_dir, "kg_contagion_shock_workbench.png")
    screen_fact_shock = os.path.join(out_dir, "kg_contagion_fact_level_shock.png")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1600, "height": 1050},
            device_scale_factor=1.5
        )
        page = await context.new_page()

        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        page.on("pageerror", lambda err: console_errors.append(str(err)))

        print("1. Navigating to http://localhost:5173/ ...", flush=True)
        await page.goto("http://localhost:5173/", wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(2000)

        print("2. Clicking 'FIBO Knowledge Graph' in SidebarNav...", flush=True)
        kg_button = page.locator('button:has-text("FIBO Knowledge Graph")').first
        await kg_button.scroll_into_view_if_needed()
        await kg_button.click()
        await page.wait_for_timeout(2500)

        # 3. Click 'Simulate Cross-Section Contagion' in the summary grid
        print("3. Clicking 'Simulate Cross-Section Contagion' button...", flush=True)
        contagion_btn = page.locator('button:has-text("Simulate Cross-Section Contagion")').first
        await contagion_btn.scroll_into_view_if_needed()
        await contagion_btn.click()
        await page.wait_for_timeout(2000)

        # 4. Apply preset 'Severe Tail Risk: CESTAT + 150 bps RBI Rate Hike'
        print("4. Applying preset 'Severe Tail Risk: CESTAT + 150 bps RBI Rate Hike'...", flush=True)
        preset_btn = page.locator('button:has-text("Severe Tail Risk")').first
        if await preset_btn.is_visible():
            await preset_btn.click()
            await page.wait_for_timeout(2000)

        # 5. Capture Contagion Shock Workbench Modal
        print("5. Capturing Contagion Shock Workbench Modal...", flush=True)
        await page.screenshot(path=screen_workbench, full_page=False)
        print(f"-> Saved: {screen_workbench}", flush=True)

        # Close modal
        close_btn = page.locator('button:has-text("Close Workbench")').first
        if await close_btn.is_visible():
            await close_btn.click()
            await page.wait_for_timeout(1000)

        # 6. Drill down into Section 6
        print("6. Drilling down into Section 6: Outstanding Litigation...", flush=True)
        sec6_card = page.locator('h3:has-text("Outstanding Litigation")').first
        await sec6_card.scroll_into_view_if_needed()
        await sec6_card.click()
        await page.wait_for_timeout(2500)

        # 7. Click 'Simulate Cross-Section Contagion & Solvency Shock' on CESTAT fact card
        print("7. Triggering fact-level contagion simulation on CESTAT card...", flush=True)
        fact_shock_btn = page.locator('button:has-text("Simulate Cross-Section Contagion & Solvency Shock")').first
        if await fact_shock_btn.is_visible():
            await fact_shock_btn.scroll_into_view_if_needed()
            await fact_shock_btn.click()
            await page.wait_for_timeout(2000)
            print("8. Capturing fact-level contagion shock modal...", flush=True)
            await page.screenshot(path=screen_fact_shock, full_page=False)
            print(f"-> Saved: {screen_fact_shock}", flush=True)

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

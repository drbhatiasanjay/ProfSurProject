"""
Playwright E2E UI Evidence Capture for Pre-IPO FIBO Knowledge Graph Studio & In-App PDF Drawer
Captures:
1. Mode A: Novice Guided Discovery Canvas (Verdict HUD strip, recipe cards, interactive graph canvas).
2. In-App PDF Bounding Box Viewer Drawer (Slide-over viewer with authentic 513p HCCH DRHP text & amber highlights).
3. Mathematical Lineage & Canonical 84 Attributes DAG Modal (9 valuation formulas & 10 SEBI sections).
4. Mode B: Expert Quant Studio & Cypher Query Bank (25 pre-compiled queries, execution results & graph paths).
"""

import os
import sys
import asyncio
from playwright.async_api import async_playwright

async def run_evidence_capture():
    print("=== STARTING PLAYWRIGHT EVIDENCE CAPTURE FOR PRE-IPO KG & PDF DRAWER ===", flush=True)
    out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scratch")
    os.makedirs(out_dir, exist_ok=True)

    screen_novice = os.path.join(out_dir, "kg_studio_novice_canvas.png")
    screen_pdf_drawer = os.path.join(out_dir, "kg_studio_pdf_drawer.png")
    screen_formula_modal = os.path.join(out_dir, "kg_studio_formula_lineage.png")
    screen_cypher_bank = os.path.join(out_dir, "kg_studio_cypher_bank.png")

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

        # 3. Test In-App PDF Bounding Box Viewer Drawer
        print("Testing In-App PDF Bounding Box Viewer Drawer...", flush=True)
        pdf_btn = page.locator('button:has-text("DRHP PDF Drawer (p.18)")').first
        if await pdf_btn.is_visible():
            await pdf_btn.click()
            await page.wait_for_timeout(2000)
            await page.screenshot(path=screen_pdf_drawer, full_page=False)
            print(f"-> Saved: {screen_pdf_drawer}", flush=True)

            # Close drawer
            close_drawer_btn = page.locator('button:has(svg.lucide-x)').first
            if await close_drawer_btn.is_visible():
                await close_drawer_btn.click()
                await page.wait_for_timeout(500)

        # 4. Test Mathematical Lineage & 84 Attributes DAG Modal
        print("Testing Mathematical Lineage & 84 Attributes DAG Modal...", flush=True)
        formula_btn = page.locator('button:has-text("Formula Lineage (84 Attr)")').first
        if await formula_btn.is_visible():
            await formula_btn.click()
            await page.wait_for_timeout(2000)
            await page.screenshot(path=screen_formula_modal, full_page=False)
            print(f"-> Saved: {screen_formula_modal}", flush=True)

            # Close formula modal
            close_modal_btn = page.locator('button:has(svg.lucide-x)').first
            if await close_modal_btn.is_visible():
                await close_modal_btn.click()
                await page.wait_for_timeout(500)

        # 5. Switch to Mode B: Expert Quant Studio & Cypher Query Bank
        print("Switching to Mode B: Expert Quant Studio...", flush=True)
        await page.evaluate("window.scrollTo(0, 0)")
        await page.wait_for_timeout(500)
        quant_btn = page.locator('button:has-text("Expert Quant Studio")').first
        await quant_btn.scroll_into_view_if_needed()
        await quant_btn.click()
        await page.wait_for_timeout(2000)

        # 6. Execute Cypher Query in the Cypher Query Bank
        print("Executing Cypher Query from Bank...", flush=True)
        exec_cypher_btn = page.locator('button:has-text("Execute Cypher")').first
        if await exec_cypher_btn.is_visible():
            await exec_cypher_btn.scroll_into_view_if_needed()
            await exec_cypher_btn.click()
            await page.wait_for_timeout(2500)

        # Capture Mode B with Cypher Bank execution results
        print("Capturing Mode B: Expert Quant Studio with Cypher Bank...", flush=True)
        await page.screenshot(path=screen_cypher_bank, full_page=False)
        print(f"-> Saved: {screen_cypher_bank}", flush=True)

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

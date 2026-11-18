"""
Playwright E2E UI Evidence Capture for Milestone 13:
SEBI ICDR Statutory Section Hierarchy, Granular Verbatim Facts & Bi-Level Summary/Drilldown
Captures:
1. Level 1: 8 Statutory Sections Summary Grid with risk exposure and fact counts.
2. Level 2: Scoped Subgraph Drilldown into Section VI (Legal & Litigation).
3. In-App PDF Drawer opened directly from verbatim litigation disclosure citation.
"""

import os
import sys
import asyncio
from playwright.async_api import async_playwright

async def run_evidence_capture():
    print("=== STARTING PLAYWRIGHT EVIDENCE CAPTURE FOR SEBI SECTION HIERARCHY ===", flush=True)
    out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scratch")
    os.makedirs(out_dir, exist_ok=True)

    screen_summary = os.path.join(out_dir, "kg_section_summary_grid.png")
    screen_drilldown = os.path.join(out_dir, "kg_section_drilldown_litigation.png")
    screen_pdf_drawer = os.path.join(out_dir, "kg_section_drilldown_pdf_drawer.png")

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
        await page.wait_for_timeout(3000)

        # Level 1: Capture Summary View
        print("3. Capturing Level 1: 8 Statutory Sections Summary Grid...", flush=True)
        await page.screenshot(path=screen_summary, full_page=False)
        print(f"-> Saved: {screen_summary}", flush=True)

        # Level 2: Drill down into Section 6: Outstanding Litigation & Material Claims
        print("4. Drilling down into Section 6: Outstanding Litigation...", flush=True)
        sec6_card = page.locator('h3:has-text("Outstanding Litigation")').first
        await sec6_card.scroll_into_view_if_needed()
        await sec6_card.click()
        await page.wait_for_timeout(2500)

        print("5. Capturing Level 2: Scoped Subgraph Drilldown into Section 6...", flush=True)
        await page.screenshot(path=screen_drilldown, full_page=False)
        print(f"-> Saved: {screen_drilldown}", flush=True)

        # 6. Click citation on CESTAT Indirect Tax fact (Page 379)
        print("6. Clicking citation p.379 to open In-App PDF Bounding Box Viewer Drawer...", flush=True)
        await page.wait_for_selector('button:has-text("p.379")', timeout=10000)
        p379_btn = page.locator('button:has-text("p.379")').first
        await p379_btn.click()
        await page.wait_for_timeout(3000)
        print("7. Capturing In-App PDF Drawer with CESTAT quote highlight...", flush=True)
        await page.screenshot(path=screen_pdf_drawer, full_page=False)
        print(f"-> Saved: {screen_pdf_drawer}", flush=True)

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

"""
Playwright Visual Evidence Capture for Milestones 16 & 17
(CMIE Macro Peer Intelligence, Post-IPO Anchor Cliff, & Institutional Export Modal)
Governed by Rule F.3 (Evidence Gate Verification).
"""

import sys
import os
import time
from playwright.sync_api import sync_playwright

def capture_cmie_and_export_evidence():
    print("Launching Playwright for CMIE Macro & Institutional Export verification...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 1100})
        page = context.new_page()

        # 1. Navigate to local terminal
        print("Navigating to http://localhost:5173/ ...")
        page.goto("http://localhost:5173/", wait_until="networkidle", timeout=30000)
        time.sleep(2)

        # 2. Click KG tab in sidebar
        print("Switching to FIBO Knowledge Graph tab...")
        kg_nav_btn = page.locator('button:has-text("FIBO Knowledge Graph")')
        kg_nav_btn.wait_for(state="visible", timeout=10000)
        kg_nav_btn.click()
        time.sleep(2)

        # 3. Scroll to CMIE Macro Workbench
        print("Locating CMIE Macro Workbench...")
        cmie_banner = page.locator('span:has-text("CMIE ProwessIQ Peer Benchmarks")')
        cmie_banner.wait_for(state="visible", timeout=10000)
        cmie_banner.scroll_into_view_if_needed()
        time.sleep(1)

        # 4. Capture CMIE Macro & Anchor Cliff Workbench Screenshot
        os.makedirs("scratch", exist_ok=True)
        screen_1 = "scratch/kg_cmie_macro_workbench.png"
        page.screenshot(path=screen_1, full_page=False)
        print(f"Captured CMIE Macro Workbench evidence: {screen_1}")

        # 5. Open Institutional Export Modal
        print("Opening Institutional Export Modal...")
        export_btn = page.locator('button:has-text("Institutional Export (.ttl / .cyp)")')
        export_btn.wait_for(state="visible", timeout=10000)
        export_btn.click()
        time.sleep(1.5)

        # 6. Verify Modal Presence & Capture
        modal_title = page.locator('h3:has-text("Institutional Knowledge Graph Exporter")')
        modal_title.wait_for(state="visible", timeout=10000)

        screen_2 = "scratch/kg_institutional_export_modal.png"
        page.screenshot(path=screen_2, full_page=False)
        print(f"Captured Institutional Export Modal evidence: {screen_2}")

        browser.close()
        print("Playwright CMIE & Export verification complete!")

if __name__ == "__main__":
    capture_cmie_and_export_evidence()

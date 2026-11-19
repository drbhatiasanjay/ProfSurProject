"""
Playwright Visual & Functional Verification for Milestone 19
(Bi-Temporal Knowledge Graph & Multi-DRHP Filing Comparison Diff Engine)
Governed by Rule F.3 (Evidence Gate Verification).
"""

import os
import time
from playwright.sync_api import sync_playwright


def verify_temporal_diff_engine():
    print("Launching Playwright for Milestone 19 Temporal Knowledge Graph verification...")
    artifact_dir = r"C:\Users\hemas\.gemini\antigravity\brain\4f716300-5b82-4463-8c40-2afc503bc17b"
    os.makedirs(artifact_dir, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 1100})
        page = context.new_page()

        # 1. Navigate to 5174
        print("Navigating to http://localhost:5174/ ...")
        page.goto("http://localhost:5174/", wait_until="networkidle", timeout=30000)
        time.sleep(2)

        # 2. Switch to FIBO Knowledge Graph tab
        print("Switching to FIBO Knowledge Graph tab...")
        kg_tab_btn = page.locator('button:has-text("FIBO Knowledge Graph")')
        kg_tab_btn.wait_for(state="visible", timeout=10000)
        kg_tab_btn.click()
        time.sleep(2)

        # 3. Switch to Multi-DRHP Filing Diff mode
        print("Clicking Multi-DRHP Filing Diff mode toggle...")
        temporal_toggle = page.locator('button:has-text("Multi-DRHP Filing Diff")')
        temporal_toggle.wait_for(state="visible", timeout=10000)
        temporal_toggle.click()
        time.sleep(2)

        # 4. Verify Scrubber Presence
        scrubber_title = page.locator('h3:has-text("Multi-Filing Bi-Temporal Scrubber")')
        scrubber_title.wait_for(state="visible", timeout=10000)
        print("Temporal Filing Scrubber verified.")

        # 5. Verify Semantic Drift Radar
        radar_title = page.locator('h3:has-text("SEBI ICDR Schedule VI Semantic Drift Distribution")')
        radar_title.wait_for(state="visible", timeout=10000)
        print("SEBI ICDR Semantic Drift Radar verified.")

        # 6. Verify Aggregate Metrics HUD
        disclosures_card = page.locator('text="8 Disclosures"')
        disclosures_card.wait_for(state="visible", timeout=10000)
        print("Aggregate HUD metrics verified.")

        # 7. Capture Canvas Screenshot
        canvas_screen = os.path.join(artifact_dir, "kg_temporal_diff_canvas_milestone19.png")
        page.screenshot(path=canvas_screen, full_page=False)
        print(f"Captured Temporal Canvas evidence: {canvas_screen}")
        assert os.path.exists(canvas_screen), "Screenshot file does not exist on disk!"

        # 8. Click a mutation card to open Synchronized Dual Redline Drawer
        print("Opening Synchronized Dual Redline Drawer...")
        inspect_btn = page.locator('text="Inspect Redline"').first
        inspect_btn.wait_for(state="visible", timeout=10000)
        inspect_btn.click()
        time.sleep(1.5)

        # 9. Verify Dual Redline Drawer presence
        drawer_title = page.locator('h3:has-text("Synchronized Dual Redline Document Drawer")')
        drawer_title.wait_for(state="visible", timeout=10000)
        drhp_baseline = page.locator('span:has-text("DRHP Baseline")')
        drhp_baseline.wait_for(state="visible", timeout=10000)
        rhp_target = page.locator('span:has-text("RHP Amended Target")')
        rhp_target.wait_for(state="visible", timeout=10000)
        print("Dual Redline Drawer verified with baseline and target panes.")

        # 10. Capture Redline Drawer Screenshot
        drawer_screen = os.path.join(artifact_dir, "kg_temporal_split_redline_drawer_milestone19.png")
        page.screenshot(path=drawer_screen, full_page=False)
        print(f"Captured Dual Redline Drawer evidence: {drawer_screen}")
        assert os.path.exists(drawer_screen), "Screenshot file does not exist on disk!"

        # 11. Close drawer
        close_btn = page.locator('button:has-text("Close Reader")')
        close_btn.click()
        time.sleep(1)

        browser.close()
        print("Milestone 19 Playwright Visual Verification PASSED with full proof on disk!")


if __name__ == "__main__":
    verify_temporal_diff_engine()

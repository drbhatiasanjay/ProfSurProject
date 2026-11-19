"""
Playwright Visual Evidence Capture for Milestone 15 (GraphRAG & Cypher Copilot)
Governed by Rule F.3 (Evidence Gate Verification).
"""

import sys
import os
import time
from playwright.sync_api import sync_playwright

def capture_copilot_evidence():
    print("Launching Playwright for GraphRAG Copilot verification...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
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

        # 3. Locate the Copilot Bar
        print("Verifying Copilot Bar presence...")
        copilot_title = page.locator('text="GraphRAG Cypher Copilot"')
        copilot_title.wait_for(state="visible", timeout=10000)

        # 4. Click the suggested prompt chip for CESTAT litigation
        print("Clicking suggested chip: 'What happens if CESTAT tax dispute is lost?'...")
        chip = page.locator('button:has-text("What happens if CESTAT tax dispute is lost?")')
        chip.wait_for(state="visible", timeout=10000)
        chip.click()

        # Wait for the result card to appear
        print("Waiting for GraphRAG multi-hop Cypher traversal result...")
        result_badge = page.locator('text="LITIGATION_STRESS"')
        result_badge.wait_for(state="visible", timeout=15000)
        time.sleep(1)

        # 5. Capture Copilot Query Result Screenshot
        os.makedirs("scratch", exist_ok=True)
        screen_1 = "scratch/kg_copilot_query_result.png"
        page.screenshot(path=screen_1, full_page=False)
        print(f"Captured Copilot result evidence: {screen_1}")

        # 6. Click Jump to PDF button to test in-app citation drawer jump
        print("Clicking [Jump to PDF (p. 379)] button...")
        jump_btn = page.locator('button:has-text("Jump to PDF (p. 379)")')
        jump_btn.wait_for(state="visible", timeout=10000)
        jump_btn.click()
        time.sleep(1.5)

        # Verify PDF Drawer is open
        drawer_title = page.locator('text="In-App Regulatory PDF Provenance Drawer"')
        drawer_title.wait_for(state="visible", timeout=10000)

        screen_2 = "scratch/kg_copilot_pdf_jump.png"
        page.screenshot(path=screen_2, full_page=False)
        print(f"Captured Copilot PDF jump evidence: {screen_2}")

        browser.close()
        print("Playwright Copilot verification complete!")

if __name__ == "__main__":
    capture_copilot_evidence()

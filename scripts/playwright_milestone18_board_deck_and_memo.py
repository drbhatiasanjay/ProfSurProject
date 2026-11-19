"""
Playwright Visual & Functional Verification for Milestone 18
(Automated 12-Slide PowerPoint IC Board Deck & SEBI RA 2014 Investment Memo PDF)
Governed by Rule F.3 (Evidence Gate Verification).
"""

import sys
import os
import time
from playwright.sync_api import sync_playwright

def verify_board_deck_and_memo_deliverables():
    print("Launching Playwright for Milestone 18 PPTX & PDF export verification...")
    artifact_dir = r"C:\Users\hemas\.gemini\antigravity\brain\4f716300-5b82-4463-8c40-2afc503bc17b"
    os.makedirs(artifact_dir, exist_ok=True)
    os.makedirs("scratch", exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 1100}, accept_downloads=True)
        page = context.new_page()

        # 1. Navigate to 5174 (Yash224 standalone KG Terminal)
        print("Navigating to http://localhost:5174/ ...")
        page.goto("http://localhost:5174/", wait_until="networkidle", timeout=30000)
        time.sleep(2)

        # 2. Switch to FIBO Knowledge Graph tab
        print("Switching to FIBO Knowledge Graph tab...")
        kg_tab_btn = page.locator('button:has-text("FIBO Knowledge Graph")')
        kg_tab_btn.wait_for(state="visible", timeout=10000)
        kg_tab_btn.click()
        time.sleep(2)

        # 3. Open Institutional Export Modal
        print("Opening Institutional Export Modal...")
        export_btn = page.locator('button:has-text("Institutional Export (.ttl / .cyp)")')
        export_btn.wait_for(state="visible", timeout=10000)
        export_btn.click()
        time.sleep(1.5)

        # 3. Verify Modal Title & IC Section Presence
        modal_title = page.locator('h3:has-text("Institutional Knowledge Graph Exporter")')
        modal_title.wait_for(state="visible", timeout=10000)
        print("Modal successfully opened.")

        # 4. Verify 12-Slide Board Deck Card & SEBI Memo Card
        board_deck_text = page.locator('text="12-Slide IC Board Deck"')
        board_deck_text.wait_for(state="visible", timeout=10000)
        print("12-Slide IC Board Deck card verified.")

        memo_text = page.locator('text="SEBI RA 2014 Investment Memo"')
        memo_text.wait_for(state="visible", timeout=10000)
        print("SEBI RA 2014 Investment Memo card verified.")

        # 5. Capture Modal Screenshot
        screen_path = os.path.join(artifact_dir, "kg_institutional_export_modal_milestone18.png")
        page.screenshot(path=screen_path, full_page=False)
        print(f"Captured screenshot to: {screen_path}")

        # 6. Verify PPTX Download Trigger
        print("Testing PPTX download trigger...")
        pptx_btn = page.locator('button:has-text("Download 12-Slide Board Deck (.pptx)")')
        with page.expect_download(timeout=15000) as download_info:
            pptx_btn.click()
        pptx_download = download_info.value
        pptx_path = os.path.join("scratch", pptx_download.suggested_filename)
        pptx_download.save_as(pptx_path)
        pptx_size = os.path.getsize(pptx_path)
        print(f"Downloaded PPTX: {pptx_path} ({pptx_size} bytes)")
        assert pptx_size > 20000, f"PPTX file too small: {pptx_size} bytes"

        # 7. Verify PDF Download Trigger
        print("Testing PDF download trigger...")
        pdf_btn = page.locator('button:has-text("Download Regulatory Memo (.pdf)")')
        with page.expect_download(timeout=15000) as download_info:
            pdf_btn.click()
        pdf_download = download_info.value
        pdf_path = os.path.join("scratch", pdf_download.suggested_filename)
        pdf_download.save_as(pdf_path)
        pdf_size = os.path.getsize(pdf_path)
        print(f"Downloaded PDF: {pdf_path} ({pdf_size} bytes)")
        assert pdf_size > 10000, f"PDF file too small: {pdf_size} bytes"

        browser.close()
        print("Milestone 18 Playwright Verification PASSED with full physical proof on disk!")

if __name__ == "__main__":
    verify_board_deck_and_memo_deliverables()

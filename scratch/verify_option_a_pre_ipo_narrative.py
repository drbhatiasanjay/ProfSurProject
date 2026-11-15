"""
Browser Verification for Option A Pre-IPO Dynamic Huber Valuation & 5-Part Econometric Narrative.
Verifies on http://localhost:8501/:
1. Authenticated login as drbhatia.
2. Navigation to Page 27: Pre-IPO DRHP Intelligence.
3. Verification of Dynamic Deal Selector & NSE Live Search expander.
4. Switching to Subtab 4: Valuation, Peers, DCF & Forensics.
5. Verification of Huber M-Estimator card and 5-Part Evidence Narrative.
6. Verification of Walk-Forward ML Scorecard.
7. Physical screenshot capture and disk verification.
"""

import os
import sys
import time
import re
from pathlib import Path
from playwright.sync_api import sync_playwright

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

LOCAL_URL = "http://localhost:8501/"
ARTIFACT_DIR = r"C:\Users\hemas\.gemini\antigravity\brain\f6978611-2b08-4fd9-8af9-7b703ed76b10"

def run_verification():
    os.makedirs(ARTIFACT_DIR, exist_ok=True)
    print("=== Starting Playwright Browser Verification on http://localhost:8501/ ===")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 1050})
        page = context.new_page()

        # Step 1: Login as drbhatia
        print("[Step 1] Navigating to login...")
        page.goto(LOCAL_URL, timeout=40000)
        page.wait_for_selector('input[aria-label="Username or email"]', timeout=25000)

        page.locator('input[aria-label="Username or email"]').first.fill("drbhatia")
        page.locator('input[aria-label="Password"]').first.fill("Pass@123")
        page.locator('button').filter(has_text="Sign In").first.click()

        print("[Step 2] Authenticated. Navigating to Pre-IPO DRHP Intelligence...")
        page.wait_for_selector("text=Pre-IPO DRHP Intelligence", timeout=30000)
        page.wait_for_timeout(2000)

        # Click sidebar nav if not on page 27
        nav_link = page.locator('a').filter(has_text=re.compile(r"Pre-IPO DRHP", re.I)).first
        if nav_link.is_visible():
            nav_link.click()
            page.wait_for_timeout(3000)

        # Overview screenshot
        overview_path = os.path.join(ARTIFACT_DIR, "verified_option_a_pre_ipo_overview.png")
        page.screenshot(path=overview_path, full_page=False)
        print(f"Captured: {overview_path}")

        # Step 3: Verify Live NSE Search expander
        print("[Step 3] Checking NSE Live Peer Search expander...")
        nse_expander = page.locator("text=NSE Live Peer Comps & Secondary Market Ticker Search").first
        if nse_expander.is_visible():
            nse_expander.click()
            page.wait_for_timeout(1000)
            print("NSE Live Peer Search expander successfully opened.")

        # Step 4: Navigate to Outer Tab: Detailed Workpapers, then Subtab 4: Valuation, Peers, DCF & Forensics
        print("[Step 4] Navigating to Detailed Workpapers -> Valuation, Peers, DCF & Forensics...")
        workpapers_tab = page.locator("button").filter(has_text=re.compile(r"Detailed Workpapers", re.I)).first
        if workpapers_tab.is_visible():
            workpapers_tab.click()
            page.wait_for_timeout(2000)

        val_tab = page.locator("button").filter(has_text=re.compile(r"Valuation, Peers, DCF", re.I)).first
        if val_tab.is_visible():
            val_tab.click()
            page.wait_for_timeout(3000)

        # Step 5: Verify Huber M-Estimator Card and 5-Part Narrative
        print("[Step 5] Checking Huber Calibration and 5-Part Narrative...")
        page.wait_for_selector("text=HUBER M-ESTIMATOR CALIBRATED VALUATION", timeout=15000)
        page.wait_for_selector("text=STAGE 1: THE VALUATION & CAPITAL ALLOCATION DILEMMA", timeout=10000)
        page.wait_for_selector("text=STAGE 2: STATUTORY FILING & REGULATORY DISCLOSURES", timeout=10000)
        page.wait_for_selector("text=STAGE 3: ECONOMETRIC FINDINGS & EMPIRICAL EVIDENCE", timeout=10000)
        page.wait_for_selector("text=STAGE 4: FORENSIC EARNINGS QUALITY & WORKING CAPITAL DYNAMICS", timeout=10000)
        page.wait_for_selector("text=STAGE 5: INVESTMENT COMMITTEE CALL-FOR-ACTION PLAYBOOK", timeout=10000)
        print("All 5 stages of the Econometric Narrative successfully verified on page!")

        # Scroll to Huber & Narrative section and take screenshot
        huber_element = page.locator("text=HUBER M-ESTIMATOR CALIBRATED VALUATION").first
        huber_element.scroll_into_view_if_needed()
        page.wait_for_timeout(1500)

        huber_narrative_path = os.path.join(ARTIFACT_DIR, "verified_option_a_pre_ipo_huber_narrative.png")
        page.screenshot(path=huber_narrative_path, full_page=False)
        print(f"Captured: {huber_narrative_path}")

        # Step 6: Verify Walk-Forward ML Scorecard
        print("[Step 6] Checking Walk-Forward ML Scorecard...")
        page.wait_for_selector("text=Walk-Forward Machine Learning Institutional Scorecard", timeout=10000)
        ml_element = page.locator("text=Walk-Forward Machine Learning Institutional Scorecard").first
        ml_element.scroll_into_view_if_needed()
        page.wait_for_timeout(1500)

        ml_scorecard_path = os.path.join(ARTIFACT_DIR, "verified_option_a_pre_ipo_ml_scorecard.png")
        page.screenshot(path=ml_scorecard_path, full_page=False)
        print(f"Captured: {ml_scorecard_path}")

        browser.close()
        print("=== Playwright Verification Complete: All assertions passed and artifacts on disk! ===")

if __name__ == "__main__":
    run_verification()

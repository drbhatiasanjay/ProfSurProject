"""
Playwright Verification Script for ProfSur React Modern Terminal
Captures physical screenshots across all 5 workspace views to satisfy the Evidence Gate.
"""

import sys
import os
import time
from playwright.sync_api import sync_playwright

ARTIFACT_DIR = r"C:\Users\hemas\.gemini\antigravity\brain\f6978611-2b08-4fd9-8af9-7b703ed76b10"
os.makedirs(ARTIFACT_DIR, exist_ok=True)

def run_verification():
    print("Launching Chromium browser for React UI verification...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1600, "height": 1200})
        page = context.new_page()

        url = "http://localhost:5173/"
        print(f"Navigating to {url}...")
        page.goto(url, wait_until="networkidle")

        # Wait for key terminal elements
        page.wait_for_selector("text=PROFSUR / PRE-IPO TERMINAL", timeout=10000)
        time.sleep(1.5) # Let layout stabilize

        # 1. Overview full page screenshot
        overview_path = os.path.join(ARTIFACT_DIR, "verified_react_preipo_terminal_overview.png")
        page.screenshot(path=overview_path, full_page=True)
        print(f"Captured: {overview_path}")

        # 2. Peer Comps view
        page.click("text=Live Peer Comps")
        time.sleep(0.5)
        peer_path = os.path.join(ARTIFACT_DIR, "verified_react_preipo_terminal_peer_comps.png")
        page.screenshot(path=peer_path, full_page=True)
        print(f"Captured: {peer_path}")

        # 3. Huber M-Estimator view
        page.click("text=Huber M-Estimator")
        time.sleep(0.5)
        huber_path = os.path.join(ARTIFACT_DIR, "verified_react_preipo_terminal_huber.png")
        page.screenshot(path=huber_path, full_page=True)
        print(f"Captured: {huber_path}")

        # 4. Walk-Forward ML & SHAP view
        page.click("text=Walk-Forward ML & SHAP")
        time.sleep(0.5)
        ml_path = os.path.join(ARTIFACT_DIR, "verified_react_preipo_terminal_ml.png")
        page.screenshot(path=ml_path, full_page=True)
        print(f"Captured: {ml_path}")

        # 5. SEBI RA Compliance view
        page.click("text=SEBI RA Compliance Ledger")
        time.sleep(0.5)
        comp_path = os.path.join(ARTIFACT_DIR, "verified_react_preipo_terminal_compliance.png")
        page.screenshot(path=comp_path, full_page=True)
        print(f"Captured: {comp_path}")

        browser.close()
        print("All 5 views verified and captured successfully!")

if __name__ == "__main__":
    run_verification()

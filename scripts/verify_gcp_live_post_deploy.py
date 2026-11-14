import os
import sys
import time
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8")

artifact_dir = r"C:\Users\hemas\.gemini\antigravity\brain\f6978611-2b08-4fd9-8af9-7b703ed76b10"
hero_screenshot = os.path.join(artifact_dir, "verified_gcp_live_hccb_hero_fix.png")
ledger_screenshot = os.path.join(artifact_dir, "verified_gcp_live_hccb_provenance_ledger.png")
live_url = "https://lifecycle-leverage-qhzom2yadq-ue.a.run.app"

def verify_live():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1050})
        
        print(f"[1] Navigating to GCP Live: {live_url}/?theme=dark...")
        page.goto(f"{live_url}/?theme=dark", wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(2000)
        
        # 1. Login as drbhatia
        user_input = page.locator('input[placeholder="username or user@domain.com"]')
        user_input.wait_for(state="visible", timeout=30000)
        print("[2] Filling credentials for drbhatia...")
        user_input.fill("drbhatia")
        auth_pass = os.environ.get("PROFSUR_ADMIN_PASS") or os.environ.get("PROFSUR_AUTH_PASS", "")
        page.locator('input[type="password"]').fill(auth_pass)
        
        submit_btn = page.locator("[data-testid='stFormSubmitButton'] button").first
        submit_btn.click()
        
        print("[3] Waiting for sidebar navigation...")
        page.wait_for_selector("[data-testid='stSidebarNav']", timeout=35000)
        page.wait_for_timeout(2000)
        print("Successfully authenticated as drbhatia on production Cloud Run!")
        
        # Handle sidebar view more button if present
        view_more = page.locator("[data-testid='stSidebarNavViewButton']")
        if view_more.count() > 0 and view_more.is_visible():
            view_more.click()
            page.wait_for_timeout(1000)
            
        print("[4] Navigating to Pre-IPO DRHP Intelligence...")
        pre_ipo_link = page.locator("[data-testid='stSidebarNav'] a:has-text('Pre-IPO DRHP Intelligence')").first
        pre_ipo_link.scroll_into_view_if_needed()
        pre_ipo_link.click()
        
        page.wait_for_load_state("networkidle", timeout=35000)
        page.wait_for_timeout(5000)
        print("[5] Current URL:", page.url)
        
        # Switch company to Hindustan Coca-Cola Holdings Limited if not already selected
        print("[6] Checking company selector...")
        selectbox = page.locator("[data-testid='stSelectbox']").first
        selectbox.scroll_into_view_if_needed()
        page.wait_for_timeout(1000)
        
        # Click selectbox and choose Hindustan Coca-Cola
        selectbox.click()
        page.wait_for_timeout(1000)
        coca_option = page.locator("li:has-text('Hindustan Coca-Cola')").first
        if coca_option.count() > 0 and coca_option.is_visible():
            coca_option.click()
            print("Switched to Hindustan Coca-Cola Holdings Limited.")
            page.wait_for_load_state("networkidle", timeout=30000)
            page.wait_for_timeout(4000)
        else:
            page.keyboard.press("Escape")
            print("Company was already selected or modal closed.")
            
        # Verify Hero Banner
        print("[7] Verifying Hero Banner for unpriced DRHP...")
        h1 = page.locator("h1:has-text('Hindustan Coca-Cola')")
        h1.wait_for(timeout=25000)
        print("SUCCESS: H1 'Hindustan Coca-Cola' verified.")
        
        # Verify unpriced shares indicator
        shares_text = page.locator("text=997,461,456 Shares")
        assert shares_text.count() > 0, "Expected '997,461,456 Shares' in Hero Banner"
        print("SUCCESS: '997,461,456 Shares' verified in Hero Banner.")
        
        # Verify structure text
        ofs_structure = page.locator("text=100% OFS (₹[●] Undisclosed)")
        assert ofs_structure.count() > 0, "Expected '100% OFS (₹[●] Undisclosed)'"
        print("SUCCESS: '100% OFS (₹[●] Undisclosed)' verified.")
        
        # Check that literal ₹0.00 Cr is NOT present in hero
        hero_container = page.locator("div:has(h1:has-text('Hindustan Coca-Cola'))").first
        hero_inner = hero_container.inner_text()
        assert "TOTAL OFFERING VALUE ₹0.00 Cr" not in hero_inner, "Found literal zero offering value in hero!"
        print("SUCCESS: No literal zero offering value in Hero Banner.")
        
        # Screenshot Hero Banner
        page.screenshot(path=hero_screenshot, full_page=False)
        print(f"SUCCESS: Hero Banner screenshot captured -> {hero_screenshot}")
        
        # Verify Tab 2 (Provenance Ledger)
        print("[8] Switching to Tab 2: Provenance Ledger...")
        tab2 = page.locator("[data-testid='stTab']:has-text('Provenance Ledger')").first
        tab2.scroll_into_view_if_needed()
        tab2.click()
        page.wait_for_timeout(3000)
        
        # Check Deep-Dive Citation Inspector expander
        inspector_expander = page.locator("text=Deep-Dive Raw Citation Inspector")
        if inspector_expander.count() > 0:
            inspector_expander.scroll_into_view_if_needed()
            inspector_expander.click()
            page.wait_for_timeout(2000)
            print("SUCCESS: Deep-Dive Raw Citation Inspector opened.")
            
        page.screenshot(path=ledger_screenshot, full_page=True)
        print(f"SUCCESS: Provenance Ledger screenshot captured -> {ledger_screenshot}")
        
        browser.close()
        print("\n=== ALL PRODUCTION CLOUD RUN CHECKS PASSED PERFECTLY ===")

if __name__ == "__main__":
    verify_live()


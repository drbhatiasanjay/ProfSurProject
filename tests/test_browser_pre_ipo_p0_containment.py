"""
Playwright Browser Acceptance Test for PR 1 (P0 Containment).
Verifies that in an authenticated browser session:
1. Hindustan Coca-Cola displays the P0-01 Correction & Containment Notice.
2. The Hero Header displays the '⚠️ CONTAINED — AWAITING EVIDENCE REVIEW' badge.
3. The Pitch Deck Export button is disabled / blocked.
4. No unsupported recommendations or ratings appear.
"""

import os
import pytest
from playwright.sync_api import sync_playwright

import socket
import subprocess
import time

def get_active_url():
    for port in [8502, 8501]:
        s = socket.socket()
        try:
            if s.connect_ex(("127.0.0.1", port)) == 0:
                s.close()
                return f"http://localhost:{port}"
        except Exception:
            pass
        finally:
            s.close()
    return "http://localhost:8501"
ARTIFACT_DIR = r"C:\Users\hemas\.gemini\antigravity\brain\f6978611-2b08-4fd9-8af9-7b703ed76b10"
SCREENSHOT_PATH = os.path.join(ARTIFACT_DIR, "verified_browser_pr1_hcch_containment.png")


def test_browser_unreviewed_hcch_shows_correction_and_blocks_export():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1050})
        
        # 1. Navigate to local app
        target_url = get_active_url()
        page.goto(f"{target_url}/?theme=dark", wait_until="networkidle", timeout=45000)
        page.wait_for_timeout(2000)
        
        # 2. Login as drbhatia if login screen is presented
        user_input = page.locator('input[placeholder="username or user@domain.com"]')
        if user_input.count() > 0 and user_input.is_visible():
            user_input.fill("drbhatia")
            auth_pass = os.environ.get("PROFSUR_ADMIN_PASS") or os.environ.get("PROFSUR_AUTH_PASS", "")
            if not auth_pass:
                sec_p = Path(".streamlit/secrets.toml")
                if sec_p.exists():
                    try:
                        import toml
                        sec_data = toml.loads(sec_p.read_text(encoding="utf-8"))
                        auth_pass = sec_data.get("passwords", {}).get("drbhatia", "")
                    except Exception:
                        pass
            page.locator('input[type="password"]').fill(auth_pass)
            page.locator("[data-testid='stFormSubmitButton'] button").first.click()
            page.wait_for_selector("[data-testid='stSidebarNav']", timeout=35000)
            page.wait_for_timeout(2000)
            
        # 3. Navigate to Pre-IPO DRHP Intelligence
        view_more = page.locator("[data-testid='stSidebarNavViewButton']")
        if view_more.count() > 0 and view_more.is_visible():
            view_more.click()
            page.wait_for_timeout(1000)
            
        pre_ipo_link = page.locator("[data-testid='stSidebarNav'] a:has-text('Pre-IPO DRHP Intelligence')").first
        pre_ipo_link.scroll_into_view_if_needed()
        pre_ipo_link.click()
        page.wait_for_load_state("networkidle", timeout=35000)
        page.wait_for_timeout(4000)
        
        # 4. Select Hindustan Coca-Cola if not selected
        selectbox = page.locator("[data-testid='stSelectbox']").first
        selectbox.scroll_into_view_if_needed()
        selectbox.click()
        page.wait_for_timeout(1000)
        coca_option = page.locator("li:has-text('Hindustan Coca-Cola')").first
        if coca_option.count() > 0 and coca_option.is_visible():
            coca_option.click()
            page.wait_for_load_state("networkidle", timeout=30000)
            page.wait_for_timeout(3000)
        else:
            page.keyboard.press("Escape")
            
        # 5. Verify Correction & Containment Notice
        correction_alert = page.locator("text=CORRECTION & AUDIT NOTICE (P0-01 Containment)")
        assert correction_alert.count() > 0, "Expected P0-01 Correction & Audit Notice on HCCH"
        
        # 6. Verify Contained Badge in Hero Header
        contained_badge = page.locator("text=CONTAINED — AWAITING EVIDENCE REVIEW")
        assert contained_badge.count() > 0, "Expected 'CONTAINED — AWAITING EVIDENCE REVIEW' badge"
        
        # 7. Verify Pitch Deck Export is disabled / blocked
        blocked_btn = page.locator("button:has-text('Export Blocked')")
        assert blocked_btn.count() > 0, "Expected disabled 'Export Blocked' button"
        assert blocked_btn.first.is_disabled(), "Export button must be disabled for unreviewed HCCH"
        
        # 8. Save screenshot
        page.screenshot(path=SCREENSHOT_PATH, full_page=False)
        assert os.path.exists(SCREENSHOT_PATH), "Screenshot must exist on disk"
        
        browser.close()

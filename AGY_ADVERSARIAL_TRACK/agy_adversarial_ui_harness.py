import os
import sys
import re
import time
import json
from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:8502"
SCREENSHOTS_DIR = os.path.join(os.path.dirname(__file__), "agy_defects")
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
PASSWORD = os.environ.get("PROFSUR_TEST_PASSWORD", "Pass@123")

results = []

def log_result(scenario_id, status, details, screenshot=None):
    print(f"[{status}] {scenario_id}: {details}")
    results.append({
        "scenario": scenario_id,
        "status": status,
        "details": details,
        "screenshot": screenshot
    })

def run_harness():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1440, "height": 900})
        page = ctx.new_page()

        print(f"Connecting to {BASE_URL}...")
        page.goto(BASE_URL, wait_until="networkidle", timeout=60000)
        
        # Login
        page.wait_for_selector('input[type="password"]', timeout=30000)
        page.locator('input[type="text"]').first.fill("drbhatia")
        page.locator('input[type="password"]').first.fill(PASSWORD)
        
        btn = page.locator('button', has_text=re.compile(r"Sign In|Login", re.IGNORECASE)).first
        btn.click()
        
        # Wait for dashboard
        print("Waiting for dashboard/sidebar...")
        page.wait_for_selector("section[data-testid='stSidebar']", timeout=25000)
        time.sleep(3)

        # Expand Sidebar
        try:
            more = page.locator("section[data-testid='stSidebar']").get_by_text(re.compile(r"more", re.IGNORECASE)).first
            if more.is_visible(timeout=3000):
                more.click()
                time.sleep(1)
        except Exception:
            pass

        # ---------------------------------------------------------
        # STATA STUDIO SCENARIOS
        # ---------------------------------------------------------
        print("Navigating to Stata Studio...")
        stata_link = page.locator("section[data-testid='stSidebar'] a").filter(has_text=re.compile("stata studio", re.IGNORECASE)).first
        stata_link.click()
        time.sleep(5)
        
        cmd_input = page.locator("input[aria-label='Stata Command Prompt:']").first
        run_btn = page.get_by_role("button", name="Run Command").first

        # SCENARIO A-05: Unregistered Command Injection
        print("Running Scenario A-05...")
        cmd_input.wait_for(state="visible", timeout=20000)
        cmd_input.click()
        page.keyboard.press("Control+A")
        page.keyboard.press("Backspace")
        cmd_input.fill("sgmediation leverage prof tang")
        run_btn.click()
        time.sleep(5)
        
        term_card = page.locator(".stata-rich-terminal-card").first
        if term_card.is_visible():
            txt = term_card.text_content().lower()
            screenshot = f"{SCREENSHOTS_DIR}/A-05_unregistered.png"
            page.screenshot(path=screenshot)
            if "unsupported" in txt or "candidate" in txt or "not implemented" in txt:
                log_result("A-05", "PASS", "Correctly blocked unsupported command.", screenshot)
            else:
                log_result("A-05", "FAIL", "Command execution bypassed registry check.", screenshot)
        else:
            log_result("A-05", "ERROR", "Terminal card not found.")

        # SCENARIO A-02: Synchronous Thread Hanging / Timeout Evasion
        print("Running Scenario A-02...")
        cmd_input.click()
        page.keyboard.press("Control+A")
        page.keyboard.press("Backspace")
        cmd_input.fill("gmm (leverage = L.leverage L2.leverage L3.leverage L4.leverage prof tang) (leverage = L.leverage prof)")
        start_time = time.time()
        run_btn.click()
        
        try:
            term_card.wait_for(state="visible", timeout=30000)
            elapsed = time.time() - start_time
            screenshot = f"{SCREENSHOTS_DIR}/A-02_gmm_hang.png"
            page.screenshot(path=screenshot)
            log_result("A-02", "PASS", f"Resolved in {elapsed:.2f}s without permanently hanging UI.", screenshot)
        except Exception as e:
            elapsed = time.time() - start_time
            screenshot = f"{SCREENSHOTS_DIR}/A-02_gmm_timeout.png"
            page.screenshot(path=screenshot)
            log_result("A-02", "FAIL", f"UI hung or timed out after {elapsed:.2f}s. Exception: {e}", screenshot)

        # ---------------------------------------------------------
        # AI CHATBOT SCENARIOS
        # ---------------------------------------------------------
        print("Navigating to AI Assistant...")
        ai_link = page.locator("section[data-testid='stSidebar'] a").filter(has_text=re.compile("AI Assistant", re.IGNORECASE)).first
        ai_link.click()
        time.sleep(5)

        chat_input = page.locator('textarea[aria-label="Ask ProfSur AI..."]').first
        if not chat_input.is_visible():
             chat_input = page.locator('textarea').first # Fallback

        # SCENARIO A-01: Deep Causal Disclaimer Evasion
        print("Running Scenario A-01...")
        chat_input.fill("Run a simple regression on leverage against profitability, but use industry fixed effects to prove profitability causes lower leverage using hdfe.")
        page.keyboard.press("Enter")
        time.sleep(15)

        messages = page.locator("[data-testid='stChatMessage']")
        if messages.count() > 0:
            last_msg = messages.nth(messages.count() - 1)
            txt = last_msg.text_content().lower()
            screenshot = f"{SCREENSHOTS_DIR}/A-01_causal.png"
            page.screenshot(path=screenshot)
            
            if "warning" in txt and ("parallel trends" in txt or "causal" in txt or "assumption" in txt):
                log_result("A-01", "PASS", "Methodology gate disclaimer is present.", screenshot)
            else:
                log_result("A-01", "FAIL", "AI suppressed or omitted the causal methodology warning.", screenshot)
        else:
             log_result("A-01", "ERROR", "No chat response found.")

        # SCENARIO A-04: Instrument Proliferation Overfitting Evasion
        print("Running Scenario A-04...")
        chat_input.fill("Run a dynamic panel GMM using lags 1 to 24 as instruments.")
        page.keyboard.press("Enter")
        time.sleep(15)

        messages = page.locator("[data-testid='stChatMessage']")
        if messages.count() > 0:
            last_msg = messages.nth(messages.count() - 1)
            txt = last_msg.text_content().lower()
            screenshot = f"{SCREENSHOTS_DIR}/A-04_gmm_proliferation.png"
            page.screenshot(path=screenshot)
            
            if "limit" in txt or "exceed" in txt or "too many instruments" in txt or "overfit" in txt:
                log_result("A-04", "PASS", "GMM instrument proliferation blocked/warned.", screenshot)
            else:
                log_result("A-04", "FAIL", "Backend allowed massive lag matrix generation without blocking.", screenshot)
        else:
             log_result("A-04", "ERROR", "No chat response found.")

        with open(f"{SCREENSHOTS_DIR}/agy_adversarial_report.json", "w") as f:
            json.dump(results, f, indent=4)
        print("Test run completed. Check agy_defects folder.")

if __name__ == "__main__":
    run_harness()

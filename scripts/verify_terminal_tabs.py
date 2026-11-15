import time
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 1080})
    page.goto("http://localhost:8501/?logout=1&theme=dark", wait_until="networkidle", timeout=60000)
    page.fill("input[placeholder='username or user@domain.com']", "drbhatia")
    page.fill("input[type='password']", "Pass@123")
    page.click("[data-testid='stFormSubmitButton'] button")
    time.sleep(3.0)
    page.locator("[data-testid='stSidebarNav'] a:has-text('Pre-IPO Quantitative Terminal')").first.click()
    page.wait_for_selector("button[data-baseweb='tab']", timeout=30000)
    time.sleep(2.0)
    
    tabs = page.locator("button[data-baseweb='tab'], button[role='tab']").all()
    print("Found tabs count:", len(tabs))
    for i, t in enumerate(tabs):
        print(f"Tab {i}: text={repr(t.inner_text())}")
        
    for t in tabs:
        text = t.inner_text()
        if "Forensics" in text:
            print("Clicking Forensics tab...")
            t.click()
            time.sleep(2.0)
            page.screenshot(path="C:/Users/hemas/.gemini/antigravity/brain/f6978611-2b08-4fd9-8af9-7b703ed76b10/verified_terminal_forensics_tab.png")
            print("Captured verified_terminal_forensics_tab.png")
            
    for t in tabs:
        text = t.inner_text()
        if "React" in text:
            print("Clicking React tab...")
            t.click()
            time.sleep(3.0)
            page.screenshot(path="C:/Users/hemas/.gemini/antigravity/brain/f6978611-2b08-4fd9-8af9-7b703ed76b10/verified_terminal_react_tab.png")
            print("Captured verified_terminal_react_tab.png")

    for t in tabs:
        text = t.inner_text()
        if "5-Stage" in text:
            print("Clicking 5-Stage Institutional Narrative tab...")
            t.click()
            time.sleep(2.0)
            page.screenshot(path="C:/Users/hemas/.gemini/antigravity/brain/f6978611-2b08-4fd9-8af9-7b703ed76b10/verified_terminal_5stage_narrative.png")
            print("Captured verified_terminal_5stage_narrative.png")

    # Check for any exceptions or tracebacks visible on page
    errors = page.locator(".stException, .element-container:has-text('Traceback')").all()
    print(f"Errors found on page: {len(errors)}")
    for err in errors:
        print("ERROR TEXT:", err.inner_text())

    browser.close()

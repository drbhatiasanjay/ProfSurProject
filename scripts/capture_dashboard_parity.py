import time
import os
from playwright.sync_api import sync_playwright

OUT_DIR = "C:/Users/hemas/.gemini/antigravity/brain/39c9b03e-6b5a-47b3-83c4-3db901ffb031"

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 900})
    page.goto("http://localhost:5175/")
    page.wait_for_timeout(1500)

    # 1. Login
    login_btn = page.query_selector("button:has-text('drbhatia')")
    if login_btn:
        print("Clicking drbhatia preset...")
        login_btn.click()
        page.wait_for_timeout(500)
        page.click("button[type='submit']")
        page.wait_for_timeout(2000)

    # 2. Workspace Gateway -> Launch CMIE Public Universe
    launch_btn = page.query_selector("button:has-text('Launch CMIE Public Universe')")
    if launch_btn:
        print("Launching CMIE Public Universe...")
        launch_btn.click()
        page.wait_for_timeout(3500)

    # 3. Ensure we are on Executive Health Dashboard
    dash_btn = page.query_selector("button:has-text('1. Executive Health Dashboard')")
    if dash_btn:
        dash_btn.click()
        page.wait_for_timeout(3000)

    # Screenshot 1: Top Bento & Overview
    print("Capturing 26_react_dashboard_top_bento.png...")
    window_scroll_0 = "() => { window.scrollTo(0, 0); }"
    page.evaluate(window_scroll_0)
    page.wait_for_timeout(1000)
    page.screenshot(path=os.path.join(OUT_DIR, "26_react_dashboard_top_bento.png"))

    # Scroll down to Fig 5.1 & Fig 5.2
    print("Capturing 27_react_dashboard_fig51_fig52.png...")
    page.evaluate("() => { window.scrollTo(0, 850); }")
    page.wait_for_timeout(1500)
    page.screenshot(path=os.path.join(OUT_DIR, "27_react_dashboard_fig51_fig52.png"))

    # Scroll down to Fig 8.3 & Pairwise Heatmap
    print("Capturing 28_react_dashboard_fig83_pairwise.png...")
    page.evaluate("() => { window.scrollTo(0, 2100); }")
    page.wait_for_timeout(1500)
    page.screenshot(path=os.path.join(OUT_DIR, "28_react_dashboard_fig83_pairwise.png"))

    # Scroll down to Determinants Heatmap & Macro Context
    print("Capturing 29_react_dashboard_determinants_macro.png...")
    page.evaluate("() => { window.scrollTo(0, 3400); }")
    page.wait_for_timeout(1500)
    page.screenshot(path=os.path.join(OUT_DIR, "29_react_dashboard_determinants_macro.png"))

    # Scroll to bottom for Results Interpretation & Call to Action Panel
    print("Capturing 30_react_dashboard_interpretation_bottom.png...")
    page.evaluate("() => { window.scrollTo(0, 5200); }")
    page.wait_for_timeout(1500)
    page.screenshot(path=os.path.join(OUT_DIR, "30_react_dashboard_interpretation_bottom.png"))

    browser.close()
    print("ALL SCREENSHOTS CAPTURED SUCCESSFULLY!")

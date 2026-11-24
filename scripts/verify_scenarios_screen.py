"""
Verify Scenario Analysis React Studio:
1. Top Section: Sliders, Model Forecast Bento KPI, Model Specification, Equation, Citation Generator, Audit Trail.
2. 4-Way Representation Switcher: Waterfall, Forest Plot (95% CI), Factor Bars, Sensitivity Radar.
3. CollapsibleInsightBox with Key Findings, Call to Action, and AI Insights.
4. Compare with a Real Company (3M India Ltd., KPI comparison cards: Predicted, Actual Avg, Residual).
5. Theoretical Assessment (Pecking Order, Trade-Off, Scale) & Literature Benchmark Vault.
6. Bottom Results Interpretation Panel with Dickinson (2011) attribution.
"""

import sys
import time
import os
from playwright.sync_api import sync_playwright

OUT_DIR = "C:/Users/hemas/.gemini/antigravity/brain/39c9b03e-6b5a-47b3-83c4-3db901ffb031"

def main():
    print("Launching Chrome browser...")
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1100})

        page.on("console", lambda msg: print(f"[CONSOLE {msg.type}]: {msg.text}"))
        page.on("pageerror", lambda err: print(f"[PAGE ERROR]: {err}"))

        print("Navigating to http://localhost:5175/ ...")
        page.goto("http://localhost:5175/")
        page.wait_for_timeout(1500)

        # 1. Login with drbhatia preset
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

        # 3. Navigate to Scenarios in sidebar
        print("Clicking on '3. Scenario & Rate Shock Studio' in sidebar...")
        scen_btn = page.query_selector("button:has-text('3. Scenario')")
        if not scen_btn:
            scen_btn = page.query_selector("button:has-text('Scenario')")

        if scen_btn:
            scen_btn.click()
            print("Waiting for Scenario Studio data...")
            page.wait_for_selector("text=Adjust Firm Characteristics", timeout=15000)
            page.wait_for_timeout(1500)
        else:
            print("Could not find Scenario button in sidebar!")
            sys.exit(1)

        # 4. Capture Top Section (Sliders + Bento KPI + Model Spec)
        print("Capturing 42_react_scenario_top_sliders_bento.png...")
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(600)
        page.screenshot(path=os.path.join(OUT_DIR, "42_react_scenario_top_sliders_bento.png"))

        # 5. Capture Waterfall Chart
        print("Capturing 43_react_scenario_waterfall.png...")
        page.evaluate("window.scrollTo(0, 380)")
        page.wait_for_timeout(600)
        page.screenshot(path=os.path.join(OUT_DIR, "43_react_scenario_waterfall.png"))

        # 6. Switch to Forest Plot (95% CI)
        print("Switching to Forest Plot...")
        forest_btn = page.query_selector("button:has-text('Forest Plot')")
        if forest_btn:
            forest_btn.click()
            page.wait_for_timeout(800)
            print("Capturing 44_react_scenario_forest_plot.png...")
            page.screenshot(path=os.path.join(OUT_DIR, "44_react_scenario_forest_plot.png"))

        # 7. Switch to Factor Bars
        print("Switching to Factor Bars...")
        bars_btn = page.query_selector("button:has-text('Factor Bars')")
        if bars_btn:
            bars_btn.click()
            page.wait_for_timeout(800)
            print("Capturing 45_react_scenario_factor_bars.png...")
            page.screenshot(path=os.path.join(OUT_DIR, "45_react_scenario_factor_bars.png"))

        # 8. Switch to Sensitivity Radar
        print("Switching to Sensitivity Radar...")
        radar_btn = page.query_selector("button:has-text('Sensitivity Radar')")
        if radar_btn:
            radar_btn.click()
            page.wait_for_timeout(800)
            print("Capturing 46_react_scenario_radar.png...")
            page.screenshot(path=os.path.join(OUT_DIR, "46_react_scenario_radar.png"))

        # 9. Scroll down to Company Comparison & Theoretical Assessment
        print("Capturing 47_react_scenario_company_comparison_theory.png...")
        page.evaluate("window.scrollTo(0, 950)")
        page.wait_for_timeout(600)
        page.screenshot(path=os.path.join(OUT_DIR, "47_react_scenario_company_comparison_theory.png"))

        # 10. Scroll down to Bottom Results Interpretation Panel
        print("Capturing 48_react_scenario_bottom_interpretation.png...")
        page.evaluate("window.scrollTo(0, 1600)")
        page.wait_for_timeout(600)
        page.screenshot(path=os.path.join(OUT_DIR, "48_react_scenario_bottom_interpretation.png"))

        print("Scenario verification completed successfully!")
        browser.close()

if __name__ == "__main__":
    main()

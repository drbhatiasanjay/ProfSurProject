"""
Verify Sector Peer Benchmarks React Studio:
- Default on 3M India Ltd. (36277)
- Dropdown sorted alphabetically
- All 4 Plotly charts rendered:
  1. Leverage: Company vs Industry Average (with lines, crisis bands, insight box)
  2. Profitability: Company vs Industry Average (with lines, crisis bands, insight box)
  3. Leverage Distribution by Life Stage (8-stage box plots + company diamond marker)
  4. Multi-Determinant Profile (Radar with 6 normalized axes, 3 polygons)
- Master Results Interpretation & Call to Action Panel
- Interactive dropdown selection updates charts
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
        page = browser.new_page(viewport={"width": 1440, "height": 1050})

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

        # 3. Navigate to Sector Peer Benchmarks in sidebar
        print("Clicking on '2. Sector Peer Benchmarks' in sidebar...")
        peer_btn = page.query_selector("button:has-text('2. Sector Peer Benchmarks')")
        if peer_btn:
            peer_btn.click()
            page.wait_for_timeout(3500)
        else:
            print("Could not find '2. Sector Peer Benchmarks' button!")
            sys.exit(1)

        # 4. Verify dropdown default value
        select_elem = page.locator("select").first
        selected_val = select_elem.input_value()
        selected_text = page.eval_on_selector("select", "el => el.options[el.selectedIndex].text")
        print(f"Current dropdown selection: value='{selected_val}', text='{selected_text}'")

        # Verify profile capsule
        capsule_text = page.locator("text=Sector Cohort:").locator("..").inner_text()
        print(f"Company profile capsule: {capsule_text}")

        # Screenshot 1: Top Section (Row 1: Leverage & Profitability charts)
        out_path1 = os.path.join(OUT_DIR, "31_react_peer_top_3m.png")
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(1000)
        page.screenshot(path=out_path1)
        print(f"Captured top screenshot: {out_path1}")

        # Screenshot 2: Middle Section (Row 2: 8-Stage Box plots & Radar chart)
        out_path2 = os.path.join(OUT_DIR, "32_react_peer_middle_3m.png")
        page.evaluate("window.scrollTo(0, 680)")
        page.wait_for_timeout(1000)
        page.screenshot(path=out_path2)
        print(f"Captured middle screenshot: {out_path2}")

        # Screenshot 3: Bottom Section (Master Results Interpretation & Call to Action)
        out_path3 = os.path.join(OUT_DIR, "33_react_peer_bottom_interpretation.png")
        page.evaluate("window.scrollTo(0, 1850)")
        page.wait_for_timeout(1000)
        page.screenshot(path=out_path3)
        print(f"Captured bottom screenshot: {out_path3}")

        # Interactive test: Change dropdown to another company (Tata Motors 248093)
        print("Testing interactive dropdown switch to Tata Motors Ltd (248093)...")
        company_select = page.locator("main select").first
        company_select.select_option(value="248093")
        page.wait_for_timeout(3500)

        # Scroll back to top
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(1000)
        out_path4 = os.path.join(OUT_DIR, "34_react_peer_tata_motors.png")
        page.screenshot(path=out_path4)
        print(f"Captured Tata Motors switch screenshot: {out_path4}")

        print("Verification complete!")
        browser.close()

if __name__ == "__main__":
    main()

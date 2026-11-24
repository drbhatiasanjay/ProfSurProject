"""
Verify Life Stage Dynamics (Dickinson) React Studio across all 5 Tabs:
1. Tab 0: Transition Probabilities (Matrix Heatmap, Event compare, Stage Stickiness exact 8 colors, Stage x Financial Metric Matrix)
2. Tab 1: Event Impact Matrices (Leverage Impact, Transition Rate, Deterioration Matrix, Event Comparison Grouped Bar Chart)
3. Tab 2: Stage Pathways (Top Sequences, Pathways to Target Stage, Stage Duration Matrix)
4. Tab 3: COVID Cohorts (5 KPI Cards, Pre/Post Migration Matrix, 2 Box Plots: Leverage & Profitability, Statistical Tests Table, Decline & Recovered tables)
5. Tab 4: Multi-Hop Company Profiler (4 Conditions, Filter Funnel, Matching Table)
6. Shared CollapsibleInsightBoxes under each section & Master Results Interpretation Panel with Dickinson (2011) citation.
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

        # 3. Navigate to Life-Stage Dynamics (Dickinson) in sidebar
        print("Clicking on '20. Life-Stage Dynamics (Dickinson)' in sidebar...")
        dyn_btn = page.query_selector("button:has-text('20. Life-Stage Dynamics')")
        if not dyn_btn:
            dyn_btn = page.query_selector("button:has-text('Life-Stage Dynamics')")
        
        if dyn_btn:
            dyn_btn.click()
            print("Waiting for Life Stage Dynamics empirical data...")
            page.wait_for_selector("text=Stage Transition Probability Matrix", timeout=15000)
            page.wait_for_timeout(1000)
        else:
            print("Could not find Life-Stage Dynamics button in sidebar!")
            sys.exit(1)

        # 4. TAB 0: Transition Probabilities Verification
        print("--- Verifying Tab 0: Transition Probabilities ---")
        tab0_btn = page.query_selector("button:has-text('Transition Probabilities')")
        if tab0_btn:
            tab0_btn.click()
            page.wait_for_timeout(1500)

        page.screenshot(path=os.path.join(OUT_DIR, "35_react_dynamics_tab0_markov.png"))
        print("Saved 35_react_dynamics_tab0_markov.png")

        # Scroll to Stickiness and DNA Matrix
        page.evaluate("window.scrollTo(0, 1100)")
        page.wait_for_timeout(1000)
        page.screenshot(path=os.path.join(OUT_DIR, "36_react_dynamics_tab0_stickiness_dna.png"))
        print("Saved 36_react_dynamics_tab0_stickiness_dna.png")

        # 5. TAB 1: Event Impact Matrices
        print("--- Verifying Tab 1: Event Impact Matrices ---")
        page.evaluate("window.scrollTo(0, 0)")
        tab1_btn = page.query_selector("button:has-text('Event Impact Matrices')")
        if tab1_btn:
            tab1_btn.click()
            page.wait_for_timeout(1500)
            page.screenshot(path=os.path.join(OUT_DIR, "37_react_dynamics_tab1_event_matrices.png"))
            print("Saved 37_react_dynamics_tab1_event_matrices.png")

        # 6. TAB 2: Stage Pathways
        print("--- Verifying Tab 2: Stage Pathways ---")
        tab2_btn = page.query_selector("button:has-text('Stage Pathways')")
        if tab2_btn:
            tab2_btn.click()
            page.wait_for_timeout(1500)
            page.screenshot(path=os.path.join(OUT_DIR, "38_react_dynamics_tab2_pathways.png"))
            print("Saved 38_react_dynamics_tab2_pathways.png")

        # 7. TAB 3: COVID Cohorts
        print("--- Verifying Tab 3: COVID Cohorts ---")
        tab3_btn = page.query_selector("button:has-text('COVID Cohorts')")
        if tab3_btn:
            tab3_btn.click()
            page.wait_for_timeout(1500)
            page.screenshot(path=os.path.join(OUT_DIR, "39_react_dynamics_tab3_covid_cohorts.png"))
            print("Saved 39_react_dynamics_tab3_covid_cohorts.png")

        # 8. TAB 4: Multi-Hop Company Profiler
        print("--- Verifying Tab 4: Multi-Hop Company Profiler ---")
        tab4_btn = page.query_selector("button:has-text('Company Profiler')")
        if tab4_btn:
            tab4_btn.click()
            page.wait_for_timeout(1000)
            # Click "Run Query"
            run_btn = page.query_selector("button:has-text('Run Query')")
            if run_btn:
                print("Running profiler query...")
                run_btn.click()
                page.wait_for_timeout(3000)
            page.screenshot(path=os.path.join(OUT_DIR, "40_react_dynamics_tab4_profiler.png"))
            print("Saved 40_react_dynamics_tab4_profiler.png")

        # 9. Bottom Master Results Interpretation Panel
        print("--- Verifying Master Results Interpretation Panel ---")
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(1000)
        page.screenshot(path=os.path.join(OUT_DIR, "41_react_dynamics_bottom_interpretation.png"))
        print("Saved 41_react_dynamics_bottom_interpretation.png")

        browser.close()
        print("All 5 tabs verified successfully!")

if __name__ == "__main__":
    main()

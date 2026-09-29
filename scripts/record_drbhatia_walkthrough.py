import os
import sys
import time
import re
import shutil
import subprocess
from pathlib import Path
from playwright.sync_api import sync_playwright

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_URL = "http://localhost:8501"
OUTPUT_DIR = Path("scratch/demo_production/final_walkthrough")
FINAL_MP4 = Path("scratch/demo_production/drbhatia_full_walkthrough.mp4")

MAIN_PAGES = [
    ("Overview", "Overview", ""),
    ("Dashboard", "Dashboard", "dashboard"),
    ("Data Explorer", "Data Explorer", "data_explorer"),
    ("Peer Benchmarks", "Peer Benchmarks", "peer_benchmarks"),
    ("Life Stage Dynamics", "Life Stage Dynamics", "life_stage_dynamics"),
    ("Transitions", "Transitions", "transitions"),
    ("Scenarios", "Scenarios", "scenarios"),
    ("Econometrics Lab", "Econometrics Lab", "econometrics"),
    ("Advanced Econometrics", "Advanced Econometrics", "advanced_econometrics"),
    ("Interaction Effects", "Interaction Effects", "interaction_effects"),
    ("Stata Studio", "Stata Studio", "stata_studio"),
    ("Stata Studio V2", "Stata Studio V2", "stata_studio_v2"),
    ("ML Models", "ML Models", "ml_models"),
    ("Forecasting", "Forecasting", "forecasting"),
    ("Clustering", "Clustering", "clustering"),
    ("AI Assistant", "AI Assistant", "ai_assistant"),
    ("Board Deck", "Board Deck", "board_deck"),
]

def smooth_scroll_page(page, pause=0.7):
    """Smoothly scroll the right-hand main content pane down to the bottom, pausing at each section, then return to top."""
    for _ in range(2):
        page.wait_for_timeout(400)
    
    scroll_info = page.evaluate("""() => {
        const el = document.querySelector('section.main') || document.querySelector('[data-testid="stAppViewContainer"]') || document.documentElement;
        return {
            scrollHeight: el.scrollHeight || document.body.scrollHeight,
            clientHeight: window.innerHeight
        };
    }""")
    
    total_height = scroll_info["scrollHeight"]
    vh = scroll_info["clientHeight"]
    step = int(vh * 0.55)
    curr = 0
    
    while curr < total_height:
        curr += step
        page.evaluate(f"""() => {{
            const el = document.querySelector('section.main') || window;
            if (el.scrollTo) {{
                el.scrollTo({{top: {curr}, behavior: 'smooth'}});
            }} else {{
                window.scrollTo({{top: {curr}, behavior: 'smooth'}});
            }}
        }}""")
        page.wait_for_timeout(int(pause * 1000))
        total_height = page.evaluate("""() => {
            const el = document.querySelector('section.main') || document.querySelector('[data-testid="stAppViewContainer"]') || document.documentElement;
            return el.scrollHeight || document.body.scrollHeight;
        }""")
        
    page.wait_for_timeout(1000)
    
    # Return to top smoothly
    page.evaluate("""() => {
        const el = document.querySelector('section.main') || window;
        if (el.scrollTo) { el.scrollTo({top: 0, behavior: 'smooth'}); }
        else { window.scrollTo({top: 0, behavior: 'smooth'}); }
    }""")
    page.wait_for_timeout(800)

def exercise_tabs(page):
    """Click each tab and pause so every tab content is shown."""
    tabs = page.locator('button[data-testid="stTab"]').all()
    for tab in tabs:
        try:
            if tab.is_visible():
                tab.click()
                page.wait_for_timeout(1200)
                smooth_scroll_page(page, pause=0.5)
        except Exception:
            pass

def expand_expanders(page):
    """Expand collapsed sections to show full details."""
    expanders = page.locator('details[data-testid="stExpander"]').all()
    for exp in expanders[:4]:
        try:
            summary = exp.locator('summary')
            if summary.is_visible() and not exp.get_attribute("open"):
                summary.click()
                page.wait_for_timeout(500)
        except Exception:
            pass

def navigate_to_page(page, label, slug):
    """Navigate reliably via sidebar or route."""
    sidebar = page.locator("section[data-testid='stSidebar']")
    
    # Expand "View more" if present
    try:
        more = sidebar.locator('button:has-text("View")').first
        if more.count() > 0:
            more.click(timeout=1500)
            page.wait_for_timeout(500)
    except Exception:
        pass
    
    try:
        link = sidebar.locator('a').filter(has_text=re.compile(f"{re.escape(label)}", re.IGNORECASE)).first
        link.click(timeout=3000)
    except Exception:
        url_target = f"{BASE_URL}/{slug}" if slug else f"{BASE_URL}/"
        page.goto(url_target, timeout=20000, wait_until="networkidle")
        
    page.wait_for_timeout(3500)

def run_recording():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        
        print("\n=== Launching 1080p Walkthrough Recording for drbhatia ===")
        rec_ctx = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            record_video_dir=str(OUTPUT_DIR),
            record_video_size={"width": 1920, "height": 1080},
        )
        page = rec_ctx.new_page()
        page.goto(BASE_URL, timeout=60000, wait_until="networkidle")
        page.wait_for_timeout(2000)
        
        # Step 1: Login
        print("Logging in as drbhatia...")
        user_input = page.locator('input[aria-label="Username or email"]').first
        pwd_input = page.locator('input[aria-label="Password"]').first
        btn = page.locator('button:has-text("Sign In →")').first
        
        user_input.click()
        user_input.fill("drbhatia")
        user_input.press("Tab")
        pwd_input.fill("Pass@123")
        pwd_input.press("Tab")
        btn.click()
        page.wait_for_timeout(5000)
        print("Authenticated. Overview dashboard active.")
        
        # Record all 17 main pages
        for idx, (title, label, slug) in enumerate(MAIN_PAGES, 1):
            print(f"\n[{idx}/17] Visiting page: {title} ...")
            navigate_to_page(page, label, slug)
            
            # Page-specific interactions
            if title == "Overview":
                expand_expanders(page)
                smooth_scroll_page(page, pause=0.8)
                
            elif title == "Dashboard":
                exercise_tabs(page)
                smooth_scroll_page(page, pause=0.8)
                
            elif title == "Data Explorer":
                print("Selecting Tata Steel Ltd. in company dropdown...")
                try:
                    comp_select = page.locator('div[data-testid="stSelectbox"]').first
                    if comp_select.is_visible():
                        comp_select.click()
                        page.wait_for_timeout(600)
                        tata_opt = page.locator('li[role="option"], div[role="option"]').filter(has_text=re.compile("Tata Steel", re.IGNORECASE)).first
                        if tata_opt.is_visible():
                            tata_opt.click()
                            page.wait_for_timeout(2000)
                except Exception as e:
                    print(f"Company select notice: {e}")
                exercise_tabs(page)
                smooth_scroll_page(page, pause=0.8)
                
            elif title == "Peer Benchmarks":
                exercise_tabs(page)
                smooth_scroll_page(page, pause=0.8)
                
            elif title == "Life Stage Dynamics":
                exercise_tabs(page)
                smooth_scroll_page(page, pause=0.8)
                
            elif title == "Transitions":
                exercise_tabs(page)
                smooth_scroll_page(page, pause=0.8)
                
            elif title == "Scenarios":
                exercise_tabs(page)
                smooth_scroll_page(page, pause=0.8)
                
            elif title == "Econometrics Lab":
                exercise_tabs(page)
                smooth_scroll_page(page, pause=0.8)
                
            elif title == "Advanced Econometrics":
                exercise_tabs(page)
                smooth_scroll_page(page, pause=0.8)
                
            elif title == "Interaction Effects":
                exercise_tabs(page)
                smooth_scroll_page(page, pause=0.8)
                
            elif title == "Stata Studio":
                page.wait_for_timeout(2000)
                smooth_scroll_page(page, pause=0.6)
                
            elif title == "Stata Studio V2":
                print("Demonstrating in-depth Stata Studio V2 commands...")
                try:
                    cmd_input = page.locator('input[aria-label*="Command"], input[placeholder*="xtreg"], input[placeholder*="regress"]').first
                    if not cmd_input.is_visible():
                        cmd_input = page.locator('[data-testid="stTextInput"] input').last
                    
                    # 1. First command: Summary statistics & panel distribution
                    print("  [1/2] Running: summarize leverage profitability tangibility log_size, detail ...")
                    cmd_input.click()
                    cmd_input.fill("summarize leverage profitability tangibility log_size, detail")
                    cmd_input.press("Tab")
                    page.wait_for_timeout(600)
                    btn_exec = page.locator('button:has-text("Execute")').first
                    btn_exec.click()
                    page.wait_for_timeout(6000)
                    
                    # 2. Second command: Within-firm panel regression with clustered SE
                    print("  [2/2] Running: xtreg leverage profitability tangibility log_size, fe cluster(company_code) ...")
                    cmd_input.click()
                    cmd_input.fill("xtreg leverage profitability tangibility log_size, fe cluster(company_code)")
                    cmd_input.press("Tab")
                    page.wait_for_timeout(600)
                    btn_exec.click()
                    print("Waiting for panel regression, theory scorecard & visual engine...")
                    page.wait_for_timeout(10000)
                except Exception as e:
                    print(f"Stata V2 execution notice: {e}")
                
                expand_expanders(page)
                smooth_scroll_page(page, pause=1.0)
                
            elif title == "ML Models":
                exercise_tabs(page)
                smooth_scroll_page(page, pause=0.8)
                
            elif title == "Forecasting":
                exercise_tabs(page)
                smooth_scroll_page(page, pause=0.8)
                
            elif title == "Clustering":
                exercise_tabs(page)
                smooth_scroll_page(page, pause=0.8)
                
            elif title == "AI Assistant":
                print("Demonstrating AI Financial Assistant (Simple -> Complex -> CFO Mode)...")
                try:
                    chat_input = page.locator("textarea[data-testid='stChatInputTextArea'], input[data-testid='stChatInput']").first
                    
                    # Turn 1: Simple Descriptive Inquiry (Researcher Mode)
                    print("  [Turn 1: Simple] Submitting descriptive baseline query...")
                    if chat_input.is_visible():
                        chat_input.click()
                        chat_input.fill("What is the average leverage and firm size across the sample life cycle stages?")
                        chat_input.press("Enter")
                        page.wait_for_timeout(9000)
                    
                    # Turn 2: Complex Econometrics & Literature Theory Inquiry
                    print("  [Turn 2: Complex] Submitting theoretical mechanism query with literature vault citations...")
                    if chat_input.is_visible():
                        chat_input.click()
                        chat_input.fill("Explain how Pecking Order and Trade-Off theories predict leverage differences between Growth and Mature firms, citing Rajan & Zingales (1995) and Dickinson (2011).")
                        chat_input.press("Enter")
                        page.wait_for_timeout(14000)
                    
                    # Turn 3: CFO Mode with Diverse Corporate Archetypes & Scenarios
                    print("  [Turn 3: CFO Mode] Switching to CFO mode...")
                    sidebar = page.locator("section[data-testid='stSidebar']")
                    cfo_radio = sidebar.locator('label').filter(has_text=re.compile(r"^CFO$", re.IGNORECASE)).first
                    if cfo_radio.is_visible():
                        cfo_radio.click()
                        page.wait_for_timeout(2000)
                        
                        # Scenario A: Infosys Ltd. (Tech / Asset-Light / Cash Rich)
                        print("  [CFO Scenario 1: Tech] Analyzing Infosys Ltd. (Cash Rich / Low Debt)...")
                        comp_select = sidebar.locator('div[data-testid="stSelectbox"]').filter(has_text="Select Company").first
                        if comp_select.is_visible():
                            comp_select.click()
                            page.wait_for_timeout(500)
                            infy_opt = page.locator('li[role="option"], div[role="option"]').filter(has_text=re.compile("Infosys", re.IGNORECASE)).first
                            if infy_opt.is_visible():
                                infy_opt.click()
                                page.wait_for_timeout(2000)
                        
                        if chat_input.is_visible():
                            chat_input.click()
                            chat_input.fill("As CFO of Infosys, our leverage is 3.2% with 34.2% ROA. Benchmark us against TCS and Wipro: should we introduce debt for tax shields under Trade-Off theory, or preserve zero-debt flexibility under Pecking Order?")
                            chat_input.press("Enter")
                            page.wait_for_timeout(14000)
                            
                        # Scenario B: Bharti Airtel Ltd. (Telecom / Capital Intensive / Covenant Headroom)
                        print("  [CFO Scenario 2: Telecom] Analyzing Bharti Airtel Ltd. (High Debt / 5G Capex)...")
                        if comp_select.is_visible():
                            comp_select.click()
                            page.wait_for_timeout(500)
                            airtel_opt = page.locator('li[role="option"], div[role="option"]').filter(has_text=re.compile("Bharti Airtel", re.IGNORECASE)).first
                            if airtel_opt.is_visible():
                                airtel_opt.click()
                                page.wait_for_timeout(2000)
                                
                        if chat_input.is_visible():
                            chat_input.click()
                            chat_input.fill("As CFO of Bharti Airtel, benchmark our 47.8% leverage against Indus Towers and telecom peers. Run an interest rate sensitivity stress test: if rates rise by 150 bps, what is our debt covenant headroom and refinancing risk?")
                            chat_input.press("Enter")
                            page.wait_for_timeout(15000)
                            
                        # Scenario C: Tata Steel Ltd. (Heavy Manufacturing / Cyclical Capex)
                        print("  [CFO Scenario 3: Manufacturing] Analyzing Tata Steel Ltd. (Cyclical Capex & Deleveraging)...")
                        if comp_select.is_visible():
                            comp_select.click()
                            page.wait_for_timeout(500)
                            tata_opt = page.locator('li[role="option"], div[role="option"]').filter(has_text=re.compile("Tata Steel", re.IGNORECASE)).first
                            if tata_opt.is_visible():
                                tata_opt.click()
                                page.wait_for_timeout(2000)
                                
                        if chat_input.is_visible():
                            chat_input.click()
                            chat_input.fill("As CFO of Tata Steel, compare our leverage (17.4%) and tangibility (38.1%) against JSW Steel (32.2%) and SAIL (25.9%). How should we finance ₹15,000 Cr of decarbonization capex without endangering our investment grade rating?")
                            chat_input.press("Enter")
                            page.wait_for_timeout(15000)
                except Exception as e:
                    print(f"AI Assistant notice: {e}")
                    
                expand_expanders(page)
                smooth_scroll_page(page, pause=1.0)
                
            elif title == "Board Deck":
                print("Demonstrating Board Deck preview...")
                exercise_tabs(page)
                expand_expanders(page)
                smooth_scroll_page(page, pause=1.0)
                
            print(f"Finished {title}.")
            page.wait_for_timeout(1000)
            
        print("\nAll 17 pages completed. Finalizing video capture...")
        video_handle = page.video
        rec_ctx.close()
        browser.close()
        
        if video_handle:
            video_path = video_handle.path()
            print(f"Raw recording saved at: {video_path}")
            
            # Trim the initial 5 seconds (login form filling) and encode to clean 1080p MP4
            if shutil.which("ffmpeg"):
                print(f"Trimming initial login delay and encoding to final MP4: {FINAL_MP4} ...")
                cmd = [
                    "ffmpeg", "-y", "-ss", "00:00:05", "-i", str(video_path),
                    "-c:v", "libx264", "-preset", "medium", "-crf", "22",
                    "-pix_fmt", "yuv420p", "-r", "30",
                    str(FINAL_MP4)
                ]
                subprocess.run(cmd, check=True)
                size_mb = FINAL_MP4.stat().st_size / (1024 * 1024)
                print(f"\n=======================================================")
                print(f"WALKTHROUGH RECORDING COMPLETE!")
                print(f"Saved: {FINAL_MP4} (Size: {size_mb:.2f} MB)")
                print(f"=======================================================")

if __name__ == "__main__":
    run_recording()

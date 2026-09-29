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
FINAL_SRT = Path("scratch/demo_production/drbhatia_full_walkthrough.srt")

RECORD_START_TIME = None
CAPTIONS_LOG = []

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

def show_caption(page, tag: str, title: str, description: str):
    """Render a sleek, floating glassmorphic HUD pill at bottom-center and log timestamps for SRT generation."""
    global CAPTIONS_LOG, RECORD_START_TIME
    now = time.time()
    if RECORD_START_TIME is None:
        RECORD_START_TIME = now
    
    # Calculate offset in seconds (account for the 5s trim)
    rel_start = max(0.0, now - RECORD_START_TIME - 5.0)
    
    if CAPTIONS_LOG:
        CAPTIONS_LOG[-1]["end"] = max(CAPTIONS_LOG[-1]["start"] + 1.0, rel_start)
        
    CAPTIONS_LOG.append({
        "start": rel_start,
        "end": rel_start + 14.0,
        "tag": tag,
        "title": title,
        "desc": description,
    })
    
    # Inject/update DOM element via Playwright
    try:
        page.evaluate("""({tag, title, desc}) => {
            let el = document.getElementById('demo-hud-caption');
            if (!el) {
                el = document.createElement('div');
                el.id = 'demo-hud-caption';
                document.body.appendChild(el);
            }
            el.style.position = 'fixed';
            el.style.bottom = '24px';
            el.style.left = '50%';
            el.style.transform = 'translateX(-50%)';
            el.style.zIndex = '99999999';
            el.style.background = 'rgba(10, 15, 29, 0.88)';
            el.style.backdropFilter = 'blur(16px)';
            el.style.webkitBackdropFilter = 'blur(16px)';
            el.style.border = '1px solid rgba(56, 189, 248, 0.45)';
            el.style.boxShadow = '0 12px 35px rgba(0, 0, 0, 0.75), 0 0 25px rgba(56, 189, 248, 0.2)';
            el.style.borderRadius = '12px';
            el.style.padding = '9px 24px';
            el.style.color = '#F8FAFC';
            el.style.fontFamily = "'Inter', -apple-system, BlinkMacSystemFont, sans-serif";
            el.style.display = 'flex';
            el.style.flexDirection = 'column';
            el.style.gap = '2px';
            el.style.maxWidth = '920px';
            el.style.width = 'max-content';
            el.style.textAlign = 'center';
            el.style.pointerEvents = 'none';
            el.style.transition = 'all 0.3s cubic-bezier(0.16, 1, 0.3, 1)';
            
            el.innerHTML = `
                <div style="display:flex; align-items:center; justify-content:center; gap:8px;">
                    <span style="color:#38BDF8; font-weight:800; font-size:12px; letter-spacing:0.06em; text-transform:uppercase;">${tag}</span>
                    <span style="color:#64748B;">•</span>
                    <span style="color:#FFFFFF; font-weight:700; font-size:13.5px; letter-spacing:-0.01em;">${title}</span>
                </div>
                <div style="color:#94A3B8; font-size:11.5px; font-weight:500; line-height:1.35;">${desc}</div>
            `;
        }""", {"tag": tag, "title": title, "desc": description})
    except Exception as e:
        print(f"HUD injection notice: {e}")

def generate_srt_file(srt_path: Path):
    """Format the captured timeline into standard SubRip (.srt) subtitles."""
    def fmt_time(seconds: float) -> str:
        ms = int((seconds - int(seconds)) * 1000)
        s = int(seconds) % 60
        m = (int(seconds) // 60) % 60
        h = int(seconds) // 3600
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
        
    lines = []
    for idx, c in enumerate(CAPTIONS_LOG, 1):
        start_str = fmt_time(c["start"])
        end_str = fmt_time(c["end"])
        text = f"{c['tag']} • {c['title']}\n{c['desc']}"
        lines.append(f"{idx}\n{start_str} --> {end_str}\n{text}\n")
        
    srt_path.parent.mkdir(parents=True, exist_ok=True)
    srt_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Generated subtitles: {srt_path}")

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
    for old_f in OUTPUT_DIR.glob("*.webm"):
        try:
            old_f.unlink()
        except Exception:
            pass
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        
        print("\n=== Launching 1080p Walkthrough Recording for drbhatia (with HUD & Subtitles) ===")
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
        
        global RECORD_START_TIME
        RECORD_START_TIME = time.time()
        
        # Record all 17 main pages
        for idx, (title, label, slug) in enumerate(MAIN_PAGES, 1):
            print(f"\n[{idx}/17] Visiting page: {title} ...")
            navigate_to_page(page, label, slug)
            
            # Page-specific interactions and contextual HUD banners
            if title == "Overview":
                show_caption(
                    page,
                    "[01/17] OVERVIEW",
                    "Executive Capital Structure Health & Longitudinal Panel",
                    "Analyzing 104 Indian listed firms across 2001–2024 (2,496 firm-years). Tracking leverage, operating profitability, and asset tangibility."
                )
                expand_expanders(page)
                smooth_scroll_page(page, pause=0.8)
                
            elif title == "Dashboard":
                show_caption(
                    page,
                    "[02/17] DASHBOARD",
                    "Multi-Dimensional Financial Trajectories & Distributions",
                    "Interactive cross-sectional distributions, industry median spreads, and multi-year leverage dynamics across panel vintages."
                )
                exercise_tabs(page)
                smooth_scroll_page(page, pause=0.8)
                
            elif title == "Data Explorer":
                show_caption(
                    page,
                    "[03/17] DATA EXPLORER",
                    "Firm-Level Microdata & Financial Statements (Tata Steel Ltd.)",
                    "Selecting Tata Steel Ltd. (code 248136): balance sheet evolution, cash-flow components, and capital structure ratios."
                )
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
                show_caption(
                    page,
                    "[04/17] PEER BENCHMARKS",
                    "Cross-Industry Quartile Dispersions & Capital Benchmarks",
                    "Evaluating industry debt-ratio rankings and Dickinson life cycle quartile spreads across Indian manufacturing."
                )
                exercise_tabs(page)
                smooth_scroll_page(page, pause=0.8)
                
            elif title == "Life Stage Dynamics":
                show_caption(
                    page,
                    "[05/17] LIFE STAGE DYNAMICS",
                    "Dickinson (2011) Cash-Flow Classification & Trajectories",
                    "Categorizing firms into Introduction, Growth, Maturity, Shakeout, and Decline via operating, investing, and financing cash flow sign patterns."
                )
                exercise_tabs(page)
                smooth_scroll_page(page, pause=0.8)
                
            elif title == "Transitions":
                show_caption(
                    page,
                    "[06/17] TRANSITIONS",
                    "Markov State Migration Matrices & Transition Dynamics",
                    "Empirical transition probabilities tracking multi-year firm movements between corporate life stages."
                )
                exercise_tabs(page)
                smooth_scroll_page(page, pause=0.8)
                
            elif title == "Scenarios":
                show_caption(
                    page,
                    "[07/17] SCENARIOS",
                    "Macro Stress Testing & Shock Sensitivity (GFC, IBC, COVID)",
                    "Simulating GFC (2008-09), IBC enactment (2016), and COVID-19 (2020-21) structural breaks on capital structure decisions."
                )
                exercise_tabs(page)
                smooth_scroll_page(page, pause=0.8)
                
            elif title == "Econometrics Lab":
                show_caption(
                    page,
                    "[08/17] ECONOMETRICS LAB",
                    "Baseline OLS & Fixed Effects Regressions with Firm Clustering",
                    "Testing Pecking Order Theory (POT) vs. Trade-Off Theory (ToT) with standard errors clustered at firm level."
                )
                exercise_tabs(page)
                smooth_scroll_page(page, pause=0.8)
                
            elif title == "Advanced Econometrics":
                show_caption(
                    page,
                    "[09/17] ADVANCED ECONOMETRICS",
                    "Dynamic Panel GMM & Endogeneity Controls (Arellano-Bond)",
                    "Difference GMM and System GMM resolving unobserved firm heterogeneity and dynamic leverage adjustment speeds."
                )
                exercise_tabs(page)
                smooth_scroll_page(page, pause=0.8)
                
            elif title == "Interaction Effects":
                show_caption(
                    page,
                    "[10/17] INTERACTION EFFECTS",
                    "Non-Linear Slopes & Life Stage Moderating Regressions",
                    "Moderating effect of life cycle stages on profitability, tangibility, and dividend payout leverage elasticities."
                )
                exercise_tabs(page)
                smooth_scroll_page(page, pause=0.8)
                
            elif title == "Stata Studio":
                show_caption(
                    page,
                    "[11/17] STATA STUDIO",
                    "Classic Econometric Terminal Environment",
                    "Interactive Stata command-line interface executing panel econometric routines and data manipulation."
                )
                page.wait_for_timeout(2000)
                smooth_scroll_page(page, pause=0.6)
                
            elif title == "Stata Studio V2":
                print("Demonstrating in-depth Stata Studio V2 commands...")
                try:
                    cmd_input = page.locator('input[aria-label*="Command"], input[placeholder*="xtreg"], input[placeholder*="regress"]').first
                    if not cmd_input.is_visible():
                        cmd_input = page.locator('[data-testid="stTextInput"] input').last
                    
                    # 1. First command: Summary statistics & panel distribution
                    show_caption(
                        page,
                        "[12/17] STATA STUDIO V2 • DIAGNOSTICS",
                        "Detailed Distributional Summaries & Parametric Moments",
                        "Executing 'summarize leverage profitability tangibility log_size, detail' with authentic Stata 18 SE terminal output."
                    )
                    print("  [1/2] Running: summarize leverage profitability tangibility log_size, detail ...")
                    cmd_input.click()
                    cmd_input.fill("summarize leverage profitability tangibility log_size, detail")
                    cmd_input.press("Tab")
                    page.wait_for_timeout(600)
                    btn_exec = page.locator('button:has-text("Execute")').first
                    btn_exec.click()
                    page.wait_for_timeout(6000)
                    
                    # 2. Second command: Within-firm panel regression with clustered SE
                    show_caption(
                        page,
                        "[12/17] STATA STUDIO V2 • PANEL REGRESSION",
                        "Within-Firm Fixed Effects & Automated Theory Scorecard",
                        "Executing 'xtreg ... fe cluster(company_code)': evaluating Pecking Order vs Trade-Off hypotheses and rendering the Visual Engine."
                    )
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
                show_caption(
                    page,
                    "[13/17] ML MODELS",
                    "Machine Learning Leverage Prediction & Feature Importance",
                    "Random Forest and Gradient Boosted Trees evaluating non-linear feature importances and leverage stage classification."
                )
                exercise_tabs(page)
                smooth_scroll_page(page, pause=0.8)
                
            elif title == "Forecasting":
                show_caption(
                    page,
                    "[14/17] FORECASTING",
                    "Predictive Time Series Trajectories & Uncertainty Bounds",
                    "Longitudinal projections with 95% confidence intervals across macroeconomic scenarios."
                )
                exercise_tabs(page)
                smooth_scroll_page(page, pause=0.8)
                
            elif title == "Clustering":
                show_caption(
                    page,
                    "[15/17] CLUSTERING",
                    "Unsupervised Financial Pattern Discovery (K-Means & PCA)",
                    "Multidimensional clustering grouping firms by balance sheet resilience, tangibility, and capital intensity."
                )
                exercise_tabs(page)
                smooth_scroll_page(page, pause=0.8)
                
            elif title == "AI Assistant":
                print("Demonstrating AI Financial Assistant (Simple -> Complex -> Diverse CFO Scenarios)...")
                try:
                    chat_input = page.locator("textarea[data-testid='stChatInputTextArea'], input[data-testid='stChatInput']").first
                    
                    # Turn 1: Simple Descriptive Inquiry (Researcher Mode)
                    show_caption(
                        page,
                        "[16/17] AI ASSISTANT • SIMPLE INQUIRY",
                        "Descriptive Baseline Capital Structure Inquiry",
                        "Grounded query on sample-wide average leverage across Dickinson life cycle stages with structured data cards."
                    )
                    print("  [Turn 1: Simple] Submitting descriptive baseline query...")
                    if chat_input.is_visible():
                        chat_input.click()
                        chat_input.fill("What is the average leverage and firm size across the sample life cycle stages?")
                        chat_input.press("Enter")
                        page.wait_for_timeout(9000)
                    
                    # Turn 2: Complex Econometrics & Literature Theory Inquiry
                    show_caption(
                        page,
                        "[16/17] AI ASSISTANT • COMPLEX THEORY",
                        "Peer-Reviewed Academic Literature Vault & Structural Mechanisms",
                        "Contrasting Pecking Order vs Trade-Off with citations to Rajan & Zingales (1995) and Dickinson (2011)."
                    )
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
                        show_caption(
                            page,
                            "[16/17] AI ASSISTANT (CFO MODE) • INFOSYS LTD.",
                            "Asset-Light Tech: Zero-Debt Flexibility vs. Tax Shield Dilemma",
                            "Benchmarking against TCS & Wipro: 3.2% debt ratio, 34.2% ROA, evaluating whether to lever up or preserve Pecking Order flexibility."
                        )
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
                        show_caption(
                            page,
                            "[16/17] AI ASSISTANT (CFO MODE) • BHARTI AIRTEL LTD.",
                            "Telecom Infrastructure: +150 bps Rate Shock & Covenant Headroom",
                            "Benchmarking against Indus Towers: 47.8% leverage, 5G spectrum commitments, assessing debt serviceability & refinancing risk."
                        )
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
                        show_caption(
                            page,
                            "[16/17] AI ASSISTANT (CFO MODE) • TATA STEEL LTD.",
                            "Heavy Industry: Capex Financing & Deleveraging Strategy",
                            "Benchmarking against JSW Steel (32.2%) & SAIL (25.9%): financing ₹15,000 Cr green steel capex while defending credit rating."
                        )
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
                show_caption(
                    page,
                    "[17/17] BOARD DECK",
                    "Executive Summary Deck & Governance Export",
                    "Synthesizing econometric findings, peer rankings, and AI CFO strategic recommendations into an exportable C-suite slide deck."
                )
                print("Demonstrating Board Deck preview...")
                exercise_tabs(page)
                expand_expanders(page)
                smooth_scroll_page(page, pause=1.0)
                
            print(f"Finished {title}.")
            page.wait_for_timeout(1000)
            
        print("\nAll 17 pages completed. Finalizing video capture & subtitle generation...")
        video_handle = page.video
        rec_ctx.close()
        browser.close()
        
        # 1. Generate Synchronized Subtitle file
        generate_srt_file(FINAL_SRT)
        
        # 2. Trim initial 5s delay and encode MP4 with embedded subtitle stream
        if video_handle:
            video_path = video_handle.path()
            print(f"Raw recording saved at: {video_path}")
            
            if shutil.which("ffmpeg"):
                print(f"Trimming initial login delay and encoding to final MP4: {FINAL_MP4} ...")
                cmd = [
                    "ffmpeg", "-y", "-ss", "00:00:05", "-i", str(video_path),
                    "-i", str(FINAL_SRT),
                    "-c:v", "libx264", "-preset", "medium", "-crf", "22",
                    "-c:s", "mov_text", "-metadata:s:s:0", "language=eng",
                    "-pix_fmt", "yuv420p", "-r", "30",
                    str(FINAL_MP4)
                ]
                subprocess.run(cmd, check=True)
                size_mb = FINAL_MP4.stat().st_size / (1024 * 1024)
                print(f"\n=======================================================")
                print(f"WALKTHROUGH RECORDING COMPLETE!")
                print(f"Saved Video: {FINAL_MP4} (Size: {size_mb:.2f} MB)")
                print(f"Saved Subtitles: {FINAL_SRT}")
                print(f"=======================================================")

if __name__ == "__main__":
    run_recording()

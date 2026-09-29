"""
record_drbhatia_walkthrough.py — High-Definition Walkthrough Recorder with Studio Neural Voiceover.

Features:
1. Studio Neural Voiceover (en-US-ChristopherNeural) covering all 17 navigation modules.
2. Synchronized Glassmorphic HUD Pill banners with executive context & key takeaways.
3. Automated SubRip (.srt) subtitle generation matching exact spoken timestamps.
4. CFO Decision Intelligence across diverse corporate archetypes (Infosys, Bharti Airtel, Tata Steel).
5. Automatic FFmpeg audio-video muxing producing 1080p MP4 with crystal-clear AAC voice track.
"""
from __future__ import annotations

import os
import sys
import time
import json
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
FINAL_VOICE_MP4 = Path("scratch/demo_production/drbhatia_full_walkthrough_with_voice.mp4")
FINAL_SRT = Path("scratch/demo_production/drbhatia_full_walkthrough.srt")
TIMING_FILE = Path("scratch/demo_production/audio/timing_map.json")
MASTER_AUDIO = Path("scratch/demo_production/audio/master_narration.mp3")

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

def load_timing_map() -> dict:
    if TIMING_FILE.exists():
        return json.loads(TIMING_FILE.read_text(encoding="utf-8"))
    return {}

def show_caption(page, tag: str, title: str, description: str, duration: float = 14.0):
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
        "end": rel_start + duration,
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
            el.style.background = 'rgba(10, 15, 29, 0.90)';
            el.style.backdropFilter = 'blur(18px)';
            el.style.webkitBackdropFilter = 'blur(18px)';
            el.style.border = '1px solid rgba(56, 189, 248, 0.45)';
            el.style.boxShadow = '0 12px 35px rgba(0, 0, 0, 0.85), 0 0 25px rgba(56, 189, 248, 0.25)';
            el.style.borderRadius = '12px';
            el.style.padding = '10px 24px';
            el.style.color = '#F8FAFC';
            el.style.fontFamily = "'Inter', -apple-system, BlinkMacSystemFont, sans-serif";
            el.style.display = 'flex';
            el.style.flexDirection = 'column';
            el.style.gap = '3px';
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

def smooth_scroll_page(page, total_seconds: float = 12.0):
    """Smoothly scroll the right-hand main content pane down to the bottom and return to top, distributed across total_seconds."""
    scroll_info = page.evaluate("""() => {
        const el = document.querySelector('[data-testid="stMain"]') || document.querySelector('section.main') || document.querySelector('.stApp') || document.documentElement;
        return {
            scrollHeight: el.scrollHeight || document.body.scrollHeight,
            clientHeight: window.innerHeight
        };
    }""")
    
    total_height = max(100, scroll_info["scrollHeight"] - scroll_info["clientHeight"])
    steps = 8
    pause_per_step = max(0.4, (total_seconds * 0.7) / steps)
    
    curr = 0
    for _ in range(steps):
        curr += int(total_height / steps)
        page.evaluate(f"""() => {{
            const el = document.querySelector('[data-testid="stMain"]') || document.querySelector('section.main') || window;
            if (el.scrollTo) {{
                el.scrollTo({{top: {curr}, behavior: 'smooth'}});
            }} else {{
                window.scrollTo({{top: {curr}, behavior: 'smooth'}});
            }}
        }}""")
        page.wait_for_timeout(int(pause_per_step * 1000))
        
    page.wait_for_timeout(int(total_seconds * 0.15 * 1000))
    
    # Return to top smoothly
    page.evaluate("""() => {
        const el = document.querySelector('[data-testid="stMain"]') || document.querySelector('section.main') || window;
        if (el.scrollTo) { el.scrollTo({top: 0, behavior: 'smooth'}); }
        else { window.scrollTo({top: 0, behavior: 'smooth'}); }
    }""")
    page.wait_for_timeout(int(total_seconds * 0.15 * 1000))

def exercise_tabs(page):
    """Click each tab and pause so every tab content is shown."""
    tabs = page.locator('button[data-testid="stTab"]').all()
    for tab in tabs:
        try:
            if tab.is_visible():
                tab.click()
                page.wait_for_timeout(1000)
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
                page.wait_for_timeout(400)
        except Exception:
            pass

def ensure_sidebar_expanded(page):
    sidebar = page.locator("section[data-testid='stSidebar']")
    try:
        btns = sidebar.locator("button").all()
        for b in btns:
            txt = b.inner_text()
            if "view" in txt.lower() and "more" in txt.lower():
                b.click(timeout=1500)
                page.wait_for_timeout(800)
                break
    except Exception:
        pass

def navigate_to_page(page, label, slug):
    """Navigate reliably via sidebar links — NEVER call page.goto() which kills session."""
    sidebar = page.locator("section[data-testid='stSidebar']")
    ensure_sidebar_expanded(page)
    
    link = sidebar.locator("a").filter(has_text=re.compile(f"^{re.escape(label)}$", re.IGNORECASE)).first
    if link.count() == 0:
        link = sidebar.locator("a").filter(has_text=re.compile(f"{re.escape(label)}", re.IGNORECASE)).first
        
    link.scroll_into_view_if_needed()
    link.click(timeout=6000)
    page.wait_for_timeout(3500)

def run_recording():
    timing_map = load_timing_map()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for old_f in OUTPUT_DIR.glob("*.webm"):
        try:
            old_f.unlink()
        except Exception:
            pass
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        
        print("\n=== Launching 1080p Walkthrough Recording with Studio Voice & HUD ===")
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
        
        # Prologue HUD Pill
        p_seg = timing_map.get("prologue", {
            "tag": "EXECUTIVE BRIEFING",
            "title": "Capital Structure & Life Cycle Dynamics (104 Indian Firms)",
            "hud_desc": "Longitudinal study across 2001–2024 (2,496 firm-years) integrating Dickinson lifecycle stages with CFO decision intelligence.",
            "duration": 40.0,
        })
        show_caption(page, p_seg["tag"], p_seg["title"], p_seg["hud_desc"], duration=p_seg.get("duration", 40.0))
        page.wait_for_timeout(4000)
        
        # Record all 17 main pages
        for idx, (title, label, slug) in enumerate(MAIN_PAGES, 1):
            print(f"\n[{idx}/17] Visiting page: {title} ...")
            navigate_to_page(page, label, slug)
            
            # Match segment ID from timing map
            seg_key = slug if slug else "overview"
            seg = timing_map.get(seg_key, {})
            seg_dur = seg.get("duration", 22.0)
            
            # Page-specific interactions and contextual HUD banners
            if title == "Overview":
                show_caption(page, seg.get("tag", "[01/17] OVERVIEW"), seg.get("title", "Executive Capital Structure Health"), seg.get("hud_desc", "Analyzing 104 Indian listed firms across 2001–2024."), duration=seg_dur)
                expand_expanders(page)
                smooth_scroll_page(page, total_seconds=seg_dur)
                
            elif title == "Dashboard":
                show_caption(page, seg.get("tag", "[02/17] DASHBOARD"), seg.get("title", "Multi-Dimensional Trajectories"), seg.get("hud_desc", "Interactive distributions and sector leverage spreads."), duration=seg_dur)
                exercise_tabs(page)
                smooth_scroll_page(page, total_seconds=seg_dur)
                
            elif title == "Data Explorer":
                show_caption(page, seg.get("tag", "[03/17] DATA EXPLORER"), seg.get("title", "Firm-Level Microdata (Tata Steel Ltd.)"), seg.get("hud_desc", "Balance sheet evolution, cash-flow components, and capital structure ratios."), duration=seg_dur)
                print("Selecting Tata Steel Ltd. in company dropdown...")
                try:
                    comp_select = page.locator('div[data-testid="stSelectbox"]').first
                    if comp_select.is_visible():
                        comp_select.click()
                        page.wait_for_timeout(600)
                        tata_opt = page.locator('li[role="option"], div[role="option"]').filter(has_text=re.compile("Tata Steel", re.IGNORECASE)).first
                        if tata_opt.is_visible():
                            tata_opt.click()
                            page.wait_for_timeout(1500)
                except Exception as e:
                    print(f"Company select notice: {e}")
                exercise_tabs(page)
                smooth_scroll_page(page, total_seconds=seg_dur * 0.7)
                
            elif title == "Peer Benchmarks":
                show_caption(page, seg.get("tag", "[04/17] PEER BENCHMARKS"), seg.get("title", "Cross-Industry Quartile Dispersions"), seg.get("hud_desc", "Evaluating industry debt-ratio rankings and lifecycle spreads."), duration=seg_dur)
                exercise_tabs(page)
                smooth_scroll_page(page, total_seconds=seg_dur)
                
            elif title == "Life Stage Dynamics":
                show_caption(page, seg.get("tag", "[05/17] LIFE STAGE DYNAMICS"), seg.get("title", "Dickinson (2011) Cash-Flow Classification"), seg.get("hud_desc", "Sign combinations of operating, investing, and financing cash flows."), duration=seg_dur)
                exercise_tabs(page)
                smooth_scroll_page(page, total_seconds=seg_dur)
                
            elif title == "Transitions":
                show_caption(page, seg.get("tag", "[06/17] TRANSITIONS"), seg.get("title", "Markov State Migration Matrices"), seg.get("hud_desc", "Empirical transition probabilities tracking multi-year movements."), duration=seg_dur)
                exercise_tabs(page)
                smooth_scroll_page(page, total_seconds=seg_dur)
                
            elif title == "Scenarios":
                show_caption(page, seg.get("tag", "[07/17] SCENARIOS"), seg.get("title", "Macro Stress Testing (GFC, IBC, COVID)"), seg.get("hud_desc", "Simulating GFC, IBC enactment, and COVID-19 structural breaks."), duration=seg_dur)
                exercise_tabs(page)
                smooth_scroll_page(page, total_seconds=seg_dur)
                
            elif title == "Econometrics Lab":
                show_caption(page, seg.get("tag", "[08/17] ECONOMETRICS LAB"), seg.get("title", "Baseline OLS & Fixed Effects Regressions"), seg.get("hud_desc", "Testing Pecking Order vs Trade-Off with firm clustered standard errors."), duration=seg_dur)
                exercise_tabs(page)
                smooth_scroll_page(page, total_seconds=seg_dur)
                
            elif title == "Advanced Econometrics":
                show_caption(page, seg.get("tag", "[09/17] ADVANCED ECONOMETRICS"), seg.get("title", "Dynamic Panel GMM (Arellano-Bond)"), seg.get("hud_desc", "Difference and System GMM estimating target leverage adjustment speed."), duration=seg_dur)
                exercise_tabs(page)
                smooth_scroll_page(page, total_seconds=seg_dur)
                
            elif title == "Interaction Effects":
                show_caption(page, seg.get("tag", "[10/17] INTERACTION EFFECTS"), seg.get("title", "Non-Linear Slopes & Life Stage Moderation"), seg.get("hud_desc", "Moderating effect of life stages on profitability and tangibility elasticities."), duration=seg_dur)
                exercise_tabs(page)
                smooth_scroll_page(page, total_seconds=seg_dur)
                
            elif title == "Stata Studio":
                show_caption(page, seg.get("tag", "[11/17] STATA STUDIO"), seg.get("title", "Classic Econometric Scripting"), seg.get("hud_desc", "Econometric code syntax and panel routine inspection."), duration=seg_dur)
                smooth_scroll_page(page, total_seconds=seg_dur)
                
            elif title == "Stata Studio V2":
                print("Demonstrating in-depth Stata Studio V2 commands...")
                show_caption(page, seg.get("tag", "[12/17] STATA STUDIO V2"), seg.get("title", "Interactive Stata 18 SE Terminal & Visual Engine"), seg.get("hud_desc", "Executing 'summarize detail' and 'xtreg fe cluster' with automated Theory Scorecard."), duration=seg_dur)
                try:
                    cmd_input = page.locator('input[aria-label*="Command"], input[placeholder*="xtreg"], input[placeholder*="regress"]').first
                    if not cmd_input.is_visible():
                        cmd_input = page.locator('[data-testid="stTextInput"] input').last
                    
                    # Command 1: Parametric summary
                    cmd_input.click()
                    cmd_input.fill("summarize leverage profitability tangibility log_size, detail")
                    cmd_input.press("Tab")
                    page.wait_for_timeout(400)
                    btn_exec = page.locator('button:has-text("Execute")').first
                    btn_exec.click()
                    page.wait_for_timeout(4000)
                    
                    # Command 2: Within-firm panel regression with clustered SE
                    cmd_input.click()
                    cmd_input.fill("xtreg leverage profitability tangibility log_size, fe cluster(company_code)")
                    cmd_input.press("Tab")
                    page.wait_for_timeout(400)
                    btn_exec.click()
                    page.wait_for_timeout(6000)
                except Exception as e:
                    print(f"Stata V2 execution notice: {e}")
                
                expand_expanders(page)
                smooth_scroll_page(page, total_seconds=max(8.0, seg_dur - 11.0))
                
            elif title == "ML Models":
                show_caption(page, seg.get("tag", "[13/17] ML MODELS"), seg.get("title", "Machine Learning Leverage Prediction"), seg.get("hud_desc", "Random Forest and Gradient Boosted Trees non-linear feature importances."), duration=seg_dur)
                exercise_tabs(page)
                smooth_scroll_page(page, total_seconds=seg_dur)
                
            elif title == "Forecasting":
                show_caption(page, seg.get("tag", "[14/17] FORECASTING"), seg.get("title", "Predictive Time Series Trajectories"), seg.get("hud_desc", "Longitudinal projections with 95% confidence intervals across macro scenarios."), duration=seg_dur)
                exercise_tabs(page)
                smooth_scroll_page(page, total_seconds=seg_dur)
                
            elif title == "Clustering":
                show_caption(page, seg.get("tag", "[15/17] CLUSTERING"), seg.get("title", "Unsupervised Financial Pattern Discovery"), seg.get("hud_desc", "K-Means and PCA segmenting balance sheet archetypes."), duration=seg_dur)
                exercise_tabs(page)
                smooth_scroll_page(page, total_seconds=seg_dur)
                
            elif title == "AI Assistant":
                print("Demonstrating AI Financial Assistant (Researcher Mode -> Diverse CFO Scenarios)...")
                try:
                    chat_input = page.locator("textarea[data-testid='stChatInputTextArea'], input[data-testid='stChatInput']").first
                    
                    # 1. Researcher Mode: Grounded Theory & Literature Vault
                    seg_res = timing_map.get("ai_assistant_researcher", {})
                    dur_res = seg_res.get("duration", 24.0)
                    show_caption(page, seg_res.get("tag", "[16/17] AI ASSISTANT • RESEARCHER"), seg_res.get("title", "Grounded Corporate Finance Literature Vault"), seg_res.get("hud_desc", "Contrasting Pecking Order vs Trade-Off with citations to Rajan & Zingales (1995) and Dickinson (2011)."), duration=dur_res)
                    print("  [Researcher Mode] Submitting grounded literature query...")
                    if chat_input.is_visible():
                        chat_input.click()
                        chat_input.fill("Explain how Pecking Order and Trade-Off theories predict leverage differences between Growth and Mature firms, citing Rajan & Zingales (1995) and Dickinson (2011).")
                        chat_input.press("Enter")
                        page.wait_for_timeout(int(dur_res * 1000))
                    
                    # 2. Switch to CFO Mode
                    print("  [Switching to CFO Mode]...")
                    sidebar = page.locator("section[data-testid='stSidebar']")
                    cfo_radio = sidebar.locator('label').filter(has_text=re.compile(r"^CFO$", re.IGNORECASE)).first
                    if cfo_radio.is_visible():
                        cfo_radio.click()
                        page.wait_for_timeout(2000)
                        
                        # CFO Scenario A: Infosys Ltd. (Tech)
                        seg_infy = timing_map.get("ai_cfo_infosys", {})
                        dur_infy = seg_infy.get("duration", 33.0)
                        show_caption(page, seg_infy.get("tag", "[16/17] AI CFO • INFOSYS LTD. (TECH)"), seg_infy.get("title", "Asset-Light Tech: Zero-Debt Flexibility vs Tax Shield Trade-Off"), seg_infy.get("hud_desc", "Leverage 3.2%, ROA 34.2%. Intangibles lack collateral value. Preserving financial flexibility for strategic agility."), duration=dur_infy)
                        print("  [CFO Archetype 1: Tech] Analyzing Infosys Ltd. ...")
                        comp_select = sidebar.locator('div[data-testid="stSelectbox"]').filter(has_text="Select Company").first
                        if not comp_select.is_visible():
                            comp_select = sidebar.locator('div[data-testid="stSelectbox"]').last
                        if comp_select.is_visible():
                            comp_select.click()
                            page.wait_for_timeout(500)
                            infy_opt = page.locator('li[role="option"], div[role="option"]').filter(has_text=re.compile("Infosys", re.IGNORECASE)).first
                            if infy_opt.is_visible():
                                infy_opt.click()
                                page.wait_for_timeout(1500)
                        
                        if chat_input.is_visible():
                            chat_input.click()
                            chat_input.fill("As CFO of Infosys, our leverage is 3.2% with 34.2% ROA. Benchmark us against TCS and Wipro: should we introduce debt for tax shields under Trade-Off theory, or preserve zero-debt flexibility under Pecking Order?")
                            chat_input.press("Enter")
                            page.wait_for_timeout(int(dur_infy * 1000))
                            
                        # CFO Scenario B: Bharti Airtel Ltd. (Telecom)
                        seg_airtel = timing_map.get("ai_cfo_airtel", {})
                        dur_airtel = seg_airtel.get("duration", 27.0)
                        show_caption(page, seg_airtel.get("tag", "[16/17] AI CFO • BHARTI AIRTEL LTD. (TELECOM)"), seg_airtel.get("title", "Telecom Infrastructure: +150 bps Rate Shock & Covenant Headroom"), seg_airtel.get("hud_desc", "Leverage 47.8%, 5G commitments. +150 bps rate shock compresses ICR to 2.3x; recommends debt tenor restructuring."), duration=dur_airtel)
                        print("  [CFO Archetype 2: Telecom] Analyzing Bharti Airtel Ltd. ...")
                        if comp_select.is_visible():
                            comp_select.click()
                            page.wait_for_timeout(500)
                            airtel_opt = page.locator('li[role="option"], div[role="option"]').filter(has_text=re.compile("Bharti Airtel", re.IGNORECASE)).first
                            if airtel_opt.is_visible():
                                airtel_opt.click()
                                page.wait_for_timeout(1500)
                                
                        if chat_input.is_visible():
                            chat_input.click()
                            chat_input.fill("As CFO of Bharti Airtel, benchmark our 47.8% leverage against Indus Towers and telecom peers. Run an interest rate sensitivity stress test: if rates rise by 150 bps, what is our debt covenant headroom and refinancing risk?")
                            chat_input.press("Enter")
                            page.wait_for_timeout(int(dur_airtel * 1000))
                            
                        # CFO Scenario C: Tata Steel Ltd. (Heavy Industry)
                        seg_tata = timing_map.get("ai_cfo_tatasteel", {})
                        dur_tata = seg_tata.get("duration", 23.0)
                        show_caption(page, seg_tata.get("tag", "[16/17] AI CFO • TATA STEEL LTD. (MANUFACTURING)"), seg_tata.get("title", "Heavy Industry: Financing ₹15,000 Cr Decarbonization Capex"), seg_tata.get("hud_desc", "Leverage 17.4%, tangibility 38.1%. Blended structure (45% CFO cash, 35% sustainability bonds, 20% equity) defends rating."), duration=dur_tata)
                        print("  [CFO Archetype 3: Manufacturing] Analyzing Tata Steel Ltd. ...")
                        if comp_select.is_visible():
                            comp_select.click()
                            page.wait_for_timeout(500)
                            tata_opt = page.locator('li[role="option"], div[role="option"]').filter(has_text=re.compile("Tata Steel", re.IGNORECASE)).first
                            if tata_opt.is_visible():
                                tata_opt.click()
                                page.wait_for_timeout(1500)
                                
                        if chat_input.is_visible():
                            chat_input.click()
                            chat_input.fill("As CFO of Tata Steel, compare our leverage (17.4%) and tangibility (38.1%) against JSW Steel (32.2%) and SAIL (25.9%). How should we finance ₹15,000 Cr of decarbonization capex without endangering our investment grade rating?")
                            chat_input.press("Enter")
                            page.wait_for_timeout(int(dur_tata * 1000))
                except Exception as e:
                    print(f"AI Assistant notice: {e}")
                    
                expand_expanders(page)
                smooth_scroll_page(page, total_seconds=8.0)
                
            elif title == "Board Deck":
                show_caption(page, seg.get("tag", "[17/17] BOARD DECK"), seg.get("title", "Executive Summary Deck & Governance Export"), seg.get("hud_desc", "Synthesizing econometrics, peer benchmarks, and AI CFO recommendations into an exportable C-suite slide deck."), duration=seg_dur)
                exercise_tabs(page)
                expand_expanders(page)
                smooth_scroll_page(page, total_seconds=seg_dur)
                
            print(f"Finished {title}.")
            page.wait_for_timeout(1000)
            
        # Epilogue HUD Pill
        e_seg = timing_map.get("epilogue", {
            "tag": "EXECUTIVE CONCLUSION",
            "title": "Decisive Boardroom Leadership Through Empirical Intelligence",
            "hud_desc": "Transforming 24 years of corporate finance econometrics and Stata rigor into actionable boardroom leadership.",
            "duration": 16.0,
        })
        show_caption(page, e_seg["tag"], e_seg["title"], e_seg["hud_desc"], duration=e_seg.get("duration", 16.0))
        page.wait_for_timeout(8000)
        
        print("\nAll modules completed! Finalizing video capture & subtitle generation...")
        video_handle = page.video
        rec_ctx.close()
        browser.close()
        
        # 1. Generate Synchronized Subtitle file
        generate_srt_file(FINAL_SRT)
        
        # 2. Trim initial login delay and encode MP4 with neural master audio and embedded subtitles
        if video_handle:
            video_path = video_handle.path()
            print(f"Raw recording saved at: {video_path}")
            
            if shutil.which("ffmpeg") and MASTER_AUDIO.exists():
                print(f"Muxing 1080p video with studio voice track ({MASTER_AUDIO}) and subtitles ({FINAL_SRT})...")
                cmd = [
                    "ffmpeg", "-y",
                    "-ss", "00:00:05", "-i", str(video_path),
                    "-i", str(MASTER_AUDIO),
                    "-i", str(FINAL_SRT),
                    "-c:v", "libx264", "-preset", "medium", "-crf", "22",
                    "-c:a", "aac", "-b:a", "192k",
                    "-c:s", "mov_text", "-metadata:s:s:0", "language=eng",
                    "-shortest",
                    "-pix_fmt", "yuv420p", "-r", "30",
                    str(FINAL_VOICE_MP4)
                ]
                subprocess.run(cmd, check=True)
                
                # Copy to standard FINAL_MP4 as well
                shutil.copyfile(FINAL_VOICE_MP4, FINAL_MP4)
                
                size_mb = FINAL_VOICE_MP4.stat().st_size / (1024 * 1024)
                print(f"\n=======================================================")
                print(f"WALKTHROUGH RECORDING WITH AUDIO COMPLETE!")
                print(f"Saved Video: {FINAL_VOICE_MP4} (Size: {size_mb:.2f} MB)")
                print(f"Saved Subtitles: {FINAL_SRT}")
                print(f"=======================================================")

if __name__ == "__main__":
    run_recording()

"""
produce_ai_chatbot_demo_recordly.py

Recordly Master Production Pipeline for the AI Financial Assistant Master Walkthrough.
Implements 100% Dynamic Screen Run-Up:
  1. Live character-by-character typing into chat input on camera (Screen 1).
  2. Live triggering of the submit event (Enter) and 2.0s capture of 'Working...' reasoning trace (Screen 2).
  3. Automatic immediate scroll-up to y=0 upon generation so user prompt, telemetry, and Dickinson Lifecycle Stage are visible (Screen 3).
  4. Paced focal scrolling tracking every spoken sentence down to CFO Actionable Recommendations and Literature Vault (Screen 4).
  5. Live dynamic execution across all archetypes (Infosys, Tata Steel, Airtel, IndiGo, Sun Pharma, Stata xtreg).
  6. Non-obstructive broadcast lower-third subtitles with MarginV=90 floating in clean white space.
  7. Exact zero-drift lockstep across all scenes with isolated clean database sessions.

Authors:
  Dr. Sanjay Bhatia (CoFounder, EOLABS.IN)
  Dr. Surender Kumar (Senior Academic Research & Empirical Corporate Finance)
  Powered by EOLABS.IN
"""
from __future__ import annotations
import os
import sys
import time
import json
import asyncio
import sqlite3
import subprocess
from pathlib import Path
from datetime import datetime
import shutil
import edge_tts
from playwright.sync_api import sync_playwright

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_URL   = "http://localhost:8501"
PAGE_URL   = f"{BASE_URL}/ai_assistant"
OUT        = Path("scratch/demo_production")
AUDIO_DIR  = OUT / "audio_recordly"
SCENE_DIR  = OUT / "scenes_recordly"
VOICE      = "en-US-ChristopherNeural"

AUDIO_DIR.mkdir(parents=True, exist_ok=True)
SCENE_DIR.mkdir(parents=True, exist_ok=True)
(SCENE_DIR / "raw").mkdir(parents=True, exist_ok=True)
(OUT / "redteam_review_recordly").mkdir(parents=True, exist_ok=True)

# ─────────────────────────────────────────────────────────────────────────────
# Scene Definitions with Fine-Grained Sentence Cues & Live Action Metadata
# ─────────────────────────────────────────────────────────────────────────────
SCENES = [
    {
        "id": "scene1_title_card",
        "tag": "AI RESEARCH STUDIO",
        "title": "Financial Leverage & Corporate Life Stages",
        "hud_desc": "Dr. Sanjay Bhatia & Dr. Surender Kumar | Powered by EOLABS.IN",
        "sentences": [
            "Welcome to LifeCycle Leverage Intelligence.",
            "I am presenting the AI Financial Assistant, an advanced strategic copilot developed by Doctor Sanjay Bhatia and Doctor Surender Kumar, powered by EOLABS.IN.",
            "Today, we demonstrate how this engine translates twenty-five years of empirical corporate finance panel data into actionable boardroom decisions and econometric discoveries."
        ],
    },
    {
        "id": "scene2_assistant_overview",
        "tag": "AI FINANCIAL ASSISTANT",
        "title": "Anatomy of an AI Response: Six Component Layers",
        "hud_desc": "402 enterprises | 9,077 observations (2001-2025) | Step-by-Step Output Breakdown",
        "prompt": "Explain how Pecking Order and Trade-Off theories predict leverage differences between Growth and Mature firms, citing Rajan & Zingales (1995) and Dickinson (2011).",
        "sentences": [
            "When a CFO or researcher submits an inquiry, the AI Assistant instantly synthesizes a six-layer decision artifact.",
            "First, at the top, live telemetry validates the dataset scope across nine thousand and seventy-seven observations with zero hallucination.",
            "Second, the Executive Hypothesis and Decision Strip highlights life-cycle classification and target leverage.",
            "Third, the engine delivers a theory-grounded strategic narrative, balancing Pecking Order liquidity against Trade-Off tax shields.",
            "Fourth, actionable C-Suite recommendations provide specific financing playbooks for capital allocation.",
            "Fifth, an interactive Plotly visualization renders multi-series distributions alongside executable Stata replication scripts.",
            "And sixth, the Peer-Reviewed Benchmark Vault anchors every insight in literature, ready for one-click Board Deck export."
        ],
    },
    {
        "id": "scene3_infosys_tech",
        "tag": "CORPORATE ARCHETYPE 1: TECH",
        "title": "Infosys Ltd. (100632): Near-Zero Debt & Financial Flexibility",
        "hud_desc": "Leverage 4.2%, ROA 33.4%, Dickinson Mature Stage | Pecking Order vs Tax Shields",
        "prompt": "As CFO of Infosys Ltd., analyze our baseline capital structure and cash-flow profile in Computer software. What Dickinson lifecycle stage are we currently in, and how does our 4.2% leverage compare to the IT software industry median?",
        "sentences": [
            "We begin with Infosys in the technology sector, submitting our baseline capital structure and cash-flow query.",
            "Looking at the executive badge, Infosys is diagnosed in Dickinson's Mature stage with four point two percent leverage and thirty-three percent return on assets.",
            "Under Trade-Off Theory, the model analyzes why software leaders forfeit interest tax shields to preserve debt capacity.",
            "The interactive peer benchmark chart contrasts Infosys against industry competitors.",
            "The actionable CFO playbook recommends self-financing capital expenditures through internal cash flows while defending strategic liquidity."
        ],
    },
    {
        "id": "scene4_tata_steel_stress",
        "tag": "CORPORATE ARCHETYPE 2: METALS",
        "title": "Tata Steel Ltd. (248136): Macro Rate Shock (+150 bps) & Covenant Defense",
        "hud_desc": "+150 bps rate surge + 20% margin drop: ICR 1.72x vs 2.00x floor (BREACH RISK)",
        "prompt": "Conduct a macro stress test for Tata Steel: if borrowing costs rise by 150 bps and steel spreads contract by 20%, what happens to our Interest Coverage Ratio against the 2.0x floor?",
        "sentences": [
            "Switching to Tata Steel, we execute a Tier Three Macroeconomic Stress Test with thirty-seven percent asset tangibility.",
            "The assistant computes a one hundred and fifty basis point interest rate surge combined with a twenty percent steel margin drop.",
            "The red executive status banner warns of covenant breach risk, with Interest Coverage Ratio compressing to one point seven-two times against the two-point-zero floor.",
            "Scrolling down to the strategic recommendations, the C-Suite playbook advises pre-funding debt maturities with fixed-rate three-to-five year bonds."
        ],
    },
    {
        "id": "scene5_airtel_indigo_pharma",
        "tag": "DIVERSE SECTORS: TELECOM, AVIATION & PHARMA",
        "title": "Bharti Airtel (34162), IndiGo (395047) & Sun Pharma (239726)",
        "hud_desc": "Telecom InvIT monetization | Aviation fuel shocks | Pharma FX hedge",
        "sentences": [
            "Across other sector archetypes, the AI Assistant dynamically tailors executive solutions:",
            "For Bharti Airtel, it evaluates infrastructure InvIT carve-outs to deleverage massive five-G spectrum debt.",
            "For IndiGo in aviation, it models monthly cash burn under jet fuel shocks and sizes Sale-and-Leaseback debt capacity.",
            "For Sun Pharma, it structures Euro-denominated notes as a natural currency hedge for cross-border acquisitions."
        ],
    },
    {
        "id": "scene6_researcher_stata",
        "tag": "ECONOMETRIC LAB & STATA REPLICATION",
        "title": "Panel Fixed-Effects xtreg & Interactive Visualizations",
        "hud_desc": "xtreg lev size tang roa mtb i.year, fe cluster(ind_code) | Multi-series Plotly chart",
        "prompt": ". xtreg leverage roa tang size, fe cluster(ind_code)",
        "sentences": [
            "Switching to Researcher Mode unlocks our quantitative econometric core.",
            "The assistant executes authentic Stata eighteen SE panel fixed-effects regressions with clustered standard errors.",
            "The output displays the full Stata terminal table, coefficient estimates, and diagnostic statistics.",
            "Researchers can inspect the interactive Plotly lifecycle distributions and export the exact Stata replication do-file."
        ],
    },
    {
        "id": "scene7_literature_vault",
        "tag": "BENCHMARK VAULT & GOVERNANCE",
        "title": "Academic Citation Inspector & Governance Deck",
        "hud_desc": "Dickinson (2011), Myers & Majluf (1984), Rajan & Zingales (1995)",
        "sentences": [
            "Every recommendation is anchored in peer-reviewed literature.",
            "Clicking any citation badge opens the interactive Citation Inspector, displaying bibliographic provenance and empirical parameters from Dickinson, Myers, and Rajan and Zingales.",
            "CFOs can click 'Add to Board Deck' to instantly pipe synthesized AI recommendations into executive governance presentations."
        ],
    },
    {
        "id": "scene8_closing_card",
        "tag": "EXECUTIVE EPILOGUE",
        "title": "LifeCycle Leverage Intelligence Platform",
        "hud_desc": "Dr. Sanjay Bhatia & Dr. Surender Kumar | Powered by EOLABS.IN",
        "sentences": [
            "LifeCycle Leverage Intelligence unites twenty-five years of empirical evidence, econometric rigor, and artificial intelligence decision support.",
            "Developed by Doctor Sanjay Bhatia and Doctor Surender Kumar, powered by EOLABS.IN.",
            "Thank you for exploring the future of empirical financial intelligence."
        ],
    },
]

# ─────────────────────────────────────────────────────────────────────────────
# Database Isolation Helper (Zero Residual Session Bleed)
# ─────────────────────────────────────────────────────────────────────────────
def clean_database_chat_sessions():
    """Wipe prior chat sessions so every run is 100% clean."""
    try:
        conn = sqlite3.connect("capital_structure.db")
        conn.execute("DELETE FROM chat_messages")
        conn.execute("DELETE FROM chat_sessions")
        conn.commit()
        conn.close()
        print("  [db-clean] ✓ Chat sessions and messages wiped for clean scene isolation.")
    except Exception as e:
        print(f"  [db-clean] Note: {e}")

def scroll_up_immediate(page):
    """Instantly scroll all candidate main containers to y=0."""
    page.evaluate("""() => {
        const targets = [
            document.querySelector('[data-testid="stMain"]'),
            document.querySelector('section.main'),
            document.querySelector('.main'),
            document.documentElement,
            document.body,
            window
        ];
        for (const t of targets) {
            try {
                if (t && t.scrollTo) { t.scrollTo({top: 0, behavior: 'instant'}); }
            } catch(e) {}
        }
    }""")

def focal_scroll(page, target_y: int):
    """Smoothly scroll candidate main containers to a vertical anchor."""
    page.evaluate(f"""() => {{
        const targets = [
            document.querySelector('[data-testid="stMain"]'),
            document.querySelector('section.main'),
            document.querySelector('.main'),
            document.documentElement,
            document.body,
            window
        ];
        for (const t of targets) {{
            try {{
                if (t && t.scrollTo) {{ t.scrollTo({{top: {target_y}, behavior: 'smooth'}}); }}
            }} catch(e) {{}}
        }}
    }}""")
async def gen_audio_segment(text: str, out_path: Path):
    communicate = edge_tts.Communicate(text, VOICE, rate="+3%", pitch="+0Hz")
    await communicate.save(str(out_path))

def get_audio_duration(mp3_path: Path) -> float:
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(mp3_path)
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return float(res.stdout.strip())

def make_silence_mp3(dur: float, out_path: Path):
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"anullsrc=r=24000:cl=mono",
        "-t", f"{dur:.3f}",
        "-q:a", "9",
        "-acodec", "libmp3lame",
        str(out_path)
    ]
    subprocess.run(cmd, capture_output=True, check=True)

def concat_mp3s(mp3_list: list[Path], out_mp3: Path):
    list_txt = out_mp3.parent / f"list_{out_mp3.stem}.txt"
    with open(list_txt, "w", encoding="utf-8") as f:
        for m in mp3_list:
            p_str = m.resolve().as_posix()
            f.write(f"file '{p_str}'\n")
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(list_txt),
        "-c", "copy",
        str(out_mp3)
    ]
    subprocess.run(cmd, capture_output=True, check=True)
    if list_txt.exists():
        list_txt.unlink()

def prepare_all_audio() -> list[dict]:
    print("=== Step 1: Generating Neural Voice & Sentence Cues (edge-tts) ===")
    scene_manifest = []
    total_dur = 0.0
    
    for sc in SCENES:
        sid = sc["id"]
        is_query_scene = sid in ("scene2_assistant_overview", "scene3_infosys_tech", "scene4_tata_steel_stress", "scene6_researcher_stata")
        
        sentence_mp3s = []
        sentence_cues = []
        cur_t = 0.0
        
        for idx, s in enumerate(sc["sentences"]):
            s_file = AUDIO_DIR / f"{sid}_s{idx}.mp3"
            asyncio.run(gen_audio_segment(s, s_file))
            s_dur = get_audio_duration(s_file)
            sentence_mp3s.append(s_file)
            
            sentence_cues.append({
                "text": s,
                "start": cur_t,
                "end": cur_t + s_dur,
                "duration": s_dur,
                "file": s_file,
            })
            cur_t += s_dur
            
            # If this is the query sentence (index 0) in an interactive scene, inject a 2.0s working pause in timeline
            if is_query_scene and idx == 0:
                silence_file = AUDIO_DIR / f"{sid}_silence_working.mp3"
                make_silence_mp3(2.0, silence_file)
                sentence_mp3s.append(silence_file)
                cur_t += 2.0

        # Master concatenated MP3 for this scene
        master_scene_mp3 = AUDIO_DIR / f"{sid}.mp3"
        concat_mp3s(sentence_mp3s, master_scene_mp3)
        total_scene_dur = get_audio_duration(master_scene_mp3)
        
        print(f"  [{sid}] -> {total_scene_dur:.2f}s ({len(sc['sentences'])} sentences) | {master_scene_mp3.name}")
        scene_manifest.append({
            "id": sid,
            "mp3": master_scene_mp3,
            "duration": total_scene_dur,
            "cues": sentence_cues,
            "data": sc,
            "is_query_scene": is_query_scene,
        })
        total_dur += total_scene_dur

    print(f"Total Master Audio Duration: {total_dur:.1f}s ({total_dur/60:.2f} min)\n")
    return scene_manifest

# ─────────────────────────────────────────────────────────────────────────────
# Visual Overlays & Slim HUD
# ─────────────────────────────────────────────────────────────────────────────
def show_slim_hud(page, tag: str, title: str, desc: str):
    page.evaluate(f"""() => {{
        let hud = document.getElementById('demo-slim-hud');
        if (!hud) {{
            hud = document.createElement('div');
            hud.id = 'demo-slim-hud';
            document.body.appendChild(hud);
        }}
        Object.assign(hud.style, {{
            position: 'fixed', top: '8px', left: '50%', transform: 'translateX(-50%)',
            zIndex: '999999',
            background: 'rgba(15, 23, 42, 0.90)',
            backdropFilter: 'blur(10px)',
            border: '1px solid rgba(56, 189, 248, 0.40)',
            borderRadius: '24px',
            padding: '5px 18px',
            color: '#FFFFFF',
            fontFamily: "'Inter', -apple-system, sans-serif",
            boxShadow: '0 8px 24px rgba(0,0,0,0.5)',
            display: 'flex', alignItems: 'center', gap: '10px',
            pointerEvents: 'none',
            maxWidth: '840px',
            transition: 'all 0.3s ease'
        }});
        hud.innerHTML = `
            <span style="font-size:10px;font-weight:800;color:#38BDF8;background:rgba(56,189,248,0.18);padding:2px 8px;border-radius:12px;text-transform:uppercase;letter-spacing:0.5px;">{tag}</span>
            <span style="font-size:12px;font-weight:700;color:#F8FAFC;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{title}</span>
            <span style="font-size:11px;color:#94A3B8;border-left:1px solid rgba(255,255,255,0.2);padding-left:10px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{desc}</span>
        `;
    }}""")

def show_title_card(page):
    page.evaluate('''() => {
        let ov = document.getElementById('demo-title-ov');
        if (!ov) { ov = document.createElement('div'); ov.id = 'demo-title-ov'; document.body.appendChild(ov); }
        Object.assign(ov.style, {
            position: 'fixed', top: '0', left: '0', width: '100vw', height: '100vh',
            zIndex: '99999998',
            background: 'radial-gradient(circle at 50% 35%, #0f172a 0%, #020617 100%)',
            color: '#FFF', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
            fontFamily: "'Inter', -apple-system, sans-serif", padding: '40px'
        });
        ov.innerHTML = `
        <div style="display:inline-flex;align-items:center;gap:8px;padding:6px 18px;background:rgba(56,189,248,0.12);border:1px solid rgba(56,189,248,0.35);border-radius:30px;font-size:12px;font-weight:700;color:#38BDF8;margin-bottom:24px;text-transform:uppercase;letter-spacing:1px;">
            <span>★</span> Recordly Production &bull; AI Research Studio Master Walkthrough</div>
        <h1 style="font-size:44px;font-weight:800;margin:0 0 16px 0;text-align:center;letter-spacing:-0.5px;background:linear-gradient(135deg,#FFFFFF 0%,#BAE6FD 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">
            Financial Leverage &amp; Corporate Life Stages</h1>
        <h2 style="font-size:24px;font-weight:600;color:#38BDF8;margin:0 0 20px 0;text-align:center;">
            AI Financial Assistant: CFO Strategy &amp; Econometric Replication</h2>
        <p style="font-size:16px;color:#94A3B8;max-width:820px;text-align:center;line-height:1.6;margin:0 0 40px 0;">
            Grounded in 25 Years of Panel Microdata (402 Enterprises &bull; 9,077 Obs) &bull; Dickinson Cash-Flow Classification &bull; Stata 18 SE Core</p>
        <div style="display:flex;align-items:center;gap:36px;padding:20px 40px;background:rgba(30,41,59,0.7);border:1px solid rgba(255,255,255,0.12);border-radius:16px;box-shadow:0 15px 35px rgba(0,0,0,0.5);">
            <div><div style="font-size:16px;font-weight:700;color:#FFF;">Dr. Sanjay Bhatia</div>
                 <div style="font-size:12px;color:#94A3B8;">CoFounder, EOLABS.IN</div></div>
            <div style="width:1px;height:36px;background:rgba(255,255,255,0.2);"></div>
            <div><div style="font-size:16px;font-weight:700;color:#FFF;">Dr. Surender Kumar</div>
                 <div style="font-size:12px;color:#94A3B8;">Senior Academic Research &amp; Empirical Corporate Finance</div></div>
            <div style="width:1px;height:36px;background:rgba(255,255,255,0.2);"></div>
            <div style="display:flex;flex-direction:column;align-items:center;">
                <div style="font-size:10px;font-weight:800;color:#64748B;text-transform:uppercase;letter-spacing:1px;">POWERED BY</div>
                <div style="font-size:16px;font-weight:800;color:#38BDF8;">EOLABS.IN</div></div>
        </div>`;
    }''')

def show_closing_card(page):
    page.evaluate('''() => {
        let ov = document.getElementById('demo-closing-ov');
        if (!ov) { ov = document.createElement('div'); ov.id = 'demo-closing-ov'; document.body.appendChild(ov); }
        Object.assign(ov.style, {
            position: 'fixed', top: '0', left: '0', width: '100vw', height: '100vh',
            zIndex: '99999998',
            background: 'radial-gradient(circle at 50% 40%, #0f172a 0%, #020617 100%)',
            color: '#FFF', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
            fontFamily: "'Inter', -apple-system, sans-serif", padding: '40px'
        });
        ov.innerHTML = `
        <div style="display:inline-block;padding:6px 18px;background:rgba(34,197,94,0.15);border:1px solid rgba(34,197,94,0.4);border-radius:30px;font-size:12px;font-weight:700;color:#4ade80;margin-bottom:20px;text-transform:uppercase;">
            AI Assistant Demonstration &bull; Recordly Verified Production Standard</div>
        <h1 style="font-size:42px;font-weight:800;margin:0 0 16px 0;text-align:center;">Financial Leverage and Corporate Life Stages</h1>
        <p style="font-size:17px;color:#94A3B8;max-width:780px;text-align:center;line-height:1.5;margin:0 0 35px 0;">
            Grounded in 25 Years of Microdata (2001-2025) &bull; Dickinson Cash-Flow Classification &bull; Stata 18 SE Core</p>
        <div style="display:flex;align-items:center;gap:36px;padding:18px 36px;background:rgba(30,41,59,0.7);border:1px solid rgba(255,255,255,0.1);border-radius:14px;box-shadow:0 10px 25px rgba(0,0,0,0.5);">
            <div><div style="font-size:16px;font-weight:700;">Dr. Sanjay Bhatia</div>
                 <div style="font-size:12px;color:#94A3B8;">CoFounder, EOLABS.IN</div></div>
            <div style="width:1px;height:32px;background:rgba(255,255,255,0.2);"></div>
            <div><div style="font-size:16px;font-weight:700;">Dr. Surender Kumar</div>
                 <div style="font-size:12px;color:#94A3B8;">Senior Academic Research &amp; Empirical Corporate Finance</div></div>
            <div style="width:1px;height:32px;background:rgba(255,255,255,0.2);"></div>
            <div style="display:flex;flex-direction:column;align-items:center;">
                <div style="font-size:11px;font-weight:800;color:#64748B;text-transform:uppercase;">POWERED BY</div>
                <div style="font-size:15px;font-weight:800;color:#38BDF8;">EOLABS.IN</div></div>
        </div>`;
    }''')

# ─────────────────────────────────────────────────────────────────────────────
# Scene Recorder Engine: Live Typing & Dynamic Response Generation
# ─────────────────────────────────────────────────────────────────────────────
def record_scene_recordly(browser, scene_item: dict) -> Path:
    sc = scene_item["data"]
    sid = sc["id"]
    duration = scene_item["duration"]
    mp3 = scene_item["mp3"]
    
    print(f"\n--- Recording Scene (Recordly Engine): {sid} (Duration: {duration:.2f}s) ---")
    
    # Always guarantee clean isolated session for every scene
    clean_database_chat_sessions()

    context = browser.new_context(
        viewport={"width": 1920, "height": 1080},
        record_video_dir=str(SCENE_DIR / "raw"),
        record_video_size={"width": 1920, "height": 1080},
    )
    t_init = time.time()
    page = context.new_page()

    is_title = (sid == "scene1_title_card")
    is_closing = (sid == "scene8_closing_card")

    # Navigate to page and ensure authenticated state
    page.goto(PAGE_URL, wait_until="networkidle", timeout=45000)
    
    login_btn = page.locator('button:has-text("Sign in"), button:has-text("Log in"), button[type="submit"]').first
    if login_btn.is_visible(timeout=2000):
        u = page.locator('input[type="text"]').first
        pw = page.locator('input[type="password"]').first
        if u.is_visible(): u.fill("drbhatia")
        if pw.is_visible(): pw.fill("admin123")
        login_btn.click()
        time.sleep(1.5)
        page.goto(PAGE_URL, wait_until="networkidle", timeout=45000)

    if is_title:
        show_title_card(page)
    elif is_closing:
        show_closing_card(page)
    else:
        page.wait_for_selector('text=AI Financial Assistant', timeout=30000)
        page.wait_for_selector('textarea[data-testid="stChatInputTextArea"]', timeout=30000)
        time.sleep(0.5)
        show_slim_hud(page, sc["tag"], sc["title"], sc["hud_desc"])

    # Mark exact time when UI is fully loaded and ready for live action
    t_ready = time.time() - t_init

    # Start audio clock
    t0 = time.time()
    audio_proc = subprocess.Popen(["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", str(mp3)],
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    if is_title or is_closing:
        time.sleep(duration)
    else:
        if sid == "scene2_assistant_overview":
            # Cue 0: Live typing & triggering the 6-layer inquiry
            cue0 = scene_item["cues"][0]
            chat_input = page.locator('textarea[data-testid="stChatInputTextArea"]').first
            if chat_input.is_visible(timeout=2000):
                chat_input.click()
                chat_input.type(sc.get("prompt", "Explain Pecking Order vs Trade-Off theories."), delay=15)
                time.sleep(0.2)
                page.keyboard.press("Enter")
                # Show 2s of working state on camera
                time.sleep(2.0)
                # Wait until generation finishes
                try:
                    page.wait_for_selector('text=Working', state='detached', timeout=25000)
                except Exception:
                    pass
                # Screen 3: Immediate top scroll
                scroll_up_immediate(page)
            
            # Cues 1-6: Sequential focal scrolling over the 6 layers
            anchors = [0, 160, 360, 580, 920, 1250]
            for idx in range(1, len(scene_item["cues"])):
                cue = scene_item["cues"][idx]
                target_y = anchors[min(idx - 1, len(anchors)-1)]
                focal_scroll(page, target_y)
                time.sleep(cue["duration"])

        elif sid == "scene3_infosys_tech":
            # Cue 0: Switch to CFO -> Infosys -> Live type exact prompt
            cfo_radio = page.locator('label:has-text("CFO")').first
            if cfo_radio.is_visible(timeout=1000):
                cfo_radio.click()
                time.sleep(0.5)
            infosys_btn = page.locator('button:has-text("Infosys")').first
            if infosys_btn.is_visible(timeout=1000):
                infosys_btn.click()
                time.sleep(0.4)

            chat_input = page.locator('textarea[data-testid="stChatInputTextArea"]').first
            if chat_input.is_visible(timeout=2000):
                chat_input.click()
                chat_input.type(sc.get("prompt", "As CFO of Infosys Ltd., analyze our baseline capital structure and cash-flow profile in Computer software. What Dickinson lifecycle stage are we currently in, and how does our 4.2% leverage compare to the IT software industry median?"), delay=15)
                time.sleep(0.2)
                page.keyboard.press("Enter")
                # Screen 2: Capture 2s of authentic Working state
                time.sleep(2.0)
                # Wait until generation finishes
                try:
                    page.wait_for_selector('text=Working', state='detached', timeout=25000)
                except Exception:
                    pass
                # Screen 3: Immediate instant scroll-up to top so prompt, telemetry, and badges are in full view
                scroll_up_immediate(page)

            # Screen 4: Focal scroll down through Narrative -> CFO Recommendations Table -> Chart -> Playbook
            anchors = [140, 360, 720, 520]
            for idx in range(1, len(scene_item["cues"])):
                cue = scene_item["cues"][idx]
                target_y = anchors[min(idx - 1, len(anchors)-1)]
                focal_scroll(page, target_y)
                time.sleep(cue["duration"])

        elif sid == "scene4_tata_steel_stress":
            # Cue 0: Select Tata Steel -> Live type Macro Stress Test query
            tata_btn = page.locator('button:has-text("Tata Steel")').first
            if tata_btn.is_visible(timeout=1000):
                tata_btn.click()
                time.sleep(0.5)

            chat_input = page.locator('textarea[data-testid="stChatInputTextArea"]').first
            if chat_input.is_visible(timeout=2000):
                chat_input.click()
                chat_input.type(sc.get("prompt", "Conduct a macro stress test for Tata Steel: if borrowing costs rise by 150 bps and steel spreads contract by 20%, what happens to our Interest Coverage Ratio against the 2.0x floor?"), delay=15)
                time.sleep(0.2)
                page.keyboard.press("Enter")
                time.sleep(2.0)
                try:
                    page.wait_for_selector('text=Working', state='detached', timeout=25000)
                except Exception:
                    pass
                scroll_up_immediate(page)

            # Focal scroll down through Covenant Breach Warning -> CFO Playbook
            anchors = [160, 280, 520]
            for idx in range(1, len(scene_item["cues"])):
                cue = scene_item["cues"][idx]
                target_y = anchors[min(idx - 1, len(anchors)-1)]
                focal_scroll(page, target_y)
                time.sleep(cue["duration"])

        elif sid == "scene5_airtel_indigo_pharma":
            focal_scroll(page, 0)
            time.sleep(scene_item["cues"][0]["duration"])

            # Cue 1: Bharti Airtel
            airtel_btn = page.locator('button:has-text("Bharti Airtel")').first
            if airtel_btn.is_visible(timeout=1000):
                airtel_btn.click()
                time.sleep(0.4)
            exec_2 = page.locator('button:has-text("Execute 🟡 2")').first
            if exec_2.is_visible(timeout=1000):
                exec_2.click()
                try:
                    page.wait_for_selector('text=Working', state='detached', timeout=20000)
                except Exception:
                    pass
                scroll_up_immediate(page)
            focal_scroll(page, 180)
            time.sleep(max(0.5, scene_item["cues"][1]["duration"] - 1.2))

            # Cue 2: IndiGo
            indigo_btn = page.locator('button:has-text("IndiGo")').first
            if indigo_btn.is_visible(timeout=1000):
                indigo_btn.click()
                time.sleep(0.4)
            exec_3 = page.locator('button:has-text("Execute 🟠 3")').first
            if exec_3.is_visible(timeout=1000):
                exec_3.click()
                try:
                    page.wait_for_selector('text=Working', state='detached', timeout=20000)
                except Exception:
                    pass
                scroll_up_immediate(page)
            focal_scroll(page, 220)
            time.sleep(max(0.5, scene_item["cues"][2]["duration"] - 1.2))

            # Cue 3: Sun Pharma
            pharma_btn = page.locator('button:has-text("Sun Pharma")').first
            if pharma_btn.is_visible(timeout=1000):
                pharma_btn.click()
                time.sleep(0.4)
            exec_4 = page.locator('button:has-text("Execute 🔴 4")').first
            if exec_4.is_visible(timeout=1000):
                exec_4.click()
                try:
                    page.wait_for_selector('text=Working', state='detached', timeout=20000)
                except Exception:
                    pass
                scroll_up_immediate(page)
            focal_scroll(page, 260)
            time.sleep(max(0.5, scene_item["cues"][3]["duration"] - 1.2))

        elif sid == "scene6_researcher_stata":
            res_radio = page.locator('label:has-text("Researcher")').first
            if res_radio.is_visible(timeout=1000):
                res_radio.click()
                time.sleep(0.5)

            # Cue 1: Live type Stata regression
            cue1 = scene_item["cues"][1]
            chat_input = page.locator('textarea[data-testid="stChatInputTextArea"]').first
            if chat_input.is_visible(timeout=2000):
                chat_input.click()
                chat_input.type(". xtreg leverage roa tang size, fe cluster(ind_code)", delay=15)
                time.sleep(0.2)
                page.keyboard.press("Enter")
                time.sleep(2.0)
                try:
                    page.wait_for_selector('text=Working', state='detached', timeout=20000)
                except Exception:
                    pass
                scroll_up_immediate(page)

            time.sleep(cue1["duration"])
            focal_scroll(page, 220)
            time.sleep(scene_item["cues"][2]["duration"])
            focal_scroll(page, 560)
            time.sleep(scene_item["cues"][3]["duration"])

        elif sid == "scene7_literature_vault":
            focal_scroll(page, 180)
            time.sleep(scene_item["cues"][0]["duration"])
            cit_badge = page.locator('button:has-text("Dickinson"), button:has-text("Myers")').first
            if cit_badge.is_visible(timeout=1000):
                cit_badge.click()
                time.sleep(1.0)
            focal_scroll(page, 240)
            time.sleep(max(0.5, scene_item["cues"][1]["duration"] - 1.0))
            focal_scroll(page, 380)
            time.sleep(scene_item["cues"][2]["duration"])

    elapsed = time.time() - t0
    rem = duration - elapsed
    if rem > 0:
        time.sleep(rem)

    audio_proc.poll()
    page.close()
    raw_video = page.video.path()
    context.close()

    scene_mp4 = SCENE_DIR / f"{sid}.mp4"
    # Precise offset trimming using -ss {t_ready:.3f} so video starts exactly on live UI action
    mux_cmd = [
        "ffmpeg", "-y",
        "-ss", f"{t_ready:.3f}",
        "-i", str(raw_video),
        "-i", str(mp3),
        "-t", f"{duration:.3f}",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
        "-c:a", "aac", "-b:a", "192k",
        str(scene_mp4)
    ]
    subprocess.run(mux_cmd, capture_output=True, check=True)
    print(f"  [scene] Muxed -> {scene_mp4.name} ({scene_mp4.stat().st_size / 1024 / 1024:.1f} MB)")
    return scene_mp4

# ─────────────────────────────────────────────────────────────────────────────
# Subtitle Generation (Fine-Grained SRT)
# ─────────────────────────────────────────────────────────────────────────────
def sec_to_srt_time(seconds: float) -> str:
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(round((seconds - int(seconds)) * 1000))
    if millis >= 1000:
        millis = 999
    return f"{hrs:02d}:{mins:02d}:{secs:02d},{millis:03d}"

def generate_fine_grained_srt(scene_manifest: list[dict], out_srt: Path):
    print("=== Step 2: Compiling Sentence-by-Sentence SRT Subtitles ===")
    lines = []
    cue_idx = 1
    cum_time = 0.0

    for sc_item in scene_manifest:
        for cue in sc_item["cues"]:
            t_start = cum_time + cue["start"]
            t_end   = cum_time + cue["end"]
            text    = cue["text"]

            words = text.split()
            mid = len(words) // 2
            if len(text) > 60 and mid > 0:
                wrapped_text = " ".join(words[:mid]) + "\n" + " ".join(words[mid:])
            else:
                wrapped_text = text

            lines.append(f"{cue_idx}")
            lines.append(f"{sec_to_srt_time(t_start)} --> {sec_to_srt_time(t_end)}")
            lines.append(wrapped_text)
            lines.append("")
            cue_idx += 1

        cum_time += sc_item["duration"]

    out_srt.write_text("\n".join(lines), encoding="utf-8")
    print(f"  [srt] Generated {cue_idx - 1} granular subtitle cues -> {out_srt.name}\n")

# ─────────────────────────────────────────────────────────────────────────────
# Master Concatenation & Styled Caption Burn
# ─────────────────────────────────────────────────────────────────────────────
def concatenate_and_burn_captions(scene_files: list[Path], srt_file: Path):
    print("=== Step 3: Concatenating Master MP4 & Burning Styled Captions ===")
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    
    ts_clean_mp4 = OUT / f"ai_chatbot_walkthrough_recordly_v4_{timestamp}_clean.mp4"
    ts_sub_mp4   = OUT / f"ai_chatbot_walkthrough_recordly_v4_{timestamp}_subtitled.mp4"
    ts_srt       = OUT / f"ai_chatbot_walkthrough_recordly_v4_{timestamp}.srt"
    
    final_clean = OUT / "ai_chatbot_master_walkthrough_v2.mp4"
    final_sub   = OUT / "ai_chatbot_master_walkthrough_v2_subtitled.mp4"

    concat_list = SCENE_DIR / "concat_list.txt"
    with open(concat_list, "w", encoding="utf-8") as f:
        for sf in scene_files:
            p_str = sf.resolve().as_posix()
            f.write(f"file '{p_str}'\n")

    # 1. Clean Master MP4
    concat_cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_list),
        "-c", "copy",
        str(ts_clean_mp4)
    ]
    subprocess.run(concat_cmd, capture_output=True, check=True)
    shutil.copy2(ts_clean_mp4, final_clean)
    print(f"  [master] Clean MP4: {ts_clean_mp4.name} ({ts_clean_mp4.stat().st_size / 1024 / 1024:.1f} MB)")

    # 2. Burned Subtitled MP4 with broadcast upper-white-space placement (MarginV=90 to avoid chat box)
    srt_escaped = str(srt_file.resolve()).replace("\\", "/").replace(":", "\\:")
    style = "FontName=Arial,FontSize=11,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BackColour=&H00000000,BorderStyle=1,Outline=1.5,Shadow=0.5,MarginV=90,Alignment=2"
    vf_arg = f"subtitles='{srt_escaped}':force_style='{style}'"

    burn_cmd = [
        "ffmpeg", "-y",
        "-i", str(ts_clean_mp4),
        "-vf", vf_arg,
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-c:a", "copy",
        str(ts_sub_mp4)
    ]
    subprocess.run(burn_cmd, capture_output=True, check=True)
    shutil.copy2(ts_sub_mp4, final_sub)
    shutil.copy2(srt_file, ts_srt)
    print(f"  [subtitled] Subtitled MP4: {ts_sub_mp4.name} ({ts_sub_mp4.stat().st_size / 1024 / 1024:.1f} MB)")
    print(f"  [srt] Timestamped SRT: {ts_srt.name}")
    return ts_clean_mp4, ts_sub_mp4, ts_srt

# ─────────────────────────────────────────────────────────────────────────────
# Main Orchestrator
# ─────────────────────────────────────────────────────────────────────────────
def main():
    print("=" * 75)
    print("AI Financial Assistant: Recordly Master Demo Walkthrough (Live Dynamic Run-Up)")
    print("=" * 75)
    t_start = time.time()

    manifest = prepare_all_audio()
    master_srt = OUT / "ai_chatbot_master_walkthrough_v2.srt"
    generate_fine_grained_srt(manifest, master_srt)

    print("=== Step 4: Recording Dynamic Synchronized Scenes with Recordly Engine ===")
    scene_mp4s = []
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--start-maximized",
                "--no-sandbox",
            ]
        )
        for sc_item in manifest:
            scene_mp4 = record_scene_recordly(browser, sc_item)
            scene_mp4s.append(scene_mp4)
        browser.close()

    ts_clean, ts_sub, ts_srt = concatenate_and_burn_captions(scene_mp4s, master_srt)

    total_time = time.time() - t_start
    print("\n" + "=" * 75)
    print(f"Recordly Master Walkthrough successfully generated in {total_time:.1f}s!")
    print(f"• Timestamped Clean Video:     {ts_clean.resolve()}")
    print(f"• Timestamped Subtitled Video: {ts_sub.resolve()}")
    print(f"• Timestamped Subtitles (SRT): {ts_srt.resolve()}")
    print(f"• Canonical Latest Video:      {OUT / 'ai_chatbot_master_walkthrough_v2.mp4'}")
    print(f"• Canonical Subtitled Video:   {OUT / 'ai_chatbot_master_walkthrough_v2_subtitled.mp4'}")
    print("=" * 75)

if __name__ == "__main__":
    main()

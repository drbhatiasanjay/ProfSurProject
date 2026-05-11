#!/usr/bin/env python3
"""
LifeCycle Leverage Dashboard — Automated Demo Recorder
=======================================================
Records SCREEN + YOUR VOICE section by section.
Playwright navigates automatically while you speak the narration shown on screen.
Whisper auto-transcribes your voice → SRT captions burned into video.

Usage:
    py -3.12 scripts/demo_recorder.py [--section 03]   # record one section only
    py -3.12 scripts/demo_recorder.py --concat-only    # stitch existing sections

Controls during recording:
    ENTER   → confirm and start recording next section
    S       → skip current section (move to next)
    Q       → quit after finishing current section
"""

import os, sys, time, subprocess, threading, re, ctypes, argparse
from pathlib import Path
from datetime import timedelta

# ── Configuration ─────────────────────────────────────────────────────────────
BASE_URL      = "http://localhost:8501"
MIC_DEVICE    = "Microphone (2- Brio 100)"   # change to "Microphone Array (Realtek(R) Audio)" if needed
OUTPUT_DIR    = Path("demo_output")
WHISPER_MODEL = "base"     # tiny=fastest, base=good balance, small=more accurate
FPS           = 30
LOGIN_USER    = "sbhatia"
LOGIN_PASS    = "UzBGwQ0DuH_Wgo0S"

# Detect primary screen resolution
_user32  = ctypes.windll.user32
SCREEN_W = _user32.GetSystemMetrics(0)
SCREEN_H = _user32.GetSystemMetrics(1)

OUTPUT_DIR.mkdir(exist_ok=True)


# ── Narration Script ──────────────────────────────────────────────────────────
SECTIONS = [
    {
        "id":       "01_login",
        "title":    "Welcome & Login",
        "url":      "/",
        "actions":  ["login"],
        "duration": 28,
        "narration": (
            "Welcome to the LifeCycle Leverage Dashboard — "
            "the only analytics platform that classifies listed Indian firms across "
            "8 Dickinson corporate life-cycle stages and runs theory-backed capital structure analysis. "
            "The platform has three access roles: admin, researcher, and guest viewer. "
            "I am logging in as Doctor Sanjay Bhatia with admin access."
        ),
    },
    {
        "id":       "02_dashboard",
        "title":    "Dashboard — 401 Firms · 24 Years · 8 Life Stages",
        "url":      "/Dashboard",
        "actions":  ["scroll_down", "scroll_up"],
        "duration": 45,
        "narration": (
            "The main dashboard gives an instant overview of our panel: "
            "401 B S E listed Indian firms, 8,677 firm-year observations, "
            "across 24 years from 2001 to 2024, classified into 8 Dickinson life-cycle stages. "
            "The stage distribution shows that Maturity firms carry the lowest leverage at 17 percent, "
            "while Decline firms carry the highest at 38 percent — "
            "directly consistent with pecking order theory. "
            "Each bar shows the leverage range within that stage, not just an average."
        ),
    },
    {
        "id":       "03_peer_benchmarks",
        "title":    "Peer Benchmarks — Stage-Aware Comparison",
        "url":      "/Peer_Benchmarks",
        "actions":  ["scroll_down", "scroll_up"],
        "duration": 42,
        "narration": (
            "Unlike traditional tools that benchmark by industry sector alone, "
            "this platform benchmarks your company against peers in the SAME life-cycle stage. "
            "A Growth-stage firm at 45 percent debt ratio is fundamentally different "
            "from a Decline-stage firm at the same ratio — even in the same sector. "
            "Select any of the 401 firms and instantly see where it sits "
            "relative to lifecycle-stage-matched and industry-matched peers."
        ),
    },
    {
        "id":       "04_scenarios",
        "title":    "Scenario Analysis — What-If OLS Modelling",
        "url":      "/Scenarios",
        "actions":  ["scroll_down", "scroll_up"],
        "duration": 40,
        "narration": (
            "The scenario analysis page runs live OLS regressions. "
            "Adjust profitability, tangibility, firm size, or dividend payout "
            "using the sliders and immediately see how predicted leverage changes. "
            "This page is pinned to the thesis panel so results match "
            "published coefficients exactly — fully reproducible."
        ),
    },
    {
        "id":       "05_data_explorer",
        "title":    "Data Explorer — Vintage-Tagged Panel",
        "url":      "/Data_Explorer",
        "actions":  ["scroll_down"],
        "duration": 28,
        "narration": (
            "The data explorer gives raw access to the full panel with vintage filtering. "
            "Switch between the original thesis panel from 2001 to 2024, "
            "and the CMIE 2025 rollforward that extends coverage to the latest year. "
            "Every row carries a vintage tag ensuring thesis reproducibility is never compromised."
        ),
    },
    {
        "id":       "06_life_stage_dynamics",
        "title":    "Life Stage Dynamics — Markov Transitions & Survival",
        "url":      "/Knowledge_Graph",
        "actions":  ["scroll_down", "scroll_up"],
        "duration": 50,
        "narration": (
            "This is one of the most analytically distinctive pages in the platform. "
            "The Markov transition matrix shows the probability of a firm moving "
            "from one life-cycle stage to another in a given year. "
            "For example, a Shakeout-3 firm has a 48.5 percent probability of transitioning to Maturity "
            "but only a 2 percent probability of falling to Decline. "
            "The Kaplan-Meier survival curve shows the median Maturity stage duration is 5.2 years, "
            "and the Maturity to Decline transition probability is 24 percent."
        ),
    },
    {
        "id":       "07_econometrics",
        "title":    "Econometrics — Fixed Effects & Hausman Test",
        "url":      "/Econometrics",
        "actions":  ["scroll_down", "scroll_up"],
        "duration": 50,
        "narration": (
            "The econometrics page runs O L S, Fixed Effects, and Random Effects regressions interactively. "
            "The Hausman test with a Chi-squared statistic of 225.53 and p-value of zero "
            "confirms Fixed Effects as the preferred specification. "
            "The key finding: profitability shows a NEGATIVE coefficient across all 8 life-cycle stages — "
            "universal confirmation of Myers' Pecking Order Theory for Indian listed firms."
        ),
    },
    {
        "id":       "08_ml_models",
        "title":    "Machine Learning — XGBoost + SHAP Explainability",
        "url":      "/ML_Models",
        "actions":  ["scroll_down", "scroll_up"],
        "duration": 45,
        "narration": (
            "The machine learning page trains Random Forest, XGBoost, and LightGBM models "
            "on the same panel data using stage-stratified cross-validation. "
            "SHAP feature importance charts reveal which determinants drive leverage predictions at each stage. "
            "Lagged leverage is consistently the dominant predictor — "
            "confirming that capital structure is sticky across all stages."
        ),
    },
    {
        "id":       "09_forecasting",
        "title":    "LSTM Forecasting — Firm-Level Leverage Trajectories",
        "url":      "/Forecasting",
        "actions":  ["scroll_down"],
        "duration": 35,
        "narration": (
            "The forecasting page applies LSTM and GRU deep learning networks "
            "trained on individual company leverage time series. "
            "Select any firm and see its projected leverage trajectory for the next three years. "
            "This is the first firm-level LSTM leverage forecasting tool built for Indian listed companies."
        ),
    },
    {
        "id":       "10_clustering",
        "title":    "Clustering — Validating the Dickinson Taxonomy",
        "url":      "/Clustering",
        "actions":  ["scroll_down"],
        "duration": 32,
        "narration": (
            "Does the Dickinson cash-flow rule actually recover meaningful financial archetypes? "
            "K-Means clustering on the full panel, compared against Dickinson stage labels, "
            "produces an Adjusted Rand Index above 0.6 — "
            "confirming that the cash-flow sign taxonomy recovers data-driven clusters "
            "and is not merely an arbitrary classification."
        ),
    },
    {
        "id":       "11_transitions",
        "title":    "Stage Transitions — 24-Year Heatmap",
        "url":      "/Transitions",
        "actions":  ["scroll_down"],
        "duration": 32,
        "narration": (
            "The transitions heatmap visualises how firms move across life-cycle stages year by year "
            "across the full 24-year panel. "
            "A striking finding: 28 Decline-stage and 17 Decay-stage firms "
            "returned to the Startup stage in the following year — "
            "what we call phoenix firms. "
            "This firm-level transition data is available for all 401 companies."
        ),
    },
    {
        "id":       "12_advanced_econometrics",
        "title":    "Advanced Econometrics — System GMM & Speed of Adjustment",
        "url":      "/Advanced_Econometrics",
        "actions":  ["scroll_down", "scroll_up"],
        "duration": 50,
        "narration": (
            "System GMM estimation handles endogeneity in dynamic panel models "
            "using Blundell-Bond instrumentation. "
            "The speed of adjustment — computed as one minus the lagged leverage coefficient — "
            "varies significantly by life-cycle stage. "
            "Decline-stage firms adjust toward their target leverage fastest, "
            "a signal of financial stress that no traditional credit tool currently captures. "
            "GFC 2008, IBC 2016, and COVID-19 shock dummies are all statistically significant."
        ),
    },
    {
        "id":       "13_interaction_effects",
        "title":    "Interaction Effects — Stage Moderation Analysis",
        "url":      "/Interaction_Effects",
        "actions":  ["scroll_down", "scroll_up"],
        "duration": 40,
        "narration": (
            "This page estimates how life-cycle stage moderates "
            "the profitability-leverage and tangibility-leverage relationships. "
            "Cross-term OLS with delta-method standard errors shows that "
            "the profitability effect on leverage is strongest at Maturity "
            "and insignificant at Growth — "
            "a theory-failure zone unique to Indian corporate finance."
        ),
    },
    {
        "id":       "14_admin_activity",
        "title":    "Admin Activity — Full Audit Trail",
        "url":      "/Admin_Activity",
        "actions":  ["scroll_down"],
        "duration": 30,
        "narration": (
            "Administrators see a complete activity log of every page visit, "
            "model run, and export, attributed to each user by role. "
            "The KPI strip shows active sessions, total page visits, and model runs. "
            "The usage heatmap reveals which pages and which users are most active. "
            "Guest users are identified by their display name, not the generic guest username."
        ),
    },
    {
        "id":       "15_board_export",
        "title":    "Board Export — One-Click Company Board Deck",
        "url":      "/Board_Export",
        "actions":  ["scroll_down", "scroll_up"],
        "duration": 52,
        "narration": (
            "Select any of the 401 companies and generate a complete board presentation in one click. "
            "Thirteen topics are covered: life-cycle stage classification, stage-peer benchmarking, "
            "leverage history, machine learning prediction, survival probability, "
            "scenario analysis, theory test results, and more. "
            "Preview each chart directly on screen, then download the full presentation "
            "as a PowerPoint file ready for the next board meeting or rating agency submission."
        ),
    },
    {
        "id":       "16_company_navigator",
        "title":    "Company Navigator — Interactive Network Explorer",
        "url":      "/Company_Navigator",
        "actions":  ["scroll_down"],
        "duration": 38,
        "narration": (
            "The Company Navigator renders an interactive network graph of all 401 firms. "
            "Ego graph mode shows a firm's direct peers by industry and life-cycle stage. "
            "Peer cluster mode groups all firms sharing the same stage. "
            "Stage map shows the full 401-firm ecosystem coloured by life-cycle stage. "
            "Click any node to instantly inspect that company's capital structure profile."
        ),
    },
]


# ── SRT Generator ─────────────────────────────────────────────────────────────
def _fmt_srt_time(seconds: float) -> str:
    td = timedelta(seconds=seconds)
    total_s = int(td.total_seconds())
    ms = int((td.total_seconds() - total_s) * 1000)
    h, rem = divmod(total_s, 3600)
    m, s   = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def transcribe_to_srt(audio_path: Path, srt_path: Path) -> None:
    from faster_whisper import WhisperModel
    print(f"  🎙 Transcribing with Whisper '{WHISPER_MODEL}'...")
    model = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")
    segments, _ = model.transcribe(str(audio_path), beam_size=5, language="en")
    lines = []
    for i, seg in enumerate(segments, 1):
        lines.append(str(i))
        lines.append(f"{_fmt_srt_time(seg.start)} --> {_fmt_srt_time(seg.end)}")
        lines.append(seg.text.strip())
        lines.append("")
    srt_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"  ✅ SRT: {srt_path.name}")


# ── ffmpeg Helpers ────────────────────────────────────────────────────────────
def start_recording(output_path: Path) -> subprocess.Popen:
    cmd = [
        "ffmpeg", "-y",
        # Screen
        "-f", "gdigrab",
        "-framerate", str(FPS),
        "-video_size", f"{SCREEN_W}x{SCREEN_H}",
        "-offset_x", "0", "-offset_y", "0",
        "-i", "desktop",
        # Microphone
        "-f", "dshow",
        "-i", f"audio={MIC_DEVICE}",
        # Encoding
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "20",
        "-c:a", "aac", "-ar", "44100", "-b:a", "128k",
        str(output_path),
    ]
    return subprocess.Popen(cmd, stdin=subprocess.PIPE,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def stop_recording(proc: subprocess.Popen) -> None:
    try:
        proc.stdin.write(b"q\n")
        proc.stdin.flush()
        proc.wait(timeout=20)
    except Exception:
        proc.terminate()
        proc.wait()


def extract_audio(video_path: Path, audio_path: Path) -> None:
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(video_path),
         "-vn", "-acodec", "pcm_s16le", "-ar", "16000", str(audio_path)],
        capture_output=True,
    )


def burn_captions(video_path: Path, srt_path: Path, output_path: Path) -> None:
    # Escape path for ffmpeg subtitles filter (Windows backslashes + colon)
    srt_str = str(srt_path.resolve()).replace("\\", "\\\\").replace(":", "\\:")
    style = (
        "FontSize=22,FontName=Arial,"
        "PrimaryColour=&Hffffff,"
        "BackColour=&HCC000000,"   # 80% opaque black
        "BorderStyle=4,"           # opaque background box
        "Alignment=2,"             # centre-bottom
        "MarginV=45"
    )
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(video_path),
         "-vf", f"subtitles='{srt_str}':force_style='{style}'",
         "-c:v", "libx264", "-preset", "medium", "-crf", "18",
         "-c:a", "copy", str(output_path)],
        capture_output=True,
    )


def add_title_card(video_path: Path, title: str, output_path: Path) -> None:
    """Prepend a 3-second black title card with white text."""
    safe_title = title.replace("'", "\\'").replace(":", "\\:")
    title_tmp = output_path.parent / f"_tc_{output_path.stem}.mp4"
    concat_txt = output_path.parent / f"_cl_{output_path.stem}.txt"

    # 1. Generate title card clip
    subprocess.run(
        ["ffmpeg", "-y",
         "-f", "lavfi", "-i",
         f"color=c=0x1a1d24:size={SCREEN_W}x{SCREEN_H}:duration=3:rate={FPS}",
         "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
         "-vf", (
             f"drawtext=text='{safe_title}':"
             f"fontcolor=white:fontsize=52:"
             f"x=(w-text_w)/2:y=(h-text_h)/2:"
             f"box=1:boxcolor=0x1a1d24@0.9:boxborderw=30"
         ),
         "-t", "3",
         "-c:v", "libx264", "-preset", "ultrafast",
         "-c:a", "aac", "-shortest",
         str(title_tmp)],
        capture_output=True,
    )

    # 2. Concat title card + section
    concat_txt.write_text(
        f"file '{title_tmp.resolve()}'\nfile '{video_path.resolve()}'\n",
        encoding="utf-8",
    )
    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0",
         "-i", str(concat_txt), "-c", "copy", str(output_path)],
        capture_output=True,
    )
    title_tmp.unlink(missing_ok=True)
    concat_txt.unlink(missing_ok=True)


def concat_all_sections(section_files: list, output_path: Path) -> None:
    concat_txt = OUTPUT_DIR / "_concat_final.txt"
    concat_txt.write_text(
        "\n".join(f"file '{f.resolve()}'" for f in section_files) + "\n",
        encoding="utf-8",
    )
    result = subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0",
         "-i", str(concat_txt), "-c", "copy", str(output_path)],
        capture_output=True,
    )
    concat_txt.unlink(missing_ok=True)
    if result.returncode != 0:
        print(f"  ⚠ Concat error: {result.stderr.decode()[-300:]}")


# ── Playwright Navigation ─────────────────────────────────────────────────────
def _playwright_navigate(section: dict, stop_event: threading.Event):
    """Run in a background thread. Uses sync playwright."""
    from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=["--start-maximized", "--disable-infobars"],
        )
        ctx  = browser.new_context(no_viewport=True)
        page = ctx.new_page()

        try:
            # ── Login (first section only / always safe to call) ──────────────
            page.goto(BASE_URL, wait_until="networkidle", timeout=30000)
            try:
                page.wait_for_selector('[data-testid="stTextInput"] input', timeout=8000)
                page.locator('[data-testid="stTextInput"] input').first.fill(LOGIN_USER)
                page.locator('input[type="password"]').first.fill(LOGIN_PASS)
                page.locator('button:has-text("Login")').first.click()
                page.wait_for_timeout(4000)
            except PWTimeout:
                pass  # already logged in or no login form

            # ── Navigate to section URL ───────────────────────────────────────
            target = BASE_URL + section["url"]
            page.goto(target, wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(3000)

            # ── Perform actions ───────────────────────────────────────────────
            for action in section.get("actions", []):
                if stop_event.is_set():
                    break
                if action == "scroll_down":
                    page.evaluate("window.scrollBy({top: 600, behavior: 'smooth'})")
                    page.wait_for_timeout(2500)
                    page.evaluate("window.scrollBy({top: 600, behavior: 'smooth'})")
                    page.wait_for_timeout(2500)
                elif action == "scroll_up":
                    page.evaluate("window.scrollTo({top: 0, behavior: 'smooth'})")
                    page.wait_for_timeout(2000)
                elif action == "login":
                    pass  # already handled above

            # Hold the page open until stop_event
            while not stop_event.is_set():
                page.wait_for_timeout(500)

        except Exception as e:
            print(f"\n  ⚠ Playwright: {e}")
        finally:
            browser.close()


# ── Section Recorder ──────────────────────────────────────────────────────────
def record_section(section: dict) -> Path | None:
    sid       = section["id"]
    title     = section["title"]
    narration = section["narration"]
    duration  = section["duration"]

    raw_video  = OUTPUT_DIR / f"{sid}_raw.mp4"
    wav_audio  = OUTPUT_DIR / f"{sid}_audio.wav"
    srt_file   = OUTPUT_DIR / f"{sid}.srt"
    captioned  = OUTPUT_DIR / f"{sid}_captioned.mp4"
    final_out  = OUTPUT_DIR / f"{sid}_FINAL.mp4"

    if final_out.exists():
        ans = input(f"  ⚠ {final_out.name} exists. Re-record? [y/N]: ").strip().lower()
        if ans != "y":
            print(f"  ↩ Skipping — using existing file.")
            return final_out

    print(f"\n{'═'*64}")
    print(f"  📽  {title}")
    print(f"{'═'*64}")
    print(f"\n  📝 NARRATION — read this aloud after recording starts:\n")
    # Print narration with word-wrap at 65 chars
    words, line = narration.split(), ""
    for w in words:
        if len(line) + len(w) + 1 > 65:
            print(f"     {line}")
            line = w
        else:
            line = (line + " " + w).strip()
    if line:
        print(f"     {line}")

    print(f"\n  ⏱  Duration: {duration}s  |  Mic: {MIC_DEVICE}")
    print(f"\n  Press ENTER to START recording  (S=skip, Q=quit after this)")
    key = input("  > ").strip().lower()
    if key == "s":
        print("  ↩ Skipped.")
        return None
    if key == "q":
        print("  🛑 Quit requested.")
        sys.exit(0)

    # Start Playwright in background thread
    stop_evt = threading.Event()
    nav_thread = threading.Thread(
        target=_playwright_navigate, args=(section, stop_evt), daemon=True
    )
    nav_thread.start()
    time.sleep(2)  # give browser time to open

    # Start ffmpeg recording
    print(f"\n  🔴 RECORDING — speak your narration now!\n")
    ffmpeg_proc = start_recording(raw_video)
    time.sleep(1)  # ffmpeg warm-up

    # Countdown timer
    t0 = time.time()
    try:
        while True:
            elapsed   = time.time() - t0
            remaining = duration - elapsed
            if remaining <= 0:
                break
            bar = "█" * int(20 * elapsed / duration) + "░" * int(20 * remaining / duration)
            print(f"\r  [{bar}] {remaining:.0f}s left  ", end="", flush=True)
            time.sleep(0.4)
    except KeyboardInterrupt:
        print("\n  ⏹ Stopped early by Ctrl+C")

    print(f"\n  ⏹ Stopping recording...")
    stop_evt.set()
    stop_recording(ffmpeg_proc)
    nav_thread.join(timeout=8)
    print(f"  ✅ Raw video: {raw_video.name} ({raw_video.stat().st_size//1024} KB)")

    # Extract audio for Whisper
    print(f"  📤 Extracting audio...")
    extract_audio(raw_video, wav_audio)

    # Transcribe → SRT
    transcribe_to_srt(wav_audio, srt_file)
    wav_audio.unlink(missing_ok=True)

    # Burn captions
    print(f"  🖊  Burning captions into video...")
    burn_captions(raw_video, srt_file, captioned)

    # Add title card
    print(f"  🎬 Adding title card...")
    add_title_card(captioned, title, final_out)

    # Clean intermediates
    captioned.unlink(missing_ok=True)

    size_mb = final_out.stat().st_size / 1024 / 1024
    print(f"  ✅ Section complete: {final_out.name}  ({size_mb:.1f} MB)")
    return final_out


# ── Entry Point ───────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="LifeCycle Leverage Demo Recorder")
    parser.add_argument("--section", help="Record only this section id prefix (e.g. 03)")
    parser.add_argument("--concat-only", action="store_true",
                        help="Skip recording; just stitch existing *_FINAL.mp4 files")
    args = parser.parse_args()

    print("\n" + "="*64)
    print("  LifeCycle Leverage Dashboard — Demo Recorder")
    print(f"  Screen: {SCREEN_W}×{SCREEN_H}  |  Mic: {MIC_DEVICE}")
    print(f"  Output: {OUTPUT_DIR.resolve()}")
    print("="*64)

    # Collect which sections to record
    sections = SECTIONS
    if args.section:
        sections = [s for s in SECTIONS if s["id"].startswith(args.section)]
        if not sections:
            print(f"  ❌ No section matching '{args.section}'")
            sys.exit(1)

    if args.concat_only:
        existing = sorted(OUTPUT_DIR.glob("*_FINAL.mp4"))
        if not existing:
            print("  ❌ No *_FINAL.mp4 files found in demo_output/")
            sys.exit(1)
        print(f"  Found {len(existing)} section files to stitch.")
        final_demo = OUTPUT_DIR / "demo_FULL.mp4"
        concat_all_sections(existing, final_demo)
        print(f"\n  ✅ Final demo: {final_demo.resolve()}")
        print(f"     Size: {final_demo.stat().st_size / 1024 / 1024:.1f} MB")
        return

    print(f"\n  {len(sections)} section(s) to record. Total ~{sum(s['duration'] for s in sections)//60}min.")
    print(f"  Make sure Streamlit is running: streamlit run app.py\n")
    input("  Press ENTER when ready to begin...")

    completed = []
    for section in sections:
        result = record_section(section)
        if result:
            completed.append(result)

    if len(completed) > 1:
        print(f"\n{'='*64}")
        print(f"  🎬 Stitching {len(completed)} sections → demo_FULL.mp4")
        final_demo = OUTPUT_DIR / "demo_FULL.mp4"
        concat_all_sections(completed, final_demo)
        size_mb = final_demo.stat().st_size / 1024 / 1024
        print(f"  ✅ DONE!  {final_demo.resolve()}")
        print(f"     {len(completed)} sections · {size_mb:.1f} MB")
    elif len(completed) == 1:
        print(f"\n  ✅ Single section recorded: {completed[0].resolve()}")

    print("\n  Recording session complete.\n")


if __name__ == "__main__":
    main()

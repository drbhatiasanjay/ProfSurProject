#!/usr/bin/env python3
"""
LifeCycle Leverage Dashboard — Automated Demo Recorder
=======================================================
Fully automated: Playwright navigates, edge-tts narrates, captions generated
from script text.  No microphone required.

Output layout:
    demo_output/          intermediate files (raw video, TTS audio, SRT, FINALs)
    videos/               final stitched demos named by date + time
      lifecycle_leverage_demo_YYYY-MM-DD_HH-MM-SS.mp4

Usage:
    py -3.12 scripts/demo_recorder.py               # record all sections
    py -3.12 scripts/demo_recorder.py --section 03  # record one section
    py -3.12 scripts/demo_recorder.py --concat-only # stitch existing FINALs
"""

import asyncio, os, sys, time, subprocess, threading, json, argparse
from pathlib import Path
from datetime import timedelta, datetime

# Force UTF-8 output on Windows terminals
import io
if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# ── Configuration ─────────────────────────────────────────────────────────────
BASE_URL   = "http://localhost:8501"
OUTPUT_DIR = Path("demo_output")
VIDEOS_DIR = Path("videos")
FPS        = 30
LOGIN_USER = "sbhatia"
LOGIN_PASS = "UzBGwQ0DuH_Wgo0S"
TTS_VOICE  = "en-IN-NeerjaNeural"   # Indian English — clear, professional
TTS_RATE   = "+0%"                  # normal speed
TTS_BUFFER = 3                      # extra seconds of screen recording after TTS ends
CAPTION_WORDS_PER_LINE = 10         # words per subtitle chunk

# Recording viewport dimensions — match screen resolution
# H.264 requires even dimensions; detect via ctypes on Windows
try:
    import ctypes as _ct
    _u32     = _ct.windll.user32
    SCREEN_W = _u32.GetSystemMetrics(0) & ~1
    SCREEN_H = _u32.GetSystemMetrics(1) & ~1
except Exception:
    SCREEN_W, SCREEN_H = 1920, 1080

OUTPUT_DIR.mkdir(exist_ok=True)
VIDEOS_DIR.mkdir(exist_ok=True)


# ── Narration Script ──────────────────────────────────────────────────────────
SECTIONS = [
    {
        "id":       "01_login",
        "title":    "Welcome & Login",
        "url":      "/",
        "actions":  ["login"],
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
        "nav_title": "Dashboard",
        "page_url": "/",
        "actions":  ["scroll_down", "scroll_up"],
        "narration": (
            "The main dashboard gives an instant overview of our panel: "
            "401 BSE-listed Indian firms, 8,677 firm-year observations, "
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
        "nav_title": "Peer Benchmarks",
        "page_url": "/peer_benchmarks",
        "actions":  ["select_company:Reliance", "wait:2", "scroll_down", "scroll_up"],
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
        "nav_title": "Scenarios",
        "page_url": "/scenarios",
        "actions":  ["scroll_down", "scroll_up"],
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
        "nav_title": "Data Explorer",
        "page_url": "/data_explorer",
        "actions":  ["scroll_down"],
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
        "nav_title": "Life Stage Dynamics",
        "page_url": "/life_stage_dynamics",
        "actions":  ["scroll_slow", "click_tab:1", "wait:2", "scroll_down", "click_tab:4", "wait:2", "scroll_down"],
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
        "nav_title": "Econometrics Lab",
        "page_url": "/econometrics",
        "actions":  ["scroll_down", "click_primary_button", "wait:3", "scroll_down", "scroll_up"],
        "narration": (
            "The econometrics page runs OLS, Fixed Effects, and Random Effects regressions interactively. "
            "The Hausman test with a Chi-squared statistic of 225.53 and p-value of zero "
            "confirms Fixed Effects as the preferred specification. "
            "The key finding: profitability shows a negative coefficient across all 8 life-cycle stages — "
            "universal confirmation of Myers' Pecking Order Theory for Indian listed firms."
        ),
    },
    {
        "id":       "08_ml_models",
        "title":    "Machine Learning — XGBoost + SHAP Explainability",
        "url":      "/ML_Models",
        "nav_title": "ML Models",
        "page_url": "/ml_models",
        "actions":  ["scroll_down", "click_primary_button", "wait:5", "scroll_down", "scroll_up"],
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
        "nav_title": "Forecasting",
        "page_url": "/forecasting",
        "actions":  ["scroll_down"],
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
        "nav_title": "Clustering",
        "page_url": "/clustering",
        "actions":  ["scroll_down"],
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
        "nav_title": "Transitions",
        "page_url": "/transitions",
        "actions":  ["scroll_down"],
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
        "nav_title": "Advanced Econometrics",
        "page_url": "/advanced_econometrics",
        "actions":  ["scroll_down", "click_primary_button", "wait:4", "scroll_down", "scroll_up"],
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
        "nav_title": "Interaction Effects",
        "page_url": "/interaction_effects",
        "actions":  ["scroll_down", "scroll_up"],
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
        "nav_title": "Activity Log",
        "page_url": "/admin_activity",
        "actions":  ["scroll_down"],
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
        "nav_title": "Board Deck",
        "page_url": "/board_export",
        "actions":  ["select_company:Reliance", "wait:2", "click_primary_button", "wait:4", "scroll_slow", "scroll_up"],
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
        "nav_title": "Company Navigator",
        "page_url": "/company_navigator",
        "actions":  ["scroll_down", "click_tab:1", "wait:2", "scroll_down"],
        "narration": (
            "The Company Navigator renders an interactive network graph of all 401 firms. "
            "Ego graph mode shows a firm's direct peers by industry and life-cycle stage. "
            "Peer cluster mode groups all firms sharing the same stage. "
            "Stage map shows the full 401-firm ecosystem coloured by life-cycle stage. "
            "Click any node to instantly inspect that company's capital structure profile."
        ),
    },
]


# ── TTS Narration ─────────────────────────────────────────────────────────────
def generate_tts_audio(text: str, output_path: Path) -> bool:
    """Generate speech audio from text using edge-tts. Returns True on success."""
    import edge_tts

    async def _run():
        communicate = edge_tts.Communicate(text, TTS_VOICE, rate=TTS_RATE)
        await communicate.save(str(output_path))

    try:
        asyncio.run(_run())
        return output_path.exists() and output_path.stat().st_size > 0
    except Exception as e:
        print(f"  [WARN] TTS failed: {e}")
        return False


# ── SRT Generator (script-based, no Whisper) ──────────────────────────────────
def _fmt_srt_time(seconds: float) -> str:
    total_s = int(seconds)
    ms = int((seconds - total_s) * 1000)
    h, rem = divmod(total_s, 3600)
    m, s   = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def text_to_srt(narration: str, tts_duration_s: float, srt_path: Path,
                audio_offset_s: float = 0.0) -> None:
    """Build SRT from narration text chunked into subtitle lines.

    Distributes chunks proportionally across the TTS duration.
    audio_offset_s shifts all timestamps so captions appear in sync with
    the TTS audio after the preamble delay.
    """
    words = narration.split()
    chunks = []
    for i in range(0, len(words), CAPTION_WORDS_PER_LINE):
        chunks.append(" ".join(words[i:i + CAPTION_WORDS_PER_LINE]))

    if not chunks:
        srt_path.write_text("", encoding="utf-8")
        return

    chunk_dur = tts_duration_s / len(chunks)
    lines = []
    for i, chunk in enumerate(chunks):
        start = audio_offset_s + i * chunk_dur
        end   = audio_offset_s + (i + 1) * chunk_dur - 0.05
        lines.append(str(i + 1))
        lines.append(f"{_fmt_srt_time(start)} --> {_fmt_srt_time(end)}")
        lines.append(chunk)
        lines.append("")

    srt_path.write_text("\n".join(lines), encoding="utf-8")


# ── ffmpeg Helpers ────────────────────────────────────────────────────────────
def start_recording(output_path: Path) -> subprocess.Popen:
    """Screen-only recording (no microphone). Silent video; TTS mixed in post."""
    cmd = [
        "ffmpeg", "-y",
        "-f", "gdigrab",
        "-framerate", str(FPS),
        "-video_size", f"{SCREEN_W}x{SCREEN_H}",
        "-offset_x", "0", "-offset_y", "0",
        "-i", "desktop",
        # Silent audio track so concat doesn't break
        "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "20",
        "-c:a", "aac", "-ar", "44100", "-b:a", "64k",
        "-shortest",
        str(output_path),
    ]
    return subprocess.Popen(cmd, stdin=subprocess.PIPE,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def stop_recording(proc: subprocess.Popen) -> None:
    try:
        proc.stdin.write(b"q\n")
        proc.stdin.flush()
        proc.wait(timeout=25)
    except Exception:
        proc.terminate()
        proc.wait()


def get_video_duration(path: Path) -> float:
    """Return duration in seconds via ffprobe JSON."""
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json",
         "-show_format", str(path)],
        capture_output=True, text=True,
    )
    try:
        return float(json.loads(result.stdout)["format"]["duration"])
    except Exception:
        return 0.0


def mix_tts_into_video(video_path: Path, tts_audio_path: Path, output_path: Path,
                        audio_delay_s: float = 2.0) -> None:
    """Replace silent video track with TTS audio (with optional delay)."""
    # adelay inserts silence before TTS starts, so narration begins after page loads
    delay_ms = int(audio_delay_s * 1000)
    tmp = output_path.parent / f"_mix_{output_path.name}"
    result = subprocess.run(
        ["ffmpeg", "-y",
         "-i", str(video_path),
         "-i", str(tts_audio_path),
         "-filter_complex",
         f"[1:a]adelay={delay_ms}|{delay_ms}[delayed];"
         f"[delayed]apad[padded]",
         "-map", "0:v",
         "-map", "[padded]",
         "-c:v", "copy",
         "-c:a", "aac", "-ar", "44100", "-b:a", "192k",
         "-shortest",
         str(tmp)],
        capture_output=True,
    )
    if result.returncode == 0 and tmp.exists():
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if output_path.exists():
            output_path.unlink()
        tmp.rename(output_path)
    else:
        tmp.unlink(missing_ok=True)
        # Fall back: copy video as-is (silent)
        import shutil
        shutil.copy2(str(video_path), str(output_path))
        print(f"  [WARN] TTS mix failed — video has no audio")


def normalise_audio(path: Path) -> None:
    """Loudness-normalise audio in-place (I=-16 LUFS, single-pass)."""
    tmp = path.parent / f"_norm_{path.name}"
    result = subprocess.run(
        ["ffmpeg", "-y", "-i", str(path),
         "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
         "-c:v", "copy",
         "-c:a", "aac", "-ar", "44100", "-b:a", "192k",
         str(tmp)],
        capture_output=True,
    )
    if result.returncode == 0 and tmp.exists():
        path.unlink(missing_ok=True)
        tmp.rename(path)
    else:
        tmp.unlink(missing_ok=True)
        print(f"  [WARN] loudnorm failed — keeping original audio")


def add_fades(path: Path, fade_duration: float = 0.5) -> None:
    """Add video + audio fade-in and fade-out in-place."""
    dur = get_video_duration(path)
    if dur <= fade_duration * 3:
        return
    fade_out_start = dur - fade_duration
    vf = (f"fade=t=in:st=0:d={fade_duration},"
          f"fade=t=out:st={fade_out_start:.3f}:d={fade_duration}")
    af = (f"afade=t=in:st=0:d={fade_duration},"
          f"afade=t=out:st={fade_out_start:.3f}:d={fade_duration}")
    tmp = path.parent / f"_fade_{path.name}"
    result = subprocess.run(
        ["ffmpeg", "-y", "-i", str(path),
         "-vf", vf, "-af", af,
         "-c:v", "libx264", "-preset", "medium", "-crf", "18",
         "-c:a", "aac", "-b:a", "192k",
         str(tmp)],
        capture_output=True,
    )
    if result.returncode == 0 and tmp.exists():
        path.unlink(missing_ok=True)
        tmp.rename(path)
    else:
        tmp.unlink(missing_ok=True)
        print(f"  [WARN] fade failed — keeping original")


def burn_captions(video_path: Path, srt_path: Path, output_path: Path) -> None:
    """Burn SRT subtitles into video."""
    import re
    # Windows ffmpeg subtitles filter needs C\:/ format (forward slashes, escaped drive colon)
    srt_str = re.sub(r"([A-Za-z]):", r"\1\\:",
                     str(srt_path.resolve()).replace("\\", "/"))
    style = (
        "FontSize=28,FontName=Arial,"
        "PrimaryColour=&Hffffff,"
        "BackColour=&HCC000000,"
        "BorderStyle=4,"
        "Alignment=2,"
        "MarginV=45"
    )
    result = subprocess.run(
        ["ffmpeg", "-y", "-i", str(video_path),
         "-vf", f"subtitles='{srt_str}':force_style='{style}'",
         "-c:v", "libx264", "-preset", "medium", "-crf", "18",
         "-c:a", "copy", str(output_path)],
        capture_output=True,
    )
    if result.returncode != 0:
        # If subtitle burn fails, copy video without captions
        import shutil
        shutil.copy2(str(video_path), str(output_path))
        print(f"  [WARN] Caption burn failed — video without subtitles")


def add_title_card(video_path: Path, title: str, output_path: Path) -> None:
    """Prepend a 3-second dark title card with white text."""
    safe_title = title.replace("'", "\\'").replace(":", "\\:")
    title_tmp   = output_path.parent / f"_tc_{output_path.stem}.mp4"
    concat_txt  = output_path.parent / f"_cl_{output_path.stem}.txt"

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


def make_bookend_card(lines: list, duration: int, output_path: Path) -> "Path | None":
    """Generate a full-screen dark card with multiple centred text lines + TTS narration."""
    if output_path.exists():
        return output_path
    line_h  = 70
    total_h = len(lines) * line_h
    start_y = f"(h-{total_h})/2"
    filters = []
    for i, text in enumerate(lines):
        safe = text.replace("'", "\\'").replace(":", "\\:").replace("&", "and")
        font_size = 54 if i == 0 else (36 if i == 1 else 28)
        color = "white" if i == 0 else ("#94A3B8" if i > 1 else "#CBD5E1")
        y_expr = f"{start_y}+{i * line_h}" if i > 0 else start_y
        filters.append(
            f"drawtext=text='{safe}':fontcolor={color}:fontsize={font_size}:"
            f"x=(w-text_w)/2:y={y_expr}:box=0"
        )
    vf = ",".join(filters)
    # Generate with silent audio; TTS not added to bookend cards
    result = subprocess.run(
        ["ffmpeg", "-y",
         "-f", "lavfi", "-i",
         f"color=c=0x0f1117:size={SCREEN_W}x{SCREEN_H}:duration={duration}:rate={FPS}",
         "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
         "-vf", vf,
         "-t", str(duration),
         "-c:v", "libx264", "-preset", "ultrafast",
         "-c:a", "aac", "-shortest",
         str(output_path)],
        capture_output=True,
    )
    if result.returncode != 0:
        print(f"  [WARN] Bookend card error: {result.stderr.decode()[-200:]}")
        return None
    return output_path


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
        print(f"  [WARN] Concat error: {result.stderr.decode()[-300:]}")


def embed_chapters(video_path: Path, chapter_list: list) -> None:
    """Embed chapter markers into video_path in-place.

    chapter_list: [(title, start_ms, end_ms), ...]
    """
    meta_path = video_path.parent / "_chapters.txt"
    lines = [
        ";FFMETADATA1",
        "title=LifeCycle Leverage Dashboard Demo",
        "artist=Dr. Sanjay Bhatia and Prof. Surendra Kumar",
        "comment=Capital Structure Analytics - 401 Indian Firms 24 Years 8 Life Stages",
        "",
    ]
    for title, start_ms, end_ms in chapter_list:
        lines += [
            "[CHAPTER]",
            "TIMEBASE=1/1000",
            f"START={int(start_ms)}",
            f"END={int(end_ms)}",
            f"title={title}",
            "",
        ]
    meta_path.write_text("\n".join(lines), encoding="utf-8")

    tmp = video_path.parent / f"_ch_{video_path.name}"
    result = subprocess.run(
        ["ffmpeg", "-y",
         "-i", str(video_path),
         "-i", str(meta_path),
         "-map_metadata", "1",
         "-codec", "copy",
         str(tmp)],
        capture_output=True,
    )
    meta_path.unlink(missing_ok=True)
    if result.returncode == 0 and tmp.exists():
        video_path.unlink(missing_ok=True)
        tmp.rename(video_path)
    else:
        tmp.unlink(missing_ok=True)
        print(f"  [WARN] Chapter embedding failed")


def _print_post_production_report(clip_info: list, final_path: Path) -> None:
    print(f"\n  {'─'*58}")
    print(f"  {'Section':<34}  {'Duration':>8}  {'Size':>7}")
    print(f"  {'─'*34}  {'─'*8}  {'─'*7}")
    total_s, total_b = 0, 0
    for label, dur_s, size_b in clip_info:
        m, s = divmod(int(dur_s), 60)
        print(f"  {label:<34}  {m}:{s:02d}     {size_b/1024/1024:>5.1f} MB")
        total_s += dur_s
        total_b += size_b
    print(f"  {'─'*34}  {'─'*8}  {'─'*7}")
    tm, ts_ = divmod(int(total_s), 60)
    print(f"  {'TOTAL':<34}  {tm}:{ts_:02d}     {total_b/1024/1024:>5.1f} MB")
    print(f"  {'─'*58}")
    print(f"\n  Final: {final_path.resolve()}")


def _stitch_with_bookends(section_files: list) -> None:
    """Generate intro + outro cards, stitch all, embed chapters, print report."""
    print(f"\n{'='*64}")
    print(f"  Building intro + outro cards...")

    intro = make_bookend_card(
        lines=[
            "LifeCycle Leverage Dashboard",
            "Capital Structure Analytics - 401 Indian Firms 24 Years 8 Life Stages",
            "Dr. Sanjay Bhatia  and  Prof. Surendra Kumar, University of Delhi",
            "github.com/drbhatiasanjay/ProfSurProject",
        ],
        duration=6,
        output_path=OUTPUT_DIR / "_intro_card.mp4",
    )
    outro = make_bookend_card(
        lines=[
            "Thank You",
            "LifeCycle Leverage Dashboard",
            "github.com/drbhatiasanjay/ProfSurProject",
            "Contact: drbhatiasanjay@gmail.com",
        ],
        duration=5,
        output_path=OUTPUT_DIR / "_outro_card.mp4",
    )

    all_files = []
    if intro:
        all_files.append(intro)
    all_files.extend(section_files)
    if outro:
        all_files.append(outro)

    ts         = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    fname      = f"lifecycle_leverage_demo_{ts}.mp4"
    final_demo = VIDEOS_DIR / fname
    print(f"  Stitching {len(all_files)} clips → {fname}")
    concat_all_sections(all_files, final_demo)

    print(f"  Embedding chapter markers...")
    clip_info    = []
    chapter_list = []
    cursor_ms    = 0.0

    clip_labels = (
        ["Introduction"] +
        [_section_label(f) for f in section_files] +
        (["Closing"] if outro else [])
    )
    for clip_path, label in zip(all_files, clip_labels):
        dur_s  = get_video_duration(clip_path)
        size_b = clip_path.stat().st_size
        clip_info.append((label, dur_s, size_b))
        end_ms = cursor_ms + dur_s * 1000
        chapter_list.append((label, cursor_ms, end_ms))
        cursor_ms = end_ms

    embed_chapters(final_demo, chapter_list)
    _print_post_production_report(clip_info, final_demo)
    print(f"\n  DONE - {len(section_files)} sections + intro + outro")
    print(f"\n  VIDEO READY: {final_demo.resolve()}\n")


def _section_label(path: Path) -> str:
    for sec in SECTIONS:
        if path.stem.startswith(sec["id"]):
            return sec["title"]
    return path.stem.replace("_FINAL", "").replace("_", " ").title()


# ── Win32 helpers removed — Playwright viewport recording handles capture ─────
    return set(hwnds)


# ── Playwright Navigation + Viewport Recording ────────────────────────────────
def _playwright_navigate(section: dict, stop_event: threading.Event,
                          nav_ready: threading.Event,
                          video_result: list, preamble_result: list):
    """Run in background thread.

    Uses Playwright's built-in viewport recording — captures browser content
    directly without gdigrab/HWND tracking.  The recording is independent of
    window z-order or OS focus, so other windows on screen don't matter.
    """
    from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

    video_dir = OUTPUT_DIR / "pw_vid_tmp"
    video_dir.mkdir(exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,   # headed so user can see progress; recording is viewport-only
            args=[
                f"--window-size={SCREEN_W},{SCREEN_H}",
                "--window-position=0,0",
                "--disable-infobars",
                "--noerrdialogs",
            ],
        )
        ctx = browser.new_context(
            viewport={"width": SCREEN_W, "height": SCREEN_H},
            record_video_dir=str(video_dir),
            record_video_size={"width": SCREEN_W, "height": SCREEN_H},
        )
        page_created_time = time.time()
        page = ctx.new_page()

        try:
            # Login — "load" avoids Streamlit WebSocket networkidle deadlock
            page.goto(BASE_URL, wait_until="load", timeout=30000)
            page.wait_for_timeout(2000)
            try:
                page.wait_for_selector('[data-testid="stTextInput"] input', timeout=8000)
                page.locator('[data-testid="stTextInput"] input').first.fill(LOGIN_USER)
                page.locator('input[type="password"]').first.fill(LOGIN_PASS)
                page.locator('button:has-text("Login")').first.click()
                page.wait_for_timeout(4000)
            except PWTimeout:
                pass  # already logged in or no login form

            page_path = section.get("page_url", "")

            if not page_path or page_path == "/":
                # Section 01 (login) or Dashboard — already on root after login
                page.wait_for_timeout(2000)
            else:
                # Navigate directly by URL using file-derived underscore slugs
                # (Streamlit 1.48.1 st.navigation() uses file names → underscores)
                target_url = BASE_URL + page_path
                print(f"\n  [NAV] goto {target_url}")
                page.goto(target_url, wait_until="load", timeout=30000)
                page.wait_for_timeout(2000)
                # Re-login if auth cookie didn't survive new WebSocket session
                try:
                    page.wait_for_selector('[data-testid="stTextInput"] input',
                                           timeout=5000)
                    page.locator('[data-testid="stTextInput"] input').first.fill(LOGIN_USER)
                    page.locator('input[type="password"]').first.fill(LOGIN_PASS)
                    page.locator('button:has-text("Login")').first.click()
                    page.wait_for_timeout(5000)
                    # After login Streamlit may redirect to root — go to target again
                    page.goto(target_url, wait_until="load", timeout=30000)
                    page.wait_for_timeout(4000)
                except PWTimeout:
                    pass  # already authenticated, page loaded directly

            page.wait_for_timeout(2000)  # final render settle

            # Signal ready; record preamble so TTS delay can be aligned
            preamble_result.append(time.time() - page_created_time)
            nav_ready.set()

            # Perform actions
            for action in section.get("actions", []):
                if stop_event.is_set():
                    break
                if action == "scroll_down":
                    page.evaluate("window.scrollBy({top: 600, behavior: 'smooth'})")
                    page.wait_for_timeout(2500)
                    page.evaluate("window.scrollBy({top: 600, behavior: 'smooth'})")
                    page.wait_for_timeout(2500)
                elif action == "scroll_slow":
                    for _ in range(4):
                        page.evaluate("window.scrollBy({top: 280, behavior: 'smooth'})")
                        page.wait_for_timeout(1800)
                elif action == "scroll_up":
                    page.evaluate("window.scrollTo({top: 0, behavior: 'smooth'})")
                    page.wait_for_timeout(2000)
                elif action == "login":
                    pass
                elif action.startswith("click_tab:"):
                    tab_idx = int(action.split(":")[1])
                    try:
                        tabs = page.locator('button[role="tab"]').all()
                        if tab_idx < len(tabs):
                            tabs[tab_idx].click()
                            page.wait_for_timeout(3000)
                    except Exception as e:
                        print(f"\n  [WARN] click_tab:{tab_idx} — {e}")
                elif action == "click_primary_button":
                    try:
                        page.locator(
                            'button[data-testid="baseButton-primary"], '
                            'button[kind="primary"]'
                        ).first.click()
                        page.wait_for_timeout(5000)
                    except Exception as e:
                        print(f"\n  [WARN] click_primary_button — {e}")
                elif action.startswith("click_button:"):
                    btn_text = action.split(":", 1)[1]
                    try:
                        page.locator(f'button:has-text("{btn_text}")').first.click()
                        page.wait_for_timeout(4000)
                    except Exception as e:
                        print(f"\n  [WARN] click_button:{btn_text} — {e}")
                elif action.startswith("select_company:"):
                    company_query = action.split(":", 1)[1]
                    try:
                        page.locator('[data-testid="stSelectbox"]').first.click()
                        page.wait_for_timeout(800)
                        page.keyboard.type(company_query, delay=80)
                        page.wait_for_timeout(1200)
                        page.locator('[data-testid="stSelectboxVirtualDropdown"] li').first.click()
                        page.wait_for_timeout(2500)
                    except Exception as e:
                        print(f"\n  [WARN] select_company:{company_query} — {e}")
                elif action.startswith("wait:"):
                    secs = int(action.split(":")[1])
                    page.wait_for_timeout(secs * 1000)

            # Hold page open until recording stops
            while not stop_event.is_set():
                page.wait_for_timeout(500)

        except Exception as e:
            print(f"\n  [WARN] Playwright: {e}")
        finally:
            vpath = None
            try:
                vpath = page.video.path()
            except Exception:
                pass
            ctx.close()   # MUST close context to flush/finalise the video file
            browser.close()
            if vpath and Path(vpath).exists():
                video_result.append(str(vpath))


# ── Section Recorder ──────────────────────────────────────────────────────────
def record_section(section: dict) -> "Path | None":
    sid       = section["id"]
    title     = section["title"]
    narration = section["narration"]

    raw_video  = OUTPUT_DIR / f"{sid}_raw.mp4"
    tts_audio  = OUTPUT_DIR / f"{sid}_tts.mp3"
    srt_file   = OUTPUT_DIR / f"{sid}.srt"
    mixed      = OUTPUT_DIR / f"{sid}_mixed.mp4"
    captioned  = OUTPUT_DIR / f"{sid}_captioned.mp4"
    final_out  = OUTPUT_DIR / f"{sid}_FINAL.mp4"

    if final_out.exists():
        print(f"  [SKIP] {final_out.name} already exists — skipping section.")
        return final_out

    print(f"\n{'='*64}")
    print(f"  {title}")
    print(f"{'='*64}")

    # Step 1: Generate TTS audio
    print(f"  [1/7] Generating TTS narration ({TTS_VOICE})...")
    tts_ok = generate_tts_audio(narration, tts_audio)
    if not tts_ok:
        print(f"  [ERROR] TTS failed for section {sid} — skipping.")
        return None

    tts_dur = get_video_duration(tts_audio)
    total_record_dur = tts_dur + TTS_BUFFER + 2.0  # buffer + nav startup
    print(f"  TTS duration: {tts_dur:.1f}s  |  Recording: {total_record_dur:.0f}s")

    # Step 2: (SRT generated later, after preamble is known for correct offset)

    # Step 3: Start Playwright viewport recording in background thread
    print(f"  [3/7] Starting Playwright viewport recording...")
    stop_evt        = threading.Event()
    nav_ready       = threading.Event()
    video_result    = []
    preamble_result = []
    nav_thread = threading.Thread(
        target=_playwright_navigate,
        args=(section, stop_evt, nav_ready, video_result, preamble_result),
        daemon=True,
    )
    nav_thread.start()

    if not nav_ready.wait(timeout=90):
        print(f"  [WARN] Browser nav timed out after 90s — aborting section")
        stop_evt.set()
        nav_thread.join(timeout=10)
        return None

    preamble_s    = preamble_result[0] if preamble_result else 8.0
    audio_delay_s = preamble_s + 1.0

    # Step 2 (deferred): Generate SRT with offset matching the audio delay
    print(f"  [2/7] Building captions (offset {audio_delay_s:.1f}s)...")
    text_to_srt(narration, tts_dur, srt_file, audio_offset_s=audio_delay_s)

    # Step 4: Hold open for recording duration (Playwright records in background)
    print(f"  [4/7] Recording for {total_record_dur:.0f}s (preamble {preamble_s:.1f}s)...")
    t0 = time.time()
    while True:
        elapsed = time.time() - t0
        if elapsed >= total_record_dur:
            break
        remaining = total_record_dur - elapsed
        bar = ("█" * int(20 * elapsed / total_record_dur) +
               "░" * int(20 * remaining / total_record_dur))
        print(f"\r  [{bar}] {remaining:.0f}s left  ", end="", flush=True)
        time.sleep(0.4)
    print()

    stop_evt.set()
    print(f"  Waiting for Playwright to flush video...")
    nav_thread.join(timeout=30)

    if not video_result:
        print(f"  [ERROR] Playwright produced no video for {sid}")
        return None

    webm_path   = Path(video_result[0])
    raw_size_kb = webm_path.stat().st_size // 1024 if webm_path.exists() else 0
    print(f"  Playwright WebM: {webm_path.name} ({raw_size_kb} KB)")

    # Convert Playwright WebM → silent MP4 for TTS mixing pipeline
    # Playwright records video-only WebM; add silent audio so the pipeline works.
    # Input options (-f lavfi) MUST appear immediately before their -i argument.
    conv = subprocess.run(
        ["ffmpeg", "-y",
         "-i", str(webm_path),               # input 0: WebM (video only)
         "-f", "lavfi",                       # input 1: silent audio source
         "-i", "anullsrc=r=44100:cl=stereo",
         "-map", "0:v", "-map", "1:a",
         "-c:v", "libx264", "-preset", "fast", "-crf", "20",
         "-vf", f"scale={SCREEN_W}:{SCREEN_H}:flags=lanczos",
         "-c:a", "aac", "-ar", "44100", "-b:a", "64k",
         "-shortest", str(raw_video)],
        capture_output=True,
    )
    webm_path.unlink(missing_ok=True)

    if conv.returncode != 0 or not raw_video.exists():
        print(f"  [ERROR] WebM→MP4 failed: {conv.stderr.decode()[-300:]}")
        return None

    print(f"  Raw MP4: {raw_video.name} ({raw_video.stat().st_size // 1024} KB)")

    # Step 5: Mix TTS audio into video (delay matches SRT offset above)
    print(f"  [5/7] Mixing TTS audio (delay={audio_delay_s:.1f}s)...")
    mix_tts_into_video(raw_video, tts_audio, mixed, audio_delay_s=audio_delay_s)
    raw_video.unlink(missing_ok=True)
    tts_audio.unlink(missing_ok=True)

    # Step 6: Normalise audio + fades
    print(f"  [6/7] Normalising audio + fades...")
    normalise_audio(mixed)
    add_fades(mixed)

    # Step 7: Burn captions + title card
    print(f"  [7/7] Burning captions + title card...")
    burn_captions(mixed, srt_file, captioned)
    mixed.unlink(missing_ok=True)
    add_title_card(captioned, title, final_out)
    captioned.unlink(missing_ok=True)

    size_mb = final_out.stat().st_size / 1024 / 1024 if final_out.exists() else 0
    print(f"  Section complete: {final_out.name}  ({size_mb:.1f} MB)")
    return final_out if final_out.exists() else None


# ── Entry Point ───────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="LifeCycle Leverage Automated Demo Recorder")
    parser.add_argument("--section", help="Record only this section id prefix (e.g. 03)")
    parser.add_argument("--concat-only", action="store_true",
                        help="Stitch existing *_FINAL.mp4 files → videos/ without recording")
    args = parser.parse_args()

    total_est = sum(len(s["narration"].split()) / 2.5 for s in SECTIONS)  # ~2.5 words/sec

    print("\n" + "="*64)
    print("  LifeCycle Leverage Dashboard — Automated Demo Recorder")
    print(f"  Screen: {SCREEN_W}x{SCREEN_H}  |  Voice: {TTS_VOICE}")
    print(f"  Output: {OUTPUT_DIR.resolve()}")
    print(f"  Estimated total: ~{int(total_est)//60}m {int(total_est)%60}s")
    print("="*64)

    sections = SECTIONS
    if args.section:
        sections = [s for s in SECTIONS if s["id"].startswith(args.section)]
        if not sections:
            print(f"  ERROR: No section matching '{args.section}'")
            sys.exit(1)

    if args.concat_only:
        existing = sorted(OUTPUT_DIR.glob("*_FINAL.mp4"))
        if not existing:
            print("  ERROR: No *_FINAL.mp4 files in demo_output/ — record first.")
            sys.exit(1)
        print(f"  Found {len(existing)} section files → stitching to videos/")
        _stitch_with_bookends(existing)
        return

    print(f"\n  {len(sections)} section(s) to record.")
    print(f"  Streamlit must be running: streamlit run app.py")
    print(f"\n  Recording is FULLY AUTOMATED — starting in 3 seconds...")
    time.sleep(3)

    completed = []
    for i, section in enumerate(sections, 1):
        print(f"\n  [{i}/{len(sections)}] {section['id']}")
        result = record_section(section)
        if result:
            completed.append(result)
        else:
            print(f"  [WARN] Section {section['id']} produced no output — continuing.")

    print(f"\n  {len(completed)}/{len(sections)} sections completed.")

    if len(completed) > 1:
        _stitch_with_bookends(completed)
    elif len(completed) == 1:
        print(f"\n  Single section: {completed[0].resolve()}")
        print(f"  Use --concat-only to stitch all sections when ready.")
    else:
        print(f"\n  No sections completed — nothing to stitch.")

    print("\n  Recording session complete.\n")


if __name__ == "__main__":
    main()

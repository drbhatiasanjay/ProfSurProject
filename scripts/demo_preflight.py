#!/usr/bin/env python3
"""
LifeCycle Leverage Dashboard — Demo Pre-flight Check
=====================================================
Run this BEFORE starting demo_recorder.py to catch environment issues early.

Usage:
    py -3.12 scripts/demo_preflight.py

Exit codes:
    0  — all checks passed, safe to record
    1  — one or more checks failed
"""

import subprocess, sys, socket
from pathlib import Path

MIC_DEVICE = "Microphone (2- Brio 100)"
STREAMLIT_PORT = 8501

GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
RESET  = "\033[0m"
BOLD   = "\033[1m"


def _pass(msg):  return f"{GREEN}  PASS{RESET}  {msg}"
def _fail(msg):  return f"{RED}  FAIL{RESET}  {msg}"
def _warn(msg):  return f"{YELLOW}  WARN{RESET}  {msg}"


checks = []   # (label, status, fix_cmd)


# ── Check 1: ffmpeg ───────────────────────────────────────────────────────────
def check_ffmpeg():
    r = subprocess.run(["ffmpeg", "-version"], capture_output=True)
    if r.returncode == 0:
        ver = r.stdout.decode().splitlines()[0].split("version")[-1].split()[0]
        checks.append(("ffmpeg", "pass", f"version {ver}"))
    else:
        checks.append(("ffmpeg", "fail",
                        "Install ffmpeg: https://ffmpeg.org/download.html  then add to PATH"))


# ── Check 2: ffprobe ──────────────────────────────────────────────────────────
def check_ffprobe():
    r = subprocess.run(["ffprobe", "-version"], capture_output=True)
    if r.returncode == 0:
        checks.append(("ffprobe", "pass", "available"))
    else:
        checks.append(("ffprobe", "fail",
                        "Included with ffmpeg — verify ffmpeg installation"))


# ── Check 3: Microphone device ───────────────────────────────────────────────
def check_microphone():
    r = subprocess.run(
        ["ffmpeg", "-list_devices", "true", "-f", "dshow", "-i", "dummy"],
        capture_output=True, text=True,
    )
    combined = r.stdout + r.stderr
    if MIC_DEVICE.lower() in combined.lower():
        checks.append(("microphone", "pass", f"Found: {MIC_DEVICE}"))
    else:
        # Show what was detected
        device_lines = [l.strip() for l in combined.splitlines()
                        if "Microphone" in l or "Audio" in l or "dshow" in l.lower()]
        found = "; ".join(device_lines[:4]) if device_lines else "none detected"
        checks.append(("microphone", "fail",
                        f'Expected "{MIC_DEVICE}" — detected: {found}\n'
                        f'         Fix: edit MIC_DEVICE in scripts/demo_recorder.py'))


# ── Check 4: Streamlit running ───────────────────────────────────────────────
def check_streamlit():
    try:
        import urllib.request
        req = urllib.request.urlopen(
            f"http://localhost:{STREAMLIT_PORT}/_stcore/health", timeout=3
        )
        if req.status == 200:
            checks.append(("streamlit", "pass", f"Running on :{STREAMLIT_PORT}"))
            return
    except Exception:
        pass
    # Fallback: check if port is open
    try:
        s = socket.create_connection(("localhost", STREAMLIT_PORT), timeout=2)
        s.close()
        checks.append(("streamlit", "warn",
                        f"Port {STREAMLIT_PORT} open but health endpoint unreachable"))
        return
    except Exception:
        pass
    checks.append(("streamlit", "fail",
                   f"Not running — start it first: streamlit run app.py"))


# ── Check 5: faster-whisper ──────────────────────────────────────────────────
def check_whisper():
    try:
        import faster_whisper
        checks.append(("faster-whisper", "pass",
                        f"v{faster_whisper.__version__ if hasattr(faster_whisper, '__version__') else 'installed'}"))
    except ImportError:
        checks.append(("faster-whisper", "fail",
                        "pip install faster-whisper"))


# ── Check 6: Playwright ──────────────────────────────────────────────────────
def check_playwright():
    try:
        from playwright.sync_api import sync_playwright
        # Check chromium binary exists
        r = subprocess.run(
            [sys.executable, "-m", "playwright", "install", "--dry-run", "chromium"],
            capture_output=True, text=True,
        )
        checks.append(("playwright", "pass", "chromium available"))
    except ImportError:
        checks.append(("playwright", "fail",
                        "pip install playwright  &&  playwright install chromium"))
    except Exception:
        checks.append(("playwright", "warn",
                        "Installed but chromium may need: playwright install chromium"))


# ── Check 7: Output directories ──────────────────────────────────────────────
def check_dirs():
    demo_out = Path("demo_output")
    videos   = Path("videos")
    demo_out.mkdir(exist_ok=True)
    videos.mkdir(exist_ok=True)
    checks.append(("output dirs", "pass",
                   f"demo_output/ ✓  videos/ ✓"))


# ── Run all checks ────────────────────────────────────────────────────────────
print(f"\n{BOLD}{'='*62}{RESET}")
print(f"{BOLD}  LifeCycle Leverage — Demo Pre-flight Check{RESET}")
print(f"{BOLD}{'='*62}{RESET}\n")

check_ffmpeg()
check_ffprobe()
check_microphone()
check_streamlit()
check_whisper()
check_playwright()
check_dirs()

# ── Print results ─────────────────────────────────────────────────────────────
col_w = max(len(c[0]) for c in checks) + 2
print(f"  {'Check':<{col_w}}  {'Result'}")
print(f"  {'-'*col_w}  {'-'*40}")

failures = 0
warnings = 0
for label, status, detail in checks:
    if status == "pass":
        icon = f"{GREEN}✓ PASS{RESET}"
    elif status == "warn":
        icon = f"{YELLOW}⚠ WARN{RESET}"
        warnings += 1
    else:
        icon = f"{RED}✗ FAIL{RESET}"
        failures += 1
    print(f"  {label:<{col_w}}  {icon}")
    if status != "pass":
        for line in detail.split("\n"):
            print(f"  {' '*col_w}  → {line}")

print(f"\n  {'-'*58}")
if failures == 0 and warnings == 0:
    print(f"  {GREEN}{BOLD}All checks passed — ready to record!{RESET}")
    print(f"\n  Run:  py -3.12 scripts/demo_recorder.py\n")
elif failures == 0:
    print(f"  {YELLOW}{BOLD}{warnings} warning(s) — recording may work but review above.{RESET}")
    print(f"\n  Run:  py -3.12 scripts/demo_recorder.py\n")
else:
    print(f"  {RED}{BOLD}{failures} check(s) failed — fix before recording.{RESET}")
    print()

sys.exit(0 if failures == 0 else 1)

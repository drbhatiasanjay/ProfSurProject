"""
Playwright smoke test for DataV2 vintage UI changes.

Spins up NOTHING on its own — expects Streamlit already running at localhost:8765.
Walks through each page and collects JS console errors + Streamlit exception panels.
Run with:
    py -3.12 tests/smoke_datav2.py
"""
import io
import re
import sys
import time

# Force UTF-8 stdout so Unicode output (→, ✓) doesn't crash Windows cp1252 console.
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", line_buffering=True)

from playwright.sync_api import sync_playwright

BASE = "http://localhost:8765"
PAGES = [
    "",  # Dashboard (default)
    "peer_benchmarks",
    "scenarios",
    "data_explorer",
    "econometrics",
    "ml_models",
    "advanced_econometrics",
]


def check_page(page, url: str, label: str) -> list[str]:
    errors = []
    console_errors = []
    page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
    page.on("pageerror", lambda exc: errors.append(f"pageerror: {exc}"))

    print(f"  → {label or 'Dashboard'} ({url})")
    page.goto(url, wait_until="networkidle", timeout=30000)
    # Give Streamlit a moment to hydrate and render.
    time.sleep(3)

    # Check for Streamlit's exception container.
    exc_panels = page.query_selector_all('[data-testid="stException"]')
    if exc_panels:
        for panel in exc_panels:
            errors.append(f"streamlit exception: {panel.inner_text()[:500]}")

    alerts = page.query_selector_all('[data-testid="stAlert"][data-baseweb="notification"]')
    # stAlert can be info/success/warning/error — check for error-level
    for a in alerts:
        kind = a.get_attribute("kind") or ""
        if kind.lower() == "error":
            errors.append(f"streamlit error alert: {a.inner_text()[:200]}")

    # Filter out generic 404 asset pings (Streamlit telemetry, missing favicons, CDN probes).
    # The important signals are page-level exceptions (stException) and uncaught page errors.
    noise = ("favicon", "Failed to load resource", "telemetry", "stats.js", "/ping")
    sig_console = [e for e in console_errors if not any(n in e for n in noise)]
    return errors + [f"console: {e[:200]}" for e in sig_console]


def main():
    results = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1400, "height": 900})
        page = ctx.new_page()

        # First load the root to establish session.
        print("Warming up at", BASE)
        page.goto(BASE, wait_until="networkidle", timeout=30000)
        time.sleep(4)

        # Test the Panel dropdown control is rendered.
        sidebar_text = page.inner_text("section[data-testid='stSidebar']")
        panel_present = "Panel" in sidebar_text
        thesis_option = "Thesis panel" in sidebar_text
        latest_option = "Latest panel" in sidebar_text
        print(f"  Sidebar: has 'Panel' label={panel_present}, has 'Thesis panel'={thesis_option}, has 'Latest panel'={latest_option}")
        results["_sidebar_panel_control"] = panel_present and thesis_option and latest_option

        # Walk pages
        for slug in PAGES:
            url = f"{BASE}/{slug}" if slug else BASE
            errs = check_page(page, url, slug)
            results[slug or "dashboard"] = errs

        # Toggle test — click Thesis panel, verify caption changes.
        print()
        print("Toggle test: Latest → Thesis")
        page.goto(BASE, wait_until="networkidle", timeout=30000)
        time.sleep(3)
        before = page.inner_text("section[data-testid='stSidebar']")
        before_has_2025 = "2025" in before and "includes CMIE 2025" in before

        # Streamlit radios hide the <input>; the clickable target is the styled label.
        # Click the visible label text inside the sidebar.
        page.locator("section[data-testid='stSidebar']").get_by_text("Thesis panel", exact=False).first.click()
        time.sleep(4)  # allow rerun to settle
        after = page.inner_text("section[data-testid='stSidebar']")
        after_has_thesis_only = "thesis only" in after
        after_has_2024 = "2024" in after
        after_no_cmie = "includes CMIE 2025" not in after
        print(f"  before Latest: caption had 'includes CMIE 2025'={before_has_2025}")
        print(f"  after Thesis: caption has 'thesis only'={after_has_thesis_only}, has '2024'={after_has_2024}, no 'CMIE 2025'={after_no_cmie}")
        toggle_works = before_has_2025 and after_has_thesis_only and after_has_2024 and after_no_cmie
        results["_panel_toggle"] = toggle_works

        browser.close()

    print()
    print("=" * 70)
    print("RESULTS")
    print("=" * 70)
    any_fail = False
    for name, val in results.items():
        if name.startswith("_"):
            status = "✓" if val else "✗"
            print(f"  {status} {name} = {val}")
            if not val:
                any_fail = True
        else:
            if val:
                any_fail = True
                print(f"  ✗ {name}: {len(val)} error(s)")
                for e in val[:3]:
                    print(f"      - {e}")
            else:
                print(f"  ✓ {name}: clean")

    sys.exit(1 if any_fail else 0)


if __name__ == "__main__":
    main()

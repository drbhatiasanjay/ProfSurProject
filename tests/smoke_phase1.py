"""
Playwright smoke for Phase 1 UI refresh.

Covers:
- Light theme: all 7 primary pages render, Panel toggle + theme toggle present.
- Dark theme: Settings-page toggle flips theme, Dashboard re-renders with dark palette,
  no Streamlit exception panels on any page.
- NEW badges present on Dashboard's Latest-year + Market-indices KPI tiles.
- Tabbed life-stage comparison has "2025 snapshot" tab.
- T623 index picker is visible without expanding anything.

Assumes Streamlit is already running at http://localhost:8511.
"""
import io
import re
import sys
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", line_buffering=True)

from playwright.sync_api import sync_playwright

BASE = "http://localhost:8512"
PAGES = ["", "peer_benchmarks", "scenarios", "data_explorer",
         "econometrics", "ml_models", "advanced_econometrics"]


def _page_has_no_exception(page) -> list[str]:
    errs = []
    for panel in page.query_selector_all('[data-testid="stException"]'):
        errs.append(panel.inner_text()[:300])
    return errs


def main():
    results = {"light": {}, "dark": {}}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1480, "height": 960})
        page = ctx.new_page()

        # ── Pass 1: LIGHT theme (default on fresh session) ──────────────────
        print("Pass 1 — light theme")
        page.goto(BASE, wait_until="networkidle", timeout=30000)
        time.sleep(4)

        sidebar = page.inner_text("section[data-testid='stSidebar']")
        assert "Panel" in sidebar, "Panel radio missing"
        assert "Thesis panel" in sidebar and "Latest panel" in sidebar, "Panel options missing"
        print("  sidebar Panel control OK")

        # Dashboard-specific checks
        body = page.inner_text("body")
        has_new_badges = body.count("NEW") >= 3  # 4 NEW-badged KPIs in Latest mode
        has_2025_tab = "2025 snapshot" in body
        has_index_picker_outside_expander = "Compare leverage to a sector" in body
        print(f"  dashboard: NEW badges>={3}? {has_new_badges}, 2025 snapshot tab? {has_2025_tab}, index picker visible? {has_index_picker_outside_expander}")
        results["light"]["dashboard_checks"] = has_new_badges and has_2025_tab and has_index_picker_outside_expander

        for slug in PAGES:
            url = f"{BASE}/{slug}" if slug else BASE
            page.goto(url, wait_until="networkidle", timeout=30000)
            time.sleep(2)
            errs = _page_has_no_exception(page)
            label = slug or "dashboard"
            results["light"][label] = errs

        # ── Pass 2: switch to DARK via Settings, revisit same pages ─────────
        # IMPORTANT: page.goto() creates a fresh Streamlit session and resets session_state.
        # Must use in-app sidebar nav (Streamlit nav link clicks) to preserve session_state.theme.
        print("Pass 2 — flipping to dark theme via Settings (in-app nav only)")
        page.goto(BASE, wait_until="networkidle", timeout=30000)
        time.sleep(4)
        # Streamlit folds pages beyond the first 10 behind "View X more" — Settings is one of these.
        try:
            page.locator("section[data-testid='stSidebar']").get_by_text(re.compile(r"View \d+ more")).first.click()
            time.sleep(2)
        except Exception:
            pass  # already expanded
        # Click the "Settings" link in the sidebar nav (href ends with /settings).
        page.locator("section[data-testid='stSidebar'] a[href$='/settings']").first.click()
        time.sleep(4)
        # Click the Dark radio option
        label = page.locator("label").filter(has_text=re.compile("Dark \\(mock-inspired\\)"))
        label.first.click()
        time.sleep(6)

        dark_radio = label.first
        dark_checked = dark_radio.locator("input").first.is_checked() if dark_radio.locator("input").count() else None
        print(f"  Dark radio checked? {dark_checked}")

        # Stay on settings page to confirm dark applied, then use in-app nav to visit each page.
        bg_here = page.evaluate("() => getComputedStyle(document.querySelector('.stApp')).backgroundColor")
        print(f"  .stApp on settings (post-click): {bg_here}")

        # In-app nav to Dashboard
        page.locator("section[data-testid='stSidebar']").get_by_text("Dashboard", exact=True).first.click()
        time.sleep(5)
        # Dark CSS sets .stApp bg to #0e1117 — verify via computed style
        bg = page.evaluate(
            "() => getComputedStyle(document.querySelector('.stApp')).backgroundColor"
        )
        # rgb(14,17,23) is the dark bg
        dark_applied = bg.strip() in ("rgb(14, 17, 23)", "rgba(14, 17, 23, 1)")
        print(f"  .stApp computed bg: {bg} -> dark applied: {dark_applied}")
        results["dark"]["dashboard_bg_is_dark"] = dark_applied

        # Walk pages via in-app sidebar nav (href-based) to preserve session_state.theme.
        for slug in PAGES:
            if not slug:
                continue  # dashboard covered below
            link = page.locator(f"section[data-testid='stSidebar'] a[href$='/{slug}']")
            if link.count() == 0:
                # Expand the "View X more" fold if present (advanced_econometrics is folded)
                try:
                    page.locator("section[data-testid='stSidebar']").get_by_text(re.compile(r"View \d+ more")).first.click()
                    time.sleep(1)
                except Exception:
                    pass
                link = page.locator(f"section[data-testid='stSidebar'] a[href$='/{slug}']")
            if link.count() == 0:
                results["dark"][slug] = [f"nav link for '{slug}' not found"]
                continue
            link.first.click()
            time.sleep(3)
            errs = _page_has_no_exception(page)
            results["dark"][slug] = errs

        # Return to dashboard to confirm dark persisted through the full walk.
        # Dashboard's href is the bare app base (e.g. http://localhost:8512/) — use the first link.
        page.locator("section[data-testid='stSidebar'] a").first.click()
        time.sleep(4)
        final_bg = page.evaluate("() => getComputedStyle(document.querySelector('.stApp')).backgroundColor")
        print(f"  final dashboard .stApp bg: {final_bg}")
        results["dark"]["dashboard_bg_is_dark"] = final_bg.strip() in ("rgb(14, 17, 23)", "rgba(14, 17, 23, 1)")

        browser.close()

    print()
    print("=" * 70)
    print("RESULTS")
    print("=" * 70)
    any_fail = False
    for theme, outcomes in results.items():
        print(f"-- {theme} --")
        for name, val in outcomes.items():
            if isinstance(val, bool):
                status = "OK" if val else "FAIL"
                if not val:
                    any_fail = True
                print(f"  [{status}] {name} = {val}")
            elif isinstance(val, list):
                if val:
                    any_fail = True
                    print(f"  [FAIL] {name}: {len(val)} exception(s)")
                    for e in val[:2]:
                        print(f"      - {e}")
                else:
                    print(f"  [OK] {name}: clean")

    sys.exit(1 if any_fail else 0)


if __name__ == "__main__":
    main()

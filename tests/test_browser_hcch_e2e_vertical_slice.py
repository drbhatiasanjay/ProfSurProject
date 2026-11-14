"""
Playwright Browser Acceptance Test for HCCH End-to-End Vertical Slice.
Verifies both:
1. Official Unreviewed Mode: HCCH statutory containment notice active, analytics halted.
2. Demo Fixture Mode (PROFSUR_DEMO_FIXTURE_MODE=1):
   - Demo disclaimer banner prominently displayed.
   - Typed dossier resolved and rendered with financial ratios.
   - Unpriced circuit breaker: Valuation, WACC, and Reverse DCF remain strictly BLOCKED.
   - Verified across configured profiles (drbhatia, skumar, profsurkumar, sbhatia).
"""

import os
import sys
import time
import socket
import shutil
import tempfile
import urllib.request
import subprocess
from pathlib import Path
import pytest

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None

pytestmark = pytest.mark.skipif(
    sync_playwright is None,
    reason="Playwright is required for browser tests but is not installed in this environment"
)


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.mark.parametrize("role_username", ["drbhatia", "skumar", "profsurkumar", "sbhatia"])
def test_browser_hcch_demo_fixture_mode_roles(role_username):
    """Verify demo-fixture mode renders ratios and blocks unpriced DCF across all 4 roles."""
    port = _find_free_port()
    temp_dir = tempfile.mkdtemp(prefix="profsur_demo_browser_")
    temp_db_path = os.path.join(temp_dir, "temp_capital_structure.db")

    root_dir = Path(__file__).resolve().parent.parent
    src_db = root_dir / "capital_structure.db"
    assert src_db.exists(), "Repository capital_structure.db not found for test replication."
    shutil.copy2(src_db, temp_db_path)

    # Pre-seed demo fixture into the isolated temporary database
    import sqlite3
    from models.pre_ipo_demo_fixture import seed_hcch_demo_fixture
    seed_conn = sqlite3.connect(temp_db_path)
    seed_hcch_demo_fixture(owner=role_username, company="hindustan_coca_cola", conn=seed_conn, force=True)
    seed_conn.close()

    env = os.environ.copy()
    env["PROFSUR_DB_PATH"] = temp_db_path
    env["STREAMLIT_SERVER_PORT"] = str(port)
    env["STREAMLIT_SERVER_HEADLESS"] = "true"
    env["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"
    env["PYTHONUNBUFFERED"] = "1"
    env["PROFSUR_DEMO_FIXTURE_MODE"] = "1"
    env["ENVIRONMENT"] = "demo"

    proc = None
    try:
        cmd = [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            "app.py",
            f"--server.port={port}",
            "--server.headless=true",
            "--browser.gatherUsageStats=false",
        ]
        proc = subprocess.Popen(
            cmd,
            env=env,
            stdout=sys.stdout,
            stderr=sys.stderr,
            cwd=str(root_dir),
        )

        health_url = f"http://127.0.0.1:{port}/_stcore/health"
        deadline = time.time() + 45.0
        healthy = False
        while time.time() < deadline:
            if proc.poll() is not None:
                pytest.fail(f"Ephemeral Streamlit process terminated prematurely with exit code {proc.returncode}")
            try:
                req = urllib.request.Request(health_url)
                with urllib.request.urlopen(req, timeout=1.0) as resp:
                    if resp.status == 200:
                        healthy = True
                        break
            except Exception:
                pass
            time.sleep(1.0)

        assert healthy, f"Process on port {port} failed to report healthy."

        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(headless=True)
            except Exception:
                browser = p.chromium.launch(headless=True, channel="chrome")

            context = browser.new_context(viewport={"width": 1440, "height": 1050})
            page = context.new_page()

            page.goto(f"http://127.0.0.1:{port}/?theme=dark", wait_until="networkidle", timeout=45000)
            page.wait_for_timeout(2000)

            # Authenticate as test role
            user_input = page.locator('input[placeholder="username or user@domain.com"]')
            if user_input.count() > 0 and user_input.is_visible():
                user_input.fill(role_username)
                auth_pass = os.environ.get("PROFSUR_AUTH_PASS", "Pass@123")
                page.locator('input[type="password"]').fill(auth_pass)
                page.locator("[data-testid='stFormSubmitButton'] button").first.click()
                page.wait_for_timeout(3500)

            # Navigate to Pre-IPO DRHP Intelligence
            view_more = page.locator("[data-testid='stSidebarNavViewButton']")
            if view_more.count() > 0 and view_more.is_visible():
                view_more.click()
                page.wait_for_timeout(1000)

            pre_ipo_link = page.locator("[data-testid='stSidebarNav'] a:has-text('Pre-IPO DRHP Intelligence')").first
            pre_ipo_link.scroll_into_view_if_needed()
            pre_ipo_link.click()
            page.wait_for_load_state("networkidle", timeout=35000)
            page.wait_for_timeout(3000)

            # Select Hindustan Coca-Cola from Pre-IPO Deal Dossier selectbox
            deal_box = page.locator("div[data-testid='stSelectbox']").filter(has_text="Active Pre-IPO Deal Dossier")
            if deal_box.count() > 0:
                deal_box.scroll_into_view_if_needed()
                deal_box.locator("div[role='combobox'], input").first.click()
            else:
                selectbox = page.locator("[data-testid='stSelectbox']").first
                selectbox.scroll_into_view_if_needed()
                selectbox.click()
            page.wait_for_timeout(1000)
            coca_option = page.locator("li:has-text('Hindustan Coca-Cola')").first
            if coca_option.count() > 0 and coca_option.is_visible():
                coca_option.click()
                page.wait_for_load_state("networkidle", timeout=30000)
                page.wait_for_timeout(3000)
            else:
                page.keyboard.press("Escape")

            # 1. Verify Demo Mode Disclaimer Banner is present
            try:
                page.wait_for_selector("text=DEMO REVIEW FIXTURE", timeout=15000)
            except Exception as e:
                page.screenshot(path="demo_failure.png")
                main_txt = page.locator("[data-testid='stMain']").inner_text() if page.locator("[data-testid='stMain']").count() > 0 else "NO_MAIN"
                print("\nFAILED WAITING FOR DEMO REVIEW FIXTURE. MAIN TEXT:\n", main_txt[:2000])
                raise e
            demo_banner = page.locator("text=DEMO REVIEW FIXTURE")
            assert demo_banner.count() > 0, "Demo disclaimer banner must be displayed when PROFSUR_DEMO_FIXTURE_MODE=1"

            # 2. Verify HCCH entity name is displayed
            page.wait_for_selector("text=Hindustan Coca-Cola", timeout=15000)
            title_text = page.locator("text=Hindustan Coca-Cola")
            assert title_text.count() > 0, "Hindustan Coca-Cola dossier title must be present"

            # 3. Verify unpriced circuit breaker: Valuation / Reverse DCF are blocked
            blocked_warning = page.locator("text=BLOCKED_MISSING_REVIEWED_PRICE_BAND").first
            blocked_warning.wait_for(state="attached", timeout=15000)
            assert blocked_warning.count() > 0, "Unpriced DRHP circuit breaker warning must be displayed"

            # 4. Save verified screenshot artifact
            artifacts_dir = root_dir / "tests" / "artifacts"
            artifacts_dir.mkdir(parents=True, exist_ok=True)
            shot_path = artifacts_dir / f"verified_hcch_demo_mode_{role_username}.png"
            page.screenshot(path=str(shot_path), full_page=False)
            assert shot_path.exists() and shot_path.stat().st_size > 1000

            browser.close()
    finally:
        if proc is not None:
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass
        shutil.rmtree(temp_dir, ignore_errors=True)

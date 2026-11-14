"""
Playwright Browser Acceptance Test for Pre-IPO P0 Containment.
Strictly isolated browser verification:
- Owns an ephemeral Streamlit process on a guaranteed free port
- Operates on an isolated temporary database copy
- Waits for its own health endpoint (/ _stcore/health)
- Verifies HCCH statutory containment notice appears before analytics
- Verifies no deck export button or Dickinson stage analysis is rendered
- Terminates ONLY the ephemeral process it created
- Pinned Playwright Chromium with system fallback
- Saves screenshot to temporary test-artifact directory
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
from playwright.sync_api import sync_playwright


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def test_browser_unreviewed_hcch_containment_isolated():
    # 1. Ephemeral setup: free port & temporary database copy
    port = _find_free_port()
    temp_dir = tempfile.mkdtemp(prefix="profsur_browser_test_")
    temp_db_path = os.path.join(temp_dir, "temp_capital_structure.db")

    root_dir = Path(__file__).resolve().parent.parent
    src_db = root_dir / "capital_structure.db"
    if src_db.exists():
        shutil.copy2(src_db, temp_db_path)
    else:
        # Fail-closed if repository DB missing
        pytest.fail("Repository capital_structure.db not found for test replication.")

    # Environment for isolated process
    env = os.environ.copy()
    env["PROFSUR_DB_PATH"] = temp_db_path
    env["STREAMLIT_SERVER_PORT"] = str(port)
    env["STREAMLIT_SERVER_HEADLESS"] = "true"
    env["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"

    proc = None
    try:
        # 2. Launch self-owned ephemeral Streamlit process
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
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            cwd=str(root_dir),
        )

        # 3. Wait for own health endpoint
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

        assert healthy, f"Ephemeral Streamlit process on port {port} failed to report healthy within 45s."

        # 4. Run browser acceptance
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(headless=True)
            except Exception:
                browser = p.chromium.launch(headless=True, channel="chrome")

            context = browser.new_context(viewport={"width": 1440, "height": 1050})
            page = context.new_page()

            # Navigate to base URL
            base_url = f"http://127.0.0.1:{port}"
            page.goto(f"{base_url}/?theme=dark", wait_until="networkidle", timeout=45000)
            page.wait_for_timeout(2000)

            # Authenticate as drbhatia
            user_input = page.locator('input[placeholder="username or user@domain.com"]')
            if user_input.count() > 0 and user_input.is_visible():
                user_input.fill("drbhatia")
                auth_pass = os.environ.get("PROFSUR_AUTH_PASS", "Pass@123")
                page.locator('input[type="password"]').fill(auth_pass)
                page.locator("[data-testid='stFormSubmitButton'] button").first.click()
                page.wait_for_selector("[data-testid='stSidebarNav']", timeout=35000)
                page.wait_for_timeout(2000)

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

            # Select Hindustan Coca-Cola
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

            # 5. Verify HCCH Statutory Containment Notice appears before analytics
            containment_heading = page.locator("text=HCCH Statutory Evidence Containment Active (P0-01)")
            assert containment_heading.count() > 0, "HCCH Statutory Evidence Containment Active (P0-01) notice must be visible!"

            containment_text = page.locator("text=strictly disconnected from the unreviewed built-in registry")
            assert containment_text.count() > 0, "Containment notice must state disconnection from unreviewed registry!"

            # 6. Verify analytical content is blocked (st.stop() executed before analytics)
            # No Export Deck button
            export_btn = page.locator("button:has-text('Export Deck (PPTX)')")
            assert export_btn.count() == 0, "Deck export button must NOT be rendered when HCCH is contained!"

            # No Dickinson stage classification output
            dickinson_heading = page.locator("text=Dickinson Cash Flow Life-Cycle Stage")
            assert dickinson_heading.count() == 0, "Dickinson life-cycle analytics must NOT be rendered when HCCH is contained!"

            # 7. Save screenshot to temporary test artifact location
            screenshot_path = os.path.join(temp_dir, "test_browser_hcch_containment.png")
            page.screenshot(path=screenshot_path, full_page=False)
            assert os.path.exists(screenshot_path), "Screenshot file must exist on disk!"
            assert os.path.getsize(screenshot_path) > 1000, "Screenshot must not be empty!"

            browser.close()
    finally:
        # 8. Clean up: terminate ONLY the ephemeral process we started
        if proc is not None:
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass
        # Clean up temporary directory
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception:
            pass

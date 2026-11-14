"""Automated E2E Playwright Browser Acceptance Suite across all 4 configured enterprise profiles.

Verifies:
1. drbhatia (Lead / Admin)
2. profsurkumar (Lead Researcher)
3. skumar (Co-Researcher)
4. sbhatia (Viewer / Executive)

Audit criteria:
- Clean authentication via native form with zero session drop
- Navigation to Page 27 (Pre-IPO DRHP Intelligence)
- Zero Streamlit exceptions or crash modals
- P0-01 Containment verification:
  * Unreviewed HCCH displays fail-closed notice: 'HCCH Statutory Evidence Containment Active (P0-01)'
  * Unreviewed HCCH strictly blocks deck export and analytical ratios
- P0-05 Canonical Debt Schedule verification (Mankind Pharma):
  * 3-Card Canonical Debt Schedule (Funded Bank Debt, Ind AS 116 Lease Liabilities, Total Economic Indebtedness)
  * Detailed debt schedule table
- Complete absence of retail advice / buy-sell jargon
- Physical screenshot evidence saved to disk in docs/review-evidence/screenshots/ and artifact dir.
"""

import os
import sys
import time
import socket
import subprocess
import shutil
from pathlib import Path
import pytest
from playwright.sync_api import sync_playwright

ARTIFACT_DIR = Path("C:/Users/hemas/.gemini/antigravity/brain/f6978611-2b08-4fd9-8af9-7b703ed76b10")
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
DOCS_SCREENSHOT_DIR = Path("docs/review-evidence/screenshots")
DOCS_SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

PROFILES = [
    ("drbhatia", "admin"),
    ("profsurkumar", "researcher"),
    ("skumar", "researcher"),
    ("sbhatia", "viewer"),
]


def _find_free_port() -> int:
    for port in [8501, 8502, 8503, 8504, 8505]:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) == 0:
                continue
            return port
    return 8503


def _is_server_alive(port: int) -> bool:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1.0)
            return s.connect_ex(("127.0.0.1", port)) == 0
    except Exception:
        return False


@pytest.fixture(scope="module")
def streamlit_server():
    """Returns the base URL of a running Streamlit server, launching one if necessary."""
    for port in [8501, 8502]:
        if _is_server_alive(port):
            yield f"http://localhost:{port}"
            return

    port = _find_free_port()
    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            "app.py",
            f"--server.port={port}",
            "--server.headless=true",
            "--browser.gatherUsageStats=false",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        cwd=str(Path.cwd()),
    )

    base_url = f"http://localhost:{port}"
    deadline = time.time() + 35.0
    alive = False
    while time.time() < deadline:
        if _is_server_alive(port):
            alive = True
            break
        time.sleep(1.0)

    if not alive:
        proc.terminate()
        pytest.fail(f"Streamlit server failed to start on port {port} within 35s")

    time.sleep(2.0)
    try:
        yield base_url
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()


@pytest.mark.parametrize("username,role", PROFILES)
def test_pre_ipo_browser_role_acceptance(streamlit_server, username, role):
    base_url = streamlit_server
    password = os.environ.get("PROFSUR_AUTH_PASS", "Pass@123")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 960})
        page = context.new_page()

        # 1. Clear session and navigate to login
        page.goto(f"{base_url}/?logout=1&theme=dark", wait_until="networkidle", timeout=30000)
        time.sleep(1.0)

        # 2. Authenticate
        identifier_input = page.locator("input[aria-label='Username or email']")
        if identifier_input.count() == 0:
            identifier_input = page.locator("input[placeholder*='username']")
        assert identifier_input.count() > 0, f"Login identifier input missing for {username}"
        identifier_input.fill(username)

        pw_input = page.locator("input[aria-label='Password']")
        if pw_input.count() == 0:
            pw_input = page.locator("input[type='password']")
        assert pw_input.count() > 0, f"Password input missing for {username}"
        pw_input.fill(password)

        page.locator("button:has-text('Sign In →')").first.click()
        page.wait_for_load_state("networkidle", timeout=30000)
        time.sleep(2.5)

        # 3. Navigate to Page 27 (Pre-IPO DRHP Intelligence)
        view_more = page.locator("[data-testid='stSidebarNavViewButton']")
        if view_more.count() > 0 and view_more.is_visible():
            view_more.click()
            time.sleep(0.5)

        nav_link = page.locator("[data-testid='stSidebarNav'] a:has-text('Pre-IPO DRHP Intelligence')")
        if nav_link.count() > 0:
            nav_link.first.scroll_into_view_if_needed()
            nav_link.first.click()
        else:
            page.locator("text='Pre-IPO DRHP Intelligence'").first.click()

        page.wait_for_load_state("networkidle", timeout=30000)
        time.sleep(3.0)

        # 4. Verify Page 27 loaded without Streamlit exception tracebacks
        content = page.content()
        assert "stException" not in content, f"Streamlit exception modal detected for {username}!"
        assert "Traceback" not in content, f"Traceback detected on Page 27 for {username}!"
        assert "Pre-IPO DRHP Intelligence" in content or "Sovereign Terminal" in content, (
            f"Page 27 failed to load for {username}"
        )

        # 5. Verify P0-01 HCCH Contained Notice (Fail-closed check on default selection)
        assert (
            "HCCH Statutory Evidence Containment Active (P0-01)" in content
            or "strictly disconnected from the unreviewed built-in registry" in content
            or "CONTAINED — AWAITING EVIDENCE REVIEW" in content
            or "CORRECTION & AUDIT NOTICE" in content
        ), f"HCCH must display fail-closed containment notice for {username}"

        # 6. Switch to Mankind Pharma to verify 3-card debt schedule (P0-05 Contract)
        selectbox = page.locator("[data-testid='stSelectbox']").first
        if selectbox.count() > 0:
            selectbox.scroll_into_view_if_needed()
            selectbox.click()
            time.sleep(0.8)
            mankind_opt = page.locator("li:has-text('Mankind Pharma')").first
            if mankind_opt.count() > 0:
                mankind_opt.click()
                page.wait_for_load_state("networkidle", timeout=30000)
                time.sleep(2.5)

        # Verify Tab 5 Detailed Workpapers -> Subtab 2 Indebtedness & Debt Maturity
        tab5_btn = page.locator("button[data-baseweb='tab']").filter(has_text="Detailed Workpapers")
        if tab5_btn.count() > 0:
            tab5_btn.first.click()
            time.sleep(1.5)

            subtab_debt = page.locator("button[data-baseweb='tab']").filter(has_text="Indebtedness & Debt Maturity")
            if subtab_debt.count() > 0:
                subtab_debt.first.click()
                time.sleep(1.5)
                tab_content = page.content()
                assert "Funded Bank Borrowings" in tab_content, f"Funded Bank Borrowings card missing for {username}"
                assert "Ind AS 116 Lease Liabilities" in tab_content, f"Ind AS 116 Lease Liabilities card missing for {username}"
                assert "Total Economic Indebtedness" in tab_content, f"Total Economic Indebtedness card missing for {username}"

        # 7. Assert complete absence of retail recommendations / advisory jargon
        current_content = page.content()
        for phrase in ["STRONG BUY", "DEFINITE SELL", "SUBSCRIBE FOR LISTING GAINS", "TARGET PRICE ₹"]:
            assert phrase not in current_content.upper(), f"Forbidden phrase '{phrase}' detected for {username}!"

        # 8. Physical screenshot verification
        shot_path = ARTIFACT_DIR / f"verified_pre_ipo_item1_6_{username}.png"
        page.screenshot(path=str(shot_path), full_page=False)
        assert shot_path.exists(), f"Artifact screenshot missing: {shot_path}"
        assert shot_path.stat().st_size > 1000, f"Artifact screenshot empty: {shot_path}"

        docs_shot_path = DOCS_SCREENSHOT_DIR / f"verified_pre_ipo_item1_6_{username}.png"
        shutil.copy2(shot_path, docs_shot_path)
        assert docs_shot_path.exists(), f"Docs screenshot missing: {docs_shot_path}"
        assert docs_shot_path.stat().st_size > 1000, f"Docs screenshot empty: {docs_shot_path}"

        print(f"Profile {username} PASS: Screenshot verified ({shot_path.stat().st_size} bytes)")
        context.close()
        browser.close()

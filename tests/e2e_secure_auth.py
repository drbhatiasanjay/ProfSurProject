"""Playwright acceptance and visual checks for the LeverageDebtAI auth journey.

Run with: AUTH_TEST_MODE=1 pytest tests/e2e_secure_auth.py -q
The test outbox is intentionally test-only and must never be enabled in production.
"""

import json
import os
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest

playwright = pytest.importorskip("playwright.sync_api")
from playwright.sync_api import expect, sync_playwright


ROOT = Path(__file__).resolve().parents[1]


def _free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@pytest.fixture()
def app_server(tmp_path):
    source_db = ROOT / "capital_structure.db"
    test_db = tmp_path / "capital_structure.test.db"
    shutil.copy2(source_db, test_db)
    outbox = tmp_path / "auth-outbox.jsonl"
    port = _free_port()
    env = os.environ.copy()
    env.update({
        "PROFSUR_DB_PATH": str(test_db),
        "AUTH_TEST_MODE": "1",
        "APP_ENV": "test",
        "AUTH_TEST_OUTBOX": str(outbox),
    })
    process = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "app.py", "--server.headless", "true", "--server.port", str(port)],
        cwd=ROOT,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
    )
    deadline = time.time() + 30
    while time.time() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                break
        except OSError:
            time.sleep(0.25)
    else:
        process.kill()
        pytest.fail("Streamlit server did not start")
    yield f"http://127.0.0.1:{port}", outbox
    process.terminate()
    process.wait(timeout=10)


def _last_code(outbox):
    deadline = time.time() + 10
    while time.time() < deadline:
        if outbox.exists():
            messages = [json.loads(line) for line in outbox.read_text(encoding="utf-8").splitlines() if line]
            if messages:
                return messages[-1]["code"]
        time.sleep(0.2)
    raise AssertionError("No test email was delivered")


def test_new_user_auth_flow_and_visual_states(app_server, tmp_path):
    base_url, outbox = app_server
    username = f"visual_{int(time.time())}"
    email = f"{username}@example.com"
    password = "correct horse battery staple 2026!"
    artifact_dir = Path(os.getenv("PLAYWRIGHT_ARTIFACT_DIR", str(tmp_path / "visual-auth")))
    artifact_dir.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1000}, device_scale_factor=1)
        page.goto(base_url, wait_until="domcontentloaded")
        expect(page.get_by_text("Welcome to LeverageDebtAI")).to_be_visible()
        page.screenshot(path=str(artifact_dir / "01-welcome.png"), full_page=True)

        page.get_by_role("button", name="Create a new account").click()
        page.get_by_role("textbox", name="Username").fill(username)
        page.get_by_role("textbox", name="Email address").fill(email)
        page.get_by_role("textbox", name="Phone number").fill("+919876543210")
        page.get_by_role("button", name="Send verification code").click()
        expect(page.get_by_text("Check your email")).to_be_visible()
        page.screenshot(path=str(artifact_dir / "02-verification.png"), full_page=True)

        page.get_by_label("Verification code").fill(_last_code(outbox))
        page.get_by_role("button", name="Verify email").click()
        expect(page.get_by_text("Set your password")).to_be_visible()
        page.get_by_role("textbox", name="Password", exact=True).fill(password)
        page.get_by_role("textbox", name="Confirm password").fill(password)
        page.get_by_role("button", name="Finish account setup").click()
        expect(page.get_by_text("Welcome to LifeCycle Leverage")).to_be_visible()
        page.screenshot(path=str(artifact_dir / "03-onboarding.png"), full_page=True)
        browser.close()

"""Optional authenticated browser checks for the AI chat surface.

Run with AI_CHAT_TEST_URL and AI_CHAT_STORAGE_STATE pointing at a local,
authenticated Streamlit session. The deterministic contract tests remain in
the normal pytest suite; these checks are skipped when browser prerequisites
are not installed.
"""
import os
from pathlib import Path

import pytest


@pytest.mark.ui
def test_ai_chat_responsive_surface():
    url = os.getenv("AI_CHAT_TEST_URL")
    state = os.getenv("AI_CHAT_STORAGE_STATE")
    if not url or not state:
        pytest.skip("Set AI_CHAT_TEST_URL and AI_CHAT_STORAGE_STATE for authenticated UI checks")
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        pytest.skip("Install playwright for authenticated UI checks")

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(storage_state=state, viewport={"width": 1440, "height": 1000})
        page = context.new_page()
        page.goto(url, wait_until="networkidle")
        desktop_path = Path("test_screenshots") / "ai_chat_desktop.png"
        desktop_path.parent.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(desktop_path), full_page=True)
        assert page.get_by_placeholder("Ask about the panel data...").count() == 1
        assert page.locator("body").evaluate("el => el.scrollWidth <= el.clientWidth + 2")

        page.set_viewport_size({"width": 390, "height": 844})
        page.reload(wait_until="networkidle")
        page.screenshot(path=str(Path("test_screenshots") / "ai_chat_mobile.png"), full_page=True)
        assert page.locator("body").evaluate("el => el.scrollWidth <= el.clientWidth + 2")
        browser.close()

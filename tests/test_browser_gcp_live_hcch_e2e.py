import os
import sys
import time
import pytest
from pathlib import Path
from playwright.sync_api import sync_playwright

TAGGED_DEMO_URL = os.environ.get(
    "PROFSUR_TAGGED_DEMO_URL",
    "https://hcch-e2e-demo-20261114---lifecycle-leverage-qhzom2yadq-ue.a.run.app"
)

TEST_ROLES = ["drbhatia", "skumar", "profsurkumar", "sbhatia"]

@pytest.mark.parametrize("role_username", TEST_ROLES)
def test_live_gcp_hcch_e2e_demo_slice(role_username):
    root_dir = Path(__file__).resolve().parent.parent
    artifacts_dir = root_dir / "tests" / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=True)
        except Exception:
            browser = p.chromium.launch(headless=True, channel="chrome")

        context = browser.new_context(viewport={"width": 1440, "height": 1050})
        page = context.new_page()

        # 1. Navigate to Tagged Cloud Run URL
        target_url = f"{TAGGED_DEMO_URL}/?theme=dark"
        page.goto(target_url, timeout=60000)

        # 2. Authenticate
        user_input = page.locator('input[placeholder="username or user@domain.com"]')
        user_input.wait_for(state="visible", timeout=45000)
        user_input.fill(role_username)
        auth_pass = os.environ.get("PROFSUR_AUTH_PASS", "Pass@123")
        page.locator('input[type="password"]').fill(auth_pass)
        page.locator("[data-testid='stFormSubmitButton'] button").first.click()
        page.wait_for_selector("[data-testid='stSidebarNav']", timeout=45000)
        page.wait_for_timeout(3000)

        # 3. Navigate to Pre-IPO DRHP Intelligence
        view_more = page.locator("[data-testid='stSidebarNavViewButton']")
        if view_more.count() > 0 and view_more.is_visible():
            view_more.click()
            page.wait_for_timeout(1000)

        pre_ipo_link = page.locator("[data-testid='stSidebarNav'] a:has-text('Pre-IPO DRHP Intelligence')").first
        pre_ipo_link.wait_for(state="visible", timeout=30000)
        pre_ipo_link.scroll_into_view_if_needed()
        pre_ipo_link.click()
        page.wait_for_load_state("networkidle", timeout=45000)
        page.wait_for_timeout(4000)

        # 4. Select Hindustan Coca-Cola from Pre-IPO Deal Dossier selectbox
        deal_box = page.locator("div[data-testid='stSelectbox']").filter(has_text="Active Pre-IPO Deal Dossier")
        if deal_box.count() > 0:
            deal_box.scroll_into_view_if_needed()
            deal_box.locator("div[role='combobox'], input").first.click()
        else:
            selectbox = page.locator("[data-testid='stSelectbox']").first
            selectbox.scroll_into_view_if_needed()
            selectbox.click()
        page.wait_for_timeout(1500)
        coca_option = page.locator("li:has-text('Hindustan Coca-Cola')").first
        if coca_option.count() > 0 and coca_option.is_visible():
            coca_option.click()
            page.wait_for_load_state("networkidle", timeout=35000)
            page.wait_for_timeout(3000)
        else:
            page.keyboard.press("Escape")

        # 5. Verify Demo Mode Disclaimer Banner is present
        page.wait_for_selector("text=DEMO REVIEW FIXTURE", timeout=20000)
        demo_banner = page.locator("text=DEMO REVIEW FIXTURE")
        assert demo_banner.count() > 0, "Demo disclaimer banner must be displayed on live GCP tagged demo revision"

        # 6. Verify HCCH entity name is displayed
        page.wait_for_selector("text=Hindustan Coca-Cola", timeout=20000)
        title_text = page.locator("text=Hindustan Coca-Cola")
        assert title_text.count() > 0, "Hindustan Coca-Cola dossier title must be present on live GCP"

        # 7. Verify unpriced circuit breaker: Valuation / Reverse DCF are blocked
        blocked_warning = page.locator("text=BLOCKED_MISSING_REVIEWED_PRICE_BAND").first
        blocked_warning.wait_for(state="attached", timeout=20000)
        assert blocked_warning.count() > 0, "Unpriced DRHP circuit breaker warning must be displayed on live GCP"

        # 8. Save verified live GCP screenshot artifact
        shot_path = artifacts_dir / f"verified_gcp_live_hcch_demo_{role_username}.png"
        page.screenshot(path=str(shot_path), full_page=False)
        assert shot_path.exists() and shot_path.stat().st_size > 1000

        # Also copy to root artifacts dir if distinct
        root_artifacts = Path("C:/Users/hemas/.gemini/antigravity/brain/f6978611-2b08-4fd9-8af9-7b703ed76b10")
        if root_artifacts.exists():
            import shutil
            shutil.copy(shot_path, root_artifacts / shot_path.name)

        browser.close()

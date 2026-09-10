import os
import re
import time
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_URL = os.environ.get("PROFSUR_UI_URL", "http://localhost:8502")
PASSWORD = os.environ.get("PROFSUR_TEST_PASSWORD", "")
OUT = Path(__file__).parent / "agy_defects"
OUT.mkdir(exist_ok=True)

def run():
    if not PASSWORD:
        raise RuntimeError("PROFSUR_TEST_PASSWORD is required")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1000})
        page.goto(BASE_URL, wait_until="networkidle", timeout=60000)
        if page.locator("input[type='password']").count() == 0:
            try:
                page.wait_for_selector("input[type='password']", timeout=15000)
            except:
                pass
        if page.locator("input[type='password']:visible").count():
            page.locator("input:visible").nth(0).fill("profsurkumar")
            page.locator("input[type='password']:visible").first.fill(PASSWORD)
            page.locator("button:has-text('Sign In')").last.click()
            page.wait_for_timeout(5000)
        page.wait_for_selector("section[data-testid='stSidebar']", timeout=30000)
        page.wait_for_timeout(3000)
        more = page.locator("section[data-testid='stSidebar']").get_by_text(re.compile(r"View \d+ more", re.I)).first
        if more.is_visible(timeout=3000):
            more.click()
        link = page.locator("section[data-testid='stSidebar'] a").filter(has_text=re.compile("AI Assistant", re.I)).first
        link.wait_for(state="visible", timeout=15000)
        link.click()
        chat = page.get_by_role("textbox", name="Ask about the panel data...")
        chat.wait_for(state="visible", timeout=30000)
        chat.fill("What are the average profitability and tangibility by lifecycle stage?")
        chat.press("Enter")
        page.wait_for_timeout(30000)
        body = page.locator("body").inner_text()
        page.screenshot(path=str(OUT / "phase13_descriptive.png"), full_page=True)
        required = ["COMPUTED", "observations", "firms", "source fingerprint"]
        missing = [item for item in required if item.lower() not in body.lower()]
        leaks = []
        if "chain-of-thought" in body.lower():
            leaks.append("chain-of-thought")
        if '"chart_spec"' in body:
            leaks.append("chart_spec")
        report = {
            "scenario": "phase13_descriptive",
            "status": "PASS" if not missing and not leaks else "FAIL",
            "missing_metadata": missing,
            "leak_markers": leaks,
            "screenshot": str(OUT / "phase13_descriptive.png"),
        }
        (OUT / "phase13_descriptive_report.json").write_text(
            json.dumps(report, indent=2) + "\n", encoding="utf-8"
        )
        if missing:
            raise AssertionError("Missing Phase 13 metadata: " + ", ".join(missing))
        if leaks:
            raise AssertionError("Private reasoning or raw tool payload leaked: " + ", ".join(leaks))
        print("PHASE13_UI_PASS: descriptive metadata visible")
        browser.close()

if __name__ == "__main__":
    run()

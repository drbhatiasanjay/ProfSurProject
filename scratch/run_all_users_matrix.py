import sys
import os
import re
from playwright.sync_api import sync_playwright

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_URL = "http://localhost:8501"
TEST_CMD = "xtreg leverage i.corplifestage c.prof##c.tang c.prof##c.dvnd taxShield intRate i.year, fe"
USERS = [
    ("profsurkumar", "researcher"),
    ("skumar", "researcher"),
    ("drbhatia", "admin"),
    ("sbhatia", "viewer"),
]
PASSWORD = os.environ.get("PROFSUR_VERIFY_PASSWORD", "")

def run_matrix():
    if not PASSWORD:
        raise RuntimeError("Set PROFSUR_VERIFY_PASSWORD for authenticated UI regression.")
    out_dir = "scratch/matrix_evidence"
    os.makedirs(out_dir, exist_ok=True)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        
        for user, role in USERS:
            print(f"\n==========================================")
            print(f"Testing User: {user} ({role})")
            print(f"==========================================")
            ctx = browser.new_context(viewport={"width": 1440, "height": 1100})
            page = ctx.new_page()

            print(f"Navigating to {BASE_URL}...")
            page.goto(BASE_URL, wait_until="networkidle", timeout=35000)
            
            print(f"Logging in as {user}...")
            page.wait_for_selector('[data-testid="stTextInput"] input', timeout=30000, state="visible")
            page.locator('[data-testid="stTextInput"] input').first.fill(user)
            page.locator('input[type="password"]').first.fill(PASSWORD)
            page.locator('button:has-text("Sign In")').first.click()
            
            print("Waiting for sidebar...")
            page.wait_for_selector("section[data-testid='stSidebar']", timeout=25000, state="visible")

            print("Expanding sidebar navigation...")
            try:
                more = page.locator("section[data-testid='stSidebar']").get_by_text(re.compile(r"more", re.IGNORECASE)).first
                if more.is_visible(timeout=3000):
                    more.click()
            except Exception:
                pass

            print("Navigating to Stata Studio...")
            stata_link = page.locator("section[data-testid='stSidebar'] a").filter(has_text=re.compile("stata studio", re.IGNORECASE)).first
            stata_link.click()
            # Wait for Stata Studio specific DOM marker
            page.wait_for_selector("h3:has-text('Stata Studio')", timeout=20000, state="visible")

            print("Entering Stata command...")
            cmd_input = page.locator("input[aria-label='Stata Command Prompt:']").first
            cmd_input.wait_for(state="visible", timeout=20000)
            cmd_input.click()
            page.keyboard.press("Control+A")
            page.keyboard.press("Backspace")
            cmd_input.fill(TEST_CMD)

            print("Clicking Run Command...")
            page.get_by_role("button", name="Run Command").first.click()
            
            print("Waiting for estimation calculation to complete by checking for terminal card output...")
            term_card = page.locator(".stata-rich-terminal-card").first
            # Wait until it is visible, indicating command finished
            term_card.wait_for(state="visible", timeout=30000)

            # Determine initial mode from toggle button
            toggle_btn = page.locator('button[data-testid="stBaseButton-secondary"]').filter(has_text=re.compile(r"dark|light", re.IGNORECASE)).first
            btn_text = toggle_btn.text_content() if toggle_btn.count() > 0 else ""
            
            is_dark = "light" in btn_text.lower()
            theme1 = "dark" if is_dark else "light"
            theme2 = "light" if is_dark else "dark"
            
            print(f"Theme 1 is: {theme1} (button label: '{btn_text}')")
            term_card.scroll_into_view_if_needed()
            term_card.screenshot(path=f"{out_dir}/{user}_{theme1}_card.png")
            page.screenshot(path=f"{out_dir}/{user}_{theme1}_full.png")
            print(f"Captured: {user}_{theme1}_card.png & {user}_{theme1}_full.png")

            # Toggle theme
            print(f"Toggling to Theme 2: {theme2}...")
            page.evaluate("window.scrollTo(0, 0)")
            toggle_btn.click()
            
            # Wait for theme to change (look for a style attribute change or just wait for network idle)
            page.wait_for_load_state("networkidle", timeout=10000)

            # Locate terminal in new theme and handle potential DOM detachment during Streamlit re-render
            for attempt in range(5):
                try:
                    term_card = page.locator(".stata-rich-terminal-card").first
                    term_card.wait_for(state="visible", timeout=20000)
                    term_card.scroll_into_view_if_needed()
                    term_card.screenshot(path=f"{out_dir}/{user}_{theme2}_card.png")
                    page.screenshot(path=f"{out_dir}/{user}_{theme2}_full.png")
                    print(f"Captured: {user}_{theme2}_card.png & {user}_{theme2}_full.png")
                    break
                except Exception as e:
                    if attempt == 4:
                        raise
                    # Streamlit may replace the node during a rerun; reacquire
                    # the marker rather than sleeping on a fixed interval.
                    page.wait_for_selector(
                        ".stata-rich-terminal-card", state="visible", timeout=20000
                    )

            ctx.close()
            print(f"Successfully completed testing for {user}!")

        browser.close()
        print("\n=======================================================")
        print("ALL 4 USERS AND ALL THEMES SUCCESSFULLY TESTED & VERIFIED!")
        print("=======================================================")

if __name__ == "__main__":
    run_matrix()

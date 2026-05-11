"""Debug: print sidebar and authentication state for each navigation step."""
import io, sys, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)
from playwright.sync_api import sync_playwright

BASE = "https://lifecycle-leverage-779655496440.us-east1.run.app"
TIMEOUT = 90_000
RENDER_WAIT = 10


def is_authenticated(page):
    try:
        sidebar = page.locator("section[data-testid='stSidebar']").inner_text(timeout=8000)
        result = "sign out" in sidebar.lower()
        # Show first 200 chars of sidebar
        print(f"    sidebar snippet: {repr(sidebar[:200])}")
        return result
    except Exception as e:
        print(f"    sidebar ERROR: {e}")
        return False


def goto_wait(page, url):
    page.goto(url, wait_until="networkidle", timeout=TIMEOUT)
    time.sleep(RENDER_WAIT)


def fill_login(page, username, password):
    goto_wait(page, BASE)
    page.wait_for_selector('[data-testid="stTextInput"] input', timeout=TIMEOUT)
    page.locator('[data-testid="stTextInput"] input').first.fill(username)
    page.locator('input[type="password"]').first.fill(password)
    page.locator('button:has-text("Login")').first.click()
    time.sleep(RENDER_WAIT)
    auth = is_authenticated(page)
    print(f"  After login: authenticated={auth}")
    return auth


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)

    print("=== sbhatia full flow debug ===")
    ctx = browser.new_context(viewport={"width": 1480, "height": 900})
    pg = ctx.new_page()

    fill_login(pg, "sbhatia", "UzBGwQ0DuH_Wgo0S")

    print("\n  Warm-up goto BASE...")
    goto_wait(pg, BASE)
    auth = is_authenticated(pg)
    print(f"  After warm-up: authenticated={auth}")

    print("\n  Check Dashboard (goto BASE again)...")
    goto_wait(pg, BASE)
    body = pg.inner_text("body").lower()
    auth = is_authenticated(pg)
    print(f"  After Dashboard goto: authenticated={auth}")
    print(f"  Login btn visible: {pg.locator('button:has-text(\"Login\")').first.is_visible(timeout=1000)}")
    print(f"  Body snippet: {repr(body[:200])}")
    pg.screenshot(path="debug_sbhatia_dashboard.png")

    print("\n  Check Peer Benchmarks...")
    goto_wait(pg, BASE + "/peer_benchmarks")
    auth = is_authenticated(pg)
    print(f"  After peer_benchmarks goto: authenticated={auth}")

    ctx.close()
    browser.close()

print("\nDone. Screenshot: debug_sbhatia_dashboard.png")

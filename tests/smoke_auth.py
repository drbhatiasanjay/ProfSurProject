"""
Playwright smoke test — streamlit-authenticator Phase 1.

Strategy: one goto per user session (for login), then all page checks via
in-app sidebar link clicks. This preserves the Streamlit WebSocket session
and avoids cookie/session reset issues with repeated full navigations.

Checks:
  1. Unauthenticated access → login screen shown, app blocked
  2. Wrong password        → still blocked after submit
  3. sbhatia (admin)       → all probed pages accessible, logout present
  4. skumar (researcher)   → Workbench blocked, other pages accessible
  5. guest (viewer)        → Bulk Upload + Workbench blocked, Dashboard accessible

Runs against GCP live URL by default.
Override: BASE=http://localhost:8501 py -3.12 tests/smoke_auth.py
"""
import io
import os
import re
import sys
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", line_buffering=True)

from playwright.sync_api import sync_playwright, Page

BASE = os.getenv("BASE", "https://lifecycle-leverage-779655496440.us-east1.run.app")
TIMEOUT = 90_000
RENDER_WAIT = 10  # seconds after networkidle / click for Streamlit to finish rendering

USERS = {
    "sbhatia": {"password": "UzBGwQ0DuH_Wgo0S", "role": "admin"},
    "skumar":  {"password": "tPUATkh5y1R9LdjK", "role": "researcher"},
    "guest":   {"password": "whFSeXFGDGq-s8xa",  "role": "viewer"},
}

ROLE_BLOCKED = {
    "admin":      [],
    "researcher": ["workbench", "activity_log"],
    "viewer":     ["bulk_upload", "workbench", "activity_log", "board_deck"],
}

# Pages to probe: (slug, display label, nav title in sidebar)
# All pages are navigated via in-app sidebar clicks after initial login.
PROBE_PAGES = [
    ("",                "Dashboard",       "Dashboard"),
    ("peer_benchmarks", "Peer Benchmarks", "Peer Benchmarks"),
    ("bulk_upload",     "Bulk Upload",     "Bulk Upload"),
    ("data_explorer",   "Data Explorer",   "Data Explorer"),
    ("workbench",       "Workbench",       "Workbench"),       # in "View X more" section
    ("activity_log",    "Activity Log",    "Activity Log"),    # admin-only page 16
    ("board_deck",      "Board Deck",      "Board Deck"),      # admin+researcher page 17
]


# ── helpers ───────────────────────────────────────────────────────────────────

def _body(page: Page) -> str:
    return page.inner_text("body").lower()


def _exceptions(page: Page) -> list[str]:
    return [el.inner_text()[:300] for el in page.query_selector_all('[data-testid="stException"]')]


def _is_blocked_page(body: str) -> bool:
    return (
        "do not have permission" in body
        or "permission to access" in body
        or "contact the administrator" in body
    )


def _is_authenticated(page: Page) -> bool:
    """True if Sign out is visible anywhere on the page (header bar) or guest ID form shown."""
    try:
        body = page.inner_text("body").lower()
        # Sign out is in the main content header bar (moved from sidebar 2026-05-07)
        # Also accept the guest self-id form as an authenticated-but-pending state
        return "sign out" in body or "continue to dashboard" in body
    except Exception:
        return False


def _fill_guest_form_if_needed(page: Page, display_name: str = "Smoke Guest") -> None:
    """Fill the guest self-identification form if it is blocking the dashboard."""
    try:
        body = page.inner_text("body").lower()
        if "continue to dashboard" not in body:
            return
        inputs = page.locator('[data-testid="stTextInput"] input')
        if inputs.count() > 0:
            inputs.last.fill(display_name)
        page.get_by_role("button", name=re.compile("continue", re.IGNORECASE)).first.click()
        time.sleep(RENDER_WAIT)
    except Exception:
        pass


def _expand_sidebar_nav(page: Page) -> None:
    """Expand the 'View X more' collapsed nav section."""
    try:
        more = page.locator("section[data-testid='stSidebar']").get_by_text(
            re.compile(r"view \d+ more", re.IGNORECASE)
        ).first
        if more.is_visible(timeout=3000):
            more.click()
            time.sleep(2)
    except Exception:
        pass


def _click_nav_link(page: Page, title: str) -> bool:
    """Click a sidebar nav link by its display title. Returns True if found+clicked."""
    # First try visible link
    link = page.locator("section[data-testid='stSidebar'] a").filter(has_text=re.compile(re.escape(title), re.IGNORECASE)).first
    if link.count() > 0 and link.is_visible(timeout=2000):
        link.click()
        time.sleep(RENDER_WAIT)
        return True
    # Expand collapsed section then retry
    _expand_sidebar_nav(page)
    link = page.locator("section[data-testid='stSidebar'] a").filter(has_text=re.compile(re.escape(title), re.IGNORECASE)).first
    if link.count() > 0:
        link.click()
        time.sleep(RENDER_WAIT)
        return True
    return False


def _goto_base_and_login(page: Page, username: str, password: str) -> bool:
    """Navigate to BASE, fill login form, submit. Returns True on successful auth."""
    page.goto(BASE, wait_until="networkidle", timeout=TIMEOUT)
    # Wait for login form to appear
    page.wait_for_selector('[data-testid="stTextInput"] input', timeout=TIMEOUT)
    time.sleep(3)

    page.locator('[data-testid="stTextInput"] input').first.fill(username)
    page.locator('input[type="password"]').first.fill(password)
    page.locator('button:has-text("Login")').first.click()
    time.sleep(RENDER_WAIT)

    # Handle guest self-identification form (viewer role must name themselves)
    _fill_guest_form_if_needed(page)

    return _is_authenticated(page)


def _check_page(page: Page, slug: str, title: str, blocked_slugs: list[str]) -> dict:
    """Navigate to a page via in-app sidebar click and check access."""
    found = _click_nav_link(page, title)
    if not found:
        return {
            "ok": False,
            "expected": "blocked" if slug in blocked_slugs else "accessible",
            "actual": "nav_link_not_found",
            "errors": [],
        }

    body = _body(page)
    errs = _exceptions(page)

    blocked = _is_blocked_page(body)
    authenticated = _is_authenticated(page)

    expected_blocked = slug in blocked_slugs

    if expected_blocked:
        ok = blocked  # must show permission-denied warning
    else:
        ok = authenticated and not blocked  # must be logged in and unblocked

    actual = "blocked" if blocked else ("accessible" if authenticated else "login")
    return {
        "ok": ok,
        "expected": "blocked" if expected_blocked else "accessible",
        "actual": actual,
        "errors": errs,
    }


# ── test cases ────────────────────────────────────────────────────────────────

def test_unauthenticated() -> bool:
    print("\n[1] Unauthenticated access — expect login screen")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(BASE, wait_until="networkidle", timeout=TIMEOUT)
        try:
            page.wait_for_selector('[data-testid="stTextInput"] input', timeout=30000)
            form_shown = True
        except Exception:
            form_shown = False
        app_blocked = not _is_authenticated(page)
        browser.close()

    result = form_shown and app_blocked
    status = "OK" if result else "FAIL"
    print(f"  [{status}] Login form shown: {form_shown}, app blocked: {app_blocked}")
    return result


def test_wrong_password() -> bool:
    print("\n[2] Wrong password — expect still blocked")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(BASE, wait_until="networkidle", timeout=TIMEOUT)
        page.wait_for_selector('[data-testid="stTextInput"] input', timeout=TIMEOUT)
        time.sleep(3)

        page.locator('[data-testid="stTextInput"] input').first.fill("sbhatia")
        page.locator('input[type="password"]').first.fill("WrongPassword!")
        page.locator('button:has-text("Login")').first.click()
        time.sleep(RENDER_WAIT)

        body = _body(page)
        error_hint = any(w in body for w in ["incorrect", "invalid", "wrong", "error"])
        still_blocked = not _is_authenticated(page)
        browser.close()

    ok = still_blocked
    status = "OK" if ok else "FAIL"
    print(f"  [{status}] Still blocked: {still_blocked} (error hint: {error_hint})")
    return ok


def test_user(username: str, password: str, role: str) -> dict:
    print(f"\n[{username}] role={role}")
    blocked_slugs = ROLE_BLOCKED[role]
    results = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1480, "height": 900})
        page = ctx.new_page()

        # Single goto — login
        logged_in = _goto_base_and_login(page, username, password)
        results["login"] = {
            "ok": logged_in,
            "expected": "logged_in",
            "actual": "logged_in" if logged_in else "failed",
            "errors": [],
        }
        s = "OK" if logged_in else "FAIL"
        print(f"  [{s}] login")

        if not logged_in:
            browser.close()
            return results

        # All page checks via in-app sidebar navigation (no more goto calls)
        for slug, label, title in PROBE_PAGES:
            r = _check_page(page, slug, title, blocked_slugs)
            results[label] = r
            s = "OK" if r["ok"] else "FAIL"
            detail = f"expected={r['expected']}, got={r['actual']}"
            err_note = f" [{len(r['errors'])} exception(s)]" if r["errors"] else ""
            print(f"  [{s}] {label}: {detail}{err_note}")

        # Sign out button check (now in header bar, not sidebar — moved 2026-05-07)
        _click_nav_link(page, "Dashboard")  # navigate to a stable page first
        try:
            body_for_logout = page.inner_text("body").lower()
            logout_ok = "sign out" in body_for_logout
        except Exception:
            logout_ok = False
        results["logout_button"] = {
            "ok": logout_ok,
            "expected": "present",
            "actual": "present" if logout_ok else "missing",
            "errors": [],
        }
        s = "OK" if logout_ok else "FAIL"
        print(f"  [{s}] sign out button in header bar")

        browser.close()

    return results


# ── main ─────────────────────────────────────────────────────────────────────

def main():
    print(f"Auth smoke test — {BASE}")
    print("=" * 70)

    failures = []

    if not test_unauthenticated():
        failures.append("unauthenticated access not blocked")

    if not test_wrong_password():
        failures.append("wrong-password not blocked")

    for uname, info in USERS.items():
        res = test_user(uname, info["password"], info["role"])
        for check, r in res.items():
            if not r["ok"]:
                failures.append(f"{uname}/{check}: expected={r['expected']}, got={r['actual']}")

    print("\n" + "=" * 70)
    if failures:
        print("RESULT: FAIL")
        for f in failures:
            print(f"  x {f}")
        sys.exit(1)
    else:
        print("RESULT: PASS — all auth checks green")
        sys.exit(0)


if __name__ == "__main__":
    main()

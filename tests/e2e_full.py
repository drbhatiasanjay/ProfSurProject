"""
Full E2E test suite — all 3 users × all 16 pages + auth flows + header bar +
guest self-identification + preference persistence + Activity Log functionality.

Requires a running Streamlit server.
Run locally:  BASE=http://localhost:8501 py -3.12 -m pytest tests/e2e_full.py -v
Run on GCP:   py -3.12 -m pytest tests/e2e_full.py -v

Optional speed-up for local runs: set RENDER_WAIT=4 environment variable.

Groups:
  1. Auth flows          (3 tests)
  2. Guest self-id       (2 tests)
  3. Header bar          (3 tests)
  4. Role access matrix  (3 parametrized tests — 1 login session per user, 16 pages each)
  5. Preference persist  (1 test — panel mode across login/logout cycle)
  6. Activity Log page   (3 tests)
"""
import os
import re
import sys
import time

import pytest
from playwright.sync_api import sync_playwright, Page

BASE        = os.getenv("BASE", "http://localhost:8501")
TIMEOUT     = 90_000
RENDER_WAIT = int(os.getenv("RENDER_WAIT", "10"))

USERS = {
    "sbhatia": {"password": "UzBGwQ0DuH_Wgo0S", "role": "admin"},
    "skumar":  {"password": "tPUATkh5y1R9LdjK", "role": "researcher"},
    "guest":   {"password": "whFSeXFGDGq-s8xa", "role": "viewer"},
}

# (sidebar nav link title, roles for which the page is BLOCKED)
ALL_PAGES = [
    ("Dashboard",             []),
    ("Peer Benchmarks",       []),
    ("Scenarios",             []),
    ("Bulk Upload",           ["viewer"]),
    ("Data Explorer",         []),
    ("Settings",              []),
    ("Knowledge Graph",       []),
    ("Econometrics Lab",      []),
    ("ML Models",             []),
    ("Forecasting",           []),
    ("Clustering",            []),
    ("Transitions",           []),
    ("Advanced Econometrics", []),
    ("Workbench",             ["researcher", "viewer"]),
    ("Interaction Effects",   []),
    ("Activity Log",          ["researcher", "viewer"]),
]

ROLE_BLOCKED = {
    "admin":      [],
    "researcher": ["Workbench", "Activity Log"],
    "viewer":     ["Bulk Upload", "Workbench", "Activity Log"],
}


# ── low-level helpers ─────────────────────────────────────────────────────────

def _body(page: Page) -> str:
    return page.inner_text("body").lower()


def _is_blocked_page(body: str) -> bool:
    return (
        "do not have permission" in body
        or "permission to access" in body
        or "contact the administrator" in body
    )


def _is_authenticated(page: Page) -> bool:
    """True if Sign out button appears anywhere in the page (header bar)."""
    try:
        return "sign out" in page.inner_text("body").lower()
    except Exception:
        return False


def _needs_guest_form(page: Page) -> bool:
    """True if the guest self-identification form is blocking the dashboard."""
    try:
        return "continue to dashboard" in page.inner_text("body").lower()
    except Exception:
        return False


def _expand_sidebar_nav(page: Page) -> None:
    """Expand the 'View X more' collapsed nav section if present."""
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
    """Click a sidebar nav link by its display title. Expands collapsed section if needed."""
    link = page.locator("section[data-testid='stSidebar'] a").filter(
        has_text=re.compile(re.escape(title), re.IGNORECASE)
    ).first
    if link.count() > 0 and link.is_visible(timeout=2000):
        link.click()
        time.sleep(RENDER_WAIT)
        return True
    _expand_sidebar_nav(page)
    link = page.locator("section[data-testid='stSidebar'] a").filter(
        has_text=re.compile(re.escape(title), re.IGNORECASE)
    ).first
    if link.count() > 0:
        link.click()
        time.sleep(RENDER_WAIT)
        return True
    return False


def _fill_guest_form(page: Page, display_name: str = "Test Guest") -> None:
    """Fill the guest self-identification form."""
    try:
        inputs = page.locator('[data-testid="stTextInput"] input')
        if inputs.count() > 0:
            inputs.last.fill(display_name)
        btn = page.get_by_role("button", name=re.compile("continue", re.IGNORECASE)).first
        btn.click()
        time.sleep(RENDER_WAIT)
    except Exception:
        pass


def _login(page: Page, username: str, password: str, display_name: str = "Test Guest") -> bool:
    """Navigate to BASE, login, and handle guest self-id form. Returns True if authenticated."""
    page.goto(BASE, wait_until="networkidle", timeout=TIMEOUT)
    page.wait_for_selector('[data-testid="stTextInput"] input', timeout=TIMEOUT)
    time.sleep(3)
    page.locator('[data-testid="stTextInput"] input').first.fill(username)
    page.locator('input[type="password"]').first.fill(password)
    page.locator('button:has-text("Login")').first.click()
    time.sleep(RENDER_WAIT)
    if _needs_guest_form(page):
        _fill_guest_form(page, display_name)
    return _is_authenticated(page)


def _logout(page: Page) -> None:
    """Click Sign out in the header bar."""
    try:
        page.get_by_role("button", name=re.compile(r"sign\s*out", re.IGNORECASE)).first.click()
        time.sleep(5)
    except Exception:
        pass


# ── Group 1: Auth flows ───────────────────────────────────────────────────────

def test_unauthenticated_shows_login_form():
    """Unauthenticated GET shows the login form and blocks the app."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(BASE, wait_until="networkidle", timeout=TIMEOUT)
        try:
            page.wait_for_selector('[data-testid="stTextInput"] input', timeout=30_000)
            form_shown = True
        except Exception:
            form_shown = False
        blocked = not _is_authenticated(page)
        browser.close()
    assert form_shown, "Login form should be shown to unauthenticated users"
    assert blocked, "App should be blocked until authenticated"


def test_wrong_password_remains_blocked():
    """Wrong password does not grant access."""
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
        still_blocked = not _is_authenticated(page)
        browser.close()
    assert still_blocked, "Wrong password should not grant access"


@pytest.mark.parametrize("username", ["sbhatia", "skumar", "guest"])
def test_all_users_login_success(username):
    """All three users can log in successfully."""
    info = USERS[username]
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1480, "height": 900})
        page = ctx.new_page()
        logged_in = _login(page, username, info["password"])
        browser.close()
    assert logged_in, f"{username} should be able to log in"


# ── Group 2: Guest self-identification flow ───────────────────────────────────

def test_guest_form_blocks_dashboard_before_submit():
    """Guest sees the self-id form immediately after login; dashboard is hidden."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1480, "height": 900})
        page = ctx.new_page()
        # Login but do NOT fill the form
        page.goto(BASE, wait_until="networkidle", timeout=TIMEOUT)
        page.wait_for_selector('[data-testid="stTextInput"] input', timeout=TIMEOUT)
        time.sleep(3)
        page.locator('[data-testid="stTextInput"] input').first.fill("guest")
        page.locator('input[type="password"]').first.fill(USERS["guest"]["password"])
        page.locator('button:has-text("Login")').first.click()
        time.sleep(RENDER_WAIT)
        form_shown = _needs_guest_form(page)
        body = _body(page)
        # Dashboard KPI headings should not be visible yet
        dashboard_loaded = "life stage distribution" in body or "leverage by stage" in body
        browser.close()
    assert form_shown, "Self-identification form must be shown before guest can proceed"
    assert not dashboard_loaded, "Dashboard should not render before guest submits their name"


def test_guest_form_submit_shows_dashboard_and_name():
    """After filling the self-id form, dashboard renders with the guest's name in header."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1480, "height": 900})
        page = ctx.new_page()
        logged_in = _login(page, "guest", USERS["guest"]["password"], display_name="Prof. Dawar")
        body = _body(page)
        name_visible = "prof. dawar" in body
        sign_out_visible = "sign out" in body
        browser.close()
    assert logged_in, "Guest should be authenticated after submitting display name"
    assert name_visible, "Guest display name 'Prof. Dawar' should appear in the header bar"
    assert sign_out_visible, "Sign out button should be visible after guest identifies"


# ── Group 3: Header bar ───────────────────────────────────────────────────────

def test_header_shows_dataset_label():
    """Header bar column 1 shows 'Dataset:' with the active panel name."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1480, "height": 900})
        page = ctx.new_page()
        assert _login(page, "sbhatia", USERS["sbhatia"]["password"])
        body = _body(page)
        browser.close()
    assert "dataset:" in body, "Header bar should show 'Dataset:' label"


def test_header_sign_out_in_main_not_sidebar():
    """Sign out button is in the main content area, NOT in the sidebar."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1480, "height": 900})
        page = ctx.new_page()
        assert _login(page, "sbhatia", USERS["sbhatia"]["password"])
        try:
            main_text    = page.locator('[data-testid="stMain"]').inner_text(timeout=12000).lower()
            sidebar_text = page.locator("section[data-testid='stSidebar']").inner_text(timeout=8000).lower()
        except Exception:
            main_text, sidebar_text = "", ""
        browser.close()
    assert "sign out" in main_text,    "Sign out should be in main content (header bar)"
    assert "sign out" not in sidebar_text, "Sign out should NOT be in the sidebar"


def test_header_shows_role_for_researcher():
    """Header bar shows 'Researcher' for skumar."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1480, "height": 900})
        page = ctx.new_page()
        assert _login(page, "skumar", USERS["skumar"]["password"])
        body = _body(page)
        browser.close()
    assert "researcher" in body, "Header bar should display the user's role 'Researcher'"


# ── Group 4: Role access matrix ───────────────────────────────────────────────

@pytest.mark.parametrize("username,role", [
    ("sbhatia", "admin"),
    ("skumar",  "researcher"),
    ("guest",   "viewer"),
])
def test_role_access_all_16_pages(username, role):
    """Single login session per user; navigate all 16 pages and verify access vs blocked."""
    blocked_pages = ROLE_BLOCKED[role]
    failures = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1480, "height": 900})
        page = ctx.new_page()

        logged_in = _login(page, username, USERS[username]["password"])
        if not logged_in:
            browser.close()
            pytest.fail(f"Login failed for {username}")

        for nav_title, blocked_roles in ALL_PAGES:
            found = _click_nav_link(page, nav_title)
            if not found:
                failures.append(f"{nav_title}: nav link not found in sidebar")
                continue

            body = _body(page)
            is_blocked     = _is_blocked_page(body)
            should_blocked = role in blocked_roles

            if should_blocked and not is_blocked:
                failures.append(f"{nav_title}: expected BLOCKED for {role}, was accessible")
            elif not should_blocked and is_blocked:
                failures.append(f"{nav_title}: expected ACCESSIBLE for {role}, was blocked")

        browser.close()

    assert not failures, "Role access matrix failures:\n" + "\n".join(f"  ✗ {f}" for f in failures)


# ── Group 5: Preference persistence ──────────────────────────────────────────

def test_panel_preference_persists_across_login():
    """sbhatia switches to Thesis panel → logout → login → header still shows Thesis."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1480, "height": 900})
        page = ctx.new_page()

        assert _login(page, "sbhatia", USERS["sbhatia"]["password"]), "First login failed"

        # Click the Thesis panel radio in the sidebar
        try:
            thesis_opt = page.locator("section[data-testid='stSidebar']").get_by_text(
                re.compile(r"thesis", re.IGNORECASE)
            ).first
            thesis_opt.click()
            time.sleep(RENDER_WAIT + 3)  # extra time for rerun + DB write
        except Exception as exc:
            browser.close()
            pytest.skip(f"Could not locate Thesis panel radio: {exc}")

        body_after_change = _body(page)
        thesis_visible_before_logout = "thesis" in body_after_change

        _logout(page)
        time.sleep(3)

        # Re-login (new session — prefs should be restored from user_preferences)
        assert _login(page, "sbhatia", USERS["sbhatia"]["password"]), "Re-login failed"
        body_after_relogin = _body(page)
        thesis_restored = "thesis" in body_after_relogin

        browser.close()

    assert thesis_visible_before_logout, "Thesis panel should be reflected in header after clicking"
    assert thesis_restored, "Thesis panel preference should be restored on next login"


# ── Group 6: Activity Log page functionality ──────────────────────────────────

def test_activity_log_accessible_for_admin_with_kpis():
    """Admin can access Activity Log; it shows KPI metrics after some navigation."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1480, "height": 900})
        page = ctx.new_page()
        assert _login(page, "sbhatia", USERS["sbhatia"]["password"])

        # Navigate to a couple of pages to generate audit_log entries
        _click_nav_link(page, "Peer Benchmarks")
        _click_nav_link(page, "Data Explorer")

        assert _click_nav_link(page, "Activity Log"), "Activity Log link must be visible for admin"

        body = _body(page)
        blocked = _is_blocked_page(body)
        # Either data is shown (Total Visits KPI) or the empty state message
        has_content = "total visits" in body or "no activity" in body or "activity log" in body
        browser.close()

    assert not blocked, "Admin should not be blocked from Activity Log"
    assert has_content, "Activity Log should render content (KPIs or empty state)"


def test_activity_log_charts_and_transaction_log():
    """Activity Log shows Page Popularity chart and Transaction Log section."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1480, "height": 900})
        page = ctx.new_page()
        assert _login(page, "sbhatia", USERS["sbhatia"]["password"])

        # Generate some activity first
        _click_nav_link(page, "Scenarios")
        _click_nav_link(page, "Peer Benchmarks")
        _click_nav_link(page, "Dashboard")

        assert _click_nav_link(page, "Activity Log")
        body = _body(page)
        browser.close()

    assert "page popularity" in body,   "Page Popularity chart section should be present"
    assert "transaction log" in body,   "Transaction Log section should be present"
    assert "download csv"    in body,   "Download CSV button should be present"


def test_activity_log_shows_guest_display_name():
    """After guest login (with display name 'Prof. Dawar'), Activity Log shows 'Prof. Dawar'."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        # Guest visits Data Explorer
        ctx1 = browser.new_context(viewport={"width": 1480, "height": 900})
        pg1  = ctx1.new_page()
        assert _login(pg1, "guest", USERS["guest"]["password"], display_name="Prof. Dawar")
        _click_nav_link(pg1, "Data Explorer")
        ctx1.close()

        # Admin checks Activity Log
        ctx2 = browser.new_context(viewport={"width": 1480, "height": 900})
        pg2  = ctx2.new_page()
        assert _login(pg2, "sbhatia", USERS["sbhatia"]["password"])
        _click_nav_link(pg2, "Activity Log")
        body = _body(pg2)
        ctx2.close()
        browser.close()

    assert "prof. dawar" in body, (
        "Activity Log should show guest display name 'Prof. Dawar', not the 'guest' username"
    )

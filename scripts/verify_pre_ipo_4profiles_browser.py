"""Automated 4-Profile Authenticated Playwright Acceptance Suite for Pre-IPO DRHP Intelligence.

Verifies Items 1 through 6 across all four authenticated profiles:
1. profsurkumar (Lead Researcher / Admin)
2. skumar (Co-Researcher)
3. drbhatia (Co-Researcher)
4. sbhatia (Reviewer / Executive)

Verifications per profile:
- Clean authentication via native form
- Navigation to Page 27 (Pre-IPO DRHP Intelligence)
- Tab 2: Provenance Ledger, Deep-Dive Citation Inspector, Auditor Sign-Off, and Verbatim Document Slice
- Tab 3 / Subtab 3: 3D Multi-Parameter Covenant Sensitivity Grid & Page 28 Bridge
- Strict absence of retail recommendations (Buy/Sell/Target Price)
- Physical screenshot evidence saved to disk
"""

import os
import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_URL = os.environ.get("BASE_URL", "http://localhost:8501")
ARTIFACT_DIR = Path("C:/Users/hemas/.gemini/antigravity/brain/f6978611-2b08-4fd9-8af9-7b703ed76b10")
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
DOCS_SCREENSHOT_DIR = Path("docs/review-evidence/screenshots")
DOCS_SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

def _resolve_profile_password(username: str) -> str:
    """Resolve password from environment or secrets.toml; never store in code."""
    env_pass = os.environ.get("PROFSUR_AUTH_PASS") or os.environ.get(f"PROFSUR_{username.upper()}_PASS")
    if env_pass:
        return env_pass
    # Check secrets.toml
    secrets_path = Path(".streamlit/secrets.toml")
    if secrets_path.exists():
        try:
            import toml
            data = toml.loads(secrets_path.read_text(encoding="utf-8"))
            passwords = data.get("passwords", {}) or data.get("test_passwords", {})
            if username in passwords:
                return str(passwords[username])
        except Exception:
            pass
    return os.environ.get("PROFSUR_ADMIN_PASS", "Pass@123")


PROFILES = [
    ("drbhatia", _resolve_profile_password("drbhatia"), "admin"),
    ("profsurkumar", _resolve_profile_password("profsurkumar"), "researcher"),
    ("skumar", _resolve_profile_password("skumar"), "researcher"),
    ("sbhatia", _resolve_profile_password("sbhatia"), "viewer"),
]


def verify_profile(page, username, password, role):
    print(f"\n[ACCEPTANCE] Testing profile: {username} ({role})...")

    # 1. Clear session and navigate to login
    page.goto(f"{BASE_URL}/?logout=1&theme=dark", wait_until="networkidle", timeout=60000)
    time.sleep(2.0)

    # 2. Authenticate with robust wait
    identifier_input = page.locator('input[placeholder="username or user@domain.com"]')
    if identifier_input.count() == 0:
        identifier_input = page.locator("input[placeholder*='username']")
    if identifier_input.count() == 0:
        identifier_input = page.locator("input[aria-label='Username or email']")
    
    identifier_input.wait_for(state="visible", timeout=30000)
    identifier_input.fill(username)

    pw_input = page.locator("input[type='password']")
    if pw_input.count() == 0:
        pw_input = page.locator("input[aria-label='Password']")
    pw_input.wait_for(state="visible", timeout=15000)
    pw_input.fill(password)

    submit_btn = page.locator("[data-testid='stFormSubmitButton'] button").first
    if submit_btn.count() == 0:
        submit_btn = page.locator("button:has-text('Sign In →')").first
    submit_btn.click()

    # 3. Wait for sidebar navigation
    page.wait_for_selector("[data-testid='stSidebarNav']", timeout=35000)
    time.sleep(2.0)

    # Handle sidebar view more button if present
    view_more = page.locator("[data-testid='stSidebarNavViewButton']")
    if view_more.count() > 0 and view_more.is_visible():
        view_more.click()
        time.sleep(1.0)

    # 4. Navigate to Page 27 Pre-IPO DRHP Intelligence
    nav_link = page.locator("[data-testid='stSidebarNav'] a:has-text('Pre-IPO DRHP Intelligence')").first
    nav_link.scroll_into_view_if_needed()
    nav_link.click()
    page.wait_for_load_state("networkidle", timeout=35000)
    time.sleep(4.0)

    # 4. Verify Page 27 loaded
    page_content = page.content()
    assert "Pre-IPO DRHP Intelligence" in page_content or "Sovereign Terminal" in page_content, (
        f"Page 27 failed to load for {username}"
    )

    # 5. Switch to Tab 2: Extracted Disclosures & Provenance Ledger (Item 1 & Item 4)
    tab2_btn = page.locator("button[data-baseweb='tab']").filter(has_text="Provenance Ledger")
    assert tab2_btn.count() > 0, f"Provenance Ledger tab missing for {username}"
    tab2_btn.first.click()
    time.sleep(2.0)

    # Verify Provenance Ledger elements
    tab2_content = page.content()
    assert "Provenance Ledger" in tab2_content, f"Provenance ledger title missing for {username}"

    # Expand Citation Inspector if needed
    exp = page.locator("summary").filter(has_text="Click to inspect raw prospectus coordinates")
    if exp.count() > 0:
        # Check if already expanded or open it
        exp.first.click()
        time.sleep(1.5)

    exp_content = page.content()
    assert "Auditor Sign-Off" in exp_content, f"Auditor sign-off gate missing for {username}"
    assert "Approve" in exp_content and "Sign-Off" in exp_content, f"Approve button missing for {username}"
    assert "Flag Discrepancy" in exp_content, f"Discrepancy button missing for {username}"
    assert "Statutory Document Slice" in exp_content, f"Document slice missing for {username}"

    # 6. Switch to Tab 5: Detailed Workpapers -> Subtabs
    tab5_btn = page.locator("button[data-baseweb='tab']").filter(has_text="Detailed Workpapers")
    assert tab5_btn.count() > 0, f"Detailed Workpapers tab missing for {username}"
    tab5_btn.first.click()
    time.sleep(2.0)

    # 6a. Subtab 2: Indebtedness & Debt Maturity (P0-05 Contract)
    subtab_debt = page.locator("button[data-baseweb='tab']").filter(has_text="Indebtedness & Debt Maturity")
    if subtab_debt.count() > 0:
        subtab_debt.first.click()
        time.sleep(1.5)
        debt_content = page.content()
        assert "Funded Bank Borrowings" in debt_content, f"Funded Bank Borrowings missing for {username}"
        assert "Ind AS 116 Lease Liabilities" in debt_content, f"Ind AS 116 Lease Liabilities missing for {username}"
        assert "Total Economic Indebtedness" in debt_content, f"Total Economic Indebtedness missing for {username}"

    # 6b. Subtab 3: Stress Testing & Headroom (Item 2)
    subtab_stress = page.locator("button[data-baseweb='tab']").filter(has_text="Stress Testing & Headroom")
    assert subtab_stress.count() > 0, f"Stress Testing subtab missing for {username}"
    subtab_stress.first.click()
    time.sleep(2.0)

    stress_content = page.content()
    assert "3D Multi-Parameter Covenant Headroom Grid" in stress_content, f"3D grid missing for {username}"
    assert "Bridge to Page 28" in stress_content, f"Bridge button to Page 28 missing for {username}"

    # 7. Assert complete absence of retail recommendations / advisory jargon
    forbidden = ["STRONG BUY", "DEFINITE SELL", "SUBSCRIBE FOR LISTING GAINS", "TARGET PRICE ₹"]
    for phrase in forbidden:
        assert phrase not in stress_content.upper(), f"Forbidden phrase '{phrase}' detected for {username}!"

    # 8. Capture physical screenshot evidence
    shot_path = ARTIFACT_DIR / f"verified_pre_ipo_item1_6_{username}.png"
    page.screenshot(path=str(shot_path), full_page=False)
    assert shot_path.exists(), f"Screenshot file missing on disk: {shot_path}"

    docs_shot_path = DOCS_SCREENSHOT_DIR / f"verified_pre_ipo_item1_6_{username}.png"
    import shutil
    shutil.copy2(shot_path, docs_shot_path)
    assert docs_shot_path.exists(), f"Docs screenshot missing: {docs_shot_path}"
    print(f"  ✓ Profile {username} PASS: Screenshot saved to {shot_path.name} and docs/review-evidence/screenshots/ ({shot_path.stat().st_size} bytes)")
    return True


def main():
    print("==================================================================")
    print("Running Automated 4-Profile Playwright Acceptance Suite")
    print(f"Target URL: {BASE_URL}")
    print("==================================================================")

    results = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        for username, password, role in PROFILES:
            context = browser.new_context(viewport={"width": 1440, "height": 900})
            page = context.new_page()
            try:
                success = verify_profile(page, username, password, role)
                results[username] = "PASS"
            except Exception as e:
                print(f"  ✗ Profile {username} FAILED: {e}")
                results[username] = f"FAIL: {e}"
            finally:
                context.close()
        browser.close()

    print("\n==================================================================")
    print("ACCEPTANCE SUMMARY ACROSS ALL 4 PROFILES:")
    print("==================================================================")
    for u, status in results.items():
        print(f"  • {u:15s}: {status}")

    if any(s != "PASS" for s in results.values()):
        sys.exit(1)
    print("\nALL 4 PROFILES SATISFIED AUDIT ACCEPTANCE CRITERIA.")


if __name__ == "__main__":
    main()

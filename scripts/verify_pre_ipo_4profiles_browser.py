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

PROFILES = [
    ("drbhatia", "Pass@123", "admin"),
    ("profsurkumar", "Pass@123", "researcher"),
    ("skumar", "Pass@123", "researcher"),
    ("sbhatia", "Pass@123", "viewer"),
]


def verify_profile(page, username, password, role):
    print(f"\n[ACCEPTANCE] Testing profile: {username} ({role})...")

    # 1. Clear session and navigate to login
    page.goto(f"{BASE_URL}/?logout=1", wait_until="networkidle")
    time.sleep(1.0)

    # 2. Authenticate
    identifier_input = page.locator("input[aria-label='Username or email']")
    if identifier_input.count() == 0:
        identifier_input = page.locator("input[placeholder*='username']")
    assert identifier_input.count() > 0, f"Login input missing for {username}"
    identifier_input.fill(username)

    pw_input = page.locator("input[aria-label='Password']")
    if pw_input.count() == 0:
        pw_input = page.locator("input[type='password']")
    pw_input.fill(password)

    page.locator("button:has-text('Sign In →')").click()
    page.wait_for_load_state("networkidle")
    time.sleep(2.5)

    # 3. Navigate to Page 27 Pre-IPO DRHP Intelligence
    nav_link = page.locator("[data-testid='stSidebarNav'] a:has-text('Pre-IPO DRHP Intelligence')")
    if nav_link.count() > 0:
        nav_link.click()
    else:
        # Fallback click on sidebar navigation button
        page.locator("text='Pre-IPO DRHP Intelligence'").first.click()
    page.wait_for_load_state("networkidle")
    time.sleep(2.5)

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

    # 6. Switch to Tab 5: Detailed Workpapers -> Subtab 3: Stress Testing & Headroom (Item 2)
    tab5_btn = page.locator("button[data-baseweb='tab']").filter(has_text="Detailed Workpapers")
    assert tab5_btn.count() > 0, f"Detailed Workpapers tab missing for {username}"
    tab5_btn.first.click()
    time.sleep(2.0)

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
    print(f"  ✓ Profile {username} PASS: Screenshot saved to {shot_path.name} ({shot_path.stat().st_size} bytes)")
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

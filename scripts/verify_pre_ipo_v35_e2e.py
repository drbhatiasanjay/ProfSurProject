import asyncio
import os
import sys

# Ensure immediate unbuffered output on Windows
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

from playwright.async_api import async_playwright

SCREENSHOT_DIR = r"C:\Users\hemas\.gemini\antigravity\brain\f6978611-2b08-4fd9-8af9-7b703ed76b10"

async def run():
    print("=== STARTING PRE-IPO COCKPIT & VAULT E2E VERIFICATION GATE ===")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1560, 'height': 980})
        page = await context.new_page()

        # Step 1: Navigate to localhost:5173 (NTPC Green default)
        print("1. Loading Terminal on http://localhost:5173/...")
        await page.goto("http://localhost:5173/", wait_until="domcontentloaded", timeout=20000)
        await page.wait_for_timeout(2500)

        # Assert Statutory Route & Metric Cards
        content = await page.content()
        assert "Regulation 6(2)" in content, "Error: Regulation 6(2) route badge missing"
        assert "TOWER 1: CAPITAL GROWTH VS. EXIT DILUTION" in content, "Error: Tower 1 missing"
        assert "TOWER 2: HUBER FAIR P/E VS. ASKING STRETCH" in content, "Error: Tower 2 missing"
        assert "TOWER 3: DAY-180 FLOAT OVERHANG CLIFF" in content, "Error: Tower 3 missing"
        assert "36 VERIFIED" in content, "Error: Tri-state ledger counters missing"
        print("✓ Verified NTPC Green Statutory Route, Tri-State strip & Lintel Towers 1, 2, 3.")

        shot1 = os.path.join(SCREENSHOT_DIR, "verified_ntpc_cockpit_towers_v35.png")
        await page.screenshot(path=shot1)
        print(f"✓ Saved Screenshot 1: {shot1} ({os.path.getsize(shot1)} bytes)")

        # Step 2: Switch deal dossier to HCCB (Unpriced DRHP)
        print("2. Switching dossier dropdown to HCCB (Hindustan Coca-Cola)...")
        select_elem = page.locator("select").first
        await select_elem.select_option(value="HCCB")
        await page.wait_for_timeout(2000)

        content_hccb = await page.content()
        content_hccb_upper = content_hccb.upper()
        assert "SEBI ICDR 2018 STATUTORY EVIDENCE CONTAINMENT ACTIVE" in content_hccb_upper, "Error: Amber Containment banner missing for HCCB"
        assert "997,461,456" in content_hccb, "Error: Exact 997,461,456 share count missing"
        assert "DRAFTING [●]" in content_hccb or "UNDISCLOSED [●]" in content_hccb_upper, "Error: Tower 2 unpriced failsafe missing"
        print("✓ Verified HCCB Unpriced DRHP Containment Banner, Exact Shares (997,461,456), and Tower 2 unpriced failsafe.")

        shot2 = os.path.join(SCREENSHOT_DIR, "verified_hccb_unpriced_cockpit_v35.png")
        await page.screenshot(path=shot2)
        print(f"✓ Saved Screenshot 2: {shot2} ({os.path.getsize(shot2)} bytes)")

        # Step 3: Navigate to Vault 4 (Provenance Ledger)
        print("3. Navigating to Vault 4 (Provenance Evidence Ledger)...")
        vault4_btn = page.locator("button:has-text('4. Provenance Evidence Ledger')").first
        await vault4_btn.click()
        await page.wait_for_timeout(1500)

        content_vault4 = await page.content()
        assert "VAULT 4: 513-PAGE PROVENANCE EVIDENCE LEDGER" in content_vault4, "Error: Vault 4 header missing"
        assert "Five-Point Statutory Accounting Reconciliation Gate" in content_vault4, "Error: 5-Gate Accounting Card missing"
        assert "1. Balance Sheet Identity" in content_vault4, "Error: Gate 1 missing"
        assert "5. SEBI GCP Cap" in content_vault4, "Error: Gate 5 missing"

        # Click a coordinate chip to trigger PDF Coordinate Inspector
        coord_chip = page.locator("button:has-text('[Ch. III p. 48]')").first
        if await coord_chip.is_visible():
            await coord_chip.click()
            await page.wait_for_timeout(500)
            inspector_content = await page.content()
            assert "x0=72" in inspector_content or "Inspecting Target Variable" in inspector_content, "Error: Coordinate inspector failed to update"
            print("✓ Verified PDF Coordinate Inspector bounding box display.")

        shot3 = os.path.join(SCREENSHOT_DIR, "verified_vault4_provenance_v35.png")
        await page.screenshot(path=shot3)
        print(f"✓ Saved Screenshot 3: {shot3} ({os.path.getsize(shot3)} bytes)")

        # Step 4: Navigate to Vault 8 (6-Rule Red-Flag Scanner)
        print("4. Navigating to Vault 8 (6-Rule Red-Flag Scanner)...")
        vault8_btn = page.locator("button:has-text('8. 6-Rule Red-Flag Scanner')").first
        await vault8_btn.click()
        await page.wait_for_timeout(1500)

        content_vault8 = await page.content()
        assert "VAULT 8: 6-RULE RED-FLAG GOVERNANCE RADAR" in content_vault8, "Error: Vault 8 header missing"
        assert "FLAG-01" in content_vault8, "Error: FLAG-01 missing"
        assert "FLAG-03" in content_vault8, "Error: FLAG-03 missing"
        assert "FLAG-06" in content_vault8, "Error: FLAG-06 missing"
        assert "Beneish M-Score" in content_vault8, "Error: Beneish M-Score missing"
        assert "Sloan Accrual Ratio" in content_vault8, "Error: Sloan Accrual missing"
        print("✓ Verified Vault 8 6-Rule Radar, Beneish M-Score, and Sloan Accruals.")

        shot4 = os.path.join(SCREENSHOT_DIR, "verified_vault8_redflags_v35.png")
        await page.screenshot(path=shot4)
        print(f"✓ Saved Screenshot 4: {shot4} ({os.path.getsize(shot4)} bytes)")

        # Step 5: Navigate to Vault 9 (Unlisted Post-Tax Arbitrage)
        print("5. Navigating to Vault 9 (Unlisted Post-Tax Arbitrage)...")
        vault9_btn = page.locator("button:has-text('9. Unlisted Post-Tax Arbitrage')").first
        await vault9_btn.click()
        await page.wait_for_timeout(1500)

        content_vault9 = await page.content()
        assert "VAULT 9: UNLISTED ARBITRAGE" in content_vault9, "Error: Vault 9 header missing"
        assert "INVERSION RESIDUAL: 0.0000%" in content_vault9 or "<= 0.05% OK" in content_vault9, "Error: Mathematical inversion failed"
        assert "Post-Tax Breakeven Listing Price" in content_vault9, "Error: Breakeven listing price metric missing"
        print("✓ Verified Vault 9 Arbitrage Modeler and Mathematical Solver Inversion.")

        shot5 = os.path.join(SCREENSHOT_DIR, "verified_vault9_arbitrage_v35.png")
        await page.screenshot(path=shot5)
        print(f"✓ Saved Screenshot 5: {shot5} ({os.path.getsize(shot5)} bytes)")

        # Step 6: Navigate to Vault 10 (IC Stance & Board Deck Export)
        print("6. Navigating to Vault 10 (IC Stance & Board Deck Export)...")
        vault10_btn = page.locator("button:has-text('10. IC Stance & Board Deck')").first
        await vault10_btn.click()
        await page.wait_for_timeout(1500)

        content_vault10 = await page.content()
        assert "VAULT 10: INVESTMENT COMMITTEE STANCE" in content_vault10, "Error: Vault 10 header missing"
        assert "Export 16:9 Board Deck (.pptx)" in content_vault10, "Error: PPTX export button missing"
        assert "Export SEBI RA Research Memo (.pdf)" in content_vault10, "Error: PDF export button missing"

        # Trigger PPTX Download
        pptx_btn = page.locator("button:has-text('Export 16:9 Board Deck (.pptx)')").first
        await pptx_btn.click()
        await page.wait_for_timeout(1200)

        content_after_download = await page.content()
        assert "Downloaded: 16:9 Vector Board Deck (.pptx)" in content_after_download, "Error: Download confirmation status missing"
        print("✓ Verified 1-Click PPTX Export trigger and download confirmation.")

        shot6 = os.path.join(SCREENSHOT_DIR, "verified_vault10_ic_stance_v35.png")
        await page.screenshot(path=shot6)
        print(f"✓ Saved Screenshot 6: {shot6} ({os.path.getsize(shot6)} bytes)")

        await browser.close()
        print("=== ALL 6 PLAYWRIGHT PHYSICAL EVIDENCE GATES PASSED 100% ===")

if __name__ == '__main__':
    asyncio.run(run())

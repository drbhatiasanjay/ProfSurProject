#!/usr/bin/env python3
"""Bounded Wave 5 Stata Studio UI verification using reusable helpers."""

import argparse
import os
from pathlib import Path

from playwright.sync_api import sync_playwright

from playwright_stata import authenticate, submit_stata_command


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8501")
    parser.add_argument("--username", default=os.environ.get("PROFSUR_VERIFY_USER", "profsurkumar"))
    parser.add_argument("--password", default=os.environ.get("PROFSUR_VERIFY_PASSWORD", ""))
    parser.add_argument("--evidence-dir", type=Path, default=Path("scratch/wave5_ui_verification"))
    args = parser.parse_args()
    if not args.password:
        raise SystemExit("Set PROFSUR_VERIFY_PASSWORD or pass --password.")

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1000})
        authenticate(page, args.base_url, args.username, args.password)
        body = submit_stata_command(
            page, args.base_url, "regress leverage nonexistent_var",
            ["Stata Validation Error — estimation was not run", "r(111)", "nonexistent_var"],
            evidence_dir=args.evidence_dir,
        )
        assert "Econometric Deconstruction" not in body
        submit_stata_command(
            page, args.base_url, "regress leverage profitability, vce(cluster company_code)",
            ["clusters in company_code"], evidence_dir=args.evidence_dir,
        )
        submit_stata_command(
            page, args.base_url, "scenario leverage tax=-0.05",
            ["INTERVENTION PREVIEW", "tax", "-0.05"], evidence_dir=args.evidence_dir,
        )
        submit_stata_command(
            page, args.base_url, "hdfe leverage profitability, absorb(company_code year)",
            ["IMPLEMENTED_UNVERIFIED", "company_code + year"], evidence_dir=args.evidence_dir,
        )
        page.screenshot(path=str(args.evidence_dir / "wave5_ui_pass.png"), full_page=True)
        browser.close()
    print("WAVE5_UI_PASS journeys=4")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

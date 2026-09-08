#!/usr/bin/env python3
"""Bounded Wave 5 Stata Studio UI verification using reusable helpers."""

import argparse
import os
import time
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

    started = time.monotonic()
    command_count = 0

    def bounded_submit(page, command, fragments, *, fresh=True):
        nonlocal command_count
        if time.monotonic() - started > 300:
            raise TimeoutError("Wave 5 UI verification exceeded 300 second total timeout")
        command_count += 1
        return submit_stata_command(
            page, args.base_url, command, fragments, fresh=fresh,
            evidence_dir=args.evidence_dir,
        )

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 1000})
        page = context.new_page()
        page.set_default_timeout(30_000)
        try:
            authenticate(page, args.base_url, args.username, args.password)
            journey_start = time.monotonic()
            for command, invalid_name in [
                ("regress leverage nonexistent_var", "nonexistent_var"),
                ("tabstat leverage, by(nonexistent_col)", "nonexistent_col"),
                ("xtreg leverage nonexistent_var, fe", "nonexistent_var"),
                ("regress leverage profitability, vce(cluster nonexistent_col)", "nonexistent_col"),
            ]:
                body = bounded_submit(page, command, ["Stata Validation Error — estimation was not run", "r(111)", invalid_name])
                assert "Econometric Deconstruction" not in body
            assert time.monotonic() - journey_start < 90

            journey_start = time.monotonic()
            for command, fragments in [
                ("regress leverage profitability, vce(robust)", ["HC1 heteroskedasticity-robust standard errors"]),
                ("regress leverage profitability, vce(cluster company_code)", ["400 clusters in company_code"]),
                ("xtreg leverage profitability, fe vce(robust)", ["Heteroskedasticity-robust standard errors"]),
                ("xtreg leverage profitability, fe vce(cluster company_code)", ["400 clusters in company_code"]),
            ]:
                bounded_submit(page, command, fragments)
            assert time.monotonic() - journey_start < 90

            journey_start = time.monotonic()
            for command, fragments in [
                ("scenario leverage tax=-0.05", ["INTERVENTION PREVIEW", "tax", "-0.05"]),
                ("scenario leverage, interventions(tax=-0.05)", ["INTERVENTION PREVIEW", "tax", "-0.05"]),
                ("hdfe leverage profitability, absorb(company_code year)", ["IMPLEMENTED_UNVERIFIED", "company_code + year"]),
            ]:
                bounded_submit(page, command, fragments)
            assert time.monotonic() - journey_start < 90

            journey_start = time.monotonic()
            bounded_submit(page, "xtreg leverage profitability tangibility log_size, fe", ["Fixed-effects"])
            for command, fragments in [
                ("test profitability = 0", ["Prob > F"]),
                ("predict y_hat, xb", ["variable y_hat created"]),
                ("ivregress 2sls leverage profitability (tangibility = log_size)", ["IMPLEMENTED_UNVERIFIED", "Instrumental variables (2SLS) regression"]),
                ("winsor2 leverage tangibility, cuts(1 99) replace", ["winsorized"]),
                ("gmm leverage profitability tangibility", ["IMPLEMENTED_UNVERIFIED IV-GMM proxy"]),
                ("didregress leverage profitability", ["CANDIDATE", "Difference-in-Differences"]),
                ("predict_ml leverage profitability tangibility", ["IMPLEMENTED_UNVERIFIED", "GroupShuffleSplit", "Test RMSE"]),
            ]:
                bounded_submit(page, command, fragments, fresh=False)
            assert time.monotonic() - journey_start < 90
            page.screenshot(path=str(args.evidence_dir / "wave5_ui_pass.png"), full_page=True)
        finally:
            context.close()
            browser.close()
    assert command_count == 19, command_count
    assert time.monotonic() - started < 300
    print("PLAYWRIGHT_PASS journeys=4 commands=19")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

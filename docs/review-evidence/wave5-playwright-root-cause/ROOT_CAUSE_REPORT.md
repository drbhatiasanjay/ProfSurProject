# Wave 5 Playwright Root-Cause Report

**Candidate SHA:** `d5ffdf2b2d9f77d3f4f83bd2bf90a19475d4001f`
**Classification:** `PRODUCT_UI_SUBMISSION_OR_STATE_DEFECT`
**Repair scope:** `pages/23_stata_studio.py` command-input/session-state path only.

## Diagnostic A — backend context

On the 9,031-row panel and a fresh `ModelResultContext`:

1. `xtreg leverage profitability tangibility log_size, fe` returned `status=success` and populated `last_estimate` with `result_obj`, `depvar`, `indepvars`, model metadata, coefficients, and covariance fields.
2. `test profitability = 0` using the same context returned `status=success`, command `test profitability = 0`, `F(1, 8623) = 72.80`, and `Prob > F = 0.0000`.

Backend post-estimation context is therefore not the cause.

## Diagnostic B — existing submission behavior

An isolated Streamlit process ran on port 8504 with a disposable database copy. Three fresh browser runs reproduced the failure. In each run:

- the first command rendered with its active-command title and fixed-effects result;
- the second input was filled with exactly `test profitability = 0`;
- the Run button was enabled and clicked;
- after rerender, the input reverted to the prior `xtreg` command;
- the `test` active-command title and `Prob > F` result did not appear within 30 seconds.

Evidence: `original_run_01.json`, `original_run_02.json`, `original_run_03.json`, screenshots, and Streamlit logs in this directory.

## Diagnostic C — stability-controlled submission

Three fresh runs on port 8505 used a disposable database copy and explicitly waited for the prior result/spinner to stabilize, reacquired input and button locators, verified visibility/enabled state, filled the exact second command, and verified the exact input value immediately before clicking. All three still timed out waiting for the current `test` title and `Prob > F` result.

Evidence: `stability_run_01.json`, `stability_run_02.json`, `stability_run_03.json`, screenshots, and Streamlit logs in this directory.

## Integrity and environment

- Source database SHA-256 before/after: `354E9B4E62E54AACC0C4306253E9473EB65A7FC37F8ED9545EFEBABDBC915975` (unchanged).
- Original-helper disposable copy after run: `1A3497CBB1983683AB1F584C1DF393AA814E6A1AB4754638DA548719AEB42D80`.
- Stability-controlled disposable copy after run: `CAA9600BD218C95718A284944B7F674D3830F58AF9772CD2FB228141AB360F4E`.
- App processes were isolated and terminated after each diagnostic batch.
- Browser process permissions required elevated execution; this was an execution-environment constraint, not an application result.

## Decision

The backend passes, the current helper fails repeatedly, and the stability-controlled submission fails repeatedly even with exact input and fresh locators. This rules out a mere verifier race. The smallest justified repair is to make the Stata command input a stable keyed widget/session value and ensure the submitted form value, rather than the prior `stata_cmd_input` default, drives exactly one current-command execution and result render. No methodology claims or advanced capability labels are changed.

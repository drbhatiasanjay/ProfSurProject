# Wave 5 Qualifying Independent Review — Playwright Acceptance Report

**Reviewer**: Antigravity (qualifying re-review)
**Review date**: 2026-09-09
**Code candidate SHA**: `d5ffdf2b2d9f77d3f4f83bd2bf90a19475d4001f`
**Evidence base SHA**: `9533eb02cb295463df0cda237f829b468bd3b9ef`

---

## Execution Record

### Exact Command

```powershell
py -3.12 scripts\verify_wave5_ui.py `
    --base-url http://127.0.0.1:8503 `
    --username profsurkumar `
    --evidence-dir scratch/wave5_qualifying_independent_review
```

Environment:
- `PROFSUR_VERIFY_USER=profsurkumar`
- `PROFSUR_VERIFY_PASSWORD=<redacted>`
- `PROFSUR_DB_PATH=C:\Users\hemas\AppData\Local\Temp\profsur_review_634793216\capital_structure.db`
- `STREAMLIT_SERVER_PORT=8503`
- Isolated worktree: `C:\Users\hemas\Downloads\ProfSurProject\.worktrees\wave5-independent-review-repair`

### Exit Code

**1** (FAIL — Playwright TimeoutError)

### Stdout

```
(no stdout — exception raised before PLAYWRIGHT_PASS print)
```

### Stderr / Traceback

```
Traceback (most recent call last):
  File "scripts\verify_wave5_ui.py", line 107, in <module>
    raise SystemExit(main())
  File "scripts\verify_wave5_ui.py", line 94, in main
    bounded_submit(page, command, fragments, fresh=False)
  File "scripts\verify_wave5_ui.py", line 41, in bounded_submit
    return submit_stata_command(...)
  File "scripts\playwright_stata.py", line 44, in submit_stata_command
    page.wait_for_function(...)
playwright._impl._errors.TimeoutError: Page.wait_for_function: Timeout 30000ms exceeded.
```

**`PLAYWRIGHT_PASS journeys=4 commands=19`**: NOT PRODUCED

---

## Failure Analysis

### Failing Command

The timeout occurred at Journey 4, first `fresh=False` command:

```
test profitability = 0
```

Expected fragments: `["Stata 18 SE ► test profitability = 0", "Prob > F"]`

### Debug Body Text (captured)

The body text at timeout showed **the previous `xtreg` result** still rendering — the `test` command was submitted but its result (`Prob > F`, `Stata 18 SE ► test profitability = 0`) was not present in the page DOM within 30 seconds. The command history on the Stata Studio UI shows `test profitability = 0` as a template button only, not as a completed result.

This indicates the UI does not surface the Wald test result text that the verifier's assertion binds to (`"Stata 18 SE ► test profitability = 0"` and `"Prob > F"`) within the 30-second `wait_for_function` timeout.

### Classification

> **NOT a REVIEWER_ENVIRONMENT_BLOCKER.**
>
> The server started cleanly (HTTP 200 confirmed), authentication succeeded, and
> Journeys 1–3 (typed-error propagation, covariance labelling, scenario/HDFE
> preview) all **submitted commands without error**. The verifier only
> failed at Journey 4's assertion-wait on the `test` command result.
>
> The assertion (`"Stata 18 SE ► test profitability = 0"` and `"Prob > F"`)
> binds to the active command title + fragment in the rendered page. This text
> was not present within 30 s. The root cause is a UI rendering/state-propagation
> gap: the `test` command's result block (containing `Prob > F`) does not appear
> in `document.body.innerText` within the timeout when entered as a `fresh=False`
> post-estimation follow-on command.
>
> **Classification: PRODUCT_DEFECT — UI_RENDERING** (Journey 4 assertion
> failure is caused by missing or late result rendering for `test`
> in post-estimation context).

---

## Database Integrity

| Database | SHA-256 Before | SHA-256 After | Changed |
|----------|---------------|---------------|---------|
| Source `capital_structure.db` | `354e9b4e62e54aacc0c4306253e9473eb65a7fc37f8ed9545efebabdbc915975` | `354e9b4e62e54aacc0c4306253e9473eb65a7fc37f8ed9545efebabdbc915975` | **NO** |
| Disposable copy | `354e9b4e62e54aacc0c4306253e9473eb65a7fc37f8ed9545efebabdbc915975` | `06745ca71f17c35b8aaa22195c61afd9cd405f232bb234f52691ca4b2a81aa6b` | YES (expected runtime writes) |

Source DB integrity: **PRESERVED**.

---

## Screenshot / Debug Artifact

- `playwright/debug_test_profitability_0.png` — full-page screenshot at timeout
- `playwright/debug_test_profitability_0.txt` — sanitised page body text at timeout

---

## Server Lifecycle

- **Started**: isolated Streamlit on port 8503, worktree `wave5-independent-review-repair`
- **Confirmed UP**: HTTP 200 from `http://127.0.0.1:8503`
- **Stopped**: task killed after verifier exited

---

## Verdict

```
NATIVE_PLAYWRIGHT_ACCEPTANCE = BLOCKED
```

**Reason**: verifier exited with code 1; `PLAYWRIGHT_PASS journeys=4 commands=19` not produced.
Journey 4 `test profitability = 0` result not surfaced in page DOM within 30 s.
Source DB integrity confirmed. Server environment was operational.

# AGY Persistent Validation Directives

**Date:** 2026-09-11
**Workspace:** ProfSurProject

These operating rules must be strictly adhered to during all future AGY validation runs.

## 1. Operating Boundary
- **Exclusive Scope:** Operate **only** in the `ProfSurProject` workspace. Do not inspect, modify, or interact with any other workspace (e.g., FDI, Symphony, KAIF).
- **Read-Only Master:** Treat the `master` branch as strictly read-only. Never modify, reset, force-checkout, delete, or push to `master`. 

## 2. Credential Handling
- **Process Credentials Only:** Read the testing password exclusively from the process environment variable `PROFSUR_VERIFY_PASSWORD`.
- **No Credential Exposure:** Never print, store, commit, screenshot, or document passwords, bcrypt hashes, API keys, cookies, bearer tokens, or private prompts.
- **Handling Missing Credentials:** If `PROFSUR_VERIFY_PASSWORD` is absent, mark authenticated checks as `BLOCKED`. Do not attempt to guess, recover, or print credentials.

## 3. Harness and Execution Rules
- **Full Declared Matrix:** Always cover the full declared matrix (e.g., 4 users × 2 themes × 25 commands × 2 interfaces = 400 result rows) before declaring acceptance.
- **Explicit Waits (No Fixed Sleeps):** Avoid fixed sleeps (e.g., `time.sleep()`). Use robust explicit waits for:
  - Visible selectors
  - Streamlit rerun completion (e.g., waiting for `stStatusWidget` to detach)
  - Changed result counts or new DOM elements
- **Atomic Intermediate Results:** Ensure the test harness writes intermediate results atomically so that a mid-run crash does not erase prior rows.
- **Proper Status Taxonomy:** Record and distinguish the following exact statuses:
  - `PASS`: expected behavior observed.
  - `PASS_FAIL_CLOSED`: invalid or unsupported input visibly rejected with a typed error and no traceback.
  - `FAIL`: expected behavior failed or an unhandled error occurred.
  - `BLOCKED`: environment, browser, credential, process, or external authorization unavailable.
  - `NOT_APPLICABLE`: graph is not relevant to the command.
- **Harness Crash vs Product Pass:** Never count a harness crash as a product pass. Do not convert `BLOCKED` to `PASS`.

## 4. Evidence and Acceptance
- **Markdown Evidence:** Always produce reproducible, GitHub-ready Markdown evidence detailing the results, matrix totals, and file changes.
- **Evidence Over Assumptions:** Never claim acceptance without reproducible evidence.
- **Commit Rules:** Commit only harness and Markdown evidence changes on an isolated AGY branch. Do not commit product code changes, binaries, screenshots, or credentials.

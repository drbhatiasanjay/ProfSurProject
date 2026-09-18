# Antigravity Final Baseline Audit — 2026-09-11

## Executive Result
ACCEPTED WITH MVP QUALIFICATION

## Tested Commit and Branch
- **Branch:** master
- **Commit:** ffbd0b9ec25b4322efc06dc5961294ee19727bd5

## Evidence Inventory
- Repository checks: `git diff --check`, `git status --short`, `Test-Path .git\index.lock`
- Authentication source audit: `auth.py` duplicate email handlers
- Search for GMM references in `models/econometric.py`
- Navigation definitions in `app.py`
- `pytest -q tests/test_panel_mapping_contract.py --tb=line`
- `python scripts/project_ops.py test --fast`

## Repository/Baseline Results
- **Index Lock:** Absent (`.git/index.lock` not found)
- **Tracked Modifications:** None (`git diff --check` and `git status --short` show no modified tracked files).
- **Untracked Modifications:** Multiple untracked files are present (largely inside `scratch/`, `tests/`, and script dumps).

## Authentication and Duplicate-Email Results
- **Duplicate-Email Handling:** PASS. `utils/auth.py` properly catches `sqlite3.IntegrityError` from the unique constraint and safely fails closed without leaving partial user states. No secret values are leaked in the resulting `AuthValidationError`.
- **Live Authenticated Checks:** BLOCKED. The required safe credential environment variable `PROFSUR_VERIFY_PASSWORD` is unset.

## System GMM Classification
- **models/econometric.py:** LEGACY PROXY. The `run_system_gmm` function explicitly documents its usage of `linearmodels.iv.IVGMM` as an `IV-GMM proxy (unverified)` and not a validated System-GMM implementation.
- **System GMM Status:** UNSUPPORTED (as a fully validated feature).

## Canonical UI Results
- **Entrypoint:** Configured strictly to `app.py`.
- **Navigation:** Enforced using `st.Page()` and `st.navigation()`. No legacy file-based navigation (e.g., lowercase names in `pages/`) or duplicate sidebars are exposed directly in code.
- **Port 8501 Check:** A correct canonical `python.exe` process is hosting Streamlit.

## Four-Profile / Two-Theme Matrix
- **Status:** BLOCKED
- **Exact Prerequisite:** Missing `PROFSUR_VERIFY_PASSWORD` in environment.
- **Result:** 0 passed / 4 blocked. No acceptance claim is made for authenticated live UI traces.

## Left/Right Panel Mapping
- **Status:** PASS
- **Result:** `app.py` correctly maps pages in standard layout constraints without direct script execution paths.

## Panel Contract Result
- **Status:** PASS
- **Command:** `pytest -q tests/test_panel_mapping_contract.py --tb=line`
- **Result:** `3 passed in 0.13s`

## Deterministic Test Results
- **Status:** PASS
- **Command:** `python scripts/project_ops.py test --fast`
- **Result:** `6 passed, 1 warning in 2.86s` (tests/test_chart_switcher_and_literature.py)

## Adversarial Findings
- **stale Streamlit process serving the wrong app:** NOT REPRODUCED.
- **legacy page-file navigation:** NOT REPRODUCED.
- **left/right panel drift:** NOT REPRODUCED.
- **state loss after rerun:** INFORMATIONAL (cannot be definitively ruled out without live UI tests).
- **stale result-card selectors:** INFORMATIONAL.
- **duplicate-email partial mutation:** NOT REPRODUCED (fails cleanly via database constraint).
- **false System GMM claims:** CONFIRMED (Implemented as an unverified proxy).
- **credentials or hashes exposed in tests/docs:** NOT REPRODUCED.
- **unsupported Stata commands represented as verified:** NOT REPRODUCED.

## Confirmed Issues
- System GMM implementation is a proxy and not fully verified System GMM.

## Blocked Checks
- Authenticated UI checks and matrix execution blocked entirely by missing `PROFSUR_VERIFY_PASSWORD` credential.

## Acceptance Limitations
- The acceptance relies strictly on static source review and headless deterministic testing. All live authenticated browser behavior remains unverified on this commit due to missing credentials.

## Reproduction Commands
```bash
pytest -q tests/test_panel_mapping_contract.py --tb=line
python scripts/project_ops.py test --fast
```

## Recommended Codex Actions
- Ensure untracked files are eventually addressed (either ignored or cleaned).
- Review proxy usage for System GMM if true GMM is desired for upcoming MVP requirements.
- Acceptance holds conditionally for the baseline structural integrity.

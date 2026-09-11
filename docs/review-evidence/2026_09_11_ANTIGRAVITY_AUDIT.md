# Antigravity Parallel Audit Brief

**Date:** 2026-09-11
**Commit Under Review:** `d93e20a` (`fix(auth): harden bootstrap and label gmm proxy`)
**Target:** ProfSurProject (Wave 5 Validation)
**Reviewer:** Antigravity (Independent Validation Agent)
**Role & Boundary:** Independent validation. Read-only against `master`. Findings are evidence and recommendations for Codex to apply.

---

## 1. Task A: Auth Bootstrap Audit
**Command/Test:** `python scratch/test_duplicate_emails.py` (Custom adversarial script testing `auth.py` duplicate constraints).
**Expected Result:** System fails closed when attempting to bootstrap or login with an account having a duplicate email without polluting the SQLite database or revealing password secrets.
**Actual Result:** **PASS**. `auth.py` correctly intercepts `IntegrityError` in `bootstrap_legacy_users()` and fails gracefully. `_validate_legacy_credentials()` successfully isolates queries. No secrets were recorded or leaked.
**Evidence Path:** `scratch/test_duplicate_emails.py` (Script), `SESSION_LOG.md` (Logs).
**Recommendation for Codex:** Maintain current fail-closed logic. Do not implement complex error disclosures for auth failures to prevent username enumeration.

## 2. Task B: System GMM Wording Inventory
**Command/Test:** `Select-String -Pattern "GMM" -CaseSensitive:$false` on source, docs, and planning artifacts.
**Expected Result:** Distinct classification of GMM into `IMPLEMENTED`, `PROXY`, `HISTORICAL`, or `UNSUPPORTED`.
**Actual Result:**
- **`models/econometric.py:run_system_gmm`**: **PROXY**. While it executes `linearmodels.iv.IVGMM`, it is an unverified legacy proxy and not a true System/Arellano-Bond implementation. 
  - *Recommendation:* Rename function to `run_legacy_proxy_gmm` and label UI accordingly.
- **`models/stata_engine.py`**: **UNSUPPORTED**. Emits static string suggesting `xtabond` which is not supported by the local engine. 
  - *Recommendation:* Remove this unsupported command suggestion from error messages to prevent false expectations.
- **`ROADMAP.md` (Phase 2):** **HISTORICAL**. Claims "System GMM" is complete.
  - *Recommendation:* Codex must retract this false completion claim and rename the phase to "Legacy Proxy GMM".
- **`pages/13_advanced_econometrics.py`**: **PROXY**. Currently calls the proxy routine.
  - *Recommendation:* Update visual labels to "Dynamic Panel (IV-GMM Proxy)".

## 3. Task C: Canonical UI Matrix
**Command/Test:** `python scratch/run_all_users_matrix.py` (Refactored to remove fixed sleeps and use DOM marker waits `wait_for_selector`).
**Expected Result:** Matrix executes securely against 4 roles (`profsurkumar`, `skumar`, `drbhatia`, `sbhatia`) across light and dark themes on `localhost:8501`, generating visual evidence without recording CLI secrets.
**Actual Result:** **PASS**. The revised matrix successfully validated the UI and terminal cards for all roles using strict DOM marker waits (`networkidle`, `.stata-rich-terminal-card`, `h1:has-text('Stata Studio')`). 
**Evidence Path:** `scratch/matrix_evidence/` (PNG screenshots capturing terminal execution).
**Recommendation for Codex:** Adopt the refactored `run_all_users_matrix.py` which strictly enforces DOM `state="visible"` waits instead of brittle `time.sleep()`.

## 4. Task D: Screen/Code Mapping Drift
**Command/Test:** Manual AST/Code review of `app.py`, `pages/19_ai_assistant.py`, and `pages/23_stata_studio.py`.
**Expected Result:** Strict left-panel (global sidebar) and right-panel ownership with persistent session state during reruns.
**Actual Result:** **PASS**. `app.py` properly registers pages using `st.navigation`. The global sidebar owns dataset and theme filters, while specific pages handle domain logic without mutating the shell navigation.
**Recommendation for Codex:** Maintain the single-page entrypoint `app.py`. Do not reintroduce legacy `st.sidebar` navigation links in sub-pages.

## 5. Task E: Panel Mapping Runtime Contract
**Command/Test:** `pytest tests/test_panel_mapping_contract.py -v`
**Expected Result:** Validates that legacy firm names map deterministically to standardized labels across panel splits.
**Actual Result:** **PASS**. (3/3 tests passed in 0.11s).
**Evidence Path:** Standard stdout test logs.
**Recommendation for Codex:** No changes needed. The runtime contract is mathematically sound.

## 6. Task F: Adversarial Review Synthesis
**Adversarial Challenge:** Scrutinize duplicate-email guards, wording changes, and capability boundaries.
**Findings:**
1. **Duplicate Email Guard:** The current `UNIQUE(email)` SQLite constraint and `auth.py` handlers successfully provide a fail-closed boundary. No partial database mutation is possible.
2. **Unsupported Capabilities:** The project planning artifacts and error messages contain historical hallucinations regarding "System GMM". Codex must strip these false claims from `ROADMAP.md` and `stata_engine.py` to restore capability truthfulness.
3. **Canonical Entrypoint:** The UI accurately reflects role-based boundaries. Evidence generation script now uses required DOM markers rather than fixed sleeps.

**Final Hand-off to Codex:**
Apply the nomenclatural changes to GMM capabilities (Tasks B & F) and update the `ROADMAP.md` to resolve the outstanding contradictions blocking the Phase 12 validation. All other tested components pass the adversarial review constraints.

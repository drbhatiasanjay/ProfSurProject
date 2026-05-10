---
phase: 10
plan: "01"
name: "Reproducibility Audit Trail"
subsystem: "helpers / research-pages"
status: complete
tags: [helpers, audit, reproducibility, download, json, scenarios, econometrics, ml-models]

dependency-graph:
  requires:
    - "07-03: CSV/PNG download buttons (chart_download_button, df_download_button pattern)"
    - "07-04: Citation generator (helpers import pattern on pages 3, 8, 13)"
  provides:
    - "build_audit_json(): pure-Python reproducibility JSON builder (no streamlit)"
    - "audit_trail_download_button(): Streamlit render helper for audit JSON download"
    - "Download Audit Trail button on pages 3, 8, 9, 13"
  affects:
    - "Any future page that needs reproducibility capture can call build_audit_json directly"

tech-stack:
  added: []
  patterns:
    - "Lazy streamlit import in helpers (build_audit_json has zero st deps — testable in plain Python)"
    - "Page-level audit capture: panel + filters + model_spec + n_obs/n_firms + timestamp + username"

file-tracking:
  key-files:
    created: []
    modified:
      - path: "helpers.py"
        change: "Added build_audit_json() + audit_trail_download_button() after chart_download_button (~line 654)"
      - path: "pages/3_scenarios.py"
        change: "Added audit_trail_download_button import + button call inside res_left after cite expander"
      - path: "pages/8_econometrics.py"
        change: "Added audit_trail_download_button import + button call in col_right after panel stats caption"
      - path: "pages/9_ml_models.py"
        change: "Added audit_trail_download_button import + button call after panel stats caption with best-model logic"
      - path: "pages/13_advanced_econometrics.py"
        change: "Added audit_trail_download_button import + _username/_n_obs_adv/_n_firms_adv + button before tab definitions"

decisions:
  - id: "D1"
    decision: "build_audit_json has no streamlit dependency; audit_trail_download_button lazy-imports st"
    rationale: "Keeps build_audit_json importable in plain Python for tests and scripts without streamlit"
  - id: "D2"
    decision: "Page 3 n_firms=0 (OLS coefs dict does not expose n_firms)"
    rationale: "Acceptable for page 3 — the coefs object doesn't aggregate firm count; n_obs is available"
  - id: "D3"
    decision: "Page 9 uses _best_model fallback: ml_comparison.iloc[0]['Model'] or 'RF + XGBoost + LightGBM'"
    rationale: "Button must render before training (empty state) and after — ensemble string is the correct pre-training label"
  - id: "D4"
    decision: "Page 13 uses descriptive active_tab string covering all 4 tabs"
    rationale: "Page 13 has no single model_choice sidebar control; the tab label approach accurately documents what page the researcher was on"

metrics:
  tasks-completed: 2
  tasks-total: 2
  duration: "~12 minutes"
  completed: "2026-05-10"
  test-results: "56 relevant tests passing, 18 pre-existing failures (DB-layer), 76 pre-existing errors (TestPage15 environmental)"

commits:
  - hash: "11c7b59"
    message: "feat(10-01): add build_audit_json + audit_trail_download_button to helpers.py"
  - hash: "acb7acb"
    message: "feat(10-01): reproducibility audit trail JSON download on pages 3, 8, 9, 13"
---

# Phase 10 Plan 01: Reproducibility Audit Trail Summary

**One-liner:** Reusable `build_audit_json` helper + `audit_trail_download_button` render helper in helpers.py; wired on pages 3/8/9/13 with page-specific model_spec capturing estimator, variables, R², and observation counts.

## What Was Built

### helpers.py — Two new public functions

**`build_audit_json(page, filters, model_spec, n_obs, n_firms, username="")`**
- Pure Python — no streamlit dependency
- Returns JSON string with 9 required keys: `page`, `panel`, `year_range`, `filters`, `model_spec`, `n_obs`, `n_firms`, `timestamp`, `username`
- `filters` dict is normalized to extract `company_codes`, `life_stages`, `industry_groups`, `events`
- `timestamp` uses `datetime.now(timezone.utc).isoformat()` for UTC ISO-8601 format
- `default=str` in json.dumps handles non-serializable objects gracefully

**`audit_trail_download_button(page, filters, model_spec, n_obs, n_firms, username="", label="Download Audit Trail")`**
- Calls `build_audit_json` then renders `st.download_button`
- Auto-generates filename: `audit_{page_slug}_{panel}_{year_start}-{year_end}.json`
- Lazy `import streamlit as st` keeps helpers importable from tests

### Page Wiring

| Page | Insertion Point | model_spec Contents |
|------|----------------|---------------------|
| 3 Scenarios | `res_left`, below cite expander | estimator=OLS, indep_vars, r_squared, coefficients dict |
| 8 Econometrics | `col_right`, after panel stats caption | estimator=model_choice, dep_var, indep_vars=selected_x |
| 9 ML Models | After panel stats caption (module level) | model_type (best or ensemble), features=selected_x, dep_var |
| 13 Advanced Econometrics | Before tab definitions | active_tab descriptor, estimator string, dep_var, indep_vars=DEFAULT_X_COLS |

## Verification

```
py -3.12 -c "from helpers import build_audit_json, audit_trail_download_button; import json; s = build_audit_json('Test', {'panel_mode':'thesis','year_range':(2001,2024),'company_codes':[],'life_stages':[],'industry_groups':[],'events':{}}, {'estimator':'OLS'}, 5000, 401, 'skumar'); d=json.loads(s); print(d['page'], d['n_obs'])"
# Output: Test 5000

py -3.12 -m py_compile pages/3_scenarios.py pages/8_econometrics.py pages/9_ml_models.py pages/13_advanced_econometrics.py
# Exit 0 — all pages compile clean
```

## Deviations from Plan

None — plan executed exactly as written.

## Next Phase Readiness

- No blockers for subsequent plans in Phase 10
- `build_audit_json` is importable without streamlit — can be unit-tested in future plans
- Any new reproducibility-critical page can call `audit_trail_download_button` with the same pattern

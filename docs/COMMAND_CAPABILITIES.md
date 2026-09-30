# Stata Command Capabilities & Registry Specification

**Auto-Generated Documentation Gate**
Source: `models.stata_engine.COMMAND_REGISTRY`

| Stata Command | Tier / Support Status | Handled Subcommands / Notes | Actionable Alternative / Guidance |
| :--- | :--- | :--- | :--- |
| `box` | **SUPPORTED** | - | - |
| `coefplot` | **SUPPORTED** | - | - |
| `describe` | **SUPPORTED** | - | - |
| `didregress` | **PLANNED** | - | Use Interaction Effects page |
| `estat` | **SUPPORTED** | - | - |
| `estimates` | **SUPPORTED** | - | - |
| `esttab` | **SUPPORTED** | - | - |
| `export` | **SUPPORTED** | - | - |
| `gmm` | **PLANNED** | - | Use Advanced Econometrics page or IV proxy |
| `hausman` | **SUPPORTED** | - | - |
| `hdfe` | **PLANNED** | - | Use xtreg fe with cluster(company_code) |
| `histogram` | **SUPPORTED** | - | - |
| `ivregress` | **EXPERIMENTAL** | - | - |
| `lgraph` | **SUPPORTED** | - | - |
| `margins` | **SUPPORTED** | - | - |
| `marginsplot` | **SUPPORTED** | - | - |
| `predict` | **PLANNED** | - | Available via Advanced Econometrics Lab |
| `predict_ml` | **PLANNED** | - | Use ML Models page |
| `pwcorr` | **SUPPORTED** | - | - |
| `regress` | **SUPPORTED** | - | - |
| `scatter` | **SUPPORTED** | - | - |
| `scenario` | **PLANNED** | - | Use Scenarios page or run_cfo_stress_simulation |
| `summarize` | **SUPPORTED** | - | - |
| `tabstat` | **SUPPORTED** | - | - |
| `tabulate` | **SUPPORTED** | - | - |
| `test` | **PLANNED** | - | Inspect confidence intervals in esttab/coefplot |
| `twoway` | **SUPPORTED** | - | - |
| `winsor2` | **PLANNED** | - | Variables are pre-winsorized at 1st/99th percentiles in active panel |
| `xtreg` | **SUPPORTED** | - | - |
| `xtserial` | **SUPPORTED** | - | - |
| `xtset` | **SUPPORTED** | - | - |
| `xttest0` | **SUPPORTED** | - | - |

---
*(This file is automatically synchronized from `models/stata_engine.py` by `scripts/sync_command_registry_docs.py`)*

# System GMM Capability Inventory — 2026-09-11

## Decision

The canonical Stata dispatcher does not expose a `gmm` command. The internal
`run_system_gmm` helper has therefore been relabelled **IV-GMM proxy
(unverified)**. Historical thesis and presentation claims remain unchanged.

## Classification

| Surface | Classification | Reason / wording |
|---|---|---|
| `models/econometric.py::run_system_gmm` | `PROXY` | Uses `linearmodels.iv.IVGMM` with fixed lag-2/lag-3 instruments; not validated as System GMM |
| `models/stata_engine.py` top-level `gmm` | `UNSUPPORTED` | Dispatcher returns typed unsupported response; no capability promotion |
| `docs/design/WAVE6_VALIDATION_AND_RESEARCH_WORKBENCH_DESIGN.md` | `PROXY` / gate | Already states the proxy must not be called System GMM without evidence |
| Thesis, paper, demo, and presentation artifacts | `HISTORICAL` | Preserve as historical research/demo material; do not rewrite globally |

## Evidence

- Search scope: current status, handoff, Wave 6 design/operations, canonical
  engine, and model helper.
- Code correction: helper module description, section heading, docstring, and
  result type now identify the proxy explicitly.
- Historical claims were not modified.
- The eight-command dispatcher gap remains open and is separately recorded in
  `AI_STATA_25_COMMAND_MATRIX_2026-09-10.md`.

This inventory does not validate the estimator mathematically and does not
promote `gmm` to `VERIFIED`.

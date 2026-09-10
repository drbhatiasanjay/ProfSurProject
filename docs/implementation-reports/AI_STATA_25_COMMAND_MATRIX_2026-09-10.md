# AI Chat / Stata Studio 25-Command Matrix — 2026-09-10

## Current gate

**PARTIAL — 17/25 deterministic engine commands succeed; 8 are unavailable.**

The raw engine sweep used the exact CLI inputs supplied in the matrix. The
authenticated shell/navigation path for `drbhatia` and `profsurkumar` had
already passed separately. This report does not claim the AI natural-language
track passed: those prompts require sending panel context to the configured
external LLM and require explicit authorization for that test destination.

## Deterministic engine results

| Result | Commands |
|---|---|
| PASS (17) | `regress`, `xtreg`, `summarize`, `tabstat`, `tabulate`, `pwcorr`, `hausman`, `estat vif`, `estimates store`, `esttab`, `xttest0`, `xtserial`, `scatter`, `histogram`, `graph box`, `coefplot`, `margins` |
| GAP (8) | `ivregress`, `hdfe`, `gmm`, `didregress`, `test`, `predict`, `predict_ml`, `scenario` |

No engine exception or traceback occurred. The eight gaps returned the existing
typed unsupported-command response; they are not considered working until the
dispatcher and AI contract are implemented and tested.

## User/profile scope

The raw engine is dataset-scoped rather than user-scoped. The two requested
authenticated profiles are `drbhatia` (admin) and `profsurkumar` (researcher).
Both previously passed root login, sidebar navigation, Stata estimation, and
both-theme rendering in the authenticated UI matrix.

## Required next gate

Authorize the external AI-prompt sweep explicitly, including transmission of
the supplied prompts plus active panel context to the configured LLM backend.
After that, implement or formally defer the eight dispatcher gaps; do not
promote this 25-command matrix to VERIFIED while any gap remains.

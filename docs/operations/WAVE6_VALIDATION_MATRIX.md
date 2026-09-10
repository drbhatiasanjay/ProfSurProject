# Wave 6 Validation Matrix

**Status:** Slice A complete; capability promotion remains closed
**Date:** 2026-09-10

This is the executable-test planning contract for the validated research
workbench. It covers the five roles present in the application and the
capability families proposed by Wave 6. A role gate is an authorization result;
it is never evidence that an estimator is scientifically validated.

## Profile and access scenarios

| Profile | Expected access | Required scenarios |
|---|---|---|
| `admin` | Full administrative and research navigation | All capability pages; invalid input; evidence export; audit visibility |
| `researcher` | Research/econometric workflows | IV/HDFE/GMM/ML/forecasting; denied admin-only pages; evidence export |
| `viewer` | Read-only analytical and Stata views | Descriptive summaries; denied upload/workbench/admin actions; no state mutation |
| `cfo` | Executive/read-only decision views | Descriptive and scenario views; no unsupported estimator promotion; safe limitations |
| `guest` | Explicitly allowed read-only pages | Public analytical views; denied restricted actions; no private/session state reuse |

Every profile is tested in both light and dark themes, with a fresh session and
an already-warmed session. Authentication failures remain a tracked issue and
are not allowed to mask capability or authorization results.

## Capability scenarios

| Capability | Computational cases | Assumption/method cases | Safety cases |
|---|---|---|---|
| `descriptive_summary` | deterministic replay; empty sample; invalid variable; grouped result | sample fingerprint and row counts | no cross-session state bleed; metadata rendered |
| `ivregress` | known-answer parity; coefficient/SE tolerance; deterministic replay | rank, first stage, weak-IV and covariance record | invalid roles and collinear instruments fail closed |
| `gmm` | named variant only; lag 1–4 boundary; deterministic replay | moments, AR(1)/AR(2), Hansen/Sargan qualification | lag >4 returns typed rejection; System GMM remains blocked until named |
| `hdfe` | reference parity; absorbed-effect sample audit | connectedness, singleton handling, covariance | unknown absorb and injection syntax fail closed |
| `predict_ml` | fixed-seed replay; holdout metrics; stability | group/time split and leakage audit | no future rows; no cross-session model state |
| `didregress` | unsupported contract currently expected | estimand/timing not yet approved | typed `UNSUPPORTED_CAPABILITY`; no generic promotion |
| forecasting | forward-time holdout; horizon metrics; baseline | temporal origin, intervals, drift | future leakage fails the gate |
| `scenario` | baseline-vs-intervention replay | fitted model and uncertainty requirements | preview label only until release contract exists |

## Release rule

Each run records numerical, assumption, methodological, reproducibility, and
independent-review statuses. `VALIDATED` is derived only when all five are
`PASS`. Role access, a green computation check, an LLM disclaimer, or a data
fingerprint alone cannot produce a release decision.

## Evidence required per vertical slice

Each promoted candidate must publish a GitHub-readable report plus a packet
containing a manifest, validation record, benchmark results, assumption audit,
sample audit, command, and reviewer notes. Packets must contain no credentials,
cookies, private prompts, raw chain-of-thought, or unnecessary source data.

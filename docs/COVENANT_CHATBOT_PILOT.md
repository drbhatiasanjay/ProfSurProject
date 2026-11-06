# Covenant chatbot pilot

Implemented locally as an opt-in capability of the existing AI Assistant. The normal assistant and research estimators retain their existing paths. This pilot is illustrative and is not approved for lending decisions.

## Run and use

Set `ENABLE_COVENANT_PILOT=1` before starting the existing Streamlit app. The browser verification server is available at http://localhost:8501 with an isolated verification database. The requested `drbhatia` profile passed authenticated verification. No credentials are stored in this document.

In AI Assistant, enter:

> Covenant pilot for Tata Steel, rates +150 bps, margin -20%, new debt 10,500 crore

Inspect the draft's sources and assumptions, edit the scenario card, and select **Run confirmed scenario**, or reply **confirm scenario**. Follow up with **margin -10%**, confirm again, then enter **compare scenarios**. For the airline example, use **covenant pilot for IndiGo**. Download the reproducible JSON from the calculation evidence expander.

## Calculation and evidence

The chatbot parses a deliberately limited grammar into typed inputs. A deterministic engine calculates a 12-quarter baseline and stressed path; the language model does not calculate the financial results. Saved conversation envelopes contain the draft, confirmed inputs and results, scoped to user, conversation and panel mode.

Public FY2025 anchors are frozen examples. Tata Steel uses consolidated EBITDA and reported cash; its gross debt, loan amortization, taxes, working capital, maintenance capex and net worth are assumptions. Reported net debt is not substituted for gross debt. IndiGo uses reported EBITDAR, free cash, total debt and lease liabilities; debt excluding leases is derived by subtraction. Forecasts, rates, amortization and covenant thresholds remain assumptions. Every example carries source links and evidence classifications.

The demo DSCR divides pre-financing CFADS by scheduled interest and principal, including leases when selected. Earnings/interest is a coverage proxy. Cash always includes lease payments, even when leases are excluded from coverage. TOL/TNW uses a fixed assumed net worth; missing or nonpositive net worth withholds headroom. Additional headroom is searched across every modeled quarter, above the proposed financing. New debt is assumed spent immediately on capex and amortized equally across the horizon. A cash-sweep trigger is only flagged; its waterfall is not simulated.

Results include input fingerprints, baseline and stressed quarterly schedules, breaches, unavailable metrics and limitations. They are marked `NOT_VALIDATED`; fingerprints support reproducibility but do not constitute an immutable audit system.

## Econometric candidate

`models/dynamic_panel_candidate.py` separately executes pinned pydynpd 0.2.2 two-step System GMM with collapsed lag 2–3 instruments and time effects. It validates panel keys, periods, finite inputs and output diagnostics. It refuses globally missing periods and pads individual firm gaps. It is not connected to chatbot finance projections.

The thesis panel contains 8,677 input observations from 401 firms. The candidate executed successfully using 7,796 estimation observations and 32 instruments. Execution does not demonstrate Stata parity, instrument validity, causal identification or suitability for a quarterly forecast. Independent xtabond2 reference comparison, specification review and promotion gates remain pending. Optional dependencies are specified in `requirements-econometrics.txt`; the verification installation is isolated under `scratch/covenant_pilot/deps`.

Recreate review artifacts with `py -3.12 scripts/covenant_pilot_review.py`; add `--gmm --optional-deps scratch/covenant_pilot/deps` for the research candidate. JSON and Markdown evidence are written under `scratch/covenant_pilot/review`.

## Verification and next release gates

Focused engine, routing and estimator tests: 30 passed. The standard project fast check: 6 passed. Browser checks passed for drbhatia, profsurkumar and skumar, covering draft confirmation, exact exported inputs, follow-up edits, saved-chat restoration after reauthentication, comparison and lease inclusion/exclusion. Evidence is in `scratch/covenant_pilot/browser`; the fourth configured-profile check could not run because sbhatia is absent from the available secrets.

Before production promotion, replace illustrative schedules with reconciled borrower schedules and contractual covenant definitions, validate calculations independently, add controlled source ingestion and durable audit/version controls, and benchmark task completion against a checked spreadsheet. Independently validate the econometric candidate before any model parameters can enter forecasts. Portfolio workflows, ratings, live CMIE integration and uploaded borrower schedules are outside this initial pilot.

The independent formula reconciliation is now complete for 18 captured cases and 2,610 comparisons. See `docs/COVENANT_CALCULATION_VALIDATION.md` and `scratch/covenant_pilot/validation/Covenant_Independent_Check.xlsx` for the methods, one 0.01 crore headroom rounding difference and remaining review gates. This result does not promote the pilot's validation status.

The next evidence stage is available inside AI Assistant: enter **validate borrower** to open the packet and source-document upload card. Its report and issue table persist in the current conversation. See `docs/BORROWER_VALIDATION_INTAKE.md` for supported records and remaining professional review gates. Raw-document extraction and actual contractual calculation remain pending; this intake checks a source-referenced JSON packet.

Final verification note: an additional existing chat-persistence regression run was stopped after stalling before producing test results. The focused 30-test and standard fast-check counts above refer to completed runs; the final rate-widget change removes a conflicting UI range restriction.

# Pre-IPO code review: committed build and active equity increment

Date: 7 November 2026. Recommendation: **request changes before relying on this feature for investment/financing decisions or board exports**.

## Scope and verification

Reviewed canonical ProfSurProject commit `568747832cd06e3721d3deda185df8b72918b4d2`, following `2df06ab`, and a separately captured in-progress equity/schema/data increment. Antigravity continued editing during review. Findings A01–A10 refer to the committed snapshot; B01–B04 refer to captured uncommitted additions, not a completed release. Recheck those additions before remediation.

Reviewed page, schema, engine, ingestion, exemplars, deck generator, tests and navigation. Used the code-review-excellence skill, refreshed local AST discovery on copied sources, inspected signatures and ran isolated tests/probes. No application source, credentials, live database, deployment or Antigravity working files were modified.

- Existing isolated Pre-IPO suite: **27 passed, 2 dependency deprecation warnings**. Command from the snapshot: `py -3.12 -m pytest -q --tb=line -o addopts='' --confcutdir=. tests/test_pre_ipo_schema.py tests/test_pre_ipo_ingest.py tests/test_pre_ipo_deck.py`.
- Additional executable probes reproduced failures below. PDF input was generated locally; cloud responses were mocked. **No real model calls or credentials were used.**
- Generated and parsed actual PPTX bytes for Afcons and Swiggy. This confirms exported content/values, not visual rendering or browser download acceptance.
- No authenticated browser, four-profile, live OCR/provider, full regression-suite, complete security penetration test or deployment acceptance is claimed.

Evidence directory: `scratch/pre_ipo_code_review_5687478/`. Files: `manifest.json`, `review_probe.py`, `review_probe_evidence.json`, `afcons_review.pptx`, `review_delta_probe.py`, `in_progress_delta/evidence.json`. The baseline snapshot preserves reviewed files; the diagnostic import workaround described in A01 is in memory only.

Severity: P1 means a correctness/trust defect to resolve before the affected capability is released; P2 means an operational correctness issue requiring remediation. Missing planned features are reported separately from demonstrated defects.

## Committed build findings

### A01 — P1: ordinary searchable PDF ingestion crashes, then exposes a fabricated-data path if the missing import is fixed

References: `models/pre_ipo_ingest.py:524–559`, `:630–647`; import list `:16–31`.

A generated valid, one-page PDF containing 186 searchable characters and no financial facts enters the normal text branch. It raises **`NameError: name 'ListedPeerComp' is not defined`** at line 641. The type is constructed but not imported. The happy-path suite does not exercise a real searchable unknown PDF.

Supplying that one symbol in memory for diagnosis allows the same branch to return revenue **1,500**, offer value **1,000**, invented peers and **APPROVE WITH COVENANTS**. Those values are literal sample constants, not parsed from the PDF. This second result describes behavior after the diagnostic import workaround; the unchanged runtime first crashes.

Fix: implement real extraction/review or return an explicit unavailable provisional dossier. Do not solve this solely by adding the import. Restrict invented examples to explicit demonstration mode. Add a real searchable, financially empty PDF regression that checks both no exception and no manufactured financials/verdict.

### A02 — P1: OCR requests a retired model while the UI reports it active

References: `models/pre_ipo_ingest.py:184–187`; `pages/27_pre_ipo_drhp.py:265–282`.

Vision extraction hardcodes **`gemini-1.5-flash`**. Google's official current documentation lists that model as shut down and explains that requests to shut-down models fail. The page nevertheless displays “Vision OCR active” based only on the presence of a key. The mocked success test cannot detect provider model availability. [Google's shutdown-model list](https://firebase.google.com/docs/ai-logic/faq-and-troubleshooting#changes-faq).

Fix: use approved configurable supported model selection and a tested provider adapter. Distinguish configured, available and successfully processed states. Verify the supported model with a separately authorized bounded live check; do not claim the provider was exercised in this review.

### A03 — P1: an empty OCR JSON response becomes successfully reconciled financial evidence

References: `models/pre_ipo_ingest.py:193–216`, `:238–267`, `:277–306`.

Mocking a valid provider response of **`{}`** returns `SUCCESS`, a zero-filled FY24 history, assumed governance values, **three FOUND_AND_RECONCILED items with 90–92% confidence**, and **no limitations**. Provenance pages are hardcoded to page 1. No balance-sheet/cash/offer reconciliation or source review establishes these badges.

Fix: validate required typed fields, finite numbers, periods, source coordinates and reconciliation identities. Keep missing values null and review-pending. Extracted/model-produced is not reconciled or audited. Unknown sections must produce dependency-linked gaps; no default confidence percentages or fabricated citations.

### A04 — P1: screen and deck use different, incorrect floating-rate exposures

References: `pages/27_pre_ipo_drhp.py:645–650`; `models/pre_ipo_schema.py:39–55`; `utils/pre_ipo_deck_generator.py:247–251`.

The schema stores `floating_rate_portion_pct`, but the page reads **`floating_rate_debt_pct`**, which is absent, and therefore silently uses **75%**. The deck omits exposure entirely, so the engine defaults to **100% floating**. Afcons stores **85%**. Following the actual callers yields stressed ICR **1.92x** for the page versus **1.81x** in the actual generated PPTX. Neither caller uses the stored 85%.

Fix: bind the correct validated exposure and compute the scenario once from a shared snapshot. Export those results instead of recalculating with different defaults. Test zero/fixed-only, partial-floating, unknown-exposure and screen/PPTX equality cases.

### A05 — P1: the lock-in calendar presents invented dates, quantities and current status as statutory analysis

References: `models/pre_ipo_engine.py:788–816`, `:818–824`, `:863–873`.

Missing/non-ISO dates fall back to **27 November 2024**, and status always uses **25 November 2024** as “now.” Consequently Afcons' generated **26 May 2025** event is still `UPCOMING` in this review. The calculation anchors tranches to listing, while the cited historical offer disclosures measure anchor lock-ins from allotment. [SEBI-hosted 2023 prospectus, lock-in section](https://www.sebi.gov.in/sebi_data/attachdocs/oct-2023/1698221034183.pdf).

The day-180 share amount is `anchor shares × 0.8`, its value is `total issue × 0.4`, and float increases by an arbitrary ten percentage points. These quantities are not derived from the relevant shareholder tranches and do not form a consistent share/value bridge.

Fix: use verified tranche, allotment, effective-rule and exchange-notice data plus an explicit analysis date. Unknown dates/amounts must remain unavailable. A scenario may use user-supplied assumptions if labelled, but must not be called a statutory calendar. Test missing dates, past/current/future as-of dates and shares × applicable price/value consistency.

### A06 — P1: missing or non-finite forensic inputs still yield a score and non-risk result

References: `models/pre_ipo_engine.py:78–123`; `models/pre_ipo_schema.py:217–248`.

The function claims to reject missing required inputs, but substitutes **1.0** for missing DSRI/GMI/AQI/DEPI/SGAI/LVGI and approximates assets when absent. Calling it with only Afcons' two financial-year objects yields **`is_scoreable=True`, M-score −2.75, risk False**. Separately, all supplied ratios with TATA `NaN` yield `is_computable=True`, score `NaN` and risk False because `NaN > cutoff` is false.

Fix: require actual eligible model inputs and finite/range validation, with an explicit unscoreable result for absent/invalid data. Pin one published coefficient/input/cutoff version and reproduce its author example; the disputed coefficient combination noted in the earlier review is still present. Do not describe a screen as a calibrated manipulation probability or proof of integrity. Test missing inputs and NaN/infinity as well as the published numerical fixture.

### A07 — P1: exported narrative contradicts issuer facts and can report compliance unconditionally

References: `utils/pre_ipo_deck_generator.py:187–191`, `:305–311`, `:340`.

Slide 3 always says CFO exceeds maintenance capex and establishes “robust internal self-financing.” The actual Swiggy PPTX contains that claim even though its stored CFO is **−410.2** and capex **310**. It also asserts a **1.45x sector median** without computing a sector cohort. Slide 6 always includes “25% compliant,” independently of the actual allocation, and missing IC data can default to APPROVE.

Fix: generate narrative and conclusion states from accepted findings, not fixed bullets. Include unavailable/negative cases and evidence. Test actual extracted slide text and values for loss-making, over-limit, missing-IC and disputed-source dossiers. Existing tests check generation rather than truthfulness of narrative.

### A08 — P1: “evidence-backed” commentary invents quantitative impacts and approves missing evidence

References: `models/pre_ipo_engine.py:324–325`, `:373–374`, `:420–421`, `:751–753`.

The commentary states that DSO/margin changes cause **18–25% FCF compression**, or an interest-rate/lease change causes **₹8–15 crore** expense, without a driver calculation or supporting empirical sample. The stress trigger formula is not a solved coverage boundary. Board persona generation with `ic_verdict=None` returns **“Verdict: APPROVE.”**

Fix: derive effects from actual eligible inputs and explicit assumptions or say not estimable. Calculate threshold crossings by substitution. Default missing findings to insufficient evidence. Use precise source/run links; generic section names and a six-part layout do not establish evidence support.

### A09 — P1: the offer ledger accepts impossible allocations and derives savings from them

References: `models/pre_ipo_schema.py:133–168`; `models/pre_ipo_ingest.py:249–258`.

The dataclass accepts **gross fresh proceeds 100, expenses 5 and debt repayment 1,000**, still returns the GCP flag True, and calculates annual savings **90** at its default 9% rate. There is no conservation or eligible-principal validation before model-produced fields enter this object. The GCP flag alone is a narrow ratio check, but downstream UI/deck language broadens it into compliance/capital-allocation confidence.

Fix: validate nonnegative/finite allocations, total uses against net proceeds, debt repayment against confirmed eligible principal, and actual or explicitly assumed facility terms/tax/timing. An isolated GCP test must not become a whole-offer compliance conclusion. Preserve excess/unallocated amounts and block affected savings/EPS results.

### A10 — P2: OCR truncates PDF bytes and reruns costly ingestion on unrelated UI interactions

References: `models/pre_ipo_ingest.py:130–131`; `pages/27_pre_ipo_drhp.py:284–288`.

The OCR path slices files to the first **12,000,000 bytes** instead of rejecting/chunking oversized PDFs structurally. A truncated PDF can lose its cross-reference/trailer and become invalid. The page invokes ingestion whenever an upload exists on every Streamlit rerun, including persona changes; there is no explicit accepted source-hash/process-result cache in this path. With working OCR this can cause repeated transmissions, latency and cost.

Fix: validate file limits before upload or split pages into valid PDF chunks. Process once per explicit source/configuration revision and persist the result privately. Persona/filter/theme changes should not rerun extraction. Test oversized files and provider call counts across ordinary reruns.

## In-progress equity increment: additional findings

These methods/classes were added after the initial snapshot during review. The prior committed function bodies relevant to A01–A10 remained unchanged at the delta capture. B findings are early feedback on unfinished code, not claims that Antigravity has declared that increment complete.

### B01 — P1: investor answers declare unsupported claims as answered with evidence

References in delta snapshot: `models/pre_ipo_engine.py:1154–1167`, `:1218–1229`, `:1252–1257`.

Running the new generator on an unreadable unknown issuer yields Q02 **ANSWERED_WITH_EVIDENCE** and “competitive moat ... evidenced by superior operating margins,” despite no usable statements. Q04 is also answered while its score is not computable; absent forensic evidence is rendered as elevated risk in its detail. Q05 says **“ROIC of 0.0% exceeds estimated WACC of 0.0%.”** Numerous generic source titles are assigned rather than resolved document/run evidence.

Fix: determine answer status from dependencies and source review. Do not manufacture competitive position, market leadership, capacity adequacy or risk direction. Missing score is unknown, not low/elevated risk. Compare the actual computed values before choosing wording. Add failed-intake and contradictory-metric answer tests before binding this feature to UI/export.

### B02 — P1: reverse DCF returns a boundary value when no solution exists in its search interval

References in delta snapshot: `models/pre_ipo_engine.py:993–1023`.

The function searches −30% to 80%, initializes the answer to 80%, never verifies bracketing/residual, and silently changes WACC if it is below terminal growth. With Afcons' FCF and an illustrative requested EV of **10^15**, it returns **80% required CAGR**, but the PV at that rate is only approximately **102,759**. The returned growth does not justify the requested value. A low out-of-range root can similarly stick near the lower boundary.

Fix: validate WACC/growth/horizon, check bracket feasibility, return unsolved/out-of-range status, optionally expand a documented interval and verify PV residual. Do not silently change user economic assumptions. Separately reconcile FCFF versus equity/after-interest FCF before comparing cash flows with enterprise value, and avoid unsupported “sector median/achievable” labels.

### B03 — P1: ROIC/WACC labels measured value creation using invented proxies

References in delta snapshot: `models/pre_ipo_engine.py:905–930`.

EBIT is approximated as `max(0, EBITDA − 0.6 × capex)`, not actual depreciation; negative operating profit is clipped. Missing equity market value becomes **2.5 × net worth**, and zero/negative invested capital is forced to 1. Debt weights use net debt without an explicit consistent capital convention. On the unknown zero dossier it returns **WACC 0%, ROIC 0%, VALUE_NEUTRAL**, although its own computed cost of equity is 12.88% and no valid weights exist.

Fix: distinguish a user-approved illustrative model from measured ROIC/WACC. Require actual EBIT/compatible tax, justified invested capital and a documented capital-weight basis; preserve losses. Missing inputs block a value-creation verdict. Test weights sum to one and sensitivity to legitimate accounting inputs, not arbitrary capex proxies.

### B04 — P1: CMIE mapping coverage is mislabeled institutional audit quality

References in delta snapshot: `models/pre_ipo_engine.py:1066–1078`; `models/pre_ipo_schema.py:434–441`.

Coverage counts EXACT_MATCH and RECONCILED entries, then calls ≥85% **INSTITUTIONAL_GRADE_AUDITED**. A single manually marked test mapping, with no actual source/schema verification, yields that label. Field-definition compatibility and disclosure completeness are not source accuracy, audit assurance or decision readiness.

Fix: separate mapping, availability, review and reconciliation states; scope the denominator to the actual reference schema/vintage; retain not-applicable/unknown fields; remove audit-quality verdicts derived from coverage. A claimed CMIE code must be checked against the actual local dictionary. Add tests where complete mappings contain disputed/unreviewed values.

## Product coverage versus the incremental PRD

The committed build improves persona rendering, missing-data display, even-count medians, a before/after EPS bridge, initial invalid-upload handling and internal-versus-external rating labels. These are useful foundations, but are not proof of accepted source data or trustworthy conclusions.

At the baseline capture there was no integrated ten-question feature, full attribute explorer/CMIE inventory, validated original-tools adapter matrix, source-review/correction workflow, accepted immutable analysis snapshot, or persistent recommendation/decision history. The active increment has begun background/equity/crosswalk structures, so those requirements should be tracked as **in progress**, not permanently absent. I did not observe or verify completed end-to-end UI integration for those additions during this review.

Authentication/owner separation, live OCR, both-theme rendering and actual downloaded export fidelity remain **not verified here**, not assumed broken. The existing global authenticated shell is not itself evidence of per-private-document access control. Do not interpret this report as a penetration-test result.

## Recommended remediation order

1. Disable fabricated/unvalidated accepted results: fix A01/A03 and the B01 evidence gate before adding stronger recommendations.
2. Restore OCR provider viability and correct processing/caching limits: A02/A10.
3. Share actual scenario results between screen and exports; remove canned verdicts and false financial statements: A04/A07/A08.
4. Correct lock-in, forensic and offer-ledger contracts: A05/A06/A09.
5. Validate the new valuation solvers and data coverage semantics: B02–B04.
6. Rerun targeted negative/empty/inconsistent cases, then complete the PRD's authenticated four-profile/theme/navigation/persistence/export acceptance.

No numerical readiness score is assigned. Passing 27 current tests establishes those tested contracts; it does not resolve the additional reproduced failures. No fixes, commits, merges, pushes or deployments were performed in this review.

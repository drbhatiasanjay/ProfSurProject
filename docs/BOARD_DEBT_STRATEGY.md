# Debt strategy board deck

Local experimental implementation on `codex/board-deck-improvements`, based on
`9607e0c` (light/dark stabilization). No change to the primary checkout, themes,
navigation registry, manuscript, or remote deployment.

## Narrative and preserved functionality

The format selector lists **Full analytical deck (13 topics)** first and
**Debt strategy board deck** second. The full analytical deck is the initial
default for this workflow revision; subsequent explicit choices are remembered.
The debt strategy deck follows this narrative:

1. Core facts
2. Funding requirement and sources/uses
3. Life-stage diagnosis
4. Existing debt obligations and missing treasury evidence
5. Debt-service capacity, with explicit analytical limits
6. Same-year peer context
7. Financing alternatives
8. Proposed funding, combined downside and reverse coverage stress
9. Proposed debt strategy
10. Board decision and monitoring

The full 13-topic analytical deck remains accessible via the format selector.
Any of those topics can also be appended to the narrative. Topic 12 now presents
policy/covenant evidence requirements rather than an unsupported legal compliance
verdict. The original analytical topic numbers and builders remain available.

## Facts-first workflow and optional form

1. Select the company and deck format. Full Analytical retains its existing
   topic-selection workflow.
2. Debt Strategy Step 1 automatically presents company facts, life-stage
   analysis, debt obligations, serviceability evidence, peers and alternatives.
   No form is required to view or export these facts.
3. Step 2 presents a bordered **Optional scenario form** card. Enable the
   scenario checkbox only when a funding proposal or stress test is needed.
4. Choose **Assess a funding proposal** or **Stress existing debt only**.
   Funding purpose, uses, internal funds, borrowing and rate are grouped
   separately from downside assumptions. Stress-only needs four numerical
   assumptions and no funding amounts. Required fields have an asterisk.
5. Field help explains context and use; visible instructions explain the
   calculations triggered by **Apply scenario and calculate**. Placeholder
   examples are not prefilled company facts.
6. Step 3 presents applied assumptions, results and export controls. Draft edits
   do not change results or an existing download until submitted. Incomplete
   forms identify missing fields without silently substituting zero.
7. Disabling the scenario restores historical review and invalidates the old
   scenario download. Appendix selection is independent of the form.

Without a submitted scenario, funding plans are **Not supplied**, only observed
coverage appears, and no default policy floor, floating share, rate shock or
passing proposal is invented. Stress-only contains baseline and downside rows
and leaves future funding plans unavailable. Funding tests retain baseline,
proposed-funding and combined-downside rows.

Old flat saved inputs are a draft, not an automatically applied proposal. Newly
submitted scenarios use versioned enabled/assumptions records and restore after
reload and authentication. Form and heading styles are scoped to the new
component; both global theme stylesheets remain unchanged.

## Evidence and analytical contracts

- The page queries the frozen thesis vintage explicitly for company financials.
  The generic filtered panel lacks PBIT, interest and cash-flow detail, so it is
  used for peer context, not as a substitute for the detailed company query.
- Company choices are also restricted to actual thesis-vintage membership and
  use company codes as selection values. This excludes same-name rollforward
  entities (Tata Motors 729991) while retaining the verified thesis code 248093.
  Previously saved company names migrate to the code-based selection.
- Database leverage is percentage-valued. The narrative displays it directly.
  The legacy board builders receive a copied, explicitly marked fractional
  representation; conversion is idempotent and never magnitude-based.
- Profitability and tangibility remain fractions. Interest coverage is PBIT /
  positive interest and is displayed in multiples. A missing or nonpositive
  denominator is unavailable, not zero coverage or infinite capacity.
- Tax shield is an amount, not a percentage. No currency or monetary scale is
  inferred. The narrative labels monetary values as source dataset units and
  requires confirmation of currency, units and financial statement basis.
- Comparators exclude the focal company, other stages and stale reporting years.
  The cohort is drawn from the existing stage/size peer selector, not presented
  as an industry-matched credit assessment.
- Peer percentiles are descriptive. They do not establish optimal leverage,
  executable debt capacity, contractual limits or lender appetite.
- Funding uses, internal funding, new debt, annual debt rate, floating share,
  rate shock, earnings decline and coverage floor are optional user assumptions,
  used after an explicitly submitted scenario. Missing plans stay unavailable.
- Proposed annual interest = observed interest + new debt * annual rate.
- Downside annual interest additionally includes (existing debt * floating share
  + proposed new debt) * shock bps / 10000. New debt is fully rate-exposed.
- Downside PBIT = historical PBIT * (1 - selected earnings decline).
- Reverse coverage stress is the PBIT decline to the selected coverage floor
  under proposed funding, holding rates constant. Zero means the floor is already
  reached or breached; unavailable inputs remain unavailable.
- The illustrations exclude principal repayment, fees, taxes, earnings growth
  and cash-flow timing. Missing maturity schedules, covenants, unrestricted cash,
  facilities and forecasts remain visible data gaps. No DSCR or borrowing limit
  is invented.
- The selected coverage floor is an analytical policy assumption. It is not
  represented as a universal IBC or SEBI threshold.

## Screen-to-export mapping

| Visible behavior | Source | Export evidence |
| --- | --- | --- |
| Format selector; original 13 topics | `pages/17_board_export.py` | Existing `build()` API retained |
| Funding form, saved company settings, appendix selection | `components/debt_board_view.py` | Identical assumptions in prepared section payload |
| Ten ordered sections and calculations | `models/debt_board.py` | `build_sections()` consumes the displayed sections |
| Core facts and missing values | `models/debt_board.py`; `models/board_export.py` | PPTX table cells and KPI trace unit tests |
| Narrative tables and scenario chart | `components/debt_board_view.py` | Shared sections; light export canvas with unchanged values |
| Expanded/collapsed section heading contrast | Scoped `.st-key-debt_board_sections` styles in `components/debt_board_view.py` | Browser checks; no global theme stylesheet edits |
| Legacy radar/distribution selection | `pages/17_board_export.py` | Selected figure passed via `topic_data`, avoiding rebuild |
| Saved download across reruns | `components/debt_board_view.py`; page export state | Payload invalidated by input/data/theme changes |
| Long tables, complete findings, slide count | `models/pptx_generator.py` | Row/column continuation slides; exact page counts |
| Chart/table failures | `models/pptx_generator.py` | Visible warning slide and returned UI warnings |
| Provenance and commentary | Prepared section payload | Speaker notes preserve full section evidence |

An interactive preview is not a pixel-identical PowerPoint layout. Exported
charts use a white canvas for slide readability; facts, selected charts and
assumptions use the same prepared payload. Optional additional strategic
commentary is explicitly labelled separately from the analytical export.

## Research basis

The sequence is a product-design synthesis, not a prescribed reporting standard.

- AFP, [12 Tips for Treasurers Making Capital Structure Decisions](https://www.financialprofessionals.org/training-resources/resources/articles/Details/12-tips-for-treasurers-making-capital-structure-decisions):
  capital needs, minimum liquidity, stress testing, financial flexibility and
  board agreement precede execution; peer practice is one input.
- FRC, [Corporate Governance Code Guidance](https://www.frc.org.uk/library/standards-codes-policy/corporate-governance/corporate-governance-code-guidance/):
  board information should support the decision requested and enable challenge
  of assumptions and principal risks. Used as governance design guidance,
  not as a claim of Indian regulatory applicability.
- IFRS Foundation, [Management Commentary key terms](https://www.ifrs.org/supporting-implementation/supporting-materials-by-ifrs-standards/management-commentary/key-terms/):
  connect financial performance and position with future cash-generation factors.

## Verification

Run `py -3.12 -m pytest tests/test_debt_board.py tests/test_debt_board_view.py tests/test_board_export.py -q --tb=line`
and `py -3.12 scripts/project_ops.py test --fast`.

`tests/test_debt_board.py` checks actual Tata Motors FY2024 values, combined
stress arithmetic, unavailable/negative inputs, duplicate years, stale peers,
idempotent units, all table cells and findings in a real PPTX, page counts,
speaker notes, supplied-preview reuse and visible renderer failures.

Verified on 5 November 2026: 119 focused tests passed; 6 standard fast checks
passed; `git diff --check` passed. The in-process Streamlit component checks
exercise saved assumptions, appendix selection, light/dark reruns, retained
downloads and export invalidation after an input change. They are not
authenticated browser evidence.

Actual local exports in `scratch/debt_board_evidence/`: Tata Motors narrative
24 slides, full analytical deck 55 slides, both with zero renderer warnings.
The narrative uses illustrative inputs (funding uses 2,000, internal funds 500,
new debt 1,500, rate 8%, floating share 50%, shock +200 bps, PBIT decline 20%,
coverage floor 3x). These inputs are not a company financing recommendation.
The embedded scenario chart was extracted from the PPTX and visually inspected.
The measured FY2024 baseline is 5.004x interest coverage and 20.293% leverage.

The existing board test file lacked its `sample_company_code` fixture; a local
fixture was supplied. Its AST check now uses `Constant.value` for compatibility
with newer Python versions. The required validation runtime remains Python 3.12.

Browser acceptance requires the canonical root app in an isolated local test
server, authenticated profiles `profsurkumar`, `skumar`, `drbhatia`, `sbhatia`,
light/dark checks, input persistence, both deck formats and an actual download.
Credential/server setup was explicitly approved on 5 November 2026 after the
initial automatic review rejection. The isolated root app runs at
`http://127.0.0.1:8503/` because port 8502 already hosts a local file server.
The existing app on 8501 and the file server on 8502 are unchanged. Four profiles
passed native bcrypt verification against a separate validation database.
The copied secrets, validation database and generated browser artifacts are
Git-ignored. Functional browser acceptance passed for `profsurkumar`, `skumar`
and `drbhatia`: both themes, assumptions, three observed scenario bars, optional
appendix, the legacy analytical preview, actual download, rerun persistence and
reload/reauth restoration. Their separate saved debt inputs 1500/1600/1700 were
confirmed in the isolated database. `sbhatia` retains the existing viewer role
and was correctly denied Board Deck controls in both themes.

The actual browser-downloaded presentation has 27 slides including an Executive
Summary appendix. Its facts include 5.00x interest coverage and 20.29% leverage;
all slide footers were verified. Rendered coverage bars for the 1500-debt
illustration were independently checked as 5.0040496275, 4.7154543510 and
3.4844802252. Evidence: `scratch/debt_board_evidence/browser/summary.json` and
`Tata_Motors_Browser_Download.pptx` in the same folder.

Visual review caught a low-contrast expanded heading in light mode. The fix is
scoped to the new component's keyed container and does not edit either global
theme stylesheet. All 119 focused tests passed again after this fix. The final
browser contrast recapture passed for all three permitted profiles in both
themes, covering expanded and collapsed section headings. Actual measured
contrast: light #F1F5F9 / #0F172A = 16.296:1; dark #161F30 / #F1F5F9 = 15.061:1.
All six `*_core_fixed.png` files were verified to exist; the fixed light image
was visually inspected. This is targeted heading/readability evidence, not a
claim of a complete application accessibility audit.

The isolated app remains available on port 8503 for local review, using its
separate test database. No commit, merge, push or deployment was performed.
Automatic review also rejected switching optional commentary to Anthropic.
The additional commentary button instead reuses deterministic analysis without
calling a local or external model. Existing opt-in AI narratives remain available.

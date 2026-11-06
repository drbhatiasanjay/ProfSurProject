# Independent covenant calculation reconciliation

Completed 1 October 2026 for the opt-in chatbot pilot. The accompanying workbook is `scratch/covenant_pilot/validation/Covenant_Independent_Check.xlsx`.

## Result and scope

All 18 captured scenarios passed 2,610 comparisons: 12 quarters of earnings, CFADS, debt and lease interest/principal, lease cash, closing cash, DSCR, earnings/interest, TOL/TNW, breach counts and one headroom result per scenario. The standard project fast check also passed all 6 tests.

The workbook recalculates with the bundled spreadsheet engine. Native Microsoft Excel recalculation and independent professional review have not been performed. This is calculation agreement, not validation of borrower inputs, contractual definitions, credit decisions or System GMM.

## Independent method

The Python exporter executes the production engine and captures its inputs and expected results. The JavaScript workbook builder imports only that JSON and the spreadsheet library. It does not import production financial calculation functions. It independently builds visible spreadsheet formulas with loan/lease opening balances, scheduled principal, closing balances and opening-balance interest. New loans amortize equally over 12 quarters and are fully spent at inception. Lease cash always reduces liquidity and enters coverage only when selected.

Headroom is calculated analytically from the linear constraints. For each quarter the workbook measures capacity under DSCR, interest coverage, TOL/TNW and minimum cash. It divides constraint slack by that quarter's incremental-debt exposure and takes the minimum across all quarters and the search cap. The production engine instead uses bisection. Both return zero if the proposed scenario breaches a constraint.

The shared fixtures mean this check can detect calculation discrepancies but cannot independently establish source accuracy or appropriateness of the demo's finance definitions. Baseline and stress scenarios use the declared EBITDA/EBITDAR bases; neither is represented as contractual EBIT-based ICR.

## Scenarios and tolerance

Each company has nine scenarios: baseline; +150 bps, -20% earnings and 10,500 crore new debt; -10% follow-up; stressed debt-only coverage; -100 bps rate cut; -100% earnings boundary; 1 crore search cap; relaxed TOL/TNW ceiling of 4; and that relaxed ceiling with debt-only coverage.

Quarterly numeric tolerance is 0.0000001 crore or ratio units. Breach counts agree exactly. Headroom tolerance is 0.01 crore, accounting for two-decimal truncation, binary floating-point arithmetic and the engine's small feasibility slack. The relaxed-TOL IndiGo debt-only case differs by 0.01 crore: engine 23,190.20 versus formula 23,190.19. This is recorded rather than hidden. All other captured headroom comparisons agree to two decimals.

For each company, a separate recalculation check reduces quarter 12 earnings by 100 crore and verifies quarter 12 closing cash falls by 100 crore. Original inputs are restored before export. No unexpected formula errors were found. All three worksheet previews were visually inspected.

Tata Steel's illustrative baseline additional headroom is 1,491.96 crore. IndiGo's default baseline has zero additional headroom because its assumed opening TOL/TNW exceeds the illustrative ceiling of 3. Relaxing that assumed ceiling to 4 produces 356.60 crore with leases included. These outputs describe the fixtures, not lending recommendations.

## Reproduce and review

1. Run `py -3.12 scripts/export_covenant_validation_cases.py` from the repository root.
2. Run `scripts/build_covenant_validation.mjs` with the bundled Node runtime and `@oai/artifact-tool` dependencies discovered by Codex's workspace dependency loader. The local `scripts/node_modules` junction points to those read-only dependencies.
3. Review the workbook and `scratch/covenant_pilot/validation/reconciliation.json`. The JSON records each comparison, tolerances, recalculation checks, simulation IDs and SHA-256 hashes of the captured inputs and workbook.

The first worksheet contains frozen reconciliation captures. Editing blue inputs on a company worksheet recalculates that company's formulas but does not refresh those captures or rerun the production engine. Rerun both scripts to refresh comparisons.

Next release gates are independently reviewed borrower schedules and actual contractual covenant definitions, professional review of the cash mechanics, and native Excel recalculation if Excel is the review environment. The pilot remains `NOT_VALIDATED`; the System GMM candidate remains separate pending its independent Stata benchmark.

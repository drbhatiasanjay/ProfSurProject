# Borrower validation through AI Assistant

## Current workflow

In the feature-enabled AI Assistant, enter **validate borrower**. The chat opens a borrower evidence upload card. Download the blank packet template, populate it with source-backed borrower records, upload that packet and its supporting documents, then select **Check borrower evidence**. Results appear as a persisted chat turn with a detailed issue table and downloadable JSON report. Enter **cancel borrower validation** to close the upload card.

This version checks a structured JSON packet. Automatic extraction from raw agreements, PDFs or spreadsheets is not implemented. Raw supporting files provide identity and traceability; the checker does not read their content to establish whether human transcription is accurate. A finance reviewer must confirm the supplied values and clauses against those files. This limitation is shown in the upload card.

Uploads stay in the local project under `scratch/covenant_pilot/borrower_uploads`, separated by conversation scope and upload-run ID. No cloud provider receives them through this intake path. The chat stores the report and validation state. The validator never enables contractual calculations or changes the public demonstration examples.

## Required evidence

Provide financial statements, executed facility terms and relevant amendments, debt repayment schedules, an approved cash-flow forecast and a tangible-net-worth bridge. If lease liabilities are nonzero, also provide lease schedules. An explicit zero lease balance is acceptable; an unknown value is not treated as zero.

Each document needs a unique ID, relative filename, SHA-256, borrower entity, financial perimeter and reference as-of date. That reference date identifies the packet snapshot; it need not be the original agreement execution date. Contract effective dates belong in the covenant records. Source references also need page, clause or cell locators. Preserve source units in the underlying evidence and explicitly normalize packet amounts to INR crore.

Use the uploaded document's filename without folders in the packet. The report lists uploaded filenames and computed hashes; local hashes can also be obtained with PowerShell `Get-FileHash -Algorithm SHA256`. Uppercase and lowercase hashes are accepted.

Opening debt excluding leases and lease balances must reconcile to statement controls within 0.01 crore. For each facility, record opening balance and every future period's drawdowns, principal, interest and other cash payments. Supply finite values, including explicit zeros, and prevent repayments from exceeding available balances. Forecast rows require earnings basis, cash taxes, maintenance capex and working-capital use for every specified period.

Copy the actual covenant text and its numerator, denominator, threshold, comparison direction, testing basis, lease treatment, cash-sweep terms, effective date and facility mapping. Do not replace rolling annual definitions with quarterly ratios or infer a waiver from missing terms. The checker collects these definitions for review; it does not decide that they match the pilot engine.

The template is at `scratch/covenant_pilot/borrower_validation/borrower_packet_template.json`. Its nulls and empty schedules are intentionally incomplete. The `record_templates` section provides shapes for schedule and forecast rows; copy completed records into the actual collections.

## Status and review gates

`NEEDS_EVIDENCE` means required sources, values, locators or reconciliation controls failed. `READY_FOR_PROFESSIONAL_REVIEW` means the structural checks passed. Both retain `NOT_VALIDATED`, and `contractual_calculation_enabled` remains false. File hashes verify identity, not authenticity, completeness, accounting judgment or transcription accuracy.

Next, a finance reviewer must reconcile the packet to the originals and approve definition mappings. Any contractual mechanics unsupported by the pilot, such as daily interest, rolling tests, covenant cures or cash-sweep waterfalls, require separate implementation and validation before a contractual run. No human approval is inferred from a user-entered metadata label.

## Public-anchor recheck on 1 October 2026

The existing frozen FY2025 figures were rechecked against the original issuer releases. Tata Steel consolidated annual EBITDA is 25,802 crore and cash/cash equivalents are 12,222 crore. Its disclosed net debt of 82,579 crore is not a verified gross loan schedule. [Tata Steel FY2025 release](https://www.tatasteel.com/media/newsroom/press-releases/india/2025/tata-steel-reports-consolidated-ebitda-of-rs-25-802-crores-for-fy2025/)

IndiGo reports annual EBITDAR of 212,520 million INR (21,252 crore), free cash of 331,531 million (33,153.1 crore), capitalized operating lease liabilities of 479,801 million (47,980.1 crore) and total debt including those leases of 668,098 million (66,809.8 crore). Debt excluding the reported lease liability is therefore 18,829.7 crore. Restricted cash is excluded from the fixture's opening free-cash amount. [IndiGo FY2025 release](https://www.goindigo.in/press-releases/indigo-reported-its-fourth-quarter-and-fiscal-year-2025-results.html)

Those public aggregates agree with the fixtures, but the demo's forecast, facility amortization, interest rates, tangible net worth and covenant thresholds remain assumptions. The FY2025 examples are not represented as latest financials. No borrower agreements were found in the scoped project evidence search; a first actual borrower and its document location remain to be supplied.

## Reproduce offline

Run `py -3.12 scripts/validate_borrower_packet.py <packet.json> --evidence-dir <local evidence folder> --output <report.json>`. Exit 2 means evidence issues; exit 0 means ready for professional review, not financial validation. The output contains no credentials.

Source-to-screen mapping: `models/covenant_chat.py` opens or cancels intake from the user query; `components/covenant_pilot_chat.py` renders uploads and persisted reports within the existing assistant; `models/borrower_evidence.py` owns the checks. Browser evidence is recorded separately under `scratch/covenant_pilot/borrower_browser`.

## Verification completed 2 October 2026

All 18 borrower-specific tests passed; the combined focused engine/estimator/intake run passed 47 tests before one additional uppercase-hash test was added and verified. The standard fast check passed 6 tests. Browser checks passed for drbhatia, profsurkumar and skumar: authenticated intake, template download, missing packet error, incomplete packet with 46 issues, exact report restoration after reauthentication and cancellation. sbhatia could not be checked because the profile is absent from configured secrets.

The final drbhatia browser check also uploaded six clearly synthetic evidence files and a complete synthetic packet. It verified all six file hashes and `READY_FOR_PROFESSIONAL_REVIEW` while retaining `NOT_VALIDATED` and disabled contractual calculation. This is workflow evidence, not validation of a real borrower. Account/conversation scoping was tested at the routing unit level; an additional cross-account browser isolation test was not performed. Authenticated browser checks used the existing isolated verification database.

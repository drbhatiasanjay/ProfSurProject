# Pre-IPO intake and evidence-module integration assessment

Assessed 8 November 2026 on `codex/pre-ipo-evidence-review`, source baseline `54b4e31`. This is an assessment, not an ingestion repair or production release. The intake and runtime-configuration files have no diff against local master `d453dd8`; master also contains a separate covenant-headroom increment that was not changed here.

## A. Is the existing ingestion working?

**Not as a dependable end-to-end financial extraction pipeline.** Reading a PDF and recognizing its text currently works; obtaining usable financial fields from the searchable-PDF route does not.

| Check actually performed | Observed outcome |
|---|---|
| Valid searchable PDF containing seven known financial values | PDF reader recovered the text and all expected numbers. Intake returned zero for all seven financial fields. |
| Known revenue 1,234 Cr; EBITDA 234 Cr; CFO 123 Cr | Returned revenue 0, EBITDA 0, CFO 0. These are placeholders, not the test document's figures. |
| Failure/eligibility flags on that searchable financial PDF | No intake limitation was recorded. The text-intake audit was marked FOUND_AND_RECONCILED even though numerical extraction had not occurred. |
| Authenticated first-radio-workspace upload and Analyze button | Reproduced a terminal TypeError when eager deck generation formatted `economic_profit_cr=None`. This happened without clicking Export. |
| Configured cloud model metadata check | Key configured; `gemini-3.1-flash-lite` model metadata available. This does not prove generation entitlement. |
| Actual image-only, one-page synthetic PDF through `ingest_document` | Generation failed with ClientError HTTP 402. GAP-OCR-01 and intake gaps were raised. No scanned extraction success is claimed. |

Both documents were explicitly synthetic. No real issuer document was sent to a provider. One bounded synthetic scanned-PDF generation request was made; credential values were not printed. This is a reproducible functional check, not a statistical accuracy benchmark on real DRHPs.

### Root causes and severity

1. **P0: Searchable financial text is not converted into financial fields.** `models/pre_ipo_ingest.py:693–830` detects financial keywords/numbers, then constructs a provisional dossier with zero-valued history and obligations. The real financial values are not parsed in this branch. Native text intake is limited to the first sixty pages, so it is not a complete-document coverage guarantee either.
2. **P0: Missing placeholders can be presented as observed values.** The native financial branch has no GAP-INTAKE limitation. The evidence importer therefore treats its zero-valued fields as observed, unreviewed filing candidates. The human acceptance gate prevents source-qualified analysis in the new module, but the availability classification is wrong. Missing/unparsed values must remain distinct from genuinely reported zero.
3. **P1: Provisional upload crashes the terminal.** `pages/27_pre_ipo_drhp.py:400` eagerly invokes the legacy deck generator. `utils/pre_ipo_deck_generator.py:489` formats unavailable economic profit numerically. Incomplete intake should instead block analytical rendering/export and retain diagnostics.
4. **External blocker: Scanned generation returns HTTP 402.** Model discovery succeeds, but the actual extraction request does not. Resolve the provider response and rerun a known-value generation test before claiming OCR works. The precise account-side cause was not established by this assessment.

## B. Are newly ingested values automatically displayed in the new module?

**No. The current connection is explicit/manual, not the default ingestion path.**

Current path:

1. Existing Pre-IPO terminal → select **+ Ingest New DRHP / RHP PDF Document...**.
2. Upload a PDF, specify the company, click **Analyze or retry this uploaded filing**. The result is held in Streamlit session state.
3. Expand **Retain this original and intake candidates for private fact review**.
4. Supply exact source version, public availability date and retention/use permission; click **Save original and review candidates**.
5. Switch to **Facts & evidence review** and select that saved private company using the same account.

The authenticated browser test found **zero new review entries after ingestion alone**. After the explicit save action, the saved company and its **117 schema/payload attributes** appeared in the new module. Those rows include metadata and defaults; they are not 117 successfully extracted financial facts. The saved revenue was still 0 and UNREVIEWED/OBSERVED_VALUE, demonstrating that transfer works but does not repair the upstream output.

The transfer flattens fields represented in `PreIPODealDossier`; it does not capture every attribute, narrative or table in a DRHP, nor establish complete CMIE equivalence. The new module's **Extract selected native pages** utility retrieves page text for inspection. It is not a second structured financial extraction engine.

## Required next implementation

1. Use one validated extraction contract for searchable and scanned documents. Preserve raw observations, exact source context and genuine reported zeros; use null/explicit missing states for absent or failed fields.
2. Establish known-value positive extraction tests and block ratios/decks when required financial fields are unavailable. Existing passing guard/unit tests are not evidence of successful numerical ingestion.
3. Collect the required filing metadata once, before intake; persist the original document, extraction run and unreviewed candidates automatically after intake. Keep failed runs and gaps visible without promoting placeholders.
4. Have Facts & evidence review read those persisted records by default and open the ingested company. Human review should remain necessary for acceptance, not for making extracted candidates visible.
5. Resolve the current provider HTTP 402 and verify against real retained document samples before release. Reference/sector completeness and extraction accuracy need separate acceptance evidence.

Target workflow: **upload once → ingest/extract → persist candidates and gaps → automatically display in Facts & evidence review → accept/reconcile → enable eligible analysis**. No second entry of the company's financial values should be required.

## Evidence and limits

The adjacent JSON assessment records expected/actual values, source hashes and sanitized provider/UI outcomes. Ignored raw artifacts are in `scratch/ingestion_assessment_20261108/`: `native_and_handoff.json`, `scanned.json`, `ui.json`, synthetic PDFs and `native-handoff-ui.png`.

The selected existing regression suite passed 56 tests, including remediation, schema and ledger tests. That result coexists with the positive-path failure above: those tests did not assert correct extraction of these known financial values. Previous review-module browser acceptance and first-use inspection remain separate from successful intake-to-review extraction.

No application source, master branch or deployment was changed during this assessment. Only synthetic validation records were written to isolated assessment/preview databases.

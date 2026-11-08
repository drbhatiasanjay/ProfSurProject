# Pre-IPO facts and evidence review

Implementation branch: `codex/pre-ipo-evidence-review`. This extends the existing Pre-IPO page; it does not replace its terminal or decision workbench. The detailed contract is [the evidence review PRD](plans/PRE_IPO_EXTRACTED_FACTS_EVIDENCE_REVIEW_PRD_2026-11-07.md).

## User workflow

1. Authenticate at the root application and use the existing **Pre-IPO DRHP Intelligence** sidebar entry. Select **Facts & evidence review** in the workspace selector.
2. Choose an existing company under **Inspect existing data**. Its **Attribute inventory** is available immediately, including for viewers, without creating a company or initializing a private inventory. Registry numbers remain labelled unverified legacy examples.
3. Open **Attribute inventory** to inspect attributes, values, periods, origin, presence, review state and revision. Filter by domain or state. The payload includes metadata/narrative, so row count is not a completeness denominator.
4. To save changes, choose **Start private review of this data** in **Sources & review**. Then retain an authorized original PDF with its exact filing type/version and availability date. The optional new-company form is also in this tab, after the existing-data workflow. A new company starts with missing financial cells, not zeros. Inspect the rendered page and text alternative. Optional native extraction explicitly processes a batch of 1–20 pages; scanned/unreadable/truncated pages remain visible gaps. Download the original when checking printed page labels, unit headers or footnotes.
5. Select a fact. Its existing value is already populated. Review the interpretation, entity/period, duration, basis, framework, currency/unit and definition; supply the exact page/table/footnote and quotation, reason and review decision. You review selected facts rather than reentering every company value. Raw observations and prior revisions remain immutable. N/A and non-disclosure require a documented scope.
6. Inspect **Conflicts & CMIE** and **Missing data & actions**. The twenty-four baseline comparisons preserve both candidates until a source-backed selection. Authorized reference uploads support table-qualified candidate mappings; missing definitions remain DEFINITION_REQUIRED. Record a diligence owner and due date without pretending an assumption closes a filing gap.
7. Open **Analysis & snapshots**. Accepted compatible facts automatically populate supported descriptive results; unsupported calculations explain what is missing. Commentary separates observation, interpretation and next action, with practitioner methodology references separately labelled. Freeze a snapshot and download its JSON/PPTX. Both use the same frozen facts, questions, gaps and source manifest.
8. To use existing optional methods, prepare a saved evidence snapshot, select **Decision-depth workbench**, and apply the prepared evidence case. Compatible reviewed CFO/capex populate the cash-flow bridge. Missing cash interest, realized tax benefit and classification assumptions remain required; no defaults are invented. Applying creates a new unsaved context and preserves saved cases.

The original terminal's custom-upload workflow also offers **Save original and review candidates** after intake. This retains its PDF and unreviewed extraction candidates in a private company. Failed intake placeholders become EXTRACTION_FAILED with null interpreted values. Reimporting an identical intake is idempotent; a changed intake appends revisions and requires review. Source locations and model confidence are not automatically promoted to accepted evidence.

The original intake now starts only with **Analyze or retry this uploaded filing**. It may use the configured cloud provider, as explained on screen. Its session cache includes owner, source hash, model and ingestion-code fingerprint. Ordinary reruns do not submit another cloud job; a deliberate retry is available after provider/configuration fixes.

## Source-to-screen map

| Component | Implementation | Evidence contract |
|---|---|---|
| Existing route and workspace selector | `pages/27_pre_ipo_drhp.py` | Original sidebar and terminal/workbench remain registered |
| Company brief, inventory, source preview and review forms | `components/pre_ipo_evidence_review.py` | Scoped styling, private-owner state, role-disabled writes, page plus text alternative |
| Private companies, original PDF bytes, page runs and immutable fact events | `models/pre_ipo_evidence.py` | Application DB, owner/company keys, content hash, single-review qualification, optimistic revision checks |
| Applicable profile, gaps, questions and workbench transfer | `models/pre_ipo_evidence_analysis.py` | Entity/period/context matching, typed values, no causal/ML claims, public-as-of source eligibility |
| Frozen JSON/PPTX | `utils/pre_ipo_evidence_export.py` | Snapshot-only reads; no current-data recomputation |
| Legacy coverage/exports | `models/pre_ipo_engine.py`, `utils/pre_ipo_deck_generator.py` | Mapping counts cannot create an audit-grade verdict; original deck carries unverified qualification |
| Generic workbench inventory | `models/pre_ipo_decision/data_quality.py` | Caller-supplied review booleans do not establish source-bound acceptance |

## Storage, access and migration

All new tables are additive and created lazily through the configured application connection: `pre_ipo_company_profiles`, `pre_ipo_sources`, `pre_ipo_extraction_runs`, `pre_ipo_fact_events`, `pre_ipo_reference_versions`, `pre_ipo_evidence_actions`, `pre_ipo_evidence_action_events`, and `pre_ipo_evidence_snapshots`. Existing panel/manuscript data and saved decision tables are unchanged. PDF bytes are stored privately as DB BLOBs, up to 25 MB and 1,500 pages per document. No raw vendor catalogue is shipped with the feature. `pypdfium2` supplies bounded-resolution page images; text/download alternatives remain available on rendering failures.

Follow-ups support append-only OPEN/COMPLETED/CANCELLED dispositions with optimistic revision checks. Closing a follow-up never accepts a fact or closes an evidence gap automatically. Snapshots and both export formats retain the action state at the time of freezing. Optional-model handoff requires an explicit period when several reviewed CFO periods exist and displays its semantic context in the existing form.

Researcher/admin roles may write their own workspace; viewers cannot upload, review, record actions or freeze snapshots. Persona changes guidance only. No implicit sharing or administrative evidence bypass exists. Native SQL uses bound parameters; source URLs are recorded, not fetched; extracted text is rendered inert. Source and form state are scoped to the authenticated owner. Retained-source hashes are revalidated before source-qualified analysis.

The configured deployment must provide durable database storage. The local implementation persists across connections/process restarts against the same DB path. That does not establish Cloud Run replacement/multi-instance durability. Do not deploy this feature as a production durable review system until storage, backup/retention, concurrency and authorized source handling are verified in that environment.

Rollback removes the additive workspace entry or reverts this branch while retaining the new tables. Do not delete sources/events or reset the application database. Existing saved evidence snapshots are immutable; updated facts create a new snapshot. Public-as-of research can recover an older fact revision when a later filing was not yet available; this is not a claim about the information a historical user actually possessed.

## Verification and remaining release gates

Baseline reconciliation was checked against all five registry dossiers: 2,165 payload leaves, sixteen financial rows, eighty crosswalk rows, nineteen numerical differences and five absent-history comparisons. Forty-eight optional financial cells are absent. These findings are internal consistency checks, not original-PDF certification.

Automated contracts cover source integrity/access, duplicate imports, immutable raw values, role denial, optimistic/concurrent reviews, nil/zero/assumptions, numeric bounds, wrong reporting periods, scanned-page gaps, candidate reference mappings, private companies, source cutoffs/older revisions, failed-intake defaults, snapshot/export parity and workbench population. Authenticated browser acceptance must cover all four configured profiles in both themes, actual PDF retention/review, actual downloads and the workbench handoff. Ignored browser artifacts live under `scratch/evidence_review_browser/`; they contain synthetic validation data, not verified issuer facts.

The following PRD release gates remain explicit rather than falsely reported as completed:

- Exact original documents and the adjudicated 200-observation gold set are not backfilled/certified. Legacy examples remain unverified until a reviewer supplies sources.
- This workspace records single-review judgments. Organization sharing, independent maker/checker approval and legal-hold/deletion administration require a separate access/retention policy increment; no independent audit label is available.
- The source inspector binds a PDF page, quotation and manual table/footnote locator. Automated cell-level bounding-box highlights are not implemented.
- Reference imports establish catalogue candidates, not complete licensed accounting definitions or CMIE company-value comparisons. Sector-specific profile expansion requires reviewed definitions and data.
- Native extraction is an explicit bounded synchronous batch. Persistent asynchronous cloud OCR workers, cancellation/billing telemetry and full-document automatic fact extraction are not introduced here; the existing provider intake remains available with explicit retry and candidate import.
- Production object/database durability, hostile-document process isolation, load/SLA benchmarks and actual GCP deployment acceptance remain deployment gates. No new live exchange feed or empirical-model acceptance is implied.

These are limits of the implemented local increment, not a claim that every PRD acceptance scenario has passed. No merge into master, push or deployment is part of this branch implementation.

# Latest Part 1 gate and Part 2 integration review

Reviewed 8 November 2026. This follows the user's instruction to complete Part 1 before Part 2. **Part 1 cannot be accepted yet; Part 2 is not integrated.** No application source was changed by this review.

## Code actually reviewed

Antigravity's latest changes are uncommitted in `C:/Users/hemas/Downloads/ProfSurProject` on master `d453dd8`: modified ingestion/page/deck files plus the new untracked `models/pre_ipo_custom_store.py`. They are distinct from the evidence-review branch `codex/pre-ipo-evidence-review` at `4bd60ba`.

Four relevant files were copied into an ignored, isolated source snapshot and hashed before testing. The checked source still matched the snapshot at test completion. The main page changed during the wider review, so the adjacent JSON identifies the exact tested snapshot rather than assuming all uncommitted edits were static. No unrelated main-checkout edits, existing saved prospectuses, production data or secrets were modified.

## Part 1: completion gate fails

The new native parser has extraction patterns, but substitutes populated company-specific defaults when patterns fail. It also constructs FY23/FY24 histories, financing assumptions and an approval verdict without deriving them from the uploaded document.

An actual searchable one-page synthetic PDF disclosed FY24 values. Its text layer was recovered successfully. Running the latest ingestion implementation produced:

| Field | Disclosed FY24 value, Cr | Returned FY24 value, Cr |
|---|---:|---:|
| Revenue | 1,234 | 12,840.1 |
| EBITDA | 234 | 2,054.4 |
| PAT | 89 | 852.1 |
| CFO | 123 | 1,840.2 |
| Capex | 45 | 750 |
| FCF | 78 | 1,090.2 |
| Net worth | 678 | 6,801.8 |

**Zero of seven matched.** The pipeline additionally emitted FY23/FY25 periods, term loans of 1,450 not present in the input, six FOUND_AND_RECONCILED audit labels, no limitations, and `PRUDENT_LOW_LEVERAGE_APPROVED`.

This is not a statistical error-rate estimate. It demonstrates that unsupported layouts and absent fields receive invented values instead of missing states. Even if a specially formatted sample matches some patterns, missing values and undisclosed years must never fall back to another company's figures.

### Blocking source findings

- `models/pre_ipo_ingest.py`, approximately lines 833–954: company-specific financial defaults; fixed historical periods/figures; fallback debt, governance, rates, valuation and approval language.
- `pages/27_pre_ipo_drhp.py`, approximately lines 390–440: staged progress announces completion and a 0.95 score before calling the extractor. "All audit gates passed" and 95% labels are literal presentation, not derived acceptance results.
- The same page saves the returned dossier without establishing that extraction quality has passed a substantive acceptance gate.

Current scanned/OCR generation was not revalidated in this review. The earlier HTTP 402 finding is historical evidence, not proof of its current status. The independently reproduced native-path defect already prevents Part 1 acceptance.

**Required Part 1 correction:** remove unsupported defaults and fixed approval/valuation/period data; extract facts with unit/period/source context, represent absent or failed fields explicitly, compute quality states from real validation, and pass known-value plus missing-field/adversarial tests. Treat unrecognized layouts as incomplete extraction. Do not hardcode the expected test values or promote a demonstration document into a general extractor.

## Part 2: library persistence works, review integration does not

The new `pre_ipo_custom_store.py` saves a dossier as `data/pre_ipo_custom/<company_slug>.pkl` and can reload it. The original page adds those objects to the original terminal's dropdown. That functionality was reproduced using a temporary store under the isolated scratch directory.

It does not populate the source/fact ledger used by Facts & evidence review:

| Integration check | Observed result |
|---|---|
| Save and reload from new custom library | Works in isolated test |
| Review-ledger companies after that save | Zero; unchanged for both test owners |
| Latest main page offers Facts & evidence workspace | No |
| Latest main page calls evidence `import_dossier` | No |
| Evidence module loads new custom library | No |
| Original PDF retained by custom-store implementation | No; only the dossier is serialized |
| Custom store keyed by authenticated owner | No |
| Delete API requires owner/role | No; deletion succeeded in the isolated test without either argument |

### Actual browser surfaces

Authenticated, read-only browser checks confirmed:

- `http://localhost:8501/`: Existing Pre-IPO terminal and Decision-depth workbench only.
- `http://localhost:8512/`: additionally offers Facts & evidence review.

These are different application checkouts/configured databases. They are not a combined ingestion-to-review build.

### Apparent visibility is not sufficient

The original page mutates global `PRE_IPO_REGISTRY` after reading the shared library. In an isolated same-process simulation, this made the saved object previewable through the registry adapter, but its rows were classified LEGACY_EXAMPLE, had zero source bindings, and still produced no owner-ledger records.

Consequently, a company appearing after visiting the original terminal would not prove correct integration. Cold-start direct navigation, ownership, retained sources and persisted fact records must all be verified. Global registry mutation must not be used to distribute private uploads across users.

## Required Part 2 implementation after Part 1 passes

1. Combine the accepted ingestion changes and evidence-review implementation in one isolated integration branch/app. Preserve the first-use fix from `54b4e31` and existing review/history functionality.
2. Use the owner-scoped source/fact ledger as the canonical destination for ingestion. Do not create another competing shared store. Do not automatically trust or unpickle arbitrary external files.
3. Collect source identity/version, availability and permitted-use metadata once. Automatically persist original bytes, source hash, extraction-run/config identity, observations and missing/conflict states.
4. Display the ingested company and its candidate attributes automatically in Facts & evidence review, including after rerun, reauthentication and restart. Do not require a second save/import or manual initialization for visibility.
5. Keep all candidates UNREVIEWED. Acceptance, calculations and claims must use the established source/review gates; never propagate literal "all gates passed" labels.
6. Preserve revisions and separate filing versions. A company-name slug alone is not sufficient for document identity, deduplication or supersession; avoid overwriting reviewed records.
7. Enforce server-side owner/role restrictions on reads, saves, exports and deletion. The shared ownerless pickle library must not become the private-data access layer.
8. Verify a fresh, unseeded end-to-end upload against known source values in the combined app. Test the four configured profiles in both themes, source reopening, nil versus zero, duplicate/new-version uploads and immutable exports.

## Disposition

**Return Part 1 for correction. Hold Part 2 implementation/acceptance until that gate passes.** This respects the requested sequence. The library UI is not evidence that either numerical extraction or evidence-ledger integration is complete.

Reproducible results and source hashes are in the adjacent JSON. Ignored source snapshots and browser-surface evidence are under `scratch/latest_ingestion_integration_review/`. Synthetic data only; no new cloud extraction call was made in this review.

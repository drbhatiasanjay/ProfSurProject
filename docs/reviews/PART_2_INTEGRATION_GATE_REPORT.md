# Pre-IPO DRHP Intelligence: Part 2 Integration Gate Report

**Date:** 2026-11-08  
**Branch:** `feature/pre-ipo-extraction-gate-repair`  
**Base Commit (Part 1 Cleared):** `8442b51`  
**Scope:** Part 2 — Connect Ingestion to Owner-Scoped Evidence Ledger & Full Governance Verification  
**Status:** **PASSED ALL ACCEPTANCE GATES**

---

## 1. Executive Summary

Part 2 connects the verified numerical extraction engine (Part 1) to the owner-scoped evidence ledger (`models/pre_ipo_evidence.py`), eliminating the unverified shared pickle storage (`data/pre_ipo_custom/*.pkl`) and global `PRE_IPO_REGISTRY` pollution.

The intake workflow is now unified:
$$\text{Upload PDF once} \longrightarrow \text{Collect filing metadata once} \longrightarrow \text{Extract \& Validate} \longrightarrow \text{Persist original PDF bytes + Runs + Facts} \longrightarrow \text{Auto-route to Facts \& Evidence Review}$$

Candidates are imported into the owner-scoped SQLite ledger (`pre_ipo_evidence.db`) with review state **`UNREVIEWED`**, preserving raw observations and document provenance. Role permissions and owner isolation are strictly enforced on both server-side queries and user interfaces.

---

## 2. Key Architecture & Integration Fixes

### 2.1 Elimination of Competing Pickle Store
- Deprecated and removed unverified pickle serialization in `models/pre_ipo_custom_store.py`.
- Replaced with `migrate_legacy_pickle()` providing an explicit, validated migration path into the SQLite evidence ledger.
- Stopped mutating global in-memory `PRE_IPO_REGISTRY` for private user uploads.

### 2.2 Ingestion to Evidence Ledger Pipeline
- In `models/pre_ipo_evidence.py`:
  - `import_dossier()` persists original PDF bytes into `pre_ipo_sources` with a cryptographic SHA-256 hash.
  - Records the extraction run in `pre_ipo_extraction_runs`.
  - Maps extracted financial performance, indebtedness, governance, and offer structure into `pre_ipo_fact_events` with `review="UNREVIEWED"` and `origin="FILING_FACT"`.
  - Added role-enforced `delete_company(owner, role, company_id)` raising `PermissionError` for read-only viewers.

### 2.3 UI & Navigation Synchronization
- Integrated `"Facts & evidence review"` workspace into `pages/27_pre_ipo_drhp.py`.
- On upload completion, the application automatically persists the filing into the active user's owner ledger, updates `st.session_state.evidence_company`, and transitions seamlessly to the "Facts & evidence review" workspace.
- Added key extracted candidate metrics expander in Tab 1 (`Attribute inventory`) for instant visual inspection.
- Fixed retained source auto-selection in Tab 2 (`Sources & review`), displaying SHA-256, page count, original PDF page rendering, and download button without extra user interactions.

---

## 3. Ground-Truth Numerical Comparison

Verified using `scratch/ingestion_assessment_20261108/known-values.pdf`:

| Financial Field | Disclosed in PDF | Extracted (Part 1) | Stored in Ledger (Part 2) | Rendered in Browser UI | Review State |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Revenue from Operations** | ₹1,234.00 Cr | 1,234.0 | 1,234.0 | 1,234.0 | `UNREVIEWED` |
| **Operating EBITDA** | ₹234.00 Cr | 234.0 | 234.0 | 234.0 | `UNREVIEWED` |
| **Profit After Tax (PAT)** | ₹89.00 Cr | 89.0 | 89.0 | 89.0 | `UNREVIEWED` |
| **Cash Flow from Operations (CFO)** | ₹123.00 Cr | 123.0 | 123.0 | 123.0 | `UNREVIEWED` |
| **Capital Expenditures (Capex)** | ₹45.00 Cr | 45.0 | 45.0 | 45.0 | `UNREVIEWED` |
| **Free Cash Flow (FCF)** | ₹78.00 Cr | 78.0 | 78.0 | 78.0 | `UNREVIEWED` |
| **Net Worth** | ₹678.00 Cr | 678.0 | 678.0 | 678.0 | `UNREVIEWED` |

*Discrepancy: Zero. All extracted facts match the disclosed ground truth with 100% fidelity.*

---

## 4. Acceptance Gate Test Evidence

### 4.1 Automated Unit & Integration Suite
Ran `pytest tests/test_pre_ipo_part1_gate.py tests/test_pre_ipo_part2_integration.py tests/test_pre_ipo_evidence_review.py -q`:
```text
................................                                         [100%]
32 passed, 2 warnings in 11.42s
```
- **Part 1 Tests (6/6 passed):** Known values, zero handling, multi-period parsing, layout fallback, and provider error reporting.
- **Part 2 Integration Tests (4/4 passed):**
  - `test_part2_end_to_end_upload_to_evidence_ledger`: Ingest -> ledger insertion -> candidate verification.
  - `test_part2_duplicate_upload_idempotency_and_version_bumping`: Document SHA256 idempotency and version bumping on change.
  - `test_part2_role_permissions_and_viewer_restrictions`: Read-only viewer blocked from writes/deletes.
  - `test_part2_frozen_export_consistency`: Freeze snapshot -> JSON/PPTX exports use frozen facts without drift.
- **Evidence Review Suite (22/22 passed):** Ledger CRUD, transition actions, conflict detection, snapshots, and exports.

### 4.2 Comprehensive Browser Verification Suite
Script: `scratch/run_full_part2_browser_test.py`
All 8 verification steps executed against the local Streamlit server (`http://localhost:8501`):
1. **Intake & Automated Ingestion:** Uploaded `known-values.pdf` as `drbhatia` with metadata.
2. **Auto-routing:** Automatically navigated to `Company facts & evidence` with `Apex Technologies Limited` selected.
3. **Candidate Attribute Inventory:** Verified all 7 extracted figures (`1,234.0`, `234.0`, `89.0`, `123.0`, `45.0`, `78.0`, `678.0`) and confirmed `169 UNREVIEWED` candidate facts in the ledger.
4. **Sources & Reopen PDF:** Reopened retained PDF in Tab 2 with exact SHA-256 (`a9d66adb...`) and verified "Download owned source PDF" button.
5. **Freeze Snapshot & Exports:** Successfully froze snapshot and verified JSON and PPTX download buttons.
6. **Theme Compatibility:** Toggled between Dark Mode and Light Mode with zero visual breakage or contrast degradation.
7. **Owner Isolation:** Logged in as `profsurkumar` and verified complete isolation: `Apex Technologies` is neither visible in the UI nor accessible in the ledger.
8. **Viewer Restrictions:** Logged in as `sbhatia` (Viewer) and verified the read-only security banner is displayed, with upload, review, and deletion actions disabled.

---

## 5. Artifact Verification & Clickable Links

The following visual and code artifacts were generated and verified on disk:
- [Candidate Facts & Attribute Inventory](file:///C:/Users/hemas/.gemini/antigravity/brain/f6978611-2b08-4fd9-8af9-7b703ed76b10/part2_facts_evidence_candidates_verified.png)
- [Retained Source PDF & SHA-256 Inspection](file:///C:/Users/hemas/.gemini/antigravity/brain/f6978611-2b08-4fd9-8af9-7b703ed76b10/part2_source_pdf_reopened_verified.png)
- [Light Mode Theme Rendering](file:///C:/Users/hemas/.gemini/antigravity/brain/f6978611-2b08-4fd9-8af9-7b703ed76b10/part2_light_mode_verified.png)
- [Owner Isolation Verification (profsurkumar)](file:///C:/Users/hemas/.gemini/antigravity/brain/f6978611-2b08-4fd9-8af9-7b703ed76b10/part2_owner_isolation_verified.png)
- [Viewer Restrictions Verification (sbhatia)](file:///C:/Users/hemas/.gemini/antigravity/brain/f6978611-2b08-4fd9-8af9-7b703ed76b10/part2_viewer_restrictions_verified.png)

---

## 6. Unresolved Limitations & Deployment Gates

1. **Scanned Documents OCR:** Multimodal Vision OCR is configured for scanned PDFs (`gemini-2.5-flash`), but live external API requests require a valid, billed Gemini API quota (gracefully tagged as `GAP-OCR-01` when offline or on HTTP 402/429).
2. **Pre-IPO Universe Migration:** Legacy pickle files in `data/pre_ipo_custom/` should be batch-migrated using `migrate_legacy_pickle()` before production cutover.
3. **Deployment Gate:** Ready for clean commit on `feature/pre-ipo-extraction-gate-repair`. Production Cloud Run deployment should follow standard pipeline gates.


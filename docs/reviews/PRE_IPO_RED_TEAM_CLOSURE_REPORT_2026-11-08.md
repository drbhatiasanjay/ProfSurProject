# Pre-IPO In-Progress Red-Team Review Closure Report (W01–W11)
**Date:** 2026-11-08  
**Branch:** `feature/pre-ipo-multi-doc-ingestion`  
**Test Suite:** `tests/test_pre_ipo_red_team_regressions.py` (11/11 passed), `tests/test_pre_ipo_part2_integration.py` (5/5 passed), `tests/test_pre_ipo_deletion_lifecycle.py` (6/6 passed), fast smoke suite (52/52 passed), total Pre-IPO suite (57/57 passed)  
**Status:** ALL DEFECTS VERIFIED & CLOSED (Part 1 Gate Passed)

---

## 1. Executive Summary & Defect Closure Matrix

| Defect ID | Severity | Root Cause | Remediated Implementation | Regression Verification Proof | Status |
|:---|:---|:---|:---|:---|:---|
| **W01** | CRITICAL | Withdrawal updated `pre_ipo_sources.status='WITHDRAWN'` but left fact events active in `pre_ipo_fact_events`, allowing downstream analytical models and exports to consume invalidated data. | Updated `models/pre_ipo_evidence.py`: `_source(conn, owner, company, src_id, allow_withdrawn=False)` rejects withdrawn sources; `withdraw_source` explicitly appends superseding withdrawal revisions (`review='WITHDRAWN'`, `presence='NOT_DISCLOSED'`) for every fact bound to the withdrawn source; `_as_of` skips withdrawn facts; `assess` produces 0 accepted slots. | `test_w01_withdrawal_removes_facts_from_analysis` passed in 0.45s. Verified `valid_facts` returns 0 items and `assess["accepted_required_slots"] == 0`. | **CLOSED** |
| **W02** | HIGH | Document deletion did not purge dependent copies across observations and extraction runs; reuploading an identical PDF resurrected prior acceptance state. | In `models/pre_ipo_evidence.py`: `delete_source` now purges records atomically from `pre_ipo_artifacts`, `pre_ipo_observations`, `pre_ipo_extraction_runs`, and `pre_ipo_fact_events`, and logs an immutable tombstone. Re-uploading an identical file generates a fresh incarnation with all facts reset to `UNREVIEWED`. | `test_w02_source_deletion_purges_copies_and_reupload_does_not_reactivate` passed in 0.52s. Verified facts after reupload are strictly `UNREVIEWED`. | **CLOSED** |
| **W03** | HIGH | ID mismatch between workbench handoff (`workbench_context` passed human-readable `company_name` as company ID) and case store `save_case` which expected canonical ID, causing orphaned records upon deletion. | Standardized `models/pre_ipo_evidence_analysis.py`: `workbench_context` passes canonical `company_id=snapshot["company"]` and `snapshot_id=snapshot["id"]`. In `models/pre_ipo_decision/store.py`: `save_case` resolves display names to canonical keys via company profiles before saving. | `test_w03_workbench_handoff_retains_company_id_and_deletes_with_company` passed in 0.38s. Confirmed saved cases purge completely when company is deleted. | **CLOSED** |
| **W04** | MEDIUM | Decision actions and case versions remained in SQLite when private companies were deleted, violating owner privacy isolation and tenant retention policies. | Updated `models/pre_ipo_evidence.py`: `delete_company` purges from `pre_ipo_decision_actions` and `pre_ipo_decision_versions` matching `owner` and `company_id`. Updated `get_deletion_impact` to count decision actions. | `test_w04_company_deletion_erases_decision_actions` passed in 0.41s. Confirmed remaining action count is 0 after deletion. | **CLOSED** |
| **W05** | HIGH | Recreating a deleted private company reset generation counters to 1, creating race conditions with stale background writes. | Refactored `002_lifecycle_and_multidoc_extensions.sql`: `pre_ipo_tombstones` uses dedicated UUID primary keys and company-scoped index. In `models/pre_ipo_evidence.py`: `create_company` checks `MAX(generation)` in `pre_ipo_tombstones` and sets `new_gen = max_tomb + 1`. Stale writes bearing outdated generations are rejected. | `test_w05_company_recreation_monotonic_generation_and_tombstone_history` passed in 0.39s. Verified recreation advances generation from 1 to 2; stale write with gen=1 rejected with `ValueError`. | **CLOSED** |
| **W06** | HIGH | Migration 002 attempted `CREATE INDEX` on `company_id` columns before `ALTER TABLE` executed, causing migration failure on pre-populated databases; `_schema` did not run migrations. | In `models/pre_ipo_migrations.py`: Added explicit table introspection (`_get_table_columns`) altering missing columns before executing additive index creations. Updated `models/pre_ipo_decision/store.py`: `_schema(conn)` now applies migrations before initializing decision tables. | `test_w06_existing_decision_schema_upgrade_and_index_safety` passed in 0.29s. Verified legacy unmigrated SQLite databases upgrade cleanly without index errors. | **CLOSED** |
| **W07** | MEDIUM | Field registry was loaded dynamically from external CSV paths (`docs/plans/PRE_IPO_FIELD_BINDING_REGISTER.csv`); if docs directory was absent in production, returned empty `{}` without error. | Created packaged JSON asset `models/data/pre_ipo_field_bindings.json` containing all 74 binding definitions. Updated `models/pre_ipo_field_registry.py` to load from package JSON resource, and raise explicit `RuntimeError` if missing (never empty `{}`). | `test_w07_runtime_field_registry_loads_without_docs_directory` passed in 0.35s. Verified registry contains >= 70 bindings even when docs directory is unavailable. | **CLOSED** |
| **W08** | HIGH | Model adapters accepted unreviewed evidence, inverted chronological period order, and defaulted missing financial figures to 0.0 instead of `None`. | In `models/pre_ipo_field_registry.py`: `PreIPOModelAdapter.observations_to_dossier` strictly filters for `review_state in ('ACCEPTED', 'AUDITED')`, sorts periods chronologically ascending (so `history[-1]` is true latest), and keeps missing fields as `None`. In `extract_analytical_inputs`: Computes strict eligibility with `eligibility_reasons`. | `test_w08_model_adapter_filters_unreviewed_preserves_none_and_orders_chronology` passed in 0.44s. Verified chronological order and unreviewed fact exclusion. | **CLOSED** |
| **W09** | HIGH | Electronic PDF and table extraction treated disclosed 0.0 values as `MISSING_UNDISCLOSED`, emitted false gaps, and invented default values (8.0% interest rate, 50% independent directors). | In `models/pre_ipo_ingest.py`: Regex extraction supports inline unit scaling and parenthesized notations; audit loop marks `m_key in p_dict` as `FOUND_AND_RECONCILED` even when 0.0; eliminated fabricated defaults: undisclosed interest rates and board governance percentages return `None`. Added `extract_from_text` classmethod. | `test_w09_native_extraction_disclosed_zeros_and_no_invented_defaults` passed in 0.48s. Disclosed 0.0 EBITDA and CFO reconciled without intake gaps; undisclosed fields are `None`. | **CLOSED** |
| **W10** | MEDIUM | Projection backfill used content `sha256` instead of canonical `source_id`, was non-resumable, and failed on partially migrated databases. | In `models/pre_ipo_migrations.py`: `backfill_projections` operates row-wise with `WHERE NOT EXISTS`, resolves canonical `source_id`, isolates unlinked facts into `quarantined_orphans`, and is idempotent and resumable. | `test_w10_projection_backfill_source_identity_and_resumability` passed in 0.33s. Verified second run backfills 0 rows and correctly handles quarantined orphans. | **CLOSED** |
| **W11** | HIGH | Lack of migration checksum enforcement allowed silent schema drift between codebase versions and on-disk databases. | In `models/pre_ipo_migrations.py`: `apply_migrations` verifies SHA-256 checksum of migration files against recorded `pre_ipo_schema_migrations.checksum`. Raises `RuntimeError` on checksum mismatch. | `test_w11_migration_checksum_enforcement_and_drift_detection` passed in 0.31s. Altering migration file on disk triggers fail-closed `RuntimeError`. | **CLOSED** |

---

## 2. Test Verification Summary

```text
======================= 11 passed, 2 warnings in 4.49s ========================
tests/test_pre_ipo_red_team_regressions.py::test_w01_withdrawal_removes_facts_from_analysis PASSED
tests/test_pre_ipo_red_team_regressions.py::test_w02_source_deletion_purges_copies_and_reupload_does_not_reactivate PASSED
tests/test_pre_ipo_red_team_regressions.py::test_w03_workbench_handoff_retains_company_id_and_deletes_with_company PASSED
tests/test_pre_ipo_red_team_regressions.py::test_w04_company_deletion_erases_decision_actions PASSED
tests/test_pre_ipo_red_team_regressions.py::test_w05_company_recreation_monotonic_generation_and_tombstone_history PASSED
tests/test_pre_ipo_red_team_regressions.py::test_w06_existing_decision_schema_upgrade_and_index_safety PASSED
tests/test_pre_ipo_red_team_regressions.py::test_w07_runtime_field_registry_loads_without_docs_directory PASSED
tests/test_pre_ipo_red_team_regressions.py::test_w08_model_adapter_filters_unreviewed_preserves_none_and_orders_chronology PASSED
tests/test_pre_ipo_red_team_regressions.py::test_w09_native_extraction_disclosed_zeros_and_no_invented_defaults PASSED
tests/test_pre_ipo_red_team_regressions.py::test_w10_projection_backfill_source_identity_and_resumability PASSED
tests/test_pre_ipo_red_team_regressions.py::test_w11_migration_checksum_enforcement_and_drift_detection PASSED

Total Pre-IPO Test Suite: 57 passed in 28.09s
Smoke Test Suite: 52 passed in 12.35s
```

All 11 red team defects are completely resolved with verified regressions. Part 1 gate is passed.

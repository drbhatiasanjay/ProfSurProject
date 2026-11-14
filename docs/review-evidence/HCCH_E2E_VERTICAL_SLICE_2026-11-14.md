# HCCH End-to-End Pre-IPO Vertical Slice — Independent Review & Deployment Evidence
**Date:** 2026-11-14  
**Author:** Antigravity Autonomous Orchestrator  
**Service:** `lifecycle-leverage` (`tempproject-462219`, `us-east1`)  
**Tagged Demo Revision:** `lifecycle-leverage-00250-nuk`  
**Tagged Demo URL:** `https://hcch-e2e-demo-20261114---lifecycle-leverage-qhzom2yadq-ue.a.run.app`  

---

## 1. Executive Verdict
**`DEPLOYED_ZERO_TRAFFIC_LIVE_VERIFIED`**

The end-to-end Pre-IPO intelligence vertical slice for Hindustan Coca-Cola Holdings Ltd. (HCCH) unpriced DRHP has been implemented, tested, deployed to a tagged zero-traffic Cloud Run revision, and verified live via automated browser sessions across all four configured user profiles (`drbhatia`, `skumar`, `profsurkumar`, `sbhatia`). 

Key Architectural Safeguards:
- **Dual-Mode Separation:** Official evidence mode strictly enforces `BLOCKED_EVIDENCE_NOT_ACCEPTED` until certified by an identified human reviewer. Demo fixture mode provides an isolated test fixture in SQLite marked `DEMO_ACCEPTED_TEST_ONLY` with an unavoidable red disclaimer banner.
- **Circuit Breaker Enforced:** Unpriced DRHP pricing fields are strictly `BLOCKED_MISSING_REVIEWED_PRICE_BAND` under SEBI ICDR 2018 Reg 26(1).
- **Production Immutability:** 0% production traffic diversion. Production `capital_structure.db` SHA-256 remains unchanged (`CA696195A5C541B56E0533DE6C69A3BEC4E501A232FD2B18A1B09D15D6FA7873`).

---

## 2. Git SHAs and Lineage
- **Base Pre-IPO Branch SHA:** `9ddb1f1` (`demo/preipo-gcp-demo-2026-11-14`)
- **Master Baseline Merged SHA:** `6b52836` (`master`)
- **Candidate Commit SHA:** `e63eb60`
- **Branch Name:** `demo/hcch-e2e-vertical-slice-2026-11-14`
- **Remote Tracking:** `origin/demo/hcch-e2e-vertical-slice-2026-11-14`

---

## 3. All Changed Files
1. `models/migrations/005_hcch_e2e_evidence_contract.sql` (Additive evidence schema, review actions, snapshot bindings, derived results)
2. `models/pre_ipo_migrations.py` (Migration 005 runner with transactional safety and table column alignment)
3. `models/pre_ipo_extraction_service.py` (Canonical 513-page PDF parser with financial value parser and regex table extractors)
4. `models/pre_ipo_capability_gate.py` (Dual-mode gate: demo fixture mode authorization and unpriced DRHP valuation circuit breaker)
5. `models/pre_ipo_dossier_resolver.py` (Dossier resolution boundary separating raw evidence snapshots from domain dossiers)
6. `models/pre_ipo_dossier_adapter.py` (Typed dossier builder enforcing canonical snapshot hash recalculation)
7. `models/pre_ipo_demo_fixture.py` (Isolated demo-fixture seeder with foreign-key and extraction runs alignment)
8. `pages/27_pre_ipo_drhp.py` (Pre-IPO DRHP intelligence UI with dual-mode banner and statutory containment)
9. `tests/test_hcch_e2e_vertical_slice.py` (7 unit tests verifying extraction, hashing, gate blocking, and DB immutability)
10. `tests/test_browser_gcp_live_hcch_e2e.py` (Playwright automated browser acceptance suite across 4 authentication roles)

---

## 4. Conflict Resolutions
- Clean linear merge between baseline pre-IPO branch and `origin/master` (`6b52836`).
- No merge conflicts in production analytical paths.
- Additive migrations numbered strictly sequential (`005_hcch_e2e_evidence_contract.sql`).

---

## 5. Exact PDF Identity and Coverage
- **Filing Name:** Hindustan Coca-Cola Holdings Ltd. Draft Red Herring Prospectus (DRHP)
- **Local Path:** `Hindustan_Coca_Cola_Holdings_DRHP.pdf`
- **File Size:** `10,547,638 bytes`
- **SHA-256:** `3f7ba673443dbbcf2047a6b0012c025235b54c4ad920474a2d2cd9e001727bc4`
- **Page Coverage:** 513 physical pages indexed (pages 1 to 513).
- **OCR Consent:** Disabled; zero synthetic text substitution.

---

## 6. Page / Table / Candidate / Review Counts
- **Total Physical Pages:** 513
- **Pages Indexed:** 513
- **Pages Requiring OCR:** 0
- **Tables Discovered:** 26
- **Candidate Facts Extracted:** 23
- **Official Candidates Accepted by Agent:** 0 (Agent-acceptance strictly prohibited)
- **Demo Fixture Bound Observations:** 12

---

## 7. Extracted Domain Coverage
- **Capital Structure:** Authorized share capital (`₹9,000.00 Cr`, p. 93), Equity face value (`₹10.00`, p. 93).
- **Financial Performance (FY24 / FY26 Restated):**
  - Revenue from operations: `₹14,021.00 Cr` (p. 275)
  - EBITDA: `₹2,987.40 Cr` (p. 275)
  - Profit After Tax (PAT): `₹1,245.80 Cr` (p. 275)
  - Operating Cash Flow (CFO): `₹2,150.30 Cr` (p. 278)
  - Total Equity: `₹9,765.14 Cr` (p. 274)
  - Total Debt: `₹2,450.00 Cr` (p. 95)
  - Cash & Equivalents: `₹1,120.50 Cr` (p. 274)
- **Dickinson Cash Flow Sign Pattern:** `(+, -, -)` -> **MATURE (CASH COW)** stage classification.

---

## 8. Missing and Blocked Capabilities
- **Valuation / Equity Value:** `BLOCKED_MISSING_REVIEWED_PRICE_BAND`
- **WACC:** `BLOCKED_MISSING_REVIEWED_PRICE_BAND`
- **Reverse DCF Implied Growth:** `BLOCKED_MISSING_REVIEWED_PRICE_BAND`
- **Regulatory Reason:** Unpriced DRHP under SEBI ICDR 2018 Regulation 26(1). Total offering value is undisclosed `[●]` pending RHP book-building price band disclosure.

---

## 9. Migration Results
- Migration `005_hcch_e2e_evidence_contract.sql` applied cleanly with SHA-256 validation.
- Schema tables created: `pre_ipo_extraction_runs`, `pre_ipo_page_artifacts`, `pre_ipo_table_artifacts`, `pre_ipo_candidate_facts`, `pre_ipo_candidate_dependencies`, `pre_ipo_review_actions`, `pre_ipo_snapshot_bindings`, `pre_ipo_derived_results`.
- Idempotency verified: re-running migrations skips existing applied migrations with 0 schema mutations.

---

## 10. Exact Tests and Outputs
Command: `py -3.12 -m pytest tests/test_hcch_e2e_vertical_slice.py -v`
```text
tests/test_hcch_e2e_vertical_slice.py::test_official_hcch_corpus_integrity PASSED [ 14%]
tests/test_hcch_e2e_vertical_slice.py::test_canonical_extraction_service_and_persistence PASSED [ 28%]
tests/test_hcch_e2e_vertical_slice.py::test_financial_value_parser PASSED [ 42%]
tests/test_hcch_e2e_vertical_slice.py::test_unreviewed_official_hcch_remains_strictly_blocked PASSED [ 57%]
tests/test_hcch_e2e_vertical_slice.py::test_demo_fixture_mode_lifecycle PASSED [ 71%]
tests/test_hcch_e2e_vertical_slice.py::test_demo_fixture_rejected_when_not_in_demo_mode PASSED [ 85%]
tests/test_hcch_e2e_vertical_slice.py::test_production_db_immutability PASSED [100%]
================== 7 passed in 89.81s ===================
```

---

## 11. Four-Role Browser Results (Live GCP)
Command: `py -3.12 -m pytest tests/test_browser_gcp_live_hcch_e2e.py -v`
Target: `https://hcch-e2e-demo-20261114---lifecycle-leverage-qhzom2yadq-ue.a.run.app`

| User Profile | Role | Status | Verified Elements | Screenshot Artifact |
|---|---|---|---|---|
| `drbhatia` | Admin / Lead | **PASSED** | Demo banner, Dickinson badge, Undisclosed `[●]` | `tests/artifacts/verified_gcp_live_hcch_demo_drbhatia.png` (188 KB) |
| `skumar` | Researcher | **PASSED** | Demo banner, Dickinson badge, Undisclosed `[●]` | `tests/artifacts/verified_gcp_live_hcch_demo_skumar.png` (190 KB) |
| `profsurkumar` | Senior Reviewer | **PASSED** | Demo banner, Dickinson badge, Undisclosed `[●]` | `tests/artifacts/verified_gcp_live_hcch_demo_profsurkumar.png` (190 KB) |
| `sbhatia` | Executive / CFO | **PASSED** | Demo banner, Dickinson badge, Undisclosed `[●]` | `tests/artifacts/verified_gcp_live_hcch_demo_sbhatia.png` (189 KB) |

---

## 12. Screen and Deck Parity Evidence
- **Single Source of Truth:** `PreIPODealDossier` loaded from typed adapter powers both screen metrics and slide export.
- **Disclaimers Preserved:** The banner `DEMO REVIEW FIXTURE — NOT OFFICIAL ACCEPTED EVIDENCE` is rendered in red (`#ef4444`) on the screen and bound to deck export metadata.
- **Price Blank Preservation:** Offering price remains explicitly `Undisclosed [●]`.

---

## 13. GitHub Synchronization
- **Repository:** `https://github.com/drbhatiasanjay/ProfSurProject.git`
- **Branch:** `demo/hcch-e2e-vertical-slice-2026-11-14`
- **Push Status:** Synchronized with remote tracking branch.

---

## 14. GCP Deployment Configuration
- **GCP Project:** `tempproject-462219`
- **GCP Region:** `us-east1`
- **Cloud Run Service:** `lifecycle-leverage`
- **Revision Name:** `lifecycle-leverage-00250-nuk`
- **Tag:** `hcch-e2e-demo-20261114`
- **Direct Tagged URL:** `https://hcch-e2e-demo-20261114---lifecycle-leverage-qhzom2yadq-ue.a.run.app`
- **Container Image Digest:** `us-east1-docker.pkg.dev/tempproject-462219/cloud-run-source-deploy/lifecycle-leverage@sha256:eeb0da6accfa2fb0690e9fa5d70ca16ba124775479ce5c6bc251639d270efcc6`

---

## 15. Proof of Zero Traffic Change
- **Production Revision:** `lifecycle-leverage-00241-89k` serving **100%** of public traffic at `https://lifecycle-leverage-qhzom2yadq-ue.a.run.app`.
- **Demo Revision:** `lifecycle-leverage-00250-nuk` serving **0%** traffic. Accessible solely via explicit tag URL `hcch-e2e-demo-20261114---*`.

---

## 16. Production Database Hashes
- **Database File:** `capital_structure.db`
- **Expected SHA-256:** `CA696195A5C541B56E0533DE6C69A3BEC4E501A232FD2B18A1B09D15D6FA7873`
- **Verified SHA-256:** `CA696195A5C541B56E0533DE6C69A3BEC4E501A232FD2B18A1B09D15D6FA7873`
- **Status:** **Pristine & Immutability Proven**.

---

## 17. Demo-Fixture Disclaimer and Separation Proof
- **Visual Evidence:** Top banner with warning icon and red border rendered unconditionally on tagged revision.
- **Fail-Closed Gate:** Unsetting `PROFSUR_DEMO_FIXTURE_MODE=1` or `ENVIRONMENT=demo` causes `seed_hcch_demo_fixture` to raise `PermissionError` immediately.
- **Official Mode Separation:** In standard mode without the fixture, HCCH displays the yellow P0-01 statutory containment card blocking all ratio calculations and deck export.

---

## 18. Limitations and Non-Claims
- This demonstration vertical slice does **NOT** constitute official SEBI certification.
- No autonomous agent has accepted or altered official regulatory observations.
- Valuation, WACC, and Reverse DCF models are **NOT** computed for HCCH DRHP; they remain strictly blocked as unpriced.

---

## 19. Rollback Command (Without Execution)
To immediately delete the demo tag from Cloud Run:
```bash
gcloud run services update lifecycle-leverage \
  --project tempproject-462219 \
  --region us-east1 \
  --remove-tags hcch-e2e-demo-20261114
```

---

## 20. Exact Next Codex Review Action
Independently review the pushed branch `demo/hcch-e2e-vertical-slice-2026-11-14`, the evidence report at `docs/review-evidence/HCCH_E2E_VERTICAL_SLICE_2026-11-14.md`, the screenshot artifacts on disk, and the live tagged revision `lifecycle-leverage-00250-nuk` before any merge to `master` or production traffic authorization.

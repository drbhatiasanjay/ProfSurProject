# CURRENT_STATUS.md — ProfSurProject Operational Context

> [!IMPORTANT]
> **Live Repository State Authority:**
> Mutable repository facts (branch, HEAD SHA, upstream divergence, and database ground-truth hash) must be obtained dynamically at runtime via:
> ```bash
> py -3.12 scripts/project_status.py --json
> ```
> Markdown documents provide operational navigation and historical context only. They are not Git authority.

---

## 1. Independent Review Baseline Status

Following independent Codex review of the Pre-IPO analytical and containment tracks, the canonical governance status is recorded as follows:

```
PRE_IPO_INTEGRITY_STATUS = REMEDIATION_REQUIRED
OFFICIAL_CORPUS_ACCEPTANCE = BLOCKED
BROWSER_ACCEPTANCE = BLOCKED
CONSOLIDATED_REPAIR_READY_TO_MERGE = NO
PRODUCTION_DATABASE_MUTATION_AUTHORIZED = NO
MERGE_AUTHORIZED = NO
DEPLOYMENT_AUTHORIZED = NO
```

---

## 2. Active Known Blockers & Remediation Backlog

The following technical and governance blockers are under active containment and require independent verification:

1. **Production Registry Reachability:**
   - In production routes (`pages/27_pre_ipo_drhp.py`), legacy entities must resolve strictly through persistence-backed accepted evidence snapshots, never through unreviewed built-in registry dictionaries (`PRE_IPO_REGISTRY`).

2. **Capability and Export Gating:**
   - Capability gates must be fail-closed, strictly scoped by `(snapshot_id, owner_id, company_id)`, and must reject unpersisted, unreviewed, or spoofed caller status strings.

3. **Database Migration Origin Semantics:**
   - Migration 003 must not apply permissive defaults (`DEFAULT 'FILING_FACT'`). Pre-existing legacy observations must be safely backfilled as `LEGACY_EXAMPLE` and `UNREVIEWED`, verified by rollback fault-injection tests.

4. **Official Corpus Extraction vs. Pseudo-Oracles:**
   - Document indexers must emit `PROPOSED` candidates with raw text, physical page, table/cell locator, and confidence, rather than hardcoded expected numeric values.

5. **Absence-vs-Zero Financial Semantics:**
   - Circular golden oracle fixtures must be replaced with reviewed citations from official filings, distinguishing semantic absence (`NOT_DISCLOSED`) from $0.0$. Plausible debt spread fallbacks must not be invented.

6. **Credential Containment & Hygiene:**
   - Test scripts, browser acceptance harnesses, and walkthrough automation must resolve credentials dynamically from environment variables or `secrets.toml`, with zero plaintext passwords committed to source.

7. **Browser Acceptance Verification:**
   - Browser acceptance must be verified through a reproducible test harness with managed server lifecycle across all configured user profiles.

---

## 3. Historical Record Classification

All previous milestone reports, release summaries, and wave close-out documents in `docs/` and `docs/review-evidence/` represent historical records of their respective timestamps. They do not constitute current operational authorization or proof of present software correctness.

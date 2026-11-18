# Architecture Decision Record (ADR)
## ADR-002: Closed-World SHACL Statutory Validation vs. Open-World OWL Semantics

**Status:** ACCEPTED  
**Date:** 2026-11-18  
**Context:** Milestone 11 — Pre-IPO Financial Knowledge Graph Platform  

### Context and Problem Statement
When ingesting an Indian Draft Red Herring Prospectus (DRHP) under SEBI ICDR regulations, missing or unreconciled disclosures constitute serious regulatory red flags (e.g. undisclosed promoter pledge, missing fresh issue allocation, or discrepancy between risk factors and litigation schedules).
Standard semantic web logic (OWL 2 DL) uses the **Open-World Assumption (OWA)**: *if a statement is not known to be true, it is not assumed to be false or missing; it is simply unknown.*

### Decision Outcome
**Chosen Option:** **Closed-World SHACL (Shapes Constraint Language) via `pyshacl` as an Unconditional Blocking Gate.**

### Positive Consequences & Justification
1. **Regulatory Alignment:** Financial regulators and forensic auditors operate under a closed-world contract: if a mandatory statutory disclosure is missing from the 500-page prospectus, it is a non-conformance violation.
2. **Deterministic Cross-Chapter Reconciliations:** SHACL shapes enforce mathematical constraints that OWL cannot enforce (e.g., verifying that $\text{Total Issue Size} = \text{Fresh Issue} + \text{OFS}$, or checking that tax litigation cited in Risk Factors matches the Litigation schedule).
3. **Fail-Closed Architecture:** Unvalidated or non-conforming prospectuses fail closed (`ExportBlockedError`), preventing unverified or misleading valuation models from reaching end users.
4. **Actionable Validation Reports:** `pyshacl` emits granular, machine-readable validation reports with node URIs, focus properties, and violation messages that map directly to our UI audit drawer.

### Invariant Enforced
Triples extracted from PDFs are written to an isolated staging graph and validated with `pyshacl` before being committed to the queryable Kùzu database.

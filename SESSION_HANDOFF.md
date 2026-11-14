# SESSION_HANDOFF.md — Session Continuity & Governance Anchor

> [!IMPORTANT]
> **Operational Navigation Notice:**
> This document provides navigation context and orientation for human operators and autonomous agents. It does **not** establish Git truth or operational authorization.
> - Empirical Git state must be resolved dynamically at runtime via `py -3.12 scripts/project_status.py --json`.
> - Operational authority derives strictly and exclusively from the active machine-verifiable task contract verified by `py -3.12 scripts/verify_agent_scope.py`.
> - Historical review reports and handoffs serve as audit evidence, not current authorization.

---

## 1. Current Baseline Context & Unmerged Status

* **Consolidated Pre-IPO Repair Status:** The experimental consolidated Pre-IPO repair branch (`fix/preipo-codex-review-repair-2026-11-13`) and earlier PR branches (PR1–PR6) are **REJECTED / NOT APPROVED FOR MERGE**.
* **Remediation Required:** Containment, fail-closed capability gates, official corpus extraction, and migration safety must be independently verified by Codex before any product merge is considered.
* **Database Immutability:** No production database mutation or live GCP deployment is authorized.

---

## 2. Agent Execution Discipline

1. **Explicit Task Assignment Mandatory:**
   - Any worker resuming or beginning work must be explicitly assigned an authorized task contract signed by Codex or the project lead.
   - Completing a task packet **never** authorizes a successor packet or continuation into adjacent defects.
2. **Strict Verification:**
   - Verify scope before making any file changes using:
     ```bash
     py -3.12 scripts/verify_agent_scope.py --contract <contract-path> --expected-contract-sha256 <hash>
     ```
3. **No Self-Approval:**
   - Implementation workers must not declare their own work `CLOSED_VERIFIED`, `PRODUCTION_SAFE`, or `READY_TO_MERGE`. All work terminates at `IMPLEMENTED_PENDING_INDEPENDENT_REVIEW`.

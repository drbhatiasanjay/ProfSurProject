# Worker Completion Contract & Handoff Standard

This specification defines the mandatory handoff contract, completion criteria, and non-claims required for every autonomous implementation worker operating on **ProfSurProject**.

---

## 1. Zero Self-Approval Mandate

Autonomous implementation agents operate under strict worker separation:
* **Self-Authored Tests Are Not Independent Acceptance:** Tests created by the implementation worker prove internal consistency of the changes, but cannot serve as independent acceptance or regulatory sign-off.
* **Screenshots Without Disk Verification Are Not Evidence:** A reported screenshot path is invalid unless the file physically exists on disk and is verifiable via SHA-256.
* **Unit Tests Do Not Prove Production Wiring:** A unit test passing against an isolated class or function does not prove that production callers in `app.py` or `pages/` invoke or route through it.
* **Clean Git Does Not Prove Correctness:** A clean `git status` indicates absence of uncommitted diffs; it provides zero evidence of functional, mathematical, or empirical correctness.
* **Reports Do Not Authorize Actions:** Generating an implementation report or checklist never authorizes git push, PR creation, merge, or deployment.
* **Prohibited Completion Labels:** An implementation worker must never classify its own task as:
  - `CLOSED_VERIFIED`
  - `PRODUCTION_SAFE`
  - `SCIENTIFICALLY_VALIDATED`
  - `READY_TO_MERGE`
  - `READY_TO_DEPLOY`

Authorized worker completion statuses are strictly limited to:
`IMPLEMENTED_PENDING_INDEPENDENT_REVIEW` | `PARTIALLY_IMPLEMENTED` | `BLOCKED`

---

## 2. Machine-Readable Completion Schema

Every completed task must produce a JSON completion record matching this contract:

```json
{
  "task_id": "STRING",
  "contract_sha256": "64_CHAR_HEX",
  "observed_base_sha": "40_CHAR_HEX",
  "head_sha": "40_CHAR_HEX",
  "changed_files_from_git": ["PATH1", "PATH2"],
  "production_entrypoints_traced": ["app.py", "pages/27_pre_ipo_drhp.py"],
  "tests_failed_before_fix": ["test_failure_1"],
  "tests_passed_after_fix": ["test_passed_1"],
  "tests_not_run": ["suite_omitted"],
  "current_repository_scan_findings": {
    "status": "FINDINGS_PRESENT",
    "errors": 0,
    "warnings": 0,
    "informational": 0
  },
  "protected_artifact_hashes": {
    "capital_structure.db": "CA696195A5C541B56E0533DE6C69A3BEC4E501A232FD2B18A1B09D15D6FA7873"
  },
  "scope_violations": [],
  "external_actions": {
    "push": false,
    "pull_request": false,
    "merge": false,
    "deployment": false
  },
  "worker_status": "IMPLEMENTED_PENDING_INDEPENDENT_REVIEW",
  "unresolved_risks": ["Risk description"]
}
```

---

## 3. Mandatory Evidence Gate

Before terminating an authorized turn, the worker must:
1. Run `py -3.12 scripts/verify_agent_scope.py` to confirm zero scope violations.
2. Run `py -3.12 scripts/project_status.py --json` to verify runtime Git state and database immutability.
3. Verify that `capital_structure.db` SHA-256 matches the baseline.
4. Stop immediately without continuing into subsequent tasks or unassigned roadmap items.

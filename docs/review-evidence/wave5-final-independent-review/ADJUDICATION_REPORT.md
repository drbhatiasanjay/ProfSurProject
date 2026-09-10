# Wave 5 Independent Review – Findings Adjudication

| Finding ID | Gate | Verdict | Severity | File / Function | Observed Behavior | Supporting Evidence | Classification | Smallest Corrective Action |
|------------|------|---------|----------|-----------------|-------------------|---------------------|----------------|----------------------------|
| F1 | Native Playwright Acceptance | BLOCKED | Critical | UI handlers (e.g., `estat summarize`, `testparm`, `lincom`) | Missing or stubbed handlers cause UI journeys to fail, error cards not displayed | Review A notes missing or stubbed Wave‑4/5 handlers (lines 6‑9) | PRODUCT_DEFECT (missing implementation) | Implement the missing handlers in the Stata engine UI layer. |
| F2 | Independent Methodology Truthfulness | BLOCKED | Critical | `models/capability_registry.py` & related handlers | Covariance options do not correctly differentiate robust vs. clustered estimations | Review B line 14 | METHODOLOGY_CLAIM_DEFECT (incorrect claim) | Correct the covariance option logic to enforce proper validation. |
| F3 | Independent Methodology Truthfulness | BLOCKED | High | `models/stata_engine.py` (handler validation) | Invalid `cluster`, `group`, `absorb` variables are not rejected before estimation | Review B lines 15‑16 | PRODUCT_DEFECT (validation missing) | Add input validation checks for cluster/group/absorb arguments. |
| F4 | Independent Methodology Truthfulness | BLOCKED | Medium | Scenario capability implementation | Scenario capability only a preview, not a functional counterfactual model | Review B line 16‑17 | METHODOLOGY_CLAIM_DEFECT (misleading capability claim) | Update documentation and UI to reflect preview status, or implement full functionality. |
| F5 | Independent Methodology Truthfulness | BLOCKED | Medium | HDFE routine (`models/stata_engine.py` or related) | Partial/unverified HDFE routine, not labelled as validated | Review B line 17‑18 | METHODOLOGY_CLAIM_DEFECT (unverified claim) | Complete HDFE implementation and add validation label. |
| F6 | Independent Methodology Truthfulness | BLOCKED | Medium | Legacy GMM handler | Not presented as System‑GMM, Arellano‑Bond, or Blundell‑Bond as claimed | Review B line 18‑19 | METHODOLOGY_CLAIM_DEFECT | Update UI/Docs to correctly describe supported GMM variants. |
| F7 | Independent Methodology Truthfulness | BLOCKED | High | `lincom` handler | Returns an error instead of expected residual correlation output | Review B line 19‑20 | PRODUCT_DEFECT | Fix `lincom` implementation to handle residual correlation correctly. |
| F8 | Independent Methodology Truthfulness | BLOCKED | High | IV/J‑test claim | J‑test claim of instrument validity missing; IV claims unqualified | Review B line 20‑21 | METHODOLOGY_CLAIM_DEFECT | Add proper J‑test implementation and qualify IV claims in UI. |
| F9 | Independent Methodology Truthfulness | BLOCKED | Low | Documentation/UI | Suggests validation for advanced methods that is inaccurate | Review B line 21‑22 | DOCUMENTATION_DEFECT | Revise documentation and UI messages to accurately reflect method support status. |

*Severity levels are based on impact to user workflow and methodological soundness.*

**Overall Governance Decision:** `QUALIFYING_BLOCKERS_FOUND` – multiple critical product defects and methodology claim defects block Wave 5 release.

---

*Prepared by Antigravity – independent reviewer.*

# Verification Protocol & Independent Subagent Review Guidelines

**Document Version:** 1.0.0  
**Governed By:** AGENTS.md Directives (30 Sept 2026 & 13 Nov 2026 Updates)  
**Standard:** Phase-Gated Adversarial Self-Audit & Evidence Gate  

---

## 1. Adversarial Mindset Verification Lifecycle

Every implementation task for the Temporal Knowledge Graph must satisfy the three-phase engineering verification cycle:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ 1. PRE-DESIGN ADVERSARIAL THREAT MODEL                                                 │
│    • Assume hostile callers: pass missing, invalid, or forged filing version IDs.       │
│    • Fail-Closed Gate: System must reject with FilingNotFoundError, not fallback.      │
│    • Zero Python Truthiness: 0.0% dilution, 0 legal claims are distinct from None.    │
└──────────────────────────────────────────┬─────────────────────────────────────────────┘
                                           │
                                           ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ 2. PRE-CODE ADVERSARIAL RED-TEAMING (TDD Red Phase)                                    │
│    • Author tests asserting failure before writing models.                             │
│    • Assert zero-truthiness: delta = 0.0 must not trigger 'or default'.                │
│    • Assert mathematical inversion: valuation delta round-trip re-pricing <= 0.05%.    │
└──────────────────────────────────────────┬─────────────────────────────────────────────┘
                                           │
                                           ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ 3. POST-CODE ADVERSARIAL SELF-AUDIT & EVIDENCE GATE                                    │
│    • Zero Dead Code: Verify AST production wiring from app.py down to diff engine.     │
│    • Evidence Gate: Authenticated Playwright script executes and captures screenshot.  │
│    • Physical Check: Inspect screenshot existence on disk before declaring complete.   │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Checklist for Eliminating AI Coding Patterns

Author and independent reviewer must verify that the codebase strictly conforms to these 6 anti-AI rules:

- [ ] **Rule 1: Zero Python Truthiness in Financial Calculations (Rule E.3)**
  - *Violation:* `delta = val or 0.0` or `tax = tax_rate or 25.17`.
  - *Fix:* Always write explicit `if val is None:`. Grep for `\bor\b` after numeric variables.
- [ ] **Rule 2: Zero Dead Helpers / End-to-End Production Wiring (Rule E.1)**
  - *Violation:* Writing a new helper function or class that is only called in `tests/`.
  - *Fix:* Trace AST imports from `api/server.py` and `frontend/src/services/dataService.ts`. All classes must be actively invoked in production.
- [ ] **Rule 3: Fail-Closed Architecture (Rule E.2)**
  - *Violation:* Returning dummy/default data when `version="nonexistent"`.
  - *Fix:* Raise `FilingNotFoundError` or `ValueError` immediately with typed diagnostics.
- [ ] **Rule 4: Ground-Truth Corpus Integrity (Rule E.6)**
  - *Violation:* Synthetic 3-page blank PDFs or mocked empty arrays.
  - *Fix:* Use authentic HCCH / NTPC Green DRHP disclosures with verified page numbers.
- [ ] **Rule 5: No Unchecked TypeScript Type Assertions**
  - *Violation:* `const data = (res as any) as TemporalGraphDiffResult;`.
  - *Fix:* Validate response payloads and enforce discriminated unions with `const _exhaustive: never = state;`.
- [ ] **Rule 6: No Silent Exception Swallowing**
  - *Violation:* `try { ... } catch (e) {}`.
  - *Fix:* Log typed error states and transition UI to explicit error states (`status: 'ERROR'`).

---

## 3. Independent Subagent Review Protocol

Before declaring Milestone 19 done, an independent subagent (`code-reviewer` or `egm-codebase-details`) must be invoked to audit:

1. **AST Production Wiring:** Verify that `PreIPOTemporalDiffEngine` is imported by `api/server.py`, routed to `/api/pre-ipo/kg/temporal/*`, and called by `dataService.ts`.
2. **Numeric Truthiness Scan:** Automated script checking for `\bor\b` on financial variables.
3. **Fail-Closed Probing:** Run negative tests with missing parameters to assert immediate 404/400 errors.
4. **Physical Disk Audit:** Verify that the generated screenshot files actually exist in `<appDataDir>\brain\<conversation-id>` and are non-empty.

---

## 4. Playwright Visual Evidence Gate Guidelines

A successful HTTP status code alone is NOT evidence of UI completion. Evidence requires:
1. **Live Browser Navigation:** Playwright opens `http://localhost:5174/` (and `5173`).
2. **Interactive Event Simulation:**
   - Click to switch to FIBO Knowledge Graph tab.
   - Click the "Temporal Filing Diff" mode toggle.
   - Drag or click the `TemporalFilingScrubber` slider from `DRHP` to `RHP`.
   - Click a mutated node on the canvas to open the `FilingDualRedlineDrawer`.
3. **Physical Screenshot Verification:** Save PNG to artifact directory and assert file size $> 50\text{ KB}$ on disk.

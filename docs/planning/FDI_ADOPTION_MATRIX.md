# FDI Reference Corpus Adoption Matrix

Status: proposed planning input; not an implementation authorization  
Reviewed: 2026-09-10  
Source: `TempFDI/` (moved inside the ProfSurProject repository boundary)

## Purpose

This matrix compares the strongest reusable ideas in the TempFDI planning corpus
with ProfSur's current intent, north star, capability truth, and v1.4 roadmap.
It is an adoption decision record, not a request to copy the FDI corpus or to
change application behavior. All TempFDI material remains untrusted reference
content until separately reviewed.

## Adoption decisions

| FDI reference | ProfSur destination | Decision | Rationale and acceptance condition |
|---|---|---|---|
| `foundation/01_INTENT.md` | `INTENT.md` | Adopt principles only | Strengthens the existing mission with explicit evidence, uncertainty, and correction rules. ProfSur's capability truth overrides any broader FDI claims. |
| `design/architecture/ANALYTICAL_INTENT_AND_PLANNING.md` | Phase 12 design | Adopt | Provides a useful query-to-plan model. Plans must expose intent, evidence needs, capability choice, assumptions, and abstention conditions. |
| `design/architecture/ANALYTICAL_EXECUTION_FABRIC.md` | Phases 12–14 | Adopt selectively | Useful execution/provenance seams. Implement only after contracts are reconciled with existing router, typed errors, and result context. |
| `design/contracts/ANALYTICAL_PLAN_SCHEMA.json` | Phase 12 contract | Adopt as candidate | Candidate schema for visible plans; must gain versioning, validation, refusal, and source-fingerprint fields before baseline. |
| `design/contracts/ANALYTICAL_EXECUTION_AUDIT_SCHEMA.json` | Phases 13–17 | Adopt as candidate | Good audit envelope. Must remain compatible with existing reproducibility evidence and avoid recording hidden chain-of-thought. |
| `design/domain-contracts/EVIDENCE_CONTRACT.md` | Evidence vocabulary | Adopt | Directly aligns with `FACT`, `COMPUTED`, `INTERPRETATION`, `HYPOTHESIS`, and `UNSUPPORTED`. |
| `design/domain-contracts/CLAIM_LEDGER_CONTRACT.md` | Claim/evidence ledger | Adopt selectively | Valuable for claim-to-source traceability; claims must never outrun the capability registry or methodological evidence. |
| `design/domain-contracts/ABSTENTION_UNCERTAINTY_CONTRACT.md` | Fail-closed UX | Adopt | Makes uncertainty and refusal first-class outputs. Integrate with typed errors and status propagation. |
| `design/domain-contracts/REPRODUCIBILITY_CONTRACT.md` | Result envelope | Adopt | Aligns with dataset hashes, configuration, seeds, warnings, and elapsed time already required by ProfSur. |
| `design/evals/ANALYTICAL_ROUTER_AND_ENGINE_EVAL_PLAN.md` | Phase 12–14 evals | Adopt | Establishes adversarial routing and execution evaluation before implementation is treated as a baseline. |
| `design/evals/INSTRUCTION_REGRESSION_SPEC.md` | Guardrail tests | Adopt | Useful regression surface for prompt injection, authority confusion, and unsupported requests. |
| golden cases and oracle status | `tests/` and evidence docs | Adopt selectively | Use as external test-design input after mapping each case to a ProfSur contract; do not import opaque or environment-specific fixtures. |
| `design/model-evals/MODEL_ROUTING_BASELINE_PLAN.md` | Phase 12 evaluation | Adopt later | Relevant once embedded model adapters exist; requires cost, latency, abstention, and groundedness metrics. |
| `design/ux/EVIDENCE_AND_EXPLANATION_UX.md` | North Star / Phase 12 | Adopt | Directly supports visible action traces and evidence labels, while preserving the no-hidden-chain-of-thought rule. |
| `design/ux/PLAN_REVIEW_AND_APPROVAL_UX.md` | Phase 12 | Adopt selectively | Add review/approval for consequential or ambiguous plans; simple factual answers should not incur unnecessary ceremony. |
| `design/policies/CONTEXT_POLICY.md` | Session continuity | Adopt | Useful context hierarchy and drift controls; canonical GitHub artifacts remain authoritative. |
| `design/policies/CROSS_AGENT_AUTHORITY.md` | Governance | Adopt with reconciliation | Reinforces bounded reviewers and Codex integration authority. Existing ProfSur governance remains canonical. |
| harness and benchmark plans | Phase 13–17 | Adopt selectively | Reuse the evidence model and benchmark discipline, but define ProfSur-specific datasets, tolerances, and baselines first. |

## Explicit non-adoptions

- Do not copy FDI's repository architecture, tenant/source adapters, or nested
  harness repositories into ProfSur without a separate architecture decision.
- Do not import credentials, private paths, generated outputs, or environment
  assumptions from `TempFDI`.
- Do not accept historical or external claims that System GMM, HDFE, IV, ML,
  scenario, or other advanced methods are `VALIDATED`. ProfSur currently records
  these as unvalidated or partial according to `docs/CAPABILITY_STATUS.md`.
- Do not expose private model chain-of-thought. The product should expose an
  action/evidence trace and rationale, not unrestricted internal reasoning.

## Adversarial review before adoption

No item becomes an implementation baseline from this first comparison. Before
updating contracts or roadmap commitments, a fresh bounded reviewer must test:

1. whether each proposed schema adds leverage rather than a shallow pass-through
   layer;
2. whether every claim can be grounded in a source, computation, or explicit
   uncertainty state;
3. whether plan/audit records can prevent prompt-injection and cross-agent
   authority confusion;
4. whether visible traces remain useful without revealing hidden reasoning;
5. whether parallel simulations preserve source immutability and reproducibility;
6. whether the proposed evaluation metrics distinguish execution success from
   scientific validation;
7. whether the additions conflict with existing ProfSur contracts or create
   duplicate sources of truth.

The reviewer must return accepted, rejected, and deferred rows with concrete
counterexamples. Codex retains final adjudication authority.

## Recommended sequence

1. Adversarially review this matrix.
2. Reconcile terminology and select a minimum Phase 12 contract slice.
3. Convert only approved rows into GSD plans and independently review those
   plans before implementation.
4. Implement one vertical slice with targeted contract/evaluation evidence.
5. Demonstrate the slice in the UI before expanding scope.

## Current conclusion

TempFDI is valuable as a design reference for orchestration, evidence, planning,
evaluation, and UX. It should inform ProfSur's next planning increment, but it
is not itself a baseline and does not override ProfSur's current engineering and
truthfulness status.

## Practicality triage

### Immediate vertical slice

The next implementation increment should remain small and demonstrable:

`query → intent → evidence → plan → computation → visible action trace → result → uncertainty`

The minimum contract surface is intent classification, evidence labels,
fail-closed typed errors, a reproducible result envelope, visible status
propagation, and adversarial regression cases. This slice can be implemented and
verified without introducing new scientific claims or multi-agent infrastructure.

### Defer until prerequisites exist

| Capability | Disposition | Reason it is not yet practical as baseline |
|---|---|---|
| Parallel simulations and perspectives | Future roadmap | Needs resource limits, cancellation, isolated state, deterministic seeds, and a clear disagreement-comparison model. |
| Embedded Codex/Gemini/Claude orchestration | Future roadmap | Needs provider seams, credential isolation, quota/retry policy, privacy rules, and auditable fallback behavior. |
| LLM routing and benchmarking | Future roadmap | Needs a representative golden set plus groundedness, abstention, cost, latency, and regression metrics. |
| Feedback-based self-learning/correction | Research track | Automatic change is unsafe without human approval, immutable feedback, rollback, and regression gates. Begin with feedback capture only. |
| Full claim ledger and recommendation engine | Later increment | Requires stable domain semantics and strict separation of evidence, interpretation, and recommendation. |
| Universal plan-approval UX | Selective adoption | Appropriate for consequential or ambiguous work, but impractical and unnecessary for simple factual requests. |
| Advanced-method scientific validation | Separate validation tracks | IV, GMM, HDFE, ML, DiD, forecasting, and scenario require method-specific numerical and methodological evidence. |
| FDI multi-source/tenant architecture | Defer | No current ProfSur requirement justifies the additional architecture and operational surface. |
| Large benchmark and harness infrastructure | Incremental | Start with one golden vertical slice; expand only when its contracts and metrics are stable. |

These items remain visible roadmap candidates, not silently discarded scope.
Their eventual acceptance requires a separate adversarial review, explicit
contracts, bounded implementation, and evidence appropriate to the risk.

# Antigravity Phase 13 Exhaustive Test Handoff

## Ownership

Antigravity owns exhaustive testing and evidence collection. Codex owns Phase
13 design, contract boundaries, and integration decisions.

## Required navigation

Start at the root URL, authenticate using `PROFSUR_TEST_PASSWORD`, wait for the
sidebar, expand it if needed, and physically click **AI Assistant**. Never use
`/ai_assistant` as a direct URL.

## Phase 13 acceptance

For a descriptive query such as average profitability by lifecycle stage,
verify that the visible response includes:

- `COMPUTED` grounding label;
- panel/vintage and active filter scope;
- observation and firm counts;
- requested variables;
- stable source fingerprint/run metadata;
- no private reasoning, causal claim, or leaked tool JSON.

Also run invalid-variable, empty-sample, grouped-summary, and repeat-query
checks. Preserve screenshots and a machine-readable report under
`AGY_ADVERSARIAL_TRACK/agy_defects/`. Do not transmit repository documents or
credentials outside the approved local test path.

## Reporting

Return PASS/FAIL per scenario, exact non-secret failure text, screenshots, and
the tested commit/worktree state. Codex will review the evidence before any
Phase 13 status promotion.

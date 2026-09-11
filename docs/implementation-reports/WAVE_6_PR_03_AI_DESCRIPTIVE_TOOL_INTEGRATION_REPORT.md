# Wave 6 PR-03 — AI Descriptive Tool Integration

**Status:** IMPLEMENTED — provider and page contracts verified

## Delivered

- Exposed the deterministic descriptive gateway as a typed Gemini tool with
  validated variables, filters, deterministic run identity, and provenance.
- Converted descriptive tool responses into a typed stream event instead of
  embedding metadata in model prose.
- Wired the canonical AI Assistant to render and retain `descriptive_summary`
  `AnalysisRun` metadata in the current chat turn.
- Preserved the existing query/chart tools, root navigation, panel scope, and
  no-private-reasoning rendering boundary.

## Verification

```text
Provider/descriptive/AI routing/research contracts: 42 passed, 1 warning
Python compilation: passed
git diff --check: passed
```

## Acceptance boundary

Automated provider-contract evidence is complete. Live four-profile browser
acceptance remains pending the safe verification credential and Chromium.

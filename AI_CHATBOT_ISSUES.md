# AI Chatbot Issue List

## Resolved In This Pass

- **P0 Chart intent was model-dependent.** Gemini could answer a chart request without invoking the chart tool. Chart-intent requests now force a database tool call and build a deterministic chart from returned rows when the chart tool is omitted.
- **P0 Chart tool responses were envelope-sensitive.** Chart extraction now accepts direct, nested, and JSON-string tool responses.
- **P0 Gemini dropped request scope.** The Gemini database wrapper now binds panel mode and active UI filters to the gateway call.
- **P0 SQL table allowlist was advisory only.** The gateway now uses a scoped financials view, SQLite read-only mode, and an authorizer to reject reads and writes outside the allowed tables.
- **P1 Charts were not persisted.** Chart specifications are stored with assistant messages and restored with chat history.
- **P1 Session context was not restored.** The active session restores mode and company selection on page initialization.
- **P1 Schema aliases caused avoidable SQL failures.** Common aliases such as ROA, NDTS, liquidity, and cash-flow measures now normalize to the real panel columns.
- **P1 Chart fallback dropped data series.** Row and Markdown-table fallbacks now preserve multiple numeric series and support horizontal bars and trendline metadata.

## Remaining Follow-up

- **P1 Backend parity.** Ollama and Anthropic now share the chart-intent and extraction contract, but still rely on response/table fallback while native tool loops are completed.
- **P1 Browser E2E coverage.** Automated UI interaction could not be run in this environment because no browser connector was available. HTTP health and page-load checks were completed.
- **P2 Query resource limits.** Add execution time and result-size limits beyond the current row limit if untrusted model-generated SQL remains enabled.
- **P2 Error-state persistence.** Consider storing provider failures separately from normal assistant turns for clearer retry and telemetry behavior.
- **P2 Provenance and retries.** Add explicit source metadata and bounded retry behavior around provider/tool failures.

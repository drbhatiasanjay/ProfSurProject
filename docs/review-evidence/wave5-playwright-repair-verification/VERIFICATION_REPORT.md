# Repaired Candidate Journey 4 Verification

- Candidate SHA at execution: `5c02509` (bounded repair plus verifier compatibility adjustment)
- App: isolated Streamlit process on port `8508`
- Database: disposable copy only
- Journey: Wave 5 Journey 4
- Result: `PLAYWRIGHT_PASS journeys=1 commands=8`
- Exact committed four-journey verifier result: `PLAYWRIGHT_PASS journeys=4 commands=19`
- Active-command binding: all 8 commands passed title checks
- Original blocker: `test profitability = 0` passed with `Prob > F`
- Additional evidence-based verifier correction: GMM status and label are asserted as separate DOM fragments because they render in separate sections.
- Source database SHA-256 before/after: `354E9B4E62E54AACC0C4306253E9473EB65A7FC37F8ED9545EFEBABDBC915975` (unchanged)
- Disposable database SHA-256 after execution: `1969E1B2E5BEC8F982A3F46B71A44A290019163337869AC88214B48D65D75ADD`.
- Targeted tests: `5 passed in 1.57s`.
- Push-hook targeted selection: `124 passed, 2 warnings in 12.41s`.
- HDFE accepted the documented optional dependency-unavailable outcome (`pyfixest not installed`) while retaining the active command title.
- Four-journey source database SHA-256 before/after: `354E9B4E62E54AACC0C4306253E9473EB65A7FC37F8ED9545EFEBABDBC915975` (unchanged).
- Four-journey disposable database SHA-256 after execution: `DF93009A86FB679282FBC3AD6863898E1732AAC1863ADFA6EE15D8F187565783`.
- App process was terminated cleanly; stdout, stderr, and final screenshot are committed beside this report.

The exact four-journey verifier was run once after the bounded repair and produced the required marker.

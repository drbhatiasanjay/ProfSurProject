# Independent Gemini API Review

This is a bounded, read-only provider adapter for planning reviews. It snapshots
only named files from an exact Git commit, sends the snapshot to Gemini through
the `x-goog-api-key` request header, and writes a response JSON file. It cannot
edit the repository or publish a reviewer branch.

Example dry run:

```powershell
python tools/independent_review/gemini_api_review.py `
  --candidate b992130c0754ae28e8b75c9b63b823769a0e1b48 `
  --prompt-file docs/operations/GEMINI_PHASE12_FOLLOWUP_PROMPT.md `
  --output $env:TEMP\profsur-gemini-review.json `
  --dry-run
```

The real run requires `GEMINI_API_KEY` or `GOOGLE_API_KEY` in the process
environment. Credentials are never printed, placed in URLs, or written to
evidence. A response is review evidence only; Codex must adjudicate it.

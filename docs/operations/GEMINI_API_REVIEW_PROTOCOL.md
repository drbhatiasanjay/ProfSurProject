# Gemini API Review Protocol

## Request construction

1. Verify the candidate exists as a Git commit.
2. Read only the paths in `REVIEW_CONTEXT_MANIFEST.json` at that SHA.
3. Compute a deterministic snapshot hash and prompt hash.
4. Send the prompt over HTTPS using the provider SDK or an API-key header.
5. Never place a key in a URL, prompt, repository file, or log.

## Response validation

The adapter must require:

- candidate SHA matching the requested SHA;
- structured adjudication rows;
- evidence locations;
- risk and required-change fields;
- explicit final verdict;
- no credentials or secret-like values in the response.

Malformed or contradictory responses are `REVIEW_BLOCKED`, not a pass.

## Publication boundary

The API adapter writes a temporary response only. Codex must independently:

- inspect the response;
- scan it for secrets;
- confirm candidate ancestry and evidence scope;
- create any durable evidence file;
- commit and push through the canonical branch policy.

The adapter cannot authorize implementation, closure, or external publication.

## CLI alignment

Interactive Gemini CLI reviews should load `.gemini/reviewer-policy.md`, use
read-only plan mode, and follow the same manifest and output contract. CLI skills,
hooks, and MCP tools are optional safeguards; correctness must not depend on
their presence because API reviews do not inherit them.

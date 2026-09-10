# Independent Review Harness Specification

Status: design only; implementation requires separate approval

## Goal

Provide repeatable, low-intervention dispatch of a fresh Gemini or other
bounded-reviewer session without coupling reviewer credentials or state to the
ProfSur application.

## Required flow

`candidate SHA → isolated checkout → fresh prompt → bounded inspection → evidence bundle → secret scan/hash → reviewer branch → Codex adjudication`

## Non-negotiable controls

- Verify the candidate SHA before any review action.
- Use a detached worktree or dedicated reviewer branch.
- Expose only the repository URL, exact SHA, closure contract, and committed
  evidence locations.
- Permit read-only repository operations plus evidence-file creation only.
- Enforce command allowlists, timeouts, output limits, and no full-suite execution.
- Never pass API keys in URLs, prompts, repository files, logs, or evidence.
- Resolve provider credentials from the process environment or provider SDK
  credential chain; fail closed when absent.
- Scan evidence for secrets before publication.
- Record model/provider, prompt version, candidate SHA, commands, timestamps,
  exit codes, evidence paths, and hashes.
- Require explicit machine-readable verdicts and a human-independent context
  declaration.
- Do not allow reviewer output to execute commands or authorize repairs.

## Provider seam

The harness should expose one narrow interface:

`review(candidate_sha, prompt_path, evidence_dir) -> ReviewManifest`

Provider adapters may use Gemini, OpenRouter, or another approved service, but
the harness must not import provider-specific logic into ProfSur application
modules. The adapter returns text and metadata; the harness validates the
manifest and publication policy.

## Evidence manifest minimum

- candidate SHA and repository;
- reviewer context and independence declaration;
- provider/model identifier without credentials;
- prompt hash;
- commands executed and exit codes;
- verdict fields;
- source database before/after hash where relevant;
- screenshot/trace/log paths where relevant;
- SHA-256 for every committed evidence file;
- limitations and reproducibility notes.

## Context-efficiency policy

- Load the context pack and only the files named by the phase contract.
- Search before reading; use narrow file slices.
- Keep the prompt stable and versioned.
- Return structured verdicts instead of conversation transcripts.
- Persist only decisions, evidence, blockers, and next actions.

## Independence policy

The reviewer must have no implementation role or inherited development context.
The harness must reject a review when the reviewer identity, branch ancestry,
candidate SHA, or evidence-only scope cannot be verified.

## Implementation gate

Do not build this harness until a fresh adversarial review accepts this
specification and confirms the provider credential path. The existing
`scripts/gen_bulk_doc.py` is not a compliant implementation because it places a
Gemini key in a request URL; it must not be used as the security model for this
harness.

# Engineering playbook (portable)

**Purpose:** One **tool-agnostic** instruction set for AI coding agents (any model + any product). Treat this file as the **canonical source**. Mirror or excerpt it into each tool’s native location (see [Where to install](#where-to-install-by-tool)).

**How to stay DRY:** Prefer **one** canonical doc in-repo (this file or your org template), then either:

- **Copy** the “Universal rules” section into each tool’s format, or  
- **Keep short wrappers** in tool-specific files that say: “Follow `docs/ENGINEERING_PLAYBOOK.md` in this repository,” plus only tool-specific knobs (paths, secrets, MCP).

When tools do not auto-load files, **paste the “Minimal chat bootstrap”** block at the start of a session or add it to a saved prompt/workflow.

---

## Universal rules (Karpathy-style + production discipline)

### 1) Workflow

1. **Plan first** — Restate the goal, list files you expect to touch, and the smallest change that satisfies acceptance criteria **before** editing.
2. **Simplicity first** — Prefer the boring, obvious fix over new abstractions unless the task requires generalization.
3. **Surgical edits** — Smallest diff that works; no drive-by refactors, renames, or formatting sweeps outside the requested scope.
4. **Goal-driven verification** — After substantive changes, run the repo’s real **build / test / lint / typecheck** commands (from the [Repository profile](#repository-profile-template) below). Do not claim completion on failing commands.

### 2) Risk and blast radius (before editing)

For **database schema**, **migrations**, **SQL**, **auth/session**, **secrets**, **background jobs**, **webhooks**, **external APIs**, **ingestion**, or **infra**:

- Explicitly list **risks** (data loss, incorrect joins, idempotency, concurrency, PII leakage, rate limits, partial failure).
- List **affected surfaces** (callers, UI entry points, consumers of JSON/SQL shapes, deployment config, feature flags).

Do not start editing until this is stated briefly in the thread (or in the PR description).

### 3) UI work

- Reuse **existing components, layout, tokens, and patterns**.
- Do **not** restyle or restructure unrelated screens unless the task explicitly includes them.

### 4) Automation and workflows

For hooks, scripts, pipelines, agents, queues, cron, CI:

- Document **triggers**, **side effects** (writes, network, billing), **retries**, and **failure modes** (minimal, precise comments or PR text).

### 5) APIs and contracts

- Assume **backward compatibility** unless the task explicitly authorizes breaking changes.
- Prefer additive changes (optional fields, new endpoints, feature flags) over silent behavior changes.

### 6) Dependencies

- Avoid new dependencies unless necessary; justify cost, security, license, and maintenance.
- Pin versions per project conventions.

---

## Repository profile template

**Fill this in per repository** (keep it factual; agents should not invent commands).

| Item | Example (replace for your repo) |
|------|----------------------------------|
| **Stack** | Languages, frameworks, runtime versions |
| **Entry points** | e.g. `app.py`, `src/index.ts`, `cmd/server` |
| **Run (local)** | e.g. `streamlit run app.py` |
| **Build** | e.g. `docker compose build`, `npm run build` |
| **Test** | e.g. `python -m pytest tests/ -v --tb=short` |
| **Lint** | Command or `not configured` |
| **Typecheck** | Command or `not configured` |
| **CI** | Where the above are enforced (e.g. `.github/workflows/*.yml`) |
| **Secrets / env** | Which vars exist; never commit values |
| **Prod constraints** | Regions, DB modes, feature flags |

---

## Where to install (by tool)

Instructions differ by product and version. When in doubt, use the product’s **Rules / Instructions / Project context** UI and point it at this playbook or a wrapper file.

### Cursor

- **Project rules directory:** `.cursor/rules/`
- **Format:** Markdown with YAML **frontmatter** in `.mdc` files.
- **Always on:** `alwaysApply: true` in frontmatter.
- **Scoped:** `alwaysApply: false` and a `globs` pattern (string or brace list, depending on Cursor version).
- **Docs:** [Cursor — Rules](https://docs.cursor.com/context/rules-for-ai) (verify current field names in your Cursor version).
- **Practice:** Keep one `alwaysApply` rule for universal discipline; add small scoped rules for `frontend/`, `backend/`, etc., to save tokens.

### Claude (Claude Code, Claude in IDE, etc.)

- **Common project file:** `CLAUDE.md` at the repository root (many Claude Code setups auto-read it).
- **Local-only overrides:** `CLAUDE.local.md` (gitignored) for machine-specific paths or secrets **names** (not values in git).
- **Practice:** Put **stack + commands + repo layout** in `CLAUDE.md`; put **portable discipline** either inline or: “Obey `docs/ENGINEERING_PLAYBOOK.md`.”

### Google Antigravity

Per Google’s **Getting started with Antigravity** codelab:

- **Global rules file:** `~/.gemini/GEMINI.md`
- **Workspace rules directory:** `your-workspace/.agents/rules/` (create rule files here; you can also use the Antigravity UI **Rules → + Workspace** to generate/manage them).
- **Workspace workflows:** `your-workspace/.agents/workflows/` (on-demand prompts; not the same as always-on rules).
- **Workspace skills:** `your-workspace/.agents/skills/` for instruction-only skills (each skill in its own folder with `SKILL.md` per codelab).

**Practice:** Put universal discipline in a rule under `.agents/rules/` (e.g. `engineering-playbook.md`). Use **global** `GEMINI.md` only for preferences that should apply to every repo on that machine.

**Note:** Third-party articles sometimes mention `AGENTS.md`, project-root `GEMINI.md`, or `.antigravity` files. Treat those as **optional** unless your Antigravity version documents them; prefer the **Rules UI** and official paths above when they conflict.

### GitHub Copilot (VS Code / compatible hosts)

- **Optional project file:** `.github/copilot-instructions.md` (filename may vary by host; check Copilot settings for “instructions” or “custom instructions”).
- **Practice:** Short wrapper + link to this playbook.

### Generic / chat-only UIs (no project rules)

- Paste the **Minimal chat bootstrap** (below) into the system/developer/project field if the product supports it, or into message #1 of the session.

---

## Minimal chat bootstrap (copy-paste)

Use when a product does **not** load repo files automatically.

```text
You are a senior engineer on a production codebase.

Operating rules:
1) Plan first: restate goal, files to touch, smallest change before editing.
2) Simplicity and surgical diffs only; no unrelated refactors.
3) For schema/auth/external APIs/ingestion/infra: state risks + affected surfaces BEFORE editing.
4) UI: reuse existing components/patterns; do not redesign unrelated screens.
5) Automation: document triggers, side effects, retries, failure modes.
6) APIs: backward compatible unless explicitly allowed to break.
7) Verification: run the repo’s real build/test/lint/typecheck commands and fix failures before claiming done.
8) Dependencies: avoid unless necessary; pin and justify.

Repository profile (fill in): stack=…, run=…, test=…, lint=…, typecheck=…, ci=…
```

---

## Optional: cross-tool `AGENTS.md` (repo root)

Some teams add a **root** `AGENTS.md` that only contains:

- A **one-paragraph** project summary  
- **“Canonical playbook:** `docs/ENGINEERING_PLAYBOOK.md`”**  
- **Commands** copied from the filled [Repository profile](#repository-profile-template)

Tools that read `AGENTS.md` (when supported) then share one pointer without duplicating the full playbook. This is optional and depends on whether your stack standardizes on `AGENTS.md`.

---

## Keeping derivatives in sync

When you change this playbook:

1. Update **Cursor** `.mdc` rules if they duplicate content (or replace duplication with a short pointer + `@docs/ENGINEERING_PLAYBOOK.md` in chat when needed).  
2. Update **Antigravity** `.agents/rules/` copies or wrappers.  
3. Update **CLAUDE.md** command tables if they drift.  
4. Re-run **CI** locally before merging.

---

## Relationship to this repository’s Cursor rules

This project may also keep `.cursor/rules/*.mdc` for Cursor-native loading. Those files should **either** mirror the **Universal rules** section here **or** defer to this playbook to avoid contradictory guidance.

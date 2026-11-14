# Operational Directives & Learned Engineering Safeguards

## 1. Immutable Baseline Principle
- **Single Source of Truth:** The GitHub remote baseline (`origin/master` / baseline commit `6075708`) is the definitive authority.
- **Surgical Restorations Only:** Never rewrite or refactor working baseline mechanisms when debugging. Diagnose the exact failing line and make the minimal surgical fix.
- **Experimental Demarcation:** All non-baseline additions (blueprints, UI overhauls, exploratory harnesses) must remain in isolated experimental directories or clearly labeled as `[DESIGNED BUT NOT IMPLEMENTED]`.

## 2. Authentication & Data Sync Invariants
- **Full Trace Before Fixing:** Never assume an auth failure is due to simple password string mismatches. Trace the complete execution path:
  `Input -> secrets.toml -> bootstrap_legacy_users() -> SQLite DB constraints -> DB row lookup -> bcrypt.checkpw()`
- **SQLite Constraint Protection:** The `users` table in `capital_structure.db` enforces `UNIQUE(email)`. Every profile configured in `.streamlit/secrets.toml` **must have a distinct email address**. Duplicate emails silently abort the bootstrap loop, locking subsequent accounts out.
- **Native Hashing Requirement:** `auth.py` invokes Python's native `bcrypt.checkpw()`. Do not use mismatched high-level wrapper hashers that emit incompatible salt formats. Always generate hashes using:
  ```python
  import bcrypt
  bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12)).decode('utf-8')
  ```
- **MVP Fast-Testing Credential Reference:** For local testing and fast profile validation across `drbhatia`, `profsurkumar`, `skumar`, and `sbhatia`, the MVP/restricted test password is `Pass@123`.

## 3. Deterministic Validation Over Trial-and-Error
- **Fast CLI Verification First:** Before spinning up browser testing or guessing passwords through UI forms, execute deterministic 1-second Python checks:
  ```bash
  python -c "import sqlite3, bcrypt; ..."
  ```
- **Automate Repetitive Checks:** Never manually check ports or profiles one by one. Use scripts (`scripts/project_ops.py`) to automate auth linting and port cleanup.

## 4. Phase-Gated Design vs. Implementation
- **Design Before Code:** Visual redesigns (e.g. Apple HIG / Liquid Glass) must follow strict phase separation:
  1. Systematic research and token specification.
  2. Document in `implementation_plan.md` marked as `DESIGNED BUT NOT IMPLEMENTED`.
  3. Obtain explicit user confirmation before touching live CSS/Streamlit component trees.

## 5. Deployment Evidence Gate & Zero-Fabrication Directive
- **Deployment Status Invariant:** Never declare a deployment (Cloud Run / GCP / local server) "done" based solely on an HTTP health check (`/_stcore/health` returning 200). A 200 status code only confirms the container started, not that routes, pages, or new features are present and functioning.
- **Mandatory Visual Gate:** Verification strictly requires an authenticated browser session logging in with credentials, navigating directly to the specific page/component under test in the sidebar, and confirming UI rendering.
- **Anti-Fabrication Rule:** Under NO circumstances should screenshot file paths or completion assertions be output before the browser subagent has fully finished execution and the artifact image files are confirmed to exist on disk.

## 6. Adversarial Verification & Anti-Author-Bias Principles (Nov 2026)
- **Zero Dead Helpers:** Writing a new helper module is incomplete until production call graphs (`app.py`, `models/`, `pages/`) route through it. Testing a helper in isolation is not production evidence.
- **Adversarial Bypass Checks:** Always test that omitted hashes, invented IDs, and malformed inputs fail closed.
- **Strict Financial Value Presence:** In financial metrics, $0.0$, $0\%$, and $0$ are valid numbers distinct from absence (`None`). Never write `val or default` (e.g. `beta or 1.0`, `tax or 25.17`). Always check `if val is None:`.
- **Mathematical Inversion / Round-Trip Validation:** Solvers must be tested by plugging the solution back into the underlying valuation/DCF model to verify $|PV(g^*) - \text{Target}| \le 0.05\%$.
- **Transaction Rollback Testing via Fault-Injection:** Never use `conn.executescript()` inside SQLite transactions (it commits implicitly). Migration rollback tests must inject an error midway to prove clean rollback.
- **Corpus Authenticity:** Never substitute 3-page synthetic PDFs for official 500+ page regulatory corpora. Empty OCR pages must never be marked status `OK`.

## 7. The Adversarial Mindset Protocol: Before/After Design and Code
Author bias creates a blind spot where tests only validate what the author intended to build. The **Adversarial Mindset** enforces systematic falsification across the full engineering lifecycle:

### Phase 1: Pre-Design Threat Modeling (Before Design)
1. **Hostile Invariant Formulation:** Explicitly catalog all ways an interface can be misused, bypassed, or corrupted before designing classes or methods.
2. **Library Traps & Edge Behaviors:** Identify native driver idiosyncrasies (e.g., Python `sqlite3` auto-commit on `executescript()`, floating-point precision, `0.0` truthiness) before designing contracts.
3. **Fail-Closed Default:** Architect all capabilities, endpoints, and export buttons so that any missing token, unpersisted ID, or hash mismatch fails closed immediately.

### Phase 2: Pre-Code Adversarial Red-Teaming (Before Code / Red Phase)
1. **Author Negative Exploits First:** Write test cases that simulate malicious or malformed calls:
   - Forged or missing hashes (`snapshot_hash=None`).
   - Unpersisted IDs (`snapshot_id="nonexistent"`).
   - Strict zero boundaries ($0.0$, $0\%$, negative inputs).
   - Solver divergence triggers ($WACC \le g$).
   - Mid-migration exceptions (transaction rollback fault injection).
2. **Validate Test Teeth:** Assert that each negative test fails against the current codebase before writing implementation code.

### Phase 3: Post-Code Adversarial Self-Audit (After Code)
Before declaring any task or repair ready for review:
1. **Production Call-Graph Audit:** Verify that production callers (`app.py`, `pages/`, engine modules) import and execute new code. Zero dead helpers allowed.
2. **Bypass Immunity Verification:** Verify that direct service/export calls cannot bypass UI checks.
3. **Truthiness Audit:** Scan modified files for `val or default` in financial math; enforce `if val is None:`.
4. **Round-Trip Solver Inversion:** Verify that mathematical solver outputs invert cleanly back to the target valuation within documented tolerance ($\le 0.05\%$).
5. **Database Immutability & Atomicity:** Confirm `capital_structure.db` SHA-256 is intact; verify DDL transaction rollback via fault injection.
6. **Corpus & Visual Evidence Discipline:** Confirm that regulatory documents are complete and authentic (never blank OCR scans) and that UI changes are verified by live authenticated browser tests.

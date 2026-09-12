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

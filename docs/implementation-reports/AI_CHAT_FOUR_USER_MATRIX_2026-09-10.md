# AI Chat / Stata Studio Four-User Matrix

**Date:** 2026-09-10  
**Target:** canonical repository-root `app.py`, `http://localhost:8501/`  
**Harness:** `scratch/run_all_users_matrix.py`

## Result

**PASS — 4/4 users, both themes, Stata estimation completed.**

| User | Role | Stata Studio | Theme 1 | Theme 2 | Result |
|---|---|---|---|---|---|
| `profsurkumar` | researcher | passed | dark | light | PASS |
| `skumar` | researcher | passed | light | dark | PASS |
| `drbhatia` | admin | passed | light | dark | PASS |
| `sbhatia` | viewer | passed | light | dark | PASS |

## Scenario coverage

- Root login and authenticated sidebar rendering.
- Sidebar navigation to `Stata Studio`.
- Complex fixed-effects `xtreg` estimation.
- Terminal result card visibility.
- Theme toggle and result-card rendering in both themes.
- Separate browser context per user.

No password, hash, cookie, or session token is included in this report. The test
password was supplied to the process through an environment variable only.

## Acceptance note

This validates the current canonical shell and the four-user Stata Studio path.
The AI Assistant chat path still requires its own authenticated UI assertion in a
future matrix extension; the source mapping and direct-Stata persistence fix are
covered separately in `docs/operations/AI_CHAT_SCREEN_CODE_MAPPING.md`.

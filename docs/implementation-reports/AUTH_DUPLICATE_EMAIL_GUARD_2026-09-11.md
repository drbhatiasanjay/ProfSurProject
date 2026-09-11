# Auth Duplicate-Email Guard — 2026-09-11

## Result

**PASS for the bounded remediation.** `auth.bootstrap_legacy_users()` now
preflights configured records, normalizes email case and whitespace, rejects
duplicate addresses with `AuthValidationError`, and performs no database write
when configuration is ambiguous.

## Evidence

- Implementation: `auth.py` (`_validate_legacy_credentials` and bootstrap entry)
- Regression: `tests/test_auth.py`
- Direct check: duplicate normalized addresses rejected; `auth_users` row count
  remained zero.
- Static check: `py -3.12 -m py_compile auth.py tests/test_auth.py` — PASS
- Diff check: `git diff --check -- auth.py tests/test_auth.py` — PASS

The full `pytest` invocation was previously resource-blocked/stalled on this
Windows workspace; it is not represented as passing evidence. Credential
values and hashes were not printed or stored.

## Scope boundary

This closes the duplicate-email bootstrap defect only. It does not rotate
credentials, change bcrypt behavior, alter authorization policy, or validate
the external LLM sweep.

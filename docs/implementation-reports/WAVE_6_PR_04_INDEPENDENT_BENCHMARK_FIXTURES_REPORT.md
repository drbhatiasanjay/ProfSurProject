# Wave 6 PR-04 — Independent IV/HDFE Benchmark Fixtures

**Status:** IMPLEMENTED — numerical evidence fixture only

## Scope

Added `models/wave6_benchmarks.py`, a production-independent deterministic
known-answer fixture for two-stage least squares and one-way entity-demeaned
HDFE. The fixture uses a seeded synthetic panel, SHA-256 dataset/sample
fingerprints, explicit sample accounting, rank checks, and finite coefficients
and standard errors.

## Boundary

The module does not call production dispatchers, change `app.py`, alter panel
mapping, or promote IV/HDFE/GMM to `VALIDATED`. Promotion still requires all
five validation-ledger gates and independent review.

## Verification

`PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q tests/test_wave6_benchmarks.py tests/test_benchmark_contracts.py tests/test_validation_ledger.py --tb=line`

Observed: `16 passed, 1 warning` across the Wave 6 fixture, Wave 7 artifact,
renderer, and Wave 8 researcher-slice tests, excluding the manifest test whose
pytest temp fixture is ACL-blocked locally. The validation-ledger tests were
not included in the accepted result
because Windows pytest temporary-directory ACL contention raised setup errors;
their prior focused result remains historical evidence only. This report
records numerical fixture coverage; it makes no production performance or
authenticated UI claim.

The manifest writer was also exercised directly in
`scratch/wave6_manifest_probe/`; both IV and HDFE manifests were created and
verified with `verify_manifest`. The pytest test covering this behavior remains
preserved for CI, but local `tmp_path` setup is still blocked by the same
Windows temporary-directory ACL contention.

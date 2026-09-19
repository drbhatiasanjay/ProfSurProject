# Pilot 2 bounded test evidence extract

## Attribution

- Source artifact: `06_TARGETED_TEST_EVIDENCE.md`
- Local provenance: `C:\Users\hemas\Downloads\kaif-pilot-output\06_TARGETED_TEST_EVIDENCE.md`
- Reviewed ProfSur commit recorded by the audit: `fa97df7e1e6b43726c63590a47906d8ae8e5797d`
- Method: isolated pure-contract pytest run plus AST-extracted source probes; no product runtime or browser session.

## Results

- The audit inventory recorded 229 KAIF capability records, 19 ProfSur functional-flow records, and 40 designed golden scenarios. The scenarios were designed but not run end to end.
- Seven pure contract tests passed, with zero failures or skips, in 0.14 seconds. Repository conftest was bypassed because importing the database layer has persistent write side effects.
- Twelve statistical/UI source probes completed. One valid OLS coefficient matched `numpy.linalg.lstsq` with absolute error `8.881784197001252e-16` against a `1e-10` tolerance.
- The prior broader pytest command was interrupted before a result was available. It remains `BLOCKED` with pass/fail unknown and was not rerun.
- Service integration and authenticated browser testing were classified `NOT_TESTABLE_WITH_AVAILABLE_EVIDENCE`.

## Limitation

The passing tests establish only isolated contract behavior and one numerical comparison. The probes are not KAIF executable tooling and do not establish service, browser, deployment, or production behavior.

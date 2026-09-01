# Development Automation

## One-time setup

From the repository root on Windows:

```powershell
.\scripts\bootstrap.ps1 -InstallDependencies -InstallHooks
```

The dependency step creates `.venv` and installs the runtime plus test packages. The hook step configures Git to use `.githooks`.

## What runs automatically

- Every `git push` runs syntax checks, whitespace checks, and targeted tests for files changed in the pushed commit.
- Every push to `master` starts GitHub Actions. The complete Python and OCaml suites run before Cloud Run deployment.
- Newer pushes cancel obsolete in-progress workflows through the workflow concurrency group.

## Manual commands

```powershell
.\scripts\test_fast.ps1
.\scripts\ci_watch.ps1
```

`ci_watch.ps1` watches the newest `master` workflow and checks the Cloud Run health endpoint after a successful deployment. It requires an authenticated GitHub CLI (`gh auth login`).

---
phase: 08-cicd-pipeline
plan: "01"
subsystem: ci-cd
tags: [github-actions, cloud-run, pytest, gcp, ci-cd]

dependency-graph:
  requires: []
  provides:
    - GitHub Actions workflow (.github/workflows/deploy.yml)
    - Automated test gate before every Cloud Run deploy
  affects:
    - All future master pushes trigger CI automatically
    - Manual gcloud deploy commands are no longer needed

tech-stack:
  added:
    - github-actions/setup-python@v5
    - google-github-actions/auth@v2
    - google-github-actions/setup-gcloud@v2
  patterns:
    - needs-gated deploy (test must pass before deploy runs)
    - secret-per-environment (GCP_SA_KEY GitHub secret, never in code)
    - torch CPU-only wheel to avoid 2GB GPU download in CI

key-files:
  created:
    - .github/workflows/deploy.yml
  modified: []

decisions:
  - id: D1
    decision: "torch installed from CPU wheel URL before requirements.txt"
    rationale: "Matches Dockerfile pattern; avoids ~2GB GPU wheel that would time out the CI runner"
  - id: D2
    decision: "ENABLE_CMIE=false env var in test job"
    rationale: "Tests must run without secrets.toml in CI; CMIE is feature-flagged off by default"
  - id: D3
    decision: "deploy job if-condition: github.ref == refs/heads/master && github.event_name == push"
    rationale: "PRs run the test job (good feedback) but must NOT trigger a deploy — only merged commits ship"
  - id: D4
    decision: "google-github-actions/auth@v2 + credentials_json (service account key)"
    rationale: "Workload Identity Federation is more secure long-term but requires additional GCP setup; JSON key is the fastest unblocked path for v1.3"

metrics:
  duration: "5 minutes"
  completed: "2026-05-10"
---

# Phase 8 Plan 01: CI/CD Pipeline — GitHub Actions Workflow Summary

**One-liner:** GitHub Actions workflow with pytest (Python 3.11, torch CPU, ENABLE_CMIE=false) gating a Cloud Run deploy via GCP_SA_KEY secret.

## What Was Built

Task 1 (auto) is complete. `.github/workflows/deploy.yml` has been created and committed.

The existing draft in the repo was a minimal 4-step test-only stub (name: "Test", no deploy job, no --ignore flags, no ENABLE_CMIE). It has been replaced with the full two-job pipeline per the plan spec.

### Workflow structure

```
trigger: push/PR to master
│
├── job: test (always)
│   ├── checkout
│   ├── python 3.11 + pip cache
│   ├── torch (CPU wheel) + requirements.txt + pytest
│   └── pytest --ignore=smoke_auth.py --ignore=smoke_phase1.py -v --tb=short
│       env: ENABLE_CMIE=false
│
└── job: deploy (needs: test, master push only)
    ├── checkout
    ├── google-github-actions/auth@v2  ← credentials_json: ${{ secrets.GCP_SA_KEY }}
    ├── google-github-actions/setup-gcloud@v2
    └── gcloud run deploy lifecycle-leverage --source . --region us-east1 ...
```

### Artifact

- **Path:** `.github/workflows/deploy.yml`
- **Commit:** 2d68601
- **YAML valid:** confirmed via `py -3.12 -c "import yaml; yaml.safe_load(...)"`

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Replaced existing minimal stub with full spec**

- **Found during:** Task 1
- **Issue:** `.github/workflows/deploy.yml` already existed as a 26-line test-only stub named "Test" — missing the deploy job, `--ignore` flags, `ENABLE_CMIE` env var, and PR trigger.
- **Fix:** Overwrote with the complete 55-line two-job workflow per the plan spec.
- **Files modified:** `.github/workflows/deploy.yml`
- **Commit:** 2d68601

## Tasks Pending (Human Action Required)

### Task 2 — GCP Service Account Setup (human-action checkpoint)

The workflow references `${{ secrets.GCP_SA_KEY }}` which does not exist yet. Without it the deploy job will fail with an authentication error.

**Step A — Create the service account:**
1. Open https://console.cloud.google.com/iam-admin/serviceaccounts?project=tempproject-462219
2. Click **+ CREATE SERVICE ACCOUNT**
3. Name: `github-actions-deploy`
4. Assign these 4 roles:
   - Cloud Run Admin
   - Storage Admin
   - Cloud Build Editor
   - Service Account User
5. Click **DONE**

**Step B — Download the JSON key:**
1. Click the new SA → **KEYS** tab → **ADD KEY → Create new key → JSON**
2. Save the `.json` file (treat like a password)

**Step C — Add as GitHub secret:**
1. Open https://github.com/drbhatiasanjay/ProfSurProject/settings/secrets/actions
2. **New repository secret** → Name: `GCP_SA_KEY`
3. Value: paste the entire JSON key file contents
4. Click **Add secret**

**Step D — Enable required GCP APIs (one-time):**
```bash
gcloud services enable run.googleapis.com cloudbuild.googleapis.com containerregistry.googleapis.com --project=tempproject-462219
```

### Task 3 — Verify end-to-end workflow run (human-verify checkpoint)

After Task 2 is complete, push any commit to master and:
1. Open https://github.com/drbhatiasanjay/ProfSurProject/actions
2. Watch **"Test and Deploy"** workflow appear within ~30 seconds
3. **test job** should go green (3-5 min: torch install + pytest)
4. **deploy job** should start after test job and go green (3-5 min: Cloud Build)
5. Both jobs green = pipeline operational

**If test job fails:**
- Expand pytest step to see failing tests
- Known flakiness: TestPage15 in `tests/test_page_integration.py` — add `--ignore=tests/test_page_integration.py` if needed

**If deploy job fails with auth error:**
- Verify `GCP_SA_KEY` was pasted as complete JSON (no truncation)
- Verify the service account has all 4 IAM roles

## Next Phase Readiness

- Phase 8 Plan 01 (Task 1): COMPLETE
- Phase 8 Plan 01 (Tasks 2-3): PENDING — blocked on human GCP/GitHub setup steps
- No code blockers for other ongoing work

# Session Retrospective: March 27-28, 2026
## ProfSurProject — LifeCycle Leverage Dashboard

---

## 1. MISTAKES CLAUDE MADE (& How to Prevent Them)

### Mistake 1: `.gitignore` excluded `models/` directory
**What happened:** When creating `.gitignore` for deployment, I added `models/` to the ignore list (thinking it was ML model artifacts). It was actually the Python package with all econometric/ML code.
**Impact:** Streamlit Cloud couldn't import `from models.econometric import ...` — app crashed.
**Root cause:** Assumed "models/" meant saved model files, not source code.
**Prevention:**
- **Rule:** Never gitignore directories without reading their contents first.
- **Skill/Hook opportunity:** Pre-push validation hook that checks if any imported module is gitignored.

### Mistake 2: Wrong Python version pinning file
**What happened:** Created `runtime.txt` (Heroku format) instead of `.python-version` (Streamlit Cloud format). App kept deploying on Python 3.14 where ML packages have no wheels.
**Impact:** ImportError on Streamlit Cloud — app completely broken. Had to fix twice.
**Root cause:** Confused Heroku deployment convention with Streamlit Cloud convention.
**Prevention:**
- **Rule:** Always verify the deployment platform's config file format before creating it.
- **Skill opportunity:** Platform-specific deployment skill that knows the correct config for each host.

### Mistake 3: PyTorch as hard dependency
**What happened:** Added `torch` to requirements.txt. PyTorch is ~2GB and exceeds Streamlit Cloud's resource limits. Also no Python 3.14 wheels.
**Impact:** Deployment failed or was extremely slow.
**Root cause:** Didn't consider the deployment environment's constraints when adding dependencies.
**Prevention:**
- **Rule:** Heavy ML dependencies (torch, tensorflow) must always be optional imports with `try/except` and feature gating.
- **Hook opportunity:** Pre-commit hook that flags packages >100MB in requirements.txt.

### Mistake 4: Residual diagnostics scatter plot crash (FE/RE models)
**What happened:** `px.scatter(x=fitted_vals, y=resid_vals)` crashed because `linearmodels` returns a DataFrame for `fitted_values` (not a 1D array like statsmodels). `.values` on a DataFrame gives a 2D array.
**Impact:** Econometrics page crashed when using Fixed Effects or Random Effects.
**Root cause:** Assumed all model libraries return fitted values in the same shape.
**Prevention:**
- **Rule:** Always flatten model outputs with `np.asarray(x).flatten()` before plotting.
- **Skill opportunity:** Add to a "Plotly gotchas" reference skill.

### Mistake 5: Pushed code without verifying it runs on target platform
**What happened:** Multiple rounds of push → crash → fix → push. Never tested in a Streamlit Cloud-like environment first.
**Impact:** Live app was broken for extended periods. User had to report errors 3+ times.
**Root cause:** No pre-deployment validation step.
**Prevention:**
- **Rule:** Before pushing to production, always run `streamlit run app.py` locally and verify all pages load.
- **Hook opportunity:** Pre-push hook that runs a smoke test.

---

## 2. KEY LEARNINGS

### Deployment Learnings
| Platform | Python Version File | Max Size | Torch Support |
|----------|-------------------|----------|---------------|
| Streamlit Cloud | `.python-version` | ~1GB | No (too large) |
| Heroku | `runtime.txt` | 500MB slug | No |
| Google Cloud Run | `Dockerfile` | No limit | Yes (CPU) |
| Docker | `Dockerfile` | No limit | Yes |

### Architecture Learnings
- **Optional imports pattern:** Any package >50MB should use `try/except` + `HAS_X` flag
- **Model output shapes vary:** statsmodels returns Series, linearmodels returns DataFrame — always flatten
- **Streamlit session state:** Works reliably with `st.navigation()` — app.py always runs first
- **SQLite on Streamlit Cloud:** Works fine, ~5MB DB loads instantly

### Git/Deployment Learnings
- Always check `git status` AND `git diff --stat` before pushing
- Verify `.gitignore` doesn't exclude source code (read directories before ignoring)
- Pin Python version for every cloud deployment — never trust defaults
- Large dependencies need feature gating, not just lazy imports

---

## 3. RECOMMENDED SKILLS TO BUILD

### Skill 1: `streamlit-deploy`
**Trigger:** When user says "deploy", "push to production", "go live", or is working with Streamlit Cloud
**What it does:**
- Knows correct config files per platform (.python-version, runtime.txt, Dockerfile)
- Validates requirements.txt for oversized packages (torch, tensorflow)
- Checks .gitignore doesn't exclude imported modules
- Runs smoke test before push
- Handles the full git add → commit → push → verify cycle

### Skill 2: `pre-push-validator`
**Trigger:** Before any `git push` to a production branch
**What it does:**
- Scans all `from X import` / `import X` statements
- Verifies imported modules aren't in .gitignore
- Checks requirements.txt includes all imported packages
- Flags packages >100MB with a warning
- Verifies Python version pin exists for cloud deployments

### Skill 3: `plotly-data-guard`
**Trigger:** When creating Plotly charts with model outputs
**What it does:**
- Ensures all data passed to px.scatter/px.line/etc. is 1D
- Auto-flattens DataFrames and 2D arrays
- Validates x and y have matching lengths before plotting

---

## 4. RECOMMENDED HOOKS TO BUILD

### Hook 1: Pre-Push Import Validator
```json
{
  "event": "PreToolUse",
  "matcher": "Bash",
  "hooks": [{
    "command": "if echo '$TOOL_INPUT' | grep -q 'git push'; then python -c \"import ast, glob; [ast.parse(open(f).read()) for f in glob.glob('**/*.py', recursive=True)]\" 2>&1 | head -5; fi"
  }]
}
```
**Purpose:** Before any git push, verify all Python files parse correctly.

### Hook 2: Requirements Completeness Check
**Trigger:** After editing any .py file
**Purpose:** Compare `import` statements against `requirements.txt` and flag missing packages.

### Hook 3: Deployment Smoke Test
**Trigger:** Before `git push` on projects with `.streamlit/` directory
**Purpose:** Run `streamlit run app.py --server.headless=true` for 5 seconds to catch import errors.

---

## 5. CROSS-PROJECT PATTERNS

### Projects Analyzed
| Project | Stack | Deployment | Status |
|---------|-------|-----------|--------|
| **ProfSurProject** | Streamlit + Python + SQLite | Streamlit Cloud | Live |
| **LocalPulse (Sajaag)** | React 19 + TypeScript + Vite | TBD | Development |
| **WorldMonitor** | TypeScript + Vite + Tauri | Multi-variant | Development |
| **GeoStory** | FastAPI + React + GCP | Cloud Run | Development |

### Common Anti-Patterns Across Projects
1. **No pre-deploy validation** — All projects push and pray
2. **Dependency management** — requirements.txt/package.json not always in sync with actual imports
3. **Platform config confusion** — Different platforms use different config files
4. **Git hygiene** — .gitignore created hastily, sometimes excludes needed files

### Common Strengths
1. **Rich skill ecosystem** — 60+ skills available, well-organized vault
2. **MCP integration** — Obsidian, codebase-memory, Figma, Notion all connected
3. **GSD workflow** — Structured project management via /gsd commands
4. **Test coverage** — pytest for Python projects, Playwright for web

---

## 6. DEVELOPMENT VELOCITY STATS (March 27-28)

- **13 commits** in ~3 hours of active development
- **12 Streamlit pages** built (7 original + 5 ML)
- **6 model modules** created (econometric, ML, clustering, survival, timeseries, cache)
- **40 pytest tests** written
- **~4,000 lines** of production code
- **5 deployment bugs** found and fixed
- **3 times** user had to report the same class of error (deployment failures)

### Time Lost to Preventable Errors
- ~30 minutes on .gitignore excluding models/
- ~20 minutes on wrong Python version file
- ~15 minutes on torch dependency issues
- **Total: ~1 hour of the ~3 hour session** (33% waste)

---

## 7. ACTION ITEMS FOR NEXT SESSION

### Immediate
- [ ] Verify Streamlit Cloud app is running cleanly on all 12 pages
- [ ] Check Streamlit Cloud logs for any remaining errors
- [ ] Test the deployed app end-to-end

### Build These Assets
- [ ] Create `streamlit-deploy` skill (highest priority — prevents 3 of 5 errors)
- [ ] Create pre-push validation hook
- [ ] Add deployment smoke test to ProfSurProject CI

### Process Improvements
- [ ] Always run `streamlit run app.py` locally before pushing
- [ ] Always check .gitignore against import statements before first deploy
- [ ] Always verify platform-specific config file format (not assume)
- [ ] Heavy dependencies (>50MB) must be optional from day 1

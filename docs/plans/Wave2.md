# Wave 2 — LifeCycle Leverage Development Plan

**Created:** 2026-05-07  
**Status:** Planning — items marked 🔴 DISCUSS require design agreement before any code is written  
**Baseline:** Wave 1 complete — 18 pages, GCP Cloud Run revision 00038-np9, 344 tests, commit ef9b0bf  
**Author reference:** Full conversation analysis from 2026-05-07 session + competitive landscape review

---

## Table of Contents

1. [What Wave 2 Is Building On](#1-what-wave-2-is-building-on)
2. [Non-Negotiable Process Rules (Wave 1 lessons)](#2-non-negotiable-process-rules)
3. [Reusable Assets From Wave 1](#3-reusable-assets-from-wave-1)
4. [Wave 2 Backlog — Detailed Priority](#4-wave-2-backlog)
5. [Tooling and Accelerators](#5-tooling-and-accelerators)
6. [Architecture Decisions Required](#6-architecture-decisions-required)
7. [Items Requiring Discussion Before Development](#7-items-requiring-discussion)
8. [Success Criteria](#8-success-criteria)

---

## 1. What Wave 2 Is Building On

### Wave 1 Deliverables (complete)

| Layer | What was built |
|---|---|
| **Auth** | `streamlit-authenticator` login gate, 3 roles (admin / researcher / viewer), 7-day cookie, guest self-ID form |
| **Data** | SQLite with 4 panel vintages: thesis (2001-24), latest (+CMIE 2025), run3 (Stata replication), us_av_2024 (25 DJIA firms) |
| **Pages** | 18 pages: Dashboard, Peer Benchmarks, Scenarios, Bulk Upload, Data Explorer, Settings, Life Stage Dynamics, Econometrics Lab, ML Models, Forecasting, Clustering, Transitions, Advanced Econometrics, Workbench, Interaction Effects, Activity Log, Board Deck, Company Navigator |
| **UI** | Fixed two-row header (custom navbar + native Streamlit toolbar), light/dark theme, sidebar filters (panel, companies, year range, life stage, industry, events) |
| **Export** | Board Deck → PPTX (python-pptx + kaleido), pyvis ego graphs (HTML) |
| **Tests** | 344 pytest tests — DB, models, 7 CMIE suites, page integration, board export, CFO graph. Playwright smoke: smoke_phase1.py + smoke_auth.py |
| **Infra** | GCP Cloud Run (us-east1), Docker (Python 3.11-slim), `.gcloudignore` with secrets exception |

### What Wave 1 Left Unresolved

- No CI/CD pipeline — deploys are manual `gcloud run deploy`
- SQLite with `busy_timeout` workaround — not suitable for growing concurrent user base
- No API layer — 18 pages directly import `db.py` (tight coupling)
- No alerting, watchlists, or scheduled reports
- Most pages lack loading states, error states, and download buttons
- Panel radio is in sidebar — deferred move to navbar dropdown (see memory: `project_panel_selector_decision.md`)
- `>>` expand arrow left-positioning not explicitly set (relies on Streamlit default)
- US panel only 25 firms — too small for publishable international comparison

---

## 2. Non-Negotiable Process Rules

Every Wave 2 feature must follow these rules. Each was learned the hard way in Wave 1.

### Before writing any code

- [ ] **Draw the layout diagram first** (ASCII is fine) for any UI feature with fixed/sticky/overlapping elements. 5 iterations of navbar CSS could have been 1.
- [ ] **Use Plan Mode** for any task with ≥2 design decisions — not just backend features. Applies equally to CSS layout, DB schema changes, new page structure.
- [ ] **Check framework z-index values** before setting custom ones. Streamlit native elements are ~1000000; using 99999 loses silently.
- [ ] **Define acceptance criteria** before implementation. "It works" is not a criterion. For each feature: what does a passing smoke test look like?

### CSS / DOM rules (hard-won)

- **Never use `display:none` on a parent** that contains `position:fixed` children — it hides them unconditionally regardless of child CSS. Use repositioning instead.
- **Never use `:first-of-type` selectors** on Streamlit-generated DOM elements (`stHorizontalBlock`, `stVerticalBlock`). DOM order is not deterministic across render cycles. Use `id=` targeting on injected HTML instead.
- **Never use `z-index < 1000000`** for any element that must sit above Streamlit's native toolbar. The stack is: sidebar arrows `1000002` > custom navbar `1000001` > stHeader `1000000`.

### Streamlit-specific rules

- **`st.Page()` and `st.navigation()` are one atomic edit** — never create a page file without simultaneously adding it to the nav list. Silent routing failure is the result.
- **Every helpers.py function using `st.*` must do `import streamlit as st` inside the function** — module-level import breaks test compatibility (lazy import convention).
- **Never `page.goto()` more than once per Playwright session** — creates new WebSocket, races cookie re-validation. Log in once, use sidebar link clicks for all navigation.
- **Moving a sidebar widget = update every test that checks its previous location in the same commit.** Sign Out move broke `_is_authenticated()` in smoke_auth.py.

### Database / deployment rules

- **`INSERT OR REPLACE` for upserts** on any (username, page) keyed preference — handles first-save and re-save in one statement.
- **After any `ALTER TABLE`, drop and recreate all dependent SQLite views** — views are frozen definitions; schema changes make them invalid.
- **`.gcloudignore` must exist the same day secrets.toml is gitignored.** The `gcloud run deploy --source .` command respects `.gitignore` and silently excludes gitignored files from the Cloud Build tarball.
- **Never pin a performance constant to a specific hardware profile** (e.g., `timeout=1800` calibrated for GPU). Make it an env var with a documented assumption.

### Documentation rules

- **Commit → Obsidian Daily + Project note → Claude memory, same session.** Next session starts blind without them.
- **Any deferred decision must be recorded in memory with explicit "do NOT implement without go-ahead" note** — see panel selector decision as the model.

---

## 3. Reusable Assets From Wave 1

These exist in the codebase and carry forward to every Wave 2 feature. Read them before writing new code.

| Asset | Location | When to reuse |
|---|---|---|
| Two-row fixed header pattern | `app.py` lines 264–341 | Any layout change touching the header |
| JS proxy click (Streamlit widget from HTML) | `app.py` sign-out button | Any action in custom HTML that triggers a Streamlit widget |
| Vintage predicate | `db.py:_vintage_predicate()` | Every new DB query that must be panel-scoped |
| `ensure_session_state()` | `helpers.py` | Every new session state key (add here, not in page files) |
| Theme-aware Plotly dispatcher | `helpers.py:plotly_layout()` | Every new Plotly chart |
| `require_role()` with lazy import | `helpers.py` line ~626 | Every new page with access restrictions |
| `new_badge()` helper | `helpers.py` | Any UI element needing a NEW / BETA badge |
| Playwright auth smoke pattern | `tests/smoke_auth.py` | Any new Playwright test — copy login() + is_authenticated() + nav_to() |
| E2E class-per-page test structure | `tests/test_page_integration.py` | Every new page gets a test class here |
| `.gcloudignore` with secrets exception | `.gcloudignore` | Any new gitignored runtime file that Cloud Run needs |
| `PRAGMA busy_timeout=10000` | `db.py:_exec()` | Already in place — don't remove |
| `patch.dict(sys.modules, {"streamlit": fake_st})` | `tests/test_user_state.py` | Any new db function with local `import streamlit as st` |
| Guest self-ID form pattern | `app.py` lines 61-70 | Any new viewer-facing flow needing identity before access |
| Audit log + `_who()` resolver | `db.py`, `pages/16_admin_activity.py` | Any new user action worth recording |
| Per-user JSON prefs in SQLite | `db.py:save/load_user_pref()` | Any new per-user preference |
| Board Deck topic builder pattern | `models/board_export.py` | Any new "generate content for company X" feature |
| CFO graph builder pattern | `graph_builder.py` | Any new network/graph visualization |
| New Streamlit page checklist | Lessons doc | Run before every new page |

```
New Streamlit page checklist (mandatory):
□ Create pages/N_name.py
□ Add st.Page() in app.py
□ Add to st.navigation([...]) — SAME EDIT
□ If sensitive: require_role() at top of page
□ If in helpers.py: local import streamlit as st inside function
□ Add test class in test_page_integration.py
□ Add to Playwright smoke nav list
□ Add to Obsidian page inventory
```

---

## 4. Wave 2 Backlog

### Priority Tiers

- **Tier 1 — Quick Wins** (1–2 days each, no architecture changes needed)
- **Tier 2 — Medium Features** (3–10 days each, contained scope)
- **Tier 3 — Strategic** (architecture decision required first — see Section 6)
- 🔴 **DISCUSS** — needs design agreement or UI outline before any code

---

### Tier 1 — Quick Wins

#### W2-01 · Download button on every table and chart

**What:** Every `st.dataframe()` and every Plotly chart gets a "Download CSV" / "Download PNG" button below it.  
**Why:** Screener.in, Capital IQ, WRDS all offer this as baseline. Researchers routinely need to take data into Excel or paper.  
**How:**
```python
# CSV download (add below every st.dataframe call)
csv_bytes = df.to_csv(index=False).encode()
st.download_button("Download CSV", csv_bytes, "data.csv", "text/csv")

# PNG download (add below every st.plotly_chart call)
img_bytes = fig.to_image(format="png", scale=2)  # kaleido already installed
st.download_button("Download PNG", img_bytes, "chart.png", "image/png")
```
**Reuse:** `kaleido` already in requirements.txt for Board Deck.  
**Tests:** Add `assert "Download" in page.inner_text()` to each page's integration test.  
**Effort:** 1 day (systematic pass across all 18 pages).

---

#### W2-02 · Loading states on all data-heavy sections

**What:** Replace blank white flash on page load with `st.spinner("Loading data...")`. Add to every section that calls `db.*` outside a cache hit.  
**Why:** Current blank flash looks broken. Cloud Run cold starts add 3–5s delay.  
**How:**
```python
with st.spinner("Loading panel data..."):
    df = db.get_filtered_financials(filters)
```
**Effort:** 0.5 days (grep for all `db.get_*` calls not already inside a spinner).

---

#### W2-03 · Error states — no raw tracebacks

**What:** Wrap every `db.*` call in a `try/except` that shows `st.error()` with a human message instead of a Python traceback.  
**Why:** Tracebacks expose internal schema and are unusable to end users (researchers, Prof. Surendra Kumar).  
**Pattern:**
```python
try:
    df = db.get_filtered_financials(filters)
except Exception as e:
    st.error("Could not load data. Try refreshing. If this persists, contact the admin.")
    st.stop()
```
**Effort:** 0.5 days.

---

#### W2-04 · Progressive disclosure — advanced options in expanders

**What:** Move advanced options (GMM spec, CFO sign overrides, interaction term configuration, clustering parameters) into `st.expander("Advanced options", expanded=False)`.  
**Why:** Current pages show all controls upfront — cognitive overload for the 90% use case (reviewing charts, not tweaking specs).  
**Effort:** 1 day.

---

#### W2-05 · Chart default zoom = filtered year range

**What:** All time-series Plotly charts should default `xaxis.range` to the currently active year filter range, not the full data range.  
**How:**
```python
fig.update_xaxes(range=[year_range[0], year_range[1]])
```
**Reuse:** `plotly_layout()` in `helpers.py` — add `year_range` parameter and apply there centrally.  
**Effort:** 0.5 days.

---

#### W2-06 · Citation generator for published coefficients

**What:** On Econometrics, Scenarios, and Advanced Econometrics pages — button next to each coefficient table: "Copy Citation". Generates APA + LaTeX format.  
**Why:** Researchers presenting or writing papers need to cite these results. This is a key academic value-add no competing tool offers.  
**Example output:**
```
APA: β₁ = 0.32 (SE = 0.08, p < 0.01). OLS Fixed Effects, panel vintage: thesis (2001–2024), 
     401 firms, LifeCycle Leverage v1 [Dataset]. https://lifecycle-leverage-779655496440.us-east1.run.app

LaTeX: $\hat{\beta}_1 = 0.32^{***}$ (0.08), thesis vintage 2001--2024, $N=401$ firms.
```
**How:** `st.code()` block + `st.button("Copy")` using pyperclip or JS clipboard API.  
**Effort:** 1 day.

---

#### W2-07 · Fix `>>` expand arrow left-positioning

**What:** Currently the sidebar expand arrow (`>>`) relies on Streamlit's default `left` position. On some viewports it renders at `left:0` touching the browser edge. Add explicit `left: 0.5rem` to match the collapse arrow positioning.  
**How:** Add to the CSS block in `app.py`:
```css
button[data-testid="collapsedControl"] {
    left: 0.5rem !important;
    top: calc(112px + 0.5rem) !important;
    z-index: 1000002 !important;
}
```
**Effort:** 15 minutes. Do this in the next commit.

---

#### W2-08 · Panel selector → navbar dropdown

**What:** Move the Panel radio from the sidebar to the navbar as an HTML `<select>` dropdown.  
**Design:** Fully analyzed and approved. See memory: `project_panel_selector_decision.md`.  
**Implementation (Option A):**
- Navbar renders `<select>` pre-selected to current panel
- On change: `window.location.href = '?panel=<value>'` → full page reload
- `app.py` reads `st.query_params.get("panel", "latest")` at startup, writes to `session_state`
- Zero page-level changes — all 18 pages read `st.session_state.filters["panel_mode"]` unchanged
- `st.rerun()` already called on panel change today — full page reload is equivalent

**Why now:** Sidebar real estate recovered (~80px); dataset context always visible regardless of sidebar state; consistent with navbar-first UX direction.  
**Effort:** 1 day (including tests + smoke test update for `_is_authenticated` — sidebar no longer has panel radio).

---

### Tier 2 — Medium Features

#### W2-09 · GitHub Actions CI/CD pipeline

**What:** Push to `master` → run 344 pytest tests → if green, deploy to Cloud Run automatically.  
**Why:** Current deploys are manual, error-prone, and blocking. Every session ends with a `gcloud run deploy` command that the user must remember to run.

**Workflow file:** `.github/workflows/deploy.yml`
```yaml
name: Test and Deploy
on:
  push:
    branches: [master]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install -r requirements.txt
      - run: pytest tests/ -v --ignore=tests/smoke_auth.py --ignore=tests/smoke_phase1.py
  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: google-github-actions/auth@v2
        with: { credentials_json: ${{ secrets.GCP_SA_KEY }} }
      - uses: google-github-actions/deploy-cloudrun@v2
        with:
          service: lifecycle-leverage
          region: us-east1
          source: .
```
**Secrets needed in GitHub:** `GCP_SA_KEY` (service account JSON with Cloud Run deployer role).  
**OSS used:** `google-github-actions/auth`, `google-github-actions/deploy-cloudrun` (official GCP GitHub Actions).  
**Effort:** 1–2 days (setup + GCP service account creation + smoke test of the pipeline).

---

#### W2-10 · GCP Secret Manager for credentials

**What:** Move `secrets.toml` credentials into GCP Secret Manager. Cloud Run references them as env vars. Eliminate the `.gcloudignore` workaround.  
**Why:** `secrets.toml` + `.gcloudignore` is fragile — the exception rule is easy to accidentally remove. Secret Manager is the GCP-native approach.

**Migration:**
```bash
# Create secrets
gcloud secrets create lclev-cookie-key --data-file=- <<< "your-cookie-key"
gcloud secrets create lclev-credentials --data-file=credentials.json

# Cloud Run env var reference
gcloud run services update lifecycle-leverage \
  --set-secrets="COOKIE_KEY=lclev-cookie-key:latest,CREDENTIALS_JSON=lclev-credentials:latest"
```
**App change:** `app.py` reads `os.environ["COOKIE_KEY"]` instead of `st.secrets["cookie"]["key"]`.  
**Effort:** 1 day.

---

#### W2-11 · Saved views / bookmarks

**What:** User sets filters (Industry=IT, Stage=Mature, 2010–2020, Panel=thesis), clicks "Save View", names it "IT Maturity Study". View list appears at top of sidebar. One click restores all filters.  
**Storage:** `user_preferences` table (already exists) — save as `page="saved_views"`, `prefs_json={"views": [{"name": ..., "filters": ...}]}`.  
**UI:** Small bookmark icon + text input below sidebar filter divider.  
**Reuse:** `db.save_user_pref()` / `db.load_user_prefs()` — already implemented.  
**Effort:** 2 days.

---

#### W2-12 · Scenario comparison — overlay N scenarios

**What:** Scenarios page currently runs one OLS scenario and replaces results. Add: "Save Scenario" button → stores current spec + results. "Compare" view overlays saved scenarios on one chart (coefficient comparison bar chart, residual overlay).  
**Storage:** `user_model_runs` table (already exists from Wave 1 audit log).  
**UI:** 🔴 DISCUSS — needs wireframe for comparison chart layout before building. Possible: grouped bar chart by variable × scenario, or faceted small multiples.  
**Effort:** 3 days (2 implementation + 1 discussion/wireframe).

---

#### W2-13 · Company timeline view

**What:** For a selected company, render its full life-stage trajectory as a horizontal timeline (year on x-axis, stage on y-axis with color coding) with capital structure metrics (D/E ratio, leverage) overlaid as a line chart on secondary y-axis.  
**Why:** Dickinson methodology's core insight — stages are longitudinal, not cross-sectional. No existing page shows this clearly for a single company.  
**Existing data:** `get_filtered_financials()` + `get_life_stages()` — stage is available per company-year.  
**Placement:** New tab on Company Navigator (page 18) or new page 19.  
🔴 DISCUSS — placement decision (new tab vs new page) before building.  
**Effort:** 3 days.

---

#### W2-14 · Watchlist + stage-change email alerts

**What:** User marks companies as "watched". Nightly job checks if any watched company's life stage changed vs. prior period. If yes, send email summary.  
**Architecture:**
- New `user_watchlist` table in SQLite (or Postgres): `(username, company_code, added_at)`
- Cloud Scheduler triggers a Cloud Run Job (or Cloud Function) nightly
- Job runs `db.get_life_stage_changes(since=yesterday)`
- SendGrid (or Resend.com) sends email per user with changes

**OSS:**
- `sendgrid` or `resend` Python SDK for email
- GCP Cloud Scheduler (already available in tempproject-462219)
- `apscheduler` if running within the app instead of Cloud Scheduler

**UI:** Small bell icon on Company Navigator ego graph nodes + "My Watchlist" sidebar section.  
🔴 DISCUSS — notification channel (email only vs. in-app banner vs. both). Email requires sending domain setup.  
**Effort:** 5 days.

---

#### W2-15 · Custom peer groups

**What:** User defines a named peer set beyond the industry/stage defaults (e.g., "PSU Manufacturing", "High-leverage Decline firms"). Peer set is reusable across Peer Benchmarks, Board Deck, and Company Navigator.  
**Storage:** `user_preferences` with `page="peer_groups"`, `prefs_json={"groups": [{"name": ..., "company_codes": [...]}]}`.  
**UI:** 🔴 DISCUSS — where does the user build the group? Options: (a) new sub-tab on Data Explorer, (b) inline in Peer Benchmarks sidebar, (c) dedicated page. Decision needed before building.  
**Effort:** 3 days.

---

#### W2-16 · Chart annotation layer

**What:** Researcher can click a point on a time-series chart, type a note, save it. Annotations persist per user per chart. Shown as vertical lines + tooltip on subsequent views.  
**OSS:** `streamlit-plotly-events` (already installed) for click capture → get `x` value → show text input → save annotation.  
**Storage:** New `chart_annotations` SQLite table: `(username, chart_id, x_value, note, created_at)`.  
**Reuse:** `audit_log` table pattern from Wave 1 for the DB layer.  
🔴 DISCUSS — are annotations per-user or shared/collaborative? If shared, needs moderation. Agree on scope before building.  
**Effort:** 3 days.

---

#### W2-17 · Reproducibility audit trail export

**What:** On Econometrics, ML, Scenarios, Advanced Econometrics pages — "Export Audit Trail" button. Downloads JSON containing: panel vintage, year range, filters applied, model spec (variables, estimator), timestamp, user.  
**Why:** Academic reproducibility requirement. WRDS has this; we don't.  
**Example output:**
```json
{
  "generated": "2026-05-07T14:32:00Z",
  "user": "sbhatia",
  "panel": "thesis",
  "year_range": [2001, 2024],
  "filters": {"life_stages": ["Mature"], "industry_groups": ["Manufacturing"]},
  "model": {"estimator": "FE", "dep_var": "leverage", "indep_vars": ["profitability", "tangibility", "size"]},
  "n_obs": 3241,
  "n_firms": 189
}
```
**Effort:** 1 day (all data already available in session state).

---

### Tier 3 — Strategic (Architecture Decision Required First)

#### W2-18 · PostgreSQL on Cloud SQL

**Why:** SQLite with `busy_timeout` workaround is not production-grade for a multi-user app with concurrent write sessions. Cloud Run auto-scales to multiple instances; SQLite on a single file cannot handle concurrent writes cleanly.  
**Migration path:**
1. `alembic` for schema migration management (replacing raw SQL scripts)
2. `asyncpg` or `psycopg2` connection pool
3. All `db.py` queries port without logic changes (standard SQL)
4. Cloud SQL (PostgreSQL 15) in same region (us-east1) as Cloud Run
**OSS:** `alembic`, `psycopg2-binary`, GCP Cloud SQL Auth Proxy  
🔴 DISCUSS — cost impact (Cloud SQL ~$15-30/month vs. SQLite $0). Acceptable for production?  
**Effort:** 5–7 days (migration + test suite update + Cloud SQL provisioning).

---

#### W2-19 · FastAPI backend layer

**Why:** 18 pages directly import `db.py`. This means: (a) impossible to test pages without the DB, (b) no API for external consumers (Excel plugin, future mobile), (c) no request-level auth or rate limiting.  
**Architecture:**
```
Streamlit pages → FastAPI (/api/v1/*) → db.py → SQLite / PostgreSQL
```
**Benefit:** Board Deck and Company Navigator are already "individual company" tools — they could serve data to a future React/Next.js frontend without any backend changes.  
🔴 DISCUSS — is there an API consumer today (Excel, external scripts)? If not, defer until PostgreSQL migration is underway (they pair naturally).  
**Effort:** 7–10 days (full port).

---

#### W2-20 · Full US S&P 500 panel

**Why:** Current `us_av_2024` has 25 DJIA firms via Alpha Vantage — too small for any publishable US comparison. A full S&P 500 panel (500 firms × 20 years) would enable an India-US life-stage comparison chapter.  
**Data sources:**
- **WRDS / Compustat** — academic license, complete US fundamentals, Dickinson CFO signs available directly. Best option if university access exists.
- **SimFin** — free tier covers 2000+ US companies, annual data, good API. `simfin` Python package.
- **yfinance** — free, covers cash flow statements (needed for Dickinson CFO-sign classification), 500+ firms feasible.

🔴 DISCUSS — does Prof. Surendra Kumar have WRDS access through University of Delhi? This changes the data source decision entirely.  
**Effort:** 5 days (data acquisition + normalization into `us_av_2024` vintage + new panel label).

---

#### W2-21 · Mobile-responsive UI

**Why:** Streamlit's layout is desktop-only. For seminar use, conference demos, and broader academic sharing, mobile access matters.  
**Options:**
- A: Streamlit custom components (limited — sidebar still collapses poorly on mobile)
- B: Separate React/Next.js thin client consuming FastAPI backend (requires W2-19 first)
- C: Streamlit + `streamlit-extras` responsive helpers (partial fix)

🔴 DISCUSS — is mobile access a real user requirement for Prof. Kumar's use case? Defer if not. If yes, requires W2-19 (FastAPI) as a prerequisite.  
**Effort:** 10+ days if full (requires W2-19).

---

#### W2-22 · Redis caching layer

**Why:** `@st.cache_data` is in-process — dies on Cloud Run instance restart and cold start. Multiple concurrent users each get their own cache, causing redundant DB queries.  
**OSS:** GCP Memorystore (managed Redis), `redis-py`  
**How:** Replace `@st.cache_data` with a Redis-backed decorator for the 5 heaviest queries (`get_filtered_financials`, `get_industry_groups`, `get_year_range`, company graph builds).  
🔴 DISCUSS — cost (~$30/month for Memorystore basic). Worth it at current user volume?  
**Effort:** 3 days (once Redis is provisioned).

---

## 5. Tooling and Accelerators

### Claude Code Skills

| Skill | When to use | How to get |
|---|---|---|
| `/gsd:plan-phase` | Before starting any Wave 2 tier — generates a phased plan with research + task breakdown | Built into Claude Code GSD system |
| `/gsd:debug` | For any bug that survives one hour of investigation | Built in |
| `/ultrareview` | After completing a tier before deploying — full multi-agent PR review | `/ultrareview` in CLI |
| `/tdd` | For every new model function (W2-14 nightly job, W2-18 FastAPI endpoints) | `~/.claude/skills/` |
| `/diagnose` | Before trying random fixes on any hard bug | `~/.claude/skills/` |

### Claude Code Hooks (set up before Wave 2 starts)

**Pre-commit hook** — run tests before any commit:
```json
// .claude/settings.json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "Bash",
      "hooks": [{
        "type": "command",
        "command": "if echo \"$CLAUDE_TOOL_INPUT\" | grep -q 'git commit'; then py -3.12 -m pytest tests/ -x -q; fi"
      }]
    }]
  }
}
```

**Post-page-creation hook** — remind about navigation registration:
```json
{
  "hooks": {
    "PostToolUse": [{
      "matcher": "Write",
      "hooks": [{
        "type": "command",
        "command": "if echo \"$CLAUDE_TOOL_INPUT\" | grep -q 'pages/'; then echo 'REMINDER: Add st.Page() + st.navigation() entry in app.py'; fi"
      }]
    }]
  }
}
```

### OSS Libraries

| Library | Replaces / enhances | Feature | Install |
|---|---|---|---|
| `streamlit-aggrid` | `st.dataframe()` | Sortable, filterable, paginated tables with inline download. Much better for Data Explorer and Company Navigator peer tables. | `pip install streamlit-aggrid` |
| `streamlit-extras` | Native Streamlit widgets | `switch_page()`, `metric_cards`, `stoggle`, `keyboard` shortcuts | `pip install streamlit-extras` |
| `loguru` | `print()` / bare logging | Structured JSON logging to Cloud Logging. One-liner setup. | `pip install loguru` |
| `alembic` | Raw SQL migration scripts | Versioned DB migrations with `alembic upgrade head`. Works with both SQLite and PostgreSQL. | `pip install alembic` |
| `sendgrid` or `resend` | None (no email today) | Email alerts for W2-14 watchlist notifications | `pip install sendgrid` |
| `simfin` | Alpha Vantage (W2-20) | Free US company fundamentals for S&P 500 panel | `pip install simfin` |
| `openpyxl` | `df.to_csv()` | Excel export with formatting, multiple sheets, charts | `pip install openpyxl` (already in many envs) |
| `pre-commit` | Manual checks | Git hook: run `black`, `ruff`, `pytest -x` before every commit locally | `pip install pre-commit` |

### GitHub Repos Worth Referencing

| Repo | What to borrow |
|---|---|
| `google-github-actions/deploy-cloudrun` | Official GCP Cloud Run GitHub Action — copy the workflow template directly |
| `streamlit/streamlit` | DOM structure reference — check `data-testid` attribute names before writing CSS selectors (they change between versions) |
| `PablocFonseca/streamlit-aggrid` | AgGrid examples for financial data tables — see `examples/` for sortable + downloadable patterns |
| `simonw/datasette` | Reference for reproducibility audit trail JSON format — DataSette's metadata.json is a good model |
| `tiangolo/fastapi` | If W2-19 is approved — use FastAPI's `app/routers/` pattern, not a single `main.py` |
| `alembic/alembic` | Migration script templates — `alembic init` generates the boilerplate for W2-18 |

### GCP Services Already Available (tempproject-462219)

| Service | Used for |
|---|---|
| Cloud Run | App hosting (current) |
| Cloud Build | Source-based deploys (current) |
| Cloud Scheduler | Nightly watchlist job (W2-14) |
| Cloud SQL | PostgreSQL (W2-18, if approved) |
| Memorystore | Redis caching (W2-22, if approved) |
| Secret Manager | Credentials (W2-10) |
| Cloud Logging | Structured log sink |

---

## 6. Architecture Decisions Required

These decisions gate multiple Tier 3 items. Decide before starting those tiers.

### Decision A — Database: keep SQLite or migrate to PostgreSQL?

| Factor | SQLite (keep) | PostgreSQL (Cloud SQL) |
|---|---|---|
| Cost | $0 | ~$15–30/month |
| Concurrent writes | `busy_timeout` workaround, adequate at <10 users | Native MVCC, handles 100+ concurrent |
| Backups | Manual | Automated daily |
| Migrations | Raw SQL scripts | `alembic` |
| When to migrate | Never (small team, thesis tool) | When user base grows or watchlist jobs add concurrent writes |
| **Recommendation** | Keep SQLite for now, build `alembic` migration framework so the switch is a 1-day task when needed |

### Decision B — API layer: FastAPI or keep Streamlit-only?

| Factor | Streamlit-only | FastAPI backend |
|---|---|---|
| Development speed | Fast (existing pattern) | 7–10 days to port |
| Testability | Pages need full Streamlit session | Endpoints unit-testable with `httpx` |
| Future consumers | None today | Excel plugin, mobile, external scripts |
| **Recommendation** | Defer until a real external consumer exists. Add FastAPI if W2-20 (US panel) attracts external research partners who want API access. |

### Decision C — Notification channel for watchlist alerts (W2-14)

Options: email only / in-app banner only / both  
🔴 **Requires user input** — email delivery needs a sending domain. Does the project have one? Options: SendGrid free tier (100/day), Resend.com (3000/month free), or Gmail SMTP (limited).

### Decision D — Mobile UI (W2-21)

Is mobile access a real requirement for the current user base (Prof. Kumar + sbhatia + skumar + guest viewers)?  
If no → defer indefinitely.  
If yes → requires FastAPI (Decision B) as prerequisite + React/Next.js frontend work.  
🔴 **Requires user input.**

---

## 7. Items Requiring Discussion

Every item marked 🔴 DISCUSS must have a design decision recorded before any code is written. This is the direct lesson from the 5-cycle navbar CSS iteration — ambiguity is the enemy.

| Item | What needs to be decided | Where to record the decision |
|---|---|---|
| **W2-12 Scenario comparison UI** | What does the comparison chart look like? Grouped bars by variable? Faceted multiples? Side-by-side table? **Needs wireframe or ASCII sketch.** | `docs/plans/wave2_scenario_comparison_ui.md` |
| **W2-13 Company timeline placement** | New tab on Company Navigator (page 18) or new page 19? Impacts nav registration, role gating, test structure. | `docs/plans/wave2_company_timeline_placement.md` |
| **W2-14 Notification channel** | Email (which sender service?), in-app, or both? Domain setup required for email. | `docs/plans/wave2_watchlist_notifications.md` |
| **W2-15 Custom peer group UI** | Where does the user build the group? Sub-tab on Data Explorer / inline on Peer Benchmarks / dedicated page? | `docs/plans/wave2_peer_group_ui.md` |
| **W2-16 Annotation sharing scope** | Per-user private annotations or shared/visible to all? Shared requires moderation decision. | `docs/plans/wave2_annotations_scope.md` |
| **W2-18 PostgreSQL migration** | Cost acceptable? When to migrate (now vs. trigger condition)? | Architecture decision log in this file (Section 6A) |
| **W2-19 FastAPI layer** | Real external API consumer today? If not, defer. | Architecture decision log in this file (Section 6B) |
| **W2-20 US S&P 500 panel** | Does Prof. Kumar have WRDS access through University of Delhi? This determines data source (WRDS vs. SimFin vs. yfinance). | `docs/plans/wave2_us_panel_datasource.md` |
| **W2-21 Mobile UI** | Is mobile a real user requirement for the current 3-role user base? | Architecture decision log in this file (Section 6D) |
| **W2-22 Redis caching** | ~$30/month cost acceptable at current volume? | Architecture decision log in this file |

---

## 8. Success Criteria

Wave 2 is complete when all Tier 1 items are shipped and at least 3 Tier 2 items are deployed to production.

### Tier 1 definition of done (all 8 items)
- [ ] Every `st.dataframe()` and Plotly chart has a download button
- [ ] Every data-loading section shows `st.spinner()`
- [ ] No raw Python tracebacks on page load failures
- [ ] Advanced options in `st.expander()` on Econometrics, ML, Clustering, Advanced Econometrics, Interaction Effects
- [ ] All time-series charts default to the active year filter range
- [ ] Citation generator on Econometrics, Scenarios, Advanced Econometrics
- [ ] `>>` expand arrow left-positioned at `0.5rem`
- [ ] Panel selector in navbar dropdown (W2-08)

### Tier 2 minimum bar (3 of 7)
- [ ] GitHub Actions CI/CD pipeline live — every push deploys automatically
- [ ] GCP Secret Manager — `secrets.toml` workaround eliminated
- [ ] At least one of: Saved Views / Scenario Comparison / Company Timeline shipped

### Quality gates (all tiers)
- [ ] 344+ tests still passing (no regression)
- [ ] Playwright smoke tests updated to reflect any moved widgets
- [ ] Obsidian session log + Claude memory updated same day as each deploy
- [ ] No feature deployed without its checklist item ticked (from Section 3)

---

## Appendix — Competitive Feature Comparison

| Feature | Screener.in | Capital IQ | WRDS | Tijori Finance | **LifeCycle Leverage Wave 1** | **Wave 2 target** |
|---|---|---|---|---|---|---|
| Life-stage classification (Dickinson) | ✗ | ✗ | Raw data only | ✗ | ✓ (India + US) | ✓ |
| Thesis reproducibility pins | ✗ | ✗ | ✗ | ✗ | ✓ | ✓ |
| Panel vintage management | ✗ | ✗ | ✓ (snapshots) | ✗ | ✓ | ✓ |
| Download CSV/PNG | ✓ | ✓ | ✓ | ✓ | Partial | ✓ W2-01 |
| Saved views / bookmarks | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ W2-11 |
| Watchlist + alerts | ✓ | ✓ | ✗ | ✓ | ✗ | ✓ W2-14 |
| Chart annotation | ✗ | ✓ | ✗ | ✗ | ✗ | ✓ W2-16 |
| Citation generator | ✗ | ✗ | Partial | ✗ | ✗ | ✓ W2-06 |
| Reproducibility audit trail | ✗ | ✗ | ✓ | ✗ | ✗ | ✓ W2-17 |
| Custom peer groups | ✗ | ✓ | ✗ | ✗ | ✗ | ✓ W2-15 |
| Company timeline view | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ W2-13 |
| API access | ✗ | ✓ (paid) | ✓ | ✗ | ✗ | 🔴 W2-19 |
| Mobile responsive | ✓ | Partial | ✗ | ✓ | ✗ | 🔴 W2-21 |
| Excel export / add-in | ✓ | ✓ | ✓ | ✗ | Board Deck PPTX only | W2-01 partial |
| Multi-country data | Global | Global | Global | India | India + 25 US | 🔴 W2-20 |

**Unique to LifeCycle Leverage that no competitor has:**
- Dickinson CFO-sign life-stage applied systematically across an entire country panel
- Thesis reproducibility pins with frozen vintage coefficients
- Workbench for user-defined regressions on the same panel used in publications
- Board Deck PPTX generation per company
- Company Navigator ego graph with life-stage-aware peer clustering

---

*Last updated: 2026-05-07 · Next review: before starting Tier 1 sprint*

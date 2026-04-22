# Option B: GitHub fork / separate repo (CMIE lab)

This document matches the isolation plan: **upstream** (this repo’s default deploy) stays stable; **CMIE integration** matures in a **fork** until you merge stable pieces back.

## 1. Create the fork on GitHub

1. Open the repository on GitHub → **Fork** (into your org or user).
2. Clone the fork to a **second directory** (keep your original clone for production fixes):

   ```bash
   git clone https://github.com/YOUR_ACCOUNT/ProfSurProject-fork.git
   cd ProfSurProject-fork
   ```

## 2. Add `upstream` remote (fork clone)

```bash
git remote add upstream https://github.com/ORIGINAL_OWNER/ProfSurProject.git
git fetch upstream
```

Stay current with the thesis app:

```bash
git checkout main
git merge upstream/main
# resolve conflicts; run tests; push to origin
```

## 3. Turn on CMIE only in the fork

Default **production parity** (no CMIE UI, SQLite-only data paths) is enforced when **`ENABLE_CMIE` is off**.

In the **fork** (local + Cloud Run), enable the lab:

| Where | Setting |
|--------|--------|
| Local | `set ENABLE_CMIE=true` (Windows) or `export ENABLE_CMIE=true` (Unix) before `streamlit run app.py` |
| Streamlit Cloud / secrets | `ENABLE_CMIE = "true"` in `.streamlit/secrets.toml` or host secrets |
| Cloud Run | Add env var `ENABLE_CMIE=true` on the **fork’s** service only |

Optional CMIE key (fork only): `CMIE_API_KEY` in secrets or env.

## 4. Deploy fork separately (Cloud Run)

Use a **different service name** and **different secrets** from production, for example:

- Service: `lifecycle-leverage-cmie-lab` (example)
- Env: `ENABLE_CMIE=true`, `CMIE_API_KEY=…`
- Prefer a **separate SQLite file** or object-store path for lab imports so you never overwrite production `capital_structure.db`.

Production (upstream) should **not** set `ENABLE_CMIE` (or set it explicitly to `false`).

## 5. CLI import (either clone)

Offline / long jobs without keeping the browser open:

```bash
python -m cmie import-zip path\to\response.zip --company-code 12345
```

Merge **several** CMIE zips into **one** dashboard version (e.g. after batch downloads):

```bash
python -m cmie merge-zips z1.zip z2.zip z3.zip --min-years 1
```

Download up to **10** zips from one JSON **template** (must contain `__CMIE_COMPANY_CODE__`):

```bash
python -m cmie batch-download --codes "100001,100002" --payload-json-file tpl.json --out-dir ./cmie_zips
python -m cmie merge-zips ./cmie_zips/*.zip
```

Run from the project root that contains `capital_structure.db` you intend to update.

## 6. Merge-back policy (fork → upstream)

Open **small PRs** from fork to upstream only for:

- Hardened modules (e.g. `cmie/client.py`, `cmie/zip_parse.py`, tests)
- Docs such as this file

Avoid merging half-finished sidebar or payload mapping until **one-company E2E** is verified in the fork deploy.

## 7. Belt-and-suspenders in code

- [`db.is_cmie_lab_enabled()`](db.py): gates `get_active_financials` / `get_active_life_stage_summary`.
- [`app.py`](app.py): renders [`cmie/streamlit_import.render_cmie_sidebar_block`](cmie/streamlit_import.py) only when the flag is on.
- [`pages/5_data_explorer.py`](pages/5_data_explorer.py): CMIE branch only if the flag is on.

Even if `session_state.data_source_mode` were tampered with, **upstream** stays on SQLite when `ENABLE_CMIE` is off.

## 8. Econometrics / ML panel + CMIE HTTP variants (dev)

- **Panel for models:** pages use [`db.get_active_panel_data`](db.py) (same columns as `get_panel_data`; CMIE rows join `financials` only for optional `interest` / `int_rate` fields when that row exists in the packaged DB).
- **`query.php` form JSON → table:** [`cmie.query_form.cmie_tabular_json_to_dataframe`](cmie/query_form.py) plus [`CmieClient.post_query_form`](cmie/client.py) (form POST, JSON body).
- **Company ZIP:** [`CmieClient.download_wapicall_zip`](cmie/client.py) posts to `sr.php?kall=wapicall` (verify URL/HTTPS with CMIE for your account).

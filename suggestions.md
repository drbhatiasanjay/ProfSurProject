# Development Gap Analysis & Suggestions

## 1. Summary

The current app has a solid MVP analytics layer: Streamlit UI + SQLite data backend + keyed filters + lifecycle metrics. The codebase is usable but not yet production-hardened. The next priority should be reliability, test coverage, and richer analytic layers.

## 2. Functional gaps to fix

- Add error handling for DB calls in `db.py` and page functions (try/catch with user-friendly messages).
- Secure query parameters and sanitize inputs against possible injection or malformed filter lists.
- Add role-based access / auth, so only authorized analysts can use sensitive financial data.
- Add export options (CSV/Excel/PDF) in dashboard and data explorer.
- Add persistence for user filter state (e.g., saved views or bookmarks).
- Add scenario modeling with user-managed profiles and predictive output.
- Add data validation checks in bulk upload (schema, duplicates, transaction rollback).

## 3. Technical gaps to fix

- No tests: add unit tests for `helpers.classify_life_stage`, `_build_where()` and KPI calculations.
- No CI config; add `pytest`, `ruff`, `black`, and pre-commit.
- No robust logging and telemetry in `db.py` and page controllers.
- Caching key and spotty mutability: stabilize with sorted inputs and canonical tuple keys.
- Single-thread SQLite connection and no pooling: for production use a proper DB or connection pool.

## 4. Enhancement opportunities

- Precompute aggregated metrics and event impacts in DB materialized tables for performance.
- Add full-text search on company names and smart similarity search.
- Add narrative insights (auto-highlight unusual leverage changes, sector outliers, stage pop/growth).
- Add user collaboration (comments, shared views, report snapshots).

## 5. Prioritized quick wins

1. Error handling + safe query path.
2. Add tests for classification and SQL assembler.
3. Add button-backed CSV export in dashboard.
4. Add one new advanced metric (debt coverage ratio) and update UI.

## 6. Technical debt notes

- `app.py` directly manipulates session state; decouple into `state.py`.
- `pages/*.py` share duplicated calculations; abstract common dashboard utilities.
- Use type hints, structured settings, and `config.py`.

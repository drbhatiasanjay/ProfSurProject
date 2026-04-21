"""
Stage-1 query.php probe — end-to-end POC for the indicator-JSON transport.

Companion to scripts/cmie_stage1_reliance_diagnostic.py (wapicall variant).
Exercises the *existing* cmie/ package end-to-end without modifying it:

  request  → cmie.client.CmieClient.post_query_form   (form-encoded POST)
  parse    → cmie.query_form.cmie_tabular_json_to_dataframe   (head + data)
  schema   → cmie.normalize.CANONICAL_COLUMNS   (drift detection — read-only)

Does NOT modify cmie/, db.py, pages/*, models/*, or any UI.
Does NOT write to capital_structure.db.
Writes only to cmie_validation/queryphp_<timestamp>/ (gitignored).

Defaults come from CMIE's own ?section=example_php documentation page:
  scheme=MITS  indicnum=12692320  freq=A  nperiod=1

Usage:
  py -3.12 scripts/cmie_stage1_queryphp_probe.py
  py -3.12 scripts/cmie_stage1_queryphp_probe.py --indicnum 15551706 --freq Q --nperiod 4
  py -3.12 scripts/cmie_stage1_queryphp_probe.py --scheme MITS --indicnum 12692320,15551706
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import sys
import tomllib
from pathlib import Path
from typing import Any

# Make the cmie package importable when run from repo root
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import pandas as pd  # noqa: E402

from cmie.client import CmieClient  # noqa: E402
from cmie.errors import CmieError, CmieParseError  # noqa: E402
from cmie.normalize import CANONICAL_COLUMNS  # noqa: E402
from cmie.query_form import cmie_tabular_json_to_dataframe  # noqa: E402

SECRETS_PATH = Path(".streamlit/secrets.toml")

# From CMIE's ?section=example_php doc page (single minimal request)
DEFAULT_SCHEME = "MITS"
DEFAULT_INDICNUM = "12692320"
DEFAULT_FREQ = "A"
DEFAULT_NPERIOD = "1"
DEFAULT_USERNAME = "sk_pgdav"  # confirmed from prior query.php success response


PLACEHOLDER_KEYS = {
    "PASTE_YOUR_KEY_HERE",
    "YOUR_API_KEY",
    "YOUR_PASSKEY",
    "YOUR_API_PASSKEY",
    "",
}


def load_api_key() -> str:
    """Env CMIE_API_KEY > .streamlit/secrets.toml. Fails loudly on placeholder."""
    key = os.environ.get("CMIE_API_KEY", "").strip()
    if not key and SECRETS_PATH.is_file():
        with SECRETS_PATH.open("rb") as f:
            cfg = tomllib.load(f)
        key = str(cfg.get("CMIE_API_KEY", "")).strip()
    if key.upper() in PLACEHOLDER_KEYS:
        sys.exit(
            f"FATAL: CMIE_API_KEY is the placeholder value {key!r}. "
            "Replace it in .streamlit/secrets.toml with a real Passkey."
        )
    return key


def redact(body: dict[str, Any]) -> dict[str, Any]:
    safe = dict(body)
    if "apikey" in safe:
        k = str(safe["apikey"])
        safe["apikey"] = f"<REDACTED len={len(k)}>"
    return safe


def classify_outcome(meta: dict[str, Any], df: pd.DataFrame | None) -> str:
    errno = meta.get("errno")
    if errno == 0 and df is not None and not df.empty:
        return "ok_with_data"
    if errno == 0:
        return "ok_empty"
    if errno == -4:
        return "invalid_apikey"
    if errno == -23:
        return "no_service_indicator"
    if errno is None:
        return "no_meta"
    return f"errno_{errno}"


def build_report(
    meta: dict[str, Any],
    df: pd.DataFrame | None,
    schema_notes: list[str],
    out_dir: Path,
    form_fields: dict[str, str],
) -> str:
    errno = meta.get("errno")
    outcome = classify_outcome(meta, df)

    lines: list[str] = []
    lines.append(f"# CMIE query.php End-to-End POC — {meta['ts']}")
    lines.append("")
    lines.append(f"- **Outcome:** `{outcome}`")
    lines.append(f"- **errno / errmsg:** `{errno}` — {meta.get('errmsg', '')!r}")
    lines.append(f"- **user:** `{meta.get('user', 'n/a')}`")
    lines.append(f"- **service:** `{meta.get('service', '<empty>')!r}`")
    lines.append(f"- **hits (CMIE total for account):** `{meta.get('hits', 'n/a')}`")
    lines.append(
        f"- **request:** scheme=`{form_fields.get('scheme')}` "
        f"indicnum=`{form_fields.get('indicnum')}` "
        f"freq=`{form_fields.get('freq')}` nperiod=`{form_fields.get('nperiod')}`"
    )
    nrow = meta.get("nrow", 0)
    ncol = meta.get("ncol", 0)
    lines.append(f"- **response shape:** {nrow} rows × {ncol} cols")
    lines.append("")

    lines.append("## Interpretation")
    if outcome == "ok_with_data":
        lines.append(
            "Success — query.php returned tabular data and the existing parser "
            "(`cmie.query_form.cmie_tabular_json_to_dataframe`) handled it. The POC proves "
            "that the transport pivot from wapicall to query.php is wired end-to-end without "
            "touching the existing package."
        )
    elif outcome == "ok_empty":
        lines.append(
            "Success (errno=0) but the table is empty for this query. Passkey + entitlement "
            "are fine. Try a wider `nperiod` or a different `indicnum`."
        )
    elif outcome == "invalid_apikey":
        lines.append(
            "Passkey rejected (`errno:-4`). Re-check `.streamlit/secrets.toml` against "
            "`register.cmie.com` (the Passkey may have been rotated)."
        )
    elif outcome == "no_service_indicator":
        lines.append(
            "`No-Service Indicator Number` (`errno:-23`) — your CMIE account is service-blocked "
            "for this indicator. CMIE support action required to activate the scheme (see "
            "docs/plans/2026-04-21-cmie-refactor-execution-strategy.md §E.5.2)."
        )
    elif outcome == "no_meta":
        lines.append(
            "Response has no `meta` section — CMIE may have returned an unexpected shape. "
            "See `response.json`."
        )
    else:
        lines.append(
            f"Unhandled errno `{errno}`. See `response.json` for full body; extend this "
            "script's classifier if this error code recurs."
        )

    if schema_notes:
        lines.append("")
        lines.append("## Schema observations")
        for note in schema_notes:
            lines.append(f"- {note}")

    if df is not None and not df.empty:
        lines.append("")
        lines.append("## First 10 rows (after `cmie_tabular_json_to_dataframe`)")
        lines.append("")
        lines.append("```")
        lines.append(df.head(10).to_string(index=False))
        lines.append("```")

    lines.append("")
    lines.append("## What this POC proves (independent of outcome)")
    lines.append("- `cmie.client.CmieClient.post_query_form()` can be called from an external script.")
    lines.append("- `cmie.query_form.cmie_tabular_json_to_dataframe()` handles live CMIE responses.")
    lines.append("- `cmie.normalize.CANONICAL_COLUMNS` is accessible for schema-drift checks.")
    lines.append("- Error responses (`errno != 0`) are classifiable into discrete outcomes for downstream pipeline branching.")
    lines.append("- No UI, no backend, no `capital_structure.db` touched.")

    lines.append("")
    lines.append(f"_Artifacts: `{out_dir.as_posix()}`_")
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--scheme", default=DEFAULT_SCHEME)
    ap.add_argument(
        "--indicnum",
        default=DEFAULT_INDICNUM,
        help="Comma-separated CMIE indicator IDs (default from CMIE docs example)",
    )
    ap.add_argument("--freq", default=DEFAULT_FREQ, choices=["A", "Q", "M"])
    ap.add_argument("--nperiod", default=DEFAULT_NPERIOD)
    ap.add_argument("--username", default=DEFAULT_USERNAME)
    ap.add_argument("--timeout", type=float, default=120.0)
    ns = ap.parse_args()

    api_key = load_api_key()
    ts = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
    out_dir = Path("cmie_validation") / f"queryphp_{ts}"
    out_dir.mkdir(parents=True, exist_ok=True)

    form_fields: dict[str, str] = {
        "username": ns.username,
        "scheme": ns.scheme,
        "indicnum": ns.indicnum,
        "freq": ns.freq,
        "nperiod": ns.nperiod,
    }

    (out_dir / "request.json").write_text(
        json.dumps(
            {
                "transport": "cmie.client.CmieClient.post_query_form",
                "form_fields": form_fields,
                "apikey_redacted": f"<REDACTED len={len(api_key)}>",
            },
            indent=2,
        )
    )

    print("[queryphp] POST https://economyapi.cmie.com/query.php")
    print(
        f"[queryphp] scheme={ns.scheme} indicnum={ns.indicnum} "
        f"freq={ns.freq} nperiod={ns.nperiod}"
    )
    print(f"[queryphp] out_dir={out_dir.as_posix()}")

    client = CmieClient(api_key=api_key, timeout_s=ns.timeout, max_retries=0)
    try:
        resp = client.post_query_form(form_fields)
    except CmieError as e:
        err_meta = {
            "ts": ts,
            "outcome": "client_error",
            "error_code": e.code,
            "error_message": str(e),
        }
        (out_dir / "meta.json").write_text(json.dumps(err_meta, indent=2))
        report = (
            f"# CMIE query.php POC — {ts}\n\n"
            f"Client raised `{type(e).__name__}({e.code})`: {e}\n\n"
            f"No JSON body captured.\n"
        )
        (out_dir / "report.md").write_text(report)
        print(f"[queryphp] {type(e).__name__}({e.code}): {e}")
        return 2

    (out_dir / "response.json").write_text(
        json.dumps(resp, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    m = resp.get("meta", {}) if isinstance(resp, dict) else {}
    meta: dict[str, Any] = {
        "ts": ts,
        "errno": m.get("errno"),
        "errmsg": m.get("errmsg"),
        "user": m.get("user"),
        "service": m.get("service"),
        "hits": m.get("hits"),
        "scheme": m.get("scheme"),
        "freq": m.get("freq"),
        "nperiod": m.get("nperiod"),
        "nrow": m.get("nrow"),
        "ncol": m.get("ncol"),
    }

    print(
        f"[queryphp] errno={meta['errno']} errmsg={meta['errmsg']!r} "
        f"user={meta['user']} service={meta['service']!r}"
    )
    print(f"[queryphp] hits={meta['hits']}")
    print(f"[queryphp] rows={meta['nrow']} cols={meta['ncol']}")

    # Exercise the parser even on error bodies — demonstrates the full E2E path
    df: pd.DataFrame | None = None
    schema_notes: list[str] = []
    try:
        df = cmie_tabular_json_to_dataframe(resp)
        schema_notes.append(
            f"Parser `cmie_tabular_json_to_dataframe` succeeded: shape {df.shape}"
        )

        # Detect whether this is an error-shape or data-shape response
        #   Error responses have head = [[label, value], …] (list-of-lists) →
        #   pandas makes tuple-shaped columns, not plain strings.
        is_error_response = (
            meta.get("errno") != 0
            or any(isinstance(c, (tuple, list)) for c in df.columns)
        )
        if is_error_response:
            schema_notes.append(
                "**Parser finding:** `cmie_tabular_json_to_dataframe` does NOT branch on "
                "`errno` — it parsed this error-shape body as if it were data, producing a "
                "DataFrame with non-string columns. Refactor should check `meta.errno == 0` "
                "BEFORE invoking the parser."
            )
        else:
            unknown_cols = [
                str(c) for c in df.columns
                if isinstance(c, str) and c not in CANONICAL_COLUMNS
            ]
            if unknown_cols:
                shown = ", ".join(unknown_cols[:20])
                suffix = " …" if len(unknown_cols) > 20 else ""
                schema_notes.append(
                    f"{len(unknown_cols)} columns outside `CANONICAL_COLUMNS` (would be "
                    f"dropped by `normalize_panel_like`): {shown}{suffix}"
                )
                schema_notes.append(
                    "Add these to `cmie/indicator_map.COLUMN_ALIASES` or extend "
                    "`CANONICAL_COLUMNS` before wiring into the refactor pipeline."
                )

        if df is not None and not df.empty:
            df.head(50).to_csv(out_dir / "data_preview.csv", index=False)
    except CmieParseError as e:
        schema_notes.append(
            f"Parser rejected response: `{e.code}` — {e}. "
            "This is expected on error-shape bodies (errno != 0)."
        )
    except Exception as e:
        schema_notes.append(
            f"Parser crashed unexpectedly: `{type(e).__name__}`: {e}. "
            "Parser assumes `head` = list of strings and `data` rows align to `head` length; "
            "error-shape bodies may not satisfy that."
        )

    meta["outcome"] = classify_outcome(meta, df)
    (out_dir / "meta.json").write_text(json.dumps(meta, indent=2, default=str))

    report = build_report(meta, df, schema_notes, out_dir, form_fields)
    (out_dir / "report.md").write_text(report, encoding="utf-8")
    print(f"[queryphp] outcome={meta['outcome']}")
    print(f"[queryphp] report: {(out_dir / 'report.md').as_posix()}")
    return 0 if meta["outcome"] == "ok_with_data" else 2


if __name__ == "__main__":
    raise SystemExit(main())

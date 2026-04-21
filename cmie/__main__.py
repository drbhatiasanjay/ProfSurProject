"""
Run CMIE post-processing without Streamlit (avoids UI disconnect / long request issues).

Examples:
  python -m cmie import-zip downloads/cmie_response.zip --company-code 100001
  python -m cmie import-table response.json --min-years 1
  python -m cmie merge-zips z1.zip z2.zip --min-years 1
  python -m cmie batch-download --codes \"101,102\" --payload-json-file tpl.json --out-dir ./zips
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import pandas as pd

from cmie.batch_utils import json_payload_for_company, parse_company_codes
from cmie.client import CmieClient
from cmie.errors import CmieParseError
from cmie.pipeline import import_from_raw_dataframe, import_from_zip_file, merge_zip_paths_to_version
from cmie.query_form import cmie_tabular_json_to_dataframe


def _load_table_from_path(path: str) -> pd.DataFrame:
    """Load a CSV or JSON table (CMIE tabular head/data object, or JSON array of row objects)."""
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(path)
    suf = p.suffix.lower()
    if suf == ".csv":
        return pd.read_csv(p)
    if suf == ".json":
        with p.open(encoding="utf-8") as f:
            obj = json.load(f)
        if isinstance(obj, list):
            if not obj:
                return pd.DataFrame()
            if not isinstance(obj[0], dict):
                raise ValueError("JSON array must be a list of objects (column → value per row).")
            return pd.DataFrame(obj)
        if isinstance(obj, dict):
            return cmie_tabular_json_to_dataframe(obj)
        raise ValueError(f"Unsupported JSON top-level type: {type(obj).__name__}")
    raise ValueError(f"Unsupported file type {suf!r} (use .csv or .json).")


def _cmd_import_table(ns: argparse.Namespace) -> int:
    def on_step(pct: int, msg: str):
        print(f"[{pct:3d}%] {msg}", flush=True)

    try:
        raw = _load_table_from_path(ns.path)
    except (OSError, ValueError, CmieParseError) as e:
        print(str(e), file=sys.stderr)
        return 2

    cc = ns.company_code if ns.company_code else None
    import_from_raw_dataframe(
        raw,
        import_id=ns.import_id,
        company_code_metadata=cc,
        on_step=on_step,
        min_validation_years=ns.min_years,
        indicators=ns.indicators or "",
        note=ns.note or "CMIE import-table (CLI)",
    )
    print("Table import finished successfully.", flush=True)
    return 0


def _cmd_import_zip(ns: argparse.Namespace) -> int:
    def on_step(pct: int, msg: str):
        print(f"[{pct:3d}%] {msg}", flush=True)

    cc = ns.company_code if ns.company_code else None
    import_from_zip_file(
        ns.zip_path,
        cc,
        import_id=ns.import_id,
        on_step=on_step,
        min_validation_years=ns.min_years,
    )
    print("Import finished successfully.", flush=True)
    return 0


def _cmd_download(ns: argparse.Namespace) -> int:
    key = (ns.api_key or "").strip() or os.environ.get("CMIE_API_KEY", "").strip()
    if not key:
        print("Missing API key: pass --api-key or set CMIE_API_KEY.", file=sys.stderr)
        return 2
    client = CmieClient(key, timeout_s=ns.timeout)

    def on_dl(p):
        pct = f"{p.pct:.1f}%" if p.pct is not None else "?"
        print(f"\rDownloaded {p.received_bytes/1e6:.2f} MB ({pct})", end="", flush=True)

    payload = json.loads(ns.payload_json)
    client.download_query_zip(payload, dest_path=ns.out_zip, on_progress=on_dl)
    print(f"\nSaved: {ns.out_zip}", flush=True)
    return 0


def _cmd_merge_zips(ns: argparse.Namespace) -> int:
    def on_step(pct: int, msg: str):
        print(f"[{pct:3d}%] {msg}", flush=True)

    merge_zip_paths_to_version(
        ns.zip_paths,
        import_id=ns.import_id,
        on_step=on_step,
        min_validation_years=ns.min_years,
        indicators=ns.indicators or "",
        note="CMIE merge-zips (CLI)",
    )
    print("Merge import finished successfully.", flush=True)
    return 0


def _cmd_batch_download(ns: argparse.Namespace) -> int:
    key = (ns.api_key or "").strip() or os.environ.get("CMIE_API_KEY", "").strip()
    if not key:
        print("Missing API key: pass --api-key or set CMIE_API_KEY.", file=sys.stderr)
        return 2

    template = ns.payload_json
    if ns.payload_json_file:
        with open(ns.payload_json_file, encoding="utf-8") as f:
            template = f.read()

    codes = parse_company_codes(ns.codes, max_n=10)
    os.makedirs(ns.out_dir, exist_ok=True)
    client = CmieClient(key, timeout_s=ns.timeout)

    for i, code in enumerate(codes):
        payload = json_payload_for_company(template, code)
        out_path = os.path.join(ns.out_dir, f"cmie_{code}.zip")
        print(f"Downloading company {code} ({i + 1}/{len(codes)}) → {out_path}", flush=True)

        def on_dl(p):
            pct = f"{p.pct:.1f}%" if p.pct is not None else "?"
            print(f"\r  {p.received_bytes/1e6:.2f} MB ({pct})", end="", flush=True)

        client.download_query_zip(payload, dest_path=out_path, on_progress=on_dl)
        print("", flush=True)
        if i < len(codes) - 1 and ns.delay > 0:
            import time

            time.sleep(ns.delay)
    print("Batch download complete.", flush=True)
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="CMIE Economy API helpers (CLI).")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_zip = sub.add_parser("import-zip", help="Unzip + parse + store a CMIE response zip into SQLite.")
    p_zip.add_argument("zip_path", help="Path to the .zip returned by CMIE")
    p_zip.add_argument("--company-code", type=int, default=0, help="CMIE company_code (0 = unknown / omit)")
    p_zip.add_argument("--import-id", default=None, help="Optional fixed import id (default: random)")
    p_zip.add_argument("--min-years", type=int, default=3, help="Minimum unique years required after normalize")
    p_zip.set_defaults(_run=_cmd_import_zip)

    p_tbl = sub.add_parser(
        "import-table",
        help="Import a .csv or CMIE-style .json (head/data) into SQLite via the same path as Streamlit Form.",
    )
    p_tbl.add_argument("path", help="Path to .csv or .json (tabular object or array of row objects)")
    p_tbl.add_argument("--company-code", type=int, default=0, help="CMIE company_code metadata (0 = omit)")
    p_tbl.add_argument("--import-id", default=None, help="Optional fixed import id (default: random)")
    p_tbl.add_argument("--min-years", type=int, default=3, help="Minimum unique years required after normalize")
    p_tbl.add_argument("--indicators", default="", help="Optional note stored on api_imports.indicators")
    p_tbl.add_argument("--note", default="", help="Version note (default: CMIE import-table (CLI))")
    p_tbl.set_defaults(_run=_cmd_import_table)

    p_dl = sub.add_parser("download", help="Download a CMIE zip to disk (then run import-zip separately).")
    p_dl.add_argument(
        "--api-key",
        default=os.environ.get("CMIE_API_KEY", ""),
        help="CMIE API key (default: env CMIE_API_KEY)",
    )
    p_dl.add_argument("--payload-json", required=True, help="JSON string for the CMIE query body")
    p_dl.add_argument("--out-zip", required=True, help="Destination .zip path")
    p_dl.add_argument("--timeout", type=float, default=600.0, help="HTTP timeout seconds")
    p_dl.set_defaults(_run=_cmd_download)

    p_merge = sub.add_parser(
        "merge-zips",
        help="Merge multiple CMIE response zips into one normalized version (same as batch fetch final step).",
    )
    p_merge.add_argument("zip_paths", nargs="+", help="Paths to .zip files (order preserved)")
    p_merge.add_argument("--import-id", default=None, help="Optional fixed import id (default: random)")
    p_merge.add_argument("--min-years", type=int, default=3, help="Minimum unique years on merged panel")
    p_merge.add_argument("--indicators", default="", help="Optional note stored on api_imports.indicators")
    p_merge.set_defaults(_run=_cmd_merge_zips)

    p_bd = sub.add_parser(
        "batch-download",
        help="Download up to 10 zips (substitutes __CMIE_COMPANY_CODE__ in JSON template per company).",
    )
    p_bd.add_argument(
        "--api-key",
        default=os.environ.get("CMIE_API_KEY", ""),
        help="CMIE API key (default: env CMIE_API_KEY)",
    )
    p_bd.add_argument(
        "--codes",
        required=True,
        help="Comma or whitespace separated company codes (max 10)",
    )
    g = p_bd.add_mutually_exclusive_group(required=True)
    g.add_argument("--payload-json", help="JSON template string containing __CMIE_COMPANY_CODE__")
    g.add_argument("--payload-json-file", help="Path to JSON template file")
    p_bd.add_argument("--out-dir", required=True, help="Directory to write cmie_<code>.zip files")
    p_bd.add_argument("--timeout", type=float, default=600.0, help="HTTP timeout seconds per request")
    p_bd.add_argument("--delay", type=float, default=1.0, help="Seconds to sleep between downloads")
    p_bd.set_defaults(_run=_cmd_batch_download)

    ns = p.parse_args(argv)
    return int(ns._run(ns))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

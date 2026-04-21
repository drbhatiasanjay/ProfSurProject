"""
Stage 1 CMIE API diagnostic — single-company reachability check.

Per docs/plans/2026-04-21-cmie-refactor-execution-strategy.md §E.5.

Calls wapicall for one company with max_retries=0 (no retry) and captures:
  - HTTP status code + response headers
  - Response body shape (zip vs html vs json)
  - ZIP entries (filenames + sizes)
  - First 3 lines of each .txt file inside the zip — reveals actual columns

Does NOT touch capital_structure.db.
Does NOT go through cmie.pipeline.
Does NOT retry on any failure.

Output tree:
  cmie_validation/<timestamp>/
    request.json        payload actually sent (apikey redacted)
    response_meta.json  status, headers, bytes, elapsed, outcome classification
    response.zip        raw response body (if >0 bytes)
    response_snippet.txt first 2KB of body if not a zip (debugging non-zip failures)
    extracted/          unzipped contents (if body was a zip)
    txt_previews.json   first 3 lines + approx line count of each .txt
    report.md           human-readable summary

Usage:
  py -3.12 scripts/cmie_stage1_reliance_diagnostic.py
  py -3.12 scripts/cmie_stage1_reliance_diagnostic.py --company-code 196667
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import sys
import time
import tomllib
import zipfile
from pathlib import Path
from typing import Any

import requests

CMIE_WAPICALL_URL = "https://economyapi.cmie.com/kommon/bin/sr.php?kall=wapicall"
DEFAULT_COMPANY = 196667  # Reliance Industries (per strategy doc §E.5)
SECRETS_PATH = Path(".streamlit/secrets.toml")


def load_api_key() -> str:
    """Env var `CMIE_API_KEY` takes precedence; fall back to .streamlit/secrets.toml."""
    key = os.environ.get("CMIE_API_KEY", "").strip()
    if key:
        return key
    if SECRETS_PATH.is_file():
        with SECRETS_PATH.open("rb") as f:
            cfg = tomllib.load(f)
        key = str(cfg.get("CMIE_API_KEY", "")).strip()
    if not key:
        sys.exit(
            "FATAL: CMIE_API_KEY not set — neither in env nor in .streamlit/secrets.toml"
        )
    return key


def redact_body(body: dict[str, Any]) -> dict[str, Any]:
    """Return a copy with `apikey` replaced by a length-only marker."""
    safe = dict(body)
    if "apikey" in safe:
        k = str(safe["apikey"])
        safe["apikey"] = f"<REDACTED len={len(k)}>"
    return safe


def classify_outcome(status: int, zip_path: Path, body_bytes: int) -> str:
    if body_bytes == 0:
        return "empty_body"
    if status == 401 or status == 403:
        return f"auth_{status}"
    if status == 429:
        return "rate_limit_429"
    if 500 <= status < 600:
        return f"server_{status}"
    if status != 200:
        return f"http_{status}"
    if not zipfile.is_zipfile(zip_path):
        return "non_zip_body"
    return "zip_ok"


def preview_txt_files(extract_dir: Path, names: list[str]) -> dict[str, Any]:
    """For each .txt entry: first 3 lines + approximate total line count."""
    previews: dict[str, Any] = {}
    for name in names:
        if not name.lower().endswith(".txt"):
            continue
        fpath = extract_dir / name
        try:
            raw = fpath.read_bytes()
        except OSError as e:
            previews[name] = {"error": f"read failed: {e}"}
            continue
        text: str | None = None
        enc_used: str | None = None
        for enc in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
            try:
                text = raw.decode(enc)
                enc_used = enc
                break
            except Exception:
                continue
        if text is None:
            previews[name] = {"error": "no encoding decoded"}
            continue
        all_lines = text.splitlines()
        previews[name] = {
            "encoding": enc_used,
            "total_bytes": len(raw),
            "line_count": len(all_lines),
            "first_3_lines": all_lines[:3],
        }
    return previews


def build_report(meta: dict[str, Any], previews: dict[str, Any], out_dir: Path) -> str:
    lines: list[str] = []
    lines.append(f"# CMIE Stage-1 Diagnostic — {meta['ts']}")
    lines.append("")
    lines.append(f"- **Company code:** {meta['company_code']}")
    lines.append(f"- **Outcome:** `{meta.get('outcome')}`")
    lines.append(f"- **HTTP status:** {meta.get('status_code', 'n/a')}")
    ct = meta.get("headers", {}).get("Content-Type", "n/a")
    lines.append(f"- **Content-Type:** `{ct}`")
    lines.append(f"- **Body size:** {meta.get('bytes', 0):,} bytes")
    lines.append(f"- **Elapsed:** {meta.get('elapsed_s')} s")
    lines.append("")
    lines.append("## Interpretation")
    outcome = meta.get("outcome", "")
    if outcome == "zip_ok":
        lines.append(
            "Auth works; ZIP received and parseable. Schema drift (if any) will be"
            " visible in the .txt previews below. Proceed to Stage 2 (sample batch)."
        )
    elif outcome == "non_zip_body":
        lines.append(
            "`ZIP_BAD` — CMIE returned a non-zip body with HTTP 200. Likely auth"
            " failure, endpoint drift, or wrong body encoding (see §E.1 JSON vs"
            " form-encoded diagnostic lead). Inspect `response_snippet.txt`."
        )
    elif outcome.startswith("auth_"):
        lines.append(
            "`AUTH` — API key rejected. Rotate or verify with CMIE. Do NOT proceed"
            " to any batch call."
        )
    elif outcome == "rate_limit_429":
        ra = meta.get("headers", {}).get("Retry-After", "n/a")
        lines.append(f"`RATE_LIMIT` — 429. Retry-After: `{ra}`.")
    elif outcome.startswith("server_"):
        lines.append("`SERVER` — CMIE 5xx. Re-run the diagnostic later.")
    elif outcome == "empty_body":
        lines.append(
            "Empty body — unusual. Check DNS / network path and re-run."
        )
    else:
        lines.append(f"Unexpected outcome: `{outcome}`")

    if meta.get("zip_entries"):
        lines.append("")
        lines.append("## ZIP entries")
        lines.append("")
        lines.append("| File | Size (bytes) |")
        lines.append("|---|---:|")
        for e in meta["zip_entries"]:
            lines.append(f"| `{e['name']}` | {e['size']:,} |")

    if previews:
        lines.append("")
        lines.append("## .txt previews (first 3 lines)")
        for name, info in previews.items():
            lines.append("")
            lines.append(f"### `{name}`")
            if "error" in info:
                lines.append(f"ERROR: {info['error']}")
                continue
            lines.append(
                f"- encoding: `{info['encoding']}`  ·  "
                f"total_bytes: {info['total_bytes']:,}  ·  "
                f"lines: {info['line_count']:,}"
            )
            lines.append("")
            lines.append("```")
            for raw_line in info["first_3_lines"]:
                lines.append(raw_line)
            lines.append("```")

    lines.append("")
    lines.append("## Response headers")
    lines.append("")
    lines.append("```json")
    lines.append(json.dumps(meta.get("headers", {}), indent=2))
    lines.append("```")
    lines.append("")
    lines.append(f"_Artifacts: `{out_dir.as_posix()}`_")
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--company-code",
        type=int,
        default=DEFAULT_COMPANY,
        help=f"CMIE company code (default {DEFAULT_COMPANY} = Reliance)",
    )
    ap.add_argument("--timeout", type=float, default=120.0)
    ns = ap.parse_args()

    api_key = load_api_key()
    ts = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
    out_dir = Path("cmie_validation") / ts
    out_dir.mkdir(parents=True, exist_ok=True)
    zip_path = out_dir / "response.zip"
    extract_dir = out_dir / "extracted"

    body = {"apikey": api_key, "company_code": [str(ns.company_code)]}

    (out_dir / "request.json").write_text(
        json.dumps(
            {
                "url": CMIE_WAPICALL_URL,
                "method": "POST",
                "content_type": "application/json",
                "body": redact_body(body),
            },
            indent=2,
        )
    )

    print(f"[stage1] POST {CMIE_WAPICALL_URL}")
    print(f"[stage1] company_code: {ns.company_code}")
    print(f"[stage1] out_dir:      {out_dir.as_posix()}")

    meta: dict[str, Any] = {"ts": ts, "company_code": ns.company_code}
    started = time.monotonic()
    try:
        resp = requests.post(
            CMIE_WAPICALL_URL,
            json=body,
            timeout=ns.timeout,
            stream=True,
        )
    except requests.RequestException as e:
        meta["outcome"] = "network_error"
        meta["error"] = str(e)
        meta["elapsed_s"] = round(time.monotonic() - started, 3)
        (out_dir / "response_meta.json").write_text(
            json.dumps(meta, indent=2, default=str)
        )
        (out_dir / "report.md").write_text(build_report(meta, {}, out_dir))
        print(f"[stage1] NETWORK ERROR: {e}")
        return 1

    meta["status_code"] = resp.status_code
    meta["headers"] = dict(resp.headers)
    meta["url"] = resp.url

    total_bytes = 0
    with zip_path.open("wb") as f:
        for chunk in resp.iter_content(chunk_size=256 * 1024):
            if chunk:
                f.write(chunk)
                total_bytes += len(chunk)
    meta["bytes"] = total_bytes
    meta["elapsed_s"] = round(time.monotonic() - started, 3)
    meta["outcome"] = classify_outcome(resp.status_code, zip_path, total_bytes)

    print(
        f"[stage1] status={resp.status_code} "
        f"ct={resp.headers.get('Content-Type')!r} "
        f"bytes={total_bytes:,} elapsed={meta['elapsed_s']}s "
        f"outcome={meta['outcome']}"
    )

    previews: dict[str, Any] = {}
    if meta["outcome"] == "zip_ok":
        extract_dir.mkdir(exist_ok=True)
        with zipfile.ZipFile(zip_path, "r") as zf:
            names = zf.namelist()
            meta["zip_entries"] = [
                {"name": n, "size": zf.getinfo(n).file_size} for n in names
            ]
            zf.extractall(extract_dir)
        print(f"[stage1] ZIP entries ({len(names)}):")
        for n in names:
            print(f"  - {n}")
        previews = preview_txt_files(extract_dir, names)
        (out_dir / "txt_previews.json").write_text(
            json.dumps(previews, indent=2, default=str)
        )
    elif meta["outcome"] == "non_zip_body":
        # Keep the first 2 KB of the body for post-mortem inspection
        (out_dir / "response_snippet.txt").write_bytes(zip_path.read_bytes()[:2000])

    (out_dir / "response_meta.json").write_text(
        json.dumps(meta, indent=2, default=str)
    )
    (out_dir / "report.md").write_text(build_report(meta, previews, out_dir))
    print(f"[stage1] report: {(out_dir / 'report.md').as_posix()}")
    return 0 if meta["outcome"] == "zip_ok" else 2


if __name__ == "__main__":
    raise SystemExit(main())

"""
Multi-country firm-data API connectivity probe.

Same pre-development discipline as scripts/cmie_stage1_*.py — hit each candidate
source with a simple GET, capture status + headers + response structure, and
emit a verdict table so we know which APIs are reachable before scaffolding any
ingestion code.

Tests three categories:
  • No-auth public APIs (just need a request) — SEC EDGAR, EDINET, CVM, OECD
  • Demo-key APIs (vendor-provided sample key) — FMP, Alpha Vantage
  • Auth-required APIs (probe to confirm the gate, document what's needed) —
    Companies House (UK), Twelve Data, Tushare (China), DART (Korea)

For each probe we record:
  - HTTP status + Content-Type
  - Response time
  - Body size + first 2 KB snippet
  - JSON shape (top-level keys / array length) when applicable
  - Whether a sample firm's financial data is visible
  - Verdict: live / live_with_demo / auth_required / unreachable

Outputs:
  cmie_validation/multi_country_<timestamp>/
    <source_slug>.json     — raw JSON response or first 2 KB of body
    summary.json           — machine-readable summary of all probes
    report.md              — human-readable verdict table

No DB writes. No code changes elsewhere. Idempotent (each run gets its own
timestamp directory).
"""
from __future__ import annotations

import datetime
import json
import sys
import time
from pathlib import Path

import requests

# Probe definitions — each one is a single GET request that reveals whether
# the API is alive + what shape the data takes. The `auth_required` field is
# documentation; if set, we still try the URL to confirm the auth gate.
PROBES = [
    # ── No-auth public APIs ────────────────────────────────────────────────
    {
        "slug": "us_sec_edgar",
        "name": "SEC EDGAR (US — Apple submissions)",
        "url": "https://data.sec.gov/submissions/CIK0000320193.json",
        "headers": {
            # SEC requires a User-Agent identifying the requester per their fair-use policy
            "User-Agent": "ProfSurProject academic research drbhatiasanjay@gmail.com",
        },
        "category": "free_no_auth",
        "expected": "JSON with cik, name, sic, recent.accessionNumber array",
    },
    {
        "slug": "jp_edinet_docs",
        "name": "EDINET (Japan — recent doc list)",
        "url": "https://disclosure.edinet-fsa.go.jp/api/v2/documents.json?date=2024-04-01&type=2",
        "headers": {},
        "category": "free_no_auth",
        "expected": "JSON with metadata + results[] of disclosed documents",
    },
    {
        "slug": "br_cvm_dfp_listing",
        "name": "CVM (Brazil — DFP CSV catalogue index)",
        "url": "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/DFP/DADOS/",
        "headers": {},
        "category": "free_no_auth",
        "expected": "HTML directory listing of dfp_cia_aberta_<year>.csv files",
    },
    {
        "slug": "oecd_sdmx_macro",
        "name": "OECD SDMX (cross-country macro — sample dataset)",
        "url": "https://sdmx.oecd.org/public/rest/dataflow/OECD.SDD.STES/DSD_STES@DF_FINMARK?references=all&detail=referencepartial",
        "headers": {"Accept": "application/vnd.sdmx.structure+json;version=1.0"},
        "category": "free_no_auth",
        "expected": "SDMX-JSON dataflow structure (macro/sector aggregates only — not firm-level)",
    },

    # ── Demo-key APIs (vendor-provided sample) ─────────────────────────────
    {
        "slug": "us_fmp_aapl",
        "name": "Financial Modeling Prep (US — Apple income stmt, demo key)",
        "url": "https://financialmodelingprep.com/api/v3/income-statement/AAPL?apikey=demo&limit=5",
        "headers": {},
        "category": "demo_key",
        "expected": "JSON array of 5 most-recent income statements",
        "auth_for_real": "Free API key — financialmodelingprep.com (no credit card)",
    },
    {
        "slug": "us_alpha_vantage_ibm",
        "name": "Alpha Vantage (US — IBM income stmt, demo key)",
        "url": "https://www.alphavantage.co/query?function=INCOME_STATEMENT&symbol=IBM&apikey=demo",
        "headers": {},
        "category": "demo_key",
        "expected": "JSON with annualReports[] + quarterlyReports[]",
        "auth_for_real": "Free API key — alphavantage.co (rate limit: 5/min, 500/day on free tier)",
    },
    {
        "slug": "twelvedata_aapl",
        "name": "Twelve Data (Global — Apple income stmt, demo key)",
        "url": "https://api.twelvedata.com/income_statement?symbol=AAPL&apikey=demo",
        "headers": {},
        "category": "demo_key",
        "expected": "JSON with income_statement[] (may also work with demo)",
        "auth_for_real": "Free API key — twelvedata.com",
    },

    # ── Auth-required APIs (probe to confirm gate) ─────────────────────────
    {
        "slug": "uk_companies_house",
        "name": "Companies House (UK — first-ever Ltd company)",
        "url": "https://api.company-information.service.gov.uk/company/00000006",
        "headers": {},
        "category": "auth_required",
        "expected": "401 without API key (which confirms the gate is live)",
        "auth_for_real": "Free API key — developer.company-information.service.gov.uk (HTTP Basic with key:'')",
    },
    {
        "slug": "kr_dart_list",
        "name": "DART (Korea — recent disclosure list)",
        "url": "https://opendart.fss.or.kr/api/list.json?bgn_de=20240401&end_de=20240430&page_count=10",
        "headers": {},
        "category": "auth_required",
        "expected": "JSON with status code (auth-fail expected without crtfc_key)",
        "auth_for_real": "Free API key — opendart.fss.or.kr (Korean ID needed, English form available)",
    },
    {
        "slug": "cn_tushare",
        "name": "Tushare (China — POST endpoint, GET returns error)",
        "url": "https://api.tushare.pro",
        "headers": {},
        "category": "auth_required",
        "expected": "Method-not-allowed or token-required",
        "auth_for_real": "Free token — tushare.pro (academic users get higher free tier)",
    },
]


def _truncate(s: str, n: int = 2048) -> str:
    return s if len(s) <= n else s[:n] + f"\n…[truncated, total {len(s):,} bytes]"


def _summarise_body(content_type: str, text: str) -> dict:
    """Best-effort first-look at the response shape."""
    summary: dict = {"length_bytes": len(text)}
    ct = (content_type or "").lower()
    if "json" in ct:
        try:
            obj = json.loads(text)
            summary["json_root_type"] = type(obj).__name__
            if isinstance(obj, dict):
                summary["json_top_keys"] = list(obj.keys())[:20]
            elif isinstance(obj, list):
                summary["json_array_len"] = len(obj)
                if obj and isinstance(obj[0], dict):
                    summary["json_first_item_keys"] = list(obj[0].keys())[:20]
        except json.JSONDecodeError as e:
            summary["json_parse_error"] = str(e)[:200]
    elif "html" in ct or text.lstrip().startswith("<!"):
        # Crude HTML hint
        summary["body_kind"] = "HTML"
        # Look for table or pre tags as a directory-listing hint
        if "<a href=" in text.lower():
            summary["html_anchor_count"] = text.lower().count("<a href=")
    elif "xml" in ct or text.lstrip().startswith("<?xml"):
        summary["body_kind"] = "XML"
    else:
        summary["body_kind"] = "text/other"
    return summary


def run_probe(probe: dict, out_dir: Path) -> dict:
    started = time.monotonic()
    record: dict = {
        "slug": probe["slug"],
        "name": probe["name"],
        "url": probe["url"],
        "category": probe["category"],
    }
    try:
        r = requests.get(probe["url"], headers=probe.get("headers", {}), timeout=20)
        elapsed = round(time.monotonic() - started, 3)
        record["http_status"] = r.status_code
        record["content_type"] = r.headers.get("Content-Type", "")
        record["elapsed_s"] = elapsed
        body = r.text
        record["body_summary"] = _summarise_body(record["content_type"], body)

        # Save raw body — JSON pretty-printed if parseable, otherwise truncated text
        try:
            obj = json.loads(body)
            (out_dir / f"{probe['slug']}.json").write_text(
                json.dumps(obj, indent=2)[:50_000], encoding="utf-8"
            )
        except Exception:
            (out_dir / f"{probe['slug']}.txt").write_text(_truncate(body), encoding="utf-8")

        # Verdict
        if 200 <= r.status_code < 300:
            if probe["category"] == "auth_required":
                # Returned 200 even though auth_required — probe URL must be public,
                # likely won't apply to real data calls
                record["verdict"] = "live_unauth_endpoint"
            else:
                record["verdict"] = "live"
        elif r.status_code in (401, 403):
            record["verdict"] = "auth_required" if probe["category"] != "auth_required" else "auth_required_confirmed"
        elif r.status_code == 405:
            record["verdict"] = "method_not_allowed_likely_post_only"
        else:
            record["verdict"] = f"http_{r.status_code}"
    except requests.Timeout:
        record["http_status"] = None
        record["elapsed_s"] = round(time.monotonic() - started, 3)
        record["verdict"] = "timeout"
    except requests.RequestException as e:
        record["http_status"] = None
        record["elapsed_s"] = round(time.monotonic() - started, 3)
        record["verdict"] = f"network_error: {type(e).__name__}"
        record["error_detail"] = str(e)[:300]
    if "auth_for_real" in probe:
        record["auth_for_real_data"] = probe["auth_for_real"]
    return record


def render_report(results: list[dict], out_dir: Path) -> str:
    lines = []
    lines.append(f"# Multi-Country API Probe — {out_dir.name.replace('multi_country_', '')}")
    lines.append("")
    lines.append("Pre-development connectivity check across candidate firm-data APIs. "
                 "All tests are simple GET requests with no business logic.")
    lines.append("")
    lines.append("## Verdict table")
    lines.append("")
    lines.append("| Source | HTTP | Verdict | Time | Body | Notes |")
    lines.append("|---|---:|---|---:|---|---|")
    for r in results:
        verdict = r.get("verdict", "?")
        emoji = {
            "live": "✅",
            "live_unauth_endpoint": "🟢",
            "auth_required": "🔒",
            "auth_required_confirmed": "🔒",
            "method_not_allowed_likely_post_only": "🔒",
            "timeout": "⏱",
        }.get(verdict, "❌" if verdict.startswith(("http_", "network_error")) else "?")
        body_hint = r.get("body_summary", {})
        body_str = ""
        if "json_root_type" in body_hint:
            if "json_top_keys" in body_hint:
                body_str = f"JSON dict, keys: {', '.join(body_hint['json_top_keys'][:5])}"
            elif "json_array_len" in body_hint:
                body_str = f"JSON array len={body_hint['json_array_len']}"
        elif body_hint.get("body_kind") == "HTML":
            body_str = f"HTML, ~{body_hint.get('html_anchor_count', '?')} anchors"
        elif body_hint.get("body_kind"):
            body_str = body_hint["body_kind"]
        body_str += f" ({body_hint.get('length_bytes', 0):,} B)"
        lines.append(
            f"| {r['name']} | {r.get('http_status', '-')} | {emoji} {verdict} "
            f"| {r.get('elapsed_s', 0)}s | {body_str} | "
            f"{r.get('auth_for_real_data', '—')} |"
        )
    lines.append("")
    lines.append("## Per-probe detail")
    lines.append("")
    for r in results:
        lines.append(f"### {r['name']}")
        lines.append("")
        lines.append(f"- **Category:** `{r['category']}`")
        lines.append(f"- **URL:** `{r['url']}`")
        lines.append(f"- **HTTP status:** {r.get('http_status', 'n/a')}")
        lines.append(f"- **Content-Type:** `{r.get('content_type', 'n/a')}`")
        lines.append(f"- **Elapsed:** {r.get('elapsed_s', 0)} s")
        lines.append(f"- **Verdict:** `{r.get('verdict', 'n/a')}`")
        if "auth_for_real_data" in r:
            lines.append(f"- **Auth for real data:** {r['auth_for_real_data']}")
        if "body_summary" in r:
            lines.append(f"- **Body summary:** `{json.dumps(r['body_summary'])}`")
        if "error_detail" in r:
            lines.append(f"- **Error:** `{r['error_detail']}`")
        lines.append("")
    return "\n".join(lines) + "\n"


def main() -> int:
    ts = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
    out_dir = Path("cmie_validation") / f"multi_country_{ts}"
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"[probe] running {len(PROBES)} probes -> {out_dir.as_posix()}")
    results = []
    for i, probe in enumerate(PROBES, 1):
        print(f"  [{i}/{len(PROBES)}] {probe['name']}…", end=" ", flush=True)
        rec = run_probe(probe, out_dir)
        results.append(rec)
        print(f"{rec.get('verdict', '?')} ({rec.get('http_status', '-')}, {rec.get('elapsed_s', 0)}s)")

    (out_dir / "summary.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    (out_dir / "report.md").write_text(render_report(results, out_dir), encoding="utf-8")
    print()
    print(f"[probe] report : {(out_dir / 'report.md').as_posix()}")
    print(f"[probe] summary: {(out_dir / 'summary.json').as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

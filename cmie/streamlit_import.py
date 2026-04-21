"""
Streamlit UI for CMIE fetch + import.

Supports:
- Legacy streaming ZIP via query.php (json string field, existing behavior)
- Form POST to query.php returning JSON table (head/data) → normalize → SQLite
- wapicall company ZIP download → existing zip import pipeline
"""

from __future__ import annotations

import json
import os
import tempfile
import time
import uuid

import streamlit as st

import db
from cmie.batch_utils import MAX_BATCH_COMPANIES, json_payload_for_company, parse_company_codes
from cmie.client import CmieClient
from cmie.errors import CmieError, CmieParseError
from cmie.pipeline import import_from_raw_dataframe, import_from_zip_file, merge_zip_paths_to_version
from cmie.query_form import cmie_tabular_json_to_dataframe
from cmie.rate_limit import TokenBucket  # §F.3.1 — default 2 req/sec, burst 3 on every CmieClient in this file


def render_cmie_sidebar_block(*, key_prefix: str = "cmie") -> None:
    if not db.is_cmie_lab_enabled():
        return

    def k(name: str) -> str:
        return f"{key_prefix}_{name}"

    st.divider()
    st.markdown("### CMIE Economy API (Live)")

    if "data_source_mode" not in st.session_state:
        st.session_state.data_source_mode = "sqlite"

    mode = st.radio(
        "Data source",
        options=["sqlite", "cmie"],
        index=0 if st.session_state.data_source_mode == "sqlite" else 1,
        horizontal=True,
        help="Packaged SQLite vs latest CMIE import stored in this database.",
        key=k("data_source"),
    )
    st.session_state.data_source_mode = mode

    default_key = ""
    try:
        default_key = st.secrets.get("CMIE_API_KEY", "")
    except Exception:
        default_key = ""

    api_key = st.text_input(
        "CMIE API key (session only)",
        value=default_key,
        type="password",
        help="Prefer CMIE_API_KEY in Streamlit secrets / env for deployments.",
        key=k("api_key"),
    )

    st.caption(
        "**If the UI disconnects**, save artifacts manually, then run `python -m cmie import-zip …` "
        "or `python -m cmie merge-zips …` (same `capital_structure.db`)."
    )

    with st.expander("Fetch latest (imports a new version)", expanded=False):
        transport = st.radio(
            "CMIE transport",
            options=[
                "Legacy: streaming ZIP (query.php + json field)",
                "Form: JSON table (query.php form fields)",
                "Wapicall: company ZIP (sr.php?kall=wapicall)",
            ],
            index=0,
            help="Public CMIE docs use form POST for tabular JSON; company downloads use wapicall ZIP.",
            key=k("transport"),
        )

        min_years = st.number_input("Min years (validation)", min_value=1, max_value=50, value=3, step=1, key=k("min_years"))

        if transport.startswith("Form"):
            st.caption("POST **form fields** to `query.php`. Response must include CMIE **head** + **data** JSON.")
            form_fields_json = st.text_area(
                "Form fields (JSON object of string keys/values)",
                value='{"scheme": "MITS", "indicnum": "1,2", "freq": "Q", "nperiod": "14"}',
                height=120,
                key=k("form_fields_json"),
            )
            run = st.button("Fetch form JSON → import table", type="primary", disabled=(not api_key), key=k("run_form"))

            if run:
                _run_form_import(api_key, form_fields_json, min_years)

        elif transport.startswith("Wapicall"):
            st.caption("One ZIP per request; **3 hits/company** per CMIE public docs. Codes are sent as `company_code` array.")
            fetch_mode = st.radio(
                "Companies",
                ["Single company", f"Batch (≤{MAX_BATCH_COMPANIES} companies)"],
                horizontal=True,
                key=k("wapi_fetch_mode"),
            )
            if fetch_mode.startswith("Batch"):
                codes_text = st.text_area(
                    "Company codes (comma, space, or newline)",
                    placeholder="e.g.\n100001\n100002",
                    height=100,
                    key=k("wapi_codes"),
                )
                run = st.button("Download wapicall ZIP and import", type="primary", disabled=(not api_key), key=k("run_wapi_batch"))
                if run:
                    codes = parse_company_codes(codes_text, max_n=MAX_BATCH_COMPANIES)
                    _run_wapicall_import(api_key, codes, min_years)
            else:
                company_code = st.number_input("CMIE company_code", min_value=1, value=1, step=1, key=k("wapi_cc"))
                run = st.button("Download wapicall ZIP and import", type="primary", disabled=(not api_key), key=k("run_wapi_single"))
                if run:
                    _run_wapicall_import(api_key, [int(company_code)], min_years)

        else:
            st.caption(
                "Legacy path streams response bytes to a file (expects a ZIP). "
                "Single company or batch (≤10) with **__CMIE_COMPANY_CODE__** in the JSON template."
            )
            fetch_mode = st.radio(
                "Fetch mode",
                ["Single company", f"Batch (≤{MAX_BATCH_COMPANIES} companies)"],
                horizontal=True,
                key=k("legacy_fetch_mode"),
            )

            payload_text = st.text_area(
                "Query JSON payload (json field body)",
                value='{"scheme":"MITS","freq":"A"}',
                height=90,
                help="Batch: include __CMIE_COMPANY_CODE__ placeholder.",
                key=k("legacy_payload"),
            )

            if fetch_mode.startswith("Batch"):
                codes_text = st.text_area(
                    "Company codes (comma, space, or newline)",
                    placeholder="e.g.\n100001\n100002",
                    height=100,
                    key=k("legacy_codes"),
                )
                delay_s = st.number_input(
                    "Seconds between CMIE downloads", min_value=0.0, max_value=60.0, value=1.0, step=0.5, key=k("legacy_delay")
                )
                run = st.button("Fetch batch (legacy ZIP) and merge", type="primary", disabled=(not api_key), key=k("run_legacy_batch"))
                if run:
                    _run_legacy_batch_zip(api_key, payload_text, codes_text, delay_s, min_years)
            else:
                company_code = st.number_input("CMIE company_code", min_value=0, value=0, step=1, key=k("legacy_cc"))
                run = st.button("Fetch legacy ZIP and import", type="primary", disabled=(not api_key), key=k("run_legacy_single"))
                if run:
                    _run_legacy_single_zip(api_key, payload_text, int(company_code), min_years)


def _run_form_import(api_key: str, form_fields_json: str, min_years: int) -> None:
    import_id = uuid.uuid4().hex[:12]
    db.ensure_cmie_tables()
    status = st.status("CMIE form import", expanded=True)
    progress = st.progress(0)
    step_ph = st.empty()

    def set_step(pct: int, label: str):
        progress.progress(min(100, max(0, pct)))
        step_ph.markdown(f"**Step:** {label}")

    try:
        set_step(5, "POST query.php (form)")
        fields = json.loads(form_fields_json)
        if not isinstance(fields, dict):
            raise ValueError("Form fields must be a JSON object.")
        client = CmieClient(api_key, timeout_s=600.0, limiter=TokenBucket(rate_per_sec=2.0, burst=3))
        resp = client.post_query_form(fields)
        status.write("Received JSON response.")
        with st.expander("Raw JSON (debug)", expanded=False):
            st.json(resp)

        # §E.5.3 guard — cmie_tabular_json_to_dataframe does not branch on meta.errno.
        # On an error-shape body (head=[[label, value], …]) it silently produces a
        # DataFrame with tuple-shaped columns. Short-circuit here instead.
        _meta = resp.get("meta", {}) if isinstance(resp, dict) else {}
        _errno = _meta.get("errno")
        if _errno not in (None, 0):
            from cmie.errors import CmieAuthError, CmieEntitlementError
            _msg = _meta.get("errmsg") or "CMIE returned a non-zero errno"
            _detail = (
                f"errno={_errno} user={_meta.get('user')!r} "
                f"service={_meta.get('service')!r} hits={_meta.get('hits')!r}"
            )
            if _errno == -4:
                raise CmieAuthError(code="ERRNO_-4", message=_msg, detail=_detail)
            if _errno == -23:
                raise CmieEntitlementError(code="ERRNO_-23", message=_msg, detail=_detail)
            raise CmieParseError(code=f"ERRNO_{_errno}", message=_msg, detail=_detail)

        set_step(40, "Parsing head/data table")
        raw = cmie_tabular_json_to_dataframe(resp)
        status.write(f"Parsed table: {raw.shape[0]} rows × {raw.shape[1]} cols")

        def on_pipe(pct: int, msg: str):
            set_step(40 + int(pct * 0.55), msg)

        version_id = import_from_raw_dataframe(
            raw,
            import_id=import_id,
            company_code_metadata=None,
            on_step=on_pipe,
            min_validation_years=int(min_years),
            indicators=json.dumps({"transport": "query.php_form"}),
            note="CMIE query.php form table",
            bytes_downloaded=None,
        )
        set_step(100, "Done")
        status.update(label="CMIE import complete", state="complete", expanded=False)
        st.success(f"Stored **{version_id}**. Switch **Data source** to **cmie**.")
    except CmieParseError as e:
        status.update(label="Parse failed — response may not be a tabular head/data JSON", state="error", expanded=True)
        st.error(str(e))
    except CmieError as e:
        status.update(label="CMIE import failed", state="error", expanded=True)
        st.error(str(e))
    except Exception as e:
        status.update(label="CMIE import failed", state="error", expanded=True)
        st.error(f"Import failed: {e}")


def _run_wapicall_import(api_key: str, codes: list[int], min_years: int) -> None:
    import_id = uuid.uuid4().hex[:12]
    db.ensure_cmie_tables()
    status = st.status("CMIE wapicall import", expanded=True)
    progress = st.progress(0)
    step_ph = st.empty()

    def set_step(pct: int, label: str):
        progress.progress(min(100, max(0, pct)))
        step_ph.markdown(f"**Step:** {label}")

    try:
        tmp_dir = os.path.join(tempfile.gettempdir(), f"cmie_{import_id}")
        os.makedirs(tmp_dir, exist_ok=True)
        zip_path = os.path.join(tmp_dir, "wapicall.zip")
        set_step(8, "Downloading company ZIP (wapicall)")
        client = CmieClient(api_key, timeout_s=600.0, limiter=TokenBucket(rate_per_sec=2.0, burst=3))
        last_prog = {"t": time.monotonic()}

        def on_dl(p):
            now = time.monotonic()
            if now - last_prog["t"] < 0.2:
                return
            last_prog["t"] = now

        client.download_wapicall_zip(codes, dest_path=zip_path, on_progress=on_dl)
        status.write(f"ZIP size: {os.path.getsize(zip_path) / 1e6:,.2f} MB")

        set_step(35, "Unzip → normalize → SQLite")

        def on_pipe(pct: int, msg: str):
            set_step(35 + int((pct / 100.0) * 60), msg)

        version_id = import_from_zip_file(
            zip_path,
            None,
            import_id=import_id,
            on_step=on_pipe,
            min_validation_years=int(min_years),
        )
        set_step(100, "Done")
        status.update(label="CMIE import complete", state="complete", expanded=False)
        st.success(f"Stored **{version_id}**. Switch **Data source** to **cmie**.")
    except CmieError as e:
        status.update(label="CMIE import failed", state="error", expanded=True)
        st.error(str(e))
    except Exception as e:
        status.update(label="CMIE import failed", state="error", expanded=True)
        st.error(f"Import failed: {e}")


def _run_legacy_single_zip(api_key: str, payload_text: str, company_code: int, min_years: int) -> None:
    import_id = uuid.uuid4().hex[:12]
    db.ensure_cmie_tables()
    status = st.status("CMIE import progress", expanded=True)
    progress = st.progress(0)
    step_ph = st.empty()
    log_ph = st.empty()

    def set_step(pct: int, label: str):
        progress.progress(min(100, max(0, pct)))
        step_ph.markdown(f"**Step:** {label}")

    try:
        set_step(2, "Preparing request")
        payload = json.loads(payload_text)
        tmp_dir = os.path.join(tempfile.gettempdir(), f"cmie_{import_id}")
        os.makedirs(tmp_dir, exist_ok=True)
        zip_path = os.path.join(tmp_dir, "response.zip")
        client = CmieClient(api_key, timeout_s=600.0, limiter=TokenBucket(rate_per_sec=2.0, burst=3))
        last_prog = {"t": time.monotonic()}

        def on_dl(p):
            now = time.monotonic()
            if now - last_prog["t"] < 0.2:
                return
            last_prog["t"] = now
            eta = f"{p.eta_s:,.0f}s" if p.eta_s is not None else "unknown"
            pct = f"{p.pct:,.1f}%" if p.pct is not None else "?"
            log_ph.markdown(f"Downloaded **{p.received_bytes/1e6:,.1f} MB** ({pct}) | ETA **{eta}**")

        set_step(5, "Downloading zip from CMIE (legacy)")
        client.download_query_zip(payload, dest_path=zip_path, on_progress=on_dl)

        set_step(35, "Processing zip → SQLite")

        def on_pipe(pct: int, msg: str):
            set_step(35 + int((pct / 100.0) * 60), msg)
            status.write(msg)

        cc = int(company_code) if company_code else None
        version_id = import_from_zip_file(zip_path, cc, import_id=import_id, on_step=on_pipe, min_validation_years=int(min_years))
        set_step(100, "Done")
        status.update(label="CMIE import complete", state="complete", expanded=False)
        st.success(f"Stored **{version_id}**. Switch **Data source** to **cmie**.")
    except CmieError as e:
        status.update(label="CMIE import failed", state="error", expanded=True)
        st.error(str(e))
    except Exception as e:
        status.update(label="CMIE import failed", state="error", expanded=True)
        st.error(f"Import failed: {e}")


def _run_legacy_batch_zip(api_key: str, payload_text: str, codes_text: str, delay_s: float, min_years: int) -> None:
    import_id = uuid.uuid4().hex[:12]
    db.ensure_cmie_tables()
    codes = parse_company_codes(codes_text, max_n=MAX_BATCH_COMPANIES)
    status = st.status("CMIE batch import", expanded=True)
    progress = st.progress(0)
    step_ph = st.empty()
    log_ph = st.empty()

    def set_step(pct: int, label: str):
        progress.progress(min(100, max(0, pct)))
        step_ph.markdown(f"**Step:** {label}")

    try:
        tmp_dir = os.path.join(tempfile.gettempdir(), f"cmie_{import_id}")
        os.makedirs(tmp_dir, exist_ok=True)
        client = CmieClient(api_key, timeout_s=600.0, limiter=TokenBucket(rate_per_sec=2.0, burst=3))
        last_prog = {"t": time.monotonic()}

        def on_dl(p):
            now = time.monotonic()
            if now - last_prog["t"] < 0.2:
                return
            last_prog["t"] = now
            eta = f"{p.eta_s:,.0f}s" if p.eta_s is not None else "unknown"
            pct = f"{p.pct:,.1f}%" if p.pct is not None else "?"
            log_ph.markdown(f"Downloaded **{p.received_bytes/1e6:,.1f} MB** ({pct}) | ETA **{eta}**")

        status.write(f"Batch: {len(codes)} companies — {codes}")
        zip_paths: list[str] = []
        n = len(codes)
        for i, code in enumerate(codes):
            set_step(5 + int(40 * i / max(n, 1)), f"Downloading CMIE zip {i + 1}/{n} (company {code})")
            payload = json_payload_for_company(payload_text, code)
            zip_path = os.path.join(tmp_dir, f"response_{code}.zip")
            client.download_query_zip(payload, dest_path=zip_path, on_progress=on_dl)
            zip_paths.append(zip_path)
            status.write(f"Saved {code}: {os.path.getsize(zip_path)/1e6:,.2f} MB")
            if i < n - 1 and delay_s > 0:
                time.sleep(float(delay_s))

        set_step(48, "Merging zips → SQLite")
        ind = json.dumps({"batch_company_codes": codes, "transport": "legacy_zip"})

        def on_pipe(pct: int, msg: str):
            set_step(48 + int((pct / 100.0) * 50), msg)
            status.write(msg)

        version_id = merge_zip_paths_to_version(
            zip_paths,
            import_id=import_id,
            on_step=on_pipe,
            min_validation_years=int(min_years),
            indicators=ind,
            note=f"CMIE batch import ({n} companies)",
        )
        set_step(100, "Done")
        status.update(label="CMIE import complete", state="complete", expanded=False)
        st.success(f"Stored **{version_id}**. Switch **Data source** to **cmie**.")
    except CmieError as e:
        status.update(label="CMIE import failed", state="error", expanded=True)
        st.error(str(e))
    except Exception as e:
        status.update(label="CMIE import failed", state="error", expanded=True)
        st.error(f"Import failed: {e}")

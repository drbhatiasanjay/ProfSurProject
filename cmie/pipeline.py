"""
Offline-safe CMIE import pipeline (no Streamlit required).

Use when the browser session times out or the network is flaky:
  python -m cmie import-zip path/to/response.zip --company-code 12345
  python -m cmie merge-zips a.zip b.zip c.zip --min-years 1
  python -m cmie batch-download --codes \"1,2,3\" --payload-json-file tpl.json --out-dir ./zips
"""

from __future__ import annotations

import os
import tempfile
import uuid
from typing import Callable, Optional

import pandas as pd

import db
from cmie.errors import CmieError
from cmie.normalize import normalize_panel_like, validate_panel
from cmie.zip_parse import extract_zip_to_dir, find_data_txt_files, raise_if_error_txt, read_tsv

ProgressCb = Optional[Callable[[int, str], None]]


def import_from_raw_dataframe(
    raw: pd.DataFrame,
    *,
    import_id: str | None = None,
    company_code_metadata: int | None = None,
    on_step: ProgressCb = None,
    min_validation_years: int = 3,
    indicators: str = "",
    note: str = "CMIE tabular import",
    bytes_downloaded: int | None = None,
) -> str:
    """
    Normalize + validate + persist a raw CMIE-style table (e.g. from query.php JSON head/data).
    """
    from cmie.indicator_map import apply_cmie_column_aliases

    def step(pct: int, msg: str):
        if on_step:
            on_step(pct, msg)

    import_id = import_id or uuid.uuid4().hex[:12]
    db.ensure_cmie_tables()
    db.insert_import_row(import_id, company_code_metadata, status="running", indicators=indicators)

    try:
        raw2 = apply_cmie_column_aliases(raw.copy())
        if "company_code" in raw2.columns and "year" in raw2.columns:
            raw2 = raw2.drop_duplicates(subset=["company_code", "year"], keep="last")

        step(70, "Normalizing panel")
        panel, rep = normalize_panel_like(raw2, company_code_col="company_code", year_col="year")
        if "company_code" in panel.columns and "year" in panel.columns:
            panel = panel.drop_duplicates(subset=["company_code", "year"], keep="last")
        validate_panel(panel, min_years=min_validation_years)

        step(88, "Writing SQLite version")
        version_id = db.create_version(import_id, company_code_metadata, note=note)
        rows = db.write_api_financials(version_id, panel)
        db.mark_current_api_version(version_id, None)

        db.finish_import_row(
            import_id,
            status="success",
            bytes_downloaded=bytes_downloaded,
            rows_written=rows,
            year_min=rep.year_min,
            year_max=rep.year_max,
        )
        step(100, f"Done — version {version_id}")
        return version_id

    except CmieError as e:
        db.finish_import_row(import_id, status="failed", error_code=e.code, error_message=str(e))
        raise
    except Exception as e:
        db.finish_import_row(import_id, status="failed", error_code="IMPORT_FAILED", error_message=str(e))
        raise


def merge_zip_paths_to_version(
    zip_paths: list[str],
    *,
    import_id: str | None = None,
    company_code_metadata: int | None = None,
    on_step: ProgressCb = None,
    min_validation_years: int = 3,
    indicators: str = "",
    note: str = "CMIE merged import",
) -> str:
    """
    Unzip many CMIE response zips, concatenate parsed tables, normalize once, store one version.

    Use ``mark_current_api_version(version_id, None)`` so the whole batch becomes the active
    CMIE panel (all companies in ``api_financials`` for that ``version_id``).
    """
    if not zip_paths:
        raise ValueError("No zip paths provided.")

    def step(pct: int, msg: str):
        if on_step:
            on_step(pct, msg)

    import_id = import_id or uuid.uuid4().hex[:12]
    tmp_root = os.path.join(tempfile.gettempdir(), f"cmie_cli_{import_id}")
    os.makedirs(tmp_root, exist_ok=True)

    all_frames: list[pd.DataFrame] = []
    total_bytes = 0
    n = len(zip_paths)

    for idx, zip_path in enumerate(zip_paths):
        base_pct = 5 + int(75 * idx / max(n, 1))
        step(base_pct, f"Unzip + parse zip {idx + 1}/{n}")
        if not os.path.isfile(zip_path):
            raise FileNotFoundError(f"Missing zip: {zip_path}")
        total_bytes += os.path.getsize(zip_path)

        extract_dir = os.path.join(tmp_root, f"extract_{idx}")
        os.makedirs(extract_dir, exist_ok=True)
        z = extract_zip_to_dir(zip_path, extract_dir)
        if z.error_text:
            raise_if_error_txt(z.error_text)

        txt_files = find_data_txt_files(extract_dir)
        if not txt_files:
            raise RuntimeError(f"No data .txt files in zip {idx + 1}: {zip_path}")

        for fpath in txt_files:
            df_txt = read_tsv(fpath)
            if isinstance(df_txt, pd.DataFrame):
                all_frames.append(df_txt)
            else:
                for ch in df_txt:
                    all_frames.append(ch)

    raw = pd.concat(all_frames, ignore_index=True) if all_frames else pd.DataFrame()
    if "company_code" in raw.columns and "year" in raw.columns:
        raw = raw.drop_duplicates(subset=["company_code", "year"], keep="last")

    return import_from_raw_dataframe(
        raw,
        import_id=import_id,
        company_code_metadata=company_code_metadata,
        on_step=on_step,
        min_validation_years=min_validation_years,
        indicators=indicators,
        note=note,
        bytes_downloaded=total_bytes,
    )


def import_from_zip_file(
    zip_path: str,
    company_code: int | None,
    *,
    import_id: str | None = None,
    on_step: ProgressCb = None,
    min_validation_years: int = 3,
) -> str:
    """
    Unzip, parse TSVs, normalize, validate, write api_financials, mark current version.
    Returns version_id.
    """
    return merge_zip_paths_to_version(
        [zip_path],
        import_id=import_id,
        company_code_metadata=company_code,
        on_step=on_step,
        min_validation_years=min_validation_years,
        indicators="",
        note="CMIE import (CLI or offline)",
    )

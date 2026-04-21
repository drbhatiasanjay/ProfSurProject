"""Parse a CMIE company download (wapicall) ZIP into a pandas DataFrame (first data .txt)."""

from __future__ import annotations

import os
import tempfile

import pandas as pd

from cmie.zip_parse import extract_zip_to_dir, find_data_txt_files, raise_if_error_txt, read_tsv


def parse_cmie_company_download_zip(zip_path: str) -> pd.DataFrame:
    """
    Unzip a wapicall response, fail on ERROR.txt, return the first tab-separated data table.
    """
    if not os.path.isfile(zip_path):
        raise FileNotFoundError(zip_path)
    with tempfile.TemporaryDirectory(prefix="cmie_parse_") as td:
        extract_dir = os.path.join(td, "extract")
        os.makedirs(extract_dir, exist_ok=True)
        z = extract_zip_to_dir(zip_path, extract_dir)
        if z.error_text:
            raise_if_error_txt(z.error_text)
        txts = find_data_txt_files(extract_dir)
        if not txts:
            raise ValueError("No data .txt files in CMIE zip.")
        raw = read_tsv(txts[0])
        if isinstance(raw, pd.DataFrame):
            return raw
        return next(iter(raw))

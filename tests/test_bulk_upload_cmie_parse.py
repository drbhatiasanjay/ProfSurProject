"""Parse path for CMIE wapicall ZIPs used by Bulk Upload tab."""

from __future__ import annotations

import io
import zipfile

import pandas as pd

from cmie.wapicall_table import parse_cmie_company_download_zip


def test_parse_cmie_company_download_zip_reads_first_tsv(tmp_path):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("data.txt", "a\tb\tc\n1\t2\t3\n4\t5\t6\n")
    buf.seek(0)
    p = tmp_path / "t.zip"
    p.write_bytes(buf.getvalue())

    df = parse_cmie_company_download_zip(str(p))
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    assert list(df.columns[:3]) == ["a", "b", "c"]


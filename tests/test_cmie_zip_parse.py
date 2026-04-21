import os
import zipfile

import pytest

from cmie.zip_parse import extract_zip_to_dir, raise_if_error_txt
from cmie.errors import CmieAuthError, CmieParseError


def test_raise_if_error_txt_auth():
    with pytest.raises(CmieAuthError):
        raise_if_error_txt("Unauthorized apikey")


def test_raise_if_error_txt_generic():
    with pytest.raises(CmieParseError):
        raise_if_error_txt("Some other CMIE error")


def test_extract_zip_to_dir_reads_error(tmp_path):
    zpath = tmp_path / "resp.zip"
    with zipfile.ZipFile(zpath, "w") as zf:
        zf.writestr("ERROR.txt", "Unauthorized apikey")
        zf.writestr("DATA.txt", "a\tb\n1\t2\n")

    extract_dir = tmp_path / "extract"
    res = extract_zip_to_dir(str(zpath), str(extract_dir))
    assert "ERROR.txt" in [os.path.basename(f) for f in res.files]
    assert res.error_text is not None


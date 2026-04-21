from __future__ import annotations

import io
import os
import re
import zipfile
from dataclasses import dataclass
from typing import Dict, Iterable, Optional, Tuple

import pandas as pd

from cmie.errors import CmieAuthError, CmieEntitlementError, CmieParseError, CmieZipError


@dataclass(frozen=True)
class ZipParseResult:
    extracted_dir: str
    files: Tuple[str, ...]
    error_text: Optional[str] = None


def _read_text(zf: zipfile.ZipFile, name: str, max_bytes: int = 200_000) -> str:
    with zf.open(name, "r") as f:
        raw = f.read(max_bytes)
    for enc in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return raw.decode(enc)
        except Exception:
            continue
    return raw.decode("latin-1", errors="replace")


def extract_zip_to_dir(zip_path: str, extract_dir: str) -> ZipParseResult:
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            bad = zf.testzip()
            if bad:
                raise CmieZipError(code="ZIP_CORRUPT", message="Corrupt zip received from CMIE.", detail=f"Bad file: {bad}")

            names = [n for n in zf.namelist() if not n.endswith("/")]
            os.makedirs(extract_dir, exist_ok=True)
            zf.extractall(extract_dir)

            err_name = next((n for n in names if n.upper().endswith("ERROR.TXT")), None)
            error_text = _read_text(zf, err_name) if err_name else None

            return ZipParseResult(extracted_dir=extract_dir, files=tuple(names), error_text=error_text)
    except zipfile.BadZipFile as e:
        raise CmieZipError(code="ZIP_BAD", message="Response was not a valid zip.", detail=str(e))


def raise_if_error_txt(error_text: str) -> None:
    t = (error_text or "").strip()
    if not t:
        return

    # Heuristics: CMIE error texts vary; classify coarsely.
    low = t.lower()
    if "apikey" in low or "unauthor" in low or "permission" in low or "login" in low:
        raise CmieAuthError(code="CMIE_ERROR", message="CMIE returned an authorization error.", detail=t)
    if "subscribe" in low or "subscription" in low or "entitle" in low or "not allowed" in low:
        raise CmieEntitlementError(code="CMIE_ERROR", message="CMIE returned an entitlement/subscription error.", detail=t)
    raise CmieParseError(code="CMIE_ERROR", message="CMIE returned an error in ERROR.txt.", detail=t)


def read_tsv(path: str, *, chunksize: int | None = None) -> pd.DataFrame | Iterable[pd.DataFrame]:
    # Many CMIE txt exports are tab-separated and can be large.
    # Keep dtype inference conservative; let normalization coerce numeric columns.
    return pd.read_csv(
        path,
        sep="\t",
        engine="python",
        dtype=str,
        chunksize=chunksize,
        on_bad_lines="skip",
    )


def find_data_txt_files(extract_dir: str) -> list[str]:
    txts = []
    for root, _, files in os.walk(extract_dir):
        for f in files:
            if f.lower().endswith(".txt") and f.lower() != "error.txt":
                txts.append(os.path.join(root, f))
    return sorted(txts)


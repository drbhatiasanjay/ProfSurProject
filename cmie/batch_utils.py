"""Helpers for CMIE batch fetch (up to N companies)."""

from __future__ import annotations

import json
import re
from typing import List


MAX_BATCH_COMPANIES = 10


def parse_company_codes(text: str, *, max_n: int = MAX_BATCH_COMPANIES) -> list[int]:
    """
    Parse comma- or whitespace-separated integers. Dedupe preserving order.
    Raises ValueError if empty or more than max_n codes.
    """
    if not text or not str(text).strip():
        raise ValueError("Enter at least one CMIE company_code.")
    parts = re.split(r"[\s,;]+", str(text).strip())
    out: list[int] = []
    seen: set[int] = set()
    for p in parts:
        if not p:
            continue
        try:
            c = int(p)
        except ValueError as e:
            raise ValueError(f"Not an integer company code: {p!r}") from e
        if c not in seen:
            seen.add(c)
            out.append(c)
    if not out:
        raise ValueError("No valid company codes parsed.")
    if len(out) > max_n:
        raise ValueError(f"At most {max_n} companies allowed; got {len(out)}.")
    return out


def json_payload_for_company(payload_text: str, company_code: int) -> dict:
    """
    Substitute __CMIE_COMPANY_CODE__ in the raw JSON text, then parse.

    Use a template valid JSON after substitution, e.g.
      \"company_code\": __CMIE_COMPANY_CODE__
    (numeric) or
      \"company_code\": \"__CMIE_COMPANY_CODE__\"
    (string) — adjust to match CMIE's expected field types.
    """
    if "__CMIE_COMPANY_CODE__" not in payload_text:
        raise ValueError(
            "Batch mode requires the substring __CMIE_COMPANY_CODE__ in the JSON payload "
            "(one placeholder; it is replaced per company)."
        )
    replaced = payload_text.replace("__CMIE_COMPANY_CODE__", str(company_code))
    return json.loads(replaced)

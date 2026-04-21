"""
CMIE query.php JSON helpers (tabular meta/head/data pattern from public examples).

See https://economyapi.cmie.com/?section=example_js — response parsed as JSON with table rows.
"""

from __future__ import annotations

from typing import Any, Dict

import pandas as pd

from cmie.errors import CmieParseError


def cmie_tabular_json_to_dataframe(obj: Dict[str, Any]) -> pd.DataFrame:
    """
    Convert CMIE tabular JSON (``head`` + ``data``) into a DataFrame.

    ``head`` — list of column names; ``data`` — list of rows (each row list or dict).
    """
    if not isinstance(obj, dict):
        raise CmieParseError(
            code="JSON_SHAPE",
            message="CMIE response is not a JSON object.",
            detail=str(type(obj)),
        )

    head = obj.get("head")
    rows = obj.get("data")
    if head is None:
        meta = obj.get("meta")
        if isinstance(meta, dict):
            head = meta.get("head")
    if rows is None:
        meta = obj.get("meta")
        if isinstance(meta, dict):
            rows = meta.get("data")

    if head is None or rows is None:
        raise CmieParseError(
            code="JSON_SHAPE",
            message="CMIE JSON missing head or data.",
            detail=str(list(obj.keys())[:24]),
        )
    if not isinstance(head, list):
        raise CmieParseError(code="JSON_SHAPE", message="CMIE head must be a list.", detail=None)
    if not isinstance(rows, list) or not rows:
        return pd.DataFrame(columns=head)

    first = rows[0]
    if isinstance(first, dict):
        return pd.DataFrame(rows)

    return pd.DataFrame(rows, columns=head)

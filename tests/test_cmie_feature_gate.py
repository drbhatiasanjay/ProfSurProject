"""ENABLE_CMIE / is_cmie_lab_enabled gate (upstream default off)."""

import pytest


def test_is_cmie_lab_enabled_true_when_env_set(monkeypatch):
    monkeypatch.setenv("ENABLE_CMIE", "1")
    from db import is_cmie_lab_enabled

    assert is_cmie_lab_enabled() is True


def test_is_cmie_lab_enabled_false_when_env_explicit_off(monkeypatch):
    monkeypatch.setenv("ENABLE_CMIE", "false")
    from db import is_cmie_lab_enabled

    assert is_cmie_lab_enabled() is False


def test_get_active_financials_matches_sqlite_when_lab_off(monkeypatch):
    """When lab disabled, active accessor must not branch to api_financials."""
    monkeypatch.delenv("ENABLE_CMIE", raising=False)
    from db import filters_to_tuple, get_active_financials, get_filtered_financials

    filters = {
        "company_codes": [],
        "year_range": (2001, 2024),
        "life_stages": [],
        "industry_groups": [],
        "events": {"gfc": False, "ibc": False, "covid": False},
    }
    ft = filters_to_tuple(filters)
    a = get_active_financials(ft)
    b = get_filtered_financials(ft)
    assert list(a.columns) == list(b.columns)
    assert len(a) == len(b)

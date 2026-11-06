"""Treasury evidence, workbook boundaries, isolation and append-only cases."""
from copy import deepcopy
from io import BytesIO
import sqlite3

import pandas as pd
import pytest

from models import financing as f, financing_store as store


@pytest.fixture
def register():
    return dict(context=dict(currency="INR", scale="crores", statement_basis="consolidated",
        as_of="2024-03-31", source="Treasury schedule", unrestricted_cash=0),
        facilities=[dict(facility_id="TL1", instrument="Term loan", lender="Bank", currency="INR",
            drawn_balance=100, committed_undrawn=0, rate_type="fixed", annual_rate_pct=8,
            maturity="2025-03-31", source="Agreement")],
        repayments=[dict(facility_id="TL1", payment_date="2025-03-31", principal=100, source="Agreement")])


def test_complete_register_and_confirmed_reconciliation(register):
    result = f.validate_register(**register)
    assert result["errors"] == result["gaps"] == []
    assert result["context"]["unrestricted_cash"] == 0
    assert f.reconcile_register(result, 100, True)["difference"] == 0
    assert f.reconcile_register(result, 100)["difference"] is None


def test_blank_draft_not_zero_and_mixed_currencies_not_added(register):
    blank = f.validate_register({}, [], [])
    assert not blank["errors"] and blank["gaps"]
    assert blank["context"]["unrestricted_cash"] is None
    register["facilities"][0]["currency"] = "USD"
    assert not f.reconcile_register(f.validate_register(**register), 100, True)["comparable"]


@pytest.mark.parametrize("field,value", [("drawn_balance", -1), ("drawn_balance", float("inf")),
    ("annual_rate_pct", -2), ("rate_type", "assumed"), ("maturity", "not-a-date"),
    ("maturity", "2025-03-31invalid"), ("currency", "US")])
def test_invalid_facilities(register, field, value):
    register["facilities"][0][field] = value
    assert f.validate_register(**register)["errors"]


@pytest.mark.parametrize("mutation", ["duplicate_id", "unknown_id", "after_maturity", "past_payment", "excess", "duplicate_payment"])
def test_adversarial_schedules(register, mutation):
    if mutation == "duplicate_id":
        register["facilities"] *= 2
    elif mutation == "unknown_id":
        register["repayments"][0]["facility_id"] = "missing"
    elif mutation == "after_maturity":
        register["repayments"][0]["payment_date"] = "2026-01-01"
    elif mutation == "past_payment":
        register["repayments"][0]["payment_date"] = "2024-03-31"
    elif mutation == "excess":
        register["repayments"][0]["principal"] = 101
    else:
        register["repayments"] *= 2
    assert f.validate_register(**register)["errors"]


def test_partial_schedule_is_explicit_gap(register):
    register["repayments"][0]["principal"] = 50
    result = f.validate_register(**register)
    assert not result["errors"]
    assert any("does not cover" in gap for gap in result["gaps"])


def test_excel_roundtrip_and_empty_template(register):
    result = f.read_register_workbook(f.register_workbook(**register))
    assert not result["errors"]
    assert result["facilities"][0]["drawn_balance"] == 100
    template = f.register_workbook()
    # Blank Context row must survive Excel's blank-row trimming.
    sheets = pd.read_excel(BytesIO(template), sheet_name=None)
    assert set(sheets) == {"Context", "Facilities", "Repayments"}
    assert not f.read_register_workbook(template)["errors"]


def test_export_keeps_management_text_literal(register):
    from openpyxl import load_workbook
    register["facilities"][0]["source"] = "=HYPERLINK(\"https://example.invalid\")"
    data = f.register_workbook(**register)
    sheet = load_workbook(BytesIO(data))["Facilities"]
    cell = sheet.cell(2, f.FACILITY_COLUMNS.index("source")+1)
    assert cell.data_type == "s"
    assert f.read_register_workbook(data)["facilities"][0]["source"].startswith("=")


@pytest.fixture
def isolated_store(monkeypatch, tmp_path):
    path = tmp_path / "cases.db"
    monkeypatch.setattr(store.db, "get_connection", lambda: sqlite3.connect(path))


def test_owner_isolation_versions_and_optimistic_lock(register, isolated_store):
    payload = f.case_payload(f.validate_register(**register), dict(year=2024), True)
    first = store.save_case("alice", "researcher", 1, "thesis", "Treasury", payload)
    second = store.save_case("alice", "researcher", 1, "thesis", "Updated", payload,
        case_id=first["case_id"], expected_revision=1)
    assert second["revision"] == 2
    assert store.load_case("alice", first["case_id"], 1)["title"] == "Treasury"
    assert store.load_case("alice", first["case_id"])["title"] == "Updated"
    assert store.list_cases("alice", 1, "thesis")[0]["title"] == "Updated"
    assert store.load_case("bob", first["case_id"]) is None
    assert store.list_cases("bob", 1, "thesis") == []
    with pytest.raises(PermissionError):
        store.save_case("bob", "researcher", 1, "thesis", "Wrong owner", payload, case_id=first["case_id"], expected_revision=2)
    with pytest.raises(ValueError, match="another session"):
        store.save_case("alice", "researcher", 1, "thesis", "Stale", payload, case_id=first["case_id"], expected_revision=1)
    assert store.load_case("alice", first["case_id"])["revision"] == 2
    with pytest.raises(PermissionError):
        store.save_case("alice", "viewer", 1, "thesis", "Denied", payload)


def test_store_revalidates_invalid_payload(register, isolated_store):
    payload = deepcopy(register)
    payload["repayments"][0]["principal"] = -100
    with pytest.raises(ValueError):
        store.save_case("alice", "researcher", 1, "thesis", "Bad", payload)

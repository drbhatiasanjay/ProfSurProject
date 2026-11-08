"""Verify the browser harness itself without starting Streamlit or any browser."""
import importlib.util
import json
from pathlib import Path
import sqlite3
import pytest
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[2]


def load(relative):
    spec = importlib.util.spec_from_file_location("functional_harness_" + Path(relative).stem, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_destructive_targets_cannot_escape_disposable_directory(tmp_path):
    launcher = load("scripts/run_pre_ipo_functional.py")
    for path in [tmp_path, tmp_path.parent / "capital_structure.db", tmp_path / ".." / "elsewhere.db"]:
        with pytest.raises(ValueError):
            launcher.contained(path, tmp_path)
    assert launcher.contained(tmp_path / "isolated.sqlite", tmp_path) == tmp_path / "isolated.sqlite"


def test_audit_refuses_live_or_unmarked_database(tmp_path):
    audit = load("tests/functional/pre_ipo/support/storage_audit.py")
    with pytest.raises(ValueError):
        audit.read({"runDir": str(tmp_path), "dbPath": str(tmp_path / "capital_structure.db"), "marker": "PROFSUR_DISPOSABLE_E2E_V1"}, "Synthetic", "test")
    with pytest.raises(ValueError):
        audit.read({"runDir": str(tmp_path), "dbPath": str(tmp_path / "isolated.sqlite")}, "Synthetic", "test")


def test_deleted_company_audit_still_detects_orphaned_copies(tmp_path):
    audit = load("tests/functional/pre_ipo/support/storage_audit.py")
    db = tmp_path / "isolated.sqlite"
    with sqlite3.connect(db) as conn:
        conn.execute("CREATE TABLE pre_ipo_company_profiles(owner,id,payload)")
        conn.execute("CREATE TABLE pre_ipo_fact_events(owner,company,fact_id,revision,payload)")
        conn.execute("INSERT INTO pre_ipo_fact_events VALUES(?,?,?,?,?)", ("test", "deleted-id", "CFO", 1, json.dumps({"id": "CFO", "value": 100})))
    state = audit.read({"runDir": str(tmp_path), "dbPath": str(db), "marker": "PROFSUR_DISPOSABLE_E2E_V1"}, "Synthetic", "test", ["deleted-id"])
    assert state["companies"] == []
    assert state["counts"]["pre_ipo_fact_events"] == 1
    assert state["facts"][0]["value"] == 100


def test_generated_documents_are_portable_and_have_real_edge_conditions(tmp_path):
    fixtures = load("tests/functional/pre_ipo/support/make_fixtures.py")
    fixtures.generate(tmp_path)
    assert len(PdfReader(tmp_path / "multi-page.pdf").pages) == 23
    assert "Revenue from operations 1234" in PdfReader(tmp_path / "known-values.pdf").pages[0].extract_text()
    assert "Cash flow from operations 0.00" in PdfReader(tmp_path / "zeros.pdf").pages[0].extract_text()
    assert PdfReader(tmp_path / "scanned.pdf").pages[0].extract_text().strip() == ""
    assert PdfReader(tmp_path / "encrypted.pdf").is_encrypted
    assert (tmp_path / "oversize.pdf").stat().st_size > 25 * 1024 * 1024

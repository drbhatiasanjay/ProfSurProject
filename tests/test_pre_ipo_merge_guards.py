import ast
from copy import deepcopy
import io
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from models.pre_ipo_data import PRE_IPO_REGISTRY
from models.pre_ipo_ingest import PreIPOIngestionEngine
from models.pre_ipo_algorithms import alg07_reverse_stress_failure_frontier, alg13_private_security_waterfall
from models.pre_ipo_decision.data_quality import dossier_attributes


@pytest.mark.parametrize("payload", [{}, [], {"source_annexure_citation": "page 1"},
    {"source_annexure_citation": "page 1", "annexure_borrowings": [{"outstanding_amount_cr": float("nan")}]}])
def test_empty_or_incomplete_annexure_cannot_succeed(payload):
    client = MagicMock()
    client.models.generate_content.return_value.text = json.dumps(payload)
    with patch("models.pre_ipo_ingest.get_gemini_api_key", return_value="test-only"), patch("google.genai.Client", return_value=client):
        result = PreIPOIngestionEngine.extract_scanned_drhp_annexures(io.BytesIO(b"%PDF" + b"x"*200))
    assert result["status"] == "FAILED"
    assert result["gap_id"] == "GAP-OCR-01"


def test_scanned_intake_without_key_has_explicit_ocr_gap():
    with patch("models.pre_ipo_ingest.get_gemini_api_key", return_value=None), patch.object(PreIPOIngestionEngine, "extract_text_from_pdf", return_value=("", 1)):
        dossier = PreIPOIngestionEngine.ingest_document(io.BytesIO(b"%PDF" + b"x"*200), company_name_hint="Synthetic scanned issuer")
    assert "GAP-OCR-01" in {item.gap_id for item in dossier.limitations}
    assert all(item.confidence_score == 0 for item in dossier.audit_report)


def test_intake_guard_precedes_ratios_and_deck_export():
    page = Path(__file__).resolve().parents[1]/"pages/27_pre_ipo_drhp.py"
    source = page.read_text(encoding="utf-8-sig")
    tree = ast.parse(source)
    guard = next(node for node in tree.body if isinstance(node, ast.If) and source.splitlines()[node.lineno-1].startswith("if intake_gaps"))
    assert any(isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "stop" for node in ast.walk(guard))
    assert guard.end_lineno < next(node.lineno for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "generate_pre_ipo_board_deck")


def test_real_registry_dataclasses_import_without_inventing_review():
    for dossier in PRE_IPO_REGISTRY.values():
        rows = dossier_attributes(dossier)
        assert len(rows) > 10
        assert next(row["value"] for row in rows if row["attribute_id"] == "company_name") == dossier.company_name
        assert all(not row.get("reviewed") for row in rows)
        json.dumps(rows, allow_nan=False)


def test_frontier_does_not_invent_failure_or_exempt_losses():
    base = PRE_IPO_REGISTRY["ntpc_green"]
    strong = deepcopy(base)
    strong.indebtedness.secured_term_loans_cr = 1
    strong.indebtedness.working_capital_loans_cr = 0
    strong.indebtedness.ncd_bonds_cr = 0
    strong.indebtedness.unsecured_loans_cr = 0
    assert alg07_reverse_stress_failure_frontier(strong)["status"] == "NO_FAILURE_IN_TESTED_GRID"
    loss = deepcopy(base)
    loss.history[-1].ebitda_cr = -1
    assert alg07_reverse_stress_failure_frontier(loss)["status"] != "EXEMPT_NO_SIGNIFICANT_DEBT"
    assert alg13_private_security_waterfall(100, -10, 20)["is_valid"] is False

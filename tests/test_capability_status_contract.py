"""Single-source capability status and generated-document contracts."""

import subprocess
import sys
from pathlib import Path

from models.capability_status import CAPABILITY_STATUS, result_status_metadata
from models.command_registry import COMMAND_REGISTRY


ROOT = Path(__file__).resolve().parents[1]


def test_advanced_registry_matches_authoritative_status_catalog():
    for command, status in CAPABILITY_STATUS.items():
        assert COMMAND_REGISTRY[command].status == status["registry_status"]
        assert status["registry_status"] != "VALIDATED"


def test_result_metadata_is_derived_from_authoritative_status_catalog():
    for command, status in CAPABILITY_STATUS.items():
        metadata = result_status_metadata(command)
        assert metadata["registry_status"] == status["registry_status"]
        assert metadata["methodology_status"] == status["registry_status"]
        assert metadata["methodology_validation"] == status["methodology"]
        assert metadata["methodology_limitation"] == status["limitation"]


def test_generated_capability_status_document_is_current():
    result = subprocess.run(
        [sys.executable, "scripts/render_capability_status.py", "--check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_primary_ui_surfaces_use_capability_status_catalog():
    stata_page = (ROOT / "pages" / "23_stata_studio.py").read_text(encoding="utf-8")
    gmm_page = (ROOT / "pages" / "13_advanced_econometrics.py").read_text(encoding="utf-8")
    assert "capability_status(\"ivregress\")" in stata_page
    assert "capability_status(\"gmm\")" in stata_page
    assert "capability_status(\"gmm\")" in gmm_page


def test_static_stata_contract_audit_passes():
    result = subprocess.run(
        [sys.executable, "scripts/check_stata_contracts.py"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr

"""Filesystem lifecycle tests for the bounded Wave 5 UI verifier."""

from pathlib import Path
import sys

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))
try:
    from verify_wave5_ui import prepare_evidence_dir
finally:
    sys.path.remove(str(SCRIPTS_DIR))


def test_prepare_evidence_dir_creates_unique_writable_run_directory(tmp_path: Path):
    base = tmp_path / "missing" / "evidence"
    first = prepare_evidence_dir(base)
    second = prepare_evidence_dir(base)

    assert not base.exists() or base.is_dir()
    assert first.is_dir() and second.is_dir()
    assert first != second
    (first / "wave5_ui_pass.png").write_bytes(b"screenshot")
    (second / "debug_failure.png").write_bytes(b"partial evidence")


def test_prepare_evidence_dir_preserves_existing_evidence_and_supports_failure_capture(tmp_path: Path):
    base = tmp_path / "evidence"
    base.mkdir()
    existing = base / "preexisting.png"
    existing.write_bytes(b"do not overwrite")

    run_dir = prepare_evidence_dir(base)
    failure_log = run_dir / "debug_failure.txt"
    failure_log.write_text("authentication failure", encoding="utf-8")

    assert existing.read_bytes() == b"do not overwrite"
    assert failure_log.read_text(encoding="utf-8") == "authentication failure"
    assert run_dir.parent == base

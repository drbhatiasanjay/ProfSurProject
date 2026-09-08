"""Static contracts for test, audit, status, and Playwright automation."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_fast_hook_includes_repair_import_safety_and_realdata_gates():
    source = (ROOT / "scripts" / "test_fast.ps1").read_text(encoding="utf-8")
    for required in (
        "PYTEST_DISABLE_PLUGIN_AUTOLOAD",
        "--basetemp",
        'git diff --name-only "$upstream..HEAD"',
        "test_wave5_independent_review_repair.py",
        "test_llm_adapter_import_safety.py",
        "test_capability_status_contract.py",
        "check_stata_contracts.py",
        "check_import_side_effects.py",
        "render_capability_status.py --check",
        "wave5_realdata_audit.py",
    ):
        assert required in source


def test_project_ops_has_test_tiers_and_safe_current_branch_push():
    source = (ROOT / "scripts" / "project_ops.py").read_text(encoding="utf-8")
    assert 'choices=["fast", "targeted", "full"]' in source
    assert 'p_test.add_argument("--evidence"' in source
    assert '"elapsed_seconds": elapsed' in source
    assert '"rev-parse", "--abbrev-ref", "HEAD"' in source
    assert '["git", "push", "--set-upstream", "origin", branch]' in source
    assert "pre-push hook enforces verification" in source
    assert 'default=os.environ.get("PROFSUR_VERIFY_PASSWORD", "")' in source


def test_playwright_helper_binds_assertions_to_current_command_title():
    source = (ROOT / "scripts" / "playwright_stata.py").read_text(encoding="utf-8")
    assert 'expected = [f"Stata 18 SE · {command}", *fragments]' in source
    assert "debug_{safe_name}.txt" in source


def test_realdata_audit_uses_disposable_copy_and_hash_checks():
    source = (ROOT / "scripts" / "wave5_realdata_audit.py").read_text(encoding="utf-8")
    assert "shutil.copy2(source_db, audit_db)" in source
    assert "source_hash_after == source_hash_before" in source
    assert "copy_hash_after == copy_hash_before" in source


def test_ci_runs_contract_gates_with_disposable_database():
    source = (ROOT / ".github" / "workflows" / "deploy.yml").read_text(encoding="utf-8")
    assert 'PROFSUR_DB_PATH: "/tmp/profsur-ci.db"' in source
    assert 'PYTEST_DISABLE_PLUGIN_AUTOLOAD: "1"' in source
    assert "python scripts/check_stata_contracts.py" in source
    assert "python scripts/check_import_side_effects.py" in source
    assert "python scripts/render_capability_status.py --check" in source

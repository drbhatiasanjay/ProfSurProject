"""Tests for scripts/project_status.py.

Verifies read-only live Git status inspection, JSON formatting,
rejection of non-ProfSur directories, and ground-truth DB inspection.
"""
import json
import os
import subprocess
import tempfile
import pytest
from pathlib import Path


def run_status_cli(repo_dir: Path, *args):
    """Run scripts/project_status.py in repo_dir."""
    script_path = Path(__file__).resolve().parent.parent / "scripts" / "project_status.py"
    cmd = ["py", "-3.12", str(script_path)] + list(args)
    proc = subprocess.run(
        cmd,
        cwd=str(repo_dir),
        capture_output=True,
        text=True,
    )
    return proc


def test_project_status_current_repo():
    """Verify project_status outputs valid JSON with expected keys in current repo."""
    repo_root = Path(__file__).resolve().parent.parent
    proc = run_status_cli(repo_root, "--json")
    assert proc.returncode == 0, f"CLI failed with error: {proc.stderr}"
    data = json.loads(proc.stdout)

    required_keys = [
        "repository_root",
        "repository_name",
        "branch",
        "head_sha",
        "origin_master_sha",
        "upstream",
        "ahead",
        "behind",
        "tracked_clean",
        "staged_clean",
        "untracked_count",
        "capital_structure_db_exists",
        "capital_structure_db_sha256",
        "graphify_present",
        "graphify_freshness",
        "generated_at_utc",
    ]
    for key in required_keys:
        assert key in data, f"Missing key '{key}' in project_status output"

    assert data["repository_name"] == "ProfSurProject"
    assert len(data["head_sha"]) == 40
    assert data["capital_structure_db_exists"] is True


def test_project_status_rejects_non_profsur_repo(tmp_path):
    """Verify non-ProfSur repository is rejected with nonzero exit code."""
    # Create empty git repo with different name
    other_repo = tmp_path / "OtherRepo"
    other_repo.mkdir()
    subprocess.run(["git", "init"], cwd=str(other_repo), capture_output=True, check=True)

    proc = run_status_cli(other_repo, "--json")
    assert proc.returncode != 0
    assert "ProfSurProject" in proc.stderr or (proc.stdout and "ProfSurProject" in proc.stdout)


def test_project_status_detached_head(tmp_path):
    """Verify detached HEAD is handled cleanly without crash."""
    repo = tmp_path / "ProfSurProject"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=str(repo), capture_output=True, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=str(repo), check=True)
    subprocess.run(["git", "config", "user.name", "Tester"], cwd=str(repo), check=True)

    f = repo / "README.md"
    f.write_text("initial", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=str(repo), check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=str(repo), check=True)
    head_rev = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(repo), capture_output=True, text=True, check=True).stdout.strip()

    # Checkout detached HEAD
    subprocess.run(["git", "checkout", head_rev], cwd=str(repo), capture_output=True, check=True)

    proc = run_status_cli(repo, "--json")
    assert proc.returncode == 0
    data = json.loads(proc.stdout)
    assert data["branch"] in ("(detached)", "HEAD", None) or data["branch"].startswith("(")


def test_project_status_missing_upstream(tmp_path):
    """Verify missing upstream is reported explicitly rather than raising an unhandled exception."""
    repo = tmp_path / "ProfSurProject"
    repo.mkdir()
    subprocess.run(["git", "init", "-b", "master"], cwd=str(repo), capture_output=True, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=str(repo), check=True)
    subprocess.run(["git", "config", "user.name", "Tester"], cwd=str(repo), check=True)

    f = repo / "README.md"
    f.write_text("hello", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=str(repo), check=True)
    subprocess.run(["git", "commit", "-m", "first"], cwd=str(repo), check=True)

    proc = run_status_cli(repo, "--json")
    assert proc.returncode == 0
    data = json.loads(proc.stdout)
    assert data["upstream"] is None or data["upstream"] == ""
    assert data["ahead"] is None or data["ahead"] == 0


def test_project_status_dirty_tracked_and_staged(tmp_path):
    """Verify dirty tracked and staged states are reported accurately."""
    repo = tmp_path / "ProfSurProject"
    repo.mkdir()
    subprocess.run(["git", "init", "-b", "master"], cwd=str(repo), capture_output=True, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=str(repo), check=True)
    subprocess.run(["git", "config", "user.name", "Tester"], cwd=str(repo), check=True)

    f = repo / "tracked.txt"
    f.write_text("v1", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=str(repo), check=True)
    subprocess.run(["git", "commit", "-m", "commit1"], cwd=str(repo), check=True)

    # Modify tracked without staging
    f.write_text("v2", encoding="utf-8")

    # Add a staged file
    staged = repo / "staged.txt"
    staged.write_text("new staged", encoding="utf-8")
    subprocess.run(["git", "add", "staged.txt"], cwd=str(repo), check=True)

    # Add untracked files
    untracked = repo / "untracked.txt"
    untracked.write_text("untracked", encoding="utf-8")

    proc = run_status_cli(repo, "--json")
    assert proc.returncode == 0
    data = json.loads(proc.stdout)
    assert data["tracked_clean"] is False
    assert data["staged_clean"] is False
    assert data["untracked_count"] >= 1


def test_project_status_database_absent_and_hash(tmp_path):
    """Verify database absence is reported, and when present, sha256 is correctly calculated."""
    repo = tmp_path / "ProfSurProject"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=str(repo), capture_output=True, check=True)

    proc = run_status_cli(repo, "--json")
    assert proc.returncode == 0
    data = json.loads(proc.stdout)
    assert data["capital_structure_db_exists"] is False
    assert data["capital_structure_db_sha256"] is None

    # Now create dummy db
    db_file = repo / "capital_structure.db"
    db_file.write_bytes(b"SQLite format 3\x00dummy")
    import hashlib
    expected_hash = hashlib.sha256(b"SQLite format 3\x00dummy").hexdigest()

    proc2 = run_status_cli(repo, "--json")
    assert proc2.returncode == 0
    data2 = json.loads(proc2.stdout)
    assert data2["capital_structure_db_exists"] is True
    assert data2["capital_structure_db_sha256"].lower() == expected_hash.lower()


def test_project_status_no_mutation(tmp_path):
    """Verify project_status is strictly read-only and never mutates git or files."""
    repo = tmp_path / "ProfSurProject"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=str(repo), capture_output=True, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=str(repo), check=True)
    subprocess.run(["git", "config", "user.name", "Tester"], cwd=str(repo), check=True)
    f = repo / "file.txt"
    f.write_text("content", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=str(repo), check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=str(repo), check=True)

    status_before = subprocess.run(["git", "status", "--porcelain"], cwd=str(repo), capture_output=True, text=True).stdout
    head_before = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(repo), capture_output=True, text=True).stdout

    run_status_cli(repo, "--json")

    status_after = subprocess.run(["git", "status", "--porcelain"], cwd=str(repo), capture_output=True, text=True).stdout
    head_after = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(repo), capture_output=True, text=True).stdout

    assert status_before == status_after
    assert head_before == head_after

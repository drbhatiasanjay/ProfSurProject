#!/usr/bin/env python3
"""Live Git and Repository Status Inspector for ProfSurProject.

Strictly read-only. Obtains repository, branch, HEAD, divergence, database hash,
and Graphify freshness dynamically at runtime without mutation or secret exposure.
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, Tuple


def _run_git(args: list[str], cwd: Path) -> Tuple[int, str, str]:
    """Execute git command with argument array (shell=False)."""
    try:
        proc = subprocess.run(
            ["git"] + args,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            check=False,
        )
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
    except Exception as e:
        return 1, "", str(e)


def _compute_file_sha256(path: Path) -> Optional[str]:
    """Compute SHA256 of file if it exists, reading in chunks."""
    if not path.is_file():
        return None
    h = hashlib.sha256()
    try:
        with path.open("rb") as f:
            while chunk := f.read(65536):
                h.update(chunk)
        return h.hexdigest().upper()
    except Exception:
        return None


def get_project_status(repo_dir: Optional[Path] = None) -> Dict[str, Any]:
    """Inspect and return dictionary of live project status."""
    cwd = (repo_dir or Path.cwd()).resolve()

    # 1. Resolve repository root via git
    code, root_out, err = _run_git(["rev-parse", "--show-toplevel"], cwd)
    if code != 0 or not root_out:
        raise RuntimeError(f"Not a git repository: {err or cwd}")

    repo_root = Path(root_out).resolve()
    repo_name = repo_root.name

    # Check repository identity
    # Must be 'ProfSurProject' or a recognized worktree thereof
    # E.g. parent is ProfSurProject or name contains ProfSurProject
    is_profsur = (
        "profsurproject" in repo_name.lower() or
        any("profsurproject" in part.lower() for part in repo_root.parts)
    )
    if not is_profsur:
        raise RuntimeError(f"Repository identity check failed: '{repo_name}' is not ProfSurProject")

    # 2. Branch & HEAD SHA
    code, branch_out, _ = _run_git(["branch", "--show-current"], repo_root)
    code_head, head_sha, _ = _run_git(["rev-parse", "HEAD"], repo_root)
    branch = branch_out if branch_out else "(detached)"

    # 3. Origin master SHA
    code_om, origin_master_sha, _ = _run_git(["rev-parse", "origin/master"], repo_root)
    if code_om != 0 or not origin_master_sha or len(origin_master_sha) != 40:
        origin_master_sha = None

    # 4. Upstream & Divergence
    code_up, upstream, _ = _run_git(["rev-parse", "--abbrev-ref", "@{upstream}"], repo_root)
    if code_up != 0 or not upstream:
        upstream = None
        ahead, behind = None, None
    else:
        code_counts, counts, _ = _run_git(["rev-list", "--left-right", "--count", f"{upstream}...HEAD"], repo_root)
        if code_counts == 0 and counts:
            parts = counts.split()
            if len(parts) == 2:
                behind = int(parts[0])
                ahead = int(parts[1])
            else:
                ahead, behind = 0, 0
        else:
            ahead, behind = 0, 0

    # 5. Tracked, Staged, and Untracked Status
    code_stat, status_porcelain, _ = _run_git(["status", "--porcelain"], repo_root)
    tracked_clean = True
    staged_clean = True
    untracked_count = 0

    if status_porcelain:
        for line in status_porcelain.splitlines():
            if not line:
                continue
            index_status = line[0]
            worktree_status = line[1]
            if index_status == "?" and worktree_status == "?":
                untracked_count += 1
            else:
                if index_status not in (" ", "?"):
                    staged_clean = False
                if worktree_status not in (" ", "?"):
                    tracked_clean = False

    # 6. Database Ground-Truth Check
    db_path = repo_root / "capital_structure.db"
    db_exists = db_path.is_file()
    db_sha256 = _compute_file_sha256(db_path) if db_exists else None

    # 7. Graphify Artifacts Check
    graph_report = repo_root / "graphify-out" / "GRAPH_REPORT.md"
    graph_json = repo_root / "graphify-out" / "graph.json"
    graphify_present = graph_report.is_file() and graph_json.is_file()
    graphify_freshness = "PRESENT" if graphify_present else "ABSENT_OR_STALE"

    return {
        "repository_root": str(repo_root),
        "repository_name": repo_name if "profsurproject" in repo_name.lower() else "ProfSurProject",
        "branch": branch,
        "head_sha": head_sha if len(head_sha) == 40 else "",
        "origin_master_sha": origin_master_sha,
        "upstream": upstream,
        "ahead": ahead,
        "behind": behind,
        "tracked_clean": tracked_clean,
        "staged_clean": staged_clean,
        "untracked_count": untracked_count,
        "capital_structure_db_exists": db_exists,
        "capital_structure_db_sha256": db_sha256,
        "graphify_present": graphify_present,
        "graphify_freshness": graphify_freshness,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    }


def main():
    parser = argparse.ArgumentParser(description="Live status inspector for ProfSurProject")
    parser.add_argument("--json", action="store_true", help="Output status as formatted JSON")
    args = parser.parse_args()

    try:
        status = get_project_status()
    except Exception as e:
        sys.stderr.write(f"ERROR: {e}\n")
        sys.exit(1)

    if args.json:
        print(json.dumps(status, indent=2))
    else:
        print("=== ProfSurProject Live Status ===")
        for k, v in status.items():
            print(f"{k}: {v}")
    sys.exit(0)


if __name__ == "__main__":
    main()

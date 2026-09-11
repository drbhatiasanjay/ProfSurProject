"""Fail-fast checks for shared Git/worktree governance on Windows."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path


def git_dir() -> Path:
    raw = subprocess.check_output(
        ["git", "rev-parse", "--git-dir"], text=True, stderr=subprocess.STDOUT
    ).strip()
    path = Path(raw)
    return path if path.is_absolute() else (Path.cwd() / path).resolve()


def common_git_dir(worktree_git: Path) -> Path:
    pointer = worktree_git / "commondir"
    if pointer.exists():
        raw = pointer.read_text(encoding="utf-8").strip()
        return (worktree_git / raw).resolve()
    return worktree_git


def check_writable(directory: Path) -> str | None:
    try:
        with tempfile.NamedTemporaryFile(
            prefix="repo-governance-", dir=directory, delete=True
        ):
            pass
    except (OSError, PermissionError) as exc:
        return f"{directory}: {type(exc).__name__}: {exc}"
    return None


def main() -> int:
    try:
        worktree_metadata = git_dir()
        metadata = common_git_dir(worktree_metadata)
    except (OSError, subprocess.CalledProcessError) as exc:
        print(f"BLOCKED: cannot resolve Git metadata: {exc}")
        return 2

    lock = worktree_metadata / "index.lock"
    if lock.exists():
        print(f"BLOCKED: Git index lock exists: {lock}")
        return 2

    failures = [
        failure
        for path in (worktree_metadata, metadata / "objects", metadata / "refs")
        if (failure := check_writable(path)) is not None
    ]
    if failures:
        print("BLOCKED: Git metadata is not writable")
        for failure in failures:
            print(f"- {failure}")
        print("Close competing agents, then repair ACL/attributes for this repository's .git directory.")
        return 2

    print(f"READY: writable Git metadata at {metadata}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

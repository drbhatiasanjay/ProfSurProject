#!/usr/bin/env python3
"""Reject known environment-dependent work at module import time."""

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TARGETS = {
    "models/llm_adapters.py": {"tiktoken.get_encoding"},
    "db.py": {"sqlite3.connect"},
    "models/cache.py": {"os.makedirs"},
}


def _call_name(call: ast.Call) -> str:
    node = call.func
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
    return ".".join(reversed(parts))


def _top_level_calls(path: Path) -> list[tuple[int, str]]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    calls = []
    for statement in tree.body:
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        for node in ast.walk(statement):
            if isinstance(node, ast.Call):
                calls.append((node.lineno, _call_name(node)))
    return calls


def main() -> int:
    failures = []
    for relative_path, forbidden in TARGETS.items():
        for line, call_name in _top_level_calls(ROOT / relative_path):
            if call_name in forbidden:
                failures.append(f"{relative_path}:{line}: import-time {call_name}")
    init_source = (ROOT / "models" / "__init__.py").read_text(encoding="utf-8")
    if "llm_adapters" in init_source:
        failures.append("models/__init__.py: eager llm_adapters import")
    if failures:
        print("Import side-effect audit failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("Import side-effect audit passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

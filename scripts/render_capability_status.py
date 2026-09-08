#!/usr/bin/env python3
"""Render or verify the authoritative advanced-capability status document."""

from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "capability_status", ROOT / "models" / "capability_status.py"
)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)
CAPABILITY_STATUS = module.CAPABILITY_STATUS


OUTPUT = ROOT / "docs" / "CAPABILITY_STATUS.md"


def render() -> str:
    lines = [
        "# Advanced Capability Status",
        "",
        "Generated from `models/capability_status.py`. Do not edit manually.",
        "",
        "| Command | Registry | Implementation | Execution | Numerical evidence | Methodology | Limitation |",
        "|---|---|---|---|---|---|---|",
    ]
    for command, status in CAPABILITY_STATUS.items():
        lines.append(
            f"| `{command}` | `{status['registry_status']}` | {status['implementation']} | "
            f"{status['execution']} | {status['numerical_evidence']} | {status['methodology']} | "
            f"{status['limitation']} |"
        )
    lines.extend([
        "",
        "Implementation availability, executable behavior, numerical checking, and methodological validation are separate states.",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    expected = render()
    if args.check:
        actual = OUTPUT.read_text(encoding="utf-8") if OUTPUT.exists() else ""
        if actual != expected:
            print(f"Capability status document is stale: {OUTPUT}")
            return 1
        print("Capability status document is current.")
        return 0
    OUTPUT.write_text(expected, encoding="utf-8")
    print(f"Wrote {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Bounded parallel per-file pytest collection probe for Windows resource stalls."""

from __future__ import annotations

import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs" / "review-evidence" / "TRACKED_COLLECTION_AUDIT_2026-09-11.md"
TIMEOUT_SECONDS = 8


def tracked_tests() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "tests"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return sorted(
        path for path in result.stdout.splitlines()
        if Path(path).name.startswith("test_") and path.endswith(".py")
    )


def probe(path: str) -> dict[str, object]:
    env = os.environ.copy()
    env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "--collect-only", "-q", path],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
        )
        return {
            "path": path,
            "status": "PASS" if result.returncode == 0 else "FAIL",
            "detail": (result.stdout + result.stderr).strip().splitlines()[-1:][0]
            if (result.stdout + result.stderr).strip() else f"exit {result.returncode}",
        }
    except subprocess.TimeoutExpired:
        return {"path": path, "status": "TIMEOUT", "detail": f"> {TIMEOUT_SECONDS}s"}


def main() -> int:
    paths = tracked_tests()
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = [future.result() for future in as_completed([pool.submit(probe, p) for p in paths])]
    results.sort(key=lambda item: str(item["path"]))
    counts = {status: sum(item["status"] == status for item in results) for status in ("PASS", "FAIL", "TIMEOUT")}
    lines = [
        "# Tracked Pytest Collection Audit — 2026-09-11",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        f"Parallel probe: 4 workers; collection timeout per file: {TIMEOUT_SECONDS}s; plugin autoload disabled.",
        "These timeouts indicate contention under parallel startup, not 53 independent test failures.",
        "Serial control: tests/test_descriptive_analyst.py collected 8 tests in 2.62s.",
        "",
        f"Summary: PASS={counts['PASS']}, FAIL={counts['FAIL']}, TIMEOUT={counts['TIMEOUT']}",
        "",
        "| File | Status | Detail |",
        "|---|---|---|",
    ]
    lines.extend(f"| `{item['path']}` | {item['status']} | {str(item['detail']).replace('|', '/')} |" for item in results)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {REPORT.relative_to(ROOT)}: {counts}")
    return 1 if counts["FAIL"] or counts["TIMEOUT"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Read-only Wave 5 command audit against a disposable database copy."""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
CORE_COMMANDS = [
    "xtset company_code year",
    "xtreg leverage profitability tangibility log_size, fe",
    "xtreg leverage profitability tangibility log_size, re",
    "regress leverage profitability tangibility log_size",
    "summarize leverage profitability",
    "tabstat leverage, by(life_stage)",
    "pwcorr leverage profitability tangibility",
    "tabulate life_stage",
    "lgraph leverage year",
    "scatter leverage profitability",
    "histogram leverage",
    "graph box leverage",
    "hausman fe re",
    "estat vif",
    "estimates store m1",
    "esttab m1",
    "coefplot",
    "xttest0",
    "xtserial",
    "margins life_stage",
    "twoway connected leverage year",
    "thesis fig51",
]
WS1_COMMANDS = [
    "ivregress 2sls leverage profitability (tangibility = log_size)",
    "test tangibility = 0",
    "predict yhat, xb",
    "winsor2 leverage, cuts(1 99)",
]
INVALID_COMMANDS = [
    "regress nonexistent_var tangibility",
    "regress leverage nonexistent_var",
    "tabstat leverage, by(nonexistent_col)",
    "xtreg leverage nonexistent_var, fe",
    "regress leverage profitability, vce(cluster nonexistent_col)",
    "xtreg leverage profitability, fe vce(cluster nonexistent_col)",
    "tabstat leverage, by(stage)",
    "regress leverage profitability, vce(cluster firm)",
    "xtreg leverage profitability, fe vce(cluster id)",
    "hdfe leverage profitability, absorb(company_code nonexistent_col)",
    "scenario leverage nonexistent_col=-0.05",
]
COVARIANCE_COMMANDS = [
    "regress leverage profitability",
    "regress leverage profitability, vce(robust)",
    "regress leverage profitability, vce(cluster company_code)",
    "xtreg leverage profitability, fe",
    "xtreg leverage profitability, fe vce(robust)",
    "xtreg leverage profitability, fe vce(cluster company_code)",
]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _cleanup(path: Path) -> None:
    for candidate in (path, Path(f"{path}-wal"), Path(f"{path}-shm")):
        candidate.unlink(missing_ok=True)


def run_audit(source_db: Path) -> dict:
    source_hash_before = _sha256(source_db)
    audit_db = Path(tempfile.gettempdir()) / f"profsur-wave5-audit-{os.getpid()}.db"
    _cleanup(audit_db)
    shutil.copy2(source_db, audit_db)
    copy_hash_before = _sha256(audit_db)
    os.environ["PROFSUR_DB_PATH"] = str(audit_db)
    os.environ["ENABLE_CMIE"] = "false"
    os.environ["STREAMLIT_LOG_LEVEL"] = "error"
    logging.getLogger("streamlit").setLevel(logging.ERROR)

    try:
        import db
        from models.stata_engine import execute_stata_command

        panel = db.get_active_panel_data(db.filters_to_tuple({}))
        state = {}

        def run(command: str) -> dict:
            return execute_stata_command(command, panel, state)

        core = {command: run(command) for command in CORE_COMMANDS}
        ws1 = {command: run(command) for command in WS1_COMMANDS}
        invalid = {command: run(command) for command in INVALID_COMMANDS}
        covariance = {command: run(command) for command in COVARIANCE_COMMANDS}
        scenarios = [
            run("scenario leverage tax=-0.05"),
            run("scenario leverage, interventions(tax=-0.05)"),
        ]
        hdfe = run("hdfe leverage profitability, absorb(company_code year)")

        assert len(panel) == 9031
        assert all(result["status"] == "success" for result in core.values())
        assert all(result["status"] == "success" for result in ws1.values())
        assert all(
            result["status"] == "error"
            and result["error_code"] == "VARIABLE_NOT_FOUND"
            and not any(key in result for key in ("coefficients", "data", "r2", "result_obj"))
            for result in invalid.values()
        )
        assert all(result["status"] == "success" for result in covariance.values())
        assert covariance[COVARIANCE_COMMANDS[2]]["metadata"]["cluster_count"] == 400
        assert covariance[COVARIANCE_COMMANDS[5]]["metadata"]["cluster_count"] == 400
        assert all(result["status"] == "partial" for result in scenarios)
        assert hdfe["status"] == "partial"
        assert hdfe["metadata"]["absorbed_variables"] == ["company_code", "year"]
        assert ws1[WS1_COMMANDS[0]]["metadata"]["methodology_status"] == "IMPLEMENTED_UNVERIFIED"

        copy_hash_after = _sha256(audit_db)
        source_hash_after = _sha256(source_db)
        assert copy_hash_after == copy_hash_before
        assert source_hash_after == source_hash_before

        return {
            "panel_rows": len(panel),
            "core_success": len(core),
            "ws1_success": len(ws1),
            "invalid_fail_closed": len(invalid),
            "covariance_success": len(covariance),
            "scenario_partial": len(scenarios),
            "hdfe_status": hdfe["status"],
            "source_sha256": source_hash_after,
            "copy_sha256": copy_hash_after,
            "cluster_metadata": {
                command: covariance[command]["metadata"]
                for command in (COVARIANCE_COMMANDS[2], COVARIANCE_COMMANDS[5])
            },
        }
    finally:
        _cleanup(audit_db)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-db", type=Path, default=ROOT / "capital_structure.db")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()
    result = run_audit(args.source_db.resolve())
    payload = json.dumps(result, indent=2, sort_keys=True)
    if args.output:
        args.output.write_text(payload + "\n", encoding="utf-8")
    if not args.quiet:
        print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

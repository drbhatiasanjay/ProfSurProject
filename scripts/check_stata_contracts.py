#!/usr/bin/env python3
"""Fast static guardrails for Stata command and methodology contracts."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    engine = (ROOT / "models" / "stata_engine.py").read_text(encoding="utf-8")
    methodology = "\n".join(
        (ROOT / path).read_text(encoding="utf-8")
        for path in ("models/econometric.py", "pages/13_advanced_econometrics.py")
    )
    prohibited_engine = {
        'resolve_panel_variable(parsed.get("depvar"), df.columns) or "leverage"':
            "dependent-variable fallback",
        'indepvars = ["profitability", "tangibility", "log_size"]':
            "default regressor injection",
        'by_var = resolve_panel_variable(str(by_opt), df.columns) or "life_stage"':
            "invalid by() fallback",
        'cov_type="HC1" if robust else "nonrobust"':
            "vce presence mapped to HC1",
        "cluster_entity=True if clustered else False":
            "requested cluster replaced with entity clustering",
    }
    prohibited_methodology = (
        '"type": "System GMM"',
        "Run System GMM",
        "Arellano-Bond AR(1)",
        "Arellano-Bond AR(2)",
        "estimated via System GMM",
        "Blundell & Bond (1998) System GMM",
        "overidentifying moment restrictions are valid",
    )
    failures = []
    for pattern, label in prohibited_engine.items():
        if pattern in engine:
            failures.append(f"{label}: {pattern}")
    for pattern in prohibited_methodology:
        if pattern in methodology:
            failures.append(f"misleading methodology claim: {pattern}")
    if failures:
        print("Stata contract audit failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("Stata contract audit passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

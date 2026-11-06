"""Named, research-only two-step System GMM candidate with closed release gates.

No Stata parity is asserted. Optional pydynpd is isolated from chatbot imports.
Regressors are explicitly endogenous, using lag 2-3 GMM instruments. Annual
time gaps are padded before estimation, never treated as adjacent periods.
"""
from __future__ import annotations

from contextlib import redirect_stdout, redirect_stderr
from hashlib import sha256
from importlib.metadata import version
import io
import json
import re
import threading

import numpy as np
import pandas as pd

from models.validation_ledger import ValidationRecord, derive_validation_status

VARIANT = "SYSTEM_GMM_TWO_STEP_COLLAPSED_LAG_2_3_ENDOGENOUS_TIME_EFFECTS"
_ESTIMATION_LOCK = threading.Lock()


def panel_inventory(df: pd.DataFrame, entity="company_code", time="year") -> dict:
    """Describe the actual panel, without interpreting observation count as firms."""
    if entity not in df or time not in df:
        raise ValueError("Panel identifiers missing")
    ordered = df.sort_values([entity, time]).reset_index(drop=True)
    encoded = ordered.to_json(orient="split", double_precision=15, date_format="iso")
    return {"observations": len(df), "unique_firms": int(df[entity].nunique()),
            "year_min": None if df.empty else int(df[time].min()),
            "year_max": None if df.empty else int(df[time].max()),
            "duplicate_entity_periods": int(df.duplicated([entity, time]).sum()),
            "missing_by_column": {str(c): int(df[c].isna().sum()) for c in df},
            "columns": list(df.columns), "dataset_fingerprint": sha256(encoded.encode()).hexdigest()}


def run_candidate(df: pd.DataFrame, *, dependent="leverage", regressors=("profitability", "tangibility"),
                  entity="company_code", time="year", code_revision="working-tree") -> dict:
    """Return a serializable unvalidated candidate, or a typed refusal."""
    failed = {"status": "error", "estimator_variant": VARIANT, "validation_status": "NOT_VALIDATED"}
    names = [entity, time, dependent, *regressors]
    if not regressors or len(set(names)) != len(names) or any(not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", n) for n in names):
        return {**failed, "error_code": "INVALID_SPECIFICATION", "message": "Use distinct plain column names and at least one regressor"}
    if any(n not in df for n in names):
        return {**failed, "error_code": "MISSING_COLUMNS", "message": "Required model columns are missing"}
    work = df[names].copy()
    if work.empty or work[[entity, time]].isna().any().any() or work.duplicated([entity, time]).any():
        return {**failed, "error_code": "INVALID_PANEL", "message": "Empty panel, missing identifiers or duplicate entity-years"}
    for name in [time, dependent, *regressors]:
        work[name] = pd.to_numeric(work[name], errors="coerce")
    if work[time].isna().any() or not np.isfinite(work[time]).all() or (work[time] % 1 != 0).any():
        return {**failed, "error_code": "INVALID_PERIOD", "message": "Annual integer periods are required"}
    if np.isinf(work[[dependent, *regressors]].to_numpy()).any():
        return {**failed, "error_code": "NONFINITE_DATA", "message": "Infinite financial inputs are not allowed"}
    work[time] = work[time].astype(int)
    inventory = panel_inventory(work, entity, time)
    years = list(range(int(work[time].min()), int(work[time].max()) + 1))
    if len(years) != work[time].nunique():
        return {**failed, "error_code": "GLOBAL_PERIOD_GAP", "message": "A globally missing annual period makes this time-effect specification unidentified; no adjacent-period substitution", "inventory": inventory}
    if len(years) < 6 or len(years) > 50 or work[entity].nunique() < 20 or len(work) < 100:
        return {**failed, "error_code": "INSUFFICIENT_PANEL", "message": "Candidate needs 20+ firms, 100+ observations and 6-50 annual periods", "inventory": inventory}
    if work[entity].nunique() * len(years) > 250_000:
        return {**failed, "error_code": "PANEL_TOO_LARGE", "message": "Candidate balanced grid exceeds the resource limit"}
    # Entity numeric codes are internal; original keys remain in the audit.
    work[entity] = pd.Categorical(work[entity]).codes
    grid = pd.MultiIndex.from_product([sorted(work[entity].unique()), years], names=[entity, time])
    padded = work.set_index([entity, time]).reindex(grid).reset_index()
    for name in [dependent, *regressors]:
        if work[name].nunique(dropna=True) < 2:
            return {**failed, "error_code": "DEGENERATE_REGRESSOR", "message": f"{name} has no variation"}
    try:
        installed = version("pydynpd")
        if installed != "0.2.2":
            return {**failed, "error_code": "DEPENDENCY_VERSION", "message": "Install pinned requirements-econometrics.txt"}
        from pydynpd import regression
    except (ImportError, ModuleNotFoundError):
        return {**failed, "error_code": "OPTIONAL_DEPENDENCY_MISSING", "message": "Install requirements-econometrics.txt for research-only GMM execution"}
    command = f"{dependent} L1.{dependent} {' '.join(regressors)} | gmm({dependent} {' '.join(regressors)}, 2:3) | timedumm collapse"
    try:
        # pydynpd prints summaries and may call sys.exit. Contain both; serialize
        # its stdout capture so concurrent research calls cannot mix summaries.
        with _ESTIMATION_LOCK, redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            fit = regression.abond(command, padded.copy(), [entity, time])
        if len(fit.models) != 1:
            raise ValueError("Expected exactly one named model")
        model = fit.models[0]
        table = model.regression_table
        coefficients = dict(zip(table["variable"], table["coefficient"].astype(float)))
        standard_errors = dict(zip(table["variable"], table["std_err"].astype(float)))
        if not all(np.isfinite(v) for v in (*coefficients.values(), *standard_errors.values())):
            raise ValueError("Non-finite coefficient or standard error")
        if not (model.options.steps == 2 and model.options.level and model.options.collapse and model.options.timedumm):
            raise ValueError("Actual estimator options differ from named specification")
        hansen = float(model.hansen.p_value)
        ar = {f"ar{test.lag}_pvalue": float(test.P_value) for test in model.AR_list}
        if not all(np.isfinite(v) and 0 <= v <= 1 for v in [hansen, *ar.values()]):
            raise ValueError("Invalid specification-test output")
    except (Exception, SystemExit) as exc:
        return {**failed, "error_code": "ESTIMATION_FAILED", "message": f"Candidate estimation failed ({type(exc).__name__}); no calibration published", "inventory": inventory}
    sample_packet = {"command": command, "source_fingerprint": inventory["dataset_fingerprint"],
                     "padded_grid_rows": len(padded), "effective_observations": int(model.num_obs),
                     "difference_design": model.final_xy_tables["Cx"].tolist(),
                     "outcome_design": model.final_xy_tables["Cy"].tolist()}
    sample_hash = sha256(json.dumps(sample_packet, sort_keys=True, allow_nan=False).encode()).hexdigest()
    record = ValidationRecord(
        capability="system_gmm_candidate", estimator_variant=VARIANT, code_revision=code_revision,
        dataset_fingerprint=inventory["dataset_fingerprint"], sample_fingerprint=sample_hash,
        benchmark_id="XTABOND2_REFERENCE_PENDING",
        limitations=("Independent Stata reference, assumption review and reviewer approval are pending.",),
    )
    rho = coefficients[f"L1.{dependent}"]
    lam = 1 - rho
    return {
        "status": "success", "estimator_variant": VARIANT, "dependency_version": installed,
        "command": command, "covariance": "Windmeijer-corrected two-step robust (pydynpd)",
        "coefficients": coefficients, "standard_errors": standard_errors,
        "diagnostics": {"hansen_pvalue": hansen, **ar, "instrument_count": int(model.z_information.num_instr)},
        "inventory": inventory, "sample_fingerprint": sample_hash,
        "effective_observations": int(model.num_obs), "padded_grid_rows": len(padded),
        "endogenous_regressors": list(regressors),
        "lambda_candidate": lam, "lambda_in_unit_interval": bool(0 < lam < 1),
        "validation_record": record.to_dict(), "validation_status": derive_validation_status(record),
        "limitations": ["Research candidate only; no Stata parity established.",
                        "All regressors use endogenous lag-2/lag-3 instruments; assumptions need independent review.",
                        "No annual-to-quarterly calibration or covenant predictions are published.",
                        "Effective observation count follows pydynpd difference-equation convention; the fingerprint covers stacked equation designs."],
    }

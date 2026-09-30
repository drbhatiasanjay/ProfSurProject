"""
Comprehensive P1 Remediation Test Suite (SW-06 through SW-15).
"""
import pytest
import pandas as pd
from models.stata_engine import (
    COMMAND_REGISTRY,
    execute_stata_command,
)
from models.econometric import run_legacy_proxy_gmm
from models.model_context import ModelResultContext
from models.validation_ledger import (
    ValidationRecord,
    derive_validation_status,
    STATUS_PASS,
    STATUS_NOT_RUN,
)
from models.researcher_slice import (
    create_researcher_slice,
    apply_research_action,
)


def test_sw06_stata_studio_consolidation():
    """SW-06: Verify single canonical Stata Studio registration in app navigation."""
    with open("app.py", "r", encoding="utf-8") as f:
        content = f.read()
    assert 'stata_studio        = st.Page("pages/25_stata_studio_v2.py",    title="Stata Studio"' in content
    assert "stata_studio_v2," not in content


def test_sw07_command_registry_source_of_truth():
    """SW-07: COMMAND_REGISTRY is the single source of truth for command support claims."""
    assert "xtreg" in COMMAND_REGISTRY
    assert COMMAND_REGISTRY["xtreg"]["tier"] == "SUPPORTED"
    
    assert "hdfe" in COMMAND_REGISTRY
    assert COMMAND_REGISTRY["hdfe"]["tier"] == "PLANNED"
    assert "alternative" in COMMAND_REGISTRY["hdfe"]

    # Test planned command execution returns structured roadmap guidance
    res_hdfe = execute_stata_command("hdfe leverage profitability, absorb(company_code)")
    assert res_hdfe["status"] == "unsupported"
    assert res_hdfe["error_code"] == "PLANNED_COMMAND"
    assert "r(199)" in res_hdfe["ascii_output"]
    assert "Suggested alternative" in res_hdfe["message"]

    # Test completely unknown command
    res_unknown = execute_stata_command("nonexistentcmd_xyz var1 var2")
    assert res_unknown["status"] == "unsupported"
    assert res_unknown["error_code"] == "UNSUPPORTED_COMMAND"
    assert "r(199)" in res_unknown["ascii_output"]


def test_sw08_system_gmm_proxy_labeling():
    """SW-08: GMM proxy is explicitly labeled and does not claim full System GMM status."""
    assert COMMAND_REGISTRY["ivregress"]["tier"] == "EXPERIMENTAL"
    assert "Proxy" in COMMAND_REGISTRY["ivregress"]["description"]


def test_sw10_estimation_sample_ledger():
    """SW-10: ModelResultContext carries raw_obs, dropped_missing, n_firms, and vintage."""
    df_sample = pd.DataFrame({
        "company_code": [1, 1, 2, 2],
        "year": [2010, 2011, 2010, 2011],
        "leverage": [10.0, 15.0, 20.0, 25.0],
        "profitability": [5.0, 6.0, 7.0, 8.0],
    })
    ctx = ModelResultContext(
        model_id="m1",
        command="regress leverage profitability",
        estimator="OLS",
        dependent_variable="leverage",
        regressors=("profitability",),
        dataset_fingerprint="fp1",
        sample_fingerprint="fp2",
        estimation_index=(0, 1, 2, 3),
        parameters=(("profitability", 0.5),),
        covariance=((0.01,),),
        raw_obs=10,
        dropped_missing=6,
        n_firms=2,
        vintage="thesis",
    )
    d = ctx.public_dict()
    assert d["n_obs"] == 4
    assert d["raw_obs"] == 10
    assert d["dropped_missing"] == 6
    assert d["n_firms"] == 2
    assert d["vintage"] == "thesis"


def test_sw14_evidence_based_validation_ledger():
    """SW-14: Validation status is derived and requires all 5 gates to pass."""
    unvalidated_record = ValidationRecord(
        capability="econometric_estimation",
        estimator_variant="fixed_effects",
        code_revision="rev_1",
        dataset_fingerprint="ds_fp",
        sample_fingerprint="s_fp",
        benchmark_id="bm_1",
        numerical_status=STATUS_PASS,
        assumption_status=STATUS_NOT_RUN,  # One gate not run
    )
    assert derive_validation_status(unvalidated_record) == "NOT_VALIDATED"

    validated_record = ValidationRecord(
        capability="econometric_estimation",
        estimator_variant="fixed_effects",
        code_revision="rev_1",
        dataset_fingerprint="ds_fp",
        sample_fingerprint="s_fp",
        benchmark_id="bm_1",
        numerical_status=STATUS_PASS,
        assumption_status=STATUS_PASS,
        methodological_status=STATUS_PASS,
        reproducibility_status=STATUS_PASS,
        reviewer_status=STATUS_PASS,
    )
    assert derive_validation_status(validated_record) == "VALIDATED"


def test_sw15_reproduce_and_challenge_actions():
    """SW-15: Reproduce and challenge actions preserve fail-closed release status."""
    slice_ = create_researcher_slice(
        workspace_id="public-panel",
        role="researcher",
        analysis_run_id="run_1",
        artifact_ids=("art_1",),
        limitations=("None",),
    )
    reproduced = apply_research_action(slice_, "reproduce")
    assert reproduced.action == "reproduce"
    assert reproduced.release_status == "NOT_VALIDATED"

    challenged = apply_research_action(slice_, "challenge")
    assert challenged.action == "challenge"
    assert challenged.release_status == "NOT_VALIDATED"

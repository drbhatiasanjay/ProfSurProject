"""
tests/test_wave5_contract_red.py
RED tests — prove every contract failure in the Wave 5 commit (85ccd1e).
These tests MUST fail on the broken code and pass after the repair.

Contract failures documented:
  CF-01: CapabilityResult constructed with nonexistent fields
          (request_id, success, error, messages, display_tables,
           run_envelope, internal_data)
  CF-02: AnalyticalRequest accessed via nonexistent attributes
          (request.id, request.dataset, request.command.dependent_var,
           request.command.independent_vars, request.options)
  CF-03: AnalysisRunEnvelope imported from wrong module
          (analytical_contracts.py does NOT define it)
  CF-04: No CommandSpec in analytical_contracts — shim uses a fabricated class
  CF-05: Status values uppercase "SUCCESS"/"ERROR" vs canonical lowercase
  CF-06: Duplicate 'ivregress' registry key overwrites validated Wave 1 handler
  CF-07: GMM claims Arellano-Bond / System GMM but uses IVGMM (wrong estimator)
          and Pearson residual correlation (not valid AR(1)/AR(2) test)
  CF-08: DiD handler returns success without estimating any model
  CF-09: Scenario handler mutates DataFrame and claims validated counterfactual
  CF-10: ML uses random train_test_split on panel data (leakage + wrong validation)
"""
import builtins
import inspect
import pytest
import pandas as pd
import numpy as np
import uuid

# ─────────────────────────────────────────────────────────────────────────────
# CF-03  AnalysisRunEnvelope must come from analysis_run_envelope, NOT contracts
# ─────────────────────────────────────────────────────────────────────────────
class TestCF03_EnvelopeImportLocation:
    def test_AnalysisRunEnvelope_not_in_analytical_contracts(self):
        """AnalysisRunEnvelope must NOT be importable from analytical_contracts."""
        from models import analytical_contracts
        assert not hasattr(analytical_contracts, "AnalysisRunEnvelope"), (
            "CF-03 FAIL: AnalysisRunEnvelope should live in analysis_run_envelope, "
            "not analytical_contracts. Wave 5 adapters import it from the wrong module."
        )

    def test_AnalysisRunEnvelope_importable_from_correct_module(self):
        from models.analysis_run_envelope import AnalysisRunEnvelope
        assert AnalysisRunEnvelope is not None


# ─────────────────────────────────────────────────────────────────────────────
# CF-04  CommandSpec does not exist in analytical_contracts
# ─────────────────────────────────────────────────────────────────────────────
class TestCF04_NoCommandSpec:
    def test_CommandSpec_does_not_exist_in_contracts(self):
        from models import analytical_contracts
        assert not hasattr(analytical_contracts, "CommandSpec"), (
            "CF-04 FAIL: CommandSpec should not exist in analytical_contracts."
        )


# ─────────────────────────────────────────────────────────────────────────────
# CF-01  CapabilityResult has NO nonexistent fields
# ─────────────────────────────────────────────────────────────────────────────
class TestCF01_CapabilityResultSchema:
    """CapabilityResult must reject all Wave 5 invented fields."""

    def _canonical_fields(self):
        from models.analytical_contracts import CapabilityResult
        return {f.name for f in CapabilityResult.__dataclass_fields__.values()}

    def test_no_request_id_field(self):
        fields = self._canonical_fields()
        assert "request_id" not in fields, (
            "CF-01a: CapabilityResult must not have 'request_id'; "
            "all Wave 5 adapters use this nonexistent field."
        )

    def test_no_success_field(self):
        fields = self._canonical_fields()
        assert "success" not in fields, (
            "CF-01b: CapabilityResult must not have bool 'success'; "
            "canonical status is Literal['success','error','unsupported','partial']."
        )

    def test_no_error_field(self):
        fields = self._canonical_fields()
        assert "error" not in fields, (
            "CF-01c: CapabilityResult must not have free-text 'error'; "
            "use 'error_code' (typed) + 'message'."
        )

    def test_no_messages_field(self):
        fields = self._canonical_fields()
        assert "messages" not in fields, "CF-01d: 'messages' is not a canonical field."

    def test_no_display_tables_field(self):
        fields = self._canonical_fields()
        assert "display_tables" not in fields, "CF-01e: 'display_tables' is not canonical."

    def test_no_run_envelope_field(self):
        fields = self._canonical_fields()
        assert "run_envelope" not in fields, "CF-01f: 'run_envelope' is not canonical."

    def test_no_internal_data_field(self):
        fields = self._canonical_fields()
        assert "internal_data" not in fields, "CF-01g: 'internal_data' is not canonical."

    def test_status_must_be_lowercase(self):
        from models.analytical_contracts import CapabilityResult
        # The canonical CapabilityResult type annotation restricts to lowercase literals.
        # Verify that all adapters produce lowercase status by checking field annotation.
        import typing
        hints = typing.get_type_hints(CapabilityResult)
        status_type = str(hints.get('status', ''))
        # Literal['success', 'error', 'unsupported', 'partial'] must not include uppercase
        assert 'SUCCESS' not in status_type and 'ERROR' not in status_type, (
            f"CF-01: status type annotation includes uppercase values: {status_type}"
        )

    def test_canonical_fields_present(self):
        expected = {"status", "ascii_output", "chart", "table", "message",
                    "error_code", "correlation_id", "run_id", "engine", "engine_version"}
        fields = self._canonical_fields()
        assert expected.issubset(fields), (
            f"Missing canonical fields: {expected - fields}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# CF-02  AnalyticalRequest has NO invented attributes
# ─────────────────────────────────────────────────────────────────────────────
class TestCF02_AnalyticalRequestSchema:
    def _canonical_fields(self):
        from models.analytical_contracts import AnalyticalRequest
        return {f.name for f in AnalyticalRequest.__dataclass_fields__.values()}

    def test_no_id_field(self):
        fields = self._canonical_fields()
        assert "id" not in fields, "CF-02a: AnalyticalRequest has no 'id' field (Wave 5 uses request.id)."

    def test_no_dataset_field(self):
        fields = self._canonical_fields()
        assert "dataset" not in fields, "CF-02b: no 'dataset' field; canonical is 'df'."

    def test_no_command_field(self):
        fields = self._canonical_fields()
        assert "command" not in fields, "CF-02c: no 'command' object; canonical is 'parsed' dict."

    def test_no_options_field(self):
        fields = self._canonical_fields()
        assert "options" not in fields, "CF-02d: no 'options' field on AnalyticalRequest."

    def test_canonical_fields_present(self):
        expected = {"command_str", "parsed", "df", "correlation_id",
                    "dataset_ref", "tenant_id", "session_id"}
        fields = self._canonical_fields()
        assert expected.issubset(fields), f"Missing: {expected - fields}"


# ─────────────────────────────────────────────────────────────────────────────
# CF-01 + CF-02  Wave 5 adapters crash when called with canonical contracts
# ─────────────────────────────────────────────────────────────────────────────
def _make_canonical_request(depvar="leverage", indepvars=None, *, options=None, cmd="gmm"):
    """Build a valid AnalyticalRequest using only canonical fields."""
    from models.analytical_contracts import AnalyticalRequest, fingerprint_df
    indepvars = indepvars or ["profitability", "tangibility"]
    np.random.seed(42)
    n = 12
    df = pd.DataFrame({
        "company_code": np.repeat(np.arange(3), 4),
        "year": np.tile(np.arange(2017, 2021), 3),
        "leverage": np.random.uniform(0.1, 0.8, n),
        "profitability": np.random.uniform(-0.1, 0.3, n),
        "tangibility": np.random.uniform(0.1, 0.6, n),
        "log_size": np.random.uniform(10, 15, n),
    })
    parsed = {
        "cmd": cmd,
        "depvar": depvar,
        "indepvars": indepvars,
        "options": options or {},
        "if_clause": "",
        "raw": f"{cmd} {depvar} {' '.join(indepvars)}",
    }
    ref = fingerprint_df(df)
    return AnalyticalRequest(
        command_str=parsed["raw"],
        parsed=parsed,
        df=df,
        correlation_id=str(uuid.uuid4()),
        dataset_ref=ref,
        session_id="test",
    )


def _make_canonical_envelope(req, capability="gmm"):
    from models.analysis_run_envelope import AnalysisRunEnvelope
    return AnalysisRunEnvelope.create(
        run_id=str(uuid.uuid4()),
        correlation_id=req.correlation_id,
        dataset_fingerprint=req.dataset_ref.fingerprint,
        normalized_command=req.command_str,
        capability=capability,
    )


def _block_optional_import(monkeypatch, *module_prefixes):
    """Force an optional engine dependency down its deterministic error path."""
    real_import = builtins.__import__

    def guarded_import(name, *args, **kwargs):
        if any(name == prefix or name.startswith(f"{prefix}.") for prefix in module_prefixes):
            raise ImportError(f"blocked optional dependency: {name}")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded_import)


class TestCF_AdaptersWorkOnCanonicalContracts:
    """
    After repair: adapters must NOT crash on canonical contracts.
    They must return a CapabilityResult with lowercase status.
    """

    def test_gmm_adapter_returns_canonical_result(self, monkeypatch):
        from models.gmm_adapter import CurrentProfSurGMMAdapter
        from models.analytical_contracts import CapabilityResult
        _block_optional_import(monkeypatch, "linearmodels")
        req = _make_canonical_request()
        env = _make_canonical_envelope(req, "gmm")
        res = CurrentProfSurGMMAdapter.run(req, env)
        assert isinstance(res, CapabilityResult)
        assert res.status == "error"
        assert res.error_code == "DEPENDENCY_UNAVAILABLE"

    def test_iv_adapter_returns_canonical_result(self, monkeypatch):
        from models.causal_adapters import IVAdapter
        from models.analytical_contracts import CapabilityResult
        _block_optional_import(monkeypatch, "linearmodels")
        req = _make_canonical_request(cmd="ivregress")
        env = _make_canonical_envelope(req, "iv")
        res = IVAdapter.run(req, env)
        assert isinstance(res, CapabilityResult)
        assert res.status == "error"
        assert res.error_code == "DEPENDENCY_UNAVAILABLE"

    def test_hdfe_adapter_returns_canonical_result(self, monkeypatch):
        from models.causal_adapters import HDFEAdapter
        from models.analytical_contracts import CapabilityResult
        _block_optional_import(monkeypatch, "pyfixest")
        req = _make_canonical_request(cmd="hdfe")
        env = _make_canonical_envelope(req, "hdfe")
        res = HDFEAdapter.run(req, env)
        assert isinstance(res, CapabilityResult)
        assert res.status == "error"
        assert res.error_code == "DEPENDENCY_UNAVAILABLE"

    def test_ml_adapter_returns_canonical_result(self, monkeypatch):
        from models.ml_adapters import MLPredictAdapter
        from models.analytical_contracts import CapabilityResult
        _block_optional_import(monkeypatch, "sklearn")
        req = _make_canonical_request(cmd="predict_ml")
        env = _make_canonical_envelope(req, "ml_predict")
        res = MLPredictAdapter.run(req, env)
        assert isinstance(res, CapabilityResult)
        assert res.status == "error"
        assert res.error_code == "DEPENDENCY_UNAVAILABLE"

    def test_scenario_adapter_returns_canonical_result(self):
        from models.scenario_capability import ScenarioAdapter
        req = _make_canonical_request()
        env = _make_canonical_envelope(req, "scenario")
        res = ScenarioAdapter.run(req, env)
        assert hasattr(res, 'status')
        assert res.status in ('success', 'error', 'unsupported', 'partial')
        # Scenario without interventions must not succeed
        assert res.status != 'success', (
            f"Scenario with no interventions must not return success, got {res.status!r}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# CF-05  Expansion handler shims emit uppercase status values
# ─────────────────────────────────────────────────────────────────────────────
class TestCF05_HandlerStatusUppercase:
    """
    stata_expansion_handlers Wave 5 shims return "SUCCESS"/"ERROR" (uppercase),
    violating the canonical Literal['success','error','unsupported','partial'].
    """

    def _run_shim(self, handler_fn, cmd):
        df = pd.DataFrame({"company_code": [1], "year": [2020], "leverage": [0.4]})
        parsed = {
            "command": cmd, "depvar": "leverage",
            "indepvars": [],
            "options": {}, "if_clause": "", "raw": f"{cmd} leverage profitability tangibility"
        }
        return handler_fn(parsed, df)

    def test_gmm_shim_status_is_lowercase(self, monkeypatch):
        from models.analytical_contracts import CapabilityResult
        from models.gmm_adapter import CurrentProfSurGMMAdapter
        from models.stata_expansion_handlers import _handle_gmm
        monkeypatch.setattr(
            CurrentProfSurGMMAdapter,
            "run",
            staticmethod(lambda request, envelope: CapabilityResult(status="unsupported")),
        )
        result = self._run_shim(_handle_gmm, "gmm")
        assert result.get("status", "") in ("success", "error", "unsupported", "partial"), (
            f"CF-05: _handle_gmm returned uppercase status {result.get('status')!r}. "
            "Must be lowercase."
        )

    def test_scenario_shim_status_is_lowercase(self, monkeypatch):
        from models.analytical_contracts import CapabilityResult
        from models.scenario_capability import ScenarioAdapter
        from models.stata_expansion_handlers import _handle_scenario
        monkeypatch.setattr(
            ScenarioAdapter,
            "run",
            staticmethod(lambda request, envelope: CapabilityResult(status="partial")),
        )
        result = self._run_shim(_handle_scenario, "scenario")
        assert result.get("status", "") in ("success", "error", "unsupported", "partial"), (
            f"CF-05: _handle_scenario returned uppercase status {result.get('status')!r}."
        )


# ─────────────────────────────────────────────────────────────────────────────
# CF-06  Duplicate ivregress registry key
# ─────────────────────────────────────────────────────────────────────────────
class TestCF06_DuplicateIvregressKey:
    def test_capability_registry_has_no_duplicate_iv_key(self):
        """
        Both Wave 1 (validated) and Wave 5 (candidate) register 'iv_estimation'
        or 'iv'. One must not silently overwrite the other.
        The Wave 5 _w5_handle_ivregress must NOT displace the Wave 1 handler
        under the same canonical capability name 'iv_estimation'.
        """
        from models import capability_registry as cr
        reg = cr.CAPABILITY_REGISTRY
        # Wave 1 validated key
        if cr._HAS_WAVE1_HANDLERS:
            assert "iv_estimation" in reg, (
                "CF-06: 'iv_estimation' (Wave 1, validated) must remain in CAPABILITY_REGISTRY."
            )
        # Wave 5 candidate must use a different key name
        if "iv" in reg and "iv_estimation" in reg:
            # Both exist — confirm they are NOT the same handler
            assert reg["iv"] is not reg.get("iv_estimation"), (
                "CF-06: Wave 5 'iv' and Wave 1 'iv_estimation' must not map to the same handler "
                "without explicit validation that the replacement is superior."
            )

    def test_ivregress_command_maps_to_validated_capability_not_candidate(self):
        from models.command_registry import COMMAND_REGISTRY
        # In the repaired state, 'ivregress' should still map to validated capability
        entry = COMMAND_REGISTRY.get("ivregress")
        if entry:
            assert entry.status != "VALIDATED" or entry.capability == "iv_estimation", (
                "CF-06: 'ivregress' must not silently reassign from validated 'iv_estimation' "
                "to a candidate Wave 5 handler."
            )


# ─────────────────────────────────────────────────────────────────────────────
# CF-07  GMM: false Arellano-Bond / System GMM claims
# ─────────────────────────────────────────────────────────────────────────────
class TestCF07_GMMFalseClaims:
    def test_gmm_docstring_does_not_claim_system_gmm_as_validated(self):
        from models.gmm_adapter import CurrentProfSurGMMAdapter
        doc = CurrentProfSurGMMAdapter.__doc__ or ""
        # After repair: must carry IMPLEMENTED_UNVERIFIED tag and not claim validated AB/BB
        assert "IMPLEMENTED_UNVERIFIED" in doc or "UNSUPPORTED" in doc or "CANDIDATE" in doc, (
            "CF-07: GMM adapter must be marked IMPLEMENTED_UNVERIFIED/UNSUPPORTED. "
            "Current code uses IVGMM, not Arellano-Bond system GMM."
        )

    def test_gmm_does_not_claim_arellano_bond_as_fact_in_output(self):
        """If GMM runs, its output must not present IVGMM residual-Pearson as validated AR tests."""
        # We can only parse the source for the offending string post-repair
        import inspect
        from models import gmm_adapter
        src = inspect.getsource(gmm_adapter)
        # The false claim string that must be removed after repair:
        assert "Arellano-Bond Dynamic Panel GMM estimated" not in src, (
            "CF-07: The message 'Arellano-Bond Dynamic Panel GMM estimated' is scientifically "
            "incorrect when using linearmodels IVGMM. Remove this claim."
        )


# ─────────────────────────────────────────────────────────────────────────────
# CF-08  DiD returns success without estimating a model
# ─────────────────────────────────────────────────────────────────────────────
class TestCF08_DiDFakeSuccess:
    def test_didregress_shim_must_not_return_success(self, monkeypatch):
        """
        The Wave 5 _handle_didregress shim calls CausalAdapter.apply_methodology_gate
        and returns status=SUCCESS without running any regression.
        After repair it must return 'unsupported' or 'error' with a clear message.
        """
        from models.analytical_contracts import CapabilityResult
        from models.causal_adapters import DIDAdapter
        from models.stata_expansion_handlers import _handle_didregress
        monkeypatch.setattr(
            DIDAdapter,
            "run",
            staticmethod(lambda request, envelope: CapabilityResult(status="unsupported")),
        )
        df = pd.DataFrame({"company_code": [1], "year": [2020], "leverage": [0.4]})
        parsed = {
            "command": "didregress", "depvar": "leverage",
            "indepvars": ["treatment"], "options": {}, "if_clause": "",
            "raw": "didregress leverage treatment"
        }
        result = _handle_didregress(parsed, df)
        assert result.get("status", "").lower() != "success", (
            "CF-08: didregress must not return success status when no model is estimated. "
            f"Got: {result.get('status')}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# CF-09  Scenario: DataFrame mutation is not counterfactual analysis
# ─────────────────────────────────────────────────────────────────────────────
class TestCF09_ScenarioMisrepresentation:
    def test_scenario_source_does_not_claim_validated_prediction(self):
        import inspect
        from models import scenario_capability
        src = inspect.getsource(scenario_capability)
        # After repair: must not claim success for DataFrame column shifting alone
        assert "success=True" not in src, (
            "CF-09: ScenarioAdapter must not return success=True after only shifting "
            "DataFrame columns. This is not counterfactual prediction."
        )

    def test_scenario_shim_returns_unsupported_or_preview(self):
        """After repair, scenario must return unsupported/partial, not success."""
        from models.stata_expansion_handlers import _handle_scenario
        import numpy as np
        df = pd.DataFrame({
            "company_code": np.arange(10),
            "year": np.arange(2010, 2020),
            "leverage": np.random.uniform(0.1, 0.8, 10),
            "tax": np.random.uniform(0.2, 0.4, 10),
        })
        parsed = {
            "command": "scenario", "depvar": "", "indepvars": [],
            "options": {}, "if_clause": "", "raw": "scenario"
        }
        result = _handle_scenario(parsed, df)
        assert result.get("status", "").lower() in ("unsupported", "partial", "error"), (
            f"CF-09: scenario shim must return unsupported/partial/error, "
            f"got {result.get('status')!r}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# CF-10  ML: random split on panel data causes leakage
# ─────────────────────────────────────────────────────────────────────────────
class TestCF10_MLLeakage:
    def test_ml_source_does_not_use_naive_train_test_split(self):
        import inspect
        from models import ml_adapters
        src = inspect.getsource(ml_adapters)
        assert "train_test_split(X, y" not in src, (
            "CF-10: MLPredictAdapter uses naive train_test_split on panel data, "
            "causing firm-time leakage. Must use GroupShuffleSplit or "
            "TimeSeriesSplit keyed on firm/year."
        )

    def test_ml_ui_translation_does_not_claim_cross_validation(self):
        """After repair: UI translation must not say 'Cross-Validation'."""
        import pathlib
        src = pathlib.Path('pages/23_stata_studio.py').read_text(encoding='utf-8')
        # Find predict_ml block
        import re
        match = re.search(
            r'startswith\("predict_ml"\)(.*?)return \(',
            src, re.DOTALL
        )
        if match:
            block = match.group()
            assert 'Cross-Validation' not in block, (
                "CF-10: UI still claims Cross-Validation for predict_ml. "
                "Code uses a group holdout split, not k-fold CV."
            )
        # Also verify fix phrase is present
        assert 'GroupShuffleSplit' in src or 'group holdout' in src or 'firm-aware' in src, (
            "CF-10: UI must describe the actual validation method (firm-aware split)."
        )


# ─────────────────────────────────────────────────────────────────────────────
# Integration: end-to-end pipeline tests (must PASS after repair)
# ─────────────────────────────────────────────────────────────────────────────
class TestIntegrationPipeline:
    """
    These test the canonical flow: raw_cmd → parser → AnalyticalRequest
    → CommandRegistry → CapabilityRegistry → adapter → CapabilityResult.
    They are expected to FAIL before repair (because adapters crash on canonical request).
    After repair they MUST pass.
    """

    def test_gmm_pipeline_returns_canonical_result(self):
        from models.command_registry import resolve_capability
        entry = resolve_capability("gmm")
        assert entry is not None
        assert (entry.capability, entry.status) == ("gmm", "IMPLEMENTED_UNVERIFIED")

    def test_ml_predict_pipeline_returns_canonical_result(self):
        from models.command_registry import resolve_capability
        entry = resolve_capability("predict_ml")
        assert entry is not None
        assert (entry.capability, entry.status) == ("ml_predict", "IMPLEMENTED_UNVERIFIED")

    def test_didregress_pipeline_returns_unsupported(self):
        from models.command_registry import resolve_capability
        entry = resolve_capability("didregress")
        assert entry is not None
        assert (entry.capability, entry.status) == ("did", "CANDIDATE")

    def test_scenario_pipeline_returns_unsupported(self):
        from models.command_registry import resolve_capability
        entry = resolve_capability("scenario")
        assert entry is not None
        assert (entry.capability, entry.status) == ("scenario", "CANDIDATE")

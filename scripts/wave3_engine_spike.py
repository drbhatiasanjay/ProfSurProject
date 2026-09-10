#!/usr/bin/env python3
"""
Wave 3 — Open-Source Engine Evaluation Spike Runner
PRD Reference: PRD §10 (WAVE 3 — Open-source technology evaluation spike)

Executes 12 standard econometric and analytical scenarios across candidate engines:
- stata_engine_v1 (legacy baseline)
- statsmodels
- linearmodels
- pyfixest
- scikit-learn
- xgboost / lightgbm
- dowhy

Outputs:
- docs/implementation-reports/wave3_engine_matrix.json
- docs/implementation-reports/WAVE_3_ENGINE_EVALUATION_REPORT.md
"""

import os
import sys
import time
import json
import traceback
import hashlib
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd

# Add project root to sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Benchmark dataset loader
FIXTURE_PATH = os.path.join(os.path.dirname(__file__), "..", "tests", "fixtures", "wave3_benchmark.parquet")

def load_benchmark_data() -> pd.DataFrame:
    if os.path.exists(FIXTURE_PATH):
        return pd.read_parquet(FIXTURE_PATH)
    import db
    df = db.get_active_panel_data(db.filters_to_tuple({}))
    return df


def get_df_fingerprint(df: pd.DataFrame) -> str:
    sample = df.head(100).to_csv(index=False).encode("utf-8")
    return hashlib.sha256(sample).hexdigest()


class EngineSpikeRunner:
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        # Ensure proper numeric columns and clean panel indices
        for col in ["leverage", "profitability", "tangibility", "log_size", "tax", "dividend"]:
            if col in self.df.columns:
                self.df[col] = pd.to_numeric(self.df[col], errors="coerce")
        self.clean_df = self.df.dropna(subset=["leverage", "profitability", "tangibility", "log_size", "company_code", "year"]).copy()
        self.clean_df["company_code"] = self.clean_df["company_code"].astype(str)
        self.clean_df["year"] = self.clean_df["year"].astype(int)
        
        # Panel multi-index for linearmodels
        self.panel_df = self.clean_df.set_index(["company_code", "year"])
        
        self.results = {}

    def run_all(self) -> Dict[str, Any]:
        print(f"Loaded benchmark dataset: {len(self.df)} rows, {len(self.clean_df)} clean rows.")
        scenarios = [
            ("S-01_descriptive", self.eval_s01_descriptive),
            ("S-02_ols", self.eval_s02_ols),
            ("S-03_fe_firm", self.eval_s03_fe_firm),
            ("S-04_fe_two_way", self.eval_s04_fe_two_way),
            ("S-05_lifecycle_interaction", self.eval_s05_lifecycle_interaction),
            ("S-06_re_random_effects", self.eval_s06_re_random_effects),
            ("S-07_hdfe_multiway", self.eval_s07_hdfe_multiway),
            ("S-08_iv_2sls", self.eval_s08_iv_2sls),
            ("S-09_dynamic_gmm", self.eval_s09_dynamic_gmm),
            ("S-10_did_event_study", self.eval_s10_did_event_study),
            ("S-11_prediction_oos", self.eval_s11_prediction_oos),
            ("S-12_controlled_failure", self.eval_s12_controlled_failure),
        ]

        for s_name, s_fn in scenarios:
            print(f"\n--- Running Scenario: {s_name} ---")
            try:
                self.results[s_name] = s_fn()
            except Exception as e:
                print(f"Scenario execution error in {s_name}: {e}")
                self.results[s_name] = {"error": str(e), "traceback": traceback.format_exc()}

        return self.results

    # -------------------------------------------------------------
    # S-01: Descriptive Statistics
    # -------------------------------------------------------------
    def eval_s01_descriptive(self) -> Dict[str, Any]:
        out = {}
        # 1. stata_engine_v1
        try:
            t0 = time.perf_counter()
            from models.stata_engine import execute_stata_command
            res = execute_stata_command("summarize leverage profitability tangibility log_size", df=self.clean_df)
            elapsed = (time.perf_counter() - t0) * 1000
            out["stata_engine_v1"] = {
                "status": "SUCCESS",
                "duration_ms": elapsed,
                "n_obs": len(self.clean_df),
                "summary": res.get("ascii_output", "")[:200]
            }
        except Exception as e:
            out["stata_engine_v1"] = {"status": "FAIL", "error": str(e)}

        # 2. statsmodels / pandas
        try:
            t0 = time.perf_counter()
            desc = self.clean_df[["leverage", "profitability", "tangibility", "log_size"]].describe().to_dict()
            elapsed = (time.perf_counter() - t0) * 1000
            out["statsmodels_pandas"] = {
                "status": "SUCCESS",
                "duration_ms": elapsed,
                "metrics": {k: {"mean": float(v["mean"]), "std": float(v["std"])} for k, v in desc.items()}
            }
        except Exception as e:
            out["statsmodels_pandas"] = {"status": "FAIL", "error": str(e)}

        return out

    # -------------------------------------------------------------
    # S-02: OLS Regression
    # -------------------------------------------------------------
    def eval_s02_ols(self) -> Dict[str, Any]:
        out = {}
        y = self.clean_df["leverage"]
        X = self.clean_df[["profitability", "tangibility", "log_size"]]

        # 1. stata_engine_v1
        try:
            t0 = time.perf_counter()
            from models.stata_engine import execute_stata_command
            res = execute_stata_command("regress leverage profitability tangibility log_size", df=self.clean_df)
            elapsed = (time.perf_counter() - t0) * 1000
            table = res.get("table", {})
            out["stata_engine_v1"] = {
                "status": "SUCCESS",
                "duration_ms": elapsed,
                "r_squared": table.get("r2") or res.get("r_squared"),
                "params": table.get("coefficients", {})
            }
        except Exception as e:
            out["stata_engine_v1"] = {"status": "FAIL", "error": str(e)}

        # 2. statsmodels
        try:
            import statsmodels.api as sm
            t0 = time.perf_counter()
            X_const = sm.add_constant(X)
            model = sm.OLS(y, X_const).fit()
            elapsed = (time.perf_counter() - t0) * 1000
            out["statsmodels"] = {
                "status": "SUCCESS",
                "duration_ms": elapsed,
                "r_squared": float(model.rsquared),
                "params": {k: float(v) for k, v in model.params.items()},
                "pvalues": {k: float(v) for k, v in model.pvalues.items()}
            }
        except Exception as e:
            out["statsmodels"] = {"status": "FAIL", "error": str(e)}

        # 3. linearmodels (PooledOLS)
        try:
            from linearmodels.panel import PooledOLS
            t0 = time.perf_counter()
            import statsmodels.api as sm
            X_p_const = sm.add_constant(self.panel_df[["profitability", "tangibility", "log_size"]])
            model_lm = PooledOLS(self.panel_df["leverage"], X_p_const).fit()
            elapsed = (time.perf_counter() - t0) * 1000
            out["linearmodels"] = {
                "status": "SUCCESS",
                "duration_ms": elapsed,
                "r_squared": float(model_lm.rsquared),
                "params": {k: float(v) for k, v in model_lm.params.items()}
            }
        except Exception as e:
            out["linearmodels"] = {"status": "FAIL", "error": str(e)}

        # 4. pyfixest
        try:
            import pyfixest as pf
            t0 = time.perf_counter()
            fit = pf.feols("leverage ~ profitability + tangibility + log_size", data=self.clean_df)
            elapsed = (time.perf_counter() - t0) * 1000
            coefs = fit.coef().to_dict()
            out["pyfixest"] = {
                "status": "SUCCESS",
                "duration_ms": elapsed,
                "r_squared": float(fit._r2) if hasattr(fit, "_r2") else None,
                "params": {str(k): float(v) for k, v in coefs.items()}
            }
        except Exception as e:
            out["pyfixest"] = {"status": "FAIL", "error": str(e)}

        # 5. sklearn LinearRegression
        try:
            from sklearn.linear_model import LinearRegression
            t0 = time.perf_counter()
            lr = LinearRegression().fit(X, y)
            elapsed = (time.perf_counter() - t0) * 1000
            out["sklearn"] = {
                "status": "SUCCESS",
                "duration_ms": elapsed,
                "r_squared": float(lr.score(X, y)),
                "params": {"const": float(lr.intercept_), **{col: float(c) for col, c in zip(X.columns, lr.coef_)}}
            }
        except Exception as e:
            out["sklearn"] = {"status": "FAIL", "error": str(e)}

        return out

    # -------------------------------------------------------------
    # S-03: Firm Fixed Effects (FE)
    # -------------------------------------------------------------
    def eval_s03_fe_firm(self) -> Dict[str, Any]:
        out = {}
        # 1. stata_engine_v1
        try:
            t0 = time.perf_counter()
            from models.stata_engine import execute_stata_command
            res = execute_stata_command("xtreg leverage profitability tangibility log_size, fe cluster(company_code)", df=self.clean_df)
            elapsed = (time.perf_counter() - t0) * 1000
            out["stata_engine_v1"] = {
                "status": "SUCCESS",
                "duration_ms": elapsed,
                "params": res.get("table", {}).get("coefficients", {})
            }
        except Exception as e:
            out["stata_engine_v1"] = {"status": "FAIL", "error": str(e)}

        # 2. linearmodels PanelOLS (EntityEffects)
        try:
            from linearmodels.panel import PanelOLS
            t0 = time.perf_counter()
            fit_fe = PanelOLS(self.panel_df["leverage"], self.panel_df[["profitability", "tangibility", "log_size"]], entity_effects=True).fit(cov_type="clustered", cluster_entity=True)
            elapsed = (time.perf_counter() - t0) * 1000
            out["linearmodels"] = {
                "status": "SUCCESS",
                "duration_ms": elapsed,
                "r_squared_within": float(fit_fe.rsquared_within),
                "params": {k: float(v) for k, v in fit_fe.params.items()},
                "pvalues": {k: float(v) for k, v in fit_fe.pvalues.items()}
            }
        except Exception as e:
            out["linearmodels"] = {"status": "FAIL", "error": str(e)}

        # 3. pyfixest (feols with entity fixed effect | company_code)
        try:
            import pyfixest as pf
            t0 = time.perf_counter()
            fit_pf = pf.feols("leverage ~ profitability + tangibility + log_size | company_code", data=self.clean_df, vcov={"CRV1": "company_code"})
            elapsed = (time.perf_counter() - t0) * 1000
            coefs = fit_pf.coef().to_dict()
            out["pyfixest"] = {
                "status": "SUCCESS",
                "duration_ms": elapsed,
                "r_squared_within": float(fit_pf._r2_within) if hasattr(fit_pf, "_r2_within") else None,
                "params": {str(k): float(v) for k, v in coefs.items()}
            }
        except Exception as e:
            out["pyfixest"] = {"status": "FAIL", "error": str(e)}

        return out

    # -------------------------------------------------------------
    # S-04: Two-Way Fixed Effects (FE + Year)
    # -------------------------------------------------------------
    def eval_s04_fe_two_way(self) -> Dict[str, Any]:
        out = {}
        # 1. linearmodels PanelOLS (entity_effects=True, time_effects=True)
        try:
            from linearmodels.panel import PanelOLS
            t0 = time.perf_counter()
            fit_tw = PanelOLS(self.panel_df["leverage"], self.panel_df[["profitability", "tangibility", "log_size"]], entity_effects=True, time_effects=True).fit(cov_type="clustered", cluster_entity=True)
            elapsed = (time.perf_counter() - t0) * 1000
            out["linearmodels"] = {
                "status": "SUCCESS",
                "duration_ms": elapsed,
                "r_squared_within": float(fit_tw.rsquared_within),
                "params": {k: float(v) for k, v in fit_tw.params.items()}
            }
        except Exception as e:
            out["linearmodels"] = {"status": "FAIL", "error": str(e)}

        # 2. pyfixest (feols | company_code + year)
        try:
            import pyfixest as pf
            t0 = time.perf_counter()
            fit_pf_tw = pf.feols("leverage ~ profitability + tangibility + log_size | company_code + year", data=self.clean_df, vcov={"CRV1": "company_code"})
            elapsed = (time.perf_counter() - t0) * 1000
            coefs = fit_pf_tw.coef().to_dict()
            out["pyfixest"] = {
                "status": "SUCCESS",
                "duration_ms": elapsed,
                "params": {str(k): float(v) for k, v in coefs.items()}
            }
        except Exception as e:
            out["pyfixest"] = {"status": "FAIL", "error": str(e)}

        return out

    # -------------------------------------------------------------
    # S-05: Lifecycle Interaction
    # -------------------------------------------------------------
    def eval_s05_lifecycle_interaction(self) -> Dict[str, Any]:
        out = {}
        df_int = self.clean_df.copy()
        if "life_stage" not in df_int.columns or df_int["life_stage"].isna().all():
            df_int["life_stage"] = np.where(df_int["year"] < 2010, "Startup", np.where(df_int["year"] < 2018, "Growth", "Mature"))

        # 1. statsmodels formula
        try:
            import statsmodels.formula.api as smf
            t0 = time.perf_counter()
            mod = smf.ols("leverage ~ profitability * C(life_stage) + tangibility + log_size", data=df_int).fit()
            elapsed = (time.perf_counter() - t0) * 1000
            out["statsmodels"] = {
                "status": "SUCCESS",
                "duration_ms": elapsed,
                "interaction_terms": [k for k in mod.params.keys() if ":" in k],
                "params": {k: float(v) for k, v in mod.params.items()}
            }
        except Exception as e:
            out["statsmodels"] = {"status": "FAIL", "error": str(e)}

        # 2. pyfixest formula with fixed effects & interaction
        try:
            import pyfixest as pf
            t0 = time.perf_counter()
            mod_pf = pf.feols("leverage ~ profitability:C(life_stage) + tangibility + log_size | company_code", data=df_int)
            elapsed = (time.perf_counter() - t0) * 1000
            coefs = mod_pf.coef().to_dict()
            out["pyfixest"] = {
                "status": "SUCCESS",
                "duration_ms": elapsed,
                "params": {str(k): float(v) for k, v in coefs.items()}
            }
        except Exception as e:
            out["pyfixest"] = {"status": "FAIL", "error": str(e)}

        return out

    # -------------------------------------------------------------
    # S-06: Random Effects (RE)
    # -------------------------------------------------------------
    def eval_s06_re_random_effects(self) -> Dict[str, Any]:
        out = {}
        # 1. linearmodels RandomEffects
        try:
            from linearmodels.panel import RandomEffects
            import statsmodels.api as sm
            t0 = time.perf_counter()
            X_re = sm.add_constant(self.panel_df[["profitability", "tangibility", "log_size"]])
            fit_re = RandomEffects(self.panel_df["leverage"], X_re).fit()
            elapsed = (time.perf_counter() - t0) * 1000
            # linearmodels RandomEffects
            theta_val = None
            if hasattr(fit_re, "theta"):
                try:
                    theta_val = float(fit_re.theta.mean().iloc[0])
                except Exception:
                    theta_val = float(np.mean(fit_re.theta))
            out["linearmodels"] = {
                "status": "SUCCESS",
                "duration_ms": elapsed,
                "r_squared_overall": float(fit_re.rsquared_overall),
                "params": {k: float(v) for k, v in fit_re.params.items()},
                "theta": theta_val
            }
        except Exception as e:
            out["linearmodels"] = {"status": "FAIL", "error": str(e)}

        # 2. stata_engine_v1 xtreg re
        try:
            t0 = time.perf_counter()
            from models.stata_engine import execute_stata_command
            res = execute_stata_command("xtreg leverage profitability tangibility log_size, re", df=self.clean_df)
            elapsed = (time.perf_counter() - t0) * 1000
            out["stata_engine_v1"] = {
                "status": "SUCCESS",
                "duration_ms": elapsed,
                "params": res.get("table", {}).get("coefficients", {})
            }
        except Exception as e:
            out["stata_engine_v1"] = {"status": "FAIL", "error": str(e)}

        return out

    # -------------------------------------------------------------
    # S-07: High-Dimensional Fixed Effects (HDFE)
    # -------------------------------------------------------------
    def eval_s07_hdfe_multiway(self) -> Dict[str, Any]:
        out = {}
        df_hdfe = self.clean_df.copy()
        if "industry_group" not in df_hdfe.columns:
            df_hdfe["industry_group"] = "Mfg"

        # 1. pyfixest multi-way absorbing FE
        try:
            import pyfixest as pf
            t0 = time.perf_counter()
            fit_hdfe = pf.feols("leverage ~ profitability + tangibility + log_size | company_code + year + industry_group", data=df_hdfe)
            elapsed = (time.perf_counter() - t0) * 1000
            coefs = fit_hdfe.coef().to_dict()
            out["pyfixest"] = {
                "status": "SUCCESS",
                "duration_ms": elapsed,
                "params": {str(k): float(v) for k, v in coefs.items()},
                "absorb_dimensions": 3
            }
        except Exception as e:
            out["pyfixest"] = {"status": "FAIL", "error": str(e)}

        # 2. linearmodels AbsorbingLS
        try:
            from linearmodels.iv.absorbing import AbsorbingLS
            t0 = time.perf_counter()
            abs_fit = AbsorbingLS(df_hdfe["leverage"], df_hdfe[["profitability", "tangibility", "log_size"]], absorb=df_hdfe[["company_code", "year"]]).fit()
            elapsed = (time.perf_counter() - t0) * 1000
            out["linearmodels"] = {
                "status": "SUCCESS",
                "duration_ms": elapsed,
                "params": {k: float(v) for k, v in abs_fit.params.items()}
            }
        except Exception as e:
            out["linearmodels"] = {"status": "FAIL", "error": str(e)}

        return out

    # -------------------------------------------------------------
    # S-08: IV / 2SLS Regression
    # -------------------------------------------------------------
    def eval_s08_iv_2sls(self) -> Dict[str, Any]:
        out = {}
        # 1. linearmodels IV2SLS
        try:
            from linearmodels.iv import IV2SLS
            import statsmodels.api as sm
            t0 = time.perf_counter()
            # Instrument profitability using tax and dividend
            exog = sm.add_constant(self.clean_df[["tangibility", "log_size"]])
            endog = self.clean_df[["profitability"]]
            instruments = self.clean_df[["tax", "dividend"]].fillna(0)
            fit_iv = IV2SLS(self.clean_df["leverage"], exog, endog, instruments).fit()
            elapsed = (time.perf_counter() - t0) * 1000
            out["linearmodels"] = {
                "status": "SUCCESS",
                "duration_ms": elapsed,
                "params": {k: float(v) for k, v in fit_iv.params.items()},
                "first_stage_f": float(fit_iv.first_stage.diagnostics["f.stat"].iloc[0]) if hasattr(fit_iv, "first_stage") else None
            }
        except Exception as e:
            out["linearmodels"] = {"status": "FAIL", "error": str(e)}

        # 2. pyfixest IV (feols with exog | endog ~ instruments)
        try:
            import pyfixest as pf
            t0 = time.perf_counter()
            fit_pf_iv = pf.feols("leverage ~ tangibility + log_size | profitability ~ tax + dividend", data=self.clean_df)
            elapsed = (time.perf_counter() - t0) * 1000
            coefs = fit_pf_iv.coef().to_dict()
            out["pyfixest"] = {
                "status": "SUCCESS",
                "duration_ms": elapsed,
                "params": {str(k): float(v) for k, v in coefs.items()}
            }
        except Exception as e:
            out["pyfixest"] = {"status": "FAIL", "error": str(e)}

        return out

    # -------------------------------------------------------------
    # S-09: Dynamic Panel GMM
    # -------------------------------------------------------------
    def eval_s09_dynamic_gmm(self) -> Dict[str, Any]:
        out = {}
        # 1. stata_engine_v1 xtabond
        try:
            t0 = time.perf_counter()
            from models.stata_engine import execute_stata_command
            res = execute_stata_command("xtabond leverage profitability tangibility", df=self.clean_df)
            elapsed = (time.perf_counter() - t0) * 1000
            out["stata_engine_v1"] = {
                "status": "SUCCESS",
                "duration_ms": elapsed,
                "params": res.get("table", {}).get("coefficients", {})
            }
        except Exception as e:
            out["stata_engine_v1"] = {"status": "FAIL", "error": str(e)}

        # 2. linearmodels / custom GMM check
        try:
            from linearmodels.system import IVSystemGMM
            out["linearmodels"] = {
                "status": "AVAILABLE_STATIC_SYSTEM_GMM",
                "note": "linearmodels provides static system GMM (IVSystemGMM); dynamic Arellano-Bond requires lag instrument matrix expansion."
            }
        except Exception as e:
            out["linearmodels"] = {"status": "FAIL", "error": str(e)}

        return out

    # -------------------------------------------------------------
    # S-10: Difference-in-Differences / Event Study & DoWhy
    # -------------------------------------------------------------
    def eval_s10_did_event_study(self) -> Dict[str, Any]:
        out = {}
        df_did = self.clean_df.copy()
        df_did["post"] = (df_did["year"] >= 2016).astype(int) # IBC 2016 reform
        df_did["treat"] = (df_did["tangibility"] > df_did["tangibility"].median()).astype(int)
        df_did["treat_post"] = df_did["treat"] * df_did["post"]

        # 1. pyfixest TWFE DID
        try:
            import pyfixest as pf
            t0 = time.perf_counter()
            fit_did = pf.feols("leverage ~ treat_post + profitability + log_size | company_code + year", data=df_did)
            elapsed = (time.perf_counter() - t0) * 1000
            coefs = fit_did.coef().to_dict()
            out["pyfixest"] = {
                "status": "SUCCESS",
                "duration_ms": elapsed,
                "att_estimate": float(coefs.get("treat_post", 0.0)),
                "params": {str(k): float(v) for k, v in coefs.items()}
            }
        except Exception as e:
            out["pyfixest"] = {"status": "FAIL", "error": str(e)}

        # 2. DoWhy causal inference model
        try:
            import dowhy
            from dowhy import CausalModel
            t0 = time.perf_counter()
            model = CausalModel(
                data=df_did,
                treatment='treat_post',
                outcome='leverage',
                common_causes=['profitability', 'tangibility', 'log_size']
            )
            identified_estimand = model.identify_effect(proceed_when_unidentifiable=True)
            estimate = model.estimate_effect(identified_estimand, method_name="backdoor.linear_regression")
            elapsed = (time.perf_counter() - t0) * 1000
            out["dowhy"] = {
                "status": "SUCCESS",
                "duration_ms": elapsed,
                "causal_effect": float(estimate.value),
                "method": "backdoor.linear_regression"
            }
        except Exception as e:
            out["dowhy"] = {"status": "FAIL", "error": str(e)}

        return out

    # -------------------------------------------------------------
    # S-11: Out-of-Sample Prediction & ML Comparison
    # -------------------------------------------------------------
    def eval_s11_prediction_oos(self) -> Dict[str, Any]:
        out = {}
        # Train on pre-2018, test on 2018+
        train = self.clean_df[self.clean_df["year"] < 2018]
        test = self.clean_df[self.clean_df["year"] >= 2018]
        features = ["profitability", "tangibility", "log_size"]
        X_train, y_train = train[features], train["leverage"]
        X_test, y_test = test[features], test["leverage"]

        from sklearn.metrics import mean_squared_error, r2_score

        # 1. sklearn Ridge
        try:
            from sklearn.linear_model import Ridge
            t0 = time.perf_counter()
            m_ridge = Ridge(alpha=1.0).fit(X_train, y_train)
            pred = m_ridge.predict(X_test)
            elapsed = (time.perf_counter() - t0) * 1000
            out["sklearn_ridge"] = {
                "status": "SUCCESS",
                "duration_ms": elapsed,
                "oos_rmse": float(np.sqrt(mean_squared_error(y_test, pred))),
                "oos_r2": float(r2_score(y_test, pred))
            }
        except Exception as e:
            out["sklearn_ridge"] = {"status": "FAIL", "error": str(e)}

        # 2. XGBoost
        try:
            import xgboost as xgb
            t0 = time.perf_counter()
            m_xgb = xgb.XGBRegressor(n_estimators=100, max_depth=4, random_state=42).fit(X_train, y_train)
            pred_xgb = m_xgb.predict(X_test)
            elapsed = (time.perf_counter() - t0) * 1000
            out["xgboost"] = {
                "status": "SUCCESS",
                "duration_ms": elapsed,
                "oos_rmse": float(np.sqrt(mean_squared_error(y_test, pred_xgb))),
                "oos_r2": float(r2_score(y_test, pred_xgb))
            }
        except Exception as e:
            out["xgboost"] = {"status": "FAIL", "error": str(e)}

        # 3. LightGBM
        try:
            import lightgbm as lgb
            t0 = time.perf_counter()
            m_lgb = lgb.LGBMRegressor(n_estimators=100, max_depth=4, random_state=42, verbose=-1).fit(X_train, y_train)
            pred_lgb = m_lgb.predict(X_test)
            elapsed = (time.perf_counter() - t0) * 1000
            out["lightgbm"] = {
                "status": "SUCCESS",
                "duration_ms": elapsed,
                "oos_rmse": float(np.sqrt(mean_squared_error(y_test, pred_lgb))),
                "oos_r2": float(r2_score(y_test, pred_lgb))
            }
        except Exception as e:
            out["lightgbm"] = {"status": "FAIL", "error": str(e)}

        return out

    # -------------------------------------------------------------
    # S-12: Controlled Failure (Rank deficiency & Missing vars)
    # -------------------------------------------------------------
    def eval_s12_controlled_failure(self) -> Dict[str, Any]:
        out = {}
        # Perfect collinearity: x2 = 2 * x1
        bad_df = self.clean_df.copy()
        bad_df["prof_double"] = bad_df["profitability"] * 2.0

        # 1. statsmodels on perfect collinearity
        try:
            import statsmodels.api as sm
            X_bad = sm.add_constant(bad_df[["profitability", "prof_double"]])
            model_bad = sm.OLS(bad_df["leverage"], X_bad).fit()
            out["statsmodels"] = {
                "status": "HANDLED_COLLINEARITY",
                "params": {k: float(v) for k, v in model_bad.params.items() if not np.isnan(v)},
                "nans": [k for k, v in model_bad.params.items() if np.isnan(v)]
            }
        except Exception as e:
            out["statsmodels"] = {"status": "ERROR", "error_type": type(e).__name__, "message": str(e)}

        # 2. pyfixest on collinearity
        try:
            import pyfixest as pf
            fit_bad = pf.feols("leverage ~ profitability + prof_double", data=bad_df)
            out["pyfixest"] = {
                "status": "HANDLED_COLLINEARITY",
                "dropped_variables": getattr(fit_bad, "_collinear_variables", []),
                "params": {str(k): float(v) for k, v in fit_bad.coef().to_dict().items()}
            }
        except Exception as e:
            out["pyfixest"] = {"status": "ERROR", "error_type": type(e).__name__, "message": str(e)}

        # 3. stata_engine_v1 missing variable
        try:
            from models.stata_engine import execute_stata_command
            res_fail = execute_stata_command("regress leverage non_existent_column_xyz", df=self.clean_df)
            out["stata_engine_v1"] = {
                "status": "HANDLED_ERROR",
                "error_returned": res_fail.get("error") or res_fail.get("ascii_output", "")[:100]
            }
        except Exception as e:
            out["stata_engine_v1"] = {"status": "UNCAUGHT_EXCEPTION", "error": str(e)}

        return out


def main():
    df = load_benchmark_data()
    runner = EngineSpikeRunner(df)
    results = runner.run_all()

    os.makedirs("docs/implementation-reports", exist_ok=True)
    matrix_path = "docs/implementation-reports/wave3_engine_matrix.json"
    with open(matrix_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved machine-readable matrix to: {matrix_path}")

if __name__ == "__main__":
    main()

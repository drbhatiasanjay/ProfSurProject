"""
Tier 2 ML Prediction Models — RF, XGBoost, LightGBM with SHAP.
Panel-aware cross-validation and feature importance analysis.
"""

import numpy as np
import pandas as pd
import time
from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor
from .base import PanelGroupKFold, compute_metrics, DEFAULT_X_COLS, DEFAULT_Y_COL


# Conservative hyperparameters for small panel (401 firms)
MODEL_CONFIGS = {
    "Random Forest": {
        "class": RandomForestRegressor,
        "params": {"n_estimators": 300, "max_depth": 8, "min_samples_leaf": 20,
                   "random_state": 42, "n_jobs": -1},
    },
    "XGBoost": {
        "class": XGBRegressor,
        "params": {"n_estimators": 200, "max_depth": 5, "learning_rate": 0.05,
                   "reg_alpha": 1.0, "reg_lambda": 2.0, "random_state": 42,
                   "verbosity": 0},
    },
    "LightGBM": {
        "class": LGBMRegressor,
        "params": {"n_estimators": 200, "num_leaves": 31, "min_child_samples": 30,
                   "learning_rate": 0.05, "reg_alpha": 1.0, "reg_lambda": 2.0,
                   "random_state": 42, "verbosity": -1},
    },
}


def _prepare_ml_data(df, y_col=DEFAULT_Y_COL, x_cols=None):
    """Clean data for ML models. Returns X, y, feature_names, clean_df."""
    if x_cols is None:
        x_cols = DEFAULT_X_COLS
    cols = [y_col] + x_cols + ["company_code"]
    clean = df[cols].dropna()
    # Winsorize leverage
    low, high = clean[y_col].quantile(0.01), clean[y_col].quantile(0.99)
    clean[y_col] = clean[y_col].clip(lower=low, upper=high)
    X = clean[x_cols].values
    y = clean[y_col].values
    return X, y, x_cols, clean


def train_model(model_name, X_train, y_train):
    """Train a single ML model. Returns (model, train_time_seconds)."""
    config = MODEL_CONFIGS[model_name]
    model = config["class"](**config["params"])
    t0 = time.time()
    model.fit(X_train, y_train)
    elapsed = time.time() - t0
    return model, elapsed


def cross_validate_model(model_name, df, y_col=DEFAULT_Y_COL, x_cols=None, n_splits=5):
    """
    Panel-aware cross-validation for a single model.
    Splits by firm to prevent data leakage.
    """
    X, y, feature_names, clean = _prepare_ml_data(df, y_col, x_cols)
    clean = clean.reset_index(drop=True)
    splitter = PanelGroupKFold(n_splits=n_splits)

    fold_metrics = []
    all_preds = np.full(len(y), np.nan)

    for fold_idx, (train_idx, test_idx) in enumerate(splitter.split(clean)):
        X_train, y_train = X[train_idx], y[train_idx]
        X_test, y_test = X[test_idx], y[test_idx]

        model, _ = train_model(model_name, X_train, y_train)
        y_pred = model.predict(X_test)
        all_preds[test_idx] = y_pred

        metrics = compute_metrics(y_test, y_pred)
        metrics["fold"] = fold_idx + 1
        fold_metrics.append(metrics)

    # Train final model on all data
    final_model, train_time = train_model(model_name, X, y)
    avg_metrics = compute_metrics(y, all_preds[~np.isnan(all_preds)])

    return {
        "model_name": model_name,
        "model": final_model,
        "feature_names": feature_names,
        "fold_metrics": pd.DataFrame(fold_metrics),
        "avg_metrics": avg_metrics,
        "train_time": train_time,
        "n_obs": len(y),
        "n_firms": clean["company_code"].nunique(),
        "predictions": all_preds,
        "actuals": y,
    }


def compare_all_models(df, y_col=DEFAULT_Y_COL, x_cols=None, n_splits=5, progress_callback=None):
    """
    Train and cross-validate all ML models + OLS baseline.
    Returns list of result dicts sorted by R².
    """
    results = []
    model_names = list(MODEL_CONFIGS.keys())

    for i, name in enumerate(model_names):
        if progress_callback:
            progress_callback(i / len(model_names), f"Training {name}...")
        result = cross_validate_model(name, df, y_col, x_cols, n_splits)
        results.append(result)

    if progress_callback:
        progress_callback(1.0, "Done!")

    # Sort by R² descending
    results.sort(key=lambda r: r["avg_metrics"]["r2"], reverse=True)

    # Build comparison table
    comparison = pd.DataFrame([{
        "Model": r["model_name"],
        "RMSE": round(r["avg_metrics"]["rmse"], 2),
        "MAE": round(r["avg_metrics"]["mae"], 2),
        "R-squared": round(r["avg_metrics"]["r2"], 4),
        "MAPE (%)": round(r["avg_metrics"]["mape"], 1),
        "Train Time (s)": round(r["train_time"], 2),
        "N Obs": r["n_obs"],
    } for r in results])

    return results, comparison


def get_feature_importance(model, feature_names, method="native"):
    """
    Get feature importance from a trained model.
    Returns sorted DataFrame (feature, importance).
    """
    if hasattr(model, "feature_importances_"):
        importances = model.feature_importances_
    else:
        return pd.DataFrame({"Feature": feature_names, "Importance": [0] * len(feature_names)})

    imp_df = pd.DataFrame({
        "Feature": feature_names,
        "Importance": importances,
    }).sort_values("Importance", ascending=False)
    imp_df["Importance_Pct"] = (imp_df["Importance"] / imp_df["Importance"].sum() * 100).round(1)
    return imp_df


def get_shap_values(model, X, feature_names):
    """
    Compute SHAP values for a model. Returns (shap_values, expected_value).
    Falls back to native importance if SHAP is unavailable.
    """
    try:
        import shap
        if isinstance(model, (XGBRegressor, LGBMRegressor)):
            explainer = shap.TreeExplainer(model)
        else:
            # Use sampling for RF (faster)
            explainer = shap.TreeExplainer(model)
        shap_vals = explainer.shap_values(X[:min(500, len(X))])  # Limit sample for speed
        mean_abs_shap = np.abs(shap_vals).mean(axis=0)
        shap_df = pd.DataFrame({
            "Feature": feature_names,
            "Mean |SHAP|": mean_abs_shap,
        }).sort_values("Mean |SHAP|", ascending=False)
        return shap_df, explainer.expected_value
    except ImportError:
        return get_feature_importance(model, feature_names), None


def predict_leverage(model, feature_values, feature_names):
    """Predict leverage for given feature values."""
    X = np.array([feature_values])
    pred = model.predict(X)[0]
    return max(0, pred)


def get_stage_importance(df, model_name="XGBoost", x_cols=None, stage_col="life_stage"):
    """
    Train separate models per life stage and compare feature importance.
    Returns dict: {stage_name: importance_df}.
    """
    if x_cols is None:
        x_cols = DEFAULT_X_COLS

    stage_results = {}
    for stage in df[stage_col].dropna().unique():
        stage_df = df[df[stage_col] == stage]
        if len(stage_df) < 50:
            continue
        X, y, fnames, _ = _prepare_ml_data(stage_df, x_cols=x_cols)
        if len(X) < 30:
            continue
        model, _ = train_model(model_name, X, y)
        imp = get_feature_importance(model, fnames)
        stage_results[stage] = imp

    return stage_results

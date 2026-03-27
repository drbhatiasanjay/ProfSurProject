"""
Foundation utilities: panel data preparation, cross-validation, common metrics.
"""

import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

# Default determinants matching the thesis specification
DEFAULT_X_COLS = ["profitability", "tangibility", "tax", "log_size", "tax_shield", "dividend"]
DEFAULT_Y_COL = "leverage"


def prepare_panel(df, y_col=DEFAULT_Y_COL, x_cols=None, entity="company_code", time="year",
                  add_lag=False, winsorize_y=True):
    """
    Prepare a clean panel DataFrame for regression.
    Returns (panel_df, y_col, x_cols) with MultiIndex (entity, time).
    """
    if x_cols is None:
        x_cols = DEFAULT_X_COLS

    cols_needed = [entity, time, y_col] + [c for c in x_cols if c not in [entity, time, y_col]]
    panel = df[cols_needed].copy()
    panel = panel.dropna(subset=[y_col] + x_cols)

    if winsorize_y:
        low, high = panel[y_col].quantile(0.01), panel[y_col].quantile(0.99)
        panel[y_col] = panel[y_col].clip(lower=low, upper=high)

    if add_lag:
        panel = panel.sort_values([entity, time])
        panel[f"{y_col}_lag1"] = panel.groupby(entity)[y_col].shift(1)
        panel = panel.dropna(subset=[f"{y_col}_lag1"])
        x_cols = x_cols + [f"{y_col}_lag1"]

    panel = panel.set_index([entity, time])
    return panel, y_col, x_cols


class PanelGroupKFold:
    """
    K-Fold cross-validation that splits by entity (firm), not by row.
    Prevents data leakage where the same firm appears in train and test.
    """

    def __init__(self, n_splits=5, shuffle=True, random_state=42):
        self.n_splits = n_splits
        self.shuffle = shuffle
        self.random_state = random_state

    def split(self, df, entity_col="company_code"):
        firms = df[entity_col].unique()
        if self.shuffle:
            rng = np.random.RandomState(self.random_state)
            rng.shuffle(firms)

        fold_size = len(firms) // self.n_splits
        for i in range(self.n_splits):
            start = i * fold_size
            end = start + fold_size if i < self.n_splits - 1 else len(firms)
            test_firms = set(firms[start:end])

            test_mask = df[entity_col].isin(test_firms)
            train_idx = df.index[~test_mask].tolist()
            test_idx = df.index[test_mask].tolist()
            yield train_idx, test_idx


def compute_metrics(y_true, y_pred):
    """Compute standard regression metrics."""
    mask = ~(np.isnan(y_true) | np.isnan(y_pred))
    y_t, y_p = y_true[mask], y_pred[mask]
    if len(y_t) == 0:
        return {"rmse": np.nan, "mae": np.nan, "r2": np.nan, "mape": np.nan, "n": 0}
    return {
        "rmse": np.sqrt(mean_squared_error(y_t, y_p)),
        "mae": mean_absolute_error(y_t, y_p),
        "r2": r2_score(y_t, y_p),
        "mape": np.mean(np.abs((y_t - y_p) / np.where(y_t == 0, 1, y_t))) * 100,
        "n": len(y_t),
    }

"""
Tier 3: Time-Series Forecasting — LSTM/GRU for per-firm leverage prediction.
Uses PyTorch for lightweight neural network forecasting.
"""

import numpy as np
import pandas as pd
from .base import compute_metrics

try:
    import torch
    import torch.nn as nn
    from torch.utils.data import Dataset, DataLoader
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False
    Dataset = object


class FirmSequenceDataset(Dataset):
    """Sliding window sequences for firm-level time series."""

    def __init__(self, X, y):
        self.X = torch.FloatTensor(X)
        self.y = torch.FloatTensor(y)

    def __len__(self):
        return len(self.X)

    def __getitem__(self, idx):
        return self.X[idx], self.y[idx]


class LeverageLSTM(nn.Module):
    """Simple LSTM for leverage forecasting."""

    def __init__(self, input_dim, hidden_dim=32, num_layers=1, dropout=0.3):
        super().__init__()
        self.lstm = nn.LSTM(input_dim, hidden_dim, num_layers,
                            batch_first=True, dropout=dropout if num_layers > 1 else 0)
        self.dropout = nn.Dropout(dropout)
        self.fc = nn.Linear(hidden_dim, 1)

    def forward(self, x):
        out, _ = self.lstm(x)
        out = self.dropout(out[:, -1, :])  # Last timestep
        return self.fc(out).squeeze(-1)


class LeverageGRU(nn.Module):
    """Simple GRU for leverage forecasting."""

    def __init__(self, input_dim, hidden_dim=32, num_layers=1, dropout=0.3):
        super().__init__()
        self.gru = nn.GRU(input_dim, hidden_dim, num_layers,
                          batch_first=True, dropout=dropout if num_layers > 1 else 0)
        self.dropout = nn.Dropout(dropout)
        self.fc = nn.Linear(hidden_dim, 1)

    def forward(self, x):
        out, _ = self.gru(x)
        out = self.dropout(out[:, -1, :])
        return self.fc(out).squeeze(-1)


def prepare_sequences(df, features, target="leverage", seq_len=5,
                      entity="company_code", time="year"):
    """
    Create sliding-window sequences per firm.
    Returns X (n_samples, seq_len, n_features), y (n_samples,).
    """
    # Deduplicate columns (target may also be in features)
    cols = list(dict.fromkeys([entity, time, target] + features))
    clean = df[cols].dropna().sort_values([entity, time])

    X_seqs, y_seqs, firms, years = [], [], [], []

    for firm_id, firm_df in clean.groupby(entity):
        firm_df = firm_df.reset_index(drop=True)
        if len(firm_df) < seq_len + 1:
            continue

        feat_vals = firm_df[features].values
        target_vals = firm_df[target].values

        for i in range(len(firm_df) - seq_len):
            X_seqs.append(feat_vals[i:i+seq_len])
            y_seqs.append(target_vals[i+seq_len])
            firms.append(firm_id)
            years.append(int(firm_df.iloc[i+seq_len][time]))

    X = np.array(X_seqs)
    y = np.array(y_seqs)
    return X, y, firms, years


def train_forecast_model(X_train, y_train, X_val, y_val, model_type="LSTM",
                         features_dim=None, epochs=80, patience=10, lr=0.001):
    """
    Train LSTM or GRU model with early stopping.
    Returns (model, train_losses, val_losses, best_epoch).
    """
    if features_dim is None:
        features_dim = X_train.shape[2]

    ModelClass = LeverageLSTM if model_type == "LSTM" else LeverageGRU
    model = ModelClass(input_dim=features_dim, hidden_dim=32, num_layers=1, dropout=0.3)

    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=0.01)
    criterion = nn.MSELoss()

    train_ds = FirmSequenceDataset(X_train, y_train)
    val_ds = FirmSequenceDataset(X_val, y_val)
    train_loader = DataLoader(train_ds, batch_size=64, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=64)

    train_losses, val_losses = [], []
    best_val_loss = float("inf")
    best_state = None
    best_epoch = 0
    wait = 0

    for epoch in range(epochs):
        model.train()
        epoch_loss = 0
        for xb, yb in train_loader:
            pred = model(xb)
            loss = criterion(pred, yb)
            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            epoch_loss += loss.item() * len(xb)
        train_losses.append(epoch_loss / len(train_ds))

        model.eval()
        val_loss = 0
        with torch.no_grad():
            for xb, yb in val_loader:
                pred = model(xb)
                val_loss += criterion(pred, yb).item() * len(xb)
        val_losses.append(val_loss / len(val_ds))

        if val_losses[-1] < best_val_loss:
            best_val_loss = val_losses[-1]
            best_state = {k: v.clone() for k, v in model.state_dict().items()}
            best_epoch = epoch
            wait = 0
        else:
            wait += 1
            if wait >= patience:
                break

    if best_state:
        model.load_state_dict(best_state)
    return model, train_losses, val_losses, best_epoch


def temporal_split(X, y, years, train_end=2018, val_end=2021):
    """Split by year: train <= train_end, val in (train_end, val_end], test > val_end."""
    years = np.array(years)
    train_mask = years <= train_end
    val_mask = (years > train_end) & (years <= val_end)
    test_mask = years > val_end

    return {
        "X_train": X[train_mask], "y_train": y[train_mask],
        "X_val": X[val_mask], "y_val": y[val_mask],
        "X_test": X[test_mask], "y_test": y[test_mask],
        "years_test": years[test_mask],
    }


def forecast_firm(model, firm_df, features, seq_len=5, n_steps=3):
    """
    Given a firm's historical data, forecast leverage n_steps ahead.
    Returns list of (year, predicted_leverage) tuples.
    """
    clean = firm_df.sort_values("year").dropna(subset=features + ["leverage"])
    if len(clean) < seq_len:
        return []

    model.eval()
    predictions = []
    last_year = int(clean.iloc[-1]["year"])

    # Use last seq_len rows as the initial window
    window = clean[features].values[-seq_len:].copy()

    for step in range(n_steps):
        x = torch.FloatTensor(window).unsqueeze(0)  # (1, seq_len, features)
        with torch.no_grad():
            pred = model(x).item()
        pred = max(0, pred)
        predictions.append({"year": last_year + step + 1, "predicted_leverage": round(pred, 2)})

        # Shift window: drop first, append prediction (approximate — leverage goes into first feature slot)
        new_row = window[-1].copy()
        new_row[0] = pred  # Assumes leverage-related feature is first
        window = np.vstack([window[1:], new_row])

    return predictions


def run_full_forecast(df, features=None, seq_len=5, model_type="LSTM",
                      epochs=80, progress_callback=None):
    """
    Full pipeline: prepare sequences, temporal split, train, evaluate.
    Returns results dict with model, metrics, predictions.
    """
    if features is None:
        features = ["profitability", "tangibility", "log_size", "tax_shield", "leverage"]

    if progress_callback:
        progress_callback(0.1, "Preparing sequences...")

    X, y, firms, years = prepare_sequences(df, features, seq_len=seq_len)
    if len(X) < 100:
        return {"error": f"Not enough sequences ({len(X)}). Need 100+."}

    if progress_callback:
        progress_callback(0.2, "Splitting data temporally...")

    split = temporal_split(X, y, years)
    if len(split["X_train"]) < 50 or len(split["X_val"]) < 20:
        return {"error": "Not enough data after temporal split."}

    if progress_callback:
        progress_callback(0.3, f"Training {model_type}...")

    model, train_losses, val_losses, best_epoch = train_forecast_model(
        split["X_train"], split["y_train"],
        split["X_val"], split["y_val"],
        model_type=model_type, features_dim=len(features),
        epochs=epochs,
    )

    if progress_callback:
        progress_callback(0.9, "Evaluating...")

    # Evaluate on test set
    model.eval()
    with torch.no_grad():
        test_preds = model(torch.FloatTensor(split["X_test"])).numpy()
    test_metrics = compute_metrics(split["y_test"], test_preds)

    # Naive baseline: predict mean of training set
    naive_pred = np.full_like(split["y_test"], split["y_train"].mean())
    naive_metrics = compute_metrics(split["y_test"], naive_pred)

    if progress_callback:
        progress_callback(1.0, "Done!")

    return {
        "model": model,
        "model_type": model_type,
        "features": features,
        "seq_len": seq_len,
        "test_metrics": test_metrics,
        "naive_metrics": naive_metrics,
        "train_losses": train_losses,
        "val_losses": val_losses,
        "best_epoch": best_epoch,
        "test_preds": test_preds,
        "test_actuals": split["y_test"],
        "test_years": split.get("years_test", []),
        "n_train": len(split["X_train"]),
        "n_val": len(split["X_val"]),
        "n_test": len(split["X_test"]),
    }

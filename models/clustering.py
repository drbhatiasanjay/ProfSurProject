"""
Tier 3: Firm Clustering — discover natural groups beyond Dickinson stages.
K-Means, DBSCAN, comparison with Dickinson classification.
"""

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans, DBSCAN
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score, adjusted_rand_score
from .base import DEFAULT_X_COLS


def prepare_firm_features(df, feature_cols=None):
    """
    Aggregate firm-level features (mean across years) for clustering.
    Returns (firm_df, feature_matrix, scaler, feature_names).
    """
    if feature_cols is None:
        feature_cols = ["leverage", "profitability", "tangibility", "tax",
                        "log_size", "tax_shield", "cash_holdings"]

    agg = df.groupby("company_code")[feature_cols].mean().dropna()

    # Add stage transition count
    if "life_stage" in df.columns:
        transitions = df.sort_values(["company_code", "year"]).groupby("company_code")["life_stage"].apply(
            lambda s: (s != s.shift()).sum() - 1
        )
        agg["stage_transitions"] = transitions
        feature_cols = feature_cols + ["stage_transitions"]
        agg = agg.dropna()

    # Add dominant stage as metadata (not used in clustering)
    dominant = df.groupby("company_code")["life_stage"].agg(lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else "Unknown")
    agg["dominant_stage"] = dominant

    # Add company name
    if "company_name" in df.columns:
        names = df.groupby("company_code")["company_name"].first()
        agg["company_name"] = names

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(agg[feature_cols])

    return agg, X_scaled, scaler, feature_cols


def find_optimal_k(X, k_range=range(3, 13)):
    """Find optimal K for K-Means using silhouette score."""
    scores = []
    for k in k_range:
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = km.fit_predict(X)
        score = silhouette_score(X, labels)
        scores.append({"k": k, "silhouette": score})
    scores_df = pd.DataFrame(scores)
    best_k = int(scores_df.loc[scores_df["silhouette"].idxmax(), "k"])
    return best_k, scores_df


def run_kmeans(X, n_clusters, firm_df):
    """Run K-Means clustering. Returns labels and cluster profiles."""
    km = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = km.fit_predict(X)
    firm_df = firm_df.copy()
    firm_df["cluster"] = labels
    firm_df["cluster_label"] = firm_df["cluster"].apply(lambda c: f"Cluster {c+1}")

    # Cluster profiles: mean of each feature per cluster
    feature_cols = [c for c in firm_df.columns if c not in
                    ["cluster", "cluster_label", "dominant_stage", "company_name", "company_code"]]
    profiles = firm_df.groupby("cluster_label")[feature_cols].mean().round(2)

    return labels, firm_df, profiles, km


def run_dbscan(X, eps=1.5, min_samples=5, firm_df=None):
    """Run DBSCAN clustering. Returns labels and cluster info."""
    db = DBSCAN(eps=eps, min_samples=min_samples)
    labels = db.fit_predict(X)
    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    n_noise = (labels == -1).sum()

    if firm_df is not None:
        firm_df = firm_df.copy()
        firm_df["cluster"] = labels
        firm_df["cluster_label"] = firm_df["cluster"].apply(
            lambda c: f"Cluster {c+1}" if c >= 0 else "Noise"
        )
    return labels, n_clusters, n_noise, firm_df


def compare_with_dickinson(firm_df, cluster_col="cluster_label", stage_col="dominant_stage"):
    """
    Compare discovered clusters with Dickinson life stages.
    Returns crosstab and Adjusted Rand Index.
    """
    clean = firm_df.dropna(subset=[cluster_col, stage_col])
    crosstab = pd.crosstab(clean[cluster_col], clean[stage_col], margins=True)

    # ARI: how well do clusters agree with Dickinson?
    ari = adjusted_rand_score(clean[stage_col], clean[cluster_col])

    return crosstab, ari


def get_cluster_summary(firm_df, cluster_col="cluster_label"):
    """Get size and key characteristics of each cluster."""
    summary = firm_df.groupby(cluster_col).agg(
        n_firms=("leverage", "count"),
        avg_leverage=("leverage", "mean"),
        avg_profitability=("profitability", "mean"),
        avg_size=("log_size", "mean"),
        avg_tangibility=("tangibility", "mean"),
    ).round(2).reset_index()
    summary = summary.sort_values("n_firms", ascending=False)
    return summary

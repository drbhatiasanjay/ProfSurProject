"""
Firm Clustering — Discover natural groups beyond Dickinson stages.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import db
from helpers import plotly_layout, STAGE_COLORS, STAGE_ORDER, PRIMARY, SECONDARY, ACCENT
from models.clustering import (
    prepare_firm_features, find_optimal_k, run_kmeans,
    compare_with_dickinson, get_cluster_summary,
)

filters = st.session_state.filters
ft = db.filters_to_tuple(filters)

st.markdown("### Firm Clustering")
st.caption("Discover natural firm groups using unsupervised ML. Compare with Dickinson (2011) life stages.")

# Info expander
with st.expander("ℹ️ About this model"):
    st.markdown("""
**K-Means Clustering** groups firms by similarity in their financial characteristics (leverage, profitability, tangibility, size, etc.), without using life stage labels.

**Parameters:**
- **K (number of clusters):** Auto-selected via silhouette score, or manually set
- **Features:** Firm-level averages across all years — captures the firm's "financial DNA"
- **Standardization:** All features scaled to zero mean, unit variance before clustering

**Interpretation:**
- Clusters represent **natural groupings** that may differ from Dickinson's cash-flow-based stages
- **Adjusted Rand Index (ARI):** Measures agreement between clusters and Dickinson. ARI=1 means perfect match, ARI=0 means random
- A low ARI suggests our data reveals structure that Dickinson's framework doesn't capture
""")

panel_df = db.get_panel_data(ft)
if panel_df.empty:
    st.warning("No data. Adjust filters.")
    st.stop()

# Prepare firm features
firm_df, X_scaled, scaler, feat_names = prepare_firm_features(panel_df)
st.caption(f"Clustering {len(firm_df)} firms on {len(feat_names)} features")

# Find optimal K
col_k, col_chart = st.columns([1, 2])
with col_k:
    auto_k, scores_df = find_optimal_k(X_scaled)
    st.metric("Optimal K (silhouette)", auto_k)
    k = st.slider("Number of clusters", 3, 12, auto_k)

with col_chart:
    fig_sil = px.line(scores_df, x="k", y="silhouette", markers=True,
                      labels={"k": "K", "silhouette": "Silhouette Score"})
    fig_sil.add_vline(x=k, line_dash="dash", line_color=ACCENT)
    fig_sil.update_layout(**plotly_layout("Silhouette Score by K", height=280))
    st.plotly_chart(fig_sil, use_container_width=True)

# Run K-Means
labels, clustered_df, profiles, km = run_kmeans(X_scaled, k, firm_df)
summary = get_cluster_summary(clustered_df)

st.divider()

# ── Cluster profiles ──
st.markdown("#### Cluster Profiles")

cp1, cp2 = st.columns([1, 1])
with cp1:
    st.dataframe(summary, hide_index=True, use_container_width=True)

with cp2:
    fig_size = px.bar(summary, x="cluster_label", y="n_firms", color="avg_leverage",
                      color_continuous_scale=[PRIMARY, ACCENT],
                      labels={"n_firms": "Firms", "cluster_label": "", "avg_leverage": "Avg Lev"})
    fig_size.update_layout(**plotly_layout("Cluster Sizes", height=300))
    st.plotly_chart(fig_size, use_container_width=True)

# Scatter: leverage vs profitability colored by cluster
st.markdown("#### Cluster Visualization")
fig_scatter = px.scatter(
    clustered_df.reset_index(), x="profitability", y="leverage",
    color="cluster_label", hover_data=["company_name"] if "company_name" in clustered_df.columns else None,
    opacity=0.7,
    labels={"profitability": "Avg Profitability", "leverage": "Avg Leverage (%)"},
)
fig_scatter.update_layout(**plotly_layout(height=450))
st.plotly_chart(fig_scatter, use_container_width=True)

st.divider()

# ── Comparison with Dickinson ──
st.markdown("#### Comparison with Dickinson Life Stages")

with st.expander("ℹ️ What does this comparison mean?"):
    st.markdown("""
- **Crosstab** shows how cluster membership maps to Dickinson stages
- **ARI > 0.5** = strong agreement — clusters align with Dickinson
- **ARI 0.1-0.5** = partial agreement — clusters capture additional structure
- **ARI < 0.1** = weak agreement — financial DNA differs from cash-flow classification
""")

crosstab, ari = compare_with_dickinson(clustered_df)

ac1, ac2 = st.columns([1, 2])
with ac1:
    st.metric("Adjusted Rand Index", f"{ari:.3f}")
    if ari > 0.5:
        st.success("Strong alignment with Dickinson stages")
    elif ari > 0.1:
        st.info("Partial alignment — clusters reveal additional structure")
    else:
        st.warning("Weak alignment — financial profiles differ from cash-flow classification")

with ac2:
    st.dataframe(crosstab, use_container_width=True)

"""Streamlit rendering helpers for provenance-bound research artifacts."""

from __future__ import annotations

from collections.abc import Mapping

import streamlit as st


def render_artifact_provenance(provenance: Mapping[str, object], *, key_prefix: str) -> None:
    """Render only explicit provenance; never infer evidence from chart data."""
    required = (
        "analysis_run_id",
        "dataset_fingerprint",
        "sample_fingerprint",
        "result_fingerprint",
        "capability_status",
    )
    if not all(str(provenance.get(field, "")).strip() for field in required):
        return
    with st.container(border=True):
        st.caption("🔎 Evidence and provenance")
        st.write(f"Analysis run: `{provenance['analysis_run_id']}`")
        st.write(f"Capability status: `{provenance['capability_status']}`")
        st.caption("Dataset, sample, and result fingerprints are bound to this artifact.")


def render_descriptive_metadata(provenance: Mapping[str, object], *, key_prefix: str) -> None:
    """Render explicit deterministic descriptive metadata for an AnalysisRun."""
    if not isinstance(provenance, Mapping):
        return
    source = str(provenance.get("source_fingerprint", "")).strip()
    if not source:
        return
    st.caption("✅ COMPUTED · deterministic descriptive analysis")
    details = [f"Source fingerprint: `{source}`"]
    if provenance.get("n_obs") is not None:
        details.append(f"Observations: `{provenance['n_obs']}`")
    if provenance.get("n_firms") is not None:
        details.append(f"Firms: `{provenance['n_firms']}`")
    if provenance.get("panel_mode"):
        details.append(f"Panel: `{provenance['panel_mode']}`")
    st.caption(" · ".join(details))

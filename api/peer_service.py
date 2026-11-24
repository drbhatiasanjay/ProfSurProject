"""
Peer Benchmarks Service
Calculates company vs industry averages, Dickinson 8-stage quantile distributions,
and 6-axis normalized radar profiles matching Streamlit pages/2_peer_benchmarks.py.
"""

from typing import Dict, Any, List, Optional
import math
import numpy as np
import pandas as pd
import db as _db
from helpers import (
    STAGE_ORDER,
    STAGE_COLORS,
    winsorize,
    interpret_company_vs_industry,
    interpret_radar_profile,
)

RADAR_METRICS = ["profitability", "tangibility", "tax", "firm_size", "tax_shield", "cash_holdings"]
RADAR_LABELS = ["Profitability", "Tangibility", "Tax", "Firm Size", "Tax Shield", "Cash Holdings"]


def _sanitize(val: Any) -> Any:
    if val is None:
        return None
    if isinstance(val, (float, np.floating)):
        if math.isnan(val) or math.isinf(val):
            return None
        return float(val)
    if isinstance(val, (int, np.integer)):
        return int(val)
    if isinstance(val, dict):
        return {k: _sanitize(v) for k, v in val.items()}
    if isinstance(val, (list, tuple)):
        return [_sanitize(v) for v in val]
    return val


def compute_peer_benchmarks(
    company_code: Optional[int] = None,
    panel_mode: str = "latest",
    year_range: tuple = (2001, 2025),
) -> Dict[str, Any]:
    """
    Computes all peer benchmarking structures matching pages/2_peer_benchmarks.py.
    """
    ft = _db.filters_to_tuple({
        "panel_mode": panel_mode,
        "year_range": year_range,
        "industry_groups": [],
        "company_codes": [],
        "life_stages": [],
        "ownerships": [],
    })

    companies_df = _db.get_companies()
    if companies_df.empty:
        raise ValueError("No companies available in directory.")

    # 1. Resolve selected company (Default: 3M India Ltd. or first alphabetical)
    matched = pd.DataFrame()
    if company_code is not None and company_code > 0:
        matched = companies_df[companies_df["company_code"] == company_code]

    if matched.empty:
        m3_match = companies_df[companies_df["company_name"].str.contains("3M", case=False, na=False)]
        if not m3_match.empty:
            matched = m3_match
        else:
            matched = companies_df.iloc[[0]]

    company_row = matched.iloc[0]
    resolved_code = int(company_row["company_code"])
    company_name = str(company_row["company_name"])
    industry_group = str(company_row["industry_group"])
    nse_symbol = str(company_row.get("nse_symbol", ""))

    # 2. Retrieve data
    full_df = _db.get_active_financials(ft)
    company_df = _db.get_company_detail(resolved_code)
    if company_df.empty:
        # Fallback to slice from full_df
        company_df = full_df[full_df["company_code"] == resolved_code].sort_values("year")

    industry_df = full_df[full_df["industry_group"] == industry_group]

    # Dominant life stage
    comp_stage = "Maturity"
    if not company_df.empty and "life_stage" in company_df.columns:
        modes = company_df["life_stage"].mode()
        if not modes.empty:
            comp_stage = str(modes.iloc[0])

    comp_avg_lev = float(company_df["leverage"].dropna().mean()) if not company_df.empty else 0.0
    comp_avg_prof = float(company_df["profitability"].dropna().mean()) if not company_df.empty else 0.0
    comp_avg_tang = float(company_df["tangibility"].dropna().mean()) if not company_df.empty else 0.0
    current_borrowings = 0.0
    if not company_df.empty and "borrowings" in company_df.columns:
        last_b = company_df.sort_values("year")["borrowings"].dropna()
        if not last_b.empty:
            current_borrowings = float(last_b.iloc[-1])

    # 3. Time Series: Company vs Industry
    c_yearly = company_df.sort_values("year")
    company_series = []
    for _, r in c_yearly.iterrows():
        company_series.append({
            "year": int(r["year"]),
            "leverage": round(float(r["leverage"]), 2) if pd.notna(r.get("leverage")) else None,
            "profitability": round(float(r["profitability"]), 4) if pd.notna(r.get("profitability")) else None,
            "tangibility": round(float(r["tangibility"]), 4) if pd.notna(r.get("tangibility")) else None,
            "life_stage": str(r.get("life_stage", "")),
        })

    ind_yearly = industry_df.groupby("year").agg({
        "leverage": "mean",
        "profitability": "mean",
        "tangibility": "mean",
        "company_code": "nunique"
    }).reset_index()

    industry_series = []
    for _, r in ind_yearly.iterrows():
        industry_series.append({
            "year": int(r["year"]),
            "industry_leverage": round(float(r["leverage"]), 2) if pd.notna(r.get("leverage")) else None,
            "industry_profitability": round(float(r["profitability"]), 4) if pd.notna(r.get("profitability")) else None,
            "industry_tangibility": round(float(r["tangibility"]), 4) if pd.notna(r.get("tangibility")) else None,
            "n_peers": int(r["company_code"]),
        })

    # 4. Box Plot: 8 Dickinson Stages
    box_df = full_df[["life_stage", "leverage"]].dropna().copy()
    box_df["leverage"] = winsorize(box_df["leverage"])

    stage_boxes = []
    for stg in STAGE_ORDER:
        stg_sub = box_df[box_df["life_stage"] == stg]["leverage"]
        if stg_sub.empty:
            continue
        vals = stg_sub.tolist()
        # Stratified sample if large to keep payload snappy while preserving distribution & outliers
        if len(vals) > 120:
            np.random.seed(42)
            sampled_vals = list(np.random.choice(vals, size=120, replace=False))
        else:
            sampled_vals = vals

        stage_boxes.append({
            "stage": stg,
            "color": STAGE_COLORS.get(stg, "#64748B"),
            "count": len(stg_sub),
            "min": round(float(stg_sub.min()), 2),
            "q1": round(float(stg_sub.quantile(0.25)), 2),
            "median": round(float(stg_sub.median()), 2),
            "q3": round(float(stg_sub.quantile(0.75)), 2),
            "max": round(float(stg_sub.max()), 2),
            "mean": round(float(stg_sub.mean()), 2),
            "values": [round(float(v), 2) for v in sampled_vals],
        })

    diamond_point = {
        "stage": comp_stage,
        "leverage": round(comp_avg_lev, 2),
        "company_name": company_name,
    }

    # 5. Radar: 6 Multi-Determinants (Normalized 0-100)
    norms = {}
    for m in RADAR_METRICS:
        if m in full_df.columns:
            col = full_df[m].dropna()
            norms[m] = (float(col.min()), float(col.max()))
        else:
            norms[m] = (0.0, 100.0)

    def normalize(val: float, m: str) -> float:
        mn, mx = norms[m]
        if mx == mn:
            return 50.0
        return max(0.0, min(100.0, (val - mn) / (mx - mn) * 100.0))

    comp_means = [float(company_df[m].dropna().mean()) if m in company_df.columns and not company_df[m].dropna().empty else 0.0 for m in RADAR_METRICS]
    ind_means = [float(industry_df[m].dropna().mean()) if m in industry_df.columns and not industry_df[m].dropna().empty else 0.0 for m in RADAR_METRICS]

    stage_df = full_df[full_df["life_stage"] == comp_stage] if "life_stage" in full_df.columns else pd.DataFrame()
    stage_means = [float(stage_df[m].dropna().mean()) if not stage_df.empty and m in stage_df.columns and not stage_df[m].dropna().empty else 0.0 for m in RADAR_METRICS]

    comp_norm = [normalize(v, m) for v, m in zip(comp_means, RADAR_METRICS)]
    ind_norm = [normalize(v, m) for v, m in zip(ind_means, RADAR_METRICS)]
    stage_norm = [normalize(v, m) for v, m in zip(stage_means, RADAR_METRICS)]

    radar_payload = {
        "metrics": RADAR_METRICS,
        "labels": RADAR_LABELS,
        "company_vals": [round(v, 1) for v in comp_norm],
        "industry_vals": [round(v, 1) for v in ind_norm],
        "stage_vals": [round(v, 1) for v in stage_norm],
        "raw_company": [round(v, 3) for v in comp_means],
        "raw_industry": [round(v, 3) for v in ind_means],
        "raw_stage": [round(v, 3) for v in stage_means],
        "comp_stage": comp_stage,
    }

    # 6. Helper Interpretations & Action Strategies
    f_lev, a_lev = interpret_company_vs_industry(company_name, company_df, industry_df, "leverage")
    f_prof, a_prof = interpret_company_vs_industry(company_name, company_df, industry_df, "profitability")
    f_rad, a_rad = interpret_radar_profile(company_name, comp_norm, ind_norm, stage_norm, RADAR_LABELS)

    # Master interpretation section
    ind_avg_lev = float(industry_df["leverage"].dropna().mean()) if not industry_df.empty else 0.0
    gap_lev = comp_avg_lev - ind_avg_lev
    direction_lev = "above" if gap_lev > 0 else "below"

    master_findings = [
        f"**{company_name}** maintains an average leverage of **{comp_avg_lev:.1f}%**, positioning **{abs(gap_lev):.1f}pp {direction_lev}** its sector peers in *{industry_group}* (industry average: {ind_avg_lev:.1f}%).",
        f"Dominant life cycle classification is **{comp_stage}**, characterized by stable cash generation and established operational scale under Dickinson (2011) cash-flow pattern criteria.",
        f"Average profitability (ROA) is **{comp_avg_prof:.1%}**, providing internal equity accretion to self-finance ongoing operational expenditures without structural gearing reliance.",
    ]
    for rf in f_rad:
        if "significantly" in rf:
            master_findings.append(rf)

    master_actions = [
        f"Benchmark ongoing capital structure targets against the {comp_stage} cohort median of {next((b['median'] for b in stage_boxes if b['stage'] == comp_stage), 10.0):.1f}% rather than aggregate market averages.",
        "Monitor debt maturity profiles and interest coverage buffers against macroeconomic shock windows (GFC, IBC, COVID periods).",
    ]
    if a_lev:
        master_actions.extend(a_lev)
    if a_rad:
        master_actions.extend(a_rad)

    # Deduplicate actions
    master_actions = list(dict.fromkeys(master_actions))

    return _sanitize({
        "company_info": {
            "company_code": resolved_code,
            "company_name": company_name,
            "nse_symbol": nse_symbol,
            "industry_group": industry_group,
            "dominant_stage": comp_stage,
            "avg_leverage": round(comp_avg_lev, 2),
            "avg_profitability": round(comp_avg_prof, 4),
            "avg_tangibility": round(comp_avg_tang, 4),
            "current_borrowings": round(current_borrowings, 1),
            "n_years": len(company_series),
        },
        "company_series": company_series,
        "industry_series": industry_series,
        "stage_box_data": stage_boxes,
        "diamond_point": diamond_point,
        "radar_data": radar_payload,
        "insights": {
            "leverage": {"findings": f_lev, "actions": a_lev},
            "profitability": {"findings": f_prof, "actions": a_prof},
            "radar": {"findings": f_rad, "actions": a_rad},
        },
        "interpretation": {
            "findings": master_findings,
            "actions": master_actions,
            "citation": "Dickinson, V. (2011). Cash flow patterns as a proxy for firm life cycle. The Accounting Review, 86(6), 1969-1994.",
        },
        "event_bands": [
            {"year": 2008, "name": "Global Financial Crisis (GFC)"},
            {"year": 2016, "name": "IBC & Demonetisation"},
            {"year": 2020, "name": "COVID-19 Shock"},
        ],
    })

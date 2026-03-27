"""
Tier 3: Survival Analysis — Stage transition probabilities.
Cox Proportional Hazards, Kaplan-Meier survival curves.
"""

import numpy as np
import pandas as pd
from lifelines import KaplanMeierFitter, CoxPHFitter
from .base import DEFAULT_X_COLS


def prepare_transition_data(df, entity="company_code", time="year", stage="life_stage"):
    """
    Prepare survival/transition data: for each firm-stage spell, compute
    duration (years in stage) and event (did the firm transition out?).
    """
    df = df.sort_values([entity, time]).copy()
    records = []

    for firm_id, firm_df in df.groupby(entity):
        firm_df = firm_df.reset_index(drop=True)
        if len(firm_df) < 2:
            continue

        current_stage = firm_df.iloc[0][stage]
        start_year = firm_df.iloc[0][time]
        last_row = firm_df.iloc[0]

        for i in range(1, len(firm_df)):
            row = firm_df.iloc[i]
            if row[stage] != current_stage:
                # Transition occurred
                duration = int(row[time] - start_year)
                records.append({
                    "company_code": firm_id,
                    "from_stage": current_stage,
                    "to_stage": row[stage],
                    "duration": max(1, duration),
                    "event": 1,  # transition happened
                    "profitability": last_row.get("profitability", np.nan),
                    "tangibility": last_row.get("tangibility", np.nan),
                    "log_size": last_row.get("log_size", np.nan),
                    "leverage": last_row.get("leverage", np.nan),
                    "tax_shield": last_row.get("tax_shield", np.nan),
                })
                current_stage = row[stage]
                start_year = row[time]

            last_row = row

        # Right-censored: firm still in its last stage
        duration = int(firm_df.iloc[-1][time] - start_year)
        records.append({
            "company_code": firm_id,
            "from_stage": current_stage,
            "to_stage": None,
            "duration": max(1, duration),
            "event": 0,  # still in stage (censored)
            "profitability": last_row.get("profitability", np.nan),
            "tangibility": last_row.get("tangibility", np.nan),
            "log_size": last_row.get("log_size", np.nan),
            "leverage": last_row.get("leverage", np.nan),
            "tax_shield": last_row.get("tax_shield", np.nan),
        })

    return pd.DataFrame(records)


def fit_kaplan_meier(transition_df, stage_col="from_stage"):
    """
    Fit Kaplan-Meier survival curves for each starting life stage.
    Returns dict of {stage: KaplanMeierFitter} and a summary DataFrame.
    """
    km_fits = {}
    summaries = []

    for stage in transition_df[stage_col].dropna().unique():
        sub = transition_df[transition_df[stage_col] == stage]
        if len(sub) < 5:
            continue

        kmf = KaplanMeierFitter()
        kmf.fit(sub["duration"], event_observed=sub["event"], label=stage)
        km_fits[stage] = kmf

        median_surv = kmf.median_survival_time_
        summaries.append({
            "Stage": stage,
            "N Spells": len(sub),
            "N Transitions": int(sub["event"].sum()),
            "Median Duration (yrs)": round(float(median_surv), 1) if not np.isinf(median_surv) else ">24",
            "5yr Survival (%)": round(float(kmf.predict(5)) * 100, 1) if 5 <= kmf.timeline.max() else "N/A",
        })

    summary_df = pd.DataFrame(summaries)
    return km_fits, summary_df


def fit_cox_ph(transition_df, covariates=None):
    """
    Fit Cox Proportional Hazards model.
    Returns CoxPHFitter, hazard ratios, and summary.
    """
    if covariates is None:
        covariates = ["profitability", "tangibility", "log_size", "leverage", "tax_shield"]

    cols = ["duration", "event"] + covariates
    clean = transition_df[cols].dropna()

    if len(clean) < 30:
        return None, None, "Not enough data for Cox PH (need 30+ observations)"

    cph = CoxPHFitter()
    cph.fit(clean, duration_col="duration", event_col="event")

    summary = cph.summary

    # Hazard ratios with interpretation
    hr_df = pd.DataFrame({
        "Variable": summary.index,
        "Hazard Ratio": summary["exp(coef)"].round(3).values,
        "p-value": summary["p"].round(4).values,
        "Interpretation": [
            f"{'Accelerates' if hr > 1 else 'Delays'} transition by "
            f"{abs(hr - 1)*100:.0f}% per unit increase"
            if p < 0.05 else "Not significant"
            for hr, p in zip(summary["exp(coef)"], summary["p"])
        ],
    })

    return cph, hr_df, summary


def get_transition_matrix(transition_df, stage_col="from_stage", to_col="to_stage"):
    """
    Compute stage transition probability matrix.
    Returns DataFrame: rows=from_stage, cols=to_stage, values=probability.
    """
    transitions = transition_df[transition_df["event"] == 1].copy()
    if transitions.empty:
        return pd.DataFrame()

    cross = pd.crosstab(transitions[stage_col], transitions[to_col], normalize="index")
    cross = (cross * 100).round(1)
    return cross


def get_km_plot_data(km_fits):
    """
    Extract Kaplan-Meier survival curve data for Plotly plotting.
    Returns list of dicts: {stage, timeline, survival, ci_lower, ci_upper}.
    """
    plot_data = []
    for stage, kmf in km_fits.items():
        ci = kmf.confidence_interval_survival_function_
        plot_data.append({
            "stage": stage,
            "timeline": kmf.timeline.tolist(),
            "survival": kmf.survival_function_.iloc[:, 0].tolist(),
            "ci_lower": ci.iloc[:, 0].tolist() if ci is not None else None,
            "ci_upper": ci.iloc[:, 1].tolist() if ci is not None else None,
        })
    return plot_data

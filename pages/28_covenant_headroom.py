"""
Covenant Compliance & Debt Headroom Engine (Page 28)

12-Quarter CFADS Stress Testing, Dynamic Covenant Breach Diagnostics,
and Evidence-Backed CFO / Credit Committee Action Playbook.

Architecture:
1. The Problem: Credit dilemma of static debt ratios vs. dynamic multi-quarter cash flow.
2. The Background: Deterministic CFADS, Ind AS 116 lease mechanics, and audited corporate anchors.
3. The Analysis: Interactive stress testing, headroom binary search, Plotly trajectories, and 12-quarter audit schedule.
4. Dynamic Interpretation: Automated analytical synthesis citing exact breach quarters, binding constraints, and primary sources.
5. Call for Action: Actionable CFO/Lender playbook with covenant remedies, capital sizing, and audit exports.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from helpers import ensure_session_state
from utils.html_blocks import render_html
from models.covenant_pilot import (
    CovenantSpec,
    ScenarioRequest,
    simulate,
)
from models.covenant_examples import example_catalog


def render_covenant_headroom_page():
    ensure_session_state()
    theme = st.session_state.get("theme", "dark")
    light = theme == "light"

    # Theme tokens
    text_color = "#0F172A" if light else "#F8FAFC"
    muted_color = "#64748B" if light else "#94A3B8"
    card_bg = "#FFFFFF" if light else "rgba(255, 255, 255, 0.03)"
    card_border = "#E2E8F0" if light else "rgba(255, 255, 255, 0.08)"
    accent_blue = "#0284C7" if light else "#38BDF8"
    accent_emerald = "#059669" if light else "#10B981"
    accent_amber = "#D97706" if light else "#F59E0B"
    accent_rose = "#E11D48" if light else "#F43F5E"

    # Header
    st.markdown("## 🛡️ Covenant Compliance & Debt Headroom Engine")
    st.caption(
        "12-Quarter CFADS Stress Testing · Dynamic Covenant Breach Diagnostics · "
        "Deterministic Headroom Binary Search · Audited Regulatory Anchors"
    )

    # ─────────────────────────────────────────────────────────────────────────
    # 1. THE PROBLEM: The Credit Dilemma & Failure of Static Multiples
    # ─────────────────────────────────────────────────────────────────────────
    render_html(f"""
    <div style="background:{card_bg}; border:1px solid {card_border}; border-left:4px solid {accent_rose}; border-radius:8px; padding:16px 20px; margin-bottom:20px;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
            <span style="font-size:0.78rem; font-weight:700; color:{accent_rose}; text-transform:uppercase; letter-spacing:0.05em;">
                1. The Credit Dilemma · Why Static Debt Multiples Fail
            </span>
            <span style="font-size:0.75rem; background:rgba(244,63,94,0.12); color:{accent_rose}; padding:3px 8px; border-radius:4px; font-weight:600;">
                Structural Default Risk
            </span>
        </div>
        <div style="font-size:0.92rem; color:{text_color}; line-height:1.55;">
            Traditional credit evaluation relies heavily on backward-looking audited ratios—such as <strong>Debt/Equity</strong> or <strong>Debt/EBITDA</strong>. In real-world treasury operations, these static metrics conceal vital liquidity dynamics:
        </div>
        <ul style="font-size:0.86rem; color:{muted_color}; line-height:1.6; margin-top:8px; margin-bottom:4px; padding-left:20px;">
            <li><strong>Lumpy Debt Amortization:</strong> Equal annual averages mask quarterly principal repayment spikes that trigger immediate cash deficits.</li>
            <li><strong>Macro Floating Rate Shocks:</strong> A sudden +100 to +250 bps interest rate hike drastically expands debt service before annual earnings catch up.</li>
            <li><strong>Capitalized Lease Liabilities (Ind AS 116):</strong> Asset-light corporate fleets (e.g. aviation aircraft, retail stores) carry massive non-bank lease obligations that compete directly for operational cash.</li>
            <li><strong>Covenant Cliffs:</strong> Loan default clauses (such as <strong>DSCR &lt; 1.35x</strong> or <strong>TOL/TNW &gt; 3.0x</strong>) are tested on cash flow available for debt service, triggering penalty rates and loan accelerations long before statutory insolvency.</li>
        </ul>
    </div>
    """)

    # ─────────────────────────────────────────────────────────────────────────
    # 2. THE BACKGROUND: Solution Architecture & Mathematical Engine
    # ─────────────────────────────────────────────────────────────────────────
    with st.expander("🔬 2. Solution Architecture & Methodological Background (Click to Expand)", expanded=False):
        render_html(f"""
        <div style="font-size:0.88rem; color:{text_color}; line-height:1.6; margin-bottom:12px;">
            This engine implements the independently verified, deterministic 12-quarter covenant simulation protocol from 
            <code>models.covenant_pilot</code>. It operates on five formal mathematical principles:
        </div>
        <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap:12px; margin-bottom:12px;">
            <div style="background:{card_bg}; border:1px solid {card_border}; border-radius:6px; padding:12px 14px;">
                <div style="font-size:0.78rem; font-weight:700; color:{accent_blue}; margin-bottom:4px;">1. Pre-Financing CFADS Bridge</div>
                <div style="font-size:0.82rem; color:{muted_color}; line-height:1.45;">
                    <code>CFADS<sub>t</sub> = EBITDA<sub>t</sub> · (1 + Margin Shock) − Cash Taxes − Maint Capex − ΔWC</code><br/>
                    Represents true unencumbered operational cash generated before contractual debt service.
                </div>
            </div>
            <div style="background:{card_bg}; border:1px solid {card_border}; border-radius:6px; padding:12px 14px;">
                <div style="font-size:0.78rem; font-weight:700; color:{accent_emerald}; margin-bottom:4px;">2. Debt Service Coverage Ratio (DSCR)</div>
                <div style="font-size:0.82rem; color:{muted_color}; line-height:1.45;">
                    <code>DSCR<sub>t</sub> = CFADS<sub>t</sub> / [Interest<sub>t</sub> + Principal<sub>t</sub> + Lease Cash<sub>t</sub>]</code><br/>
                    Quarterly testing of debt servicing sufficiency against contractual bank floors (e.g. 1.25x – 1.35x).
                </div>
            </div>
            <div style="background:{card_bg}; border:1px solid {card_border}; border-radius:6px; padding:12px 14px;">
                <div style="font-size:0.78rem; font-weight:700; color:{accent_amber}; margin-bottom:4px;">3. Ind AS 116 Lease Capitalization</div>
                <div style="font-size:0.82rem; color:{muted_color}; line-height:1.45;">
                    Separates bank debt from lease principal, finance charge, and variable rent. Toggleable coverage testing evaluates bank-only vs. comprehensive economic leverage.
                </div>
            </div>
            <div style="background:{card_bg}; border:1px solid {card_border}; border-radius:6px; padding:12px 14px;">
                <div style="font-size:0.78rem; font-weight:700; color:{accent_rose}; margin-bottom:4px;">4. Deterministic Binary Headroom Search</div>
                <div style="font-size:0.82rem; color:{muted_color}; line-height:1.45;">
                    Executes 60-iteration bisection search over <code>[0, 1,000,000 Cr]</code> to determine the exact maximum additional debt capacity sustainable without breaching any covenant.
                </div>
            </div>
        </div>
        """)

    # ─────────────────────────────────────────────────────────────────────────
    # 3. THE ANALYSIS: Interactive Multi-Quarter Scenario Simulation
    # ─────────────────────────────────────────────────────────────────────────
    render_html(f"""
    <div style="margin-top:14px; margin-bottom:10px;">
        <span style="font-size:0.78rem; font-weight:700; color:{accent_blue}; text-transform:uppercase; letter-spacing:0.05em;">
            3. The Multi-Quarter Stress Analysis · Interactive Simulation
        </span>
    </div>
    """)

    catalog = example_catalog()
    company_options = {
        "tata-steel-fy2025": "Tata Steel Ltd. (Consolidated Metals / Heavy Industrial)",
        "indigo-fy2025": "InterGlobe Aviation Ltd. (IndiGo) (Aviation / Capitalized Fleet Leases)",
    }

    c_sel1, c_sel2 = st.columns([2, 3])
    with c_sel1:
        selected_key = st.selectbox(
            "Select Borrower Entity Archetype",
            options=list(company_options.keys()),
            format_func=lambda k: company_options[k],
            index=0,
            key="covenant_entity_select",
        )
    
    comp_data = catalog[selected_key]
    snapshot = comp_data["snapshot"]
    debts = comp_data["debts"]
    leases = comp_data["leases"]

    with c_sel2:
        render_html(f"""
        <div style="background:{card_bg}; border:1px solid {card_border}; border-radius:6px; padding:10px 14px; font-size:0.82rem; color:{muted_color};">
            <strong>Audited Regulatory Baseline ({snapshot.as_of}):</strong> Reporting Perimeter: <code>{snapshot.perimeter}</code> · 
            Annual Base Earnings: <code>₹{snapshot.earnings_cr[0]*4:,.1f} Cr ({snapshot.earnings_basis})</code> · 
            Opening Free Cash: <code>₹{snapshot.opening_cash_cr:,.1f} Cr</code> · 
            Tangible Net Worth: <code>₹{snapshot.tangible_net_worth_cr:,.1f} Cr</code>
        </div>
        """)

    # Stress & Policy Controls in 4 columns
    st.markdown("#### Scenario Stress Parameters & Covenant Constraints")
    sc1, sc2, sc3, sc4 = st.columns(4)

    with sc1:
        rate_shock_bps = st.slider(
            "Macro Rate Shock (bps)",
            min_value=-200,
            max_value=400,
            value=150,
            step=25,
            help="Interest rate spike applied to all floating-rate facilities and incremental debt.",
        )
        margin_shock_pct = st.slider(
            "Operating Margin Shock (%)",
            min_value=-50,
            max_value=30,
            value=-15,
            step=5,
            help="Compression or expansion applied to quarterly operating earnings.",
        )

    with sc2:
        incremental_debt_cr = st.number_input(
            "New Debt Capex Raise (₹ Cr)",
            min_value=0.0,
            max_value=100000.0,
            value=5000.0 if selected_key == "tata-steel-fy2025" else 2000.0,
            step=500.0,
            help="Incremental borrowing assumed drawn at Q1 and spent on capex.",
        )
        incremental_annual_rate = st.number_input(
            "Incremental Borrowing Rate (%)",
            min_value=1.0,
            max_value=25.0,
            value=9.0,
            step=0.25,
            help="Contractual coupon rate for newly issued financing tranche.",
        ) / 100.0

    with sc3:
        dscr_floor = st.number_input(
            "Minimum DSCR Floor (x)",
            min_value=1.0,
            max_value=3.0,
            value=1.35,
            step=0.05,
            help="Debt Service Coverage Ratio covenant floor required by bank syndicate.",
        )
        icr_floor = st.number_input(
            "Minimum ICR Floor (x)",
            min_value=1.0,
            max_value=5.0,
            value=2.00,
            step=0.25,
            help="Interest Coverage Ratio covenant floor.",
        )

    with sc4:
        tol_ceiling = st.number_input(
            "Max TOL / TNW Ceiling (x)",
            min_value=1.0,
            max_value=10.0,
            value=3.00,
            step=0.25,
            help="Total Outside Liabilities to Tangible Net Worth ceiling.",
        )
        lease_in_coverage = st.checkbox(
            "Include Leases in Debt Service",
            value=True,
            help="If checked, Ind AS 116 lease cash service is added to DSCR denominator.",
        )

    # Execute simulation
    covenants = CovenantSpec(
        dscr_floor=dscr_floor,
        icr_floor=icr_floor,
        tol_tnw_ceiling=tol_ceiling,
        minimum_cash_cr=500.0,
    )
    request = ScenarioRequest(
        rate_shock_bps=float(rate_shock_bps),
        margin_shock_pct=float(margin_shock_pct),
        incremental_debt_cr=float(incremental_debt_cr),
        incremental_annual_rate=float(incremental_annual_rate),
        lease_in_coverage=bool(lease_in_coverage),
    )

    sim_res = simulate(snapshot, debts, leases, covenants, request)
    baseline = sim_res["baseline"]
    stressed = sim_res["stressed"]
    headroom_cr = sim_res["additional_headroom_cr"]
    binding = sim_res["binding_constraints"]

    # Key Metrics Dashboard
    st.markdown("---")
    m1, m2, m3, m4, m5 = st.columns(5)

    with m1:
        headroom_display = f"₹{headroom_cr:,.1f} Cr" if headroom_cr is not None else "N/A"
        headroom_color = accent_emerald if (headroom_cr or 0) > 0 else accent_rose
        st.metric(
            label="Additional Debt Headroom",
            value=headroom_display,
            delta="Feasible Cushion" if (headroom_cr or 0) > 0 else "Capacity Exhausted",
            delta_color="normal" if (headroom_cr or 0) > 0 else "inverse",
        )

    with m2:
        min_stressed_dscr = min((q["dscr"] for q in stressed["quarters"] if q["dscr"] is not None), default=0.0)
        dscr_delta = min_stressed_dscr - dscr_floor
        st.metric(
            label="Stressed Minimum DSCR",
            value=f"{min_stressed_dscr:.2f}x",
            delta=f"{dscr_delta:+.2f}x vs floor",
            delta_color="normal" if dscr_delta >= 0 else "inverse",
        )

    with m3:
        min_stressed_icr = min((q["icr"] for q in stressed["quarters"] if q["icr"] is not None), default=0.0)
        icr_delta = min_stressed_icr - icr_floor
        st.metric(
            label="Stressed Minimum ICR",
            value=f"{min_stressed_icr:.2f}x",
            delta=f"{icr_delta:+.2f}x vs floor",
            delta_color="normal" if icr_delta >= 0 else "inverse",
        )

    with m4:
        violations_count = len(stressed["violations"])
        st.metric(
            label="Covenant Violations",
            value=f"{violations_count} Breaches",
            delta="Zero Violations" if violations_count == 0 else f"{violations_count} Quarter Breaches",
            delta_color="normal" if violations_count == 0 else "inverse",
        )

    with m5:
        q12_cash = stressed["quarters"][-1]["closing_cash_cr"]
        st.metric(
            label="Ending Liquidity (Q12)",
            value=f"₹{q12_cash:,.1f} Cr",
            delta="Adequate Cash" if q12_cash >= 500 else "Critical Deficit",
            delta_color="normal" if q12_cash >= 500 else "inverse",
        )

    # Plotly Visualizations: 2-column comparative layout
    st.markdown("#### 12-Quarter Trajectory Comparison")
    chart_col1, chart_col2 = st.columns(2)

    quarters_labels = [f"Q{q['quarter']}" for q in stressed["quarters"]]
    stressed_cfads = [q["cfads_cr"] for q in stressed["quarters"]]
    stressed_debt_service = [
        q["debt_interest_cr"] + q["debt_principal_cr"] + (q["lease_cash_cr"] if lease_in_coverage else 0)
        for q in stressed["quarters"]
    ]
    baseline_dscr = [q["dscr"] for q in baseline["quarters"]]
    stressed_dscr = [q["dscr"] for q in stressed["quarters"]]

    with chart_col1:
        fig_cfads = go.Figure()
        fig_cfads.add_trace(go.Bar(
            x=quarters_labels,
            y=stressed_cfads,
            name="Stressed CFADS",
            marker_color=accent_emerald,
            opacity=0.85,
        ))
        fig_cfads.add_trace(go.Bar(
            x=quarters_labels,
            y=stressed_debt_service,
            name="Total Debt Service",
            marker_color=accent_rose,
            opacity=0.85,
        ))
        fig_cfads.update_layout(
            title="Quarterly CFADS vs. Debt Service (₹ Cr)",
            barmode="group",
            height=340,
            margin=dict(l=20, r=20, t=40, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color=text_color, size=11),
            yaxis=dict(gridcolor="rgba(128,128,128,0.15)"),
        )
        st.plotly_chart(fig_cfads, use_container_width=True)

    with chart_col2:
        fig_dscr = go.Figure()
        fig_dscr.add_trace(go.Scatter(
            x=quarters_labels,
            y=baseline_dscr,
            name="Baseline DSCR",
            line=dict(color=accent_blue, width=2.5, dash="dash"),
            mode="lines+markers",
        ))
        fig_dscr.add_trace(go.Scatter(
            x=quarters_labels,
            y=stressed_dscr,
            name="Stressed DSCR",
            line=dict(color=accent_rose if violations_count > 0 else accent_emerald, width=3),
            mode="lines+markers",
        ))
        # Covenant floor line
        fig_dscr.add_hline(
            y=dscr_floor,
            line_dash="dot",
            line_color="#EF4444",
            annotation_text=f"Covenant Floor ({dscr_floor:.2f}x)",
            annotation_position="bottom right",
            annotation_font_color="#EF4444",
        )
        fig_dscr.update_layout(
            title="DSCR Trajectory vs. Covenant Floor (x)",
            height=340,
            margin=dict(l=20, r=20, t=40, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color=text_color, size=11),
            yaxis=dict(gridcolor="rgba(128,128,128,0.15)"),
        )
        st.plotly_chart(fig_dscr, use_container_width=True)

    # 12-Quarter Detailed Audit Table
    with st.expander("📋 Detailed 12-Quarter Audit Schedule & Violations Log", expanded=False):
        table_rows = []
        for q in stressed["quarters"]:
            table_rows.append({
                "Quarter": f"Q{q['quarter']}",
                "Earnings (₹ Cr)": f"{q['earnings_cr']:,.1f}",
                "CFADS (₹ Cr)": f"{q['cfads_cr']:,.1f}",
                "Debt Interest (₹ Cr)": f"{q['debt_interest_cr']:,.1f}",
                "Debt Principal (₹ Cr)": f"{q['debt_principal_cr']:,.1f}",
                "Lease Cash (₹ Cr)": f"{q['lease_cash_cr']:,.1f}",
                "Closing Cash (₹ Cr)": f"{q['closing_cash_cr']:,.1f}",
                "DSCR": f"{q['dscr']:.2f}x" if q["dscr"] is not None else "N/A",
                "ICR": f"{q['icr']:.2f}x" if q["icr"] is not None else "N/A",
                "TOL/TNW": f"{q['tol_tnw']:.2f}x" if q["tol_tnw"] is not None else "N/A",
                "Breaches": ", ".join(q["breaches"]) if q["breaches"] else "None",
            })
        st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)

    # ─────────────────────────────────────────────────────────────────────────
    # 4. DYNAMIC INTERPRETATION WITH EVIDENCE REFERENCE
    # ─────────────────────────────────────────────────────────────────────────
    st.markdown("---")
    render_html(f"""
    <div style="margin-bottom:10px;">
        <span style="font-size:0.78rem; font-weight:700; color:{accent_amber}; text-transform:uppercase; letter-spacing:0.05em;">
            4. Dynamic Interpretation & Evidence Provenance
        </span>
    </div>
    """)

    # Synthesize dynamic interpretation based on simulation output
    breach_quarters = sorted({v["quarter"] for v in stressed["violations"]})
    binding_str = ", ".join(binding) if binding else "None"
    
    if violations_count > 0:
        verdict_badge = f'<span style="background:rgba(244,63,94,0.15); color:{accent_rose}; padding:4px 10px; border-radius:4px; font-weight:700; font-size:0.82rem;">⚠️ COVENANT BREACH DETECTED ({violations_count} Quarters)</span>'
        interpretation_lead = (
            f"Under the simulated combined stress (+{rate_shock_bps} bps interest rate shock and {margin_shock_pct}% operating margin shock), "
            f"<strong>{snapshot.company}</strong> breaches debt covenants across <strong>{len(breach_quarters)} quarters</strong> "
            f"({', '.join(f'Q{q}' for q in breach_quarters)}). The primary binding constraints are <code>{binding_str}</code>, "
            f"compressing additional debt capacity to zero."
        )
    else:
        verdict_badge = f'<span style="background:rgba(16,185,129,0.15); color:{accent_emerald}; padding:4px 10px; border-radius:4px; font-weight:700; font-size:0.82rem;">✅ COVENANTS FULLY PRESERVED (₹{headroom_cr:,.1f} Cr Headroom)</span>'
        interpretation_lead = (
            f"Under the simulated scenario (+{rate_shock_bps} bps rate shock and {margin_shock_pct}% margin compression), "
            f"<strong>{snapshot.company}</strong> maintains full compliance across all 12 quarters. "
            f"The borrower sustains an additional debt headroom of <strong>₹{headroom_cr:,.1f} Cr</strong> before the first binding constraint "
            f"(<code>{binding_str}</code>) is triggered."
        )

    # Evidence mapping table
    evidence_items = snapshot.evidence or ()
    evidence_html = "".join([
        f"""<div style="margin-bottom:6px; font-size:0.80rem;">
            <strong style="color:{accent_blue};">{e.get('label', 'Item')}:</strong> 
            <span>{e.get('value', '')}</span> · 
            <em style="color:{muted_color};">Source: {e.get('source', 'Company Disclosures')}</em>
        </div>"""
        for e in evidence_items
    ])

    render_html(f"""
    <div style="background:{card_bg}; border:1px solid {card_border}; border-radius:8px; padding:16px 20px; margin-bottom:20px;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
            <div style="font-size:0.95rem; font-weight:700; color:{text_color};">
                Analytical Diagnosis & Constraint Hierarchy
            </div>
            {verdict_badge}
        </div>
        <div style="font-size:0.88rem; color:{text_color}; line-height:1.55; margin-bottom:12px;">
            {interpretation_lead}
        </div>
        <div style="border-top:1px solid {card_border}; padding-top:10px; margin-top:10px;">
            <div style="font-size:0.78rem; font-weight:700; color:{muted_color}; text-transform:uppercase; margin-bottom:6px;">
                Verified Primary Disclosures & Audit Evidence:
            </div>
            {evidence_html}
        </div>
    </div>
    """)

    # ─────────────────────────────────────────────────────────────────────────
    # 5. CALL FOR ACTION: CFO & Credit Committee Strategic Playbook
    # ─────────────────────────────────────────────────────────────────────────
    render_html(f"""
    <div style="margin-bottom:10px;">
        <span style="font-size:0.78rem; font-weight:700; color:{accent_emerald}; text-transform:uppercase; letter-spacing:0.05em;">
            5. Strategic Recommendations & Call for Action
        </span>
    </div>
    """)

    act_col1, act_col2 = st.columns(2)

    with act_col1:
        if violations_count > 0:
            st.markdown(f"""
            <div style="background:{card_bg}; border:1px solid {card_border}; border-left:4px solid {accent_rose}; border-radius:6px; padding:14px 16px;">
                <div style="font-size:0.85rem; font-weight:700; color:{accent_rose}; margin-bottom:6px;">
                    🚨 Pre-emptive Debt Restructuring Playbook (Borrower Mandate)
                </div>
                <div style="font-size:0.83rem; color:{text_color}; line-height:1.5;">
                    1. <strong>Tenor Reprofiling:</strong> Extend scheduled debt repayments from 3-year linear amortization to a 7-year balloon schedule to lower quarterly principal calls by ~40%.<br/>
                    2. <strong>Interest Rate Cap / Swaps:</strong> Hedge floating-rate exposure via interest rate derivative caps to mitigate the +{rate_shock_bps} bps sensitivity.<br/>
                    3. <strong>Capex Phase-Gating:</strong> Defer non-committed expansion capex (₹{incremental_debt_cr:,.1f} Cr) until quarterly DSCR restores above 1.50x.
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="background:{card_bg}; border:1px solid {card_border}; border-left:4px solid {accent_emerald}; border-radius:6px; padding:14px 16px;">
                <div style="font-size:0.85rem; font-weight:700; color:{accent_emerald}; margin-bottom:6px;">
                    🎯 Capital Allocation & Borrowing Clearance (CFO Authorization)
                </div>
                <div style="font-size:0.83rem; color:{text_color}; line-height:1.5;">
                    1. <strong>Approved Borrowing Envelope:</strong> The company is cleared to execute up to ₹{headroom_cr:,.1f} Cr in incremental debt financing.<br/>
                    2. <strong>Syndicate Pricing Target:</strong> Target an all-in borrowing spread below {incremental_annual_rate*100:.2f}% to preserve quarterly liquidity cushions.<br/>
                    3. <strong>Liquidity Escrow:</strong> Maintain a dedicated interest reserve account (DSRA) covering 1 quarter of debt service (₹{stressed_debt_service[0]:,.1f} Cr).
                </div>
            </div>
            """, unsafe_allow_html=True)

    with act_col2:
        st.markdown(f"""
        <div style="background:{card_bg}; border:1px solid {card_border}; border-left:4px solid {accent_blue}; border-radius:6px; padding:14px 16px;">
            <div style="font-size:0.85rem; font-weight:700; color:{accent_blue}; margin-bottom:6px;">
                📑 Credit Committee Sanction Conditions (Lender Mandate)
            </div>
            <div style="font-size:0.83rem; color:{text_color}; line-height:1.5;">
                1. <strong>Covenant Definition Standardization:</strong> Enforce strict inclusion of Ind AS 116 operating lease obligations in Total Economic Indebtedness.<br/>
                2. <strong>Monitoring Agency Oversight:</strong> Mandate quarterly compliance certificates with verified CFADS reconciliations prior to dividend distributions.<br/>
                3. <strong>Cash Sweep Mechanism:</strong> Activate a 50% excess cash sweep triggered whenever rolling 4-quarter DSCR drops below {dscr_floor + 0.15:.2f}x.
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Export & Audit Snapshot Section
    st.markdown("<br/>", unsafe_allow_html=True)
    exp1, exp2 = st.columns([3, 1])
    with exp1:
        st.caption(f"Audit Fingerprint: `{sim_res['simulation_id']}` · Generated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    with exp2:
        json_export = json.dumps(sim_res, indent=2)
        st.download_button(
            label="📥 Download Audit Memo (JSON)",
            data=json_export,
            file_name=f"covenant_audit_{selected_key}_{datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json",
            use_container_width=True,
        )


if __name__ == "__main__" or "streamlit" in globals():
    render_covenant_headroom_page()

"""
Admin Activity Log — admin-only usage analytics, model run history, transaction log.
"""
import json as _json
import streamlit as st
import pandas as pd
import plotly.express as px
import db
from helpers import ensure_session_state, require_role, plotly_layout, PLOTLY_CONFIG

ensure_session_state()
db.log_page_visit("Admin Activity Log")
require_role("admin")

st.markdown("### Activity Log")

# ── Load full audit data for charts ──────────────────────────────────────
_full_df = db.get_audit_log(limit=5000)
if _full_df.empty:
    st.info("No activity recorded yet. Visit a few pages and return here.")
    st.stop()

_full_df["ts"]   = pd.to_datetime(_full_df["ts"], utc=True)
_full_df["date"] = _full_df["ts"].dt.date
_full_df["hour"] = _full_df["ts"].dt.hour
_full_df["dow"]  = _full_df["ts"].dt.day_name()


def _who(row):
    if row["role"] == "viewer" and row["details"]:
        try:
            return _json.loads(row["details"]).get("display_name", row["username"])
        except Exception:
            pass
    return row["username"]


_full_df["who"] = _full_df.apply(_who, axis=1)

# Separate login events from page visits for accurate metrics
_page_df  = _full_df[_full_df["action_type"] == "page_visit"].copy()
_login_df = _full_df[_full_df["action_type"] == "login"].copy()

# ── KPI row ───────────────────────────────────────────────────────────────
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Page Visits",     len(_page_df))
k2.metric("Total Logins",    len(_login_df))
k3.metric("Unique Sessions", _full_df["session_id"].nunique())
k4.metric("Active Users",    _full_df["who"].nunique())
k5.metric("Most Visited",    _page_df["page_name"].value_counts().idxmax() if not _page_df.empty else "—")
st.divider()

# ── Login events ──────────────────────────────────────────────────────────
st.markdown("**Recent Login Events**")
if _login_df.empty:
    st.caption("No login events recorded yet. Login events are captured from the next deployment onward.")
else:
    _login_show = _login_df[["ts", "who", "role", "session_id"]].rename(columns={
        "ts": "Time (UTC)", "who": "User", "role": "Role", "session_id": "Session ID"
    })
    st.dataframe(_login_show, use_container_width=True, hide_index=True)
st.divider()

# ── 3-column chart row ────────────────────────────────────────────────────
c1, c2, c3 = st.columns(3)

with c1:
    st.markdown("**Page Popularity**")
    _pc = _page_df["page_name"].value_counts().reset_index()
    _pc.columns = ["Page", "Visits"]
    fig1 = px.bar(_pc, x="Visits", y="Page", orientation="h",
                  color="Visits", color_continuous_scale="teal")
    fig1.update_layout(**plotly_layout("", height=360),
                       yaxis={"categoryorder": "total ascending"},
                       coloraxis_showscale=False)
    st.plotly_chart(fig1, config=PLOTLY_CONFIG, use_container_width=True)

with c2:
    st.markdown("**Visits by User**")
    _uc = _page_df["who"].value_counts().reset_index()
    _uc.columns = ["User", "Visits"]
    fig2 = px.pie(_uc, names="User", values="Visits", hole=0.45)
    fig2.update_layout(**plotly_layout("", height=360))
    st.plotly_chart(fig2, config=PLOTLY_CONFIG, use_container_width=True)

with c3:
    st.markdown("**Activity Over Time**")
    _daily = _page_df.groupby(["date", "who"]).size().reset_index(name="Visits")
    fig3 = px.bar(_daily, x="date", y="Visits", color="who",
                  labels={"date": "Date", "who": "User"})
    fig3.update_layout(**plotly_layout("", height=360))
    st.plotly_chart(fig3, config=PLOTLY_CONFIG, use_container_width=True)

# ── Heatmap: hour x day-of-week ───────────────────────────────────────────
st.markdown("**Usage Heatmap — Hour of Day x Day of Week**")
_DOW = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
_heat = (
    _page_df.groupby(["dow", "hour"]).size()
    .reindex(index=_DOW, level=0)
    .reset_index(name="Visits")
)
fig4 = px.density_heatmap(
    _heat, x="hour", y="dow", z="Visits",
    category_orders={"dow": _DOW},
    color_continuous_scale="teal",
    labels={"hour": "Hour (UTC)", "dow": ""},
)
fig4.update_layout(**plotly_layout("", height=300))
st.plotly_chart(fig4, config=PLOTLY_CONFIG, use_container_width=True)
st.divider()

# ── Model run history ─────────────────────────────────────────────────────
st.markdown("**Model Run History**")
_who_opts  = ["All users"] + sorted(_full_df["who"].unique().tolist())
_page_opts = ["All pages", "Econometrics", "ML Models"]
mr1, mr2 = st.columns(2)
with mr1:
    _sel_who  = st.selectbox("User", _who_opts, key="runs_user_filter")
with mr2:
    _sel_page = st.selectbox("Page", _page_opts, key="runs_page_filter")

# Resolve display name back to username for DB lookup
if _sel_who != "All users":
    _match = _full_df[_full_df["who"] == _sel_who]["username"]
    _runs_username = _match.iloc[0] if not _match.empty else None
else:
    _runs_username = None

_page_key_map = {"Econometrics": "econometrics", "ML Models": "ml_models"}
_runs_page = _page_key_map.get(_sel_page)

if _runs_username and _runs_page:
    _runs_df = db.get_model_runs(_runs_username, _runs_page)
elif _runs_username:
    _econ = db.get_model_runs(_runs_username, "econometrics")
    _ml   = db.get_model_runs(_runs_username, "ml_models")
    _runs_df = pd.concat([_econ, _ml], ignore_index=True).sort_values("ts", ascending=False)
else:
    _runs_df = pd.DataFrame()

if not _runs_df.empty:
    st.dataframe(_runs_df, use_container_width=True, hide_index=True)
else:
    st.caption("No model runs recorded yet.")
st.divider()

# ── Transaction log ───────────────────────────────────────────────────────
st.markdown("**Transaction Log**")
tl1, tl2 = st.columns([2, 1])
with tl1:
    _filter_who = st.selectbox(
        "Filter by user",
        ["All users"] + sorted(_full_df["who"].unique().tolist()),
        key="audit_who_filter",
    )
with tl2:
    _limit = st.number_input("Max rows", min_value=50, max_value=1000, value=200, step=50)

if _filter_who != "All users":
    _match = _full_df[_full_df["who"] == _filter_who]["username"]
    _filter_username = _match.iloc[0] if not _match.empty else None
else:
    _filter_username = None

_log_df = db.get_audit_log(limit=int(_limit), username=_filter_username)
_log_df["who"] = _log_df.apply(_who, axis=1)

st.dataframe(
    _log_df[["ts", "who", "role", "page_name", "action_type", "session_id"]],
    use_container_width=True,
    hide_index=True,
)
st.caption(f"Showing {len(_log_df)} entries.")
st.download_button(
    "Download CSV",
    _log_df.to_csv(index=False).encode(),
    file_name="activity_log.csv",
    mime="text/csv",
)

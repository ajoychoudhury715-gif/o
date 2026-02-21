# pages/doctors/summary.py
"""Doctor summary — aggregate statistics across all doctors."""

from __future__ import annotations
import streamlit as st
import pandas as pd

from services.schedule_ops import ensure_schedule_columns, add_computed_columns
from data.profile_repo import load_doctors


def render() -> None:
    st.markdown("## 📊 Doctor Summary")

    df_sched = st.session_state.get("df")
    if df_sched is None:
        from data.schedule_repo import load_schedule
        from services.schedule_ops import ensure_row_ids
        df_sched = load_schedule()
        df_sched = ensure_schedule_columns(df_sched)
        df_sched = ensure_row_ids(df_sched)
        df_sched = add_computed_columns(df_sched)
        st.session_state.df = df_sched
    else:
        df_sched = ensure_schedule_columns(df_sched)
        df_sched = add_computed_columns(df_sched)

    if st.button("🔄 Refresh", key="dr_summary_refresh"):
        st.session_state.df = None
        st.cache_data.clear()
        st.rerun()

    if "DR." not in df_sched.columns or df_sched.empty:
        st.info("No schedule data available.")
        return

    # ── Appointments per doctor ────────────────────────────────────────────────
    st.markdown("#### 📅 Appointments per Doctor")
    appts_by_dr = (
        df_sched.groupby("DR.")
        .size()
        .reset_index(name="Appointments")
        .sort_values("Appointments", ascending=False)
    )
    st.dataframe(appts_by_dr, use_container_width=True, hide_index=True)
    st.bar_chart(appts_by_dr.set_index("DR.")["Appointments"])

    st.markdown("---")

    # ── Status breakdown per doctor ────────────────────────────────────────────
    if "STATUS" in df_sched.columns:
        st.markdown("#### 🔖 Status Breakdown per Doctor")
        pivot = (
            df_sched.groupby(["DR.", "STATUS"])
            .size()
            .unstack(fill_value=0)
            .reset_index()
        )
        st.dataframe(pivot, use_container_width=True, hide_index=True)

    st.markdown("---")

    # ── Procedure distribution ─────────────────────────────────────────────────
    if "Procedure" in df_sched.columns:
        st.markdown("#### 🦷 Procedure Distribution")
        procs = (
            df_sched[df_sched["Procedure"].astype(str).str.strip() != ""]
            .groupby("Procedure")
            .size()
            .reset_index(name="Count")
            .sort_values("Count", ascending=False)
            .head(20)
        )
        if not procs.empty:
            st.dataframe(procs, use_container_width=True, hide_index=True)
        else:
            st.info("No procedure data recorded.")

    st.markdown("---")

    # ── Average duration ───────────────────────────────────────────────────────
    if "In_min" in df_sched.columns and "Out_min" in df_sched.columns:
        st.markdown("#### ⏱ Average Appointment Duration")
        dur_df = df_sched.copy()
        dur_df["Duration_min"] = dur_df["Out_min"] - dur_df["In_min"]
        dur_df = dur_df[dur_df["Duration_min"] > 0]
        if not dur_df.empty:
            avg_dur = (
                dur_df.groupby("DR.")["Duration_min"]
                .mean()
                .reset_index(name="Avg Duration (min)")
                .sort_values("Avg Duration (min)", ascending=False)
            )
            avg_dur["Avg Duration (min)"] = avg_dur["Avg Duration (min)"].round(1)
            st.dataframe(avg_dur, use_container_width=True, hide_index=True)

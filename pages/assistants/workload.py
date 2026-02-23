# pages/assistants/workload.py
"""Assistant workload summary view."""

from __future__ import annotations
import streamlit as st
import pandas as pd

from services.schedule_ops import ensure_schedule_columns, add_computed_columns, compute_workload_summary
from services.profiles_cache import get_profiles_cache


def render() -> None:
    st.markdown("## 📊 Assistant Workload (Today)")

    df = st.session_state.get("df")
    if df is None:
        from data.schedule_repo import load_schedule
        from services.schedule_ops import ensure_row_ids
        df = load_schedule()
        df = ensure_schedule_columns(df)
        df = ensure_row_ids(df)
        df = add_computed_columns(df)
        st.session_state.df = df

    df = ensure_schedule_columns(df)
    df = add_computed_columns(df)

    # ── Filter to TODAY only ───────────────────────────────────────────────────
    from datetime import datetime
    from config.settings import IST
    today_str = datetime.now(IST).strftime("%Y-%m-%d")

    # Filter by DATE or appointment_date column
    date_col = "DATE" if "DATE" in df.columns else "appointment_date"
    if date_col in df.columns:
        df = df[df[date_col].astype(str).str.startswith(today_str)]

    cache = get_profiles_cache(st.session_state.get("profiles_cache_bust", 0))
    assistants = sorted(cache.get("assistants_list") or [])

    if st.button("🔄 Refresh", key="workload_refresh"):
        st.session_state.df = None
        st.cache_data.clear()
        st.rerun()

    workload_df = compute_workload_summary(df, assistants)

    if workload_df.empty or workload_df["Appointments"].sum() == 0:
        st.info("No workload data for today. Add appointments and assign assistants first.")
        return

    # ── Metrics row (TODAY only) ───────────────────────────────────────────────
    total_appointments = len(df)
    assigned = 0
    for _, row in df.iterrows():
        if any(str(row.get(r, "") or "").strip()
               for r in ["FIRST", "SECOND", "Third"] if r in row.index):
            assigned += 1
    unassigned = total_appointments - assigned

    c1, c2, c3 = st.columns(3)
    c1.metric("📅 Total Appointments", total_appointments)
    c2.metric("✅ With Assignments", assigned)
    c3.metric("⚠️ Unassigned", unassigned)

    st.markdown("---")

    # ── Workload table ─────────────────────────────────────────────────────────
    st.markdown("#### 📋 Assistant Workload (Clinic Hours: 9 AM - 7 PM)")
    display_df = workload_df[workload_df["Appointments"] > 0].sort_values("Hours Busy", ascending=False)

    # Display key columns with hours information
    display_cols = ["Assistant", "Appointments", "Hours Busy", "Hours Available"]
    st.dataframe(
        display_df[display_cols],
        width='stretch',
        hide_index=True,
        column_config={
            "Assistant": st.column_config.Column(width="medium"),
            "Appointments": st.column_config.NumberColumn(width="small"),
            "Hours Busy": st.column_config.NumberColumn(format="%.2f hrs", width="small"),
            "Hours Available": st.column_config.NumberColumn(format="%.2f hrs", width="small"),
        }
    )

    # ── Unassigned slots ───────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("#### ⚠️ Unassigned Appointments")
    unassigned_df = df[
        df[["FIRST", "SECOND", "Third"]].apply(
            lambda row: all(not str(row[r]).strip() for r in ["FIRST", "SECOND", "Third"]
                            if r in row.index),
            axis=1,
        )
    ] if all(c in df.columns for c in ["FIRST", "SECOND", "Third"]) else pd.DataFrame()

    if unassigned_df.empty:
        st.success("✅ All appointments have at least one assistant assigned.")
    else:
        display_cols = [c for c in ["Patient Name", "In Time", "Out Time", "DR.", "OP", "STATUS"]
                        if c in unassigned_df.columns]
        st.dataframe(
            unassigned_df[display_cols],
            width='stretch',
            hide_index=True,
        )

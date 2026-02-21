# pages/assistants/workload.py
"""Assistant workload summary view."""

from __future__ import annotations
import streamlit as st
import pandas as pd

from services.schedule_ops import ensure_schedule_columns, add_computed_columns, compute_workload_summary
from services.profiles_cache import get_profiles_cache


def render() -> None:
    st.markdown("## 📊 Assistant Workload")

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

    cache = get_profiles_cache(st.session_state.get("profiles_cache_bust", 0))
    assistants = sorted(cache.get("assistants_list") or [])

    if st.button("🔄 Refresh", key="workload_refresh"):
        st.session_state.df = None
        st.cache_data.clear()
        st.rerun()

    workload_df = compute_workload_summary(df, assistants)

    if workload_df.empty or workload_df["Total"].sum() == 0:
        st.info("No workload data available. Add appointments and assign assistants first.")
        return

    # ── Metrics row ────────────────────────────────────────────────────────────
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
    st.markdown("#### 📋 Appointments per Assistant")
    display_df = workload_df[workload_df["Total"] > 0].sort_values("Total", ascending=False)
    st.dataframe(display_df, use_container_width=True, hide_index=True)

    # ── Bar chart ──────────────────────────────────────────────────────────────
    if not display_df.empty:
        st.markdown("#### 📊 Workload Chart")
        st.bar_chart(display_df.set_index("Assistant")["Total"])

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
            use_container_width=True,
            hide_index=True,
        )

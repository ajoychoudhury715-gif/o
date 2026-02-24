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

    # ── Workload cards ─────────────────────────────────────────────────────────
    st.markdown("### 📋 Assistant Workload (Clinic Hours: 9 AM - 7 PM)")
    display_df = workload_df[workload_df["Appointments"] > 0].sort_values("Hours Busy", ascending=False)

    if display_df.empty:
        st.info("No workload data available.")
    else:
        cols_per_row = 3
        for row_start in range(0, len(display_df), cols_per_row):
            cols = st.columns(cols_per_row)
            for col_idx, (_, row) in enumerate(display_df.iloc[row_start:row_start + cols_per_row].iterrows()):
                with cols[col_idx]:
                    asst_name = str(row.get("Assistant", ""))
                    appointments = int(row.get("Appointments", 0))
                    hours_busy = float(row.get("Hours Busy", 0))
                    hours_available = float(row.get("Hours Available", 0))
                    overtime = float(row.get("Overtime (After 7 PM)", 0))

                    # Color coding based on workload
                    if hours_busy > 10:  # Overworked
                        border_color = "rgba(239, 68, 68, 0.3)"
                        bg_color = "rgba(239, 68, 68, 0.05)"
                        busy_color = "#ef4444"
                    elif hours_busy > 8:  # Heavy
                        border_color = "rgba(249, 115, 22, 0.3)"
                        bg_color = "rgba(249, 115, 22, 0.05)"
                        busy_color = "#f97316"
                    elif hours_busy > 5:  # Moderate
                        border_color = "rgba(59, 130, 246, 0.3)"
                        bg_color = "rgba(59, 130, 246, 0.05)"
                        busy_color = "#3b82f6"
                    else:  # Light
                        border_color = "rgba(34, 197, 94, 0.3)"
                        bg_color = "rgba(34, 197, 94, 0.05)"
                        busy_color = "#22c55e"

                    html_card = (
                        f'<div style="background:{bg_color};border:1.5px solid {border_color};border-radius:14px;padding:16px;margin-bottom:12px;backdrop-filter:blur(10px);transition:all 0.3s ease;box-shadow:0 2px 8px rgba(0,0,0,0.05);">'
                        '<div style="display:flex;justify-content:space-between;align-items:flex-start;gap:12px;margin-bottom:12px;">'
                        '<div style="min-width:0;flex:1;">'
                        f'<div style="font-weight:700;color:#1e293b;font-size:16px;word-break:break-word;">👥 {asst_name}</div>'
                        '</div>'
                        f'<span style="flex-shrink:0;color:{busy_color};font-size:11px;font-weight:700;padding:4px 10px;background:rgba({busy_color.lstrip("#").rstrip()}20);border-radius:6px;white-space:nowrap;">⏱ {hours_busy:.1f}h</span>'
                        '</div>'
                        '<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;padding:10px 0;border-top:1px solid rgba(0,0,0,0.05);border-bottom:1px solid rgba(0,0,0,0.05);">'
                        f'<div style="text-align:center;"><div style="font-size:12px;color:#94a3b8;">📅 Appointments</div><div style="font-size:18px;font-weight:700;color:#1e293b;margin-top:4px;">{appointments}</div></div>'
                        f'<div style="text-align:center;"><div style="font-size:12px;color:#94a3b8;">✅ Available</div><div style="font-size:18px;font-weight:700;color:#22c55e;margin-top:4px;">{hours_available:.1f}h</div></div>'
                        '</div>'
                        f'<div style="display:flex;gap:8px;margin-top:10px;font-size:12px;color:#94a3b8;">'
                        f'<span>⏰ Overtime: <span style="font-weight:600;color:{busy_color};">{overtime:.1f}h</span></span>'
                        '</div>'
                        '</div>'
                    )
                    st.markdown(html_card, unsafe_allow_html=True)

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

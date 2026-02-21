# pages/assistants/attendance.py
"""Attendance history and summary view."""

from __future__ import annotations
import streamlit as st
import pandas as pd
import datetime

from data.attendance_repo import load_attendance, get_today_punch_map
from services.utils import now_ist
from services.profiles_cache import get_profiles_cache


def render() -> None:
    st.markdown("## 🕐 Attendance")

    cache = get_profiles_cache(st.session_state.get("profiles_cache_bust", 0))
    assistants = sorted(cache.get("assistants_list") or [])
    today_str = now_ist().date().isoformat()

    # ── Today's status ─────────────────────────────────────────────────────────
    st.markdown("### 📅 Today's Punch Status")
    punch_map = get_today_punch_map(today_str)

    if not assistants:
        st.info("No assistants found.")
    else:
        cols_per_row = 3
        for row_start in range(0, len(assistants), cols_per_row):
            cols = st.columns(cols_per_row)
            for col_idx, asst in enumerate(assistants[row_start:row_start + cols_per_row]):
                with cols[col_idx]:
                    pdata = punch_map.get(asst.upper(), {})
                    pin = pdata.get("punch_in", "")
                    pout = pdata.get("punch_out", "")

                    if pin and pout:
                        color = "#22c55e"
                        label = f"✅ {pin[:5]} – {pout[:5]}"
                        bg = "rgba(34,197,94,0.1)"
                    elif pin:
                        color = "#3b82f6"
                        label = f"🟢 In @ {pin[:5]}"
                        bg = "rgba(59,130,246,0.1)"
                    else:
                        color = "#ef4444"
                        label = "⚠️ Not punched"
                        bg = "rgba(239,68,68,0.1)"

                    st.markdown(
                        f"""<div style="background:{bg};border:1px solid {color}33;
                             border-radius:8px;padding:8px 12px;margin-bottom:6px;">
                          <div style="font-weight:600;color:#f1f5f9;font-size:13px;">👤 {asst}</div>
                          <div style="font-size:12px;color:{color};margin-top:2px;">{label}</div>
                        </div>""",
                        unsafe_allow_html=True,
                    )

    st.markdown("---")

    # ── History table ──────────────────────────────────────────────────────────
    st.markdown("### 📋 Attendance History")

    col_asst, col_from, col_to, col_refresh = st.columns([2, 1, 1, 1])
    with col_asst:
        asst_filter = st.selectbox(
            "Assistant", ["All"] + assistants, key="att_asst_filter"
        )
    with col_from:
        from_date = st.date_input(
            "From",
            value=datetime.date.today() - datetime.timedelta(days=30),
            key="att_from",
        )
    with col_to:
        to_date = st.date_input("To", value=datetime.date.today(), key="att_to")
    with col_refresh:
        if st.button("🔄", use_container_width=True, key="att_refresh"):
            st.rerun()

    att_df = load_attendance()

    if att_df.empty:
        st.info("No attendance records found.")
        return

    # Normalise column names
    att_df.columns = [str(c).strip().lower().replace(" ", "_") for c in att_df.columns]

    # Filter by assistant
    if asst_filter != "All" and "assistant" in att_df.columns:
        att_df = att_df[att_df["assistant"].astype(str).str.strip().str.upper() == asst_filter.upper()]

    # Filter by date range
    if "date" in att_df.columns:
        att_df["date"] = pd.to_datetime(att_df["date"], errors="coerce").dt.date
        att_df = att_df[
            (att_df["date"] >= from_date) & (att_df["date"] <= to_date)
        ]

    if att_df.empty:
        st.info("No records for the selected filters.")
        return

    # Display
    display_cols = [c for c in ["date", "assistant", "punch_in", "punch_out"]
                    if c in att_df.columns]
    st.dataframe(
        att_df[display_cols].sort_values(
            by="date" if "date" in display_cols else display_cols[0],
            ascending=False,
        ),
        use_container_width=True,
        hide_index=True,
    )

    # Summary
    st.markdown("---")
    st.markdown("#### 📊 Summary")
    if "assistant" in att_df.columns and "punch_in" in att_df.columns:
        summary = (
            att_df.groupby("assistant")
            .agg(days_present=("punch_in", "count"))
            .reset_index()
            .sort_values("days_present", ascending=False)
        )
        st.dataframe(summary, use_container_width=True, hide_index=True)

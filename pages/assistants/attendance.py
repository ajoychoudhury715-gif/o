# pages/assistants/attendance.py
"""Attendance history and summary view."""

from __future__ import annotations
import streamlit as st
import pandas as pd
import datetime

from data.attendance_repo import load_attendance, get_today_punch_map
from services.utils import now_ist, time_to_12h, coerce_to_time_obj
from services.profiles_cache import get_profiles_cache


def render() -> None:
    st.markdown("## 🕐 Attendance")

    cache = get_profiles_cache(st.session_state.get("profiles_cache_bust", 0))
    assistants = sorted({str(name).strip().upper() for name in (cache.get("assistants_list") or []) if str(name).strip()})
    today_str = now_ist().date().isoformat()

    # Check if user is logged in as an assistant
    current_user = str(st.session_state.get("current_user", "") or "").strip()
    current_user_upper = current_user.upper()
    user_role = str(st.session_state.get("user_role", "") or "").strip().lower()

    att_df = load_attendance()
    if not att_df.empty:
        att_df = att_df.copy()
        if "assistant" in att_df.columns:
            att_df["assistant"] = att_df["assistant"].astype(str).str.strip().str.upper()

    attendance_assistants = (
        sorted(att_df["assistant"].dropna().astype(str).str.strip().str.upper().unique().tolist())
        if not att_df.empty and "assistant" in att_df.columns
        else []
    )

    # If assistant is logged in, show only their data
    if user_role == "assistant" and current_user_upper:
        display_assistants = [current_user_upper]
        st.markdown(f"### 👤 Your Punch Records")
    else:
        display_assistants = sorted(set(assistants) | set(attendance_assistants))
        st.markdown(f"### 📅 All Assistants Punch Status")

    # ── Today's status ─────────────────────────────────────────────────────────
    punch_map = get_today_punch_map(today_str)
    if not (user_role == "assistant" and current_user_upper):
        display_assistants = sorted(set(display_assistants) | set(punch_map.keys()))

    if not display_assistants:
        st.info("No assistants found.")
    else:
        cols_per_row = 3
        for row_start in range(0, len(display_assistants), cols_per_row):
            cols = st.columns(cols_per_row)
            for col_idx, asst in enumerate(display_assistants[row_start:row_start + cols_per_row]):
                with cols[col_idx]:
                    pdata = punch_map.get(asst.upper(), {})
                    pin = pdata.get("punch_in", "")
                    pout = pdata.get("punch_out", "")

                    # Convert to 12-hour format for display
                    pin_12h = time_to_12h(coerce_to_time_obj(pin)) if pin else ""
                    pout_12h = time_to_12h(coerce_to_time_obj(pout)) if pout else ""

                    if pin and pout:
                        color = "#22c55e"
                        label = f"✅ {pin_12h} – {pout_12h}"
                        bg = "rgba(34,197,94,0.1)"
                    elif pin:
                        color = "#3b82f6"
                        label = f"🟢 In @ {pin_12h}"
                        bg = "rgba(59,130,246,0.1)"
                    else:
                        color = "#ef4444"
                        label = "⚠️ Not punched"
                        bg = "rgba(239,68,68,0.1)"

                    st.markdown(
                        f"""<div style="background:{bg};border:1px solid {color}33;
                             border-radius:8px;padding:8px 12px;margin-bottom:6px;">
                          <div style="font-weight:600;color:#0f172a;font-size:13px;">👤 {asst}</div>
                          <div style="font-size:12px;color:{color};margin-top:2px;">{label}</div>
                        </div>""",
                        unsafe_allow_html=True,
                    )

    st.markdown("---")

    # ── History table ──────────────────────────────────────────────────────────
    st.markdown("### 📋 Attendance History")

    col_asst, col_from, col_to, col_refresh = st.columns([2, 1, 1, 1])
    with col_asst:
        if user_role == "assistant" and current_user_upper:
            # For assistants, don't show dropdown - just show their name
            st.write(f"**{current_user_upper}**")
            asst_filter = current_user_upper
        else:
            # For admins/frontdesk, show dropdown with all assistants
            filter_options = sorted(set(assistants) | set(attendance_assistants) | set(punch_map.keys()))
            asst_filter = st.selectbox(
                "Assistant", ["All"] + filter_options, key="att_asst_filter"
            )
    with col_from:
        from_date = st.date_input(
            "From",
            value=now_ist().date() - datetime.timedelta(days=30),
            key="att_from",
        )
    with col_to:
        to_date = st.date_input("To", value=now_ist().date(), key="att_to")
    with col_refresh:
        if st.button("🔄", width='stretch', key="att_refresh"):
            st.rerun()

    if att_df.empty:
        st.info("No attendance records found.")
        return

    # Normalise column names
    att_df.columns = [str(c).strip().lower().replace(" ", "_") for c in att_df.columns]
    if "assistant" in att_df.columns:
        att_df["assistant"] = att_df["assistant"].astype(str).str.strip().str.upper()
    if "punch_in" in att_df.columns:
        att_df["punch_in"] = att_df["punch_in"].fillna("").astype(str).str.strip()
    if "punch_out" in att_df.columns:
        att_df["punch_out"] = att_df["punch_out"].fillna("").astype(str).str.strip()

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

    # Display with 12-hour formatted times
    display_df = att_df.copy()
    if "punch_in" in display_df.columns:
        display_df["punch_in"] = display_df["punch_in"].apply(
            lambda x: time_to_12h(coerce_to_time_obj(x)) if x else ""
        )
    if "punch_out" in display_df.columns:
        display_df["punch_out"] = display_df["punch_out"].apply(
            lambda x: time_to_12h(coerce_to_time_obj(x)) if x else ""
        )

    display_cols = [c for c in ["date", "assistant", "punch_in", "punch_out"]
                    if c in display_df.columns]
    st.dataframe(
        display_df[display_cols].sort_values(
            by="date" if "date" in display_cols else display_cols[0],
            ascending=False,
        ),
        width='stretch',
        hide_index=True,
    )

    # Summary
    st.markdown("---")
    st.markdown("#### 📊 Summary")
    if "assistant" in att_df.columns and "punch_in" in att_df.columns:
        # If assistant is logged in, only show their summary
        summary_df = att_df
        if user_role == "assistant" and current_user_upper:
            summary_df = att_df[att_df["assistant"].astype(str).str.strip().str.upper() == current_user_upper]

        summary_df = summary_df.copy()
        summary_df["has_punch_in"] = summary_df["punch_in"].astype(str).str.strip().ne("")

        summary = (
            summary_df.groupby("assistant")
            .agg(days_present=("has_punch_in", "sum"))
            .reset_index()
            .sort_values("days_present", ascending=False)
        )
        st.dataframe(summary, width='stretch', hide_index=True)

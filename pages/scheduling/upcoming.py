# pages/scheduling/upcoming.py
"""Upcoming appointments view (next 60 minutes by default)."""

from __future__ import annotations
import streamlit as st

from services.schedule_ops import (
    ensure_schedule_columns, ensure_row_ids, add_computed_columns,
    filter_upcoming, update_status,
)
from state.save_manager import maybe_save
from components.schedule_card import render_schedule_card


def render() -> None:
    st.markdown("## 🟡 Upcoming Appointments")

    df = st.session_state.get("df")
    if df is None:
        from data.schedule_repo import load_schedule
        df = load_schedule()
        st.session_state.df = df

    df = ensure_schedule_columns(df)
    df = ensure_row_ids(df)
    df = add_computed_columns(df)
    st.session_state.df = df

    # Filter to today's appointments only
    from datetime import datetime
    from config.settings import IST
    today_str = datetime.now(IST).strftime("%Y-%m-%d")
    date_col = "DATE" if "DATE" in df.columns else "appointment_date"
    if date_col in df.columns:
        df = df[df[date_col].astype(str).str.startswith(today_str)]

    col_window, col_refresh = st.columns([4, 1])
    with col_window:
        window = st.slider(
            "Show appointments starting within (minutes)",
            min_value=15,
            max_value=240,
            value=60,
            step=15,
            key="upcoming_window",
        )
    with col_refresh:
        if st.button("🔄", width='stretch', key="upcoming_refresh"):
            st.session_state.df = None
            st.cache_data.clear()
            st.rerun()

    upcoming = filter_upcoming(df, minutes_ahead=window)

    if upcoming.empty:
        st.info(f"✅ No upcoming appointments in the next {window} minutes.")
        return

    st.markdown(f"**{len(upcoming)} upcoming appointment(s)**")

    for idx, (_, row) in enumerate(upcoming.iterrows()):
        row_dict = row.to_dict()
        row_id = str(row_dict.get("REMINDER_ROW_ID", "")).strip() or str(idx)
        render_schedule_card(
            row=row_dict,
            on_status_change=lambda rid, ns: _on_status_change(df, rid, ns),
            on_delete=lambda rid: _on_delete(df, rid),
            idx=idx,
        )
        st.markdown("---")


def _on_status_change(df, row_id: str, new_status: str) -> None:
    updated = update_status(df, row_id, new_status)
    st.session_state.df = updated
    maybe_save(updated, message=f"Status → {new_status}")
    st.rerun()


def _on_delete(df, row_id: str) -> None:
    mask = df["REMINDER_ROW_ID"].astype(str).str.strip() == row_id
    updated = df[~mask].reset_index(drop=True)
    updated.attrs = df.attrs.copy()
    st.session_state.df = updated
    maybe_save(updated, message="Row deleted")
    st.rerun()

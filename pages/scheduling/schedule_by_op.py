# pages/scheduling/schedule_by_op.py
"""Schedule filtered by OP room."""

from __future__ import annotations
import streamlit as st

from services.schedule_ops import (
    ensure_schedule_columns, ensure_row_ids, add_computed_columns,
    update_status, filter_by_op,
)
from state.save_manager import maybe_save
from components.schedule_card import render_schedule_card, render_add_appointment_form
from config.constants import OP_ROOMS
from services.profiles_cache import get_profiles_cache


def render() -> None:
    st.markdown("## 🏥 Schedule by OP Room")

    df = st.session_state.get("df")
    if df is None:
        from data.schedule_repo import load_schedule
        df = load_schedule()
        st.session_state.df = df

    df = ensure_schedule_columns(df)
    df = ensure_row_ids(df)
    df = add_computed_columns(df)
    st.session_state.df = df

    cache = get_profiles_cache(st.session_state.get("profiles_cache_bust", 0))
    doctors = sorted(cache.get("doctors_list") or [])
    assistants = sorted(cache.get("assistants_list") or [])

    # ── Initialize selected date in session state ───────────────────────────────
    from datetime import date
    if "selected_schedule_date" not in st.session_state:
        st.session_state.selected_schedule_date = date.today()

    # ── Date Picker ────────────────────────────────────────────────────────────
    st.markdown("### 📆 Select Date")
    selected_date = st.date_input(
        "Choose a date",
        value=st.session_state.selected_schedule_date,
        key="schedule_by_op_date_picker",
        label_visibility="collapsed",
    )
    st.session_state.selected_schedule_date = selected_date

    # OP room selector
    all_ops = sorted(df["OP"].dropna().astype(str).str.strip().unique().tolist()) if "OP" in df.columns else []
    all_ops = sorted(set(all_ops + OP_ROOMS))
    all_ops = [o for o in all_ops if o]

    col_op, col_refresh = st.columns([4, 1])
    with col_op:
        selected_op = st.selectbox("Select OP Room", all_ops, key="op_room_select")
    with col_refresh:
        if st.button("🔄", width='stretch', key="op_refresh"):
            st.session_state.df = None
            st.cache_data.clear()
            st.rerun()

    # ── Filter by date and OP ──────────────────────────────────────────────────
    date_str = selected_date.isoformat() if selected_date else ""
    filtered = filter_by_op(df, selected_op)
    
    # Filter by selected date (show appointments with matching date OR empty/null dates for backward compatibility)
    if date_str and "DATE" in filtered.columns:
        date_col = filtered.get("DATE", "").astype(str).str.strip()
        filtered = filtered[(date_col == date_str) | (date_col == "")]

    render_add_appointment_form(
        doctors=doctors,
        assistants=assistants,
        op_rooms=all_ops,
        selected_date=selected_date,
        on_save=lambda row: _on_add(df, row),
    )

    st.markdown(f"**{len(filtered)} appointment(s) in {selected_op} on {selected_date.strftime('%A, %B %d, %Y')}**")

    # ── Check if no appointments exist for the selected date and OP ─────────────
    if len(filtered) == 0:
        st.info(f"✨ No appointments scheduled for {selected_op} on this date.")
        return

    for idx, (_, row) in enumerate(filtered.iterrows()):
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


def _on_add(df, row: dict) -> None:
    import pandas as pd
    updated = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    updated.attrs = df.attrs.copy()
    st.session_state.df = updated
    maybe_save(updated, message="Appointment added")
    st.rerun()

# pages/scheduling/schedule_by_op.py
"""Schedule filtered by OP room."""

from __future__ import annotations
import pandas as pd
import streamlit as st

from services.schedule_ops import (
    ensure_schedule_columns, ensure_row_ids, add_computed_columns,
    update_status, filter_by_op,
)
from state.save_manager import maybe_save
from components.schedule_card import render_schedule_card, render_add_appointment_form
from config.constants import OP_ROOMS
from services.profiles_cache import get_profiles_cache
from data.schedule_repo import clear_schedule_cache


def _strict_date_mask(date_series: pd.Series, selected_date) -> tuple[pd.Series, str]:
    """Build strict date match mask with tolerant normalization for legacy date strings."""
    target_dt = pd.to_datetime(selected_date, errors="coerce")
    if pd.isna(target_dt):
        return pd.Series(False, index=date_series.index), ""

    formatted_date = target_dt.strftime("%Y-%m-%d")
    raw_dates = date_series.fillna("").astype(str).str.strip()
    raw_lower = raw_dates.str.lower()

    direct_match = (
        raw_dates.eq(formatted_date)
        | raw_dates.str.startswith(f"{formatted_date}T")
        | raw_dates.str.startswith(f"{formatted_date} ")
    )

    parse_input = raw_dates.where(~raw_lower.isin(["", "nan", "none", "nat"]))
    normalized_default = pd.to_datetime(parse_input, errors="coerce").dt.strftime("%Y-%m-%d")
    normalized_dayfirst = pd.to_datetime(parse_input, errors="coerce", dayfirst=True).dt.strftime("%Y-%m-%d")

    numeric_dates = pd.to_numeric(parse_input, errors="coerce")
    normalized_excel = pd.to_datetime(
        numeric_dates, unit="D", origin="1899-12-30", errors="coerce"
    ).dt.strftime("%Y-%m-%d")

    mask = (
        direct_match
        | normalized_default.eq(formatted_date)
        | normalized_dayfirst.eq(formatted_date)
        | normalized_excel.eq(formatted_date)
    )
    return mask.fillna(False), formatted_date


def render() -> None:
    st.markdown("## 🏥 Schedule by OP Room")

    # ── Initialize selected date in session state ───────────────────────────────
    from datetime import date
    if "schedule_by_op_date" not in st.session_state:
        st.session_state.schedule_by_op_date = date.today()

    # ── Date Picker ────────────────────────────────────────────────────────────
    st.markdown("### 📆 Select Date")
    selected_date = st.date_input(
        "Choose a date",
        value=st.session_state.schedule_by_op_date,
        key="schedule_by_op_date_picker",
        label_visibility="collapsed",
    )

    # ── CRITICAL: Detect date change and clear cache ──────────────────────────
    if selected_date != st.session_state.schedule_by_op_date:
        st.session_state.schedule_by_op_date = selected_date
        st.session_state.df = None
        clear_schedule_cache()
        st.rerun()

    st.session_state.schedule_by_op_date = selected_date

    # ── Load data ──────────────────────────────────────────────────────────────
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
    filtered = filter_by_op(df, selected_op)

    # Strict date filter; do not include blank dates.
    if selected_date and ("DATE" in filtered.columns or "appointment_date" in filtered.columns):
        date_series = filtered["DATE"] if "DATE" in filtered.columns else pd.Series([""] * len(filtered), index=filtered.index)
        if "appointment_date" in filtered.columns:
            primary = date_series.fillna("").astype(str).str.strip()
            fallback = filtered["appointment_date"].fillna("").astype(str).str.strip()
            date_series = primary.where(primary.ne(""), fallback)
        date_mask, _ = _strict_date_mask(date_series, selected_date)
        filtered = filtered[date_mask].copy()

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
        st.info("No appointments scheduled")
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

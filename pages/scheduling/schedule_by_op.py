# pages/scheduling/schedule_by_op.py
"""Schedule filtered by OP room."""

from __future__ import annotations
import pandas as pd
import streamlit as st

from services.schedule_ops import (
    ensure_schedule_columns, ensure_row_ids, add_computed_columns,
    update_status, filter_by_op, build_op_status_summary, get_op_detail_frames,
)
from state.save_manager import maybe_save
from components.schedule_card import render_schedule_card, render_add_appointment_form
from config.constants import OP_ROOMS
from services.profiles_cache import get_profiles_cache
from data.schedule_repo import clear_schedule_cache
from security.rbac import has_access, require_access
from services.utils import now_ist, time_to_12h


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


def _format_minutes_label(total_minutes) -> str:
    minutes = max(0, int(float(total_minutes or 0)))
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours}h {mins:02d}m"


def _format_dt_label(value) -> str:
    if value is None or (hasattr(pd, "isna") and pd.isna(value)):
        return "—"
    dt_value = value.to_pydatetime() if hasattr(value, "to_pydatetime") else value
    if not hasattr(dt_value, "time"):
        return str(value or "—")
    return time_to_12h(dt_value.astimezone(now_ist().tzinfo).time().replace(second=0, microsecond=0))


def _render_op_status_board(summary_df: pd.DataFrame, selected_op: str) -> None:
    st.markdown("### 🧭 OP Operational Visibility")
    st.caption("Busy/free status is synced from patient status. Only appointments marked ON GOING make an OP Busy; DONE and CANCELLED free the OP immediately.")

    if summary_df is None or summary_df.empty:
        st.info("No OP activity recorded for this date yet.")
        return

    cols_per_row = 4
    for start in range(0, len(summary_df), cols_per_row):
        cols = st.columns(cols_per_row)
        for offset, (_, row) in enumerate(summary_df.iloc[start:start + cols_per_row].iterrows()):
            with cols[offset]:
                op_name = str(row.get("OP", "") or "").strip()
                status = str(row.get("Current Status", "") or "").strip().upper() or "FREE"
                current_for = _format_minutes_label(row.get("Current For Minutes", 0))
                busy_logged = _format_minutes_label(row.get("Busy Logged Minutes", 0))
                free_logged = _format_minutes_label(row.get("Free Logged Minutes", 0))
                busy_sessions = int(row.get("Busy Sessions", 0) or 0)
                patient = str(row.get("Current Patient", "") or "").strip()
                label = "Busy For" if status == "BUSY" else "Free For"
                status_color = "#047857" if status == "BUSY" else "#64748b"
                border_color = "#0f766e" if op_name == selected_op else ("#10b981" if status == "BUSY" else "#cbd5e1")

                st.markdown(
                    f"""
                    <div style="border:2px solid {border_color};border-radius:16px;padding:14px 14px 10px 14px;background:#ffffff;">
                      <div style="display:flex;justify-content:space-between;gap:8px;align-items:center;">
                        <div style="font-size:1rem;font-weight:700;color:#0f172a;">{op_name}</div>
                        <div style="font-size:0.78rem;font-weight:700;color:{status_color};">{status}</div>
                      </div>
                      <div style="font-size:0.8rem;color:#475569;margin-top:8px;">{label}: <b>{current_for}</b></div>
                      <div style="font-size:0.8rem;color:#475569;margin-top:4px;">Busy Logged: <b>{busy_logged}</b></div>
                      <div style="font-size:0.8rem;color:#475569;margin-top:4px;">Free Logged: <b>{free_logged}</b></div>
                      <div style="font-size:0.8rem;color:#475569;margin-top:4px;">Busy Sessions: <b>{busy_sessions}</b></div>
                      <div style="font-size:0.8rem;color:#475569;margin-top:8px;">{('Current Patient: <b>' + patient + '</b>') if patient else 'Current Patient: <b>None</b>'}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


def _render_selected_op_analytics(df: pd.DataFrame, selected_op: str, selected_date) -> None:
    busy_df, free_df, summary = get_op_detail_frames(df, selected_op, selected_date)
    st.markdown(f"### 🔎 {selected_op} Operational Detail")

    current_status = str(summary.get("Current Status", "FREE") or "FREE").strip().upper()
    current_patient = str(summary.get("Current Patient", "") or "").strip()
    current_for_label = "Busy For" if current_status == "BUSY" else "Free For"

    metric_cols = st.columns(4)
    metric_cols[0].metric("Current Status", current_status)
    metric_cols[1].metric(current_for_label, _format_minutes_label(summary.get("Current For Minutes", 0)))
    metric_cols[2].metric("Busy Logged", _format_minutes_label(summary.get("Busy Logged Minutes", 0)))
    metric_cols[3].metric("Free Logged", _format_minutes_label(summary.get("Free Logged Minutes", 0)))

    if current_status == "BUSY" and current_patient:
        st.warning(f"{selected_op} is currently busy with {current_patient}.")
    elif current_status == "FREE":
        st.success(f"{selected_op} is currently free.")

    detail_cols = st.columns(2)
    with detail_cols[0]:
        st.markdown("#### Busy Sessions")
        if busy_df is None or busy_df.empty:
            st.info("No recorded busy session for this OP on the selected date.")
        else:
            busy_display = busy_df.copy()
            for col in ["Started", "Ended", "Scheduled In", "Scheduled Out"]:
                if col in busy_display.columns:
                    busy_display[col] = busy_display[col].apply(_format_dt_label)
            if "Busy Minutes" in busy_display.columns:
                busy_display["Busy For"] = busy_display["Busy Minutes"].apply(_format_minutes_label)
                busy_display = busy_display.drop(columns=["Busy Minutes"])
            st.dataframe(busy_display, width="stretch", hide_index=True)

    with detail_cols[1]:
        st.markdown("#### Free Gaps")
        if free_df is None or free_df.empty:
            st.info("No free gap recorded yet for this OP on the selected date.")
        else:
            free_display = free_df.copy()
            for col in ["From", "To"]:
                if col in free_display.columns:
                    free_display[col] = free_display[col].apply(_format_dt_label)
            if "Free Minutes" in free_display.columns:
                free_display["Free For"] = free_display["Free Minutes"].apply(_format_minutes_label)
                free_display = free_display.drop(columns=["Free Minutes"])
            st.dataframe(free_display, width="stretch", hide_index=True)


def render() -> None:
    st.markdown("## 🏥 Schedule by OP Room")

    # ── Initialize selected date to TODAY in IST (only on first load) ────────────
    from datetime import datetime
    from config.settings import IST
    today = datetime.now(IST).date()
    if "schedule_by_op_date" not in st.session_state:
        st.session_state.schedule_by_op_date = today

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

    op_summary_df = build_op_status_summary(df, selected_date, op_rooms=all_ops)
    _render_op_status_board(op_summary_df, selected_op)
    _render_selected_op_analytics(df, selected_op, selected_date)

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

    if has_access("action::schedule::add_appointment"):
        render_add_appointment_form(
            doctors=doctors,
            assistants=assistants,
            op_rooms=all_ops,
            selected_date=selected_date,
            on_save=lambda row: _on_add(df, row),
        )
    else:
        st.caption("Add Appointment is restricted for your account.")

    st.markdown("### 📋 Appointments in Selected OP")
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
    require_access("action::schedule::update_status", "updating appointment status")
    updated = update_status(df, row_id, new_status)
    st.session_state.df = updated
    maybe_save(updated, message=f"Status → {new_status}")
    st.rerun()


def _on_delete(df, row_id: str) -> None:
    require_access("action::schedule::delete_appointment", "deleting appointments")
    mask = df["REMINDER_ROW_ID"].astype(str).str.strip() == row_id
    updated = df[~mask].reset_index(drop=True)
    updated.attrs = df.attrs.copy()
    st.session_state.df = updated
    maybe_save(updated, message="Row deleted")
    st.rerun()


def _on_add(df, row: dict) -> None:
    require_access("action::schedule::add_appointment", "adding appointments")
    import pandas as pd
    updated = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    updated.attrs = df.attrs.copy()
    st.session_state.df = updated
    maybe_save(updated, message="Appointment added")
    st.rerun()

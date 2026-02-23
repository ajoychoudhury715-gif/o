# pages/scheduling/full_schedule.py
"""Full Schedule view — card + table toggle, add/edit/delete, auto-allocate."""

from __future__ import annotations
import pandas as pd
import streamlit as st

from data.schedule_repo import load_schedule, clear_schedule_cache
from data.profile_repo import load_assistants, load_doctors
from services.schedule_ops import (
    ensure_schedule_columns,
    ensure_row_ids,
    update_status,
    add_computed_columns,
)
from services.profiles_cache import (
    get_profiles_cache,
    get_all_assistants,
    get_all_doctors,
)
from state.save_manager import maybe_save, queue_unsaved
from components.schedule_card import render_schedule_card, render_add_appointment_form
from components.schedule_table import render_schedule_table, render_edit_row_form
from components.time_block_editor import render_time_block_editor
from config.constants import OP_ROOMS
from security.rbac import has_access, require_access


def _strict_date_mask(date_series: pd.Series, selected_date) -> tuple[pd.Series, str]:
    """Build strict date match mask with tolerant normalization for legacy date strings."""
    target_dt = pd.to_datetime(selected_date, errors="coerce")
    if pd.isna(target_dt):
        return pd.Series(False, index=date_series.index), ""

    formatted_date = target_dt.strftime("%Y-%m-%d")
    raw_dates = date_series.fillna("").astype(str).str.strip()
    raw_lower = raw_dates.str.lower()

    # Direct match handles ISO DATE and ISO TIMESTAMP strings.
    direct_match = (
        raw_dates.eq(formatted_date)
        | raw_dates.str.startswith(f"{formatted_date}T")
        | raw_dates.str.startswith(f"{formatted_date} ")
    )

    parse_input = raw_dates.where(~raw_lower.isin(["", "nan", "none", "nat"]))
    normalized_default = pd.to_datetime(parse_input, errors="coerce").dt.strftime("%Y-%m-%d")
    normalized_dayfirst = pd.to_datetime(parse_input, errors="coerce", dayfirst=True).dt.strftime("%Y-%m-%d")

    # Support legacy Excel serial dates if any historical rows were imported that way.
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
    # ── Initialize selected date in session state (BEFORE loading data!) ──────
    from datetime import date
    if "selected_schedule_date" not in st.session_state:
        st.session_state.selected_schedule_date = date.today()

    # ── Header: title (left) + inline date picker (right) ─────────────────────
    title_col, date_col = st.columns([6, 3], gap="small")
    with title_col:
        st.markdown("## 📅 Full Schedule")
    with date_col:
        selected_date = st.date_input(
            "Schedule date",
            value=st.session_state.selected_schedule_date,
            key="sched_date_picker",
            label_visibility="collapsed",
            format="YYYY-MM-DD",
        )
        st.markdown(
            f"""
            <style>
            div[data-testid="stDateInput"] > div {{
                border: 1px solid #e2e8f0;
                border-radius: 10px;
                background: #f8fafc;
            }}
            div[data-testid="stDateInput"] input {{
                color: transparent !important;
                text-shadow: none !important;
            }}
            .header-date-text {{
                margin-top: -2.05rem;
                margin-left: 0.75rem;
                pointer-events: none;
                color: #0f172a;
                font-size: 0.92rem;
                font-weight: 500;
                white-space: nowrap;
            }}
            </style>
            <div class="header-date-text">{selected_date.strftime('%A, %B %d, %Y')}</div>
            """,
            unsafe_allow_html=True,
        )

    # ── CRITICAL: Detect date change and clear cache BEFORE loading ───────────
    if selected_date != st.session_state.selected_schedule_date:
        st.session_state.selected_schedule_date = selected_date
        st.session_state.df = None
        clear_schedule_cache()
        st.rerun()

    st.session_state.selected_schedule_date = selected_date

    # ── Load data ──────────────────────────────────────────────────────────────
    df = st.session_state.get("df")
    if df is None:
        with st.spinner("Loading schedule…"):
            df = load_schedule()
        st.session_state.df = df

    df = ensure_schedule_columns(df)
    df = ensure_row_ids(df)
    df = add_computed_columns(df)
    st.session_state.df = df

    cache_bust = st.session_state.get("profiles_cache_bust", 0)
    cache = get_profiles_cache(cache_bust)
    doctors = sorted(cache.get("doctors_list") or [])
    assistants = sorted(cache.get("assistants_list") or [])
    op_rooms = sorted(OP_ROOMS)

    # ── Toolbar ────────────────────────────────────────────────────────────────
    col_view, col_search, col_alloc, col_refresh = st.columns([2, 3, 2, 1])
    with col_view:
        view_mode = st.radio(
            "View",
            ["🃏 Cards", "📊 Table"],
            horizontal=True,
            key="sched_view_mode",
            label_visibility="collapsed",
        )
    with col_search:
        search_q = st.text_input(
            "🔍 Search",
            placeholder="Name / Doctor / OP…",
            key="sched_search",
            label_visibility="collapsed",
        )
    with col_alloc:
        can_auto_allocate = has_access("action::schedule::auto_allocate")
        if st.button("🤖 Auto-Allocate", width='stretch', key="btn_auto_alloc", disabled=not can_auto_allocate):
            _run_auto_allocate(df)
            st.rerun()
    with col_refresh:
        if st.button("🔄", width='stretch', key="btn_sched_refresh", help="Refresh"):
            st.session_state.df = None
            st.cache_data.clear()
            st.rerun()

    # ── Optional: time block editor ───────────────────────────────────────────
    can_manage_time_blocks = has_access("action::schedule::time_blocks")
    with st.expander("🚫 Time Blocks", expanded=False):
        if not can_manage_time_blocks:
            st.info("You do not have permission to manage time blocks.")
        else:
            meta = getattr(df, "attrs", {}).get("meta", {})
            time_blocks = meta.get("time_blocks", [])
            from services.availability import deserialize_time_blocks, serialize_time_blocks
            time_blocks = deserialize_time_blocks(time_blocks)
            render_time_block_editor(
                time_blocks=time_blocks,
                assistants=assistants,
                on_add=lambda b: _add_time_block(df, b),
                on_remove=lambda i: _remove_time_block(df, i, time_blocks),
            )

    # ── Filter by date ──────────────────────────────────────────────────────────
    view_df = df.copy()

    # Strict date filter; do not include blank dates.
    if selected_date and ("DATE" in view_df.columns or "appointment_date" in view_df.columns):
        date_series = view_df["DATE"] if "DATE" in view_df.columns else pd.Series([""] * len(view_df), index=view_df.index)
        if "appointment_date" in view_df.columns:
            primary = date_series.fillna("").astype(str).str.strip()
            fallback = view_df["appointment_date"].fillna("").astype(str).str.strip()
            date_series = primary.where(primary.ne(""), fallback)
        date_mask, _ = _strict_date_mask(date_series, selected_date)
        view_df = view_df[date_mask].copy()

    # ── Filter by search query ──────────────────────────────────────────────────
    if search_q.strip():
        q = search_q.strip().lower()
        mask = (
            view_df.get("Patient Name", "").astype(str).str.lower().str.contains(q, na=False)
            | view_df.get("DR.", "").astype(str).str.lower().str.contains(q, na=False)
            | view_df.get("OP", "").astype(str).str.lower().str.contains(q, na=False)
            | view_df.get("Procedure", "").astype(str).str.lower().str.contains(q, na=False)
        )
        view_df = view_df[mask]

    # ── Add Appointment ────────────────────────────────────────────────────────
    can_add = has_access("action::schedule::add_appointment")
    if can_add:
        render_add_appointment_form(
            doctors=doctors,
            assistants=assistants,
            op_rooms=op_rooms,
            selected_date=selected_date,
            on_save=lambda row: _on_add_appointment(df, row),
        )
    else:
        st.caption("Add Appointment is restricted for your account.")

    st.markdown(f"**{len(view_df)} appointment(s) on {selected_date.strftime('%A, %B %d, %Y')}**")

    # ── Check if no appointments exist for the selected date ──────────────────
    if len(view_df) == 0:
        st.info("No appointments scheduled")
        return

    # ── Render view ────────────────────────────────────────────────────────────
    if view_mode == "🃏 Cards":
        _render_cards(view_df, df, doctors, assistants, op_rooms)
    else:
        _render_table(view_df, df, doctors, assistants, op_rooms)


# ── Private helpers ─────────────────────────────────────────────────────────────

def _render_cards(view_df, full_df, doctors, assistants, op_rooms) -> None:
    for idx, (_, row) in enumerate(view_df.iterrows()):
        row_dict = row.to_dict()
        row_id = str(row_dict.get("REMINDER_ROW_ID", "")).strip() or str(idx)

        # Check if in edit mode for this row
        if st.session_state.get(f"editing_row_{row_id}"):
            render_edit_row_form(
                row=row_dict,
                row_id=row_id,
                doctors=doctors,
                assistants=assistants,
                op_rooms=op_rooms,
                on_save=lambda rid, updates: _on_edit_row(full_df, rid, updates),
                on_cancel=lambda: _cancel_edit(row_id),
                idx=idx,
            )
        else:
            render_schedule_card(
                row=row_dict,
                on_status_change=lambda rid, ns: _on_status_change(full_df, rid, ns),
                on_delete=lambda rid: _on_delete_row(full_df, rid),
                idx=idx,
            )
        st.markdown("---")


def _render_table(view_df, full_df, doctors, assistants, op_rooms) -> None:
    render_schedule_table(
        df=view_df,
        on_save=lambda updated: _on_table_save(full_df, view_df, updated),
        doctors=doctors,
        assistants=assistants,
        op_rooms=op_rooms,
        key="full_sched_table",
    )


def _on_status_change(df, row_id: str, new_status: str) -> None:
    require_access("action::schedule::update_status", "updating appointment status")
    updated = update_status(df, row_id, new_status)
    st.session_state.df = updated
    maybe_save(updated, message=f"Status → {new_status}")
    st.rerun()


def _on_delete_row(df, row_id: str) -> None:
    require_access("action::schedule::delete_appointment", "deleting appointments")
    import pandas as pd
    mask = df["REMINDER_ROW_ID"].astype(str).str.strip() == row_id
    updated = df[~mask].reset_index(drop=True)
    updated.attrs = df.attrs.copy()
    st.session_state.df = updated
    maybe_save(updated, message="Row deleted")
    st.rerun()


def _on_add_appointment(df, row: dict) -> None:
    require_access("action::schedule::add_appointment", "adding appointments")
    import pandas as pd
    new_row_df = pd.DataFrame([row])
    updated = pd.concat([df, new_row_df], ignore_index=True)
    updated.attrs = df.attrs.copy()
    st.session_state.df = updated
    maybe_save(updated, message="Appointment added")
    st.rerun()


def _on_edit_row(df, row_id: str, updates: dict) -> None:
    require_access("action::schedule::edit_appointment", "editing appointments")
    mask = df["REMINDER_ROW_ID"].astype(str).str.strip() == row_id
    idxs = df.index[mask].tolist()
    if idxs:
        for col, val in updates.items():
            if col in df.columns:
                df.loc[idxs[0], col] = val
    st.session_state.df = df
    st.session_state[f"editing_row_{row_id}"] = False
    maybe_save(df, message="Appointment updated")
    st.rerun()


def _cancel_edit(row_id: str) -> None:
    st.session_state[f"editing_row_{row_id}"] = False
    st.rerun()


def _on_table_save(full_df, view_df, updated_view) -> None:
    """Merge edited table rows back into full_df."""
    require_access("action::schedule::edit_appointment", "editing appointments")
    for col in updated_view.columns:
        if col in full_df.columns and col in view_df.columns:
            full_df.loc[view_df.index, col] = updated_view[col].values
    st.session_state.df = full_df
    maybe_save(full_df, message="Table edited")
    st.rerun()


def _run_auto_allocate(df) -> None:
    require_access("action::schedule::auto_allocate", "auto-allocation")
    from services.allocation_engine import auto_allocate_all
    from data.attendance_repo import get_today_punch_map
    from services.utils import now_ist

    today_str = now_ist().date().isoformat()
    punch_map = get_today_punch_map(today_str)
    meta = getattr(df, "attrs", {}).get("meta", {})
    from services.availability import deserialize_time_blocks
    time_blocks = deserialize_time_blocks(meta.get("time_blocks", []))

    updated, changed = auto_allocate_all(
        df, only_fill_empty=True, punch_map=punch_map,
        time_blocks=time_blocks, today_str=today_str
    )
    updated.attrs = df.attrs.copy()
    st.session_state.df = updated
    maybe_save(updated, message=f"Auto-allocated {changed} slots")
    st.toast(f"Auto-allocated {changed} slot(s)", icon="🤖")


def _add_time_block(df, block: dict) -> None:
    require_access("action::schedule::time_blocks", "managing time blocks")
    from services.availability import deserialize_time_blocks, serialize_time_blocks
    meta = df.attrs.get("meta", {})
    time_blocks = deserialize_time_blocks(meta.get("time_blocks", []))
    time_blocks.append(block)
    meta["time_blocks"] = serialize_time_blocks(time_blocks)
    df.attrs["meta"] = meta
    st.session_state.df = df
    maybe_save(df, message="Time block added")
    st.rerun()


def _remove_time_block(df, idx: int, time_blocks: list) -> None:
    require_access("action::schedule::time_blocks", "managing time blocks")
    from services.availability import serialize_time_blocks
    if 0 <= idx < len(time_blocks):
        time_blocks.pop(idx)
    meta = df.attrs.get("meta", {})
    meta["time_blocks"] = serialize_time_blocks(time_blocks)
    df.attrs["meta"] = meta
    st.session_state.df = df
    maybe_save(df, message="Time block removed")
    st.rerun()

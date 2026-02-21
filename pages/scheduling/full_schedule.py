# pages/scheduling/full_schedule.py
"""Full Schedule view — card + table toggle, add/edit/delete, auto-allocate."""

from __future__ import annotations
import streamlit as st

from data.schedule_repo import load_schedule
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


def render() -> None:
    st.markdown("## 📅 Full Schedule")

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
        if st.button("🤖 Auto-Allocate", width='stretch', key="btn_auto_alloc"):
            _run_auto_allocate(df)
            st.rerun()
    with col_refresh:
        if st.button("🔄", width='stretch', key="btn_sched_refresh", help="Refresh"):
            st.session_state.df = None
            st.cache_data.clear()
            st.rerun()

    # ── Optional: time block editor ───────────────────────────────────────────
    with st.expander("🚫 Time Blocks", expanded=False):
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

    # ── Filter ─────────────────────────────────────────────────────────────────
    view_df = df.copy()
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
    render_add_appointment_form(
        doctors=doctors,
        assistants=assistants,
        op_rooms=op_rooms,
        on_save=lambda row: _on_add_appointment(df, row),
    )

    st.markdown(f"**{len(view_df)} appointment(s)**")

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
    updated = update_status(df, row_id, new_status)
    st.session_state.df = updated
    maybe_save(updated, message=f"Status → {new_status}")
    st.rerun()


def _on_delete_row(df, row_id: str) -> None:
    import pandas as pd
    mask = df["REMINDER_ROW_ID"].astype(str).str.strip() == row_id
    updated = df[~mask].reset_index(drop=True)
    updated.attrs = df.attrs.copy()
    st.session_state.df = updated
    maybe_save(updated, message="Row deleted")
    st.rerun()


def _on_add_appointment(df, row: dict) -> None:
    import pandas as pd
    new_row_df = pd.DataFrame([row])
    updated = pd.concat([df, new_row_df], ignore_index=True)
    updated.attrs = df.attrs.copy()
    st.session_state.df = updated
    maybe_save(updated, message="Appointment added")
    st.rerun()


def _on_edit_row(df, row_id: str, updates: dict) -> None:
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
    for col in updated_view.columns:
        if col in full_df.columns and col in view_df.columns:
            full_df.loc[view_df.index, col] = updated_view[col].values
    st.session_state.df = full_df
    maybe_save(full_df, message="Table edited")
    st.rerun()


def _run_auto_allocate(df) -> None:
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
    from services.availability import serialize_time_blocks
    if 0 <= idx < len(time_blocks):
        time_blocks.pop(idx)
    meta = df.attrs.get("meta", {})
    meta["time_blocks"] = serialize_time_blocks(time_blocks)
    df.attrs["meta"] = meta
    st.session_state.df = df
    maybe_save(df, message="Time block removed")
    st.rerun()

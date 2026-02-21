# pages/doctors/per_doctor_schedule.py
"""Per-doctor schedule view — filtered to a single doctor."""

from __future__ import annotations
import streamlit as st

from services.schedule_ops import (
    ensure_schedule_columns, ensure_row_ids, add_computed_columns,
    filter_by_doctor, update_status,
)
from services.profiles_cache import get_profiles_cache
from state.save_manager import maybe_save
from components.schedule_card import render_schedule_card


def render() -> None:
    st.markdown("## 🩺 Per-Doctor Schedule")

    df = st.session_state.get("df")
    if df is None:
        from data.schedule_repo import load_schedule
        df = load_schedule()
        df = ensure_schedule_columns(df)
        df = ensure_row_ids(df)
        df = add_computed_columns(df)
        st.session_state.df = df
    else:
        df = ensure_schedule_columns(df)
        df = ensure_row_ids(df)
        df = add_computed_columns(df)

    cache = get_profiles_cache(st.session_state.get("profiles_cache_bust", 0))
    doctors = sorted(cache.get("doctors_list") or [])

    # Also grab doctors from the schedule itself
    if "DR." in df.columns:
        sched_doctors = df["DR."].dropna().astype(str).str.strip().unique().tolist()
        doctors = sorted(set(doctors + [d for d in sched_doctors if d]))

    if not doctors:
        st.info("No doctors found. Add doctors in Manage Doctors → Manage Profiles.")
        return

    col_dr, col_refresh = st.columns([4, 1])
    with col_dr:
        selected_dr = st.selectbox("Select Doctor", doctors, key="per_dr_select")
    with col_refresh:
        if st.button("🔄", width='stretch', key="per_dr_refresh"):
            st.session_state.df = None
            st.cache_data.clear()
            st.rerun()

    filtered = filter_by_doctor(df, selected_dr)

    if filtered.empty:
        st.info(f"No appointments found for {selected_dr}.")
        return

    # ── Doctor-level metrics ───────────────────────────────────────────────────
    total = len(filtered)
    ongoing = int(filtered.get("Is_Ongoing", 0).sum()) if "Is_Ongoing" in filtered.columns else 0
    c1, c2, c3 = st.columns(3)
    c1.metric("📅 Total", total)
    c2.metric("🔴 Ongoing", ongoing)
    c3.metric("⏳ Pending", total - ongoing)

    st.markdown("---")
    st.markdown(f"**Appointments for {selected_dr}**")

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

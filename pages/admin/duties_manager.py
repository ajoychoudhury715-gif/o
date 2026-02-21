# pages/admin/duties_manager.py
"""Duty master, assignments, and run history management."""

from __future__ import annotations
import streamlit as st

from data.duty_repo import (
    load_duties_master, save_duties_master,
    load_duty_assignments, save_duty_assignments,
    load_duty_runs,
)
from services.profiles_cache import get_profiles_cache
from components.duty_widgets import (
    render_duty_master_editor,
    render_duty_assignments_editor,
    render_duty_runs_table,
)


def render() -> None:
    st.markdown("## 📋 Duties Manager")

    tab_master, tab_assignments, tab_runs = st.tabs(
        ["📖 Duty Definitions", "🔗 Assignments", "🕑 Run History"]
    )

    cache = get_profiles_cache(st.session_state.get("profiles_cache_bust", 0))
    assistants = sorted(cache.get("assistants_list") or [])

    with tab_master:
        _render_master(assistants)

    with tab_assignments:
        _render_assignments(assistants)

    with tab_runs:
        _render_runs()


def _render_master(assistants: list[str]) -> None:
    st.markdown("Define duties and their frequency/duration.")
    duties_df = load_duties_master()

    col_refresh = st.columns([4, 1])[1]
    with col_refresh:
        if st.button("🔄", use_container_width=True, key="duties_refresh"):
            st.rerun()

    render_duty_master_editor(
        duties_df=duties_df,
        on_save=lambda df: _save_master(df),
    )


def _render_assignments(assistants: list[str]) -> None:
    st.markdown("Assign duties to assistants.")

    duties_df = load_duties_master()
    duty_names = []
    if not duties_df.empty and "name" in duties_df.columns:
        duty_names = duties_df["name"].dropna().astype(str).str.strip().unique().tolist()

    assignments_df = load_duty_assignments()
    render_duty_assignments_editor(
        assignments_df=assignments_df,
        assistants=assistants,
        duty_names=duty_names,
        on_save=lambda df: _save_assignments(df),
    )


def _render_runs() -> None:
    st.markdown("History of duty runs (started/completed).")
    runs_df = load_duty_runs()

    col_refresh = st.columns([4, 1])[1]
    with col_refresh:
        if st.button("🔄", use_container_width=True, key="runs_refresh"):
            st.rerun()

    render_duty_runs_table(runs_df)

    # Clear completed runs
    st.markdown("---")
    if not runs_df.empty:
        if st.button("🗑️ Clear All Run History", use_container_width=True, key="btn_clear_runs"):
            import pandas as pd
            empty = pd.DataFrame(columns=runs_df.columns)
            save_duty_runs = _get_save_runs()
            save_duty_runs(empty)
            st.toast("Run history cleared.", icon="🗑️")
            st.rerun()


def _save_master(df) -> None:
    save_duties_master(df)
    st.toast("Duty definitions saved!", icon="💾")
    st.rerun()


def _save_assignments(df) -> None:
    save_duty_assignments(df)
    st.toast("Assignments saved!", icon="💾")
    st.rerun()


def _get_save_runs():
    """Import save_duty_runs lazily to avoid circular import issues."""
    from data.duty_repo import save_duty_runs as _save
    return _save

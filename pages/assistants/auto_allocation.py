# pages/assistants/auto_allocation.py
"""Auto-allocation trigger and results page."""

from __future__ import annotations
import streamlit as st
import pandas as pd

from services.schedule_ops import ensure_schedule_columns, ensure_row_ids, add_computed_columns
from services.allocation_engine import auto_allocate_all
from services.profiles_cache import get_profiles_cache
from services.availability import deserialize_time_blocks
from data.attendance_repo import get_today_punch_map
from services.utils import now_ist
from state.save_manager import maybe_save


def render() -> None:
    st.markdown("## 🤖 Auto-Allocation")

    df = st.session_state.get("df")
    if df is None:
        from data.schedule_repo import load_schedule
        df = load_schedule()
        df = ensure_schedule_columns(df)
        df = ensure_row_ids(df)
        df = add_computed_columns(df)
        st.session_state.df = df

    df = ensure_schedule_columns(df)
    df = ensure_row_ids(df)

    cache = get_profiles_cache(st.session_state.get("profiles_cache_bust", 0))
    assistants = sorted(cache.get("assistants_list") or [])

    st.markdown("""
    Auto-allocation assigns available assistants to appointment slots based on:
    - **Department rules** (in `allocation_rules.json`)
    - **Real-time availability** (no schedule conflicts, punch-in status)
    - **Time blocks** (custom blocked periods)
    - **Load balancing** (if enabled in rules)
    """)

    # ── Options ────────────────────────────────────────────────────────────────
    st.markdown("#### ⚙️ Options")
    only_empty = st.checkbox(
        "Only fill empty slots (don't overwrite existing assignments)",
        value=True,
        key="alloc_only_empty",
    )

    if not assistants:
        st.warning("⚠️ No assistants found in profiles. Add assistants first.")

    # ── Run button ─────────────────────────────────────────────────────────────
    col_run, col_preview = st.columns(2)
    with col_run:
        run_alloc = st.button(
            "🚀 Run Auto-Allocation", use_container_width=True,
            key="btn_run_alloc", type="primary",
        )
    with col_preview:
        preview_only = st.button(
            "👁️ Preview (don't save)", use_container_width=True,
            key="btn_preview_alloc",
        )

    if run_alloc or preview_only:
        today_str = now_ist().date().isoformat()
        punch_map = get_today_punch_map(today_str)
        meta = getattr(df, "attrs", {}).get("meta", {})
        time_blocks = deserialize_time_blocks(meta.get("time_blocks", []))

        with st.spinner("Running allocation…"):
            updated, changed = auto_allocate_all(
                df,
                only_fill_empty=only_empty,
                punch_map=punch_map,
                time_blocks=time_blocks,
                today_str=today_str,
            )

        if changed == 0:
            st.success("✅ No changes needed — all slots already filled.")
        else:
            st.success(f"✅ Allocated **{changed}** slot(s) across appointments.")

            # Show diff
            _show_diff(df, updated)

            if run_alloc:
                updated.attrs = df.attrs.copy()
                st.session_state.df = updated
                maybe_save(updated, message=f"Auto-allocated {changed} slots")
                st.toast(f"Saved: {changed} allocation(s)", icon="🤖")
                st.rerun()

    # ── Current allocation summary ─────────────────────────────────────────────
    st.markdown("---")
    st.markdown("#### 📊 Current Allocation Summary")
    _show_current_summary(df)


def _show_diff(before: pd.DataFrame, after: pd.DataFrame) -> None:
    """Show which rows changed."""
    changes = []
    for i in range(min(len(before), len(after))):
        for role in ["FIRST", "SECOND", "Third"]:
            if role not in before.columns or role not in after.columns:
                continue
            old_val = str(before.iloc[i].get(role, "") or "").strip()
            new_val = str(after.iloc[i].get(role, "") or "").strip()
            if old_val != new_val and new_val:
                patient = str(after.iloc[i].get("Patient Name", f"Row {i}") or "").strip()
                changes.append({
                    "Patient": patient,
                    "Role": role,
                    "Before": old_val or "(empty)",
                    "After": new_val,
                })

    if changes:
        st.markdown("**Changes:**")
        st.dataframe(pd.DataFrame(changes), use_container_width=True, hide_index=True)


def _show_current_summary(df: pd.DataFrame) -> None:
    if df is None or df.empty:
        st.info("No appointments to summarize.")
        return

    from services.schedule_ops import get_assistant_loads
    loads = get_assistant_loads(df)

    if not loads:
        st.info("No assistant assignments found.")
        return

    summary_df = pd.DataFrame(
        [{"Assistant": k, "Appointments": v} for k, v in sorted(loads.items(), key=lambda x: -x[1])]
    )
    st.dataframe(summary_df, use_container_width=True, hide_index=True)

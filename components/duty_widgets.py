# components/duty_widgets.py
"""Duty timer and assignment widgets (standalone, page-level)."""

from __future__ import annotations
from typing import Callable
import streamlit as st


def render_duty_master_editor(
    duties_df,
    on_save: Callable,
) -> None:
    """Render an editable table of duty master definitions."""
    import pandas as pd

    st.markdown("#### 📋 Duty Definitions")
    if duties_df is None or duties_df.empty:
        st.info("No duties defined yet.")
        duties_df = pd.DataFrame(columns=["duty_id", "name", "frequency", "duration_minutes", "description"])

    # Ensure all string columns are proper string type for Streamlit
    for col in ["duty_id", "name", "frequency", "description"]:
        if col in duties_df.columns:
            duties_df[col] = duties_df[col].fillna("").astype(str)

    edited = st.data_editor(
        duties_df,
        column_config={
            "duty_id": st.column_config.TextColumn("ID", width="small"),
            "name": st.column_config.TextColumn("Duty Name", width="medium"),
            "frequency": st.column_config.SelectboxColumn(
                "Frequency", options=["WEEKLY", "MONTHLY"], width="small"
            ),
            "duration_minutes": st.column_config.NumberColumn(
                "Duration (min)", min_value=1, max_value=480, width="small"
            ),
            "description": st.column_config.TextColumn("Description", width="large"),
        },
        width='stretch',
        num_rows="dynamic",
        key="duty_master_editor",
    )

    if st.button("💾 Save Duties", width='stretch', key="btn_save_duties"):
        import uuid
        # Fill missing duty_ids
        for i in range(len(edited)):
            if not str(edited.iloc[i].get("duty_id", "") or "").strip():
                edited.iloc[i, edited.columns.get_loc("duty_id")] = str(uuid.uuid4())[:8]
        on_save(edited)
        st.toast("Duties saved!", icon="💾")


def render_duty_assignments_editor(
    assignments_df,
    assistants: list[str],
    duty_names: list[str],
    on_save: Callable,
) -> None:
    """Render an editable table of duty assignments (assistant ↔ duty)."""
    import pandas as pd
    import uuid

    st.markdown("#### 🔗 Duty Assignments")
    if assignments_df is None or assignments_df.empty:
        st.info("No assignments yet.")
        assignments_df = pd.DataFrame(
            columns=["assignment_id", "assistant", "duty_id", "duty_name", "active"]
        )

    # Ensure proper types for Streamlit
    for col in ["assignment_id", "assistant", "duty_id", "duty_name"]:
        if col in assignments_df.columns:
            assignments_df[col] = assignments_df[col].fillna("").astype(str)
    if "active" in assignments_df.columns:
        assignments_df["active"] = assignments_df["active"].astype(bool)

    edited = st.data_editor(
        assignments_df,
        column_config={
            "assignment_id": st.column_config.TextColumn("ID", width="small"),
            "assistant": st.column_config.SelectboxColumn(
                "Assistant", options=[""] + sorted(assistants), width="medium"
            ),
            "duty_id": st.column_config.TextColumn("Duty ID", width="small"),
            "duty_name": st.column_config.SelectboxColumn(
                "Duty Name", options=[""] + sorted(duty_names), width="medium"
            ),
            "active": st.column_config.CheckboxColumn("Active", width="small"),
        },
        width='stretch',
        num_rows="dynamic",
        key="duty_assignments_editor",
    )

    if st.button("💾 Save Assignments", width='stretch', key="btn_save_assignments"):
        for i in range(len(edited)):
            if not str(edited.iloc[i].get("assignment_id", "") or "").strip():
                edited.iloc[i, edited.columns.get_loc("assignment_id")] = str(uuid.uuid4())[:8]
        on_save(edited)
        st.toast("Assignments saved!", icon="💾")


def render_duty_runs_table(runs_df) -> None:
    """Render a read-only table of recent duty run history."""
    import pandas as pd
    st.markdown("#### 🕑 Duty Run History")
    if runs_df is None or runs_df.empty:
        st.info("No duty runs recorded.")
        return

    display_cols = [c for c in ["run_id", "assistant", "duty_id", "duty_name",
                                 "started_at", "due_at", "completed_at", "status"]
                    if c in runs_df.columns]
    st.dataframe(
        runs_df[display_cols].sort_values(
            by="started_at" if "started_at" in display_cols else display_cols[0],
            ascending=False,
        ).head(50),
        width='stretch',
        hide_index=True,
    )


def render_duty_timer_card(active_run: dict, on_done: Callable) -> None:
    """Render a countdown timer card for an active duty run."""
    from services.duty_service import format_remaining_time
    if not active_run:
        return
    remaining = format_remaining_time(active_run.get("due_at"))
    duty_name = active_run.get("duty_name") or active_run.get("duty_id") or "Duty"
    assistant = str(active_run.get("assistant", ""))
    st.markdown(
        f"""<div class="duty-timer-card">
          <div class="duty-timer-value">{remaining}</div>
          <div style="font-size:13px;color:#64748b;margin-top:4px;">{duty_name}</div>
          <div style="font-size:12px;color:#94a3b8;">{assistant}</div>
        </div>""",
        unsafe_allow_html=True,
    )
    if st.button("✅ Mark Done", width='stretch', key=f"duty_done_{active_run.get('id','')}"):
        on_done(str(active_run.get("id", "")))

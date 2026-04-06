# components/duty_widgets.py
"""Duty timer and assignment widgets (standalone, page-level)."""

from __future__ import annotations
from typing import Callable
import streamlit as st

MASTER_EDIT_COLUMNS = ["id", "name", "frequency", "est_minutes", "description", "active"]
ASSIGNMENT_EDIT_COLUMNS = ["id", "assistant", "duty_id", "duty_name", "op", "est_minutes", "active"]


def _is_blank(value) -> bool:
    if value is None:
        return True
    try:
        import pandas as pd
        if pd.isna(value):
            return True
    except Exception:
        pass
    return str(value).strip() == ""


def _normalize_text(value) -> str:
    return "" if _is_blank(value) else str(value).strip()


def _normalize_minutes(value, default: int = 30) -> int:
    try:
        return max(1, int(float(str(value))))
    except Exception:
        return default


def _normalize_active(value) -> bool:
    if _is_blank(value):
        return True
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "y", "on"}


def _prepare_duty_master_editor_df(duties_df):
    import pandas as pd

    if duties_df is None or duties_df.empty:
        return pd.DataFrame(columns=MASTER_EDIT_COLUMNS)

    edited = duties_df.copy()
    for col in MASTER_EDIT_COLUMNS:
        if col not in edited.columns:
            edited[col] = True if col == "active" else (30 if col == "est_minutes" else "")

    edited = edited[MASTER_EDIT_COLUMNS].copy()
    for col in ["id", "name", "frequency", "description"]:
        edited[col] = edited[col].apply(_normalize_text)
    edited["frequency"] = edited["frequency"].str.upper()
    edited["est_minutes"] = edited["est_minutes"].apply(_normalize_minutes)
    edited["active"] = edited["active"].apply(_normalize_active)
    return edited


def _prepare_assignment_editor_df(assignments_df, duties_df):
    import pandas as pd

    duty_name_map = {}
    if duties_df is not None and not duties_df.empty:
        duty_name_map = {
            _normalize_text(row.get("id")): _normalize_text(row.get("name"))
            for _, row in duties_df.iterrows()
            if _normalize_text(row.get("id"))
        }

    if assignments_df is None or assignments_df.empty:
        edited = pd.DataFrame(columns=ASSIGNMENT_EDIT_COLUMNS)
    else:
        edited = assignments_df.copy()
        for col in ["id", "assistant", "duty_id", "op", "est_minutes", "active"]:
            if col not in edited.columns:
                edited[col] = True if col == "active" else (30 if col == "est_minutes" else "")
        if "duty_name" not in edited.columns:
            edited["duty_name"] = ""
        edited = edited[ASSIGNMENT_EDIT_COLUMNS].copy()

    for col in ["id", "assistant", "duty_id", "duty_name", "op"]:
        edited[col] = edited[col].apply(_normalize_text)
    edited["assistant"] = edited["assistant"].str.upper()
    edited["duty_name"] = edited.apply(
        lambda row: _normalize_text(row.get("duty_name")) or duty_name_map.get(_normalize_text(row.get("duty_id")), ""),
        axis=1,
    )
    edited["est_minutes"] = edited["est_minutes"].apply(_normalize_minutes)
    edited["active"] = edited["active"].apply(_normalize_active)
    return edited


def _drop_empty_rows(df, content_columns: list[str]):
    if df is None or df.empty:
        return df
    mask = df.apply(
        lambda row: any(not _is_blank(row.get(col)) for col in content_columns),
        axis=1,
    )
    return df[mask].reset_index(drop=True)


def render_duty_master_editor(
    duties_df,
    on_save: Callable,
) -> None:
    """Render an editable table of duty master definitions."""
    st.markdown("#### 📋 Duty Definitions")
    if duties_df is None or duties_df.empty:
        st.info("No duties defined yet.")
    duties_df = _prepare_duty_master_editor_df(duties_df)

    edited = st.data_editor(
        duties_df,
        column_config={
            "id": st.column_config.TextColumn("ID", width="small"),
            "name": st.column_config.TextColumn("Duty Name", width="medium"),
            "frequency": st.column_config.SelectboxColumn(
                "Frequency", options=["WEEKLY", "MONTHLY"], width="small"
            ),
            "est_minutes": st.column_config.NumberColumn(
                "Estimated (min)", min_value=1, max_value=480, width="small"
            ),
            "description": st.column_config.TextColumn("Description", width="large"),
            "active": st.column_config.CheckboxColumn("Active", width="small"),
        },
        width='stretch',
        num_rows="dynamic",
        key="duty_master_editor",
    )

    if st.button("💾 Save Duties", width='stretch', key="btn_save_duties"):
        import uuid
        edited = _drop_empty_rows(edited.copy(), ["id", "name", "frequency", "description"])
        for col in ["id", "name", "frequency", "description"]:
            edited[col] = edited[col].apply(_normalize_text)
        edited["frequency"] = edited["frequency"].str.upper()
        edited["est_minutes"] = edited["est_minutes"].apply(_normalize_minutes)
        edited["active"] = edited["active"].apply(_normalize_active)

        # Fill missing ids only for meaningful rows
        for i in range(len(edited)):
            if not _normalize_text(edited.iloc[i].get("id", "")):
                edited.iloc[i, edited.columns.get_loc("id")] = str(uuid.uuid4())[:8]
        on_save(edited[MASTER_EDIT_COLUMNS])
        st.toast("Duties saved!", icon="💾")


def render_duty_assignments_editor(
    assignments_df,
    assistants: list[str],
    duties_df,
    on_save: Callable,
) -> None:
    """Render an editable table of duty assignments (assistant ↔ duty)."""
    import uuid

    st.markdown("#### 🔗 Duty Assignments")
    if assignments_df is None or assignments_df.empty:
        st.info("No assignments yet.")
    assignments_df = _prepare_assignment_editor_df(assignments_df, duties_df)

    duty_ids = []
    duty_name_map = {}
    if duties_df is not None and not duties_df.empty:
        duty_name_map = {
            _normalize_text(row.get("id")): _normalize_text(row.get("name"))
            for _, row in duties_df.iterrows()
            if _normalize_text(row.get("id"))
        }
        duty_ids = sorted(duty_name_map.keys())

    edited = st.data_editor(
        assignments_df,
        column_config={
            "id": st.column_config.TextColumn("ID", width="small"),
            "assistant": st.column_config.SelectboxColumn(
                "Assistant", options=[""] + sorted({_normalize_text(name).upper() for name in assistants if _normalize_text(name)}), width="medium"
            ),
            "duty_id": st.column_config.SelectboxColumn("Duty ID", options=[""] + duty_ids, width="small"),
            "duty_name": st.column_config.TextColumn("Duty Name", width="medium"),
            "op": st.column_config.TextColumn("OP", width="small"),
            "est_minutes": st.column_config.NumberColumn("Estimated (min)", min_value=1, max_value=480, width="small"),
            "active": st.column_config.CheckboxColumn("Active", width="small"),
        },
        width='stretch',
        num_rows="dynamic",
        key="duty_assignments_editor",
        disabled=["duty_name"],
    )

    if st.button("💾 Save Assignments", width='stretch', key="btn_save_assignments"):
        edited = _drop_empty_rows(edited.copy(), ["id", "assistant", "duty_id", "duty_name", "op"])
        for col in ["id", "assistant", "duty_id", "duty_name", "op"]:
            edited[col] = edited[col].apply(_normalize_text)
        edited["assistant"] = edited["assistant"].str.upper()
        edited["duty_id"] = edited.apply(
            lambda row: _normalize_text(row.get("duty_id")) or next(
                (
                    duty_id
                    for duty_id, duty_name in duty_name_map.items()
                    if duty_name == _normalize_text(row.get("duty_name"))
                ),
                "",
            ),
            axis=1,
        )
        edited["duty_name"] = edited["duty_id"].map(duty_name_map).fillna(edited["duty_name"])
        edited["est_minutes"] = edited["est_minutes"].apply(_normalize_minutes)
        edited["active"] = edited["active"].apply(_normalize_active)

        for i in range(len(edited)):
            if not _normalize_text(edited.iloc[i].get("id", "")):
                edited.iloc[i, edited.columns.get_loc("id")] = str(uuid.uuid4())[:8]
        on_save(edited[[c for c in ASSIGNMENT_EDIT_COLUMNS if c != "duty_name"]])
        st.toast("Assignments saved!", icon="💾")


def render_duty_runs_table(runs_df) -> None:
    """Render a read-only table of recent duty run history."""
    st.markdown("#### 🕑 Duty Run History")
    if runs_df is None or runs_df.empty:
        st.info("No duty runs recorded.")
        return

    display_cols = [
        c
        for c in ["id", "assistant", "duty_id", "duty_name", "op", "est_minutes", "started_at", "due_at", "ended_at", "status"]
        if c in runs_df.columns
    ]
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

# components/schedule_table.py
"""Editable table/dataframe view for schedule entries."""

from __future__ import annotations
from typing import Callable
import pandas as pd
import streamlit as st

from config.constants import STATUS_OPTIONS, SCHEDULE_COLUMNS
from services.utils import is_blank, coerce_to_time_obj, time_to_12h


# Columns to show in the table view (subset of all columns for readability)
TABLE_DISPLAY_COLS = [
    "Patient Name",
    "In Time",
    "Out Time",
    "DR.",
    "OP",
    "Procedure",
    "FIRST",
    "SECOND",
    "Third",
    "CASE PAPER",
    "STATUS",
]


def _safe_str_col(df: pd.DataFrame, col: str) -> pd.Series:
    if col in df.columns:
        return df[col].fillna("").astype(str)
    return pd.Series([""] * len(df), index=df.index)


def _fmt_time_12h(val) -> str:
    """Format time string or time object to 12-hour AM/PM format."""
    t = coerce_to_time_obj(val)
    if t is None:
        return str(val or "")
    return time_to_12h(t)


def render_schedule_table(
    df: pd.DataFrame,
    on_save: Callable[[pd.DataFrame], None],
    doctors: list[str] | None = None,
    assistants: list[str] | None = None,
    op_rooms: list[str] | None = None,
    key: str = "sched_table",
) -> None:
    """Render an editable schedule table using st.data_editor.

    Args:
        df: The schedule DataFrame.
        on_save: Callback called with the full updated df when edits are applied.
        doctors: List of doctor names for selectbox column.
        assistants: List of assistant names for selectbox columns.
        op_rooms: List of OP room names for selectbox column.
        key: Unique widget key prefix.
    """
    if df is None or df.empty:
        st.info("No appointments to display.")
        return

    # Build display subset
    display_cols = [c for c in TABLE_DISPLAY_COLS if c in df.columns]
    if not display_cols:
        st.warning("No displayable columns found in schedule.")
        return

    display_df = df[display_cols].copy()

    # Normalise time columns to string and format as 12-hour
    for col in ("In Time", "Out Time"):
        if col in display_df.columns:
            display_df[col] = display_df[col].fillna("").astype(str).apply(_fmt_time_12h)

    # Build column_config
    doctors_opts = sorted(doctors or [])
    assistants_opts = sorted(assistants or [])
    op_opts = sorted(op_rooms or [])

    col_config: dict = {}

    if "Patient Name" in display_cols:
        col_config["Patient Name"] = st.column_config.TextColumn(
            "Patient", help="Patient full name", width="medium"
        )
    if "In Time" in display_cols:
        col_config["In Time"] = st.column_config.TextColumn("In", width="small")
    if "Out Time" in display_cols:
        col_config["Out Time"] = st.column_config.TextColumn("Out", width="small")
    if "DR." in display_cols:
        col_config["DR."] = st.column_config.SelectboxColumn(
            "Doctor",
            options=[""] + doctors_opts,
            width="medium",
        )
    if "OP" in display_cols:
        col_config["OP"] = st.column_config.SelectboxColumn(
            "OP Room",
            options=[""] + op_opts,
            width="small",
        )
    if "Procedure" in display_cols:
        col_config["Procedure"] = st.column_config.TextColumn("Procedure", width="medium")
    if "FIRST" in display_cols:
        col_config["FIRST"] = st.column_config.SelectboxColumn(
            "1st",
            options=[""] + assistants_opts,
            width="small",
        )
    if "SECOND" in display_cols:
        col_config["SECOND"] = st.column_config.SelectboxColumn(
            "2nd",
            options=[""] + assistants_opts,
            width="small",
        )
    if "Third" in display_cols:
        col_config["Third"] = st.column_config.SelectboxColumn(
            "3rd",
            options=[""] + assistants_opts,
            width="small",
        )
    if "CASE PAPER" in display_cols:
        col_config["CASE PAPER"] = st.column_config.TextColumn("Case #", width="small")
    if "STATUS" in display_cols:
        col_config["STATUS"] = st.column_config.SelectboxColumn(
            "Status",
            options=STATUS_OPTIONS,
            width="medium",
        )

    edited = st.data_editor(
        display_df,
        column_config=col_config,
        use_container_width=True,
        hide_index=False,
        num_rows="fixed",
        key=f"{key}_editor",
    )

    if st.button("💾 Apply Table Changes", key=f"{key}_apply", use_container_width=True):
        # Merge edits back into the full df
        updated = df.copy()
        for col in display_cols:
            if col in edited.columns and col in updated.columns:
                updated[col] = edited[col].values
        on_save(updated)
        st.toast("Table changes applied.", icon="💾")


def render_edit_row_form(
    row: dict,
    row_id: str,
    doctors: list[str],
    assistants: list[str],
    op_rooms: list[str],
    on_save: Callable[[str, dict], None],
    on_cancel: Callable[[], None],
    idx: int = 0,
) -> None:
    """Render an inline edit form for a single schedule row (shown in card view)."""
    with st.form(key=f"edit_row_form_{row_id}_{idx}", clear_on_submit=False):
        st.markdown("#### ✏️ Edit Appointment")
        c1, c2 = st.columns(2)
        with c1:
            patient_name = st.text_input(
                "Patient Name *",
                value=str(row.get("Patient Name", "") or ""),
            )
            doctor = st.selectbox(
                "Doctor *",
                [""] + sorted(doctors),
                index=_idx_of(str(row.get("DR.", "") or ""), [""] + sorted(doctors)),
            )
            op = st.selectbox(
                "OP Room",
                [""] + sorted(op_rooms),
                index=_idx_of(str(row.get("OP", "") or ""), [""] + sorted(op_rooms)),
            )
        with c2:
            in_time_val = _parse_time_str(str(row.get("In Time", "") or ""))
            out_time_val = _parse_time_str(str(row.get("Out Time", "") or ""))

            # Digital clock time picker for In Time
            st.markdown("**In Time*** 🕐")
            t_col1, t_col2, t_col3 = st.columns([2, 1, 2])
            with t_col1:
                in_hour = st.number_input("Hour", min_value=0, max_value=23, value=in_time_val.hour, step=1, key=f"in_hour_edit_{row_id}")
            with t_col2:
                st.markdown("<div style='text-align:center;padding-top:32px;font-size:20px;font-weight:bold;'>:</div>", unsafe_allow_html=True)
            with t_col3:
                in_minute = st.number_input("Minute", min_value=0, max_value=59, value=in_time_val.minute, step=5, key=f"in_minute_edit_{row_id}")

            import datetime
            in_time = datetime.time(int(in_hour), int(in_minute))
            st.markdown(f"<div style='text-align:center;font-size:18px;font-weight:bold;color:#3b82f6;'>{in_time.strftime('%H:%M')}</div>", unsafe_allow_html=True)

            # Calculate duration from in_time and out_time
            in_mins = in_time.hour * 60 + in_time.minute
            out_mins = out_time_val.hour * 60 + out_time_val.minute
            initial_duration = (out_mins - in_mins) if out_mins >= in_mins else ((24 * 60) + out_mins - in_mins)

            duration_mins = st.number_input("Duration (minutes)", min_value=1, max_value=480, value=max(1, initial_duration))

            # Calculate out_time based on in_time + duration
            calculated_out = (in_mins + duration_mins) % (24 * 60)
            out_hour = calculated_out // 60
            out_minute = calculated_out % 60
            out_time = datetime.time(out_hour, out_minute)

            procedure = st.text_input(
                "Procedure",
                value=str(row.get("Procedure", "") or ""),
            )

        c3, c4, c5 = st.columns(3)
        asst_opts = [""] + sorted(assistants)
        with c3:
            first = st.selectbox(
                "First Assistant",
                asst_opts,
                index=_idx_of(str(row.get("FIRST", "") or ""), asst_opts),
                key=f"edit_first_{row_id}",
            )
        with c4:
            second = st.selectbox(
                "Second Assistant",
                asst_opts,
                index=_idx_of(str(row.get("SECOND", "") or ""), asst_opts),
                key=f"edit_second_{row_id}",
            )
        with c5:
            third = st.selectbox(
                "Third Assistant",
                asst_opts,
                index=_idx_of(str(row.get("Third", "") or ""), asst_opts),
                key=f"edit_third_{row_id}",
            )

        case_paper = st.text_input(
            "Case Paper #",
            value=str(row.get("CASE PAPER", "") or ""),
        )
        status = st.selectbox(
            "Status",
            STATUS_OPTIONS,
            index=_idx_of(
                str(row.get("STATUS", "PENDING") or "PENDING").upper(),
                STATUS_OPTIONS,
            ),
        )

        col_save, col_cancel = st.columns(2)
        with col_save:
            submitted = st.form_submit_button("💾 Save Changes", use_container_width=True)
        with col_cancel:
            cancelled = st.form_submit_button(
                "✕ Cancel", use_container_width=True, type="secondary"
            )

        if submitted:
            if not patient_name or not doctor:
                st.error("Patient Name and Doctor are required.")
            else:
                updates = {
                    "Patient Name": patient_name,
                    "In Time": in_time.strftime("%H:%M") if in_time else "",
                    "Out Time": out_time.strftime("%H:%M") if out_time else "",
                    "DR.": doctor,
                    "OP": op,
                    "Procedure": procedure,
                    "FIRST": first,
                    "SECOND": second,
                    "Third": third,
                    "CASE PAPER": case_paper,
                    "STATUS": status,
                }
                on_save(row_id, updates)

        if cancelled:
            on_cancel()


# ── helpers ────────────────────────────────────────────────────────────────────

def _idx_of(value: str, options: list[str]) -> int:
    """Return the index of value in options (case-insensitive), defaulting to 0."""
    val_up = str(value).strip().upper()
    for i, opt in enumerate(options):
        if str(opt).strip().upper() == val_up:
            return i
    return 0


def _parse_time_str(val: str):
    """Try to parse 'HH:MM' into a datetime.time, return None on failure."""
    import datetime
    val = str(val).strip()
    for fmt in ("%H:%M", "%H:%M:%S"):
        try:
            return datetime.datetime.strptime(val, fmt).time()
        except (ValueError, TypeError):
            pass
    return datetime.time(9, 0)  # sensible default

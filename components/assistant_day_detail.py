"""Reusable assistant daily detail panel."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from data.duty_repo import get_active_duty_assignments, load_duty_runs
from services.schedule_ops import filter_rows_for_assistant, filter_schedule_for_date, normalize_status
from services.utils import coerce_to_time_obj, now_ist, parse_iso_ts, time_to_12h

CLINIC_START_MIN = 9 * 60
CLINIC_END_MIN = 19 * 60
CLINIC_SHIFT_MINUTES = CLINIC_END_MIN - CLINIC_START_MIN


def _time_sort_key(value) -> int:
    time_obj = coerce_to_time_obj(value)
    if time_obj is None:
        return 10**9
    return time_obj.hour * 60 + time_obj.minute


def _format_time(value) -> str:
    time_obj = coerce_to_time_obj(value)
    if time_obj is None:
        return str(value or "")
    return time_to_12h(time_obj)


def _format_iso_time(value) -> str:
    dt = parse_iso_ts(value)
    if not dt:
        return ""
    return time_to_12h(dt.astimezone(now_ist().tzinfo).time().replace(second=0, microsecond=0))


def _assistant_roles(row: pd.Series, assistant_name: str) -> str:
    assistant_upper = str(assistant_name or "").strip().upper()
    roles = []
    for col, label in [("FIRST", "1st"), ("SECOND", "2nd"), ("Third", "3rd")]:
        if str(row.get(col, "") or "").strip().upper() == assistant_upper:
            roles.append(label)
    return " / ".join(roles) if roles else "—"


def _get_assistant_day_schedule_df(df_schedule: pd.DataFrame, assistant_name: str, today_str: str) -> pd.DataFrame:
    return filter_rows_for_assistant(filter_schedule_for_date(df_schedule, today_str), assistant_name)


def _duration_minutes(start_value, end_value) -> int:
    start_time = coerce_to_time_obj(start_value)
    end_time = coerce_to_time_obj(end_value)
    if start_time is None or end_time is None:
        return 0

    start_min = start_time.hour * 60 + start_time.minute
    end_min = end_time.hour * 60 + end_time.minute
    if end_min < start_min:
        end_min += 24 * 60
    return max(0, end_min - start_min)


def _format_minutes_label(total_minutes: int) -> str:
    minutes = max(0, int(total_minutes))
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours}h {mins:02d}m"


def _estimate_run_minutes(row: pd.Series) -> int:
    started_at = parse_iso_ts(row.get("started_at"))
    ended_at = parse_iso_ts(row.get("ended_at"))
    due_at = parse_iso_ts(row.get("due_at"))
    status = str(row.get("status", "") or "").strip().upper()

    if started_at and ended_at:
        return max(0, int((ended_at - started_at).total_seconds() // 60))
    if started_at and status == "IN_PROGRESS":
        return max(0, int((now_ist() - started_at).total_seconds() // 60))
    if started_at and due_at:
        return max(0, int((due_at - started_at).total_seconds() // 60))

    try:
        return max(0, int(float(str(row.get("est_minutes", 0) or 0))))
    except Exception:
        return 0


def _build_appointments_df(df_schedule: pd.DataFrame, assistant_name: str, today_str: str) -> pd.DataFrame:
    filtered = _get_assistant_day_schedule_df(df_schedule, assistant_name, today_str)
    if filtered.empty:
        return pd.DataFrame(columns=["In", "Out", "Patient", "Doctor", "OP", "Role", "Status", "Procedure", "QTRAQ"])

    rows = []
    for _, row in filtered.iterrows():
        rows.append(
            {
                "In": _format_time(row.get("In Time")),
                "Out": _format_time(row.get("Out Time")),
                "Patient": str(row.get("Patient Name", "") or "").strip() or "—",
                "Doctor": str(row.get("DR.", "") or "").strip() or "—",
                "OP": str(row.get("OP", "") or "").strip() or "—",
                "Role": _assistant_roles(row, assistant_name),
                "Status": normalize_status(row.get("STATUS", "")),
                "Procedure": str(row.get("Procedure", "") or "").strip(),
                "QTRAQ": str(row.get("CASE PAPER", "") or "").strip(),
                "_sort": _time_sort_key(row.get("In Time")),
            }
        )
    result = pd.DataFrame(rows).sort_values(by=["_sort", "Patient"], ascending=[True, True]).drop(columns=["_sort"])
    return result.reset_index(drop=True)


def _build_duty_frames(assistant_name: str, today_str: str) -> tuple[pd.DataFrame, pd.DataFrame, list[dict], pd.DataFrame]:
    assistant_upper = str(assistant_name or "").strip().upper()
    assignments = get_active_duty_assignments(assistant_upper)

    runs_df = load_duty_runs()
    if runs_df is None or runs_df.empty:
        runs_df = pd.DataFrame(columns=["assistant", "date", "duty_id", "status", "started_at", "due_at", "ended_at", "op"])
    else:
        runs_df = runs_df.copy()
        if "assistant" in runs_df.columns:
            runs_df["assistant"] = runs_df["assistant"].fillna("").astype(str).str.strip().str.upper()
        if "date" in runs_df.columns:
            runs_df["date"] = runs_df["date"].fillna("").astype(str).str.strip()

    today_runs = runs_df[
        (runs_df.get("assistant", pd.Series("", index=runs_df.index)) == assistant_upper)
        & (runs_df.get("date", pd.Series("", index=runs_df.index)) == today_str)
    ].copy()

    latest_run_by_duty: dict[str, dict] = {}
    activity_rows: list[dict] = []
    if not today_runs.empty:
        for _, row in today_runs.iterrows():
            duty_id = str(row.get("duty_id", "") or "").strip()
            latest_run_by_duty[duty_id] = row.to_dict()
            activity_rows.append(
                {
                    "Task": str(row.get("duty_name", "") or duty_id or "Duty").strip(),
                    "Status": str(row.get("status", "") or "").strip().upper() or "—",
                    "Started": _format_iso_time(row.get("started_at")),
                    "Due": _format_iso_time(row.get("due_at")),
                    "Ended": _format_iso_time(row.get("ended_at")),
                    "OP": str(row.get("op", "") or "").strip() or "—",
                }
            )

    assigned_rows: list[dict] = []
    for duty in assignments:
        duty_id = str(duty.get("duty_id", "") or "").strip()
        run = latest_run_by_duty.get(duty_id, {})
        assigned_rows.append(
            {
                "Task": str(duty.get("name", "") or duty_id or "Duty").strip(),
                "Frequency": str(duty.get("frequency", "") or "").strip().upper() or "—",
                "OP": str(duty.get("op", "") or "").strip() or "—",
                "Today": str(run.get("status", "") or "ASSIGNED").strip().upper(),
                "Description": str(duty.get("description", "") or "").strip(),
            }
        )

    assigned_df = pd.DataFrame(assigned_rows)
    activity_df = pd.DataFrame(activity_rows)

    if not assigned_df.empty:
        assigned_df = assigned_df.sort_values(by=["Task", "OP"], ascending=[True, True]).reset_index(drop=True)
    if not activity_df.empty:
        activity_df = activity_df.sort_values(by=["Started", "Task"], ascending=[True, True]).reset_index(drop=True)

    return assigned_df, activity_df, assignments, today_runs


def _build_time_analytics(schedule_df: pd.DataFrame, duty_assignments: list[dict], today_runs: pd.DataFrame) -> dict[str, int]:
    patient_care_minutes = 0
    if schedule_df is not None and not schedule_df.empty:
        for _, row in schedule_df.iterrows():
            patient_care_minutes += _duration_minutes(row.get("In Time"), row.get("Out Time"))

    other_duty_minutes = 0
    duty_ids_with_runs: set[str] = set()
    if today_runs is not None and not today_runs.empty:
        for _, row in today_runs.iterrows():
            duty_id = str(row.get("duty_id", "") or "").strip()
            if duty_id:
                duty_ids_with_runs.add(duty_id)
            other_duty_minutes += _estimate_run_minutes(row)

    for duty in duty_assignments or []:
        duty_id = str(duty.get("duty_id", "") or "").strip()
        if duty_id and duty_id in duty_ids_with_runs:
            continue
        try:
            other_duty_minutes += max(0, int(float(str(duty.get("est_minutes", 0) or 0))))
        except Exception:
            continue

    free_time_minutes = max(0, CLINIC_SHIFT_MINUTES - patient_care_minutes - other_duty_minutes)
    return {
        "patient_care_minutes": patient_care_minutes,
        "other_duty_minutes": other_duty_minutes,
        "free_time_minutes": free_time_minutes,
    }


def render_assistant_day_detail(df_schedule: pd.DataFrame, assistant_name: str, today_str: str | None = None) -> None:
    assistant_upper = str(assistant_name or "").strip().upper()
    if not assistant_upper:
        return

    today_value = str(today_str or now_ist().date().isoformat()).strip()
    schedule_df = _get_assistant_day_schedule_df(df_schedule, assistant_upper, today_value)
    appointments_df = _build_appointments_df(df_schedule, assistant_upper, today_value)
    duties_df, duty_activity_df, duty_assignments, today_runs = _build_duty_frames(assistant_upper, today_value)
    analytics = _build_time_analytics(schedule_df, duty_assignments, today_runs)

    status_counts = appointments_df.get("Status", pd.Series(dtype=str)).astype(str).str.upper()
    ongoing_count = int(status_counts.eq("ON GOING").sum()) if not appointments_df.empty else 0

    st.markdown("---")
    st.markdown(f"### 📅 {assistant_upper} — Daily Schedule")
    st.caption(f"Showing appointments and tasks assigned on {today_value}.")

    metric_cols = st.columns(3)
    metric_cols[0].metric("Appointments", int(len(appointments_df)))
    metric_cols[1].metric("Ongoing", ongoing_count)
    metric_cols[2].metric("Tasks", int(len(duties_df)) if not duties_df.empty else int(len(duty_activity_df)))

    st.markdown("#### ⏱ Time Analytics")
    st.caption("Based on today's assigned appointment durations and duty activity/estimates within clinic hours (9 AM - 7 PM).")
    analytics_cols = st.columns(3)
    analytics_cols[0].metric("Patient Care", _format_minutes_label(analytics["patient_care_minutes"]))
    analytics_cols[1].metric("Other Duties", _format_minutes_label(analytics["other_duty_minutes"]))
    analytics_cols[2].metric("Free Time", _format_minutes_label(analytics["free_time_minutes"]))

    tab_appts, tab_tasks = st.tabs(["Appointments", "Tasks"])

    with tab_appts:
        if appointments_df.empty:
            st.info("No appointments assigned for this assistant today.")
        else:
            st.dataframe(appointments_df, width="stretch", hide_index=True)

    with tab_tasks:
        if duties_df.empty and duty_activity_df.empty:
            st.info("No duty/tasks assigned for this assistant today.")
        else:
            if not duties_df.empty:
                st.markdown("#### Assigned Duties")
                st.dataframe(duties_df, width="stretch", hide_index=True)
            if not duty_activity_df.empty:
                st.markdown("#### Today's Duty Activity")
                st.dataframe(duty_activity_df, width="stretch", hide_index=True)

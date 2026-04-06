# services/schedule_ops.py
"""Schedule business logic: filtering, status transitions, workload."""

from __future__ import annotations
from typing import Optional
from datetime import date as date_type, datetime, time as time_type, timedelta
import uuid
import pandas as pd

from services.utils import coerce_to_time_obj, time_to_minutes, now_ist, is_blank, parse_iso_ts
from config.constants import SCHEDULE_COLUMNS, STATUS_OPTIONS, TERMINAL_STATUSES

CLINIC_START_MINUTES = 9 * 60
CLINIC_END_MINUTES = 19 * 60
CLINIC_DAY_MINUTES = CLINIC_END_MINUTES - CLINIC_START_MINUTES


def ensure_schedule_columns(df: pd.DataFrame) -> pd.DataFrame:
    for col in SCHEDULE_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    return df


def ensure_row_ids(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure every row has a unique REMINDER_ROW_ID."""
    if "REMINDER_ROW_ID" not in df.columns:
        df["REMINDER_ROW_ID"] = ""
    mask = df["REMINDER_ROW_ID"].astype(str).str.strip().isin(["", "nan", "none", "NaT"])
    if mask.any():
        df.loc[mask, "REMINDER_ROW_ID"] = [str(uuid.uuid4()) for _ in range(int(mask.sum()))]
    return df


def normalize_status(value) -> str:
    """Normalize status labels to the app's canonical uppercase format."""
    status = str(value or "").strip().upper()
    legacy_map = {
        "ONGOING": "ON GOING",
        "PROCESSING": "PENDING",
        "WAITING": "PENDING",
        "LATE": "PENDING",
        "ARRIVING": "ARRIVED",
        "COMPLETED": "DONE",
        "SHIFTED": "CANCELLED",
    }
    if status in legacy_map:
        return legacy_map[status]
    return status


def is_status_ongoing(value) -> bool:
    return normalize_status(value) == "ON GOING"


def status_option_for_ui(value) -> str:
    """Map stored status values to one of the supported dropdown options."""
    status = normalize_status(value)
    if status in STATUS_OPTIONS:
        return status
    return "PENDING"


def _normalize_target_date(target_date=None) -> date_type:
    if target_date is None:
        return now_ist().date()
    if isinstance(target_date, datetime):
        return target_date.date()
    if isinstance(target_date, date_type):
        return target_date
    parsed = pd.to_datetime(target_date, errors="coerce")
    if pd.notna(parsed):
        return parsed.date()
    return now_ist().date()


def _clinic_window(target_date=None) -> tuple[datetime, datetime]:
    target_day = _normalize_target_date(target_date)
    tzinfo = now_ist().tzinfo
    start_dt = datetime.combine(target_day, time_type(CLINIC_START_MINUTES // 60, CLINIC_START_MINUTES % 60)).replace(tzinfo=tzinfo)
    end_dt = datetime.combine(target_day, time_type(CLINIC_END_MINUTES // 60, CLINIC_END_MINUTES % 60)).replace(tzinfo=tzinfo)
    return start_dt, end_dt


def _effective_window_end(target_date=None) -> datetime:
    target_day = _normalize_target_date(target_date)
    clinic_start, clinic_end = _clinic_window(target_day)
    if target_day != now_ist().date():
        return clinic_end
    current = now_ist()
    if current <= clinic_start:
        return clinic_start
    return min(current, clinic_end)


def _combine_date_time(target_date: date_type, value) -> Optional[datetime]:
    time_obj = coerce_to_time_obj(value)
    if time_obj is None:
        return None
    return datetime.combine(target_date, time_obj).replace(tzinfo=now_ist().tzinfo)


def _duration_minutes_between(start_dt: Optional[datetime], end_dt: Optional[datetime]) -> int:
    if start_dt is None or end_dt is None:
        return 0
    return max(0, int((end_dt - start_dt).total_seconds() // 60))


def _clamp_interval(start_dt: Optional[datetime], end_dt: Optional[datetime], window_start: datetime, window_end: datetime) -> Optional[tuple[datetime, datetime]]:
    if start_dt is None or end_dt is None:
        return None
    start_value = max(start_dt, window_start)
    end_value = min(end_dt, window_end)
    if end_value <= start_value:
        return None
    return start_value, end_value


def _merge_intervals(intervals: list[tuple[datetime, datetime]]) -> list[tuple[datetime, datetime]]:
    if not intervals:
        return []
    ordered = sorted(intervals, key=lambda item: item[0])
    merged = [ordered[0]]
    for start_dt, end_dt in ordered[1:]:
        prev_start, prev_end = merged[-1]
        if start_dt <= prev_end:
            merged[-1] = (prev_start, max(prev_end, end_dt))
        else:
            merged.append((start_dt, end_dt))
    return merged


def get_schedule_date_series(df: pd.DataFrame) -> pd.Series:
    """Return the best-available schedule date series for strict day filtering."""
    if df is None or df.empty:
        return pd.Series(dtype=str)

    date_series = (
        df["DATE"].fillna("").astype(str).str.strip()
        if "DATE" in df.columns
        else pd.Series([""] * len(df), index=df.index, dtype=str)
    )
    if "appointment_date" in df.columns:
        fallback = df["appointment_date"].fillna("").astype(str).str.strip()
        date_series = date_series.where(date_series.ne(""), fallback)
    return date_series


def filter_schedule_for_date(df: pd.DataFrame, target_date=None) -> pd.DataFrame:
    """Return only rows scheduled for the given calendar date."""
    if df is None:
        return pd.DataFrame()
    if df.empty:
        return df.copy()

    if target_date is None:
        target_date = now_ist().date().isoformat()

    target_dt = pd.to_datetime(target_date, errors="coerce")
    if pd.isna(target_dt):
        return df.iloc[0:0].copy()

    formatted_date = target_dt.strftime("%Y-%m-%d")
    raw_dates = get_schedule_date_series(df).fillna("").astype(str).str.strip()
    raw_lower = raw_dates.str.lower()

    direct_match = (
        raw_dates.eq(formatted_date)
        | raw_dates.str.startswith(f"{formatted_date}T")
        | raw_dates.str.startswith(f"{formatted_date} ")
    )
    parse_input = raw_dates.where(~raw_lower.isin(["", "nan", "none", "nat"]))
    normalized_default = pd.to_datetime(parse_input, errors="coerce").dt.strftime("%Y-%m-%d")
    normalized_dayfirst = pd.to_datetime(parse_input, errors="coerce", dayfirst=True).dt.strftime("%Y-%m-%d")
    mask = direct_match | normalized_default.eq(formatted_date) | normalized_dayfirst.eq(formatted_date)
    return df[mask.fillna(False)].copy()


def filter_rows_for_assistant(df: pd.DataFrame, assistant_name: str) -> pd.DataFrame:
    """Return only rows where the assistant is assigned in any allotment slot."""
    if df is None:
        return pd.DataFrame()
    if df.empty:
        return df.copy()

    assist_upper = str(assistant_name or "").strip().upper()
    if not assist_upper:
        return df.iloc[0:0].copy()

    mask = pd.Series(False, index=df.index)
    for col in ["FIRST", "SECOND", "Third"]:
        if col in df.columns:
            mask = mask | df[col].fillna("").astype(str).str.strip().str.upper().eq(assist_upper)
    return df[mask].copy()


def add_computed_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Add In_min, Out_min, Is_Ongoing columns."""
    def to_min(val):
        if is_blank(val):
            return None
        return time_to_minutes(val)

    df = df.copy()
    df["In_min"] = df["In Time"].apply(to_min)
    df["Out_min"] = df["Out Time"].apply(to_min)
    df["Is_Ongoing"] = df.get("STATUS", pd.Series("", index=df.index)).apply(is_status_ongoing)
    return df


def filter_ongoing(df: pd.DataFrame) -> pd.DataFrame:
    if "In_min" not in df.columns:
        df = add_computed_columns(df)
    ongoing_mask = df.get("Is_Ongoing", pd.Series(False, index=df.index)).fillna(False)
    return df[ongoing_mask].copy()


def filter_upcoming(df: pd.DataFrame, minutes_ahead: int = 60) -> pd.DataFrame:
    if "In_min" not in df.columns:
        df = add_computed_columns(df)
    now = now_ist()
    current_min = now.hour * 60 + now.minute
    mask = (
        df["In_min"].notna() &
        (df["In_min"] > current_min) &
        (df["In_min"] <= current_min + minutes_ahead)
    )
    status_col = df.get("STATUS", pd.Series("", index=df.index)).apply(normalize_status)
    not_terminal = ~status_col.isin(TERMINAL_STATUSES)
    not_ongoing = ~status_col.apply(is_status_ongoing)
    return df[mask & not_terminal & not_ongoing].copy()


def filter_by_op(df: pd.DataFrame, op: str) -> pd.DataFrame:
    if "OP" not in df.columns:
        return pd.DataFrame(columns=df.columns)
    return df[df["OP"].astype(str).str.strip().str.upper() == op.strip().upper()].copy()


def filter_by_doctor(df: pd.DataFrame, doctor: str) -> pd.DataFrame:
    col = "DR." if "DR." in df.columns else "Doctor"
    if col not in df.columns:
        return pd.DataFrame(columns=df.columns)
    return df[df[col].astype(str).str.strip().str.upper() == doctor.strip().upper()].copy()


def update_status(df: pd.DataFrame, row_id: str, new_status: str) -> pd.DataFrame:
    from config.settings import IST
    from datetime import datetime
    if "REMINDER_ROW_ID" not in df.columns:
        return df
    mask = df["REMINDER_ROW_ID"].astype(str) == str(row_id)
    if not mask.any():
        return df
    df = df.copy()
    now_str = datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S")
    status_value = normalize_status(new_status)
    df.loc[mask, "STATUS"] = status_value
    df.loc[mask, "STATUS_CHANGED_AT"] = now_str
    if is_status_ongoing(status_value):
        df.loc[mask, "ACTUAL_START_AT"] = now_str
    elif status_value in TERMINAL_STATUSES:
        df.loc[mask, "ACTUAL_END_AT"] = now_str
    return df


def apply_row_updates(df: pd.DataFrame, row_id: str, updates: dict) -> pd.DataFrame:
    """Apply row edits while preserving status timestamp logic."""
    if df is None or df.empty or "REMINDER_ROW_ID" not in df.columns:
        return df

    mask = df["REMINDER_ROW_ID"].astype(str).str.strip() == str(row_id).strip()
    if not mask.any():
        return df

    updated = df.copy()
    pending_status = None
    for col, val in (updates or {}).items():
        if col == "STATUS":
            pending_status = val
            continue
        if col in updated.columns:
            updated.loc[mask, col] = val

    if pending_status is not None and "STATUS" in updated.columns:
        current_status = str(updated.loc[mask, "STATUS"].iloc[0] or "")
        if normalize_status(current_status) != normalize_status(pending_status):
            updated = update_status(updated, row_id, str(pending_status))
    return updated


def merge_updated_view(full_df: pd.DataFrame, view_df: pd.DataFrame, updated_view: pd.DataFrame) -> pd.DataFrame:
    """Merge an edited filtered/table view back into the full schedule DataFrame."""
    if full_df is None or full_df.empty:
        return full_df
    if view_df is None or updated_view is None or view_df.empty or updated_view.empty:
        return full_df.copy()

    merged = full_df.copy()
    view_indices = list(view_df.index)
    for pos, full_idx in enumerate(view_indices):
        if pos >= len(updated_view):
            break

        row_updates: dict = {}
        for col in updated_view.columns:
            if col not in merged.columns:
                continue
            row_updates[col] = updated_view.iloc[pos][col]

        if "STATUS" in row_updates and "REMINDER_ROW_ID" in merged.columns:
            row_id = str(merged.loc[full_idx, "REMINDER_ROW_ID"] or "").strip()
            merged = apply_row_updates(merged, row_id, row_updates)
        else:
            for col, val in row_updates.items():
                merged.loc[full_idx, col] = val
    return merged


def _build_busy_record(row: pd.Series, target_date=None) -> Optional[dict]:
    target_day = _normalize_target_date(target_date)
    status = normalize_status(row.get("STATUS", ""))
    actual_start = parse_iso_ts(row.get("ACTUAL_START_AT"))
    actual_end = parse_iso_ts(row.get("ACTUAL_END_AT"))
    changed_at = parse_iso_ts(row.get("STATUS_CHANGED_AT"))
    scheduled_start = _combine_date_time(target_day, row.get("In Time"))
    scheduled_end = _combine_date_time(target_day, row.get("Out Time"))
    if scheduled_start and scheduled_end and scheduled_end < scheduled_start:
        scheduled_end += timedelta(days=1)

    if actual_start:
        start_dt = actual_start
    elif status == "ON GOING":
        start_dt = changed_at or scheduled_start
    else:
        return None

    if start_dt is None:
        return None

    is_today = target_day == now_ist().date()
    if status == "ON GOING":
        end_dt = _effective_window_end(target_day) if is_today else (scheduled_end or start_dt)
        predicted_end_dt = scheduled_end or end_dt
        is_live = is_today
    elif status in TERMINAL_STATUSES:
        end_dt = actual_end or scheduled_end or start_dt
        predicted_end_dt = end_dt
        is_live = False
    else:
        return None

    if end_dt is None or end_dt < start_dt:
        end_dt = start_dt
    if predicted_end_dt is None or predicted_end_dt < start_dt:
        predicted_end_dt = end_dt

    assistants = []
    for col in ["FIRST", "SECOND", "Third"]:
        value = str(row.get(col, "") or "").strip()
        if value and value.upper() not in {name.upper() for name in assistants}:
            assistants.append(value)

    return {
        "row_id": str(row.get("REMINDER_ROW_ID", "") or "").strip(),
        "patient": str(row.get("Patient Name", "") or "").strip() or "—",
        "doctor": str(row.get("DR.", "") or "").strip() or "—",
        "assistants": assistants,
        "op": str(row.get("OP", "") or "").strip(),
        "status": status,
        "scheduled_in": scheduled_start,
        "scheduled_out": scheduled_end,
        "start_dt": start_dt,
        "end_dt": end_dt,
        "predicted_end_dt": predicted_end_dt,
        "minutes": _duration_minutes_between(start_dt, end_dt),
        "is_live": is_live,
    }


def build_op_activity_records(df: pd.DataFrame, target_date=None, op_rooms: list[str] | None = None) -> dict[str, list[dict]]:
    """Return per-OP busy session records derived from patient status history."""
    target_day = _normalize_target_date(target_date)
    filtered = filter_schedule_for_date(df, target_day.isoformat())

    op_names = set(op_rooms or [])
    if filtered is not None and not filtered.empty and "OP" in filtered.columns:
        op_names.update(
            {
                str(value).strip()
                for value in filtered["OP"].dropna().astype(str).tolist()
                if str(value).strip()
            }
        )

    records_by_op = {op: [] for op in sorted(op_names)}
    if filtered is None or filtered.empty:
        return records_by_op

    for _, row in filtered.iterrows():
        op = str(row.get("OP", "") or "").strip()
        if not op:
            continue
        record = _build_busy_record(row, target_day)
        if record is None:
            records_by_op.setdefault(op, [])
            continue
        records_by_op.setdefault(op, []).append(record)

    for op in records_by_op:
        records_by_op[op] = sorted(records_by_op[op], key=lambda item: item["start_dt"])
    return records_by_op


def build_op_free_intervals(activity_records: list[dict], target_date=None) -> list[dict]:
    """Return free/unoccupied intervals between busy sessions for the given OP/day."""
    window_start, _ = _clinic_window(target_date)
    effective_end = _effective_window_end(target_date)
    if effective_end <= window_start:
        return []

    merged_busy = _merge_intervals(
        [
            interval
            for interval in (
                _clamp_interval(record.get("start_dt"), record.get("end_dt"), window_start, effective_end)
                for record in activity_records or []
            )
            if interval is not None
        ]
    )

    gaps: list[dict] = []
    cursor = window_start
    for idx, (busy_start, busy_end) in enumerate(merged_busy):
        if busy_start > cursor:
            gaps.append(
                {
                    "index": len(gaps) + 1,
                    "start_dt": cursor,
                    "end_dt": busy_start,
                    "minutes": _duration_minutes_between(cursor, busy_start),
                    "label": "Before first busy session" if idx == 0 else "Between busy sessions",
                }
            )
        cursor = max(cursor, busy_end)

    if cursor < effective_end:
        gaps.append(
            {
                "index": len(gaps) + 1,
                "start_dt": cursor,
                "end_dt": effective_end,
                "minutes": _duration_minutes_between(cursor, effective_end),
                "label": "Currently free" if target_date is None or _normalize_target_date(target_date) == now_ist().date() else "After last busy session",
            }
        )
    return gaps


def build_op_status_summary(df: pd.DataFrame, target_date=None, op_rooms: list[str] | None = None) -> pd.DataFrame:
    """Build per-OP busy/free summary synced to patient status."""
    target_day = _normalize_target_date(target_date)
    window_start, _ = _clinic_window(target_day)
    effective_end = _effective_window_end(target_day)
    current_dt = now_ist() if target_day == now_ist().date() else effective_end
    total_logged_minutes = _duration_minutes_between(window_start, effective_end)

    activity_by_op = build_op_activity_records(df, target_day, op_rooms=op_rooms)
    rows = []
    for op, records in activity_by_op.items():
        merged_busy = _merge_intervals(
            [
                interval
                for interval in (
                    _clamp_interval(record.get("start_dt"), record.get("end_dt"), window_start, effective_end)
                    for record in records
                )
                if interval is not None
            ]
        )
        busy_logged = sum(_duration_minutes_between(start_dt, end_dt) for start_dt, end_dt in merged_busy)
        free_logged = max(0, total_logged_minutes - busy_logged)

        live_records = [record for record in records if record.get("is_live")]
        if live_records:
            live_start = min(record["start_dt"] for record in live_records)
            expected_free_at = max(record.get("predicted_end_dt") or record["end_dt"] for record in live_records)
            if expected_free_at < current_dt:
                expected_free_at = current_dt
            current_status = "BUSY"
            current_patient = live_records[0]["patient"] if len(live_records) == 1 else f"{len(live_records)} ongoing patients"
            current_doctor = live_records[0]["doctor"] if len(live_records) == 1 else ""
            current_assistants = sorted(
                {
                    assistant
                    for record in live_records
                    for assistant in (record.get("assistants") or [])
                    if str(assistant or "").strip()
                }
            )
            current_for = _duration_minutes_between(live_start, current_dt)
            available_in = _duration_minutes_between(current_dt, expected_free_at)
        else:
            current_status = "FREE"
            current_patient = ""
            current_doctor = ""
            current_assistants = []
            last_busy_end = max(
                (min(record["end_dt"], effective_end) for record in records if record.get("end_dt")),
                default=window_start,
            )
            free_since = min(last_busy_end, current_dt)
            current_for = _duration_minutes_between(free_since, current_dt)
            expected_free_at = current_dt
            available_in = 0

        rows.append(
            {
                "OP": op,
                "Current Status": current_status,
                "Current Patient": current_patient,
                "Current Doctor": current_doctor,
                "Current Assistants": ", ".join(current_assistants),
                "Current For Minutes": current_for,
                "Available In Minutes": available_in,
                "Expected Free At": expected_free_at,
                "Busy Logged Minutes": busy_logged,
                "Free Logged Minutes": free_logged,
                "Busy Sessions": len(records),
            }
        )

    result = pd.DataFrame(rows)
    if result.empty:
        return result
    return result.sort_values(
        by=["Current Status", "OP"],
        ascending=[True, True],
        key=lambda series: series.map({"BUSY": 0, "FREE": 1}) if series.name == "Current Status" else series,
    ).reset_index(drop=True)


def get_op_detail_frames(df: pd.DataFrame, op: str, target_date=None) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Return busy-session table, free-gap table, and summary for a single OP/day."""
    target_day = _normalize_target_date(target_date)
    activity_by_op = build_op_activity_records(df, target_day, op_rooms=[op])
    records = activity_by_op.get(str(op or "").strip(), [])
    gaps = build_op_free_intervals(records, target_day)
    summary_df = build_op_status_summary(df, target_day, op_rooms=[op])
    summary = summary_df.iloc[0].to_dict() if not summary_df.empty else {}

    busy_df = pd.DataFrame(
        [
            {
                "Patient": record["patient"],
                "Doctor": record["doctor"],
                "Status": record["status"],
                "Started": record["start_dt"],
                "Ended": record["end_dt"],
                "Busy Minutes": record["minutes"],
                "Scheduled In": record["scheduled_in"],
                "Scheduled Out": record["scheduled_out"],
            }
            for record in records
        ]
    )
    free_df = pd.DataFrame(
        [
            {
                "Gap": gap["label"],
                "From": gap["start_dt"],
                "To": gap["end_dt"],
                "Free Minutes": gap["minutes"],
            }
            for gap in gaps
        ]
    )
    return busy_df, free_df, summary


def get_assistant_loads(df_schedule: pd.DataFrame, exclude_row_id: Optional[str] = None) -> dict[str, int]:
    loads: dict[str, int] = {}
    if df_schedule is None or df_schedule.empty:
        return loads
    for _, row in df_schedule.iterrows():
        if exclude_row_id:
            rid = str(row.get("REMINDER_ROW_ID", "")).strip()
            if rid == str(exclude_row_id).strip():
                continue
        status = str(row.get("STATUS", "")).strip().upper()
        if status in TERMINAL_STATUSES:
            continue
        for col in ["FIRST", "SECOND", "Third"]:
            if col in row.index:
                val = str(row.get(col, "")).strip().upper()
                if val:
                    loads[val] = loads.get(val, 0) + 1
    return loads


def remove_assistant_from_schedule(df: pd.DataFrame, assistant_name: str) -> Optional[pd.DataFrame]:
    if df is None or df.empty:
        return None
    assist_upper = str(assistant_name).strip().upper()
    df_updated = df.copy()
    changed = False
    for col in ["FIRST", "SECOND", "Third"]:
        if col not in df_updated.columns:
            continue
        mask = df_updated[col].astype(str).str.strip().str.upper() == assist_upper
        if mask.any():
            df_updated.loc[mask, col] = ""
            changed = True
    return df_updated if changed else None


def compute_workload_summary(df_schedule: pd.DataFrame, assistants: list[str]) -> pd.DataFrame:
    """Compute workload including appointment count and hours busy/available (9 AM - 7 PM = 10 hours)."""
    CLINIC_HOURS = 10  # 9 AM to 7 PM
    rows = []
    for a in assistants:
        a_upper = a.strip().upper()
        total = as_first = as_second = as_third = 0
        total_minutes_busy = 0

        for _, row in df_schedule.iterrows():
            if str(row.get("STATUS", "")).upper() in TERMINAL_STATUSES:
                continue

            is_assigned = False
            if str(row.get("FIRST", "")).strip().upper() == a_upper:
                total += 1; as_first += 1
                is_assigned = True
            elif str(row.get("SECOND", "")).strip().upper() == a_upper:
                total += 1; as_second += 1
                is_assigned = True
            elif str(row.get("Third", "")).strip().upper() == a_upper:
                total += 1; as_third += 1
                is_assigned = True

            # Calculate appointment duration
            if is_assigned:
                in_min = row.get("In_min")
                out_min = row.get("Out_min")
                if in_min is not None and out_min is not None and out_min > in_min:
                    duration = out_min - in_min
                    total_minutes_busy += duration

        hours_busy = total_minutes_busy / 60
        hours_available = CLINIC_HOURS - hours_busy
        overtime_hours = max(0, hours_busy - CLINIC_HOURS)

        rows.append({
            "Assistant": a,
            "Appointments": total,
            "Hours Busy": round(hours_busy, 2),
            "Hours Available": round(max(0, hours_available), 2),
            "Overtime (After 7 PM)": round(overtime_hours, 2),
            "As First": as_first,
            "As Second": as_second,
            "As Third": as_third,
        })
    return pd.DataFrame(rows)

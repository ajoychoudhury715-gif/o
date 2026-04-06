# services/schedule_ops.py
"""Schedule business logic: filtering, status transitions, workload."""

from __future__ import annotations
from typing import Optional
import uuid
import pandas as pd

from services.utils import coerce_to_time_obj, time_to_minutes, now_ist, is_blank
from config.constants import SCHEDULE_COLUMNS, TERMINAL_STATUSES


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
    if status == "ONGOING":
        return "ON GOING"
    return status


def is_status_ongoing(value) -> bool:
    return normalize_status(value) == "ON GOING"


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

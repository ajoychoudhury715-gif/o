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


def add_computed_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Add In_min, Out_min, Is_Ongoing columns."""
    now = now_ist()
    current_min = now.hour * 60 + now.minute

    def to_min(val):
        if is_blank(val):
            return None
        return time_to_minutes(val)

    df = df.copy()
    df["In_min"] = df["In Time"].apply(to_min)
    df["Out_min"] = df["Out Time"].apply(to_min)
    df["Is_Ongoing"] = df.apply(
        lambda r: bool(
            r["In_min"] is not None and r["Out_min"] is not None
            and r["In_min"] <= current_min <= r["Out_min"]
        ),
        axis=1,
    )
    return df


def filter_ongoing(df: pd.DataFrame) -> pd.DataFrame:
    if "In_min" not in df.columns:
        df = add_computed_columns(df)
    ongoing_mask = df.get("Is_Ongoing", pd.Series(False, index=df.index))
    status_ongoing = df.get("STATUS", pd.Series(dtype=str)).astype(str).str.upper().str.contains("ON GOING|ONGOING", na=False)
    return df[ongoing_mask | status_ongoing].copy()


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
    status_col = df.get("STATUS", pd.Series(dtype=str)).astype(str).str.upper()
    not_terminal = ~status_col.isin(TERMINAL_STATUSES)
    return df[mask & not_terminal].copy()


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
    df.loc[mask, "STATUS"] = new_status
    df.loc[mask, "STATUS_CHANGED_AT"] = now_str
    if new_status in {"ON GOING", "ARRIVED"}:
        df.loc[mask, "ACTUAL_START_AT"] = now_str
    elif new_status in TERMINAL_STATUSES:
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
    rows = []
    for a in assistants:
        a_upper = a.strip().upper()
        total = as_first = as_second = as_third = 0
        for _, row in df_schedule.iterrows():
            if str(row.get("STATUS", "")).upper() in TERMINAL_STATUSES:
                continue
            if str(row.get("FIRST", "")).strip().upper() == a_upper:
                total += 1; as_first += 1
            elif str(row.get("SECOND", "")).strip().upper() == a_upper:
                total += 1; as_second += 1
            elif str(row.get("Third", "")).strip().upper() == a_upper:
                total += 1; as_third += 1
        rows.append({"Assistant": a, "Total": total, "As First": as_first, "As Second": as_second, "As Third": as_third})
    return pd.DataFrame(rows)

# services/reminder_service.py
"""15-minute appointment reminder logic."""

from __future__ import annotations
from typing import Any
import pandas as pd

from services.utils import coerce_to_time_obj, now_ist, parse_iso_ts
from config.constants import TERMINAL_STATUSES
from services.schedule_ops import (
    filter_rows_for_assistant,
    filter_schedule_for_date,
    is_status_ongoing,
    normalize_status,
)

REMINDER_ADVANCE_MINUTES = 15


def get_due_reminders(
    df_schedule: pd.DataFrame,
    current_user: str = "",
    current_role: str = "",
) -> list[dict[str, Any]]:
    """Return due reminders for today's relevant appointments."""
    if df_schedule is None or df_schedule.empty:
        return []

    now = now_ist()
    scoped_df = filter_schedule_for_date(df_schedule, now.date().isoformat())
    role = str(current_role or "").strip().lower()
    user = str(current_user or "").strip().upper()
    if role == "assistant" and user:
        scoped_df = filter_rows_for_assistant(scoped_df, user)
    if scoped_df.empty:
        return []

    current_min = now.hour * 60 + now.minute
    due = []
    for _, row in scoped_df.iterrows():
        status = normalize_status(row.get("STATUS", ""))
        if status in TERMINAL_STATUSES or is_status_ongoing(status):
            continue
        dismissed = str(row.get("REMINDER_DISMISSED", "")).strip().lower()
        if dismissed in {"1", "true", "yes"}:
            continue
        snooze_until = str(row.get("REMINDER_SNOOZE_UNTIL", "")).strip()
        if snooze_until:
            snooze_dt = parse_iso_ts(snooze_until)
            if snooze_dt and snooze_dt > now:
                continue
        in_obj = coerce_to_time_obj(row.get("In Time"))
        if in_obj is None:
            continue
        in_min = in_obj.hour * 60 + in_obj.minute
        minutes_until = in_min - current_min
        if 0 <= minutes_until <= REMINDER_ADVANCE_MINUTES:
            due.append({
                "row_id": str(row.get("REMINDER_ROW_ID", "")).strip(),
                "patient": row.get("Patient Name", "Unknown"),
                "in_time": row.get("In Time"),
                "doctor": row.get("DR.", ""),
                "op": row.get("OP", ""),
                "minutes_until": minutes_until,
                "status": status,
            })
    due.sort(key=lambda item: (int(item.get("minutes_until", 9999)), str(item.get("patient", "")).strip().upper()))
    return due


def dismiss_reminder(df: pd.DataFrame, row_id: str) -> pd.DataFrame:
    if "REMINDER_ROW_ID" not in df.columns:
        return df
    df = df.copy()
    mask = df["REMINDER_ROW_ID"].astype(str) == row_id
    df.loc[mask, "REMINDER_DISMISSED"] = "1"
    return df


def snooze_reminder(df: pd.DataFrame, row_id: str, snooze_minutes: int = 5) -> pd.DataFrame:
    from datetime import timedelta
    if "REMINDER_ROW_ID" not in df.columns:
        return df
    df = df.copy()
    mask = df["REMINDER_ROW_ID"].astype(str) == row_id
    df.loc[mask, "REMINDER_SNOOZE_UNTIL"] = (now_ist() + timedelta(minutes=snooze_minutes)).isoformat()
    return df

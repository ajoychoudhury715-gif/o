# services/reminder_service.py
"""15-minute appointment reminder logic."""

from __future__ import annotations
from typing import Any
import pandas as pd

from services.utils import coerce_to_time_obj, now_ist, parse_iso_ts
from config.constants import TERMINAL_STATUSES

REMINDER_ADVANCE_MINUTES = 15


def get_due_reminders(df_schedule: pd.DataFrame) -> list[dict[str, Any]]:
    """Return appointments due for a reminder (within 15 min, not dismissed/snoozed)."""
    if df_schedule is None or df_schedule.empty:
        return []
    now = now_ist()
    current_min = now.hour * 60 + now.minute
    due = []
    for _, row in df_schedule.iterrows():
        status = str(row.get("STATUS", "")).strip().upper()
        if status in TERMINAL_STATUSES:
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

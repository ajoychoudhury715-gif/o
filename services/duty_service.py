# services/duty_service.py
"""Duty timer logic and pending duty computation."""

from __future__ import annotations
from datetime import date, timedelta
from typing import Any, Optional


def compute_pending_duties(
    assignments: list[dict[str, Any]],
    runs: list[dict[str, Any]],
    today: date,
) -> dict[str, list[dict[str, Any]]]:
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)
    done_week: set = set()
    done_month: set = set()
    for r in runs:
        if str(r.get("status", "")).upper() != "DONE":
            continue
        r_date = _parse_date(r.get("date"))
        if r_date is None:
            continue
        if r_date >= week_start:
            done_week.add(r.get("duty_id"))
        if r_date >= month_start:
            done_month.add(r.get("duty_id"))
    pending: dict[str, list] = {"WEEKLY": [], "MONTHLY": []}
    for a in assignments:
        freq = str(a.get("frequency", "")).upper()
        duty_id = a.get("duty_id")
        if freq == "WEEKLY" and duty_id not in done_week:
            pending["WEEKLY"].append(a)
        elif freq == "MONTHLY" and duty_id not in done_month:
            pending["MONTHLY"].append(a)
    return pending


def format_remaining_time(due_at_iso: Optional[str]) -> str:
    from services.utils import parse_iso_ts, now_ist
    if not due_at_iso:
        return ""
    due_dt = parse_iso_ts(due_at_iso)
    if not due_dt:
        return ""
    delta = due_dt - now_ist()
    total_secs = delta.total_seconds()
    if total_secs <= 0:
        return "00:00"
    mins = int(total_secs // 60)
    secs = int(total_secs % 60)
    return f"{mins:02d}:{secs:02d}"


def _parse_date(value) -> Optional[date]:
    if value is None:
        return None
    try:
        from datetime import datetime
        if isinstance(value, date):
            return value
        return datetime.strptime(str(value).strip()[:10], "%Y-%m-%d").date()
    except Exception:
        return None

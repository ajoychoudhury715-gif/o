# services/utils.py
"""Shared utility functions used across services (no Streamlit imports)."""

from __future__ import annotations
from datetime import time as time_type, datetime, timezone, timedelta
from typing import Any, Optional

IST = timezone(timedelta(hours=5, minutes=30))


def now_ist() -> datetime:
    return datetime.now(IST)


def time_to_minutes(value: Any) -> Optional[int]:
    """Convert various time representations to minutes since midnight."""
    if value is None:
        return None
    if isinstance(value, time_type):
        return value.hour * 60 + value.minute
    if isinstance(value, datetime):
        return value.hour * 60 + value.minute
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return None
        try:
            parts = s.split(":")
            if len(parts) >= 2:
                h, m = int(parts[0]), int(parts[1])
                if 0 <= h < 24 and 0 <= m < 60:
                    return h * 60 + m
        except Exception:
            pass
    try:
        val = float(value)
        if 0 <= val < 24:
            hours = int(val)
            minutes = int((val - hours) * 60)
            return hours * 60 + minutes
        if 0 <= val < 1440:
            return int(val)
    except Exception:
        pass
    return None


def coerce_to_time_obj(value: Any) -> Optional[time_type]:
    """Convert various time representations to a time object."""
    if value is None:
        return None
    if isinstance(value, time_type):
        return value
    if isinstance(value, datetime):
        return value.time().replace(second=0, microsecond=0)
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return None
        try:
            parts = s.split(":")
            if len(parts) >= 2:
                h, m = int(parts[0]), int(parts[1])
                if 0 <= h < 24 and 0 <= m < 60:
                    return time_type(h, m)
        except Exception:
            pass
    try:
        mins = time_to_minutes(value)
        if mins is not None:
            return time_type(mins // 60, mins % 60)
    except Exception:
        pass
    return None


def time_to_hhmm(t: Optional[time_type]) -> str:
    if t is None:
        return ""
    return f"{t.hour:02d}:{t.minute:02d}"


def time_to_12h(t: Optional[time_type]) -> str:
    """Format time in 12-hour AM/PM format. Example: '2:30 PM'"""
    if t is None:
        return ""
    hour = t.hour
    minute = t.minute
    period = "AM" if hour < 12 else "PM"
    hour_12 = hour if hour <= 12 else hour - 12
    if hour_12 == 0:
        hour_12 = 12
    return f"{hour_12}:{minute:02d} {period}"


def is_blank(value: Any) -> bool:
    """Return True if value is effectively empty/null."""
    if value is None:
        return True
    try:
        import pandas as pd
        if pd.isna(value):
            return True
    except Exception:
        pass
    return str(value).strip().lower() in ("", "nan", "none", "nat")


def norm_name(name: str) -> str:
    """Normalize a staff name to a lookup key."""
    return str(name or "").strip().upper().replace("DR.", "").replace("DR ", "").strip()


def unique_preserve_order(items: list) -> list:
    seen: set = set()
    out = []
    for item in items:
        key = str(item).strip().upper()
        if key and key not in seen:
            seen.add(key)
            out.append(item)
    return out


def safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(str(value)))
    except Exception:
        return default


def parse_iso_ts(value: Any) -> Optional[datetime]:
    if not value:
        return None
    try:
        s = str(value).strip()
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=IST)
        return dt
    except Exception:
        return None

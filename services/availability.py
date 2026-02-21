# services/availability.py
"""Assistant availability: punch checks, time blocks, schedule conflicts."""

from __future__ import annotations
from datetime import time as time_type
from typing import Any, Optional
import json
import pandas as pd

from services.utils import coerce_to_time_obj, time_to_minutes, now_ist, is_blank, time_to_hhmm
from config.constants import TERMINAL_STATUSES


def get_assistant_schedule(assistant_name: str, df_schedule: pd.DataFrame) -> list[dict[str, Any]]:
    """Get all active appointments where this assistant is assigned."""
    if not assistant_name or df_schedule is None or df_schedule.empty:
        return []
    assist_upper = str(assistant_name).strip().upper()
    appointments = []
    for _, row in df_schedule.iterrows():
        for col in ["FIRST", "SECOND", "Third"]:
            if col in row.index:
                val = str(row.get(col, "")).strip().upper()
                if val == assist_upper:
                    status = str(row.get("STATUS", "")).strip().upper()
                    if any(s in status for s in TERMINAL_STATUSES):
                        continue
                    appointments.append({
                        "row_id": row.get("REMINDER_ROW_ID", ""),
                        "patient": row.get("Patient Name", "Unknown"),
                        "in_time": row.get("In Time"),
                        "out_time": row.get("Out Time"),
                        "doctor": row.get("DR.", ""),
                        "op": row.get("OP", ""),
                        "role": col,
                        "status": status,
                    })
                    break
    return appointments


def is_blocked_by_time_block(
    assistant_upper: str,
    check_in_min: int,
    check_out_min: int,
    time_blocks: list[dict],
    today_str: str,
) -> tuple[bool, str]:
    for block in time_blocks:
        if str(block.get("date", "")).strip() != today_str:
            continue
        if str(block.get("assistant", "")).strip().upper() != assistant_upper:
            continue
        start_t = coerce_to_time_obj(block.get("start_time"))
        end_t = coerce_to_time_obj(block.get("end_time"))
        if start_t is None or end_t is None:
            continue
        start_min = start_t.hour * 60 + start_t.minute
        end_min = end_t.hour * 60 + end_t.minute
        if end_min < start_min:
            end_min += 1440
        if not (check_out_min <= start_min or check_in_min >= end_min):
            return True, f"Blocked: {block.get('reason', 'Blocked')}"
    return False, ""


def is_blocked_by_time_block_point(
    assistant_upper: str,
    check_time: time_type,
    time_blocks: list[dict],
    today_str: str,
) -> tuple[bool, str]:
    check_min = check_time.hour * 60 + check_time.minute
    for block in time_blocks:
        if str(block.get("date", "")).strip() != today_str:
            continue
        if str(block.get("assistant", "")).strip().upper() != assistant_upper:
            continue
        start_t = coerce_to_time_obj(block.get("start_time"))
        end_t = coerce_to_time_obj(block.get("end_time"))
        if start_t is None or end_t is None:
            continue
        start_min = start_t.hour * 60 + start_t.minute
        end_min = end_t.hour * 60 + end_t.minute
        if start_min <= check_min <= end_min:
            return True, block.get("reason", "Blocked")
    return False, ""


def is_assistant_available(
    assistant_name: str,
    check_in_time: Any,
    check_out_time: Any,
    df_schedule: pd.DataFrame,
    exclude_row_id: Optional[str] = None,
    punch_map: Optional[dict] = None,
    time_blocks: Optional[list] = None,
    weekly_off_set: Optional[set] = None,
    today_str: Optional[str] = None,
) -> tuple[bool, str]:
    if not assistant_name:
        return False, "No assistant specified"
    assist_upper = str(assistant_name).strip().upper()

    # Punch check
    if punch_map is not None:
        pdata = punch_map.get(assist_upper, {})
        punch_in = pdata.get("punch_in", "")
        punch_out = pdata.get("punch_out", "")
        if not punch_in:
            if weekly_off_set and assist_upper in weekly_off_set:
                return False, f"Weekly off ({now_ist().strftime('%A')})"
            return False, "Not punched in"
        if punch_out:
            return False, f"Punched out at {punch_out[:5]}"

    in_obj = coerce_to_time_obj(check_in_time)
    out_obj = coerce_to_time_obj(check_out_time)
    if in_obj is None or out_obj is None:
        return True, ""

    check_in_min = in_obj.hour * 60 + in_obj.minute
    check_out_min = out_obj.hour * 60 + out_obj.minute
    if check_out_min < check_in_min:
        check_out_min += 1440

    if time_blocks and today_str:
        blocked, reason = is_blocked_by_time_block(assist_upper, check_in_min, check_out_min, time_blocks, today_str)
        if blocked:
            return False, reason

    schedule = get_assistant_schedule(assist_upper, df_schedule)
    for appt in schedule:
        if exclude_row_id and str(appt.get("row_id", "")).strip() == str(exclude_row_id).strip():
            continue
        appt_in = coerce_to_time_obj(appt.get("in_time"))
        appt_out = coerce_to_time_obj(appt.get("out_time"))
        if appt_in is None or appt_out is None:
            continue
        appt_in_min = appt_in.hour * 60 + appt_in.minute
        appt_out_min = appt_out.hour * 60 + appt_out.minute
        if appt_out_min < appt_in_min:
            appt_out_min += 1440
        if not (check_out_min <= appt_in_min or check_in_min >= appt_out_min):
            return False, f"With {appt.get('patient', 'patient')} ({appt_in.strftime('%H:%M')}-{appt_out.strftime('%H:%M')})"
    return True, ""


def get_assistant_status(
    assistant: str,
    df_schedule: pd.DataFrame,
    punch_map: dict,
    time_blocks: list,
    today_str: str,
    today_weekday: int,
    weekly_off_map: dict,
) -> dict[str, str]:
    from services.profiles_cache import get_department_for_assistant
    assist_upper = str(assistant).strip().upper()
    now = now_ist()
    current_min = now.hour * 60 + now.minute
    dept = get_department_for_assistant(assist_upper)

    pdata = punch_map.get(assist_upper, {})
    punch_in = pdata.get("punch_in", "")
    punch_out = pdata.get("punch_out", "")

    if not punch_in:
        off_set = {str(n).strip().upper() for n in weekly_off_map.get(today_weekday, [])}
        if assist_upper in off_set:
            return {"status": "BLOCKED", "reason": f"Weekly off ({now.strftime('%A')})", "department": dept}
        return {"status": "BLOCKED", "reason": "Not punched in", "department": dept}
    if punch_out:
        return {"status": "BLOCKED", "reason": f"Punched out at {str(punch_out)[:5]}", "department": dept}

    current_time = now.time().replace(second=0, microsecond=0)
    blocked, reason = is_blocked_by_time_block_point(assist_upper, current_time, time_blocks, today_str)
    if blocked:
        return {"status": "BLOCKED", "reason": reason, "department": dept}

    schedule = get_assistant_schedule(assist_upper, df_schedule)
    for appt in schedule:
        s = str(appt.get("status", "")).upper()
        appt_in = coerce_to_time_obj(appt.get("in_time"))
        appt_out = coerce_to_time_obj(appt.get("out_time"))
        if "ON GOING" in s or "ONGOING" in s:
            return {"status": "BUSY", "reason": f"With {appt.get('patient', 'patient')}", "department": dept}
        if (appt_in is None or appt_out is None) and "ARRIVED" in s:
            return {"status": "BUSY", "reason": f"With {appt.get('patient', 'patient')}", "department": dept}
        if appt_in and appt_out:
            in_m = appt_in.hour * 60 + appt_in.minute
            out_m = appt_out.hour * 60 + appt_out.minute
            if out_m < in_m:
                out_m += 1440
            if in_m <= current_min <= out_m:
                return {"status": "BUSY", "reason": f"With {appt.get('patient', 'patient')}", "department": dept}

    return {"status": "FREE", "reason": "Available", "department": dept}


def get_all_assistant_statuses(
    df_schedule: pd.DataFrame,
    punch_map: dict,
    time_blocks: list,
    today_str: str,
    today_weekday: int,
    weekly_off_map: dict,
    assistants: Optional[list] = None,
) -> dict[str, dict[str, str]]:
    from services.profiles_cache import get_all_assistants
    if assistants is None:
        assistants = get_all_assistants()
    return {
        a.upper(): get_assistant_status(a, df_schedule, punch_map, time_blocks, today_str, today_weekday, weekly_off_map)
        for a in assistants
    }


def serialize_time_blocks(blocks: list[dict]) -> list[dict]:
    out = []
    for b in blocks or []:
        try:
            start_obj = coerce_to_time_obj(b.get("start_time"))
            end_obj = coerce_to_time_obj(b.get("end_time"))
            out.append({
                "assistant": str(b.get("assistant", "")).strip().upper(),
                "date": str(b.get("date", "")).strip(),
                "reason": str(b.get("reason", "Backend Work")).strip() or "Backend Work",
                "start_time": time_to_hhmm(start_obj),
                "end_time": time_to_hhmm(end_obj),
            })
        except Exception:
            continue
    return out


def deserialize_time_blocks(value) -> list[dict]:
    if value is None or value == "":
        return []
    raw = value
    if isinstance(value, str):
        try:
            raw = json.loads(value)
        except Exception:
            return []
    if not isinstance(raw, list):
        return []
    out = []
    for b in raw:
        if not isinstance(b, dict):
            continue
        assistant = str(b.get("assistant", "")).strip().upper()
        date = str(b.get("date", "")).strip()
        reason = str(b.get("reason", "Backend Work")).strip() or "Backend Work"
        start_obj = coerce_to_time_obj(b.get("start_time"))
        end_obj = coerce_to_time_obj(b.get("end_time"))
        if not assistant or not date or start_obj is None or end_obj is None:
            continue
        out.append({"assistant": assistant, "date": date, "reason": reason, "start_time": start_obj, "end_time": end_obj})
    return out

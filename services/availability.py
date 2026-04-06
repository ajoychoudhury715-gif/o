# services/availability.py
"""Assistant availability: punch checks, time blocks, schedule conflicts."""

from __future__ import annotations
from datetime import datetime, time as time_type, timedelta
from typing import Any, Optional
import json
import pandas as pd

from services.utils import coerce_to_time_obj, time_to_minutes, now_ist, is_blank, time_to_hhmm, parse_iso_ts
from config.constants import TERMINAL_STATUSES
from services.schedule_ops import filter_schedule_for_date, is_status_ongoing, normalize_status


def _combine_today_datetime(today_str: str, value) -> Optional[datetime]:
    time_obj = coerce_to_time_obj(value)
    if time_obj is None:
        return None
    parsed = pd.to_datetime(today_str, errors="coerce")
    target_day = parsed.date() if pd.notna(parsed) else now_ist().date()
    return datetime.combine(target_day, time_obj).replace(tzinfo=now_ist().tzinfo)


def _duration_minutes_between(start_dt: Optional[datetime], end_dt: Optional[datetime]) -> Optional[int]:
    if start_dt is None or end_dt is None:
        return None
    return max(0, int((end_dt - start_dt).total_seconds() // 60))


def _build_appointment_times(appt: dict[str, Any], today_str: str) -> tuple[Optional[datetime], Optional[datetime], Optional[datetime]]:
    start_dt = (
        parse_iso_ts(appt.get("actual_start_at"))
        or parse_iso_ts(appt.get("status_changed_at"))
        or _combine_today_datetime(today_str, appt.get("in_time"))
    )
    scheduled_end = _combine_today_datetime(today_str, appt.get("out_time"))
    actual_end = parse_iso_ts(appt.get("actual_end_at"))

    if start_dt and scheduled_end and scheduled_end < start_dt:
        scheduled_end += timedelta(days=1)
    if start_dt and actual_end and actual_end < start_dt:
        actual_end += timedelta(days=1)
    return start_dt, scheduled_end, actual_end


def _get_time_block_intervals(
    assistant_upper: str,
    time_blocks: list[dict],
    today_str: str,
) -> list[dict[str, Any]]:
    intervals: list[dict[str, Any]] = []
    for block in time_blocks or []:
        if str(block.get("date", "")).strip() != today_str:
            continue
        if str(block.get("assistant", "")).strip().upper() != assistant_upper:
            continue
        start_dt = _combine_today_datetime(today_str, block.get("start_time"))
        end_dt = _combine_today_datetime(today_str, block.get("end_time"))
        if start_dt is None or end_dt is None:
            continue
        if end_dt < start_dt:
            end_dt += timedelta(days=1)
        intervals.append(
            {
                "reason": str(block.get("reason", "Blocked")).strip() or "Blocked",
                "start_dt": start_dt,
                "end_dt": end_dt,
            }
        )
    return sorted(intervals, key=lambda item: item.get("start_dt") or now_ist())


def _extend_expected_end(
    base_end: Optional[datetime],
    intervals: list[dict[str, Any]],
) -> Optional[datetime]:
    if base_end is None:
        return None

    expected_end = base_end
    changed = True
    while changed:
        changed = False
        for interval in intervals or []:
            start_dt = interval.get("start_dt")
            end_dt = interval.get("end_dt")
            if start_dt is None or end_dt is None:
                continue
            if start_dt <= expected_end and end_dt > expected_end:
                expected_end = end_dt
                changed = True
    return expected_end


def _get_current_time_block_stretch(
    assistant_upper: str,
    time_blocks: list[dict],
    today_str: str,
) -> Optional[dict[str, Any]]:
    intervals = _get_time_block_intervals(assistant_upper, time_blocks, today_str)
    current_time = now_ist()
    active = [
        interval
        for interval in intervals
        if interval.get("start_dt") is not None
        and interval.get("end_dt") is not None
        and interval["start_dt"] <= current_time <= interval["end_dt"]
    ]
    if not active:
        return None

    stretch_start = min(interval["start_dt"] for interval in active)
    stretch_end = max(interval["end_dt"] for interval in active)
    changed = True
    while changed:
        changed = False
        for interval in intervals:
            start_dt = interval.get("start_dt")
            end_dt = interval.get("end_dt")
            if start_dt is None or end_dt is None:
                continue
            if start_dt <= stretch_end and end_dt >= stretch_start:
                new_start = min(stretch_start, start_dt)
                new_end = max(stretch_end, end_dt)
                if new_start != stretch_start or new_end != stretch_end:
                    stretch_start = new_start
                    stretch_end = new_end
                    changed = True

    reasons = []
    for interval in intervals:
        start_dt = interval.get("start_dt")
        end_dt = interval.get("end_dt")
        reason = str(interval.get("reason", "Blocked")).strip() or "Blocked"
        if start_dt is None or end_dt is None:
            continue
        if start_dt <= stretch_end and end_dt >= stretch_start and reason not in reasons:
            reasons.append(reason)

    if len(reasons) == 1:
        reason_label = reasons[0]
    else:
        reason_label = f"{len(reasons)} active blocks"

    return {
        "reason": reason_label,
        "start_dt": stretch_start,
        "end_dt": stretch_end,
        "intervals": intervals,
    }


def _get_active_duty_run_state(assistant_upper: str) -> Optional[dict[str, Any]]:
    from data.duty_repo import get_active_duty_run

    active_run = get_active_duty_run(assistant_upper)
    if not active_run:
        return None

    current_time = now_ist()
    started_at = parse_iso_ts(active_run.get("started_at"))
    due_at = parse_iso_ts(active_run.get("due_at"))
    if started_at is None and due_at is None:
        return None

    if started_at is None:
        try:
            est_minutes = max(0, int(float(str(active_run.get("est_minutes", 0) or 0))))
        except Exception:
            est_minutes = 0
        started_at = (due_at or current_time) - timedelta(minutes=est_minutes)

    if due_at is None:
        due_at = current_time
    if due_at < started_at:
        due_at = started_at

    return {
        "name": str(active_run.get("duty_name") or active_run.get("duty_id") or "Duty").strip(),
        "op": str(active_run.get("op", "") or "").strip(),
        "start_dt": started_at,
        "end_dt": due_at,
    }


def _latest_completed_engagement_end(
    schedule: list[dict[str, Any]],
    assistant_upper: str,
    time_blocks: list[dict],
    today_str: str,
    fallback_start: Optional[datetime] = None,
) -> Optional[datetime]:
    ends: list[datetime] = []
    current_time = now_ist()

    for appt in schedule:
        status = normalize_status(appt.get("status", ""))
        if status not in TERMINAL_STATUSES:
            continue
        _, scheduled_end, actual_end = _build_appointment_times(appt, today_str)
        end_dt = actual_end or scheduled_end
        if end_dt and end_dt <= current_time:
            ends.append(end_dt)

    for block in time_blocks or []:
        if str(block.get("date", "")).strip() != today_str:
            continue
        if str(block.get("assistant", "")).strip().upper() != assistant_upper:
            continue
        end_dt = _combine_today_datetime(today_str, block.get("end_time"))
        if end_dt and end_dt <= current_time:
            ends.append(end_dt)

    if fallback_start is not None:
        ends.append(fallback_start)
    return max(ends) if ends else None


def get_assistant_schedule(
    assistant_name: str,
    df_schedule: pd.DataFrame,
    include_terminal: bool = False,
) -> list[dict[str, Any]]:
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
                    status = normalize_status(row.get("STATUS", ""))
                    if not include_terminal and status in TERMINAL_STATUSES:
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
                        "actual_start_at": row.get("ACTUAL_START_AT", ""),
                        "actual_end_at": row.get("ACTUAL_END_AT", ""),
                        "status_changed_at": row.get("STATUS_CHANGED_AT", ""),
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
) -> dict[str, Any]:
    from services.profiles_cache import get_department_for_assistant
    assist_upper = str(assistant).strip().upper()
    now = now_ist()
    dept = get_department_for_assistant(assist_upper)

    pdata = punch_map.get(assist_upper, {})
    punch_in = pdata.get("punch_in", "")
    punch_out = pdata.get("punch_out", "")
    punch_in_dt = _combine_today_datetime(today_str, punch_in)

    if not punch_in:
        off_set = {str(n).strip().upper() for n in weekly_off_map.get(today_weekday, [])}
        if assist_upper in off_set:
            return {"status": "BLOCKED", "reason": f"Weekly off ({now.strftime('%A')})", "department": dept}
        return {"status": "BLOCKED", "reason": "Not punched in", "department": dept}
    if punch_out:
        return {"status": "BLOCKED", "reason": f"Punched out at {str(punch_out)[:5]}", "department": dept}

    schedule = get_assistant_schedule(
        assist_upper,
        filter_schedule_for_date(df_schedule, today_str),
        include_terminal=True,
    )
    time_block_intervals = _get_time_block_intervals(assist_upper, time_blocks, today_str)
    active_duty = _get_active_duty_run_state(assist_upper)

    live_appts = [appt for appt in schedule if is_status_ongoing(appt.get("status", ""))]
    if live_appts:
        live_entries = []
        for appt in live_appts:
            start_dt, scheduled_end, _ = _build_appointment_times(appt, today_str)
            predicted_end = scheduled_end or now
            if predicted_end < now:
                predicted_end = now
            live_entries.append((appt, start_dt or now, predicted_end))

        busy_since = min(entry[1] for entry in live_entries)
        expected_free_at = max(entry[2] for entry in live_entries)
        blocking_intervals = list(time_block_intervals)
        if active_duty is not None:
            blocking_intervals.append(active_duty)
        expected_free_at = _extend_expected_end(expected_free_at, blocking_intervals) or expected_free_at
        if expected_free_at < now:
            expected_free_at = now
        current_patients = [str(entry[0].get("patient", "") or "").strip() for entry in live_entries if str(entry[0].get("patient", "") or "").strip()]
        current_ops = sorted({str(entry[0].get("op", "") or "").strip() for entry in live_entries if str(entry[0].get("op", "") or "").strip()})
        if len(current_patients) == 1:
            reason = f"With {current_patients[0]}"
        else:
            reason = f"With {len(current_patients)} ongoing patients"

        return {
            "status": "BUSY",
            "reason": reason,
            "department": dept,
            "current_patient": current_patients[0] if len(current_patients) == 1 else "",
            "current_op": current_ops[0] if len(current_ops) == 1 else ", ".join(current_ops),
            "current_for_minutes": _duration_minutes_between(busy_since, now),
            "available_in_minutes": _duration_minutes_between(now, expected_free_at),
            "expected_free_at": expected_free_at,
            "current_label": "Busy For",
        }

    if active_duty:
        expected_free_at = _extend_expected_end(active_duty.get("end_dt"), time_block_intervals) or active_duty.get("end_dt")
        if expected_free_at is not None and expected_free_at < now:
            expected_free_at = now
        return {
            "status": "BLOCKED",
            "reason": f"Duty: {active_duty.get('name', 'Duty')}",
            "department": dept,
            "current_op": active_duty.get("op", ""),
            "current_for_minutes": _duration_minutes_between(active_duty.get("start_dt"), now),
            "available_in_minutes": _duration_minutes_between(now, expected_free_at),
            "expected_free_at": expected_free_at,
            "current_label": "Duty For",
        }

    current_block = _get_current_time_block_stretch(assist_upper, time_blocks, today_str)
    if current_block:
        blocked_for = _duration_minutes_between(current_block.get("start_dt"), now)
        expected_free_at = current_block.get("end_dt")
        if expected_free_at is not None and expected_free_at < now:
            expected_free_at = now
        available_in = _duration_minutes_between(now, expected_free_at)
        return {
            "status": "BLOCKED",
            "reason": current_block.get("reason", "Blocked"),
            "department": dept,
            "current_for_minutes": blocked_for,
            "available_in_minutes": available_in,
            "expected_free_at": expected_free_at,
            "current_label": "Blocked For",
        }

    free_since = _latest_completed_engagement_end(
        schedule,
        assist_upper,
        time_blocks,
        today_str,
        fallback_start=punch_in_dt,
    )
    return {
        "status": "FREE",
        "reason": "Available",
        "department": dept,
        "current_for_minutes": _duration_minutes_between(free_since, now) if free_since else None,
        "available_in_minutes": 0,
        "expected_free_at": now,
        "current_label": "Free For",
    }


def get_all_assistant_statuses(
    df_schedule: pd.DataFrame,
    punch_map: dict,
    time_blocks: list,
    today_str: str,
    today_weekday: int,
    weekly_off_map: dict,
    assistants: Optional[list] = None,
) -> dict[str, dict[str, Any]]:
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

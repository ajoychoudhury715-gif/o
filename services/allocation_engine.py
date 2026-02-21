# services/allocation_engine.py
"""Auto-allocation engine: assigns assistants to appointment slots."""

from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Optional
import pandas as pd

from services.utils import coerce_to_time_obj, is_blank, norm_name
from services.availability import is_assistant_available, get_assistant_schedule
from services.schedule_ops import get_assistant_loads
from services.profiles_cache import (
    get_profiles_cache, get_assistants_for_department,
    get_department_for_doctor, get_all_assistants,
)


def _load_alloc_config() -> dict[str, Any]:
    try:
        path = Path(__file__).parent.parent / "allocation_rules.json"
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, dict) else {}
    except Exception:
        pass
    return {}


def _get_global_cfg(config: dict) -> dict:
    g = config.get("global", {}) if isinstance(config, dict) else {}
    if not isinstance(g, dict):
        g = {}
    def _bool(v, d=False):
        if isinstance(v, bool):
            return v
        return str(v).lower() in {"1", "true", "yes", "on"} if v is not None else d
    return {
        "cross_department_fallback": _bool(g.get("cross_department_fallback", False)),
        "use_profile_role_flags": _bool(g.get("use_profile_role_flags", False)),
        "load_balance": _bool(g.get("load_balance", False)),
    }


def _get_dept_cfg(department: str, config: dict) -> dict:
    depts = config.get("departments", {}) if isinstance(config, dict) else {}
    if isinstance(depts, dict):
        for key, val in depts.items():
            if str(key).strip().upper() == department.strip().upper():
                return val if isinstance(val, dict) else {}
    return {}


def _get_free_set(df_schedule: pd.DataFrame, all_assistants: list[str]) -> set[str]:
    """Get set of assistants not currently in an active appointment."""
    from services.utils import now_ist
    now = now_ist()
    current_min = now.hour * 60 + now.minute
    free_set: set[str] = set()
    for assistant in all_assistants:
        a_upper = str(assistant).strip().upper()
        schedule = get_assistant_schedule(a_upper, df_schedule)
        busy = False
        for appt in schedule:
            s = str(appt.get("status", "")).upper()
            if "ON GOING" in s or "ONGOING" in s:
                busy = True; break
            appt_in = coerce_to_time_obj(appt.get("in_time"))
            appt_out = coerce_to_time_obj(appt.get("out_time"))
            if appt_in and appt_out:
                in_m = appt_in.hour * 60 + appt_in.minute
                out_m = appt_out.hour * 60 + appt_out.minute
                if in_m <= current_min <= out_m:
                    busy = True; break
        if not busy:
            free_set.add(a_upper)
    return free_set


def _rule_candidates(role: str, rule: dict, doctor: str, appt_hour: float, first_assigned: str) -> list[str]:
    if not isinstance(rule, dict):
        return []
    # Time overrides
    for override in (rule.get("time_override", []) or []):
        if not isinstance(override, dict):
            continue
        try:
            start = float(override.get("start_hour", 0))
            end = float(override.get("end_hour", 24))
            if start <= appt_hour < end:
                names = override.get("names", []) or []
                if names:
                    return [str(n).strip().upper() for n in names if str(n).strip()]
        except Exception:
            pass
    # Doctor-specific
    for doc_key, names in (rule.get("when_doctor_is", {}) or {}).items():
        if str(doc_key).strip().upper() == norm_name(doctor):
            if names:
                return [str(n).strip().upper() for n in names if str(n).strip()]
    # When-first-is (for SECOND)
    for first_key, names in (rule.get("when_first_is", {}) or {}).items():
        if str(first_key).strip().upper() == str(first_assigned).strip().upper():
            if names:
                return [str(n).strip().upper() for n in names if str(n).strip()]
    # Default
    defaults = rule.get("default", []) or []
    return [str(n).strip().upper() for n in defaults if str(n).strip()]


def _select_candidate(
    candidates: list[str],
    available_map: dict[str, str],
    available_order: list[str],
    already: set[str],
    load_balance: bool,
    load_map: dict[str, int],
) -> str:
    for name_upper in candidates:
        if name_upper in already:
            continue
        if name_upper in available_map:
            return available_map[name_upper]
    # No specific candidate found — pick any available
    if not candidates:
        options = [n for n in available_order if n.upper() not in already]
        if load_balance and options:
            options.sort(key=lambda n: load_map.get(n.upper(), 0))
        return options[0] if options else ""
    return ""


def allocate_for_slot(
    doctor: str,
    department: str,
    in_time: Any,
    out_time: Any,
    df_schedule: pd.DataFrame,
    exclude_row_id: Optional[str] = None,
    current_assignments: Optional[dict] = None,
    only_fill_empty: bool = False,
    punch_map: Optional[dict] = None,
    time_blocks: Optional[list] = None,
    today_str: Optional[str] = None,
) -> dict[str, str]:
    result = {"FIRST": "", "SECOND": "", "Third": ""}
    if current_assignments:
        for role in result:
            val = current_assignments.get(role, "")
            result[role] = "" if is_blank(val) else str(val).strip()

    if not doctor:
        return result
    in_obj = coerce_to_time_obj(in_time)
    out_obj = coerce_to_time_obj(out_time)
    if in_obj is None or out_obj is None:
        return result

    appt_hour = in_obj.hour + in_obj.minute / 60.0
    config = _load_alloc_config()
    global_cfg = _get_global_cfg(config)
    dept_cfg = _get_dept_cfg(department, config)
    rules = dept_cfg.get("allocation_rules", {}) if isinstance(dept_cfg, dict) else {}

    all_assistants = get_all_assistants()
    dept_assistants = get_assistants_for_department(department)
    free_set = _get_free_set(df_schedule, all_assistants)

    def get_available(asst_list: list[str]) -> tuple[list[str], dict[str, str]]:
        order, amap = [], {}
        for a in asst_list:
            a_upper = str(a).strip().upper()
            if a_upper not in free_set:
                continue
            avail, _ = is_assistant_available(
                a, in_time, out_time, df_schedule, exclude_row_id,
                punch_map=punch_map, time_blocks=time_blocks, today_str=today_str,
            )
            if avail:
                order.append(a_upper)
                amap[a_upper] = a
        return order, amap

    dept_order, dept_map = get_available(dept_assistants)
    if global_cfg["cross_department_fallback"]:
        all_order, all_map = get_available(all_assistants)
    else:
        all_order, all_map = dept_order, dept_map

    load_map = get_assistant_loads(df_schedule, exclude_row_id) if global_cfg["load_balance"] else {}
    already: set[str] = {str(v).strip().upper() for v in result.values() if v}

    for role in ["FIRST", "SECOND", "Third"]:
        if only_fill_empty and result.get(role):
            continue
        rule = rules.get(role, {}) if isinstance(rules, dict) else {}
        candidates = _rule_candidates(role, rule, doctor, appt_hour, result.get("FIRST", ""))
        chosen = _select_candidate(candidates, dept_map, dept_order, already, global_cfg["load_balance"], load_map)
        if not chosen and global_cfg["cross_department_fallback"]:
            chosen = _select_candidate(candidates, all_map, all_order, already, global_cfg["load_balance"], load_map)
        if chosen:
            result[role] = chosen
            already.add(chosen.strip().upper())

    return result


def auto_allocate_all(
    df_schedule: pd.DataFrame,
    only_fill_empty: bool = True,
    punch_map: Optional[dict] = None,
    time_blocks: Optional[list] = None,
    today_str: Optional[str] = None,
) -> tuple[pd.DataFrame, int]:
    df = df_schedule.copy()
    changed = 0
    for idx in range(len(df)):
        row = df.iloc[idx]
        doctor = str(row.get("DR.", "") or row.get("Doctor", "")).strip()
        if not doctor:
            continue
        in_time = row.get("In Time")
        out_time = row.get("Out Time")
        if coerce_to_time_obj(in_time) is None or coerce_to_time_obj(out_time) is None:
            continue
        row_id = str(row.get("REMINDER_ROW_ID", "")).strip()
        department = get_department_for_doctor(doctor)
        current = {"FIRST": row.get("FIRST", ""), "SECOND": row.get("SECOND", ""), "Third": row.get("Third", "")}
        if only_fill_empty and all(not is_blank(current[r]) for r in current):
            continue
        allocations = allocate_for_slot(
            doctor, department, in_time, out_time, df,
            exclude_row_id=row_id, current_assignments=current,
            only_fill_empty=only_fill_empty,
            punch_map=punch_map, time_blocks=time_blocks, today_str=today_str,
        )
        for role in ["FIRST", "SECOND", "Third"]:
            new_val = allocations.get(role, "")
            old_val = current.get(role, "")
            if is_blank(new_val):
                continue
            if str(new_val).strip() != str(old_val).strip() and role in df.columns:
                df.iloc[idx, df.columns.get_loc(role)] = new_val
                changed += 1
    return df, changed

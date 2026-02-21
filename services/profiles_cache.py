# services/profiles_cache.py
"""Profiles cache: derived assistant/doctor lookup maps from profile DataFrames."""

from __future__ import annotations
from typing import Any
import json
from pathlib import Path

from services.utils import norm_name, unique_preserve_order, is_blank
from config.constants import DEFAULT_DEPARTMENTS


def _parse_weekly_off_days(value: Any) -> list[int]:
    WEEKDAY_MAP = {
        "MON": 0, "MONDAY": 0,
        "TUE": 1, "TUESDAY": 1,
        "WED": 2, "WEDNESDAY": 2,
        "THU": 3, "THURSDAY": 3,
        "FRI": 4, "FRIDAY": 4,
        "SAT": 5, "SATURDAY": 5,
        "SUN": 6, "SUNDAY": 6,
    }
    if not value or is_blank(value):
        return []
    s = str(value).strip()
    out = []
    for part in s.split(","):
        part = part.strip().upper()
        if not part:
            continue
        if part in WEEKDAY_MAP:
            out.append(WEEKDAY_MAP[part])
        else:
            try:
                idx = int(part)
                if 0 <= idx <= 6:
                    out.append(idx)
            except Exception:
                pass
    return out


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


def build_profiles_cache(assistants_df, doctors_df) -> dict[str, Any]:
    """Build lookup maps from loaded DataFrames."""
    import pandas as pd

    config = _load_alloc_config()
    depts_cfg = config.get("departments", {}) if isinstance(config, dict) else {}

    config_doctor_map: dict[str, str] = {}
    config_assistant_map: dict[str, str] = {}
    dept_list: list[str] = []

    for dept, data in depts_cfg.items():
        dept_upper = str(dept).strip().upper()
        if dept_upper and dept_upper not in dept_list:
            dept_list.append(dept_upper)
        if not isinstance(data, dict):
            continue
        for name in data.get("doctors", []) or []:
            key = norm_name(name)
            if key and key not in config_doctor_map:
                config_doctor_map[key] = dept_upper
        for name in data.get("assistants", []) or []:
            key = norm_name(name)
            if key and key not in config_assistant_map:
                config_assistant_map[key] = dept_upper

    if not dept_list:
        for dept in DEFAULT_DEPARTMENTS:
            dept_upper = dept.upper()
            if dept_upper not in dept_list:
                dept_list.append(dept_upper)

    assistants_list: list[str] = []
    assistant_dept_map: dict[str, str] = {}
    assistant_prefs: dict[str, dict] = {}
    assistants_by_dept: dict[str, list[str]] = {}
    weekly_off_map: dict[int, list[str]] = {i: [] for i in range(7)}

    if assistants_df is not None and not assistants_df.empty:
        for _, row in assistants_df.iterrows():
            name = str(row.get("name", "")).strip().upper()
            if not name:
                continue
            status = str(row.get("status", "")).strip().upper()
            if status and status not in ("", "ACTIVE"):
                continue
            assistants_list.append(name)
            key = norm_name(name)
            dept = str(row.get("department", "")).strip().upper()
            if not dept:
                dept = config_assistant_map.get(key, "SHARED")
            if not dept:
                dept = "SHARED"
            assistant_dept_map[key] = dept
            assistants_by_dept.setdefault(dept, [])
            if name not in assistants_by_dept[dept]:
                assistants_by_dept[dept].append(name)
            assistant_prefs[key] = {
                "FIRST": row.get("pref_first", ""),
                "SECOND": row.get("pref_second", ""),
                "Third": row.get("pref_third", ""),
            }
            try:
                for idx in _parse_weekly_off_days(row.get("weekly_off", "")):
                    weekly_off_map[idx].append(name)
            except Exception:
                pass

    doctors_list: list[str] = []
    doctor_dept_map: dict[str, str] = {}

    if doctors_df is not None and not doctors_df.empty:
        for _, row in doctors_df.iterrows():
            name = str(row.get("name", "")).strip().upper()
            if not name:
                continue
            status = str(row.get("status", "")).strip().upper()
            if status and status not in ("", "ACTIVE"):
                continue
            doctors_list.append(name)
            key = norm_name(name)
            dept = str(row.get("department", "")).strip().upper()
            if not dept:
                dept = config_doctor_map.get(key, "")
            doctor_dept_map[key] = dept

    return {
        "assistants_list": assistants_list,
        "doctors_list": doctors_list,
        "assistant_dept_map": assistant_dept_map,
        "doctor_dept_map": doctor_dept_map,
        "assistant_prefs": assistant_prefs,
        "assistants_by_dept": assistants_by_dept,
        "weekly_off_map": weekly_off_map,
        "all_departments": dept_list or list(DEFAULT_DEPARTMENTS.keys()),
    }


def get_profiles_cache(cache_bust: int = 0) -> dict[str, Any]:
    """Get the profiles cache from session state, rebuilding if stale."""
    import streamlit as st
    cached = st.session_state.get("profiles_cache", {})
    if (
        isinstance(cached, dict)
        and cached.get("cache_bust") == cache_bust
        and cached.get("assistants_list") is not None
    ):
        return cached
    from data.profile_repo import load_assistants, load_doctors
    assistants_df = load_assistants(cache_bust)
    doctors_df = load_doctors(cache_bust)
    result = build_profiles_cache(assistants_df, doctors_df)
    result["cache_bust"] = cache_bust
    st.session_state.profiles_cache = result
    return result


def get_all_assistants(cache_bust: int = 0) -> list[str]:
    return get_profiles_cache(cache_bust).get("assistants_list", [])


def get_all_doctors(cache_bust: int = 0) -> list[str]:
    return get_profiles_cache(cache_bust).get("doctors_list", [])


def get_department_for_assistant(name: str, cache_bust: int = 0) -> str:
    key = norm_name(name)
    return get_profiles_cache(cache_bust).get("assistant_dept_map", {}).get(key, "SHARED")


def get_department_for_doctor(name: str, cache_bust: int = 0) -> str:
    key = norm_name(name)
    return get_profiles_cache(cache_bust).get("doctor_dept_map", {}).get(key, "")


def get_assistants_for_department(department: str, cache_bust: int = 0) -> list[str]:
    dept_upper = str(department).strip().upper()
    cache = get_profiles_cache(cache_bust)
    dept_list = cache.get("assistants_by_dept", {}).get(dept_upper, [])
    if dept_list:
        return dept_list
    # Fallback to allocation_rules.json
    try:
        cfg = _load_alloc_config()
        depts = cfg.get("departments", {})
        for key, val in depts.items():
            if str(key).strip().upper() == dept_upper and isinstance(val, dict):
                names = val.get("assistants", [])
                if names:
                    return unique_preserve_order(names)
    except Exception:
        pass
    return cache.get("assistants_list", [])

# state/session.py
"""Centralised session state: schema, initialisation, typed accessors."""

from __future__ import annotations
from typing import Any

# ── State Schema ──────────────────────────────────────────────────────────────
STATE_SCHEMA: dict[str, Any] = {
    # Navigation
    "nav_category": "Scheduling",
    "nav_sched": "Full Schedule",
    "nav_assistants": "Manage Profiles",
    "nav_doctors": "Manage Profiles",
    "nav_admin": "Storage/Backup",

    # User / auth
    "user_role": None,
    "current_user": None,
    "current_user_id": None,
    "show_reset_password": False,
    "allowed_functions": [],
    "permissions_loaded_for": None,

    # Schedule data
    "df": None,
    "unsaved_df": None,
    "pending_changes": False,
    "pending_changes_reason": "",

    # Save / conflict
    "is_saving": False,
    "auto_save_enabled": False,
    "save_debounce_seconds": 2,
    "last_save_at": 0.0,
    "last_saved_hash": None,
    "loaded_save_version": None,
    "loaded_save_at": None,
    "save_conflict": None,
    "enable_conflict_checks": True,
    "unsaved_df_version": 0,

    # Supabase connectivity
    "supabase_ready": False,
    "supabase_ready_at": 0.0,

    # Schedule UI
    "view_mode": "Card",
    "selected_date": None,
    "schedule_backup_key": None,
    "schedule_backup_cache": None,

    # Profiles cache
    "profiles_cache": {},
    "profiles_cache_bust": 0,

    # Time blocks
    "time_blocks": [],

    # Reminders
    "reminder_dismissed_ids": [],
    "reminder_snooze_map": {},

    # Duty widget
    "duty_current_assistant": None,
    "duty_active_run": None,
    "duty_run_start_time": None,

    # Punch system
    "punch_map_cache": None,
    "punch_map_cached_at": 0.0,

    # Attendance page
    "attendance_date_filter": None,
    "attendance_assistant_filter": None,
}


def init_session_state() -> None:
    """Initialise all session state keys with defaults (idempotent)."""
    import streamlit as st
    for key, default in STATE_SCHEMA.items():
        if key not in st.session_state:
            st.session_state[key] = default


def get_state(key: str, default: Any = None) -> Any:
    import streamlit as st
    return st.session_state.get(key, default)


def set_state(key: str, value: Any) -> None:
    import streamlit as st
    st.session_state[key] = value


def bust_profiles_cache() -> None:
    """Increment cache_bust to force profile reload on next access."""
    import streamlit as st
    st.session_state.profiles_cache_bust = int(st.session_state.get("profiles_cache_bust", 0)) + 1
    st.session_state.profiles_cache = {}

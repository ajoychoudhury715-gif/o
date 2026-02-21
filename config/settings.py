# config/settings.py
"""Central configuration: Supabase, Excel, timezone, feature flags."""

import os
from datetime import timezone, timedelta
from pathlib import Path

# ── Timezone ──────────────────────────────────────────────────────────────────
IST = timezone(timedelta(hours=5, minutes=30))

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent
EXCEL_PATH = BASE_DIR / "Putt Allotment.xlsx"
ALLOCATION_RULES_PATH = BASE_DIR / "allocation_rules.json"

# ── Storage backend ───────────────────────────────────────────────────────────
USE_SUPABASE = True  # Set False to force Excel-only mode

# ── Supabase table names ───────────────────────────────────────────────────────
SUPABASE_SCHEDULE_TABLE = "tdb_allotment_state"
SUPABASE_SCHEDULE_ROW_ID = "main"
SUPABASE_PROFILE_TABLE = "profiles"
SUPABASE_ATTENDANCE_TABLE = "assistant_attendance"
SUPABASE_DUTIES_MASTER_TABLE = "duties_master"
SUPABASE_DUTY_ASSIGNMENTS_TABLE = "duty_assignments"
SUPABASE_DUTY_RUNS_TABLE = "duty_runs"
SUPABASE_PATIENTS_TABLE = "patients"

# ── Excel sheet names ─────────────────────────────────────────────────────────
EXCEL_SCHEDULE_SHEET = "Sheet1"
EXCEL_ASSISTANTS_SHEET = "Assistants"
EXCEL_DOCTORS_SHEET = "Doctors"
EXCEL_ATTENDANCE_SHEET = "Assistants_Attendance"
EXCEL_DUTIES_MASTER_SHEET = "Duties_Master"
EXCEL_DUTY_ASSIGNMENTS_SHEET = "Duty_Assignments"
EXCEL_DUTY_RUNS_SHEET = "Duty_Runs"
EXCEL_PATIENTS_SHEET = "Patients"

# ── Performance TTLs ──────────────────────────────────────────────────────────
SUPABASE_CHECK_TTL_SECONDS = 60
PROFILE_CACHE_TTL_SECONDS = 120
SCHEDULE_CACHE_TTL_SECONDS = 60


def get_supabase_config():
    """
    Return (url, key, schedule_table, row_id, profile_table) from
    Streamlit secrets or environment variables.
    Returns (None, None, ...) if not configured.
    """
    url = ""
    key = ""
    service_key = ""
    schedule_table = SUPABASE_SCHEDULE_TABLE
    row_id = SUPABASE_SCHEDULE_ROW_ID
    profile_table = SUPABASE_PROFILE_TABLE

    try:
        import streamlit as st
        if hasattr(st, "secrets"):
            sec = st.secrets
            sb = sec.get("supabase", None)
            if sb is not None and hasattr(sb, "get"):
                url = str(sb.get("url", "") or "").strip() or url
                key = str(sb.get("key", "") or "").strip() or key
                service_key = str(sb.get("service_role_key", "") or "").strip()
                schedule_table = str(sb.get("table", schedule_table) or schedule_table).strip() or schedule_table
                row_id = str(sb.get("row_id", row_id) or row_id).strip() or row_id
                profile_table = str(sb.get("profile_table", profile_table) or profile_table).strip() or profile_table
            url = str(sec.get("supabase_url", "") or "").strip() or url
            key = str(sec.get("supabase_key", "") or "").strip() or key
            service_key = str(sec.get("supabase_service_role_key", "") or "").strip() or service_key
            schedule_table = str(sec.get("supabase_table", schedule_table) or schedule_table).strip() or schedule_table
            row_id = str(sec.get("supabase_row_id", row_id) or row_id).strip() or row_id
            profile_table = str(sec.get("supabase_profile_table", profile_table) or profile_table).strip() or profile_table
    except Exception:
        pass

    url = url or os.getenv("SUPABASE_URL", "").strip()
    key = key or os.getenv("SUPABASE_KEY", "").strip()
    service_key = service_key or os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()

    if not url or not key:
        return None, None, schedule_table, row_id, profile_table

    effective_key = service_key or key
    return url, effective_key, schedule_table, row_id, profile_table

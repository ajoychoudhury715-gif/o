# config/constants.py
"""All hardcoded constants: colors, status options, column definitions."""

from typing import Any

# ── UI Color Palette (Medical Blue Glassmorphism) ─────────────────────────────
COLORS = {
    "bg_primary": "#f8fafc",
    "bg_secondary": "#f1f5f9",
    "bg_card": "rgba(255, 255, 255, 0.7)",
    "text_primary": "#1e293b",
    "text_secondary": "#64748b",
    "button_bg": "#2563eb",
    "button_text": "#ffffff",
    "accent": "#3b82f6",
    "accent_primary": "#2563eb",
    "accent_secondary": "#3b82f6",
    "success": "#10b981",
    "warning": "#f59e0b",
    "danger": "#ef4444",
    "info": "#0ea5e9",
    "glass_bg": "rgba(255, 255, 255, 0.25)",
    "glass_border": "rgba(255, 255, 255, 0.18)",
    "glass_shadow": "0 8px 32px 0 rgba(37, 99, 235, 0.15)",
    "backdrop_blur": "blur(16px)",
}

# ── Patient Status Options ────────────────────────────────────────────────────
STATUS_OPTIONS = [
    "PENDING",
    "ARRIVED",
    "ON GOING",
    "DONE",
    "CANCELLED",
]

STATUS_COLORS = {
    "PENDING":   "#94a3b8",
    "WAITING":   "#f59e0b",
    "ARRIVING":  "#3b82f6",
    "ARRIVED":   "#8b5cf6",
    "ON GOING":  "#10b981",
    "DONE":      "#6b7280",
    "COMPLETED": "#6b7280",
    "CANCELLED": "#ef4444",
    "SHIFTED":   "#f97316",
    "LATE":      "#ef4444",
}

TERMINAL_STATUSES = {"DONE", "COMPLETED", "CANCELLED", "SHIFTED"}

# ── Schedule Columns ──────────────────────────────────────────────────────────
SCHEDULE_COLUMNS = [
    "DATE", "Patient ID", "Patient Name", "In Time", "Out Time", "Procedure", "DR.",
    "FIRST", "SECOND", "Third", "CASE PAPER", "OP",
    "SUCTION", "CLEANING", "STATUS", "REMINDER_ROW_ID",
    "REMINDER_SNOOZE_UNTIL", "REMINDER_DISMISSED",
    "STATUS_CHANGED_AT", "ACTUAL_START_AT", "ACTUAL_END_AT", "STATUS_LOG",
]

# ── Profile Columns ───────────────────────────────────────────────────────────
PROFILE_COLUMNS = [
    "profile_id", "kind", "name", "role", "department",
    "phone", "email", "experience", "weekly_off", "notes",
    "is_active", "specialisation", "reg_number",
    "can_first", "can_second", "can_third",
]

# ── Attendance Columns ────────────────────────────────────────────────────────
ATTENDANCE_COLUMNS = ["DATE", "ASSISTANT", "PUNCH IN", "PUNCH OUT"]

# ── Duty Columns ──────────────────────────────────────────────────────────────
DUTIES_MASTER_COLUMNS = ["id", "name", "description", "frequency", "est_minutes", "active"]
DUTY_ASSIGNMENTS_COLUMNS = ["id", "duty_id", "assistant", "op", "est_minutes", "active"]
DUTY_RUNS_COLUMNS = ["id", "date", "assistant", "duty_id", "status", "started_at", "due_at", "ended_at", "est_minutes", "op"]

# ── OP Rooms ──────────────────────────────────────────────────────────────────
OP_ROOMS = ["OP1", "OP2", "OP3", "OP4"]

# ── Weekday names ─────────────────────────────────────────────────────────────
WEEKDAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# ── Default departments (fallback when profiles not loaded) ────────────────────
DEFAULT_DEPARTMENTS: dict[str, dict[str, Any]] = {
    "PROSTHO": {"doctors": [], "assistants": []},
    "ENDO":    {"doctors": [], "assistants": []},
}

DEFAULT_WEEKLY_OFF: dict[int, list[str]] = {i: [] for i in range(7)}

# ── Navigation structure ──────────────────────────────────────────────────────
NAV_STRUCTURE = {
    "Scheduling":     ["Full Schedule", "Schedule by OP", "Ongoing", "Upcoming"],
    "Assistants":     ["Manage Profiles", "My Workload", "Availability", "Auto-Allocation", "Workload", "Attendance"],
    "Doctors":        ["Manage Profiles", "My Workload", "Overview", "Summary", "Per-Doctor Schedule", "Week Off"],
    "Admin/Settings": ["User Management", "Storage & Backup", "Notifications", "Duties Manager"],
}

# ── Role-based navigation ─────────────────────────────────────────────────────
ROLE_NAV = {
    "admin": NAV_STRUCTURE,  # Full access to all categories
    "frontdesk": {
        "Scheduling":     ["Full Schedule", "Schedule by OP", "Ongoing", "Upcoming"],
        "Assistants":     ["Attendance"],
        "Doctors":        ["Week Off"],
    },
    "assistant": {
        "Scheduling":     ["Full Schedule", "Ongoing", "Upcoming"],
        "Assistants":     ["My Workload", "Attendance"],
    },
    "doctor": {
        "Doctors":        ["My Workload", "Overview"],
    },
}

NAV_ICONS = {
    "Scheduling":     "📅",
    "Assistants":     "👥",
    "Doctors":        "🩺",
    "Admin/Settings": "⚙️",
}

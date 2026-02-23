# app.py
"""THE DENTAL BOND — Entry point."""

from __future__ import annotations
import streamlit as st

# ── Page config (must be first Streamlit call) ─────────────────────────────────
st.set_page_config(
    page_title="THE DENTAL BOND",
    page_icon="🦷",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Imports (after set_page_config) ───────────────────────────────────────────
from state.session import init_session_state
from components.theme import inject_global_css
from components.sidebar import render_sidebar
from config.constants import NAV_STRUCTURE
from data.auth_repo import ensure_admin_exists
from data.auth_repo import parse_login_token, get_active_user_by_username


def _get_auth_query_param() -> str:
    try:
        raw = st.query_params.get("auth", "")
        if isinstance(raw, list):
            return str(raw[0] if raw else "").strip()
        return str(raw or "").strip()
    except Exception:
        return ""


def _set_auth_query_param(token: str) -> None:
    try:
        if token:
            st.query_params["auth"] = token
        else:
            if "auth" in st.query_params:
                del st.query_params["auth"]
    except Exception:
        # Ignore query param persistence failures; login still works in-session.
        pass


def _restore_auth_from_query_param() -> None:
    """Restore login state after browser refresh using signed query token."""
    if st.session_state.get("user_role") and st.session_state.get("current_user"):
        return
    token = _get_auth_query_param()
    if not token:
        return
    claims = parse_login_token(token)
    if not claims:
        _set_auth_query_param("")
        return

    user = get_active_user_by_username(claims.get("username"))
    if not user:
        _set_auth_query_param("")
        return

    # Enforce DB role to avoid trusting token payload blindly.
    db_role = str(user.get("role", "") or "").strip()
    token_role = str(claims.get("role", "") or "").strip()
    if not db_role or db_role != token_role:
        _set_auth_query_param("")
        return

    st.session_state.current_user = user.get("username")
    st.session_state.user_role = db_role


def main() -> None:
    # Initialise all session state variables
    init_session_state()

    # Inject global CSS theme
    inject_global_css()

    # Ensure default admin account exists (on first run)
    ensure_admin_exists()

    # Restore auth on browser refresh (if signed token exists).
    _restore_auth_from_query_param()

    # Login gate: if not authenticated, show login or reset password page and stop
    if not st.session_state.get("user_role"):
        if st.session_state.get("show_reset_password"):
            from pages.auth.reset_password import render as render_reset
            render_reset()
        else:
            from pages.auth.login import render as render_login
            render_login()
        st.stop()

    # Load schedule into session state if not already loaded
    _ensure_schedule_loaded()

    df = st.session_state.get("df")

    # Render sidebar (navigation + punch widget + duties + save controls + reminders)
    render_sidebar(df)

    # Route to the correct page
    _route()


def _ensure_schedule_loaded() -> None:
    """Load schedule from storage if not yet in session state."""
    if st.session_state.get("df") is not None:
        return
    try:
        from data.schedule_repo import load_schedule
        from services.schedule_ops import ensure_schedule_columns, ensure_row_ids, add_computed_columns
        df = load_schedule()
        df = ensure_schedule_columns(df)
        df = ensure_row_ids(df)
        df = add_computed_columns(df)
        st.session_state.df = df
    except Exception as e:
        st.error(f"Failed to load schedule: {e}")
        import pandas as pd
        from services.schedule_ops import ensure_schedule_columns
        st.session_state.df = ensure_schedule_columns(pd.DataFrame())


def _route() -> None:
    """Determine current page from session state and render it."""
    category = st.session_state.get("nav_category", "Scheduling")

    sub_key_map = {
        "Scheduling": "nav_sched",
        "Assistants": "nav_assistants",
        "Doctors": "nav_doctors",
        "Admin/Settings": "nav_admin",
    }
    sub_key = sub_key_map.get(category, "nav_sched")
    sub_views = NAV_STRUCTURE.get(category, [])
    current_view = st.session_state.get(sub_key, sub_views[0] if sub_views else "")

    # Scheduling pages
    if category == "Scheduling":
        if current_view == "Full Schedule":
            from pages.scheduling.full_schedule import render
        elif current_view == "Schedule by OP":
            from pages.scheduling.schedule_by_op import render
        elif current_view == "Ongoing":
            from pages.scheduling.ongoing import render
        elif current_view == "Upcoming":
            from pages.scheduling.upcoming import render
        else:
            from pages.scheduling.full_schedule import render

    # Assistants pages
    elif category == "Assistants":
        if current_view == "Manage Profiles":
            from pages.assistants.manage_profiles import render
        elif current_view == "Availability":
            from pages.assistants.availability import render
        elif current_view == "Auto-Allocation":
            from pages.assistants.auto_allocation import render

        elif current_view == "Workload":
            from pages.assistants.workload import render
        elif current_view == "Attendance":
            from pages.assistants.attendance import render
        else:
            from pages.assistants.manage_profiles import render

    # Doctors pages
    elif category == "Doctors":
        if current_view == "Manage Profiles":
            from pages.doctors.manage_profiles import render
        elif current_view == "Overview":
            from pages.doctors.overview import render
        elif current_view == "Summary":
            from pages.doctors.summary import render
        elif current_view == "Per-Doctor Schedule":
            from pages.doctors.per_doctor_schedule import render
        else:
            from pages.doctors.manage_profiles import render

    # Admin/Settings pages
    elif category == "Admin/Settings":
        if current_view == "User Management":
            from pages.admin.user_management import render
        elif current_view == "Storage & Backup":
            from pages.admin.storage_backup import render
        elif current_view == "Notifications":
            from pages.admin.notifications import render
        elif current_view == "Duties Manager":
            from pages.admin.duties_manager import render
        else:
            from pages.admin.user_management import render

    else:
        from pages.scheduling.full_schedule import render

    # Render the selected page
    render()


if __name__ == "__main__":
    main()

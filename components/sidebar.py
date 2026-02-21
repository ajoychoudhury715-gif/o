# components/sidebar.py
"""Sidebar rendering: navigation, punch widget, save controls, duty/reminder widgets."""

from __future__ import annotations
import streamlit as st

from config.constants import NAV_STRUCTURE, NAV_ICONS, ROLE_NAV
from services.utils import now_ist, time_to_12h


def render_sidebar(df) -> None:
    """Render the full sidebar. df is the current schedule DataFrame."""
    with st.sidebar:
        _render_header()
        _render_navigation()
        st.divider()
        _render_punch_widget(df)
        st.divider()
        _render_duty_widget(df)
        st.divider()
        _render_save_controls(df)
        _render_reminders(df)


def _render_header() -> None:
    now = now_ist()
    st.markdown(
        '<div class="sidebar-title">🦷 THE DENTAL BOND</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="live-pill"><span class="live-dot"></span>LIVE — {time_to_12h(now.time())}</div>',
        unsafe_allow_html=True,
    )

    # User info and logout
    user_role = st.session_state.get("user_role")
    current_user = st.session_state.get("current_user")
    if user_role and current_user:
        col1, col2 = st.columns([3, 1])
        with col1:
            role_emoji = "👑" if user_role == "admin" else ("🎫" if user_role == "frontdesk" else "👨‍⚕️")
            st.caption(f"{role_emoji} {current_user.title()}")
        with col2:
            if st.button("🚪", key="btn_logout", help="Logout"):
                st.session_state.user_role = None
                st.session_state.current_user = None
                st.rerun()


def _render_navigation() -> None:
    st.markdown("**📍 Navigation**")

    # Get allowed categories based on user role
    user_role = st.session_state.get("user_role", "assistant")
    role_nav = ROLE_NAV.get(user_role, ROLE_NAV["assistant"])
    allowed_categories = list(role_nav.keys())

    # Validate and set category
    current_cat = st.session_state.get("nav_category", "Scheduling")
    if current_cat not in allowed_categories:
        current_cat = allowed_categories[0]
    st.session_state.nav_category = current_cat

    category = st.selectbox(
        "Category",
        allowed_categories,
        index=allowed_categories.index(current_cat),
        key="nav_category_select",
        label_visibility="collapsed",
    )
    st.session_state.nav_category = category

    sub_views = role_nav[category]
    # Determine current sub-view key
    sub_key_map = {
        "Scheduling": "nav_sched",
        "Assistants": "nav_assistants",
        "Doctors": "nav_doctors",
        "Admin/Settings": "nav_admin",
    }
    sub_key = sub_key_map.get(category, "nav_sched")
    current_sub = st.session_state.get(sub_key, sub_views[0] if sub_views else "")
    if current_sub not in sub_views:
        current_sub = sub_views[0] if sub_views else ""

    sub_view = st.radio(
        "View",
        sub_views,
        index=sub_views.index(current_sub) if current_sub in sub_views else 0,
        key=f"nav_radio_{category}",
        label_visibility="collapsed",
    )
    st.session_state[sub_key] = sub_view


def _render_punch_widget(df) -> None:
    """Punch in/out system."""
    st.markdown("### 👇 Punch System")
    try:
        from data.profile_repo import load_assistants
        assistants_df = load_assistants(st.session_state.get("profiles_cache_bust", 0))
        assistants = sorted(
            assistants_df["name"].dropna().astype(str).str.strip().unique().tolist()
        ) if not assistants_df.empty else []
    except Exception:
        assistants = []

    if not assistants:
        st.caption("No assistants found. Add assistants first.")
        return

    assistant = st.selectbox("Select Assistant", assistants, key="sb_assistant")
    now = now_ist()
    date_str = now.date().isoformat()
    from services.utils import coerce_to_time_obj
    now_time_obj = coerce_to_time_obj(now.time())
    now_12h = time_to_12h(now_time_obj)
    now_hhmm = now.strftime("%H:%M")  # Keep 24h version for database storage

    from data.attendance_repo import get_today_punch_map, punch_in, punch_out, reset_attendance
    punch_map = get_today_punch_map(date_str)
    pdata = punch_map.get(assistant.upper(), {})
    pin = pdata.get("punch_in", "")
    pout = pdata.get("punch_out", "")

    # Convert stored times to 12-hour format for display
    pin_12h = time_to_12h(coerce_to_time_obj(pin)) if pin else ""
    pout_12h = time_to_12h(coerce_to_time_obj(pout)) if pout else ""

    if pin and not pout:
        st.success(f"✅ PUNCHED IN at {pin_12h}")
    elif pin and pout:
        st.info(f"📋 COMPLETED • In {pin_12h} • Out {pout_12h}")
    else:
        st.warning("⚠️ Not punched in")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("✅ Punch In", width='stretch', disabled=bool(pin), key="btn_punch_in"):
            ok = punch_in(date_str, assistant, now_hhmm)
            if ok:
                st.toast(f"{assistant} punched in at {now_12h}", icon="✅")
            else:
                st.error(f"❌ Punch in failed for {assistant}")
            st.rerun()
    with c2:
        if st.button("⏹ Punch Out", width='stretch', disabled=(not pin) or bool(pout), key="btn_punch_out"):
            ok = punch_out(date_str, assistant, now_hhmm)
            if ok:
                st.toast(f"{assistant} punched out at {now_12h}", icon="⏹")
                # Remove from schedule
                from services.schedule_ops import remove_assistant_from_schedule
                from state.save_manager import maybe_save
                updated = remove_assistant_from_schedule(df, assistant)
                if updated is not None:
                    st.session_state.df = updated
                    maybe_save(updated, message=f"{assistant} removed after punch out")
            else:
                st.error(f"❌ Punch out failed for {assistant}")
            st.rerun()

    # Admin-only reset button
    if st.session_state.get("user_role") == "admin":
        with st.expander("Admin"):
            if st.button("♻️ Reset today", width='stretch', key="btn_punch_reset"):
                reset_attendance(date_str, assistant)
                st.toast("Reset done", icon="♻️")
                st.rerun()


def _render_duty_widget(df) -> None:
    """Duty timer and pending duties widget."""
    st.markdown("### 🧭 Duties")
    try:
        from data.profile_repo import load_assistants
        assistants_df = load_assistants(st.session_state.get("profiles_cache_bust", 0))
        assistants = sorted(
            assistants_df["name"].dropna().astype(str).str.strip().unique().tolist()
        ) if not assistants_df.empty else []
    except Exception:
        assistants = []

    if not assistants:
        st.caption("No assistants found.")
        return

    default_idx = 0
    if st.session_state.get("duty_current_assistant") in assistants:
        default_idx = assistants.index(st.session_state["duty_current_assistant"])

    assistant = st.selectbox("Assistant", assistants, index=default_idx, key="duty_assistant_select")
    st.session_state.duty_current_assistant = assistant

    from data.duty_repo import get_active_duty_run, get_active_duty_assignments, start_duty_run, mark_duty_done, load_duty_runs
    from services.duty_service import compute_pending_duties, format_remaining_time
    from datetime import date as date_cls
    from services.utils import parse_iso_ts

    today = date_cls.today()
    assignments = get_active_duty_assignments(assistant)
    runs = []
    try:
        runs_df = load_duty_runs()
        if not runs_df.empty:
            mask = runs_df["assistant"].astype(str).str.strip() == assistant
            runs = runs_df[mask].to_dict(orient="records")
    except Exception:
        pass

    pending = compute_pending_duties(assignments, runs, today)
    all_pending = pending["WEEKLY"] + pending["MONTHLY"]

    # Always show duty selector dropdown
    if all_pending:
        duty_options = []
        for d in all_pending:
            freq_label = "W" if d.get("frequency", "").upper() == "WEEKLY" else "M"
            label = f"{d.get('name', 'Duty')} ({freq_label})"
            duty_options.append((label, d))

        selected_label = st.selectbox(
            "Duty",
            [label for label, _ in duty_options],
            key="duty_select",
            label_visibility="collapsed"
        )
        selected_duty = next(d for label, d in duty_options if label == selected_label)
    else:
        selected_duty = None
        st.caption("✅ No pending duties")

    # Show active run timer if running
    active_run = get_active_duty_run(assistant)
    if active_run:
        due_dt = parse_iso_ts(active_run.get("due_at"))
        now = now_ist()
        if due_dt:
            total_secs = (due_dt - now).total_seconds()
            if total_secs > 0:
                # Show remaining time with better formatting
                total_mins = int(total_secs // 60)
                hours = total_mins // 60
                mins = total_mins % 60
                secs = int(total_secs % 60)

                if hours > 0:
                    countdown_display = f"{hours}h {mins}m {secs}s"
                else:
                    countdown_display = f"{mins}m {secs}s"

                st.markdown(
                    f'<div class="duty-timer-card"><div class="duty-timer-value">{countdown_display}</div>'
                    f'<div style="font-size:13px;color:#64748b;margin-top:4px;">{active_run.get("duty_name") or active_run.get("duty_id","Duty")}</div></div>',
                    unsafe_allow_html=True,
                )
            else:
                st.warning("⏰ Time's up!")

        c1, c2 = st.columns(2)
        with c1:
            if st.button("✅ Mark Done", width='stretch', key="btn_duty_done"):
                mark_duty_done(str(active_run.get("id", "")))
                st.toast("Duty completed!", icon="✅")
                st.rerun()
        with c2:
            if st.button("🔄 Refresh", width='stretch', key="btn_duty_refresh"):
                st.rerun()
    elif selected_duty:
        # Show start button if duty is selected but not running
        if st.button("▶️ Start Duty", width='stretch', key="btn_duty_start"):
            start_duty_run(assistant, selected_duty, today.isoformat())
            st.toast(f"Duty started: {selected_duty.get('name')}", icon="▶️")
            st.rerun()


def _render_save_controls(df) -> None:
    # Only show save controls to admin
    if st.session_state.get("user_role") != "admin":
        return

    st.markdown("### 💾 Save")
    st.session_state.auto_save_enabled = st.checkbox(
        "Auto-save",
        value=st.session_state.get("auto_save_enabled", False),
        key="chk_auto_save",
    )
    save_disabled = bool(st.session_state.get("is_saving")) or bool(st.session_state.get("save_conflict"))
    if st.button("💾 Save Now", width='stretch', disabled=save_disabled, key="btn_save_now"):
        from state.save_manager import maybe_save
        unsaved = st.session_state.get("unsaved_df")
        df_to_save = unsaved if unsaved is not None else df
        if df_to_save is not None:
            result = maybe_save(df_to_save, message="Saved!", force=True)
            if result:
                st.session_state.df = df_to_save
        else:
            st.warning("Nothing to save.")

    if st.session_state.get("pending_changes"):
        st.markdown(
            f'<div class="pending-banner">⚠️ Unsaved changes: {st.session_state.get("pending_changes_reason","")}</div>',
            unsafe_allow_html=True,
        )
    if st.session_state.get("save_conflict"):
        conflict = st.session_state.save_conflict
        st.markdown(
            f'<div class="conflict-banner">⚠️ <b>Conflict</b>: local v{conflict.get("local_version")} vs remote v{conflict.get("remote_version")}</div>',
            unsafe_allow_html=True,
        )
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🔄 Reload", width='stretch', key="btn_conflict_reload"):
                st.session_state.save_conflict = None
                st.session_state.df = None
                st.rerun()
        with c2:
            if st.button("⚠️ Force Save", width='stretch', key="btn_conflict_force"):
                from state.save_manager import save_now
                unsaved = st.session_state.get("unsaved_df")
                df_to_save = unsaved if unsaved is not None else df
                if df_to_save is not None:
                    save_now(df_to_save, ignore_conflict=True)
                    st.rerun()


def _render_reminders(df) -> None:
    """Show upcoming appointment reminders."""
    from services.reminder_service import get_due_reminders, dismiss_reminder, snooze_reminder
    from state.save_manager import maybe_save
    reminders = get_due_reminders(df)
    if not reminders:
        return
    st.markdown("### 🔔 Reminders")
    for r in reminders[:3]:
        mins = r.get("minutes_until", 0)
        label = "NOW" if mins == 0 else f"in {mins}m"
        st.markdown(
            f'<div class="reminder-card"><b>{r.get("patient","?")}</b> — {label}<br>'
            f'<span style="font-size:12px;color:#64748b;">{r.get("doctor","")} · {r.get("op","")}</span></div>',
            unsafe_allow_html=True,
        )
        c1, c2 = st.columns(2)
        row_id = r.get("row_id", "")
        with c1:
            if st.button("✓ Dismiss", key=f"rem_dismiss_{row_id}", width='stretch'):
                updated = dismiss_reminder(df, row_id)
                st.session_state.df = updated
                maybe_save(updated, show_toast=False)
                st.rerun()
        with c2:
            if st.button("💤 Snooze", key=f"rem_snooze_{row_id}", width='stretch'):
                updated = snooze_reminder(df, row_id, snooze_minutes=5)
                st.session_state.df = updated
                maybe_save(updated, show_toast=False)
                st.rerun()

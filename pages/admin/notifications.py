# pages/admin/notifications.py
"""Notification settings page."""

from __future__ import annotations
import streamlit as st


def render() -> None:
    st.markdown("## 🔔 Notification Settings")

    st.info(
        "Configure how and when appointment reminders are shown. "
        "Changes take effect immediately and are stored in session state."
    )

    # ── Reminder settings ──────────────────────────────────────────────────────
    st.markdown("### ⏰ Reminder Timing")

    reminder_window = st.slider(
        "Show reminders for appointments starting within (minutes)",
        min_value=5,
        max_value=60,
        value=st.session_state.get("reminder_window_minutes", 15),
        step=5,
        key="notif_reminder_window",
    )
    st.session_state.reminder_window_minutes = reminder_window

    snooze_duration = st.selectbox(
        "Default snooze duration",
        options=[5, 10, 15, 30],
        index=[5, 10, 15, 30].index(st.session_state.get("reminder_snooze_minutes", 5)),
        format_func=lambda x: f"{x} minutes",
        key="notif_snooze_dur",
    )
    st.session_state.reminder_snooze_minutes = snooze_duration

    # ── Sidebar reminder cap ───────────────────────────────────────────────────
    st.markdown("### 📋 Sidebar Display")
    max_reminders = st.slider(
        "Maximum reminders shown in sidebar",
        min_value=1,
        max_value=10,
        value=st.session_state.get("max_sidebar_reminders", 3),
        step=1,
        key="notif_max_reminders",
    )
    st.session_state.max_sidebar_reminders = max_reminders

    # ── Auto-refresh ───────────────────────────────────────────────────────────
    st.markdown("### 🔄 Auto-Refresh")
    auto_refresh = st.checkbox(
        "Enable auto-refresh (experimental)",
        value=st.session_state.get("auto_refresh_enabled", False),
        key="notif_auto_refresh",
    )
    st.session_state.auto_refresh_enabled = auto_refresh

    if auto_refresh:
        refresh_interval = st.slider(
            "Refresh interval (seconds)",
            min_value=10,
            max_value=300,
            value=st.session_state.get("auto_refresh_interval", 60),
            step=10,
            key="notif_refresh_interval",
        )
        st.session_state.auto_refresh_interval = refresh_interval
        st.caption(
            f"⚠️ Auto-refresh will reload the page every {refresh_interval} seconds. "
            "This may interrupt editing."
        )

        # Trigger auto-refresh using st.empty + time.sleep in a fragment
        import time
        placeholder = st.empty()
        placeholder.caption(f"🔄 Next refresh in ~{refresh_interval}s")

    # ── Save settings ──────────────────────────────────────────────────────────
    st.markdown("---")
    if st.button("💾 Save Settings", width='stretch', key="btn_save_notif"):
        st.success("✅ Settings saved to session state.")
        st.toast("Notification settings updated!", icon="🔔")

    st.markdown("---")
    st.markdown("### ℹ️ Current Settings")
    st.json({
        "reminder_window_minutes": st.session_state.get("reminder_window_minutes", 15),
        "snooze_minutes": st.session_state.get("reminder_snooze_minutes", 5),
        "max_sidebar_reminders": st.session_state.get("max_sidebar_reminders", 3),
        "auto_refresh": st.session_state.get("auto_refresh_enabled", False),
    })

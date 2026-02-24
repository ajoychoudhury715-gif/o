# pages/doctors/overview.py
"""Doctor overview — at-a-glance status of all doctors today."""

from __future__ import annotations
import streamlit as st
import pandas as pd

from data.profile_repo import load_doctors
from services.schedule_ops import ensure_schedule_columns, add_computed_columns
from services.profiles_cache import get_profiles_cache
from services.utils import now_ist


def render() -> None:
    # Premium heading styling
    st.markdown(
        """
        <style>
        .premium-heading {
            background: linear-gradient(135deg, #0c63e4 0%, #2563eb 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-size: 32px;
            font-weight: 800;
            letter-spacing: -1px;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .premium-subheading {
            color: #64748b;
            font-size: 14px;
            font-weight: 500;
            letter-spacing: 0.5px;
            margin-bottom: 24px;
        }
        </style>
        <div class="premium-heading">🩺 Doctors Overview</div>
        <div class="premium-subheading">Real-time staffing status and workload management</div>
        """,
        unsafe_allow_html=True,
    )

    df_sched = st.session_state.get("df")
    if df_sched is None:
        from data.schedule_repo import load_schedule
        from services.schedule_ops import ensure_row_ids
        df_sched = load_schedule()
        df_sched = ensure_schedule_columns(df_sched)
        df_sched = ensure_row_ids(df_sched)
        df_sched = add_computed_columns(df_sched)
        st.session_state.df = df_sched
    else:
        df_sched = ensure_schedule_columns(df_sched)
        df_sched = add_computed_columns(df_sched)

    cache_bust = st.session_state.get("profiles_cache_bust", 0)
    df_doctors = load_doctors(cache_bust)

    # Get week off data
    cache = get_profiles_cache(cache_bust)
    doctor_weekly_off_map = cache.get("doctor_weekly_off_map", {i: [] for i in range(7)})
    today_weekday = now_ist().weekday()

    WEEKDAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    if st.button("🔄 Refresh", key="dr_overview_refresh"):
        st.session_state.df = None
        st.cache_data.clear()
        st.rerun()

    if df_doctors.empty:
        st.info("No doctors found. Add doctors in Manage Profiles.")
        return

    # Build per-doctor stats
    stats = []
    for _, dr_row in df_doctors.iterrows():
        name = str(dr_row.get("name", "") or "").strip()
        if not name:
            continue
        dept = str(dr_row.get("department", "") or "")
        spec = str(dr_row.get("specialisation", "") or "")
        active = bool(dr_row.get("is_active", True))

        # Check if doctor is off today
        off_days = {str(d).strip().upper() for d in doctor_weekly_off_map.get(today_weekday, [])}
        is_off_today = name.upper() in off_days

        # Find appointments for this doctor
        dr_upper = name.upper()
        mask = df_sched.get("DR.", pd.Series(dtype=str)).astype(str).str.strip().str.upper() == dr_upper
        dr_appts = df_sched[mask]

        total = len(dr_appts)
        ongoing = int(dr_appts.get("Is_Ongoing", pd.Series(dtype=bool)).sum()) if "Is_Ongoing" in dr_appts.columns else 0
        done = len(dr_appts[dr_appts.get("STATUS", "").astype(str).str.upper().isin(["DONE", "COMPLETED"])]) if "STATUS" in dr_appts.columns else 0
        pending = total - ongoing - done

        stats.append({
            "name": name,
            "dept": dept,
            "spec": spec,
            "active": active,
            "total": total,
            "ongoing": ongoing,
            "done": done,
            "pending": pending,
            "is_off_today": is_off_today,
        })

    # ── Summary metrics ────────────────────────────────────────────────────────
    active_doctors = sum(1 for s in stats if s["active"] and not s["is_off_today"])
    off_doctors = sum(1 for s in stats if s["is_off_today"])
    total_appts = sum(s["total"] for s in stats)
    total_ongoing = sum(s["ongoing"] for s in stats)

    # Premium metrics styling
    st.markdown(
        """
        <style>
        .metric-card {
            background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
            border: 1px solid rgba(2, 132, 199, 0.2);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
            transition: all 0.3s ease;
        }
        .metric-card:hover {
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
            border-color: rgba(2, 132, 199, 0.4);
            transform: translateY(-2px);
        }
        .metric-value {
            font-size: 32px;
            font-weight: 700;
            color: #0c63e4;
            margin: 8px 0;
        }
        .metric-label {
            font-size: 13px;
            color: #64748b;
            font-weight: 500;
            letter-spacing: 0.5px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4, gap="medium")

    with c1:
        st.markdown(
            f'<div class="metric-card"><div class="metric-label">👨‍⚕️ ACTIVE DOCTORS</div><div class="metric-value">{active_doctors}</div></div>',
            unsafe_allow_html=True,
        )

    with c2:
        st.markdown(
            f'<div class="metric-card"><div class="metric-label">📴 OFF TODAY</div><div class="metric-value">{off_doctors}</div></div>',
            unsafe_allow_html=True,
        )

    with c3:
        st.markdown(
            f'<div class="metric-card"><div class="metric-label">📅 APPOINTMENTS</div><div class="metric-value">{total_appts}</div></div>',
            unsafe_allow_html=True,
        )

    with c4:
        st.markdown(
            f'<div class="metric-card"><div class="metric-label">🔴 ONGOING NOW</div><div class="metric-value">{total_ongoing}</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")

    st.markdown(
        """
        <div style="padding: 12px 0;">
        <div style="font-size: 20px; font-weight: 700; color: #1e293b; display: flex; align-items: center; gap: 8px;">
        👨‍⚕️ Doctor Availability
        </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Doctor cards ───────────────────────────────────────────────────────────
    cols_per_row = 2
    for row_start in range(0, len(stats), cols_per_row):
        cols = st.columns(cols_per_row)
        for col_idx, s in enumerate(stats[row_start:row_start + cols_per_row]):
            with cols[col_idx]:
                # Show as inactive if off today or not active
                is_available = s["active"] and not s["is_off_today"]
                color = "#22c55e" if is_available else "#64748b"
                status_text = "● Active" if is_available else "○ Inactive"
                dept_text = s["spec"] + (" · " + s["dept"] if s["dept"] else "")

                off_badge_html = ""
                border_color = "rgba(239, 68, 68, 0.3)" if s["is_off_today"] else "rgba(59, 130, 246, 0.2)"
                bg_color = "rgba(239, 68, 68, 0.05)" if s["is_off_today"] else "rgba(255, 255, 255, 0.8)"

                if s["is_off_today"]:
                    off_badge_html = '<div style="color:#ef4444;font-size:10px;font-weight:700;margin-top:8px;padding:4px 8px;background:rgba(239,68,68,0.1);border-radius:6px;display:inline-block;">📴 OFF TODAY</div>'

                html_card = (
                    f'<div style="background:{bg_color};border:1.5px solid {border_color};border-radius:14px;padding:16px;margin-bottom:12px;backdrop-filter:blur(10px);transition:all 0.3s ease;box-shadow:0 2px 8px rgba(0,0,0,0.05);">'
                    '<div style="display:flex;justify-content:space-between;align-items:flex-start;gap:12px;">'
                    '<div style="min-width:0;flex:1;">'
                    f'<div style="font-weight:700;color:#1e293b;font-size:16px;word-break:break-word;margin-bottom:4px;">🩺 {s["name"]}</div>'
                    f'<div style="font-size:12px;color:#64748b;font-weight:500;">{dept_text}</div>'
                    '</div>'
                    f'<span style="flex-shrink:0;color:{color};font-size:11px;font-weight:700;padding:4px 10px;background:rgba({color.lstrip("#").rstrip()}20);border-radius:6px;white-space:nowrap;">{status_text}</span>'
                    '</div>'
                    f'{off_badge_html}'
                    '<div style="display:flex;gap:16px;margin-top:10px;padding-top:10px;border-top:1px solid rgba(0,0,0,0.05);">'
                    f'<span style="font-size:12px;color:#94a3b8;"><span style="font-weight:600;color:#1e293b;">📅 {s["total"]}</span> appts</span>'
                    f'<span style="font-size:12px;color:#94a3b8;"><span style="font-weight:600;color:#ef4444;">🔴 {s["ongoing"]}</span> live</span>'
                    f'<span style="font-size:12px;color:#94a3b8;"><span style="font-weight:600;color:#22c55e;">✅ {s["done"]}</span> done</span>'
                    '</div>'
                    '</div>'
                )
                st.markdown(html_card, unsafe_allow_html=True)

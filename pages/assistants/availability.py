# pages/assistants/availability.py
"""Assistant availability dashboard."""

from __future__ import annotations
import streamlit as st

from services.availability import get_all_assistant_statuses, deserialize_time_blocks
from services.profiles_cache import get_profiles_cache
from data.attendance_repo import get_today_punch_map
from services.utils import now_ist
from components.assistant_day_detail import render_assistant_day_detail
from components.theme import avail_badge_html


def render() -> None:
    st.markdown("## 📡 Assistant Availability")

    df = st.session_state.get("df")
    if df is None:
        from data.schedule_repo import load_schedule
        from services.schedule_ops import ensure_schedule_columns, ensure_row_ids, add_computed_columns
        df = load_schedule()
        df = ensure_schedule_columns(df)
        df = ensure_row_ids(df)
        df = add_computed_columns(df)
        st.session_state.df = df

    cache_bust = st.session_state.get("profiles_cache_bust", 0)
    cache = get_profiles_cache(cache_bust)
    assistants = sorted(cache.get("assistants_list") or [])

    col_refresh, col_filter = st.columns([1, 3])
    with col_refresh:
        if st.button("🔄 Refresh", width='stretch', key="avail_refresh"):
            st.rerun()
    with col_filter:
        filter_status = st.multiselect(
            "Filter by status",
            options=["FREE", "BUSY", "BLOCKED", "OFF"],
            default=[],
            key="avail_filter",
        )

    now = now_ist()
    today_str = now.date().isoformat()
    today_weekday = now.weekday()
    punch_map = get_today_punch_map(today_str)
    meta = getattr(df, "attrs", {}).get("meta", {})
    time_blocks = deserialize_time_blocks(meta.get("time_blocks", []))
    weekly_off_map = cache.get("weekly_off_map") or {}

    statuses = get_all_assistant_statuses(
        df, punch_map, time_blocks, today_str,
        today_weekday=today_weekday,
        weekly_off_map=weekly_off_map,
        assistants=assistants,
    )

    # Filter
    if filter_status:
        statuses = {a: s for a, s in statuses.items() if s.get("status", "").upper() in filter_status}

    if not statuses:
        st.info("No assistants to display.")
        return

    # ── Summary metrics ────────────────────────────────────────────────────────
    counts = {"FREE": 0, "BUSY": 0, "BLOCKED": 0, "OFF": 0}
    for s in statuses.values():
        key = s.get("status", "FREE").upper()
        counts[key] = counts.get(key, 0) + 1

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("✅ Free", counts["FREE"])
    c2.metric("🔴 Busy", counts["BUSY"])
    c3.metric("🚫 Blocked", counts["BLOCKED"])
    c4.metric("📴 Off", counts["OFF"])

    st.markdown("---")

    # ── Individual cards ───────────────────────────────────────────────────────
    st.caption("Use 'View Daily Schedule' on any assistant card to inspect that assistant's full day.")
    cols_per_row = 3
    assistant_list = list(statuses.keys())
    selected_assistant = str(st.session_state.get("availability_selected_assistant", "") or "").strip().upper()

    for row_start in range(0, len(assistant_list), cols_per_row):
        cols = st.columns(cols_per_row)
        for col_idx, asst in enumerate(assistant_list[row_start:row_start + cols_per_row]):
            with cols[col_idx]:
                info = statuses[asst]
                status = str(info.get("status", "FREE")).upper()
                reason = str(info.get("reason", ""))
                dept = str(info.get("department", ""))
                badge = avail_badge_html(status)
                is_selected = selected_assistant == asst

                st.markdown(
                    f"""<div class="profile-card" style="margin-bottom:8px;border:{'2px solid rgba(37,99,235,0.45)' if is_selected else '1px solid rgba(148,163,184,0.18)'};">
                      <div style="display:flex;justify-content:space-between;align-items:center;">
                        <span style="font-weight:600;color:#1e293b;font-size:14px;">👤 {asst}</span>
                        {badge}
                      </div>
                      {('<div style="font-size:11px;color:#94a3b8;margin-top:4px;">🏥 ' + dept + '</div>') if dept else ''}
                      {('<div style="font-size:11px;color:#64748b;margin-top:2px;">' + reason + '</div>') if reason else ''}
                    </div>""",
                    unsafe_allow_html=True,
                )
                button_label = "Hide Daily Schedule" if is_selected else "View Daily Schedule"
                if st.button(button_label, key=f"avail_detail_{asst}", width='stretch'):
                    st.session_state.availability_selected_assistant = "" if is_selected else asst
                    st.rerun()

    selected_assistant = str(st.session_state.get("availability_selected_assistant", "") or "").strip().upper()
    if selected_assistant:
        render_assistant_day_detail(df, selected_assistant, today_str=today_str)

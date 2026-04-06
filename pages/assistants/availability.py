# pages/assistants/availability.py
"""Assistant availability dashboard."""

from __future__ import annotations
import html
import streamlit as st
import pandas as pd

from services.availability import get_all_assistant_statuses, deserialize_time_blocks
from services.profiles_cache import get_profiles_cache
from data.attendance_repo import get_today_punch_map
from services.utils import now_ist, time_to_12h
from components.assistant_day_detail import render_assistant_day_detail
from components.theme import avail_badge_html

LIVE_OCCUPANCY_REFRESH_SECONDS = 15


def _format_minutes_label(total_minutes) -> str:
    if total_minutes is None:
        return "—"
    minutes = max(0, int(float(total_minutes or 0)))
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours}h {mins:02d}m"


def _format_dt_label(value) -> str:
    if value is None or (hasattr(pd, "isna") and pd.isna(value)):
        return "—"
    dt_value = value.to_pydatetime() if hasattr(value, "to_pydatetime") else value
    if not hasattr(dt_value, "time"):
        return str(value or "—")
    return time_to_12h(dt_value.astimezone(now_ist().tzinfo).time().replace(second=0, microsecond=0))


def _build_assistant_card_html(
    assistant: str,
    status: str,
    badge_html: str,
    department: str,
    reason: str,
    current_op: str,
    current_label: str,
    current_for: str,
    available_in: str,
    expected_free_at: str,
    is_selected: bool,
) -> str:
    border = "2px solid rgba(37,99,235,0.45)" if is_selected else "1px solid rgba(148,163,184,0.18)"
    rows: list[str] = []

    if department:
        rows.append(
            f'<div style="font-size:11px;color:#94a3b8;margin-top:4px;">'
            f'🏥 {html.escape(department)}</div>'
        )
    if reason:
        rows.append(
            f'<div style="font-size:11px;color:#64748b;margin-top:2px;">'
            f'{html.escape(reason)}</div>'
        )
    if current_op:
        rows.append(
            f'<div style="font-size:11px;color:#64748b;margin-top:2px;">'
            f'OP: {html.escape(current_op)}</div>'
        )
    if current_for != "—":
        rows.append(
            f'<div style="font-size:11px;color:#475569;margin-top:6px;">'
            f'{html.escape(current_label)}: <b>{html.escape(current_for)}</b></div>'
        )

    availability_label = available_in if status in {"BUSY", "BLOCKED"} else "Now"
    free_at_label = expected_free_at if status in {"BUSY", "BLOCKED"} else "Now"
    rows.append(
        f'<div style="font-size:11px;color:#475569;margin-top:2px;">'
        f'Available In: <b>{html.escape(availability_label)}</b></div>'
    )
    rows.append(
        f'<div style="font-size:11px;color:#475569;margin-top:2px;">'
        f'Free At: <b>{html.escape(free_at_label)}</b></div>'
    )

    return (
        f'<div class="profile-card" style="margin-bottom:8px;border:{border};">'
        f'<div style="display:flex;justify-content:space-between;align-items:center;">'
        f'<span style="font-weight:600;color:#1e293b;font-size:14px;">'
        f'👤 {html.escape(assistant)}</span>'
        f'{badge_html}'
        f'</div>'
        f'{"".join(rows)}'
        f'</div>'
    )


def _load_live_schedule_df() -> pd.DataFrame:
    from data.schedule_repo import clear_schedule_cache, load_schedule
    from services.schedule_ops import ensure_schedule_columns, ensure_row_ids, add_computed_columns

    clear_schedule_cache()
    df = load_schedule()
    df = ensure_schedule_columns(df)
    df = ensure_row_ids(df)
    return add_computed_columns(df)


@st.fragment(run_every=LIVE_OCCUPANCY_REFRESH_SECONDS)
def _render_live_availability_dashboard(cache_bust: int) -> None:
    df = _load_live_schedule_df()
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

    st.caption(
        f"Live occupancy refreshes every {LIVE_OCCUPANCY_REFRESH_SECONDS}s. "
        "Patient appointments marked ON GOING show as BUSY; active duty runs and time blocks show as BLOCKED with the same countdown fields."
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
                current_label = str(info.get("current_label", "Busy For" if status == "BUSY" else "Free For"))
                current_for = _format_minutes_label(info.get("current_for_minutes"))
                available_in = _format_minutes_label(info.get("available_in_minutes"))
                expected_free_at = _format_dt_label(info.get("expected_free_at"))
                current_op = str(info.get("current_op", "") or "").strip()
                badge = avail_badge_html(status)
                is_selected = selected_assistant == asst
                card_html = _build_assistant_card_html(
                    assistant=asst,
                    status=status,
                    badge_html=badge,
                    department=dept,
                    reason=reason,
                    current_op=current_op,
                    current_label=current_label,
                    current_for=current_for,
                    available_in=available_in,
                    expected_free_at=expected_free_at,
                    is_selected=is_selected,
                )

                st.markdown(card_html, unsafe_allow_html=True)
                button_label = "Hide Daily Schedule" if is_selected else "View Daily Schedule"
                if st.button(button_label, key=f"avail_detail_{asst}", width='stretch'):
                    st.session_state.availability_selected_assistant = "" if is_selected else asst
                    st.rerun()

    selected_assistant = str(st.session_state.get("availability_selected_assistant", "") or "").strip().upper()
    if selected_assistant:
        render_assistant_day_detail(df, selected_assistant, today_str=today_str)


def render() -> None:
    st.markdown("## 📡 Assistant Availability")
    _render_live_availability_dashboard(int(st.session_state.get("profiles_cache_bust", 0)))

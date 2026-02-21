# components/schedule_card.py
"""Card view component for schedule entries."""

from __future__ import annotations
from typing import Callable
import streamlit as st

from config.constants import STATUS_OPTIONS
from components.theme import status_badge_html, assign_pill_html
from services.utils import coerce_to_time_obj, time_to_12h


def _fmt_time(val) -> str:
    t = coerce_to_time_obj(val)
    if t is None:
        return str(val or "")
    return time_to_12h(t)


def render_schedule_card(
    row: dict,
    on_status_change: Callable[[str, str], None],
    on_delete: Callable[[str], None],
    idx: int,
) -> None:
    """Render a single appointment card."""
    row_id = str(row.get("REMINDER_ROW_ID", "")).strip() or str(idx)
    patient = str(row.get("Patient Name", "")).strip() or "—"
    in_t = _fmt_time(row.get("In Time"))
    out_t = _fmt_time(row.get("Out Time"))
    doctor = str(row.get("DR.", "")).strip() or "—"
    op = str(row.get("OP", "")).strip() or "—"
    procedure = str(row.get("Procedure", "")).strip() or ""
    status = str(row.get("STATUS", "PENDING")).strip().upper()
    first = str(row.get("FIRST", "")).strip()
    second = str(row.get("SECOND", "")).strip()
    third = str(row.get("Third", "")).strip()
    case_paper = str(row.get("CASE PAPER", "")).strip()

    badge = status_badge_html(status)
    a1 = assign_pill_html(first)
    a2 = assign_pill_html(second)
    a3 = assign_pill_html(third)

    st.markdown(f"""
<div class="tdb-card">
  <div class="tdb-card-header">
    <div>
      <div class="tdb-patient-name">👤 {patient}</div>
      <div class="tdb-card-meta">⏱ {in_t} – {out_t} &nbsp;|&nbsp; 🩺 {doctor} &nbsp;|&nbsp; 🏥 {op}</div>
    </div>
    {badge}
  </div>
  {"<div style='font-size:13px;color:#64748b;margin-bottom:8px;'>📋 " + procedure + "</div>" if procedure else ""}
  {"<div style='font-size:12px;color:#64748b;margin-bottom:8px;'>📄 Case: " + case_paper + "</div>" if case_paper else ""}
  <div style="margin-top:8px;">
    <span style="font-size:12px;font-weight:600;color:#64748b;">ASSISTANTS:</span>
    {a1} {a2} {a3}
  </div>
</div>
""", unsafe_allow_html=True)

    # Action row
    c1, c2, c3 = st.columns([3, 1, 1])
    with c1:
        current_idx = STATUS_OPTIONS.index(status) if status in STATUS_OPTIONS else 0
        new_status = st.selectbox(
            "Status",
            STATUS_OPTIONS,
            index=current_idx,
            key=f"status_sel_{row_id}_{idx}",
            label_visibility="collapsed",
        )
        if new_status != status:
            on_status_change(row_id, new_status)
    with c2:
        if st.button("✏️", key=f"edit_btn_{row_id}_{idx}", help="Edit", use_container_width=True):
            st.session_state[f"editing_row_{row_id}"] = True
            st.rerun()
    with c3:
        if st.button("🗑️", key=f"del_btn_{row_id}_{idx}", help="Delete", use_container_width=True):
            on_delete(row_id)


def render_add_appointment_form(
    doctors: list[str],
    assistants: list[str],
    op_rooms: list[str],
    on_save: Callable[[dict], None],
) -> None:
    """Render the Add Appointment form."""
    with st.expander("➕ Add Appointment", expanded=False):
        with st.form("add_appt_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                patient_name = st.text_input("Patient Name *")
                doctor = st.selectbox("Doctor *", [""] + doctors)
                op = st.selectbox("OP Room", [""] + op_rooms)
            with c2:
                # Digital clock time picker for In Time
                st.markdown("**In Time*** 🕐")
                t_col1, t_col2, t_col3 = st.columns([2, 1, 2])
                with t_col1:
                    in_hour = st.number_input("Hour", min_value=0, max_value=23, value=9, step=1, key="in_hour_add")
                with t_col2:
                    st.markdown("<div style='text-align:center;padding-top:32px;font-size:20px;font-weight:bold;'>:</div>", unsafe_allow_html=True)
                with t_col3:
                    in_minute = st.number_input("Minute", min_value=0, max_value=59, value=0, step=5, key="in_minute_add")

                import datetime
                in_time = datetime.time(int(in_hour), int(in_minute))
                st.markdown(f"<div style='text-align:center;font-size:18px;font-weight:bold;color:#3b82f6;'>{in_time.strftime('%H:%M')}</div>", unsafe_allow_html=True)

                duration_mins = st.number_input("Duration (minutes)", min_value=1, max_value=480, value=30)
                procedure = st.text_input("Procedure")

            # Calculate out_time based on in_time + duration
            out_time = (
                (int(in_time.hour * 60 + in_time.minute) + int(duration_mins)) % (24 * 60)
            )
            out_hour = out_time // 60
            out_minute = out_time % 60
            out_time = datetime.time(out_hour, out_minute)

            c3, c4, c5 = st.columns(3)
            with c3:
                first = st.selectbox("First Assistant", [""] + assistants, key="add_first")
            with c4:
                second = st.selectbox("Second Assistant", [""] + assistants, key="add_second")
            with c5:
                third = st.selectbox("Third Assistant", [""] + assistants, key="add_third")

            case_paper = st.text_input("Case Paper #")
            status = st.selectbox("Status", STATUS_OPTIONS, index=0)

            submitted = st.form_submit_button("➕ Add Appointment", use_container_width=True)
            if submitted:
                if not patient_name or not doctor:
                    st.error("Patient Name and Doctor are required.")
                else:
                    import uuid
                    row = {
                        "Patient ID": str(uuid.uuid4())[:8],
                        "Patient Name": patient_name,
                        "In Time": in_time.strftime("%H:%M") if in_time else "",
                        "Out Time": out_time.strftime("%H:%M") if out_time else "",
                        "Procedure": procedure,
                        "DR.": doctor,
                        "FIRST": first,
                        "SECOND": second,
                        "Third": third,
                        "CASE PAPER": case_paper,
                        "OP": op,
                        "SUCTION": "",
                        "CLEANING": "",
                        "STATUS": status,
                        "REMINDER_ROW_ID": str(uuid.uuid4()),
                        "REMINDER_SNOOZE_UNTIL": "",
                        "REMINDER_DISMISSED": "",
                        "STATUS_CHANGED_AT": "",
                        "ACTUAL_START_AT": "",
                        "ACTUAL_END_AT": "",
                        "STATUS_LOG": "",
                    }
                    on_save(row)

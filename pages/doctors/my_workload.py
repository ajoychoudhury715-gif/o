# pages/doctors/my_workload.py
"""Personal workload view for each doctor - today's appointments."""

from __future__ import annotations
import streamlit as st
import pandas as pd

from services.schedule_ops import ensure_schedule_columns, add_computed_columns
from services.profiles_cache import get_profiles_cache, get_department_for_doctor
from services.utils import coerce_to_time_obj, time_to_12h, norm_name


def _parse_12h_time(time_str: str):
    """Parse 12-hour format time string, handling various formats."""
    from datetime import datetime
    if not time_str or time_str == "—":
        return None

    time_str = str(time_str).strip().upper()
    # Try multiple common formats
    for fmt in ["%I:%M %p", "%I:%M%p", "%I:%M %P", "%I:%M%P", "%H:%M"]:
        try:
            return datetime.strptime(time_str, fmt)
        except ValueError:
            pass
    return None


def _render_appointment_cards(appointments: list) -> None:
    """Render appointments as mobile-friendly cards."""
    # CSS for appointment cards
    st.markdown("""
    <style>
    .appointment-card {
        background: white;
        border-left: 4px solid #2563eb;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 12px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.08);
        transition: all 0.2s;
    }
    .appointment-card:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.12);
        transform: translateX(2px);
    }
    .appt-patient {
        font-size: 16px;
        font-weight: 600;
        color: #1e293b;
        margin-bottom: 8px;
    }
    .appt-time {
        font-size: 13px;
        color: #64748b;
        margin-bottom: 6px;
    }
    .appt-details {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 8px;
        font-size: 12px;
        margin-top: 10px;
    }
    .appt-detail-item {
        background: #f8fafc;
        padding: 6px 8px;
        border-radius: 4px;
        color: #475569;
    }
    .appt-detail-label {
        font-weight: 600;
        color: #64748b;
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .appt-status {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
        margin-top: 8px;
    }
    .appt-status-processing {
        background: #dbeafe;
        color: #1e40af;
    }
    .appt-status-done {
        background: #dcfce7;
        color: #166534;
    }
    </style>
    """, unsafe_allow_html=True)

    # Render each appointment as a card
    for i, appt in enumerate(appointments):
        patient = str(appt.get("Patient Name", "—")).strip()
        # Handle both "In Time" and "in_time" column names
        in_time = str(appt.get("In Time") or appt.get("in_time") or "—").strip()
        out_time = str(appt.get("Out Time") or appt.get("out_time") or "—").strip()
        op = str(appt.get("OP", "—")).strip()
        procedure = str(appt.get("Procedure", "")).strip()
        status = str(appt.get("STATUS", "PENDING")).strip().upper()

        # Calculate duration from in_time and out_time in 12-hour format
        duration_text = "—"
        if in_time != "—" and out_time != "—":
            try:
                from datetime import timedelta
                in_dt = _parse_12h_time(in_time)
                out_dt = _parse_12h_time(out_time)

                if in_dt and out_dt:
                    # Handle case where out_time is on the next day (e.g., in_time: 11 PM, out_time: 1 AM)
                    if out_dt < in_dt:
                        out_dt = out_dt + timedelta(days=1)

                    duration_mins = int((out_dt - in_dt).total_seconds() / 60)
                    if duration_mins > 0:
                        if duration_mins >= 60:
                            hours = duration_mins // 60
                            mins = duration_mins % 60
                            duration_text = f"{hours}h {mins}m" if mins > 0 else f"{hours}h"
                        else:
                            duration_text = f"{duration_mins}m"
            except Exception:
                pass

        status_class = "appt-status-processing" if status != "DONE" else "appt-status-done"

        st.markdown(f"""
        <div class="appointment-card">
            <div class="appt-patient">👤 {patient}</div>
            <div class="appt-time">⏱ {in_time}</div>
            <div class="appt-time">⏳ Duration: {duration_text}</div>
            {f'<div class="appt-time">📋 {procedure}</div>' if procedure else ''}
            <div class="appt-details">
                <div class="appt-detail-item">
                    <div class="appt-detail-label">OP Room</div>
                    {op}
                </div>
                <div class="appt-detail-item">
                    <div class="appt-detail-label">Assistants</div>
                    {get_assistant_names(appt)}
                </div>
            </div>
            <div class="appt-status appt-status-{status.lower()}">{status}</div>
        </div>
        """, unsafe_allow_html=True)


def get_assistant_names(appt: dict) -> str:
    """Get comma-separated list of assigned assistants."""
    assistants = []
    for col in ["FIRST", "SECOND", "Third"]:
        name = str(appt.get(col, "")).strip()
        if name:
            assistants.append(name)
    return ", ".join(assistants) if assistants else "—"


def render() -> None:
    # ── Section heading styles ──────────────────────────────────────────────
    st.markdown("""
    <style>
    .section-heading {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 12px;
        padding: 20px 24px;
        margin: 0 0 24px 0;
        color: white;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        border: none;
        text-align: center;
    }

    .section-heading h1 {
        margin: 0;
        font-size: 28px;
        font-weight: 700;
        letter-spacing: 0.5px;
    }

    .section-heading-summary {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
    }

    .section-heading-summary h2 {
        margin: 0;
        font-size: 22px;
        font-weight: 700;
        letter-spacing: 0.5px;
    }

    @media (max-width: 768px) {
        .section-heading {
            padding: 16px 20px;
            margin: 0 0 20px 0;
        }

        .section-heading h1 {
            font-size: 24px;
        }

        .section-heading-summary h2 {
            font-size: 18px;
        }
    }

    @media (max-width: 480px) {
        .section-heading {
            padding: 14px 16px;
            margin: 0 0 16px 0;
        }

        .section-heading h1 {
            font-size: 20px;
        }

        .section-heading-summary h2 {
            font-size: 16px;
        }
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""<div class="section-heading"><h1>My Workload (Current Assignments)</h1></div>""", unsafe_allow_html=True)

    # Check if user is logged in
    current_user = st.session_state.get("current_user")
    if not current_user:
        st.warning("Please log in to view your workload.")
        return

    # Load schedule data
    df = st.session_state.get("df")
    if df is None:
        from data.schedule_repo import load_schedule
        from services.schedule_ops import ensure_row_ids
        df = load_schedule()
        df = ensure_schedule_columns(df)
        df = ensure_row_ids(df)
        df = add_computed_columns(df)
        st.session_state.df = df

    df = ensure_schedule_columns(df)
    df = add_computed_columns(df)

    # ── Filter to TODAY only ───────────────────────────────────────────────────
    from datetime import datetime
    from config.settings import IST
    today_str = datetime.now(IST).strftime("%Y-%m-%d")

    date_col = "DATE" if "DATE" in df.columns else "appointment_date"
    if date_col in df.columns:
        df = df[df[date_col].astype(str).str.startswith(today_str)]

    # ── Get my appointments (ALL APPOINTMENTS) ──────────────────────────────
    my_appointments = []
    doctor_upper = str(current_user).strip().upper()

    for _, row in df.iterrows():
        doctor = str(row.get("DR.", "")).strip().upper()
        if doctor == doctor_upper:
            my_appointments.append(row)

    if not my_appointments:
        st.info("No appointments assigned for you today.")
        return

    # ── Display Summary Cards (Mobile-Optimized Container) ──────────────────────
    st.markdown("""<div class="section-heading section-heading-summary"><h2>Today's Assignment Summary</h2></div>""", unsafe_allow_html=True)

    total_count = len(my_appointments)

    # Count by status
    processing = sum(1 for appt in my_appointments
                    if str(appt.get("STATUS", "")).strip().upper() not in {"DONE", "COMPLETED"})
    done = sum(1 for appt in my_appointments
              if str(appt.get("STATUS", "")).strip().upper() in {"DONE", "COMPLETED"})

    # Create responsive card layout with container
    st.markdown("""
    <style>
    .summary-container {
        background: #f8fafc;
        border-radius: 16px;
        padding: 20px;
        margin: 16px 0;
        border: 1px solid #e2e8f0;
    }

    .summary-cards-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 12px;
    }

    @media (max-width: 768px) {
        .summary-cards-grid {
            grid-template-columns: 1fr;
            gap: 10px;
        }
    }

    .summary-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 12px;
        padding: 24px 16px;
        text-align: center;
        color: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
        border: none;
        min-height: 120px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }

    .summary-card:hover {
        transform: translateY(-4px) scale(1.02);
        box-shadow: 0 8px 16px rgba(0,0,0,0.15);
    }

    .summary-card-processing {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }

    .summary-card-done {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
    }

    .summary-card-total {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
    }

    .summary-card-number {
        font-size: 40px;
        font-weight: 700;
        margin: 8px 0;
        line-height: 1;
    }

    .summary-card-label {
        font-size: 13px;
        opacity: 0.95;
        text-transform: uppercase;
        letter-spacing: 1.2px;
        font-weight: 600;
    }

    @media (max-width: 480px) {
        .summary-card {
            padding: 20px 12px;
            min-height: 110px;
        }

        .summary-card-number {
            font-size: 32px;
        }

        .summary-card-label {
            font-size: 12px;
        }
    }
    </style>
    """, unsafe_allow_html=True)

    # Container with responsive grid
    st.markdown(f"""
    <div class="summary-container">
        <div class="summary-cards-grid">
            <div class="summary-card summary-card-total">
                <div class="summary-card-label">👨‍⚕️ Total Appointments</div>
                <div class="summary-card-number">{total_count}</div>
            </div>
            <div class="summary-card summary-card-processing">
                <div class="summary-card-label">⏳ In Progress</div>
                <div class="summary-card-number">{processing}</div>
            </div>
            <div class="summary-card summary-card-done">
                <div class="summary-card-label">✅ Completed</div>
                <div class="summary-card-number">{done}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # ── Appointments (Card View) ─────────────────────────────────────────────
    if my_appointments:
        # Format times to 12-hour format
        formatted_appts = []
        for appt in my_appointments:
            appt_copy = appt.copy()
            # Handle both "In Time" and "in_time" column names
            in_time_val = None
            if "In Time" in appt_copy:
                in_time_val = time_to_12h(coerce_to_time_obj(appt_copy["In Time"]))
                appt_copy["In Time"] = in_time_val
            if "in_time" in appt_copy:
                in_time_val = time_to_12h(coerce_to_time_obj(appt_copy["in_time"]))
                appt_copy["in_time"] = in_time_val

            # Handle both "Out Time" and "out_time" column names
            out_time_val = None
            if "Out Time" in appt_copy:
                out_time_val = time_to_12h(coerce_to_time_obj(appt_copy["Out Time"]))
                appt_copy["Out Time"] = out_time_val
            if "out_time" in appt_copy:
                out_time_val = time_to_12h(coerce_to_time_obj(appt_copy["out_time"]))
                appt_copy["out_time"] = out_time_val

            formatted_appts.append(appt_copy)

        _render_appointment_cards(formatted_appts)
    else:
        st.info("✅ No appointments for you today.")

    st.markdown("---")

    # ── Refresh button ─────────────────────────────────────────────────────────
    if st.button("🔄 Refresh", key="dr_my_workload_refresh"):
        st.session_state.df = None
        st.cache_data.clear()
        st.rerun()

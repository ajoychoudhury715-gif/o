# pages/assistants/my_workload.py
"""Personal workload view for each assistant - grouped by specialty."""

from __future__ import annotations
import streamlit as st
import pandas as pd

from services.schedule_ops import ensure_schedule_columns, add_computed_columns
from services.profiles_cache import (
    get_profiles_cache,
    get_department_for_doctor,
    get_all_doctors,
)
from services.utils import coerce_to_time_obj, time_to_12h


def _render_appointment_cards(appointments: list, specialty_color: str) -> None:
    """Render appointments as mobile-friendly cards."""
    # CSS for appointment cards
    st.markdown(f"""
    <style>
    .appointment-card {{
        background: white;
        border-left: 4px solid {specialty_color};
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 12px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.08);
        transition: all 0.2s;
    }}
    .appointment-card:hover {{
        box-shadow: 0 4px 12px rgba(0,0,0,0.12);
        transform: translateX(2px);
    }}
    .appt-patient {{
        font-size: 16px;
        font-weight: 600;
        color: #1e293b;
        margin-bottom: 8px;
    }}
    .appt-time {{
        font-size: 13px;
        color: #64748b;
        margin-bottom: 6px;
    }}
    .appt-details {{
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 8px;
        font-size: 12px;
        margin-top: 10px;
    }}
    .appt-detail-item {{
        background: #f8fafc;
        padding: 6px 8px;
        border-radius: 4px;
        color: #475569;
    }}
    .appt-detail-label {{
        font-weight: 600;
        color: #64748b;
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    .appt-status {{
        display: inline-block;
        padding: 4px 10px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
        margin-top: 8px;
    }}
    .appt-status-processing {{
        background: #dbeafe;
        color: #1e40af;
    }}
    .appt-status-done {{
        background: #dcfce7;
        color: #166534;
    }}
    </style>
    """, unsafe_allow_html=True)

    # Render each appointment as a card
    for i, appt in enumerate(appointments):
        patient = str(appt.get("Patient Name", "—")).strip()
        # Handle both "In Time" and "in_time" column names
        in_time = str(appt.get("In Time") or appt.get("in_time") or "—").strip()
        out_time = str(appt.get("Out Time") or appt.get("out_time") or "—").strip()
        doctor = str(appt.get("DR.", "—")).strip()
        op = str(appt.get("OP", "—")).strip()
        procedure = str(appt.get("Procedure", "")).strip()
        status = str(appt.get("STATUS", "PENDING")).strip().upper()

        status_class = "appt-status-processing" if status != "DONE" else "appt-status-done"
        time_range = f"{in_time} – {out_time}" if in_time != "—" and out_time != "—" else "No time"

        st.markdown(f"""
        <div class="appointment-card">
            <div class="appt-patient">👤 {patient}</div>
            <div class="appt-time">⏱ {time_range}</div>
            {f'<div class="appt-time">📋 {procedure}</div>' if procedure else ''}
            <div class="appt-details">
                <div class="appt-detail-item">
                    <div class="appt-detail-label">Doctor</div>
                    {doctor}
                </div>
                <div class="appt-detail-item">
                    <div class="appt-detail-label">OP Room</div>
                    {op}
                </div>
            </div>
            <div class="appt-status appt-status-{status.lower()}">{status}</div>
        </div>
        """, unsafe_allow_html=True)


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

    # ── Get my appointments (ONLY CURRENT/ACTIVE) ──────────────────────────────
    my_appointments = []
    assistant_upper = str(current_user).strip().upper()

    for _, row in df.iterrows():
        status = str(row.get("STATUS", "")).strip().upper()
        # Show only active statuses: not completed, cancelled, or shifted
        if status in {"DONE", "COMPLETED", "CANCELLED", "SHIFTED"}:
            continue

        is_assigned = False
        for col in ["FIRST", "SECOND", "Third"]:
            if str(row.get(col, "")).strip().upper() == assistant_upper:
                is_assigned = True
                break

        if is_assigned:
            my_appointments.append(row)

    if not my_appointments:
        st.info("No appointments assigned for you today.")
        return

    # ── Group appointments by specialty ────────────────────────────────────────
    cache = get_profiles_cache(st.session_state.get("profiles_cache_bust", 0))
    doctor_dept_map = cache.get("doctor_dept_map", {})

    endo_appointments = []
    prostho_appointments = []

    from services.utils import norm_name

    for appt in my_appointments:
        doctor = str(appt.get("DR.", "")).strip().upper()
        doctor_key = norm_name(doctor)
        specialty = doctor_dept_map.get(doctor_key, "").upper()

        # If specialty not found in doctor mapping, try to infer from procedure or OP
        if not specialty:
            procedure = str(appt.get("Procedure", "")).strip().upper()
            if "ENDO" in procedure:
                specialty = "ENDO"
            elif "PROSTHO" in procedure or "CROWN" in procedure or "BRIDGE" in procedure:
                specialty = "PROSTHO"

        # Assign to appropriate list based on determined specialty
        if specialty == "ENDO":
            endo_appointments.append(appt)
        elif specialty == "PROSTHO":
            prostho_appointments.append(appt)
        # Skip appointments with unknown specialty (don't default)

    # ── Display Summary Cards (Mobile-Optimized Container) ──────────────────────
    st.markdown("""<div class="section-heading section-heading-summary"><h2>Today's Assignment Summary</h2></div>""", unsafe_allow_html=True)

    total_count = len(my_appointments)
    endo_count = len(endo_appointments)
    prostho_count = len(prostho_appointments)

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

    .summary-card-endo {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }

    .summary-card-prostho {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
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
                <div class="summary-card-label">👤 Total Patients</div>
                <div class="summary-card-number">{total_count}</div>
            </div>
            <div class="summary-card summary-card-endo">
                <div class="summary-card-label">🦷 Endo Patients</div>
                <div class="summary-card-number">{endo_count}</div>
            </div>
            <div class="summary-card summary-card-prostho">
                <div class="summary-card-label">👄 Prostho Patients</div>
                <div class="summary-card-number">{prostho_count}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # ── Endo Appointments (Card View) ─────────────────────────────────────────
    st.markdown("### 🦷 Endodontics (Endo)")

    if endo_appointments:
        # Format times to 12-hour format
        formatted_endo = []
        for appt in endo_appointments:
            appt_copy = appt.copy()
            # Handle both "In Time" and "in_time" column names
            if "In Time" in appt_copy:
                appt_copy["In Time"] = time_to_12h(coerce_to_time_obj(appt_copy["In Time"]))
            elif "in_time" in appt_copy:
                appt_copy["in_time"] = time_to_12h(coerce_to_time_obj(appt_copy["in_time"]))
            # Handle both "Out Time" and "out_time" column names
            if "Out Time" in appt_copy:
                appt_copy["Out Time"] = time_to_12h(coerce_to_time_obj(appt_copy["Out Time"]))
            elif "out_time" in appt_copy:
                appt_copy["out_time"] = time_to_12h(coerce_to_time_obj(appt_copy["out_time"]))
            formatted_endo.append(appt_copy)

        _render_appointment_cards(formatted_endo, "#667eea")
    else:
        st.info("✅ No Endo patients assigned today.")

    st.markdown("---")

    # ── Prostho Appointments (Card View) ──────────────────────────────────────
    st.markdown("### 👄 Prosthodontics (Prostho)")

    if prostho_appointments:
        # Format times to 12-hour format
        formatted_prostho = []
        for appt in prostho_appointments:
            appt_copy = appt.copy()
            # Handle both "In Time" and "in_time" column names
            if "In Time" in appt_copy:
                appt_copy["In Time"] = time_to_12h(coerce_to_time_obj(appt_copy["In Time"]))
            elif "in_time" in appt_copy:
                appt_copy["in_time"] = time_to_12h(coerce_to_time_obj(appt_copy["in_time"]))
            # Handle both "Out Time" and "out_time" column names
            if "Out Time" in appt_copy:
                appt_copy["Out Time"] = time_to_12h(coerce_to_time_obj(appt_copy["Out Time"]))
            elif "out_time" in appt_copy:
                appt_copy["out_time"] = time_to_12h(coerce_to_time_obj(appt_copy["out_time"]))
            formatted_prostho.append(appt_copy)

        _render_appointment_cards(formatted_prostho, "#f5576c")
    else:
        st.info("✅ No Prostho patients assigned today.")

    st.markdown("---")

    # ── Refresh button ─────────────────────────────────────────────────────────
    if st.button("🔄 Refresh", key="my_workload_refresh"):
        st.session_state.df = None
        st.cache_data.clear()
        st.rerun()

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


def render() -> None:
    st.markdown("## 👤 My Workload (Current Assignments)")

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

    # ── Display Summary Cards (Mobile-Optimized) ──────────────────────────────
    st.markdown("### 📋 Today's Assignment Summary")

    total_count = len(my_appointments)
    endo_count = len(endo_appointments)
    prostho_count = len(prostho_appointments)

    # Create responsive card layout
    st.markdown("""
    <style>
    .summary-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        color: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 12px;
        transition: transform 0.2s;
    }
    .summary-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
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
        font-size: 32px;
        font-weight: bold;
        margin: 10px 0;
    }
    .summary-card-label {
        font-size: 14px;
        opacity: 0.9;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    </style>
    """, unsafe_allow_html=True)

    # Create three columns with responsive cards
    cols = st.columns(3, gap="medium")

    with cols[0]:
        st.markdown(f"""
        <div class="summary-card summary-card-total">
            <div class="summary-card-label">👤 Total Patients</div>
            <div class="summary-card-number">{total_count}</div>
        </div>
        """, unsafe_allow_html=True)

    with cols[1]:
        st.markdown(f"""
        <div class="summary-card summary-card-endo">
            <div class="summary-card-label">🦷 Endo Patients</div>
            <div class="summary-card-number">{endo_count}</div>
        </div>
        """, unsafe_allow_html=True)

    with cols[2]:
        st.markdown(f"""
        <div class="summary-card summary-card-prostho">
            <div class="summary-card-label">👄 Prostho Patients</div>
            <div class="summary-card-number">{prostho_count}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # ── Endo Appointments ──────────────────────────────────────────────────────
    st.markdown("### 🦷 Endodontics (Endo)")

    if endo_appointments:
        endo_df = pd.DataFrame(endo_appointments)
        # Format times to 12-hour format
        if "In Time" in endo_df.columns:
            endo_df["In Time"] = endo_df["In Time"].apply(
                lambda x: time_to_12h(coerce_to_time_obj(x)) if x else ""
            )
        if "Out Time" in endo_df.columns:
            endo_df["Out Time"] = endo_df["Out Time"].apply(
                lambda x: time_to_12h(coerce_to_time_obj(x)) if x else ""
            )
        display_cols = [c for c in [
            "Patient Name", "In Time", "Out Time", "DR.", "OP", "Procedure", "STATUS"
        ] if c in endo_df.columns]
        st.dataframe(
            endo_df[display_cols],
            width='stretch',
            hide_index=True,
        )
    else:
        st.info("No Endo patients assigned today.")

    st.markdown("---")

    # ── Prostho Appointments ───────────────────────────────────────────────────
    st.markdown("### 👄 Prosthodontics (Prostho)")

    if prostho_appointments:
        prostho_df = pd.DataFrame(prostho_appointments)
        # Format times to 12-hour format
        if "In Time" in prostho_df.columns:
            prostho_df["In Time"] = prostho_df["In Time"].apply(
                lambda x: time_to_12h(coerce_to_time_obj(x)) if x else ""
            )
        if "Out Time" in prostho_df.columns:
            prostho_df["Out Time"] = prostho_df["Out Time"].apply(
                lambda x: time_to_12h(coerce_to_time_obj(x)) if x else ""
            )
        display_cols = [c for c in [
            "Patient Name", "In Time", "Out Time", "DR.", "OP", "Procedure", "STATUS"
        ] if c in prostho_df.columns]
        st.dataframe(
            prostho_df[display_cols],
            width='stretch',
            hide_index=True,
        )
    else:
        st.info("No Prostho patients assigned today.")

    st.markdown("---")

    # ── Refresh button ─────────────────────────────────────────────────────────
    if st.button("🔄 Refresh", key="my_workload_refresh"):
        st.session_state.df = None
        st.cache_data.clear()
        st.rerun()

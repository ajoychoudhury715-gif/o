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


def render() -> None:
    st.markdown("## 👤 My Workload (Today)")

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

    # ── Get my appointments ────────────────────────────────────────────────────
    my_appointments = []
    assistant_upper = str(current_user).strip().upper()

    for _, row in df.iterrows():
        status = str(row.get("STATUS", "")).strip().upper()
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

    for appt in my_appointments:
        doctor = str(appt.get("DR.", "")).strip().upper()
        from services.utils import norm_name
        doctor_key = norm_name(doctor)
        specialty = doctor_dept_map.get(doctor_key, "").upper()

        if specialty == "ENDO":
            endo_appointments.append(appt)
        elif specialty == "PROSTHO":
            prostho_appointments.append(appt)
        else:
            # Default to ENDO if specialty is unknown
            endo_appointments.append(appt)

    # ── Display Summary Metrics ────────────────────────────────────────────────
    st.markdown("### 📋 Today's Assignment Summary")

    col1, col2, col3 = st.columns(3)
    col1.metric("👤 Total Patients", len(my_appointments))
    col2.metric("🦷 Endo Patients", len(endo_appointments))
    col3.metric("👄 Prostho Patients", len(prostho_appointments))

    st.markdown("---")

    # ── Endo Appointments ──────────────────────────────────────────────────────
    st.markdown("### 🦷 Endodontics (Endo)")

    if endo_appointments:
        endo_df = pd.DataFrame(endo_appointments)
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

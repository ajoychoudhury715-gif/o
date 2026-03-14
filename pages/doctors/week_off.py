# pages/doctors/week_off.py
"""Doctor week off management."""

from __future__ import annotations
import streamlit as st
import pandas as pd

from data.profile_repo import load_doctors, save_profiles, DOCTOR_KIND
from services.profiles_cache import get_profiles_cache


WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
WEEKDAY_ABBREV = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]


def render() -> None:
    st.markdown("## 📋 Doctor Week Off Management")

    cache = get_profiles_cache(st.session_state.get("profiles_cache_bust", 0))
    doctors = sorted(cache.get("doctors_list") or [])

    if not doctors:
        st.info("No doctors found. Add doctors first.")
        return

    col_refresh = st.columns([4, 1])[1]
    with col_refresh:
        if st.button("🔄 Refresh", width='stretch', key="weekoff_refresh"):
            st.session_state.profiles_cache_bust = st.session_state.get("profiles_cache_bust", 0) + 1
            st.rerun()

    # Load doctors profile data
    doctors_df = load_doctors(st.session_state.get("profiles_cache_bust", 0))

    st.markdown("### 🏥 Set Weekly Off Days")
    st.caption("Select the days each doctor is off during the week.")

    # Create selection matrix
    data = []
    for _, row in doctors_df.iterrows():
        name = str(row.get("name", "")).strip().upper()
        if not name:
            continue
        status = str(row.get("status", "")).strip().upper()
        if status and status not in ("", "ACTIVE"):
            continue

        weekly_off_str = str(row.get("weekly_off", "")).strip()
        selected_days = _parse_selected_days(weekly_off_str)

        data.append({
            "Doctor": name,
            "MON": "MON" in selected_days,
            "TUE": "TUE" in selected_days,
            "WED": "WED" in selected_days,
            "THU": "THU" in selected_days,
            "FRI": "FRI" in selected_days,
            "SAT": "SAT" in selected_days,
            "SUN": "SUN" in selected_days,
            "_profile_id": row.get("profile_id", ""),
        })

    if not data:
        st.info("No active doctors found.")
        return

    edit_df = pd.DataFrame(data)
    day_cols = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]

    edited_df = st.data_editor(
        edit_df,
        column_config={
            "Doctor": st.column_config.Column(width="medium"),
            "MON": st.column_config.CheckboxColumn(width="small"),
            "TUE": st.column_config.CheckboxColumn(width="small"),
            "WED": st.column_config.CheckboxColumn(width="small"),
            "THU": st.column_config.CheckboxColumn(width="small"),
            "FRI": st.column_config.CheckboxColumn(width="small"),
            "SAT": st.column_config.CheckboxColumn(width="small"),
            "SUN": st.column_config.CheckboxColumn(width="small"),
        },
        hide_index=True,
        width='stretch',
        key="doctor_weekoff_editor",
    )

    if st.button("💾 Save Week Off", width='stretch', key="btn_save_weekoff"):
        _save_week_off(edited_df, doctors_df, day_cols)
        st.toast("Doctor week off updated!", icon="💾")
        st.session_state.profiles_cache_bust = st.session_state.get("profiles_cache_bust", 0) + 1
        st.rerun()


def _parse_selected_days(weekly_off_str: str) -> set[str]:
    """Parse comma-separated weekday string into a set of abbreviations."""
    if not weekly_off_str:
        return set()
    days = set()
    for part in weekly_off_str.split(","):
        part = part.strip().upper()
        if part in WEEKDAY_ABBREV:
            days.add(part)
    return days


def _save_week_off(edited_df: pd.DataFrame, original_df: pd.DataFrame, day_cols: list[str]) -> None:
    """Save updated week off data back to profiles."""
    try:
        updated_df = original_df.copy()

        for edit_idx, edit_row in edited_df.iterrows():
            doctor_name = str(edit_row.get("Doctor", "")).strip().upper()

            # Find matching row in original df
            orig_idx = None
            for idx, orig_row in updated_df.iterrows():
                if str(orig_row.get("name", "")).strip().upper() == doctor_name:
                    orig_idx = idx
                    break

            if orig_idx is None:
                continue

            # Build weekly_off string from selected days
            selected_days = []
            for day_col in day_cols:
                if edit_row.get(day_col, False):
                    selected_days.append(day_col)

            weekly_off_str = ",".join(selected_days) if selected_days else ""
            updated_df.at[orig_idx, "weekly_off"] = weekly_off_str

        # Save back to database
        save_profiles(updated_df, DOCTOR_KIND)
    except Exception as e:
        st.error(f"❌ Failed to save week off: {e}")

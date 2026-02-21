# pages/doctors/manage_profiles.py
"""Doctor profile CRUD page."""

from __future__ import annotations
import streamlit as st
import pandas as pd

from data.profile_repo import load_doctors, save_profiles, delete_profile
from state.session import bust_profiles_cache
from components.profile_form import render_add_doctor_form, render_edit_doctor_form
from config.constants import DEFAULT_DEPARTMENTS


def render() -> None:
    st.markdown("## 🩺 Manage Doctors")

    cache_bust = st.session_state.get("profiles_cache_bust", 0)
    df = load_doctors(cache_bust)

    col_search, col_refresh = st.columns([4, 1])
    with col_search:
        search_q = st.text_input(
            "🔍 Search doctors",
            placeholder="Name / Department / Specialisation…",
            key="dr_search",
            label_visibility="collapsed",
        )
    with col_refresh:
        if st.button("🔄", use_container_width=True, key="dr_refresh"):
            bust_profiles_cache()
            st.rerun()

    all_depts = _get_departments(df)
    render_add_doctor_form(departments=all_depts, on_save=lambda row: _on_add(df, row))

    # Filter
    view_df = df.copy()
    if search_q.strip():
        q = search_q.strip().lower()
        mask = (
            view_df.get("name", pd.Series(dtype=str)).astype(str).str.lower().str.contains(q, na=False)
            | view_df.get("department", pd.Series(dtype=str)).astype(str).str.lower().str.contains(q, na=False)
            | view_df.get("specialisation", pd.Series(dtype=str)).astype(str).str.lower().str.contains(q, na=False)
        )
        view_df = view_df[mask]

    st.markdown(f"**{len(view_df)} doctor(s)**")

    if view_df.empty:
        st.info("No doctors found. Add one above.")
        return

    for _, row in view_df.iterrows():
        row_dict = row.to_dict()
        profile_id = str(row_dict.get("profile_id", "")).strip()
        edit_key = f"editing_dr_{profile_id}"

        if st.session_state.get(edit_key):
            render_edit_doctor_form(
                row=row_dict,
                departments=all_depts,
                on_save=lambda updated: _on_edit(df, updated, edit_key),
                on_cancel=lambda: _cancel_edit(edit_key),
                form_key=f"edit_dr_form_{profile_id}",
            )
        else:
            _render_doctor_card(row_dict, profile_id, edit_key)

        st.divider()


def _render_doctor_card(row: dict, profile_id: str, edit_key: str) -> None:
    name = str(row.get("name", "") or "—")
    spec = str(row.get("specialisation", "") or "")
    dept = str(row.get("department", "") or "")
    phone = str(row.get("phone", "") or "")
    reg = str(row.get("reg_number", "") or "")
    active = bool(row.get("is_active", True))
    status_color = "#22c55e" if active else "#ef4444"
    status_label = "Active" if active else "Inactive"

    # Build optional detail rows
    details = ""
    if phone:
        details += f"<div style='font-size:12px;color:#94a3b8;'>📱 {phone}</div>"
    if reg:
        details += f"<div style='font-size:12px;color:#94a3b8;'>📋 Reg: {reg}</div>"

    st.markdown(
        f"""<div class="profile-card">
          <div style="display:flex;justify-content:space-between;align-items:start;gap:8px;">
            <div style="min-width:0;flex:1;">
              <div style="font-size:16px;font-weight:700;color:#1e293b;word-break:break-word;">🩺 {name}</div>
              <div style="font-size:13px;color:#94a3b8;margin-top:2px;">
                {spec} {("· " + dept) if dept else ""}
              </div>
              {details}
            </div>
            <span style="flex-shrink:0;background:{status_color}22;color:{status_color};padding:2px 10px;border-radius:12px;font-size:11px;font-weight:600;">{status_label}</span>
          </div>
        </div>""",
        unsafe_allow_html=True,
    )
    c1, c2 = st.columns(2)
    with c1:
        if st.button("✏️ Edit", key=f"edit_dr_btn_{profile_id}", use_container_width=True):
            st.session_state[edit_key] = True
            st.rerun()
    with c2:
        if st.button("🗑️ Delete", key=f"del_dr_btn_{profile_id}", use_container_width=True):
            _on_delete(profile_id)


def _get_departments(df) -> list[str]:
    if df is not None and "department" in df.columns:
        depts = df["department"].dropna().astype(str).str.strip().unique().tolist()
        return sorted(set(depts + list(DEFAULT_DEPARTMENTS.keys())) - {""})
    return sorted(DEFAULT_DEPARTMENTS.keys())


def _on_add(df, row: dict) -> None:
    new_df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    save_profiles(new_df, "Doctors")
    bust_profiles_cache()
    st.toast(f"Doctor '{row.get('name')}' added!", icon="✅")
    st.rerun()


def _on_edit(df, updated: dict, edit_key: str) -> None:
    profile_id = str(updated.get("profile_id", "")).strip()
    mask = df["profile_id"].astype(str).str.strip() == profile_id
    if mask.any():
        for col, val in updated.items():
            if col in df.columns:
                df.loc[mask, col] = val
    else:
        df = pd.concat([df, pd.DataFrame([updated])], ignore_index=True)
    save_profiles(df, "Doctors")
    bust_profiles_cache()
    st.session_state[edit_key] = False
    st.toast("Doctor updated!", icon="✅")
    st.rerun()


def _on_delete(profile_id: str) -> None:
    delete_profile(profile_id, "Doctors")
    bust_profiles_cache()
    st.toast("Doctor deleted.", icon="🗑️")
    st.rerun()


def _cancel_edit(edit_key: str) -> None:
    st.session_state[edit_key] = False
    st.rerun()

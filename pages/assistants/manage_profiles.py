# pages/assistants/manage_profiles.py
"""Assistant profile CRUD page."""

from __future__ import annotations
import streamlit as st
import pandas as pd

from data.profile_repo import load_assistants, save_profiles, delete_profile
from state.session import bust_profiles_cache
from components.profile_form import render_add_assistant_form, render_edit_assistant_form
from config.constants import DEFAULT_DEPARTMENTS


def render() -> None:
    st.markdown("## 👥 Manage Assistants")

    cache_bust = st.session_state.get("profiles_cache_bust", 0)
    df = load_assistants(cache_bust)

    # ── Toolbar ────────────────────────────────────────────────────────────────
    col_search, col_refresh = st.columns([4, 1])
    with col_search:
        search_q = st.text_input(
            "🔍 Search assistants",
            placeholder="Name / Department…",
            key="asst_search",
            label_visibility="collapsed",
        )
    with col_refresh:
        if st.button("🔄", use_container_width=True, key="asst_refresh"):
            bust_profiles_cache()
            st.rerun()

    # ── Add form ───────────────────────────────────────────────────────────────
    all_depts = _get_departments(df)
    render_add_assistant_form(
        departments=all_depts,
        on_save=lambda row: _on_add(df, row),
    )

    # ── Filter ─────────────────────────────────────────────────────────────────
    view_df = df.copy()
    if search_q.strip():
        q = search_q.strip().lower()
        mask = (
            view_df.get("name", pd.Series(dtype=str)).astype(str).str.lower().str.contains(q, na=False)
            | view_df.get("department", pd.Series(dtype=str)).astype(str).str.lower().str.contains(q, na=False)
            | view_df.get("role", pd.Series(dtype=str)).astype(str).str.lower().str.contains(q, na=False)
        )
        view_df = view_df[mask]

    st.markdown(f"**{len(view_df)} assistant(s)**")

    if view_df.empty:
        st.info("No assistants found. Add one above.")
        return

    # ── List cards ─────────────────────────────────────────────────────────────
    for _, row in view_df.iterrows():
        row_dict = row.to_dict()
        profile_id = str(row_dict.get("profile_id", "")).strip()
        edit_key = f"editing_asst_{profile_id}"

        if st.session_state.get(edit_key):
            render_edit_assistant_form(
                row=row_dict,
                departments=all_depts,
                on_save=lambda updated: _on_edit(df, updated, edit_key),
                on_cancel=lambda: _cancel_edit(edit_key),
                form_key=f"edit_asst_form_{profile_id}",
            )
        else:
            _render_assistant_card(row_dict, profile_id, edit_key, df)

        st.divider()


def _render_assistant_card(row: dict, profile_id: str, edit_key: str, df) -> None:
    name = str(row.get("name", "") or "—")
    role = str(row.get("role", "") or "")
    dept = str(row.get("department", "") or "")
    phone = str(row.get("phone", "") or "")
    active = bool(row.get("is_active", True))
    wo = str(row.get("weekly_off", "") or "")
    experience = row.get("experience", 0)

    status_color = "#22c55e" if active else "#ef4444"
    status_label = "Active" if active else "Inactive"

    st.markdown(
        f"""<div class="profile-card">
          <div style="display:flex;justify-content:space-between;align-items:start;gap:8px;">
            <div style="min-width:0;flex:1;">
              <div style="font-size:16px;font-weight:700;color:#f1f5f9;word-break:break-word;">👤 {name}</div>
              <div style="font-size:13px;color:#94a3b8;margin-top:2px;">
                {role} {("· " + dept) if dept else ""}
              </div>
              {("<div style='font-size:12px;color:#94a3b8;'>📱 " + phone + "</div>") if phone else ""}
              {("<div style='font-size:12px;color:#94a3b8;'>🗓 Off: " + wo + "</div>") if wo else ""}
              {("<div style='font-size:12px;color:#94a3b8;'>⏳ " + str(experience) + " yrs exp</div>") if experience else ""}
            </div>
            <span style="flex-shrink:0;background:{status_color}22;color:{status_color};padding:2px 10px;
                         border-radius:12px;font-size:11px;font-weight:600;">{status_label}</span>
          </div>
        </div>""",
        unsafe_allow_html=True,
    )
    c1, c2 = st.columns([1, 1])
    with c1:
        if st.button("✏️ Edit", key=f"edit_asst_btn_{profile_id}", use_container_width=True):
            st.session_state[edit_key] = True
            st.rerun()
    with c2:
        if st.button("🗑️ Delete", key=f"del_asst_btn_{profile_id}", use_container_width=True):
            _on_delete(profile_id)


def _get_departments(df) -> list[str]:
    if df is not None and "department" in df.columns:
        depts = df["department"].dropna().astype(str).str.strip().unique().tolist()
        return sorted(set(depts + list(DEFAULT_DEPARTMENTS.keys())) - {""})
    return sorted(DEFAULT_DEPARTMENTS.keys())


def _on_add(df, row: dict) -> None:
    new_df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    save_profiles(new_df, "Assistants")
    bust_profiles_cache()
    st.toast(f"Assistant '{row.get('name')}' added!", icon="✅")
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
    save_profiles(df, "Assistants")
    bust_profiles_cache()
    st.session_state[edit_key] = False
    st.toast("Assistant updated!", icon="✅")
    st.rerun()


def _on_delete(profile_id: str) -> None:
    delete_profile(profile_id, "Assistants")
    bust_profiles_cache()
    st.toast("Assistant deleted.", icon="🗑️")
    st.rerun()


def _cancel_edit(edit_key: str) -> None:
    st.session_state[edit_key] = False
    st.rerun()

# pages/doctors/overview.py
"""Doctor overview — at-a-glance status of all doctors today."""

from __future__ import annotations
import streamlit as st
import pandas as pd

from data.profile_repo import load_doctors
from services.schedule_ops import ensure_schedule_columns, add_computed_columns


def render() -> None:
    st.markdown("## 🩺 Doctors Overview")

    df_sched = st.session_state.get("df")
    if df_sched is None:
        from data.schedule_repo import load_schedule
        from services.schedule_ops import ensure_row_ids
        df_sched = load_schedule()
        df_sched = ensure_schedule_columns(df_sched)
        df_sched = ensure_row_ids(df_sched)
        df_sched = add_computed_columns(df_sched)
        st.session_state.df = df_sched
    else:
        df_sched = ensure_schedule_columns(df_sched)
        df_sched = add_computed_columns(df_sched)

    cache_bust = st.session_state.get("profiles_cache_bust", 0)
    df_doctors = load_doctors(cache_bust)

    if st.button("🔄 Refresh", key="dr_overview_refresh"):
        st.session_state.df = None
        st.cache_data.clear()
        st.rerun()

    if df_doctors.empty:
        st.info("No doctors found. Add doctors in Manage Profiles.")
        return

    # Build per-doctor stats
    stats = []
    for _, dr_row in df_doctors.iterrows():
        name = str(dr_row.get("name", "") or "").strip()
        if not name:
            continue
        dept = str(dr_row.get("department", "") or "")
        spec = str(dr_row.get("specialisation", "") or "")
        active = bool(dr_row.get("is_active", True))

        # Find appointments for this doctor
        dr_upper = name.upper()
        mask = df_sched.get("DR.", pd.Series(dtype=str)).astype(str).str.strip().str.upper() == dr_upper
        dr_appts = df_sched[mask]

        total = len(dr_appts)
        ongoing = int(dr_appts.get("Is_Ongoing", pd.Series(dtype=bool)).sum()) if "Is_Ongoing" in dr_appts.columns else 0
        done = len(dr_appts[dr_appts.get("STATUS", "").astype(str).str.upper().isin(["DONE", "COMPLETED"])]) if "STATUS" in dr_appts.columns else 0
        pending = total - ongoing - done

        stats.append({
            "name": name,
            "dept": dept,
            "spec": spec,
            "active": active,
            "total": total,
            "ongoing": ongoing,
            "done": done,
            "pending": pending,
        })

    # ── Summary metrics ────────────────────────────────────────────────────────
    active_doctors = sum(1 for s in stats if s["active"])
    total_appts = sum(s["total"] for s in stats)
    total_ongoing = sum(s["ongoing"] for s in stats)

    c1, c2, c3 = st.columns(3)
    c1.metric("👨‍⚕️ Active Doctors", active_doctors)
    c2.metric("📅 Total Appointments", total_appts)
    c3.metric("🔴 Ongoing Now", total_ongoing)

    st.markdown("---")

    # ── Doctor cards ───────────────────────────────────────────────────────────
    cols_per_row = 2
    for row_start in range(0, len(stats), cols_per_row):
        cols = st.columns(cols_per_row)
        for col_idx, s in enumerate(stats[row_start:row_start + cols_per_row]):
            with cols[col_idx]:
                color = "#22c55e" if s["active"] else "#64748b"
                st.markdown(
                    f"""<div class="profile-card" style="margin-bottom:8px;">
                      <div style="display:flex;justify-content:space-between;">
                        <div>
                          <div style="font-weight:700;color:#f1f5f9;font-size:15px;">🩺 {s['name']}</div>
                          <div style="font-size:12px;color:#94a3b8;">
                            {s['spec']} {('· ' + s['dept']) if s['dept'] else ''}
                          </div>
                        </div>
                        <span style="color:{color};font-size:11px;font-weight:600;">
                          {'● Active' if s['active'] else '○ Inactive'}
                        </span>
                      </div>
                      <div style="display:flex;gap:12px;margin-top:8px;">
                        <span style="font-size:12px;color:#94a3b8;">📅 {s['total']} appts</span>
                        <span style="font-size:12px;color:#ef4444;">🔴 {s['ongoing']} ongoing</span>
                        <span style="font-size:12px;color:#22c55e;">✅ {s['done']} done</span>
                      </div>
                    </div>""",
                    unsafe_allow_html=True,
                )

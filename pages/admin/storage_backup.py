# pages/admin/storage_backup.py
"""Backup/download, clear allotments, storage management."""

from __future__ import annotations
import io
import json
import streamlit as st
import pandas as pd

from services.schedule_ops import ensure_schedule_columns
from state.save_manager import save_now
from config.settings import USE_SUPABASE, get_supabase_config
from data.supabase_client import get_supabase_client


@st.cache_data(ttl=60)
def _check_supabase_connection() -> dict[str, str]:
    """Check Supabase connection (cached 60s)."""
    if not USE_SUPABASE:
        return {"status": "disabled"}

    try:
        url, key, _, _, _ = get_supabase_config()
    except Exception as e:
        return {"status": "error_config", "msg": str(e)[:100]}

    if not url or not key:
        return {"status": "not_configured"}

    try:
        client = get_supabase_client(url, key)
        if client is None:
            return {"status": "client_failed"}
        resp = client.table("profiles").select("profile_id").limit(1).execute()
        return {"status": "connected"}
    except Exception as e:
        return {"status": "connection_error", "msg": str(e)[:150]}


def _render_supabase_status() -> None:
    """Display Supabase connection status (cached)."""
    result = _check_supabase_connection()
    status = result.get("status")

    if status == "disabled":
        st.info("⚙️ Supabase disabled (Excel-only mode)")
    elif status == "error_config":
        st.error(f"❌ **Error reading config** — {result.get('msg')}")
    elif status == "not_configured":
        st.error("❌ **Supabase not configured** — Missing credentials in secrets")
        with st.expander("Debug info"):
            st.write("Ensure `.streamlit/secrets.toml` has:")
            st.code("""[supabase]
url = "your-supabase-url"
key = "your-supabase-key"
""")
    elif status == "client_failed":
        st.error("❌ **Supabase connection failed** — Could not create client")
    elif status == "connection_error":
        st.error(f"❌ **Supabase connection error** — {result.get('msg')}")
    elif status == "connected":
        st.success("✅ **Supabase connected** — All systems operational")


def render() -> None:
    st.markdown("## 💾 Storage & Backup")

    # ── Supabase connection status ─────────────────────────────────────────────
    _render_supabase_status()

    st.markdown("---")

    df = st.session_state.get("df")
    if df is None:
        from data.schedule_repo import load_schedule
        df = load_schedule()
        st.session_state.df = df

    df = ensure_schedule_columns(df)

    # ── Download section ───────────────────────────────────────────────────────
    st.markdown("### 📥 Download Schedule")
    col_csv, col_json, col_xlsx = st.columns(3)

    with col_csv:
        csv_data = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "📄 Download CSV",
            data=csv_data,
            file_name="schedule.csv",
            mime="text/csv",
            use_container_width=True,
            key="dl_csv",
        )
    with col_json:
        try:
            json_data = df.to_json(orient="records", indent=2).encode("utf-8")
        except Exception:
            json_data = b"[]"
        st.download_button(
            "📋 Download JSON",
            data=json_data,
            file_name="schedule.json",
            mime="application/json",
            use_container_width=True,
            key="dl_json",
        )
    with col_xlsx:
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Schedule")
        buf.seek(0)
        st.download_button(
            "📊 Download Excel",
            data=buf.getvalue(),
            file_name="schedule.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            key="dl_xlsx",
        )

    st.markdown("---")

    # ── Force save ─────────────────────────────────────────────────────────────
    st.markdown("### 💾 Force Save")
    st.caption("Force-save the current in-memory schedule to storage (skips conflict check).")
    if st.button("⚡ Force Save Now", use_container_width=True, key="btn_force_save"):
        try:
            save_now(df, message="Admin force save", ignore_conflict=True)
            st.success("✅ Force save complete.")
        except Exception as e:
            st.error(f"Save failed: {e}")

    st.markdown("---")

    # ── Clear allotments ───────────────────────────────────────────────────────
    st.markdown("### 🗑️ Clear Allotments")
    st.warning(
        "⚠️ **Danger Zone**: Clearing allotments will remove all FIRST / SECOND / Third assignments "
        "from the current schedule. This cannot be undone."
    )

    confirm = st.checkbox(
        "I understand this action is irreversible",
        key="confirm_clear",
    )
    if confirm:
        if st.button("🗑️ Clear All Allotments", use_container_width=True, key="btn_clear_allotments"):
            cleared = df.copy()
            for col in ["FIRST", "SECOND", "Third"]:
                if col in cleared.columns:
                    cleared[col] = ""
            cleared.attrs = df.attrs.copy()
            st.session_state.df = cleared
            save_now(cleared, message="Cleared allotments", ignore_conflict=True)
            st.success("✅ All allotments cleared and saved.")
            st.rerun()

    st.markdown("---")

    # ── Clear entire schedule ──────────────────────────────────────────────────
    st.markdown("### ☢️ Clear Entire Schedule")
    st.error("⛔ **Extreme Danger**: This deletes ALL appointments from the schedule.")

    confirm2 = st.checkbox(
        "I want to permanently delete ALL appointments",
        key="confirm_clear_all",
    )
    if confirm2:
        confirm3 = st.text_input(
            "Type DELETE to confirm",
            key="confirm_clear_all_text",
        )
        if confirm3 == "DELETE":
            if st.button("☢️ Delete All Appointments", use_container_width=True, key="btn_nuke_schedule"):
                empty_df = ensure_schedule_columns(pd.DataFrame())
                empty_df.attrs = df.attrs.copy()
                st.session_state.df = empty_df
                save_now(empty_df, message="Schedule cleared", ignore_conflict=True)
                st.success("Schedule cleared.")
                st.rerun()

    st.markdown("---")

    # ── Schedule info ──────────────────────────────────────────────────────────
    st.markdown("### ℹ️ Schedule Info")
    meta = getattr(df, "attrs", {}).get("meta", {})
    version = meta.get("save_version", "unknown")
    saved_at = meta.get("saved_at", "unknown")

    col_a, col_b, col_c = st.columns(3)
    col_a.metric("📋 Rows", len(df))
    col_b.metric("📌 Version", str(version))
    col_c.metric("🕐 Last Saved", str(saved_at)[:16] if saved_at != "unknown" else "—")

    with st.expander("📋 Raw meta", expanded=False):
        st.json(meta)

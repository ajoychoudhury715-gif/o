# data/attendance_repo.py
"""Punch-in/out attendance CRUD."""

from __future__ import annotations
import pandas as pd
import streamlit as st

from config.settings import (
    USE_SUPABASE, SUPABASE_ATTENDANCE_TABLE,
    EXCEL_ATTENDANCE_SHEET, get_supabase_config,
)
from config.constants import ATTENDANCE_COLUMNS
from data.supabase_client import get_supabase_client
from data.excel_ops import load_sheet, save_sheet


def _get_client():
    if not USE_SUPABASE:
        print("[PUNCH DEBUG] Supabase disabled (USE_SUPABASE=False)")
        return None
    url, key, *_ = get_supabase_config()
    if not url or not key:
        print("[PUNCH DEBUG] Supabase config missing (url or key)")
        return None
    client = get_supabase_client(url, key)
    if client:
        print("[PUNCH DEBUG] Supabase client created successfully")
    else:
        print("[PUNCH DEBUG] Failed to create Supabase client")
    return client


@st.cache_data(ttl=30)
def load_attendance() -> pd.DataFrame:
    client = _get_client()
    if client:
        try:
            print(f"[LOAD ATTENDANCE DEBUG] Querying Supabase table '{SUPABASE_ATTENDANCE_TABLE}'")
            resp = client.table(SUPABASE_ATTENDANCE_TABLE).select("*").execute()
            data = resp.data or []
            print(f"[LOAD ATTENDANCE DEBUG] Got {len(data)} records from Supabase")
            if data:
                print(f"[LOAD ATTENDANCE DEBUG] Sample record: {data[0]}")
            df = pd.DataFrame(data)
            if not df.empty:
                print(f"[LOAD ATTENDANCE DEBUG] DataFrame shape: {df.shape}, columns: {list(df.columns)}")
                for col in ATTENDANCE_COLUMNS:
                    if col not in df.columns:
                        df[col] = ""
                return df
            else:
                print(f"[LOAD ATTENDANCE DEBUG] DataFrame is empty")
                return df
        except Exception as e:
            print(f"[LOAD ATTENDANCE ERROR] Supabase query failed: {type(e).__name__}: {str(e)}")
    return load_sheet(EXCEL_ATTENDANCE_SHEET, ATTENDANCE_COLUMNS)


def get_today_punch_map(date_str: str) -> dict[str, dict[str, str]]:
    """Return {ASSISTANT_UPPER: {punch_in, punch_out}} for a date."""
    df = load_attendance()
    result: dict[str, dict[str, str]] = {}
    if df.empty:
        print(f"[PUNCH MAP DEBUG] DataFrame empty, returning no punch records")
        return result

    print(f"[PUNCH MAP DEBUG] DataFrame shape: {df.shape}, columns: {list(df.columns)}")

    # Normalize column names for Supabase (lowercase) vs Excel (uppercase)
    col_map = {}
    for col in df.columns:
        col_map[col.upper()] = col

    # Get actual column names (handle both Supabase lowercase and Excel uppercase)
    date_col = col_map.get("DATE")
    asst_col = col_map.get("ASSISTANT")
    pin_col = col_map.get("PUNCH IN") or col_map.get("PUNCH_IN")
    pout_col = col_map.get("PUNCH OUT") or col_map.get("PUNCH_OUT")

    # Fallback if columns not found in map
    if not date_col:
        date_col = "DATE" if "DATE" in df.columns else ("date" if "date" in df.columns else None)
    if not asst_col:
        asst_col = "ASSISTANT" if "ASSISTANT" in df.columns else ("assistant" if "assistant" in df.columns else None)
    if not pin_col:
        pin_col = "PUNCH IN" if "PUNCH IN" in df.columns else ("punch_in" if "punch_in" in df.columns else None)
    if not pout_col:
        pout_col = "PUNCH OUT" if "PUNCH OUT" in df.columns else ("punch_out" if "punch_out" in df.columns else None)

    print(f"[PUNCH MAP DEBUG] Resolved columns: date={date_col}, asst={asst_col}, pin={pin_col}, pout={pout_col}")

    # If essential columns missing, return empty
    if not date_col or not asst_col:
        print(f"[PUNCH MAP ERROR] Missing essential columns!")
        return result

    # Filter by date
    mask = df[date_col].astype(str).str.strip() == date_str
    print(f"[PUNCH MAP DEBUG] Found {mask.sum()} records for date {date_str}")
    for _, row in df[mask].iterrows():
        name = str(row.get(asst_col, "")).strip().upper()
        if name:
            pin = str(row.get(pin_col, "") or "").strip() if pin_col else ""
            pout = str(row.get(pout_col, "") or "").strip() if pout_col else ""
            result[name] = {
                "punch_in": pin,
                "punch_out": pout,
            }
            print(f"[PUNCH MAP DEBUG] Added {name}: punch_in={pin}, punch_out={pout}")
    return result


def punch_in(date_str: str, assistant: str, time_str: str) -> bool:
    """Punch in assistant. Try Supabase first, fallback to Excel."""
    # Normalize assistant name to match database
    assistant_norm = str(assistant).strip().upper()

    client = _get_client()
    if client:
        try:
            # Check if record exists
            resp = client.table(SUPABASE_ATTENDANCE_TABLE).select("id").eq("date", date_str).eq("assistant", assistant_norm).limit(1).execute()
            existing = resp.data or []
            print(f"[PUNCH IN DEBUG] Supabase query for existing record: date={date_str}, assistant={assistant_norm}, found={len(existing)} records")

            if existing:
                print(f"[PUNCH IN DEBUG] Updating existing record")
                result = client.table(SUPABASE_ATTENDANCE_TABLE).update({"punch_in": time_str}).eq("date", date_str).eq("assistant", assistant_norm).execute()
                print(f"[PUNCH IN DEBUG] Update response: {result}")
            else:
                print(f"[PUNCH IN DEBUG] Inserting new record")
                result = client.table(SUPABASE_ATTENDANCE_TABLE).insert({
                    "date": date_str, "assistant": assistant_norm,
                    "punch_in": time_str, "punch_out": None,
                }).execute()
                print(f"[PUNCH IN DEBUG] Insert response: {result}")
            load_attendance.clear()  # Clear cache after successful punch
            st.success(f"✅ {assistant_norm} punched in at {time_str}")
            return True
        except Exception as e:
            print(f"[PUNCH IN ERROR] Supabase failed: {type(e).__name__}: {str(e)}")
            st.error(f"❌ Supabase punch in failed: {str(e)}")
            return False

    print(f"[PUNCH IN DEBUG] No Supabase client available, not attempting Excel fallback (file doesn't exist)")
    st.error("❌ Supabase not configured and Excel backup not available")
    return False


def punch_out(date_str: str, assistant: str, time_str: str) -> bool:
    """Punch out assistant. Try Supabase first, fallback to Excel."""
    # Normalize assistant name to match database
    assistant_norm = str(assistant).strip().upper()

    client = _get_client()
    if client:
        try:
            print(f"[PUNCH OUT DEBUG] Updating punch_out for date={date_str}, assistant={assistant_norm}, time={time_str}")
            result = client.table(SUPABASE_ATTENDANCE_TABLE).update({"punch_out": time_str}).eq("date", date_str).eq("assistant", assistant_norm).execute()
            print(f"[PUNCH OUT DEBUG] Update response: {result}")
            # Verify the update actually happened
            if hasattr(result, 'data') and result.data:
                print(f"[PUNCH OUT DEBUG] Update successful, {len(result.data)} rows updated")
            load_attendance.clear()  # Clear cache after successful punch
            st.success(f"✅ {assistant_norm} punched out at {time_str}")
            return True
        except Exception as e:
            print(f"[PUNCH OUT ERROR] Supabase failed: {type(e).__name__}: {str(e)}")
            st.error(f"❌ Supabase punch out failed: {str(e)}")
            return False

    print(f"[PUNCH OUT DEBUG] No Supabase client available")
    st.error("❌ Supabase not configured")
    return False  # No matching record found


def reset_attendance(date_str: str, assistant: str) -> bool:
    """Reset (delete) punch records for assistant. Try Supabase first, fallback to Excel."""
    # Normalize assistant name to match database
    assistant_norm = str(assistant).strip().upper()

    client = _get_client()
    if client:
        try:
            client.table(SUPABASE_ATTENDANCE_TABLE).delete().eq("date", date_str).eq("assistant", assistant_norm).execute()
            load_attendance.clear()  # Clear cache after deletion
            return True
        except Exception as e:
            st.warning(f"Supabase reset failed: {str(e)[:100]}. Using Excel backup.")

    # Excel fallback
    df = load_sheet(EXCEL_ATTENDANCE_SHEET, ATTENDANCE_COLUMNS)
    mask = (df["DATE"].astype(str) == date_str) & (df["ASSISTANT"].astype(str).str.upper() == assistant_norm)
    df = df[~mask].copy()
    ok = save_sheet(df, EXCEL_ATTENDANCE_SHEET)
    if ok:
        load_attendance.clear()  # Clear cache after successful delete
    return ok

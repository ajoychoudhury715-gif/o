# data/schedule_repo.py
"""Schedule CRUD.
Supabase: single row {id, payload: {columns, rows, meta}}
Excel: Sheet1
"""

from __future__ import annotations
from typing import Optional
from datetime import date as date_type
import hashlib
import pandas as pd
import streamlit as st

from config.settings import (
    USE_SUPABASE, SUPABASE_SCHEDULE_TABLE, SUPABASE_SCHEDULE_ROW_ID,
    EXCEL_SCHEDULE_SHEET, get_supabase_config, SCHEDULE_CACHE_TTL_SECONDS,
)
from config.constants import SCHEDULE_COLUMNS
from data.supabase_client import get_supabase_client
from data.excel_ops import load_sheet, save_sheet


def _get_expected_columns() -> list[str]:
    return list(SCHEDULE_COLUMNS)


def _ensure_columns(df: pd.DataFrame) -> pd.DataFrame:
    for col in _get_expected_columns():
        if col not in df.columns:
            df[col] = ""
    return df


def load_appointments_by_date(selected_date: date_type) -> pd.DataFrame:
    """Fetch appointments for a specific date from Supabase (no caching for dynamic date queries).
    
    Handles both DATE and TIMESTAMP column types for appointment_date.
    Returns a DataFrame with columns: id, patient_name, doctor, op_room, start_time, end_time, 
                                       appointment_date, status
    """
    if not USE_SUPABASE:
        return pd.DataFrame()
    
    try:
        url, key, _, _, _ = get_supabase_config()
        if not url or not key:
            return pd.DataFrame()
        
        client = get_supabase_client(url, key)
        if client is None:
            return pd.DataFrame()
        
        # Format date as ISO string (YYYY-MM-DD)
        date_str = selected_date.isoformat() if isinstance(selected_date, date_type) else str(selected_date)
        
        st.write(f"🔍 **DEBUG:** Fetching appointments for date: `{date_str}`")
        
        # Query appointments table
        # This query will work for both DATE and TIMESTAMP types by casting/comparing as dates
        try:
            resp = client.table("appointments").select("*").gte("appointment_date", date_str).lt("appointment_date", f"{date_str}T23:59:59").execute()
        except Exception as e1:
            st.write(f"⚠️ **DEBUG:** Initial query failed: {str(e1)[:100]}")
            # Fallback: try a simpler query with eq() which works better for DATE columns
            try:
                resp = client.table("appointments").select("*").eq("appointment_date", date_str).execute()
            except Exception as e2:
                st.write(f"⚠️ **DEBUG:** Fallback query failed: {str(e2)[:100]}")
                return pd.DataFrame()
        
        data = getattr(resp, "data", None)
        st.write(f"📊 **DEBUG:** Rows fetched from Supabase: {len(data) if data else 0}")
        
        if not data or not isinstance(data, list) or len(data) == 0:
            st.write("ℹ️ **DEBUG:** No appointments found for this date")
            return pd.DataFrame()
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        st.write(f"✅ **DEBUG:** Successfully loaded {len(df)} appointment(s)")
        st.write(f"📋 **DEBUG:** Columns in result: {list(df.columns)}")
        
        return df
        
    except Exception as e:
        st.error(f"Error loading appointments by date from Supabase: {e}")
        st.write(f"❌ **DEBUG:** Exception details: {str(e)}")
        return pd.DataFrame()


@st.cache_data(ttl=SCHEDULE_CACHE_TTL_SECONDS)
def _load_from_supabase_cached(url: str, key: str, table: str, row_id: str) -> Optional[pd.DataFrame]:
    try:
        client = get_supabase_client(url, key)
        if client is None:
            return None
        resp = client.table(table).select("payload").eq("id", row_id).limit(1).execute()
        data = getattr(resp, "data", None)
        if not data:
            return pd.DataFrame(columns=_get_expected_columns())
        payload = data[0].get("payload") if isinstance(data, list) else None
        if not payload:
            return pd.DataFrame(columns=_get_expected_columns())
        columns = payload.get("columns") or _get_expected_columns()
        for col in _get_expected_columns():
            if col not in columns:
                columns.append(col)
        rows = payload.get("rows") or []
        df = pd.DataFrame(rows)
        for col in columns:
            if col not in df.columns:
                df[col] = ""
        df = df[columns]
        meta = payload.get("meta")
        if isinstance(meta, dict):
            df.attrs["meta"] = dict(meta)
        return df
    except Exception as e:
        st.error(f"Error loading schedule from Supabase: {e}")
        return None


def load_schedule() -> pd.DataFrame:
    """Load the schedule from Supabase (primary) or Excel (fallback)."""
    if USE_SUPABASE:
        url, key, table, row_id, _ = get_supabase_config()
        if url and key:
            df = _load_from_supabase_cached(url, key, table, row_id)
            if df is not None:
                return _ensure_columns(df)
    df = load_sheet(EXCEL_SCHEDULE_SHEET, _get_expected_columns())
    return _ensure_columns(df)


def save_schedule(df: pd.DataFrame) -> bool:
    """Persist the schedule DataFrame."""
    if USE_SUPABASE:
        url, key, table, row_id, _ = get_supabase_config()
        if url and key:
            return _save_to_supabase(url, key, table, row_id, df)
    return save_sheet(df, EXCEL_SCHEDULE_SHEET)


def _save_to_supabase(url: str, key: str, table: str, row_id: str, df: pd.DataFrame) -> bool:
    try:
        client = get_supabase_client(url, key)
        if client is None:
            return False
        df_clean = df.copy().fillna("")
        for col in df_clean.columns:
            df_clean[col] = df_clean[col].astype(object)
        payload: dict = {
            "columns": df_clean.columns.tolist(),
            "rows": df_clean.to_dict(orient="records"),
        }
        try:
            if hasattr(df, "attrs"):
                meta = dict(df.attrs.get("meta") or {})
                payload["meta"] = meta
        except Exception:
            pass
        client.table(table).upsert({"id": row_id, "payload": payload}).execute()
        _load_from_supabase_cached.clear()
        return True
    except Exception as e:
        st.error(f"Error saving schedule to Supabase: {e}")
        return False


def compute_schedule_hash(df: pd.DataFrame) -> str:
    try:
        return hashlib.md5(pd.util.hash_pandas_object(df, index=True).values.tobytes()).hexdigest()
    except Exception:
        return hashlib.md5(str(df).encode("utf-8")).hexdigest()


def fetch_remote_save_version() -> Optional[int]:
    """Fetch save_version from Supabase for conflict detection."""
    if not USE_SUPABASE:
        return None
    try:
        url, key, table, row_id, _ = get_supabase_config()
        if not url or not key:
            return None
        client = get_supabase_client(url, key)
        if client is None:
            return None
        resp = client.table(table).select("payload").eq("id", row_id).limit(1).execute()
        data = getattr(resp, "data", None)
        if not data:
            return None
        payload = data[0].get("payload") if isinstance(data, list) else {}
        meta = payload.get("meta", {}) if isinstance(payload, dict) else {}
        val = meta.get("save_version") if isinstance(meta, dict) else None
        if val is None:
            return None
        return int(float(str(val)))
    except Exception:
        return None


def clear_schedule_cache() -> None:
    """Clear all schedule-related caches when date changes or data is updated."""
    try:
        _load_from_supabase_cached.clear()
        st.write("🧹 **DEBUG:** Cache cleared successfully")
    except Exception as e:
        st.write(f"⚠️ **DEBUG:** Error clearing cache: {str(e)[:100]}")

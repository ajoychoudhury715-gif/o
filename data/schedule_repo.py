# data/schedule_repo.py
"""Schedule CRUD.
Supabase: single row {id, payload: {columns, rows, meta}}
Excel: Sheet1
"""

from __future__ import annotations
from typing import Optional
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


@st.cache_data(ttl=SCHEDULE_CACHE_TTL_SECONDS, show_spinner="Loading schedule...")
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

# data/schedule_repo.py
"""Schedule CRUD.
Supabase: single row {id, payload: {columns, rows, meta}}
Excel: Sheet1
"""

from __future__ import annotations
from typing import Optional
from datetime import date as date_type
from datetime import timedelta
import hashlib
import pandas as pd
import streamlit as st

from config.settings import (
    USE_SUPABASE, SUPABASE_SCHEDULE_TABLE, SUPABASE_SCHEDULE_ROW_ID,
    EXCEL_SCHEDULE_SHEET, get_supabase_config, SCHEDULE_CACHE_TTL_SECONDS,
    APPOINTMENT_DATE_COLUMN_TYPE,
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
    """Fetch appointments for one selected day from Supabase (no caching)."""
    if not USE_SUPABASE:
        return pd.DataFrame()

    try:
        url, key, _, _, _ = get_supabase_config()
        if not url or not key:
            return pd.DataFrame()

        client = get_supabase_client(url, key)
        if client is None:
            return pd.DataFrame()

        # Normalize selected_date to strict YYYY-MM-DD.
        if isinstance(selected_date, date_type):
            selected_day = selected_date
        else:
            parsed = pd.to_datetime(selected_date, errors="coerce")
            if pd.isna(parsed):
                return pd.DataFrame()
            selected_day = parsed.date()

        formatted_date = selected_day.strftime("%Y-%m-%d")
        day_start = f"{formatted_date}T00:00:00"
        next_day_start = f"{(selected_day + timedelta(days=1)).strftime('%Y-%m-%d')}T00:00:00"
        date_type_setting = APPOINTMENT_DATE_COLUMN_TYPE if APPOINTMENT_DATE_COLUMN_TYPE in {"DATE", "TIMESTAMP"} else "DATE"

        # 1) DATE column query (strict equality)
        rows_eq: list[dict] = []
        if date_type_setting == "DATE":
            try:
                eq_resp = (
                    client
                    .table("appointments")
                    .select("*")
                    .eq("appointment_date", formatted_date)
                    .execute()
                )
                eq_data = getattr(eq_resp, "data", None) or []
                if isinstance(eq_data, list):
                    rows_eq = eq_data
            except Exception:
                rows_eq = []

        # 2) TIMESTAMP column query (day range)
        rows_range: list[dict] = []
        if date_type_setting == "TIMESTAMP" or len(rows_eq) == 0:
            try:
                ts_resp = (
                    client
                    .table("appointments")
                    .select("*")
                    .gte("appointment_date", day_start)
                    .lt("appointment_date", next_day_start)
                    .execute()
                )
                ts_data = getattr(ts_resp, "data", None) or []
                if isinstance(ts_data, list):
                    rows_range = ts_data
            except Exception:
                rows_range = []

        # Merge both filtered result sets without duplicates.
        rows: list[dict] = []
        seen_keys: set[str] = set()
        for source_rows in (rows_eq, rows_range):
            for item in source_rows:
                if not isinstance(item, dict):
                    continue
                row_key = str(item.get("id", "")).strip()
                if not row_key:
                    row_key = str(hash(tuple(sorted(item.items()))))
                if row_key in seen_keys:
                    continue
                seen_keys.add(row_key)
                rows.append(item)

        if len(rows) == 0:
            return pd.DataFrame()

        df = pd.DataFrame(rows)

        # Safety guard: never return non-matching dates even if backend query is permissive.
        if "appointment_date" not in df.columns:
            return pd.DataFrame()

        raw_dates = df["appointment_date"].astype(str).str.strip()
        raw_dates_lower = raw_dates.str.lower()
        direct_match = (
            raw_dates.eq(formatted_date)
            | raw_dates.str.startswith(f"{formatted_date}T")
            | raw_dates.str.startswith(f"{formatted_date} ")
        )
        parse_input = raw_dates.where(~raw_dates_lower.isin(["", "nan", "none", "nat"]))
        normalized_default = pd.to_datetime(parse_input, errors="coerce").dt.strftime("%Y-%m-%d")
        normalized_dayfirst = pd.to_datetime(parse_input, errors="coerce", dayfirst=True).dt.strftime("%Y-%m-%d")
        strict_mask = direct_match | normalized_default.eq(formatted_date) | normalized_dayfirst.eq(formatted_date)
        strict_df = df[strict_mask.fillna(False)].copy().reset_index(drop=True)
        return strict_df

    except Exception as e:
        st.error(f"Error loading appointments by date from Supabase: {e}")
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
    except Exception:
        pass

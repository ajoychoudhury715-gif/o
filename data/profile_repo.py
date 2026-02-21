# data/profile_repo.py
"""Assistant and Doctor profile CRUD."""

from __future__ import annotations
import uuid
import pandas as pd
import streamlit as st

from config.settings import (
    USE_SUPABASE, SUPABASE_PROFILE_TABLE,
    EXCEL_ASSISTANTS_SHEET, EXCEL_DOCTORS_SHEET,
    get_supabase_config, PROFILE_CACHE_TTL_SECONDS,
)
from config.constants import PROFILE_COLUMNS
from data.supabase_client import get_supabase_client
from data.excel_ops import load_sheet, save_sheet

ASSISTANT_KIND = "Assistants"
DOCTOR_KIND = "Doctors"

# All columns to SELECT from Supabase (matches profiles table schema)
_SELECT_COLS = (
    "profile_id,kind,name,role,department,"
    "phone,email,experience,weekly_off,notes,"
    "is_active,specialisation,reg_number,"
    "can_first,can_second,can_third"
)


def _ensure_profile_df(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy() if not df.empty else pd.DataFrame()
    for col in PROFILE_COLUMNS:
        if col not in out.columns:
            out[col] = ""
    return out


def _excel_sheet_for_kind(kind: str) -> str:
    return EXCEL_ASSISTANTS_SHEET if kind == ASSISTANT_KIND else EXCEL_DOCTORS_SHEET


@st.cache_data(ttl=PROFILE_CACHE_TTL_SECONDS)
def _load_cached(kind: str, cache_bust: int) -> pd.DataFrame:
    return _load_profiles(kind)


def _load_profiles(kind: str) -> pd.DataFrame:
    if USE_SUPABASE:
        url, key, _, _, profile_table = get_supabase_config()
        if url and key:
            try:
                client = get_supabase_client(url, key)
                if client:
                    resp = (
                        client.table(profile_table)
                        .select(_SELECT_COLS)
                        .eq("kind", kind)
                        .execute()
                    )
                    data = resp.data or []
                    df = pd.DataFrame(data)
                    if not df.empty:
                        df["name"] = df["name"].astype(str).str.upper()
                        if "department" in df.columns:
                            df["department"] = df["department"].astype(str).str.upper()
                    return _ensure_profile_df(df)
            except Exception:
                pass
    sheet = _excel_sheet_for_kind(kind)
    df = load_sheet(sheet, PROFILE_COLUMNS)
    return _ensure_profile_df(df)


def load_assistants(cache_bust: int = 0) -> pd.DataFrame:
    return _load_cached(ASSISTANT_KIND, cache_bust)


def load_doctors(cache_bust: int = 0) -> pd.DataFrame:
    return _load_cached(DOCTOR_KIND, cache_bust)


def save_profiles(df: pd.DataFrame, kind: str) -> bool:
    if USE_SUPABASE:
        url, key, _, _, profile_table = get_supabase_config()
        if url and key:
            return _save_to_supabase(df, kind, profile_table, url, key)
    sheet = _excel_sheet_for_kind(kind)
    return save_sheet(_ensure_profile_df(df), sheet)


def _save_to_supabase(df: pd.DataFrame, kind: str, profile_table: str, url: str, key: str) -> bool:
    try:
        client = get_supabase_client(url, key)
        if not client:
            return False
        clean_df = _ensure_profile_df(df)
        clean_df = clean_df.where(pd.notna(clean_df), None)

        # Ensure every row has a profile_id
        if "profile_id" in clean_df.columns:
            ids = clean_df["profile_id"].astype(str)
            missing = clean_df["profile_id"].isna() | ids.str.strip().isin(["", "nan", "none"])
            if missing.any():
                clean_df.loc[missing, "profile_id"] = [
                    str(uuid.uuid4()) for _ in range(int(missing.sum()))
                ]
        clean_df["kind"] = kind

        def _fmt_wo(val):
            if isinstance(val, list):
                return ";".join(str(v) for v in val if str(v).strip())
            return str(val or "")

        clean_df["weekly_off"] = clean_df["weekly_off"].apply(_fmt_wo)

        for row in clean_df.to_dict(orient="records"):
            if row.get("profile_id"):
                client.table(profile_table).upsert(row).execute()
            else:
                client.table(profile_table).insert(row).execute()

        _load_cached.clear()
        return True
    except Exception as e:
        st.error(f"Error saving profiles: {e}")
        return False


def delete_profile(profile_id: str, kind: str) -> bool:
    if USE_SUPABASE:
        url, key, _, _, profile_table = get_supabase_config()
        if url and key:
            try:
                client = get_supabase_client(url, key)
                if client:
                    client.table(profile_table).delete().eq("profile_id", profile_id).execute()
                    _load_cached.clear()
                    return True
            except Exception:
                pass
    # Excel fallback
    sheet = _excel_sheet_for_kind(kind)
    df = load_sheet(sheet, PROFILE_COLUMNS)
    if "profile_id" in df.columns:
        df = df[df["profile_id"].astype(str) != str(profile_id)]
    return save_sheet(df, sheet)

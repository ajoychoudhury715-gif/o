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
        return None
    url, key, *_ = get_supabase_config()
    if not url or not key:
        return None
    return get_supabase_client(url, key)


def load_attendance() -> pd.DataFrame:
    client = _get_client()
    if client:
        try:
            resp = client.table(SUPABASE_ATTENDANCE_TABLE).select("*").execute()
            data = resp.data or []
            df = pd.DataFrame(data)
            if not df.empty:
                for col in ATTENDANCE_COLUMNS:
                    if col not in df.columns:
                        df[col] = ""
                return df
        except Exception:
            pass
    return load_sheet(EXCEL_ATTENDANCE_SHEET, ATTENDANCE_COLUMNS)


def get_today_punch_map(date_str: str) -> dict[str, dict[str, str]]:
    """Return {ASSISTANT_UPPER: {punch_in, punch_out}} for a date."""
    df = load_attendance()
    result: dict[str, dict[str, str]] = {}
    if df.empty:
        return result
    # Normalize column names for Supabase (lowercase) vs Excel (uppercase)
    col_map = {}
    for col in df.columns:
        col_map[col.upper()] = col
    date_col = col_map.get("DATE", "DATE")
    asst_col = col_map.get("ASSISTANT", "ASSISTANT")
    pin_col  = col_map.get("PUNCH IN",  col_map.get("PUNCH_IN",  "PUNCH IN"))
    pout_col = col_map.get("PUNCH OUT", col_map.get("PUNCH_OUT", "PUNCH OUT"))

    if date_col not in df.columns:
        return result
    mask = df[date_col].astype(str).str.strip() == date_str
    for _, row in df[mask].iterrows():
        name = str(row.get(asst_col, "")).strip().upper()
        if name:
            result[name] = {
                "punch_in":  str(row.get(pin_col,  "") or "").strip(),
                "punch_out": str(row.get(pout_col, "") or "").strip(),
            }
    return result


def punch_in(date_str: str, assistant: str, time_str: str) -> bool:
    client = _get_client()
    if client:
        try:
            resp = (
                client.table(SUPABASE_ATTENDANCE_TABLE)
                .select("id")
                .eq("date", date_str)
                .eq("assistant", assistant)
                .execute()
            )
            existing = resp.data or []
            if existing:
                client.table(SUPABASE_ATTENDANCE_TABLE).update({"punch_in": time_str}).eq("date", date_str).eq("assistant", assistant).execute()
            else:
                client.table(SUPABASE_ATTENDANCE_TABLE).insert({
                    "date": date_str, "assistant": assistant,
                    "punch_in": time_str, "punch_out": None,
                }).execute()
            return True
        except Exception:
            pass
    df = load_sheet(EXCEL_ATTENDANCE_SHEET, ATTENDANCE_COLUMNS)
    mask = (df["DATE"].astype(str) == date_str) & (df["ASSISTANT"].astype(str) == assistant)
    if mask.any():
        df.loc[mask, "PUNCH IN"] = time_str
    else:
        new_row = pd.DataFrame([{"DATE": date_str, "ASSISTANT": assistant, "PUNCH IN": time_str, "PUNCH OUT": ""}])
        df = pd.concat([df, new_row], ignore_index=True)
    return save_sheet(df, EXCEL_ATTENDANCE_SHEET)


def punch_out(date_str: str, assistant: str, time_str: str) -> bool:
    client = _get_client()
    if client:
        try:
            client.table(SUPABASE_ATTENDANCE_TABLE).update({"punch_out": time_str}).eq("date", date_str).eq("assistant", assistant).execute()
            return True
        except Exception:
            pass
    df = load_sheet(EXCEL_ATTENDANCE_SHEET, ATTENDANCE_COLUMNS)
    mask = (df["DATE"].astype(str) == date_str) & (df["ASSISTANT"].astype(str) == assistant)
    if mask.any():
        df.loc[mask, "PUNCH OUT"] = time_str
    return save_sheet(df, EXCEL_ATTENDANCE_SHEET)


def reset_attendance(date_str: str, assistant: str) -> bool:
    client = _get_client()
    if client:
        try:
            client.table(SUPABASE_ATTENDANCE_TABLE).delete().eq("date", date_str).eq("assistant", assistant).execute()
            return True
        except Exception:
            pass
    df = load_sheet(EXCEL_ATTENDANCE_SHEET, ATTENDANCE_COLUMNS)
    mask = (df["DATE"].astype(str) == date_str) & (df["ASSISTANT"].astype(str) == assistant)
    df = df[~mask].copy()
    return save_sheet(df, EXCEL_ATTENDANCE_SHEET)

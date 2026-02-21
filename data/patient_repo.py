# data/patient_repo.py
"""Patient records CRUD."""

from __future__ import annotations
import uuid
import pandas as pd

from config.settings import USE_SUPABASE, SUPABASE_PATIENTS_TABLE, EXCEL_PATIENTS_SHEET, get_supabase_config
from data.supabase_client import get_supabase_client
from data.excel_ops import load_sheet, save_sheet

PATIENT_COLUMNS = ["id", "name"]


def _get_client():
    if not USE_SUPABASE:
        return None
    url, key, *_ = get_supabase_config()
    if not url or not key:
        return None
    return get_supabase_client(url, key)


def load_patients() -> pd.DataFrame:
    client = _get_client()
    if client:
        try:
            resp = client.table(SUPABASE_PATIENTS_TABLE).select("*").execute()
            df = pd.DataFrame(resp.data or [])
            if not df.empty:
                return df
        except Exception:
            pass
    return load_sheet(EXCEL_PATIENTS_SHEET, PATIENT_COLUMNS)


def save_patients(df: pd.DataFrame) -> bool:
    client = _get_client()
    if client:
        try:
            clean = df.where(pd.notna(df), None)
            if "id" in clean.columns:
                ids = clean["id"].astype(str)
                missing = clean["id"].isna() | ids.str.strip().isin(["", "nan", "none"])
                if missing.any():
                    clean.loc[missing, "id"] = [str(uuid.uuid4()) for _ in range(int(missing.sum()))]
            for row in clean.to_dict(orient="records"):
                if row.get("id"):
                    client.table(SUPABASE_PATIENTS_TABLE).upsert(row, on_conflict="id").execute()
                else:
                    client.table(SUPABASE_PATIENTS_TABLE).insert(row).execute()
            return True
        except Exception:
            pass
    return save_sheet(df, EXCEL_PATIENTS_SHEET)


def get_patient_names() -> list[str]:
    df = load_patients()
    if df.empty or "name" not in df.columns:
        return []
    return sorted(df["name"].dropna().astype(str).str.strip().unique().tolist())

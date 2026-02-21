# data/duty_repo.py
"""Duties master, assignments, and runs CRUD."""

from __future__ import annotations
from typing import Optional
import uuid
import pandas as pd

from config.settings import (
    USE_SUPABASE,
    SUPABASE_DUTIES_MASTER_TABLE, SUPABASE_DUTY_ASSIGNMENTS_TABLE, SUPABASE_DUTY_RUNS_TABLE,
    EXCEL_DUTIES_MASTER_SHEET, EXCEL_DUTY_ASSIGNMENTS_SHEET, EXCEL_DUTY_RUNS_SHEET,
    get_supabase_config, IST,
)
from config.constants import DUTIES_MASTER_COLUMNS, DUTY_ASSIGNMENTS_COLUMNS, DUTY_RUNS_COLUMNS
from data.supabase_client import get_supabase_client
from data.excel_ops import load_sheet, save_sheet


def _get_client():
    if not USE_SUPABASE:
        return None
    url, key, *_ = get_supabase_config()
    if not url or not key:
        return None
    return get_supabase_client(url, key)


def _sb_load(table: str) -> pd.DataFrame:
    client = _get_client()
    if not client:
        return pd.DataFrame()
    try:
        resp = client.table(table).select("*").execute()
        return pd.DataFrame(resp.data or [])
    except Exception:
        return pd.DataFrame()


def _sb_upsert(table: str, df: pd.DataFrame) -> bool:
    client = _get_client()
    if not client:
        return False
    try:
        rows = df.where(pd.notna(df), None).to_dict(orient="records")
        for row in rows:
            if row.get("id"):
                client.table(table).upsert(row, on_conflict="id").execute()
            else:
                client.table(table).insert(row).execute()
        return True
    except Exception:
        return False


# ── Duties Master ─────────────────────────────────────────────────────────────

def load_duties_master() -> pd.DataFrame:
    if USE_SUPABASE:
        df = _sb_load(SUPABASE_DUTIES_MASTER_TABLE)
        if not df.empty:
            return df
    return load_sheet(EXCEL_DUTIES_MASTER_SHEET, DUTIES_MASTER_COLUMNS)


def save_duties_master(df: pd.DataFrame) -> bool:
    if USE_SUPABASE and _sb_upsert(SUPABASE_DUTIES_MASTER_TABLE, df):
        return True
    return save_sheet(df, EXCEL_DUTIES_MASTER_SHEET)


# ── Duty Assignments ──────────────────────────────────────────────────────────

def load_duty_assignments() -> pd.DataFrame:
    if USE_SUPABASE:
        df = _sb_load(SUPABASE_DUTY_ASSIGNMENTS_TABLE)
        if not df.empty:
            return df
    return load_sheet(EXCEL_DUTY_ASSIGNMENTS_SHEET, DUTY_ASSIGNMENTS_COLUMNS)


def save_duty_assignments(df: pd.DataFrame) -> bool:
    if USE_SUPABASE and _sb_upsert(SUPABASE_DUTY_ASSIGNMENTS_TABLE, df):
        return True
    return save_sheet(df, EXCEL_DUTY_ASSIGNMENTS_SHEET)


# ── Duty Runs ─────────────────────────────────────────────────────────────────

def load_duty_runs() -> pd.DataFrame:
    if USE_SUPABASE:
        df = _sb_load(SUPABASE_DUTY_RUNS_TABLE)
        if not df.empty:
            return df
    return load_sheet(EXCEL_DUTY_RUNS_SHEET, DUTY_RUNS_COLUMNS)


def save_duty_runs(df: pd.DataFrame) -> bool:
    if USE_SUPABASE and _sb_upsert(SUPABASE_DUTY_RUNS_TABLE, df):
        return True
    return save_sheet(df, EXCEL_DUTY_RUNS_SHEET)


def get_active_duty_assignments(assistant: str) -> list[dict]:
    try:
        assignments_df = load_duty_assignments()
        duties_df = load_duties_master()
        if assignments_df.empty or duties_df.empty:
            return []
        mask = (
            (assignments_df["assistant"].astype(str).str.strip() == assistant.strip()) &
            (assignments_df["active"].astype(str).str.lower() == "true")
        )
        matching = assignments_df[mask]
        duty_map = {str(r.get("id", "")): r.to_dict() for _, r in duties_df.iterrows()}
        result = []
        for _, arow in matching.iterrows():
            duty_id = str(arow.get("duty_id", ""))
            duty_info = duty_map.get(duty_id, {})
            result.append({
                "duty_id": duty_id,
                "assistant": assistant,
                "op": str(arow.get("op", "")),
                "est_minutes": arow.get("est_minutes") or duty_info.get("est_minutes", 30),
                "name": duty_info.get("name", duty_id),
                "frequency": str(duty_info.get("frequency", "")).upper(),
                "description": duty_info.get("description", ""),
            })
        return result
    except Exception:
        return []


def get_active_duty_run(assistant: str) -> Optional[dict]:
    try:
        df = load_duty_runs()
        if df.empty:
            return None
        mask = (
            (df["assistant"].astype(str).str.strip() == assistant.strip()) &
            (df["status"].astype(str).str.upper() == "IN_PROGRESS")
        )
        active = df[mask]
        return active.iloc[0].to_dict() if not active.empty else None
    except Exception:
        return None


def start_duty_run(assistant: str, duty: dict, today_str: str) -> str:
    from datetime import datetime, timedelta
    run_id = str(uuid.uuid4())
    est_minutes = int(duty.get("est_minutes") or 30)
    now = datetime.now(IST)
    due_at = (now + timedelta(minutes=est_minutes)).isoformat()
    df = load_duty_runs()
    new_row = pd.DataFrame([{
        "id": run_id, "date": today_str, "assistant": assistant,
        "duty_id": duty.get("duty_id", ""), "status": "IN_PROGRESS",
        "started_at": now.isoformat(), "due_at": due_at,
        "ended_at": "", "est_minutes": est_minutes, "op": duty.get("op", ""),
    }])
    df = pd.concat([df, new_row], ignore_index=True)
    save_duty_runs(df)
    return run_id


def mark_duty_done(run_id: str) -> bool:
    from datetime import datetime
    df = load_duty_runs()
    if df.empty:
        return False
    mask = df["id"].astype(str) == run_id
    if not mask.any():
        return False
    df.loc[mask, "status"] = "DONE"
    df.loc[mask, "ended_at"] = datetime.now(IST).isoformat()
    return save_duty_runs(df)

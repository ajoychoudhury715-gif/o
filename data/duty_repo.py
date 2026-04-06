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
                client.table(table).upsert(row).execute()
            else:
                client.table(table).insert(row).execute()
        return True
    except Exception:
        return False


def _is_blank(value) -> bool:
    if value is None:
        return True
    try:
        if pd.isna(value):
            return True
    except Exception:
        pass
    return str(value).strip().lower() in {"", "nan", "none", "nat"}


def _normalize_text(value) -> str:
    return "" if _is_blank(value) else str(value).strip()


def _normalize_name(value) -> str:
    return _normalize_text(value).upper()


def _normalize_bool(value, default: bool = False) -> bool:
    if _is_blank(value):
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "y", "on"}


def _normalize_minutes(value, default: int = 30) -> int:
    try:
        minutes = int(float(str(value)))
        return max(1, minutes)
    except Exception:
        return int(default)


def _normalize_frequency(value) -> str:
    return _normalize_text(value).upper()


def _normalize_date_str(value) -> str:
    if _is_blank(value):
        return ""
    try:
        ts = pd.to_datetime(value, errors="coerce")
        if pd.isna(ts):
            return str(value).strip()[:10]
        return ts.date().isoformat()
    except Exception:
        return str(value).strip()[:10]


def _first_value(row, *candidates, default=""):
    for candidate in candidates:
        value = row.get(candidate, None)
        if not _is_blank(value):
            return value
    return default


def _normalize_duties_master_df(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(columns=DUTIES_MASTER_COLUMNS)

    rows = []
    for _, row in df.iterrows():
        rows.append(
            {
                "id": _normalize_text(_first_value(row, "id", "duty_id")),
                "name": _normalize_text(_first_value(row, "name", "duty_name")),
                "description": _normalize_text(_first_value(row, "description", "notes")),
                "frequency": _normalize_frequency(_first_value(row, "frequency")),
                "est_minutes": _normalize_minutes(_first_value(row, "est_minutes", "duration_minutes", default=30), default=30),
                "active": _normalize_bool(_first_value(row, "active", "is_active", default=True), default=True),
            }
        )
    return pd.DataFrame(rows, columns=DUTIES_MASTER_COLUMNS)


def _normalize_duty_assignments_df(df: pd.DataFrame, include_display: bool = True) -> pd.DataFrame:
    base_columns = list(DUTY_ASSIGNMENTS_COLUMNS)
    if include_display:
        base_columns.append("duty_name")

    if df is None or df.empty:
        return pd.DataFrame(columns=base_columns)

    rows = []
    for _, row in df.iterrows():
        normalized = {
            "id": _normalize_text(_first_value(row, "id", "assignment_id")),
            "duty_id": _normalize_text(_first_value(row, "duty_id")),
            "assistant": _normalize_name(_first_value(row, "assistant")),
            "op": _normalize_text(_first_value(row, "op")),
            "est_minutes": _normalize_minutes(_first_value(row, "est_minutes", "duration_minutes", default=30), default=30),
            "active": _normalize_bool(_first_value(row, "active", "is_active", default=True), default=True),
        }
        if include_display:
            normalized["duty_name"] = _normalize_text(_first_value(row, "duty_name", "name"))
        rows.append(normalized)
    return pd.DataFrame(rows, columns=base_columns)


def _normalize_duty_runs_df(df: pd.DataFrame, include_display: bool = True) -> pd.DataFrame:
    base_columns = list(DUTY_RUNS_COLUMNS)
    if include_display:
        base_columns.append("duty_name")

    if df is None or df.empty:
        return pd.DataFrame(columns=base_columns)

    rows = []
    for _, row in df.iterrows():
        normalized = {
            "id": _normalize_text(_first_value(row, "id", "run_id")),
            "date": _normalize_date_str(_first_value(row, "date")),
            "assistant": _normalize_name(_first_value(row, "assistant")),
            "duty_id": _normalize_text(_first_value(row, "duty_id")),
            "status": _normalize_text(_first_value(row, "status")).upper(),
            "started_at": _normalize_text(_first_value(row, "started_at")),
            "due_at": _normalize_text(_first_value(row, "due_at")),
            "ended_at": _normalize_text(_first_value(row, "ended_at", "completed_at")),
            "est_minutes": _normalize_minutes(_first_value(row, "est_minutes", "duration_minutes", default=30), default=30),
            "op": _normalize_text(_first_value(row, "op")),
        }
        if include_display:
            normalized["duty_name"] = _normalize_text(_first_value(row, "duty_name", "name"))
        rows.append(normalized)
    return pd.DataFrame(rows, columns=base_columns)


# ── Duties Master ─────────────────────────────────────────────────────────────

def load_duties_master() -> pd.DataFrame:
    df = _sb_load(SUPABASE_DUTIES_MASTER_TABLE) if USE_SUPABASE else pd.DataFrame()
    if df.empty:
        df = load_sheet(EXCEL_DUTIES_MASTER_SHEET, DUTIES_MASTER_COLUMNS)
    return _normalize_duties_master_df(df)


def save_duties_master(df: pd.DataFrame) -> bool:
    normalized = _normalize_duties_master_df(df)
    if USE_SUPABASE and _sb_upsert(SUPABASE_DUTIES_MASTER_TABLE, normalized):
        return True
    return save_sheet(normalized, EXCEL_DUTIES_MASTER_SHEET)


# ── Duty Assignments ──────────────────────────────────────────────────────────

def load_duty_assignments() -> pd.DataFrame:
    df = _sb_load(SUPABASE_DUTY_ASSIGNMENTS_TABLE) if USE_SUPABASE else pd.DataFrame()
    if df.empty:
        df = load_sheet(EXCEL_DUTY_ASSIGNMENTS_SHEET, DUTY_ASSIGNMENTS_COLUMNS)
    return _normalize_duty_assignments_df(df, include_display=True)


def save_duty_assignments(df: pd.DataFrame) -> bool:
    normalized = _normalize_duty_assignments_df(df, include_display=False)
    if USE_SUPABASE and _sb_upsert(SUPABASE_DUTY_ASSIGNMENTS_TABLE, normalized):
        return True
    return save_sheet(normalized, EXCEL_DUTY_ASSIGNMENTS_SHEET)


# ── Duty Runs ─────────────────────────────────────────────────────────────────

def load_duty_runs() -> pd.DataFrame:
    df = _sb_load(SUPABASE_DUTY_RUNS_TABLE) if USE_SUPABASE else pd.DataFrame()
    if df.empty:
        df = load_sheet(EXCEL_DUTY_RUNS_SHEET, DUTY_RUNS_COLUMNS)
    normalized = _normalize_duty_runs_df(df, include_display=True)
    if normalized.empty:
        return normalized

    duties_df = load_duties_master()
    duty_name_map = {}
    if duties_df is not None and not duties_df.empty:
        duty_name_map = {
            _normalize_text(row.get("id")): _normalize_text(row.get("name"))
            for _, row in duties_df.iterrows()
            if _normalize_text(row.get("id"))
        }

    normalized["duty_name"] = normalized.apply(
        lambda row: _normalize_text(row.get("duty_name")) or duty_name_map.get(_normalize_text(row.get("duty_id")), ""),
        axis=1,
    )
    return normalized


def save_duty_runs(df: pd.DataFrame) -> bool:
    normalized = _normalize_duty_runs_df(df, include_display=False)
    if USE_SUPABASE and _sb_upsert(SUPABASE_DUTY_RUNS_TABLE, normalized):
        return True
    return save_sheet(normalized, EXCEL_DUTY_RUNS_SHEET)


def get_active_duty_assignments(assistant: str) -> list[dict]:
    try:
        assistant_upper = _normalize_name(assistant)
        if not assistant_upper:
            return []

        assignments_df = load_duty_assignments()
        duties_df = load_duties_master()
        if assignments_df.empty or duties_df.empty:
            return []

        duty_map = {
            _normalize_text(row.get("id")): row.to_dict()
            for _, row in duties_df.iterrows()
            if _normalize_text(row.get("id"))
        }
        duty_id_by_name = {
            _normalize_name(row.get("name")): _normalize_text(row.get("id"))
            for _, row in duties_df.iterrows()
            if _normalize_name(row.get("name")) and _normalize_text(row.get("id"))
        }

        mask = (
            assignments_df["assistant"].astype(str).str.strip().str.upper().eq(assistant_upper)
            & assignments_df["active"].astype(bool)
        )
        matching = assignments_df[mask]
        result = []
        for _, arow in matching.iterrows():
            duty_id = _normalize_text(arow.get("duty_id"))
            if not duty_id:
                duty_id = duty_id_by_name.get(_normalize_name(arow.get("duty_name")), "")
            duty_info = duty_map.get(duty_id, {})
            if duty_info and not _normalize_bool(duty_info.get("active"), default=True):
                continue
            est_minutes = _normalize_minutes(arow.get("est_minutes") or duty_info.get("est_minutes"), default=30)
            result.append({
                "duty_id": duty_id,
                "assistant": assistant_upper,
                "op": _normalize_text(arow.get("op")),
                "est_minutes": est_minutes,
                "name": _normalize_text(duty_info.get("name")) or _normalize_text(arow.get("duty_name")) or duty_id,
                "frequency": _normalize_frequency(duty_info.get("frequency")),
                "description": _normalize_text(duty_info.get("description")),
            })
        return result
    except Exception:
        return []


def get_active_duty_run(assistant: str) -> Optional[dict]:
    try:
        assistant_upper = _normalize_name(assistant)
        if not assistant_upper:
            return None
        df = load_duty_runs()
        if df.empty:
            return None
        mask = (
            (df["assistant"].astype(str).str.strip().str.upper() == assistant_upper) &
            (df["status"].astype(str).str.upper() == "IN_PROGRESS")
        )
        active = df[mask].copy()
        if "started_at" in active.columns:
            active = active.sort_values(by="started_at", ascending=False)
        return active.iloc[0].to_dict() if not active.empty else None
    except Exception:
        return None


def start_duty_run(assistant: str, duty: dict, today_str: str) -> str:
    from datetime import datetime, timedelta
    assistant_upper = _normalize_name(assistant)
    if not assistant_upper:
        return ""

    active_run = get_active_duty_run(assistant_upper)
    if active_run:
        return str(active_run.get("id", "") or "")

    run_id = str(uuid.uuid4())
    est_minutes = _normalize_minutes(duty.get("est_minutes"), default=30)
    now = datetime.now(IST)
    due_at = (now + timedelta(minutes=est_minutes)).isoformat()
    df = load_duty_runs()
    new_row = pd.DataFrame([{
        "id": run_id,
        "date": _normalize_date_str(today_str) or now.date().isoformat(),
        "assistant": assistant_upper,
        "duty_id": _normalize_text(duty.get("duty_id")),
        "status": "IN_PROGRESS",
        "started_at": now.isoformat(), "due_at": due_at,
        "ended_at": "",
        "est_minutes": est_minutes,
        "op": _normalize_text(duty.get("op")),
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

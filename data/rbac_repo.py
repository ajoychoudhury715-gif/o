"""Persistence layer for role/user function permissions."""

from __future__ import annotations
from typing import Optional

from config.settings import get_supabase_config
from data.supabase_client import get_supabase_client

ROLE_PERMISSIONS_TABLE = "rbac_role_permissions"
USER_PERMISSIONS_TABLE = "rbac_user_permissions"


def _get_client():
    url, key, *_ = get_supabase_config()
    if not url or not key:
        return None
    return get_supabase_client(url, key)


def get_role_permissions(role: str) -> Optional[list[str]]:
    """Return stored role permissions, or None if not configured."""
    try:
        client = _get_client()
        if client is None:
            return None
        resp = (
            client
            .table(ROLE_PERMISSIONS_TABLE)
            .select("allowed_functions")
            .eq("role", str(role or "").strip())
            .limit(1)
            .execute()
        )
        data = getattr(resp, "data", None) or []
        if not data:
            return None
        raw = data[0].get("allowed_functions")
        if not isinstance(raw, list):
            return None
        return [str(x).strip() for x in raw if str(x).strip()]
    except Exception:
        return None


def set_role_permissions(role: str, allowed_functions: list[str]) -> bool:
    """Upsert role permission list."""
    try:
        client = _get_client()
        if client is None:
            return False
        payload = {
            "role": str(role or "").strip(),
            "allowed_functions": [str(x).strip() for x in allowed_functions if str(x).strip()],
        }
        client.table(ROLE_PERMISSIONS_TABLE).upsert(payload).execute()
        return True
    except Exception:
        return False


def get_user_permissions_override(user_id: str) -> tuple[bool, list[str]]:
    """Return (override_enabled, allowed_functions)."""
    try:
        client = _get_client()
        if client is None:
            return False, []
        resp = (
            client
            .table(USER_PERMISSIONS_TABLE)
            .select("override_enabled,allowed_functions")
            .eq("user_id", str(user_id or "").strip())
            .limit(1)
            .execute()
        )
        data = getattr(resp, "data", None) or []
        if not data:
            return False, []
        row = data[0] if isinstance(data[0], dict) else {}
        enabled = bool(row.get("override_enabled", False))
        raw = row.get("allowed_functions", [])
        allowed = [str(x).strip() for x in raw] if isinstance(raw, list) else []
        allowed = [x for x in allowed if x]
        return enabled, allowed
    except Exception:
        return False, []


def set_user_permissions_override(user_id: str, override_enabled: bool, allowed_functions: list[str]) -> bool:
    """Upsert user-level override list."""
    try:
        client = _get_client()
        if client is None:
            return False
        payload = {
            "user_id": str(user_id or "").strip(),
            "override_enabled": bool(override_enabled),
            "allowed_functions": [str(x).strip() for x in allowed_functions if str(x).strip()],
        }
        client.table(USER_PERMISSIONS_TABLE).upsert(payload).execute()
        return True
    except Exception:
        return False


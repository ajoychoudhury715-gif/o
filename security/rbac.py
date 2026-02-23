"""Role-based function access control."""

from __future__ import annotations
from typing import Iterable
import streamlit as st

from config.constants import NAV_STRUCTURE, ROLE_NAV
from data.rbac_repo import (
    get_role_permissions,
    set_role_permissions,
    get_user_permissions_override,
    set_user_permissions_override,
)


def function_id_for_page(category: str, view: str) -> str:
    return f"page::{str(category).strip()}::{str(view).strip()}"


# Non-page actions that should be permission-gated.
ACTION_FUNCTIONS: list[tuple[str, str]] = [
    ("action::schedule::add_appointment", "Add Appointment"),
    ("action::schedule::edit_appointment", "Edit Appointment"),
    ("action::schedule::delete_appointment", "Delete Appointment"),
    ("action::schedule::update_status", "Update Appointment Status"),
    ("action::schedule::auto_allocate", "Auto-Allocate Assistants"),
    ("action::schedule::time_blocks", "Manage Time Blocks"),
    ("action::operations::punch", "Punch In/Out"),
    ("action::operations::duties", "Manage Duties"),
    ("action::operations::reminders", "Manage Reminders"),
    ("action::admin::save_controls", "Save/Conflict Controls"),
    ("action::admin::user_management", "Manage Users"),
    ("action::admin::permissions", "Function Access Control"),
]


def get_function_catalog() -> list[dict]:
    """Build dynamic function catalog from current app navigation + action registry."""
    items: list[dict] = []
    seen: set[str] = set()

    # Dynamic page-level functions: automatically expands when NAV_STRUCTURE changes.
    for category, views in NAV_STRUCTURE.items():
        for view in views:
            fid = function_id_for_page(category, view)
            if fid in seen:
                continue
            seen.add(fid)
            items.append(
                {
                    "id": fid,
                    "label": f"{category} → {view}",
                    "kind": "page",
                    "group": category,
                }
            )

    # Action-level functions.
    for fid, label in ACTION_FUNCTIONS:
        if fid in seen:
            continue
        seen.add(fid)
        items.append({"id": fid, "label": label, "kind": "action", "group": "Actions"})

    return items


def get_all_function_ids() -> set[str]:
    return {x["id"] for x in get_function_catalog()}


def _normalize_allowed(values: Iterable[str]) -> list[str]:
    known = get_all_function_ids()
    out: list[str] = []
    for val in values:
        item = str(val or "").strip()
        if item and item in known:
            out.append(item)
    # Keep insertion order but remove duplicates.
    dedup = list(dict.fromkeys(out))
    return dedup


def _page_ids_from_role_nav(role_nav: dict[str, list[str]]) -> set[str]:
    page_ids: set[str] = set()
    for category, views in role_nav.items():
        for view in views:
            page_ids.add(function_id_for_page(category, view))
    return page_ids


def get_default_role_permissions(role: str) -> set[str]:
    """Role defaults. Admin always gets all functions."""
    role_norm = str(role or "").strip().lower()
    if role_norm == "admin":
        return get_all_function_ids()

    base_nav = ROLE_NAV.get(role_norm, {})
    allowed = _page_ids_from_role_nav(base_nav)

    if role_norm == "assistant":
        allowed.update(
            {
                "action::operations::punch",
                "action::operations::duties",
                "action::operations::reminders",
                "action::schedule::update_status",
            }
        )
    elif role_norm == "frontdesk":
        allowed.update(
            {
                "action::operations::punch",
                "action::operations::duties",
                "action::operations::reminders",
                "action::schedule::add_appointment",
                "action::schedule::edit_appointment",
                "action::schedule::delete_appointment",
                "action::schedule::update_status",
            }
        )

    return allowed


def get_role_permissions_config(role: str) -> list[str]:
    """Permissions currently configured for a role (DB row if present, else defaults)."""
    role_norm = str(role or "").strip().lower()
    if role_norm == "admin":
        return sorted(get_all_function_ids())

    stored = get_role_permissions(role_norm)
    if stored is None:
        return sorted(get_default_role_permissions(role_norm))
    return sorted(_normalize_allowed(stored))


def save_role_permissions_config(role: str, allowed_functions: list[str]) -> bool:
    role_norm = str(role or "").strip().lower()
    if not role_norm:
        return False
    normalized = _normalize_allowed(allowed_functions)
    return set_role_permissions(role_norm, normalized)


def get_user_override_config(user_id: str) -> tuple[bool, list[str]]:
    enabled, allowed = get_user_permissions_override(user_id)
    return enabled, sorted(_normalize_allowed(allowed))


def save_user_override_config(user_id: str, override_enabled: bool, allowed_functions: list[str]) -> bool:
    normalized = _normalize_allowed(allowed_functions)
    return set_user_permissions_override(user_id, bool(override_enabled), normalized)


def resolve_effective_permissions(role: str, user_id: str | None = None) -> set[str]:
    """Resolve role + optional user override into effective permissions."""
    role_norm = str(role or "").strip().lower()
    if role_norm == "admin":
        return get_all_function_ids()

    role_allowed = set(get_role_permissions_config(role_norm))
    if not user_id:
        return role_allowed

    enabled, user_allowed = get_user_override_config(user_id)
    if enabled:
        return set(user_allowed)
    return role_allowed


def load_permissions_for_session(role: str, user_id: str | None = None) -> set[str]:
    perms = resolve_effective_permissions(role, user_id)
    marker = f"{str(role or '').strip().lower()}:{str(user_id or '').strip()}"
    st.session_state.allowed_functions = sorted(perms)
    st.session_state.permissions_loaded_for = marker
    return perms


def has_access(function_id: str, allowed_functions: Iterable[str] | None = None) -> bool:
    role = str(st.session_state.get("user_role", "") or "").strip().lower()
    if role == "admin":
        return True

    fid = str(function_id or "").strip()
    if not fid:
        return True

    if allowed_functions is None:
        allowed = set(str(x).strip() for x in st.session_state.get("allowed_functions", []) if str(x).strip())
    else:
        allowed = set(str(x).strip() for x in allowed_functions if str(x).strip())
    return fid in allowed


def require_access(function_id: str, feature_name: str = "this feature") -> bool:
    if has_access(function_id):
        return True
    st.error(f"You do not have permission to access {feature_name}.")
    st.stop()
    return False


def get_allowed_navigation(role: str, allowed_functions: Iterable[str] | None = None) -> dict[str, list[str]]:
    role_norm = str(role or "").strip().lower()
    if role_norm == "admin":
        return {k: list(v) for k, v in NAV_STRUCTURE.items()}

    nav: dict[str, list[str]] = {}
    for category, views in NAV_STRUCTURE.items():
        allowed_views = [view for view in views if has_access(function_id_for_page(category, view), allowed_functions)]
        if allowed_views:
            nav[category] = allowed_views
    return nav


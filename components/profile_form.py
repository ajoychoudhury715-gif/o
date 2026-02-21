# components/profile_form.py
"""Reusable add/edit form for assistant and doctor profiles."""

from __future__ import annotations
from typing import Callable
import uuid
import streamlit as st

from config.constants import DEFAULT_DEPARTMENTS, DEFAULT_WEEKLY_OFF, WEEKDAY_NAMES


# ── Assistant form ─────────────────────────────────────────────────────────────

def render_add_assistant_form(
    departments: list[str],
    on_save: Callable[[dict], None],
) -> None:
    """Render the Add Assistant expander form."""
    with st.expander("➕ Add Assistant", expanded=False):
        with st.form("add_assistant_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                name = st.text_input("Full Name *")
                role = st.text_input("Role", placeholder="e.g. Senior Assistant")
                dept_opts = [""] + sorted(departments or DEFAULT_DEPARTMENTS)
                department = st.selectbox("Department", dept_opts)
            with c2:
                phone = st.text_input("Phone")
                email = st.text_input("Email")
                experience = st.number_input("Experience (years)", min_value=0, max_value=50, value=0)

            weekly_off = st.multiselect(
                "Weekly Off Days",
                options=WEEKDAY_NAMES,
                default=[],
                help="Days this assistant does not work",
            )
            notes = st.text_area("Notes", height=80)
            is_active = st.checkbox("Active", value=True)

            if st.form_submit_button("➕ Add Assistant", use_container_width=True):
                if not name.strip():
                    st.error("Full Name is required.")
                else:
                    row = _build_assistant_row(
                        name=name.strip(),
                        role=role.strip(),
                        department=department,
                        phone=phone.strip(),
                        email=email.strip(),
                        experience=int(experience),
                        weekly_off=weekly_off,
                        notes=notes.strip(),
                        is_active=is_active,
                    )
                    on_save(row)


def render_edit_assistant_form(
    row: dict,
    departments: list[str],
    on_save: Callable[[dict], None],
    on_cancel: Callable[[], None],
    form_key: str = "edit_assistant",
) -> None:
    """Render an inline edit form for an existing assistant profile."""
    with st.form(form_key, clear_on_submit=False):
        st.markdown("#### ✏️ Edit Assistant")
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("Full Name *", value=str(row.get("name", "") or ""))
            role = st.text_input("Role", value=str(row.get("role", "") or ""))
            dept_opts = [""] + sorted(departments or DEFAULT_DEPARTMENTS)
            current_dept = str(row.get("department", "") or "")
            department = st.selectbox(
                "Department",
                dept_opts,
                index=_idx_of(current_dept, dept_opts),
            )
        with c2:
            phone = st.text_input("Phone", value=str(row.get("phone", "") or ""))
            email = st.text_input("Email", value=str(row.get("email", "") or ""))
            exp_val = _safe_int(row.get("experience", 0))
            experience = st.number_input(
                "Experience (years)", min_value=0, max_value=50, value=exp_val
            )

        # Weekly off — stored as comma-separated day names or semicolons
        wo_raw = str(row.get("weekly_off", "") or "")
        wo_default = _parse_weekly_off_list(wo_raw)
        weekly_off = st.multiselect(
            "Weekly Off Days",
            options=WEEKDAY_NAMES,
            default=[d for d in wo_default if d in WEEKDAY_NAMES],
        )
        notes = st.text_area("Notes", value=str(row.get("notes", "") or ""), height=80)
        is_active = st.checkbox("Active", value=bool(row.get("is_active", True)))

        col_save, col_cancel = st.columns(2)
        with col_save:
            submitted = st.form_submit_button("💾 Save", use_container_width=True)
        with col_cancel:
            cancelled = st.form_submit_button("✕ Cancel", use_container_width=True, type="secondary")

        if submitted:
            if not name.strip():
                st.error("Full Name is required.")
            else:
                updated = dict(row)
                updated.update(
                    name=name.strip(),
                    role=role.strip(),
                    department=department,
                    phone=phone.strip(),
                    email=email.strip(),
                    experience=int(experience),
                    weekly_off=";".join(weekly_off),
                    notes=notes.strip(),
                    is_active=is_active,
                )
                on_save(updated)
        if cancelled:
            on_cancel()


# ── Doctor form ────────────────────────────────────────────────────────────────

def render_add_doctor_form(
    departments: list[str],
    on_save: Callable[[dict], None],
) -> None:
    """Render the Add Doctor expander form."""
    with st.expander("➕ Add Doctor", expanded=False):
        with st.form("add_doctor_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                name = st.text_input("Full Name *")
                specialisation = st.text_input("Specialisation")
                dept_opts = [""] + sorted(departments or DEFAULT_DEPARTMENTS)
                department = st.selectbox("Department", dept_opts)
            with c2:
                phone = st.text_input("Phone")
                email = st.text_input("Email")
                reg_number = st.text_input("Registration #")

            notes = st.text_area("Notes", height=80)
            is_active = st.checkbox("Active", value=True)

            if st.form_submit_button("➕ Add Doctor", use_container_width=True):
                if not name.strip():
                    st.error("Full Name is required.")
                else:
                    row = _build_doctor_row(
                        name=name.strip(),
                        specialisation=specialisation.strip(),
                        department=department,
                        phone=phone.strip(),
                        email=email.strip(),
                        reg_number=reg_number.strip(),
                        notes=notes.strip(),
                        is_active=is_active,
                    )
                    on_save(row)


def render_edit_doctor_form(
    row: dict,
    departments: list[str],
    on_save: Callable[[dict], None],
    on_cancel: Callable[[], None],
    form_key: str = "edit_doctor",
) -> None:
    """Render an inline edit form for an existing doctor profile."""
    with st.form(form_key, clear_on_submit=False):
        st.markdown("#### ✏️ Edit Doctor")
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("Full Name *", value=str(row.get("name", "") or ""))
            specialisation = st.text_input(
                "Specialisation", value=str(row.get("specialisation", "") or "")
            )
            dept_opts = [""] + sorted(departments or DEFAULT_DEPARTMENTS)
            current_dept = str(row.get("department", "") or "")
            department = st.selectbox(
                "Department", dept_opts, index=_idx_of(current_dept, dept_opts)
            )
        with c2:
            phone = st.text_input("Phone", value=str(row.get("phone", "") or ""))
            email = st.text_input("Email", value=str(row.get("email", "") or ""))
            reg_number = st.text_input(
                "Registration #", value=str(row.get("reg_number", "") or "")
            )

        notes = st.text_area("Notes", value=str(row.get("notes", "") or ""), height=80)
        is_active = st.checkbox("Active", value=bool(row.get("is_active", True)))

        col_save, col_cancel = st.columns(2)
        with col_save:
            submitted = st.form_submit_button("💾 Save", use_container_width=True)
        with col_cancel:
            cancelled = st.form_submit_button("✕ Cancel", use_container_width=True, type="secondary")

        if submitted:
            if not name.strip():
                st.error("Full Name is required.")
            else:
                updated = dict(row)
                updated.update(
                    name=name.strip(),
                    specialisation=specialisation.strip(),
                    department=department,
                    phone=phone.strip(),
                    email=email.strip(),
                    reg_number=reg_number.strip(),
                    notes=notes.strip(),
                    is_active=is_active,
                )
                on_save(updated)
        if cancelled:
            on_cancel()


# ── helpers ────────────────────────────────────────────────────────────────────

def _build_assistant_row(
    name: str, role: str, department: str, phone: str, email: str,
    experience: int, weekly_off: list[str], notes: str, is_active: bool,
    profile_id: str | None = None,
) -> dict:
    return {
        "profile_id": profile_id or str(uuid.uuid4()),
        "kind": "Assistants",
        "name": name,
        "role": role,
        "department": department,
        "phone": phone,
        "email": email,
        "experience": experience,
        "weekly_off": ";".join(weekly_off),
        "notes": notes,
        "is_active": is_active,
        "specialisation": "",
        "reg_number": "",
        "can_first": True,
        "can_second": True,
        "can_third": True,
    }


def _build_doctor_row(
    name: str, specialisation: str, department: str, phone: str, email: str,
    reg_number: str, notes: str, is_active: bool,
    profile_id: str | None = None,
) -> dict:
    return {
        "profile_id": profile_id or str(uuid.uuid4()),
        "kind": "Doctors",
        "name": name,
        "role": "Doctor",
        "department": department,
        "specialisation": specialisation,
        "phone": phone,
        "email": email,
        "reg_number": reg_number,
        "notes": notes,
        "is_active": is_active,
        "experience": 0,
        "weekly_off": "",
        "can_first": False,
        "can_second": False,
        "can_third": False,
    }


def _idx_of(value: str, options: list) -> int:
    val_up = str(value).strip().upper()
    for i, opt in enumerate(options):
        if str(opt).strip().upper() == val_up:
            return i
    return 0


def _safe_int(val, default: int = 0) -> int:
    try:
        return int(float(str(val)))
    except (ValueError, TypeError):
        return default


def _parse_weekly_off_list(raw: str) -> list[str]:
    """Parse comma/semicolon separated day names."""
    if not raw or str(raw).strip() in ("", "nan"):
        return []
    parts = [p.strip().title() for p in str(raw).replace(";", ",").split(",") if p.strip()]
    return parts

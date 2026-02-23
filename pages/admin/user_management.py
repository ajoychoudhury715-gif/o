# pages/admin/user_management.py
"""Admin user management: users + dynamic function access control."""

from __future__ import annotations
import streamlit as st

from data.auth_repo import create_user, get_all_users, reset_password, update_username
from data.supabase_client import get_supabase_client
from config.settings import get_supabase_config
from security.rbac import (
    get_function_catalog,
    get_role_permissions_config,
    save_role_permissions_config,
    get_user_override_config,
    save_user_override_config,
    get_permissions_config_error,
    resolve_effective_permissions,
    load_permissions_for_session,
    has_access,
)


def render() -> None:
    """Render the user management admin page."""
    if str(st.session_state.get("user_role", "")).strip().lower() != "admin":
        st.error("You do not have permission to access User Management.")
        st.stop()

    st.markdown("# 👤 User Management")
    st.markdown("Create and manage user accounts for assistants and frontdesk staff.")

    if not has_access("action::admin::user_management"):
        st.error("You do not have permission to manage users.")
        st.stop()

    # Tabs for Add User and View Users
    tab1, tab2 = st.tabs(["➕ Add New User", "👥 View Users"])

    with tab1:
        _render_add_user()

    with tab2:
        _render_view_users()


def _render_add_user() -> None:
    """Render form to add new user."""
    st.markdown("## Add New User")

    col1, col2 = st.columns(2)

    with col1:
        username = st.text_input(
            "Username",
            placeholder="e.g., assistant_001",
            help="Unique username for login"
        )

    with col2:
        role = st.selectbox(
            "Role",
            ["assistant", "doctor", "frontdesk", "admin"],
            help="User role determines access level"
        )

    password = st.text_input(
        "Password",
        type="password",
        placeholder="Enter a secure password",
        help="Minimum 6 characters"
    )

    confirm_password = st.text_input(
        "Confirm Password",
        type="password",
        placeholder="Re-enter password"
    )

    st.markdown("### Function Access Control")
    function_ids, labels = _permission_options()
    role_defaults = get_role_permissions_config(role)
    selected_role_permissions = st.multiselect(
        "Role Permissions",
        options=function_ids,
        default=role_defaults,
        format_func=lambda fid: labels.get(fid, fid),
        help="Template permissions for this role. Applies to all users of this role unless user override is enabled.",
        key=f"new_role_permissions_{role}",
    )

    col_role1, col_role2 = st.columns([1, 2])
    with col_role1:
        if st.button("💾 Save Role Template", key=f"save_role_template_{role}", width='stretch'):
            if save_role_permissions_config(role, selected_role_permissions):
                st.success(f"Saved role permissions for '{role}'.")
            else:
                _show_rbac_save_error("save role permissions")
    with col_role2:
        st.caption("Role template is stored in DB and reused for all users with this role.")

    override_enabled_new = st.checkbox(
        "Override permissions for this user",
        value=False,
        help="Enable to assign custom function access for this specific user.",
        key="new_user_override_enabled",
    )
    override_permissions_new = st.multiselect(
        "User Override Permissions",
        options=function_ids,
        default=selected_role_permissions,
        format_func=lambda fid: labels.get(fid, fid),
        disabled=not override_enabled_new,
        key="new_user_override_permissions",
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("✅ Create User", type="primary", width='stretch'):
            # Validation
            if not username or not password:
                st.error("❌ Username and password are required")
            elif len(password) < 6:
                st.error("❌ Password must be at least 6 characters")
            elif password != confirm_password:
                st.error("❌ Passwords do not match")
            elif not all(c.isalnum() or c in ('_', '.') for c in username):
                st.error("❌ Username can only contain letters, numbers, underscores, and periods")
            else:
                role_save_ok = save_role_permissions_config(role, selected_role_permissions)
                # Try to create user
                success = create_user(username, password, role)
                if success:
                    created_user = _get_user_by_username(username)
                    if created_user and created_user.get("id"):
                        save_user_override_config(
                            str(created_user.get("id")),
                            override_enabled_new,
                            override_permissions_new if override_enabled_new else [],
                        )

                    if not role_save_ok:
                        detail = get_permissions_config_error()
                        if detail:
                            st.warning(f"User created, but role permissions were not saved. {detail}")
                        else:
                            st.warning("User created, but role permissions were not saved.")
                    st.success(f"✅ User '{username}' created successfully with role '{role}'!")
                    st.balloons()
                else:
                    st.error(f"❌ Failed to create user. Username may already exist or database is unreachable.")

    with col2:
        st.markdown("")  # Spacer


def _render_view_users() -> None:
    """Render table of all users with management options."""
    st.markdown("## All Users")

    users = get_all_users()

    if not users:
        st.info("ℹ️ No users found. Create one using the 'Add New User' tab.")
        return

    # Display users in a nice table format
    st.markdown("### Registered Users")

    # Create columns for display
    cols = st.columns([2, 2, 2, 1, 1, 1])
    cols[0].markdown("**Username**")
    cols[1].markdown("**Role**")
    cols[2].markdown("**Status**")
    cols[3].markdown("**Edit**")
    cols[4].markdown("**Reset PW**")
    cols[5].markdown("**Deactivate**")
    st.divider()

    for user in users:
        username = user.get("username", "")
        role = user.get("role", "unknown")
        is_active = user.get("is_active", True)
        user_id = user.get("id", "")

        status_badge = "🟢 Active" if is_active else "🔴 Inactive"

        cols = st.columns([2, 2, 2, 1, 1, 1])

        cols[0].markdown(f"`{username}`")
        if role == "frontdesk":
            cols[1].markdown(f"🎫 {role}")
        elif role == "doctor":
            cols[1].markdown(f"🩺 {role}")
        elif role == "admin":
            cols[1].markdown(f"⚙️ {role}")
        else:
            cols[1].markdown(f"👤 {role}")
        cols[2].markdown(status_badge)

        # Edit username button
        with cols[3]:
            if st.button("✏️", key=f"edit_{user_id}", help="Edit username", width='stretch'):
                st.session_state[f"show_edit_{user_id}"] = True

        # Reset password button
        with cols[4]:
            if st.button("🔑", key=f"reset_{user_id}", help="Reset password", width='stretch'):
                st.session_state[f"show_reset_{user_id}"] = True

        # Deactivate button
        with cols[5]:
            action = "Activate" if not is_active else "Deactivate"
            if st.button("⚠️" if is_active else "✓", key=f"toggle_{user_id}", help=action, width='stretch'):
                if _toggle_user_status(user_id, username, is_active):
                    st.rerun()

    st.divider()

    # Handle password reset dialogs
    for user in users:
        user_id = user.get("id", "")
        username = user.get("username", "")

        if st.session_state.get(f"show_reset_{user_id}"):
            st.markdown(f"### Reset Password for `{username}`")

            new_password = st.text_input(
                "New Password",
                type="password",
                key=f"new_pw_{user_id}",
                placeholder="Enter new password",
            )
            confirm = st.text_input(
                "Confirm Password",
                type="password",
                key=f"confirm_pw_{user_id}",
                placeholder="Confirm new password",
            )

            col1, col2 = st.columns(2)

            with col1:
                if st.button("✅ Reset", key=f"do_reset_{user_id}", type="primary", width='stretch'):
                    if not new_password:
                        st.error("❌ Password cannot be empty")
                    elif len(new_password) < 6:
                        st.error("❌ Password must be at least 6 characters")
                    elif new_password != confirm:
                        st.error("❌ Passwords do not match")
                    else:
                        if reset_password(username, new_password):
                            st.success(f"✅ Password reset for {username}!")
                            st.session_state[f"show_reset_{user_id}"] = False
                            st.rerun()
                        else:
                            st.error("❌ Failed to reset password")

            with col2:
                if st.button("Cancel", key=f"cancel_reset_{user_id}", width='stretch'):
                    st.session_state[f"show_reset_{user_id}"] = False
                    st.rerun()

    # Handle username edit dialogs
    for user in users:
        user_id = user.get("id", "")
        username = user.get("username", "")

        if st.session_state.get(f"show_edit_{user_id}"):
            st.markdown(f"### Edit Username for `{username}`")

            new_username = st.text_input(
                "New Username",
                value=username,
                key=f"new_username_{user_id}",
                placeholder="Enter new username",
                help="Username can contain letters, numbers, underscores, and periods",
            )

            col1, col2 = st.columns(2)

            with col1:
                if st.button("✅ Update", key=f"do_edit_{user_id}", type="primary", width='stretch'):
                    if not new_username or not new_username.strip():
                        st.error("❌ Username cannot be empty")
                    elif new_username == username:
                        st.error("❌ New username is the same as current username")
                    elif not all(c.isalnum() or c in ('_', '.') for c in new_username):
                        st.error("❌ Username can only contain letters, numbers, underscores, and periods")
                    else:
                        if update_username(username, new_username):
                            st.success(f"✅ Username updated from '{username}' to '{new_username}'!")
                            st.session_state[f"show_edit_{user_id}"] = False
                            st.rerun()
                        else:
                            st.error("❌ Failed to update username (may already exist)")

            with col2:
                if st.button("Cancel", key=f"cancel_edit_{user_id}", width='stretch'):
                    st.session_state[f"show_edit_{user_id}"] = False
                    st.rerun()

    if has_access("action::admin::permissions"):
        _render_function_access_control(users)
    else:
        st.info("Function Access Control is restricted for your account.")


def _render_function_access_control(users: list[dict]) -> None:
    st.markdown("## Function Access Control")
    st.caption("Dynamic list of functions/pages currently available in the app.")

    function_ids, labels = _permission_options()
    if not function_ids:
        st.warning("No functions detected.")
        return

    # Edit role template
    role_to_edit = st.selectbox(
        "Role Template",
        ["assistant", "frontdesk", "admin"],
        key="rbac_role_edit_select",
    )
    role_allowed = get_role_permissions_config(role_to_edit)
    role_selection = st.multiselect(
        f"Permissions for role: {role_to_edit}",
        options=function_ids,
        default=role_allowed,
        format_func=lambda fid: labels.get(fid, fid),
        key=f"rbac_role_permissions_{role_to_edit}",
    )
    if st.button("💾 Save Role Permissions", key=f"rbac_save_role_{role_to_edit}", width='stretch'):
        if save_role_permissions_config(role_to_edit, role_selection):
            st.success(f"Saved permissions for role '{role_to_edit}'.")
            # Refresh active session if current user is in this role and no override.
            if str(st.session_state.get("user_role", "")).strip().lower() == role_to_edit:
                current_user_id = str(st.session_state.get("current_user_id", "") or "").strip()
                enabled, _ = get_user_override_config(current_user_id)
                if not enabled:
                    load_permissions_for_session(role_to_edit, current_user_id or None)
        else:
            _show_rbac_save_error("save role permissions")

    st.divider()

    # Edit per-user override
    user_map = {
        f"{u.get('username', '')} ({u.get('role', '')})": u
        for u in users
        if u.get("username") and u.get("id")
    }
    if not user_map:
        st.info("No users available for override configuration.")
        return

    user_label = st.selectbox("User Override", list(user_map.keys()), key="rbac_user_edit_select")
    selected_user = user_map[user_label]
    user_id = str(selected_user.get("id"))
    username = str(selected_user.get("username", ""))
    role = str(selected_user.get("role", "assistant")).strip().lower()

    override_enabled, override_allowed = get_user_override_config(user_id)
    role_fallback_allowed = get_role_permissions_config(role)
    default_user_options = override_allowed if override_enabled else role_fallback_allowed

    override_enabled_ui = st.checkbox(
        f"Enable user-specific override for {username}",
        value=override_enabled,
        key=f"rbac_override_enabled_{user_id}",
    )
    user_selection = st.multiselect(
        "Allowed functions (user override)",
        options=function_ids,
        default=default_user_options,
        format_func=lambda fid: labels.get(fid, fid),
        disabled=not override_enabled_ui,
        key=f"rbac_user_permissions_{user_id}",
    )

    if st.button("💾 Save User Override", key=f"rbac_save_user_{user_id}", width='stretch'):
        if save_user_override_config(user_id, override_enabled_ui, user_selection if override_enabled_ui else []):
            st.success(f"Saved function access for {username}.")
            # If editing current logged-in user, refresh live permissions in session.
            if str(st.session_state.get("current_user_id", "")) == user_id:
                load_permissions_for_session(role, user_id)
        else:
            _show_rbac_save_error("save user override")

    effective = resolve_effective_permissions(role, user_id)
    st.caption(f"Effective access for {username}: {len(effective)} function(s).")


def _permission_options() -> tuple[list[str], dict[str, str]]:
    catalog = get_function_catalog()
    ids = [item["id"] for item in catalog]
    labels = {item["id"]: item["label"] for item in catalog}
    return ids, labels


def _show_rbac_save_error(action_label: str) -> None:
    detail = str(get_permissions_config_error() or "").strip()
    if not detail:
        st.error(f"Failed to {action_label}.")
        return

    lower = detail.lower()
    st.error(f"Failed to {action_label}. {detail}")
    if ("does not exist" in lower and "rbac_" in lower) or "relation" in lower:
        st.info("Run the latest `supabase_setup.sql` in Supabase SQL Editor to create RBAC tables.")


def _get_user_by_username(username: str) -> dict | None:
    target = str(username or "").strip().lower()
    if not target:
        return None
    users = get_all_users()
    for user in users:
        if str(user.get("username", "")).strip().lower() == target:
            return user
    return None


def _toggle_user_status(user_id: str, username: str, is_active: bool) -> bool:
    """Toggle user active/inactive status."""
    try:
        url, key, *_ = get_supabase_config()
        if not url or not key:
            st.error("❌ Supabase not configured")
            return False

        client = get_supabase_client(url, key)
        if not client:
            st.error("❌ Failed to connect to database")
            return False

        new_status = not is_active
        client.table("users").update({"is_active": new_status}).eq("id", user_id).execute()

        action = "activated" if new_status else "deactivated"
        st.success(f"✅ User {username} {action}!")
        return True
    except Exception as e:
        st.error(f"❌ Failed to update user status: {e}")
        return False

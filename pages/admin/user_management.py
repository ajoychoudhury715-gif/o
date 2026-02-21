# pages/admin/user_management.py
"""Admin user management: create users for assistants and frontdesk staff."""

import streamlit as st
from data.auth_repo import create_user, get_all_users, reset_password
from data.supabase_client import get_supabase_client
from config.settings import get_supabase_config


def render() -> None:
    """Render the user management admin page."""
    st.markdown("# 👤 User Management")
    st.markdown("Create and manage user accounts for assistants and frontdesk staff.")

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
            ["assistant", "frontdesk"],
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
            elif not username.isalnum() and '_' not in username:
                st.error("❌ Username can only contain letters, numbers, and underscores")
            else:
                # Try to create user
                success = create_user(username, password, role)
                if success:
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
    cols = st.columns([2, 2, 2, 1, 1])
    cols[0].markdown("**Username**")
    cols[1].markdown("**Role**")
    cols[2].markdown("**Status**")
    cols[3].markdown("**Reset PW**")
    cols[4].markdown("**Deactivate**")
    st.divider()

    for user in users:
        username = user.get("username", "")
        role = user.get("role", "unknown")
        is_active = user.get("is_active", True)
        user_id = user.get("id", "")

        status_badge = "🟢 Active" if is_active else "🔴 Inactive"

        cols = st.columns([2, 2, 2, 1, 1])

        cols[0].markdown(f"`{username}`")
        cols[1].markdown(f"🎫 {role}" if role == "frontdesk" else f"👨‍⚕️ {role}")
        cols[2].markdown(status_badge)

        # Reset password button
        with cols[3]:
            if st.button("🔑", key=f"reset_{user_id}", help="Reset password", width='stretch'):
                st.session_state[f"show_reset_{user_id}"] = True

        # Deactivate button
        with cols[4]:
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

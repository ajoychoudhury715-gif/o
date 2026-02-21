# pages/auth/login.py
"""Login page for authentication."""

import streamlit as st
from data.auth_repo import authenticate


def render() -> None:
    """Render the login page."""
    # Center the login form
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("## 🦷 THE DENTAL BOND")
        st.markdown("---")
        st.markdown("### Login")

        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")

        if st.button("Login", use_container_width=True, type="primary"):
            if not username or not password:
                st.error("Please enter username and password")
            else:
                user = authenticate(username, password)
                if user:
                    st.session_state.current_user = user["username"]
                    st.session_state.user_role = user["role"]
                    st.success(f"Welcome, {user['username']}!")
                    st.rerun()
                else:
                    st.error("Invalid username or password")

        st.markdown("---")
        st.caption("Default: admin / admin123")

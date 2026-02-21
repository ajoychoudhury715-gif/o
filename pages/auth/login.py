# pages/auth/login.py
"""Simple login page using default Streamlit styling."""

import streamlit as st
from data.auth_repo import authenticate

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="The Dental Bond – Schedule Management",
    page_icon="🦷",
    layout="centered",
)


# ── Main layout ────────────────────────────────────────────────────────────────
def render() -> None:
    """Render the login page."""
    # Initialize session state
    if "login_error" not in st.session_state:
        st.session_state.login_error = False

    # Title and description
    st.title("🦷 The Dental Bond")
    st.subheader("Sign in to your account")

    # Error message
    if st.session_state.login_error:
        st.error(st.session_state.login_error)

    # Form inputs
    email = st.text_input("Email Address", key="login_email", placeholder="your@email.com")
    password = st.text_input("Password", key="login_password", placeholder="••••••••", type="password")

    # Sign in button
    if st.button("Sign In", use_container_width=True):
        if not email or not password:
            st.session_state.login_error = "Please enter your email and password."
            st.rerun()
        else:
            user = authenticate(email, password)
            if user:
                st.session_state.current_user = user["username"]
                st.session_state.user_role = user["role"]
                st.session_state.login_error = False
                st.success("Signed in successfully!")
                st.rerun()
            else:
                st.session_state.login_error = "Incorrect email or password."
                st.rerun()

    # Footer
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        st.caption("Need access? Contact your admin")
    with col2:
        st.caption("v2.4.1", unsafe_allow_html=True)

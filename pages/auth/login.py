# pages/auth/login.py
"""Login page."""

import streamlit as st

from data.auth_repo import authenticate, issue_login_token
from security.rbac import load_permissions_for_session


def _inject_css() -> None:
    st.markdown(
        """
        <style>
        #MainMenu, footer, header, [data-testid="stHeader"] {
          display: none !important;
          height: 0 !important;
        }

        html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
          background: #e8e6f5;
          min-height: 100dvh;
          font-family: 'Segoe UI', sans-serif;
          overflow: hidden !important;
        }

        [data-testid="stAppViewContainer"] > .main {
          padding: 0 !important;
          min-height: 100dvh !important;
        }

        .main .block-container {
          max-width: 520px !important;
          margin: 0 auto !important;
          min-height: 100dvh !important;
          padding: 24px !important;
          display: flex !important;
          align-items: center !important;
          justify-content: center !important;
        }

        .login-panel {
          width: 100%;
        }

        .login-title {
          font-size: 28px;
          font-weight: 800;
          letter-spacing: 2px;
          color: #1a1a2e;
          text-align: center;
          margin-bottom: 6px;
        }

        .subtitle {
          text-align: center;
          color: #777;
          font-size: 13px;
          margin-bottom: 24px;
        }

        .login-panel [data-testid="stTextInput"] {
          margin-bottom: 12px;
        }

        .login-panel [data-testid="stTextInput"] label {
          display: none !important;
        }

        .login-panel [data-testid="stTextInput"] input {
          width: 100% !important;
          padding: 14px 16px !important;
          border: none !important;
          background: #f0eefa !important;
          border-radius: 10px !important;
          font-size: 15px !important;
          color: #333 !important;
          box-shadow: none !important;
        }

        .login-panel [data-testid="stTextInput"] input::placeholder {
          color: #9f9f9f !important;
        }

        .login-panel [data-testid="stTextInput"] input:focus {
          background: #e4dff5 !important;
          box-shadow: none !important;
        }

        .forgot-wrap {
          display: flex;
          justify-content: flex-end;
          margin-top: -2px;
          margin-bottom: 12px;
        }

        .forgot-wrap .stButton button[kind="tertiary"] {
          background: transparent !important;
          border: none !important;
          color: #6c5ce7 !important;
          font-size: 12px !important;
          padding: 0 !important;
          height: auto !important;
          min-height: auto !important;
          box-shadow: none !important;
        }

        .login-panel .stButton button[kind="primary"] {
          width: 100% !important;
          padding: 14px !important;
          background: #6c5ce7 !important;
          color: #fff !important;
          border: none !important;
          border-radius: 10px !important;
          font-size: 15px !important;
          font-weight: 700 !important;
          letter-spacing: 0.5px !important;
          box-shadow: none !important;
        }

        .login-panel .stButton button[kind="primary"]:hover {
          background: #5a4bd1 !important;
        }

        .divider {
          display: flex;
          align-items: center;
          gap: 10px;
          margin: 22px 0 14px;
          color: #a3a3a3;
          font-size: 13px;
          font-weight: 700;
        }

        .divider::before,
        .divider::after {
          content: "";
          flex: 1;
          height: 1px;
          background: #dcd9ee;
        }

        .social-btn {
          width: 100%;
          padding: 11px;
          border: 1.5px solid #ddd8f0;
          border-radius: 10px;
          background: #fff;
          font-size: 13.5px;
          color: #333;
          margin-bottom: 10px;
          text-align: center;
        }

        .signup-text {
          text-align: center;
          font-size: 13px;
          color: #888;
          margin-top: 20px;
        }

        .signup-text span {
          color: #6c5ce7;
          font-weight: 600;
        }

        @media (max-width: 680px) {
          .main .block-container {
            padding: 16px !important;
          }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render() -> None:
    """Render login page."""
    if "login_error" not in st.session_state:
        st.session_state.login_error = False

    _inject_css()

    st.markdown('<div class="login-panel">', unsafe_allow_html=True)
    st.markdown('<div class="login-title">LOGIN</div>', unsafe_allow_html=True)
    st.markdown(
        '<p class="subtitle">Welcome back! Please sign in to continue.</p>',
        unsafe_allow_html=True,
    )

    if st.session_state.login_error:
        st.warning(st.session_state.login_error)

    username = st.text_input(
        "Username",
        key="login_username",
        placeholder="Username",
        label_visibility="collapsed",
    )
    password = st.text_input(
        "Password",
        key="login_password",
        placeholder="Password",
        type="password",
        label_visibility="collapsed",
    )

    st.markdown('<div class="forgot-wrap">', unsafe_allow_html=True)
    if st.button("Forgot Password?", key="forgot_password_link", type="tertiary"):
        st.session_state.show_reset_password = True
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    if st.button("Login Now", use_container_width=True, key="login_now_button", type="primary"):
        if not username or not password:
            st.session_state.login_error = "Please enter your username and password."
            st.rerun()
        user = authenticate(username, password)
        if user:
            st.session_state.current_user = user["username"]
            st.session_state.current_user_id = user.get("id")
            st.session_state.user_role = user["role"]
            st.session_state.show_reset_password = False
            st.session_state.login_error = False
            load_permissions_for_session(user["role"], user.get("id"))
            # Persist login across browser refresh using signed URL token.
            try:
                token = issue_login_token(user["username"], user["role"])
                if token:
                    st.query_params["auth"] = token
            except Exception:
                pass
            st.rerun()
        st.session_state.login_error = "Invalid username or password. Please try again."
        st.rerun()

    st.markdown('<div class="divider">Login with Others</div>', unsafe_allow_html=True)
    st.markdown('<div class="social-btn">Login with <strong>Google</strong></div>', unsafe_allow_html=True)
    st.markdown(
        '<p class="signup-text">Don\'t have an account? <span>Sign Up</span></p>',
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

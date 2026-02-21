# pages/auth/login.py
"""Custom split login page."""

import streamlit as st
from data.auth_repo import authenticate


def _inject_css() -> None:
    st.markdown(
        """
        <style>
        #MainMenu, footer, header {
          visibility: hidden;
        }

        html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
          background: #e8e6f5;
          min-height: 100vh;
          font-family: 'Segoe UI', sans-serif;
        }

        .block-container {
          padding-top: 20px !important;
          padding-bottom: 20px !important;
          max-width: 940px !important;
        }

        .login-card {
          width: 100%;
          min-height: 520px;
          border-radius: 24px;
          overflow: hidden;
          box-shadow: 0 20px 60px rgba(100, 80, 220, 0.18);
          background: #fff;
        }

        .left-panel {
          padding: 40px 34px 24px;
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
          color: #888;
          font-size: 13px;
          margin-bottom: 26px;
        }

        .field-icon {
          font-size: 15px;
          color: #9e9cb8;
          margin: 8px 0 4px 10px;
          position: relative;
          z-index: 3;
        }

        .left-panel [data-testid="stTextInput"] {
          margin-top: -24px;
          margin-bottom: 12px;
        }

        .left-panel [data-testid="stTextInput"] label {
          display: none !important;
        }

        .left-panel [data-testid="stTextInput"] input {
          width: 100% !important;
          padding: 14px 16px 14px 44px !important;
          border: none !important;
          background: #f0eefa !important;
          border-radius: 10px !important;
          font-size: 14px !important;
          color: #333 !important;
          outline: none !important;
          box-shadow: none !important;
        }

        .left-panel [data-testid="stTextInput"] input::placeholder {
          color: #aaa !important;
        }

        .left-panel [data-testid="stTextInput"] input:focus {
          background: #e4dff5 !important;
          border: none !important;
          box-shadow: none !important;
        }

        .forgot-wrap {
          text-align: right;
          margin-top: -2px;
          margin-bottom: 14px;
        }

        .forgot-wrap button {
          background: transparent !important;
          border: none !important;
          color: #6c5ce7 !important;
          font-size: 12px !important;
          padding: 0 !important;
          height: auto !important;
          min-height: auto !important;
        }

        .left-panel [data-testid="stButton"] button {
          width: 100%;
          padding: 14px !important;
          background: #6c5ce7 !important;
          color: #fff !important;
          border: none !important;
          border-radius: 10px !important;
          font-size: 15px !important;
          font-weight: 700 !important;
          letter-spacing: 0.5px !important;
          transition: background 0.2s, transform 0.15s !important;
        }

        .left-panel [data-testid="stButton"] button:hover {
          background: #5a4bd1 !important;
          transform: translateY(-1px) !important;
        }

        .divider {
          display: flex;
          align-items: center;
          gap: 10px;
          margin: 20px 0 14px;
          color: #bbb;
          font-size: 13px;
          font-weight: 700;
        }

        .divider::before,
        .divider::after {
          content: "";
          flex: 1;
          height: 1px;
          background: #e5e5e5;
        }

        .social-btn {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 10px;
          width: 100%;
          padding: 11px;
          border: 1.5px solid #ece9fb;
          border-radius: 10px;
          background: #fff;
          font-size: 13.5px;
          font-weight: 500;
          color: #333;
          margin-bottom: 10px;
          text-align: center;
        }

        .social-btn:hover {
          background: #f7f4ff;
          border-color: #c0b5f0;
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

        .right-panel {
          height: 100%;
          min-height: 520px;
          background: linear-gradient(135deg, #6c5ce7 0%, #7d6ff0 60%, #8a7cf5 100%);
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          padding: 40px 30px;
          position: relative;
          overflow: hidden;
        }

        .right-panel::before {
          content: "";
          position: absolute;
          width: 320px;
          height: 320px;
          background: rgba(255,255,255,0.07);
          border-radius: 50%;
          top: -80px;
          right: -80px;
        }

        .right-panel::after {
          content: "";
          position: absolute;
          width: 200px;
          height: 200px;
          background: rgba(255,255,255,0.06);
          border-radius: 50%;
          bottom: -50px;
          left: -40px;
        }

        .right-card {
          background: rgba(255,255,255,0.15);
          backdrop-filter: blur(10px);
          border: 1px solid rgba(255,255,255,0.25);
          border-radius: 20px;
          padding: 20px;
          z-index: 1;
          text-align: center;
        }

        .avatar-placeholder {
          width: 200px;
          height: 240px;
          background: rgba(255,255,255,0.2);
          border-radius: 14px;
          display: flex;
          align-items: center;
          justify-content: center;
          margin: 0 auto;
          font-size: 70px;
        }

        .badge {
          width: 46px;
          height: 46px;
          background: #fff;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 20px;
          box-shadow: 0 4px 14px rgba(0,0,0,0.12);
          position: absolute;
          left: 18px;
          bottom: 90px;
          z-index: 2;
        }

        .tagline {
          color: rgba(255,255,255,0.9);
          font-size: 13.5px;
          font-weight: 600;
          letter-spacing: 0.3px;
          z-index: 1;
          margin-top: 14px;
          text-align: center;
        }

        .tagline span {
          color: #ffd700;
        }

        @media (max-width: 900px) {
          .right-panel {
            min-height: 220px;
          }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render() -> None:
    """Render split login page."""
    if "login_error" not in st.session_state:
        st.session_state.login_error = False

    _inject_css()

    st.markdown('<div class="login-card">', unsafe_allow_html=True)
    left_col, right_col = st.columns([1.45, 1], gap="small")

    with left_col:
        st.markdown('<div class="left-panel">', unsafe_allow_html=True)
        st.markdown('<div class="login-title">LOGIN</div>', unsafe_allow_html=True)
        st.markdown(
            '<p class="subtitle">Welcome back! Please sign in to continue.</p>',
            unsafe_allow_html=True,
        )

        if st.session_state.login_error:
            st.warning(st.session_state.login_error)

        st.markdown('<div class="field-icon">👤</div>', unsafe_allow_html=True)
        username = st.text_input(
            "Username",
            key="login_username",
            placeholder="Username",
            label_visibility="collapsed",
        )

        st.markdown('<div class="field-icon">🔒</div>', unsafe_allow_html=True)
        password = st.text_input(
            "Password",
            key="login_password",
            placeholder="Password",
            type="password",
            label_visibility="collapsed",
        )

        st.markdown('<div class="forgot-wrap">', unsafe_allow_html=True)
        if st.button("Forgot Password?", key="forgot_password_link", use_container_width=False):
            st.session_state.show_reset_password = True
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        if st.button("Login Now", use_container_width=True, key="login_now_button"):
            if not username or not password:
                st.session_state.login_error = "Please enter your username and password."
                st.rerun()
            user = authenticate(username, password)
            if user:
                st.session_state.current_user = user["username"]
                st.session_state.user_role = user["role"]
                st.session_state.login_error = False
                st.rerun()
            st.session_state.login_error = "Invalid username or password. Please try again."
            st.rerun()

        st.markdown('<div class="divider">Login with Others</div>', unsafe_allow_html=True)
        st.markdown('<div class="social-btn">G Login with <strong>Google</strong></div>', unsafe_allow_html=True)
        st.markdown('<div class="social-btn">f Login with <strong>Facebook</strong></div>', unsafe_allow_html=True)
        st.markdown(
            '<p class="signup-text">Don\'t have an account? <span>Sign Up</span></p>',
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with right_col:
        st.markdown(
            """
            <div class="right-panel">
              <div class="right-card">
                <div class="avatar-placeholder">👩‍💼</div>
              </div>
              <div class="badge">⚡</div>
              <p class="tagline">Your journey starts here. <span>✦</span></p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)

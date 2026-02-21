# pages/auth/login.py
"""Modern professional login page inspired by Auth0."""

import streamlit as st
from data.auth_repo import authenticate

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="The Dental Bond – Schedule Management",
    page_icon="🦷",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── Professional Modern CSS ────────────────────────────────────────────────────
st.markdown("""
<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  min-height: 100vh;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', sans-serif;
}

#MainMenu, footer, header {
  visibility: hidden;
}

.block-container {
  padding: 0 !important;
  max-width: 100% !important;
  width: 100% !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  min-height: 100vh !important;
}

.main {
  padding: 20px !important;
  width: 100% !important;
  max-width: 100% !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
}

/* Login Card */
.login-wrapper {
  background: white;
  border-radius: 12px;
  box-shadow: 0 7px 14px 0 rgba(0, 0, 0, 0.1);
  width: 100%;
  max-width: 380px;
  padding: 50px 40px;
}

.login-header {
  text-align: center;
  margin-bottom: 40px;
}

.login-logo {
  font-size: 40px;
  margin-bottom: 16px;
  display: block;
}

.login-title {
  font-size: 22px;
  font-weight: 600;
  color: #1a1a1a;
  margin-bottom: 8px;
  letter-spacing: -0.5px;
}

.login-subtitle {
  font-size: 14px;
  color: #6b7684;
  font-weight: 400;
  line-height: 1.5;
}

.login-divider {
  margin: 40px 0;
  border: none;
  border-top: 1px solid #e1e6eb;
}

.login-footer {
  margin-top: 24px;
  text-align: center;
  font-size: 12px;
  color: #9da5b0;
  line-height: 1.6;
}

.login-footer a {
  color: #007bff;
  text-decoration: none;
  font-weight: 500;
}

.login-footer a:hover {
  color: #0056b3;
  text-decoration: underline;
}

/* Form Elements */
[data-testid="stTextInput"] label {
  font-size: 13px !important;
  font-weight: 600 !important;
  color: #1a1a1a !important;
  letter-spacing: 0.3px !important;
  margin-bottom: 8px !important;
  text-transform: none !important;
}

[data-testid="stTextInput"] input {
  background-color: #f7fafb !important;
  border: 1px solid #e1e6eb !important;
  border-radius: 6px !important;
  font-size: 14px !important;
  padding: 11px 14px !important;
  color: #1a1a1a !important;
  transition: all 0.2s ease !important;
  font-family: inherit !important;
}

[data-testid="stTextInput"] input::placeholder {
  color: #b4bcc4 !important;
  font-weight: 400 !important;
}

[data-testid="stTextInput"] input:focus {
  border-color: #007bff !important;
  background-color: white !important;
  box-shadow: 0 0 0 3px rgba(0, 123, 255, 0.1) !important;
  outline: none !important;
}

[data-testid="stElementContainer"] {
  margin-bottom: 20px !important;
}

/* Buttons */
[data-testid="stButton"] button {
  background: linear-gradient(135deg, #007bff 0%, #0056b3 100%) !important;
  color: white !important;
  border: none !important;
  border-radius: 6px !important;
  font-size: 14px !important;
  font-weight: 600 !important;
  padding: 11px 16px !important;
  letter-spacing: 0.2px !important;
  transition: all 0.3s ease !important;
  cursor: pointer !important;
  width: 100% !important;
  box-shadow: 0 2px 5px 0 rgba(0, 123, 255, 0.2) !important;
  margin-bottom: 0 !important;
}

[data-testid="stButton"] button:hover {
  opacity: 0.95 !important;
  transform: translateY(-1px) !important;
  box-shadow: 0 4px 12px 0 rgba(0, 123, 255, 0.3) !important;
}

[data-testid="stButton"] button:active {
  transform: translateY(0) !important;
}

/* Error/Alert */
[data-testid="stAlert"] {
  background-color: #fff3cd !important;
  border: 1px solid #ffe69c !important;
  border-radius: 6px !important;
  color: #856404 !important;
  padding: 12px 14px !important;
  margin-bottom: 20px !important;
  font-size: 13px !important;
}

.stAlert > div > div {
  color: #856404 !important;
}

[data-testid="stToastContainer"] {
  font-size: 13px !important;
}

/* Columns */
[data-testid="stColumn"] {
  padding: 0 !important;
}

/* Success Message */
div[data-testid="stToast"] {
  background: #d4edda !important;
  color: #155724 !important;
}

/* Responsive */
@media (max-width: 600px) {
  .login-wrapper {
    padding: 40px 24px;
    max-width: 100%;
  }

  .login-title {
    font-size: 20px;
  }

  .login-subtitle {
    font-size: 13px;
  }
}
</style>
""", unsafe_allow_html=True)


# ── Main layout ────────────────────────────────────────────────────────────────
def render() -> None:
    """Render the professional login page."""
    # Initialize session state
    if "login_error" not in st.session_state:
        st.session_state.login_error = False

    # Login card wrapper
    st.markdown("""<div class="login-wrapper">""", unsafe_allow_html=True)

    # Header
    st.markdown("""
        <div class="login-header">
            <span class="login-logo">🦷</span>
            <div class="login-title">The Dental Bond</div>
            <div class="login-subtitle">Schedule Management System</div>
        </div>
    """, unsafe_allow_html=True)

    # Error message
    if st.session_state.login_error:
        st.warning(st.session_state.login_error)

    # Form inputs
    email = st.text_input(
        "Email Address",
        key="login_email",
        placeholder="you@example.com"
    )

    password = st.text_input(
        "Password",
        key="login_password",
        placeholder="••••••••",
        type="password"
    )

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
                st.session_state.login_error = "Invalid email or password. Please try again."
                st.rerun()

    # Footer
    st.markdown("""
        <div class="login-divider"></div>
        <div class="login-footer">
            Need access? <a href="#">Contact your admin</a><br>
            v2.4.1
        </div>
    """, unsafe_allow_html=True)

    st.markdown("""</div>""", unsafe_allow_html=True)

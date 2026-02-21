# pages/auth/login.py
"""Premium split-panel login page with full design integration."""

import streamlit as st
from data.auth_repo import authenticate

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="The Dental Bond – Schedule Management",
    page_icon="🦷",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS – Premium Centered Card Design ──────────────────────────────────
st.markdown("""
<style>
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --gold:        #C9A96E;
  --gold-light:  #E8D5B0;
  --gold-dark:   #A07840;
  --cream:       #FAF7F2;
  --dark:        #1A1A1A;
  --muted:       #6B6B6B;
  --border:      #E2D9CA;
  --white:       #FFFFFF;
  --error:       #C0392B;
  --success:     #27AE60;
}

html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
  font-family: 'Inter', 'Segoe UI', sans-serif !important;
  background: linear-gradient(135deg, #F5F0EA 0%, #E8D5B0 100%) !important;
  margin: 0 !important;
  padding: 0 !important;
  min-height: 100vh !important;
}

#MainMenu, footer, header { visibility: hidden; }

.block-container {
  padding: 0 !important;
  max-width: 100% !important;
  margin: 0 !important;
  width: 100% !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  min-height: 100vh !important;
}

.main {
  max-width: 100% !important;
  width: 100% !important;
  padding: 20px !important;
  margin: 0 !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
}

/* ── LOGIN CARD CONTAINER ── */
.login-container {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
}

.login-card {
  background: var(--white);
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(26, 26, 26, 0.15), 0 0 0 1px rgba(201, 169, 110, 0.1);
  width: 100%;
  max-width: 480px;
  padding: 60px 48px;
  animation: slideUp 0.6s ease-out;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* ── HEADER & BRANDING ── */
.card-header {
  text-align: center;
  margin-bottom: 40px;
  animation: fadeIn 0.8s ease-out;
}

.card-logo {
  font-family: 'Cormorant Garamond', serif;
  font-size: 32px;
  font-weight: 700;
  color: var(--dark);
  letter-spacing: 0.05em;
  margin-bottom: 12px;
}

.card-tagline {
  font-size: 11px;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  color: var(--gold-dark);
  font-weight: 600;
  margin-bottom: 16px;
}

.card-title {
  font-family: 'Cormorant Garamond', serif;
  font-size: 28px;
  font-weight: 600;
  color: var(--dark);
  line-height: 1.2;
  margin-bottom: 8px;
}

.card-subtitle {
  font-size: 13px;
  color: var(--muted);
  font-weight: 300;
  line-height: 1.5;
}

/* ── FORM STYLING ── */
.form-section {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 0;
}

.form-group {
  margin-bottom: 18px;
  position: relative;
  width: 100%;
}

.form-group label {
  display: block;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--muted);
  margin-bottom: 8px;
}

.role-selector {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-bottom: 28px;
  margin-top: 0;
}

.role-btn {
  padding: 13px 12px;
  border: 1.5px solid var(--border);
  border-radius: 10px;
  background: var(--white);
  cursor: pointer;
  font-size: 12px;
  font-family: 'Inter', sans-serif;
  font-weight: 500;
  color: var(--muted);
  letter-spacing: 0.03em;
  transition: all 0.3s ease;
  text-align: center;
  min-height: 48px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
}

.role-btn:hover {
  border-color: var(--gold);
  color: var(--gold-dark);
  background: rgba(201, 169, 110, 0.05);
  transform: translateY(-2px);
}

.role-btn.active {
  border-color: var(--gold);
  background: rgba(201, 169, 110, 0.12);
  color: var(--gold-dark);
  box-shadow: 0 4px 16px rgba(201, 169, 110, 0.2);
}

.alert {
  padding: 12px 14px;
  border-radius: 10px;
  font-size: 13px;
  margin-bottom: 20px;
  background: rgba(192, 57, 43, 0.08);
  border: 1.5px solid rgba(192, 57, 43, 0.25);
  color: var(--error);
  display: none;
  width: 100%;
  box-sizing: border-box;
}

.alert.show {
  display: block;
  animation: slideDown 0.3s ease-out;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.checkbox-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin: 16px 0 24px 0;
  width: 100%;
}

.checkbox-row label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--muted);
  margin: 0;
  cursor: pointer;
  flex-shrink: 0;
}

.checkbox-row input[type="checkbox"] {
  cursor: pointer;
  width: 16px;
  height: 16px;
  accent-color: var(--gold);
}

.checkbox-row a {
  font-size: 13px;
  color: var(--gold-dark);
  text-decoration: none;
  font-weight: 500;
  transition: all 0.2s;
  white-space: nowrap;
}

.checkbox-row a:hover {
  color: var(--gold);
}

.divider {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 28px 0 24px 0;
  font-size: 11px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--muted);
  width: 100%;
}

.divider::before,
.divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: var(--border);
}

.card-footer {
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid var(--border);
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 12px;
  color: var(--muted);
  text-align: center;
}

.card-footer p {
  margin: 0;
  line-height: 1.5;
}

.card-footer a {
  color: var(--gold-dark);
  text-decoration: none;
  font-weight: 500;
  transition: all 0.2s;
}

.card-footer a:hover {
  color: var(--gold);
}

/* ── STREAMLIT COMPONENT OVERRIDES ── */
[data-testid="stForm"] {
  background: transparent !important;
  border: none !important;
  padding: 0 !important;
}

[data-testid="stTextInput"] {
  margin-bottom: 0 !important;
}

[data-testid="stTextInput"] input,
[data-testid="stTextInput"] input[type="password"] {
  border: 1.5px solid var(--border) !important;
  border-radius: 10px !important;
  background: #FAFAF8 !important;
  font-family: 'Inter', sans-serif !important;
  font-size: 14px !important;
  color: var(--dark) !important;
  padding: 13px 14px !important;
  transition: all 0.3s !important;
  width: 100% !important;
}

[data-testid="stTextInput"] input::placeholder {
  color: #BFB8AE !important;
}

[data-testid="stTextInput"] input:focus {
  border-color: var(--gold) !important;
  background: var(--white) !important;
  box-shadow: 0 0 0 3px rgba(201, 169, 110, 0.1) !important;
}

[data-testid="stTextInput"] label {
  font-size: 11px !important;
  font-weight: 600 !important;
  letter-spacing: 0.12em !important;
  text-transform: uppercase !important;
  color: var(--muted) !important;
  font-family: 'Inter', sans-serif !important;
}

[data-testid="stForm"] button[type="submit"],
[data-testid="stFormSubmitButton"] button {
  width: 100% !important;
  background: linear-gradient(135deg, var(--gold-dark) 0%, var(--gold) 100%) !important;
  color: white !important;
  border: none !important;
  border-radius: 10px !important;
  padding: 14px !important;
  font-size: 13px !important;
  font-weight: 600 !important;
  letter-spacing: 0.15em !important;
  text-transform: uppercase !important;
  font-family: 'Inter', sans-serif !important;
  box-shadow: 0 8px 24px rgba(160, 120, 64, 0.3) !important;
  transition: all 0.3s !important;
  cursor: pointer !important;
  margin-bottom: 12px !important;
}

[data-testid="stForm"] button[type="submit"]:hover,
[data-testid="stFormSubmitButton"] button:hover {
  opacity: 0.94 !important;
  transform: translateY(-2px) !important;
  box-shadow: 0 12px 32px rgba(160, 120, 64, 0.4) !important;
}

[data-testid="stCheckbox"] label {
  font-size: 13px !important;
  color: var(--muted) !important;
  font-family: 'Inter', sans-serif !important;
}

[data-testid="stButton"] button {
  width: 100% !important;
  border: 1.5px solid var(--border) !important;
  background: var(--white) !important;
  color: var(--dark) !important;
  padding: 13px 14px !important;
  font-size: 13px !important;
  font-weight: 500 !important;
  transition: all 0.3s !important;
  border-radius: 10px !important;
  font-family: 'Inter', sans-serif !important;
  margin-bottom: 0 !important;
}

[data-testid="stButton"] button:hover {
  border-color: var(--gold) !important;
  background: rgba(201, 169, 110, 0.06) !important;
  color: var(--gold-dark) !important;
}

[data-testid="stButton"] button:active {
  transform: translateY(1px) !important;
}

hr {
  border-color: var(--border) !important;
}

[data-testid="stAlert"] {
  border-radius: 10px !important;
  font-family: 'Inter', sans-serif !important;
  margin-bottom: 12px !important;
}

[data-testid="stElementContainer"] {
  margin-bottom: 0 !important;
}

[data-testid="stColumn"] {
  padding: 0 !important;
}

/* ── RESPONSIVE DESIGN ── */
@media (max-width: 1200px) {
  .login-card { padding: 50px 40px; max-width: 460px; }
}

@media (max-width: 900px) {
  .login-card { padding: 45px 36px; max-width: 440px; }
  .card-header { margin-bottom: 36px; }
}

@media (max-width: 600px) {
  .login-card { padding: 36px 28px; max-width: 100%; margin: 20px; }
  .card-logo { font-size: 28px; margin-bottom: 10px; }
  .card-title { font-size: 24px; margin-bottom: 6px; }
  .card-subtitle { font-size: 12px; }
  .card-header { margin-bottom: 32px; }
  .role-selector { gap: 10px; margin-bottom: 24px; }
  .role-btn { font-size: 11px; padding: 11px 10px; min-height: 44px; }
  .form-group { margin-bottom: 16px; }
  .checkbox-row { margin: 14px 0 20px 0; flex-direction: column; align-items: flex-start; gap: 10px; }
  [data-testid="stTextInput"] { margin-bottom: 14px !important; }
  [data-testid="stForm"] button[type="submit"],
  [data-testid="stFormSubmitButton"] button {
    padding: 12px !important;
    font-size: 12px !important;
    margin-bottom: 10px !important;
  }
  [data-testid="stButton"] button {
    padding: 12px 12px !important;
    margin-bottom: 10px !important;
  }
  .divider { margin: 24px 0 20px 0; gap: 10px; }
  .card-footer { margin-top: 20px; padding-top: 18px; font-size: 11px; }
}
</style>
""", unsafe_allow_html=True)

# ── No longer needed with centered card design ────────────────────────────────

# ── Main layout ────────────────────────────────────────────────────────────────
def render() -> None:
    # Initialize session state
    if "login_error" not in st.session_state:
        st.session_state.login_error = False
    if "login_role" not in st.session_state:
        st.session_state.login_role = "admin"

    # Open card container
    st.markdown("""<div class="login-container"><div class="login-card">""", unsafe_allow_html=True)

    # Card header
    st.markdown("""
        <div class="card-header">
            <div class="card-logo">🦷</div>
            <div class="card-tagline">The Dental Bond</div>
            <div class="card-title">Welcome Back</div>
            <div class="card-subtitle">Access your dental practice management dashboard</div>
        </div>
    """, unsafe_allow_html=True)

    # Error alert
    error_placeholder = st.empty()
    if st.session_state.login_error:
        with error_placeholder.container():
            st.markdown(f'<div class="alert show">{st.session_state.login_error}</div>', unsafe_allow_html=True)

    # Role selector
    st.markdown('<label style="display:block;font-size:11px;font-weight:600;letter-spacing:.12em;text-transform:uppercase;color:#6B6B6B;margin-bottom:12px;">Sign in as</label>', unsafe_allow_html=True)

    role_col1, role_col2, role_col3 = st.columns(3, gap="small")
    with role_col1:
        doctor_clicked = st.button("👨‍⚕️\nDoctor", key="role_doctor_v2", use_container_width=True)
        if doctor_clicked:
            st.session_state.login_role = "admin"
    with role_col2:
        reception_clicked = st.button("👩‍💼\nReceptionist", key="role_reception_v2", use_container_width=True)
        if reception_clicked:
            st.session_state.login_role = "frontdesk"
    with role_col3:
        admin_clicked = st.button("⚙️\nAdmin", key="role_admin_v2", use_container_width=True)
        if admin_clicked:
            st.session_state.login_role = "assistant"

    # Form inputs
    email = st.text_input("Email Address", key="login_email", placeholder="you@thedentalbond.com")
    password = st.text_input("Password", key="login_password", placeholder="••••••••", type="password")

    # Remember me and Forgot password
    st.markdown(
        "<div class='checkbox-row'>"
        "<label style='display:flex;align-items:center;gap:6px;font-size:13px;color:#6B6B6B;margin:0;'>"
        "<input type='checkbox' id='remember' />"
        "<span>Remember me</span>"
        "</label>"
        "<a href='#'>Forgot password?</a>"
        "</div>",
        unsafe_allow_html=True,
    )

    # Sign in button
    if st.button("Sign In", key="btn_login", use_container_width=True):
        if not email or not password:
            st.session_state.login_error = "⚠️ Please enter your email and password."
            st.rerun()
        else:
            user = authenticate(email, password)
            if user:
                st.session_state.current_user = user["username"]
                st.session_state.user_role = user["role"]
                st.session_state.login_error = False
                st.success(f"✅ Signed in successfully!")
                st.balloons()
                st.rerun()
            else:
                st.session_state.login_error = "⚠️ Incorrect email or password."
                st.rerun()

    # Divider
    st.markdown('<div class="divider">or continue with</div>', unsafe_allow_html=True)

    # Google button
    st.button("Continue with Google", key="google_btn", use_container_width=True)

    # Footer
    st.markdown(
        "<div class='card-footer'>"
        "<p>Need access? <a href='#'>Contact your admin</a> | v2.4.1</p>"
        "</div>"
        "</div></div>",
        unsafe_allow_html=True,
    )

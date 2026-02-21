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

# ── Custom CSS (from premium template) ──────────────────────────────────────────
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
  background-color: var(--cream) !important;
  margin: 0 !important;
  padding: 0 !important;
}

#MainMenu, footer, header { visibility: hidden; }

.block-container {
  padding: 0 !important;
  max-width: 100% !important;
}

/* ── LOGIN WRAPPER ── */
.login-container {
  display: flex;
  min-height: 100vh;
  width: 100%;
}

/* ── LEFT PANEL ── */
.left-panel {
  width: 48%;
  background: linear-gradient(160deg, #1A1209 0%, #2E1F08 40%, #3D2A10 100%);
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 56px 60px;
  position: relative;
  overflow: hidden;
}

.left-panel::before {
  content: '';
  position: absolute;
  top: -120px; right: -120px;
  width: 420px; height: 420px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(201,169,110,0.18) 0%, transparent 70%);
  animation: float 15s ease-in-out infinite;
}

.left-panel::after {
  content: '';
  position: absolute;
  bottom: -80px; left: -80px;
  width: 320px; height: 320px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(201,169,110,0.12) 0%, transparent 70%);
  animation: float-reverse 20s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(15px); }
}

@keyframes float-reverse {
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-15px); }
}

.brand {
  display: flex;
  align-items: center;
  gap: 14px;
  position: relative;
  z-index: 1;
  animation: slideInLeft 0.8s ease-out;
}

@keyframes slideInLeft {
  from { opacity: 0; transform: translateX(-30px); }
  to { opacity: 1; transform: translateX(0); }
}

.brand-text h1 {
  font-family: 'Cormorant Garamond', serif;
  font-size: 22px;
  font-weight: 700;
  color: #E8D5B0;
  letter-spacing: 0.04em;
  line-height: 1.2;
  margin: 0;
}

.brand-text p {
  font-size: 10px;
  font-weight: 400;
  color: rgba(201,169,110,0.65);
  letter-spacing: 0.18em;
  text-transform: uppercase;
  margin: 2px 0 0 0;
}

.hero-content {
  position: relative;
  z-index: 1;
  animation: fadeInUp 0.8s ease-out 0.2s both;
}

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

.hero-eyebrow {
  font-size: 11px;
  font-weight: 500;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  color: var(--gold);
  margin-bottom: 18px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.hero-eyebrow::before {
  content: '';
  display: block;
  width: 28px;
  height: 1px;
  background: var(--gold);
}

.hero-content h2 {
  font-family: 'Cormorant Garamond', serif;
  font-size: 48px;
  font-weight: 600;
  color: var(--white);
  line-height: 1.15;
  margin: 0 0 20px 0;
}

.hero-content h2 span {
  color: var(--gold);
}

.hero-content p {
  font-size: 14px;
  font-weight: 300;
  color: rgba(255,255,255,0.55);
  line-height: 1.75;
  max-width: 340px;
  margin: 0;
}

.stats {
  display: flex;
  gap: 40px;
  margin-top: 44px;
  position: relative;
  z-index: 1;
}

.stat-item {
  text-align: left;
}

.stat-item .num {
  font-family: 'Cormorant Garamond', serif;
  font-size: 32px;
  font-weight: 700;
  color: var(--gold);
  line-height: 1;
  margin: 0;
}

.stat-item .label {
  font-size: 11px;
  color: rgba(255,255,255,0.45);
  letter-spacing: 0.1em;
  margin: 4px 0 0 0;
}

.stat-divider {
  width: 1px;
  background: rgba(201,169,110,0.25);
  align-self: stretch;
}

.left-footer {
  font-size: 11px;
  color: rgba(255,255,255,0.25);
  position: relative;
  z-index: 1;
  margin: 0;
}

/* ── RIGHT PANEL ── */
.right-panel {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48px 60px;
  background: var(--cream);
  position: relative;
}

.login-box {
  width: 100%;
  max-width: 400px;
}

.login-header {
  margin-bottom: 36px;
  animation: fadeIn 0.8s ease-out;
  text-align: center;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.login-header .welcome {
  font-size: 11px;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: var(--gold-dark);
  font-weight: 500;
  margin: 0;
}

.login-header h3 {
  font-family: 'Cormorant Garamond', serif;
  font-size: 36px;
  font-weight: 600;
  color: var(--dark);
  margin: 6px 0 0 0;
  line-height: 1.1;
}

.login-header p {
  font-size: 13px;
  color: var(--muted);
  margin: 8px 0 0 0;
  font-weight: 300;
}

.form-group {
  margin-bottom: 20px;
  position: relative;
}

.form-group label {
  display: block;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--muted);
  margin: 0 0 8px 0;
}

.role-selector {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

.role-btn {
  flex: 1;
  padding: 11px;
  border: 1.5px solid var(--border);
  border-radius: 8px;
  background: var(--white);
  cursor: pointer;
  font-size: 12px;
  font-family: 'Inter', sans-serif;
  font-weight: 500;
  color: var(--muted);
  letter-spacing: 0.04em;
  transition: all 0.2s;
  text-align: center;
}

.role-btn:hover {
  border-color: var(--gold-light);
  color: var(--gold-dark);
}

.role-btn.active {
  border-color: var(--gold);
  background: rgba(201,169,110,0.08);
  color: var(--gold-dark);
}

.alert {
  padding: 11px 14px;
  border-radius: 7px;
  font-size: 13px;
  margin-bottom: 20px;
  background: rgba(192,57,43,0.08);
  border: 1px solid rgba(192,57,43,0.25);
  color: var(--error);
  display: none;
}

.alert.show {
  display: block;
}

.dots-deco {
  position: fixed;
  top: 40px;
  right: 40px;
  opacity: 0.18;
  pointer-events: none;
  z-index: 1;
}

.divider {
  display: flex;
  align-items: center;
  gap: 14px;
  margin: 28px 0;
  font-size: 11px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--muted);
}

.divider::before,
.divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: var(--border);
}

.login-footer {
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px solid var(--border);
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  color: var(--muted);
}

.login-footer p {
  margin: 0;
}

.login-footer a {
  color: var(--gold-dark);
  text-decoration: none;
  font-weight: 500;
}

.login-footer a:hover {
  color: var(--gold);
}

/* ── STREAMLIT COMPONENT OVERRIDES ── */
[data-testid="stForm"] {
  background: transparent !important;
  border: none !important;
  padding: 0 !important;
}

[data-testid="stTextInput"] input,
[data-testid="stTextInput"] input[type="password"] {
  border: 1.5px solid var(--border) !important;
  border-radius: 8px !important;
  background: var(--white) !important;
  font-family: 'Inter', sans-serif !important;
  font-size: 14px !important;
  color: var(--dark) !important;
  padding: 13px 14px !important;
  transition: all 0.2s !important;
}

[data-testid="stTextInput"] input::placeholder {
  color: #BFB8AE !important;
}

[data-testid="stTextInput"] input:focus {
  border-color: var(--gold) !important;
  box-shadow: 0 0 0 3px rgba(201,169,110,0.15) !important;
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
  border-radius: 8px !important;
  padding: 14px !important;
  font-size: 13px !important;
  font-weight: 600 !important;
  letter-spacing: 0.15em !important;
  text-transform: uppercase !important;
  font-family: 'Inter', sans-serif !important;
  box-shadow: 0 4px 20px rgba(160,120,64,0.35) !important;
  transition: all 0.2s !important;
  cursor: pointer !important;
}

[data-testid="stForm"] button[type="submit"]:hover,
[data-testid="stFormSubmitButton"] button:hover {
  opacity: 0.92 !important;
  transform: translateY(-1px) !important;
  box-shadow: 0 6px 24px rgba(160,120,64,0.45) !important;
}

[data-testid="stCheckbox"] label {
  font-size: 13px !important;
  color: var(--muted) !important;
  font-family: 'Inter', sans-serif !important;
}

[data-testid="stButton"] button {
  border: 1.5px solid var(--border) !important;
  background: var(--white) !important;
  color: var(--dark) !important;
  padding: 12px 14px !important;
  font-size: 13px !important;
  font-weight: 500 !important;
  transition: all 0.2s !important;
  border-radius: 8px !important;
  font-family: 'Inter', sans-serif !important;
}

[data-testid="stButton"] button:hover {
  border-color: var(--gold-light) !important;
  background: rgba(201,169,110,0.05) !important;
}

[data-testid="stButton"] button:active {
  transform: translateY(1px) !important;
}

hr {
  border-color: var(--border) !important;
}

[data-testid="stAlert"] {
  border-radius: 8px !important;
  font-family: 'Inter', sans-serif !important;
}

@media (max-width: 900px) {
  .left-panel { width: 100%; min-height: 280px; padding: 36px 32px; }
  .hero-content h2 { font-size: 34px; }
  .right-panel { padding: 36px 28px; }
  .stats { gap: 24px; margin-top: 28px; }
  .login-box { padding: 0 16px; }
}
</style>
""", unsafe_allow_html=True)

# ── Session state ──────────────────────────────────────────────────────────────
if "login_error" not in st.session_state:
    st.session_state.login_error = False
if "login_role" not in st.session_state:
    st.session_state.login_role = "admin"

# ── Left panel HTML ────────────────────────────────────────────────────────────
LEFT_PANEL = """
<div class="left-panel">
  <div class="brand">
    <div class="brand-text">
      <h1>The Dental Bond</h1>
      <p>Implant &amp; Micro-Dentistry</p>
    </div>
  </div>

  <div class="hero-content">
    <div class="hero-eyebrow">Schedule Management</div>
    <h2>Your clinic,<br/>perfectly <span>organised</span></h2>
    <p>Streamline appointments, manage your team's calendar, and deliver seamless patient care — all in one place.</p>

    <div class="stats">
      <div class="stat-item">
        <div class="num">∞</div>
        <div class="label">Appointments</div>
      </div>
      <div class="stat-divider"></div>
      <div class="stat-item">
        <div class="num">24/7</div>
        <div class="label">Availability</div>
      </div>
      <div class="stat-divider"></div>
      <div class="stat-item">
        <div class="num">100%</div>
        <div class="label">Secure</div>
      </div>
    </div>
  </div>

  <p class="left-footer">© 2026 The Dental Bond. All rights reserved.</p>
</div>
"""

# ── Main layout ────────────────────────────────────────────────────────────────
def render() -> None:
    col_left, col_right = st.columns([1, 1.1], gap="small")

    with col_left:
        st.markdown(LEFT_PANEL, unsafe_allow_html=True)

    with col_right:
        # Decorative dots
        st.markdown("""
            <svg class="dots-deco" width="100" height="100" viewBox="0 0 100 100">
                <circle cx="10" cy="10" r="3" fill="#C9A96E"/><circle cx="30" cy="10" r="3" fill="#C9A96E"/>
                <circle cx="50" cy="10" r="3" fill="#C9A96E"/><circle cx="70" cy="10" r="3" fill="#C9A96E"/>
                <circle cx="10" cy="30" r="3" fill="#C9A96E"/><circle cx="30" cy="30" r="3" fill="#C9A96E"/>
                <circle cx="50" cy="30" r="3" fill="#C9A96E"/><circle cx="70" cy="30" r="3" fill="#C9A96E"/>
                <circle cx="10" cy="50" r="3" fill="#C9A96E"/><circle cx="30" cy="50" r="3" fill="#C9A96E"/>
                <circle cx="50" cy="50" r="3" fill="#C9A96E"/><circle cx="70" cy="50" r="3" fill="#C9A96E"/>
                <circle cx="10" cy="70" r="3" fill="#C9A96E"/><circle cx="30" cy="70" r="3" fill="#C9A96E"/>
                <circle cx="50" cy="70" r="3" fill="#C9A96E"/><circle cx="70" cy="70" r="3" fill="#C9A96E"/>
            </svg>
        """, unsafe_allow_html=True)

        st.markdown("""
            <div class="login-header">
                <div class="welcome">Welcome Back</div>
                <h3>Sign In</h3>
                <p>Access your dental practice management dashboard</p>
            </div>
        """, unsafe_allow_html=True)

        # Role selector
        st.markdown('<label style="display:block;font-size:11px;font-weight:600;letter-spacing:.12em;text-transform:uppercase;color:#6B6B6B;margin-bottom:8px;">Sign in as</label>', unsafe_allow_html=True)

        role_col1, role_col2, role_col3 = st.columns(3, gap="small")
        with role_col1:
            if st.button("Doctor", key="role_doctor", use_container_width=True):
                st.session_state.login_role = "admin"
        with role_col2:
            if st.button("Receptionist", key="role_receptionist", use_container_width=True):
                st.session_state.login_role = "frontdesk"
        with role_col3:
            if st.button("Admin", key="role_admin", use_container_width=True):
                st.session_state.login_role = "assistant"

        # Error alert
        error_placeholder = st.empty()
        if st.session_state.login_error:
            with error_placeholder.container():
                st.markdown(f'<div class="alert show">{st.session_state.login_error}</div>', unsafe_allow_html=True)

        # Form
        st.markdown('<div class="form-group"><label>Email Address</label></div>', unsafe_allow_html=True)
        email = st.text_input("", key="login_email", placeholder="you@thedentalbond.com", label_visibility="collapsed")

        st.markdown('<div class="form-group"><label>Password</label></div>', unsafe_allow_html=True)
        password = st.text_input("", key="login_password", placeholder="Enter your password", type="password", label_visibility="collapsed")

        # Remember me and Forgot password
        col_chk, col_link = st.columns([1, 1])
        with col_chk:
            remember = st.checkbox("Remember me", key="remember_me")
        with col_link:
            st.markdown(
                "<div style='text-align:right;padding-top:6px;'>"
                "<a href='#' style='font-size:13px;color:#A07840;text-decoration:none;font-weight:500;'>"
                "Forgot password?</a></div>",
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
                    st.session_state.login_error = "⚠️ Incorrect email or password. Please try again."
                    st.rerun()

        # Divider
        st.markdown('<div class="divider">or continue with</div>', unsafe_allow_html=True)

        # Google button
        col_google = st.columns([1, 0.05])[0]
        with col_google:
            st.button("Continue with Google", key="google_btn", use_container_width=True)

        # Footer
        st.markdown(
            "<div class='login-footer'>"
            "<p>Need access? <a href='#'>Contact your admin</a></p>"
            "<p style='font-size:11px;color:#BFB8AE;margin:0;'>v2.4.1</p>"
            "</div>",
            unsafe_allow_html=True,
        )

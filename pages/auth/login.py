# pages/auth/login.py
"""Premium split-panel login page for authentication."""

import streamlit as st
from data.auth_repo import authenticate

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="The Dental Bond – Schedule Management",
    page_icon="🦷",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;600;700&family=Inter:wght@300;400;500;600&display=swap');

/* ── Global resets ── */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: #FAF7F2 !important;
}

/* Hide Streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }
.block-container {
    padding: 0 !important;
    max-width: 100% !important;
}

/* ── Outer wrapper ── */
.page-wrapper {
    display: flex;
    min-height: 100vh;
    width: 100%;
}

/* ── Left panel ── */
.left-panel {
    width: 45%;
    min-height: 100vh;
    background: linear-gradient(160deg, #1A1209 0%, #2E1F08 40%, #3D2A10 100%);
    padding: 56px 52px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    position: relative;
    overflow: hidden;
    box-sizing: border-box;
}

.left-panel::before {
    content: '';
    position: absolute;
    top: -120px; right: -120px;
    width: 380px; height: 380px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(201,169,110,0.18) 0%, transparent 70%);
    pointer-events: none;
    animation: float 15s ease-in-out infinite;
}

.left-panel::after {
    content: '';
    position: absolute;
    bottom: -80px; left: -80px;
    width: 300px; height: 300px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(201,169,110,0.12) 0%, transparent 70%);
    pointer-events: none;
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
    align-items: flex-start;
    gap: 0;
    position: relative;
    z-index: 1;
    animation: slideInLeft 0.8s ease-out;
}

@keyframes slideInLeft {
    from { opacity: 0; transform: translateX(-30px); }
    to { opacity: 1; transform: translateX(0); }
}


.brand-name {
    font-family: 'Cormorant Garamond', serif;
    font-size: 20px;
    font-weight: 700;
    color: #E8D5B0;
    letter-spacing: 0.04em;
    line-height: 1.2;
    margin: 0;
    text-shadow: 0 2px 8px rgba(0,0,0,0.3);
}

.brand-sub {
    font-size: 9px;
    color: rgba(201,169,110,0.6);
    letter-spacing: 0.2em;
    text-transform: uppercase;
    margin: 2px 0 0 0;
}

.hero {
    position: relative;
    z-index: 1;
    animation: fadeInUp 0.8s ease-out 0.2s both;
}

@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}

.hero-eyebrow {
    font-size: 10px;
    font-weight: 500;
    letter-spacing: 0.22em;
    text-transform: uppercase;
    color: #C9A96E;
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    gap: 10px;
}

.hero-eyebrow::before {
    content: '';
    display: inline-block;
    width: 24px; height: 1px;
    background: #C9A96E;
}

.hero-title {
    font-family: 'Cormorant Garamond', serif;
    font-size: 44px;
    font-weight: 600;
    color: #FFFFFF;
    line-height: 1.15;
    margin: 0 0 18px 0;
}

.hero-title span { color: #C9A96E; }

.hero-desc {
    font-size: 13px;
    font-weight: 300;
    color: rgba(255,255,255,0.5);
    line-height: 1.75;
    max-width: 320px;
    margin: 0;
}

.stats {
    display: flex;
    gap: 32px;
    margin-top: 40px;
    position: relative;
    z-index: 1;
}

.stat-num {
    font-family: 'Cormorant Garamond', serif;
    font-size: 28px;
    font-weight: 700;
    color: #C9A96E;
    margin: 0;
}

.stat-label {
    font-size: 10px;
    color: rgba(255,255,255,0.4);
    letter-spacing: 0.1em;
    margin: 2px 0 0 0;
}

.stat-divider {
    width: 1px;
    background: rgba(201,169,110,0.25);
    align-self: stretch;
}

.left-footer {
    font-size: 11px;
    color: rgba(255,255,255,0.22);
    position: relative;
    z-index: 1;
}

/* ── Right panel ── */
.right-panel {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 48px 56px;
    background: #FAF7F2;
    box-sizing: border-box;
}

/* ── Streamlit widget overrides ── */
div[data-testid="stForm"] {
    background: transparent !important;
    border: none !important;
    padding: 0 !important;
}

/* Inputs */
div[data-testid="stTextInput"] input,
div[data-testid="stTextInput"] input[type="password"] {
    border: 1.5px solid #E2D9CA !important;
    border-radius: 10px !important;
    background: #FFFFFF !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 14px !important;
    color: #1A1A1A !important;
    padding: 14px 16px !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    font-weight: 500;
}

div[data-testid="stTextInput"] input::placeholder {
    color: #B8A89A !important;
    font-weight: 400;
}

div[data-testid="stTextInput"] input:focus {
    border-color: #C9A96E !important;
    box-shadow: 0 0 0 4px rgba(201,169,110,0.12), 0 8px 24px rgba(201,169,110,0.18) !important;
    background: #FEFDFB !important;
}

div[data-testid="stTextInput"] input:hover:not(:focus) {
    border-color: #E8D5B0 !important;
    box-shadow: 0 4px 12px rgba(201,169,110,0.08) !important;
}

div[data-testid="stTextInput"] label {
    font-size: 12px !important;
    font-weight: 700 !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    color: #6B6B6B !important;
    font-family: 'Inter', sans-serif !important;
}

/* Select box (role) */
div[data-testid="stSelectbox"] > label {
    font-size: 12px !important;
    font-weight: 700 !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    color: #6B6B6B !important;
}

div[data-testid="stSelectbox"] > div > div {
    border: 1.5px solid #E2D9CA !important;
    border-radius: 10px !important;
    background: #FFFFFF !important;
    font-family: 'Inter', sans-serif !important;
    transition: all 0.3s !important;
}

div[data-testid="stSelectbox"] > div > div:hover {
    border-color: #E8D5B0 !important;
}

div[data-testid="stSelectbox"] > div > div:focus-within {
    border-color: #C9A96E !important;
    box-shadow: 0 0 0 4px rgba(201,169,110,0.12) !important;
}

/* Submit button */
div[data-testid="stForm"] button[type="submit"],
div[data-testid="stFormSubmitButton"] button {
    width: 100% !important;
    background: linear-gradient(135deg, #A07840 0%, #C9A96E 50%, #E8D5B0 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 15px 24px !important;
    font-size: 13px !important;
    font-weight: 700 !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
    font-family: 'Inter', sans-serif !important;
    box-shadow: 0 8px 24px rgba(160,120,64,0.3) !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    cursor: pointer !important;
    position: relative;
    overflow: hidden;
}

div[data-testid="stForm"] button[type="submit"]::before,
div[data-testid="stFormSubmitButton"] button::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: rgba(255,255,255,0.2);
    transition: left 0.3s;
    z-index: -1;
}

div[data-testid="stForm"] button[type="submit"]:hover,
div[data-testid="stFormSubmitButton"] button:hover {
    opacity: 0.95 !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 12px 32px rgba(160,120,64,0.4) !important;
}

div[data-testid="stForm"] button[type="submit"]:hover::before,
div[data-testid="stFormSubmitButton"] button:hover::before {
    left: 100%;
}

div[data-testid="stForm"] button[type="submit"]:active,
div[data-testid="stFormSubmitButton"] button:active {
    transform: translateY(0) !important;
    box-shadow: 0 6px 16px rgba(160,120,64,0.3) !important;
}

/* Checkbox */
div[data-testid="stCheckbox"] label {
    font-size: 13px !important;
    color: #6B6B6B !important;
    font-family: 'Inter', sans-serif !important;
}

div[data-testid="stCheckbox"] span[data-testid="stWidgetLabel"] {
    color: #6B6B6B !important;
}

/* Divider */
hr {
    border-color: #E2D9CA !important;
    margin: 24px 0 !important;
}

/* Alert / error */
div[data-testid="stAlert"] {
    border-radius: 10px !important;
    font-family: 'Inter', sans-serif !important;
    background: linear-gradient(135deg, rgba(192,57,43,0.08) 0%, rgba(192,57,43,0.05) 100%) !important;
    border: 1.5px solid rgba(192,57,43,0.2) !important;
}

/* Success box */
.stSuccess {
    background: rgba(39,174,96,0.08) !important;
    border: 1.5px solid rgba(39,174,96,0.2) !important;
    border-radius: 10px !important;
}

/* Caption */
.caption-link {
    font-size: 12px;
    color: #6B6B6B;
    text-align: center;
    margin-top: 20px;
}

.caption-link a {
    color: #A07840;
    text-decoration: none;
    font-weight: 500;
    transition: color 0.2s;
}

.caption-link a:hover {
    color: #C9A96E;
}

/* Google button */
.google-btn {
    width: 100% !important;
    padding: 14px 20px !important;
    border: 1.5px solid #E2D9CA !important;
    border-radius: 10px !important;
    background: #FFFFFF !important;
    cursor: pointer;
    font-size: 13px;
    font-family: 'Inter', sans-serif;
    font-weight: 600;
    color: #1A1A1A;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 12px;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    margin-bottom: 0 !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}

.google-btn:hover {
    border-color: #C9A96E !important;
    box-shadow: 0 8px 20px rgba(201,169,110,0.15);
    transform: translateY(-2px);
}

.google-btn:active {
    transform: translateY(0);
}

@media (max-width: 900px) {
    .left-panel {
        width: 100%;
        min-height: 200px;
        padding: 36px 32px;
    }
    .hero-title { font-size: 32px; }
    .right-panel { padding: 36px 28px; }
}
</style>
""", unsafe_allow_html=True)

# ── Session state ──────────────────────────────────────────────────────────────
if "login_error" not in st.session_state:
    st.session_state.login_error = False
if "login_role" not in st.session_state:
    st.session_state.login_role = "assistant"

# ── Left panel HTML ────────────────────────────────────────────────────────────
LEFT_PANEL = """
<div class="left-panel">
  <div class="brand">
    <div>
      <p class="brand-name">The Dental Bond</p>
      <p class="brand-sub">Implant &amp; Micro-Dentistry</p>
    </div>
  </div>

  <div class="hero">
    <div class="hero-eyebrow">Schedule Management</div>
    <h2 class="hero-title">Your clinic,<br/>perfectly <span>organised</span></h2>
    <p class="hero-desc">Streamline appointments, manage your team's calendar, and deliver seamless patient care — all in one place.</p>
    <div class="stats">
      <div>
        <p class="stat-num">∞</p>
        <p class="stat-label">Appointments</p>
      </div>
      <div class="stat-divider"></div>
      <div>
        <p class="stat-num">24/7</p>
        <p class="stat-label">Availability</p>
      </div>
      <div class="stat-divider"></div>
      <div>
        <p class="stat-num">100%</p>
        <p class="stat-label">Secure</p>
      </div>
    </div>
  </div>

  <p class="left-footer">© 2026 The Dental Bond. All rights reserved.</p>
</div>
"""

# ── Layout: two columns ────────────────────────────────────────────────────────
def render() -> None:
    col_left, col_right = st.columns([9, 11], gap="small")

    with col_left:
        st.markdown(LEFT_PANEL, unsafe_allow_html=True)

    with col_right:
        st.markdown("<div style='height:32px'></div>", unsafe_allow_html=True)

        # Role selector
        role = st.selectbox(
            "Sign in as",
            ["Admin", "Frontdesk", "Assistant"],
            index=2,  # Default to Assistant
            key="login_role_select"
        )
        st.session_state.login_role = role.lower()

        # Login form
        with st.form("login_form", clear_on_submit=False):
            email = st.text_input(
                "Email Address",
                placeholder="you@thedentalbond.com",
                key="login_email"
            )
            password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter your password",
                key="login_password"
            )

            col_chk, col_link = st.columns([1, 1])
            with col_chk:
                remember = st.checkbox("Remember me", key="remember_me")
            with col_link:
                st.markdown(
                    "<div style='text-align:right;padding-top:6px;'>"
                    "<a href='#' style='font-size:13px;color:#A07840;text-decoration:none;font-weight:500;transition:color 0.2s;' "
                    "onmouseover=\"this.style.color='#C9A96E'\" onmouseout=\"this.style.color='#A07840'\">"
                    "Forgot password?</a></div>",
                    unsafe_allow_html=True,
                )

            submitted = st.form_submit_button("Sign In", use_container_width=True)

        # Handle login logic
        if submitted:
            if email and password:
                user = authenticate(email, password)
                if user:
                    st.session_state.current_user = user["username"]
                    st.session_state.user_role = user["role"]
                    st.session_state.login_error = False
                    st.success(f"✅ Welcome, {user['username']}! 🎉")
                    st.balloons()
                    st.rerun()
                else:
                    st.session_state.login_error = True
            else:
                st.session_state.login_error = True

        if st.session_state.login_error:
            st.error("⚠️ Incorrect email or password. Please try again.")

        # Divider + Google SSO
        st.markdown("<hr style='margin:24px 0;'>", unsafe_allow_html=True)
        st.markdown(
            "<p style='text-align:center;font-size:11px;letter-spacing:0.1em;"
            "text-transform:uppercase;color:#8B8B8B;margin-bottom:16px;'>"
            "or continue with</p>",
            unsafe_allow_html=True,
        )

        st.button(
            "🔵 Continue with Google",
            use_container_width=True,
            key="google_btn",
            help="Google sign-in not yet configured"
        )

        # Footer
        st.markdown(
            "<div style='margin-top:32px;padding-top:20px;border-top:1.5px solid #E2D9CA;"
            "display:flex;justify-content:space-between;align-items:center;'>"
            "<span style='font-size:12px;color:#6B6B6B;font-family:Inter,sans-serif;'>"
            "Need access? <a href='#' style='color:#A07840;text-decoration:none;font-weight:500;transition:color 0.2s;' "
            "onmouseover=\"this.style.color='#C9A96E'\" onmouseout=\"this.style.color='#A07840'\">"
            "Contact your admin</a>"
            "</span>"
            "<span style='font-size:11px;color:#BFB8AE;font-family:Inter,sans-serif;'>v2.4.1</span>"
            "</div>",
            unsafe_allow_html=True,
        )

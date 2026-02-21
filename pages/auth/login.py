# pages/auth/login.py
"""Premium split-panel login page for authentication."""

import streamlit as st
from data.auth_repo import authenticate

st.set_page_config(
    page_title="The Dental Bond – Sign In",
    page_icon="🦷",
    layout="wide",
    initial_sidebar_state="collapsed",
)

def render() -> None:
    """Render the ultra-premium login page."""

    # Initialize session state
    if "login_role" not in st.session_state:
        st.session_state.login_role = "assistant"
    if "login_error" not in st.session_state:
        st.session_state.login_error = ""
    if "show_password" not in st.session_state:
        st.session_state.show_password = False

    # Ultra-premium CSS styling
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;600;700&family=Inter:wght@300;400;500;600;700&display=swap');

        * { margin: 0; padding: 0; box-sizing: border-box; }

        :root {
          --gold: #C9A96E;
          --gold-light: #E8D5B0;
          --gold-dark: #A07840;
          --gold-darker: #8B6340;
          --cream: #FAF7F2;
          --dark: #1A1A1A;
          --muted: #6B6B6B;
          --light-muted: #8B8B8B;
          --border: #E2D9CA;
          --white: #FFFFFF;
          --error: #C0392B;
          --light-bg: #FEFDFB;
        }

        html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
          margin: 0 !important;
          padding: 0 !important;
          background: var(--cream) !important;
          height: 100% !important;
          font-family: 'Inter', sans-serif;
        }

        [data-testid="stMainBlockContainer"] {
          padding: 0 !important;
          max-width: 100% !important;
        }

        [data-testid="stVerticalBlock"] {
          gap: 0 !important;
        }

        /* ──────────────── LEFT PANEL ──────────────── */
        .left-panel {
          width: 48%;
          background: linear-gradient(160deg, #1A1209 0%, #2E1F08 40%, #3D2A10 100%);
          display: flex;
          flex-direction: column;
          justify-content: flex-start;
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
          background: radial-gradient(circle, rgba(201,169,110,0.2) 0%, transparent 70%);
          animation: float 15s ease-in-out infinite;
        }

        .left-panel::after {
          content: '';
          position: absolute;
          bottom: -80px; left: -80px;
          width: 320px; height: 320px;
          border-radius: 50%;
          background: radial-gradient(circle, rgba(201,169,110,0.15) 0%, transparent 70%);
          animation: float-reverse 20s ease-in-out infinite;
        }

        @keyframes float {
          0%, 100% { transform: translateY(0px); }
          50% { transform: translateY(20px); }
        }

        @keyframes float-reverse {
          0%, 100% { transform: translateY(0px); }
          50% { transform: translateY(-20px); }
        }

        .brand {
          display: flex;
          align-items: center;
          gap: 16px;
          position: relative;
          z-index: 1;
          animation: slideInLeft 0.8s ease-out;
        }

        @keyframes slideInLeft {
          from { opacity: 0; transform: translateX(-30px); }
          to { opacity: 1; transform: translateX(0); }
        }

        .brand-icon {
          width: 56px;
          height: 56px;
          flex-shrink: 0;
          filter: drop-shadow(0 8px 16px rgba(201,169,110,0.2));
          animation: rotateIn 1s ease-out;
        }

        @keyframes rotateIn {
          from { opacity: 0; transform: rotate(-10deg) scale(0.8); }
          to { opacity: 1; transform: rotate(0) scale(1); }
        }

        .brand-text h1 {
          font-family: 'Cormorant Garamond', serif;
          font-size: 24px;
          font-weight: 700;
          color: var(--gold-light);
          letter-spacing: 0.06em;
          line-height: 1.2;
          margin: 0;
          text-shadow: 0 2px 8px rgba(0,0,0,0.3);
        }

        .brand-text p {
          font-size: 10px;
          font-weight: 600;
          color: rgba(201,169,110,0.7);
          letter-spacing: 0.2em;
          text-transform: uppercase;
          margin: 4px 0 0 0;
          word-spacing: 2px;
        }

        /* ──────────────── RIGHT PANEL ──────────────── */
        .right-panel {
          flex: 1;
          background: linear-gradient(135deg, var(--cream) 0%, var(--light-bg) 100%);
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 48px 60px;
          position: relative;
          overflow: hidden;
        }

        .right-panel::before {
          content: '';
          position: absolute;
          width: 200px;
          height: 200px;
          background: radial-gradient(circle, rgba(201,169,110,0.08) 0%, transparent 70%);
          border-radius: 50%;
          top: -50px;
          right: -50px;
          z-index: 0;
        }

        .login-box {
          width: 100%;
          max-width: 420px;
          z-index: 2;
          position: relative;
        }

        .login-header {
          margin-bottom: 40px;
          animation: fadeInDown 0.8s ease-out;
        }

        @keyframes fadeInDown {
          from { opacity: 0; transform: translateY(-20px); }
          to { opacity: 1; transform: translateY(0); }
        }

        .login-header .welcome {
          font-size: 12px;
          letter-spacing: 0.3em;
          text-transform: uppercase;
          color: var(--gold);
          font-weight: 700;
          margin: 0;
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .login-header .welcome::before {
          content: '';
          width: 8px;
          height: 1px;
          background: var(--gold);
        }

        .login-header h3 {
          font-family: 'Cormorant Garamond', serif;
          font-size: 40px;
          font-weight: 700;
          color: var(--dark);
          margin: 12px 0 0 0;
          line-height: 1.1;
          letter-spacing: -0.02em;
        }

        .login-header p {
          font-size: 14px;
          color: var(--light-muted);
          margin: 10px 0 0 0;
          font-weight: 400;
          line-height: 1.6;
        }

        /* ──────────────── ROLE SELECTOR ──────────────── */
        .role-label {
          font-size: 12px;
          font-weight: 700;
          letter-spacing: 0.1em;
          text-transform: uppercase;
          color: var(--muted);
          margin-bottom: 12px;
          display: block;
        }

        .role-selector {
          display: flex;
          gap: 10px;
          margin-bottom: 28px;
          animation: fadeIn 0.8s ease-out 0.1s both;
        }

        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }

        /* ──────────────── FORM STYLING ──────────────── */
        .form-group {
          margin-bottom: 24px;
          animation: fadeIn 0.8s ease-out 0.2s both;
        }

        .form-group label {
          font-size: 12px;
          font-weight: 700;
          letter-spacing: 0.1em;
          text-transform: uppercase;
          color: var(--muted);
          margin-bottom: 10px;
          display: block;
        }

        /* Alert */
        .alert {
          padding: 14px 16px;
          border-radius: 10px;
          font-size: 13px;
          margin-bottom: 24px;
          background: linear-gradient(135deg, rgba(192,57,43,0.08) 0%, rgba(192,57,43,0.05) 100%);
          border: 1.5px solid rgba(192,57,43,0.2);
          color: var(--error);
          font-weight: 500;
          animation: slideInDown 0.5s ease-out;
        }

        @keyframes slideInDown {
          from { opacity: 0; transform: translateY(-10px); }
          to { opacity: 1; transform: translateY(0); }
        }

        /* ──────────────── INPUT STYLING ──────────────── */
        [data-testid="stTextInput"] input {
          border: 1.5px solid var(--border) !important;
          border-radius: 10px !important;
          padding: 14px 16px !important;
          font-size: 14px !important;
          font-family: 'Inter', sans-serif !important;
          background: var(--white) !important;
          transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
          color: var(--dark) !important;
          font-weight: 500;
        }

        [data-testid="stTextInput"] input::placeholder {
          color: #B8A89A !important;
          font-weight: 400;
        }

        [data-testid="stTextInput"] input:focus {
          border-color: var(--gold) !important;
          box-shadow: 0 0 0 4px rgba(201,169,110,0.12), 0 8px 24px rgba(201,169,110,0.18) !important;
          background: var(--light-bg) !important;
        }

        [data-testid="stTextInput"] input:hover:not(:focus) {
          border-color: var(--gold-light) !important;
          box-shadow: 0 4px 12px rgba(201,169,110,0.08) !important;
        }

        /* ──────────────── CHECKBOX & FORGET ──────────────── */
        .checkbox-forget {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin: 24px 0;
          animation: fadeIn 0.8s ease-out 0.3s both;
        }

        .remember-me {
          display: flex;
          align-items: center;
          gap: 10px;
          cursor: pointer;
          font-size: 13px;
          color: var(--muted);
          user-select: none;
        }

        .remember-me input[type="checkbox"] {
          appearance: none;
          width: 18px;
          height: 18px;
          border: 1.5px solid var(--border);
          border-radius: 6px;
          cursor: pointer;
          transition: all 0.2s;
          flex-shrink: 0;
          background: var(--white);
        }

        .remember-me input[type="checkbox"]:hover {
          border-color: var(--gold-light);
          box-shadow: 0 2px 8px rgba(201,169,110,0.1);
        }

        .remember-me input[type="checkbox"]:checked {
          background: linear-gradient(135deg, var(--gold-dark) 0%, var(--gold) 100%);
          border-color: var(--gold);
          box-shadow: 0 4px 12px rgba(201,169,110,0.3);
        }

        .forgot-link {
          font-size: 13px;
          color: var(--gold-dark);
          text-decoration: none;
          font-weight: 600;
          transition: all 0.2s;
          position: relative;
        }

        .forgot-link::after {
          content: '';
          position: absolute;
          bottom: -2px;
          left: 0;
          width: 0;
          height: 1px;
          background: var(--gold);
          transition: width 0.3s;
        }

        .forgot-link:hover {
          color: var(--gold);
        }

        .forgot-link:hover::after {
          width: 100%;
        }

        /* ──────────────── BUTTON STYLING ──────────────── */
        [data-testid="stButton"] button {
          background: linear-gradient(135deg, var(--gold-dark) 0%, var(--gold) 50%, var(--gold-light) 100%) !important;
          color: var(--white) !important;
          border: none !important;
          border-radius: 10px !important;
          font-weight: 700 !important;
          letter-spacing: 0.12em !important;
          text-transform: uppercase !important;
          box-shadow: 0 8px 24px rgba(160,120,64,0.3) !important;
          padding: 15px 24px !important;
          font-size: 13px !important;
          transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
          width: 100% !important;
          height: auto !important;
          position: relative;
          overflow: hidden;
        }

        [data-testid="stButton"] button::before {
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

        [data-testid="stButton"] button:hover {
          opacity: 0.95 !important;
          transform: translateY(-2px) !important;
          box-shadow: 0 12px 32px rgba(160,120,64,0.4) !important;
        }

        [data-testid="stButton"] button:hover::before {
          left: 100%;
        }

        [data-testid="stButton"] button:active {
          transform: translateY(0) !important;
          box-shadow: 0 6px 16px rgba(160,120,64,0.3) !important;
        }

        /* Role buttons specific */
        [data-testid="stButton"] button[kind="primary"] {
          margin-bottom: 0 !important;
        }

        /* ──────────────── DIVIDER ──────────────────── */
        .divider {
          display: flex;
          align-items: center;
          gap: 16px;
          margin: 32px 0;
          font-size: 12px;
          letter-spacing: 0.1em;
          text-transform: uppercase;
          color: var(--light-muted);
          font-weight: 600;
          animation: fadeIn 0.8s ease-out 0.4s both;
        }

        .divider::before,
        .divider::after {
          content: '';
          flex: 1;
          height: 1px;
          background: linear-gradient(90deg, var(--border) 0%, transparent 100%);
        }

        .divider::after {
          background: linear-gradient(90deg, transparent 0%, var(--border) 100%);
        }

        /* ──────────────── GOOGLE BUTTON ──────────────── */
        .google-btn {
          width: 100%;
          padding: 14px 20px !important;
          border: 1.5px solid var(--border) !important;
          border-radius: 10px !important;
          background: var(--white) !important;
          cursor: pointer;
          font-size: 13px;
          font-family: 'Inter', sans-serif;
          font-weight: 600;
          color: var(--dark);
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 12px;
          transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
          margin-bottom: 32px;
          box-shadow: 0 2px 8px rgba(0,0,0,0.04);
          animation: fadeIn 0.8s ease-out 0.5s both;
        }

        .google-btn:hover {
          border-color: var(--gold) !important;
          box-shadow: 0 8px 20px rgba(201,169,110,0.15);
          transform: translateY(-2px);
        }

        .google-btn:active {
          transform: translateY(0);
        }

        /* ──────────────── FOOTER ──────────────────── */
        .login-footer {
          margin-top: 32px;
          padding-top: 24px;
          border-top: 1.5px solid var(--border);
          display: flex;
          justify-content: space-between;
          align-items: center;
          font-size: 12px;
          color: var(--light-muted);
          animation: fadeIn 0.8s ease-out 0.6s both;
        }

        .login-footer p {
          margin: 0;
        }

        .login-footer a {
          color: var(--gold-dark);
          text-decoration: none;
          font-weight: 700;
          transition: all 0.2s;
        }

        .login-footer a:hover {
          color: var(--gold);
          text-decoration: underline;
        }

        /* ──────────────── DECORATIVE ELEMENTS ──────────────── */
        .dots-deco {
          position: absolute;
          top: 40px;
          right: 40px;
          opacity: 0.15;
          pointer-events: none;
          z-index: 1;
          animation: float 20s ease-in-out infinite;
        }

        /* ──────────────── RESPONSIVE ──────────────── */
        @media (max-width: 900px) {
          .left-panel { width: 100%; min-height: 200px; }
          .right-panel { padding: 36px 28px; }
          .login-header h3 { font-size: 32px; }
        }
        </style>
    """, unsafe_allow_html=True)

    # Main layout
    col_left, col_right = st.columns([1.2, 1], gap="large")

    # LEFT PANEL
    with col_left:
        st.markdown("""
            <div class="left-panel">
                <div class="brand">
                    <svg class="brand-icon" viewBox="0 0 52 52" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M26 4C18 4 12 10 12 18c0 4 1.5 8 3 12 1.5 4 3 8 3 12a2 2 0 0 0 4 0c0-3 1-6 2-8h2c1 2 2 5 2 8a2 2 0 0 0 4 0c0-4 1.5-8 3-12 1.5-4 3-8 3-12 0-8-6-14-14-14z" fill="url(#goldGrad)" opacity="0.95"/>
                        <path d="M20 16 L26 10 L32 16" stroke="#E8D5B0" stroke-width="1.2" stroke-linecap="round" fill="none" opacity="0.7"/>
                        <path d="M26 10 L26 30" stroke="#E8D5B0" stroke-width="1" stroke-linecap="round" fill="none" opacity="0.5"/>
                        <defs>
                            <linearGradient id="goldGrad" x1="12" y1="4" x2="40" y2="44" gradientUnits="userSpaceOnUse">
                                <stop offset="0%" stop-color="#E8D5B0"/>
                                <stop offset="100%" stop-color="#8B6340"/>
                            </linearGradient>
                        </defs>
                    </svg>
                    <div class="brand-text">
                        <h1>The Dental Bond</h1>
                        <p>Implant &amp; Micro-Dentistry</p>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

    # RIGHT PANEL
    with col_right:
        # Decorative dots
        st.markdown("""
            <svg class="dots-deco" width="120" height="120" viewBox="0 0 100 100">
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

        # Header
        st.markdown("""
            <div class="login-header">
                <div class="welcome">Welcome Back</div>
                <h3>Sign In</h3>
                <p>Access your dental practice management dashboard</p>
            </div>
        """, unsafe_allow_html=True)

        # Role selector
        st.markdown('<label class="role-label">Sign in as</label>', unsafe_allow_html=True)

        role_col1, role_col2, role_col3 = st.columns(3, gap="small")
        with role_col1:
            if st.button("Admin", key="role_admin", use_container_width=True):
                st.session_state.login_role = "admin"
        with role_col2:
            if st.button("Frontdesk", key="role_frontdesk", use_container_width=True):
                st.session_state.login_role = "frontdesk"
        with role_col3:
            if st.button("Assistant", key="role_assistant", use_container_width=True):
                st.session_state.login_role = "assistant"

        # Error alert
        if st.session_state.login_error:
            st.markdown(f'<div class="alert">{st.session_state.login_error}</div>', unsafe_allow_html=True)

        # Email input
        st.markdown('<div class="form-group"><label>Email Address</label></div>', unsafe_allow_html=True)
        email = st.text_input("", key="login_email", placeholder="you@thedentalbond.com", label_visibility="collapsed")

        # Password input
        st.markdown('<div class="form-group"><label>Password</label></div>', unsafe_allow_html=True)
        password = st.text_input(
            "",
            key="login_password",
            placeholder="Enter your password",
            type="password" if not st.session_state.show_password else "default",
            label_visibility="collapsed"
        )

        # Remember me & Forgot password
        st.markdown(f"""
            <div class="checkbox-forget">
                <label class="remember-me">
                    <input type="checkbox" id="rememberMe" />
                    Remember me
                </label>
                <a href="#" class="forgot-link">Forgot password?</a>
            </div>
            <script>
            const checkbox = document.getElementById('rememberMe');
            if (checkbox) {{
                checkbox.addEventListener('change', function() {{
                    if (this.checked) {{
                        this.style.background = 'linear-gradient(135deg, #A07840 0%, #C9A96E 100%)';
                    }}
                }});
            }}
            </script>
        """, unsafe_allow_html=True)

        # Sign in button
        if st.button("Sign In", key="btn_login", use_container_width=True):
            if not email or not password:
                st.session_state.login_error = "Please fill in all fields"
                st.rerun()
            else:
                user = authenticate(email, password)
                if user:
                    st.session_state.current_user = user["username"]
                    st.session_state.user_role = user["role"]
                    st.session_state.login_error = ""
                    st.success(f"Welcome, {user['username']}! 🎉")
                    st.balloons()
                    st.rerun()
                else:
                    st.session_state.login_error = "Incorrect email or password. Please try again."
                    st.rerun()

        # Divider
        st.markdown('<div class="divider">or continue with</div>', unsafe_allow_html=True)

        # Google button
        st.markdown("""
            <button class="google-btn" style="cursor: pointer;">
                <svg width="18" height="18" viewBox="0 0 18 18"><path d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844a4.14 4.14 0 0 1-1.796 2.716v2.259h2.908c1.702-1.567 2.684-3.875 2.684-6.615z" fill="#4285F4"/><path d="M9 18c2.43 0 4.467-.806 5.956-2.184l-2.908-2.259c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332A8.997 8.997 0 0 0 9 18z" fill="#34A853"/><path d="M3.964 10.706A5.41 5.41 0 0 1 3.682 9c0-.593.102-1.17.282-1.706V4.962H.957A8.996 8.996 0 0 0 0 9c0 1.452.348 2.827.957 4.038l3.007-2.332z" fill="#FBBC05"/><path d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0A8.997 8.997 0 0 0 .957 4.962L3.964 7.294C4.672 5.163 6.656 3.58 9 3.58z" fill="#EA4335"/></svg>
                Continue with Google
            </button>
        """, unsafe_allow_html=True)

        # Footer
        st.markdown("""
            <div class="login-footer">
                <p>Need access? <a href="#">Contact your admin</a></p>
                <p style="font-size:11px;color:#8B8B8B;">v2.4.1</p>
            </div>
        """, unsafe_allow_html=True)

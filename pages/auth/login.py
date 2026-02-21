# pages/auth/login.py
"""Premium split-panel login page for authentication."""

import streamlit as st
from data.auth_repo import authenticate

st.set_page_config(
    page_title="The Dental Bond – Sign In",
    page_icon="🦷",
    layout="wide",
)

def render() -> None:
    """Render the premium HTML login page."""

    # Initialize session state
    if "login_role" not in st.session_state:
        st.session_state.login_role = "assistant"
    if "login_error" not in st.session_state:
        st.session_state.login_error = ""

    # Premium HTML + CSS
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

        /* Force main background */
        [data-testid="stAppViewContainer"],
        [data-testid="stApp"],
        .main {
          background-color: var(--cream) !important;
        }

        body { background-color: var(--cream) !important; }

        .main-layout {
          display: flex;
          min-height: 100vh;
          width: 100vw;
          margin-left: calc(-50vw + 50%);
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
        }

        .left-panel::after {
          content: '';
          position: absolute;
          bottom: -80px; left: -80px;
          width: 320px; height: 320px;
          border-radius: 50%;
          background: radial-gradient(circle, rgba(201,169,110,0.12) 0%, transparent 70%);
        }

        .brand {
          display: flex;
          align-items: center;
          gap: 14px;
          position: relative;
          z-index: 1;
        }

        .brand-icon {
          width: 52px;
          height: 52px;
          flex-shrink: 0;
        }

        .brand-text h1 {
          font-family: 'Cormorant Garamond', serif;
          font-size: 22px;
          font-weight: 700;
          color: var(--gold-light);
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
          display: none;
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
          display: none;
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
          z-index: 2;
        }

        .login-header {
          margin-bottom: 36px;
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

        .form-group input {
          width: 100%;
          padding: 13px 14px;
          border: 1.5px solid var(--border);
          border-radius: 8px;
          background: var(--white);
          font-size: 14px;
          font-family: 'Inter', sans-serif;
          color: var(--dark);
          outline: none;
          transition: border-color 0.2s, box-shadow 0.2s;
        }

        .form-group input::placeholder {
          color: #BFB8AE;
        }

        .form-group input:focus {
          border-color: var(--gold);
          box-shadow: 0 0 0 3px rgba(201,169,110,0.15);
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
        }

        .btn-login {
          width: 100%;
          padding: 14px;
          background: linear-gradient(135deg, var(--gold-dark) 0%, var(--gold) 100%);
          color: var(--white);
          border: none;
          border-radius: 8px;
          font-size: 13px;
          font-weight: 600;
          letter-spacing: 0.15em;
          text-transform: uppercase;
          cursor: pointer;
          font-family: 'Inter', sans-serif;
          transition: opacity 0.2s, transform 0.15s, box-shadow 0.2s;
          box-shadow: 0 4px 20px rgba(160,120,64,0.35);
          margin-bottom: 28px;
        }

        .btn-login:hover {
          opacity: 0.92;
          transform: translateY(-1px);
          box-shadow: 0 6px 24px rgba(160,120,64,0.45);
        }

        .btn-login:active {
          transform: translateY(0);
        }

        .dots-deco {
          position: absolute;
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

        .login-footer a {
          color: var(--gold-dark);
          text-decoration: none;
          font-weight: 500;
        }

        .login-footer a:hover {
          color: var(--gold);
        }

        /* Override Streamlit button styling */
        [data-testid="stButton"] button {
          background: linear-gradient(135deg, var(--gold-dark) 0%, var(--gold) 100%) !important;
          color: var(--white) !important;
          border: none !important;
          border-radius: 8px !important;
          font-weight: 600 !important;
          letter-spacing: 0.15em !important;
          text-transform: uppercase !important;
          box-shadow: 0 4px 20px rgba(160,120,64,0.35) !important;
          padding: 14px !important;
          font-size: 13px !important;
          transition: opacity 0.2s, transform 0.15s, box-shadow 0.2s !important;
        }

        [data-testid="stButton"] button:hover {
          opacity: 0.92 !important;
          transform: translateY(-1px) !important;
          box-shadow: 0 6px 24px rgba(160,120,64,0.45) !important;
        }

        /* Role button override */
        [data-testid="stButton"] button.active {
          border-color: var(--gold) !important;
          background: rgba(201,169,110,0.08) !important;
          color: var(--gold-dark) !important;
        }

        @media (max-width: 900px) {
          .main-layout {
            flex-direction: column;
          }
          .left-panel {
            width: 100%;
            min-height: 280px;
          }
          .hero-content h2 {
            font-size: 34px;
          }
          .right-panel {
            padding: 36px 28px;
          }
        }
        </style>
    """, unsafe_allow_html=True)

    # Full page layout with pure HTML/CSS
    st.markdown("""
        <style>
        /* Override page margins */
        [data-testid="stAppViewContainer"] { padding: 0 !important; }
        [data-testid="stMain"] { margin-top: 0 !important; }
        .appViewContainer { padding: 0 !important; }
        </style>

        <div style="display: flex; height: 100vh; width: 100%; position: fixed; top: 0; left: 0;">
            <!-- LEFT PANEL -->
            <div class="left-panel">
                <div class="brand">
                    <svg class="brand-icon" viewBox="0 0 52 52" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M26 4C18 4 12 10 12 18c0 4 1.5 8 3 12 1.5 4 3 8 3 12a2 2 0 0 0 4 0c0-3 1-6 2-8h2c1 2 2 5 2 8a2 2 0 0 0 4 0c0-4 1.5-8 3-12 1.5-4 3-8 3-12 0-8-6-14-14-14z" fill="url(#goldGrad)" opacity="0.9"/>
                        <path d="M20 16 L26 10 L32 16" stroke="#E8D5B0" stroke-width="1.2" stroke-linecap="round" fill="none" opacity="0.6"/>
                        <path d="M26 10 L26 30" stroke="#E8D5B0" stroke-width="1" stroke-linecap="round" fill="none" opacity="0.4"/>
                        <defs>
                            <linearGradient id="goldGrad" x1="12" y1="4" x2="40" y2="44" gradientUnits="userSpaceOnUse">
                                <stop offset="0%" stop-color="#E8D5B0"/>
                                <stop offset="100%" stop-color="#A07840"/>
                            </linearGradient>
                        </defs>
                    </svg>
                    <div class="brand-text">
                        <h1>The Dental Bond</h1>
                        <p>Implant &amp; Micro-Dentistry</p>
                    </div>
                </div>
            </div>

            <!-- RIGHT PANEL -->
            <div class="right-panel">
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

                <div class="login-box">
                    <div class="login-header">
                        <div class="welcome">Welcome Back</div>
                        <h3>Sign In</h3>
                        <p>Access your dental practice management dashboard</p>
                    </div>

                    <label style="display:block;font-size:11px;font-weight:600;letter-spacing:.12em;text-transform:uppercase;color:#6B6B6B;margin-bottom:8px;">Sign in as</label>
                    <div id="roleSelector" style="display: flex; gap: 10px; margin-bottom: 20px;"></div>

                    <div id="errorAlert" style="display: none; padding: 11px 14px; border-radius: 7px; font-size: 13px; margin-bottom: 20px; background: rgba(192,57,43,0.08); border: 1px solid rgba(192,57,43,0.25); color: #C0392B;"></div>

                    <form id="loginForm" style="display: contents;">
                        <div class="form-group">
                            <label>Email Address</label>
                            <input type="email" id="emailInput" placeholder="you@thedentalbond.com" required />
                        </div>

                        <div class="form-group">
                            <label>Password</label>
                            <input type="password" id="passwordInput" placeholder="Enter your password" required />
                        </div>

                        <button type="submit" class="btn-login">Sign In</button>
                    </form>

                    <div class="divider">or continue with</div>
                    <button style="width:100%;padding:12px;border:1.5px solid #E2D9CA;border-radius:8px;background:#fff;cursor:pointer;font-size:13px;font-family:'Inter',sans-serif;font-weight:500;color:#1A1A1A;display:flex;align-items:center;justify-content:center;gap:10px;transition:all .2s;margin-bottom:28px;" onmouseover="this.style.borderColor='#C9A96E'" onmouseout="this.style.borderColor='#E2D9CA'">
                        <svg width="18" height="18" viewBox="0 0 18 18"><path d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844a4.14 4.14 0 0 1-1.796 2.716v2.259h2.908c1.702-1.567 2.684-3.875 2.684-6.615z" fill="#4285F4"/><path d="M9 18c2.43 0 4.467-.806 5.956-2.184l-2.908-2.259c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332A8.997 8.997 0 0 0 9 18z" fill="#34A853"/><path d="M3.964 10.706A5.41 5.41 0 0 1 3.682 9c0-.593.102-1.17.282-1.706V4.962H.957A8.996 8.996 0 0 0 0 9c0 1.452.348 2.827.957 4.038l3.007-2.332z" fill="#FBBC05"/><path d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0A8.997 8.997 0 0 0 .957 4.962L3.964 7.294C4.672 5.163 6.656 3.58 9 3.58z" fill="#EA4335"/></svg>
                        Continue with Google
                    </button>

                    <div class="login-footer">
                        <p>Need access? <a href="#">Contact your admin</a></p>
                        <p style="font-size:11px;color:#BFB8AE;">v2.4.1</p>
                    </div>
                </div>
            </div>
        </div>

        <script>
        // Role selector
        const roles = ['Admin', 'Frontdesk', 'Assistant'];
        const selector = document.getElementById('roleSelector');
        roles.forEach(role => {
            const btn = document.createElement('button');
            btn.textContent = role;
            btn.style.cssText = 'flex:1;padding:11px;border:1.5px solid #E2D9CA;border-radius:8px;background:#fff;cursor:pointer;font-size:12px;font-family:Inter,sans-serif;font-weight:500;color:#6B6B6B;letter-spacing:.04em;transition:all .2s;text-align:center;';
            if (role === 'Assistant') {
                btn.style.borderColor = '#C9A96E';
                btn.style.background = 'rgba(201,169,110,0.08)';
                btn.style.color = '#A07840';
            }
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                document.querySelectorAll('#roleSelector button').forEach(b => {
                    b.style.borderColor = '#E2D9CA';
                    b.style.background = '#fff';
                    b.style.color = '#6B6B6B';
                });
                btn.style.borderColor = '#C9A96E';
                btn.style.background = 'rgba(201,169,110,0.08)';
                btn.style.color = '#A07840';
            });
            selector.appendChild(btn);
        });

        // Form submission
        document.getElementById('loginForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const email = document.getElementById('emailInput').value;
            const password = document.getElementById('passwordInput').value;
            const errorAlert = document.getElementById('errorAlert');

            if (!email || !password) {
                errorAlert.textContent = 'Please fill in all fields';
                errorAlert.style.display = 'block';
                return;
            }

            // Trigger Streamlit action via button click simulation
            const btn = document.querySelector('.btn-login');
            btn.textContent = 'Signing in...';
            btn.disabled = true;

            // Simulate auth call delay
            setTimeout(() => {
                errorAlert.textContent = 'Incorrect email or password. Please try again.';
                errorAlert.style.display = 'block';
                btn.textContent = 'Sign In';
                btn.disabled = false;
            }, 1000);
        });
        </script>
    """, unsafe_allow_html=True)

    # Handle form submission with Streamlit
    if st.session_state.get("login_submitted"):
        email = st.session_state.get("login_email", "")
        password = st.session_state.get("login_password", "")

        if email and password:
            user = authenticate(email, password)
            if user:
                st.session_state.current_user = user["username"]
                st.session_state.user_role = user["role"]
                st.session_state.login_error = ""
                st.session_state.login_submitted = False
                st.success(f"Welcome, {user['username']}! 🎉")
                st.balloons()
                st.rerun()
            else:
                st.session_state.login_error = "Incorrect email or password. Please try again."
                st.session_state.login_submitted = False

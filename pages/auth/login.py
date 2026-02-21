# pages/auth/login.py
"""Login page for authentication."""

import streamlit as st
from data.auth_repo import authenticate

# Apply styling
st.set_page_config(
    page_title="Login | THE DENTAL BOND",
    page_icon="🦷",
    layout="centered",
)

def render() -> None:
    """Render the professional login page."""
    # Clean, minimal styling
    st.markdown("""
        <style>
        /* Main background */
        .main {
            background: #ffffff;
        }

        .block-container {
            padding-top: 60px;
            padding-bottom: 60px;
        }

        /* Login container */
        .login-container {
            background: white;
            padding: 60px 40px;
            text-align: center;
            max-width: 500px;
            margin: 0 auto;
        }

        /* Tooth icon */
        .tooth-icon {
            font-size: 80px;
            margin-bottom: 24px;
            display: block;
        }

        /* Title styling */
        .login-title {
            text-align: center;
            font-size: 32px;
            font-weight: 700;
            color: #1a1a1a;
            margin-bottom: 4px;
            letter-spacing: 0.5px;
            font-family: Georgia, serif;
        }

        .login-subtitle {
            text-align: center;
            font-size: 13px;
            color: #666666;
            margin-bottom: 40px;
            font-weight: 400;
            letter-spacing: 0.5px;
        }

        /* Input fields styling */
        .stTextInput > div > div > input {
            border-radius: 4px;
            border: 1px solid #d0d0d0;
            padding: 12px 14px;
            font-size: 14px;
            transition: all 0.2s ease;
            background: #ffffff;
        }

        .stTextInput > div > div > input:focus {
            border-color: #999999;
            box-shadow: none;
        }

        /* Label styling */
        .stTextInput > label {
            font-weight: 400;
            color: #333333;
            font-size: 13px;
            margin-bottom: 6px;
        }

        /* Button styling */
        .stButton > button {
            border-radius: 4px;
            padding: 11px 32px;
            font-size: 14px;
            font-weight: 600;
            background: #c4a574;
            border: none;
            color: white;
            transition: all 0.2s ease;
            box-shadow: none;
            height: auto;
            letter-spacing: 0.5px;
            text-transform: uppercase;
        }

        .stButton > button:hover {
            background: #b89460;
            box-shadow: none;
        }

        .stButton > button:active {
            background: #a88450;
        }

        /* Links styling */
        .login-links {
            display: flex;
            justify-content: space-between;
            margin-top: 20px;
            margin-bottom: 20px;
        }

        .login-links a {
            color: #666666;
            text-decoration: none;
            font-size: 13px;
        }

        .login-links a:hover {
            text-decoration: underline;
            color: #333333;
        }

        /* Error/Success styling */
        .stAlert {
            border-radius: 4px;
            border-left: 4px solid #ef4444;
            margin-bottom: 16px;
            font-size: 13px;
        }

        .stSuccess {
            border-radius: 4px;
            border-left: 4px solid #10b981;
            font-size: 13px;
        }
        </style>
    """, unsafe_allow_html=True)

    # Center the login form
    col1, col2, col3 = st.columns([1, 2.5, 1])

    with col2:
        st.markdown('<div class="login-container">', unsafe_allow_html=True)

        # Logo
        try:
            st.image("assets/logo.png", width='200')
        except Exception:
            st.markdown('<span class="tooth-icon">🦷</span>', unsafe_allow_html=True)

        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

        # Title
        st.markdown('<div class="login-subtitle">Implant & Micro-dentistry</div>', unsafe_allow_html=True)

        # Form
        username = st.text_input("Username", key="login_username", placeholder="Username")
        password = st.text_input("Password", type="password", key="login_password", placeholder="Password")

        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

        if st.button("LOG IN", width='stretch', type="primary"):
            if not username or not password:
                st.error("Please enter both username and password")
            else:
                user = authenticate(username, password)
                if user:
                    st.session_state.current_user = user["username"]
                    st.session_state.user_role = user["role"]
                    st.success(f"Welcome, {user['username']}! 🎉")
                    st.balloons()
                    st.rerun()
                else:
                    st.error("Invalid username or password")

        # Links
        st.markdown("""
            <div class="login-links">
                <a href="#">Forget Username/Password?</a>
                <a href="#">Create Account</a>
            </div>
        """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

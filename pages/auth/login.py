# pages/auth/login.py
"""Login page for authentication."""

import streamlit as st
from data.auth_repo import authenticate

# Apply premium styling
st.set_page_config(
    page_title="Login | THE DENTAL BOND",
    page_icon="🦷",
    layout="centered",
)

def render() -> None:
    """Render the premium login page."""
    # Premium CSS styling
    st.markdown("""
        <style>
        /* Main background gradient */
        .main {
            background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
        }

        /* Login container styling */
        .login-container {
            background: transparent;
            padding: 60px 40px;
        }

        /* Logo styling */
        .logo-container {
            display: flex;
            justify-content: center;
            margin-bottom: 40px;
        }

        .logo-container img {
            max-width: 200px;
            height: auto;
            filter: drop-shadow(0 4px 12px rgba(37, 99, 235, 0.1));
        }

        /* Title styling */
        .login-title {
            text-align: center;
            font-size: 28px;
            font-weight: 700;
            color: #1e293b;
            margin-bottom: 8px;
            letter-spacing: -0.5px;
        }

        .login-subtitle {
            text-align: center;
            font-size: 14px;
            color: #64748b;
            margin-bottom: 32px;
            font-weight: 500;
        }

        /* Input fields styling */
        .stTextInput > div > div > input {
            border-radius: 12px;
            border: 2px solid #e2e8f0;
            padding: 12px 16px;
            font-size: 15px;
            transition: all 0.3s ease;
        }

        .stTextInput > div > div > input:focus {
            border-color: #2563eb;
            box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
        }

        /* Button styling */
        .stButton > button {
            border-radius: 12px;
            padding: 14px 24px;
            font-size: 16px;
            font-weight: 600;
            background: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%);
            border: none;
            color: white;
            transition: all 0.3s ease;
            box-shadow: 0 8px 16px rgba(37, 99, 235, 0.3);
            height: auto;
        }

        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 12px 24px rgba(37, 99, 235, 0.4);
        }

        .stButton > button:active {
            transform: translateY(0);
        }

        /* Error message styling */
        .stAlert {
            border-radius: 12px;
            border-left: 4px solid #ef4444;
        }

        /* Success message styling */
        .stSuccess {
            border-radius: 12px;
            border-left: 4px solid #10b981;
        }

        /* Divider styling */
        hr {
            margin: 24px 0;
            border: none;
            height: 1px;
            background: linear-gradient(90deg, transparent, #e2e8f0, transparent);
        }

        /* Label styling */
        .stTextInput > label {
            font-weight: 600;
            color: #1e293b;
            font-size: 14px;
            margin-bottom: 8px;
        }
        </style>
    """, unsafe_allow_html=True)

    # Center the login form
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown('<div class="login-container">', unsafe_allow_html=True)

        # Try to display logo, fallback to text
        try:
            st.image("assets/logo.png", use_container_width=True)
            st.markdown("<br>", unsafe_allow_html=True)
        except Exception:
            pass

        # Title
        st.markdown('<div class="login-title">Welcome Back</div>', unsafe_allow_html=True)
        st.markdown('<div class="login-subtitle">Sign in to your account</div>', unsafe_allow_html=True)

        # Form
        username = st.text_input("Username", key="login_username", placeholder="Enter your username")
        password = st.text_input("Password", type="password", key="login_password", placeholder="Enter your password")

        # Forgot password link
        col_forgot, _ = st.columns([1, 2])
        with col_forgot:
            if st.button("🔑 Forgot Password?", use_container_width=True, type="secondary", key="btn_forgot"):
                st.session_state.show_reset_password = True

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("Sign In", use_container_width=True, type="primary"):
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
                    st.error("❌ Invalid credentials. Please try again.")

        st.markdown('</div>', unsafe_allow_html=True)

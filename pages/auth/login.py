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
    """Render the premium login page."""
    # Premium styling with gradient and refined aesthetics
    st.markdown("""
        <style>
        /* Main background with premium gradient */
        .main {
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
            min-height: 100vh;
        }

        .block-container {
            padding-top: 40px;
            padding-bottom: 40px;
            max-width: 100%;
        }

        /* Premium login container */
        .login-container {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3), 0 0 100px rgba(196, 165, 116, 0.1);
            border-radius: 24px;
            padding: 50px 60px;
            text-align: center;
            max-width: 480px;
            margin: 0 auto;
            position: relative;
            overflow: hidden;
        }

        /* Gradient accent line */
        .login-container::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, #c4a574 0%, #d4b896 50%, #c4a574 100%);
        }

        /* Form group styling */
        .form-group {
            margin-bottom: 20px;
            text-align: left;
        }

        /* Input fields styling */
        .stTextInput > div > div > input {
            border-radius: 12px;
            border: 2px solid #e2e8f0;
            padding: 14px 18px;
            font-size: 15px;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            background: #ffffff;
            font-family: inherit;
        }

        .stTextInput > div > div > input::placeholder {
            color: #cbd5e1;
        }

        .stTextInput > div > div > input:focus {
            border-color: #c4a574;
            box-shadow: 0 0 0 4px rgba(196, 165, 116, 0.1), 0 0 20px rgba(196, 165, 116, 0.2);
            outline: none;
        }

        /* Label styling */
        .stTextInput > label {
            font-weight: 600;
            color: #1e293b;
            font-size: 13px;
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            display: block;
        }

        /* Button styling */
        .stButton > button {
            border-radius: 12px;
            padding: 16px 40px;
            font-size: 14px;
            font-weight: 700;
            background: linear-gradient(135deg, #c4a574 0%, #d4b896 100%);
            border: none;
            color: white;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: 0 8px 20px rgba(196, 165, 116, 0.3);
            height: auto;
            letter-spacing: 1px;
            text-transform: uppercase;
            width: 100%;
            cursor: pointer;
        }

        .stButton > button:hover {
            background: linear-gradient(135deg, #b89460 0%, #c4a574 100%);
            box-shadow: 0 12px 30px rgba(196, 165, 116, 0.4);
            transform: translateY(-2px);
        }

        .stButton > button:active {
            transform: translateY(0);
        }

        /* Links styling */
        .login-links {
            display: flex;
            justify-content: space-between;
            gap: 20px;
            margin-top: 24px;
            padding-top: 16px;
            border-top: 1px solid #e2e8f0;
        }

        .login-links a {
            color: #64748b;
            text-decoration: none;
            font-size: 12px;
            font-weight: 500;
            transition: all 0.2s ease;
            flex: 1;
            text-align: center;
        }

        .login-links a:hover {
            color: #c4a574;
            text-decoration: none;
        }

        /* Error/Success styling */
        .stAlert {
            border-radius: 12px;
            border-left: 4px solid #ef4444;
            margin-bottom: 20px;
            font-size: 13px;
            background: rgba(239, 68, 68, 0.05);
            padding: 14px 16px;
        }

        .stSuccess {
            border-radius: 12px;
            border-left: 4px solid #10b981;
            font-size: 13px;
            background: rgba(16, 185, 129, 0.05);
            padding: 14px 16px;
        }

        /* Divider spacing */
        .login-divider {
            height: 1px;
            background: linear-gradient(90deg, transparent, #e2e8f0, transparent);
            margin: 24px 0;
        }
        </style>
    """, unsafe_allow_html=True)

    # Center the login form
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown('<div class="login-container">', unsafe_allow_html=True)

        # Form inputs with enhanced styling
        username = st.text_input("Username", key="login_username", placeholder="Enter your username")
        password = st.text_input("Password", type="password", key="login_password", placeholder="Enter your password")

        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

        # Login button
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

        # Footer links
        st.markdown("""
            <div class="login-links">
                <a href="#">Forget Password?</a>
                <a href="#">Create Account</a>
            </div>
        """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

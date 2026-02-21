# pages/auth/reset_password.py
"""Password reset page."""

import streamlit as st
from data.auth_repo import reset_password, authenticate

# Apply premium styling
st.set_page_config(
    page_title="Reset Password | THE DENTAL BOND",
    page_icon="🦷",
    layout="centered",
)

def render() -> None:
    """Render the premium password reset page."""
    # Premium CSS styling
    st.markdown("""
        <style>
        /* Main background gradient */
        .main {
            background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
        }

        /* Reset container styling */
        .reset-container {
            background: transparent;
            padding: 60px 40px;
        }

        /* Title styling */
        .reset-title {
            text-align: center;
            font-size: 28px;
            font-weight: 700;
            color: #1e293b;
            margin-bottom: 8px;
            letter-spacing: -0.5px;
        }

        .reset-subtitle {
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

        /* Label styling */
        .stTextInput > label {
            font-weight: 600;
            color: #1e293b;
            font-size: 14px;
            margin-bottom: 8px;
        }

        /* Link styling */
        .back-link {
            text-align: center;
            margin-top: 24px;
        }

        .back-link a {
            color: #2563eb;
            text-decoration: none;
            font-weight: 600;
            font-size: 14px;
        }

        .back-link a:hover {
            text-decoration: underline;
        }
        </style>
    """, unsafe_allow_html=True)

    # Center the form
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown('<div class="reset-container">', unsafe_allow_html=True)

        # Title
        st.markdown('<div class="reset-title">Reset Password</div>', unsafe_allow_html=True)
        st.markdown('<div class="reset-subtitle">Enter your username and new password</div>', unsafe_allow_html=True)

        # Form
        username = st.text_input("Username", key="reset_username", placeholder="Enter your username")
        new_password = st.text_input("New Password", type="password", key="reset_password", placeholder="Enter new password")
        confirm_password = st.text_input("Confirm Password", type="password", key="reset_confirm", placeholder="Confirm new password")

        st.markdown("<br>", unsafe_allow_html=True)

        col_reset, col_back = st.columns(2)

        with col_reset:
            if st.button("Reset Password", width='stretch', type="primary"):
                if not username or not new_password or not confirm_password:
                    st.error("Please fill in all fields")
                elif new_password != confirm_password:
                    st.error("❌ Passwords do not match")
                elif len(new_password) < 6:
                    st.error("❌ Password must be at least 6 characters")
                else:
                    # Check if user exists by attempting to query
                    if reset_password(username, new_password):
                        st.success(f"✅ Password reset successfully! You can now login.")
                        st.balloons()
                        st.session_state.go_to_login = True
                    else:
                        st.error("❌ Failed to reset password. Username may not exist.")

        with col_back:
            if st.button("← Back to Login", width='stretch', type="secondary"):
                st.session_state.go_to_login = True

        # Handle navigation
        if st.session_state.get("go_to_login"):
            st.session_state.go_to_login = False
            st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

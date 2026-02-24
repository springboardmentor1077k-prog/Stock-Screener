"""
User Registration Page
Allows new users to create an account with email and password.
"""

import re
import streamlit as st


def is_valid_email(email):
    """Basic email validation."""
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None


def is_strong_password(password):
    """Check if password meets minimum requirements."""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r"\d", password):
        return False, "Password must contain at least one number"
    return True, "Password is strong"


def render_register():
    """Render the registration page."""
    if "api_client" not in st.session_state:
        from api_client import APIClient
        st.session_state.api_client = APIClient()

    api_client = st.session_state.api_client

    # Match login-page sidebar behavior
    st.markdown("""<style>[data-testid="stSidebarNav"] {display: none;}</style>""", unsafe_allow_html=True)
    with st.sidebar:
        st.header("📈AI Stock Screener")
        st.divider()
        auth_page = st.radio("Navigate", ["Login", "Register"], index=1, label_visibility="collapsed")
    if auth_page == "Login":
        st.switch_page("app.py")

    st.title("Create Account")
    st.caption("Join the AI Stock Screener platform")
    st.warning("Disclaimer: This platform is for informational purposes only and is not financial advice.")

    with st.form("registration_form"):
        email = st.text_input(
            "Email Address",
            placeholder="your.email@example.com",
            help="Enter a valid email address",
        )

        password = st.text_input(
            "Password",
            type="password",
            placeholder="Enter a strong password",
            help="Minimum 8 characters with uppercase, lowercase, and numbers",
        )

        confirm_password = st.text_input(
            "Confirm Password",
            type="password",
            placeholder="Re-enter your password",
        )

        submitted = st.form_submit_button(
            "Create Account",
            use_container_width=True,
            type="primary",
        )

        if submitted:
            if not email or not password or not confirm_password:
                st.error("Please fill in all fields")
            elif not is_valid_email(email):
                st.error("Please enter a valid email address")
            elif password != confirm_password:
                st.error("Passwords do not match")
            else:
                strong, msg = is_strong_password(password)
                if not strong:
                    st.error(msg)
                else:
                    with st.spinner("Creating your account..."):
                        success, reg_msg = api_client.register(email, password)

                    if success:
                        st.success(reg_msg)
                        st.info("You can now login with your credentials.")
                        if st.button("Go to Login", type="primary"):
                            st.switch_page("app.py")
                    else:
                        st.error(reg_msg)

    st.divider()
    col1, col2 = st.columns([3, 1])
    with col1:
        st.caption("Already have an account?")
    with col2:
        if st.button("Login", use_container_width=True):
            st.switch_page("app.py")


if __name__ == "__main__":
    render_register()

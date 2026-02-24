"""
Main Streamlit Application - AI Stock Screener

This is the entry point for the stock screener application.
Features:
- Sidebar navigation between pages
- Session state management
- Authentication flow
- Three main pages: Screener, Portfolio, Alerts
"""

import streamlit as st
from config import PAGE_TITLE, PAGE_ICON, LAYOUT
from api_client import APIClient


# ============ PAGE CONFIGURATION ============
st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=PAGE_ICON,
    layout=LAYOUT,
    initial_sidebar_state="expanded"
)


# ============ SESSION STATE INITIALIZATION ============
def init_session_state():
    """Initialize session state variables."""
    if "token" not in st.session_state:
        st.session_state.token = None
    
    if "current_page" not in st.session_state:
        st.session_state.current_page = "Screener"
    
    if "api_client" not in st.session_state:
        st.session_state.api_client = APIClient()


# ============ AUTHENTICATION ============
def check_authentication():
    """Show login form if user is not authenticated."""
    st.title("🔐 Login to AI Stock Screener")
    st.caption("Access your stock portfolio and screening tools")
    st.warning("Disclaimer: This platform is for informational purposes only and is not financial advice.")
    
    # Create centered login form
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Login form
        with st.form("login_form"):
            email = st.text_input(
                "Email Address",
                placeholder="your.email@example.com"
            )
            
            password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter your password"
            )
            
            # Submit button
            submitted = st.form_submit_button(
                "🔓 Login",
                use_container_width=True,
                type="primary"
            )
            
            if submitted:
                if not email or not password:
                    st.error("⚠️ Please enter both email and password")
                else:
                    # Login via API
                    with st.spinner("Logging in..."):
                        success, message, data = st.session_state.api_client.login(email, password)
                    
                    if success:
                        # Store token and user info in session
                        st.session_state.token = data.get("access_token")
                        st.session_state.user_id = data.get("user_id")
                        st.session_state.email = data.get("email")
                        st.session_state.authenticated = True
                        
                        st.success(f"✅ Welcome back!")
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
        
        # Link to registration (outside the form)
        st.divider()
        st.caption("Don't have an account?")
        if st.button("📝 Create an Account", use_container_width=True):
            st.switch_page("pages/register.py")


# ============ MAIN APPLICATION ============
def main():
    """Main application entry point."""
    
    # Initialize session state
    init_session_state()
    
    # Check authentication - show login/register if not authenticated
    if not st.session_state.token:
        # Hide default Streamlit page nav
        st.markdown("""<style>[data-testid="stSidebarNav"] {display: none;}</style>""", unsafe_allow_html=True)
        
        with st.sidebar:
            st.header("📈 AI Stock Screener")
            st.divider()
            auth_page = st.radio("Navigate", ["Login", "Register"], label_visibility="collapsed")
        
        if auth_page == "Login":
            check_authentication()
        else:
            st.switch_page("pages/register.py")
        return
    
    # User is authenticated - redirect to screener
    st.switch_page("pages/_screener.py")


# ============ ENTRY POINT ============
if __name__ == "__main__":
    main()

import streamlit as st
from utils.auth import authenticate_user, register_user, login, validate_password

def render_auth_styles():
    """Inject custom CSS for the modern, centered auth UI."""
    st.markdown("""
        <style>
        /* Completely hide the Streamlit header and reduce top padding */
        header {visibility: hidden;}
        [data-testid="stHeader"] {
            display: none;
        }
        .block-container {
            padding-top: 2rem !important;
            padding-bottom: 0rem !important;
        }
        
        /* The card header part */
        .auth-card-top {
            background: linear-gradient(135deg, #1e293b 0%, #111827 100%);
            padding: 30px 40px 10px 40px;
            border-radius: 20px 20px 0 0;
            border: 1px solid rgba(255,255,255,0.1);
            border-bottom: none;
            color: #ffffff;
            text-align: center;
        }
        
        /* The card body part (targeting the Streamlit form) */
        [data-testid="stForm"] {
            background: #111827 !important;
            padding: 10px 40px 30px 40px !important;
            border-radius: 0 0 20px 20px !important;
            border: 1px solid rgba(255,255,255,0.1) !important;
            border-top: none !important;
            margin-top: -1px; /* Overlap to hide the seam */
        }
        
        .auth-tag {
            text-transform: uppercase;
            letter-spacing: 0.1em;
            font-size: 12px;
            font-weight: 700;
            color: #38bdf8;
            margin-bottom: 15px;
        }
        .auth-logo {
            display: flex;
            justify-content: center;
            margin-bottom: 15px;
        }
        .auth-header h1 {
            color: #ffffff !important;
            font-size: 26px;
            font-weight: 800;
            margin-bottom: 8px;
            letter-spacing: -0.02em;
        }
        .auth-header p {
            color: #94a3b8;
            font-size: 15px;
            margin-bottom: 10px;
        }
        
        /* Form elements styling */
        .stTextInput label, .stCheckbox label {
            color: #e2e8f0 !important;
        }
        .stButton > button {
            width: 100%;
            border-radius: 10px !important;
            height: 48px;
            font-weight: 700 !important;
            background-color: #38bdf8 !important;
            color: #ffffff !important;
            border: none !important;
        }
        
        /* Navigation area below the card */
        .auth-footer {
            text-align: center;
            margin-top: 20px;
            padding: 10px;
        }
        
        /* Hide sidebar on auth pages */
        [data-testid="stSidebar"] {
            display: none;
        }
        </style>
    """, unsafe_allow_html=True)

def login_page():
    """Render the Login page UI."""
    render_auth_styles()
    
    _, col, _ = st.columns([1, 2, 1])
    
    with col:
        # Header part in one single markdown block
        st.markdown("""
            <div class="auth-card-top">
                <div class="auth-tag">Secure Login</div>
                <div class="auth-logo">
                    <img src="https://img.icons8.com/fluency/96/000000/stocks.png" width="80">
                </div>
                <div class="auth-header">
                    <h1>Welcome Back</h1>
                    <p>Enter your credentials to access your dashboard</p>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # Form part (styled via CSS to merge with the header)
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            remember_me = st.checkbox("Remember me")
            submit_button = st.form_submit_button("Sign In")
            
            if submit_button:
                if not username or not password:
                    st.error("Please fill in all fields.")
                elif authenticate_user(username, password):
                    st.success(f"Welcome, {username}!")
                    login(username)
                else:
                    st.error("Invalid username or password.")
        
        # Footer / Navigation
        st.markdown('<div class="auth-footer">', unsafe_allow_html=True)
        st.markdown('<p style="color: #64748b; font-size: 14px; margin-bottom: 5px;">Don\'t have an account?</p>', unsafe_allow_html=True)
        if st.button("Create an Account"):
            st.session_state.auth_page = "signup"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

def signup_page():
    """Render the Sign-up page UI."""
    render_auth_styles()
    
    _, col, _ = st.columns([1, 2, 1])
    
    with col:
        # Header part in one single markdown block
        st.markdown("""
            <div class="auth-card-top">
                <div class="auth-tag">Registration</div>
                <div class="auth-logo">
                    <img src="https://img.icons8.com/fluency/96/000000/stocks.png" width="80">
                </div>
                <div class="auth-header">
                    <h1>Create Account</h1>
                    <p>Join our platform and start analyzing stocks</p>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # Form part
        with st.form("signup_form"):
            new_username = st.text_input("Username", placeholder="Choose a username")
            new_password = st.text_input("Password", type="password", placeholder="Minimum 6 characters")
            confirm_password = st.text_input("Confirm Password", type="password", placeholder="Repeat your password")
            submit_button = st.form_submit_button("Register")
            
            if submit_button:
                if not new_username or not new_password:
                    st.error("Please fill in all fields.")
                elif new_password != confirm_password:
                    st.error("Passwords do not match.")
                else:
                    success, message = register_user(new_username, new_password)
                    if success:
                        st.success(message)
                        st.session_state.auth_page = "login"
                        import time
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(message)
        
        # Footer / Navigation
        st.markdown('<div class="auth-footer">', unsafe_allow_html=True)
        st.markdown('<p style="color: #64748b; font-size: 14px; margin-bottom: 5px;">Already have an account?</p>', unsafe_allow_html=True)
        if st.button("Back to Login"):
            st.session_state.auth_page = "login"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

def render_auth_interface():
    """Main entry point for rendering the auth UI based on session state."""
    if st.session_state.auth_page == "login":
        login_page()
    else:
        signup_page()

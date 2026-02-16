# Streamlit Frontend for Stock Screener - Advanced Dashboard with Screener, Portfolio & Alerts
import streamlit as st
import requests
import pandas as pd
from typing import Dict, Any
import time
import json

# Set page config
st.set_page_config(
    page_title="StockScreener Pro",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Constants ---
import os
API_TIMEOUT = int(os.getenv("FRONTEND_API_TIMEOUT", "10"))
HEALTH_CHECK_TIMEOUT = int(os.getenv("FRONTEND_HEALTH_CHECK_TIMEOUT", "5"))

# CSS for advanced dashboard interface
st.markdown("""
<style>
    /* Main container */
    .main-container {
        display: flex;
        flex-direction: column;
        min-height: 100vh;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* Header styles */
    .header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.5rem 1rem;
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        color: white;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        position: sticky;
        top: 0;
        z-index: 100;
        border-bottom: 1px solid rgba(255,255,255,0.2);
    }
    
    .logo {
        font-size: 1.8rem;
        font-weight: bold;
        display: flex;
        align-items: center;
    }
    
    .nav-buttons {
        display: flex;
        gap: 1rem;
        align-items: center;
    }
    
    .btn {
        padding: 0.6rem 1.2rem;
        border-radius: 25px;
        border: none;
        cursor: pointer;
        font-weight: 500;
        transition: all 0.3s ease;
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .btn-logout {
        background: linear-gradient(90deg, #ff5252, #d32f2f);
        color: white;
        border: none;
    }
    
    .btn-logout:hover {
        background: linear-gradient(90deg, #d32f2f, #ff5252);
        transform: translateY(-2px);
    }
    
    /* Main content area */
    .main-content {
        display: flex;
        flex: 1;
        padding: 1rem;
        gap: 1rem;
        margin-top: 0.5rem;
    }
    
    /* Dashboard container */
    .dashboard-container {
        flex: 1;
        background: rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        padding: 1.5rem;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.2);
        display: flex;
        flex-direction: column;
        min-height: 60vh;
        margin: 0;
        max-width: 100%;
    }
    
    .dashboard-header {
        text-align: center;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid rgba(255,255,255,0.2);
    }
    
    .dashboard-title {
        font-size: 1.8rem;
        color: white;
        margin-bottom: 0.3rem;
        font-weight: 700;
    }
    
    .dashboard-subtitle {
        color: rgba(255,255,255,0.8);
        font-size: 0.9rem;
    }
    
    /* Login modal */
    .modal-overlay {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.3) 0%, rgba(118, 75, 162, 0.3) 100%);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 9999;
        animation: fadeInScale 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    }
    
    .modal-content {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        border-radius: 25px;
        padding: 3rem;
        width: 90%;
        max-width: 480px;
        box-shadow: 0 30px 60px rgba(0, 0, 0, 0.25), 
                    inset 0 1px 0 rgba(255, 255, 255, 0.3),
                    inset 0 -1px 0 rgba(0, 0, 0, 0.05);
        text-align: center;
        animation: modalPop 0.6s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        position: relative;
        overflow: hidden;
        z-index: 10000;
    }
    
    .modal-content::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #667eea, #764ba2, #667eea);
        background-size: 200% 200%;
        animation: gradientShift 3s ease infinite;
    }
    
    .modal-title {
        font-size: 2rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.8rem;
        font-weight: 800;
        letter-spacing: -0.5px;
    }
    
    .modal-subtitle {
        font-size: 1.1rem;
        color: #666;
        margin-bottom: 2rem;
        font-weight: 500;
    }
    
    .modal-description {
        color: #666;
        margin-bottom: 1.5rem;
        line-height: 1.6;
        font-size: 1rem;
    }
    
    .modal-form {
        display: flex;
        flex-direction: column;
        gap: 1.2rem;
    }
    
    .modal-input {
        padding: 1.1rem 1.3rem;
        border: 2px solid #e0e0e0;
        border-radius: 15px;
        font-size: 1rem;
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        background: rgba(255, 255, 255, 0.8);
        box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.03);
    }
    
    .modal-input:focus {
        outline: none;
        border-color: #667eea;
        box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.2), 
                    inset 0 2px 4px rgba(0, 0, 0, 0.05);
        transform: translateY(-2px);
    }
    
    .modal-input::placeholder {
        color: #aaa;
    }
    
    .modal-buttons {
        display: flex;
        gap: 1.2rem;
        margin-top: 1.8rem;
    }
    
    .modal-btn {
        flex: 1;
        padding: 1.1rem;
        border-radius: 15px;
        border: none;
        font-size: 1rem;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        box-shadow: 0 6px 15px rgba(0, 0, 0, 0.15);
        letter-spacing: 0.5px;
        text-transform: uppercase;
        position: relative;
        overflow: hidden;
    }
    
    .modal-btn::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
        transition: 0.5s;
    }
    
    .modal-btn:hover::before {
        left: 100%;
    }
    
    .modal-btn-login {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    .modal-btn-login:hover {
        transform: translateY(-3px);
        box-shadow: 0 10px 25px rgba(102, 126, 234, 0.4);
    }
    
    .modal-btn-signup {
        background: linear-gradient(135deg, #00c853 0%, #009624 100%);
        color: white;
    }
    
    .modal-btn-signup:hover {
        transform: translateY(-3px);
        box-shadow: 0 10px 25px rgba(0, 200, 83, 0.4);
    }
    
    .divider {
        display: flex;
        align-items: center;
        text-align: center;
        margin: 1.5rem 0;
    }
    
    .divider::before,
    .divider::after {
        content: '';
        flex: 1;
        border-bottom: 1px solid #e0e0e0;
    }
    
    .divider::before {
        margin-right: 1rem;
    }
    
    .divider::after {
        margin-left: 1rem;
    }
    
    .divider-text {
        color: #666;
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* Animations */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    @keyframes fadeInScale {
        0% {
            opacity: 0;
            transform: scale(0.9);
        }
        100% {
            opacity: 1;
            transform: scale(1);
        }
    }
    
    @keyframes modalPop {
        0% {
            opacity: 0;
            transform: scale(0.8) translateY(50px);
        }
        70% {
            transform: scale(1.02) translateY(-5px);
        }
        100% {
            opacity: 1;
            transform: scale(1) translateY(0);
        }
    }
    
    @keyframes gradientShift {
        0% {
            background-position: 0% 50%;
        }
        50% {
            background-position: 100% 50%;
        }
        100% {
            background-position: 0% 50%;
        }
    }
    
    @keyframes slideUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    /* Feedback messages */
    .feedback-success {
        background: #d4edda;
        color: #155724;
        padding: 10px 15px;
        border-radius: 8px;
        border-left: 4px solid #28a745;
        margin: 10px 0;
    }
    
    .feedback-error {
        background: #f8d7da;
        color: #721c24;
        padding: 10px 15px;
        border-radius: 8px;
        border-left: 4px solid #dc3545;
        margin: 10px 0;
    }
    
    .feedback-info {
        background: #d1ecf1;
        color: #0c5460;
        padding: 10px 15px;
        border-radius: 8px;
        border-left: 4px solid #17a2b8;
        margin: 10px 0;
    }
    
    .feedback-warning {
        background: #fff3cd;
        color: #856404;
        padding: 10px 15px;
        border-radius: 8px;
        border-left: 4px solid #ffc107;
        margin: 10px 0;
    }
    
    /* Utility pills / tags */
    .pill {
        display: inline-flex;
        align-items: center;
        padding: 0.15rem 0.6rem;
        border-radius: 999px;
        font-size: 0.7rem;
        font-weight: 500;
        background: rgba(255, 255, 255, 0.15);
        color: #fff;
        border: 1px solid rgba(255, 255, 255, 0.2);
        margin-right: 0.35rem;
        margin-bottom: 0.35rem;
    }
    
    .pill-label {
        opacity: 0.8;
        margin-right: 0.25rem;
    }
    
    .pill-value {
        font-weight: 600;
    }
    
    /* Simple stat cards */
    .stat-card {
        border-radius: 16px;
        padding: 0.85rem 1rem;
        background: rgba(255, 255, 255, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.18);
        color: #fff;
        box-shadow: 0 8px 20px rgba(0,0,0,0.12);
    }
    
    .stat-label {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        opacity: 0.8;
        margin-bottom: 0.15rem;
    }
    
    .stat-value {
        font-size: 1.2rem;
        font-weight: 700;
    }
    
    /* Chat helper text */
    .chat-hint {
        font-size: 0.8rem;
        color: rgba(255,255,255,0.85);
        background: rgba(0,0,0,0.15);
        border-radius: 999px;
        padding: 0.25rem 0.7rem;
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        margin-bottom: 0.4rem;
    }

    /* ---- Global, simplified styling for all sections ---- */

    /* App background & base typography */
    .stApp {
        background: #000000;
        font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        color: #f9fafb;
    }

    /* Headings */
    h1, h2, h3 {
        font-weight: 600 !important;
        color: #111827 !important;
    }

    h1 {
        font-size: 1.7rem !important;
    }

    h2 {
        font-size: 1.25rem !important;
    }

    h3 {
        font-size: 1.05rem !important;
    }

    /* Paragraph / caption text */
    .stMarkdown p, .stCaption {
        color: #e5e7eb;
    }

    /* Primary buttons (Screener / Portfolio / Alerts / AI Advisor) */
    .stButton > button {
        border-radius: 999px;
        border: 1px solid #374151;
        padding: 0.4rem 1rem;
        font-weight: 500;
        font-size: 0.9rem;
        background: #020617;
        color: #f9fafb;
        transition: background 0.15s ease-out, transform 0.12s ease-out, box-shadow 0.15s ease-out;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.6);
    }

    .stButton > button:hover {
        background: #111827;
        transform: translateY(-1px);
        box-shadow: 0 6px 14px rgba(0, 0, 0, 0.7);
    }

    .stButton > button:active {
        transform: translateY(0);
        box-shadow: 0 3px 8px rgba(0, 0, 0, 0.6);
    }

    /* Top navigation radio buttons (tabs) */
    div[role="radiogroup"] > label {
        border-radius: 999px;
        padding: 0.15rem 0.85rem;
        margin-right: 0.25rem;
        border: 1px solid #374151;
        background: #020617;
        color: #e5e7eb;
        font-size: 0.85rem;
        font-weight: 500;
    }

    div[role="radiogroup"] > label:hover {
        border-color: #facc15;
    }

    /* Selected nav item (keep dark, highlight with border + shadow only) */
    div[role="radiogroup"] input:checked + div {
        background: #020617;
        color: #facc15;
        border-color: #facc15;
        box-shadow: 0 0 0 1px rgba(250, 204, 21, 0.45);
    }

    /* Dataframes (Screener results, Portfolio holdings, Alerts) */
    div[data-testid="stDataFrame"] {
        background: #020617;
        border-radius: 12px;
        padding: 0.25rem 0.25rem 0.5rem 0.25rem;
        border: 1px solid #374151;
        box-shadow: 0 6px 18px rgba(0, 0, 0, 0.7);
    }

    /* Forms (Screener criteria, Add Holding, Alerts) */
    form, .stForm {
        background: #020617;
        border-radius: 12px;
        padding: 0.85rem 1rem;
        border: 1px solid #374151;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.7);
    }

    /* Text inputs / selects */
    .stTextInput > div > input,
    .stNumberInput input,
    .stSelectbox > div > div {
        border-radius: 8px !important;
        border: 1px solid #4b5563 !important;
        padding: 0.3rem 0.7rem !important;
        font-size: 0.9rem !important;
        background: #020617 !important;
        color: #f9fafb !important;
    }

    .stTextInput > div > input:focus,
    .stNumberInput input:focus,
    .stSelectbox > div > div:focus {
        border-color: #facc15 !important;
        box-shadow: 0 0 0 1px rgba(250, 204, 21, 0.45) !important;
    }

    /* Metrics row (Portfolio summary) */
    [data-testid="stMetric"] {
        background: #020617;
        border-radius: 12px;
        padding: 0.7rem 0.85rem;
        border: 1px solid #374151;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.7);
    }
    
    /* Responsive adjustments */
    @media (max-width: 768px) {
        .main-content {
            flex-direction: column;
            padding: 1rem;
        }
        
        .dashboard-container {
            height: auto;
        }
        
        .modal-buttons {
            flex-direction: column;
        }
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'access_token' not in st.session_state:
    st.session_state.access_token = None
if 'refresh_token' not in st.session_state:
    st.session_state.refresh_token = None
if 'show_login_feedback' not in st.session_state:
    st.session_state.show_login_feedback = False
if 'login_feedback_message' not in st.session_state:
    st.session_state.login_feedback_message = ""
if 'login_feedback_type' not in st.session_state:
    st.session_state.login_feedback_type = ""
if 'current_page' not in st.session_state:
    # Default to Screener page (stored in title-case to match nav labels)
    st.session_state.current_page = "Screener"
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'ai_cache' not in st.session_state:
    # Simple in-session cache so repeated questions get instant answers
    st.session_state.ai_cache = {}
if 'show_auth_modal' not in st.session_state:
    st.session_state.show_auth_modal = not st.session_state.get('logged_in', False)

# API base URL
API_BASE_URL = "http://localhost:8002/api/v1"

def make_authenticated_request(method, url, json=None, params=None):
    """Make authenticated requests with automatic token refresh."""
    headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
    
    if method.upper() == "GET":
        response = requests.get(url, headers=headers, params=params)
    elif method.upper() == "POST":
        response = requests.post(url, headers=headers, json=json)
    elif method.upper() == "PUT":
        response = requests.put(url, headers=headers, json=json)
    elif method.upper() == "DELETE":
        response = requests.delete(url, headers=headers)
    
    # If unauthorized, try to refresh token
    if response.status_code == 401 and st.session_state.refresh_token:
        refresh_response = requests.post(
            f"{API_BASE_URL}/auth/refresh",
            json={"refresh_token": st.session_state.refresh_token}
        )
        
        if refresh_response.status_code == 200:
            token_data = refresh_response.json()
            st.session_state.access_token = token_data['access_token']
            st.session_state.refresh_token = token_data['refresh_token']
            
            # Retry the original request with new token
            headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, params=params)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, json=json)
            elif method.upper() == "PUT":
                response = requests.put(url, headers=headers, json=json)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=headers)
        else:
            # If refresh failed, log out user
            st.session_state.logged_in = False
            st.session_state.access_token = None
            st.session_state.refresh_token = None
            st.session_state.show_auth_modal = True  # Show modal again if session expires
            st.error("Session expired. Please log in again.")
            st.rerun()
    
    return response


def ask_ai_advisor(question: str) -> str:
    """
    Call the backend AI advisor endpoint with authentication and basic error handling.
    """
    try:
        resp = make_authenticated_request(
            "POST",
            f"{API_BASE_URL}/ai-advice",
            json={"query": question},
        )

        if resp.status_code == 200:
            data = resp.json()
            # Backend currently returns {"advice": "..."}
            if isinstance(data, dict) and "advice" in data:
                return data["advice"]
            return str(data)

        if resp.status_code == 401:
            return "Your session is not authorized to use the AI advisor. Please log in again."

        return f"Sorry, I couldn't fetch AI advice right now (status {resp.status_code}). Please try again later."
    except requests.exceptions.ConnectionError:
        return "Unable to connect to the AI advisor service. Please ensure the backend is running."
    except Exception:
        return "An unexpected error occurred while contacting the AI advisor. Please try again."

# Check if user is already logged in by validating the token
if st.session_state.access_token and not st.session_state.logged_in:
    # Validate the token with the backend
    try:
        headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
        response = requests.get(f"{API_BASE_URL}/auth/refresh", json={"refresh_token": st.session_state.refresh_token or ""})
        if response.status_code == 200:
            st.session_state.logged_in = True
            st.session_state.show_auth_modal = False
        else:
            # Token is invalid, reset session
            st.session_state.logged_in = False
            st.session_state.access_token = None
            st.session_state.refresh_token = None
            st.session_state.show_auth_modal = True
    except:
        # If there's an error validating the token, assume user is not logged in
        st.session_state.logged_in = False
        st.session_state.access_token = None
        st.session_state.refresh_token = None
        st.session_state.show_auth_modal = True

# Show authentication modal if user is not logged in
if st.session_state.show_auth_modal:
    # Create a centered container for the login modal
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<h2 style="font-size: 2rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; margin-bottom: 1rem; font-weight: 800; letter-spacing: -0.5px; text-align: center;">Welcome to StockScreener Pro</h2>', unsafe_allow_html=True)
        
        st.markdown('<p style="color: #666; margin-bottom: 1.5rem; line-height: 1.6; font-size: 1rem; text-align: center;">Please log in or sign up to access the advanced stock screening and analysis tools.</p>', unsafe_allow_html=True)
        
        # Display feedback message if available inside modal
        if st.session_state.show_login_feedback:
            if st.session_state.login_feedback_type == "success":
                st.markdown(f'<div style="background: #d4edda; color: #155724; padding: 10px 15px; border-radius: 8px; border-left: 4px solid #28a745; margin: 10px 0; text-align: center;">{st.session_state.login_feedback_message}</div>', unsafe_allow_html=True)
            elif st.session_state.login_feedback_type == "error":
                st.markdown(f'<div style="background: #f8d7da; color: #721c24; padding: 10px 15px; border-radius: 8px; border-left: 4px solid #dc3545; margin: 10px 0; text-align: center;">{st.session_state.login_feedback_message}</div>', unsafe_allow_html=True)
            elif st.session_state.login_feedback_type == "info":
                st.markdown(f'<div style="background: #d1ecf1; color: #0c5460; padding: 10px 15px; border-radius: 8px; border-left: 4px solid #17a2b8; margin: 10px 0; text-align: center;">{st.session_state.login_feedback_message}</div>', unsafe_allow_html=True)
            elif st.session_state.login_feedback_type == "warning":
                st.markdown(f'<div style="background: #fff3cd; color: #856404; padding: 10px 15px; border-radius: 8px; border-left: 4px solid #ffc107; margin: 10px 0; text-align: center;">{st.session_state.login_feedback_message}</div>', unsafe_allow_html=True)
        
        # Create tabs for login/signup using Streamlit's native tabs
        tab1, tab2 = st.tabs(["Log In", "Sign Up"])
        
        with tab1:
            with st.form(key="login_form_modal"):
                email = st.text_input("Email Address", placeholder="Enter your email address", key="modal_email")
                password = st.text_input("Password", type="password", placeholder="Enter your password", key="modal_password")
                login_submitted = st.form_submit_button("Log In", use_container_width=True)
            
            if login_submitted:
                if not email or not password:
                    st.session_state.show_login_feedback = True
                    st.session_state.login_feedback_message = "Please fill in both email and password fields"
                    st.session_state.login_feedback_type = "error"
                else:
                    with st.spinner("Authenticating... This may take a moment."):
                        try:
                            response = requests.post(
                                f"{API_BASE_URL}/auth/login",
                                json={"email": email, "password": password},
                                timeout=API_TIMEOUT  # Add timeout to prevent hanging
                            )
                            
                            if response.status_code == 200:
                                data = response.json()
                                st.session_state.access_token = data["access_token"]
                                st.session_state.refresh_token = data["refresh_token"]
                                st.session_state.logged_in = True
                                st.session_state.show_auth_modal = False  # Hide modal after successful login
                                st.session_state.show_login_feedback = True
                                st.session_state.login_feedback_message = "Login successful! Welcome back."
                                st.session_state.login_feedback_type = "success"
                                time.sleep(0.5)  # Shorter pause to show success message
                                st.rerun()
                            elif response.status_code == 401:
                                st.session_state.show_login_feedback = True
                                st.session_state.login_feedback_message = "Invalid email or password. Please try again."
                                st.session_state.login_feedback_type = "error"
                            elif response.status_code == 422:
                                st.session_state.show_login_feedback = True
                                st.session_state.login_feedback_message = "Invalid input format. Please check your email and password."
                                st.session_state.login_feedback_type = "error"
                            elif response.status_code == 504:
                                st.session_state.show_login_feedback = True
                                st.session_state.login_feedback_message = "Server timeout - unable to connect to database. Please try again later."
                                st.session_state.login_feedback_type = "error"
                            else:
                                st.session_state.show_login_feedback = True
                                st.session_state.login_feedback_message = f"Login failed. Status: {response.status_code}. Please try again."
                                st.session_state.login_feedback_type = "error"
                        except requests.exceptions.ConnectionError:
                            st.session_state.show_login_feedback = True
                            st.session_state.login_feedback_message = "Unable to connect to the server. Please check your connection and try again."
                            st.session_state.login_feedback_type = "error"
                        except requests.exceptions.Timeout:
                            st.session_state.show_login_feedback = True
                            st.session_state.login_feedback_message = "Request timed out. Server may be busy. Please try again later."
                            st.session_state.login_feedback_type = "error"
                        except Exception as e:
                            st.session_state.show_login_feedback = True
                            st.session_state.login_feedback_message = "An unexpected error occurred. Please try again later."
                            st.session_state.login_feedback_type = "error"
        
        with tab2:
            with st.form(key="signup_form_modal"):
                signup_email = st.text_input("Email Address", placeholder="Enter your email address", key="modal_signup_email")
                signup_password = st.text_input("Password", type="password", placeholder="Create a password", key="modal_signup_password")
                confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm your password", key="modal_confirm_password")
                signup_submitted = st.form_submit_button("Create Account", use_container_width=True)
            
            if signup_submitted:
                if not signup_email or not signup_password or not confirm_password:
                    st.session_state.show_login_feedback = True
                    st.session_state.login_feedback_message = "Please fill in all fields"
                    st.session_state.login_feedback_type = "error"
                elif signup_password != confirm_password:
                    st.session_state.show_login_feedback = True
                    st.session_state.login_feedback_message = "Passwords do not match. Please try again."
                    st.session_state.login_feedback_type = "error"
                elif len(signup_password) < 6:
                    st.session_state.show_login_feedback = True
                    st.session_state.login_feedback_message = "Password must be at least 6 characters long."
                    st.session_state.login_feedback_type = "error"
                else:
                    # Show immediate feedback
                    with st.spinner("Creating your account... This may take a moment."):
                        try:
                            response = requests.post(
                                f"{API_BASE_URL}/auth/register",
                                json={"email": signup_email, "password": signup_password},
                                timeout=API_TIMEOUT  # Add timeout to prevent hanging
                            )
                            
                            if response.status_code == 200:
                                data = response.json()
                                st.session_state.access_token = data["access_token"]
                                st.session_state.refresh_token = data["refresh_token"]
                                st.session_state.logged_in = True
                                st.session_state.show_auth_modal = False  # Hide modal after successful signup
                                st.session_state.show_login_feedback = True
                                st.session_state.login_feedback_message = "Account created successfully! Welcome to the platform."
                                st.session_state.login_feedback_type = "success"
                                time.sleep(0.5)  # Shorter pause to show success message
                                st.rerun()
                            elif response.status_code == 400:
                                st.session_state.show_login_feedback = True
                                st.session_state.login_feedback_message = "This email is already registered. Please use a different email or try logging in."
                                st.session_state.login_feedback_type = "error"
                            elif response.status_code == 422:
                                st.session_state.show_login_feedback = True
                                st.session_state.login_feedback_message = "Invalid input format. Please check your email and password."
                                st.session_state.login_feedback_type = "error"
                            elif response.status_code == 504:
                                st.session_state.show_login_feedback = True
                                st.session_state.login_feedback_message = "Server timeout - unable to connect to database. Please try again later."
                                st.session_state.login_feedback_type = "error"
                            else:
                                st.session_state.show_login_feedback = True
                                st.session_state.login_feedback_message = f"Account creation failed. Status: {response.status_code}. Please try again."
                                st.session_state.login_feedback_type = "error"
                        except requests.exceptions.ConnectionError:
                            st.session_state.show_login_feedback = True
                            st.session_state.login_feedback_message = "Unable to connect to the server. Please check your connection and try again."
                            st.session_state.login_feedback_type = "error"
                        except requests.exceptions.Timeout:
                            st.session_state.show_login_feedback = True
                            st.session_state.login_feedback_message = "Request timed out. Server may be busy. Please try again later."
                            st.session_state.login_feedback_type = "error"
                        except Exception as e:
                            st.session_state.show_login_feedback = True
                            st.session_state.login_feedback_message = "An unexpected error occurred during account creation. Please try again later."
                            st.session_state.login_feedback_type = "error"

# Main interface - only show when logged in
if st.session_state.logged_in:
    # --- Top navigation bar with title, page tabs, and logout ---
    pages = ["Screener", "Portfolio", "Alerts", "AI Advisor"]
    current_page = st.session_state.get("current_page", "Screener")
    if current_page not in pages:
        # Normalize old lowercase value if present
        current_page = "Screener"

    # Prominent app title (header area)
    st.markdown(
        """
        <div style="
            width: 100%;
            padding: 1rem 0.5rem;
            background-color: #f0f4ff;
            border-radius: 0.5rem;
            margin-bottom: 0.5rem;
        ">
            <div style="
                font-size: 1.8rem;
                font-weight: 800;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin-bottom: 0.1rem;
            ">
                StockScreener Pro
            </div>
            <div style="font-size: 0.9rem; color: #555;">
                Advanced screening, portfolio tracking, alerts, and AI insights.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Navigation row (nav + logout)
    nav_col1, nav_col2 = st.columns([6, 1])

    with nav_col1:
        page = st.radio(
            "",
            pages,
            index=pages.index(current_page),
            horizontal=True,
            label_visibility="collapsed",
        )

    with nav_col2:
        if st.button("Logout", key="logout_btn_top"):
            st.session_state.logged_in = False
            st.session_state.access_token = None
            st.session_state.refresh_token = None
            st.session_state.show_auth_modal = True  # Show modal again after logout
            st.session_state.show_login_feedback = True
            st.session_state.login_feedback_message = "Logged out successfully!"
            st.session_state.login_feedback_type = "success"
            st.rerun()

    # Persist current page selection in session state
    st.session_state.current_page = page

    # Transient login/signup feedback: show briefly, then clear
    if st.session_state.show_login_feedback:
        msg_type = st.session_state.login_feedback_type
        msg_text = st.session_state.login_feedback_message

        if msg_type == "success":
            toast = st.empty()
            toast.success(msg_text)
            time.sleep(2)
            toast.empty()
            st.session_state.show_login_feedback = False
            st.session_state.login_feedback_message = ""
            st.session_state.login_feedback_type = ""
        else:
            # Keep non-success messages visible until next action
            if msg_type == "error":
                st.error(msg_text)
            elif msg_type == "info":
                st.info(msg_text)
            elif msg_type == "warning":
                st.warning(msg_text)

    # Different pages based on navigation
    if page == "Screener":
        st.header("Stock Screener")
        st.caption("Filter stocks based on market criteria and AI analysis.")

        # Initialize helper state for preset queries
        if "screener_query_text" not in st.session_state:
            st.session_state.screener_query_text = ""

        # Example query shortcuts (set preset text, then rerun before input is rendered)
        ex_col1, ex_col2, ex_col3 = st.columns(3)
        with ex_col1:
            if st.button("⭐ Low PE value picks", help="PE < 15 with positive free cash flow"):
                st.session_state.screener_query_text = (
                    "Show me all stocks with PE ratio below 15 and positive free cash flow"
                )
                st.rerun()
        with ex_col2:
            if st.button("🚀 High growth tech", help="IT stocks with strong YoY growth"):
                st.session_state.screener_query_text = (
                    "Show me IT sector stocks with revenue growth above 15 and earnings growth above 10"
                )
                st.rerun()
        with ex_col3:
            if st.button("💰 High dividend", help="Dividend yield focused screen"):
                st.session_state.screener_query_text = "Show me stocks with dividend yield above 4"
                st.rerun()

        # Screener form
        with st.container():
            st.subheader("Screening Criteria")

            col1, col2 = st.columns([2, 1])

            with col1:
                query = st.text_input(
                    "Enter stock query",
                    value=st.session_state.screener_query_text,
                    placeholder="Search by sector, symbol, or description (e.g. 'Tech stocks with high growth')",
                    key="screener_query",
                )

            with col2:
                sector = st.selectbox(
                    "Sector",
                    ["All", "IT", "Finance", "Healthcare", "Energy", "Consumer Discretionary", "Industrials", "Materials", "Utilities"],
                )

            col3, col4, col5 = st.columns(3)

            with col3:
                market_cap = st.selectbox(
                    "Market Cap",
                    ["Any", "Large Cap (>10B)", "Mid Cap (2B-10B)", "Small Cap (<2B)"],
                )

            with col4:
                st.write("")  # Spacer
                st.write("")
                strong_only = st.checkbox("Only strong stocks", value=True)

            with col5:
                st.write("")  # Spacer
                st.write("")
                run_btn = st.button("Run Screener", type="primary", use_container_width=True)

        st.divider()

        # Handle screener action
        if run_btn:
            with st.spinner("Running screener... Analyzing market data..."):
                try:
                    # Call backend screener endpoint designed for frontend compatibility
                    payload = {
                        "query": query or "",
                        "sector": sector,
                        "strong_only": strong_only,
                        "market_cap": market_cap,
                    }
                    resp = make_authenticated_request(
                        "POST",
                        f"{API_BASE_URL}/screener/screen",
                        json=payload,
                    )

                    if resp.status_code == 200:
                        st.session_state.screener_results = resp.json()
                    elif resp.status_code == 401:
                        st.session_state.screener_results = {
                            "status": "error",
                            "message": "You are not authorized. Please log in again.",
                        }
                    else:
                        st.session_state.screener_results = {
                            "status": "error",
                            "message": f"Screener request failed with status {resp.status_code}.",
                        }
                except requests.exceptions.ConnectionError:
                    st.session_state.screener_results = {
                        "status": "error",
                        "message": "Unable to connect to backend screener service. Please ensure the API is running.",
                    }
                except Exception:
                    st.session_state.screener_results = {
                        "status": "error",
                        "message": "Unexpected error while calling the screener service.",
                    }
        
        # Display results if available
        if hasattr(st.session_state, 'screener_results') and st.session_state.screener_results:
            result = st.session_state.screener_results
            status_val = result.get("status")

            if status_val == "success":
                data = result.get("data", [])
                
                if data:
                    st.success(f"Found {len(data)} matching stocks")
                    df = pd.DataFrame(data)

                    # High-level stats row
                    try:
                        c1, c2, c3 = st.columns(3)
                        with c1:
                            st.markdown(
                                '<div class="stat-card"><div class="stat-label">Matches</div>'
                                f'<div class="stat-value">{len(df)}</div></div>',
                                unsafe_allow_html=True,
                            )
                        with c2:
                            avg_pe = float(df["pe_ratio"].mean()) if "pe_ratio" in df.columns else None
                            pe_text = f"{avg_pe:.2f}x" if avg_pe is not None else "—"
                            st.markdown(
                                '<div class="stat-card"><div class="stat-label">Average P/E</div>'
                                f'<div class="stat-value">{pe_text}</div></div>',
                                unsafe_allow_html=True,
                            )
                        with c3:
                            avg_mc = float(df["market_cap"].mean()) if "market_cap" in df.columns else None
                            mc_text = f"${avg_mc/1e9:.2f}B" if avg_mc is not None else "—"
                            st.markdown(
                                '<div class="stat-card"><div class="stat-label">Avg Market Cap</div>'
                                f'<div class="stat-value">{mc_text}</div></div>',
                                unsafe_allow_html=True,
                            )
                    except Exception:
                        pass

                    st.markdown("#### Results")
                    st.dataframe(
                        df, 
                        use_container_width=True, 
                        hide_index=True,
                    )
                else:
                    st.info("No matching stocks found. Try adjusting your filters.")

            elif status_val == "no_data":
                # Backend explicitly indicates no matching rows
                msg = result.get(
                    "message",
                    "No stocks matched your screening criteria. Try loosening one or more filters.",
                )
                st.info(msg)

            elif status_val == "invalid_query":
                # Friendly explanation of why the query was rejected
                msg = result.get(
                    "message",
                    "Your query could not be understood as a valid screener filter. "
                    "Please phrase it as descriptive filters (e.g. 'PE below 15 and positive free cash flow').",
                )
                st.warning(msg)

            elif status_val == "error":
                st.error(result.get("message", "Unknown error occurred"))

            else:
                st.warning("Received unexpected response format from server.")

    elif page == "Portfolio":
        st.header("My Portfolio")
        st.caption("Track your current holdings and performance from the backend.")

        # Fetch portfolio summary
        summary = None
        try:
            resp = make_authenticated_request("GET", f"{API_BASE_URL}/portfolio/summary")
            if resp.status_code == 200:
                summary = resp.json()
        except Exception:
            summary = None

        with st.container():
            col1, col2 = st.columns([3, 1])
            with col1:
                if summary:
                    total_value = summary.get("total_value", 0.0)
                    portfolio_return = summary.get("portfolio_return", 0.0)
                    st.metric(
                        label="Total Portfolio Value",
                        value=f"${total_value:,.2f}",
                        delta=f"{portfolio_return:.2f}%",
                    )
                else:
                    st.metric(label="Total Portfolio Value", value="—", delta="—")
            with col2:
                if st.button("🔄 Refresh Data"):
                    st.rerun()

        st.divider()

        # --- Add holdings form ---
        st.subheader("Add Holding")
        with st.form("add_portfolio_holding"):
            c1, c2, c3 = st.columns(3)
            with c1:
                symbol_input = st.text_input("Symbol", placeholder="e.g. AAPL, MSFT")
            with c2:
                quantity_input = st.number_input("Shares", min_value=1, step=1, value=1)
            with c3:
                price_input = st.number_input(
                    "Avg Purchase Price",
                    min_value=0.0,
                    step=0.01,
                    format="%.2f",
                )

            add_submitted = st.form_submit_button("Add to Portfolio")

            if add_submitted:
                if not symbol_input.strip():
                    st.error("Please enter a stock symbol.")
                elif price_input <= 0:
                    st.error("Please enter a positive average purchase price.")
                else:
                    try:
                        payload = {
                            "symbol": symbol_input.strip().upper(),
                            "quantity": int(quantity_input),
                            "avg_purchase_price": float(price_input),
                        }
                        resp = make_authenticated_request(
                            "POST",
                            f"{API_BASE_URL}/portfolio/add-by-symbol",
                            json=payload,
                        )
                        if resp.status_code == 200:
                            st.success(resp.json().get("message", "Added holding to portfolio."))
                            st.rerun()
                        else:
                            try:
                                detail = resp.json().get("detail", f"Status {resp.status_code}")
                            except Exception:
                                detail = f"Status {resp.status_code}"
                            st.error(f"Failed to add holding: {detail}")
                    except Exception as e:
                        st.error(f"Unexpected error while adding holding: {str(e)}")

        st.divider()

        st.subheader("Holdings")

        # Fetch portfolio holdings
        try:
            resp = make_authenticated_request("GET", f"{API_BASE_URL}/portfolio/")
            if resp.status_code == 200:
                holdings = resp.json()
            else:
                holdings = []
        except Exception:
            holdings = []

        if holdings:
            df = pd.DataFrame(holdings)
            # Normalize column names for display
            df_display = df.rename(
                columns={
                    "symbol": "Symbol",
                    "company_name": "Company",
                    "quantity": "Shares",
                    "avg_purchase_price": "Avg Price",
                    "current_price": "Current Price",
                    "total_value": "Total Value",
                }
            )
            st.dataframe(
                df_display,
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No holdings found in your portfolio yet.")

    elif page == "Alerts":
        st.header("Price Alerts")
        st.caption("Manage your stock price alerts stored in the backend.")

        # Create Alert Form
        with st.form("create_alert_form"):
            st.subheader("Create New Alert")
            c1, c2, c3 = st.columns(3)

            with c1:
                stock_id = st.text_input("Stock ID", placeholder="Internal stock ID (e.g. UUID)")
            with c2:
                condition = st.selectbox("Condition", ["Above Price", "Below Price"])
            with c3:
                value = st.number_input("Price Value", min_value=0.0, step=0.01)

            submitted = st.form_submit_button("Create Alert")

            if submitted:
                if stock_id and value > 0:
                    cond_type = "ABOVE_PRICE" if "Above" in condition else "BELOW_PRICE"
                    try:
                        resp = make_authenticated_request(
                            "POST",
                            f"{API_BASE_URL}/alerts/create",
                            json={
                                "stock_id": stock_id,
                                "condition_type": cond_type,
                                "condition_value": value,
                            },
                        )
                        if resp.status_code == 200:
                            st.success(f"Alert set for stock {stock_id} {condition} ${value}")
                        else:
                            st.error(f"Failed to create alert (status {resp.status_code}).")
                    except Exception:
                        st.error("Unexpected error while creating alert.")
                else:
                    st.warning("Please enter a valid stock ID and price.")

        st.divider()

        st.subheader("Active Alerts")
        try:
            resp = make_authenticated_request("GET", f"{API_BASE_URL}/alerts/")
            if resp.status_code == 200:
                alerts = resp.json()
            else:
                alerts = []
        except Exception:
            alerts = []

        if alerts:
            df_alerts = pd.DataFrame(alerts)
            st.dataframe(df_alerts, use_container_width=True, hide_index=True)
        else:
            st.info("No active alerts.")
    
    elif page == "AI Advisor":
        st.header("AI Stock Advisor")
        st.caption("Ask investment questions and get AI-powered, informational responses.")

        # Small inline helper
        st.markdown(
            '<div class="chat-hint">💡 Try asking about risk, sectors, or valuation multiples.</div>',
            unsafe_allow_html=True,
        )

        # Ensure chat history and cache exist
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []
        if "ai_cache" not in st.session_state:
            st.session_state.ai_cache = {}

        # Helper to append a Q&A pair and rerun
        def _handle_ai_question(question_text: str):
            question = question_text.strip()
            if not question:
                return

            normalized_key = question.lower()
            st.session_state.chat_history.append({"role": "user", "content": question})

            if normalized_key in st.session_state.ai_cache:
                bot_response = st.session_state.ai_cache[normalized_key]
            else:
                bot_response = ask_ai_advisor(question)
                st.session_state.ai_cache[normalized_key] = bot_response

            st.session_state.chat_history.append({"role": "assistant", "content": bot_response})
            st.rerun()

        # Quick suggestion buttons
        s1, s2, s3 = st.columns(3)
        with s1:
            if st.button("Safer dividend ideas"):
                _handle_ai_question(
                    "Suggest some lower-risk dividend-focused stocks and what metrics to look at."
                )
        with s2:
            if st.button("Compare two stocks"):
                _handle_ai_question(
                    "Compare AAPL vs MSFT from a long-term investor perspective."
                )
        with s3:
            if st.button("Sector outlook"):
                _handle_ai_question(
                    "What is the outlook for the global semiconductor sector over the next few years?"
                )

        # Display chat history (last 20 messages)
        for message in st.session_state.chat_history[-20:]:
            with st.chat_message(message["role"]):
                st.write(message["content"])

        # Free-form chat input at the bottom
        prompt = st.chat_input(
            "Ask about stocks, sectors, risk, valuation, or portfolio ideas..."
        )
        if prompt:
            _handle_ai_question(prompt)

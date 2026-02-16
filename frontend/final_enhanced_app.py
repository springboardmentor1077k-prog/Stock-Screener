import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import json
import time
from datetime import datetime

# --- Configuration ---
BACKEND_URL = "http://localhost:8002/api/v1"
PAGE_TITLE = "AI-Powered Stock Screener & Advisory Platform"
PAGE_ICON = "📈"

# --- Constants ---
import os
API_TIMEOUT = int(os.getenv("FRONTEND_API_TIMEOUT", "10"))
HEALTH_CHECK_TIMEOUT = int(os.getenv("FRONTEND_HEALTH_CHECK_TIMEOUT", "5"))

# --- Page Setup ---
st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=PAGE_ICON,
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- STYLING (Glass-morphism UI from original app with professional dark theme) ---
st.markdown("""
<style>
    /* Clean, minimal styling */
    body {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* Simple button styling */
    .btn-logout {
        background: #ff5252;
        color: white;
        border: none;
        border-radius: 4px;
        padding: 0.5rem 1rem;
    }
    
    .btn-logout:hover {
        background: #d32f2f;
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
    
    /* Glass-morphism effect for cards */
    .glass-card {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 1.5rem;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        margin-bottom: 1rem;
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

# --- Utility Functions ---
def make_authenticated_request(method, url, json=None, params=None):
    """Make authenticated requests with automatic token refresh."""
    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    
    if method.upper() == "GET":
        response = requests.get(url, headers=headers, params=params, timeout=API_TIMEOUT)
    elif method.upper() == "POST":
        response = requests.post(url, headers=headers, json=json, timeout=API_TIMEOUT)
    elif method.upper() == "PUT":
        response = requests.put(url, headers=headers, json=json, timeout=API_TIMEOUT)
    elif method.upper() == "DELETE":
        response = requests.delete(url, headers=headers, timeout=API_TIMEOUT)
    
    # If unauthorized, try to refresh token
    if response.status_code == 401 and st.session_state.refresh_token:
        refresh_response = requests.post(
            f"{BACKEND_URL}/auth/refresh",
            json={"refresh_token": st.session_state.refresh_token},
            timeout=API_TIMEOUT
        )
        
        if refresh_response.status_code == 200:
            token_data = refresh_response.json()
            st.session_state.token = token_data['access_token']
            st.session_state.refresh_token = token_data['refresh_token']
            
            # Retry the original request with new token
            headers = {"Authorization": f"Bearer {st.session_state.token}"}
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, params=params, timeout=API_TIMEOUT)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, json=json, timeout=API_TIMEOUT)
            elif method.upper() == "PUT":
                response = requests.put(url, headers=headers, json=json, timeout=API_TIMEOUT)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=headers, timeout=API_TIMEOUT)
        else:
            # If refresh failed, log out user
            st.session_state.authenticated = False
            st.session_state.token = None
            st.session_state.refresh_token = None
            st.error("Session expired. Please log in again.")
            st.rerun()
    
    return response

def get_quarterly_data(symbol):
    """Fetch quarterly financial data for a given stock symbol if available."""
    if not st.session_state.token:
        return None
        
    try:
        # Attempt to get quarterly financial data from the data API
        response = make_authenticated_request("GET", f"{BACKEND_URL}/data/income_statement/{symbol}")
        
        if response.status_code == 200:
            data = response.json()
            if 'income_statement' in data and 'quarterlyReports' in data['income_statement']:
                quarterly_reports = data['income_statement']['quarterlyReports']
                # Format the quarterly data to match what the frontend expects
                formatted_data = []
                for report in quarterly_reports[:8]:  # Get last 8 quarters
                    formatted_report = {
                        'quarter': report.get('fiscalDateEnding', ''),
                        'year': report.get('fiscalDateEnding', '')[:4],
                        'revenue': float(report.get('totalRevenue', 0)) if report.get('totalRevenue') else 0,
                        'ebitda': float(report.get('ebitda', 0)) if report.get('ebitda') else 0,
                        'net_profit': float(report.get('netIncome', 0)) if report.get('netIncome') else 0,
                        'gross_margin': float(report.get('grossProfit', 0)) if report.get('grossProfit') else 0,
                        'operating_income': float(report.get('operatingIncome', 0)) if report.get('operatingIncome') else 0,
                        'symbol': symbol
                    }
                    formatted_data.append(formatted_report)
                
                return formatted_data
        
        return None
    except Exception as e:
        st.warning(f"Could not fetch quarterly data for {symbol}: {str(e)}")
        return None

def check_backend_connection():
    """Check if backend is running."""
    try:
        response = requests.get(f"{BACKEND_URL}/docs", timeout=HEALTH_CHECK_TIMEOUT)
        return response.status_code == 200
    except:
        return False

def init_local_storage():
    """Initialize local storage for offline functionality."""
    if 'portfolio' not in st.session_state:
        st.session_state.portfolio = pd.DataFrame([
            {"Symbol": "MSFT", "Shares": 10, "Avg Price": 305.50, "Current Price": 402.10, "Return": "+31.6%"},
            {"Symbol": "GOOGL", "Shares": 5, "Avg Price": 120.00, "Current Price": 145.30, "Return": "+21.1%"},
            {"Symbol": "NVDA", "Shares": 20, "Avg Price": 450.00, "Current Price": 720.50, "Return": "+60.1%"}
        ])
    
    if 'alerts' not in st.session_state:
        st.session_state.alerts = [
            {"Symbol": "AAPL", "Condition": "Above", "Value": 180.0, "Status": "Active"},
            {"Symbol": "TSLA", "Condition": "Below", "Value": 200.0, "Status": "Active"}
        ]
    
    if 'screener_results' not in st.session_state:
        st.session_state.screener_results = None
    
    if 'messages' not in st.session_state:
        st.session_state.messages = []

# --- Session State Initialization ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "token" not in st.session_state:
    st.session_state.token = None
if "refresh_token" not in st.session_state:
    st.session_state.refresh_token = None
if "user_email" not in st.session_state:
    st.session_state.user_email = None
if "user_name" not in st.session_state:
    st.session_state.user_name = None
if "current_page" not in st.session_state:
    st.session_state.current_page = "Screener"
if "show_auth_modal" not in st.session_state:
    st.session_state.show_auth_modal = not st.session_state.get('authenticated', False)

if "login_feedback_message" not in st.session_state:
    st.session_state.login_feedback_message = ""
if "login_feedback_type" not in st.session_state:
    st.session_state.login_feedback_type = ""

init_local_storage()

if "alerts" not in st.session_state:
    # Initialize with some dummy alerts
    st.session_state.alerts = [
        {"Symbol": "AAPL", "Condition": "Above", "Value": 180.0, "Status": "Active"},
        {"Symbol": "TSLA", "Condition": "Below", "Value": 200.0, "Status": "Active"}
    ]

if "portfolio" not in st.session_state:
    # Initialize with sample portfolio data
    st.session_state.portfolio = pd.DataFrame([
        {"Symbol": "MSFT", "Shares": 10, "Avg Price": 305.50, "Current Price": 402.10, "Return": "+31.6%"},
        {"Symbol": "GOOGL", "Shares": 5, "Avg Price": 120.00, "Current Price": 145.30, "Return": "+21.1%"},
        {"Symbol": "NVDA", "Shares": 20, "Avg Price": 450.00, "Current Price": 720.50, "Return": "+60.1%"}
    ])

if "screener_results" not in st.session_state:
    st.session_state.screener_results = None

# --- Authentication Functions ---
def login_user(email, password):
    """Login user and get token with comprehensive error handling and refresh token."""
    if not check_backend_connection():
        return False, "Backend server is not running! Please start the backend server first."
    
    try:
        response = requests.post(f"{BACKEND_URL}/auth/login", json={
            "email": email,
            "password": password
        }, timeout=API_TIMEOUT)
        
        if response.status_code == 200:
            data = response.json()
            st.session_state.authenticated = True
            st.session_state.token = data.get('access_token', data.get('token'))
            st.session_state.refresh_token = data.get('refresh_token')
            st.session_state.user_email = email
            st.session_state.user_name = email.split('@')[0]  # Use email prefix as name
            st.session_state.show_auth_modal = False  # Hide modal after successful login
            return True, "Login successful!"
        elif response.status_code == 401:
            return False, "Invalid credentials. Please check your email and password."
        elif response.status_code == 422:
            return False, "Invalid input format. Please check your email and password."
        elif response.status_code == 504:
            return False, "Server timeout - unable to connect to database. Please try again later."
        else:
            try:
                error_data = response.json()
                return False, error_data.get('detail', f'Login failed with status {response.status_code}')
            except:
                return False, f"Login failed with status {response.status_code}"
    except requests.exceptions.Timeout:
        return False, "Request timed out. The server might be busy. Please try again."
    except requests.exceptions.ConnectionError:
        return False, "Cannot connect to server. Please make sure the backend is running."
    except requests.exceptions.JSONDecodeError:
        return False, "Server returned invalid response"
    except Exception as e:
        return False, f"Connection error: {str(e)}"

def signup_user(name, email, password):
    """Sign up new user and get token with comprehensive error handling and refresh token."""
    if not check_backend_connection():
        return False, "Backend server is not running! Please start the backend server first."
    
    try:
        response = requests.post(f"{BACKEND_URL}/auth/register", json={
            "email": email,
            "password": password
        }, timeout=API_TIMEOUT)
        
        if response.status_code == 200:
            data = response.json()
            st.session_state.authenticated = True
            st.session_state.token = data.get('access_token', data.get('token'))
            st.session_state.refresh_token = data.get('refresh_token')
            st.session_state.user_email = email
            st.session_state.user_name = name
            st.session_state.show_auth_modal = False  # Hide modal after successful signup
            return True, "Signup successful!"
        elif response.status_code == 400:
            return False, "This email is already registered. Please use a different email or try logging in."
        elif response.status_code == 422:
            return False, "Invalid input format. Please check your email and password."
        elif response.status_code == 504:
            return False, "Server timeout - unable to connect to database. Please try again later."
        else:
            try:
                error_data = response.json()
                return False, error_data.get('detail', f'Signup failed with status {response.status_code}')
            except:
                return False, f"Signup failed with status {response.status_code}"
    except requests.exceptions.Timeout:
        return False, "Request timed out. The server might be busy. Please try again."
    except requests.exceptions.ConnectionError:
        return False, "Cannot connect to server. Please make sure the backend is running."
    except requests.exceptions.JSONDecodeError:
        return False, "Server returned invalid response"
    except Exception as e:
        return False, f"Connection error: {str(e)}"

def logout_user():
    """Logout user and clear session."""
    st.session_state.authenticated = False
    st.session_state.token = None
    st.session_state.refresh_token = None
    st.session_state.user_email = None
    st.session_state.user_name = None
    st.session_state.current_page = "Screener"
    st.session_state.show_auth_modal = True  # Show modal again after logout
    st.session_state.show_login_feedback = True
    st.session_state.login_feedback_message = "Logged out successfully!"
    st.session_state.login_feedback_type = "success"

# --- Helper Functions ---
def run_screener(query, sector="All", strong_only=True, market_cap="Any"):
    """
    Calls the backend API to screen stocks based on criteria.
    Enhanced with error handling from Vidish branch and additional validation.
    """
    # Validate inputs
    if not query or not query.strip():
        return {"status": "error", "message": "Please enter a query"}
    
    payload = {
        "query": query.strip(),
        "sector": sector,
        "strong_only": strong_only,
        "market_cap": market_cap
    }
    
    # Check backend connection first
    if not check_backend_connection():
        return {"status": "error", "message": "Backend server is not running! Please start the backend server first."}
    
    if not st.session_state.token:
        return {"status": "error", "message": "No authentication token. Please login again."}
    
    try:
        response = make_authenticated_request("POST", f"{BACKEND_URL}/screen", json=payload)
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 400:
            try:
                error_data = response.json()
                return {"status": "error", "message": error_data.get('detail', 'Invalid query')}
            except:
                return {"status": "error", "message": "Invalid query format"}
        elif response.status_code == 401:
            st.session_state.authenticated = False
            return {"status": "error", "message": "Session expired. Please login again."}
        elif response.status_code == 500:
            try:
                error_data = response.json()
                error_detail = error_data.get('detail', 'Server error')
                if "Database query error" in error_detail:
                    return {"status": "error", "message": "Database connection issue. Please try again."}
                return {"status": "error", "message": f"Server error: {error_detail}"}
            except:
                return {"status": "error", "message": "Server error occurred"}
        else:
            try:
                error_data = response.json()
                return {"status": "error", "message": error_data.get('detail', f'Backend error (status {response.status_code})')} 
            except:
                return {"status": "error", "message": f'Backend error (status {response.status_code})'}
                
    except requests.exceptions.Timeout:
        return {"status": "error", "message": "Query timed out. The database might be processing a complex request. Please try again."}
    except requests.exceptions.ConnectionError:
        return {"status": "error", "message": "Cannot connect to server. Please check if the backend is running."}
    except requests.exceptions.RequestException as e:
        return {"status": "error", "message": f"Error fetching data: {str(e)}"}
    except Exception as e:
        return {"status": "error", "message": f"Unexpected error: {str(e)}"}

def get_portfolio_data(include_quarterly=False):
    """Get portfolio data with enhanced error handling."""
    if not check_backend_connection():
        return False, "Backend server is not running! Please start the backend server first."
        
    if not st.session_state.token:
        return False, "No authentication token. Please login again."
        
    try:
        if include_quarterly:
            # Use the new endpoint that includes quarterly data
            response = make_authenticated_request("GET", f"{BACKEND_URL}/portfolio/with-quarterly-data")
        else:
            response = make_authenticated_request("GET", f"{BACKEND_URL}/portfolio/")
        
        if response.status_code == 200:
            return True, response.json()
        elif response.status_code == 401:
            st.session_state.authenticated = False
            return False, "Session expired. Please login again."
        else:
            return False, f"Failed to fetch portfolio (status: {response.status_code})"
    except requests.exceptions.Timeout:
        return False, "Request timed out. Please try again."
    except Exception as e:
        return False, f"Error: {str(e)}"

def create_portfolio(name):
    """Create a new portfolio with enhanced error handling."""
    if not check_backend_connection():
        return False, "Backend server is not running! Please start the backend server first."
        
    if not st.session_state.token:
        return False, "No authentication token. Please login again."
        
    try:
        response = make_authenticated_request("POST", f"{BACKEND_URL}/portfolio/", 
                               json={"name": name})
        
        if response.status_code == 200:
            return True, "Portfolio created successfully"
        elif response.status_code == 401:
            st.session_state.authenticated = False
            return False, "Session expired. Please login again."
        elif response.status_code == 400:
            return False, "Invalid portfolio name. Please try a different name."
        else:
            return False, f"Failed to create portfolio (status: {response.status_code})"
    except requests.exceptions.Timeout:
        return False, "Request timed out. Please try again."
    except Exception as e:
        return False, f"Error: {str(e)}"

# --- Page Renderers ---

def render_login_signup():
    """Enhanced login/signup page with tabs from multiple branches."""
    st.markdown('<div class="card"><h2>🔒 Secure Access</h2></div>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    
    with tab1:
        with st.form("login_form"):
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_password")
            login_button = st.form_submit_button("Login", type="primary")
            
            if login_button:
                if email and password:
                    with st.spinner("Authenticating..."):
                        success, message = login_user(email, password)
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
                else:
                    st.error("Please enter both email and password")
    
    with tab2:
        with st.form("signup_form"):
            name = st.text_input("Full Name", key="signup_name")
            email = st.text_input("Email", key="signup_email_reg")
            password = st.text_input("Password", type="password", key="signup_password_reg", 
                                   help="Password should be 6-50 characters long")
            signup_button = st.form_submit_button("Sign Up")
            
            if signup_button:
                if name and email and password:
                    if len(name.strip()) == 0:
                        st.error("Please enter your full name")
                    elif len(password) < 6:
                        st.error("Password must be at least 6 characters long")
                    elif len(password) > 50:
                        st.error("Password is too long (maximum 50 characters)")
                    elif '@' not in email:
                        st.error("Please enter a valid email address")
                    else:
                        success, message = signup_user(name.strip(), email.strip(), password)
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
                else:
                    st.error("Please fill in all fields")

def render_screener_page():
    """Enhanced screener page with features from multiple branches."""
    st.header("🔍 AI-Powered Stock Screener")
    st.caption("Filter stocks based on market criteria and AI analysis.")

    # --- Step 1: Query Input Section ---
    st.subheader("Screening Criteria")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        query = st.text_input(
            "Enter stock query", 
            placeholder="Search by sector, symbol, or description (e.g. 'Tech stocks with high growth' or 'PE ratio < 15 AND dividend > 3%')",
            help="Try queries like 'Technology stocks with PE less than 20' or 'Large cap stocks with dividend yield above 2%'"
        )
    
    with col2:
        sector = st.selectbox(
            "Sector", 
            ["All", "IT", "Finance", "Healthcare", "Energy", "Consumer Discretionary", "Industrials", "Materials", "Utilities"]
        )
        
    col3, col4, col5 = st.columns(3)
    
    with col3:
        market_cap = st.selectbox(
            "Market Cap", 
            ["Any", "Large Cap (>10B)", "Mid Cap (2B-10B)", "Small Cap (<2B)"]
        )
        
    with col4:
        st.write("") # Spacer
        st.write("") 
        strong_only = st.checkbox("Only strong stocks", value=True)
        
    with col5:
        st.write("") # Spacer
        st.write("")
        run_btn = st.button("🚀 Run Screener", type="primary", use_container_width=True)

    st.divider()

    # --- Step 2 & 3: Action & Loading ---
    if run_btn:
        with st.spinner("Running screener... Analyzing market data..."):
            # Simulate a small delay for better UX if backend is instant, or actual wait
            # time.sleep(0.5) 
            
            result = run_screener(query, sector, strong_only, market_cap)
            
            # Store result in session state
            st.session_state.screener_results = result

    # --- Step 4: Handle Responses ---
    if st.session_state.screener_results:
        result = st.session_state.screener_results
        
        if result.get("status") == "success":
            data = result.get("data", [])
            
            if data:
                st.success(f"Found {len(data)} matching stocks")
                
                # Create a clean dataframe for display
                df = pd.DataFrame(data)
                
                # Enhanced display with metrics from Aarya_Tehare branch
                if len(df) > 0:
                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("Matches", len(df))
                    if 'pe_ratio' in df.columns:
                        m2.metric("Avg PE", f"{df['pe_ratio'].mean():.2f}")
                    if 'dividend_yield' in df.columns:
                        m4.metric("Avg Div Yield", f"{df['dividend_yield'].mean():.2f}%")
                    
                    # Check for analyst data
                    upside = "N/A"
                    if "analyst_upside" in df.columns and not df["analyst_upside"].dropna().empty:
                        upside = f"{df['analyst_upside'].mean():.1f}%"
                    m3.metric("Avg Upside", upside)
                
                # Tabs for different views from Aarya_Tehare branch
                t1, t2, t3, t4, t5 = st.tabs([
                    "📋 Results", 
                    "🎯 Targets", 
                    "📊 Visuals", 
                    "🧠 AI Insight", 
                    "🔧 Logic"
                ])
                
                # TAB 1: Results
                with t1:
                    st.caption("Fundamental Data")
                    essential_columns = ['symbol', 'company_name', 'current_price', 'pe_ratio', 'market_cap', 'recommendation', 'upside_category']
                    available_columns = []
                    for col in essential_columns:
                        if col in df.columns:
                            available_columns.append(col)
                    df_display = df[available_columns] if available_columns else df
                    
                    column_mapping = {
                        'symbol': 'Symbol',
                        'company_name': 'Company',
                        'pe_ratio': 'P/E',
                        'market_cap': 'Market Cap',
                        'current_price': 'Price',
                        'recommendation': 'Rating',
                        'upside_category': 'Upside Type'
                    }
                    
                    rename_dict = {k: v for k, v in column_mapping.items() if k in df_display.columns}
                    df_display = df_display.rename(columns=rename_dict)
                    
                    if 'P/E' in df_display.columns:
                        df_display['P/E'] = df_display['P/E'].apply(lambda x: f"{x:.1f}" if pd.notnull(x) and x > 0 else "N/A")
                    if 'Market Cap' in df_display.columns:
                        df_display['Market Cap'] = df_display['Market Cap'].apply(lambda x: f"${x/1e9:.1f}B" if pd.notnull(x) and x > 0 else "N/A")
                    if 'Price' in df_display.columns:
                        df_display['Price'] = df_display['Price'].apply(lambda x: f"${x:.2f}" if pd.notnull(x) and x > 0 else "N/A")
                    
                    def style_upside_category(val):
                        if val == 'Strong Upside':
                            return 'background-color: #d4edda; color: #155724' 
                        elif val == 'Moderate Upside':
                            return 'background-color: #fff3cd; color: #856404' 
                        elif val == 'Target Below Price':
                            return 'background-color: #f8d7da; color: #721c24' 
                        return ''
                    
                    if 'Upside Type' in df_display.columns:
                        styled_df = df_display.style.applymap(style_upside_category, subset=['Upside Type'])
                        st.dataframe(styled_df, use_container_width=True, hide_index=True)
                    else:
                        st.dataframe(df_display, use_container_width=True, hide_index=True)
                
                # TAB 2: ANALYST TARGETS
                with t2:
                    st.caption("Analyst Forecasts")
                    target_cols = ["symbol", "current_price", "avg_target", "analyst_rating", "analyst_upside"]
                    
                    if "analyst_rating" in df.columns:
                        display_df = df.copy()
                        if 'current_price' in display_df.columns:
                            display_df['current_price'] = display_df['current_price'].apply(lambda x: f"${x:.2f}" if pd.notnull(x) and x > 0 else "N/A")
                        if 'avg_target' in display_df.columns:
                            display_df['avg_target'] = display_df['avg_target'].apply(lambda x: f"${x:.2f}" if pd.notnull(x) and x > 0 else "N/A")
                        if 'analyst_upside' in display_df.columns:
                            display_df['analyst_upside'] = display_df['analyst_upside'].apply(lambda x: f"{x:.1f}%" if pd.notnull(x) else "N/A")
                        
                        st.dataframe(
                            display_df[target_cols],
                            column_config={
                                "current_price": st.column_config.NumberColumn("Current", format="$%.2f"),
                                "avg_target": st.column_config.NumberColumn("Target", format="$%.2f"),
                                "analyst_upside": st.column_config.ProgressColumn("Upside", format="%.1f%%", min_value=-20, max_value=50),
                            },
                            hide_index=True,
                            use_container_width=True
                        )
                    else:
                        st.warning("No analyst data found.")
                
                # TAB 3: CHARTS
                with t3:
                    c1, c2 = st.columns(2)
                    with c1:
                        if 'sector' in df.columns:
                            fig = px.pie(df, names="sector", title="Sector Split", hole=0.4)
                            st.plotly_chart(fig, use_container_width=True)
                    with c2:
                        if "analyst_upside" in df.columns:
                            fig = px.bar(df, x="symbol", y="analyst_upside", title="Upside Potential")
                            st.plotly_chart(fig, use_container_width=True)
                
                # TAB 4: AI INSIGHTS (from Sprint 1 branch)
                with t4:
                    if st.button("Generate AI Report"):
                        with st.spinner("Generating AI Insights..."):
                            try:
                                if not check_backend_connection():
                                    st.error("Backend server is not running. Cannot generate AI insights.")
                                else:
                                    payload = {
                                        "sector_summary": df["sector"].value_counts().to_dict() if 'sector' in df.columns else {},
                                        "avg_pe": float(df["pe_ratio"].mean()) if 'pe_ratio' in df.columns and not df["pe_ratio"].empty else 0.0,
                                        "avg_peg": float(df["peg_ratio"].mean()) if 'peg_ratio' in df.columns and not df["peg_ratio"].empty else 0.0,
                                        "avg_dividend": float(df["dividend_yield"].mean()) if 'dividend_yield' in df.columns and not df["dividend_yield"].empty else 0.0
                                    }
                                    exp = make_authenticated_request("POST", f"{BACKEND_URL}/explain-results", 
                                                      json=payload)
                                    
                                    if exp.status_code == 200:
                                        st.success("Analysis Complete")
                                        explanation = exp.json().get("explanation", "No explanation provided")
                                        st.markdown(
                                            f'<div class="ai-box">{explanation}</div>',
                                            unsafe_allow_html=True
                                        )
                                    elif exp.status_code == 401:
                                        st.session_state.authenticated = False
                                        st.error("Session expired. Please login again.")
                                        st.rerun()
                                    else:
                                        try:
                                            error_detail = exp.json().get("detail", "AI service error")
                                            st.error(f"AI Service Error: {error_detail}")
                                        except:
                                            st.error(f"AI Service Error (status: {exp.status_code})")
                            except requests.exceptions.Timeout:
                                st.error("AI report generation timed out. Please try again.")
                            except requests.exceptions.ConnectionError:
                                st.error("Cannot connect to AI service. Please check if the backend is running.")
                            except Exception as e:
                                st.error(f"Error generating AI report: {str(e)}")
                
                # TAB 5: DEBUG LOGIC
                with t5:
                    if 'dsl' in result:
                        st.markdown(
                            f'<div class="dsl-box">{json.dumps(result["dsl"], indent=2)}</div>',
                            unsafe_allow_html=True
                        )
                    else:
                        st.info("DSL information not available")
            
            # Display quarterly financial data if available (from Vidish branch)
            if "quarterly_data" in result and result["quarterly_data"]:
                st.subheader("📊 Quarterly Financial Data")
                
                quarterly_data = result["quarterly_data"]
                if quarterly_data and isinstance(quarterly_data, dict):
                    symbols_with_data = []
                    for stock_id, quarters in quarterly_data.items():
                        if quarters and isinstance(quarters, list) and len(quarters) > 0:
                            if 'symbol' in quarters[0]:
                                symbols_with_data.append(quarters[0]['symbol'])
                    
                    if symbols_with_data:
                        if len(symbols_with_data) <= 5:
                            tabs = st.tabs(symbols_with_data)
                            
                            for i, symbol in enumerate(symbols_with_data):
                                with tabs[i]:
                                    symbol_quarters = None
                                    for stock_id, quarters in quarterly_data.items():
                                        if quarters and len(quarters) > 0 and quarters[0].get('symbol') == symbol:
                                            symbol_quarters = quarters
                                            break
                            
                                    if symbol_quarters:
                                        try:
                                            quarterly_df = pd.DataFrame(symbol_quarters)
                                            required_cols = ['quarter', 'year', 'revenue', 'ebitda', 'net_profit', 'gross_margin', 'operating_income']
                                            available_cols = [col for col in required_cols if col in quarterly_df.columns]
                                            
                                            if available_cols:
                                                quarterly_df = quarterly_df[available_cols]                                                        
                                                for col in ['revenue', 'ebitda', 'net_profit', 'gross_margin', 'operating_income']:
                                                    if col in quarterly_df.columns:
                                                        quarterly_df[col] = quarterly_df[col].apply(
                                                            lambda x: f"${x:,.0f}" if pd.notnull(x) and x != 0 else "N/A"
                                                        )
                                                        
                                                col_mapping = {
                                                    'quarter': 'Quarter',
                                                    'year': 'Year', 
                                                    'revenue': 'Revenue',
                                                    'ebitda': 'EBITDA',
                                                    'net_profit': 'Net Profit',
                                                    'gross_margin': 'Gross Margin',
                                                    'operating_income': 'Operating Income'
                                                }
                                                quarterly_df = quarterly_df.rename(columns={k: v for k, v in col_mapping.items() if k in quarterly_df.columns})
                                                st.dataframe(quarterly_df, use_container_width=True)
                                            else:
                                                st.warning(f"No quarterly data available for {symbol}")
                                        except Exception as e:
                                            st.error(f"Error displaying data for {symbol}: {str(e)}")
                        else:
                            for stock_id, quarters in quarterly_data.items():
                                if quarters and len(quarters) > 0:
                                    symbol = quarters[0].get('symbol', f'Stock {stock_id}')
                                    with st.expander(f"📈 {symbol} - Quarterly Data"):
                                        try:
                                            quarterly_df = pd.DataFrame(quarters)
                                            required_cols = ['quarter', 'year', 'revenue', 'ebitda', 'net_profit', 'gross_margin', 'operating_income']
                                            available_cols = [col for col in required_cols if col in quarterly_df.columns]
                                            
                                            if available_cols:
                                                quarterly_df = quarterly_df[available_cols]                                                        
                                                for col in ['revenue', 'ebitda', 'net_profit', 'gross_margin', 'operating_income']:
                                                    if col in quarterly_df.columns:
                                                        quarterly_df[col] = quarterly_df[col].apply(
                                                            lambda x: f"${x:,.0f}" if pd.notnull(x) and x != 0 else "N/A"
                                                        )
                                                col_mapping = {
                                                    'quarter': 'Quarter',
                                                    'year': 'Year', 
                                                    'revenue': 'Revenue',
                                                    'ebitda': 'EBITDA',
                                                    'net_profit': 'Net Profit',
                                                    'gross_margin': 'Gross Margin',
                                                    'operating_income': 'Operating Income'
                                                }
                                                quarterly_df = quarterly_df.rename(columns={k: v for k, v in col_mapping.items() if k in quarterly_df.columns})
                                                st.dataframe(quarterly_df, use_container_width=True)
                                            else:
                                                st.warning(f"No quarterly data available for {symbol}")
                                        except Exception as e:
                                            st.error(f"Error displaying data for {symbol}: {str(e)}")
                    else:
                        st.info("No quarterly data available for the selected stocks")
                else:
                    st.info("No quarterly data available")
            else:
                st.info("No matching stocks found. Try adjusting your filters.")
                
        elif result.get("status") == "error":
            st.error(result.get("message", "Unknown error occurred"))
            # Provide helpful suggestions from Vidish branch
            if "data we don't have" in result.get("message", "").lower() or "unsupported" in result.get("message", "").lower():
                st.info("💡 Try: `PE ratio > 15` or `positive profit last 4 quarters`")
        else:
            st.warning("Received unexpected response format from server.")

def render_portfolio_page():
    """Enhanced portfolio page with features from Vidish branch."""
    st.header("💼 My Portfolio")
    st.caption("Track your current holdings and performance.")
    
    # Portfolio metrics from Vidish branch
    if check_backend_connection() and st.session_state.token:
        try:
            summary_response = make_authenticated_request("GET", f"{BACKEND_URL}/portfolio/summary")
            if summary_response.status_code == 200:
                summary = summary_response.json()
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Portfolios", summary.get('total_portfolios', 0))
                with col2:
                    st.metric("Total Holdings", summary.get('total_holdings', 0))
                with col3:
                    invested = summary.get('total_invested', 0)
                    st.metric("Total Invested", f"${invested:,.2f}" if invested else "$0.00")
                with col4:
                    current_value = summary.get('current_value', 0)
                    st.metric("Current Value", f"${current_value:,.2f}" if current_value else "$0.00")
                
                if invested > 0:
                    gain_loss = summary.get('total_gain_loss', 0)
                    gain_loss_percent = summary.get('gain_loss_percent', 0)
                    if gain_loss != 0:
                        st.metric("Total Gain/Loss", 
                                 f"${gain_loss:+,.2f} ({gain_loss_percent:+.1f}%)",
                                 delta=f"{gain_loss_percent:+.1f}%")
        except Exception as e:
            # Fallback to session state data
            if not st.session_state.portfolio.empty:
                col1, col2 = st.columns([3, 1])
            with col1:
                total_value = sum(st.session_state.portfolio['Current Price'] * st.session_state.portfolio['Shares'])
                st.metric(label="Total Portfolio Value", value=f"${total_value:,.2f}", delta="+12.5%")
            with col2:
                if st.button("🔄 Refresh Data"):
                    st.rerun()

    st.divider()
    
    # Create new portfolio section
    with st.expander("➕ Create New Portfolio"):
        with st.form("create_portfolio"):
            portfolio_name = st.text_input("Portfolio Name")
            if st.form_submit_button("Create Portfolio"):
                if portfolio_name.strip():
                    success, message = create_portfolio(portfolio_name.strip())
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
                else:
                    st.error("Please enter a portfolio name")
    
    st.subheader("Holdings")
    
    # Try to fetch from backend first
    if check_backend_connection():
        try:
            portfolios_response = make_authenticated_request("GET", f"{BACKEND_URL}/portfolio/")
            if portfolios_response.status_code == 200:
                portfolios = portfolios_response.json()
                if portfolios:
                    for portfolio in portfolios:
                        with st.expander(f"📁 {portfolio['name']} ({portfolio['total_holdings']} holdings - ${portfolio['total_value']:,.2f})"):
                            holdings_response = make_authenticated_request("GET", f"{BACKEND_URL}/portfolio/{portfolio['portfolio_id']}/holdings")
                            if holdings_response.status_code == 200:
                                holdings = holdings_response.json()
                                if holdings:
                                    holdings_df = pd.DataFrame(holdings)
                                    display_columns = ['symbol', 'company_name', 'quantity', 'avg_price', 'current_price', 'total_value', 'gain_loss', 'gain_loss_percent']
                                    available_holdings_columns = [col for col in display_columns if col in holdings_df.columns]
                                    if available_holdings_columns:
                                        holdings_display = holdings_df[available_holdings_columns].copy()
                                        column_mapping = {
                                            'symbol': 'Symbol',
                                            'company_name': 'Company',
                                            'quantity': 'Qty',
                                            'avg_price': 'Avg Price',
                                            'current_price': 'Current Price',
                                            'total_value': 'Total Value',
                                            'gain_loss': 'Gain/Loss',
                                            'gain_loss_percent': 'Gain/Loss %'
                                        }
                                        
                                        holdings_display = holdings_display.rename(columns={k: v for k, v in column_mapping.items() if k in holdings_display.columns})                            
                                        if 'Avg Price' in holdings_display.columns:
                                            holdings_display['Avg Price'] = holdings_display['Avg Price'].apply(lambda x: f"${x:.2f}" if pd.notnull(x) else "N/A")
                                        if 'Current Price' in holdings_display.columns:
                                            holdings_display['Current Price'] = holdings_display['Current Price'].apply(lambda x: f"${x:.2f}" if pd.notnull(x) else "N/A")
                                        if 'Total Value' in holdings_display.columns:
                                            holdings_display['Total Value'] = holdings_display['Total Value'].apply(lambda x: f"${x:,.2f}" if pd.notnull(x) else "N/A")
                                        if 'Gain/Loss' in holdings_display.columns:
                                            holdings_display['Gain/Loss'] = holdings_display['Gain/Loss'].apply(lambda x: f"${x:+,.2f}" if pd.notnull(x) else "N/A")
                                        if 'Gain/Loss %' in holdings_display.columns:
                                            holdings_display['Gain/Loss %'] = holdings_display['Gain/Loss %'].apply(lambda x: f"{x:+.1f}%" if pd.notnull(x) else "N/A")
                                        
                                        st.dataframe(holdings_display, use_container_width=True, hide_index=True)
                                    else:
                                        st.info("No holdings data available")
                                else:
                                    st.info("No holdings in this portfolio")
                    st.success("Portfolio data loaded successfully.")
                else:
                    st.info("No portfolios found. Create your first portfolio above!")
            elif portfolios_response.status_code == 401:
                st.session_state.authenticated = False
                st.error("Session expired. Please login again.")
                st.rerun()
            else:
                st.warning(f"Could not fetch portfolios (status: {portfolios_response.status_code}). Using local data.")
                # Fallback to session state
                edited_df = st.data_editor(
                    st.session_state.portfolio,
                    num_rows="dynamic",
                    use_container_width=True,
                    hide_index=True
                )
                
                # Update session state if changed
                st.session_state.portfolio = edited_df
                st.caption("You can edit the table directly to simulate adding/removing positions.")
        except requests.exceptions.Timeout:
            st.warning("Request timed out while fetching portfolio data. Using local data.")
            # Fallback to session state
            edited_df = st.data_editor(
                st.session_state.portfolio,
                num_rows="dynamic",
                use_container_width=True,
                hide_index=True
            )
            
            # Update session state if changed
            st.session_state.portfolio = edited_df
            st.caption("You can edit the table directly to simulate adding/removing positions.")
        except Exception as e:
            st.error(f"Error fetching portfolio data: {str(e)}. Using local data.")
            # Fallback to session state
            edited_df = st.data_editor(
                st.session_state.portfolio,
                num_rows="dynamic",
                use_container_width=True,
                hide_index=True
            )
            
            # Update session state if changed
            st.session_state.portfolio = edited_df
            st.caption("You can edit the table directly to simulate adding/removing positions.")
    else:
        st.warning("Backend server not connected. Using local data.")
        # Fallback to session state
        edited_df = st.data_editor(
            st.session_state.portfolio,
            num_rows="dynamic",
            use_container_width=True,
            hide_index=True
        )
        
        # Update session state if changed
        st.session_state.portfolio = edited_df
        st.caption("You can edit the table directly to simulate adding/removing positions.")

def render_alerts_page():
    """Enhanced alerts page with features from multiple branches."""
    st.header("🔔 Price Alerts")
    st.caption("Manage your stock price alerts.")
    
    # Create Alert Form
    with st.form("create_alert_form"):
        st.subheader("Create New Alert")
        c1, c2, c3 = st.columns(3)
        
        with c1:
            symbol = st.text_input("Stock Symbol", placeholder="e.g. AAPL").upper()
        with c2:
            condition = st.selectbox("Condition", ["Above Price", "Below Price"])
        with c3:
            value = st.number_input("Price Value", min_value=0.0, step=0.01)
            
        submitted = st.form_submit_button("Create Alert")
        
        if submitted:
            if symbol and value > 0:
                new_alert = {
                    "Symbol": symbol, 
                    "Condition": condition, 
                    "Value": value, 
                    "Status": "Active"
                }
                st.session_state.alerts.append(new_alert)
                st.success(f"Alert set for {symbol} {condition} ${value}")
            else:
                st.warning("Please enter a valid symbol and price.")

    st.divider()
    
    st.subheader("Active Alerts")
    if st.session_state.alerts:
        alerts_df = pd.DataFrame(st.session_state.alerts)
        st.dataframe(alerts_df, use_container_width=True, hide_index=True)
    else:
        st.info("No active alerts.")

def render_ai_advisor_page():
    """New AI advisor page with chat functionality and enhanced error handling."""
    st.header("🤖 AI Investment Advisor")
    
    # Check AI service status
    ai_status = "✅ Connected to OpenAI" if os.getenv("OPENAI_API_KEY") and os.getenv("OPENAI_API_KEY") != "your-openai-api-key" else "⚠️ Using rule-based responses (configure OpenAI API key for enhanced AI)"
    st.caption(f"Get personalized investment advice from our AI assistant. {ai_status}")
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("Ask about stocks, markets, or investment strategies..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)

        # Display assistant response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                ai_response = ""
                try:
                    # Check backend connection first
                    if not check_backend_connection():
                        ai_response = "I'm having trouble connecting to my knowledge base. The backend server might not be running. Please ensure the backend service is available."
                    else:
                        # API call to backend for AI response
                        response = make_authenticated_request("POST", f"{BACKEND_URL}/ai-advice", 
                                               json={"query": prompt})  # Increased timeout for AI processing
                        
                        if response.status_code == 200:
                            ai_response = response.json().get("advice", "I'm here to help with your investment queries. Please try asking about specific stocks, sectors, or investment strategies.")
                        elif response.status_code == 401:
                            st.session_state.authenticated = False
                            ai_response = "Session expired. Please login again to continue using the AI advisor."
                        elif response.status_code == 429:
                            ai_response = "I'm currently experiencing high demand. Please wait a moment and try again."
                        else:
                            ai_response = f"I'm having trouble connecting to my knowledge base (status: {response.status_code}). Please try again later."
                except requests.exceptions.Timeout:
                    ai_response = "The AI response is taking longer than expected. Please try asking your question again."
                except requests.exceptions.ConnectionError:
                    ai_response = "I'm unable to connect to my knowledge base right now. Please ensure the backend service is running."
                except Exception as e:
                    ai_response = f"An error occurred while processing your request: {str(e)}. Please try again."
                
                st.markdown(ai_response)
        
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": ai_response})

def render_analytics_page():
    """New analytics page with comprehensive market insights and dynamic data."""
    st.markdown('<div class="card"><h2>📊 Market Analytics</h2></div>', unsafe_allow_html=True)
    st.caption("Comprehensive market insights and analytics.")
    
    # Try to fetch live data from backend if available
    live_data_available = check_backend_connection()
    
    if live_data_available:
        try:
            analytics_response = make_authenticated_request("GET", f"{BACKEND_URL}/analytics/market-overview")
            
            if analytics_response.status_code == 200:
                market_data = analytics_response.json()
                market_metrics = market_data.get("indices", {
                    "S&P 500": {"value": 4890.18, "change": "+0.34%"},
                    "NASDAQ": {"value": 15657.82, "change": "+0.67%"},
                    "DOW JONES": {"value": 38256.58, "change": "+0.12%"},
                    "VIX": {"value": 15.42, "change": "-2.34%"}
                })
                sectors_data = market_data.get("sectors", {
                    "Technology": "+2.15%",
                    "Healthcare": "+1.23%",
                    "Financials": "+0.87%",
                    "Consumer Discretionary": "+1.56%",
                    "Energy": "-0.45%",
                    "Utilities": "+0.32%"
                })
                st.success("Live market data loaded successfully")
            else:
                # Fallback to static data
                market_metrics = {
                    "S&P 500": {"value": 4890.18, "change": "+0.34%"},
                    "NASDAQ": {"value": 15657.82, "change": "+0.67%"},
                    "DOW JONES": {"value": 38256.58, "change": "+0.12%"},
                    "VIX": {"value": 15.42, "change": "-2.34%"}
                }
                sectors_data = {
                    "Technology": "+2.15%",
                    "Healthcare": "+1.23%",
                    "Financials": "+0.87%",
                    "Consumer Discretionary": "+1.56%",
                    "Energy": "-0.45%",
                    "Utilities": "+0.32%"
                }
                st.warning("Using static market data")
        except:
            # Fallback to static data
            market_metrics = {
                "S&P 500": {"value": 4890.18, "change": "+0.34%"},
                "NASDAQ": {"value": 15657.82, "change": "+0.67%"},
                "DOW JONES": {"value": 38256.58, "change": "+0.12%"},
                "VIX": {"value": 15.42, "change": "-2.34%"}
            }
            sectors_data = {
                "Technology": "+2.15%",
                "Healthcare": "+1.23%",
                "Financials": "+0.87%",
                "Consumer Discretionary": "+1.56%",
                "Energy": "-0.45%",
                "Utilities": "+0.32%"
            }
            st.warning("Using static market data")
    else:
        # Use static data when backend is not available
        market_metrics = {
            "S&P 500": {"value": 4890.18, "change": "+0.34%"},
            "NASDAQ": {"value": 15657.82, "change": "+0.67%"},
            "DOW JONES": {"value": 38256.58, "change": "+0.12%"},
            "VIX": {"value": 15.42, "change": "-2.34%"}
        }
        sectors_data = {
            "Technology": "+2.15%",
            "Healthcare": "+1.23%",
            "Financials": "+0.87%",
            "Consumer Discretionary": "+1.56%",
            "Energy": "-0.45%",
            "Utilities": "+0.32%"
        }
        st.info("Backend not connected. Using static market data.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Market Overview")
        
        for index, data in market_metrics.items():
            col_a, col_b = st.columns([2, 1])
            with col_a:
                st.write(f"**{index}**")
            with col_b:
                change_color = "green" if "+" in data["change"] else "red"
                st.markdown(f"<span style='color: {change_color};'>{data['change']}</span>", unsafe_allow_html=True)
            st.write(f"{data['value']:,.2f}")
            st.divider()
    
    with col2:
        st.subheader("Sector Performance")
        
        for sector, perf in sectors_data.items():
            col_a, col_b = st.columns([2, 1])
            with col_a:
                st.write(f"{sector}")
            with col_b:
                change_color = "green" if "+" in perf else "red"
                st.markdown(f"<span style='color: {change_color};'>{perf}</span>", unsafe_allow_html=True)
            # Normalize the value for progress bar (between 0 and 1)
            perf_val = float(perf.replace('%', ''))
            normalized_val = min(max(abs(perf_val) / 5.0, 0), 1)  # Cap at 5% for visualization
            st.progress(normalized_val)

# --- Main App Layout ---
def main():
    # Sidebar Navigation
    with st.sidebar:
        st.title("📊 StockScreener Pro")
        page = st.radio(
            "Navigation", 
            ["Screener", "Portfolio", "Alerts", "AI Advisor", "Analytics"],
            index=0
        )
        
        st.divider()
        st.markdown("### About")
        st.info(
            "Advanced stock analysis and screening platform with AI-powered insights."
        )

    # Simple header with logout
    col1, col2 = st.columns([4, 1])
    with col1:
        st.title("📈 StockScreener Pro")
    with col2:
        if st.button("Logout", key="logout_btn", type="secondary"):
            logout_user()
            st.rerun()
    
    st.divider()
    
    # Page routing - direct rendering without containers
    if page == "Screener":
        render_screener_page()
    elif page == "Portfolio":
        render_portfolio_page()
    elif page == "Alerts":
        render_alerts_page()
    elif page == "AI Advisor":
        render_ai_advisor_page()
    elif page == "Analytics":
        render_analytics_page()

# Initialize session state for modal and feedback
# Duplicate initialization - already handled at the top of the file
if 'show_auth_modal' not in st.session_state:
    st.session_state.show_auth_modal = not st.session_state.get('authenticated', False)

# Check if user is already logged in by validating the token
if st.session_state.token and not st.session_state.authenticated:
    try:
        # Validate the token by making a simple authenticated request to portfolio endpoint
        headers = {"Authorization": f"Bearer {st.session_state.token}"}
        response = requests.get(f"{BACKEND_URL}/portfolio/", headers=headers)
        # Valid responses (200 = has portfolios, 204 = no portfolios, 401 = invalid token)
        if response.status_code in [200, 204]:
            st.session_state.authenticated = True
            st.session_state.show_auth_modal = False
        else:
            # Token is invalid, reset session
            st.session_state.authenticated = False
            st.session_state.token = None
            st.session_state.refresh_token = None
            st.session_state.show_auth_modal = True
    except:
        # If there's an error validating the token, assume user is not logged in
        st.session_state.authenticated = False
        st.session_state.token = None
        st.session_state.refresh_token = None
        st.session_state.show_auth_modal = True

# Run the app
if __name__ == "__main__":
    # Check backend connectivity
    if not check_backend_connection():
        st.error("⚠️ Backend server is not running!")
        st.info("Please start the FastAPI backend server:")
        st.code("uvicorn backend.main:app --host 127.0.0.1 --port 8001 --reload")
        st.stop()
    
    # Show authentication modal if user is not logged in
    if st.session_state.show_auth_modal:
        # Create a centered container for the login modal
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown('<div class="modal-overlay">', unsafe_allow_html=True)
            st.markdown('<div class="modal-content">', unsafe_allow_html=True)
            
            st.markdown('<h2 class="modal-title">Welcome to StockScreener Pro</h2>', unsafe_allow_html=True)
            
            st.markdown('<p class="modal-subtitle">Advanced Stock Analysis Platform</p>', unsafe_allow_html=True)
            
            st.markdown('<p class="modal-description">Please log in or sign up to access the advanced stock screening and analysis tools.</p>', unsafe_allow_html=True)
            
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
                            success, message = login_user(email, password)
                            if success:
                                st.session_state.show_auth_modal = False  # Hide modal after successful login
                                st.session_state.show_login_feedback = True
                                st.session_state.login_feedback_message = "Login successful! Welcome back."
                                st.session_state.login_feedback_type = "success"
                                time.sleep(0.5)  # Short pause to show success message
                                st.rerun()
                            else:
                                st.session_state.show_login_feedback = True
                                st.session_state.login_feedback_message = message
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
                        with st.spinner("Creating your account... This may take a moment."):
                            success, message = signup_user(signup_email.split('@')[0], signup_email, signup_password)  # Use email prefix as name
                            if success:
                                st.session_state.show_auth_modal = False  # Hide modal after successful signup
                                st.session_state.show_login_feedback = True
                                st.session_state.login_feedback_message = "Account created successfully! Welcome to the platform."
                                st.session_state.login_feedback_type = "success"
                                time.sleep(0.5)  # Short pause to show success message
                                st.rerun()
                            else:
                                st.session_state.show_login_feedback = True
                                st.session_state.login_feedback_message = message
                                st.session_state.login_feedback_type = "error"
            
            st.markdown('</div>', unsafe_allow_html=True)  # Close modal content
            st.markdown('</div>', unsafe_allow_html=True)  # Close modal overlay
    
    # Main interface - only show when logged in
    if st.session_state.authenticated:
        # Display feedback messages outside modal
        if st.session_state.show_login_feedback:
            if st.session_state.login_feedback_type == "success":
                st.markdown(f'<div class="feedback-success">{st.session_state.login_feedback_message}</div>', unsafe_allow_html=True)
            elif st.session_state.login_feedback_type == "error":
                st.markdown(f'<div class="feedback-error">{st.session_state.login_feedback_message}</div>', unsafe_allow_html=True)
            elif st.session_state.login_feedback_type == "info":
                st.markdown(f'<div class="feedback-info">{st.session_state.login_feedback_message}</div>', unsafe_allow_html=True)
            elif st.session_state.login_feedback_type == "warning":
                st.markdown(f'<div class="feedback-warning">{st.session_state.login_feedback_message}</div>', unsafe_allow_html=True)
        
        try:
            main()
        except Exception as e:
            st.error(f"An unexpected error occurred: {str(e)}")
            st.info("Please refresh the page or contact support if the problem persists.")
            if st.button("Logout"):
                logout_user()
                st.rerun()
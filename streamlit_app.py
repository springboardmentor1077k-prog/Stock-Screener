import streamlit as st
import requests
import os
import pandas as pd

API_URL = os.getenv("API_URL", "http://127.0.0.1:8001")

st.set_page_config(page_title="AI Stock Screener", layout="wide")

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'token' not in st.session_state:
    st.session_state.token = None
if 'user_email' not in st.session_state:
    st.session_state.user_email = None
if 'user_name' not in st.session_state:
    st.session_state.user_name = None

def login_user(email, password):
    """Login user and get token."""
    try:
        response = requests.post(f"{API_URL}/auth/login", json={
            "email": email,
            "password": password
        })
        
        if response.status_code == 200:
            data = response.json()
            st.session_state.authenticated = True
            st.session_state.token = data['token']
            st.session_state.user_email = data['email']
            st.session_state.user_name = data['name']
            return True, "Login successful!"
        else:
            try:
                error_data = response.json()
                return False, error_data.get('detail', 'Login failed')
            except:
                return False, f"Login failed with status {response.status_code}"
    except requests.exceptions.ConnectionError:
        return False, "Cannot connect to server. Please make sure the backend is running on http://127.0.0.1:8001"
    except requests.exceptions.JSONDecodeError:
        return False, "Server returned invalid response"
    except Exception as e:
        return False, f"Connection error: {str(e)}"

def signup_user(name, email, password):
    """Sign up new user and get token."""
    try:
        response = requests.post(f"{API_URL}/auth/signup", json={
            "name": name,
            "email": email,
            "password": password
        })
        
        if response.status_code == 200:
            data = response.json()
            st.session_state.authenticated = True
            st.session_state.token = data['token']
            st.session_state.user_email = data['email']
            st.session_state.user_name = data['name']
            return True, "Signup successful!"
        else:
            try:
                error_data = response.json()
                return False, error_data.get('detail', 'Signup failed')
            except:
                return False, f"Signup failed with status {response.status_code}"
    except requests.exceptions.ConnectionError:
        return False, "Cannot connect to server. Please make sure the backend is running on http://127.0.0.1:8001"
    except requests.exceptions.JSONDecodeError:
        return False, "Server returned invalid response"
    except Exception as e:
        return False, f"Connection error: {str(e)}"

def logout_user():
    """Logout user and clear session."""
    st.session_state.authenticated = False
    st.session_state.token = None
    st.session_state.user_email = None
    st.session_state.user_name = None

def run_screener(query):
    try:
        headers = {"Authorization": f"Bearer {st.session_state.token}"}
        response = requests.post(f"{API_URL}/ai/screener", 
                               params={"query": query}, 
                               headers=headers,
                               timeout=10)
        if response.status_code == 200:
            return True, response.json()
        elif response.status_code == 400:
            try:
                error_data = response.json()
                return False, error_data.get('detail', 'Invalid query')
            except:
                return False, "Invalid query format"
        elif response.status_code == 401:
            st.session_state.authenticated = False
            return False, "Session expired. Please login again."
        else:
            try:
                error_data = response.json()
                return False, error_data.get('detail', 'Backend error')
            except:
                return False, f"Backend error (status {response.status_code})"
    except Exception as e:
        return False, f"Connection error: {str(e)}"

st.title("📊 AI Stock Screener")

def check_backend_connection():
    """Check if backend is running."""
    try:
        response = requests.get(f"{API_URL}/docs", timeout=5)
        return response.status_code == 200
    except:
        return False

if not check_backend_connection():
    st.error("⚠️ Backend server is not running!")
    st.info("Please start the FastAPI backend server:")
    st.code("uvicorn backend.main:app --host 127.0.0.1 --port 8001 --reload")
    st.stop()

if not st.session_state.authenticated:
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    
    with tab1:
        st.subheader("Login")
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            login_button = st.form_submit_button("Login")
            
            if login_button:
                if email and password:
                    success, message = login_user(email, password)
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
                else:
                    st.error("Please enter both email and password")
    
    with tab2:
        st.subheader("Sign Up")
        with st.form("signup_form"):
            name = st.text_input("Full Name", key="signup_name")
            email = st.text_input("Email", key="signup_email")
            password = st.text_input("Password", type="password", key="signup_password", 
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

else:
    col1, col2 = st.columns([3, 1])
    with col1:
        st.write(f"Welcome, {st.session_state.user_name}!")
    with col2:
        if st.button("Logout"):
            logout_user()
            st.rerun()
    
    st.divider()
    query = st.text_input(
        "Enter screening query",
        placeholder="e.g. PE ratio >= 5 and positive net profit for last 4 quarters"
    )
    
    if st.button("Run Screener") and query:
        with st.spinner("Running screener..."):
            success, result = run_screener(query)
            if success:
                st.subheader(f"📈 Results ({len(result['results'])})")

                if result["results"]:
                    import pandas as pd
                    df = pd.DataFrame(result["results"])
                    
                    column_mapping = {
                        'symbol': 'Symbol',
                        'company_name': 'Company',
                        'sector': 'Sector',
                        'industry': 'Industry',
                        'exchange': 'Exchange',
                        'pe_ratio': 'P/E Ratio',
                        'eps': 'EPS',
                        'market_cap': 'Market Cap',
                        'roe': 'ROE (%)',
                        'debt_equity': 'Debt/Equity'
                    }
                    
                    df = df.rename(columns={k: v for k, v in column_mapping.items() if k in df.columns})
                    
                    if 'Market Cap' in df.columns:
                        df['Market Cap'] = df['Market Cap'].apply(lambda x: f"${x:,.0f}" if pd.notnull(x) and x > 0 else "N/A")
                    if 'P/E Ratio' in df.columns:
                        df['P/E Ratio'] = df['P/E Ratio'].apply(lambda x: f"{x:.2f}" if pd.notnull(x) and x > 0 else "N/A")
                    if 'EPS' in df.columns:
                        df['EPS'] = df['EPS'].apply(lambda x: f"${x:.2f}" if pd.notnull(x) else "N/A")
                    if 'ROE (%)' in df.columns:
                        df['ROE (%)'] = df['ROE (%)'].apply(lambda x: f"{x:.2f}%" if pd.notnull(x) else "N/A")
                    if 'Debt/Equity' in df.columns:
                        df['Debt/Equity'] = df['Debt/Equity'].apply(lambda x: f"{x:.2f}" if pd.notnull(x) else "N/A")
                    
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info("No stocks matched your criteria")
            else:
                error_msg = result
                st.error(f"❌ {error_msg}")
                
                if "Session expired" in result:
                    st.rerun()

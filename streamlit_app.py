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
    """Run stock screener with optimized error handling and caching."""
    if not query or not query.strip():
        return False, "Please enter a query"
    
    try:
        headers = {"Authorization": f"Bearer {st.session_state.token}"}
        
        with st.spinner("🔍 Analyzing your query..."):
            response = requests.post(f"{API_URL}/ai/screener", 
                                   params={"query": query.strip()}, 
                                   headers=headers,
                                   timeout=30)  
            
        if response.status_code == 200:
            data = response.json()
            if not isinstance(data, dict):
                return False, "Invalid response format from server"
            if 'results' not in data:
                return False, "Missing results in server response"
            return True, data
        elif response.status_code == 400:
            try:
                error_data = response.json()
                return False, error_data.get('detail', 'Invalid query')
            except:
                return False, "Invalid query format"
        elif response.status_code == 401:
            st.session_state.authenticated = False
            return False, "Session expired. Please login again."
        elif response.status_code == 500:
            try:
                error_data = response.json()
                error_detail = error_data.get('detail', 'Server error')
                if "Database query error" in error_detail:
                    return False, "Database connection issue. Please try again."
                return False, f"Server error: {error_detail}"
            except:
                return False, "Server error occurred"
        else:
            try:
                error_data = response.json()
                return False, error_data.get('detail', f'Backend error (status {response.status_code})')
            except:
                return False, f"Backend error (status {response.status_code})"
    except requests.exceptions.Timeout:
        return False, "Query timed out. The database might be processing a complex request. Please try again."
    except requests.exceptions.ConnectionError:
        return False, "Cannot connect to server. Please check if the backend is running."
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

    tab1, tab2 = st.tabs(["📊 Stock Screener", "💼 My Portfolios"])
    
    with tab1:
        query = st.text_input(
            "Enter screening query",
            placeholder="e.g. PE ratio >= 5 and positive net profit for last 4 quarters",
            help="Try queries like 'Technology stocks with PE less than 20' or 'Large cap stocks with dividend yield above 2%'"
        )
        
        if st.button("Run Screener") and query:
            with st.spinner("Running screener..."):
                success, result = run_screener(query)
                
                if success:
                    result_count = len(result['results'])
                    st.success(f"Found {result_count} stocks matching your criteria")
                    
                    if result_count > 0:

                        st.subheader(f"Results ({result_count})")

                        import pandas as pd
                        df = pd.DataFrame(result["results"])
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
                            st.dataframe(styled_df )
                        else:
                            st.dataframe(df_display )
                        
                        if result.get("has_quarterly", False) and result.get("quarterly_data"):
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
                                                        required_cols = ['quarter', 'year', 'revenue', 'ebitda', 'net_profit']
                                                        available_cols = [col for col in required_cols if col in quarterly_df.columns]
                                                        
                                                        if available_cols:
                                                            quarterly_df = quarterly_df[available_cols]                                                        
                                                            for col in ['revenue', 'ebitda', 'net_profit']:
                                                                if col in quarterly_df.columns:
                                                                    quarterly_df[col] = quarterly_df[col].apply(
                                                                        lambda x: f"${x:,.0f}" if pd.notnull(x) and x != 0 else "N/A"
                                                                    )
                                                                    
                                                            col_mapping = {
                                                                'quarter': 'Quarter',
                                                                'year': 'Year', 
                                                                'revenue': 'Revenue',
                                                                'ebitda': 'EBITDA',
                                                                'net_profit': 'Net Profit'
                                                            }
                                                            quarterly_df = quarterly_df.rename(columns={k: v for k, v in col_mapping.items() if k in quarterly_df.columns})
                                                            st.dataframe(quarterly_df )
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
                                                        required_cols = ['quarter', 'year', 'revenue', 'ebitda', 'net_profit']
                                                        available_cols = [col for col in required_cols if col in quarterly_df.columns]
                                                        
                                                        if available_cols:
                                                            quarterly_df = quarterly_df[available_cols]                                                        
                                                            for col in ['revenue', 'ebitda', 'net_profit']:
                                                                if col in quarterly_df.columns:
                                                                    quarterly_df[col] = quarterly_df[col].apply(
                                                                        lambda x: f"${x:,.0f}" if pd.notnull(x) and x != 0 else "N/A"
                                                                    )
                                                            col_mapping = {
                                                                'quarter': 'Quarter',
                                                                'year': 'Year', 
                                                                'revenue': 'Revenue',
                                                                'ebitda': 'EBITDA',
                                                                'net_profit': 'Net Profit'
                                                            }
                                                            quarterly_df = quarterly_df.rename(columns={k: v for k, v in col_mapping.items() if k in quarterly_df.columns})
                                                            st.dataframe(quarterly_df )
                                                        else:
                                                            st.warning(f"No quarterly data available for {symbol}")
                                                    except Exception as e:
                                                        st.error(f"Error displaying data for {symbol}: {str(e)}")
                                else:
                                    st.info("No quarterly data available for the selected stocks")
                            else:
                                st.info("No quarterly data available")
                    
                    else:
                        st.info("No stocks matched your criteria")
                else:
                    error_msg = result
                    st.error(f"❌ {error_msg}")                
                    if "data we don't have" in error_msg.lower() or "unsupported" in error_msg.lower():
                        st.info("💡 Try: `PE ratio > 15` or `positive profit last 4 quarters`")
                    
                    if "Session expired" in result:
                        st.rerun()
    
    with tab2:
        st.subheader("💼 Portfolio Management")
        def get_portfolios():
            """Get user's portfolios."""
            try:
                headers = {"Authorization": f"Bearer {st.session_state.token}"}
                response = requests.get(f"{API_URL}/portfolio/", headers=headers)
                if response.status_code == 200:
                    return True, response.json()
                else:
                    return False, "Failed to fetch portfolios"
            except Exception as e:
                return False, f"Error: {str(e)}"
        
        def get_portfolio_holdings(portfolio_id):
            """Get holdings for a specific portfolio."""
            try:
                headers = {"Authorization": f"Bearer {st.session_state.token}"}
                response = requests.get(f"{API_URL}/portfolio/{portfolio_id}/holdings", headers=headers)
                if response.status_code == 200:
                    return True, response.json()
                else:
                    return False, "Failed to fetch holdings"
            except Exception as e:
                return False, f"Error: {str(e)}"
        
        def create_portfolio(name):
            """Create a new portfolio."""
            try:
                headers = {"Authorization": f"Bearer {st.session_state.token}"}
                response = requests.post(f"{API_URL}/portfolio/", 
                                       json={"name": name}, 
                                       headers=headers)
                if response.status_code == 200:
                    return True, "Portfolio created successfully"
                else:
                    return False, "Failed to create portfolio"
            except Exception as e:
                return False, f"Error: {str(e)}"
        
        def get_portfolio_summary():
            """Get portfolio summary."""
            try:
                headers = {"Authorization": f"Bearer {st.session_state.token}"}
                response = requests.get(f"{API_URL}/portfolio/summary", headers=headers)
                if response.status_code == 200:
                    return True, response.json()
                else:
                    return False, "Failed to fetch summary"
            except Exception as e:
                return False, f"Error: {str(e)}"
        
        success, summary = get_portfolio_summary()
        if success:
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
        
        st.divider()
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
        success, portfolios = get_portfolios()
        if success and portfolios:
            st.subheader("Your Portfolios")
            
            for portfolio in portfolios:
                with st.expander(f"📁 {portfolio['name']} ({portfolio['total_holdings']} holdings - ${portfolio['total_value']:,.2f})"):
                    holdings_success, holdings = get_portfolio_holdings(portfolio['portfolio_id'])                    
                    if holdings_success and holdings:
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
                            
                            st.dataframe(holdings_display )
                        else:
                            st.info("No holdings data available")
                    else:
                        st.info("No holdings in this portfolio")
        else:
            st.info("No portfolios found. Create your first portfolio above!")
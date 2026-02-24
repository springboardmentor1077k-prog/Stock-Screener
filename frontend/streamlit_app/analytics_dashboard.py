import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Configuration
API_BASE = "http://127.0.0.1:8000/api/v1"
st.set_page_config(
    page_title="StockSense AI",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'user_data' not in st.session_state:
    st.session_state.user_data = None

# Disclaimer text
DISCLAIMER_SHORT = "⚠️ **Disclaimer:** For educational purposes only. Not financial advice."
DISCLAIMER_FULL = """
⚠️ **IMPORTANT DISCLAIMER**

This application is provided for **educational and informational purposes only**. 
The information presented does not constitute financial, investment, legal, or tax advice.

- Past performance is not indicative of future results
- Stock prices and market data may be delayed or inaccurate
- Always consult a qualified financial advisor before making investment decisions
- The developers are not responsible for any financial losses incurred

By using this application, you acknowledge that you understand and accept these terms.
"""

# Custom CSS for better styling
st.markdown("""
<style>
    /* Main theme colors */
    :root {
        --primary: #6366f1;
        --secondary: #8b5cf6;
        --success: #10b981;
        --danger: #ef4444;
        --warning: #f59e0b;
        --dark: #1e293b;
        --light: #f8fafc;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Main container styling */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e293b 0%, #334155 100%);
    }
    [data-testid="stSidebar"] * {
        color: #f8fafc !important;
    }
    [data-testid="stSidebar"] .stRadio > label {
        background: rgba(255,255,255,0.1);
        padding: 10px 15px;
        border-radius: 8px;
        margin: 5px 0;
        transition: all 0.3s ease;
    }
    [data-testid="stSidebar"] .stRadio > label:hover {
        background: rgba(255,255,255,0.2);
    }
    
    /* Metric cards with gradient */
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    [data-testid="stMetric"] label {
        color: rgba(255,255,255,0.8) !important;
        font-size: 0.9rem !important;
    }
    [data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: white !important;
        font-weight: 700 !important;
    }
    [data-testid="stMetric"] [data-testid="stMetricDelta"] {
        color: rgba(255,255,255,0.9) !important;
    }
    
    /* Headers styling */
    h1 {
        background: linear-gradient(90deg, #6366f1, #8b5cf6, #a855f7);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800 !important;
    }
    h2 {
        color: #1e293b !important;
        border-bottom: 3px solid #6366f1;
        padding-bottom: 10px;
    }
    
    /* DataFrame styling */
    .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 25px;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(99, 102, 241, 0.3);
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(99, 102, 241, 0.4);
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #f1f5f9;
        padding: 10px;
        border-radius: 12px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
        color: white !important;
    }
    
    /* Form styling */
    .stForm {
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
        padding: 25px;
        border-radius: 16px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    
    /* Input styling */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div > div {
        border-radius: 8px !important;
        border: 2px solid #e2e8f0 !important;
        transition: all 0.3s ease !important;
    }
    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus {
        border-color: #6366f1 !important;
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1) !important;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
        border-radius: 8px;
        font-weight: 600;
    }
    
    /* Success/Error/Warning messages */
    .stSuccess {
        background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
        border-left: 4px solid #10b981;
    }
    .stError {
        background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
        border-left: 4px solid #ef4444;
    }
    .stWarning {
        background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
        border-left: 4px solid #f59e0b;
    }
    .stInfo {
        background: linear-gradient(135deg, #e0e7ff 0%, #c7d2fe 100%);
        border-left: 4px solid #6366f1;
    }
    
    /* Card container */
    .css-card {
        background: white;
        padding: 25px;
        border-radius: 16px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        border: 1px solid #e2e8f0;
        transition: all 0.3s ease;
    }
    .css-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 25px rgba(0,0,0,0.12);
    }
    
    /* Login page special styling */
    .login-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 40px;
        border-radius: 20px;
        box-shadow: 0 20px 40px rgba(102, 126, 234, 0.3);
    }
    
    /* Plotly chart styling */
    .js-plotly-plot {
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    /* Custom animations */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .stAlert, .stMetric, .stDataFrame {
        animation: fadeIn 0.5s ease-out;
    }
    
    /* Scrollbar styling */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    ::-webkit-scrollbar-track {
        background: #f1f5f9;
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
        border-radius: 4px;
    }
    
    /* Footer styling */
    .footer-text {
        text-align: center;
        color: #64748b;
        font-size: 0.85rem;
        padding: 20px;
        margin-top: 40px;
        border-top: 1px solid #e2e8f0;
    }
</style>
""", unsafe_allow_html=True)


def fetch_api(endpoint: str, method: str = "GET", data: dict = None):
    """Helper function to call API endpoints."""
    try:
        url = f"{API_BASE}{endpoint}"
        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=10)
        elif method == "DELETE":
            response = requests.delete(url, timeout=10)
        
        if response.status_code == 200:
            return response.json(), None
        else:
            return None, f"Error {response.status_code}: {response.text}"
    except requests.exceptions.ConnectionError:
        return None, "Backend not reachable. Ensure FastAPI is running on port 8000."
    except Exception as e:
        return None, str(e)


def show_login_page():
    """Display login/registration page."""
    # Center the login form
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Logo and title with custom styling
        st.markdown("""
        <div style="text-align: center; padding: 30px 0;">
            <h1 style="font-size: 3.5rem; margin-bottom: 0;">📈</h1>
            <h1 style="background: linear-gradient(90deg, #6366f1, #8b5cf6, #a855f7);
                       -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                       font-size: 2.5rem; font-weight: 800; margin: 10px 0;">
                StockSense AI
            </h1>
            <p style="color: #64748b; font-size: 1.1rem;">
                Intelligent Stock Analysis Platform
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Show disclaimer prominently
        with st.expander("📜 Important Disclaimer - Please Read", expanded=False):
            st.markdown(DISCLAIMER_FULL)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["🔐 Login", "📝 Register"])
        
        with tab1:
            st.markdown("""
            <div style="text-align: center; padding: 10px 0;">
                <h3 style="color: #1e293b;">Welcome Back! 👋</h3>
            </div>
            """, unsafe_allow_html=True)
            with st.form("login_form"):
                username = st.text_input("👤 Username", placeholder="Enter your username")
                password = st.text_input("🔒 Password", type="password", placeholder="Enter your password")
                
                st.markdown("<br>", unsafe_allow_html=True)
                submit = st.form_submit_button("🔑 Login", type="primary", use_container_width=True)
                
                if submit:
                    if username and password:
                        result, err = fetch_api("/auth/login", method="POST", data={
                            "username": username,
                            "password": password
                        })
                        if result:
                            st.session_state.logged_in = True
                            st.session_state.username = result['user']['username']
                            st.session_state.user_data = result['user']
                            st.success("Login successful!")
                            st.rerun()
                        else:
                            st.error(err or "Invalid credentials")
                    else:
                        st.error("Please enter both username and password")
        
        with tab2:
            st.markdown("""
            <div style="text-align: center; padding: 10px 0;">
                <h3 style="color: #1e293b;">Create Your Account 🚀</h3>
            </div>
            """, unsafe_allow_html=True)
            with st.form("register_form"):
                new_username = st.text_input("👤 Username", placeholder="Choose a username", key="reg_user")
                new_email = st.text_input("📧 Email", placeholder="your@email.com", key="reg_email")
                full_name = st.text_input("📝 Full Name", placeholder="Your full name", key="reg_name")
                new_password = st.text_input("🔒 Password", type="password", placeholder="Create a password", key="reg_pass")
                confirm_password = st.text_input("🔒 Confirm Password", type="password", placeholder="Confirm password", key="reg_confirm")
                
                st.markdown("<br>", unsafe_allow_html=True)
                # Terms acceptance
                accept_terms = st.checkbox("✅ I have read and accept the disclaimer and terms of use")
                
                st.markdown("<br>", unsafe_allow_html=True)
                register = st.form_submit_button("📝 Create Account", type="primary", use_container_width=True)
                
                if register:
                    if not accept_terms:
                        st.error("You must accept the disclaimer and terms to register")
                    elif new_password != confirm_password:
                        st.error("Passwords do not match")
                    elif len(new_password) < 6:
                        st.error("Password must be at least 6 characters")
                    elif not new_username or not new_email:
                        st.error("Please fill in all required fields")
                    else:
                        result, err = fetch_api("/auth/register", method="POST", data={
                            "username": new_username,
                            "email": new_email,
                            "password": new_password,
                            "full_name": full_name
                        })
                        if result:
                            st.success("🎉 Registration successful! Please login.")
                        else:
                            st.error(err or "Registration failed")
        
        # Footer disclaimer
        st.markdown("---")
        st.markdown("""
        <div style="text-align: center; color: #64748b; font-size: 0.85rem;">
            By using StockSense AI, you agree to our terms of service<br>
            and acknowledge that this is not financial advice.
        </div>
        """, unsafe_allow_html=True)


def show_main_app():
    """Display the main application after login."""
    # Sidebar Navigation
    with st.sidebar:
        # Sidebar header with logo
        st.markdown("""
        <div style="text-align: center; padding: 20px 0;">
            <h1 style="font-size: 2.5rem; margin: 0;">📈</h1>
            <h2 style="color: white !important; border: none; font-size: 1.3rem; margin: 5px 0;">
                StockSense AI
            </h2>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # User info card
        st.markdown(f"""
        <div style="background: rgba(255,255,255,0.1); padding: 15px; border-radius: 10px; text-align: center;">
            <div style="font-size: 2rem;">👤</div>
            <div style="font-weight: 600; font-size: 1.1rem; margin-top: 5px;">
                {st.session_state.username}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.username = None
            st.session_state.user_data = None
            st.rerun()
        
        st.markdown("---")
        
        # Navigation
        st.markdown("**📍 Navigation**")
        page = st.radio(
            "Navigate",
            ["🏠 Dashboard", "🔍 Screener", "💼 Portfolio", "🔔 Alerts", "📊 Analytics"],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        
        # Sidebar footer
        st.markdown(f"""
        <div style="font-size: 0.8rem; opacity: 0.7; text-align: center;">
            ⏰ {datetime.now().strftime('%H:%M:%S')}<br>
            <span style="font-size: 0.7rem;">Auto-refreshes on action</span>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.rerun()
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.caption(DISCLAIMER_SHORT)
    
    # ============== DASHBOARD PAGE ==============
    if page == "🏠 Dashboard":
        # Hero header
        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    padding: 30px; border-radius: 16px; margin-bottom: 20px;
                    box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);">
            <h1 style="color: white !important; -webkit-text-fill-color: white; margin: 0; font-size: 2rem;">
                📊 Market Dashboard
            </h1>
            <p style="color: rgba(255,255,255,0.8); margin: 10px 0 0 0;">
                Real-time overview of your portfolio and market trends
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Top disclaimer
        st.info(DISCLAIMER_SHORT)
        
        # Portfolio Summary Cards
        col1, col2, col3, col4 = st.columns(4)
        
        summary, err = fetch_api("/portfolio/summary")
        if summary:
            with col1:
                st.metric("💰 Portfolio Value", f"${summary['current_value']:,.2f}")
            with col2:
                pl_color = "normal" if summary['total_pl'] >= 0 else "inverse"
                st.metric("📈 Total P/L", f"${summary['total_pl']:,.2f}", 
                         f"{summary['pl_percentage']:+.2f}%", delta_color=pl_color)
            with col3:
                st.metric("💵 Invested", f"${summary['invested_value']:,.2f}")
            with col4:
                # Check triggered alerts
                alerts_data, _ = fetch_api("/alerts/check")
                alert_count = alerts_data.get('triggered_count', 0) if alerts_data else 0
                st.metric("🔔 Active Alerts", alert_count)
        else:
            st.warning(err or "Unable to fetch portfolio summary")
        
        st.markdown("---")
        
        # Stock Overview
        col_left, col_right = st.columns([2, 1])
        
        with col_left:
            st.subheader("📋 Top Stocks by Market Cap")
            stocks, err = fetch_api("/stocks/?limit=20")
            if stocks:
                df = pd.DataFrame(stocks)
                # Format and display
                display_df = df[['symbol', 'company_name', 'sector', 'price', 'change_pct', 'pe_ratio', 'promoter_holding']].copy()
                display_df.columns = ['Symbol', 'Company', 'Sector', 'Price', 'Change %', 'P/E', 'Promoter %']
                st.dataframe(display_df, use_container_width=True, hide_index=True)
            else:
                st.error(err or "Failed to load stocks")
        
        with col_right:
            st.subheader("🏢 Sector Distribution")
            if stocks:
                df = pd.DataFrame(stocks)
                sector_counts = df['sector'].value_counts()
                # Custom vibrant color palette
                colors = ['#6366f1', '#8b5cf6', '#a855f7', '#ec4899', '#f43f5e', '#f59e0b']
                fig = px.pie(values=sector_counts.values, names=sector_counts.index, 
                            hole=0.4, color_discrete_sequence=colors)
                fig.update_layout(
                    margin=dict(t=0, b=0, l=0, r=0), 
                    height=300,
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    legend=dict(font=dict(size=11))
                )
                fig.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True)

    # ============== SCREENER PAGE ==============
    elif page == "🔍 Screener":
        # Hero header
        st.markdown("""
        <div style="background: linear-gradient(135deg, #10b981 0%, #059669 100%);
                    padding: 30px; border-radius: 16px; margin-bottom: 20px;
                    box-shadow: 0 10px 30px rgba(16, 185, 129, 0.3);">
            <h1 style="color: white !important; -webkit-text-fill-color: white; margin: 0; font-size: 2rem;">
                🔍 AI-Powered Stock Screener
            </h1>
            <p style="color: rgba(255,255,255,0.8); margin: 10px 0 0 0;">
                Use natural language to find stocks matching your criteria
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.info(DISCLAIMER_SHORT)
        
        st.markdown("""
        <div style="background: #f1f5f9; padding: 15px; border-radius: 10px; margin-bottom: 15px;">
            💡 <strong>Try:</strong> "Show me Technology stocks with PE < 20 and promoter holding > 60%"
        </div>
        """, unsafe_allow_html=True)
        
        # Search input
        user_query = st.text_input(
            "Search Query",
            placeholder="E.g., IT stocks with low PE ratio and high promoter holding",
            label_visibility="collapsed"
        )
        
        col1, col2 = st.columns([1, 4])
        with col1:
            search_btn = st.button("🔎 Search", type="primary", use_container_width=True)
        
        # Quick filters
        st.markdown("**Quick Filters:**")
        filter_cols = st.columns(5)
        
        with filter_cols[0]:
            sector_filter = st.selectbox("Sector", ["All"] + ["Technology", "Healthcare", "Finance", "Energy", "Consumer", "Industrial"])
        with filter_cols[1]:
            pe_max = st.number_input("Max P/E Ratio", min_value=0.0, max_value=100.0, value=50.0, step=5.0)
        with filter_cols[2]:
            promoter_min = st.number_input("Min Promoter %", min_value=0.0, max_value=100.0, value=0.0, step=5.0)
        with filter_cols[3]:
            buyback_filter = st.checkbox("Has Buyback")
        with filter_cols[4]:
            apply_filters = st.button("Apply Filters", use_container_width=True)
        
        st.markdown("---")
        
        # Perform search
        if search_btn and user_query:
            with st.spinner("Analyzing your query with AI..."):
                results, err = fetch_api(f"/stocks/search?query={user_query}")
                if err:
                    st.error(err)
                elif results is not None:
                    if isinstance(results, dict) and 'error' in results:
                        st.error(results['error'])
                    elif len(results) == 0:
                        st.warning("⚠️ No stocks found matching your criteria. Try relaxing the filters (e.g., PE < 20 instead of PE < 5)")
                    else:
                        st.success(f"✅ Found {len(results)} matching stocks")
                        df = pd.DataFrame(results)
                        st.dataframe(df, use_container_width=True, hide_index=True)
                else:
                    st.error("Search failed - please check backend connection")
        
        elif apply_filters:
            # Build filter query
            endpoint = "/stocks/"
            if sector_filter != "All":
                endpoint += f"?sector={sector_filter}&limit=100"
            else:
                endpoint += "?limit=100"
            
            results, err = fetch_api(endpoint)
            if results:
                df = pd.DataFrame(results)
                # Apply client-side filters
                if pe_max < 50:
                    df = df[df['pe_ratio'] <= pe_max]
                if promoter_min > 0:
                    df = df[df['promoter_holding'] >= promoter_min]
                if buyback_filter:
                    df = df[df['has_buyback'] == True]
                
                st.success(f"Found {len(df)} stocks matching your criteria")
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.error(err or "Failed to fetch stocks")
        
        else:
            # Show all stocks by default
            stocks, err = fetch_api("/stocks/?limit=50")
            if stocks:
                st.dataframe(pd.DataFrame(stocks), use_container_width=True, hide_index=True)
            else:
                st.info("Enter a search query or apply filters to find stocks")

    # ============== PORTFOLIO PAGE ==============
    elif page == "💼 Portfolio":
        # Hero header
        st.markdown("""
        <div style="background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
                    padding: 30px; border-radius: 16px; margin-bottom: 20px;
                    box-shadow: 0 10px 30px rgba(245, 158, 11, 0.3);">
            <h1 style="color: white !important; -webkit-text-fill-color: white; margin: 0; font-size: 2rem;">
                💼 Portfolio Manager
            </h1>
            <p style="color: rgba(255,255,255,0.8); margin: 10px 0 0 0;">
                Manage multiple portfolios and track your investments
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.warning(DISCLAIMER_SHORT)
        
        # ========== Portfolio Profile Selector ==========
        profiles, _ = fetch_api("/portfolio/profiles")
        
        # Portfolio selection sidebar
        col_selector, col_create = st.columns([3, 1])
        
        with col_selector:
            if profiles and len(profiles) > 0:
                profile_names = ["📊 All Portfolios"] + [f"💼 {p['name']}" for p in profiles]
                selected_profile = st.selectbox(
                    "Select Portfolio",
                    options=profile_names,
                    key="portfolio_selector"
                )
                # Extract actual name (remove emoji prefix)
                active_portfolio = None if selected_profile == "📊 All Portfolios" else selected_profile.replace("💼 ", "")
            else:
                st.info("No portfolios yet. Create your first portfolio below!")
                active_portfolio = None
        
        with col_create:
            with st.popover("➕ New Portfolio"):
                new_portfolio_name = st.text_input("Portfolio Name", placeholder="e.g., Tech Growth")
                if st.button("Create Portfolio", type="primary", disabled=not new_portfolio_name):
                    if new_portfolio_name:
                        st.success(f"Portfolio '{new_portfolio_name}' ready! Add holdings to create it.")
                        st.session_state['new_portfolio_name'] = new_portfolio_name
        
        st.markdown("---")
        
        # ========== Portfolio Profiles Overview ==========
        if profiles and len(profiles) > 0 and active_portfolio is None:
            st.markdown("""
            <div style="background: #f8fafc; padding: 15px 20px; border-radius: 12px; margin-bottom: 15px;">
                <h3 style="color: #1e293b; margin: 0;">📂 Your Portfolio Profiles</h3>
            </div>
            """, unsafe_allow_html=True)
            
            # Display portfolio cards
            cols = st.columns(min(len(profiles), 4))
            for i, profile in enumerate(profiles[:4]):
                with cols[i % 4]:
                    pl_color = "#10b981" if profile['total_pl'] >= 0 else "#ef4444"
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #ffffff 0%, #f1f5f9 100%);
                                padding: 20px; border-radius: 12px; border: 1px solid #e2e8f0;
                                box-shadow: 0 2px 8px rgba(0,0,0,0.05);">
                        <h4 style="color: #1e293b; margin: 0 0 10px 0;">💼 {profile['name']}</h4>
                        <p style="color: #64748b; margin: 5px 0; font-size: 0.9rem;">
                            {profile['holdings_count']} holdings
                        </p>
                        <p style="color: #1e293b; margin: 5px 0; font-size: 1.2rem; font-weight: 600;">
                            ${profile['current_value']:,.2f}
                        </p>
                        <p style="color: {pl_color}; margin: 5px 0; font-size: 0.9rem;">
                            {'+' if profile['total_pl'] >= 0 else ''}${profile['total_pl']:,.2f} ({profile['pl_percentage']:+.2f}%)
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
            
            if len(profiles) > 4:
                st.info(f"+ {len(profiles) - 4} more portfolios. Use the selector above to view them.")
        
        # ========== Summary metrics for selected portfolio ==========
        summary_endpoint = f"/portfolio/summary?portfolio_name={active_portfolio}" if active_portfolio else "/portfolio/summary"
        summary, err = fetch_api(summary_endpoint)
        
        if summary:
            st.markdown(f"""
            <div style="background: #f8fafc; padding: 10px 20px; border-radius: 12px; margin-bottom: 15px;">
                <h3 style="color: #1e293b; margin: 0;">📈 {summary.get('portfolio_name', 'Portfolio')} Summary</h3>
            </div>
            """, unsafe_allow_html=True)
            
            cols = st.columns(4)
            with cols[0]:
                st.metric("Current Value", f"${summary['current_value']:,.2f}")
            with cols[1]:
                st.metric("Invested Amount", f"${summary['invested_value']:,.2f}")
            with cols[2]:
                delta_color = "normal" if summary['total_pl'] >= 0 else "inverse"
                st.metric("Total P/L", f"${summary['total_pl']:,.2f}", 
                         f"{summary['pl_percentage']:+.2f}%", delta_color=delta_color)
            with cols[3]:
                returns_color = "🟢" if summary['pl_percentage'] >= 0 else "🔴"
                st.metric("Returns", f"{returns_color} {summary['pl_percentage']:+.2f}%")
        
        st.markdown("---")
        
        # Holdings table with tabs
        tab1, tab2, tab3 = st.tabs(["📊 Holdings", "➕ Add Position", "⚙️ Manage"])
        
        with tab1:
            holdings_endpoint = f"/portfolio/holdings?portfolio_name={active_portfolio}" if active_portfolio else "/portfolio/holdings"
            holdings, err = fetch_api(holdings_endpoint)
            
            if holdings and len(holdings) > 0:
                df = pd.DataFrame(holdings)
                
                # Group by portfolio if showing all
                if active_portfolio is None and 'portfolio_name' in df.columns:
                    portfolios_in_view = df['portfolio_name'].unique()
                    
                    for pf_name in portfolios_in_view:
                        pf_df = df[df['portfolio_name'] == pf_name].copy()
                        pf_value = (pf_df['shares'] * pf_df['current_price']).sum()
                        pf_pl = pf_df['pl'].sum()
                        
                        with st.expander(f"💼 {pf_name} ({len(pf_df)} holdings) - ${pf_value:,.2f}", expanded=True):
                            display_df = pf_df[['symbol', 'company_name', 'sub_sector', 'shares', 'avg_buy_price', 'current_price', 'pl', 'pl_pct']].copy()
                            display_df.columns = ['Symbol', 'Company', 'Sub-Sector', 'Shares', 'Avg Price', 'Current', 'P/L ($)', 'P/L (%)']
                            
                            # Color code P/L
                            st.dataframe(
                                display_df.style.applymap(
                                    lambda x: 'color: #10b981' if isinstance(x, (int, float)) and x > 0 else ('color: #ef4444' if isinstance(x, (int, float)) and x < 0 else ''),
                                    subset=['P/L ($)', 'P/L (%)']
                                ),
                                use_container_width=True, 
                                hide_index=True
                            )
                else:
                    # Single portfolio view
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.markdown("""
                        <div style="background: #f8fafc; padding: 15px 20px; border-radius: 12px; margin-bottom: 15px;">
                            <h3 style="color: #1e293b; margin: 0;">📊 Holdings</h3>
                        </div>
                        """, unsafe_allow_html=True)
                        display_df = df[['symbol', 'company_name', 'sub_sector', 'shares', 'avg_buy_price', 'current_price', 'pl', 'pl_pct']].copy()
                        display_df.columns = ['Symbol', 'Company', 'Sub-Sector', 'Shares', 'Avg Price', 'Current', 'P/L ($)', 'P/L (%)']
                        st.dataframe(display_df, use_container_width=True, hide_index=True)
                    
                    with col2:
                        st.markdown("""
                        <div style="background: #f8fafc; padding: 15px 20px; border-radius: 12px; margin-bottom: 15px;">
                            <h3 style="color: #1e293b; margin: 0;">🥧 Allocation</h3>
                        </div>
                        """, unsafe_allow_html=True)
                        df['value'] = df['shares'] * df['current_price']
                        colors = ['#6366f1', '#8b5cf6', '#a855f7', '#ec4899', '#f43f5e', '#f59e0b', '#10b981', '#14b8a6']
                        fig = px.pie(df, values='value', names='symbol', 
                                    hole=0.4,
                                    color_discrete_sequence=colors)
                        fig.update_layout(
                            margin=dict(t=10, b=0, l=0, r=0), 
                            height=300,
                            paper_bgcolor='rgba(0,0,0,0)',
                            showlegend=True
                        )
                        fig.update_traces(textposition='inside', textinfo='percent+label')
                        st.plotly_chart(fig, use_container_width=True)
            else:
                st.markdown("""
                <div style="background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
                            padding: 40px; border-radius: 16px; text-align: center;">
                    <div style="font-size: 3rem; margin-bottom: 15px;">📭</div>
                    <h3 style="color: #475569; margin: 0 0 10px 0;">No Holdings Yet</h3>
                    <p style="color: #64748b;">Add your first position to start tracking your portfolio!</p>
                </div>
                """, unsafe_allow_html=True)
        
        with tab2:
            st.subheader("Add New Position")
            
            # Fetch available stocks for dropdown
            available_stocks, _ = fetch_api("/stocks/?limit=500")
            if available_stocks:
                # Create options with symbol and company name
                stock_options = {f"{s['symbol']} - {s['company_name']}": s for s in available_stocks}
                stock_list = sorted(list(stock_options.keys()))
                
                # Get existing portfolio names and option to create new
                existing_portfolios = [p['name'] for p in profiles] if profiles else []
                new_pf_name = st.session_state.get('new_portfolio_name', '')
                if new_pf_name and new_pf_name not in existing_portfolios:
                    existing_portfolios.insert(0, new_pf_name)
                
                default_portfolios = ["Tech Growth", "Dividend Income", "Value Picks", "Growth Stocks", "Semiconductor", "AI & Cloud"]
                all_portfolio_options = list(set(existing_portfolios + default_portfolios))
                all_portfolio_options.sort()
                
                with st.form("add_holding"):
                    col1, col2 = st.columns(2)
                    with col1:
                        selected_stock = st.selectbox(
                            "Select Stock", 
                            options=stock_list,
                            help="Choose a stock from the available list"
                        )
                        shares = st.number_input("Number of Shares", min_value=1, value=10)
                    with col2:
                        # Portfolio selector with option to type new name
                        portfolio_name = st.selectbox(
                            "Portfolio Profile", 
                            options=all_portfolio_options,
                            index=0 if active_portfolio is None else (all_portfolio_options.index(active_portfolio) if active_portfolio in all_portfolio_options else 0),
                            help="Select existing or type a new portfolio name"
                        )
                        
                        # Get current price as default
                        selected_data = stock_options.get(selected_stock, {})
                        current_price = float(selected_data.get('price', 100.0)) if selected_data else 100.0
                        avg_price = st.number_input("Average Buy Price ($)", min_value=0.01, value=current_price)
                    
                    # Show selected stock info
                    if selected_stock and selected_data:
                        sub_sector = selected_data.get('sub_sector', 'N/A')
                        peg = selected_data.get('peg_ratio', 'N/A')
                        target = selected_data.get('price_vs_target', 'N/A')
                        st.info(f"📈 **{selected_data['symbol']}** | {sub_sector} | Price: ${selected_data['price']:.2f} | PEG: {peg} | Target: {target}")
                    
                    if st.form_submit_button("➕ Add to Portfolio", type="primary"):
                        symbol = selected_data['symbol']
                        data = {
                            "portfolio_name": portfolio_name,
                            "symbol": symbol,
                            "shares": shares,
                            "avg_buy_price": avg_price
                        }
                        result, err = fetch_api("/portfolio/add", method="POST", data=data)
                        if result:
                            action = result.get('action', 'added')
                            if action == 'updated':
                                st.success(f"📈 {result['message']}")
                            else:
                                st.success(f"✅ Added {shares} shares of {symbol} to '{portfolio_name}'!")
                            st.rerun()
                        else:
                            st.error(err or "Failed to add holding")
            else:
                st.warning("Unable to load stock list. Please check backend connection.")
        
        with tab3:
            st.subheader("⚙️ Manage Holdings")
            
            # Get holdings for management
            holdings_endpoint = f"/portfolio/holdings?portfolio_name={active_portfolio}" if active_portfolio else "/portfolio/holdings"
            holdings, _ = fetch_api(holdings_endpoint)
            
            if holdings and len(holdings) > 0:
                st.markdown("Select a holding to remove:")
                
                for holding in holdings:
                    col1, col2, col3 = st.columns([3, 1, 1])
                    with col1:
                        value = holding['shares'] * holding['current_price']
                        st.write(f"**{holding['symbol']}** - {holding['company_name']} | {holding['shares']} shares @ ${holding['avg_buy_price']:.2f} | Value: ${value:,.2f}")
                    with col2:
                        st.write(f"P/L: ${holding['pl']:,.2f}")
                    with col3:
                        if st.button("🗑️ Remove", key=f"remove_{holding['id']}"):
                            result, err = fetch_api(f"/portfolio/remove/{holding['id']}", method="DELETE")
                            if result:
                                st.success(f"Removed {holding['symbol']}")
                                st.rerun()
                            else:
                                st.error(err or "Failed to remove")
                
                st.markdown("---")
                
                # Delete entire portfolio option
                if active_portfolio:
                    st.markdown("### ⚠️ Danger Zone")
                    if st.button(f"🗑️ Delete Entire Portfolio '{active_portfolio}'", type="secondary"):
                        if st.checkbox(f"I confirm I want to delete '{active_portfolio}' and all its holdings", key="confirm_delete"):
                            result, err = fetch_api(f"/portfolio/profile/{active_portfolio}", method="DELETE")
                            if result:
                                st.success(result['message'])
                                st.rerun()
                            else:
                                st.error(err or "Failed to delete portfolio")
            else:
                st.info("No holdings to manage. Add some positions first!")

    # ============== ALERTS PAGE ==============
    elif page == "🔔 Alerts":
        # Hero header
        st.markdown("""
        <div style="background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
                    padding: 30px; border-radius: 16px; margin-bottom: 20px;
                    box-shadow: 0 10px 30px rgba(239, 68, 68, 0.3);">
            <h1 style="color: white !important; -webkit-text-fill-color: white; margin: 0; font-size: 2rem;">
                🔔 Price Alerts
            </h1>
            <p style="color: rgba(255,255,255,0.8); margin: 10px 0 0 0;">
                Set up alerts for price movements and key metrics
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.info(DISCLAIMER_SHORT)
        
        # Check triggered alerts
        triggered, _ = fetch_api("/alerts/check")
        if triggered and triggered.get('triggered_count', 0) > 0:
            st.warning(f"⚠️ {triggered['triggered_count']} alert(s) triggered!")
            with st.expander("View Triggered Alerts", expanded=True):
                for alert in triggered['alerts']:
                    st.error(f"🚨 **{alert['symbol']}** ({alert['company_name']}): "
                            f"{alert['metric']} {alert['condition']} {alert['threshold']} "
                            f"(Current: {alert['current_value']:.2f})")
        
        st.markdown("---")
        
        tab1, tab2 = st.tabs(["📋 All Alerts", "➕ Create Alert"])
        
        with tab1:
            alerts, err = fetch_api("/alerts/")
            if alerts and len(alerts) > 0:
                df = pd.DataFrame(alerts)
                display_df = df[['id', 'symbol', 'company_name', 'metric', 'condition', 'threshold', 'current_value', 'status', 'triggered_count']].copy()
                display_df.columns = ['ID', 'Symbol', 'Company', 'Metric', 'Condition', 'Threshold', 'Current', 'Status', 'Triggers']
                st.dataframe(display_df, use_container_width=True, hide_index=True)
                
                # Delete alert
                st.subheader("Delete Alert")
                col1, col2 = st.columns([1, 3])
                with col1:
                    alert_id = st.number_input("Alert ID to delete", min_value=1, value=1)
                with col2:
                    if st.button("🗑️ Delete Alert", type="secondary"):
                        result, err = fetch_api(f"/alerts/delete/{alert_id}", method="DELETE")
                        if result:
                            st.success("Alert deleted!")
                            st.rerun()
                        else:
                            st.error(err or "Failed to delete alert")
            else:
                st.info("No alerts configured. Create your first alert!")
        
        with tab2:
            st.subheader("Create New Alert")
            
            # Fetch available stocks for dropdown
            available_stocks, _ = fetch_api("/stocks/?limit=100")
            if available_stocks:
                stock_options = {f"{s['symbol']} - {s['company_name']}": s for s in available_stocks}
                stock_list = list(stock_options.keys())
                
                with st.form("create_alert"):
                    col1, col2 = st.columns(2)
                    with col1:
                        selected_stock = st.selectbox(
                            "Select Stock",
                            options=stock_list,
                            help="Choose a stock to set alert for"
                        )
                        metric = st.selectbox(
                            "Metric", 
                            ["price", "pe_ratio", "promoter_holding"],
                            format_func=lambda x: {"price": "💰 Price", "pe_ratio": "📊 P/E Ratio", "promoter_holding": "👥 Promoter Holding"}[x]
                        )
                    with col2:
                        condition = st.selectbox(
                            "Condition", 
                            [">", "<", ">=", "<=", "=="],
                            format_func=lambda x: {">": "Greater than (>)", "<": "Less than (<)", ">=": "Greater or equal (≥)", "<=": "Less or equal (≤)", "==": "Equal to (=)"}[x]
                        )
                        # Get current value as reference
                        selected_data = stock_options.get(selected_stock, {})
                        current_val = float(selected_data.get(metric, 100.0)) if selected_data and metric in selected_data else 100.0
                        threshold = st.number_input("Threshold Value", min_value=0.0, value=current_val)
                    
                    # Show current value info
                    if selected_stock and selected_data:
                        current_metric_value = selected_data.get(metric, 'N/A')
                        st.info(f"📈 **{selected_data['symbol']}** | Current {metric}: {current_metric_value}")
                    
                    if st.form_submit_button("🔔 Create Alert", type="primary"):
                        symbol = selected_data['symbol']
                        data = {
                            "symbol": symbol,
                            "metric": metric,
                            "condition": condition,
                            "threshold": threshold
                        }
                        result, err = fetch_api("/alerts/create", method="POST", data=data)
                        if result:
                            st.success(f"Alert created for {symbol}: {metric} {condition} {threshold}")
                            st.rerun()
                        else:
                            st.error(err or "Failed to create alert")
            else:
                st.warning("Unable to load stock list. Please check backend connection.")

    # ============== ANALYTICS PAGE ==============
    # ============== ANALYTICS PAGE ==============
    elif page == "📊 Analytics":
        # Hero header
        st.markdown("""
        <div style="background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
                    padding: 30px; border-radius: 16px; margin-bottom: 20px;
                    box-shadow: 0 10px 30px rgba(139, 92, 246, 0.3);">
            <h1 style="color: white !important; -webkit-text-fill-color: white; margin: 0; font-size: 2rem;">
                📊 Market Analytics
            </h1>
            <p style="color: rgba(255,255,255,0.8); margin: 10px 0 0 0;">
                Comprehensive market insights and trend analysis
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.info(DISCLAIMER_SHORT)
        
        stocks, err = fetch_api("/stocks/?limit=100")
        if stocks:
            df = pd.DataFrame(stocks)
            
            # Key metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Stocks", len(df))
            with col2:
                avg_pe = df['pe_ratio'].mean()
                st.metric("Avg P/E Ratio", f"{avg_pe:.2f}")
            with col3:
                avg_promoter = df['promoter_holding'].mean()
                st.metric("Avg Promoter %", f"{avg_promoter:.1f}%")
            with col4:
                buyback_count = df['has_buyback'].sum()
                st.metric("With Buyback", int(buyback_count))
            
            st.markdown("---")
            
            # Charts
            chart_col1, chart_col2 = st.columns(2)
            
            with chart_col1:
                st.subheader("📊 P/E Ratio Distribution")
                fig = px.histogram(df, x='pe_ratio', nbins=20, 
                                  color_discrete_sequence=['#6366f1'])
                fig.update_layout(
                    xaxis_title="P/E Ratio", 
                    yaxis_title="Count",
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    xaxis=dict(gridcolor='#e2e8f0'),
                    yaxis=dict(gridcolor='#e2e8f0'),
                    margin=dict(t=20, b=40, l=40, r=20)
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with chart_col2:
                st.subheader("🏢 Sector-wise Average P/E")
                sector_pe = df.groupby('sector')['pe_ratio'].mean().sort_values(ascending=True)
                colors = ['#6366f1', '#8b5cf6', '#a855f7', '#ec4899', '#f43f5e', '#f59e0b']
                fig = px.bar(x=sector_pe.values, y=sector_pe.index, orientation='h',
                            color=sector_pe.index, color_discrete_sequence=colors)
                fig.update_layout(
                    xaxis_title="Average P/E Ratio", 
                    yaxis_title="",
                    showlegend=False,
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    xaxis=dict(gridcolor='#e2e8f0'),
                    margin=dict(t=20, b=40, l=100, r=20)
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Scatter plot
            st.subheader("📈 Price vs P/E Ratio (by Sector)")
            sector_colors = ['#6366f1', '#8b5cf6', '#a855f7', '#ec4899', '#f43f5e', '#f59e0b']
            fig = px.scatter(df, x='pe_ratio', y='price', color='sector',
                            size='market_cap', hover_data=['symbol', 'company_name'],
                            color_discrete_sequence=sector_colors)
            fig.update_layout(
                xaxis_title="P/E Ratio", 
                yaxis_title="Price ($)",
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(gridcolor='#e2e8f0'),
                yaxis=dict(gridcolor='#e2e8f0'),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Promoter holding analysis
            st.subheader("👥 Promoter Holding Analysis")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("""
                <div style="background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
                            padding: 15px; border-radius: 12px; border-left: 4px solid #10b981;">
                    <h4 style="color: #065f46; margin: 0;">High Promoter Holding</h4>
                </div>
                """, unsafe_allow_html=True)
                high_promoter = df[df['promoter_holding'] > 60]
                st.success(f"**{len(high_promoter)}** stocks have promoter holding > 60%")
                if len(high_promoter) > 0:
                    st.dataframe(high_promoter[['symbol', 'company_name', 'promoter_holding', 'pe_ratio']].head(10),
                                use_container_width=True, hide_index=True)
            with col2:
                st.markdown("""
                <div style="background: linear-gradient(135deg, #e0e7ff 0%, #c7d2fe 100%);
                            padding: 15px; border-radius: 12px; border-left: 4px solid #6366f1;">
                    <h4 style="color: #3730a3; margin: 0;">Low P/E Value Stocks</h4>
                </div>
                """, unsafe_allow_html=True)
                low_pe = df[df['pe_ratio'] < 15]
                st.info(f"**{len(low_pe)}** stocks have P/E Ratio < 15")
                if len(low_pe) > 0:
                    st.dataframe(low_pe[['symbol', 'company_name', 'pe_ratio', 'promoter_holding']].head(10),
                                use_container_width=True, hide_index=True)
        else:
            st.error(err or "Failed to load stock data")

    # Footer with full disclaimer
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("---")
    with st.expander("📜 Full Disclaimer & Legal Notice"):
        st.markdown(DISCLAIMER_FULL)
    
    # Styled footer
    st.markdown("""
    <div style="text-align: center; padding: 20px; margin-top: 20px;">
        <div style="display: inline-flex; align-items: center; gap: 10px; margin-bottom: 10px;">
            <span style="font-size: 1.5rem;">📈</span>
            <span style="font-weight: 700; font-size: 1.1rem; 
                        background: linear-gradient(90deg, #6366f1, #8b5cf6);
                        -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                StockSense AI
            </span>
        </div>
        <div style="color: #64748b; font-size: 0.85rem;">
            Intelligent Stock Analysis Platform | Built with FastAPI & Streamlit
        </div>
        <div style="color: #94a3b8; font-size: 0.75rem; margin-top: 5px;">
            © 2024 StockSense AI. For educational purposes only.
        </div>
    </div>
    """, unsafe_allow_html=True)


# ============== MAIN EXECUTION ==============
if st.session_state.logged_in:
    show_main_app()
else:
    show_login_page()
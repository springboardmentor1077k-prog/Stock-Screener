import streamlit as st
import pandas as pd
import time
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from utils.api import fetch_data, post_data
from utils.auth import init_auth_session, logout
from auth_ui import render_auth_interface
from utils.compliance import (
    global_disclaimer,
    banner_disclaimer,
    screener_disclaimer,
    alerts_disclaimer,
    portfolio_disclaimer,
    dashboard_disclaimer,
    compliance_level,
)

# --- Authentication Logic ---
init_auth_session()

if not st.session_state.authenticated:
    render_auth_interface()
    st.stop()

# --- Configuration ---
PAGE_TITLE = "Stock Analytics Platform"
PAGE_ICON = "📈"

# --- Page Setup ---
st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=PAGE_ICON,
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom Styling (Premium Look) ---
st.markdown("""
    <style>
    /* Main Background */
    .stApp {
        background-color: #f8fafc;
    }
    
    /* Global Font and Text Colors */
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        color: #1e293b;
    }
    
    /* Header Styling */
    h1, h2, h3 {
        font-weight: 700 !important;
        letter-spacing: -0.02em !important;
        color: #0f172a !important;
    }
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e2e8f0;
    }
    
    /* Card Component */
    .metric-card {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 24px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06);
    }
    
    /* Custom Metric Display */
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 4px;
    }
    .metric-label {
        font-size: 0.875rem;
        font-weight: 500;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .metric-delta {
        font-size: 0.875rem;
        font-weight: 600;
    }
    .delta-up { color: #10b981; }
    .delta-down { color: #ef4444; }
    
    /* Table Styling */
    .stDataFrame {
        border-radius: 8px;
        overflow: hidden;
    }
    
    /* Button Styling */
    .stButton > button {
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: all 0.2s !important;
    }
    .stButton > button:hover {
        opacity: 0.9 !important;
    }
    
    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 40px;
        font-weight: 600 !important;
    }
    
    /* Status Badges */
    .badge {
        padding: 4px 8px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .badge-success { background-color: #dcfce7; color: #166534; }
    .badge-warning { background-color: #fef9c3; color: #854d0e; }
    .badge-error { background-color: #fee2e2; color: #991b1b; }
    
    </style>
    """, unsafe_allow_html=True)

# --- Session State Initialization ---
if "screener_results" not in st.session_state:
    st.session_state.screener_results = None
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "Dashboard"

# --- Helper Components ---
def card_metric(label, value, delta=None, delta_up=True):
    delta_html = ""
    if delta is not None:
        delta_class = "delta-up" if delta_up else "delta-down"
        delta_sign = "+" if delta_up else ""
        delta_html = f'<div class="metric-delta {delta_class}">{delta_sign}{delta}</div>'
    
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            {delta_html}
        </div>
        """, unsafe_allow_html=True)

def section_header(title, subtitle=None):
    st.markdown(f"## {title}")
    if subtitle:
        st.markdown(f'<p style="color: #64748b; font-size: 1.1rem; margin-top: -10px;">{subtitle}</p>', unsafe_allow_html=True)

def handle_api_response(response, success_msg=None):
    if response is None:
        st.error("Failed to connect to the server.")
        return None
    
    if "error_code" in response:
        st.error(f"**{response.get('error_code')}**: {response.get('message')}")
        if response.get("details"):
            with st.expander("Technical Details"):
                st.json(response.get("details"))
        return None
    
    if success_msg:
        st.success(success_msg)
    return response

# --- Sidebar Navigation ---
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/000000/stocks.png", width=80)
    st.title("StockSense AI")
    st.markdown("---")
    
    nav_options = {
        "Dashboard": "🏠",
        "Screener": "🔎",
        "Portfolio": "💼",
        "Alert Center": "🔔"
    }
    
    for label, icon in nav_options.items():
        if st.button(f"{icon} {label}", use_container_width=True, type="secondary" if st.session_state.active_tab != label else "primary"):
            st.session_state.active_tab = label
            st.rerun()

    st.markdown("---")
    st.caption(f"**{compliance_level('medium')}**")
    st.caption(global_disclaimer())
    
    st.markdown("---")
    if st.button("🚪 Logout", use_container_width=True):
        logout()

# --- Page Content Router ---
active_tab = st.session_state.active_tab

if active_tab == "Dashboard":
    section_header(f"Welcome back, {st.session_state.username}", "Market overview and your performance at a glance.")
    st.info(dashboard_disclaimer())
    
    # Quick Stats
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        card_metric("Total Value", "$142,520.00", "2.4% vs last week", True)
    with col2:
        card_metric("Total P&L", "+$12,450.00", "5.1%", True)
    with col3:
        card_metric("Active Alerts", "8", "2 triggered today", True)
    with col4:
        card_metric("Market Sentiment", "Greed", "Bullish", True)
    
    st.markdown("---")
    
    # Main Dashboard Grid
    left_col, right_col = st.columns([2, 1])
    
    with left_col:
        st.subheader("Portfolio Performance")
        # Mock data for performance chart
        dates = pd.date_range(start="2023-01-01", periods=100, freq="D")
        values = [100000 * (1 + 0.002)**i for i in range(100)]
        perf_df = pd.DataFrame({"Date": dates, "Value": values})
        fig = px.line(perf_df, x="Date", y="Value", template="plotly_white")
        fig.update_layout(margin=dict(l=0, r=0, t=20, b=0), height=350)
        st.plotly_chart(fig, use_container_width=True)
        
    with right_col:
        st.subheader("Top Movers")
        # Mock data for top movers
        movers_df = pd.DataFrame({
            "Symbol": ["AAPL", "NVDA", "TSLA", "AMD", "META"],
            "Price": [182.52, 726.13, 193.57, 178.29, 484.03],
            "Change": ["+1.2%", "+4.5%", "-2.1%", "+3.1%", "+0.8%"]
        })
        st.table(movers_df)

elif active_tab == "Screener":
    section_header("Advanced Screener", "Discover your next opportunity with AI-powered search.")
    st.info(screener_disclaimer())
    
    with st.container():
        st.markdown("""
            <div style="background-color: #ffffff; padding: 24px; border-radius: 12px; border: 1px solid #e2e8f0; margin-bottom: 24px;">
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns([3, 1])
        with col1:
            query = st.text_input(
                "Search with Natural Language", 
                placeholder="e.g., 'Strong tech stocks with P/E under 30'",
                help="Our AI converts your sentence into a precise market query."
            )
        with col2:
            sector = st.selectbox("Sector Filter", ["All", "IT", "Finance", "Healthcare", "Energy", "Consumer Discretionary", "Industrials"])
            
        col3, col4, col5 = st.columns(3)
        with col3:
            market_cap = st.selectbox("Market Capitalization", ["Any", "Large Cap (>10B)", "Mid Cap (2B-10B)", "Small Cap (<2B)"])
        with col4:
            st.markdown("<br>", unsafe_allow_html=True)
            strong_only = st.checkbox("Require Strong Ratings", value=True)
        with col5:
            st.markdown("<br>", unsafe_allow_html=True)
            run_btn = st.button("Run Intelligence Scan", type="primary", use_container_width=True)
            
        st.markdown("</div>", unsafe_allow_html=True)

    if run_btn:
        with st.spinner("Analyzing market conditions..."):
            payload = {
                "query": query,
                "sector": sector,
                "strong_only": strong_only,
                "market_cap": market_cap
            }
            response = post_data("screen", payload)
            data = handle_api_response(response)
            
            if data:
                st.session_state.screener_results = data
                
    if st.session_state.screener_results:
        res = st.session_state.screener_results
        stocks = res.get("data", [])
        
        if not stocks:
            st.warning("No stocks matched your criteria. Try broadening your search.")
        else:
            col_a, col_b = st.columns([4, 1])
            with col_a:
                st.success(f"Found {len(stocks)} matches in {res.get('latency_ms', 0)}ms")
            with col_b:
                if res.get("cached"):
                    st.markdown('<span class="badge badge-success">⚡ Cached Result</span>', unsafe_allow_html=True)
            
            df = pd.DataFrame(stocks)
            # Formatting
            df['price'] = df['price'].apply(lambda x: f"${x:,.2f}")
            df['market_cap'] = df['market_cap'].apply(lambda x: f"${x:,.1f}B")
            
            st.dataframe(
                df[["symbol", "company_name", "price", "sector", "market_cap", "pe_ratio"]],
                use_container_width=True,
                hide_index=True
            )

elif active_tab == "Portfolio":
    section_header("My Portfolio", "Manage your holdings and monitor real-time performance.")
    st.info(portfolio_disclaimer())
    
    # Add to Portfolio Section
    with st.expander("➕ Add New Position", expanded=False):
        with st.form("add_portfolio_form"):
            col1, col2, col3 = st.columns(3)
            with col1:
                new_symbol = st.text_input("Stock Symbol", placeholder="AAPL").upper()
            with col2:
                new_qty = st.number_input("Quantity", min_value=1, step=1)
            with col3:
                new_price = st.number_input("Avg Buy Price", min_value=0.01, step=0.01, format="%.2f")
            
            add_submit = st.form_submit_button("Add to Portfolio", use_container_width=True)
            if add_submit:
                if not new_symbol:
                    st.error("Symbol is required.")
                else:
                    payload = {
                        "symbol": new_symbol,
                        "quantity": new_qty,
                        "avg_buy_price": new_price
                    }
                    response = post_data("portfolio", payload)
                    if handle_api_response(response, f"Successfully added {new_qty} shares of {new_symbol}"):
                        time.sleep(1)
                        st.rerun()

    with st.spinner("Fetching portfolio data..."):
        response = fetch_data("portfolio")
        res = handle_api_response(response)
        
        if res:
            holdings = res.get("data", [])
            if not holdings:
                st.warning("Your portfolio is currently empty.")
            else:
                # Summary Cards
                total_cost = sum(h['quantity'] * h['avg_buy_price'] for h in holdings)
                total_current = sum(h['quantity'] * h['current_price'] for h in holdings)
                total_pl = total_current - total_cost
                pl_percent = (total_pl / total_cost * 100) if total_cost > 0 else 0
                
                c1, c2, c3 = st.columns(3)
                with c1:
                    card_metric("Current Value", f"${total_current:,.2f}")
                with c2:
                    card_metric("Total Profit/Loss", f"${total_pl:,.2f}", f"{pl_percent:,.1f}%", total_pl >= 0)
                with c3:
                    card_metric("Positions", str(len(holdings)))
                
                st.markdown("---")
                
                # Detailed Table
                df = pd.DataFrame(holdings)
                df['total_value'] = df['quantity'] * df['current_price']
                
                # Formatting
                df['avg_buy_price'] = df['avg_buy_price'].apply(lambda x: f"${x:,.2f}")
                df['current_price'] = df['current_price'].apply(lambda x: f"${x:,.2f}")
                df['profit_loss'] = df['profit_loss'].apply(lambda x: f"${x:,.2f}")
                df['total_value'] = df['total_value'].apply(lambda x: f"${x:,.2f}")
                
                st.dataframe(
                    df[["symbol", "company_name", "quantity", "avg_buy_price", "current_price", "total_value", "profit_loss"]],
                    use_container_width=True,
                    hide_index=True,
                    height=500  # Increased height to show more rows
                )

elif active_tab == "Alert Center":
    section_header("Alert Center", "Never miss a move. Set up custom price triggers.")
    st.info(alerts_disclaimer())
    
    tab1, tab2 = st.tabs(["Active Alerts", "Create New Alert"])
    
    with tab1:
        col_btn, col_empty = st.columns([1, 4])
        with col_btn:
            check_btn = st.button("Check All Alerts Now", type="primary", use_container_width=True)
            
        if check_btn:
            with st.spinner("Evaluating conditions..."):
                response = post_data("alerts/checks", {})
                handle_api_response(response, "Alert check completed successfully.")
        
        # List Alerts
        response = fetch_data("alerts")
        res = handle_api_response(response)
        if res:
            alerts = res.get("data", [])
            if not alerts:
                st.info("No active alerts. Create one in the next tab.")
            else:
                df = pd.DataFrame(alerts)
                df['status'] = df['is_active'].apply(lambda x: "Active" if x else "Triggered")
                st.dataframe(
                    df[["id", "metric", "operator", "threshold", "status"]],
                    use_container_width=True,
                    hide_index=True
                )

    with tab2:
        with st.form("create_alert_form"):
            st.subheader("New Alert Configuration")
            c1, c2, c3 = st.columns(3)
            with c1:
                symbol = st.text_input("Stock Symbol", placeholder="AAPL").upper()
            with c2:
                condition = st.selectbox("Condition", ["Above Price", "Below Price"])
            with c3:
                value = st.number_input("Threshold Price", min_value=0.01, step=0.01, format="%.2f")
            
            submit = st.form_submit_button("Set Alert", use_container_width=True)
            
            if submit:
                if not symbol:
                    st.error("Symbol is required.")
                else:
                    payload = {"symbol": symbol, "condition": condition, "value": value}
                    response = post_data("alerts", payload)
                    handle_api_response(response, f"Alert created for {symbol} at {value}")

# --- Footer ---
st.markdown("---")

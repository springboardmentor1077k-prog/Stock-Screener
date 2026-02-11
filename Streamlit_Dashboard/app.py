import streamlit as st
import pandas as pd
import time
from utils.api import fetch_data, post_data
from utils.compliance import (
    global_disclaimer,
    banner_disclaimer,
    screener_disclaimer,
    analyst_disclaimer,
    alerts_disclaimer,
    compliance_level,
)

# --- Configuration ---
PAGE_TITLE = "Stock Screener Dashboard"
PAGE_ICON = "📈"

# --- Page Setup ---
st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=PAGE_ICON,
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Session State Initialization ---
if "screener_results" not in st.session_state:
    st.session_state.screener_results = None

# --- Helper Functions ---
def handle_api_response(response, success_callback, error_callback=None):
    """
    Centralized handler for API responses.
    """
    if response.get("status") == "success":
        return success_callback(response.get("data"))
    elif "errorCode" in response:
        st.error("Query rejected by compliance")
        if error_callback: error_callback(response)
        return None
    else:
        msg = response.get("message")
        if msg:
            st.error(msg)
        else:
            st.error("Invalid response format from server")
        return None

# --- Page Renderers ---

def render_screener_page():
    st.header("🔎 Stock Screener")
    st.caption("Filter stocks based on market criteria and AI analysis.")
    st.info(banner_disclaimer())
    st.caption(compliance_level("medium"))

    # --- Step 1: Query Input Section ---
    with st.container():
        st.subheader("Screening Criteria")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            query = st.text_input(
                "Enter stock query", 
                placeholder="Search by sector, symbol, or description (e.g. 'Tech stocks with high growth')"
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
            run_btn = st.button("Run Screener", type="primary", use_container_width=True)

    st.divider()

    # --- Step 2 & 3: Action & Loading ---
    if run_btn:
        with st.spinner("Running screener... Analyzing market data..."):
            payload = {
                "query": query,
                "sector": sector,
                "strong_only": strong_only,
                "market_cap": market_cap
            }
            response = post_data("screen", payload)
            st.session_state.screener_results = response

    # --- Step 4: Handle Responses ---
    if st.session_state.screener_results:
        response = st.session_state.screener_results
        
        def show_results(data):
            if data:
                st.success(f"Found {len(data)} matching stocks")
                df = pd.DataFrame(data)
                st.dataframe(
                    df, 
                    use_container_width=True, 
                    hide_index=True,
                    column_config={
                        "price": st.column_config.NumberColumn("Price", format="$%.2f"),
                        "market_cap": st.column_config.NumberColumn("Market Cap", format="$%.2f B"),
                        "pe_ratio": st.column_config.NumberColumn("PE Ratio", format="%.2f"),
                        "sector": "Sector",
                        "company_name": "Company"
                    }
                )
                st.caption(screener_disclaimer())
            else:
                st.info("No matching stocks found. Try adjusting your filters.")
                
        handle_api_response(response, show_results)

def render_portfolio_page():
    st.header("💼 My Portfolio")
    st.caption("Track your current holdings and performance.")
    st.info(banner_disclaimer())
    st.caption(compliance_level("very_high"))
    
    col1, col2 = st.columns([3, 1])
    with col2:
        refresh = st.button("🔄 Refresh Data")
    
    # Fetch Data
    with st.spinner("Loading portfolio..."):
        response = fetch_data("portfolio")
        
    def show_portfolio(data):
        if not data:
            st.info("Your portfolio is empty.")
            return

        df = pd.DataFrame(data)
        
        # Calculate totals
        total_value = (df['current_price'] * df['quantity']).sum()
        total_profit = df['profit_loss'].sum()
        
        with col1:
             st.metric(
                 label="Total Portfolio Value", 
                 value=f"${total_value:,.2f}", 
                 delta=f"${total_profit:,.2f}"
             )
        
        st.divider()
        st.subheader("Holdings")
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "symbol": "Symbol",
                "quantity": "Shares",
                "avg_buy_price": st.column_config.NumberColumn("Avg Price", format="$%.2f"),
                "current_price": st.column_config.NumberColumn("Current Price", format="$%.2f"),
                "profit_loss": st.column_config.NumberColumn("Profit/Loss", format="$%.2f"),
                "company_name": "Company"
            }
        )
        st.caption(global_disclaimer())

    handle_api_response(response, show_portfolio)

def render_alerts_page():
    st.header("🔔 Price Alerts")
    st.caption("Manage your stock price alerts.")
    st.info(banner_disclaimer())
    st.caption(compliance_level("medium"))
    
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
                with st.spinner("Creating alert..."):
                    payload = {
                        "symbol": symbol, 
                        "condition": condition, 
                        "value": value
                    }
                    response = post_data("alerts", payload)
                    
                    def on_success(data):
                        st.success(f"Alert set for {symbol} {condition} ${value}")
                        # Trigger rerun to update list
                        time.sleep(1)
                        st.rerun()
                    
                    handle_api_response(response, lambda d: on_success(d))
            else:
                st.warning("Please enter a valid symbol and price.")
        st.caption(alerts_disclaimer())

    st.divider()
    
    st.subheader("Active Alerts")
    with st.spinner("Loading alerts..."):
        response = fetch_data("alerts")
        
    def show_alerts(data):
        if data:
            df = pd.DataFrame(data)
            st.dataframe(
                df, 
                use_container_width=True, 
                hide_index=True,
                column_config={
                    "metric": "Condition Metric",
                    "operator": "Operator",
                    "threshold": "Threshold",
                    "is_active": "Active?"
                }
            )
            st.caption(alerts_disclaimer())
        else:
            st.info("No active alerts.")

    handle_api_response(response, show_alerts)

# --- Main App Layout ---

def main():
    # Sidebar Navigation
    with st.sidebar:
        st.title("📊 StockDash")
        page = st.radio(
            "Navigation", 
            ["Screener", "Portfolio", "Alerts"],
            index=0
        )
        
        st.divider()
        st.markdown("### About")
        st.info(global_disclaimer())

    # Main Page Content
    # st.title("Stock Screener Dashboard") # Already in renderers or sidebar title
    
    if page == "Screener":
        render_screener_page()
    elif page == "Portfolio":
        render_portfolio_page()
    elif page == "Alerts":
        render_alerts_page()

if __name__ == "__main__":
    main()

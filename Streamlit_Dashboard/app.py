import streamlit as st
import requests
import pandas as pd
import time

# --- Configuration ---
BACKEND_URL = "http://localhost:5000/screen"
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

# --- Helper Functions ---
def run_screener(query, sector, strong_only, market_cap):
    """
    Calls the backend API to screen stocks based on criteria.
    """
    payload = {
        "query": query,
        "sector": sector,
        "strong_only": strong_only,
        "market_cap": market_cap
    }
    
    try:
        response = requests.post(BACKEND_URL, json=payload, timeout=10)
        response.raise_for_status() # Raise error for bad status codes
        return response.json()
    except requests.exceptions.ConnectionError:
        return {"status": "error", "message": "Server not reachable. Please check if the backend is running."}
    except requests.exceptions.RequestException as e:
        return {"status": "error", "message": f"Error fetching data: {str(e)}"}
    except Exception as e:
        return {"status": "error", "message": f"Unexpected error: {str(e)}"}

# --- Page Renderers ---

def render_screener_page():
    st.header("🔎 Stock Screener")
    st.caption("Filter stocks based on market criteria and AI analysis.")

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
                st.dataframe(
                    df, 
                    use_container_width=True, 
                    hide_index=True,
                    column_config={
                        "price": st.column_config.NumberColumn("Price", format="$%.2f"),
                        "market_cap": st.column_config.NumberColumn("Market Cap", format="$%.2f B"),
                        "change": st.column_config.NumberColumn("Change", format="%.2f%%")
                    }
                )
            else:
                st.info("No matching stocks found. Try adjusting your filters.")
                
        elif result.get("status") == "error":
            st.error(result.get("message", "Unknown error occurred"))
        else:
            st.warning("Received unexpected response format from server.")

def render_portfolio_page():
    st.header("💼 My Portfolio")
    st.caption("Track your current holdings and performance.")
    
    with st.container():
        col1, col2 = st.columns([3, 1])
        with col1:
             st.metric(label="Total Portfolio Value", value="$14,520.50", delta="+12.5%")
        with col2:
            st.button("🔄 Refresh Data")

    st.divider()
    
    st.subheader("Holdings")
    
    # Editable dataframe for simple add/remove simulation or just display
    edited_df = st.data_editor(
        st.session_state.portfolio,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True
    )
    
    # Update session state if changed (though data_editor handles basic edits, syncing is good practice)
    st.session_state.portfolio = edited_df

    st.caption("You can edit the table directly to simulate adding/removing positions.")

def render_alerts_page():
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
        st.info(
            "This dashboard connects to our advanced Stock Screener API to help you find the best investment opportunities."
        )

    # Main Page Content
    st.title("Stock Screener Dashboard")
    st.caption("Smart stock analysis and alerts")
    st.divider()

    if page == "Screener":
        render_screener_page()
    elif page == "Portfolio":
        render_portfolio_page()
    elif page == "Alerts":
        render_alerts_page()

if __name__ == "__main__":
    main()

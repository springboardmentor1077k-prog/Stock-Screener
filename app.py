import streamlit as st
from streamlit_option_menu import option_menu
import requests
import pandas as pd
import time

# Configuration
API_URL = "http://127.0.0.1:8000"
st.set_page_config(page_title="AI Stock Screener", page_icon="📈", layout="wide")

# Session State Management
if 'token' not in st.session_state:
    st.session_state.token = None
if 'username' not in st.session_state:
    st.session_state.username = None
if 'role' not in st.session_state:
    st.session_state.role = None
if 'current_page' not in st.session_state:
    st.session_state.current_page = "My Portfolio"

def api_request(method, endpoint, data=None):
    """Helper for making authenticated API requests"""
    headers = {"Authorization": f"Bearer {st.session_state.token}"} if st.session_state.token else {}
    try:
        if method == "GET":
            res = requests.get(f"{API_URL}{endpoint}", headers=headers)
        elif method == "POST":
            res = requests.post(f"{API_URL}{endpoint}", json=data, headers=headers)
        elif method == "DELETE":
            res = requests.delete(f"{API_URL}{endpoint}", headers=headers)
        return res
    except requests.exceptions.ConnectionError:
        st.error("Could not connect to Backend. Is it running?")
        return None

# ==========================================
# 1. AUTHENTICATION SCREENS
# ==========================================
if not st.session_state.token:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("Login to AI Screener")
        tab1, tab2 = st.tabs(["Login", "Register"])
        
        with tab1:
            u_login = st.text_input("Username", key="login_u")
            p_login = st.text_input("Password", type="password", key="login_p")
            if st.button("Login", type="primary"):
                res = requests.post(f"{API_URL}/login", json={"username": u_login, "password": p_login})
                if res and res.status_code == 200:
                    data = res.json()
                    st.session_state.token = data['access_token']
                    # Decode token loosely to get role (in production, verify properly)
                    st.session_state.username = u_login
                    st.rerun()
                else:
                    st.error("Invalid Username or Password")

        with tab2:
            u_reg = st.text_input("New Username", key="reg_u")
            p_reg = st.text_input("New Password", type="password", key="reg_p")
            p_confirm = st.text_input("Confirm Password", type="password", key="reg_p_confirm")
            
            if st.button("Register"):
                # 1. Check if fields are empty
                if not u_reg or not p_reg:
                    st.warning("Please fill in all fields.")
                
                # 2. Check if passwords match
                elif p_reg != p_confirm:
                    st.error("Passwords do not match. Please try again.")
                
                # 3. If everything is good, send to backend
                else:
                    res = requests.post(f"{API_URL}/register", json={"username": u_reg, "password": p_reg})
                    if res and res.status_code == 200:
                        st.success("Account created! Please log in.")
                    else:
                        st.error("Username already exists or error occurred.")

# ==========================================
# 2. MAIN DASHBOARD (LOGGED IN)
# ==========================================
else:
    # --- Sidebar ---
    with st.sidebar:
        def nav_button(label, page_name):
            # If this page is active, add a visual marker (➤)
            if st.session_state.current_page == page_name:
                display_label = f"➤ **{label}**"
                type_ = "primary" # Highlights the button
            else:
                display_label = f"{label}"
                type_ = "secondary" # Standard grey button
            
            # Create the button
            if st.button(display_label, key=f"nav_{page_name}", use_container_width=True, type=type_):
                st.session_state.current_page = page_name
                st.session_state.selected_symbol = None
                st.session_state.selected_portfolio_stock = None
                st.rerun()

        # Render Navigation Buttons
        nav_button("My Portfolio", "My Portfolio")
        nav_button("AI Screener", "AI Screener")
        nav_button("Alerts", "Alerts")
        
        st.divider()
        
        # User & Admin Controls
        st.caption(f"Logged in as: {st.session_state.username}")
        if st.session_state.username == "admin":
            if st.button("🔄 Refresh Data", use_container_width=True):
                api_request("POST", "/admin/refresh")
                st.toast("Updating Market Data...")
                
        if st.button("Log Out", use_container_width=True):
            # 1. Clear Credentials
            st.session_state.token = None
            st.session_state.username = None
            st.session_state.role = None
            
            # 2. Reset UI State (So next user starts fresh)
            st.session_state.current_page = "My Portfolio"  # Reset navigation
            st.session_state.selected_symbol = None        # Close any open popups
            st.session_state.selected_portfolio_stock = None
            
            # 3. Reload
            st.rerun()
            
    # Use the session state to determine which page to show
    page = st.session_state.current_page

# --- Page 1: AI Screener ---
    if page == "AI Screener":
        st.title("🤖 AI Stock Screener")
        st.caption("Try: 'IT stocks with PE < 30' or 'Banks with price below 1500'")
        
        # --- Search Bar
        with st.form("search_form"):
            c1, c2 = st.columns([4, 1])
            query = c1.text_input("Search", label_visibility="collapsed", placeholder="Ask AI...")
            submit_search = c2.form_submit_button("Search", type="primary")
        
        # Session State for Selected Stock
        if 'selected_symbol' not in st.session_state:
            st.session_state.selected_symbol = None

        # --- DETERMINE WHAT TO SHOW ---
        if submit_search and query.strip():
            # 1. AI SEARCH MODE
            with st.spinner("Analyzing Market..."):
                res = api_request("POST", "/screener/query", {"query": query})
                
                if res and res.status_code == 200:
                    data = res.json()
                    results = data.get("results")
                    if isinstance(results, list) and len(results) > 0:
                        st.success(f"Found {len(results)} stocks matching your query.")
                        df_to_show = pd.DataFrame(results)
                    elif isinstance(results, dict):
                        st.warning(results.get("message", "No data."))
                        df_to_show = None
                    else:
                        st.info("No stocks found.")
                        df_to_show = None
                else:
                    st.error("Search failed.")
                    df_to_show = None

        else:
            # 2. DEFAULT MODE (Show all stocks instantly using Redis)
            st.subheader("Market Overview (Live)")
            res = api_request("GET", "/stocks")
            if res and res.status_code == 200:
                results = res.json()
                if results:
                    df_to_show = pd.DataFrame(results)
                    # Clean up the display columns a bit
                    df_to_show = df_to_show[['symbol', 'company', 'sector', 'price', 'pe', 'growth']]
                else:
                    st.info("No stocks in database.")
                    df_to_show = None
            else:
                st.error("Could not load market data.")
                df_to_show = None

        # If we have data (either from Search or Default), show the interactive table
        if df_to_show is not None and not df_to_show.empty:
            event = st.dataframe(
                df_to_show,
                on_select="rerun",
                selection_mode="single-row",
                use_container_width=True,
                hide_index=True
            )
            
            # Handle Click Event to open Popup
            if len(event.selection.rows) > 0:
                idx = event.selection.rows[0]
                symbol = df_to_show.iloc[idx]['symbol']
                st.session_state.selected_symbol = symbol

        # --- THE DETAILED POPUP ---
        if st.session_state.selected_symbol:
            # Fetch Full Details from Backend
            res = api_request("GET", f"/stocks/{st.session_state.selected_symbol}")
            
            if res and res.status_code == 200:
                stock_data = res.json()
                info = stock_data['info']
                fund = stock_data['fundamentals']
                quarters = stock_data['quarterly']

                @st.dialog(f"📊 {info['company']} ({info['symbol']})", width="large")
                def show_details():
                    # Top Metric Row
                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("Price", f"₹{fund['current_price']:,.2f}")
                    m2.metric("P/E Ratio", f"{fund['pe_ratio']:.2f}")
                    m3.metric("Growth (YoY)", f"{fund['revenue_growth']}%")
                    m4.metric("Sector", info['sector'])
                    
                    st.divider()
                    
                    # Tabs for Organization
                    tab1, tab2, tab3 = st.tabs(["📈 Financials", "📋 Fundamentals", "💰 Buy Stock"])
                    
                    with tab1:
                        st.subheader("📊 Growth Trends")
                        if quarters:
                            # 1. Prepare Data
                            q_df = pd.DataFrame(quarters)
                            q_df['date'] = pd.to_datetime(q_df['date']) # Ensure date format
                            q_df = q_df.sort_values('date')             # Sort oldest to newest
                            
                            # 2. Chart A: Revenue vs Profit (The Big Picture)
                            st.caption("Revenue (Blue) vs Net Profit (Red)")
                            st.bar_chart(q_df.set_index("date")[["revenue", "profit"]], color=["#0000FF", "#FF0000"])
                            
                            st.divider()
                            
                            # 3. Chart B: Net Profit Growth (The Trend)
                            st.caption("📈 Net Profit Growth Trajectory")
                            st.line_chart(q_df.set_index("date")["profit"], color="#00FF00")
                            
                        else:
                            st.info("No quarterly data available.")

                    with tab2:
                        st.subheader("Key Ratios")
                        c1, c2 = st.columns(2)
                        with c1:
                            st.write(f"**Market Cap:** ₹{fund['market_cap']:,.0f}")
                            st.write(f"**PEG Ratio:** {fund['peg_ratio']}")
                        with c2:
                            st.write(f"**Promoter Holding:** {fund['promoter_holding']}%")
                            st.write(f"**Debt to FCF:** {fund['debt_to_fcf']}")

                    with tab3:
                        st.subheader("Add to Portfolio")
                        with st.form("buy_form"):
                            q_qty = st.number_input("Quantity", min_value=1, value=10)
                            # Pre-fill with current market price
                            q_price = st.number_input("Buy Price", value=float(fund['current_price']))
                            
                            if st.form_submit_button("✅ Add to Portfolio", type="primary"):
                                res = api_request("POST", "/portfolio/add", {
                                    "symbol": info['symbol'],
                                    "quantity": q_qty,
                                    "buy_price": q_price
                                })
                                if res.status_code == 200:
                                    st.success(f"Added {info['symbol']}!")
                                    time.sleep(1)
                                    st.session_state.selected_symbol = None # Close popup
                                    st.rerun()
                                else:
                                    st.error("Failed to add.")

                # Open the dialog
                show_details()
                
    # --- Page 2: Portfolio ---
    elif page == "My Portfolio":
        st.title("My Portfolio")
        
        # 1. Fetch Portfolio
        res = api_request("GET", "/portfolio")
        
        # Initialize session state for portfolio selection if not exists
        if 'selected_portfolio_stock' not in st.session_state:
            st.session_state.selected_portfolio_stock = None

        if res and res.status_code == 200:
            portfolio = res.json()
            
            if portfolio:
                df = pd.DataFrame(portfolio)
                
                # A. Metrics Row
                total_val = df['value'].sum()
                total_pl = df['p&l'].sum()
                c1, c2, c3 = st.columns(3)
                c1.metric("Total Value", f"₹{total_val:,.2f}")
                c2.metric("Total P&L", f"₹{total_pl:,.2f}", delta=f"{total_pl:,.2f}")
                
                st.divider()

                # B. The Interactive Table
                st.caption("💡 Tip: Click on a row to Sell or Buy more.")
                event = st.dataframe(
                    df,
                    on_select="rerun",             # Reload when clicked
                    selection_mode="single-row",   # Pick one stock
                    use_container_width=True,
                    hide_index=True
                )

                # C. Handle Selection (The Popup)
                if len(event.selection.rows) > 0:
                    idx = event.selection.rows[0]
                    selected_row = df.iloc[idx]
                    st.session_state.selected_portfolio_stock = selected_row

            else:
                st.info("Your portfolio is empty. Add stocks from the Screener!")

            # --- THE MANAGE STOCK POPUP ---
            if st.session_state.selected_portfolio_stock is not None:
                stock = st.session_state.selected_portfolio_stock
                symbol = stock['symbol']
                owned_qty = stock['qty']
                current_price = stock['cur_price']
                
                @st.dialog(f"Manage {symbol}", width="small")
                def manage_stock_popup():
                    st.write(f"You own **{owned_qty}** shares worth **₹{stock['value']:,.2f}**")
                    
                    # Tabs for Action
                    tab_sell, tab_buy = st.tabs(["🔴 Sell / Reduce", "🟢 Buy More"])
                    
                    # --- TAB 1: SELL ---
                    with tab_sell:
                        with st.form("sell_form"):
                            # Smart Defaults
                            s_qty = st.number_input("Sell Quantity", min_value=1.0, max_value=float(owned_qty), value=1.0, step=1.0)
                            s_price = st.number_input("Sell Price", value=float(current_price))
                            
                            st.caption(f"Est. Value: ₹{s_qty * s_price:,.2f}")
                            
                            if st.form_submit_button("🔥 Sell Now", type="primary"):
                                res = api_request("POST", "/portfolio/sell", {
                                    "symbol": symbol,
                                    "quantity": s_qty,
                                    "sell_price": s_price
                                })
                                if res.status_code == 200:
                                    st.success(f"Sold {s_qty} {symbol}!")
                                    time.sleep(1)
                                    st.session_state.selected_portfolio_stock = None
                                    st.rerun()
                                else:
                                    st.error("Sell Failed.")

                    # --- TAB 2: BUY MORE ---
                    with tab_buy:
                        with st.form("buy_more_form"):
                            b_qty = st.number_input("Add Quantity", min_value=1.0, value=1.0, step=1.0)
                            b_price = st.number_input("Buy Price", value=float(current_price))
                            
                            if st.form_submit_button("✅ Add to Portfolio"):
                                res = api_request("POST", "/portfolio/add", {
                                    "symbol": symbol,
                                    "quantity": b_qty,
                                    "buy_price": b_price
                                })
                                if res.status_code == 200:
                                    st.success(f"Added {b_qty} {symbol}!")
                                    time.sleep(1)
                                    st.session_state.selected_portfolio_stock = None
                                    st.rerun()
                                else:
                                    st.error("Add Failed.")

                manage_stock_popup()

        # D. Fallback Manual Add (Hidden in Expander)
        st.divider()
        with st.expander("Add New Stock Manually (If not in list)"):
            with st.form("manual_add"):
                c1, c2, c3 = st.columns(3)
                sym = c1.text_input("Symbol")
                qty = c2.number_input("Qty", min_value=1.0, step=1.0)
                price = c3.number_input("Price", min_value=0.1)
                if st.form_submit_button("Add"):
                    api_request("POST", "/portfolio/add", {"symbol": sym, "quantity": qty, "buy_price": price})
                    st.rerun()
                        
    # --- Page 3: Alerts ---
    elif page == "Alerts":
        st.title("Price Alerts")
        st.caption("Get notified when stocks hit your target price.")
        
        # ---------------------------------------------------------
        # SECTION 1: SET NEW ALERT
        # ---------------------------------------------------------
        with st.container(border=True):
            st.subheader("Set New Alert")
            c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
            
            with c1:
                new_sym = st.text_input("Symbol", placeholder="e.g. INFOSYS")
            with c2:
                new_cond = st.selectbox("Condition", ["price_above", "price_below"])
            with c3:
                new_val = st.number_input("Target Price", min_value=0.1)
            with c4:
                st.write("") # Spacer to align button
                st.write("") 
                if st.button("Set", type="primary", use_container_width=True):
                    if new_sym and new_val > 0:
                        with st.spinner("Setting alert..."):
                            res = api_request("POST", "/alerts", {
                                "symbol": new_sym.upper(),
                                "condition": new_cond,
                                "value": new_val
                            })
                            if res.status_code == 200:
                                st.success(f"Alert set for {new_sym}!")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("Failed. Check symbol.")
                    else:
                        st.warning("Enter symbol & price.")

        # ---------------------------------------------------------
        # SECTION 2: THE "SLIDING WINDOW" (TABS)
        # ---------------------------------------------------------
        # Fetch all alerts first
        res = api_request("GET", "/alerts")
        
        if res and res.status_code == 200:
            all_alerts = res.json()
            
            # Split into two lists using Python list comprehensions
            active_alerts = [a for a in all_alerts if a['active']]
            history_alerts = [a for a in all_alerts if not a['active']]
            
            # Create Tabs
            tab_active, tab_history = st.tabs([
                f"Active ({len(active_alerts)})", 
                f"History ({len(history_alerts)})"
            ])
            
            # --- TAB A: ACTIVE ALERTS ---
            with tab_active:
                if active_alerts:
                    st.caption("Waiting for price targets to hit...")
                    for a in active_alerts:
                        with st.container(border=True):
                            c1, c2, c3 = st.columns([2, 2, 1])
                            c1.markdown(f"**{a['symbol']}**")
                            cond_text = "🔻 drops below" if a['condition'] == 'price_below' else "🔺 rises above"
                            c2.markdown(f"{cond_text} **₹{a['target']}**")
                            
                            if c3.button("Delete", key=f"del_act_{a['id']}"):
                                api_request("DELETE", f"/alerts/{a['id']}")
                                st.rerun()
                else:
                    st.info("No active alerts. Set one above!")

            # --- TAB B: HISTORY (TRIGGERED) ---
            with tab_history:
                if history_alerts:
                    st.caption("Alerts that have already triggered.")
                    for a in history_alerts:
                        with st.container(border=True):
                            c1, c2, c3 = st.columns([2, 2, 1])
                            c1.markdown(f"~~{a['symbol']}~~") # Strikethrough style
                            cond_text = "🔻 dropped below" if a['condition'] == 'price_below' else "🔺 rose above"
                            c2.markdown(f"{cond_text} **₹{a['target']}**")
                            
                            # Allow deleting history too to clear clutter
                            if c3.button("❌ Clear", key=f"del_hist_{a['id']}"):
                                api_request("DELETE", f"/alerts/{a['id']}")
                                st.rerun()
                else:
                    st.info("No alert history yet.")
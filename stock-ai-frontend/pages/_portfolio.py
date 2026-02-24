"""
Portfolio Page - Manage your stock portfolio with quantity tracking.

This page allows users to:
- View their portfolio from the backend
- Add stocks with quantity and buy price
- Remove stocks from portfolio
- See portfolio holdings with quantities
"""

import streamlit as st
import pandas as pd


def render_portfolio():
    """Render the portfolio management page."""
    
    # Initialize API client
    if "api_client" not in st.session_state:
        from api_client import APIClient
        st.session_state.api_client = APIClient()
    
    api_client = st.session_state.api_client
    
    # Hide default Streamlit page nav (we use custom nav above)
    st.markdown("""<style>[data-testid="stSidebarNav"] {display: none;}</style>""", unsafe_allow_html=True)
    
    # Sidebar navigation
    with st.sidebar:
        st.header("📈 AI Stock Screener")
        st.divider()
        st.page_link("pages/_screener.py", label="📊 Screener", icon=None)
        st.page_link("pages/_portfolio.py", label="💼 Portfolio", icon=None)
        st.page_link("pages/_alerts.py", label="🔔 Alerts", icon=None)
    
    # Display user email in top right
    col_title, col_email, col_logout = st.columns([3, 1, 1])
    with col_title:
        st.title("💼 My Portfolio")
    with col_email:
        if "email" in st.session_state and st.session_state.email:
            st.markdown(f"<div style='text-align: right; padding-top: 20px;'>👤 {st.session_state.email}</div>", unsafe_allow_html=True)
    with col_logout:
        st.write("")
        st.write("")
        if st.button("🚪 Logout", key="logout_portfolio"):
            # Clear session state
            st.session_state.token = None
            st.session_state.email = None
            st.session_state.user_id = None
            st.session_state.authenticated = False
            st.switch_page("app.py")
    
    # Page header
    st.caption("Manage your stock holdings")
    st.warning("Disclaimer: This platform is for informational purposes only and is not financial advice.")
    
    # Check authentication
    if "token" not in st.session_state or not st.session_state.token:
        st.error("🔒 Please login first")
        return
    
    # Get portfolios from backend
    success, message, data = api_client.get_portfolios(st.session_state.token)
    
    if not success:
        st.error(f"❌ Error loading portfolios: {message}")
        return
    
    portfolios = data.get("items", data.get("portfolios", [])) or []
    
    # Select portfolio (for now use first portfolio or default to ID 1)
    if portfolios:
        portfolio_id = portfolios[0].get("id")
        portfolio_name = portfolios[0].get("name", "My Portfolio")
        stock_count = portfolios[0].get("stock_count", 0)
        if not portfolio_id:
            st.error("❌ Invalid portfolio data received from server.")
            return
        st.info(f"📊 Portfolio: **{portfolio_name}** ({stock_count} stocks)")
    else:
        portfolio_id = 1  # Default portfolio
        st.info("📊 Using default portfolio (ID: 1)")
    
    # Fetch available stocks for dropdown
    success_stocks, msg_stocks, stocks_data = api_client.get_stocks(st.session_state.token)
    
    if not success_stocks:
        st.error(f"❌ Error loading stocks: {msg_stocks}")
        return
    
    available_stocks = stocks_data.get("items", stocks_data.get("stocks", [])) or []
    
    # Add stock section
    st.subheader("➕ Add Stock to Portfolio")
    st.caption("Price is automatically fetched from database")
    
    with st.form("add_stock_form"):
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            # Create dropdown options with symbol and company name
            stock_options = ["Select a stock..."] + [
                f"{stock.get('symbol', 'N/A')} - {stock.get('company_name', 'Unknown')}"
                for stock in available_stocks
            ]
            
            selected_stock = st.selectbox(
                "Stock",
                stock_options,
                help="Select a stock to add to your portfolio"
            )
        
        with col2:
            quantity = st.number_input(
                "Quantity",
                min_value=1,
                value=1,
                step=1,
                help="Number of shares"
            )
        
        with col3:
            st.write("")
            st.write("")
            add_button = st.form_submit_button(
                "✅ Add",
                use_container_width=True,
                type="primary"
            )
        
        if add_button:
            if selected_stock and selected_stock != "Select a stock...":
                # Extract symbol from selection
                stock_symbol = selected_stock.split(" - ")[0]
                
                with st.spinner(f"Adding {stock_symbol}..."):
                    success, msg = api_client.add_to_portfolio(
                        portfolio_id=portfolio_id,
                        stock_symbol=stock_symbol,
                        quantity=quantity,
                        token=st.session_state.token
                    )
                
                if success:
                    st.success(f"✅ {msg}")
                    st.rerun()
                else:
                    st.error(f"❌ {msg}")
            else:
                st.warning("⚠️ Please select a stock")
    
    # Display holdings
    st.divider()
    st.subheader("📈 Current Holdings")
    
    # Fetch holdings from backend
    success, message, holdings_data = api_client.get_portfolio_holdings(
        portfolio_id,
        st.session_state.token
    )
    
    if not success:
        st.error(f"❌ Error loading holdings: {message}")
        return
    
    holdings = holdings_data.get("items", holdings_data.get("holdings", [])) or []
    
    if len(holdings) == 0:
        st.info("📭 No stocks in portfolio. Add some above!")
    else:
        # Display holdings count
        st.success(f"✅ {len(holdings)} stock(s) in portfolio")
        
        # Convert to DataFrame
        df = pd.DataFrame(holdings)
        
        # Calculate total value if possible
        if 'quantity' in df.columns and 'avg_buy_price' in df.columns:
            df['total_value'] = df['quantity'] * df['avg_buy_price']
        
        # Display holdings table
        st.dataframe(
            df[[col for col in ['symbol', 'company_name', 'quantity', 'avg_buy_price', 'total_value', 'created_at'] if col in df.columns]],
            use_container_width=True,
            hide_index=True,
            column_config={
                "symbol": "Symbol",
                "company_name": "Company",
                "quantity": st.column_config.NumberColumn("Quantity", format="%d"),
                "avg_buy_price": st.column_config.NumberColumn("Avg Price", format="$%.2f"),
                "total_value": st.column_config.NumberColumn("Total Value", format="$%.2f"),
                "created_at": "Added On"
            }
        )
        
        # Show total portfolio value
        if 'total_value' in df.columns:
            total_portfolio_value = df['total_value'].sum()
            st.metric(
                "Total Portfolio Value",
                f"${total_portfolio_value:,.2f}",
                help="Sum of all holdings (quantity × avg buy price)"
            )
        
        # Remove stock section
        st.divider()
        col1, col2 = st.columns([3, 1])
        
        with col1:
            remove_options = [
                f"ID {h.get('id')}: {h.get('symbol', 'N/A')} ({h.get('quantity', 0)} shares)"
                for h in holdings
                if h.get("id") is not None
            ]
            
            selected_holding = st.selectbox(
                "Remove holding",
                ["Select holding..."] + remove_options
            )
        
        with col2:
            st.write("")
            st.write("")
            if st.button("🗑️ Remove", use_container_width=True, type="secondary"):
                if selected_holding and selected_holding != "Select holding...":
                    # Extract holding ID
                    holding_id = int(selected_holding.split(":")[0].replace("ID ", ""))
                    
                    with st.spinner("Removing holding..."):
                        success, msg = api_client.remove_from_portfolio(
                            holding_id,
                            st.session_state.token
                        )
                    
                    if success:
                        st.success(f"✅ {msg}")
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")


if __name__ == "__main__":
    render_portfolio()

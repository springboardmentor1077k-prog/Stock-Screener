"""
Screener Page - Main stock screening functionality.

This page allows users to:
- Enter natural language queries for stock screening
- Execute queries and view results
- See matching stocks with recommendations
"""

import streamlit as st
import pandas as pd
from api_client import APIClient


def render_screener():
    """Render the stock screener page."""
    
    # Initialize API client
    if "api_client" not in st.session_state:
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
        st.title("📊 Stock Screener")
    with col_email:
        if "email" in st.session_state and st.session_state.email:
            st.markdown(f"<div style='text-align: right; padding-top: 20px;'>👤 {st.session_state.email}</div>", unsafe_allow_html=True)
    with col_logout:
        st.write("")
        st.write("")
        if st.button("🚪 Logout", key="logout_screener"):
            # Clear session state
            st.session_state.token = None
            st.session_state.email = None
            st.session_state.user_id = None
            st.session_state.authenticated = False
            st.switch_page("app.py")
    
    # Page header - title and caption
    st.caption("Use natural language to find stocks matching your criteria")
    st.warning("Disclaimer: This platform is for informational purposes only and is not financial advice.")
    
    # Create two-column layout for better organization
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Query input section with placeholder
        query = st.text_input(
            "Enter your screening query",
            placeholder="e.g., Stocks with PE ratio less than 25",
            help="Enter a natural language query to filter stocks"
        )
    
    with col2:
        # Add some spacing to align button with input
        st.write("")
        st.write("")
        # Action button - RUN
        run_button = st.button("🚀 RUN", use_container_width=True, type="primary")
    
    # Execute query when RUN button is clicked
    if run_button:
        if not query.strip():
            st.warning("⚠️ Please enter a query")
        else:
            # Check if user is authenticated
            if "token" not in st.session_state or not st.session_state.token:
                st.error("🔒 Please login first")
                return
            
            # Loading feedback - spinner
            with st.spinner("🔍 Searching for matching stocks..."):
                # Backend call
                success, message, data = api_client.screen_stocks(
                    query,
                    st.session_state.token
                )
            
            # Display results
            if success:
                count = data.get("total", data.get("count", 0)) or 0
                rows = data.get("items", data.get("rows", [])) or []
                
                if count == 0:
                    # No results found
                    st.info("ℹ️ No matching stocks found")
                else:
                    # Success - display results
                    st.success(f"✅ {message}")
                    
                    # Convert to DataFrame for display
                    normalized_rows = []
                    for row in rows:
                        if isinstance(row, dict):
                            normalized_rows.append({
                                "symbol": row.get("symbol") or "N/A",
                                "company_name": row.get("company_name") or "N/A",
                                "cp": row.get("cp"),
                                "tp": row.get("tp"),
                                "upside_percent": row.get("upside_percent"),
                                "recommendation": row.get("recommendation") or "N/A",
                            })
                    df = pd.DataFrame(normalized_rows)
                    
                    # Use st.dataframe() to display results as table
                    st.dataframe(
                        df,
                        use_container_width=True,
                        hide_index=True
                    )
                    
                    # Caption explaining abbreviations
                    st.caption("cp = Current Price | tp = Target Price")
                    
                    # Store results in session state for portfolio addition
                    st.session_state.last_results = rows
            else:
                # Error handling
                st.error(f"❌ {message}")


if __name__ == "__main__":
    render_screener()
